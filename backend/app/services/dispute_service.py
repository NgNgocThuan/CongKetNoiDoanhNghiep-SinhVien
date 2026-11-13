"""Group D disputes. Only finance owns escrow, settlement and terminal money states."""

from datetime import timedelta

from sqlalchemy import select

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.freelancer_enums import (
    DisputeDecisionStatus,
    DisputeStatus,
    HoldReason,
    MilestoneStatus,
    ScheduledJobStatus,
    SettlementStatus,
)
from app.models import (
    ActiveMilestoneDispute,
    ClientProfile,
    Company,
    ContractMilestoneTerm,
    ContractVersion,
    Deliverable,
    Dispute,
    DisputeDecision,
    DisputeEvidence,
    DisputeWithdrawal,
    Milestone,
    MilestoneHold,
    ScheduledJob,
    Settlement,
    Student,
    User,
)
from app.services.freelancer_accounts.identity_service import checked_file
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import (
    admin,
    audit,
    ctx,
    lock,
    milestone_scope,
    now,
    page,
    record,
)
from app.services.freelancer_finance import get_finance_port
from app.services.freelancer_policy_service import read_policy
from app.services.milestone_hold_service import MilestoneHoldService
from app.utils.hashing import sha256_json

OPEN = (
    DisputeStatus.OPEN,
    DisputeStatus.EVIDENCE_COLLECTION,
    DisputeStatus.UNDER_REVIEW,
    DisputeStatus.ESCALATED,
)


def scope(db, dispute_id, user_id, *, admin_only=False):
    d = db.get(Dispute, dispute_id)
    if not d:
        raise NotFoundError("Dispute not found")
    if admin_only:
        admin(db, user_id)
    p, c, m, e = milestone_scope(db, d.milestone_id, user_id, allow_admin=admin_only)
    return p, c, m, e, lock(db, Dispute, id=d.id)


def _unreserved(e):
    if not e or e.reserved_amount or e.released_gross or e.refunded_amount:
        raise ConflictError("Funds have already been reserved or settled", code="FUNDS_RESERVED")


def open_in_tx(db, *, user_id, milestone_id, payload, finance=None):
    p, c, m, e = milestone_scope(db, milestone_id, user_id)
    # A funded milestone may need administrator intervention even before work
    # starts (for example, when the other party ignores a mutual cancellation).
    # Financial checks below still require the full escrow to be held and
    # untouched, so unfunded or already-settled milestones remain ineligible.
    if m.status not in (
        MilestoneStatus.FUNDED,
        MilestoneStatus.IN_PROGRESS,
        MilestoneStatus.SUBMITTED,
        MilestoneStatus.REVISION_REQUESTED,
    ):
        raise ConflictError("Milestone is not disputable")
    if db.get(ActiveMilestoneDispute, m.id):
        raise ConflictError("A dispute is already active")
    _unreserved(e)
    (finance or get_finance_port()).assert_disputable_in_tx(db, ctx=ctx(user_id), milestone_id=m.id)
    policy, rev = read_policy(db)
    term = db.get(ContractMilestoneTerm, m.effective_terms_id) if m.effective_terms_id else None
    version = db.get(ContractVersion, term.contract_version_id) if term else None
    evidence_seconds = (
        (version.terms_json or {}).get("evidence_period_seconds", policy.evidence_period_seconds)
        if version
        else policy.evidence_period_seconds
    )
    at = now()
    if m.status == MilestoneStatus.SUBMITTED and m.review_deadline and m.review_deadline <= at:
        raise ConflictError("Review period has elapsed")
    remaining = max(0, int((m.review_deadline - at).total_seconds())) if m.review_deadline else None
    d = Dispute(
        milestone_id=m.id,
        opened_by=user_id,
        reason_code=payload.reason_code,
        description=payload.description,
        previous_milestone_status=m.status,
        remaining_review_seconds=remaining,
        evidence_deadline=at + timedelta(seconds=evidence_seconds),
        status=DisputeStatus.EVIDENCE_COLLECTION,
    )
    db.add(d)
    db.flush()
    db.add(ActiveMilestoneDispute(milestone_id=m.id, dispute_id=d.id))
    MilestoneHoldService().place_hold_in_tx(
        db,
        ctx=ctx(user_id),
        milestone_id=m.id,
        reason_type="DISPUTE",
        reason_key=f"dispute:{d.id}",
        dispute_id=d.id,
        note=payload.description,
    )
    m.status = MilestoneStatus.DISPUTED
    m.review_deadline = None
    for j in db.scalars(
        select(ScheduledJob).where(
            ScheduledJob.entity_type == "milestones",
            ScheduledJob.entity_id == m.id,
            ScheduledJob.job_type == "milestone.auto_accept",
            ScheduledJob.status.in_(["PENDING", "RETRY"]),
        )
    ).all():
        j.status = ScheduledJobStatus.CANCELLED
    db.add(
        ScheduledJob(
            job_key=f"dispute.evidence_deadline:{d.id}",
            job_type="dispute.evidence_deadline",
            entity_type="disputes",
            entity_id=d.id,
            run_at=d.evidence_deadline,
            payload_json={"dispute_id": d.id},
        )
    )
    audit(db, user_id, "dispute.opened", "disputes", d.id, after={"policy_revision": rev})
    from app.services.freelancer_domain import notify, notify_admins

    freelancer = db.get(Student, c.freelancer_student_id)
    other_user_id = freelancer.user_id if user_id == c.client_user_id and freelancer else c.client_user_id
    notify(
        db,
        other_user_id,
        "Một tranh chấp Freelancer đã được mở",
        payload.description,
        ref_type="FREELANCE_DISPUTE",
        ref_id=d.id,
    )
    notify_admins(
        db,
        "Tranh chấp Freelancer mới cần xử lý",
        payload.description,
        ref_type="FREELANCE_DISPUTE",
        ref_id=d.id,
    )
    db.flush()
    return record(d)


def evidence_in_tx(db, *, user_id, dispute_id, payload, late_reason=None):
    _, c, m, e, d = scope(db, dispute_id, user_id, admin_only=bool(late_reason))
    if d.status not in OPEN:
        raise ConflictError("Dispute is closed")
    final_decision = db.scalar(
        select(DisputeDecision.id).where(
            DisputeDecision.dispute_id == d.id,
            DisputeDecision.status.in_(("APPROVED", "EXECUTING", "EXECUTED")),
        )
    )
    if final_decision:
        raise ConflictError("An administrator decision has already closed evidence collection")
    if now() > d.evidence_deadline and not late_reason:
        raise ConflictError("Evidence deadline has passed")
    if not (payload.file_id or payload.deliverable_id or (payload.note and payload.note.strip())):
        raise BadRequestError("Evidence is empty")
    if payload.file_id:
        checked_file(db, payload.file_id, user_id)
    if payload.deliverable_id:
        delivery = db.get(Deliverable, payload.deliverable_id)
        if not delivery or delivery.milestone_id != m.id:
            raise NotFoundError("Deliverable not found")
    evidence = DisputeEvidence(dispute_id=d.id, submitted_by=user_id, **payload.model_dump())
    db.add(evidence)
    db.flush()
    audit(
        db, user_id, "dispute.evidence_added", "dispute_evidence", evidence.id, reason=late_reason
    )
    return record(evidence)


def get_dispute(db, *, user_id, dispute_id, is_admin=False):
    _, c, m, e, d = scope(db, dispute_id, user_id, admin_only=is_admin)
    data = record(d)
    # Evidence bodies are only returned through a separately paginated endpoint.
    return data


def list_disputes(db, *, user_id, number=1, size=20):
    admin(db, user_id)
    return page(db, select(Dispute).order_by(Dispute.id.desc()), number, size)


def evidence_list(db, *, user_id, dispute_id, number=1, size=20, is_admin=False):
    scope(db, dispute_id, user_id, admin_only=is_admin)
    result = page(
        db,
        select(DisputeEvidence)
        .where(DisputeEvidence.dispute_id == dispute_id)
        .order_by(DisputeEvidence.id),
        number,
        size,
    )
    ids = [int(item["submitted_by"]) for item in result["items"]]
    users = {u.id: u for u in db.scalars(select(User).where(User.id.in_(ids)))}
    names = {}
    for model, name_column in ((Student, "full_name"), (Company, "name"), (ClientProfile, "full_name")):
        for profile in db.scalars(select(model).where(model.user_id.in_(ids))):
            names[profile.user_id] = getattr(profile, name_column)
    labels = {"STUDENT": "Sinh viên", "COMPANY": "Nhà tuyển dụng", "CLIENT": "Người thuê", "ADMIN": "Quản trị viên"}
    for item in result["items"]:
        sender = users.get(int(item["submitted_by"]))
        item["submitted_by_name"] = names.get(sender.id) or sender.email if sender else "Tài khoản đã ngừng hoạt động"
        item["submitted_by_role_label"] = labels.get(sender.role, "Người dùng") if sender else "Người dùng"
    return result


def assign_in_tx(db, *, user_id, dispute_id, admin_id):
    admin(db, admin_id)
    *_, d = scope(db, dispute_id, user_id, admin_only=True)
    if d.status not in OPEN:
        raise ConflictError("Dispute is closed")
    d.assigned_admin_id = admin_id
    d.status = DisputeStatus.UNDER_REVIEW
    audit(db, user_id, "dispute.assigned", "disputes", d.id, after={"admin_id": str(admin_id)})
    return record(d)


def _no_decision(db, d):
    if db.scalar(
        select(DisputeDecision.id).where(
            DisputeDecision.dispute_id == d.id,
            DisputeDecision.status.in_(["APPROVED", "EXECUTING", "EXECUTED"]),
        )
    ):
        raise ConflictError("An approved decision requires administrator handling")


def request_withdrawal_in_tx(db, *, user_id, dispute_id, reason):
    *_, d = scope(db, dispute_id, user_id)
    if d.status not in OPEN:
        raise ConflictError("Dispute is closed")
    _no_decision(db, d)
    if db.scalar(select(DisputeWithdrawal.id).where(DisputeWithdrawal.dispute_id == d.id)):
        raise ConflictError("Withdrawal already requested")
    hashed = sha256_json({"dispute_id": d.id, "requested_by": user_id, "reason": reason})
    row = DisputeWithdrawal(
        dispute_id=d.id, requested_by=user_id, reason=reason, terms_hash=hashed, created_at=now()
    )
    db.add(row)
    db.flush()
    audit(db, user_id, "dispute.withdrawal_requested", "dispute_withdrawals", row.id)
    return record(row)


def confirm_withdrawal_in_tx(db, *, user_id, dispute_id, content_hash):
    p, c, m, e, d = scope(db, dispute_id, user_id)
    if d.status not in OPEN:
        raise ConflictError("Dispute is closed")
    _no_decision(db, d)
    _unreserved(e)
    w = lock(db, DisputeWithdrawal, dispute_id=d.id)
    if not w:
        raise NotFoundError("Withdrawal request not found")
    if w.requested_by == user_id:
        raise ForbiddenError("The other contract party must confirm")
    if w.terms_hash != content_hash:
        raise ConflictError("Withdrawal hash mismatch")
    w.confirmed_by = user_id
    w.confirmed_at = now()
    d.status = DisputeStatus.WITHDRAWN
    d.withdrawal_note = w.reason
    d.resolved_at = now()
    for h in db.scalars(
        select(MilestoneHold).where(
            MilestoneHold.dispute_id == d.id,
            MilestoneHold.reason_type == HoldReason.DISPUTE,
            MilestoneHold.released_at.is_(None),
        )
    ).all():
        h.released_at = now()
        h.released_by = user_id
        h.release_note = w.reason
    guard = db.get(ActiveMilestoneDispute, m.id)
    if guard:
        db.delete(guard)
    m.status = d.previous_milestone_status
    if m.status == MilestoneStatus.SUBMITTED:
        m.review_deadline = now() + timedelta(seconds=max(d.remaining_review_seconds or 0, 1))
        latest = db.scalar(
            select(Deliverable)
            .where(Deliverable.milestone_id == m.id)
            .order_by(Deliverable.submission_no.desc())
        )
        if latest:
            db.add(
                ScheduledJob(
                    job_key=f"milestone.auto_accept:{m.id}:resume:{d.id}",
                    job_type="milestone.auto_accept",
                    entity_type="milestones",
                    entity_id=m.id,
                    run_at=m.review_deadline,
                    payload_json={
                        "milestone_id": m.id,
                        "deliverable_id": latest.id,
                        "submission_no": latest.submission_no,
                    },
                )
            )
    audit(db, user_id, "dispute.withdrawn", "disputes", d.id, reason=w.reason)
    return record(d)


def decision_in_tx(db, *, user_id, dispute_id, payload):
    p, c, m, e, d = scope(db, dispute_id, user_id, admin_only=True)
    if d.status not in OPEN:
        raise ConflictError("Dispute is closed")
    if user_id == c.client_user_id:
        raise ForbiddenError("Cannot decide own contract")
    _unreserved(e)
    if now() < d.evidence_deadline:
        raise ConflictError("Collect evidence before deciding")
    if payload.freelancer_gross + payload.refund_amount != e.funded_amount:
        raise BadRequestError("Decision must cover the unsettled amount")
    g, r = payload.freelancer_gross, payload.refund_amount
    if not (
        (payload.outcome == "PAYOUT" and g > 0 and r == 0)
        or (payload.outcome == "REFUND" and g == 0 and r > 0)
        or (payload.outcome == "SPLIT" and g > 0 and r > 0)
    ):
        raise BadRequestError("Decision outcome/amount mismatch")
    previous = db.scalars(select(DisputeDecision).where(DisputeDecision.dispute_id == d.id)).all()
    if any(x.status in ("APPROVED", "EXECUTING", "EXECUTED") for x in previous):
        raise ConflictError("An approved decision already exists")
    for x in previous:
        if x.status == "PROPOSED":
            x.status = DisputeDecisionStatus.SUPERSEDED
    policy, rev = read_policy(db)
    row = DisputeDecision(
        dispute_id=d.id,
        revision_no=max((x.revision_no for x in previous), default=0) + 1,
        **payload.model_dump(),
        proposed_by=user_id,
        approval_threshold_snapshot=policy.second_approval_threshold,
        # One school administrator has full authority to resolve a dispute.
        # Snapshot columns remain for audit and backward compatibility.
        requires_second_approval=False,
        status=DisputeDecisionStatus.APPROVED,
        approved_at=now(),
    )
    db.add(row)
    db.flush()
    d.status = DisputeStatus.UNDER_REVIEW
    audit(
        db,
        user_id,
        "dispute.decision_created",
        "dispute_decisions",
        row.id,
        after={"policy_revision": rev},
    )
    from app.services.freelancer_domain import notify

    student = db.get(Student, c.freelancer_student_id)
    for recipient_id in filter(None, (c.client_user_id, student.user_id if student else None)):
        notify(
            db,
            recipient_id,
            "Admin đã ra quyết định tranh chấp",
            "Quyết định phân chia tiền cho tranh chấp Freelancer đã được ghi nhận và đang được thực thi.",
            ref_type="FREELANCE_DISPUTE",
            ref_id=d.id,
        )
    return record(row)


def approve_decision_in_tx(db, *, user_id, decision_id, approve, reason):
    raw = db.get(DisputeDecision, decision_id)
    if not raw:
        raise NotFoundError("Decision not found")
    p, c, m, e, d = scope(db, raw.dispute_id, user_id, admin_only=True)
    row = lock(db, DisputeDecision, id=decision_id)
    if row.status != "PROPOSED":
        raise ConflictError("Decision is not awaiting approval")
    if d.status not in OPEN:
        raise ConflictError("Dispute is closed")
    _unreserved(e)
    row.status = DisputeDecisionStatus.APPROVED if approve else DisputeDecisionStatus.REJECTED
    if approve:
        # Legacy PROPOSED rows may be confirmed by their original admin. The
        # historical DB constraint disallows proposed_by == approved_by, while
        # the audit log still records who confirmed the row.
        row.approved_by = None if row.proposed_by == user_id else user_id
        row.approved_at = now()
    audit(db, user_id, "dispute.decision_reviewed", "dispute_decisions", row.id, reason=reason)
    return record(row)


def execute_decision_in_tx(db, *, user_id, decision_id, finance=None):
    raw = db.get(DisputeDecision, decision_id)
    if not raw:
        raise NotFoundError("Decision not found")
    p, c, m, e, d = scope(db, raw.dispute_id, user_id, admin_only=True)
    row = lock(db, DisputeDecision, id=decision_id)
    if row.status != "APPROVED":
        raise ConflictError("Only approved decisions may execute")
    other = db.scalar(
        select(MilestoneHold.id).where(
            MilestoneHold.milestone_id == m.id,
            MilestoneHold.released_at.is_(None),
            (MilestoneHold.dispute_id.is_(None)) | (MilestoneHold.dispute_id != d.id),
        )
    )
    if other:
        raise ConflictError("Another hold blocks this decision", code="FUNDS_ON_HOLD")
    result = (finance or get_finance_port()).prepare_decision_settlement_in_tx(
        db, ctx=ctx(user_id), decision_id=row.id
    )
    row.status = DisputeDecisionStatus.EXECUTING
    audit(db, user_id, "dispute.decision_executing", "dispute_decisions", row.id)
    return {
        "decision_id": str(row.id),
        "settlement_id": str(result.settlement_id),
        "status": "EXECUTING",
    }


def reconcile_decision_in_tx(db, *, decision_id):
    raw = db.get(DisputeDecision, decision_id)
    if not raw:
        return
    # Internal worker only; find owning party to acquire the normal hierarchy.

    d = db.get(Dispute, raw.dispute_id)
    m = db.get(Milestone, d.milestone_id)
    _, c, m, e = milestone_scope(db, m.id, None, internal=True)
    d = lock(db, Dispute, id=d.id)
    row = lock(db, DisputeDecision, id=decision_id)
    settlement = db.scalar(select(Settlement).where(Settlement.source_decision_id == row.id))
    if (
        row.status != "EXECUTING"
        or not settlement
        or settlement.status != SettlementStatus.SUCCEEDED
    ):
        return
    row.status = DisputeDecisionStatus.EXECUTED
    row.executed_at = now()
    d.status = DisputeStatus.RESOLVED
    d.resolved_at = now()
    guard = db.get(ActiveMilestoneDispute, m.id)
    if guard:
        db.delete(guard)
    for h in db.scalars(
        select(MilestoneHold).where(
            MilestoneHold.dispute_id == d.id,
            MilestoneHold.reason_type == HoldReason.DISPUTE,
            MilestoneHold.released_at.is_(None),
        )
    ).all():
        h.released_at = now()
        h.release_note = "Decision settlement succeeded"
    audit(db, None, "dispute.resolved", "disputes", d.id)
    from app.services.freelancer_domain import notify

    freelancer = db.get(Student, c.freelancer_student_id)
    for recipient_id in filter(None, (c.client_user_id, freelancer.user_id if freelancer else None)):
        notify(
            db,
            recipient_id,
            "Tranh chấp Freelancer đã được giải quyết",
            "Quyết định của Admin đã được thực hiện và hồ sơ tranh chấp đã đóng.",
            ref_type="FREELANCE_DISPUTE",
            ref_id=d.id,
        )


class DisputeService:
    def open_dispute(self, db, *, ctx, milestone_id, reason_code, description):
        from app.contracts.freelancer.types import DisputeRef
        from app.schemas.freelancer_disputes import DisputeCreate

        result = run_command(
            db,
            lambda: open_in_tx(
                db,
                user_id=ctx.actor_user_id,
                milestone_id=milestone_id,
                payload=DisputeCreate(reason_code=reason_code, description=description),
            ),
        )
        return DisputeRef(
            dispute_id=int(result["id"]),
            milestone_id=milestone_id,
            status=DisputeStatus(result["status"]),
            evidence_deadline=__import__("datetime").datetime.fromisoformat(
                result["evidence_deadline"].replace("Z", "+00:00")
            ),
        )


def finalize_settlement_in_tx(db, *, settlement_id):
    """F calls in its confirmation TX, or emits settlement.completed to the outbox.
    This hook never marks transfers, escrow or milestones paid.
    """
    raw = db.get(Settlement, settlement_id)
    if raw is None:
        return
    p, c, m, e = milestone_scope(db, raw.milestone_id, None, internal=True)
    settled = lock(db, Settlement, id=settlement_id)
    if settled.status != SettlementStatus.SUCCEEDED:
        return
    if settled.source_decision_id:
        reconcile_decision_in_tx(db, decision_id=settled.source_decision_id)
    if settled.source_cancellation_id:
        from app.services.cancellation_service import reconcile_in_tx

        reconcile_in_tx(db, cancellation_id=settled.source_cancellation_id)
    db.flush()
    from app.services.freelance_closure_service import FreelanceClosureService

    closure = FreelanceClosureService()
    closure.recompute_contract_closure_in_tx(db, ctx=ctx(None), contract_id=c.id)
    closure.recompute_project_closure_in_tx(db, ctx=ctx(None), project_id=p.id)


def decision_history(db, *, user_id, dispute_id, number=1, size=20):
    scope(db, dispute_id, user_id, admin_only=True)
    return page(
        db,
        select(DisputeDecision)
        .where(DisputeDecision.dispute_id == dispute_id)
        .order_by(DisputeDecision.revision_no.desc()),
        number,
        size,
    )


def open_command_in_tx(db, *, user_id, milestone_id, payload, key):
    from app.services.freelancer_domain import replay

    milestone_scope(db, milestone_id, user_id)
    return replay(
        db,
        actor_id=user_id,
        operation="freelance.open_dispute",
        key=key,
        body={"milestone_id": str(milestone_id), **payload.model_dump(mode="json")},
        action=lambda: open_in_tx(db, user_id=user_id, milestone_id=milestone_id, payload=payload),
    )


def decision_command_in_tx(db, *, user_id, dispute_id, payload, key):
    from app.services.freelancer_domain import replay

    scope(db, dispute_id, user_id, admin_only=True)
    return replay(
        db,
        actor_id=user_id,
        operation="freelance.dispute_decision",
        key=key,
        body={"dispute_id": str(dispute_id), **payload.model_dump(mode="json")},
        action=lambda: decision_in_tx(db, user_id=user_id, dispute_id=dispute_id, payload=payload),
    )
