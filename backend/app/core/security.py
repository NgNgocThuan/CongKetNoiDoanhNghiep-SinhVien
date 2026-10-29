"""Băm mật khẩu, JWT, token đặt lại mật khẩu."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

# ---- Lưu trữ thu hồi token (in-memory) ----
_revoked_token_hashes: set[str] = set()


def revoke_token(raw_token: str) -> None:
    """Đánh dấu thu hồi token vào bộ nhớ."""
    _revoked_token_hashes.add(hash_token(raw_token))


def is_token_revoked(raw_token: str) -> bool:
    """Kiểm tra token đã bị thu hồi chưa."""
    return hash_token(raw_token) in _revoked_token_hashes


def clear_revoked_tokens() -> None:
    """Xóa toàn bộ danh sách token đã bị thu hồi (phục vụ test)."""
    _revoked_token_hashes.clear()


# ---- Mật khẩu ----
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---- JWT ----
def _create_token(user_id: int, token_type: str, expires_delta: timedelta, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": token_type, "iat": now, "exp": now + expires_delta, "jti": secrets.token_hex(12)}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), {"role": role}
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Phiên đăng nhập đã hết hạn", code="TOKEN_EXPIRED") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token không hợp lệ", code="TOKEN_INVALID") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("Loại token không đúng", code="TOKEN_INVALID")
    if is_token_revoked(token):
        raise UnauthorizedError("Phiên đăng nhập đã bị thu hồi", code="TOKEN_REVOKED")
    return payload


# ---- Token đặt lại mật khẩu: gửi `raw` qua email, chỉ lưu `hash` vào DB ----
def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_reset_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)
