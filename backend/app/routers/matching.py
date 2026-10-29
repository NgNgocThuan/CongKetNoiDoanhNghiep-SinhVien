"""AI Job Matching. Người phụ trách: TV5.

Endpoints cần làm:
  - GET /matching/jobs/recommended — sinh viên: gợi ý việc làm xếp hạng theo score; kèm matched_skills, missing_skills, explanation; chỉ tin APPROVED, còn hạn, đạt điều kiện bắt buộc
  - GET /matching/jobs/{job_id}/score — điểm phù hợp của tôi với một tin cụ thể
  - GET /matching/jobs/{job_id}/candidates — doanh nghiệp: gợi ý ứng viên cho tin của mình; CHỈ sinh viên is_open_to_work; ẨN GPA/liên hệ/thành tích nếu show_* = false
  - POST /matching/recompute — admin: tính lại hàng loạt (nền)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/matching", tags=["AI Matching"])

# TODO(TV5): triển khai các endpoint ở docstring trên.
