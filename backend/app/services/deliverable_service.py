"""Deliverable service: WorkPort implementation, submissions, revisions, and acceptance (Ticket C4, C5)."""

from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.contracts.freelancer.ports import FinancePort, WorkPort
from app.contracts.freelancer.types import (
    AcceptanceRef,
    CommandContext,
    SettlementRef,
)
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableError,
)
from app.core.freelancer_enums import (
    AcceptanceSource,
    ActorType,
    ContractStatus,
    FileAvailability,
    FileScanStatus,
    MilestoneReviewAction,
    MilestoneStatus,
    ScheduledJobStatus,
    SettlementKind,
    SettlementStatus,
)
from app.models import FreelanceProject, Student
from app.models.freelancer_contracts import (
    ContractMilestoneTerm,
    ContractVersion,
    Deliverable,
    DeliverableFile,
    FreelanceContract,
    Milestone,
    MilestoneReview,
)
from app.models.freelancer_disputes import ActiveMilestoneDispute, MilestoneHold
from app.models.freelancer_identity import StoredFile
from app.models.freelancer_operations import AuditLog, CommandRequest, ScheduledJob
from app.services.freelancer_commands import run_command
from app.services.freelancer_finance import get_finance_port
from app.utils.hashing import sha256_json


def _norm_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _for_update(query, db: Session):
    bind = db.get_bind()
    if bind is not None and bind.dialect.name != "sqlite":
        return query.populate_existing().with_for_update()
    return query


class DeliverableService:
    """Manages student submissions and client revision requests."""

    def submit_deliverable_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        milestone_id: int,
        file_ids: list[int] | None = None,
        note: str | None = None,
    ) -> Deliverable:
        """Submit a deliverable for a milestone in progress or revision requested."""
        milestone_raw = db.get(Milestone, milestone_id)
        if not milestone_raw:
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        contract_raw = db.get(FreelanceContract, milestone_raw.contract_id)
        if not contract_raw:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        # Global lock ordering: project -> contract -> milestone
        _for_update(db.query(FreelanceProject).filter_by(id=contract_raw.project_id), db).first()
        _for_update(db.query(FreelanceContract).filter_by(id=contract_raw.id), db).first()
        milestone = _for_update(db.query(Milestone).filter_by(id=milestone_raw.id), db).first()

        student = db.get(Student, contract_raw.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check
        if ctx.actor_user_id not in (contract_raw.client_user_id, student.user_id):
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        # Only contracted student can submit
        if ctx.actor_user_id != student.user_id:
            raise ForbiddenError(
                "Only the contracted student can submit deliverables", code="FORBIDDEN"
            )

        if contract_raw.status != ContractStatus.ACTIVE:
            raise ConflictError(
                "Contract must be ACTIVE to submit deliverable", code="INVALID_STATE_TRANSITION"
            )

        if milestone.status not in (
            MilestoneStatus.IN_PROGRESS,
            MilestoneStatus.REVISION_REQUESTED,
        ):
            raise ConflictError(
                "Milestone must be IN_PROGRESS or REVISION_REQUESTED to submit deliverable",
                code="INVALID_STATE_TRANSITION",
            )

        # Invariant checks: holds and disputes
        active_holds = (
            db.query(MilestoneHold)
            .filter(
                MilestoneHold.milestone_id == milestone.id,
                MilestoneHold.released_at.is_(None),
            )
            .count()
        )
        if active_holds > 0:
            raise ConflictError("Milestone has active hold or dispute", code="FUNDS_ON_HOLD")

        active_disputes = (
            db.query(ActiveMilestoneDispute)
            .filter_by(
                milestone_id=milestone.id,
            )
            .count()
        )
        if active_disputes > 0:
            raise ConflictError("Milestone has active hold or dispute", code="FUNDS_ON_HOLD")

        f_ids = file_ids or []
        if len(set(f_ids)) != len(f_ids):
            raise UnprocessableError("Duplicate file_ids are not allowed", code="VALIDATION_ERROR")
        clean_note = note.strip() if note else None

        if not f_ids and not clean_note:
            raise UnprocessableError(
                "Deliverable requires at least one attached file or a note", code="VALIDATION_ERROR"
            )

        # Validate attached files
        for fid in f_ids:
            stored_file = db.get(StoredFile, fid)
            if not stored_file or stored_file.uploaded_by != ctx.actor_user_id:
                raise NotFoundError("File not found", code="NOT_FOUND")
            if (
                stored_file.scan_status != FileScanStatus.CLEAN
                or stored_file.availability_status != FileAvailability.AVAILABLE
            ):
                raise ConflictError(
                    "Attached file is not clean or available", code="VALIDATION_ERROR"
                )

        # Next submission number
        max_sub = (
            db.query(func.coalesce(func.max(Deliverable.submission_no), 0))
            .filter_by(milestone_id=milestone.id)
            .scalar()
            or 0
        )
        submission_no = max_sub + 1

        now = _norm_utc(ctx.now_utc)
        deliverable = Deliverable(
            milestone_id=milestone.id,
            submission_no=submission_no,
            submitted_by=ctx.actor_user_id,
            note=clean_note,
            submitted_at=now,
        )
        db.add(deliverable)
        db.flush()

        for fid in f_ids:
            db.add(DeliverableFile(deliverable_id=deliverable.id, file_id=fid))
        db.flush()

        # Update milestone status and review deadline
        term = (
            db.get(ContractMilestoneTerm, milestone.effective_terms_id)
            if milestone.effective_terms_id
            else None
        )
        version = db.get(ContractVersion, term.contract_version_id) if term else None
        if version is None:
            raise ConflictError(
                "Milestone has no effective policy snapshot", code="INVALID_STATE_TRANSITION"
            )
        review_seconds = version.review_period_seconds if version else 604800
        review_deadline = now + timedelta(seconds=review_seconds)

        milestone.status = MilestoneStatus.SUBMITTED
        milestone.submitted_at = now
        milestone.review_deadline = review_deadline

        # Cancel any pending auto_accept jobs for milestone
        old_jobs = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.entity_type == "milestones",
                ScheduledJob.entity_id == milestone.id,
                ScheduledJob.job_type == "milestone.auto_accept",
                ScheduledJob.status == ScheduledJobStatus.PENDING,
            )
            .all()
        )
        for oj in old_jobs:
            oj.status = ScheduledJobStatus.CANCELLED

        # Create auto_accept scheduled job
        db.add(
            ScheduledJob(
                job_key=f"milestone.auto_accept:{milestone.id}:{submission_no}",
                job_type="milestone.auto_accept",
                entity_type="milestones",
                entity_id=milestone.id,
                run_at=review_deadline,
                payload_json={
                    "milestone_id": milestone.id,
                    "deliverable_id": deliverable.id,
                    "submission_no": submission_no,
                },
                status=ScheduledJobStatus.PENDING,
            )
        )

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="deliverable.submitted",
                entity_type="deliverables",
                entity_id=deliverable.id,
                request_id=ctx.request_id,
            )
        )
        from app.services.freelancer_domain import notify

        notify(
            db,
            contract_raw.client_user_id,
            "Sinh viên đã gửi sản phẩm",
            f"Sinh viên đã gửi lần bàn giao #{submission_no}. Hãy mở công việc để xem tệp và nghiệm thu.",
            ref_type="FREELANCE_MILESTONE",
            ref_id=milestone.id,
        )
        db.flush()

        return deliverable

    def submit_deliverable(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        milestone_id: int,
        file_ids: list[int] | None = None,
        note: str | None = None,
    ) -> Deliverable:
        return run_command(
            db,
            lambda: self.submit_deliverable_in_tx(
                db,
                ctx=ctx,
                milestone_id=milestone_id,
                file_ids=file_ids,
                note=note,
            ),
        )

    def request_revision_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        milestone_id: int,
        deliverable_id: int,
        reason: str,
    ) -> MilestoneReview:
        """Client requests revisions on the latest submitted deliverable under lock."""
        milestone_raw = db.get(Milestone, milestone_id)
        if not milestone_raw:
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        contract_raw = db.get(FreelanceContract, milestone_raw.contract_id)
        if not contract_raw:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        # Global lock ordering: project -> contract -> milestone
        _for_update(db.query(FreelanceProject).filter_by(id=contract_raw.project_id), db).first()
        _for_update(db.query(FreelanceContract).filter_by(id=contract_raw.id), db).first()
        milestone = _for_update(db.query(Milestone).filter_by(id=milestone_raw.id), db).first()

        student = db.get(Student, contract_raw.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check
        if ctx.actor_user_id not in (contract_raw.client_user_id, student.user_id):
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        # Role permission: Only client can request revision
        if ctx.actor_user_id != contract_raw.client_user_id:
            raise ForbiddenError("Only the contract client can request revision", code="FORBIDDEN")

        # Invariant checks: holds and disputes
        active_holds = (
            db.query(MilestoneHold)
            .filter(
                MilestoneHold.milestone_id == milestone.id,
                MilestoneHold.released_at.is_(None),
            )
            .count()
        )
        if active_holds > 0:
            raise ConflictError("Milestone has active hold or dispute", code="FUNDS_ON_HOLD")

        active_disputes = (
            db.query(ActiveMilestoneDispute)
            .filter_by(
                milestone_id=milestone.id,
            )
            .count()
        )
        if active_disputes > 0:
            raise ConflictError("Milestone has active hold or dispute", code="FUNDS_ON_HOLD")

        clean_reason = reason.strip() if reason else ""
        if not clean_reason:
            raise UnprocessableError(
                "Reason is required to request revision", code="VALIDATION_ERROR"
            )

        if milestone.status != MilestoneStatus.SUBMITTED:
            raise ConflictError(
                "Milestone is not in SUBMITTED status", code="INVALID_STATE_TRANSITION"
            )

        deliverable = db.get(Deliverable, deliverable_id)
        if not deliverable or deliverable.milestone_id != milestone.id:
            raise NotFoundError("Deliverable not found", code="NOT_FOUND")

        # Must be latest submission
        max_sub = (
            db.query(func.max(Deliverable.submission_no))
            .filter_by(milestone_id=milestone.id)
            .scalar()
        )
        if deliverable.submission_no != max_sub:
            raise ConflictError(
                "Only the latest submitted deliverable can be reviewed",
                code="INVALID_STATE_TRANSITION",
            )

        # Check revision limit
        term = (
            db.get(ContractMilestoneTerm, milestone.effective_terms_id)
            if milestone.effective_terms_id
            else None
        )
        version = db.get(ContractVersion, term.contract_version_id) if term else None
        if version is None:
            raise ConflictError(
                "Milestone has no effective policy snapshot", code="INVALID_STATE_TRANSITION"
            )
        max_revisions = version.max_revision_count if version else 3
        if milestone.revision_count >= max_revisions:
            raise ConflictError("Maximum revision count reached", code="REVISION_LIMIT_EXCEEDED")

        now = _norm_utc(ctx.now_utc)
        review = MilestoneReview(
            milestone_id=milestone.id,
            deliverable_id=deliverable.id,
            reviewed_by=ctx.actor_user_id,
            action=MilestoneReviewAction.REQUEST_REVISION,
            reason=clean_reason,
            reviewed_at=now,
        )
        db.add(review)
        db.flush()

        milestone.revision_count += 1
        milestone.status = MilestoneStatus.REVISION_REQUESTED
        milestone.review_deadline = None

        # Cancel auto_accept jobs
        pending_jobs = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.entity_type == "milestones",
                ScheduledJob.entity_id == milestone.id,
                ScheduledJob.job_type == "milestone.auto_accept",
                ScheduledJob.status == ScheduledJobStatus.PENDING,
            )
            .all()
        )
        for pj in pending_jobs:
            pj.status = ScheduledJobStatus.CANCELLED

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="milestone.revision_requested",
                entity_type="milestones",
                entity_id=milestone.id,
                request_id=ctx.request_id,
            )
        )
        from app.services.freelancer_domain import notify

        notify(
            db,
            student.user_id,
            "Người thuê yêu cầu chỉnh sửa",
            clean_reason,
            ref_type="FREELANCE_MILESTONE",
            ref_id=milestone.id,
        )
        db.flush()

        return review

    def request_revision(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        milestone_id: int,
        deliverable_id: int,
        reason: str,
    ) -> MilestoneReview:
        return run_command(
            db,
            lambda: self.request_revision_in_tx(
                db,
                ctx=ctx,
                milestone_id=milestone_id,
                deliverable_id=deliverable_id,
                reason=reason,
            ),
        )

    def get_deliverables(
        self,
        db: Session,
        *,
        milestone_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> list[Deliverable]:
        """List deliverables for a milestone with zero-leak check."""
        milestone = db.get(Milestone, milestone_id)
        if not milestone:
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        contract = db.get(FreelanceContract, milestone.contract_id)
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        if not is_admin:
            student = db.get(Student, contract.freelancer_student_id)
            if not student or actor_user_id not in (contract.client_user_id, student.user_id):
                raise NotFoundError("Milestone not found", code="NOT_FOUND")

        return (
            db.query(Deliverable)
            .filter_by(milestone_id=milestone_id)
            .order_by(Deliverable.submission_no.asc())
            .all()
        )

    def get_deliverables_page(
        self, db, *, milestone_id, actor_user_id, is_admin=False, page=1, size=20
    ):
        from sqlalchemy import select

        from app.services.freelancer_domain import page as paginate
        from app.services.freelancer_domain import party

        m = db.get(Milestone, milestone_id)
        c = db.get(FreelanceContract, m.contract_id) if m else None
        if not c:
            raise NotFoundError("Milestone not found")
        party(db, c, actor_user_id, allow_admin=is_admin)
        return paginate(
            db,
            select(Deliverable)
            .where(Deliverable.milestone_id == milestone_id)
            .order_by(Deliverable.submission_no.desc()),
            page,
            size,
            project=lambda x: x,
        )

    def get_deliverable(
        self,
        db: Session,
        *,
        deliverable_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> Deliverable:
        """Fetch single deliverable with zero-leak check."""
        deliverable = db.get(Deliverable, deliverable_id)
        if not deliverable:
            raise NotFoundError("Deliverable not found", code="NOT_FOUND")

        milestone = db.get(Milestone, deliverable.milestone_id)
        if not milestone:
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        contract = db.get(FreelanceContract, milestone.contract_id)
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        if not is_admin:
            student = db.get(Student, contract.freelancer_student_id)
            if not student or actor_user_id not in (contract.client_user_id, student.user_id):
                raise NotFoundError("Deliverable not found", code="NOT_FOUND")

        return deliverable


class DeliverableWorkService(WorkPort):
    """WorkPort implementation for milestone acceptance recording."""

    def record_acceptance_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        milestone_id: int,
        deliverable_id: int,
        source: Literal["MANUAL", "AUTO"],
    ) -> AcceptanceRef:
        """Record acceptance under strict lock ordering (project -> contract -> milestone)."""
        milestone_raw = db.get(Milestone, milestone_id)
        if not milestone_raw:
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        contract_raw = db.get(FreelanceContract, milestone_raw.contract_id)
        if not contract_raw:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        # 1. Lock in strict order
        _for_update(db.query(FreelanceProject).filter_by(id=contract_raw.project_id), db).first()
        contract = _for_update(
            db.query(FreelanceContract).filter_by(id=contract_raw.id), db
        ).first()
        milestone = _for_update(db.query(Milestone).filter_by(id=milestone_raw.id), db).first()

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # 2. Permission check
        if source == "MANUAL":
            if ctx.actor_type != ActorType.USER:
                raise ForbiddenError("Manual acceptance requires a USER actor", code="FORBIDDEN")
            if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
                raise NotFoundError("Milestone not found", code="NOT_FOUND")
            if ctx.actor_user_id != contract.client_user_id:
                raise ForbiddenError(
                    "Only the contract client can accept a milestone", code="FORBIDDEN"
                )
        elif source == "AUTO":
            if ctx.actor_type != ActorType.SYSTEM:
                raise ForbiddenError("Auto acceptance requires a SYSTEM actor", code="FORBIDDEN")
            now = _norm_utc(ctx.now_utc)
            if milestone.review_deadline is None or now < milestone.review_deadline:
                raise ConflictError(
                    "Review deadline has not passed yet", code="INVALID_STATE_TRANSITION"
                )

        # 3. Status checks
        if contract.status != ContractStatus.ACTIVE:
            raise ConflictError("Contract is not active", code="INVALID_STATE_TRANSITION")

        if milestone.status != MilestoneStatus.SUBMITTED:
            raise ConflictError(
                "Milestone is not in SUBMITTED status", code="INVALID_STATE_TRANSITION"
            )

        # 4. Invariant checks: holds and disputes
        active_holds = (
            db.query(MilestoneHold)
            .filter(
                MilestoneHold.milestone_id == milestone.id,
                MilestoneHold.released_at.is_(None),
            )
            .count()
        )
        if active_holds > 0:
            raise ConflictError("Milestone funds are on hold", code="FUNDS_ON_HOLD")

        active_disputes = (
            db.query(ActiveMilestoneDispute)
            .filter_by(
                milestone_id=milestone.id,
            )
            .count()
        )
        if active_disputes > 0:
            raise ConflictError("Milestone has active hold or dispute", code="FUNDS_ON_HOLD")

        # 5. Deliverable check
        deliverable = db.get(Deliverable, deliverable_id)
        if not deliverable or deliverable.milestone_id != milestone.id:
            raise NotFoundError("Deliverable not found", code="NOT_FOUND")

        max_sub = (
            db.query(func.max(Deliverable.submission_no))
            .filter_by(milestone_id=milestone.id)
            .scalar()
        )
        if deliverable.submission_no != max_sub:
            raise ConflictError(
                "Only the latest deliverable can be accepted", code="INVALID_STATE_TRANSITION"
            )

        # 6. Record review
        now = _norm_utc(ctx.now_utc)
        review = MilestoneReview(
            milestone_id=milestone.id,
            deliverable_id=deliverable.id,
            reviewed_by=ctx.actor_user_id if source == "MANUAL" else None,
            action=MilestoneReviewAction.ACCEPT
            if source == "MANUAL"
            else MilestoneReviewAction.AUTO_ACCEPT,
            reviewed_at=now,
        )
        db.add(review)
        db.flush()

        # 7. Update milestone state
        milestone.status = MilestoneStatus.ACCEPTED
        milestone.accepted_at = now
        milestone.acceptance_source = (
            AcceptanceSource.MANUAL if source == "MANUAL" else AcceptanceSource.AUTO
        )
        milestone.review_deadline = None
        db.flush()

        # 8. Manage auto_accept scheduled job
        jobs = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.entity_type == "milestones",
                ScheduledJob.entity_id == milestone.id,
                ScheduledJob.job_type == "milestone.auto_accept",
                ScheduledJob.status == ScheduledJobStatus.PENDING,
            )
            .all()
        )
        for j in jobs:
            if ctx.job_key and j.job_key == ctx.job_key:
                j.status = ScheduledJobStatus.SUCCEEDED
                j.finished_at = now
            else:
                j.status = ScheduledJobStatus.CANCELLED

        # 9. Audit
        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="milestone.accepted",
                entity_type="milestones",
                entity_id=milestone.id,
                request_id=ctx.request_id,
            )
        )
        from app.services.freelancer_domain import notify

        notify(
            db,
            student.user_id,
            "Sản phẩm đã được nghiệm thu",
            "Người thuê đã nghiệm thu sản phẩm. Hệ thống đang xử lý quyết toán và giải ngân.",
            ref_type="FREELANCE_MILESTONE",
            ref_id=milestone.id,
        )
        db.flush()

        return AcceptanceRef(
            review_id=review.id,
            milestone_id=milestone.id,
            deliverable_id=deliverable.id,
            source=source,
            accepted_at=now,
        )


def _assert_milestone_accept_permission(
    db: Session,
    *,
    milestone_id: int,
    actor_user_id: int,
) -> None:
    """Validate that actor has client permission on the milestone's contract (Zero-Leak)."""
    milestone = db.get(Milestone, milestone_id)
    if not milestone:
        raise NotFoundError("Milestone not found", code="NOT_FOUND")

    contract = db.get(FreelanceContract, milestone.contract_id)
    if not contract:
        raise NotFoundError("Contract not found", code="NOT_FOUND")

    student = db.get(Student, contract.freelancer_student_id)
    if not student:
        raise NotFoundError("Student not found", code="NOT_FOUND")

    if actor_user_id not in (contract.client_user_id, student.user_id):
        raise NotFoundError("Milestone not found", code="NOT_FOUND")

    if actor_user_id != contract.client_user_id:
        raise ForbiddenError("Only the contract client can accept a milestone", code="FORBIDDEN")


def accept_milestone_command(
    db: Session,
    *,
    ctx: CommandContext,
    milestone_id: int,
    deliverable_id: int,
    finance_port: FinancePort | None = None,
    automatic: bool = False,
) -> SettlementRef:
    """Atomic acceptance entrypoint supporting CommandRequest idempotency replay in a single transaction."""
    # Check permissions upfront before executing or reading replay cache to maintain zero-leak invariants
    if not automatic and ctx.actor_type == ActorType.USER and ctx.actor_user_id is not None:
        _assert_milestone_accept_permission(
            db, milestone_id=milestone_id, actor_user_id=ctx.actor_user_id
        )

    finance = finance_port or get_finance_port()
    work = DeliverableWorkService()
    req_hash = sha256_json({"milestone_id": milestone_id, "deliverable_id": deliverable_id})

    def operation() -> SettlementRef:
        from app.services.freelancer_domain import milestone_scope

        milestone_scope(db, milestone_id, ctx.actor_user_id, internal=automatic)
        # 1. Check idempotency replay inside tx under lock
        if ctx.actor_type == ActorType.USER and ctx.idempotency_key:
            existing = _for_update(
                db.query(CommandRequest).filter_by(
                    actor_user_id=ctx.actor_user_id,
                    operation="freelance.accept_milestone",
                    idempotency_key=ctx.idempotency_key,
                ),
                db,
            ).first()
            if existing:
                if existing.request_hash == req_hash and existing.response_json:
                    data = existing.response_json
                    return SettlementRef(
                        settlement_id=data["settlement_id"],
                        milestone_id=data["milestone_id"],
                        kind=SettlementKind(data["kind"]),
                        status=SettlementStatus(data["status"]),
                    )
                raise ConflictError(
                    "Idempotency key reused with different payload", code="IDEMPOTENCY_CONFLICT"
                )

        # 2. Execute work & finance in tx
        source = "AUTO" if automatic else "MANUAL"
        acc_ref = work.record_acceptance_in_tx(
            db,
            ctx=ctx,
            milestone_id=milestone_id,
            deliverable_id=deliverable_id,
            source=source,
        )
        settlement_ref = finance.prepare_acceptance_settlement_in_tx(
            db,
            ctx=ctx,
            review_id=acc_ref.review_id,
        )

        # 3. Save CommandRequest replay record inside the same transaction
        if ctx.actor_type == ActorType.USER and ctx.idempotency_key:
            cmd_rec = CommandRequest(
                actor_user_id=ctx.actor_user_id,
                operation="freelance.accept_milestone",
                idempotency_key=ctx.idempotency_key,
                request_hash=req_hash,
                result_entity_type="settlements",
                result_entity_id=settlement_ref.settlement_id,
                response_json={
                    "settlement_id": settlement_ref.settlement_id,
                    "milestone_id": settlement_ref.milestone_id,
                    "kind": settlement_ref.kind.value
                    if hasattr(settlement_ref.kind, "value")
                    else str(settlement_ref.kind),
                    "status": settlement_ref.status.value
                    if hasattr(settlement_ref.status, "value")
                    else str(settlement_ref.status),
                },
                completed_at=_norm_utc(ctx.now_utc),
            )
            db.add(cmd_rec)
            db.flush()

        return settlement_ref

    return run_command(db, operation)
