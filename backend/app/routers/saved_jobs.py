"""Việc làm yêu thích. Người phụ trách: TV3.

Endpoints cần làm:
  - GET /saved-jobs — danh sách tin đã lưu (kèm thông tin tin), phân trang
  - POST /saved-jobs/{job_id} — lưu (idempotent)
  - DELETE /saved-jobs/{job_id} — bỏ lưu

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])

# TODO(TV3): triển khai các endpoint ở docstring trên.
