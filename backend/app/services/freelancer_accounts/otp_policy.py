"""A1 - Chính sách OTP: chống spam, hết hạn, giới hạn số lần thử.

Module thuần: không DB, không gửi email/SMS. Service gọi các hàm này, lưu
OtpChallenge vào bảng của nó và gửi mã sau commit/qua outbox.

Nguyên tắc:
- Mã chỉ lưu dưới dạng HMAC-SHA256 gắn với (purpose, subject); không lưu mã thô.
- So sánh bằng hmac.compare_digest để tránh lộ thông tin qua thời gian.
- Quá số lần thử thì khóa challenge, kể cả khi sau đó nhập đúng mã.
- Challenge đã dùng thì không dùng lại được.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Sequence

from .time_utils import ensure_utc


@dataclass(frozen=True)
class OtpConfig:
    length: int = 6
    ttl: timedelta = timedelta(minutes=5)
    max_attempts: int = 5
    resend_cooldown: timedelta = timedelta(seconds=60)
    max_sends_per_window: int = 5
    send_window: timedelta = timedelta(hours=1)

    def __post_init__(self) -> None:
        if not 4 <= self.length <= 10:
            raise ValueError("length phải trong khoảng 4..10")
        if self.max_attempts < 1 or self.max_sends_per_window < 1:
            raise ValueError("max_attempts và max_sends_per_window phải >= 1")
        if self.ttl <= timedelta(0) or self.send_window <= timedelta(0):
            raise ValueError("ttl và send_window phải dương")


@dataclass(frozen=True)
class OtpChallenge:
    code_hash: str
    issued_at: datetime
    expires_at: datetime
    attempts: int = 0
    consumed_at: datetime | None = None


class SendOutcome(str, Enum):
    ALLOWED = "ALLOWED"
    COOLDOWN = "COOLDOWN"
    RATE_LIMITED = "RATE_LIMITED"


@dataclass(frozen=True)
class SendDecision:
    outcome: SendOutcome
    retry_after_seconds: int = 0

    @property
    def allowed(self) -> bool:
        return self.outcome is SendOutcome.ALLOWED


class VerifyOutcome(str, Enum):
    OK = "OK"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"
    ALREADY_USED = "ALREADY_USED"


@dataclass(frozen=True)
class VerifyResult:
    outcome: VerifyOutcome
    challenge: OtpChallenge  # trạng thái mới cần lưu lại (attempts/consumed_at)
    attempts_left: int = 0

    @property
    def ok(self) -> bool:
        return self.outcome is VerifyOutcome.OK


def generate_code(length: int = 6) -> str:
    """Sinh mã số ngẫu nhiên an toàn mật mã, giữ số 0 đứng đầu."""
    upper = 10**length
    return str(secrets.randbelow(upper)).zfill(length)


def hash_code(secret: bytes, purpose: str, subject: str, code: str) -> str:
    """HMAC-SHA256(secret, purpose|subject|code). subject vd: 'user:12' hoặc email."""
    if not secret:
        raise ValueError("secret không được rỗng")
    message = f"{purpose}\x1f{subject}\x1f{code}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def check_send_allowed(
    config: OtpConfig, now_utc: datetime, previous_sends: Sequence[datetime]
) -> SendDecision:
    """Quyết định có được gửi OTP mới không, dựa trên lịch sử gửi của cùng subject+purpose."""
    now = ensure_utc(now_utc)
    sends = sorted(ensure_utc(s) for s in previous_sends)
    if not sends:
        return SendDecision(SendOutcome.ALLOWED)

    last_allowed_at = sends[-1] + config.resend_cooldown
    if now < last_allowed_at:
        return SendDecision(SendOutcome.COOLDOWN, _ceil_seconds(last_allowed_at - now))

    in_window = [s for s in sends if s > now - config.send_window]
    if len(in_window) >= config.max_sends_per_window:
        # Được gửi lại khi lần gửi cũ nhất trong cửa sổ trượt ra ngoài cửa sổ.
        oldest_needed = in_window[len(in_window) - config.max_sends_per_window]
        free_at = oldest_needed + config.send_window
        return SendDecision(SendOutcome.RATE_LIMITED, _ceil_seconds(free_at - now))

    return SendDecision(SendOutcome.ALLOWED)


def issue_challenge(
    config: OtpConfig,
    secret: bytes,
    purpose: str,
    subject: str,
    now_utc: datetime,
) -> tuple[str, OtpChallenge]:
    """Tạo mã mới. Trả (mã thô để gửi đi, challenge để lưu). Không log mã thô."""
    now = ensure_utc(now_utc)
    code = generate_code(config.length)
    challenge = OtpChallenge(
        code_hash=hash_code(secret, purpose, subject, code),
        issued_at=now,
        expires_at=now + config.ttl,
    )
    return code, challenge


def verify_challenge(
    config: OtpConfig,
    secret: bytes,
    purpose: str,
    subject: str,
    challenge: OtpChallenge,
    submitted: str,
    now_utc: datetime,
) -> VerifyResult:
    now = ensure_utc(now_utc)

    if challenge.consumed_at is not None:
        return VerifyResult(VerifyOutcome.ALREADY_USED, challenge)

    if now >= ensure_utc(challenge.expires_at):
        return VerifyResult(VerifyOutcome.EXPIRED, challenge)

    if challenge.attempts >= config.max_attempts:
        return VerifyResult(VerifyOutcome.TOO_MANY_ATTEMPTS, challenge)

    candidate = (submitted or "").strip()
    format_ok = candidate.isascii() and candidate.isdigit() and len(candidate) == config.length
    # Luôn tính hash (kể cả sai định dạng) để thời gian xử lý không phân biệt trường hợp.
    expected = hash_code(secret, purpose, subject, candidate if format_ok else "")
    matches = hmac.compare_digest(expected, challenge.code_hash) and format_ok

    if matches:
        updated = replace(challenge, consumed_at=now)
        return VerifyResult(VerifyOutcome.OK, updated, config.max_attempts - challenge.attempts)

    updated = replace(challenge, attempts=challenge.attempts + 1)
    left = max(config.max_attempts - updated.attempts, 0)
    outcome = VerifyOutcome.INVALID if left > 0 else VerifyOutcome.TOO_MANY_ATTEMPTS
    return VerifyResult(outcome, updated, left)


def _ceil_seconds(delta: timedelta) -> int:
    total = delta.total_seconds()
    whole = int(total)
    return whole if whole == total else whole + 1
