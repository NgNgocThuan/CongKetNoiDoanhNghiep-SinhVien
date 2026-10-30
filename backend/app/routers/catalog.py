"""Danh mục dùng chung (khoa, ngành, lĩnh vực, loại hình công việc, kỹ năng).

Người phụ trách: TV2.   *** ĐÂY LÀ MODULE MẪU: các module khác làm theo khuôn này. ***

Khuôn mẫu một router:
  1. Chỉ khai báo endpoint, khai báo quyền bằng dependency (CurrentUser / AdminUser ...).
  2. Không truy vấn DB, không viết nghiệp vụ trong router: gọi hàm trong app/services/.
  3. response_model luôn là schema (Pydantic), không trả thẳng model SQLAlchemy.
  4. Danh sách trả về Page[Schema] qua Pagination + utils.pagination.paginate (làm trong service).

Gồm: /catalog/faculties, majors, industries, job-types, skills (+ /skills/search, /skills/{id}/aliases).
Đọc: mọi user đăng nhập.  Ghi: AdminUser.
"""
from fastapi import APIRouter, Query, Response

from app.core.enums import UserRole
from app.dependencies import AdminUser, CurrentUser, DbSession, Pagination
from app.schemas.catalog import (
    FacultyCreate,
    FacultyRead,
    FacultyUpdate,
    IndustryCreate,
    IndustryRead,
    IndustryUpdate,
    JobTypeCreate,
    JobTypeRead,
    JobTypeUpdate,
    MajorCreate,
    MajorRead,
    MajorUpdate,
    SkillAliasCreate,
    SkillAliasRead,
    SkillCreate,
    SkillRead,
    SkillUpdate,
)
from app.schemas.common import Page
from app.services import catalog_service

router = APIRouter(prefix="/catalog", tags=["Catalog"])


# ---------------------------------------------------------------- Faculties
@router.get("/faculties", response_model=Page[FacultyRead], summary="Danh sách khoa")
def list_faculties(
    db: DbSession,
    user: CurrentUser,
    pagination: Pagination,
    q: str | None = None,
    include_inactive: bool = False,
):
    # Chỉ admin mới được xem cả khoa đã ngừng hoạt động
    include_inactive = include_inactive and user.role == UserRole.ADMIN
    return catalog_service.list_faculties(db, pagination, q=q, include_inactive=include_inactive)


@router.post("/faculties", response_model=FacultyRead, status_code=201, summary="Tạo khoa")
def create_faculty(data: FacultyCreate, db: DbSession, _: AdminUser):
    return catalog_service.create_faculty(db, data)


@router.get("/faculties/{faculty_id}", response_model=FacultyRead, summary="Chi tiết khoa")
def get_faculty(faculty_id: int, db: DbSession, _: CurrentUser):
    return catalog_service.get_faculty(db, faculty_id)


@router.put("/faculties/{faculty_id}", response_model=FacultyRead, summary="Cập nhật khoa")
def update_faculty(faculty_id: int, data: FacultyUpdate, db: DbSession, _: AdminUser):
    return catalog_service.update_faculty(db, faculty_id, data)


@router.delete("/faculties/{faculty_id}", status_code=204, summary="Ngừng hoạt động khoa (xóa mềm)")
def deactivate_faculty(faculty_id: int, db: DbSession, _: AdminUser):
    catalog_service.deactivate_faculty(db, faculty_id)
    return Response(status_code=204)


# ---------------------------------------------------------------- Majors
@router.get("/majors", response_model=Page[MajorRead], summary="Danh sách ngành")
def list_majors(
    db: DbSession,
    user: CurrentUser,
    pagination: Pagination,
    q: str | None = None,
    faculty_id: int | None = None,
    include_inactive: bool = False,
):
    include_inactive = include_inactive and user.role == UserRole.ADMIN
    return catalog_service.list_majors(
        db, pagination, q=q, faculty_id=faculty_id, include_inactive=include_inactive
    )


@router.post("/majors", response_model=MajorRead, status_code=201, summary="Tạo ngành")
def create_major(data: MajorCreate, db: DbSession, _: AdminUser):
    return catalog_service.create_major(db, data)


@router.get("/majors/{major_id}", response_model=MajorRead, summary="Chi tiết ngành")
def get_major(major_id: int, db: DbSession, _: CurrentUser):
    return catalog_service.get_major(db, major_id)


@router.put("/majors/{major_id}", response_model=MajorRead, summary="Cập nhật ngành")
def update_major(major_id: int, data: MajorUpdate, db: DbSession, _: AdminUser):
    return catalog_service.update_major(db, major_id, data)


@router.delete("/majors/{major_id}", status_code=204, summary="Ngừng hoạt động ngành (xóa mềm)")
def deactivate_major(major_id: int, db: DbSession, _: AdminUser):
    catalog_service.deactivate_major(db, major_id)
    return Response(status_code=204)


# ---------------------------------------------------------------- Industries
@router.get("/industries", response_model=Page[IndustryRead], summary="Danh sách lĩnh vực")
def list_industries(
    db: DbSession, user: CurrentUser, pagination: Pagination, q: str | None = None, include_inactive: bool = False
):
    include_inactive = include_inactive and user.role == UserRole.ADMIN
    return catalog_service.list_industries(db, pagination, q=q, include_inactive=include_inactive)


@router.post("/industries", response_model=IndustryRead, status_code=201, summary="Tạo lĩnh vực")
def create_industry(data: IndustryCreate, db: DbSession, _: AdminUser):
    return catalog_service.create_industry(db, data)


@router.get("/industries/{industry_id}", response_model=IndustryRead, summary="Chi tiết lĩnh vực")
def get_industry(industry_id: int, db: DbSession, _: CurrentUser):
    return catalog_service.get_industry(db, industry_id)


@router.put("/industries/{industry_id}", response_model=IndustryRead, summary="Cập nhật lĩnh vực")
def update_industry(industry_id: int, data: IndustryUpdate, db: DbSession, _: AdminUser):
    return catalog_service.update_industry(db, industry_id, data)


@router.delete("/industries/{industry_id}", status_code=204, summary="Ngừng hoạt động lĩnh vực (xóa mềm)")
def deactivate_industry(industry_id: int, db: DbSession, _: AdminUser):
    catalog_service.deactivate_industry(db, industry_id)
    return Response(status_code=204)


# ---------------------------------------------------------------- Job types
@router.get("/job-types", response_model=Page[JobTypeRead], summary="Danh sách loại hình công việc")
def list_job_types(
    db: DbSession, user: CurrentUser, pagination: Pagination, q: str | None = None, include_inactive: bool = False
):
    include_inactive = include_inactive and user.role == UserRole.ADMIN
    return catalog_service.list_job_types(db, pagination, q=q, include_inactive=include_inactive)


@router.post("/job-types", response_model=JobTypeRead, status_code=201, summary="Tạo loại hình công việc")
def create_job_type(data: JobTypeCreate, db: DbSession, _: AdminUser):
    return catalog_service.create_job_type(db, data)


@router.get("/job-types/{job_type_id}", response_model=JobTypeRead, summary="Chi tiết loại hình công việc")
def get_job_type(job_type_id: int, db: DbSession, _: CurrentUser):
    return catalog_service.get_job_type(db, job_type_id)


@router.put("/job-types/{job_type_id}", response_model=JobTypeRead, summary="Cập nhật loại hình công việc")
def update_job_type(job_type_id: int, data: JobTypeUpdate, db: DbSession, _: AdminUser):
    return catalog_service.update_job_type(db, job_type_id, data)


@router.delete("/job-types/{job_type_id}", status_code=204, summary="Ngừng hoạt động loại hình công việc (xóa mềm)")
def deactivate_job_type(job_type_id: int, db: DbSession, _: AdminUser):
    catalog_service.deactivate_job_type(db, job_type_id)
    return Response(status_code=204)


# ---------------------------------------------------------------- Skills
@router.get("/skills", response_model=Page[SkillRead], summary="Danh sách kỹ năng")
def list_skills(
    db: DbSession,
    user: CurrentUser,
    pagination: Pagination,
    q: str | None = None,
    category: str | None = None,
    include_inactive: bool = False,
):
    include_inactive = include_inactive and user.role == UserRole.ADMIN
    return catalog_service.list_skills(db, pagination, q=q, category=category, include_inactive=include_inactive)


# Phải khai báo trước /skills/{skill_id} để "search" không bị hiểu là skill_id
@router.get("/skills/search", response_model=list[SkillRead], summary="Gợi ý kỹ năng theo tên hoặc alias")
def search_skills(db: DbSession, _: CurrentUser, q: str = Query(min_length=1), limit: int = Query(10, ge=1, le=50)):
    return catalog_service.search_skills(db, q, limit=limit)


@router.post("/skills", response_model=SkillRead, status_code=201, summary="Tạo kỹ năng")
def create_skill(data: SkillCreate, db: DbSession, _: AdminUser):
    return catalog_service.create_skill(db, data)


@router.get("/skills/{skill_id}", response_model=SkillRead, summary="Chi tiết kỹ năng")
def get_skill(skill_id: int, db: DbSession, _: CurrentUser):
    return catalog_service.get_skill(db, skill_id)


@router.put("/skills/{skill_id}", response_model=SkillRead, summary="Cập nhật kỹ năng")
def update_skill(skill_id: int, data: SkillUpdate, db: DbSession, _: AdminUser):
    return catalog_service.update_skill(db, skill_id, data)


@router.delete("/skills/{skill_id}", status_code=204, summary="Ngừng hoạt động kỹ năng (xóa mềm)")
def deactivate_skill(skill_id: int, db: DbSession, _: AdminUser):
    catalog_service.deactivate_skill(db, skill_id)
    return Response(status_code=204)


# ---------------------------------------------------------------- Skill aliases
@router.get("/skills/{skill_id}/aliases", response_model=list[SkillAliasRead], summary="Danh sách alias của kỹ năng")
def list_skill_aliases(skill_id: int, db: DbSession, _: CurrentUser):
    return catalog_service.list_skill_aliases(db, skill_id)


@router.post(
    "/skills/{skill_id}/aliases", response_model=SkillAliasRead, status_code=201, summary="Thêm alias cho kỹ năng"
)
def create_skill_alias(skill_id: int, data: SkillAliasCreate, db: DbSession, _: AdminUser):
    return catalog_service.create_skill_alias(db, skill_id, data)


@router.delete("/skills/{skill_id}/aliases/{alias_id}", status_code=204, summary="Xóa alias của kỹ năng")
def delete_skill_alias(skill_id: int, alias_id: int, db: DbSession, _: AdminUser):
    catalog_service.delete_skill_alias(db, skill_id, alias_id)
    return Response(status_code=204)
