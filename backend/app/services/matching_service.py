"""Nghiệp vụ: AI Job Matching. Người phụ trách: TV5.

Hàm cần viết:
  - get_or_compute_match(db, student, job) — nếu input_hash không đổi thì dùng lại MatchingResult (KHÔNG gọi API lặp)
  - recommend_jobs_for_student, recommend_candidates_for_job, recompute_all
  - build_input_hash(cv, job, student) — dùng utils.hashing

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
