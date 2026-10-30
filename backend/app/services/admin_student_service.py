"""Nghiệp vụ: Nhà trường: quản lý dữ liệu sinh viên. Người phụ trách: TV2.

Gồm:
  - list_students, get_student_detail, update_academic_data
  - import_students (upsert theo student_code, báo cáo lỗi từng dòng, KHÔNG dừng cả file vì 1 dòng lỗi)
  - issue_account (sinh token kích hoạt + gửi email), add_achievement, delete_achievement, verify_certificate

File import (.xlsx/.csv), dòng đầu là tiêu đề. Cột bắt buộc: student_code, full_name, email, faculty, major,
cohort. Cột tùy chọn: date_of_birth, class_name, gpa, academic_result, phone. `faculty` và `major` ghi mã hoặc tên.
Tiêu đề tiếng Việt thông dụng (Mã sinh viên, Họ và tên, Ngày sinh, Lớp, Khoa, Ngành, Khóa học, GPA, ...)
cũng được nhận, xem HEADER_ALIASES.

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
import re
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from fastapi import BackgroundTasks
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.enums import ImportType, UserRole, UserStatus
from app.core.exceptions import AppException, BadRequestError, ConflictError, NotFoundError
from app.core.security import generate_reset_token
from app.models import (
    Faculty,
    ImportBatch,
    Major,
    PasswordResetToken,
    Student,
    StudentAchievement,
    StudentCertificate,
    StudentProfile,
    User,
)
from app.schemas.admin_students import AchievementCreate, StudentAcademicUpdate
from app.schemas.common import PageParams
from app.services import email_service, notification_service
from app.utils.datetime_utils import utcnow
from app.utils.pagination import paginate
from app.utils.spreadsheet import read_rows

ACTIVATION_TOKEN_EXPIRE_DAYS = 7
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REQUIRED_FIELDS = ("student_code", "full_name", "email", "faculty", "major", "cohort")
# Tiêu đề (đã bỏ dấu, viết thường) -> tên trường chuẩn
HEADER_ALIASES = {
    "student_code": ("student_code", "ma sinh vien", "ma sv", "mssv"),
    "full_name": ("full_name", "ho va ten", "ho ten", "ten sinh vien"),
    "email": ("email", "e-mail"),
    "date_of_birth": ("date_of_birth", "ngay sinh", "dob"),
    "class_name": ("class_name", "lop", "ten lop"),
    "faculty": ("faculty", "faculty_code", "faculty_name", "khoa", "ma khoa", "ten khoa"),
    "major": ("major", "major_code", "major_name", "nganh", "ma nganh", "ten nganh"),
    "cohort": ("cohort", "khoa hoc", "nien khoa", "khoa tuyen sinh"),
    "gpa": ("gpa", "diem tb", "diem trung binh"),
    "academic_result": ("academic_result", "xep loai", "xep loai hoc luc"),
    "phone": ("phone", "so dien thoai", "sdt", "dien thoai"),
}
_ALIAS_TO_FIELD = {alias: field for field, aliases in HEADER_ALIASES.items() for alias in aliases}


class _RowError(Exception):
    """Lỗi dữ liệu của một dòng import (không làm hỏng cả file)."""


# ---------------------------------------------------------------- Đọc dữ liệu
def _student_row(student: Student) -> dict:
    return {
        "id": student.id,
        "user_id": student.user_id,
        "student_code": student.student_code,
        "full_name": student.full_name,
        "email": student.user.email,
        "account_status": student.user.status,
        "date_of_birth": student.date_of_birth,
        "class_name": student.class_name,
        "faculty_id": student.faculty_id,
        "faculty_name": student.faculty.name,
        "major_id": student.major_id,
        "major_name": student.major.name,
        "cohort": student.cohort,
        "gpa": student.gpa,
        "academic_result": student.academic_result,
        "phone": student.phone,
        "synced_at": student.synced_at,
    }


def get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise NotFoundError("Không tìm thấy sinh viên")
    return student


def list_students(
    db: Session,
    params: PageParams,
    *,
    q: str | None = None,
    faculty_id: int | None = None,
    major_id: int | None = None,
    cohort: str | None = None,
    account_status: UserStatus | None = None,
) -> dict:
    stmt = (
        select(Student)
        .join(User, Student.user_id == User.id)
        .options(selectinload(Student.user), selectinload(Student.faculty), selectinload(Student.major))
    )
    if faculty_id is not None:
        stmt = stmt.where(Student.faculty_id == faculty_id)
    if major_id is not None:
        stmt = stmt.where(Student.major_id == major_id)
    if cohort:
        stmt = stmt.where(Student.cohort == cohort)
    if account_status is not None:
        stmt = stmt.where(User.status == account_status)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Student.student_code.ilike(like), Student.full_name.ilike(like), User.email.ilike(like))
        )
    page = paginate(db, stmt.order_by(Student.student_code), params)
    page["items"] = [_student_row(s) for s in page["items"]]
    return page


def get_student_detail(db: Session, student_id: int) -> dict:
    """Chi tiết sinh viên, tách rõ dữ liệu của trường (official) và sinh viên tự khai (self_declared)."""
    student = get_student(db, student_id)
    profile = student.profile
    return {
        "official": {
            "academic": _student_row(student),
            "achievements": student.achievements,
            "school_certificates": [c for c in student.certificates if c.source.value == "SCHOOL"],
        },
        "self_declared": {
            "profile": profile,
            "skills": [
                {"skill_id": s.skill_id, "name": s.skill.name, "level": s.level, "source": s.source}
                for s in student.skills
            ],
            "experiences": student.experiences,
            "projects": student.projects,
            "certificates": [c for c in student.certificates if c.source.value == "SELF"],
        },
    }


# ---------------------------------------------------------------- Cập nhật dữ liệu học thuật
def update_academic_data(db: Session, student_id: int, data: StudentAcademicUpdate) -> dict:
    student = get_student(db, student_id)
    changes = data.model_dump(exclude_unset=True)
    # Các trường bắt buộc trong DB không được set về null
    for field in ("full_name", "faculty_id", "major_id", "cohort"):
        if field in changes and changes[field] is None:
            raise BadRequestError(f"Trường {field} không được để trống")

    faculty_id = changes.get("faculty_id", student.faculty_id)
    major_id = changes.get("major_id", student.major_id)
    if "faculty_id" in changes and db.get(Faculty, faculty_id) is None:
        raise NotFoundError("Không tìm thấy khoa")
    major = db.get(Major, major_id)
    if major is None:
        raise NotFoundError("Không tìm thấy ngành")
    if major.faculty_id != faculty_id:
        raise BadRequestError("Ngành không thuộc khoa đã chọn")

    for field, value in changes.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return _student_row(student)


# ---------------------------------------------------------------- Cấp tài khoản / email kích hoạt
def _activation_email_html(student: Student, link: str) -> str:
    return (
        f"<p>Chào {student.full_name},</p>"
        f"<p>Nhà trường đã tạo tài khoản cho bạn trên hệ thống kết nối doanh nghiệp - sinh viên "
        f"(mã sinh viên: <b>{student.student_code}</b>).</p>"
        f'<p>Vui lòng <a href="{link}">bấm vào đây để kích hoạt tài khoản và đặt mật khẩu</a>. '
        f"Liên kết có hiệu lực {ACTIVATION_TOKEN_EXPIRE_DAYS} ngày.</p>"
        f"<p>Nếu không bấm được, hãy sao chép địa chỉ sau vào trình duyệt: {link}</p>"
    )


def _send_activation(db: Session, background_tasks: BackgroundTasks, student: Student) -> None:
    """Sinh token kích hoạt (chỉ lưu hash), thu hồi token chưa dùng cũ, xếp hàng gửi email."""
    raw, token_hash = generate_reset_token()
    db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == student.user_id, PasswordResetToken.used_at.is_(None)
        )
    )
    db.add(
        PasswordResetToken(
            user_id=student.user_id,
            token_hash=token_hash,
            expires_at=utcnow() + timedelta(days=ACTIVATION_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()
    link = f"{settings.FRONTEND_URL.rstrip('/')}/activate?token={raw}"
    email_service.queue_email(
        db,
        background_tasks,
        to_email=student.user.email,
        subject="Kích hoạt tài khoản sinh viên",
        body_html=_activation_email_html(student, link),
        type="ACCOUNT_ACTIVATION",
        user_id=student.user_id,
        ref_type="STUDENT",
        ref_id=student.id,
    )


def issue_account(db: Session, background_tasks: BackgroundTasks, student_id: int) -> None:
    """Cấp tài khoản / gửi lại email kích hoạt. Chỉ áp dụng cho tài khoản đang chờ kích hoạt."""
    student = get_student(db, student_id)
    if student.user.status != UserStatus.PENDING_ACTIVATION:
        raise ConflictError("Tài khoản không ở trạng thái chờ kích hoạt")
    _send_activation(db, background_tasks, student)


# ---------------------------------------------------------------- Thành tích
def add_achievement(db: Session, student_id: int, data: AchievementCreate) -> StudentAchievement:
    student = get_student(db, student_id)
    achievement = StudentAchievement(student_id=student.id, **data.model_dump())
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return achievement


def delete_achievement(db: Session, student_id: int, achievement_id: int) -> None:
    achievement = db.get(StudentAchievement, achievement_id)
    if achievement is None or achievement.student_id != student_id:
        raise NotFoundError("Không tìm thấy thành tích của sinh viên này")
    db.delete(achievement)
    db.commit()


# ---------------------------------------------------------------- Xác thực chứng chỉ
def verify_certificate(db: Session, certificate_id: int, admin: User) -> StudentCertificate:
    cert = db.get(StudentCertificate, certificate_id)
    if cert is None:
        raise NotFoundError("Không tìm thấy chứng chỉ")
    if not cert.is_verified:
        cert.is_verified = True
        cert.verified_by = admin.id
        cert.verified_at = utcnow()
        db.commit()
        db.refresh(cert)
        student = db.get(Student, cert.student_id)
        notification_service.create_notification(
            db,
            user_id=student.user_id,
            type="CERTIFICATE_VERIFIED",
            title="Chứng chỉ đã được nhà trường xác thực",
            content=f"Chứng chỉ \"{cert.name}\" của bạn đã được xác thực.",
            ref_type="CERTIFICATE",
            ref_id=cert.id,
        )
    return cert


# ---------------------------------------------------------------- Đồng bộ (chưa có nguồn)
def sync_students(db: Session) -> None:
    raise AppException("Chưa có nguồn đồng bộ từ hệ thống đào tạo", code="NOT_IMPLEMENTED", status_code=501)


# ---------------------------------------------------------------- Import sinh viên
def _strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def canonical_row(row: dict[str, str]) -> dict[str, str]:
    """Đổi tiêu đề cột về tên trường chuẩn (bỏ dấu, không phân biệt hoa thường)."""
    result: dict[str, str] = {}
    for header, value in row.items():
        key = " ".join(_strip_accents(header).lower().split())
        field = _ALIAS_TO_FIELD.get(key)
        if field and field not in result:
            result[field] = value
    return result


def _parse_date(value: str) -> date:
    text = value.strip()[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", value.strip()) else value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise _RowError(f"Ngày sinh '{value}' không hợp lệ (dùng dd/mm/yyyy hoặc yyyy-mm-dd)")


def _parse_gpa(value: str) -> Decimal:
    try:
        gpa = Decimal(value.replace(",", "."))
    except InvalidOperation:
        raise _RowError(f"GPA '{value}' không phải số") from None
    if not Decimal(0) <= gpa <= Decimal(4):
        raise _RowError(f"GPA {value} ngoài khoảng 0-4")
    return gpa.quantize(Decimal("0.01"))


class _Lookups:
    """Tra khoa/ngành theo mã hoặc tên (không phân biệt hoa thường), nạp một lần cho cả file."""

    def __init__(self, db: Session):
        self.faculties: dict[str, Faculty] = {}
        for faculty in db.scalars(select(Faculty).where(Faculty.is_active.is_(True))):
            self.faculties[faculty.code.lower()] = faculty
            self.faculties[faculty.name.lower()] = faculty
        self.majors: dict[str, list[Major]] = {}
        for major in db.scalars(select(Major).where(Major.is_active.is_(True))):
            for key in {major.code.lower(), major.name.lower()}:
                self.majors.setdefault(key, []).append(major)

    def faculty(self, value: str) -> Faculty:
        faculty = self.faculties.get(value.lower())
        if faculty is None:
            raise _RowError(f"Không tìm thấy khoa '{value}'")
        return faculty

    def major(self, value: str, faculty: Faculty) -> Major:
        candidates = [m for m in self.majors.get(value.lower(), []) if m.faculty_id == faculty.id]
        if not candidates:
            raise _RowError(f"Không tìm thấy ngành '{value}' thuộc khoa '{faculty.name}'")
        return candidates[0]


def _apply_row(db: Session, fields: dict[str, str], lookups: _Lookups, batch: ImportBatch) -> tuple[str, Student]:
    """Tạo mới hoặc cập nhật một sinh viên. Raise _RowError nếu dữ liệu sai."""
    code = fields.get("student_code", "")
    student = db.scalar(select(Student).where(func.lower(Student.student_code) == code.lower()))

    missing = [f for f in REQUIRED_FIELDS if not fields.get(f)]
    if student is not None:
        # Cập nhật: chỉ cần mã sinh viên; ô trống nghĩa là giữ nguyên dữ liệu cũ
        missing = [f for f in missing if f == "student_code"]
    if missing:
        raise _RowError(f"Thiếu dữ liệu bắt buộc: {', '.join(missing)}")

    values: dict = {}
    if fields.get("full_name"):
        values["full_name"] = fields["full_name"]
    if fields.get("cohort"):
        values["cohort"] = fields["cohort"]
    if fields.get("date_of_birth"):
        values["date_of_birth"] = _parse_date(fields["date_of_birth"])
    if fields.get("gpa"):
        values["gpa"] = _parse_gpa(fields["gpa"])
    for field in ("class_name", "academic_result", "phone"):
        if fields.get(field):
            values[field] = fields[field]

    faculty = major = None
    if fields.get("faculty"):
        faculty = lookups.faculty(fields["faculty"])
    elif student is not None:
        faculty = student.faculty
    if fields.get("major"):
        major = lookups.major(fields["major"], faculty)
    elif student is not None and fields.get("faculty"):
        # Đổi khoa mà không ghi ngành mới: ngành cũ phải còn thuộc khoa mới
        if student.major.faculty_id != faculty.id:
            raise _RowError("Đổi khoa thì phải ghi cả ngành thuộc khoa mới")
    if faculty is not None and (student is None or fields.get("faculty")):
        values["faculty_id"] = faculty.id
    if major is not None:
        values["major_id"] = major.id

    if student is not None:
        for field, value in values.items():
            setattr(student, field, value)
        student.import_batch_id = batch.id
        db.flush()
        return "updated", student

    email = fields["email"].lower()
    if not EMAIL_PATTERN.match(email):
        raise _RowError(f"Email '{fields['email']}' không hợp lệ")
    if db.scalar(select(User.id).where(func.lower(User.email) == email)) is not None:
        raise _RowError(f"Email '{fields['email']}' đã được dùng bởi tài khoản khác")

    user = User(email=email, password_hash=None, role=UserRole.STUDENT, status=UserStatus.PENDING_ACTIVATION)
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, student_code=code, import_batch_id=batch.id, **values)
    db.add(student)
    db.flush()
    db.add(StudentProfile(student_id=student.id))
    db.flush()
    return "created", student


def import_students(
    db: Session, background_tasks: BackgroundTasks, admin: User, filename: str, content: bytes
) -> dict:
    """Import sinh viên từ Excel/CSV. Một dòng lỗi chỉ bị bỏ qua và ghi vào error_report, các dòng còn lại vẫn lưu."""
    rows = read_rows(filename, content)
    if not rows:
        raise BadRequestError("File không có dòng dữ liệu nào")
    present = set(canonical_row(rows[0]))
    missing_columns = [f for f in REQUIRED_FIELDS if f not in present]
    if missing_columns:
        raise BadRequestError(f"File thiếu cột bắt buộc: {', '.join(missing_columns)}")

    batch = ImportBatch(type=ImportType.STUDENTS, file_name=filename, total_rows=len(rows), imported_by=admin.id)
    db.add(batch)
    db.flush()

    lookups = _Lookups(db)
    errors: list[dict] = []
    created: list[Student] = []
    updated = 0
    for index, raw in enumerate(rows):
        row_number = index + 2  # dòng 1 là tiêu đề
        fields = canonical_row(raw)
        code = fields.get("student_code") or None
        try:
            if not code:
                raise _RowError("Thiếu mã sinh viên")
            with db.begin_nested():
                outcome, student = _apply_row(db, fields, lookups, batch)
        except _RowError as exc:
            errors.append({"row": row_number, "key": code, "message": str(exc)})
            continue
        except IntegrityError:
            errors.append({"row": row_number, "key": code, "message": "Dữ liệu trùng hoặc vi phạm ràng buộc"})
            continue
        if outcome == "created":
            created.append(student)
        else:
            updated += 1

    batch.success_rows = len(created) + updated
    batch.failed_rows = len(errors)
    batch.error_report = {"errors": errors}
    db.commit()
    db.refresh(batch)

    for student in created:
        _send_activation(db, background_tasks, student)

    return {
        "batch": {**_batch_dict(batch), "errors": errors},
        "activation_emails_queued": len(created),
    }


# ---------------------------------------------------------------- Lịch sử import
def _batch_dict(batch: ImportBatch) -> dict:
    return {
        "id": batch.id,
        "type": batch.type,
        "file_name": batch.file_name,
        "total_rows": batch.total_rows,
        "success_rows": batch.success_rows,
        "failed_rows": batch.failed_rows,
        "imported_by": batch.imported_by,
        "created_at": batch.created_at,
    }


def list_import_batches(db: Session, params: PageParams, *, type: ImportType | None = None) -> dict:
    stmt = select(ImportBatch)
    if type is not None:
        stmt = stmt.where(ImportBatch.type == type)
    return paginate(db, stmt.order_by(ImportBatch.id.desc()), params)


def get_import_batch(db: Session, batch_id: int) -> dict:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise NotFoundError("Không tìm thấy lần import")
    return {**_batch_dict(batch), "errors": (batch.error_report or {}).get("errors", [])}
