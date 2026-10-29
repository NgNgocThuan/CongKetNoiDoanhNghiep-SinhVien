"""Nghiệp vụ: Xác thực & phiên đăng nhập. Người phụ trách: TV1.

Hàm cần viết:
  - login, refresh_tokens, get_me, change_password
  - request_password_reset, reset_password
  - activate_student_account, register_company

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
