"""Milestone service: terms lookup and start guard verification (Ticket C3)."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.contracts.freelancer.ports import FinancePort
from app.contracts.freelancer.types import CommandContext
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.core.freelancer_enums import (
    ContractStatus,
    FundingPolicy,
    MilestoneStatus,
)
from app.models import FreelanceProject, Student
from app.models.freelancer_contracts import (
    ContractMilestoneTerm,
    ContractVersion,
    FreelanceContract,
    Milestone,
)
from app.models.freelancer_disputes import ActiveMilestoneDispute, MilestoneHold
from app.models.freelancer_operations import AuditLog
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import notify
from app.services.freelancer_finance import get_finance_port


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


class MilestoneService:
    """Manages milestone access and start lifecycle enforcing financial and term guards."""

    def start_milestone_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        milestone_id: int,
        finance_port: FinancePort | None = None,
    ) -> Milestone:
        """Start a funded milestone after verifying contract, funding guards, and finance port."""
        # Lock in strict order: project -> contract -> milestone
        milestone_raw = db.get(Milestone, milestone_id)
        if not milestone_raw:
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        contract_raw = db.get(FreelanceContract, milestone_raw.contract_id)
        if not contract_raw:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        # Lock rows in strict order
        _for_update(db.query(FreelanceProject).filter_by(id=contract_raw.project_id), db).first()
        contract = _for_update(
            db.query(FreelanceContract).filter_by(id=contract_raw.id), db
        ).first()
        milestone = _for_update(db.query(Milestone).filter_by(id=milestone_raw.id), db).first()

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check: actor must be a party
        if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
            raise NotFoundError("Milestone not found", code="NOT_FOUND")

        # Role permission: Only contracted student can start
        if ctx.actor_user_id != student.user_id:
            raise ForbiddenError(
                "Only the contracted student can start a milestone", code="FORBIDDEN"
            )

        if contract.status != ContractStatus.ACTIVE:
            raise ConflictError(
                "Contract must be ACTIVE to start milestone", code="INVALID_STATE_TRANSITION"
            )

        if milestone.effective_terms_id is None:
            raise ConflictError("Milestone has no effective terms", code="INVALID_STATE_TRANSITION")

        # State guard: must be FUNDED
        if milestone.status in (MilestoneStatus.NOT_FUNDED, MilestoneStatus.FUNDING_PENDING):
            raise ConflictError("Milestone is not funded", code="MILESTONE_NOT_FUNDED")

        if milestone.status != MilestoneStatus.FUNDED:
            raise ConflictError(
                f"Milestone cannot be started from status {milestone.status}",
                code="INVALID_STATE_TRANSITION",
            )

        # Policy check: FULL requires all included milestones of THIS contract to be funded
        version = db.get(ContractVersion, contract.effective_version_id)
        if version and version.funding_policy == FundingPolicy.FULL:
            included_terms = (
                db.query(ContractMilestoneTerm)
                .filter(
                    ContractMilestoneTerm.contract_version_id == version.id,
                    ContractMilestoneTerm.included.is_(True),
                )
                .all()
            )
            for term in included_terms:
                ms = db.get(Milestone, term.milestone_id)
                if ms and ms.status in (
                    MilestoneStatus.NOT_FUNDED,
                    MilestoneStatus.FUNDING_PENDING,
                ):
                    raise ConflictError(
                        "Full contract funding required before starting",
                        code="MILESTONE_NOT_FUNDED",
                    )

        # Guard: No active holds on milestone
        active_holds_count = (
            db.query(MilestoneHold)
            .filter(
                MilestoneHold.milestone_id == milestone.id,
                MilestoneHold.released_at.is_(None),
            )
            .count()
        )
        if active_holds_count > 0:
            raise ConflictError("Milestone funds are on hold", code="FUNDS_ON_HOLD")

        # Guard: No active dispute
        active_dispute_count = (
            db.query(ActiveMilestoneDispute)
            .filter_by(
                milestone_id=milestone.id,
            )
            .count()
        )
        if active_dispute_count > 0:
            raise ConflictError("Milestone is under dispute", code="FUNDS_ON_HOLD")

        # Assert through finance port
        finance = finance_port or get_finance_port()
        finance.assert_can_start_in_tx(db, ctx=ctx, milestone_id=milestone.id)

        # Transition
        now = _norm_utc(ctx.now_utc)
        milestone.status = MilestoneStatus.IN_PROGRESS
        milestone.started_at = now

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="milestone.started",
                entity_type="milestones",
                entity_id=milestone.id,
                request_id=ctx.request_id,
            )
        )
        notify(
            db,
            contract.client_user_id,
            "Sinh viên đã bắt đầu công việc",
            "Sinh viên đã bắt đầu thực hiện một mốc trong hợp đồng Freelancer.",
            ref_type="FREELANCE_MILESTONE",
            ref_id=milestone.id,
        )
        db.flush()

        return milestone

    def start_milestone(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        milestone_id: int,
        finance_port: FinancePort | None = None,
    ) -> Milestone:
        """Outer command boundary for starting a milestone."""
        return run_command(
            db,
            lambda: self.start_milestone_in_tx(
                db,
                ctx=ctx,
                milestone_id=milestone_id,
                finance_port=finance_port,
            ),
        )

    def get_milestone(
        self,
        db: Session,
        *,
        milestone_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> Milestone:
        """Fetch milestone ensuring zero-leak checks."""
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

        return milestone

    def get_contract_milestones(
        self,
        db: Session,
        *,
        contract_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> list[Milestone]:
        """List milestones of a contract with zero-leak check."""
        contract = db.get(FreelanceContract, contract_id)
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        if not is_admin:
            student = db.get(Student, contract.freelancer_student_id)
            if not student or actor_user_id not in (contract.client_user_id, student.user_id):
                raise NotFoundError("Contract not found", code="NOT_FOUND")

        return (
            db.query(Milestone)
            .filter_by(contract_id=contract_id)
            .order_by(Milestone.sequence_no.asc())
            .all()
        )
