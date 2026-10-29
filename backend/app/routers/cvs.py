"""Quản lý CV. Người phụ trách: TV3.

Endpoints cần làm:
  - GET /cvs/me — danh sách CV của tôi (bỏ CV đã xóa mềm)
  - POST /cvs/upload — upload PDF/DOCX (utils.file_storage.save_upload, CV_EXTENSIONS)
  - POST /cvs/online — tạo CV trực tuyến, TỰ ĐỘNG điền dữ liệu học thuật từ trường + cho bổ sung kỹ năng/dự án/kinh nghiệm
  - PUT /cvs/{id} — sửa tiêu đề/nội dung CV online
  - DELETE /cvs/{id} — xóa mềm (deleted_at); CV đã dùng ứng tuyển vẫn phải truy cập được
  - POST /cvs/{id}/set-default — đặt CV mặc định (đảm bảo mỗi sinh viên chỉ có 1 CV mặc định)
  - GET /cvs/{id}/download — tải file (chủ CV hoặc doanh nghiệp có đơn ứng tuyển dùng CV này)
  - POST /cvs/{id}/analyze — gọi ai.cv_parser.parse_cv (TV5) để phân tích CV; trả parsed_json

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/cvs", tags=["CVs"])

# TODO(TV3): triển khai các endpoint ở docstring trên.
