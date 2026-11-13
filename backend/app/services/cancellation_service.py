"""Cancellation proposals are immutable; finance is the sole settlement writer."""

from sqlalchemy import select

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.freelancer_enums import CancellationStatus, MilestoneStatus
from app.models import (
    ActiveMilestoneDispute,
    CancellationAgreement,
    ContractMilestoneTerm,
    ContractVersion,
    FreelanceContract,
    Milestone,
    MilestoneFundingGuard,
    PaymentOrder,
    Settlement,
    Student,
)
from app.services.freelancer_accounts.common import as_naive_utc
from app.services.freelancer_domain import audit, ctx, lock, milestone_scope, notify, now, record
from app.services.freelancer_finance import get_finance_port
from app.utils.hashing import sha256_json


def create_in_tx(db, *, user_id, milestone_id, payload):
    p, c, m, e = milestone_scope(db, milestone_id, user_id)
    if m.status in (
        "PAID_OUT",
        "REFUNDED",
        "PARTIALLY_RELEASED",
        "CANCELLED",
        "SETTLEMENT_PENDING",
        "ACCEPTED",
        "DISPUTED",
    ):
        raise ConflictError("Milestone cannot be cancelled")
    if db.get(ActiveMilestoneDispute, m.id):
        raise ConflictError("Resolve the dispute first")
    if e and (e.reserved_amount or e.released_gross or e.refunded_amount):
        raise ConflictError("Funds already reserved or settled", code="FUNDS_RESERVED")
    if db.scalar(
        select(CancellationAgreement.id).where(
            CancellationAgreement.milestone_id == m.id,
            CancellationAgreement.status.in_(["PROPOSED", "ACCEPTED"]),
        )
    ):
        raise ConflictError("A cancellation is already pending")
    term = db.get(ContractMilestoneTerm, m.effective_terms_id) if m.effective_terms_id else None
    version = db.get(ContractVersion, term.contract_version_id) if term else None
    policy = (version.terms_json or {}).get("cancellation_policy", {}) if version else {}
    funded = e.funded_amount if e else 0
    if payload.freelancer_gross + payload.refund_amount != funded:
        raise BadRequestError("Cancellation amounts must equal remaining funded money")
    # Once real money is held in escrow, neither party may unilaterally cancel.
    # They must either agree on a MUTUAL split/refund or ask an administrator to
    # resolve a dispute.  This prevents a signed policy flag from silently
    # moving money after funding.
    if funded and payload.basis != "MUTUAL":
        raise ConflictError(
            "Funded milestones require mutual cancellation or an administrator dispute"
        )
    if not e:
        if db.get(MilestoneFundingGuard, m.id) or db.scalar(
            select(PaymentOrder.id).where(
                PaymentOrder.milestone_id == m.id,
                PaymentOrder.status.in_(
                    ["CREATING", "PENDING", "PROCESSING", "PAID", "UNKNOWN", "NEEDS_REVIEW"]
                ),
            )
        ):
            raise ConflictError("Reconcile payment before cancellation")
        if m.status != MilestoneStatus.NOT_FUNDED:
            raise ConflictError("Unfunded milestone state is inconsistent")
    unilateral = False
    if payload.basis != "MUTUAL":
        if user_id != c.client_user_id:
            raise ForbiddenError("Only the client may invoke this contractual cancellation clause")
        if payload.freelancer_gross or payload.refund_amount != funded:
            raise BadRequestError("Unilateral cancellation requires a full refund")
        if payload.basis == "BEFORE_START":
            unilateral = (
                (policy.get("allow_before_start") is True)
                and m.started_at is None
                and m.status in ("NOT_FUNDED", "FUNDED")
            )
        else:
            from datetime import timedelta

            unilateral = (
                (policy.get("allow_overdue") is True)
                and term is not None
                and version is not None
                and now()
                > as_naive_utc(term.due_at) + timedelta(seconds=version.grace_period_seconds)
                and m.status in ("FUNDED", "IN_PROGRESS", "REVISION_REQUESTED")
            )
        if not unilateral:
            raise ConflictError(
                "The signed contract does not permit unilateral cancellation in this state"
            )
    snapshot = {
        "contract_version_id": version.id if version else None,
        "terms_id": m.effective_terms_id,
        "cancellation_policy": policy,
        "milestone_status": m.status.value if hasattr(m.status, "value") else m.status,
        "funded_amount": str(funded),
        "unilateral": unilateral,
    }
    hashed = sha256_json(
        {"milestone_id": m.id, **payload.model_dump(mode="json"), "policy": snapshot}
    )
    row = CancellationAgreement(
        milestone_id=m.id,
        requested_by=user_id,
        **payload.model_dump(),
        terms_hash=hashed,
        policy_snapshot=snapshot,
    )
    if unilateral:
        row.status = CancellationStatus.ACCEPTED
    elif user_id == c.client_user_id:
        row.client_accepted_at = now()
    else:
        row.freelancer_accepted_at = now()
    db.add(row)
    db.flush()
    audit(db, user_id, "cancellation.proposed", "cancellation_agreements", row.id)
    student = db.get(Student, c.freelancer_student_id)
    other_user_id = student.user_id if user_id == c.client_user_id and student else c.client_user_id
    notify(
        db,
        other_user_id,
        "Đề nghị hủy mốc công việc",
        "Đối tác đã gửi một đề nghị hủy và phân chia khoản ký quỹ. Vui lòng xem và phản hồi.",
        ref_type="FREELANCE_MILESTONE",
        ref_id=m.id,
    )
    return record(row)


def scope(db, cancellation_id, user_id):
    raw = db.get(CancellationAgreement, cancellation_id)
    if not raw:
        raise NotFoundError("Cancellation not found")
    p, c, m, e = milestone_scope(db, raw.milestone_id, user_id)
    return p, c, m, e, lock(db, CancellationAgreement, id=raw.id)


def action_in_tx(db, *, user_id, cancellation_id, action, content_hash=None):
    p, c, m, e, row = scope(db, cancellation_id, user_id)
    if row.status != CancellationStatus.PROPOSED:
        raise ConflictError("Cancellation is not proposed")
    if action == "withdraw":
        if row.requested_by != user_id:
            raise ForbiddenError("Only proposer may withdraw")
        row.status = CancellationStatus.WITHDRAWN
    elif action == "reject":
        if row.requested_by == user_id:
            raise ForbiddenError("Proposer must withdraw instead")
        row.status = CancellationStatus.REJECTED
    else:
        if row.terms_hash != content_hash:
            raise ConflictError("Cancellation hash mismatch")
        if user_id == c.client_user_id:
            if row.client_accepted_at:
                raise ConflictError("Already accepted")
            row.client_accepted_at = now()
        else:
            if row.freelancer_accepted_at:
                raise ConflictError("Already accepted")
            row.freelancer_accepted_at = now()
        if row.client_accepted_at and row.freelancer_accepted_at:
            row.status = CancellationStatus.ACCEPTED
    audit(db, user_id, "cancellation." + action, "cancellation_agreements", row.id)
    student = db.get(Student, c.freelancer_student_id)
    other_user_id = student.user_id if user_id == c.client_user_id and student else c.client_user_id
    notify(
        db,
        other_user_id,
        "Cập nhật đề nghị hủy mốc",
        {
            "accept": "Đối tác đã đồng ý đề nghị hủy.",
            "reject": "Đối tác đã từ chối đề nghị hủy.",
            "withdraw": "Đối tác đã rút đề nghị hủy.",
        }.get(action, "Đề nghị hủy vừa được cập nhật."),
        ref_type="FREELANCE_MILESTONE",
        ref_id=m.id,
    )
    return record(row)


def execute_in_tx(db, *, user_id, cancellation_id, finance=None):
    p, c, m, e, row = scope(db, cancellation_id, user_id)
    if row.status != CancellationStatus.ACCEPTED:
        raise ConflictError("Cancellation is not accepted")
    if db.get(ActiveMilestoneDispute, m.id):
        raise ConflictError("Dispute blocks cancellation")
    from app.models import MilestoneHold

    if db.scalar(
        select(MilestoneHold.id).where(
            MilestoneHold.milestone_id == m.id, MilestoneHold.released_at.is_(None)
        )
    ):
        raise ConflictError("Funds are held", code="FUNDS_ON_HOLD")
    if not e:
        if db.get(MilestoneFundingGuard, m.id) or db.scalar(
            select(PaymentOrder.id).where(
                PaymentOrder.milestone_id == m.id,
                PaymentOrder.status.in_(
                    ["CREATING", "PENDING", "PROCESSING", "PAID", "UNKNOWN", "NEEDS_REVIEW"]
                ),
            )
        ):
            raise ConflictError("Reconcile payment first")
        if m.status != MilestoneStatus.NOT_FUNDED:
            raise ConflictError("Milestone state changed")
        m.status = MilestoneStatus.CANCELLED
        row.status = CancellationStatus.EXECUTED
        row.executed_at = now()
        from app.services.freelance_closure_service import FreelanceClosureService

        db.flush()
        closure = FreelanceClosureService()
        closure.recompute_contract_closure_in_tx(db, ctx=ctx(user_id), contract_id=c.id)
        closure.recompute_project_closure_in_tx(db, ctx=ctx(user_id), project_id=p.id)
        audit(db, user_id, "cancellation.executed", "cancellation_agreements", row.id)
        student = db.get(Student, c.freelancer_student_id)
        for recipient_id in filter(None, (c.client_user_id, student.user_id if student else None)):
            notify(
                db,
                recipient_id,
                "Mốc công việc đã được hủy",
                "Thỏa thuận hủy đã hoàn tất.",
                ref_type="FREELANCE_MILESTONE",
                ref_id=m.id,
            )
        return record(row)
    if e.reserved_amount or e.released_gross or e.refunded_amount:
        raise ConflictError("Funds already reserved or settled")
    result = (finance or get_finance_port()).prepare_cancellation_settlement_in_tx(
        db, ctx=ctx(user_id), cancellation_id=row.id
    )
    # ACCEPTED remains until finance confirms success; no fake EXECUTED state.
    return {
        "cancellation_id": str(row.id),
        "settlement_id": str(result.settlement_id),
        "status": "ACCEPTED",
    }


def reconcile_in_tx(db, *, cancellation_id):
    row = lock(db, CancellationAgreement, id=cancellation_id)
    if not row:
        return
    settlement = db.scalar(select(Settlement).where(Settlement.source_cancellation_id == row.id))
    if row.status == "ACCEPTED" and settlement and settlement.status == "SUCCEEDED":
        row.status = CancellationStatus.EXECUTED
        row.executed_at = now()
        audit(db, None, "cancellation.executed", "cancellation_agreements", row.id)
        milestone = db.get(Milestone, row.milestone_id)
        contract = db.get(FreelanceContract, milestone.contract_id)
        student = db.get(Student, contract.freelancer_student_id)
        for recipient_id in filter(None, (contract.client_user_id, student.user_id if student else None)):
            notify(
                db,
                recipient_id,
                "Hoàn tiền/hủy mốc đã hoàn tất",
                "Khoản tiền theo thỏa thuận hủy đã được xử lý thành công.",
                ref_type="FREELANCE_MILESTONE",
                ref_id=milestone.id,
            )


def propose_command_in_tx(db, *, user_id, milestone_id, payload, key):
    from app.services.freelancer_domain import replay

    milestone_scope(db, milestone_id, user_id)
    return replay(
        db,
        actor_id=user_id,
        operation="freelance.propose_cancellation",
        key=key,
        body={"milestone_id": str(milestone_id), **payload.model_dump(mode="json")},
        action=lambda: create_in_tx(
            db, user_id=user_id, milestone_id=milestone_id, payload=payload
        ),
    )
