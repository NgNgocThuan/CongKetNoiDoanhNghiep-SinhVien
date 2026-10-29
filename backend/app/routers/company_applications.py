"""Quản lý ứng viên (Kanban). Người phụ trách: TV4.

Endpoints cần làm:
  - GET /company/applications — danh sách đơn theo job_id; lọc ngành, GPA, kỹ năng, kinh nghiệm; có thể gom nhóm theo trạng thái cho Kanban
  - GET /company/applications/{id} — hồ sơ sinh viên + CV snapshot (chỉ đơn thuộc tin của công ty mình)
  - PUT /company/applications/{id}/status — kéo thả đổi trạng thái; kiểm tra chuyển trạng thái hợp lệ (APPLIED→SCREENING→SHORTLISTED→INTERVIEW→OFFER→HIRED, REJECTED từ bất kỳ bước nào); ghi log; gửi thông báo + email cho sinh viên. Body có `note` (tùy chọn): khi chuyển INTERVIEW/OFFER, doanh nghiệp nhập nội dung (thời gian, địa điểm/link...) -> lưu vào status log và gửi email cho sinh viên. KHÔNG có bảng lịch phỏng vấn
  - GET /company/applications/{id}/history — lịch sử xử lý

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/company/applications", tags=["Company - Applications"])

# TODO(TV4): triển khai các endpoint ở docstring trên.
