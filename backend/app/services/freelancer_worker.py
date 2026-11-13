"""Durable database worker. Claim short leases; provider calls never hold a DB TX."""

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import and_, or_, select

from app.contracts.freelancer.types import CommandContext
from app.core.config import settings
from app.core.exceptions import AppException, ConflictError
from app.core.freelancer_enums import ActorType
from app.models import (
    Company,
    ContractVersion,
    Deliverable,
    Dispute,
    FreelanceContract,
    Milestone,
    MouAgreement,
    Notification,
    OutboxEvent,
    ScheduledJob,
)
from app.services.freelancer_domain import audit, lock, now


def claim(db, model, worker_id):
    at = now()
    is_job = model is ScheduledJob
    queued = ("PENDING", "RETRY")
    running = "RUNNING" if is_job else "PROCESSING"
    due = model.run_at if is_job else model.available_at
    stmt = (
        select(model)
        .where(
            or_(
                and_(model.status.in_(queued), due <= at),
                and_(model.status == running, model.lease_until < at),
            )
        )
        .order_by(due, model.id)
        .limit(1)
    )
    if db.get_bind().dialect.name != "sqlite":
        # Blocking row locks also work on MariaDB versions without SKIP LOCKED.
        # Claim transactions are short and commit before any provider calls.
        stmt = stmt.with_for_update()
    row = db.scalars(stmt.execution_options(populate_existing=True)).first()
    if not row:
        db.rollback()
        return None
    row.status = running
    row.locked_by = worker_id
    row.lease_until = at + timedelta(seconds=settings.FREELANCER_WORKER_LEASE_SECONDS)
    row.attempts += 1
    ident = row.id
    db.commit()
    return ident


def _system(job):
    return CommandContext(
        actor_user_id=None,
        actor_type=ActorType.SYSTEM,
        request_id=job.job_key,
        idempotency_key=None,
        now_utc=now(),
        job_key=job.job_key,
    )


def dispatch_job(db, job):
    data = job.payload_json
    at = now()
    if job.job_type == "contract_version.expire":
        from app.services.freelance_contract_service import FreelanceContractService

        version = db.get(ContractVersion, data.get("version_id") or job.entity_id)
        if (
            version
            and version.status == "OFFERED"
            and version.acceptance_deadline
            and version.acceptance_deadline <= at
        ):
            FreelanceContractService().expire_version_in_tx(
                db, ctx=_system(job), version_id=version.id
            )
    elif job.job_type == "milestone.auto_accept":
        from app.services.deliverable_service import DeliverableWorkService
        from app.services.freelancer_finance import get_finance_port

        m = db.get(Milestone, data["milestone_id"])
        latest = db.scalar(
            select(Deliverable)
            .where(Deliverable.milestone_id == data["milestone_id"])
            .order_by(Deliverable.submission_no.desc())
        )
        if not m or m.status != "SUBMITTED" or not latest or latest.id != data["deliverable_id"]:
            return
        if not m.review_deadline or m.review_deadline > at:
            raise AppException(
                "Review period has not elapsed", code="REVIEW_NOT_DUE", status_code=409
            )
        work = DeliverableWorkService()
        review = work.record_acceptance_in_tx(
            db, ctx=_system(job), milestone_id=m.id, deliverable_id=latest.id, source="AUTO"
        )
        get_finance_port().prepare_acceptance_settlement_in_tx(
            db, ctx=_system(job), review_id=review.review_id
        )
    elif job.job_type in ("mou.expire", "mou.reminder"):
        raw = db.get(MouAgreement, data["mou_id"])
        if not raw:
            return
        c = lock(db, Company, id=raw.company_id)
        m = lock(db, MouAgreement, id=raw.id)
        if m.status != "ACTIVE":
            return
        if job.job_type == "mou.expire":
            if at >= m.effective_until:
                m.status = "EXPIRED"
                audit(db, None, "mou.expired", "mou_agreements", m.id)
                from app.services.freelancer_domain import notify

                notify(db, c.user_id, "Thỏa thuận MOU đã hết hạn",
                       "Vui lòng gia hạn thỏa thuận MOU để tiếp tục sử dụng các quyền hợp tác tương ứng.",
                       ref_type="mou_agreements", ref_id=m.id)
        elif m.effective_until > at:
            from app.services.freelancer_domain import notify

            notify(db, c.user_id, "Thỏa thuận MOU sắp hết hạn",
                   f"Thỏa thuận MOU sẽ hết hạn ngày {m.effective_until:%d/%m/%Y}. Vui lòng gia hạn để tiếp tục hợp tác.",
                   ref_type="mou_agreements", ref_id=m.id)
    elif job.job_type == "dispute.evidence_deadline":
        d = lock(db, Dispute, id=data["dispute_id"])
        if d and d.status == "EVIDENCE_COLLECTION" and d.evidence_deadline <= at:
            d.status = "UNDER_REVIEW"
    elif job.job_type == "contract.closure":
        from app.services.freelance_closure_service import FreelanceClosureService

        service = FreelanceClosureService()
        c = db.get(FreelanceContract, job.entity_id)
        if c:
            service.recompute_contract_closure_in_tx(db, ctx=_system(job), contract_id=c.id)
            service.recompute_project_closure_in_tx(db, ctx=_system(job), project_id=c.project_id)
    else:
        raise AppException("Unsupported job type", code="UNKNOWN_JOB_TYPE")


def dispatch_outbox(db, row):
    data = row.payload_json
    if row.event_type.startswith("finance."):
        from app.services.freelancer_finance_worker import dispatch

        kind, payload = row.event_type, dict(row.payload_json)
        db.rollback()
        dispatch(db, kind, payload)
    elif row.event_type == "file.scan":
        from app.services.stored_file_service import scan_outside_tx

        scan_outside_tx(db, data["file_id"])
    elif row.event_type == "settlement.completed":
        from app.services.dispute_service import finalize_settlement_in_tx
        from app.services.freelancer_ledger_service import finance_gate

        finance_gate(db)
        finalize_settlement_in_tx(db, settlement_id=data["settlement_id"])
    elif row.event_type == "email":
        from html import escape

        from app.models import EmailLog, User
        from app.services.email_service import queue_email

        recipient = db.get(User, data["user_id"])
        if not recipient:
            return
        if db.scalar(select(EmailLog.id).where(EmailLog.ref_type == "OUTBOX", EmailLog.ref_id == row.id)) is None:
            queue_email(db, None, to_email=recipient.email,
                        user_id=recipient.id, type="FREELANCER",
                        subject=data["title"], body_html=f"<p>{escape(data.get('message') or '')}</p>",
                        ref_type="OUTBOX", ref_id=row.id, commit=False)
    elif row.event_type == "notification":
        # Completion of this event and the notification insert share the same transaction.
        db.add(
            Notification(
                user_id=data["user_id"],
                type="FREELANCER",
                title=data["title"],
                content=data["message"],
                ref_type=row.entity_type[:30],
                ref_id=row.entity_id,
            )
        )
    else:
        raise AppException("Unsupported outbox type", code="UNKNOWN_EVENT_TYPE")


def process_one(db, model, record_id, worker_id):
    row = db.get(model, record_id)
    if not row or row.locked_by != worker_id:
        db.rollback()
        return False
    # Copy scalar metadata; file scanning may explicitly end the read-only transaction.
    try:
        if model is ScheduledJob:
            from app.services.freelancer_ledger_service import finance_gate

            finance_gate(db)
            dispatch_job(db, row)
        else:
            dispatch_outbox(db, row)
        db.flush()
        current = lock(db, model, id=record_id)
        if current.locked_by != worker_id or current.lease_until < now():
            db.rollback()
            return False
        current.status = "SUCCEEDED"
        current.lease_until = None
        current.locked_by = None
        if model is ScheduledJob:
            current.finished_at = now()
        else:
            current.completed_at = now()
        current.last_error = None
        audit(db, None, "worker.attempt.finished", model.__tablename__, record_id,
              after={"status": "SUCCEEDED", "finished_at": now().isoformat(), "error": None})
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        current = lock(db, model, id=record_id)
        if current and current.locked_by == worker_id:
            waiting_for_balance = (
                model is OutboxEvent
                and current.event_type == "finance.transfer"
                and isinstance(exc, AppException)
                and exc.code == "PAYOUT_BALANCE_REQUIRED"
            )
            if waiting_for_balance:
                # Waiting for a top-up is not a provider failure. Keep polling
                # without exhausting retries before the administrator funds it.
                current.attempts = max(0, current.attempts - 1)
            current.status = (
                "DEAD"
                if not waiting_for_balance
                and current.attempts >= settings.FREELANCER_WORKER_MAX_ATTEMPTS
                else "RETRY"
            )
            # Do not persist arbitrary HTTP/SQL exception strings or secrets.
            current.last_error = exc.code if isinstance(exc, AppException) else type(exc).__name__
            audit(db, None, "worker.attempt.finished", model.__tablename__, record_id,
                  after={"status": "FAILED", "finished_at": now().isoformat(),
                         "error": current.last_error})
            current.lease_until = None
            current.locked_by = None
            when = now() + timedelta(seconds=min(3600, 30 * 2 ** min(current.attempts, 7)))
            if waiting_for_balance:
                when = now() + timedelta(seconds=60)
            if model is ScheduledJob:
                current.run_at = when
            else:
                current.available_at = when
            db.commit()
        return False


def run_once(db, *, limit=20):
    from app.services.student_lifecycle import process_graduates

    worker_id = uuid4().hex
    processed = process_graduates(db, limit=limit)
    for model in (ScheduledJob, OutboxEvent):
        for _ in range(limit):
            record_id = claim(db, model, worker_id)
            if record_id is None:
                break
            process_one(db, model, record_id, worker_id)
            processed += 1
    from app.tasks.email_tasks import process_pending_emails

    processed += process_pending_emails(db, limit=limit)
    return processed


def retry_in_tx(db, *, user_id, model, record_id, reason):
    from app.services.freelancer_domain import admin, record

    admin(db, user_id)
    row = lock(db, model, id=record_id)
    if not row:
        raise ConflictError("Worker item not found")
    if row.status not in ("DEAD", "RETRY"):
        raise ConflictError("Only failed/retry work can be requeued")
    row.status = "PENDING"
    row.attempts = 0
    row.locked_by = None
    row.lease_until = None
    row.last_error = None
    if model is ScheduledJob:
        row.run_at = now()
    else:
        row.available_at = now()
    audit(db, user_id, "worker.requeued", model.__tablename__, row.id, reason=reason)
    return record(row, exclude=("payload_json",))
