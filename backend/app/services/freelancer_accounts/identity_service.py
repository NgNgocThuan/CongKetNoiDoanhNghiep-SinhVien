"""Transactional onboarding services; no model/schema changes required."""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.freelancer_enums import (
    ActorType,
    BusinessStatus,
    FileAvailability,
    FileScanStatus,
    MouStatus,
)
from app.models import (
    AuditLog,
    Company,
    MouAgreement,
    StoredFile,
    User,
)

from .common import as_naive_utc


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def locked(db, model, **filters):
    return db.scalars(
        select(model)
        .filter_by(**filters)
        .execution_options(populate_existing=True)
        .with_for_update()
    ).first()


def audit(db, user_id, action, entity, entity_id):
    db.add(
        AuditLog(
            actor_user_id=user_id,
            actor_type=ActorType.USER,
            action=action,
            entity_type=entity,
            entity_id=entity_id,
        )
    )


def checked_file(db, file_id, user_id, *, category=None):
    f = locked(db, StoredFile, id=file_id)
    if f is None or f.uploaded_by != user_id:
        raise NotFoundError("File not found")
    if f.scan_status != FileScanStatus.CLEAN or f.availability_status != FileAvailability.AVAILABLE:
        raise ConflictError("File has not passed scanning", code="FILE_NOT_READY")
    if category and f.category != category:
        raise BadRequestError("Wrong document category")
    return f



def submit_mou_in_tx(db: Session, *, user_id: int, payload):
    user = locked(db, User, id=user_id)
    company = locked(db, Company, id=payload.company_id)
    if user is not None and user.role != UserRole.ADMIN:
        raise ForbiddenError("Only administrators may submit MOU agreements")
    if company is None or user is None:
        raise NotFoundError("Company not found")
    if user.status not in (UserStatus.ACTIVE, UserStatus.PENDING_APPROVAL):
        raise ForbiddenError("Account is not active")
    if company.business_status != BusinessStatus.VERIFIED:
        raise ConflictError("Company must be verified first")
    from app.core.freelancer_enums import CompanyOperationStatus

    if company.operation_status != CompanyOperationStatus.ENABLED:
        raise ForbiddenError("Company is suspended")
    now = now_utc()
    start, end, signed = map(
        as_naive_utc, (payload.effective_from, payload.effective_until, payload.signed_at)
    )
    if end <= start or end <= now or signed > now or signed > start:
        raise BadRequestError("Invalid MOU signature or effective dates")
    # Signed documents may be uploaded after their effective start date.
    file_ids = {payload.document_file_id}
    file_ids.update(
        i for i in (payload.company_authority_file_id, payload.school_authority_file_id) if i
    )
    for file_id in sorted(file_ids):
        checked_file(db, file_id, user_id)
    if db.scalar(select(MouAgreement.id).where(MouAgreement.agreement_code == payload.mou_code)):
        raise ConflictError("Agreement code already exists")
    values = payload.model_dump(exclude={"mou_code"})
    values.update(
        agreement_code=payload.mou_code,
        effective_from=start,
        effective_until=end,
        signed_at=signed,
        status=MouStatus.PENDING_REVIEW,
    )
    mou = MouAgreement(**values)
    db.add(mou)
    db.flush()
    audit(db, user_id, "mou.submitted", "mou_agreements", mou.id)
    return {"status": "PENDING_REVIEW", "mou_id": str(mou.id), "company_id": str(company.id)}


def download_file(db: Session, *, user_id: int, file_id: int):
    f = db.get(StoredFile, file_id)
    user = db.get(User, user_id)
    if (
        f is None
        or user is None
        or user.status not in (UserStatus.ACTIVE, UserStatus.PENDING_APPROVAL)
    ):
        raise NotFoundError("File not found")
    allowed = f.uploaded_by == user_id or user.role == UserRole.ADMIN
    if not allowed:
        from app.models import FreelanceProject, FreelanceProjectAttachment
        from app.services.freelance_project_service import LIVE

        allowed = (
            db.scalar(
                select(FreelanceProjectAttachment.file_id)
                .join(
                    FreelanceProject, FreelanceProject.id == FreelanceProjectAttachment.project_id
                )
                .where(
                    FreelanceProjectAttachment.file_id == file_id, FreelanceProject.status.in_(LIVE)
                )
                .limit(1)
            )
            is not None
            and user.status == UserStatus.ACTIVE
        )
    if not allowed:
        from app.models import Deliverable, DeliverableFile, FreelanceContract, Milestone, Student

        linked_contracts = db.scalars(
            select(FreelanceContract)
            .join(Milestone, Milestone.contract_id == FreelanceContract.id)
            .join(Deliverable, Deliverable.milestone_id == Milestone.id)
            .join(DeliverableFile, DeliverableFile.deliverable_id == Deliverable.id)
            .where(DeliverableFile.file_id == file_id)
        ).all()
        for contract in linked_contracts:
            student = db.get(Student, contract.freelancer_student_id)
            if user_id == contract.client_user_id or (student and student.user_id == user_id):
                allowed = True
                break
    if not allowed:
        from app.models import (
            Dispute,
            DisputeEvidence,
            FreelanceApplication,
            FreelanceContract,
            FreelanceProject,
            Milestone,
            Student,
        )

        companies = db.scalars(select(Company.id).where(Company.user_id == user_id)).all()
        if companies:
            allowed = (
                db.scalar(
                    select(MouAgreement.id).where(
                        MouAgreement.company_id.in_(companies),
                        (MouAgreement.document_file_id == file_id)
                        | (MouAgreement.school_authority_file_id == file_id)
                        | (MouAgreement.company_authority_file_id == file_id),
                    )
                )
                is not None
            )
        evidence_contracts = db.scalars(
            select(FreelanceContract)
            .join(Milestone, Milestone.contract_id == FreelanceContract.id)
            .join(Dispute, Dispute.milestone_id == Milestone.id)
            .join(DisputeEvidence, DisputeEvidence.dispute_id == Dispute.id)
            .where(DisputeEvidence.file_id == file_id)
        ).all()
        for c in evidence_contracts:
            st = db.get(Student, c.freelancer_student_id)
            if c.client_user_id == user_id or (st and st.user_id == user_id):
                allowed = True
        applications = db.scalars(
            select(FreelanceApplication).where(FreelanceApplication.cv_snapshot_file_id == file_id)
        ).all()
        for a in applications:
            project = db.get(FreelanceProject, a.project_id)
            st = db.get(Student, a.student_id)
            if (project and project.client_user_id == user_id) or (st and st.user_id == user_id):
                allowed = True
    if not allowed:
        raise NotFoundError("File not found")
    if f.scan_status != FileScanStatus.CLEAN or f.availability_status != FileAvailability.AVAILABLE:
        raise ConflictError("File has not passed scanning", code="FILE_NOT_READY")
    root = Path(settings.UPLOAD_DIR).resolve()
    target = (root / f.storage_key).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise NotFoundError("File content not found")
    import hashlib
    if target.stat().st_size != f.size_bytes or hashlib.sha256(target.read_bytes()).hexdigest() != f.checksum_sha256:
        raise ConflictError("Stored file integrity check failed", code="FILE_INTEGRITY_FAILED")
    return target, f.original_name, f.content_type
