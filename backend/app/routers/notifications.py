"""Thông báo trong ứng dụng. Người phụ trách: TV1.

Endpoints cần làm:
  - GET /notifications — thông báo của tôi (lọc is_read), phân trang
  - GET /notifications/unread-count — số chưa đọc
  - POST /notifications/{id}/read — đánh dấu đã đọc (chỉ của chính mình)
  - POST /notifications/read-all — đánh dấu tất cả đã đọc

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# TODO(TV1): triển khai các endpoint ở docstring trên.
