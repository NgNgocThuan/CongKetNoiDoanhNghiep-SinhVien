"""A2 - ClientEligibility + ownership theo SHARED_CONTRACTS mục 5.1 (EligibilityPort)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.freelancer.types import ClientEligibility
from app.core.exceptions import NotFoundError
from app.core.freelancer_enums import MouStatus
from app.models import Company, MouAgreement, User
from app.services.freelancer_accounts import eligibility_rules as rules
from app.services.freelancer_accounts import mou_rules
from app.services.freelancer_accounts.common import as_naive_utc, enum_value

Capability = Literal["draft", "submit", "sign", "fund"]


def company_has_valid_mou(db: Session, company_id: int, now_utc: datetime) -> bool:
    now = as_naive_utc(now_utc)
    mou = db.scalars(
        select(MouAgreement)
        .where(MouAgreement.company_id == company_id, MouAgreement.status == MouStatus.ACTIVE)
        .order_by(MouAgreement.id.desc()).limit(1)
    ).first()
    return mou is not None and mou_rules.is_in_effect(
        status=enum_value(mou.status), effective_from=as_naive_utc(mou.effective_from),
        effective_until=as_naive_utc(mou.effective_until), now=now,
    )


def _facts(db: Session, user: User, now_utc: datetime) -> tuple[rules.UserFacts, rules.CompanyFacts | None, int | None]:
    user_facts = rules.UserFacts(
        role=enum_value(user.role), status=enum_value(user.status),
        email_verified_at=as_naive_utc(user.email_verified_at), phone_verified_at=as_naive_utc(user.phone_verified_at),
    )
    if user_facts.role != rules.ROLE_COMPANY:
        return user_facts, None, None
    company = db.scalars(select(Company).where(Company.user_id == user.id)).first()
    if company is None:
        return user_facts, None, None
    facts = rules.CompanyFacts(
        business_status=enum_value(company.business_status), operation_status=enum_value(company.operation_status),
        has_valid_mou=company_has_valid_mou(db, company.id, now_utc),
    )
    return user_facts, facts, company.id


def decide_for_user(db: Session, *, user_id: int, now_utc: datetime) -> tuple[rules.Eligibility, int | None]:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Tài khoản không tồn tại")
    user_facts, company_facts, company_id = _facts(db, user, now_utc)
    return rules.decide_eligibility(user_facts, company_facts), company_id


def get_client_eligibility(db: Session, *, user_id: int, now_utc: datetime) -> ClientEligibility:
    decision, company_id = decide_for_user(db, user_id=user_id, now_utc=now_utc)
    return ClientEligibility(
        user_id=user_id, company_id=company_id, tier=decision.tier.value, can_draft=decision.can_draft_project,
        can_submit=decision.can_submit_project, can_fund=decision.can_fund, reason_codes=decision.reasons,
    )


class EligibilityService:
    def get_client_eligibility(self, db: Session, *, user_id: int, now_utc: datetime) -> ClientEligibility:
        return get_client_eligibility(db, user_id=user_id, now_utc=now_utc)