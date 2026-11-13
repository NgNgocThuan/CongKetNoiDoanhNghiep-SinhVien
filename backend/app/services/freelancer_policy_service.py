from sqlalchemy import select

from app.core.exceptions import ConflictError
from app.core.freelancer_enums import CompanyLimitSource
from app.models import CompanyLimit, FreelancerPolicy
from app.schemas.freelancer_policy import FreelancerPolicyValues
from app.services.freelancer_accounts.eligibility_service import company_has_valid_mou
from app.services.freelancer_domain import admin, audit, lock, now


def read_policy(db):
    row = db.scalar(select(FreelancerPolicy).where(FreelancerPolicy.policy_key == "default"))
    return (
        (FreelancerPolicyValues.model_validate(row.values_json), row.revision)
        if row
        else (FreelancerPolicyValues(), 0)
    )


def update_policy_in_tx(db, *, user_id, payload):
    # Serialize even first creation on the singleton school admin role via DB advisory-safe row:
    # lock all admin users in stable order, so two different admins cannot race initial insert.
    from app.core.enums import UserRole
    from app.models import User

    admin(db, user_id)
    db.scalars(
        select(User).where(User.role == UserRole.ADMIN).order_by(User.id).with_for_update()
    ).all()
    row = lock(db, FreelancerPolicy, policy_key="default")
    old, revision = read_policy(db)
    if revision != payload.expected_revision:
        raise ConflictError("Policy revision changed")
    values = payload.values.model_dump(mode="json")
    if row:
        row.values_json = values
        row.revision += 1
        row.updated_by = user_id
        row.updated_at = now()
    else:
        row = FreelancerPolicy(
            policy_key="default", values_json=values, revision=1, updated_by=user_id
        )
        db.add(row)
        db.flush()
    audit(
        db,
        user_id,
        "policy.updated",
        "freelancer_policies",
        row.id,
        before=old.model_dump(mode="json"),
        after=values,
        reason=payload.reason,
    )
    return {"revision": row.revision, "values": values}


def company_limits(db, company, *, at=None):
    row = db.scalar(select(CompanyLimit).where(CompanyLimit.company_id == company.id))
    if row and row.source == CompanyLimitSource.OVERRIDE:
        return row
    policy, _ = read_policy(db)
    partner = company_has_valid_mou(db, company.id, at or now())
    tier = "partner" if partner else "verified"
    return dict(
        max_open_projects=getattr(policy, tier + "_max_open_projects"),
        max_project_amount=getattr(policy, tier + "_max_project_amount"),
        max_daily_funding=getattr(policy, tier + "_max_daily_funding"),
        full_prefunding_required=not partner,
        source="PARTNER" if partner else "VERIFIED",
    )
