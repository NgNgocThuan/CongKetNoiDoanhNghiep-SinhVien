"""Xác thực & phiên đăng nhập. Người phụ trách: TV1.

Endpoints cần làm:
  - POST /auth/token — OAuth2 form (username=email, password) cho nút Authorize của Swagger
  - POST /auth/login — đăng nhập JSON (LoginRequest) -> TokenPair; chặn user LOCKED / chưa kích hoạt; cập nhật last_login_at
  - POST /auth/refresh — đổi refresh token lấy cặp token mới
  - POST /auth/logout — đăng xuất (phía server có thể bỏ qua nếu dùng JWT thuần; nếu cần thì thêm blacklist)
  - GET /auth/me — thông tin user hiện tại + hồ sơ theo role (student/company/admin)
  - POST /auth/change-password — đổi mật khẩu (kiểm tra mật khẩu cũ)
  - POST /auth/forgot-password — luôn trả 200 dù email không tồn tại; tạo PasswordResetToken (core.security.generate_reset_token), gửi email
  - POST /auth/reset-password — đặt lại mật khẩu bằng token (kiểm tra hết hạn / đã dùng)
  - POST /auth/activate — sinh viên kích hoạt tài khoản do trường cấp/import: token + mật khẩu mới -> status ACTIVE
  - POST /auth/register-company — tạo User(COMPANY, PENDING_APPROVAL) + Company(PENDING); doanh nghiệp chờ trường duyệt

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

# TODO(TV1): triển khai các endpoint ở docstring trên.
