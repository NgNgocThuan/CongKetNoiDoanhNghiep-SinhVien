"""Băm mật khẩu, JWT, token đặt lại mật khẩu."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

import bcrypt
import jwt
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.utils.datetime_utils import utcnow

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# ---- Lưu trữ thu hồi token (L1 cache + L2 Database dùng chung giữa các worker) ----
_revoked_token_hashes: set[str] = set()


def revoke_token(raw_token: str, db: Optional["Session"] = None) -> None:
    """Đánh dấu thu hồi token vào DB dùng chung (có thời hạn theo exp) kèm L1 cache."""
    token_hash = hash_token(raw_token)
    _revoked_token_hashes.add(token_hash)

    if db is None:
        return

    try:
        payload = jwt.decode(
            raw_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        user_id = int(payload["sub"])
        exp_val = payload.get("exp")
        if isinstance(exp_val, (int, float)):
            expires_at = datetime.fromtimestamp(exp_val, tz=timezone.utc).replace(tzinfo=None)
        else:
            expires_at = utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    except Exception:  # noqa: BLE001
        return

    from app.models.user import PasswordResetToken

    now = utcnow()
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at < now))
    existing = db.scalar(
        select(PasswordResetToken.id).where(PasswordResetToken.token_hash == token_hash)
    )
    if existing is None:
        db.add(
            PasswordResetToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                used_at=now,
            )
        )
        db.commit()


def is_token_revoked(raw_token: str, db: Optional["Session"] = None) -> bool:
    """Kiểm tra token đã bị thu hồi chưa (tra L1 cache và L2 Database dùng chung)."""
    token_hash = hash_token(raw_token)
    if token_hash in _revoked_token_hashes:
        return True

    if db is not None:
        from app.models.user import PasswordResetToken

        revoked_id = db.scalar(
            select(PasswordResetToken.id)
            .where(PasswordResetToken.token_hash == token_hash)
            .where(PasswordResetToken.used_at.is_not(None))
            .where(PasswordResetToken.expires_at >= utcnow())
        )
        if revoked_id is not None:
            _revoked_token_hashes.add(token_hash)
            return True

    return False


def clear_revoked_tokens() -> None:
    """Xóa bộ nhớ đệm token đã bị thu hồi (phục vụ test)."""
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


def decode_token(token: str, expected_type: str = "access", db: Optional["Session"] = None) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Phiên đăng nhập đã hết hạn", code="TOKEN_EXPIRED") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token không hợp lệ", code="TOKEN_INVALID") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("Loại token không đúng", code="TOKEN_INVALID")
    if is_token_revoked(token, db=db):
        raise UnauthorizedError("Phiên đăng nhập đã bị thu hồi", code="TOKEN_REVOKED")
    return payload


# ---- Token đặt lại mật khẩu: gửi `raw` qua email, chỉ lưu `hash` vào DB ----
def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_reset_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)
