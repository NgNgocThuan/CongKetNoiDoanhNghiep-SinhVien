"""Hồ sơ doanh nghiệp. Người phụ trách: TV4.

Endpoints cần làm:
  - GET /companies/me — hồ sơ + trạng thái xác thực (verification_status, reject_reason)
  - PUT /companies/me — cập nhật lĩnh vực, quy mô, địa chỉ, website, công nghệ, phúc lợi, logo
  - POST /companies/me/documents — upload giấy tờ xác thực (utils.file_storage, DOCUMENT_EXTENSIONS); DELETE /me/documents/{id}
  - GET /companies/{id} — hồ sơ công khai cho sinh viên (chỉ công ty đã APPROVED)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/companies", tags=["Companies"])

# TODO(TV4): triển khai các endpoint ở docstring trên.
