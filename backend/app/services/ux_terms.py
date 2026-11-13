from app.core.enums import UserRole
from app.core.exceptions import ForbiddenError
from app.models import User
from app.schemas.terms import TERMS_VERSION
from app.services.freelancer_domain import audit, lock, now, user
from app.services.freelancer_policy_service import read_policy


def status(db, user_id):
    u = user(db, user_id, UserRole.CLIENT, UserRole.COMPANY)
    policy, _ = read_policy(db)
    return {
        "has_accepted_escrow_terms": bool(u.escrow_terms_accepted_at),
        "accepted_at": u.escrow_terms_accepted_at,
        "version": TERMS_VERSION,
        "review_period_seconds": policy.review_period_seconds,
    }


def accept_in_tx(db, user_id, payload):
    user(db, user_id, UserRole.CLIENT, UserRole.COMPANY)
    u = lock(db, User, id=user_id)
    if not u.escrow_terms_accepted_at:
        u.escrow_terms_accepted_at = now()
        u.escrow_terms_version = payload.version
        audit(db, user_id, "escrow.terms.accepted", "users", user_id)
    return status(db, user_id)


def require_escrow_terms(db, user_id):
    if not db.get(User, user_id).escrow_terms_accepted_at:
        raise ForbiddenError(
            "Bạn cần đồng ý điều khoản ký quỹ trước khi tạo dự án",
            code="ESCROW_TERMS_REQUIRED",
        )
