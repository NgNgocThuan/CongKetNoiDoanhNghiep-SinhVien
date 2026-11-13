"""Schedule reminders and expiry in the same transaction as MOU activation."""
from datetime import timedelta

from sqlalchemy import select

from app.models import ScheduledJob
from app.utils.datetime_utils import utcnow


def schedule_mou_lifecycle(db, mou):
    db.flush()
    jobs = [(f"mou.expire:{mou.id}", "mou.expire", mou.effective_until, {"mou_id": mou.id})]
    for days in (30, 14, 7, 1):
        at = mou.effective_until - timedelta(days=days)
        if at > utcnow():
            jobs.append((f"mou.reminder:{mou.id}:{days}", "mou.reminder", at, {"mou_id": mou.id, "days": days}))
    for key, kind, at, payload in jobs:
        if not db.scalar(select(ScheduledJob.id).where(ScheduledJob.job_key == key)):
            db.add(ScheduledJob(job_key=key, job_type=kind, entity_type="mou_agreements", entity_id=mou.id, run_at=at, payload_json=payload))
