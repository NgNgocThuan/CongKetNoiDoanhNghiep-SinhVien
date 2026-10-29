"""Nghiệp vụ: Quản lý ứng viên (Kanban). Người phụ trách: TV4.

Hàm cần viết:
  - list_applications, get_application, change_status (dùng application_service.log_status_change), get_history

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
