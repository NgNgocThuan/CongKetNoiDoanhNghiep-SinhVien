"""Danh mục dùng chung (khoa, ngành, lĩnh vực, loại hình công việc, kỹ năng).

Người phụ trách: TV2.   *** ĐÂY LÀ MODULE MẪU: các module khác làm theo khuôn này. ***

Khuôn mẫu một router:
  1. Chỉ khai báo endpoint, khai báo quyền bằng dependency (CurrentUser / AdminUser ...).
  2. Không truy vấn DB, không viết nghiệp vụ trong router: gọi hàm trong app/services/.
  3. response_model luôn là schema (Pydantic), không trả thẳng model SQLAlchemy.
  4. Danh sách trả về Page[Schema] qua Pagination + utils.pagination.paginate (làm trong service).

TODO(TV2): làm tương tự cho
  /catalog/majors, /catalog/industries, /catalog/job-types,
  /catalog/skills (+ GET /catalog/skills/search?q=...), /catalog/skills/{id}/aliases
Đọc: mọi user đăng nhập.  Ghi: AdminUser.
"""
from fastapi import APIRouter, Response

from app.core.enums import UserRole
from app.dependencies import AdminUser, CurrentUser, DbSession, Pagination
from app.schemas.catalog import FacultyCreate, FacultyRead, FacultyUpdate
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
