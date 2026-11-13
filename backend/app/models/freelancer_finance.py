"""Freelancer finance tables. Rules crossing rows belong in transactional services."""
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
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
from app.models.base import ID, Base, USmallInt, pk
from app.models.freelancer_base import UTCDateTime, binary_string, state_type


class BankDestination(Base):
    __tablename__ = "bank_destinations"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    bank_bin: Mapped[str] = mapped_column(String(20), nullable=False)
    account_number_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    account_fingerprint: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    account_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_status: Mapped[fe.BankDestinationStatus] = mapped_column(state_type(fe.BankDestinationStatus, "bank_destinations_verification_status"), nullable=False, default='ACTIVE', server_default='ACTIVE')
    verification_source: Mapped[str | None] = mapped_column(String(40), nullable=True)
    verified_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    encryption_key_version: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'bank_bin', 'account_fingerprint', name='uq_bank_destinations_user_id_bank_bin_account_fingerprint'),
        Index('ix_bank_destinations_verified_by', 'verified_by'),
    )


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = pk()
    milestone_id: Mapped[int] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[fe.SettlementKind] = mapped_column(state_type(fe.SettlementKind, "settlements_kind"), nullable=False)
    source: Mapped[fe.SettlementSource] = mapped_column(state_type(fe.SettlementSource, "settlements_source"), nullable=False)
    source_review_id: Mapped[int | None] = mapped_column(ID, ForeignKey("milestone_reviews.id", ondelete="RESTRICT"), nullable=True, unique=True)
    source_cancellation_id: Mapped[int | None] = mapped_column(ID, ForeignKey("cancellation_agreements.id", ondelete="RESTRICT"), nullable=True, unique=True)
    source_decision_id: Mapped[int | None] = mapped_column(ID, ForeignKey("dispute_decisions.id", ondelete="RESTRICT"), nullable=True, unique=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    freelancer_gross: Mapped[int] = mapped_column(BigInteger, nullable=False)
    refund_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fee_rate_bp: Mapped[int] = mapped_column(USmallInt, nullable=False)
    fee_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    net_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[fe.SettlementStatus] = mapped_column(state_type(fe.SettlementStatus, "settlements_status"), nullable=False, default='PREPARED', server_default='PREPARED')
    request_key: Mapped[str] = mapped_column(binary_string(191), nullable=False, unique=True)
    requested_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('sequence_no > 0', name='sequence_no_nonnegative'),
        CheckConstraint('amount > 0', name='amount_amount'),
        CheckConstraint('freelancer_gross >= 0', name='freelancer_gross_amount'),
        CheckConstraint('refund_amount >= 0', name='refund_amount_amount'),
        CheckConstraint('fee_rate_bp >= 0', name='fee_rate_bp_nonnegative'),
        CheckConstraint('fee_rate_bp <= 10000', name='fee_rate_bp_range'),
        CheckConstraint('fee_amount >= 0', name='fee_amount_amount'),
        CheckConstraint('net_amount >= 0', name='net_amount_amount'),
        UniqueConstraint('milestone_id', 'sequence_no', name='uq_settlements_milestone_id_sequence_no'),
        CheckConstraint('freelancer_gross + refund_amount = amount', name='settlement_total'),
        CheckConstraint('fee_amount + net_amount = freelancer_gross', name='settlement_fee'),
        CheckConstraint("(kind = 'RELEASE' AND refund_amount = 0 AND freelancer_gross > 0) OR (kind = 'REFUND' AND freelancer_gross = 0 AND refund_amount > 0) OR (kind = 'SPLIT' AND freelancer_gross > 0 AND refund_amount > 0)", name='settlement_kind_amounts'),
        CheckConstraint("(source IN ('ACCEPTANCE','AUTO_ACCEPT') AND source_review_id IS NOT NULL AND source_cancellation_id IS NULL AND source_decision_id IS NULL) OR (source = 'CANCELLATION' AND source_review_id IS NULL AND source_cancellation_id IS NOT NULL AND source_decision_id IS NULL) OR (source = 'DISPUTE' AND source_review_id IS NULL AND source_cancellation_id IS NULL AND source_decision_id IS NOT NULL)", name='settlement_source'),
        Index('ix_settlements_source_review_id', 'source_review_id'),
        Index('ix_settlements_source_cancellation_id', 'source_cancellation_id'),
        Index('ix_settlements_source_decision_id', 'source_decision_id'),
        Index('ix_settlements_requested_by', 'requested_by'),
    )


class MoneyTransfer(Base):
    __tablename__ = "money_transfers"

    id: Mapped[int] = pk()
    settlement_id: Mapped[int | None] = mapped_column(ID, ForeignKey("settlements.id", ondelete="RESTRICT"), nullable=True)
    payment_transaction_id: Mapped[int | None] = mapped_column(ID, ForeignKey("payment_transactions.id", ondelete="RESTRICT"), nullable=True)
    purpose: Mapped[fe.TransferPurpose] = mapped_column(state_type(fe.TransferPurpose, "money_transfers_purpose"), nullable=False)
    recipient_user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    destination_id: Mapped[int | None] = mapped_column(ID, ForeignKey("bank_destinations.id", ondelete="RESTRICT"), nullable=True)
    destination_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[fe.TransferStatus] = mapped_column(state_type(fe.TransferStatus, "money_transfers_status"), nullable=False, default='READY', server_default='READY')
    idempotency_key: Mapped[str] = mapped_column(binary_string(191), nullable=False, unique=True)
    provider_reference_id: Mapped[str] = mapped_column(binary_string(191), nullable=False, unique=True)
    payos_payout_id: Mapped[str | None] = mapped_column(binary_string(191), nullable=True, unique=True)
    payos_transaction_id: Mapped[str | None] = mapped_column(binary_string(191), nullable=True, unique=True)
    provider_approval_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    provider_transaction_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    obligation_journal_id: Mapped[int | None] = mapped_column(ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), nullable=True, unique=True)
    disbursement_journal_id: Mapped[int | None] = mapped_column(ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), nullable=True, unique=True)
    provider_fee_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fee_journal_id: Mapped[int | None] = mapped_column(ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), nullable=True, unique=True)
    succeeded_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    reserved_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    reservation_released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_amount'),
        CheckConstraint("(status = 'WAITING_BANK' AND destination_id IS NULL) OR (status <> 'WAITING_BANK' AND destination_id IS NOT NULL)", name='transfer_bank_state'),
        CheckConstraint('provider_fee_amount >= 0', name='provider_fee_amount_amount'),
        UniqueConstraint('settlement_id', 'purpose', name='uq_money_transfers_settlement_id_purpose'),
        CheckConstraint("(purpose IN ('RELEASE','REFUND') AND settlement_id IS NOT NULL AND payment_transaction_id IS NULL) OR (purpose = 'UNALLOCATED_REFUND' AND settlement_id IS NULL AND payment_transaction_id IS NOT NULL)", name='transfer_source'),
        Index('ix_money_transfers_payment_transaction_id', 'payment_transaction_id'),
        Index('ix_money_transfers_recipient_user_id', 'recipient_user_id'),
        Index('ix_money_transfers_destination_id', 'destination_id'),
        Index('ix_money_transfers_obligation_journal_id', 'obligation_journal_id'),
        Index('ix_money_transfers_disbursement_journal_id', 'disbursement_journal_id'),
        Index('ix_money_transfers_fee_journal_id', 'fee_journal_id'),
    )


class TransferAttempt(Base):
    __tablename__ = "transfer_attempts"

    id: Mapped[int] = pk()
    transfer_id: Mapped[int] = mapped_column(ID, ForeignKey("money_transfers.id", ondelete="RESTRICT"), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    operation: Mapped[fe.TransferOperation] = mapped_column(state_type(fe.TransferOperation, "transfer_attempts_operation"), nullable=False)
    status: Mapped[fe.TransferAttemptStatus] = mapped_column(state_type(fe.TransferAttemptStatus, "transfer_attempts_status"), nullable=False, default='STARTED', server_default='STARTED')
    request_hash: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    provider_response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    next_check_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('attempt_no > 0', name='attempt_no_nonnegative'),
        UniqueConstraint('transfer_id', 'attempt_no', name='uq_transfer_attempts_transfer_id_attempt_no'),
    )


class DailyLimitBucket(Base):
    __tablename__ = "daily_limit_buckets"

    id: Mapped[int] = pk()
    scope_key: Mapped[str] = mapped_column(binary_string(100), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    limit_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reserved_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default='0')
    consumed_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default='0')
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('limit_amount > 0', name='limit_amount_amount'),
        CheckConstraint('reserved_amount >= 0', name='reserved_amount_amount'),
        CheckConstraint('consumed_amount >= 0', name='consumed_amount_amount'),
        UniqueConstraint('scope_key', 'local_date', name='uq_daily_limit_buckets_scope_key_local_date'),
        CheckConstraint('reserved_amount + consumed_amount <= limit_amount', name='limit_conservation'),
    )


class DailyLimitReservation(Base):
    __tablename__ = "daily_limit_reservations"

    id: Mapped[int] = pk()
    bucket_id: Mapped[int] = mapped_column(ID, ForeignKey("daily_limit_buckets.id", ondelete="RESTRICT"), nullable=False)
    payment_order_id: Mapped[int | None] = mapped_column(ID, ForeignKey("payment_orders.id", ondelete="RESTRICT"), nullable=True)
    money_transfer_id: Mapped[int | None] = mapped_column(ID, ForeignKey("money_transfers.id", ondelete="RESTRICT"), nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[fe.LimitReservationStatus] = mapped_column(state_type(fe.LimitReservationStatus, "daily_limit_reservations_status"), nullable=False, default='RESERVED', server_default='RESERVED')
    consumed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_amount'),
        UniqueConstraint('bucket_id', 'payment_order_id', name='uq_daily_limit_reservations_bucket_id_payment_order_id'),
        UniqueConstraint('bucket_id', 'money_transfer_id', name='uq_daily_limit_reservations_bucket_id_money_transfer_id'),
        CheckConstraint('(payment_order_id IS NOT NULL AND money_transfer_id IS NULL) OR (payment_order_id IS NULL AND money_transfer_id IS NOT NULL)', name='limit_source'),
        Index('ix_daily_limit_reservations_payment_order_id', 'payment_order_id'),
        Index('ix_daily_limit_reservations_money_transfer_id', 'money_transfer_id'),
    )
