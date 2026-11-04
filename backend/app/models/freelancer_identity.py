"""Freelancer identity tables. Rules crossing rows belong in transactional services."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core import freelancer_enums as fe
from app.models.base import ID, Base, pk
from app.models.freelancer_base import UTCDateTime, binary_string, state_type


class StoredFile(Base):
    __tablename__ = "stored_files"

    id: Mapped[int] = pk()
    uploaded_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    storage_key: Mapped[str] = mapped_column(binary_string(500), nullable=False, unique=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    scan_status: Mapped[fe.FileScanStatus] = mapped_column(state_type(fe.FileScanStatus, "stored_files_scan_status"), nullable=False, default='PENDING', server_default='PENDING')
    availability_status: Mapped[fe.FileAvailability] = mapped_column(state_type(fe.FileAvailability, "stored_files_availability_status"), nullable=False, default='AVAILABLE', server_default='AVAILABLE')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('size_bytes > 0', name='size_bytes_nonnegative'),
        Index('ix_stored_files_uploaded_by_created_at', 'uploaded_by', 'created_at'),
        Index('ix_stored_files_checksum_sha256', 'checksum_sha256'),
        Index('ix_stored_files_uploaded_by', 'uploaded_by'),
    )


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_client_profiles_user_id', 'user_id'),
    )


class UserVerification(Base):
    __tablename__ = "user_verifications"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    channel: Mapped[fe.VerificationChannel] = mapped_column(state_type(fe.VerificationChannel, "user_verifications_channel"), nullable=False)
    purpose: Mapped[fe.VerificationPurpose] = mapped_column(state_type(fe.VerificationPurpose, "user_verifications_purpose"), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    otp_hash: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    key_version: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[fe.OtpStatus] = mapped_column(state_type(fe.OtpStatus, "user_verifications_status"), nullable=False, default='PENDING', server_default='PENDING')
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    resend_after: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('attempts >= 0', name='attempts_nonnegative'),
        CheckConstraint('max_attempts > 0', name='max_attempts_nonnegative'),
        CheckConstraint('attempts <= max_attempts', name='attempt_limit'),
        Index('ix_user_verifications_user_id_channel_created_at', 'user_id', 'channel', 'created_at'),
        Index('ix_user_verifications_status_expires_at', 'status', 'expires_at'),
        Index('ix_user_verifications_user_id', 'user_id'),
    )


class BusinessVerification(Base):
    __tablename__ = "business_verifications"

    id: Mapped[int] = pk()
    company_id: Mapped[int] = mapped_column(ID, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    submission_no: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_by: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    submitted_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[fe.BusinessSubmissionStatus] = mapped_column(state_type(fe.BusinessSubmissionStatus, "business_verifications_status"), nullable=False, default='PENDING', server_default='PENDING')
    decided_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('submission_no > 0', name='submission_no_nonnegative'),
        UniqueConstraint('company_id', 'submission_no', name='uq_business_verifications_company_id_submission_no'),
        Index('ix_business_verifications_status_created_at', 'status', 'created_at'),
        Index('ix_business_verifications_submitted_by', 'submitted_by'),
        Index('ix_business_verifications_decided_by', 'decided_by'),
    )


class BusinessVerificationFile(Base):
    __tablename__ = "business_verification_files"

    verification_id: Mapped[int] = mapped_column(ID, ForeignKey("business_verifications.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    file_id: Mapped[int] = mapped_column(ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    document_type: Mapped[fe.BusinessDocumentType] = mapped_column(state_type(fe.BusinessDocumentType, "business_verification_files_document_type"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_business_verification_files_verification_id', 'verification_id'),
        Index('ix_business_verification_files_file_id', 'file_id'),
    )


class CompanyLimit(Base):
    __tablename__ = "company_limits"

    id: Mapped[int] = pk()
    company_id: Mapped[int] = mapped_column(ID, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False, unique=True)
    max_open_projects: Mapped[int] = mapped_column(Integer, nullable=False)
    max_project_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    max_daily_funding: Mapped[int] = mapped_column(BigInteger, nullable=False)
    full_prefunding_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source: Mapped[fe.CompanyLimitSource] = mapped_column(state_type(fe.CompanyLimitSource, "company_limits_source"), nullable=False)
    set_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('max_open_projects > 0', name='max_open_projects_nonnegative'),
        CheckConstraint('max_project_amount > 0', name='max_project_amount_amount'),
        CheckConstraint('max_daily_funding > 0', name='max_daily_funding_amount'),
        Index('ix_company_limits_company_id', 'company_id'),
        Index('ix_company_limits_set_by', 'set_by'),
    )


class MouAgreement(Base):
    __tablename__ = "mou_agreements"

    id: Mapped[int] = pk()
    company_id: Mapped[int] = mapped_column(ID, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False)
    agreement_code: Mapped[str] = mapped_column(binary_string(100), nullable=False, unique=True)
    document_file_id: Mapped[int] = mapped_column(ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=False)
    school_name: Mapped[str] = mapped_column(String(255), nullable=False)
    school_signer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_signer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    school_signer_position: Mapped[str] = mapped_column(String(100), nullable=False)
    company_signer_position: Mapped[str] = mapped_column(String(100), nullable=False)
    company_authority_file_id: Mapped[int | None] = mapped_column(ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=True)
    school_authority_file_id: Mapped[int | None] = mapped_column(ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), nullable=True)
    signature_method: Mapped[fe.MouSignatureMethod] = mapped_column(state_type(fe.MouSignatureMethod, "mou_agreements_signature_method"), nullable=False)
    signature_verification_status: Mapped[fe.SignatureVerificationStatus] = mapped_column(state_type(fe.SignatureVerificationStatus, "mou_agreements_signature_verification_status"), nullable=False, default='NOT_CHECKED', server_default='NOT_CHECKED')
    signed_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    effective_until: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    scope_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[fe.MouStatus] = mapped_column(state_type(fe.MouStatus, "mou_agreements_status"), nullable=False, default='PENDING_REVIEW', server_default='PENDING_REVIEW')
    reviewed_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('effective_until > effective_from', name='effective_dates'),
        Index('ix_mou_agreements_company_id_status_effective_until', 'company_id', 'status', 'effective_until'),
        Index('ix_mou_agreements_status_effective_until', 'status', 'effective_until'),
        Index('ix_mou_agreements_company_id', 'company_id'),
        Index('ix_mou_agreements_document_file_id', 'document_file_id'),
        Index('ix_mou_agreements_company_authority_file_id', 'company_authority_file_id'),
        Index('ix_mou_agreements_school_authority_file_id', 'school_authority_file_id'),
        Index('ix_mou_agreements_reviewed_by', 'reviewed_by'),
    )
