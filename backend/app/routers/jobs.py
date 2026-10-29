"""Tin tuyển dụng. Người phụ trách: TV4.

Endpoints cần làm:
  - GET /jobs — tìm kiếm cho sinh viên: lọc ngành, kỹ năng, vị trí, địa điểm, mức lương, work_mode, job_type, luồng (free/term). CHỈ trả tin APPROVED + còn hạn; tin thuộc đợt chỉ hiện với sinh viên nằm trong đợt đó
  - GET /jobs/{id} — chi tiết; ghi JobView và tăng view_count
  - GET /jobs/me — tin của doanh nghiệp (mọi trạng thái) kèm số lượt xem/số đơn
  - POST /jobs — tạo tin (DRAFT); chỉ doanh nghiệp đã APPROVED; kèm skills (is_required) + majors
  - PUT /jobs/{id} — sửa (chỉ chủ tin; sửa tin đã APPROVED thì quay lại PENDING_APPROVAL)
  - POST /jobs/{id}/submit — gửi nhà trường kiểm duyệt (DRAFT/REJECTED -> PENDING_APPROVAL)
  - POST /jobs/{id}/close — đóng tin
  - GET /jobs/{id}/stats — thống kê lượt xem theo ngày và số đơn theo trạng thái

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# TODO(TV4): triển khai các endpoint ở docstring trên.
