"""Doanh nghiệp và giấy tờ xác thực."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CompanyDocType, CompanySize, VerificationStatus
from app.core.freelancer_enums import BusinessStatus, CompanyOperationStatus
from app.models.base import Base, TimestampMixin, db_enum, fk, pk
from app.models.catalog import Industry
from app.models.freelancer_base import UTCDateTime, state_type

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE", unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    industry_id: Mapped[Optional[int]] = fk("industries.id", nullable=True)
    company_size: Mapped[Optional[CompanySize]] = mapped_column(db_enum(CompanySize))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    tech_stack: Mapped[Optional[str]] = mapped_column(String(500))
    benefits: Mapped[Optional[str]] = mapped_column(Text)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    # Xác thực bởi nhà trường
    verification_status: Mapped[VerificationStatus] = mapped_column(
        db_enum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.PENDING,
        server_default=VerificationStatus.PENDING.value,
    )
    verified_by: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reject_reason: Mapped[Optional[str]] = mapped_column(String(500))
    legal_name: Mapped[Optional[str]] = mapped_column(String(255))
    representative_name: Mapped[Optional[str]] = mapped_column(String(255))
    representative_position: Mapped[Optional[str]] = mapped_column(String(100))
    is_legal_representative: Mapped[Optional[bool]]
    authorization_file_id: Mapped[Optional[int]] = fk(
        "stored_files.id", ondelete="RESTRICT", nullable=True
    )
    business_status: Mapped[BusinessStatus] = mapped_column(
        state_type(BusinessStatus, "companies_business_status"),
        default=BusinessStatus.UNVERIFIED, server_default="UNVERIFIED", nullable=False,
    )
    business_verified_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    business_verified_by: Mapped[Optional[int]] = fk(
        "users.id", ondelete="RESTRICT", nullable=True
    )
    operation_status: Mapped[CompanyOperationStatus] = mapped_column(
        state_type(CompanyOperationStatus, "companies_operation_status"),
        default=CompanyOperationStatus.ENABLED, server_default="ENABLED", nullable=False,
    )
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text)
    suspended_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    suspended_by: Mapped[Optional[int]] = fk("users.id", ondelete="RESTRICT", nullable=True)

    # Có hai FK tới users (user_id, verified_by) nên phải chỉ rõ foreign_keys
    user: Mapped["User"] = relationship(back_populates="company", foreign_keys=[user_id])
    industry: Mapped[Optional["Industry"]] = relationship()
    documents: Mapped[list["CompanyDocument"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(back_populates="company")

    __table_args__ = (
        Index("idx_companies_status", "verification_status"),
        Index("idx_companies_industry", "industry_id"),
        Index("ix_companies_business_status_created_at", "business_status", "created_at"),
    )


class CompanyDocument(Base):
    __tablename__ = "company_documents"

    id: Mapped[int] = pk()
    company_id: Mapped[int] = fk("companies.id", ondelete="CASCADE")
    doc_type: Mapped[CompanyDocType] = mapped_column(db_enum(CompanyDocType), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    stored_file_id: Mapped[Optional[int]] = fk(
        "stored_files.id", ondelete="RESTRICT", nullable=True
    )
    uploaded_by: Mapped[Optional[int]] = fk("users.id", ondelete="RESTRICT", nullable=True)

    company: Mapped["Company"] = relationship(back_populates="documents")

    __table_args__ = (Index("idx_cdocs_company", "company_id"),)
