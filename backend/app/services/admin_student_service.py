"""Nghiệp vụ: Nhà trường: quản lý dữ liệu sinh viên. Người phụ trách: TV2.

Hàm cần viết:
  - list_students, get_student_detail, update_academic_data
  - import_students (upsert theo student_code, báo cáo lỗi từng dòng, KHÔNG dừng cả file vì 1 dòng lỗi)
  - issue_account, add_achievement, verify_certificate

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
