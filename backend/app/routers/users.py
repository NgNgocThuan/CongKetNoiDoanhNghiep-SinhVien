"""Quản lý tài khoản (admin). Người phụ trách: TV1.

Endpoints cần làm:
  - GET /admin/users — danh sách, lọc role/status/q, phân trang
  - GET /admin/users/{id} — chi tiết
  - POST /admin/users/{id}/lock — khóa tài khoản (bắt buộc lý do -> locked_reason), gửi thông báo
  - POST /admin/users/{id}/unlock — mở khóa
  - POST /admin/users/admins — tạo tài khoản quản trị mới (User ADMIN + Admin profile)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

# TODO(TV1): triển khai các endpoint ở docstring trên.
