"""Freelancer payments tables. Rules crossing rows belong in transactional services."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
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


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False)
    payer_user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    expected_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    order_code: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    payment_link_id: Mapped[str | None] = mapped_column(binary_string(191), nullable=True, unique=True)
    status: Mapped[fe.PaymentOrderStatus] = mapped_column(state_type(fe.PaymentOrderStatus, "payment_orders_status"), nullable=False, default='CREATING', server_default='CREATING')
    request_key: Mapped[str] = mapped_column(binary_string(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    checkout_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    qr_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    receiving_account_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    provider_response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('expected_amount > 0', name='expected_amount_amount'),
        CheckConstraint('order_code > 0 AND order_code <= 9007199254740991', name='safe_order_code'),
        UniqueConstraint('payer_user_id', 'request_key', name='uq_payment_orders_payer_user_id_request_key'),
        Index('ix_payment_orders_milestone_id_created_at', 'milestone_id', 'created_at'),
        Index('ix_payment_orders_status_expires_at', 'status', 'expires_at'),
        Index('ix_payment_orders_milestone_id', 'milestone_id'),
    )


class MilestoneFundingGuard(Base):
    __tablename__ = "milestone_funding_guards"

    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False, primary_key=True)
    payment_order_id: Mapped[int] = mapped_column(ID, ForeignKey("payment_orders.id", ondelete="RESTRICT"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_milestone_funding_guards_milestone_id', 'milestone_id'),
        Index('ix_milestone_funding_guards_payment_order_id', 'payment_order_id'),
    )


class ProviderEvent(Base):
    __tablename__ = "provider_events"

    id: Mapped[int] = pk()
    channel_key: Mapped[str] = mapped_column(binary_string(100), nullable=False)
    event_key: Mapped[str] = mapped_column(binary_string(191), nullable=False)
    event_type: Mapped[fe.ProviderEventType] = mapped_column(state_type(fe.ProviderEventType, "provider_events_event_type"), nullable=False)
    payload_hash: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[fe.ProviderEventStatus] = mapped_column(state_type(fe.ProviderEventStatus, "provider_events_status"), nullable=False, default='RECEIVED', server_default='RECEIVED')
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    available_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('attempts >= 0', name='attempts_nonnegative'),
        UniqueConstraint('channel_key', 'event_key', name='uq_provider_events_channel_key_event_key'),
        Index('ix_provider_events_status_available_at_lease_until', 'status', 'available_at', 'lease_until'),
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = pk()
    payment_order_id: Mapped[int | None] = mapped_column(ID, ForeignKey("payment_orders.id", ondelete="RESTRICT"), nullable=True)
    provider_event_id: Mapped[int | None] = mapped_column(ID, ForeignKey("provider_events.id", ondelete="RESTRICT"), nullable=True)
    channel_key: Mapped[str] = mapped_column(binary_string(100), nullable=False)
    external_ref: Mapped[str] = mapped_column(binary_string(191), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default='VND', server_default='VND')
    receiving_account_ref: Mapped[str] = mapped_column(binary_string(191), nullable=False)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    received_time_raw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    allocation_status: Mapped[fe.PaymentAllocationStatus] = mapped_column(state_type(fe.PaymentAllocationStatus, "payment_transactions_allocation_status"), nullable=False, default='UNALLOCATED', server_default='UNALLOCATED')
    receipt_journal_id: Mapped[int] = mapped_column(ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), nullable=False, unique=True)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_amount'),
        UniqueConstraint('channel_key', 'external_ref', name='uq_payment_transactions_channel_key_external_ref'),
        CheckConstraint("currency = 'VND'", name='vnd_only'),
        Index('ix_payment_transactions_allocation_status_created_at', 'allocation_status', 'created_at'),
        Index('ix_payment_transactions_payment_order_id', 'payment_order_id'),
        Index('ix_payment_transactions_provider_event_id', 'provider_event_id'),
        Index('ix_payment_transactions_receipt_journal_id', 'receipt_journal_id'),
    )


class MilestoneFunding(Base):
    __tablename__ = "milestone_fundings"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False, unique=True)
    payment_transaction_id: Mapped[int] = mapped_column(ID, ForeignKey("payment_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    funding_journal_id: Mapped[int] = mapped_column(ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_amount'),
        Index('ix_milestone_fundings_milestone_id', 'milestone_id'),
        Index('ix_milestone_fundings_payment_transaction_id', 'payment_transaction_id'),
        Index('ix_milestone_fundings_funding_journal_id', 'funding_journal_id'),
    )


class PaymentReviewCase(Base):
    __tablename__ = "payment_review_cases"

    id: Mapped[int] = pk()
    payment_transaction_id: Mapped[int] = mapped_column(ID, ForeignKey("payment_transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    reason: Mapped[fe.PaymentReviewReason] = mapped_column(state_type(fe.PaymentReviewReason, "payment_review_cases_reason"), nullable=False)
    status: Mapped[fe.PaymentReviewStatus] = mapped_column(state_type(fe.PaymentReviewStatus, "payment_review_cases_status"), nullable=False, default='OPEN', server_default='OPEN')
    assigned_to: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    resolution: Mapped[fe.PaymentReviewResolution | None] = mapped_column(state_type(fe.PaymentReviewResolution, "payment_review_cases_resolution"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('ix_payment_review_cases_status_created_at', 'status', 'created_at'),
        Index('ix_payment_review_cases_payment_transaction_id', 'payment_transaction_id'),
        Index('ix_payment_review_cases_assigned_to', 'assigned_to'),
        Index('ix_payment_review_cases_resolved_by', 'resolved_by'),
    )


class EscrowAccount(Base):
    __tablename__ = "escrow_accounts"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False, unique=True)
    ledger_account_id: Mapped[int] = mapped_column(ID, ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False, unique=True)
    funded_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reserved_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default='0')
    released_gross: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default='0')
    refunded_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default='0')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('funded_amount > 0', name='funded_amount_amount'),
        CheckConstraint('reserved_amount >= 0', name='reserved_amount_amount'),
        CheckConstraint('released_gross >= 0', name='released_gross_amount'),
        CheckConstraint('refunded_amount >= 0', name='refunded_amount_amount'),
        CheckConstraint('released_gross + refunded_amount + reserved_amount <= funded_amount', name='escrow_conservation'),
        Index('ix_escrow_accounts_milestone_id', 'milestone_id'),
        Index('ix_escrow_accounts_ledger_account_id', 'ledger_account_id'),
    )
