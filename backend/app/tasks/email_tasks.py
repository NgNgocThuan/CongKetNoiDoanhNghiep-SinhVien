"""SMTP transport and durable delivery shared by BackgroundTasks and the worker."""
import logging
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import EmailStatus
from app.models import EmailLog
from app.services.email_payload import decrypt_body
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


def _deliver(to_email: str, subject: str, body_html: str) -> None:
    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_NOT_CONFIGURED")
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = " ".join(subject.split())[:255]
    msg.set_content("Vui lòng xem email ở định dạng HTML.")
    msg.add_alternative(body_html, subtype="html")
    context = ssl.create_default_context()
    transport = smtplib.SMTP_SSL if settings.SMTP_SSL else smtplib.SMTP
    kwargs = {"context": context} if settings.SMTP_SSL else {}
    with transport(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15, **kwargs) as smtp:
        if not settings.SMTP_SSL:
            smtp.starttls(context=context)
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        refused = smtp.send_message(msg)
        if refused:
            raise RuntimeError("SMTP_RECIPIENT_REFUSED")


def send_email_task(email_log_id: int, body_html=None, db_session=None) -> bool:
    # A bind outlives the request-scoped Session. Retain the argument for callers.
    bind = db_session.get_bind() if isinstance(db_session, Session) else db_session
    db = Session(bind=bind, expire_on_commit=False) if bind is not None else SessionLocal()
    try:
        # Serialize background/worker deliveries of the same log on MariaDB.
        log = db.scalar(select(EmailLog).where(EmailLog.id == email_log_id).with_for_update())
        if log is None:
            return False
        if log.status == EmailStatus.SENT:
            return True
        if log.retry_count >= MAX_RETRIES:
            return False
        at = utcnow()
        if log.next_attempt_at and log.next_attempt_at > at:
            return False
        try:
            if log.expires_at and log.expires_at <= at:
                log.body_encrypted = None
                raise RuntimeError("EMAIL_EXPIRED")
            if not log.body_encrypted:
                raise RuntimeError("EMAIL_CONTENT_UNAVAILABLE")
            original = decrypt_body(log.body_encrypted)
            _deliver(log.recipient_email, log.subject, original)
            log.status = EmailStatus.SENT
            log.sent_at = utcnow()
            log.error_message = None
            log.next_attempt_at = None
            if log.type in ("PASSWORD_RESET", "ACCOUNT_ACTIVATION"):
                log.body_encrypted = None
            success = True
        except Exception as exc:
            log.status = EmailStatus.FAILED
            log.sent_at = None
            safe_codes = {"SMTP_NOT_CONFIGURED", "SMTP_RECIPIENT_REFUSED", "EMAIL_EXPIRED", "EMAIL_CONTENT_UNAVAILABLE"}
            log.error_message = str(exc) if str(exc) in safe_codes else type(exc).__name__
            log.retry_count = (log.retry_count or 0) + 1
            log.next_attempt_at = utcnow() + timedelta(minutes=2 ** log.retry_count)
            logger.warning("Email delivery failed: id=%s code=%s", log.id, log.error_message)
            success = False
        db.commit()
        return success
    except Exception:
        db.rollback()
        logger.error("Email delivery database error: id=%s", email_log_id)
        return False
    finally:
        db.close()


def process_pending_emails(db: Session, *, limit=20) -> int:
    """Recover interrupted BackgroundTasks and retry transient failures."""
    at = utcnow()
    ids = db.scalars(select(EmailLog.id).where(
        EmailLog.status.in_((EmailStatus.PENDING, EmailStatus.FAILED)),
        EmailLog.body_encrypted.is_not(None),
        EmailLog.retry_count < MAX_RETRIES,
        or_(EmailLog.next_attempt_at.is_(None), EmailLog.next_attempt_at <= at),
    ).order_by(EmailLog.id).limit(limit)).all()
    bind = db.get_bind()
    db.rollback()
    for ident in ids:
        send_email_task(ident, db_session=bind)
    return len(ids)
