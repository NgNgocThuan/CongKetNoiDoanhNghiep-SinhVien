"""Freelancer operations tables. Rules crossing rows belong in transactional services."""
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


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = pk()
    actor_user_id: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    actor_type: Mapped[fe.ActorType] = mapped_column(state_type(fe.ActorType, "audit_logs_actor_type"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    request_id: Mapped[str | None] = mapped_column(binary_string(100), nullable=True)
    job_key: Mapped[str | None] = mapped_column(binary_string(191), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    before_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(binary_string(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('ix_audit_logs_entity_type_entity_id_created_at', 'entity_type', 'entity_id', 'created_at'),
        Index('ix_audit_logs_actor_user_id_created_at', 'actor_user_id', 'created_at'),
        Index('ix_audit_logs_actor_user_id', 'actor_user_id'),
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[int] = pk()
    event_key: Mapped[str] = mapped_column(binary_string(191), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(ID, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[fe.OutboxStatus] = mapped_column(state_type(fe.OutboxStatus, "outbox_events_status"), nullable=False, default='PENDING', server_default='PENDING')
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    available_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    locked_by: Mapped[str | None] = mapped_column(binary_string(100), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('attempts >= 0', name='attempts_nonnegative'),
        Index('ix_outbox_events_status_available_at_lease_until', 'status', 'available_at', 'lease_until'),
    )


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = pk()
    job_key: Mapped[str] = mapped_column(binary_string(191), nullable=False, unique=True)
    job_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(ID, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    run_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    status: Mapped[fe.ScheduledJobStatus] = mapped_column(state_type(fe.ScheduledJobStatus, "scheduled_jobs_status"), nullable=False, default='PENDING', server_default='PENDING')
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default='0')
    lease_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    locked_by: Mapped[str | None] = mapped_column(binary_string(100), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('attempts >= 0', name='attempts_nonnegative'),
        Index('ix_scheduled_jobs_status_run_at_lease_until', 'status', 'run_at', 'lease_until'),
    )


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[int] = pk()
    period_from: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    period_until: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    status: Mapped[fe.ReconciliationRunStatus] = mapped_column(state_type(fe.ReconciliationRunStatus, "reconciliation_runs_status"), nullable=False, default='RUNNING', server_default='RUNNING')
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('period_until > period_from', name='period_dates'),
    )


class ReconciliationItem(Base):
    __tablename__ = "reconciliation_items"

    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ID, ForeignKey("reconciliation_runs.id", ondelete="RESTRICT"), nullable=False)
    issue_key: Mapped[str] = mapped_column(binary_string(191), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    actual_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[fe.ReconciliationItemStatus] = mapped_column(state_type(fe.ReconciliationItemStatus, "reconciliation_items_status"), nullable=False, default='OPEN', server_default='OPEN')
    resolved_by: Mapped[int | None] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('expected_amount >= 0', name='expected_amount_amount'),
        CheckConstraint('actual_amount >= 0', name='actual_amount_amount'),
        UniqueConstraint('run_id', 'issue_key', name='uq_reconciliation_items_run_id_issue_key'),
        Index('ix_reconciliation_items_status_created_at', 'status', 'created_at'),
        Index('ix_reconciliation_items_resolved_by', 'resolved_by'),
    )


class CommandRequest(Base):
    __tablename__ = "command_requests"

    id: Mapped[int] = pk()
    actor_user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(binary_string(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(binary_string(64), nullable=False)
    result_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result_entity_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('actor_user_id', 'operation', 'idempotency_key', name='uq_command_requests_actor_user_id_operation_idempotency_key'),
    )
