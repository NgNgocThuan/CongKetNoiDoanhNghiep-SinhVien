"""Nghiệp vụ: Tin tuyển dụng. Người phụ trách: TV4.

Hàm cần viết:
  - search_jobs (xây câu truy vấn có điều kiện, tránh N+1 bằng selectinload), get_job_detail, record_view
  - create_job, update_job, submit_for_approval, close_job, get_job_stats
  - expire_overdue_jobs() — chuyển tin quá hạn sang EXPIRED (gọi bằng job định kỳ)

Quy ước (xem catalog_service.py): nhận db: Session đầu tiên; lỗi nghiệp vụ -> raise các exception ở
app/core/exceptions.py; service tự commit; không import app.routers.
"""
