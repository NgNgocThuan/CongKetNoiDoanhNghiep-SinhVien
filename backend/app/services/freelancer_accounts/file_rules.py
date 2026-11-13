"""A5 - Quy tắc file thuần: kiểm tra upload, checksum, cổng tải xuống theo kết quả quét.

Không ghi đĩa, không gọi bộ quét. Service lưu file qua storage adapter, rồi
dùng các hàm này. Nếu chưa có bộ quét thật, trạng thái giữ PENDING và file KHÔNG
được tải xuống; tuyệt đối không tự đánh dấu CLEAN.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

MAGIC_PDF = b"%PDF-"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_ZIP = b"PK\x03\x04"  # docx/xlsx là zip


class FileRejected(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FileTypeRule:
    extension: str  # chữ thường, không dấu chấm
    mime_types: frozenset[str]
    magic_prefixes: tuple[bytes, ...]


@dataclass(frozen=True)
class FilePolicy:
    name: str
    max_bytes: int
    rules: tuple[FileTypeRule, ...]

    def rule_for_extension(self, ext: str) -> FileTypeRule | None:
        for rule in self.rules:
            if rule.extension == ext:
                return rule
        return None


_PDF = FileTypeRule("pdf", frozenset({"application/pdf"}), (MAGIC_PDF,))
_PNG = FileTypeRule("png", frozenset({"image/png"}), (MAGIC_PNG,))
_JPG = FileTypeRule("jpg", frozenset({"image/jpeg"}), (MAGIC_JPEG,))
_JPEG = FileTypeRule("jpeg", frozenset({"image/jpeg"}), (MAGIC_JPEG,))

# Giá trị mẫu, chỉnh theo đặc tả. 10 MiB cho hồ sơ/MOU.
DOCUMENT_POLICY = FilePolicy("document", 10 * 1024 * 1024, (_PDF, _PNG, _JPG, _JPEG))


@dataclass(frozen=True)
class ValidatedFile:
    safe_name: str
    extension: str
    mime_type: str
    size: int


_NAME_MAX = 120
_UNSAFE = re.compile(r"[^\w.\-]+", re.UNICODE)


def sanitize_filename(raw: str) -> str:
    """Bỏ đường dẫn, ký tự điều khiển, ký tự nguy hiểm; giữ phần mở rộng."""
    if not raw or not raw.strip():
        raise FileRejected("FILE_NAME_INVALID", "Tên file trống.")
    name = unicodedata.normalize("NFC", raw).replace("\\", "/").split("/")[-1]
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C")
    name = _UNSAFE.sub("_", name.strip()).strip("._")
    if not name:
        raise FileRejected("FILE_NAME_INVALID", "Tên file không hợp lệ.")
    if len(name) > _NAME_MAX:
        stem, dot, ext = name.rpartition(".")
        if dot and len(ext) <= 10:
            name = stem[: _NAME_MAX - len(ext) - 1] + "." + ext
        else:
            name = name[:_NAME_MAX]
    return name


def validate_upload(
    policy: FilePolicy,
    *,
    filename: str,
    declared_mime: str | None,
    head: bytes,
    size: int,
) -> ValidatedFile:
    """Kiểm tra phần đầu file (đủ ~16 byte) + kích thước đã biết. Ném FileRejected."""
    if size <= 0:
        raise FileRejected("FILE_EMPTY", "File rỗng.")
    if size > policy.max_bytes:
        raise FileRejected("FILE_TOO_LARGE", "File vượt quá dung lượng cho phép.")

    safe_name = sanitize_filename(filename)
    # Chỉ xét phần mở rộng cuối; file kiểu 'a.php.pdf' vẫn bị kiểm tra magic bytes.
    ext = safe_name.rpartition(".")[2].lower() if "." in safe_name else ""
    rule = policy.rule_for_extension(ext)
    if rule is None:
        raise FileRejected("FILE_TYPE_NOT_ALLOWED", "Định dạng file không được phép.")

    if not any(head.startswith(prefix) for prefix in rule.magic_prefixes):
        raise FileRejected("FILE_CONTENT_MISMATCH", "Nội dung file không khớp phần mở rộng.")

    mime = (declared_mime or "").split(";")[0].strip().lower()
    if mime and mime != "application/octet-stream" and mime not in rule.mime_types:
        raise FileRejected("FILE_MIME_MISMATCH", "MIME khai báo không khớp định dạng file.")

    return ValidatedFile(safe_name, ext, sorted(rule.mime_types)[0], size)


def sha256_of_chunks(chunks: Iterable[bytes]) -> tuple[str, int]:
    """Băm streaming. Trả (hex digest, tổng số byte)."""
    digest = hashlib.sha256()
    total = 0
    for chunk in chunks:
        digest.update(chunk)
        total += len(chunk)
    return digest.hexdigest(), total


def checksum_matches(expected_hex: str, actual_hex: str) -> bool:
    return hmac.compare_digest(expected_hex.lower(), actual_hex.lower())


class ScanStatus(str, Enum):
    PENDING = "PENDING"  # chưa quét hoặc chưa có bộ quét
    CLEAN = "CLEAN"
    QUARANTINED = "QUARANTINED"  # phát hiện mối đe dọa
    ERROR = "ERROR"  # lỗi quét, coi như chưa an toàn


def can_download(scan_status: ScanStatus | str) -> bool:
    """Chỉ file CLEAN mới được tải. Giá trị lạ -> không cho tải."""
    try:
        return ScanStatus(scan_status) is ScanStatus.CLEAN
    except ValueError:
        return False
