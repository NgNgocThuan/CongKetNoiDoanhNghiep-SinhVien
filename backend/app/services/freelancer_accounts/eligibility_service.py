"""Eligibility reads the real schema and the approved role policy."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.freelancer.types import ClientEligibility
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import NotFoundError
from app.core.freelancer_enums import BusinessStatus, CompanyOperationStatus, MouStatus
from app.models import Company, MouAgreement, User

from .common import as_naive_utc
from .eligibility_rules import ClientFacts, evaluate_client_eligibility


def company_has_valid_mou(db: Session, company_id: int, now_utc: datetime) -> bool:
    now = as_naive_utc(now_utc)
    return (
        db.scalar(
            select(MouAgreement.id)
            .where(
                MouAgreement.company_id == company_id,
                MouAgreement.status == MouStatus.ACTIVE,
                MouAgreement.effective_from <= now,
                MouAgreement.effective_until > now,
            )
            .limit(1)
        )
        is not None
    )


def get_client_eligibility(db: Session, *, user_id: int, now_utc: datetime) -> ClientEligibility:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("Account not found")
    company = (
        db.scalar(select(Company).where(Company.user_id == user.id))
        if user.role == UserRole.COMPANY
        else None
    )
    decision = evaluate_client_eligibility(
        ClientFacts(
            user_id=user_id,
            role=user.role.value,
            user_active=user.status == UserStatus.ACTIVE,
            email_verified=user.email_verified_at is not None,
            company_id=company.id if company else None,
            company_verified=bool(company and company.business_status == BusinessStatus.VERIFIED),
            company_suspended=bool(
                company and company.operation_status != CompanyOperationStatus.ENABLED
            ),
            mou_active=bool(company and company_has_valid_mou(db, company.id, now_utc)),
        )
    )
    return ClientEligibility(
        user_id=user_id,
        company_id=company.id if company else None,
        tier=decision.tier,
        can_draft=decision.can_draft,
        can_submit=decision.can_submit,
        can_fund=decision.can_fund,
        reason_codes=decision.reason_codes,
    )


def assert_student_eligible(db, *, student_id, now_utc):
    from app.models import Student
    from app.services.freelancer_domain import student

    row = db.get(Student, student_id)
    if row is None:
        raise NotFoundError("Student not found")
    student(db, row.user_id)


def assert_contract_party(db, *, contract_id, actor_user_id):
    from app.models import FreelanceContract
    from app.services.freelancer_domain import party

    c = db.get(FreelanceContract, contract_id)
    if not c:
        raise NotFoundError("Contract not found")
    party(db, c, actor_user_id)


def assert_project_owner(db, *, project_id, actor_user_id):
    from app.services.freelancer_domain import owner

    owner(db, project_id, actor_user_id)


class EligibilityService:
    def get_client_eligibility(
        self, db: Session, *, user_id: int, now_utc: datetime
    ) -> ClientEligibility:
        return get_client_eligibility(db, user_id=user_id, now_utc=now_utc)

    def assert_student_eligible(self, db, *, student_id, now_utc):
        return assert_student_eligible(db, student_id=student_id, now_utc=now_utc)

    def assert_contract_party(self, db, *, contract_id, actor_user_id):
        return assert_contract_party(db, contract_id=contract_id, actor_user_id=actor_user_id)

    def assert_project_owner(self, db, *, project_id, actor_user_id):
        return assert_project_owner(db, project_id=project_id, actor_user_id=actor_user_id)
