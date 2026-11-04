"""Freelancer ledger tables. Rules crossing rows belong in transactional services."""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core import freelancer_enums as fe
from app.models.base import ID, Base, pk
from app.models.freelancer_base import UTCDateTime, binary_string, state_type


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"

    id: Mapped[int] = pk()
    code: Mapped[str] = mapped_column(binary_string(150), nullable=False, unique=True)
    kind: Mapped[fe.LedgerAccountKind] = mapped_column(state_type(fe.LedgerAccountKind, "ledger_accounts_kind"), nullable=False)
    normal_side: Mapped[fe.PostingSide] = mapped_column(state_type(fe.PostingSide, "ledger_accounts_normal_side"), nullable=False)
    owner_user_id: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    milestone_id: Mapped[int | None] = mapped_column(ID, ForeignKey("milestones.id", ondelete="RESTRICT"), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default='VND', server_default='VND')
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("currency = 'VND'", name='vnd_only'),
        Index('ix_ledger_accounts_owner_user_id', 'owner_user_id'),
        Index('ix_ledger_accounts_milestone_id', 'milestone_id'),
    )


class LedgerJournal(Base):
    __tablename__ = "ledger_journals"

    id: Mapped[int] = pk()
    reference_type: Mapped[str] = mapped_column(String(40), nullable=False)
    reference_id: Mapped[int] = mapped_column(ID, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(binary_string(191), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    reversal_of_id: Mapped[int | None] = mapped_column(ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), nullable=True, unique=True)
    posted_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_ledger_journals_reference_type_reference_id', 'reference_type', 'reference_id'),
        Index('ix_ledger_journals_posted_at', 'posted_at'),
        Index('ix_ledger_journals_reversal_of_id', 'reversal_of_id'),
        Index('ix_ledger_journals_actor_user_id', 'actor_user_id'),
    )


class LedgerPosting(Base):
    __tablename__ = "ledger_postings"

    id: Mapped[int] = pk()
    journal_id: Mapped[int] = mapped_column(ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int] = mapped_column(ID, ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False)
    side: Mapped[fe.PostingSide] = mapped_column(state_type(fe.PostingSide, "ledger_postings_side"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint('line_no > 0', name='line_no_nonnegative'),
        CheckConstraint('amount > 0', name='amount_amount'),
        UniqueConstraint('journal_id', 'line_no', name='uq_ledger_postings_journal_id_line_no'),
        Index('ix_ledger_postings_account_id_journal_id', 'account_id', 'journal_id'),
        Index('ix_ledger_postings_account_id', 'account_id'),
    )
