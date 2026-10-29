"""Báo cáo vi phạm. Người phụ trách: TV1.

Endpoints cần làm:
  - POST /reports — user gửi báo cáo vi phạm về JOB/COMPANY/STUDENT (target_type, target_id, reason)
  - GET /reports — admin: danh sách, lọc status/target_type
  - GET /reports/{id} — admin: chi tiết
  - POST /reports/{id}/handle — admin xử lý: RESOLVED/REJECTED + resolution_note (có thể kèm khóa tài khoản/đóng tin)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["Reports"])

# TODO(TV1): triển khai các endpoint ở docstring trên.
