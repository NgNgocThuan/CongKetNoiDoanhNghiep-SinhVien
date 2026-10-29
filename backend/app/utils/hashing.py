"""Hash nội dung, dùng làm khóa cache cho kết quả AI (cv.content_hash, job.content_hash...)."""
import hashlib
import json
from typing import Any


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    """Hash ổn định của dict/list (sắp xếp key)."""
    return sha256_text(json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str))
