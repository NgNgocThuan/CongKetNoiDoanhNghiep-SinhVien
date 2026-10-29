"""Xuất báo cáo Excel/PDF. Người phụ trách: TV5.

Endpoints cần làm:
  - GET /admin/exports/students.xlsx — danh sách sinh viên (lọc khoa/ngành/khóa/đợt)
  - GET /admin/exports/companies.xlsx; GET /admin/exports/jobs.xlsx; GET /admin/exports/applications.xlsx
  - GET /admin/exports/skill-report.xlsx — kỹ năng được yêu cầu, kỹ năng còn thiếu, cung - cầu nhân lực
  - GET /admin/exports/dashboard.pdf — thống kê tổng quan + biểu đồ

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin/exports", tags=["Admin - Exports"])

# TODO(TV5): triển khai các endpoint ở docstring trên.
