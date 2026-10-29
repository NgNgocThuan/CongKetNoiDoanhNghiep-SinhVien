"""Tác vụ nền gửi email. Chạy trong FastAPI BackgroundTasks nên tự mở session riêng hoặc dùng session test."""
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import EmailStatus
from app.models import EmailLog
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


def _deliver(to_email: str, subject: str, body_html: str) -> None:
    if not settings.SMTP_HOST:
        if settings.is_development:
            logger.info("[DEV EMAIL] to=%s subject=%s", to_email, subject)
            return
        raise RuntimeError("SMTP chưa được cấu hình")

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content("Vui lòng xem email ở định dạng HTML.")
    msg.add_alternative(body_html, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


def send_email_task(email_log_id: int, body_html: str, db_session: Optional[Session] = None) -> None:
    session_to_close: Optional[Session] = None

    try:
        # ƯU TIÊN KIỂM TRA db_session trước để tránh timeout TCP tới MariaDB trong test
        if db_session is not None:
            session_to_close = Session(bind=db_session.get_bind(), autoflush=False, expire_on_commit=False)
            db = session_to_close
        else:
            session_to_close = SessionLocal()
            db = session_to_close

        log = db.get(EmailLog, email_log_id)
        if log is None:
            return

        try:
            _deliver(log.recipient_email, log.subject, body_html)
            log.status = EmailStatus.SENT
            log.sent_at = utcnow()
            log.error_message = None
        except Exception as exc:  # noqa: BLE001 - mọi lỗi gửi đều chỉ ghi nhận vào log
            log.status = EmailStatus.FAILED
            log.error_message = str(exc)[:500]
            log.retry_count = (log.retry_count or 0) + 1
            logger.exception("Gửi email thất bại (email_log_id=%s)", email_log_id)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi trong tác vụ gửi email nền (email_log_id=%s): %s", email_log_id, exc)
    finally:
        if session_to_close is not None:
            session_to_close.close()
