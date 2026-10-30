"""Nghiệp vụ: Nhà trường: quản lý giảng viên. Người phụ trách: TV2.

CRUD giảng viên; "xóa" là ngừng hoạt động (is_active=False) vì giảng viên còn gắn với đợt thực tập.

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Lecturer
from app.schemas.admin_lecturers import LecturerCreate, LecturerUpdate
from app.schemas.common import PageParams
from app.services import catalog_service
from app.utils.pagination import paginate


def list_lecturers(
    db: Session,
    params: PageParams,
    *,
    q: str | None = None,
    faculty_id: int | None = None,
    include_inactive: bool = False,
) -> dict:
    stmt = select(Lecturer)
    if not include_inactive:
        stmt = stmt.where(Lecturer.is_active.is_(True))
    if faculty_id is not None:
        stmt = stmt.where(Lecturer.faculty_id == faculty_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Lecturer.full_name.ilike(like), Lecturer.code.ilike(like), Lecturer.email.ilike(like)))
    return paginate(db, stmt.order_by(Lecturer.full_name), params)


def get_lecturer(db: Session, lecturer_id: int) -> Lecturer:
    lecturer = db.get(Lecturer, lecturer_id)
    if lecturer is None:
        raise NotFoundError("Không tìm thấy giảng viên")
    return lecturer


def _ensure_unique_code(db: Session, code: str | None, exclude_id: int | None = None) -> None:
    if not code:
        return
    stmt = select(Lecturer).where(Lecturer.code == code)
    if exclude_id is not None:
        stmt = stmt.where(Lecturer.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise ConflictError("Mã giảng viên đã tồn tại")


def create_lecturer(db: Session, data: LecturerCreate) -> Lecturer:
    catalog_service.get_faculty(db, data.faculty_id)
    _ensure_unique_code(db, data.code)
    lecturer = Lecturer(**data.model_dump())
    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)
    return lecturer


def update_lecturer(db: Session, lecturer_id: int, data: LecturerUpdate) -> Lecturer:
    lecturer = get_lecturer(db, lecturer_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("faculty_id") is not None:
        catalog_service.get_faculty(db, changes["faculty_id"])
    _ensure_unique_code(db, changes.get("code"), exclude_id=lecturer.id)
    for field, value in changes.items():
        setattr(lecturer, field, value)
    db.commit()
    db.refresh(lecturer)
    return lecturer


def deactivate_lecturer(db: Session, lecturer_id: int) -> None:
    lecturer = get_lecturer(db, lecturer_id)
    lecturer.is_active = False
    db.commit()
