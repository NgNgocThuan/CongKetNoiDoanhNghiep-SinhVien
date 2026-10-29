"""Nghiệp vụ: Ứng tuyển & theo dõi đơn (phía sinh viên). Người phụ trách: TV3.

Hàm cần viết:
  - apply, list_my_applications, get_my_application, withdraw
  - log_status_change(db, application, new_status, changed_by, note) — dùng chung với TV4

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
