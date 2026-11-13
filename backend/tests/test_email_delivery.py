"""Email reliability: real transport is always replaced in these tests."""
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import EmailLog
from app.services import email_service
from app.services.email_payload import decrypt_body
from app.tasks import email_tasks
from app.utils.datetime_utils import utcnow


def queued(db, **kwargs):
    return email_service.queue_email(db, None, to_email="recipient@example.test",
                                    subject="Thông báo", body_html="<p>Nội dung gốc</p>",
                                    type="TEST", **kwargs)


def test_worker_recovers_pending_email_after_request_session_closed(db, monkeypatch):
    sent = []
    monkeypatch.setattr(email_tasks, "_deliver", lambda *args: sent.append(args))
    log = queued(db)
    ident = log.id
    assert "Nội dung" not in log.body_encrypted
    assert decrypt_body(log.body_encrypted) == "<p>Nội dung gốc</p>"
    with Session(bind=db.get_bind()) as restarted_worker:
        assert email_tasks.process_pending_emails(restarted_worker) == 1
        assert email_tasks.process_pending_emails(restarted_worker) == 0
    db.expire_all()
    assert db.get(EmailLog, ident).status == "SENT"
    assert len(sent) == 1
    assert email_tasks.send_email_task(ident, db_session=db) is True
    assert len(sent) == 1


def test_failure_backoff_manual_retry_preserves_original_body(db, monkeypatch):
    def fail(*args):
        raise OSError("sensitive remote error must not appear in the log")
    monkeypatch.setattr(email_tasks, "_deliver", fail)
    log = queued(db)
    assert not email_tasks.send_email_task(log.id, db_session=db)
    db.refresh(log)
    assert log.status == "FAILED" and log.sent_at is None
    assert log.retry_count == 1 and log.error_message == "OSError"
    assert email_tasks.process_pending_emails(db) == 0
    tasks = BackgroundTasks()
    assert email_service.retry_failed_emails(db, tasks) == 1
    assert email_service.retry_failed_emails(db, BackgroundTasks()) == 0
    received = []
    monkeypatch.setattr(email_tasks, "_deliver", lambda *args: received.append(args))
    assert email_tasks.send_email_task(log.id, db_session=db)
    assert received[0][2] == "<p>Nội dung gốc</p>"


def test_no_smtp_never_marked_sent(db, monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    log = queued(db)
    assert not email_tasks.send_email_task(log.id, db_session=db)
    db.refresh(log)
    assert log.status == "FAILED" and log.error_message == "SMTP_NOT_CONFIGURED"
    assert log.sent_at is None


def test_expired_and_legacy_missing_payload_are_never_sent(db, monkeypatch):
    transport = MagicMock()
    monkeypatch.setattr(email_tasks, "_deliver", transport)
    expired = queued(db, expires_at=utcnow() - timedelta(seconds=1))
    legacy = EmailLog(recipient_email="old@example.test", subject="Old", type="TEST", status="FAILED")
    db.add(legacy)
    db.commit()
    assert not email_tasks.send_email_task(expired.id, db_session=db)
    assert email_service.retry_failed_emails(db, BackgroundTasks()) == 0
    transport.assert_not_called()
    db.refresh(expired)
    assert expired.error_message == "EMAIL_EXPIRED" and expired.body_encrypted is None


def test_sensitive_payload_removed_after_success_and_not_exposed(client, make_user, auth_headers, db, monkeypatch):
    from app.core.enums import UserRole
    monkeypatch.setattr(email_tasks, "_deliver", lambda *args: None)
    subject, body = email_service.render_email_template("PASSWORD_RESET", {"reset_token": "secret-token"})
    log = email_service.queue_email(db, None, to_email="reset@example.test", subject=subject,
                                    body_html=body, type="PASSWORD_RESET")
    assert "secret-token" not in log.body_encrypted
    admin = make_user(UserRole.ADMIN)
    response = client.get("/api/v1/admin/users/email-logs", headers=auth_headers(admin))
    assert response.status_code == 200
    assert "body_encrypted" not in response.text and "secret-token" not in response.text
    assert email_tasks.send_email_task(log.id, db_session=db)
    db.refresh(log)
    assert log.body_encrypted is None


def test_freelancer_notification_and_mail_share_transaction(db, make_user):
    from app.services.freelancer_domain import notify
    recipient = make_user()
    notify(db, recipient.id, "Hợp đồng đã được chấp nhận", "<script>bad</script>", ref_type="CONTRACT", ref_id=9)
    log = db.scalar(select(EmailLog).where(EmailLog.user_id == recipient.id))
    assert log and log.ref_id == 9
    assert "<script>" not in decrypt_body(log.body_encrypted)
    assert "&lt;script&gt;" in decrypt_body(log.body_encrypted)
    db.rollback()
    assert db.scalar(select(EmailLog).where(EmailLog.user_id == recipient.id)) is None


def test_legacy_email_outbox_queues_once_and_failure_is_visible(db, make_user, monkeypatch):
    from app.models import OutboxEvent
    from app.services.freelancer_worker import claim, process_one

    recipient = make_user()
    row = OutboxEvent(event_key="email:test", event_type="email", entity_type="users",
                      entity_id=recipient.id, available_at=utcnow(),
                      payload_json={"user_id": recipient.id, "title": "Kết quả duyệt", "message": "<b>Nội dung</b>"})
    db.add(row)
    db.commit()
    ident = claim(db, OutboxEvent, "mail-worker")
    assert process_one(db, OutboxEvent, ident, "mail-worker")
    log = db.scalar(select(EmailLog).where(EmailLog.ref_type == "OUTBOX", EmailLog.ref_id == ident))
    assert log and log.recipient_email == recipient.email
    assert log.status == "PENDING"
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    assert email_tasks.process_pending_emails(db) == 1
    db.refresh(log)
    assert log.status == "FAILED"
    assert db.scalar(select(OutboxEvent.status).where(OutboxEvent.id == ident)) == "SUCCEEDED"
    assert claim(db, OutboxEvent, "mail-worker") is None
    assert len(db.scalars(select(EmailLog)).all()) == 1


@pytest.mark.parametrize("implicit", [False, True])
def test_smtp_tls_modes_and_rejected_recipient(monkeypatch, implicit):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.test")
    monkeypatch.setattr(settings, "SMTP_SSL", implicit)
    transport = MagicMock()
    smtp = transport.return_value.__enter__.return_value
    smtp.send_message.return_value = {}
    monkeypatch.setattr(email_tasks.smtplib, "SMTP_SSL" if implicit else "SMTP", transport)
    email_tasks._deliver("recipient@example.test", "Tiêu đề", "<p>Tiếng Việt</p>")
    assert smtp.starttls.call_count == (0 if implicit else 1)
    smtp.send_message.return_value = {"recipient@example.test": (550, "rejected")}
    with pytest.raises(RuntimeError, match="SMTP_RECIPIENT_REFUSED"):
        email_tasks._deliver("recipient@example.test", "Tiêu đề", "<p>Nội dung</p>")
