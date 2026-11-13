"""A single database gate orders all real-money writers and allocates order codes."""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ID, Base, pk
from app.models.freelancer_base import UTCDateTime, binary_string


class FinanceCounter(Base):
    __tablename__ = "finance_counters"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    next_value: Mapped[int] = mapped_column(BigInteger, nullable=False)


class TreasuryEntry(Base):
    """Evidence-backed external treasury movement; requires a second administrator."""

    __tablename__ = "treasury_entries"
    id: Mapped[int] = pk()
    external_reference: Mapped[str] = mapped_column(binary_string(150), unique=True)
    kind: Mapped[str] = mapped_column(String(30))
    amount: Mapped[int] = mapped_column(BigInteger)
    evidence_file_id: Mapped[int] = mapped_column(
        ID, ForeignKey("stored_files.id", ondelete="RESTRICT"), index=True
    )
    proposed_by: Mapped[int] = mapped_column(
        ID, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    approved_by: Mapped[int | None] = mapped_column(
        ID, ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="PROPOSED", server_default="PROPOSED")
    journal_id: Mapped[int | None] = mapped_column(
        ID, ForeignKey("ledger_journals.id", ondelete="RESTRICT"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, server_default=func.now())
    posted_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
        CheckConstraint(
            "kind IN ('TRANSFER_TO_PAYOUT','EQUITY_BANK','EQUITY_PAYOUT','FEE_BANK','FEE_PAYOUT')",
            name="valid_kind",
        ),
        CheckConstraint("status IN ('PROPOSED','POSTED','REJECTED')", name="valid_status"),
        CheckConstraint(
            "approved_by IS NULL OR approved_by <> proposed_by", name="distinct_approvers"
        ),
    )
