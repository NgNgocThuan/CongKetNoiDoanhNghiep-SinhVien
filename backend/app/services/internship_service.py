"""Nghiệp vụ: Thực tập theo đợt & kết quả thực tập. Người phụ trách: TV2.

Hàm cần viết:
  - CRUD đợt + chuyển trạng thái hợp lệ
  - add_students / import_term_students / remove_student / assign_lecturers
  - submit_company_evaluation (kiểm tra công ty đúng là nơi sinh viên thực tập), confirm_result
  - is_student_in_term(db, student_id, term_id) — TV3 (ứng tuyển) và TV5 (matching) sẽ gọi hàm này

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
