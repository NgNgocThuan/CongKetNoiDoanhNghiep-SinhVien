"""Role policy from approved Freelancer specification section 2.2."""

from __future__ import annotations

from dataclasses import dataclass

TIER_UNVERIFIED = "UNVERIFIED"
TIER_VERIFIED = "VERIFIED"
TIER_MOU = "OFFICIAL_PARTNER"

R_USER_INACTIVE = "USER_INACTIVE"
R_CONTACT_NOT_VERIFIED = "CONTACT_NOT_VERIFIED"
R_NO_COMPANY = "NO_COMPANY"
R_COMPANY_NOT_VERIFIED = "COMPANY_NOT_VERIFIED"
R_COMPANY_SUSPENDED = "COMPANY_SUSPENDED"


@dataclass(frozen=True)
class ClientFacts:
    user_id: int
    user_active: bool
    email_verified: bool
    company_id: int | None
    company_verified: bool = False
    company_suspended: bool = False
    role: str = "COMPANY"
    mou_active: bool = False  # đã tính theo thời điểm hiện tại (xem mou_rules)


@dataclass(frozen=True)
class EligibilityDecision:
    tier: str
    can_draft: bool
    can_submit: bool
    can_fund: bool
    reason_codes: tuple[str, ...]


def evaluate_client_eligibility(facts: ClientFacts) -> EligibilityDecision:
    reasons = []
    tier = TIER_UNVERIFIED
    draft = submit = False
    if facts.role == "CLIENT":
        draft = facts.email_verified
        submit = draft
        tier = "CONTACT_VERIFIED" if submit else TIER_UNVERIFIED
        if not facts.email_verified:
            reasons.append("EMAIL_NOT_VERIFIED")
    elif facts.role == "COMPANY":
        draft = facts.company_id is not None and not facts.company_suspended
        submit = draft and facts.company_verified and facts.email_verified
        if not facts.email_verified:
            reasons.append("EMAIL_NOT_VERIFIED")
        if facts.company_id is None:
            reasons.append(R_NO_COMPANY)
        elif facts.company_suspended:
            reasons.append(R_COMPANY_SUSPENDED)
        elif not facts.company_verified:
            reasons.append(R_COMPANY_NOT_VERIFIED)
        if submit:
            tier = TIER_MOU if facts.mou_active else TIER_VERIFIED
    else:
        reasons.append("ROLE_NOT_ELIGIBLE")
    if not facts.user_active:
        draft = submit = False
        reasons.append(R_USER_INACTIVE)
    return EligibilityDecision(tier, draft, submit, submit, tuple(reasons))
