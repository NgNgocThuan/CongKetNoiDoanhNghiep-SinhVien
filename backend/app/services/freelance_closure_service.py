"""Freelance closure service: ClosurePort implementation for contracts and projects (Ticket C6)."""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.contracts.freelancer.ports import ClosurePort
from app.contracts.freelancer.types import (
    CommandContext,
    ProjectClosureState,
)
from app.core.exceptions import ConflictError, NotFoundError
from app.core.freelancer_enums import (
    ActorType,
    ContractBudgetStatus,
    ContractStatus,
    ContractVersionStatus,
    MilestoneStatus,
    PaymentOrderStatus,
    PaymentReviewStatus,
    ProjectStatus,
    RecruitmentStatus,
    SettlementStatus,
    TransferStatus,
)
from app.models import FreelanceProject, Student
from app.models.freelancer_contracts import (
    ContractMilestoneTerm,
    ContractVersion,
    FreelanceContract,
    Milestone,
    ProjectContractBudget,
)
from app.models.freelancer_disputes import ActiveMilestoneDispute, MilestoneHold
from app.models.freelancer_finance import MoneyTransfer, Settlement
from app.models.freelancer_operations import AuditLog
from app.models.freelancer_payments import (
    EscrowAccount,
    MilestoneFundingGuard,
    PaymentOrder,
    PaymentReviewCase,
    PaymentTransaction,
)
from app.services.freelancer_commands import run_command


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


class FreelanceClosureService(ClosurePort):
    """Coordinates contract and multi-contract project closure invariants."""

    def recompute_contract_closure_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
    ) -> None:
        """Recompute terminal status for a contract after milestone or dispute completion."""
        contract_raw = db.get(FreelanceContract, contract_id)
        if not contract_raw or contract_raw.status in (
            ContractStatus.COMPLETED,
            ContractStatus.CANCELLED,
            ContractStatus.TERMINATED,
        ):
            return

        # Lock global hierarchy: project -> contract -> milestones (id asc)
        project = _for_update(
            db.query(FreelanceProject).filter_by(id=contract_raw.project_id), db
        ).first()
        contract = _for_update(
            db.query(FreelanceContract).filter_by(id=contract_raw.id), db
        ).first()
        milestones = _for_update(
            db.query(Milestone).filter_by(contract_id=contract.id).order_by(Milestone.id.asc()),
            db,
        ).all()
        m_ids = [m.id for m in milestones]

        if m_ids:
            # Active disputes
            if (
                db.query(ActiveMilestoneDispute)
                .filter(ActiveMilestoneDispute.milestone_id.in_(m_ids))
                .first()
            ):
                return
            # Active holds
            if (
                db.query(MilestoneHold)
                .filter(MilestoneHold.milestone_id.in_(m_ids), MilestoneHold.released_at.is_(None))
                .first()
            ):
                return
            # Pending settlements
            if (
                db.query(Settlement)
                .filter(
                    Settlement.milestone_id.in_(m_ids),
                    Settlement.status.in_(
                        [
                            SettlementStatus.PREPARED,
                            SettlementStatus.PROCESSING,
                            SettlementStatus.PARTIALLY_SUCCEEDED,
                        ]
                    ),
                )
                .first()
            ):
                return
            # Pending transfers
            if (
                db.query(MoneyTransfer)
                .join(Settlement, MoneyTransfer.settlement_id == Settlement.id)
                .filter(
                    Settlement.milestone_id.in_(m_ids),
                    MoneyTransfer.status.in_(
                        [TransferStatus.READY, TransferStatus.PROCESSING, TransferStatus.UNKNOWN]
                    ),
                )
                .first()
            ):
                return
            # Open payment orders
            if (
                db.query(PaymentOrder)
                .filter(
                    PaymentOrder.milestone_id.in_(m_ids),
                    PaymentOrder.status.in_(
                        [
                            PaymentOrderStatus.CREATING,
                            PaymentOrderStatus.PENDING,
                            PaymentOrderStatus.PROCESSING,
                            PaymentOrderStatus.NEEDS_REVIEW,
                            PaymentOrderStatus.UNKNOWN,
                        ]
                    ),
                )
                .first()
            ):
                return
            # Open payment review cases
            if (
                db.query(PaymentReviewCase)
                .filter(
                    PaymentReviewCase.status.in_(
                        [PaymentReviewStatus.OPEN, PaymentReviewStatus.UNDER_REVIEW]
                    ),
                )
                .join(
                    PaymentTransaction,
                    PaymentReviewCase.payment_transaction_id == PaymentTransaction.id,
                )
                .join(PaymentOrder, PaymentTransaction.payment_order_id == PaymentOrder.id)
                .filter(PaymentOrder.milestone_id.in_(m_ids))
                .first()
            ):
                return

        now = _norm_utc(ctx.now_utc)

        # Pre-activation cancellation
        if contract.status in (ContractStatus.DRAFT, ContractStatus.PENDING_ACCEPTANCE):
            # Verify no funded guards or escrow
            if m_ids:
                has_guards = (
                    db.query(MilestoneFundingGuard)
                    .filter(MilestoneFundingGuard.milestone_id.in_(m_ids))
                    .first()
                )
                if has_guards:
                    return
                for esc in (
                    db.query(EscrowAccount).filter(EscrowAccount.milestone_id.in_(m_ids)).all()
                ):
                    if (
                        esc.funded_amount - esc.released_gross - esc.refunded_amount > 0
                    ) or esc.reserved_amount > 0:
                        return

            # Check whether pre-activation contract is eligible for cancellation:
            # Condition 1: The project itself is cancelled/closed,
            # AND no OFFERED version currently valid (deadline is None or deadline >= now)
            has_active_offered = (
                db.query(ContractVersion)
                .filter(
                    ContractVersion.contract_id == contract.id,
                    ContractVersion.status == ContractVersionStatus.OFFERED,
                    (
                        ContractVersion.acceptance_deadline.is_(None)
                        | (ContractVersion.acceptance_deadline >= now)
                    ),
                )
                .first()
                is not None
            )

            project_closed = False
            if project:
                project_closed = project.status in (ProjectStatus.CANCELLED, ProjectStatus.CLOSED)

            eligible_by_project = project_closed and not has_active_offered

            # Condition 2: Has >=1 version, ALL versions failed (DECLINED, WITHDRAWN, EXPIRED),
            # AND all milestones (if any) marked CANCELLED
            versions = db.query(ContractVersion).filter_by(contract_id=contract.id).all()
            has_versions = len(versions) > 0
            all_versions_failed = has_versions and all(
                v.status
                in (
                    ContractVersionStatus.DECLINED,
                    ContractVersionStatus.WITHDRAWN,
                    ContractVersionStatus.EXPIRED,
                )
                for v in versions
            )
            all_milestones_cancelled = (
                all(m.status == MilestoneStatus.CANCELLED for m in milestones)
                if milestones
                else True
            )
            eligible_by_versions_and_milestones = all_versions_failed and all_milestones_cancelled

            if not (eligible_by_project or eligible_by_versions_and_milestones):
                return

            contract.status = ContractStatus.CANCELLED
            contract.closed_at = now
            contract.closure_reason = "Cancelled before activation"

            budget = db.query(ProjectContractBudget).filter_by(contract_id=contract.id).first()
            if budget:
                budget.status = ContractBudgetStatus.RELEASED
                budget.released_at = now

            db.add(
                AuditLog(
                    actor_user_id=ctx.actor_user_id,
                    actor_type=ctx.actor_type,
                    action="contract.closed",
                    entity_type="freelance_contracts",
                    entity_id=contract.id,
                    reason=contract.closure_reason,
                    request_id=ctx.request_id,
                )
            )
            db.flush()
            return

        # Active contract closure
        if contract.status == ContractStatus.ACTIVE:
            if not contract.effective_version_id:
                return

            included_terms = (
                db.query(ContractMilestoneTerm)
                .filter(
                    ContractMilestoneTerm.contract_id == contract.id,
                    ContractMilestoneTerm.contract_version_id == contract.effective_version_id,
                    ContractMilestoneTerm.included.is_(True),
                )
                .all()
            )

            if not included_terms:
                return

            included_m_ids = {t.milestone_id for t in included_terms}
            active_ms = db.query(Milestone).filter(Milestone.id.in_(included_m_ids)).all()

            if len(active_ms) != len(included_m_ids):
                return

            terminal_statuses = {
                MilestoneStatus.PAID_OUT,
                MilestoneStatus.REFUNDED,
                MilestoneStatus.PARTIALLY_RELEASED,
                MilestoneStatus.CANCELLED,
            }

            for m in active_ms:
                if m.status not in terminal_statuses:
                    return

            # Verify no residual escrow held
            for esc in (
                db.query(EscrowAccount).filter(EscrowAccount.milestone_id.in_(included_m_ids)).all()
            ):
                if (
                    esc.funded_amount - esc.released_gross - esc.refunded_amount > 0
                ) or esc.reserved_amount > 0:
                    return

            all_paid_out = all(m.status == MilestoneStatus.PAID_OUT for m in active_ms)
            if all_paid_out:
                contract.status = ContractStatus.COMPLETED
                contract.closed_at = now
                contract.closure_reason = "All milestones paid out"
            else:
                contract.status = ContractStatus.TERMINATED
                contract.closed_at = now
                contract.closure_reason = "Contract terminated after partial release or refund"

            # Committed budget remains COMMITTED as per spec section 6.6
            db.add(
                AuditLog(
                    actor_user_id=ctx.actor_user_id,
                    actor_type=ctx.actor_type,
                    action="contract.closed",
                    entity_type="freelance_contracts",
                    entity_id=contract.id,
                    reason=contract.closure_reason,
                    request_id=ctx.request_id,
                )
            )
            db.flush()

    def get_project_closure_state(self, db: Session, *, project_id: int) -> ProjectClosureState:
        """Evaluate whether a multi-contract project satisfies all closure invariants."""
        project = db.get(FreelanceProject, project_id)
        if not project:
            raise NotFoundError("Project not found", code="NOT_FOUND")

        # 1. Contract counts
        rows = (
            db.query(FreelanceContract.status, func.count(FreelanceContract.id))
            .filter(FreelanceContract.project_id == project_id)
            .group_by(FreelanceContract.status)
            .all()
        )
        counts_map = {s.value if hasattr(s, "value") else str(s): cnt for s, cnt in rows}
        contract_counts = tuple(sorted(counts_map.items()))

        # 2. Check open obligations
        has_open = False

        # Open contracts check
        open_contracts_count = (
            db.query(FreelanceContract)
            .filter(
                FreelanceContract.project_id == project_id,
                FreelanceContract.status.in_(
                    [ContractStatus.DRAFT, ContractStatus.PENDING_ACCEPTANCE, ContractStatus.ACTIVE]
                ),
            )
            .count()
        )
        if open_contracts_count > 0:
            has_open = True

        c_ids = [
            c.id for c in db.query(FreelanceContract.id).filter_by(project_id=project_id).all()
        ]
        if c_ids:
            m_ids = [
                m.id for m in db.query(Milestone.id).filter(Milestone.contract_id.in_(c_ids)).all()
            ]
            if m_ids:
                terminal_m = [
                    MilestoneStatus.PAID_OUT,
                    MilestoneStatus.REFUNDED,
                    MilestoneStatus.PARTIALLY_RELEASED,
                    MilestoneStatus.CANCELLED,
                ]
                non_terminal_count = (
                    db.query(Milestone)
                    .filter(
                        Milestone.id.in_(m_ids),
                        ~Milestone.status.in_(terminal_m),
                    )
                    .count()
                )
                if non_terminal_count > 0:
                    has_open = True

                if (
                    db.query(ActiveMilestoneDispute)
                    .filter(ActiveMilestoneDispute.milestone_id.in_(m_ids))
                    .count()
                    > 0
                ):
                    has_open = True

                if (
                    db.query(MilestoneHold)
                    .filter(
                        MilestoneHold.milestone_id.in_(m_ids), MilestoneHold.released_at.is_(None)
                    )
                    .count()
                    > 0
                ):
                    has_open = True

                for esc in (
                    db.query(EscrowAccount).filter(EscrowAccount.milestone_id.in_(m_ids)).all()
                ):
                    if (
                        esc.funded_amount - esc.released_gross - esc.refunded_amount > 0
                    ) or esc.reserved_amount > 0:
                        has_open = True
                        break

                if (
                    db.query(Settlement)
                    .filter(
                        Settlement.milestone_id.in_(m_ids),
                        Settlement.status.in_(
                            [
                                SettlementStatus.PREPARED,
                                SettlementStatus.PROCESSING,
                                SettlementStatus.PARTIALLY_SUCCEEDED,
                            ]
                        ),
                    )
                    .count()
                    > 0
                ):
                    has_open = True

                if (
                    db.query(MoneyTransfer)
                    .join(Settlement, MoneyTransfer.settlement_id == Settlement.id)
                    .filter(
                        Settlement.milestone_id.in_(m_ids),
                        MoneyTransfer.status.in_(
                            [
                                TransferStatus.READY,
                                TransferStatus.PROCESSING,
                                TransferStatus.UNKNOWN,
                            ]
                        ),
                    )
                    .count()
                    > 0
                ):
                    has_open = True

                if (
                    db.query(PaymentOrder)
                    .filter(
                        PaymentOrder.milestone_id.in_(m_ids),
                        PaymentOrder.status.in_(
                            [
                                PaymentOrderStatus.CREATING,
                                PaymentOrderStatus.PENDING,
                                PaymentOrderStatus.PROCESSING,
                                PaymentOrderStatus.NEEDS_REVIEW,
                                PaymentOrderStatus.UNKNOWN,
                            ]
                        ),
                    )
                    .count()
                    > 0
                ):
                    has_open = True

                if (
                    db.query(PaymentReviewCase)
                    .filter(
                        PaymentReviewCase.status.in_(
                            [PaymentReviewStatus.OPEN, PaymentReviewStatus.UNDER_REVIEW]
                        ),
                    )
                    .join(
                        PaymentTransaction,
                        PaymentReviewCase.payment_transaction_id == PaymentTransaction.id,
                    )
                    .join(PaymentOrder, PaymentTransaction.payment_order_id == PaymentOrder.id)
                    .filter(PaymentOrder.milestone_id.in_(m_ids))
                    .count()
                    > 0
                ):
                    has_open = True

        # 3. Determine eligible terminal status
        eligible: ProjectStatus | None = None
        if project.recruitment_status == RecruitmentStatus.CLOSED and not has_open:
            contracts = db.query(FreelanceContract).filter_by(project_id=project_id).all()
            completed_count = sum(1 for c in contracts if c.status == ContractStatus.COMPLETED)
            terminated_count = sum(1 for c in contracts if c.status == ContractStatus.TERMINATED)

            if terminated_count > 0:
                eligible = ProjectStatus.CLOSED
            elif completed_count > 0:
                eligible = ProjectStatus.COMPLETED
            else:
                eligible = ProjectStatus.CANCELLED

        return ProjectClosureState(
            project_id=project.id,
            recruitment_status=RecruitmentStatus(project.recruitment_status),
            contract_counts=contract_counts,
            has_open_obligations=has_open,
            eligible_terminal_status=eligible,
        )

    def recompute_project_closure_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        project_id: int,
    ) -> None:
        """Apply eligible project terminal transition in-transaction."""
        _for_update(db.query(FreelanceProject).filter_by(id=project_id), db).first()
        _for_update(
            db.query(FreelanceContract)
            .filter_by(project_id=project_id)
            .order_by(FreelanceContract.id.asc()),
            db,
        ).all()

        state = self.get_project_closure_state(db, project_id=project_id)
        if state.eligible_terminal_status is not None:
            project = db.get(FreelanceProject, project_id)
            if project and project.status not in (
                ProjectStatus.COMPLETED,
                ProjectStatus.CLOSED,
                ProjectStatus.CANCELLED,
                ProjectStatus.REJECTED,
            ):
                now = _norm_utc(ctx.now_utc)
                project.status = state.eligible_terminal_status
                project.closed_at = now

                db.add(
                    AuditLog(
                        actor_user_id=ctx.actor_user_id,
                        actor_type=ctx.actor_type,
                        action="project.closed",
                        entity_type="freelance_projects",
                        entity_id=project.id,
                        reason=f"Closed with status {state.eligible_terminal_status}",
                        request_id=ctx.request_id,
                    )
                )
                db.flush()

    def recompute_contract_closure(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
    ) -> None:
        run_command(
            db, lambda: self.recompute_contract_closure_in_tx(db, ctx=ctx, contract_id=contract_id)
        )

    def recompute_project_closure(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        project_id: int,
    ) -> None:
        run_command(
            db, lambda: self.recompute_project_closure_in_tx(db, ctx=ctx, project_id=project_id)
        )

    def cancel_draft_contract_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
        reason: str | None = None,
    ) -> None:
        """Explicitly cancel a DRAFT or PENDING_ACCEPTANCE contract before activation."""
        from app.services.freelance_contract_service import _lock_contract_hierarchy

        _, contract, budget, _, milestones = _lock_contract_hierarchy(
            db,
            contract_id=contract_id,
            lock_milestones=True,
        )
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        # Zero-leak check: only project client or student or system/admin
        student = (
            db.get(Student, contract.freelancer_student_id)
            if contract.freelancer_student_id
            else None
        )
        allowed_users = {contract.client_user_id}
        if student:
            allowed_users.add(student.user_id)
        if ctx.actor_type != ActorType.SYSTEM and ctx.actor_user_id not in allowed_users:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        if contract.status not in (ContractStatus.DRAFT, ContractStatus.PENDING_ACCEPTANCE):
            raise ConflictError(
                "Only draft or pending contracts can be cancelled pre-activation",
                code="INVALID_STATE_TRANSITION",
            )

        m_ids = [m.id for m in milestones]
        if m_ids:
            if (
                db.query(PaymentOrder)
                .filter(
                    PaymentOrder.milestone_id.in_(m_ids),
                    PaymentOrder.status.in_(
                        [
                            PaymentOrderStatus.CREATING,
                            PaymentOrderStatus.PENDING,
                            PaymentOrderStatus.PROCESSING,
                            PaymentOrderStatus.UNKNOWN,
                            PaymentOrderStatus.NEEDS_REVIEW,
                            PaymentOrderStatus.PAID,
                        ]
                    ),
                )
                .first()
            ):
                raise ConflictError(
                    "Payment must be reconciled before cancellation", code="TERMS_IMMUTABLE"
                )
            has_guards = (
                db.query(MilestoneFundingGuard)
                .filter(MilestoneFundingGuard.milestone_id.in_(m_ids))
                .first()
            )
            if has_guards:
                raise ConflictError(
                    "Cannot cancel contract with guarded milestones", code="TERMS_IMMUTABLE"
                )
            for esc in db.query(EscrowAccount).filter(EscrowAccount.milestone_id.in_(m_ids)).all():
                if (
                    esc.funded_amount - esc.released_gross - esc.refunded_amount > 0
                ) or esc.reserved_amount > 0:
                    raise ConflictError(
                        "Cannot cancel contract with funded escrow", code="TERMS_IMMUTABLE"
                    )

        now = _norm_utc(ctx.now_utc)
        contract.status = ContractStatus.CANCELLED
        contract.closed_at = now
        contract.closure_reason = reason or "Cancelled draft contract"

        for version in (
            db.query(ContractVersion)
            .filter(
                ContractVersion.contract_id == contract.id,
                ContractVersion.status.in_(
                    [ContractVersionStatus.DRAFT, ContractVersionStatus.OFFERED]
                ),
            )
            .all()
        ):
            version.status = ContractVersionStatus.WITHDRAWN

        # Cancel unstarted milestones
        for m in milestones:
            if m.status == MilestoneStatus.NOT_FUNDED:
                m.status = MilestoneStatus.CANCELLED

        # Release reserved budget
        if budget:
            budget.status = ContractBudgetStatus.RELEASED
            budget.released_at = now

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract.closed",
                entity_type="freelance_contracts",
                entity_id=contract.id,
                reason=contract.closure_reason,
                request_id=ctx.request_id,
            )
        )
        db.flush()

    def cancel_draft_contract(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
        reason: str | None = None,
    ) -> None:
        """Atomic command runner for cancelling a draft contract."""
        run_command(
            db,
            lambda: self.cancel_draft_contract_in_tx(
                db, ctx=ctx, contract_id=contract_id, reason=reason
            ),
        )
