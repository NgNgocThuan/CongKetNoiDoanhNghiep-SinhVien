from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.core.exceptions import NotFoundError
from app.dependencies import AdminUser, DbSession
from app.models import AuditLog, FreelanceReview, OutboxEvent, ScheduledJob
from app.schemas.freelance_projects import Resource, ResourcePage
from app.schemas.freelancer_disputes import Reason
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import audit, lock, page, record
from app.services.freelancer_worker import retry_in_tx

router = APIRouter(tags=["Freelancer operations"])


@router.get(
    "/admin/freelancer/jobs", response_model=ResourcePage, summary="Jobs: /admin/freelancer/jobs"
)
def jobs(
    db: DbSession,
    u: AdminUser,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    important_only: bool = False,
):
    stmt = select(ScheduledJob)
    if important_only:
        stmt = stmt.where(
            ScheduledJob.status.in_(("PENDING", "RUNNING", "RETRY", "DEAD"))
        )
    return page(
        db,
        stmt.order_by(ScheduledJob.id.desc()),
        number,
        size,
        project=lambda x: worker_record(db, x),
    )


@router.get(
    "/admin/freelancer/outbox",
    response_model=ResourcePage,
    summary="Outbox: /admin/freelancer/outbox",
)
def outbox(
    db: DbSession,
    u: AdminUser,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    important_only: bool = False,
):
    stmt = select(OutboxEvent)
    if important_only:
        # This screen is an operator queue. Successful synchronous collection
        # calls and completed technical work belong in audit/history views.
        important_finance = (
            "finance.transfer",
            "finance.receipt",
            "settlement.completed",
        )
        latest_per_task = (
            select(func.max(OutboxEvent.id))
            .group_by(
                OutboxEvent.event_type,
                OutboxEvent.entity_type,
                OutboxEvent.entity_id,
            )
        )
        stmt = stmt.where(
            OutboxEvent.id.in_(latest_per_task),
            or_(
                OutboxEvent.status.in_(("RETRY", "DEAD")),
                and_(
                    OutboxEvent.status.in_(("PENDING", "PROCESSING")),
                    OutboxEvent.event_type.in_(important_finance),
                ),
            )
        )
    return page(
        db,
        stmt.order_by(OutboxEvent.id.desc()),
        number,
        size,
        project=lambda x: worker_record(db, x),
    )


@router.get(
    "/admin/freelancer/audit",
    response_model=ResourcePage,
    summary="Audits: /admin/freelancer/audit",
)
def audits(
    db: DbSession,
    u: AdminUser,
    entity_type: str,
    entity_id: int,
    number: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return page(
        db,
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.id.desc()),
        number,
        size,
    )


@router.post(
    "/admin/freelance-reviews/{review_id}/hide",
    response_model=Resource,
    summary="Hide: /admin/freelance-reviews/{review_id}/hide",
)
def hide(review_id: int, payload: Reason, db: DbSession, u: AdminUser):
    def op():
        row = lock(db, FreelanceReview, id=review_id)
        if not row:
            raise NotFoundError("Review not found")
        row.visibility = "HIDDEN"
        audit(db, u.id, "review.hidden", "freelance_reviews", row.id, reason=payload.reason)
        return record(row)

    return {"data": run_command(db, op)}


@router.post(
    "/admin/freelancer/jobs/{record_id}/retry",
    response_model=Resource,
    summary="Retry jobs: /admin/freelancer/jobs/{record_id}/retry",
)
def retry_jobs(record_id: int, payload: Reason, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: retry_in_tx(
                db, user_id=u.id, model=ScheduledJob, record_id=record_id, reason=payload.reason
            ),
        )
    }


@router.post(
    "/admin/freelancer/outbox/{record_id}/retry",
    response_model=Resource,
    summary="Retry outbox: /admin/freelancer/outbox/{record_id}/retry",
)
def retry_outbox(record_id: int, payload: Reason, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: retry_in_tx(
                db, user_id=u.id, model=OutboxEvent, record_id=record_id, reason=payload.reason
            ),
        )
    }


def worker_record(db, row):
    from app.models import (
        Company,
        FreelanceContract,
        FreelanceProject,
        Milestone,
        MoneyTransfer,
        PaymentOrder,
        Settlement,
        StoredFile,
        Student,
        User,
    )
    result = record(row, exclude=("payload_json",))
    kind = getattr(row, "event_type", None) or getattr(row, "job_type", "")
    result["task_type"] = kind
    milestone = None
    contract = None
    target = None
    if row.entity_type == "money_transfers":
        target = db.get(MoneyTransfer, row.entity_id)
        settlement = db.get(Settlement, target.settlement_id) if target and target.settlement_id else None
        milestone = db.get(Milestone, settlement.milestone_id) if settlement else None
        if target:
            result["transfer_id"] = str(target.id)
            result["transfer_status"] = str(target.status)
            result["amount"] = str(target.amount)
            result["provider_reference"] = target.provider_reference_id
    elif row.entity_type == "payment_orders":
        target = db.get(PaymentOrder, row.entity_id)
        milestone = db.get(Milestone, target.milestone_id) if target else None
    elif row.entity_type == "milestones":
        milestone = db.get(Milestone, row.entity_id)
    elif row.entity_type == "freelance_contracts":
        contract = db.get(FreelanceContract, row.entity_id)
    elif row.entity_type == "stored_files":
        file = db.get(StoredFile, row.entity_id)
        if file:
            result["file_name"] = file.original_name
            uploader = db.get(User, file.uploaded_by)
            result["uploaded_by"] = uploader.email if uploader else str(file.uploaded_by)
    if milestone:
        result["milestone_id"] = str(milestone.id)
        contract = db.get(FreelanceContract, milestone.contract_id)
    project = db.get(FreelanceProject, contract.project_id) if contract else None
    if contract:
        result["contract_id"] = str(contract.id)
        student = db.get(Student, contract.freelancer_student_id)
        client = db.get(User, contract.client_user_id)
        company = db.scalar(select(Company).where(Company.user_id == contract.client_user_id))
        result["student_name"] = student.full_name if student else None
        result["client_name"] = company.name if company else client.email if client else None
    if project:
        result["project_id"] = str(project.id)
        result["project_title"] = project.title
    result["attempt_history"] = [x.after_json for x in db.scalars(select(AuditLog).where(
        AuditLog.entity_type == row.__tablename__, AuditLog.entity_id == row.id,
        AuditLog.action == "worker.attempt.finished").order_by(AuditLog.id.desc()).limit(50))]
    return result
