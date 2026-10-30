"""Nghiệp vụ danh mục. Người phụ trách: TV2.   *** MODULE MẪU cho tầng service. ***

Quy ước service:
  * Hàm nhận `db: Session` làm tham số đầu, trả về model hoặc dict phân trang.
  * Mọi lỗi nghiệp vụ -> raise NotFoundError / ConflictError / BadRequestError... (core/exceptions.py).
  * Service tự commit khi ghi dữ liệu; router không gọi db.commit().
  * Không import từ app.routers; không phụ thuộc Request/Response của FastAPI.

Gồm: Faculty, Major, Industry, JobType, Skill, SkillAlias (CRUD + xóa mềm bằng is_active) và
normalize_skill_names (TV5 gọi để chuẩn hóa kỹ năng do LLM trả về).
"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Faculty, Industry, JobType, Major, Skill, SkillAlias
from app.schemas.catalog import (
    FacultyCreate,
    FacultyUpdate,
    IndustryCreate,
    IndustryUpdate,
    JobTypeCreate,
    JobTypeUpdate,
    MajorCreate,
    MajorUpdate,
    SkillAliasCreate,
    SkillCreate,
    SkillUpdate,
)
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


# ---------------------------------------------------------------- Majors
def list_majors(
    db: Session,
    params: PageParams,
    *,
    q: str | None = None,
    faculty_id: int | None = None,
    include_inactive: bool = False,
) -> dict:
    stmt = select(Major)
    if not include_inactive:
        stmt = stmt.where(Major.is_active.is_(True))
    if faculty_id is not None:
        stmt = stmt.where(Major.faculty_id == faculty_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Major.name.ilike(like), Major.code.ilike(like)))
    return paginate(db, stmt.order_by(Major.name), params)


def get_major(db: Session, major_id: int) -> Major:
    major = db.get(Major, major_id)
    if major is None:
        raise NotFoundError("Không tìm thấy ngành")
    return major


def _ensure_unique_major_code(db: Session, code: str | None, exclude_id: int | None = None) -> None:
    if not code:
        return
    stmt = select(Major).where(Major.code == code)
    if exclude_id is not None:
        stmt = stmt.where(Major.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise ConflictError("Mã ngành đã tồn tại")


def create_major(db: Session, data: MajorCreate) -> Major:
    get_faculty(db, data.faculty_id)
    _ensure_unique_major_code(db, data.code)
    major = Major(faculty_id=data.faculty_id, code=data.code, name=data.name)
    db.add(major)
    db.commit()
    db.refresh(major)
    return major


def update_major(db: Session, major_id: int, data: MajorUpdate) -> Major:
    major = get_major(db, major_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("faculty_id") is not None:
        get_faculty(db, changes["faculty_id"])
    _ensure_unique_major_code(db, changes.get("code"), exclude_id=major.id)
    for field, value in changes.items():
        setattr(major, field, value)
    db.commit()
    db.refresh(major)
    return major


def deactivate_major(db: Session, major_id: int) -> None:
    major = get_major(db, major_id)
    major.is_active = False
    db.commit()


# ---------------------------------------------------------------- Industries
def list_industries(
    db: Session, params: PageParams, *, q: str | None = None, include_inactive: bool = False
) -> dict:
    stmt = select(Industry)
    if not include_inactive:
        stmt = stmt.where(Industry.is_active.is_(True))
    if q:
        stmt = stmt.where(Industry.name.ilike(f"%{q.strip()}%"))
    return paginate(db, stmt.order_by(Industry.name), params)


def get_industry(db: Session, industry_id: int) -> Industry:
    industry = db.get(Industry, industry_id)
    if industry is None:
        raise NotFoundError("Không tìm thấy lĩnh vực")
    return industry


def _ensure_unique_industry_name(db: Session, name: str | None, exclude_id: int | None = None) -> None:
    if not name:
        return
    stmt = select(Industry).where(Industry.name == name)
    if exclude_id is not None:
        stmt = stmt.where(Industry.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise ConflictError("Tên lĩnh vực đã tồn tại")


def create_industry(db: Session, data: IndustryCreate) -> Industry:
    _ensure_unique_industry_name(db, data.name)
    industry = Industry(name=data.name)
    db.add(industry)
    db.commit()
    db.refresh(industry)
    return industry


def update_industry(db: Session, industry_id: int, data: IndustryUpdate) -> Industry:
    industry = get_industry(db, industry_id)
    changes = data.model_dump(exclude_unset=True)
    _ensure_unique_industry_name(db, changes.get("name"), exclude_id=industry.id)
    for field, value in changes.items():
        setattr(industry, field, value)
    db.commit()
    db.refresh(industry)
    return industry


def deactivate_industry(db: Session, industry_id: int) -> None:
    industry = get_industry(db, industry_id)
    industry.is_active = False
    db.commit()


# ---------------------------------------------------------------- Job types
def list_job_types(
    db: Session, params: PageParams, *, q: str | None = None, include_inactive: bool = False
) -> dict:
    stmt = select(JobType)
    if not include_inactive:
        stmt = stmt.where(JobType.is_active.is_(True))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(JobType.name.ilike(like), JobType.code.ilike(like)))
    return paginate(db, stmt.order_by(JobType.name), params)


def get_job_type(db: Session, job_type_id: int) -> JobType:
    job_type = db.get(JobType, job_type_id)
    if job_type is None:
        raise NotFoundError("Không tìm thấy loại hình công việc")
    return job_type


def _ensure_unique_job_type_code(db: Session, code: str | None, exclude_id: int | None = None) -> None:
    if not code:
        return
    stmt = select(JobType).where(JobType.code == code)
    if exclude_id is not None:
        stmt = stmt.where(JobType.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise ConflictError("Mã loại hình công việc đã tồn tại")


def create_job_type(db: Session, data: JobTypeCreate) -> JobType:
    _ensure_unique_job_type_code(db, data.code)
    job_type = JobType(code=data.code, name=data.name)
    db.add(job_type)
    db.commit()
    db.refresh(job_type)
    return job_type


def update_job_type(db: Session, job_type_id: int, data: JobTypeUpdate) -> JobType:
    job_type = get_job_type(db, job_type_id)
    changes = data.model_dump(exclude_unset=True)
    _ensure_unique_job_type_code(db, changes.get("code"), exclude_id=job_type.id)
    for field, value in changes.items():
        setattr(job_type, field, value)
    db.commit()
    db.refresh(job_type)
    return job_type


def deactivate_job_type(db: Session, job_type_id: int) -> None:
    job_type = get_job_type(db, job_type_id)
    job_type.is_active = False
    db.commit()


# ---------------------------------------------------------------- Skills
def list_skills(
    db: Session,
    params: PageParams,
    *,
    q: str | None = None,
    category: str | None = None,
    include_inactive: bool = False,
) -> dict:
    stmt = select(Skill)
    if not include_inactive:
        stmt = stmt.where(Skill.is_active.is_(True))
    if category:
        stmt = stmt.where(Skill.category == category)
    if q:
        stmt = stmt.where(Skill.name.ilike(f"%{q.strip()}%"))
    return paginate(db, stmt.order_by(Skill.name), params)


def search_skills(db: Session, q: str, *, limit: int = 10) -> list[Skill]:
    """Gợi ý kỹ năng theo tên hoặc tên gọi khác (alias); dùng cho ô autocomplete."""
    like = f"%{q.strip()}%"
    alias_skill_ids = select(SkillAlias.skill_id).where(SkillAlias.alias.ilike(like))
    stmt = (
        select(Skill)
        .where(Skill.is_active.is_(True), or_(Skill.name.ilike(like), Skill.id.in_(alias_skill_ids)))
        .order_by(Skill.name)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_skill(db: Session, skill_id: int) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise NotFoundError("Không tìm thấy kỹ năng")
    return skill


def _ensure_unique_skill_name(db: Session, name: str | None, exclude_id: int | None = None) -> None:
    """Tên kỹ năng không trùng kỹ năng khác và không trùng một alias (không phân biệt hoa thường)."""
    if not name:
        return
    lowered = name.lower()
    stmt = select(Skill).where(func.lower(Skill.name) == lowered)
    if exclude_id is not None:
        stmt = stmt.where(Skill.id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise ConflictError("Tên kỹ năng đã tồn tại")
    if db.scalars(select(SkillAlias).where(func.lower(SkillAlias.alias) == lowered)).first() is not None:
        raise ConflictError("Tên kỹ năng trùng với một tên gọi khác (alias) đã có")


def create_skill(db: Session, data: SkillCreate) -> Skill:
    _ensure_unique_skill_name(db, data.name)
    skill = Skill(name=data.name, category=data.category)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def update_skill(db: Session, skill_id: int, data: SkillUpdate) -> Skill:
    skill = get_skill(db, skill_id)
    changes = data.model_dump(exclude_unset=True)
    _ensure_unique_skill_name(db, changes.get("name"), exclude_id=skill.id)
    for field, value in changes.items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return skill


def deactivate_skill(db: Session, skill_id: int) -> None:
    skill = get_skill(db, skill_id)
    skill.is_active = False
    db.commit()


# ---------------------------------------------------------------- Skill aliases
def list_skill_aliases(db: Session, skill_id: int) -> list[SkillAlias]:
    skill = get_skill(db, skill_id)
    return sorted(skill.aliases, key=lambda a: a.alias.lower())


def create_skill_alias(db: Session, skill_id: int, data: SkillAliasCreate) -> SkillAlias:
    skill = get_skill(db, skill_id)
    lowered = data.alias.lower()
    if db.scalars(select(SkillAlias).where(func.lower(SkillAlias.alias) == lowered)).first() is not None:
        raise ConflictError("Tên gọi khác (alias) đã tồn tại")
    if db.scalars(select(Skill).where(func.lower(Skill.name) == lowered)).first() is not None:
        raise ConflictError("Alias trùng với tên một kỹ năng đã có")
    alias = SkillAlias(skill_id=skill.id, alias=data.alias)
    db.add(alias)
    db.commit()
    db.refresh(alias)
    return alias


def delete_skill_alias(db: Session, skill_id: int, alias_id: int) -> None:
    alias = db.get(SkillAlias, alias_id)
    if alias is None or alias.skill_id != skill_id:
        raise NotFoundError("Không tìm thấy alias của kỹ năng này")
    db.delete(alias)
    db.commit()


def normalize_skill_names(db: Session, names: list[str]) -> list[Skill]:
    """Chuẩn hóa tên kỹ năng (vd từ LLM) về Skill trong danh mục.

    Tra theo Skill.name rồi SkillAlias.alias, không phân biệt hoa thường, bỏ khoảng trắng thừa.
    Chỉ trả kỹ năng đang hoạt động; tên không có trong danh mục bị bỏ qua; kết quả không trùng,
    giữ thứ tự xuất hiện đầu tiên.
    """
    wanted = {n.strip().lower() for n in names if n and n.strip()}
    if not wanted:
        return []

    by_name = {
        skill.name.lower(): skill
        for skill in db.scalars(select(Skill).where(Skill.is_active.is_(True), func.lower(Skill.name).in_(wanted)))
    }
    by_alias = {
        alias.alias.lower(): alias.skill
        for alias in db.scalars(select(SkillAlias).where(func.lower(SkillAlias.alias).in_(wanted)))
        if alias.skill.is_active
    }

    result: list[Skill] = []
    seen: set[int] = set()
    for name in names:
        key = (name or "").strip().lower()
        skill = by_name.get(key) or by_alias.get(key)
        if skill is not None and skill.id not in seen:
            seen.add(skill.id)
            result.append(skill)
    return result
