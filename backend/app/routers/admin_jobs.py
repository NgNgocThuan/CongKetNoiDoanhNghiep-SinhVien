"""Nhà trường: kiểm duyệt tin tuyển dụng. Người phụ trách: TV1.

Endpoints cần làm:
  - GET /admin/jobs — danh sách, lọc status (mặc định PENDING_APPROVAL), company, term
  - GET /admin/jobs/{id} — chi tiết tin
  - POST /admin/jobs/{id}/approve — duyệt: status=APPROVED, ghi approved_by/at, thông báo + email cho doanh nghiệp, kích hoạt ai.job_parser.parse_job (nền)
  - POST /admin/jobs/{id}/reject — từ chối, bắt buộc reject_reason, thông báo + email
  - POST /admin/jobs/{id}/close — đóng tin vi phạm

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin/jobs", tags=["Admin - Jobs"])

# TODO(TV1): triển khai các endpoint ở docstring trên.
