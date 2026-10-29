"""Business rules for uploaded and online CVs."""
import json
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.ai import cv_parser
from app.core.config import settings
from app.core.enums import CVType, UserRole
from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Application, CV, Job, Student, User
from app.schemas.cvs import CVOnlineCreate, CVUpdate
from app.utils.datetime_utils import utcnow
from app.utils.file_storage import CV_EXTENSIONS, absolute_path, save_upload


def list_my_cvs(db: Session, student: Student) -> list[CV]:
    stmt = (
        select(CV)
        .where(CV.student_id == student.id, CV.deleted_at.is_(None))
        .order_by(CV.is_default.desc(), CV.updated_at.desc(), CV.id.desc())
    )
    return list(db.scalars(stmt).all())


def _has_active_cv(db: Session, student_id: int) -> bool:
    return (
        db.scalar(
            select(CV.id).where(CV.student_id == student_id, CV.deleted_at.is_(None)).limit(1)
        )
        is not None
    )


def upload_cv(db: Session, student: Student, title: str, file: UploadFile) -> CV:
    clean_title = title.strip()
    if not clean_title:
        raise BadRequestError("Tiêu đề CV không được để trống")
    file_url = save_upload(file, f"cvs/{student.id}", CV_EXTENSIONS)
    cv = CV(
        student_id=student.id,
        title=clean_title,
        type=CVType.UPLOADED,
        file_url=file_url,
        is_default=not _has_active_cv(db, student.id),
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


def _official_content(student: Student) -> dict:
    return {
        "student_code": student.student_code,
        "full_name": student.full_name,
        "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
        "class_name": student.class_name,
        "faculty": {"id": student.faculty.id, "name": student.faculty.name},
        "major": {"id": student.major.id, "name": student.major.name},
        "cohort": student.cohort,
        "gpa": float(student.gpa) if student.gpa is not None else None,
        "academic_result": student.academic_result,
    }


def _online_content(student: Student, supplied: dict) -> dict:
    content = dict(supplied)
    # Dữ liệu học thuật luôn lấy lại từ nguồn chính thức, không tin dữ liệu client gửi lên.
    content["official"] = _official_content(student)
    return content


def create_online_cv(db: Session, student: Student, data: CVOnlineCreate) -> CV:
    cv = CV(
        student_id=student.id,
        title=data.title,
        type=CVType.ONLINE,
        content_json=_online_content(student, data.content_json),
        is_default=not _has_active_cv(db, student.id),
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


def _get_owned_cv(
    db: Session, student: Student, cv_id: int, *, active_only: bool = True
) -> CV:
    cv = db.get(CV, cv_id)
    if (
        cv is None
        or cv.student_id != student.id
        or (active_only and cv.deleted_at is not None)
    ):
        raise NotFoundError("Không tìm thấy CV")
    return cv


def update_cv(db: Session, student: Student, cv_id: int, data: CVUpdate) -> CV:
    cv = _get_owned_cv(db, student, cv_id)
    changes = data.model_dump(exclude_unset=True)
    if "content_json" in changes:
        if cv.type != CVType.ONLINE:
            raise BadRequestError("Chỉ CV trực tuyến mới sửa được nội dung")
        cv.content_json = _online_content(student, changes.pop("content_json") or {})
        # Bất kỳ thay đổi nội dung nào cũng làm cache AI cũ mất hiệu lực.
        cv.content_hash = None
        cv.parsed_json = None
        cv.parsed_at = None
    if "title" in changes:
        cv.title = changes["title"]
    db.commit()
    db.refresh(cv)
    return cv


def soft_delete_cv(db: Session, student: Student, cv_id: int) -> None:
    cv = _get_owned_cv(db, student, cv_id)
    was_default = cv.is_default
    cv.deleted_at = utcnow()
    cv.is_default = False
    if was_default:
        replacement = db.scalar(
            select(CV)
            .where(CV.student_id == student.id, CV.id != cv.id, CV.deleted_at.is_(None))
            .order_by(CV.updated_at.desc(), CV.id.desc())
            .limit(1)
        )
        if replacement is not None:
            replacement.is_default = True
    db.commit()


def set_default(db: Session, student: Student, cv_id: int) -> CV:
    cv = _get_owned_cv(db, student, cv_id)
    db.execute(
        update(CV)
        .where(CV.student_id == student.id, CV.id != cv.id)
        .values(is_default=False)
    )
    cv.is_default = True
    db.commit()
    db.refresh(cv)
    return cv


def _company_can_download(db: Session, company_id: int, cv_id: int) -> bool:
    stmt = (
        select(Application.id)
        .join(Job, Job.id == Application.job_id)
        .where(Application.cv_id == cv_id, Job.company_id == company_id)
        .limit(1)
    )
    return db.scalar(stmt) is not None


def _write_online_cv(cv: CV) -> Path:
    relative = Path("cvs") / "online" / str(cv.student_id) / f"cv-{cv.id}.json"
    path = Path(settings.UPLOAD_DIR) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cv.content_json or {}, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def get_downloadable_path(db: Session, cv_id: int, user: User) -> tuple[Path, str, str]:
    cv = db.get(CV, cv_id)
    if cv is None:
        raise NotFoundError("Không tìm thấy CV")

    allowed = False
    if user.role == UserRole.STUDENT and user.student is not None:
        allowed = cv.student_id == user.student.id
    elif user.role == UserRole.COMPANY and user.company is not None:
        allowed = _company_can_download(db, user.company.id, cv.id)
    if not allowed:
        raise NotFoundError("Không tìm thấy CV")

    if cv.type == CVType.UPLOADED:
        if not cv.file_url:
            raise NotFoundError("File CV không còn tồn tại")
        path = absolute_path(cv.file_url)
        media_type = (
            "application/pdf"
            if path.suffix.lower() == ".pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    else:
        path = _write_online_cv(cv)
        media_type = "application/json"
    if not path.is_file():
        raise NotFoundError("File CV không còn tồn tại")
    return path, path.name, media_type


def analyze_cv(db: Session, student: Student, cv_id: int) -> dict:
    cv = _get_owned_cv(db, student, cv_id)
    parsed = cv_parser.parse_cv(db, cv)
    if not isinstance(parsed, dict):
        raise BadRequestError("Kết quả phân tích CV không hợp lệ")
    cv.parsed_json = parsed
    db.commit()
    return {"cv_id": cv.id, "parsed_json": parsed}
