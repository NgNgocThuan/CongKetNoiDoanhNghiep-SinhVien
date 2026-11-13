from sqlalchemy import select

from app.core.enums import UserRole
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import (
    Company,
    CompanyLimit,
    FreelanceContract,
    FreelanceProject,
    Milestone,
    MilestoneHold,
    MouAgreement,
    StoredFile,
)
from app.services.freelancer_accounts.identity_service import submit_mou_in_tx
from app.services.freelancer_domain import admin, audit, ctx, lock, notify, now, page, record, user
from app.services.freelancer_policy_service import company_limits
from app.services.milestone_hold_service import MilestoneHoldService


def _owned_company(db, user_id):
    user(db, user_id, UserRole.COMPANY, onboarding=True)
    c = db.scalar(select(Company).where(Company.user_id == user_id))
    if not c:
        raise NotFoundError("Company not found")
    return c


def create_mou_in_tx(db, *, user_id, company_id, payload):
    admin(db, user_id)
    if company_id != payload.company_id:
        raise BadRequestError("Company ID mismatch")
    return submit_mou_in_tx(db, user_id=user_id, payload=payload)


def list_mous(db, *, user_id, company_id=None, number=1, size=20):
    if company_id is None:
        company_id = _owned_company(db, user_id).id
    else:
        admin(db, user_id)
    return page(
        db,
        select(MouAgreement)
        .where(MouAgreement.company_id == company_id)
        .order_by(MouAgreement.id.desc()),
        number,
        size,
    )


def review_mou_in_tx(db, *, user_id, mou_id, action, payload):
    admin(db, user_id)
    raw = db.get(MouAgreement, mou_id)
    if not raw:
        raise NotFoundError("MOU not found")
    c = lock(db, Company, id=raw.company_id)
    m = lock(db, MouAgreement, id=mou_id)
    payload.reason = (payload.reason or "").strip()
    if action != "approve" and not payload.reason:
        raise BadRequestError("Reason is required when rejecting or revoking an MOU")
    if action == "approve":
        if (
            m.status != "PENDING_REVIEW"
            or c.business_status != "VERIFIED"
            or c.operation_status != "ENABLED"
        ):
            raise ConflictError("MOU cannot be approved")
        if not (
            payload.school_authority_checked
            and payload.company_authority_checked
            and payload.signed_document_checked
        ):
            raise BadRequestError("Both signing authorities and signed document must be checked")
        if not (m.effective_from <= now() < m.effective_until):
            raise ConflictError("MOU is outside its effective period")
        f = db.get(StoredFile, m.document_file_id)
        if not f or f.scan_status != "CLEAN" or f.availability_status != "AVAILABLE":
            raise ConflictError("MOU document is not clean")
        for old in db.scalars(
            select(MouAgreement).where(
                MouAgreement.company_id == c.id, MouAgreement.status == "ACTIVE"
            )
        ).all():
            old.status = "SUPERSEDED"
        m.status = "ACTIVE"
        m.signature_verification_status = "MANUALLY_REVIEWED"
        from app.services.mou_lifecycle import schedule_mou_lifecycle
        schedule_mou_lifecycle(db, m)
    elif action == "reject":
        if m.status != "PENDING_REVIEW":
            raise ConflictError("MOU is not pending review")
        m.status = "REJECTED"
    else:
        if m.status != "ACTIVE":
            raise ConflictError("Only active MOU can be revoked")
        m.status = "REVOKED"
    m.reviewed_by = user_id
    m.reviewed_at = now()
    m.review_note = payload.reason
    audit(db, user_id, "mou." + action, "mou_agreements", m.id, reason=payload.reason)
    notify(
        db,
        c.user_id,
        "Cập nhật thỏa thuận MOU",
        "MOU đã được duyệt và có hiệu lực."
        if action == "approve"
        else f"MOU đã bị {('từ chối' if action == 'reject' else 'thu hồi')}: {payload.reason}",
        ref_type="MOU_AGREEMENT",
        ref_id=m.id,
    )
    return record(m)


def limits(db, *, user_id):
    c = _owned_company(db, user_id)
    values = company_limits(db, c)
    return (
        record(values)
        if isinstance(values, CompanyLimit)
        else {
            k: str(v) if "amount" in k or "funding" in k and not isinstance(v, bool) else v
            for k, v in values.items()
        }
    )


def override_limits_in_tx(db, *, user_id, company_id, payload):
    admin(db, user_id)
    c = lock(db, Company, id=company_id)
    if not c:
        raise NotFoundError("Company not found")
    if payload.max_project_amount <= 0 or payload.max_daily_funding <= 0:
        raise BadRequestError("Limits must be positive")
    row = lock(db, CompanyLimit, company_id=c.id)
    values = payload.model_dump(exclude={"reason"})
    if row:
        for k, v in values.items():
            setattr(row, k, v)
    else:
        row = CompanyLimit(company_id=c.id, **values)
        db.add(row)
    row.source = "OVERRIDE"
    row.set_by = user_id
    row.reason = payload.reason
    db.flush()
    audit(
        db,
        user_id,
        "company.limits_overridden",
        "company_limits",
        row.id,
        after=record(row),
        reason=payload.reason,
    )
    return record(row)


def suspension_in_tx(db, *, user_id, company_id, suspend, reason):
    admin(db, user_id)
    c = lock(db, Company, id=company_id)
    if not c:
        raise NotFoundError("Company not found")
    if suspend and c.operation_status == "SUSPENDED":
        return record(c)
    if not suspend and c.operation_status != "SUSPENDED":
        raise ConflictError("Company is not suspended")
    if suspend:
        c.operation_status = "SUSPENDED"
        c.suspended_at = now()
        c.suspended_by = user_id
        c.suspension_reason = reason
    else:
        c.operation_status = "ENABLED"
    projects = db.scalars(
        select(FreelanceProject)
        .where(FreelanceProject.company_id == c.id)
        .order_by(FreelanceProject.id)
        .with_for_update()
    ).all()
    for p in projects:
        contracts = db.scalars(
            select(FreelanceContract)
            .where(FreelanceContract.project_id == p.id)
            .order_by(FreelanceContract.id)
            .with_for_update()
        ).all()
        for contract in contracts:
            ms = db.scalars(
                select(Milestone)
                .where(Milestone.contract_id == contract.id)
                .order_by(Milestone.id)
                .with_for_update()
            ).all()
            for m in ms:
                if suspend and m.status not in (
                    "PAID_OUT",
                    "REFUNDED",
                    "PARTIALLY_RELEASED",
                    "CANCELLED",
                ):
                    MilestoneHoldService().place_hold_in_tx(
                        db,
                        ctx=ctx(user_id),
                        milestone_id=m.id,
                        reason_type="COMPANY_SUSPENSION",
                        reason_key=f"company:{c.id}:{c.suspended_at.isoformat()}:{m.id}",
                        dispute_id=None,
                        note=reason,
                    )
                elif not suspend:
                    for h in db.scalars(
                        select(MilestoneHold).where(
                            MilestoneHold.milestone_id == m.id,
                            MilestoneHold.reason_type == "COMPANY_SUSPENSION",
                            MilestoneHold.released_at.is_(None),
                        )
                    ).all():
                        h.released_at = now()
                        h.released_by = user_id
                        h.release_note = reason
    audit(
        db,
        user_id,
        "company.suspended" if suspend else "company.resumed",
        "companies",
        c.id,
        reason=reason,
    )
    return {"company_id": str(c.id), "operation_status": c.operation_status}
