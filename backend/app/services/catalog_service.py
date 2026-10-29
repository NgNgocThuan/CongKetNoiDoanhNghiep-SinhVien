"""Nghiệp vụ danh mục. Người phụ trách: TV2.   *** MODULE MẪU cho tầng service. ***

Quy ước service:
  * Hàm nhận `db: Session` làm tham số đầu, trả về model hoặc dict phân trang.
  * Mọi lỗi nghiệp vụ -> raise NotFoundError / ConflictError / BadRequestError... (core/exceptions.py).
  * Service tự commit khi ghi dữ liệu; router không gọi db.commit().
  * Không import từ app.routers; không phụ thuộc Request/Response của FastAPI.

TODO(TV2):
  - Major, Industry, JobType, Skill, SkillAlias (CRUD + xóa mềm bằng is_active).
  - normalize_skill_names(db, names: list[str]) -> list[Skill]: tra Skill.name và SkillAlias.alias
    (không phân biệt hoa thường) để chuẩn hóa kỹ năng do LLM trả về. TV5 sẽ gọi hàm này.
"""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Faculty
from app.schemas.catalog import FacultyCreate, FacultyUpdate
from app.schemas.common import PageParams
from app.utils.pagination import paginate


# ---------------------------------------------------------------- Faculties
def list_faculties(db: Session, params: PageParams, *, q: str | None = None, include_inactive: bool = False) -> dict:
    stmt = select(Faculty)
    if not include_inactive:
        stmt = stmt.where(Faculty.is_active.is_(True))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Faculty.name.ilike(like), Faculty.code.ilike(like)))
    stmt = stmt.order_by(Faculty.name)
    return paginate(db, stmt, params)


def get_faculty(db: Session, faculty_id: int) -> Faculty:
    faculty = db.get(Faculty, faculty_id)
    if faculty is None:
        raise NotFoundError("Không tìm thấy khoa")
    return faculty


def _ensure_unique(db: Session, *, code: str | None, name: str | None, exclude_id: int | None = None) -> None:
    conditions = []
    if code:
        conditions.append(Faculty.code == code)
    if name:
        conditions.append(Faculty.name == name)
    if not conditions:
        return
    stmt = select(Faculty).where(or_(*conditions))
    if exclude_id is not None:
        stmt = stmt.where(Faculty.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise ConflictError("Mã khoa hoặc tên khoa đã tồn tại")


def create_faculty(db: Session, data: FacultyCreate) -> Faculty:
    _ensure_unique(db, code=data.code, name=data.name)
    faculty = Faculty(code=data.code, name=data.name)
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


def update_faculty(db: Session, faculty_id: int, data: FacultyUpdate) -> Faculty:
    faculty = get_faculty(db, faculty_id)
    changes = data.model_dump(exclude_unset=True)
    _ensure_unique(db, code=changes.get("code"), name=changes.get("name"), exclude_id=faculty.id)
    for field, value in changes.items():
        setattr(faculty, field, value)
    db.commit()
    db.refresh(faculty)
    return faculty


def deactivate_faculty(db: Session, faculty_id: int) -> None:
    faculty = get_faculty(db, faculty_id)
    faculty.is_active = False
    db.commit()
