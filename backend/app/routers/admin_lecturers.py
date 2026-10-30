"""Nhà trường: quản lý giảng viên. Người phụ trách: TV2.

Endpoints (chỉ admin):
  - GET /admin/lecturers — danh sách, lọc faculty/q
  - POST /admin/lecturers — tạo
  - GET/PUT /admin/lecturers/{id} — xem/cập nhật
  - DELETE /admin/lecturers/{id} — ngừng hoạt động (is_active=False)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter, Response

from app.dependencies import AdminUser, DbSession, Pagination
from app.schemas.admin_lecturers import LecturerCreate, LecturerRead, LecturerUpdate
from app.schemas.common import Page
from app.services import lecturer_service

router = APIRouter(prefix="/admin/lecturers", tags=["Admin - Lecturers"])


@router.get("", response_model=Page[LecturerRead], summary="Danh sách giảng viên")
def list_lecturers(
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    q: str | None = None,
    faculty_id: int | None = None,
    include_inactive: bool = False,
):
    return lecturer_service.list_lecturers(
        db, pagination, q=q, faculty_id=faculty_id, include_inactive=include_inactive
    )


@router.post("", response_model=LecturerRead, status_code=201, summary="Tạo giảng viên")
def create_lecturer(data: LecturerCreate, db: DbSession, _: AdminUser):
    return lecturer_service.create_lecturer(db, data)


@router.get("/{lecturer_id}", response_model=LecturerRead, summary="Chi tiết giảng viên")
def get_lecturer(lecturer_id: int, db: DbSession, _: AdminUser):
    return lecturer_service.get_lecturer(db, lecturer_id)


@router.put("/{lecturer_id}", response_model=LecturerRead, summary="Cập nhật giảng viên")
def update_lecturer(lecturer_id: int, data: LecturerUpdate, db: DbSession, _: AdminUser):
    return lecturer_service.update_lecturer(db, lecturer_id, data)


@router.delete("/{lecturer_id}", status_code=204, summary="Ngừng hoạt động giảng viên")
def deactivate_lecturer(lecturer_id: int, db: DbSession, _: AdminUser):
    lecturer_service.deactivate_lecturer(db, lecturer_id)
    return Response(status_code=204)
