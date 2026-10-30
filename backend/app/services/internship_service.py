"""Nghiệp vụ: Thực tập theo đợt & kết quả thực tập. Người phụ trách: TV2.

Gồm:
  - CRUD đợt + chuyển trạng thái hợp lệ (DRAFT -> OPEN -> ONGOING -> CLOSED, chỉ tiến một bước)
  - add_students / import_term_students / remove_student / assign_lecturers
  - submit_company_evaluation (kiểm tra công ty đúng là nơi sinh viên thực tập), lecturer_review, confirm_result
  - is_student_in_term(db, student_id, term_id) — TV3 (ứng tuyển), TV4 (tìm tin) và TV5 (matching) gọi hàm này

Mỗi sinh viên trong đợt có đúng một InternshipResult (tạo cùng lúc với TermStudent, mặc định PENDING).

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import (
    ApplicationStatus,
    ImportType,
    InternshipResultStatus,
    JobStatus,
    TermStatus,
    UserRole,
    UserStatus,
)
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models import (
    Application,
    Company,
    ImportBatch,
    InternshipResult,
    InternshipTerm,
    Job,
    Lecturer,
    Student,
    TermStudent,
    User,
)
from app.schemas.common import PageParams
from app.schemas.internship_terms import (
    CompanyEvaluation,
    LecturerReview,
    TermCreate,
    TermUpdate,
)
from app.services import notification_service
from app.services.admin_student_service import canonical_row
from app.utils.datetime_utils import utcnow
from app.utils.pagination import paginate
from app.utils.spreadsheet import read_numbered_rows

# Chuyển trạng thái hợp lệ của đợt: chỉ tiến một bước
NEXT_STATUS = {
    TermStatus.DRAFT: TermStatus.OPEN,
    TermStatus.OPEN: TermStatus.ONGOING,
    TermStatus.ONGOING: TermStatus.CLOSED,
}


# ---------------------------------------------------------------- Hàm cho module khác
def is_student_in_term(db: Session, student_id: int, term_id: int) -> bool:
    """True nếu sinh viên nằm trong danh sách của đợt thực tập."""
    stmt = select(TermStudent.id).where(
        TermStudent.term_id == term_id, TermStudent.student_id == student_id
    )
    return db.scalar(stmt) is not None


# ---------------------------------------------------------------- Đợt thực tập
def _term_rows(db: Session, terms: list[InternshipTerm]) -> list[dict]:
    counts: dict[int, int] = {}
    if terms:
        counts = dict(
            db.execute(
                select(TermStudent.term_id, func.count())
                .where(TermStudent.term_id.in_([t.id for t in terms]))
                .group_by(TermStudent.term_id)
            ).all()
        )
    return [
        {
            "id": t.id,
            "name": t.name,
            "semester": t.semester,
            "academic_year": t.academic_year,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "status": t.status,
            "created_by": t.created_by,
            "created_at": t.created_at,
            "student_count": counts.get(t.id, 0),
        }
        for t in terms
    ]


def get_term(db: Session, term_id: int) -> InternshipTerm:
    term = db.get(InternshipTerm, term_id)
    if term is None:
        raise NotFoundError("Không tìm thấy đợt thực tập")
    return term


def _ensure_can_view(db: Session, user: User, term_id: int) -> InternshipTerm:
    """Admin xem được mọi đợt; sinh viên chỉ xem đợt của mình; doanh nghiệp không có quyền."""
    term = get_term(db, term_id)
    if user.role == UserRole.ADMIN:
        return term
    if (
        user.role == UserRole.STUDENT
        and user.student is not None
        and is_student_in_term(db, user.student.id, term_id)
    ):
        return term
    raise ForbiddenError("Bạn không thuộc đợt thực tập này")


def list_terms(
    db: Session,
    user: User,
    params: PageParams,
    *,
    academic_year: str | None = None,
    semester: str | None = None,
    status: TermStatus | None = None,
) -> dict:
    stmt = select(InternshipTerm)
    if user.role == UserRole.STUDENT:
        student_id = user.student.id if user.student else None
        stmt = stmt.join(TermStudent, TermStudent.term_id == InternshipTerm.id).where(
            TermStudent.student_id == student_id
        )
    elif user.role != UserRole.ADMIN:
        raise ForbiddenError("Bạn không có quyền xem danh sách đợt thực tập")
    if academic_year:
        stmt = stmt.where(InternshipTerm.academic_year == academic_year)
    if semester:
        stmt = stmt.where(InternshipTerm.semester == semester)
    if status is not None:
        stmt = stmt.where(InternshipTerm.status == status)
    page = paginate(
        db, stmt.order_by(InternshipTerm.start_date.desc(), InternshipTerm.id.desc()), params
    )
    page["items"] = _term_rows(db, page["items"])
    return page


def get_term_detail(db: Session, user: User, term_id: int) -> dict:
    return _term_rows(db, [_ensure_can_view(db, user, term_id)])[0]


def create_term(db: Session, admin: User, data: TermCreate) -> dict:
    term = InternshipTerm(**data.model_dump(), created_by=admin.id)
    db.add(term)
    db.commit()
    db.refresh(term)
    return _term_rows(db, [term])[0]


def update_term(db: Session, term_id: int, data: TermUpdate) -> dict:
    term = get_term(db, term_id)
    if term.status == TermStatus.CLOSED:
        raise ConflictError("Đợt thực tập đã đóng, không thể chỉnh sửa")
    changes = data.model_dump(exclude_unset=True)
    for field in changes:
        if changes[field] is None:
            raise BadRequestError(f"Trường {field} không được để trống")
    for field, value in changes.items():
        setattr(term, field, value)
    if term.start_date > term.end_date:
        db.rollback()
        raise BadRequestError("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc")
    db.commit()
    db.refresh(term)
    return _term_rows(db, [term])[0]


def change_status(db: Session, term_id: int, new_status: TermStatus) -> dict:
    term = get_term(db, term_id)
    if NEXT_STATUS.get(term.status) != new_status:
        raise BadRequestError(
            f"Không thể chuyển đợt từ {term.status.value} sang {new_status.value}"
        )
    term.status = new_status
    db.commit()
    db.refresh(term)
    return _term_rows(db, [term])[0]


# ---------------------------------------------------------------- Sinh viên trong đợt
def _ensure_editable(term: InternshipTerm) -> None:
    if term.status == TermStatus.CLOSED:
        raise ConflictError("Đợt thực tập đã đóng, không thể thay đổi danh sách sinh viên")


def _add_to_term(db: Session, term: InternshipTerm, student: Student) -> None:
    term_student = TermStudent(term_id=term.id, student_id=student.id)
    term_student.result = InternshipResult()
    db.add(term_student)
    notification_service.create_notification(
        db,
        user_id=student.user_id,
        type="TERM_ASSIGNED",
        title="Bạn đã được thêm vào đợt thực tập",
        content=f'Nhà trường đã thêm bạn vào đợt "{term.name}" ({term.academic_year}, {term.semester}).',
        ref_type="TERM",
        ref_id=term.id,
        commit=False,
    )


def add_students(db: Session, term_id: int, student_ids: list[int]) -> dict:
    term = get_term(db, term_id)
    _ensure_editable(term)
    wanted = list(dict.fromkeys(student_ids))
    students = {s.id: s for s in db.scalars(select(Student).where(Student.id.in_(wanted)))}
    existing = set(db.scalars(select(TermStudent.student_id).where(TermStudent.term_id == term_id)))
    added = 0
    already = 0
    for student_id in wanted:
        if student_id not in students:
            continue
        if student_id in existing:
            already += 1
            continue
        _add_to_term(db, term, students[student_id])
        added += 1
    db.commit()
    return {
        "added": added,
        "already_in_term": already,
        "not_found_ids": [i for i in wanted if i not in students],
    }


def import_term_students(
    db: Session, admin: User, term_id: int, filename: str, content: bytes
) -> dict:
    """Thêm sinh viên vào đợt theo mã sinh viên từ Excel/CSV (cột student_code). Dòng lỗi được ghi vào báo cáo."""
    term = get_term(db, term_id)
    _ensure_editable(term)
    rows = read_numbered_rows(filename, content)
    if not rows:
        raise BadRequestError("File không có dòng dữ liệu nào")
    if "student_code" not in canonical_row(rows[0][1]):
        raise BadRequestError("File thiếu cột bắt buộc: student_code")

    batch = ImportBatch(
        type=ImportType.TERM_STUDENTS,
        file_name=filename,
        total_rows=len(rows),
        imported_by=admin.id,
    )
    db.add(batch)
    db.flush()

    existing = set(db.scalars(select(TermStudent.student_id).where(TermStudent.term_id == term_id)))
    errors: list[dict] = []
    added = 0
    for row_number, raw in rows:
        if "_import_error" in raw:
            errors.append({"row": row_number, "key": None, "message": raw["_import_error"]})
            continue
        code = canonical_row(raw).get("student_code") or None
        if not code:
            errors.append({"row": row_number, "key": None, "message": "Thiếu mã sinh viên"})
            continue
        student = db.scalar(select(Student).where(func.lower(Student.student_code) == code.lower()))
        if student is None:
            errors.append({"row": row_number, "key": code, "message": "Không tìm thấy sinh viên"})
        elif student.id in existing:
            errors.append({"row": row_number, "key": code, "message": "Sinh viên đã thuộc đợt này"})
        else:
            _add_to_term(db, term, student)
            existing.add(student.id)
            added += 1

    batch.success_rows = added
    batch.failed_rows = len(errors)
    batch.error_report = {"errors": errors}
    db.commit()
    db.refresh(batch)
    return {
        "batch": {
            "id": batch.id,
            "type": batch.type,
            "file_name": batch.file_name,
            "total_rows": batch.total_rows,
            "success_rows": batch.success_rows,
            "failed_rows": batch.failed_rows,
            "imported_by": batch.imported_by,
            "created_at": batch.created_at,
            "errors": errors,
        },
        "added": added,
    }


def remove_student(db: Session, term_id: int, student_id: int) -> None:
    term = get_term(db, term_id)
    _ensure_editable(term)
    term_student = db.scalar(
        select(TermStudent).where(
            TermStudent.term_id == term_id, TermStudent.student_id == student_id
        )
    )
    if term_student is None:
        raise NotFoundError("Sinh viên không thuộc đợt thực tập này")
    result = term_student.result
    if result is not None and (
        result.result != InternshipResultStatus.PENDING or result.company_evaluation
    ):
        raise ConflictError("Sinh viên đã có đánh giá/kết quả thực tập, không thể xóa khỏi đợt")
    db.delete(term_student)
    db.commit()


def list_term_students(
    db: Session,
    term_id: int,
    params: PageParams,
    *,
    q: str | None = None,
    lecturer_id: int | None = None,
) -> dict:
    get_term(db, term_id)
    stmt = (
        select(TermStudent)
        .join(Student, TermStudent.student_id == Student.id)
        .where(TermStudent.term_id == term_id)
        .options(selectinload(TermStudent.student), selectinload(TermStudent.lecturer))
    )
    if lecturer_id is not None:
        stmt = stmt.where(TermStudent.lecturer_id == lecturer_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Student.student_code.ilike(like) | Student.full_name.ilike(like))
    page = paginate(db, stmt.order_by(Student.student_code), params)
    page["items"] = [
        {
            "term_student_id": ts.id,
            "student_id": ts.student_id,
            "student_code": ts.student.student_code,
            "full_name": ts.student.full_name,
            "class_name": ts.student.class_name,
            "lecturer_id": ts.lecturer_id,
            "lecturer_name": ts.lecturer.full_name if ts.lecturer else None,
        }
        for ts in page["items"]
    ]
    return page


def assign_lecturers(
    db: Session, term_id: int, lecturer_id: int | None, student_ids: list[int]
) -> dict:
    """Phân công một giảng viên hướng dẫn cho nhiều sinh viên của đợt (lecturer_id=None: bỏ phân công)."""
    term = get_term(db, term_id)
    _ensure_editable(term)
    if lecturer_id is not None:
        lecturer = db.get(Lecturer, lecturer_id)
        if lecturer is None:
            raise NotFoundError("Không tìm thấy giảng viên")
        if not lecturer.is_active:
            raise BadRequestError("Giảng viên đã ngừng hoạt động")
    wanted = list(dict.fromkeys(student_ids))
    members = {
        ts.student_id: ts
        for ts in db.scalars(
            select(TermStudent).where(
                TermStudent.term_id == term_id, TermStudent.student_id.in_(wanted)
            )
        )
    }
    for term_student in members.values():
        term_student.lecturer_id = lecturer_id
    db.commit()
    return {"updated": len(members), "not_in_term_ids": [i for i in wanted if i not in members]}


# ---------------------------------------------------------------- Tin thuộc đợt
def list_term_jobs(db: Session, user: User, term_id: int, params: PageParams) -> dict:
    """Tin tuyển dụng gắn với đợt. Sinh viên chỉ thấy tin đã duyệt; admin thấy tất cả."""
    _ensure_can_view(db, user, term_id)
    stmt = select(Job).where(Job.term_id == term_id).options(selectinload(Job.company))
    if user.role != UserRole.ADMIN:
        stmt = stmt.where(Job.status == JobStatus.APPROVED, Job.deadline >= utcnow().date())
    page = paginate(db, stmt.order_by(Job.id.desc()), params)
    page["items"] = [
        {
            "id": j.id,
            "title": j.title,
            "position": j.position,
            "company_id": j.company_id,
            "company_name": j.company.name,
            "quantity": j.quantity,
            "deadline": j.deadline,
            "status": j.status,
        }
        for j in page["items"]
    ]
    return page


# ---------------------------------------------------------------- Kết quả thực tập
def _result_rows(db: Session, results: list[InternshipResult]) -> list[dict]:
    company_ids = {r.company_id for r in results if r.company_id}
    companies = {}
    if company_ids:
        companies = {
            c.id: c.name for c in db.scalars(select(Company).where(Company.id.in_(company_ids)))
        }
    rows = []
    for r in results:
        ts = r.term_student
        rows.append(
            {
                "id": r.id,
                "term_id": ts.term_id,
                "term_student_id": ts.id,
                "student_id": ts.student_id,
                "student_code": ts.student.student_code,
                "student_name": ts.student.full_name,
                "lecturer_id": ts.lecturer_id,
                "lecturer_name": ts.lecturer.full_name if ts.lecturer else None,
                "company_id": r.company_id,
                "company_name": companies.get(r.company_id),
                "application_id": r.application_id,
                "company_evaluation": r.company_evaluation,
                "company_score": r.company_score,
                "evaluated_at": r.evaluated_at,
                "lecturer_comment": r.lecturer_comment,
                "lecturer_score": r.lecturer_score,
                "result": r.result,
                "confirmed_by": r.confirmed_by,
                "confirmed_at": r.confirmed_at,
            }
        )
    return rows


def _get_result(db: Session, result_id: int) -> InternshipResult:
    result = db.get(InternshipResult, result_id)
    if result is None:
        raise NotFoundError("Không tìm thấy kết quả thực tập")
    return result


def list_results(
    db: Session,
    term_id: int,
    params: PageParams,
    *,
    result_status: InternshipResultStatus | None = None,
    lecturer_id: int | None = None,
) -> dict:
    get_term(db, term_id)
    stmt = (
        select(InternshipResult)
        .join(TermStudent, InternshipResult.term_student_id == TermStudent.id)
        .join(Student, TermStudent.student_id == Student.id)
        .where(TermStudent.term_id == term_id)
        .options(
            selectinload(InternshipResult.term_student).selectinload(TermStudent.student),
            selectinload(InternshipResult.term_student).selectinload(TermStudent.lecturer),
        )
    )
    if result_status is not None:
        stmt = stmt.where(InternshipResult.result == result_status)
    if lecturer_id is not None:
        stmt = stmt.where(TermStudent.lecturer_id == lecturer_id)
    page = paginate(db, stmt.order_by(Student.student_code), params)
    page["items"] = _result_rows(db, page["items"])
    return page


def _ensure_not_confirmed(result: InternshipResult) -> None:
    if result.result != InternshipResultStatus.PENDING:
        raise ConflictError("Kết quả đã được nhà trường xác nhận, không thể thay đổi")


def submit_company_evaluation(
    db: Session, company: Company, result_id: int, data: CompanyEvaluation
) -> dict:
    """Doanh nghiệp gửi đánh giá. Chỉ công ty đã nhận sinh viên (đơn HIRED vào tin của công ty thuộc đợt này) mới được gửi."""
    result = _get_result(db, result_id)
    term_student = result.term_student
    _ensure_not_confirmed(result)

    application_id = db.scalar(
        select(Application.id)
        .join(Job, Application.job_id == Job.id)
        .where(
            Application.student_id == term_student.student_id,
            Application.current_status == ApplicationStatus.HIRED,
            Job.company_id == company.id,
            Job.term_id == term_student.term_id,
        )
        .order_by(Application.id)
    )
    if application_id is None:
        raise ForbiddenError("Chỉ doanh nghiệp nơi sinh viên thực tập mới được gửi đánh giá")
    if result.company_id not in (None, company.id):
        raise ConflictError("Sinh viên đã được doanh nghiệp khác đánh giá")
    if term_student.term.status not in (TermStatus.ONGOING, TermStatus.CLOSED):
        raise BadRequestError("Chỉ được đánh giá khi đợt thực tập đang diễn ra hoặc đã kết thúc")

    result.company_id = company.id
    result.application_id = application_id
    result.company_evaluation = data.evaluation
    result.company_score = data.score
    result.evaluated_at = utcnow()

    student = term_student.student
    admins = db.scalars(
        select(User).where(User.role == UserRole.ADMIN, User.status == UserStatus.ACTIVE)
    ).all()
    for admin in admins:
        notification_service.create_notification(
            db,
            user_id=admin.id,
            type="INTERNSHIP_EVALUATION",
            title="Doanh nghiệp đã gửi đánh giá thực tập",
            content=f"{company.name} đã đánh giá sinh viên {student.full_name} ({student.student_code}).",
            ref_type="INTERNSHIP_RESULT",
            ref_id=result.id,
            commit=False,
        )
    db.commit()
    return _result_rows(db, [result])[0]


def lecturer_review(db: Session, result_id: int, data: LecturerReview) -> dict:
    """Giảng viên/admin nhập nhận xét và điểm (giảng viên chưa có tài khoản nên admin nhập thay)."""
    result = _get_result(db, result_id)
    _ensure_not_confirmed(result)
    changes = data.model_dump(exclude_unset=True)
    if "comment" in changes:
        result.lecturer_comment = changes["comment"]
    if "score" in changes:
        result.lecturer_score = changes["score"]
    db.commit()
    return _result_rows(db, [result])[0]


def confirm_result(db: Session, admin: User, result_id: int, outcome: str) -> dict:
    """Admin xác nhận PASSED/FAILED. Sau khi xác nhận, đánh giá và nhận xét bị khóa."""
    result = _get_result(db, result_id)
    _ensure_not_confirmed(result)
    result.result = InternshipResultStatus(outcome)
    result.confirmed_by = admin.id
    result.confirmed_at = utcnow()
    student = result.term_student.student
    label = "ĐẠT" if result.result == InternshipResultStatus.PASSED else "KHÔNG ĐẠT"
    notification_service.create_notification(
        db,
        user_id=student.user_id,
        type="INTERNSHIP_RESULT",
        title="Nhà trường đã xác nhận kết quả thực tập",
        content=f"Kết quả thực tập của bạn: {label}.",
        ref_type="INTERNSHIP_RESULT",
        ref_id=result.id,
        commit=False,
    )
    db.commit()
    return _result_rows(db, [result])[0]
