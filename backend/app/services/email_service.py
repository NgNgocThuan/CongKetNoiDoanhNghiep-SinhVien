"""Gửi email tự động (ghi email_logs + gửi nền bằng FastAPI BackgroundTasks). Người phụ trách: TV1.

Hàm `queue_email` ĐÃ CÓ BẢN CƠ BẢN để các module khác gọi:

    email_service.queue_email(
        db, background_tasks,
        to_email=student.user.email, subject="Đơn ứng tuyển đã được ghi nhận",
        body_html="<p>...</p>", type="APPLY_SUCCESS", user_id=student.user_id,
        ref_type="APPLICATION", ref_id=application.id,
    )

TODO(TV1): thư mục templates HTML (Jinja2) cho từng loại email, cơ chế retry email FAILED,
(tùy chọn) chuyển sang Celery khi cần.
"""
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.models import EmailLog
from app.tasks.email_tasks import send_email_task


def queue_email(
    db: Session,
    background_tasks: BackgroundTasks,
    *,
    to_email: str,
    subject: str,
    body_html: str,
    type: str,
    user_id: Optional[int] = None,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
) -> EmailLog:
    log = EmailLog(
        user_id=user_id,
        recipient_email=to_email,
        type=type,
        subject=subject,
        ref_type=ref_type,
        ref_id=ref_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    background_tasks.add_task(send_email_task, log.id, body_html)
    return log
