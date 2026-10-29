"""Nhà trường: quản lý dữ liệu sinh viên. Người phụ trách: TV2.

Endpoints cần làm:
  - GET /admin/students — danh sách, lọc faculty/major/cohort/q
  - GET /admin/students/{id} — chi tiết (dữ liệu trường + hồ sơ tự khai, phân biệt rõ nguồn)
  - PUT /admin/students/{id} — cập nhật dữ liệu học thuật (GPA, lớp, ngành, khóa...)
  - POST /admin/students/import — upload Excel/CSV (utils.spreadsheet): tạo/cập nhật Student + User(PENDING_ACTIVATION), ghi ImportBatch + error_report từng dòng
  - GET /admin/students/imports — lịch sử import; GET /admin/students/imports/{id} — chi tiết + dòng lỗi
  - POST /admin/students/{id}/issue-account — cấp/gửi lại email kích hoạt tài khoản (sinh token, dùng email_service)
  - POST /admin/students/{id}/achievements — thêm nghiên cứu khoa học/thành tích; DELETE .../achievements/{aid}
  - POST /admin/students/certificates/{cert_id}/verify — xác thực chứng chỉ tự khai (is_verified, verified_by/at)
  - POST /admin/students/sync — (tùy chọn) đồng bộ từ hệ thống đào tạo; để stub nếu chưa có nguồn

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin/students", tags=["Admin - Students"])

# TODO(TV2): triển khai các endpoint ở docstring trên.
