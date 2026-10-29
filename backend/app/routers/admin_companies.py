"""Nhà trường: kiểm duyệt doanh nghiệp. Người phụ trách: TV1.

Endpoints cần làm:
  - GET /admin/companies — danh sách, lọc verification_status/q
  - GET /admin/companies/{id} — chi tiết kèm giấy tờ xác thực (documents)
  - POST /admin/companies/{id}/approve — duyệt: verification_status=APPROVED, user.status=ACTIVE, ghi verified_by/at, gửi thông báo + email
  - POST /admin/companies/{id}/reject — từ chối, bắt buộc reject_reason, gửi thông báo + email

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin/companies", tags=["Admin - Companies"])

# TODO(TV1): triển khai các endpoint ở docstring trên.
