"""Shared domain guards and projections, never own a transaction."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import inspect, select

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.freelancer_enums import ActorType
from app.models import (
    AuditLog,
    EscrowAccount,
    FreelanceContract,
    FreelanceProject,
    Milestone,
    Notification,
    OutboxEvent,
    Student,
    User,
)
from app.services.freelancer_accounts.common import as_naive_utc
from app.utils.hashing import sha256_json


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def lock(db, model, **filters):
    return db.scalars(
        select(model)
        .filter_by(**filters)
        .execution_options(populate_existing=True)
        .with_for_update()
    ).first()


def user(db, user_id, *roles, onboarding=False):
    u = db.get(User, user_id)
    allowed = (
        (UserStatus.ACTIVE, UserStatus.PENDING_APPROVAL) if onboarding else (UserStatus.ACTIVE,)
    )
    if not u or u.status not in allowed or (roles and u.role not in roles):
        raise ForbiddenError("Account cannot perform this operation")
    return u


def admin(db, user_id):
    return user(db, user_id, UserRole.ADMIN)


def student(db, user_id):
    user(db, user_id, UserRole.STUDENT)
    s = db.scalar(select(Student).where(Student.user_id == user_id))
    if s is None:
        raise ForbiddenError(
            "A school-registered student profile is required", code="STUDENT_NOT_ELIGIBLE"
        )
    return s


def owner(db, project_id, user_id, *, write=False):
    u = user(db, user_id)
    p = lock(db, FreelanceProject, id=project_id) if write else db.get(FreelanceProject, project_id)
    if not p or (p.client_user_id != user_id and (write or u.role != UserRole.ADMIN)):
        raise NotFoundError("Project not found")
    return p


def party(db, contract, user_id, *, allow_admin=False):
    u = user(db, user_id)
    s = db.get(Student, contract.freelancer_student_id)
    if (
        user_id != contract.client_user_id
        and (not s or s.user_id != user_id)
        and not (allow_admin and u.role == UserRole.ADMIN)
    ):
        raise NotFoundError("Contract not found")
    return u


def milestone_scope(db, milestone_id, user_id, *, allow_admin=False, internal=False):
    raw = db.get(Milestone, milestone_id)
    c = db.get(FreelanceContract, raw.contract_id) if raw else None
    if not c:
        raise NotFoundError("Milestone not found")
    if not internal:
        party(db, c, user_id, allow_admin=allow_admin)
    if c.company_id:
        from app.models import Company

        lock(db, Company, id=c.company_id)
    p = lock(db, FreelanceProject, id=c.project_id)
    c = lock(db, FreelanceContract, id=c.id)
    m = lock(db, Milestone, id=milestone_id)
    esc = lock(db, EscrowAccount, milestone_id=m.id)
    return p, c, m, esc


def audit(db, user_id, action, entity, entity_id, *, before=None, after=None, reason=None):
    db.add(
        AuditLog(
            actor_user_id=user_id,
            actor_type=ActorType.USER if user_id else ActorType.SYSTEM,
            action=action,
            entity_type=entity,
            entity_id=entity_id,
            before_json=before,
            after_json=after,
            reason=reason,
        )
    )


def event(db, key, kind, entity, entity_id, payload, *, when=None):
    if db.scalar(select(OutboxEvent.id).where(OutboxEvent.event_key == key)) is None:
        db.add(
            OutboxEvent(
                event_key=key,
                event_type=kind,
                entity_type=entity,
                entity_id=entity_id,
                payload_json=payload,
                available_at=when or now(),
            )
        )


def notify(db, user_id, title, message, *, ref_type="FREELANCE", ref_id=None):
    """Persist in-app and email notifications atomically with the domain action."""
    db.add(
        Notification(
            user_id=user_id,
            type="FREELANCER",
            title=title,
            content=message,
            ref_type=ref_type[:30],
            ref_id=ref_id,
        )
    )
    from html import escape

    from app.core.config import settings
    from app.services.email_service import queue_email

    recipient = db.get(User, user_id)
    if recipient:
        area = {"STUDENT": "student", "COMPANY": "company", "CLIENT": "client", "ADMIN": "admin"}.get(str(recipient.role))
        link = f"{settings.FRONTEND_URL.rstrip('/')}/{area}/notifications" if area else f"{settings.FRONTEND_URL.rstrip('/')}/login"
        queue_email(db, None, to_email=recipient.email, subject=f"[Student Connect] {title}",
                    body_html=(f"<h2>{escape(title)}</h2><p>{escape(message or '')}</p>"
                               f'<p><a href="{escape(link)}">Mở thông báo trên Student Connect</a></p>'),
                    type="FREELANCER", user_id=user_id,
                    ref_type=ref_type[:30], ref_id=ref_id, commit=False)


def notify_admins(db, title, message, *, ref_type="FREELANCE", ref_id=None):
    admin_ids = db.scalars(
        select(User.id).where(User.role == UserRole.ADMIN, User.status == UserStatus.ACTIVE)
    ).all()
    for admin_id in admin_ids:
        notify(db, admin_id, title, message, ref_type=ref_type, ref_id=ref_id)


def ctx(user_id, key=None):
    return CommandContext(
        actor_user_id=user_id,
        actor_type=ActorType.USER if user_id else ActorType.SYSTEM,
        request_id=key or "freelancer-command",
        idempotency_key=key,
        now_utc=now(),
    )


def record(obj, *, fields=None, exclude=()):
    result = {}
    for col in inspect(type(obj)).columns:
        k = col.key
        if (fields is not None and k not in fields) or k in exclude:
            continue
        v = getattr(obj, k)
        if isinstance(v, Enum):
            v = v.value
        elif isinstance(v, datetime):
            v = as_naive_utc(v).isoformat() + "Z"
        elif (
            isinstance(v, int)
            and not isinstance(v, bool)
            and (
                k == "id"
                or k.endswith("_id")
                or "amount" in k
                or k in ("freelancer_gross", "refund_amount", "allocated_amount")
            )
        ):
            v = str(v)
        result[k] = v
    return result


def page(db, stmt, number=1, size=20, *, project=None):
    from sqlalchemy import func

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.scalars(stmt.offset((number - 1) * size).limit(size)).all()
    return {
        "items": [project(x) if project else record(x) for x in rows],
        "total": total,
        "page": number,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def replay(db, *, actor_id, operation, key, body, action):
    from app.models import CommandRequest

    if not key or len(key) > 128:
        raise ConflictError(
            "Idempotency-Key is required and must be at most 128 characters",
            code="IDEMPOTENCY_KEY_REQUIRED",
        )
    # Callers serialize on their domain parent lock and recheck ownership BEFORE replay.
    hashed = sha256_json(body)
    existing = db.scalar(
        select(CommandRequest)
        .where(
            CommandRequest.actor_user_id == actor_id,
            CommandRequest.operation == operation,
            CommandRequest.idempotency_key == key,
        )
        .with_for_update()
    )
    if existing:
        if existing.request_hash != hashed:
            raise ConflictError("Key was used for another command", code="IDEMPOTENCY_CONFLICT")
        return existing.response_json
    result = action()
    db.add(
        CommandRequest(
            actor_user_id=actor_id,
            operation=operation,
            idempotency_key=key,
            request_hash=hashed,
            response_json=result,
            completed_at=now(),
        )
    )
    db.flush()
    return result
