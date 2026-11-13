from sqlalchemy import select

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.freelancer_enums import HoldReason
from app.models import Dispute, MilestoneHold
from app.services.freelancer_domain import admin, audit, lock, milestone_scope, now


class MilestoneHoldService:
    def place_hold_in_tx(self, db, *, ctx, milestone_id, reason_type, reason_key, dispute_id, note):
        # Domain caller has locked project/contract/milestone/escrow already.
        reason = HoldReason(reason_type)
        old = db.scalar(select(MilestoneHold).where(MilestoneHold.reason_key == reason_key))
        if old:
            if (
                old.milestone_id != milestone_id
                or old.reason_type != reason
                or old.dispute_id != dispute_id
            ):
                raise ConflictError("Hold key conflict", code="IDEMPOTENCY_CONFLICT")
            return old.id
        if reason == HoldReason.DISPUTE:
            d = db.get(Dispute, dispute_id)
            if not d or d.milestone_id != milestone_id:
                raise BadRequestError("Hold/dispute milestone mismatch")
        h = MilestoneHold(
            milestone_id=milestone_id,
            reason_type=reason,
            reason_key=reason_key,
            dispute_id=dispute_id,
            placed_by=ctx.actor_user_id,
            note=note,
            placed_at=ctx.now_utc,
        )
        db.add(h)
        db.flush()
        audit(db, ctx.actor_user_id, "hold.placed", "milestone_holds", h.id, reason=note)
        return h.id

    def release_hold_in_tx(self, db, *, ctx, hold_id, note):
        admin(db, ctx.actor_user_id)
        raw = db.get(MilestoneHold, hold_id)
        if not raw:
            raise NotFoundError("Hold not found")
        milestone_scope(db, raw.milestone_id, ctx.actor_user_id, allow_admin=True)
        h = lock(db, MilestoneHold, id=hold_id)
        if h.reason_type != HoldReason.ADMIN_REVIEW:
            raise ConflictError("Release this hold through its dispute or suspension workflow")
        if h.released_at is None:
            h.released_at = now()
            h.released_by = ctx.actor_user_id
            h.release_note = note
            audit(db, ctx.actor_user_id, "hold.released", "milestone_holds", h.id, reason=note)
