"""Persist OTP lifecycle and attempts; only configured transports may send."""

import secrets

from sqlalchemy import select

from app.core.config import settings
from app.core.enums import UserStatus
from app.core.exceptions import AppException, BadRequestError, ConflictError, ForbiddenError
from app.core.freelancer_enums import OtpStatus, VerificationChannel, VerificationPurpose
from app.models import EmailLog, User, UserVerification
from app.services.freelancer_commands import run_command
from app.tasks.email_tasks import _deliver

from . import otp_policy
from .identity_service import locked, now_utc


def verification_status(db, *, user_id):
    """Own contact state and resumable challenge metadata; never return an OTP/hash."""
    user = db.get(User, user_id)
    if user is None or user.status not in (UserStatus.ACTIVE, UserStatus.PENDING_APPROVAL):
        raise ForbiddenError("Account cannot access onboarding")
    from .time_utils import ensure_utc

    now = now_utc()
    contacts = {}
    for channel, target_value, verified_at in (
        (VerificationChannel.EMAIL, user.email, user.email_verified_at),
    ):
        row = db.scalar(
            select(UserVerification)
            .where(
                UserVerification.user_id == user_id,
                UserVerification.channel == channel,
                UserVerification.purpose == VerificationPurpose.VERIFY_CONTACT,
            )
            .order_by(UserVerification.id.desc())
            .limit(1)
        )
        challenge = None
        if row and row.target == target_value and not verified_at:
            challenge = {
                "challenge_id": str(row.id),
                "status": row.status,
                "expires_at": ensure_utc(row.expires_at).isoformat(),
                "resend_after": ensure_utc(row.resend_after).isoformat(),
                "attempts_left": max(0, row.max_attempts - row.attempts),
            }
        contacts[channel.value] = {
            "identifier": target_value,
            "verified": verified_at is not None,
            "verified_at": ensure_utc(verified_at).isoformat() if verified_at else None,
            "challenge": challenge,
        }
    return {"server_time": ensure_utc(now).isoformat(), "contacts": contacts}


def secret():
    value = settings.FREELANCER_OTP_SECRET
    if len(value) < 32:
        raise AppException("OTP secret is not configured", code="OTP_NOT_READY", status_code=503)
    return value.encode()


def target(user, payload):
    email_only(payload.channel)
    if user is None or user.status not in (UserStatus.ACTIVE, UserStatus.PENDING_APPROVAL):
        raise ForbiddenError("Account cannot access onboarding")
    if payload.purpose != VerificationPurpose.VERIFY_CONTACT:
        raise BadRequestError("Contact changes require a separate verified change flow")
    actual = user.email
    identifier = payload.identifier.lower()
    if not actual or identifier != actual:
        raise ForbiddenError("OTP must target the account's current contact")
    return actual


def email_only(channel):
    if channel != VerificationChannel.EMAIL:
        raise BadRequestError("Only email verification is supported")


def deliver_code(channel, destination, code):
    email_only(channel)
    if not settings.SMTP_HOST:
        raise AppException(
            "OTP delivery is not configured for this channel", code="OTP_NOT_READY", status_code=503
        )
    _deliver(
        destination,
        "[Student Connect] Mã xác minh email",
        f"<p>Mã xác minh email của bạn: <b>{code}</b>.</p>"
        f"<p>Mã có hiệu lực trong {int(otp_policy.OtpConfig().ttl.total_seconds() // 60)} phút. "
        "Không chia sẻ mã với bất kỳ ai.</p>",
    )


def request_otp(db, *, user_id, payload, ip_key="unknown"):
    email_only(payload.channel)
    key = secret()
    config = otp_policy.OtpConfig()
    # Fail before creating a challenge when there is no actual transport.
    if not settings.SMTP_HOST:
        raise AppException(
            "OTP delivery is not configured for this channel", code="OTP_NOT_READY", status_code=503
        )

    def operation():
        user = locked(db, User, id=user_id)
        destination = target(user, payload)
        now = now_utc()
        from app.services.freelancer_rate_limit import consume_in_tx

        consume_in_tx(
            db,
            scopes=[(f"otp:ip:{ip_key}", 20, 3600), (f"otp:target:{destination}", 5, 3600)],
            at=now,
        )
        # User-wide history prevents bypassing limits by switching target/channel.
        history = db.scalars(
            select(UserVerification)
            .where(
                UserVerification.user_id == user_id,
                UserVerification.channel == VerificationChannel.EMAIL,
                UserVerification.created_at > now - config.send_window,
            )
            .order_by(UserVerification.created_at)
        ).all()
        decision = otp_policy.check_send_allowed(config, now, [v.created_at for v in history])
        if not decision.allowed:
            raise AppException(
                "OTP send limit reached", code=decision.outcome.value, status_code=429
            )
        for old in db.scalars(
            select(UserVerification)
            .where(
                UserVerification.user_id == user_id,
                UserVerification.channel == payload.channel,
                UserVerification.purpose == payload.purpose,
                UserVerification.status == OtpStatus.PENDING,
            )
            .with_for_update()
        ).all():
            old.status = OtpStatus.SUPERSEDED
        nonce = secrets.token_hex(12)
        subject = f"user:{user_id}:{destination}:{nonce}"
        code, challenge = otp_policy.issue_challenge(
            config, key, payload.purpose.value, subject, now
        )
        record = UserVerification(
            user_id=user_id,
            channel=payload.channel,
            purpose=payload.purpose,
            target=destination,
            otp_hash=challenge.code_hash,
            key_version=nonce,
            max_attempts=config.max_attempts,
            expires_at=challenge.expires_at,
            resend_after=now + config.resend_cooldown,
            created_at=now,
        )
        db.add(record)
        db.flush()
        return record.id, destination, code

    record_id, destination, code = run_command(db, operation)
    # Transport runs AFTER commit; never persist raw OTP in logs, outbox or response.
    try:
        deliver_code(payload.channel, destination, code)
    except Exception:

        def invalidate():
            locked(db, User, id=user_id)
            record = locked(db, UserVerification, id=record_id)
            if record.status == OtpStatus.PENDING:
                record.status = OtpStatus.SUPERSEDED
            db.add(EmailLog(user_id=user_id, recipient_email=destination,
                            type="EMAIL_OTP", subject="[Student Connect] Mã xác minh email",
                            status="FAILED", error_message="OTP_DELIVERY_FAILED", retry_count=1,
                            ref_type="USER_VERIFICATION", ref_id=record_id))

        run_command(db, invalidate)
        raise AppException(
            "OTP delivery failed", code="OTP_DELIVERY_FAILED", status_code=503
        ) from None
    db.add(EmailLog(user_id=user_id, recipient_email=destination,
                    type="EMAIL_OTP", subject="[Student Connect] Mã xác minh email",
                    status="SENT", sent_at=now_utc(),
                    ref_type="USER_VERIFICATION", ref_id=record_id))
    db.commit()
    state = verification_status(db, user_id=user_id)
    challenge = state["contacts"][payload.channel.value]["challenge"]
    return {
        "status": "sent",
        "challenge_id": str(record_id),
        "server_time": state["server_time"],
        **(
            {k: challenge[k] for k in ("expires_at", "resend_after", "attempts_left")}
            if challenge
            else {}
        ),
    }


def verify_otp(db, *, user_id, payload, verification_id=None):
    email_only(payload.channel)
    key = secret()

    def operation():
        user = locked(db, User, id=user_id)
        destination = target(user, payload)
        record = db.scalars(
            select(UserVerification)
            .where(
                UserVerification.user_id == user_id,
                UserVerification.channel == payload.channel,
                UserVerification.purpose == payload.purpose,
            )
            .order_by(UserVerification.id.desc())
            .with_for_update()
        ).first()
        if (
            record is None
            or (verification_id is not None and record.id != verification_id)
            or record.target != destination
            or record.status != OtpStatus.PENDING
        ):
            return False
        now = now_utc()
        config = otp_policy.OtpConfig(max_attempts=record.max_attempts)
        challenge = otp_policy.OtpChallenge(
            code_hash=record.otp_hash,
            issued_at=record.created_at,
            expires_at=record.expires_at,
            attempts=record.attempts,
        )
        result = otp_policy.verify_challenge(
            config,
            key,
            payload.purpose.value,
            f"user:{user_id}:{destination}:{record.key_version}",
            challenge,
            payload.code,
            now,
        )
        record.attempts = result.challenge.attempts
        if result.ok:
            record.status = OtpStatus.VERIFIED
            record.verified_at = now
            user.email_verified_at = now
        elif result.outcome == otp_policy.VerifyOutcome.EXPIRED:
            record.status = OtpStatus.EXPIRED
        elif result.outcome == otp_policy.VerifyOutcome.TOO_MANY_ATTEMPTS:
            record.status = OtpStatus.LOCKED
        return result.ok

    # Commit failed attempts BEFORE returning an error (do not roll them back).
    if not run_command(db, operation):
        raise ConflictError("OTP is invalid, expired or already used", code="OTP_INVALID")
    return {"status": "success", "verified": True}
