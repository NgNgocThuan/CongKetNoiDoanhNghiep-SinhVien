"""FastAPI router for freelance contracts and version negotiations."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, Query, status

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole
from app.core.freelancer_enums import ActorType
from app.dependencies import CurrentUser, DbSession
from app.models import ClientProfile, Company, FreelanceProject, Student
from app.models.freelancer_contracts import (
    ContractMilestoneTerm,
    ContractVersion,
    FreelanceContract,
    ProjectContractBudget,
)
from app.schemas.common import Page
from app.schemas.freelance_contracts import (
    ContractMilestoneTermRead,
    ContractRead,
    ContractVersionAcceptRequest,
    ContractVersionCreate,
    ContractVersionDeclineRequest,
    ContractVersionOfferRequest,
    ContractVersionRead,
)
from app.services.freelance_contract_service import FreelanceContractService

router = APIRouter(tags=["Freelance Contracts"])
service = FreelanceContractService()


def _build_context(
    user: CurrentUser, request_id: str | None, idempotency_key: str | None
) -> CommandContext:
    return CommandContext(
        actor_user_id=user.id,
        actor_type=ActorType.USER,
        request_id=request_id or str(uuid.uuid4()),
        idempotency_key=idempotency_key,
        now_utc=datetime.now(timezone.utc),
    )


def _format_version(db: DbSession, version: ContractVersion) -> ContractVersionRead:
    terms = (
        db.query(ContractMilestoneTerm)
        .filter_by(contract_version_id=version.id)
        .order_by(ContractMilestoneTerm.id.asc())
        .all()
    )
    terms_read = [
        ContractMilestoneTermRead(
            id=t.id,
            milestone_id=t.milestone_id,
            title=t.title,
            description=t.description,
            amount=t.amount,
            acceptance_criteria=t.acceptance_criteria,
            due_at=t.due_at,
            included=t.included,
        )
        for t in terms
    ]
    return ContractVersionRead(
        id=version.id,
        contract_id=version.contract_id,
        version_no=version.version_no,
        created_by=version.created_by,
        status=version.status,
        total_amount=version.total_amount,
        fee_rate_bp=version.fee_rate_bp,
        review_period_seconds=version.review_period_seconds,
        max_revision_count=version.max_revision_count,
        grace_period_seconds=version.grace_period_seconds,
        funding_policy=version.funding_policy,
        terms_json=version.terms_json,
        content_hash=version.content_hash,
        offered_at=version.offered_at,
        acceptance_deadline=version.acceptance_deadline,
        client_accepted_at=version.client_accepted_at,
        freelancer_accepted_at=version.freelancer_accepted_at,
        effective_at=version.effective_at,
        response_note=version.response_note,
        milestone_terms=terms_read,
        created_at=version.created_at,
    )


def _format_contract(db: DbSession, contract: FreelanceContract) -> ContractRead:
    student = db.get(Student, contract.freelancer_student_id)
    project = db.get(FreelanceProject, contract.project_id)
    company = db.get(Company, contract.company_id) if contract.company_id else None
    client = (
        db.query(ClientProfile).filter_by(user_id=contract.client_user_id).first()
        if not company
        else None
    )
    budget = db.query(ProjectContractBudget).filter_by(contract_id=contract.id).first()
    eff_ver = None
    if contract.effective_version_id:
        v = db.get(ContractVersion, contract.effective_version_id)
        if v:
            eff_ver = _format_version(db, v)

    return ContractRead(
        id=contract.id,
        project_id=contract.project_id,
        application_id=contract.application_id,
        client_user_id=contract.client_user_id,
        company_id=contract.company_id,
        freelancer_student_id=contract.freelancer_student_id,
        status=contract.status,
        effective_version_id=contract.effective_version_id,
        activated_at=contract.activated_at,
        closed_at=contract.closed_at,
        closure_reason=contract.closure_reason,
        created_at=contract.created_at,
        allocated_amount=budget.allocated_amount if budget else None,
        effective_version=eff_ver,
        student_name=student.full_name if student else None,
        project_title=project.title if project else None,
        project_deadline=project.deadline if project else None,
        client_name=company.name if company else client.full_name if client else None,
    )


@router.get("/freelance-contracts/{contract_id}", response_model=ContractRead)
def get_contract(
    contract_id: int,
    db: DbSession,
    user: CurrentUser,
):
    contract = service.get_contract(
        db,
        contract_id=contract_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
    )
    return _format_contract(db, contract)


@router.get("/freelance-contracts/{contract_id}/versions", response_model=Page[ContractVersionRead])
def list_contract_versions(
    contract_id: int,
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    versions = service.get_contract_versions_page(
        db,
        contract_id=contract_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
        page=page,
        size=size,
    )
    return {**versions, "items": [_format_version(db, v) for v in versions["items"]]}


@router.post(
    "/freelance-contracts/{contract_id}/versions",
    response_model=ContractVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_version(
    contract_id: int,
    payload: ContractVersionCreate,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    version = service.create_version(db, ctx=ctx, contract_id=contract_id, payload=payload)
    return _format_version(db, version)


@router.get("/contract-versions/{version_id}", response_model=ContractVersionRead)
def get_contract_version(
    version_id: int,
    db: DbSession,
    user: CurrentUser,
):
    version = service.get_contract_version(
        db,
        version_id=version_id,
        actor_user_id=user.id,
        is_admin=user.role == UserRole.ADMIN,
    )
    return _format_version(db, version)


@router.post("/contract-versions/{version_id}/offer", response_model=ContractVersionRead)
def offer_version(
    version_id: int,
    db: DbSession,
    user: CurrentUser,
    payload: ContractVersionOfferRequest | None = None,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    deadline = payload.acceptance_deadline if payload else None
    version = service.offer_version(
        db, ctx=ctx, version_id=version_id, acceptance_deadline=deadline
    )
    return _format_version(db, version)


@router.post("/contract-versions/{version_id}/accept", response_model=ContractVersionRead)
def accept_version(
    version_id: int,
    payload: ContractVersionAcceptRequest,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    version = service.accept_version(
        db, ctx=ctx, version_id=version_id, content_hash=payload.content_hash
    )
    return _format_version(db, version)


@router.post("/contract-versions/{version_id}/decline", response_model=ContractVersionRead)
def decline_version(
    version_id: int,
    payload: ContractVersionDeclineRequest,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    version = service.decline_version(
        db, ctx=ctx, version_id=version_id, response_note=payload.response_note
    )
    return _format_version(db, version)


@router.post("/contract-versions/{version_id}/withdraw", response_model=ContractVersionRead)
def withdraw_version(
    version_id: int,
    db: DbSession,
    user: CurrentUser,
    x_request_id: str | None = Header(None),
    x_idempotency_key: str | None = Header(None, alias="Idempotency-Key", max_length=128),
):
    ctx = _build_context(user, x_request_id, x_idempotency_key)
    version = service.withdraw_version(db, ctx=ctx, version_id=version_id)
    return _format_version(db, version)
