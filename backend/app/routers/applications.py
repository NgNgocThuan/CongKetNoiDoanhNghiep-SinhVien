"""Ứng tuyển & theo dõi đơn (phía sinh viên). Người phụ trách: TV3.

Endpoints cần làm:
  - POST /applications — nộp đơn (job_id, cv_id, cover_letter?, invitation_id?). QUY TẮC: tin APPROVED + còn hạn; CV thuộc sinh viên; tin thuộc đợt -> sinh viên phải nằm trong term_students (internship_service.is_student_in_term); không ứng tuyển trùng (409); sao chép CV vào cv_snapshot_url; ghi application_status_logs (old_status=None); gửi email xác nhận + thông báo cho doanh nghiệp; nếu có invitation_id -> chuyển lời mời sang ACCEPTED
  - GET /applications/me — đơn của tôi, lọc status, phân trang
  - GET /applications/{id} — chi tiết + lịch sử trạng thái (chỉ chủ đơn)
  - POST /applications/{id}/withdraw — rút đơn (chỉ khi chưa OFFER/HIRED/REJECTED)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/applications", tags=["Applications"])

# TODO(TV3): triển khai các endpoint ở docstring trên.
