"""Financial transaction writer, separate from all provider I/O."""

import uuid

from sqlalchemy import select

from app.contracts.freelancer.types import FundingState, SettlementRef
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.freelancer_enums import SettlementKind, SettlementStatus
from app.models import (
    CancellationAgreement,
    Dispute,
    DisputeDecision,
    EscrowAccount,
    Milestone,
    MilestoneHold,
    MilestoneReview,
    MoneyTransfer,
    Settlement,
)
from app.services import freelancer_bank_service as banks
from app.services import freelancer_limits as limits
from app.services.freelance_contract_service import FreelanceContractService
from app.services.freelancer_domain import audit, event, lock, milestone_scope, notify, now
from app.services.freelancer_ledger_service import account, post


def payos_idempotency_key(provider_reference_id: str) -> str:
    """Return the stable UUID required by payOS for one payout reference."""
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"student-connect:payos-payout:{provider_reference_id}",
        )
    )


def terms(db, milestone_id):
    return FreelanceContractService().get_milestone_financial_terms(db, milestone_id=milestone_id)


def holds(db, milestone_id, *, allowed_dispute=None):
    rows = db.scalars(
        select(MilestoneHold)
        .where(MilestoneHold.milestone_id == milestone_id, MilestoneHold.released_at.is_(None))
        .with_for_update()
    ).all()
    if any(
        not (allowed_dispute and h.reason_type == "DISPUTE" and h.dispute_id == allowed_dispute)
        for h in rows
    ):
        raise ConflictError("Funds are held", code="FUNDS_ON_HOLD")
    return rows


def ref(row):
    return SettlementRef(
        settlement_id=row.id,
        milestone_id=row.milestone_id,
        kind=SettlementKind(row.kind),
        status=SettlementStatus(row.status),
    )


class DatabaseFinancePort:
    def get_funding_state(self, db, *, milestone_id):
        m = db.get(Milestone, milestone_id)
        if not m:
            raise NotFoundError("Milestone not found")
        e = lock(db, EscrowAccount, milestone_id=milestone_id)
        ids = tuple(
            db.scalars(
                select(MilestoneHold.id)
                .where(
                    MilestoneHold.milestone_id == milestone_id, MilestoneHold.released_at.is_(None)
                )
                .order_by(MilestoneHold.id)
            ).all()
        )
        funded = e.funded_amount if e else 0
        remaining = funded - e.released_gross - e.refunded_amount if e else 0
        return FundingState(
            milestone_id=milestone_id,
            funded_amount=funded,
            held_amount=remaining,
            reserved_amount=e.reserved_amount if e else 0,
            active_hold_ids=ids,
            is_fully_funded=funded == terms(db, milestone_id).amount,
        )

    def assert_can_start_in_tx(self, db, *, ctx, milestone_id):
        _, c, m, _ = milestone_scope(db, milestone_id, None, internal=True)
        t = terms(db, milestone_id)
        milestones = (
            db.scalars(
                select(Milestone)
                .where(Milestone.contract_id == c.id, Milestone.status != "CANCELLED")
                .order_by(Milestone.id)
                .with_for_update()
            ).all()
            if t.funding_policy == "FULL"
            else [m]
        )
        for item in milestones:
            holds(db, item.id)
            state = self.get_funding_state(db, milestone_id=item.id)
            if not state.is_fully_funded:
                raise ConflictError(
                    "All required milestones must be funded", code="FUNDING_REQUIRED"
                )
        if self.get_funding_state(db, milestone_id=m.id).reserved_amount:
            raise ConflictError("Funds already reserved")

    def assert_disputable_in_tx(self, db, *, ctx, milestone_id):
        state = self.get_funding_state(db, milestone_id=milestone_id)
        holds(db, milestone_id)
        if (
            not state.is_fully_funded
            or state.reserved_amount
            or state.held_amount != state.funded_amount
        ):
            raise ConflictError("Milestone funds cannot be disputed")

    def prepare_acceptance_settlement_in_tx(self, db, *, ctx, review_id):
        row = db.get(MilestoneReview, review_id)
        if not row or row.action not in ("ACCEPT", "AUTO_ACCEPT"):
            raise ConflictError("An acceptance review is required")
        t = terms(db, row.milestone_id)
        return self._prepare(
            db,
            ctx=ctx,
            milestone_id=row.milestone_id,
            gross=t.amount,
            refund=0,
            source="AUTO_ACCEPT" if row.action == "AUTO_ACCEPT" else "ACCEPTANCE",
            source_field="source_review_id",
            source_id=row.id,
        )

    def prepare_decision_settlement_in_tx(self, db, *, ctx, decision_id):
        row = db.get(DisputeDecision, decision_id)
        if not row or row.status not in ("APPROVED", "EXECUTING"):
            raise ConflictError("Approved dispute decision required")
        d = db.get(Dispute, row.dispute_id)
        return self._prepare(
            db,
            ctx=ctx,
            milestone_id=d.milestone_id,
            gross=row.freelancer_gross,
            refund=row.refund_amount,
            source="DISPUTE",
            source_field="source_decision_id",
            source_id=row.id,
            allowed_dispute=d.id,
        )

    def prepare_cancellation_settlement_in_tx(self, db, *, ctx, cancellation_id):
        row = db.get(CancellationAgreement, cancellation_id)
        if not row or row.status != "ACCEPTED":
            raise ConflictError("Accepted cancellation required")
        return self._prepare(
            db,
            ctx=ctx,
            milestone_id=row.milestone_id,
            gross=row.freelancer_gross,
            refund=row.refund_amount,
            source="CANCELLATION",
            source_field="source_cancellation_id",
            source_id=row.id,
        )

    def _prepare(
        self,
        db,
        *,
        ctx,
        milestone_id,
        gross,
        refund,
        source,
        source_field,
        source_id,
        allowed_dispute=None,
    ):
        _, c, m, e = milestone_scope(db, milestone_id, None, internal=True)
        old = lock(db, Settlement, **{source_field: source_id})
        if old:
            return ref(old)
        holds(db, milestone_id, allowed_dispute=allowed_dispute)
        if (
            not e
            or e.reserved_amount
            or e.released_gross
            or e.refunded_amount
            or gross + refund != e.funded_amount
        ):
            raise ConflictError("Settlement must reserve all remaining funded money")
        if source in ("ACCEPTANCE", "AUTO_ACCEPT") and m.status != "ACCEPTED":
            raise ConflictError("Milestone has not been accepted")
        t = terms(db, milestone_id)
        fee = (gross * t.fee_rate_bp + 5000) // 10000
        kind = "SPLIT" if gross and refund else "RELEASE" if gross else "REFUND"
        previous = db.scalars(
            select(Settlement).where(Settlement.milestone_id == m.id).with_for_update()
        ).all()
        row = Settlement(
            milestone_id=m.id,
            sequence_no=max((s.sequence_no for s in previous), default=0) + 1,
            kind=kind,
            source=source,
            **{source_field: source_id},
            amount=gross + refund,
            freelancer_gross=gross,
            refund_amount=refund,
            fee_rate_bp=t.fee_rate_bp,
            fee_amount=fee,
            net_amount=gross - fee,
            request_key=f"{source}:{source_id}",
            requested_by=ctx.actor_user_id,
        )
        db.add(row)
        db.flush()
        e.reserved_amount += row.amount
        m.status = "SETTLEMENT_PENDING"
        for purpose, user_id, amount in (
            ("RELEASE", t.student_user_id, gross - fee),
            ("REFUND", c.client_user_id, refund),
        ):
            if amount:
                self.create_transfer(
                    db, settlement=row, purpose=purpose, user_id=user_id, amount=amount
                )
        if gross and gross - fee <= 0:
            raise ConflictError("The signed fee leaves no payable amount")
        audit(db, ctx.actor_user_id, "settlement.prepared", "settlements", row.id)
        db.flush()
        return ref(row)

    def create_transfer(
        self, db, *, settlement=None, transaction_id=None, purpose, user_id, amount
    ):
        dest = banks.destination(db, user_id, required=False)
        source_key = (
            f"settlement:{settlement.id}:{purpose}"
            if settlement
            else f"receipt:{transaction_id}:refund"
        )
        provider_reference_id = source_key.replace(":", "-")
        key = payos_idempotency_key(provider_reference_id)
        existing = db.scalar(select(MoneyTransfer).where(MoneyTransfer.provider_reference_id == provider_reference_id).with_for_update())
        if existing:
            return existing
        transfer = MoneyTransfer(
            settlement_id=settlement.id if settlement else None,
            payment_transaction_id=transaction_id,
            purpose=purpose,
            recipient_user_id=user_id,
            destination_id=dest.id if dest else None,
            destination_snapshot=banks.snapshot(dest) if dest else {},
            status="READY" if dest else "WAITING_BANK",
            amount=amount,
            idempotency_key=key,
            provider_reference_id=provider_reference_id,
            reserved_at=now(),
        )
        db.add(transfer)
        db.flush()
        limits.reserve(
            db,
            scope="platform:payout",
            limit=settings.FREELANCER_DAILY_PAYOUT_LIMIT,
            amount=amount,
            transfer_id=transfer.id,
        )
        if dest:
            event(db, f"transfer:{transfer.id}:send", "finance.transfer", "money_transfers",
                  transfer.id, {"transfer_id": transfer.id})
        else:
            notify(db, user_id, "Bổ sung tài khoản ngân hàng để nhận tiền",
                   f"Bạn có khoản {'giải ngân' if purpose == 'RELEASE' else 'hoàn tiền'} {amount:,} VND đang chờ. Vui lòng thêm tài khoản trong mục Ngân hàng nhận tiền; hệ thống sẽ tự động tiếp tục chi trả sau khi bạn thêm thành công.",
                   ref_type="BANK_DESTINATION", ref_id=None)
        return transfer


def confirm_transfer_in_tx(db, *, transfer_id, payout):
    """Only a signed matching provider transaction can recognize money leaving."""
    transfer = lock(db, MoneyTransfer, id=transfer_id)
    if not transfer:
        raise NotFoundError("Transfer not found")
    if transfer.status == "SUCCEEDED":
        return
    if transfer.status == "WAITING_BANK":
        raise ConflictError("Bổ sung ngân hàng trước khi xử lý lệnh chi", code="BANK_DESTINATION_REQUIRED")
    if payout.get("referenceId") != transfer.provider_reference_id or not payout.get("id"):
        raise ConflictError("Payout reference mismatch", code="PAYOS_PAYOUT_MISMATCH")
    txs = payout.get("transactions")
    if not isinstance(txs, list) or len(txs) != 1:
        raise ConflictError("Expected one transfer transaction", code="PAYOS_PAYOUT_MISMATCH")
    tx = txs[0]
    snap = transfer.destination_snapshot
    if (
        tx.get("referenceId") != transfer.provider_reference_id
        or type(tx.get("amount")) is not int
        or tx["amount"] != transfer.amount
        or tx.get("toBin") != snap["bank_bin"]
        or tx.get("toAccountNumber") != banks.decrypt_snapshot(snap)
        or not tx.get("id")
    ):
        raise ConflictError("Payout transaction mismatch", code="PAYOS_PAYOUT_MISMATCH")
    transfer.payos_payout_id = payout["id"]
    transfer.payos_transaction_id = tx["id"]
    transfer.provider_approval_state = payout.get("approvalState")
    transfer.provider_transaction_state = tx.get("state")
    if tx.get("state") != "SUCCEEDED":
        transfer.status = (
            "FAILED" if tx.get("state") in ("FAILED", "CANCELLED", "REVERSED") else "UNKNOWN"
        )
        # Retain reservations even on FAILED, until manually reconciled. No automatic re-create.
        db.flush()
        return
    # Recorded payout movements only, not the provider's available balance:
    # external wallet top-ups/fees are not inferred or fabricated as journals.
    source = account(
        db, "PAYOUT_ACCOUNT" if settings.PAYOS_PAYOUT_TREASURY_SEPARATE else "PLATFORM_BANK"
    )
    settlement = lock(db, Settlement, id=transfer.settlement_id) if transfer.settlement_id else None
    if settlement:
        _, _, m, escrow = milestone_scope(db, settlement.milestone_id, None, internal=True)
        gross = (
            settlement.freelancer_gross
            if transfer.purpose == "RELEASE"
            else settlement.refund_amount
        )
        liability = account(
            db,
            "FREELANCER_PAYABLE" if transfer.purpose == "RELEASE" else "CLIENT_REFUND_PAYABLE",
            owner_user_id=transfer.recipient_user_id,
        )
        lines = [(escrow.ledger_account_id, "D", gross), (liability.id, "C", transfer.amount)]
        if transfer.purpose == "RELEASE" and settlement.fee_amount:
            lines.append((account(db, "PLATFORM_FEE_REVENUE").id, "C", settlement.fee_amount))
        transfer.obligation_journal_id = post(
            db,
            key=f"transfer:{transfer.id}:obligation",
            entity="money_transfers",
            entity_id=transfer.id,
            lines=lines,
        )
        escrow.reserved_amount -= gross
        if transfer.purpose == "RELEASE":
            escrow.released_gross += gross
        else:
            escrow.refunded_amount += gross
        debit = liability.id
    else:
        from app.models import PaymentTransaction

        receipt = lock(db, PaymentTransaction, id=transfer.payment_transaction_id)
        debit = account(db, "UNALLOCATED_RECEIPTS").id
        receipt.allocation_status = (
            "RETURNED" if transfer.amount == receipt.amount else "PARTIALLY_RETURNED"
        )
        from app.models import PaymentReviewCase

        case = lock(db, PaymentReviewCase, payment_transaction_id=receipt.id)
        if case and transfer.amount == receipt.amount:
            case.status = "RESOLVED"
            case.resolved_at = now()
        if receipt.payment_order_id:
            event(
                db,
                f"receipt:{receipt.id}:close-order",
                "finance.order",
                "payment_orders",
                receipt.payment_order_id,
                {"order_id": receipt.payment_order_id, "cancel": True},
            )
    transfer.disbursement_journal_id = post(
        db,
        key=f"transfer:{transfer.id}:disbursement",
        entity="money_transfers",
        entity_id=transfer.id,
        lines=[(debit, "D", transfer.amount), (source.id, "C", transfer.amount)],
    )
    transfer.status = "SUCCEEDED"
    transfer.succeeded_at = now()
    transfer.reservation_released_at = now()
    from app.services.freelancer_domain import notify

    notify(
        db,
        transfer.recipient_user_id,
        "Giao dịch Freelancer đã thành công",
        "Tiền giải ngân hoặc hoàn tiền đã được PayOS xác nhận chuyển thành công.",
        ref_type="FREELANCE_SETTLEMENT",
        ref_id=transfer.settlement_id,
    )
    limits.finish(db, transfer_id=transfer.id, consume=True)
    db.flush()
    if settlement:
        legs = db.scalars(
            select(MoneyTransfer)
            .where(MoneyTransfer.settlement_id == settlement.id)
            .with_for_update()
        ).all()
        complete = all(leg.status == "SUCCEEDED" for leg in legs)
        settlement.status = "SUCCEEDED" if complete else "PARTIALLY_SUCCEEDED"
        if complete:
            settlement.completed_at = now()
            m.status = (
                "PARTIALLY_RELEASED"
                if settlement.kind == "SPLIT"
                else "PAID_OUT"
                if settlement.kind == "RELEASE"
                else "REFUNDED"
            )
            db.flush()
            from app.services.dispute_service import finalize_settlement_in_tx

            finalize_settlement_in_tx(db, settlement_id=settlement.id)
    audit(db, None, "transfer.confirmed", "money_transfers", transfer.id)
