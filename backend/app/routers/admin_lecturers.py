"""Nhà trường: quản lý giảng viên. Người phụ trách: TV2.

Endpoints cần làm:
  - GET /admin/lecturers — danh sách, lọc faculty/q
  - POST /admin/lecturers — tạo
  - GET/PUT /admin/lecturers/{id} — xem/cập nhật
  - DELETE /admin/lecturers/{id} — ngừng hoạt động (is_active=False)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin/lecturers", tags=["Admin - Lecturers"])

# TODO(TV2): triển khai các endpoint ở docstring trên.
