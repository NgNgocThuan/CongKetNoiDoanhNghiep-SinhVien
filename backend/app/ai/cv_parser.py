"""Phân tích CV bằng NLP. Người phụ trách: TV5.  Người gọi: cv_service (TV3).

HỢP ĐỒNG GIỮA CÁC MODULE (đừng đổi chữ ký nếu chưa báo nhóm):
"""
from sqlalchemy.orm import Session

from app.models import CV


def parse_cv(db: Session, cv: CV) -> dict:
    """Trích xuất kỹ năng, kinh nghiệm, dự án, lĩnh vực từ CV, trả về `parsed_json` đã chuẩn hóa.

    TODO(TV5):
      1. Lấy văn bản: CV UPLOADED -> đọc PDF/DOCX từ utils.file_storage; ONLINE -> từ content_json.
         Lưu vào cv.extracted_text.
      2. Tính cv.content_hash (utils.hashing). Nếu trùng hash cũ và đã có parsed_json -> trả luôn, KHÔNG gọi API.
      3. Gọi LLM (ai.client) với prompt ở ai/prompts.py, bắt buộc đầu ra JSON.
      4. Chuẩn hóa tên kỹ năng bằng catalog_service.normalize_skill_names (TV2).
      5. Lưu cv.parsed_json, cv.parsed_at; (tùy chọn) đồng bộ student_skills(source=CV_AI).
    """
    raise NotImplementedError
