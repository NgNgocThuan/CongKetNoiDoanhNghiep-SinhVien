"""Lời mời ứng tuyển. Người phụ trách: TV4.

Endpoints cần làm:
  - POST /invitations — doanh nghiệp mời sinh viên (job_id, student_id, message). Chỉ mời sinh viên is_open_to_work; unique (job, student); thông báo + email
  - GET /invitations/company — lời mời đã gửi; GET /invitations/me — lời mời tôi nhận
  - POST /invitations/{id}/decline — sinh viên từ chối (chấp nhận = nộp đơn qua POST /applications với invitation_id)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/invitations", tags=["Invitations"])

# TODO(TV4): triển khai các endpoint ở docstring trên.
