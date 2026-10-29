"""Hồ sơ sinh viên (phía sinh viên). Người phụ trách: TV3.

Endpoints cần làm:
  - GET /students/me — hồ sơ đầy đủ, TÁCH RÕ 2 nhóm: official (từ trường, chỉ đọc) và self_declared (tự khai)
  - PUT /students/me/profile — cập nhật giới thiệu, định hướng, liên hệ, quyền riêng tư (is_open_to_work, show_*)
  - GET/POST/PUT/DELETE /students/me/skills — kỹ năng (source=SELF; level)
  - GET/POST/PUT/DELETE /students/me/experiences — kinh nghiệm làm việc/thực tập
  - GET/POST/PUT/DELETE /students/me/projects — dự án cá nhân
  - GET/POST/PUT/DELETE /students/me/certificates — chứng chỉ tự khai (source=SELF, is_verified=False); KHÔNG sửa/xóa được chứng chỉ SCHOOL
  - GET /students/me/achievements — nghiên cứu khoa học, thành tích do trường xác nhận (chỉ đọc)
  - GET /students/me/internship — đợt thực tập và giảng viên hướng dẫn (nếu có)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/students", tags=["Students"])

# TODO(TV3): triển khai các endpoint ở docstring trên.
