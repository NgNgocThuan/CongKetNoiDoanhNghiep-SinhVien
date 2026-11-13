from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.core.enums import UserRole, UserStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import _create_token, hash_password, verify_password
from app.models import ClientProfile, User, UserVerification
from app.services.freelancer_domain import audit, lock, now, record, user


def register_in_tx(db, *, payload, ip_key="unknown"):
    from app.services.freelancer_rate_limit import consume_in_tx

    consume_in_tx(db, scopes=[(f"register:ip:{ip_key}", 10, 3600)], at=now())
    email = str(payload.email).lower()
    if len(payload.password.encode("utf-8")) > 72:
        raise BadRequestError("Password is too long for password hashing")
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise ConflictError("Account already exists")
    u = User(
        email=email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.CLIENT,
        status=UserStatus.ACTIVE,
        registration_terms_accepted_at=datetime.now(timezone.utc),
        registration_terms_version=payload.terms_acceptance.version,
    )
    db.add(u)
    db.flush()
    db.add(ClientProfile(user_id=u.id, full_name=payload.full_name, address=payload.address))
    audit(db, u.id, "client.registered", "users", u.id)
    return {"user_id": str(u.id), "status": "ACTIVE", "contact_verified": False}


def onboarding_login(db, *, email, password, ip_key="unknown"):
    from app.services.freelancer_commands import run_command
    from app.services.freelancer_rate_limit import consume_in_tx

    run_command(
        db,
        lambda: consume_in_tx(
            db,
            scopes=[
                (f"onboarding:ip:{ip_key}", 30, 3600),
                (f"onboarding:email:{email.lower()}", 10, 3600),
            ],
            at=now(),
        ),
    )
    u = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
    # Use the existing shared login guard for ACTIVE accounts; pending-company authentication
    # has the same password work, with a distinct token type unusable by old routers.
    from app.services.auth_service import _DUMMY_PASSWORD_HASH

    valid = verify_password(password, u.password_hash if u else _DUMMY_PASSWORD_HASH)
    if not valid or not u:
        raise UnauthorizedError("Invalid credentials")
    if u.role not in (UserRole.COMPANY, UserRole.CLIENT) or u.status not in (
        UserStatus.ACTIVE,
        UserStatus.PENDING_APPROVAL,
    ):
        raise ForbiddenError("Account cannot access onboarding")
    return {
        "access_token": _create_token(u.id, "onboarding", timedelta(minutes=15)),
        "token_type": "bearer",
        "expires_in": 900,
    }


def profile_in_tx(db, *, user_id, payload):
    user(db, user_id, UserRole.CLIENT)
    lock(db, User, id=user_id)
    profile = lock(db, ClientProfile, user_id=user_id)
    if not profile:
        raise ConflictError("Client profile is missing")
    profile.full_name = payload.full_name
    profile.address = payload.address
    audit(db, user_id, "client.profile_updated", "client_profiles", profile.id)
    return record(profile)


def change_contact_in_tx(db, *, user_id, payload):
    u = lock(db, User, id=user_id)
    user(db, user_id, onboarding=True)
    if not verify_password(payload.password, u.password_hash):
        raise UnauthorizedError("Invalid password")
    email_changed = False
    if payload.email is not None:
        email = str(payload.email).lower()
        if email != u.email:
            if db.scalar(select(User.id).where(func.lower(User.email) == email, User.id != u.id)):
                raise ConflictError("Contact already in use")
            u.email = email
            u.email_verified_at = None
            email_changed = True
            if u.role == UserRole.COMPANY:
                from app.models import Company, CompanyVerification
                company = db.scalar(select(Company).where(Company.user_id == u.id).with_for_update())
                if company:
                    company.business_status = 'NEEDS_REVISION'
                    company.verification_status = 'PENDING'
                    verification = db.scalar(select(CompanyVerification).where(CompanyVerification.company_id == company.id))
                    if verification:
                        verification.verification_status = 'NEEDS_REVISION'
                        verification.rejection_reason = 'Email đã thay đổi. Vui lòng xác minh email mới và nộp lại quyền đại diện.'
    if payload.phone is not None and payload.phone != u.phone:
        u.phone = payload.phone
        u.phone_verified_at = None
    for v in db.scalars(
        select(UserVerification)
        .where(UserVerification.user_id == u.id, UserVerification.status == "PENDING",
               UserVerification.channel == "EMAIL", email_changed)
        .with_for_update()
    ).all():
        v.status = "SUPERSEDED"
    audit(db, user_id, "contact.changed", "users", u.id)
    return {
        "status": "CONTACT_UPDATED",
        "email_verified": u.email_verified_at is not None,
    }


def get_profile(db, *, user_id):
    user(db, user_id, UserRole.CLIENT)
    profile = db.scalar(select(ClientProfile).where(ClientProfile.user_id == user_id))
    if not profile:
        raise ConflictError("Client profile is missing")
    return record(profile)
