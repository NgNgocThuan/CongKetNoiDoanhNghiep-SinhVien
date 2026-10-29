"""Phân tích tin tuyển dụng bằng NLP. Người phụ trách: TV5.  Người gọi: job_service / admin_job_service (TV4, TV2)."""
from sqlalchemy.orm import Session

from app.models import Job


def parse_job(db: Session, job: Job) -> dict:
    """Trích xuất vị trí, ngành nghề, kỹ năng bắt buộc/ưu tiên, kinh nghiệm, trình độ -> `job.parsed_json`.

    TODO(TV5): giống cv_parser.parse_job: hash nội dung (title + description + requirements),
    bỏ qua nếu không đổi, chuẩn hóa kỹ năng, lưu job.parsed_json / parsed_at / content_hash.
    """
    raise NotImplementedError
