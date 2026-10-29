"""Lưu file upload (CV, giấy tờ doanh nghiệp) vào thư mục UPLOAD_DIR."""
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestError

CV_EXTENSIONS = {".pdf", ".docx"}
DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
IMPORT_EXTENSIONS = {".xlsx", ".csv"}


def save_upload(file: UploadFile, subdir: str, allowed_extensions: set[str]) -> str:
    """Kiểm tra đuôi file + dung lượng, lưu với tên ngẫu nhiên, trả về đường dẫn tương đối.

    Ví dụ: save_upload(file, "cvs/12", CV_EXTENSIONS) -> "cvs/12/3f9a....pdf"
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_extensions:
        raise BadRequestError(f"Định dạng không được hỗ trợ. Chấp nhận: {', '.join(sorted(allowed_extensions))}")

    data = file.file.read()
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise BadRequestError(f"File vượt quá {settings.MAX_UPLOAD_MB}MB")

    target_dir = Path(settings.UPLOAD_DIR) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (target_dir / name).write_bytes(data)
    return f"{subdir}/{name}"


def absolute_path(relative_path: str) -> Path:
    return Path(settings.UPLOAD_DIR) / relative_path