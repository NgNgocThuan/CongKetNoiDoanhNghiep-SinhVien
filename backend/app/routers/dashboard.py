"""Dashboard thống kê nhà trường. Người phụ trách: TV5.

Endpoints cần làm:
  - GET /admin/dashboard/overview — tổng sinh viên, doanh nghiệp, tin; số ứng tuyển, phỏng vấn, trúng tuyển
  - GET /admin/dashboard/breakdown — thống kê theo ngành, khoa, khóa, đợt thực tập (tham số group_by)
  - GET /admin/dashboard/top-skills — top kỹ năng doanh nghiệp yêu cầu
  - GET /admin/dashboard/skill-gap — kỹ năng doanh nghiệp yêu cầu nhưng sinh viên còn thiếu
  - GET /admin/dashboard/match-rate — tỷ lệ sinh viên đáp ứng yêu cầu tuyển dụng theo ngành / mức độ phù hợp trung bình
  - GET /admin/dashboard/trends — xu hướng nhu cầu nhân lực, kỹ năng theo thời gian
  - GET /admin/dashboard/flow-comparison — so sánh kết quả hai luồng: tự do và thực tập theo đợt

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin/dashboard", tags=["Admin - Dashboard"])

# TODO(TV5): triển khai các endpoint ở docstring trên.
