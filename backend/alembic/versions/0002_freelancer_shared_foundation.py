"""freelancer shared foundation

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04 16:54:59.689545
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen table list: downgrade refuses to discard any Freelancer records.
NEW_TABLES = ('daily_limit_buckets', 'outbox_events', 'provider_events', 'reconciliation_runs', 'scheduled_jobs', 'audit_logs', 'bank_destinations', 'client_profiles', 'command_requests', 'ledger_journals', 'reconciliation_items', 'stored_files', 'user_verifications', 'business_verifications', 'company_limits', 'freelance_projects', 'mou_agreements', 'business_verification_files', 'freelance_applications', 'freelance_project_reviews', 'freelance_project_skills', 'project_milestone_proposals', 'freelance_contracts', 'contract_versions', 'freelance_reviews', 'milestones', 'project_contract_budgets', 'cancellation_agreements', 'contract_milestone_terms', 'deliverables', 'disputes', 'ledger_accounts', 'payment_orders', 'active_milestone_disputes', 'deliverable_files', 'dispute_decisions', 'dispute_evidence', 'escrow_accounts', 'ledger_postings', 'milestone_funding_guards', 'milestone_holds', 'milestone_reviews', 'payment_transactions', 'milestone_fundings', 'payment_review_cases', 'settlements', 'money_transfers', 'daily_limit_reservations', 'transfer_attempts')


def _install_append_only_guards() -> None:
    dialect = op.get_bind().dialect.name
    for table in ("ledger_journals", "ledger_postings", "audit_logs"):
        for action in ("UPDATE", "DELETE"):
            trigger = f"trg_{table}_{action.lower()}_blocked"
            if dialect == "sqlite":
                op.execute(sa.text(f"CREATE TRIGGER {trigger} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'append-only table'); END"))
            elif dialect in ("mysql", "mariadb"):
                op.execute(sa.text(f"CREATE TRIGGER {trigger} BEFORE {action} ON {table} FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'append-only table'"))


def _drop_append_only_guards() -> None:
    for table in ("ledger_journals", "ledger_postings", "audit_logs"):
        for action in ("update", "delete"):
            op.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_{table}_{action}_blocked"))


def upgrade() -> None:
    # Frozen schema; deliberately independent of live application models.
    op.create_table('daily_limit_buckets',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('scope_key', sa.String(length=100).with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('local_date', sa.Date(), nullable=False),
    sa.Column('limit_amount', sa.BigInteger(), nullable=False),
    sa.Column('reserved_amount', sa.BigInteger(), server_default='0', nullable=False),
    sa.Column('consumed_amount', sa.BigInteger(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('consumed_amount >= 0', name=op.f('ck_daily_limit_buckets_consumed_amount_amount')),
    sa.CheckConstraint('limit_amount > 0', name=op.f('ck_daily_limit_buckets_limit_amount_amount')),
    sa.CheckConstraint('reserved_amount + consumed_amount <= limit_amount', name=op.f('ck_daily_limit_buckets_limit_conservation')),
    sa.CheckConstraint('reserved_amount >= 0', name=op.f('ck_daily_limit_buckets_reserved_amount_amount')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_daily_limit_buckets')),
    sa.UniqueConstraint('scope_key', 'local_date', name=op.f('uq_daily_limit_buckets_scope_key_local_date'))
    )
    op.create_table('outbox_events',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('event_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('event_type', sa.String(length=60), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'SUCCEEDED', 'RETRY', 'DEAD', name='outbox_events_status', native_enum=False, create_constraint=True, length=40), server_default='PENDING', nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('available_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('lease_until', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('locked_by', sa.String(length=100).with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('completed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_outbox_events_attempts_nonnegative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_outbox_events')),
    sa.UniqueConstraint('event_key', name=op.f('uq_outbox_events_event_key'))
    )
    op.create_index('ix_outbox_events_status_available_at_lease_until', 'outbox_events', ['status', 'available_at', 'lease_until'], unique=False)
    op.create_table('provider_events',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('channel_key', sa.String(length=100).with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('event_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('event_type', sa.Enum('PAYMENT', 'PAYOUT', name='provider_events_event_type', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('payload_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.Enum('RECEIVED', 'PROCESSING', 'PROCESSED', 'UNMATCHED', 'RETRY', 'DEAD', 'PROBE', name='provider_events_status', native_enum=False, create_constraint=True, length=40), server_default='RECEIVED', nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('available_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('lease_until', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('processed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_provider_events_attempts_nonnegative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_provider_events')),
    sa.UniqueConstraint('channel_key', 'event_key', name=op.f('uq_provider_events_channel_key_event_key'))
    )
    op.create_index('ix_provider_events_status_available_at_lease_until', 'provider_events', ['status', 'available_at', 'lease_until'], unique=False)
    op.create_table('reconciliation_runs',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('period_from', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('period_until', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('status', sa.Enum('RUNNING', 'SUCCEEDED', 'FAILED', name='reconciliation_runs_status', native_enum=False, create_constraint=True, length=40), server_default='RUNNING', nullable=False),
    sa.Column('summary_json', sa.JSON(), nullable=True),
    sa.Column('started_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('finished_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('period_until > period_from', name=op.f('ck_reconciliation_runs_period_dates')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reconciliation_runs'))
    )
    op.create_table('scheduled_jobs',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('job_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('job_type', sa.String(length=60), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('run_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'SUCCEEDED', 'RETRY', 'CANCELLED', 'DEAD', name='scheduled_jobs_status', native_enum=False, create_constraint=True, length=40), server_default='PENDING', nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('lease_until', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('locked_by', sa.String(length=100).with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('finished_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_scheduled_jobs_attempts_nonnegative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scheduled_jobs')),
    sa.UniqueConstraint('job_key', name=op.f('uq_scheduled_jobs_job_key'))
    )
    op.create_index('ix_scheduled_jobs_status_run_at_lease_until', 'scheduled_jobs', ['status', 'run_at', 'lease_until'], unique=False)
    op.create_table('audit_logs',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('actor_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('actor_type', sa.Enum('USER', 'SYSTEM', 'PROVIDER', name='audit_logs_actor_type', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('request_id', sa.String(length=100).with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('job_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('before_json', sa.JSON(), nullable=True),
    sa.Column('after_json', sa.JSON(), nullable=True),
    sa.Column('ip_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_audit_logs_actor_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index('ix_audit_logs_actor_user_id', 'audit_logs', ['actor_user_id'], unique=False)
    op.create_index('ix_audit_logs_actor_user_id_created_at', 'audit_logs', ['actor_user_id', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_entity_type_entity_id_created_at', 'audit_logs', ['entity_type', 'entity_id', 'created_at'], unique=False)
    op.create_table('bank_destinations',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('bank_bin', sa.String(length=20), nullable=False),
    sa.Column('account_number_ciphertext', sa.Text(), nullable=False),
    sa.Column('account_fingerprint', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('account_last4', sa.String(length=4), nullable=False),
    sa.Column('account_name', sa.String(length=255), nullable=False),
    sa.Column('verification_status', sa.Enum('PENDING', 'VERIFIED', 'REJECTED', 'DISABLED', name='bank_destinations_verification_status', native_enum=False, create_constraint=True, length=40), server_default='PENDING', nullable=False),
    sa.Column('verification_source', sa.String(length=40), nullable=True),
    sa.Column('verified_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('verified_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('verification_note', sa.Text(), nullable=True),
    sa.Column('encryption_key_version', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_bank_destinations_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['verified_by'], ['users.id'], name=op.f('fk_bank_destinations_verified_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bank_destinations')),
    sa.UniqueConstraint('user_id', 'bank_bin', 'account_fingerprint', name=op.f('uq_bank_destinations_user_id_bank_bin_account_fingerprint'))
    )
    op.create_index('ix_bank_destinations_verified_by', 'bank_destinations', ['verified_by'], unique=False)
    op.create_table('client_profiles',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('address', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_client_profiles_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_client_profiles')),
    sa.UniqueConstraint('user_id', name=op.f('uq_client_profiles_user_id'))
    )
    op.create_index('ix_client_profiles_user_id', 'client_profiles', ['user_id'], unique=False)
    op.create_table('command_requests',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('actor_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('operation', sa.String(length=80), nullable=False),
    sa.Column('idempotency_key', sa.String(length=128).with_variant(sa.String(length=128, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=128, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('request_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('result_entity_type', sa.String(length=50), nullable=True),
    sa.Column('result_entity_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('response_json', sa.JSON(), nullable=True),
    sa.Column('completed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_command_requests_actor_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_command_requests')),
    sa.UniqueConstraint('actor_user_id', 'operation', 'idempotency_key', name=op.f('uq_command_requests_actor_user_id_operation_idempotency_key'))
    )
    op.create_table('ledger_journals',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('reference_type', sa.String(length=40), nullable=False),
    sa.Column('reference_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('idempotency_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=False),
    sa.Column('reversal_of_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('posted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('actor_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_ledger_journals_actor_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reversal_of_id'], ['ledger_journals.id'], name=op.f('fk_ledger_journals_reversal_of_id_ledger_journals'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ledger_journals')),
    sa.UniqueConstraint('idempotency_key', name=op.f('uq_ledger_journals_idempotency_key')),
    sa.UniqueConstraint('reversal_of_id', name=op.f('uq_ledger_journals_reversal_of_id'))
    )
    op.create_index('ix_ledger_journals_actor_user_id', 'ledger_journals', ['actor_user_id'], unique=False)
    op.create_index('ix_ledger_journals_posted_at', 'ledger_journals', ['posted_at'], unique=False)
    op.create_index('ix_ledger_journals_reference_type_reference_id', 'ledger_journals', ['reference_type', 'reference_id'], unique=False)
    op.create_index('ix_ledger_journals_reversal_of_id', 'ledger_journals', ['reversal_of_id'], unique=False)
    op.create_table('reconciliation_items',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('run_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('issue_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('issue_type', sa.String(length=50), nullable=False),
    sa.Column('expected_amount', sa.BigInteger(), nullable=True),
    sa.Column('actual_amount', sa.BigInteger(), nullable=True),
    sa.Column('details_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.Enum('OPEN', 'RESOLVED', 'ACKNOWLEDGED', name='reconciliation_items_status', native_enum=False, create_constraint=True, length=40), server_default='OPEN', nullable=False),
    sa.Column('resolved_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('resolved_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('resolution_note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('actual_amount >= 0', name=op.f('ck_reconciliation_items_actual_amount_amount')),
    sa.CheckConstraint('expected_amount >= 0', name=op.f('ck_reconciliation_items_expected_amount_amount')),
    sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], name=op.f('fk_reconciliation_items_resolved_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['run_id'], ['reconciliation_runs.id'], name=op.f('fk_reconciliation_items_run_id_reconciliation_runs'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reconciliation_items')),
    sa.UniqueConstraint('run_id', 'issue_key', name=op.f('uq_reconciliation_items_run_id_issue_key'))
    )
    op.create_index('ix_reconciliation_items_resolved_by', 'reconciliation_items', ['resolved_by'], unique=False)
    op.create_index('ix_reconciliation_items_status_created_at', 'reconciliation_items', ['status', 'created_at'], unique=False)
    op.create_table('stored_files',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('uploaded_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('storage_key', sa.String(length=500).with_variant(sa.String(length=500, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=500, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('original_name', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=150), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('checksum_sha256', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('category', sa.String(length=40), nullable=False),
    sa.Column('scan_status', sa.Enum('PENDING', 'CLEAN', 'REJECTED', name='stored_files_scan_status', native_enum=False, create_constraint=True, length=40), server_default='PENDING', nullable=False),
    sa.Column('availability_status', sa.Enum('AVAILABLE', 'QUARANTINED', 'REMOVED', name='stored_files_availability_status', native_enum=False, create_constraint=True, length=40), server_default='AVAILABLE', nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('size_bytes > 0', name=op.f('ck_stored_files_size_bytes_nonnegative')),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], name=op.f('fk_stored_files_uploaded_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stored_files')),
    sa.UniqueConstraint('storage_key', name=op.f('uq_stored_files_storage_key'))
    )
    op.create_index('ix_stored_files_checksum_sha256', 'stored_files', ['checksum_sha256'], unique=False)
    op.create_index('ix_stored_files_uploaded_by', 'stored_files', ['uploaded_by'], unique=False)
    op.create_index('ix_stored_files_uploaded_by_created_at', 'stored_files', ['uploaded_by', 'created_at'], unique=False)
    op.create_table('user_verifications',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('channel', sa.Enum('EMAIL', 'PHONE', name='user_verifications_channel', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('purpose', sa.Enum('VERIFY_CONTACT', 'CHANGE_CONTACT', name='user_verifications_purpose', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('target', sa.String(length=255), nullable=False),
    sa.Column('otp_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('key_version', sa.String(length=30), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'VERIFIED', 'EXPIRED', 'LOCKED', 'SUPERSEDED', name='user_verifications_status', native_enum=False, create_constraint=True, length=40), server_default='PENDING', nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('max_attempts', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('resend_after', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('verified_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('attempts <= max_attempts', name=op.f('ck_user_verifications_attempt_limit')),
    sa.CheckConstraint('attempts >= 0', name=op.f('ck_user_verifications_attempts_nonnegative')),
    sa.CheckConstraint('max_attempts > 0', name=op.f('ck_user_verifications_max_attempts_nonnegative')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_verifications_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_verifications'))
    )
    op.create_index('ix_user_verifications_status_expires_at', 'user_verifications', ['status', 'expires_at'], unique=False)
    op.create_index('ix_user_verifications_user_id', 'user_verifications', ['user_id'], unique=False)
    op.create_index('ix_user_verifications_user_id_channel_created_at', 'user_verifications', ['user_id', 'channel', 'created_at'], unique=False)
    op.create_table('business_verifications',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('submission_no', sa.Integer(), nullable=False),
    sa.Column('submitted_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('submitted_snapshot', sa.JSON(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'NEEDS_REVISION', 'APPROVED', 'REJECTED', name='business_verifications_status', native_enum=False, create_constraint=True, length=40), server_default='PENDING', nullable=False),
    sa.Column('decided_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('decided_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('submission_no > 0', name=op.f('ck_business_verifications_submission_no_nonnegative')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_business_verifications_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['decided_by'], ['users.id'], name=op.f('fk_business_verifications_decided_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], name=op.f('fk_business_verifications_submitted_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_business_verifications')),
    sa.UniqueConstraint('company_id', 'submission_no', name=op.f('uq_business_verifications_company_id_submission_no'))
    )
    op.create_index('ix_business_verifications_decided_by', 'business_verifications', ['decided_by'], unique=False)
    op.create_index('ix_business_verifications_status_created_at', 'business_verifications', ['status', 'created_at'], unique=False)
    op.create_index('ix_business_verifications_submitted_by', 'business_verifications', ['submitted_by'], unique=False)
    op.create_table('company_limits',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('max_open_projects', sa.Integer(), nullable=False),
    sa.Column('max_project_amount', sa.BigInteger(), nullable=False),
    sa.Column('max_daily_funding', sa.BigInteger(), nullable=False),
    sa.Column('full_prefunding_required', sa.Boolean(), nullable=False),
    sa.Column('source', sa.Enum('VERIFIED', 'PARTNER', 'OVERRIDE', name='company_limits_source', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('set_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('max_daily_funding > 0', name=op.f('ck_company_limits_max_daily_funding_amount')),
    sa.CheckConstraint('max_open_projects > 0', name=op.f('ck_company_limits_max_open_projects_nonnegative')),
    sa.CheckConstraint('max_project_amount > 0', name=op.f('ck_company_limits_max_project_amount_amount')),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_company_limits_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['set_by'], ['users.id'], name=op.f('fk_company_limits_set_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_company_limits')),
    sa.UniqueConstraint('company_id', name=op.f('uq_company_limits_company_id'))
    )
    op.create_index('ix_company_limits_company_id', 'company_limits', ['company_id'], unique=False)
    op.create_index('ix_company_limits_set_by', 'company_limits', ['set_by'], unique=False)
    op.create_table('freelance_projects',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('client_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('company_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('budget_amount', sa.BigInteger(), nullable=False),
    sa.Column('max_students', sa.Integer(), nullable=False),
    sa.Column('recruitment_status', sa.Enum('NOT_OPEN', 'OPEN', 'CLOSED', name='freelance_projects_recruitment_status', native_enum=False, create_constraint=True, length=40), server_default='NOT_OPEN', nullable=False),
    sa.Column('recruitment_closed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('deadline', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('acceptance_criteria', sa.Text(), nullable=False),
    sa.Column('deliverables_description', sa.Text(), nullable=False),
    sa.Column('funding_policy', sa.Enum('FULL', 'PER_MILESTONE', name='freelance_projects_funding_policy', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'IN_PROGRESS', 'COMPLETED', 'NEEDS_REVISION', 'REJECTED', 'CANCELLED', 'CLOSED', name='freelance_projects_status', native_enum=False, create_constraint=True, length=40), server_default='DRAFT', nullable=False),
    sa.Column('submitted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('reviewed_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('reviewed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('review_reason', sa.Text(), nullable=True),
    sa.Column('closed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('budget_amount > 0', name=op.f('ck_freelance_projects_budget_amount_amount')),
    sa.CheckConstraint('max_students > 0', name=op.f('ck_freelance_projects_max_students_nonnegative')),
    sa.ForeignKeyConstraint(['client_user_id'], ['users.id'], name=op.f('fk_freelance_projects_client_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_freelance_projects_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name=op.f('fk_freelance_projects_reviewed_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_freelance_projects'))
    )
    op.create_index('ix_freelance_projects_client_user_id', 'freelance_projects', ['client_user_id'], unique=False)
    op.create_index('ix_freelance_projects_client_user_id_status', 'freelance_projects', ['client_user_id', 'status'], unique=False)
    op.create_index('ix_freelance_projects_company_id', 'freelance_projects', ['company_id'], unique=False)
    op.create_index('ix_freelance_projects_company_id_status', 'freelance_projects', ['company_id', 'status'], unique=False)
    op.create_index('ix_freelance_projects_reviewed_by', 'freelance_projects', ['reviewed_by'], unique=False)
    op.create_index('ix_freelance_projects_status_recruitment_status_created_at', 'freelance_projects', ['status', 'recruitment_status', 'created_at'], unique=False)
    op.create_table('mou_agreements',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('agreement_code', sa.String(length=100).with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('document_file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('school_name', sa.String(length=255), nullable=False),
    sa.Column('school_signer_name', sa.String(length=255), nullable=False),
    sa.Column('company_signer_name', sa.String(length=255), nullable=False),
    sa.Column('school_signer_position', sa.String(length=100), nullable=False),
    sa.Column('company_signer_position', sa.String(length=100), nullable=False),
    sa.Column('company_authority_file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('school_authority_file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('signature_method', sa.Enum('SCANNED_SIGNED_DOCUMENT', 'EXTERNALLY_DIGITALLY_SIGNED', name='mou_agreements_signature_method', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('signature_verification_status', sa.Enum('NOT_CHECKED', 'MANUALLY_REVIEWED', 'CRYPTOGRAPHICALLY_VERIFIED', 'FAILED', name='mou_agreements_signature_verification_status', native_enum=False, create_constraint=True, length=40), server_default='NOT_CHECKED', nullable=False),
    sa.Column('signed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('effective_from', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('effective_until', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('scope_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.Enum('PENDING_REVIEW', 'ACTIVE', 'REJECTED', 'EXPIRED', 'REVOKED', 'SUPERSEDED', name='mou_agreements_status', native_enum=False, create_constraint=True, length=40), server_default='PENDING_REVIEW', nullable=False),
    sa.Column('reviewed_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('reviewed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('effective_until > effective_from', name=op.f('ck_mou_agreements_effective_dates')),
    sa.ForeignKeyConstraint(['company_authority_file_id'], ['stored_files.id'], name=op.f('fk_mou_agreements_company_authority_file_id_stored_files'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_mou_agreements_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['document_file_id'], ['stored_files.id'], name=op.f('fk_mou_agreements_document_file_id_stored_files'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name=op.f('fk_mou_agreements_reviewed_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['school_authority_file_id'], ['stored_files.id'], name=op.f('fk_mou_agreements_school_authority_file_id_stored_files'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mou_agreements')),
    sa.UniqueConstraint('agreement_code', name=op.f('uq_mou_agreements_agreement_code'))
    )
    op.create_index('ix_mou_agreements_company_authority_file_id', 'mou_agreements', ['company_authority_file_id'], unique=False)
    op.create_index('ix_mou_agreements_company_id', 'mou_agreements', ['company_id'], unique=False)
    op.create_index('ix_mou_agreements_company_id_status_effective_until', 'mou_agreements', ['company_id', 'status', 'effective_until'], unique=False)
    op.create_index('ix_mou_agreements_document_file_id', 'mou_agreements', ['document_file_id'], unique=False)
    op.create_index('ix_mou_agreements_reviewed_by', 'mou_agreements', ['reviewed_by'], unique=False)
    op.create_index('ix_mou_agreements_school_authority_file_id', 'mou_agreements', ['school_authority_file_id'], unique=False)
    op.create_index('ix_mou_agreements_status_effective_until', 'mou_agreements', ['status', 'effective_until'], unique=False)
    op.create_table('business_verification_files',
    sa.Column('verification_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('document_type', sa.Enum('BUSINESS_LICENSE', 'TAX_CERTIFICATE', 'AUTHORIZATION', 'OTHER', name='business_verification_files_document_type', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['stored_files.id'], name=op.f('fk_business_verification_files_file_id_stored_files'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['verification_id'], ['business_verifications.id'], name=op.f('fk_business_verification_files_verification_id_business_verifications'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('verification_id', 'file_id', name=op.f('pk_business_verification_files'))
    )
    op.create_index('ix_business_verification_files_file_id', 'business_verification_files', ['file_id'], unique=False)
    op.create_index('ix_business_verification_files_verification_id', 'business_verification_files', ['verification_id'], unique=False)
    op.create_table('freelance_applications',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('project_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('student_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('proposal', sa.Text(), nullable=False),
    sa.Column('quoted_amount', sa.BigInteger(), nullable=False),
    sa.Column('estimated_days', sa.Integer(), nullable=False),
    sa.Column('cv_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('cv_snapshot_file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('status', sa.Enum('SUBMITTED', 'SHORTLISTED', 'SELECTED', 'REJECTED', 'WITHDRAWN', name='freelance_applications_status', native_enum=False, create_constraint=True, length=40), server_default='SUBMITTED', nullable=False),
    sa.Column('selected_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('estimated_days > 0', name=op.f('ck_freelance_applications_estimated_days_nonnegative')),
    sa.CheckConstraint('quoted_amount > 0', name=op.f('ck_freelance_applications_quoted_amount_amount')),
    sa.ForeignKeyConstraint(['cv_id'], ['cvs.id'], name=op.f('fk_freelance_applications_cv_id_cvs'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['cv_snapshot_file_id'], ['stored_files.id'], name=op.f('fk_freelance_applications_cv_snapshot_file_id_stored_files'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['project_id'], ['freelance_projects.id'], name=op.f('fk_freelance_applications_project_id_freelance_projects'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_freelance_applications_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_freelance_applications')),
    sa.UniqueConstraint('project_id', 'student_id', name=op.f('uq_freelance_applications_project_id_student_id'))
    )
    op.create_index('ix_freelance_applications_cv_id', 'freelance_applications', ['cv_id'], unique=False)
    op.create_index('ix_freelance_applications_cv_snapshot_file_id', 'freelance_applications', ['cv_snapshot_file_id'], unique=False)
    op.create_index('ix_freelance_applications_project_id_status', 'freelance_applications', ['project_id', 'status'], unique=False)
    op.create_index('ix_freelance_applications_student_id', 'freelance_applications', ['student_id'], unique=False)
    op.create_index('ix_freelance_applications_student_id_status_created_at', 'freelance_applications', ['student_id', 'status', 'created_at'], unique=False)
    op.create_table('freelance_project_reviews',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('project_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('reviewed_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('decision', sa.Enum('APPROVED', 'NEEDS_REVISION', 'REJECTED', name='freelance_project_reviews_decision', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('project_snapshot', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['freelance_projects.id'], name=op.f('fk_freelance_project_reviews_project_id_freelance_projects'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name=op.f('fk_freelance_project_reviews_reviewed_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_freelance_project_reviews'))
    )
    op.create_index('ix_freelance_project_reviews_project_id', 'freelance_project_reviews', ['project_id'], unique=False)
    op.create_index('ix_freelance_project_reviews_project_id_created_at', 'freelance_project_reviews', ['project_id', 'created_at'], unique=False)
    op.create_index('ix_freelance_project_reviews_reviewed_by', 'freelance_project_reviews', ['reviewed_by'], unique=False)
    op.create_table('freelance_project_skills',
    sa.Column('project_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('skill_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('is_required', sa.Boolean(), server_default='1', nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['freelance_projects.id'], name=op.f('fk_freelance_project_skills_project_id_freelance_projects'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_freelance_project_skills_skill_id_skills'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('project_id', 'skill_id', name=op.f('pk_freelance_project_skills'))
    )
    op.create_index('ix_freelance_project_skills_project_id', 'freelance_project_skills', ['project_id'], unique=False)
    op.create_index('ix_freelance_project_skills_skill_id', 'freelance_project_skills', ['skill_id'], unique=False)
    op.create_table('project_milestone_proposals',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('project_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('sequence_no', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('acceptance_criteria', sa.Text(), nullable=False),
    sa.Column('due_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('amount > 0', name=op.f('ck_project_milestone_proposals_amount_amount')),
    sa.CheckConstraint('sequence_no > 0', name=op.f('ck_project_milestone_proposals_sequence_no_nonnegative')),
    sa.ForeignKeyConstraint(['project_id'], ['freelance_projects.id'], name=op.f('fk_project_milestone_proposals_project_id_freelance_projects'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_project_milestone_proposals')),
    sa.UniqueConstraint('project_id', 'sequence_no', name=op.f('uq_project_milestone_proposals_project_id_sequence_no'))
    )
    op.create_table('freelance_contracts',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('project_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('application_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('client_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('company_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('freelancer_student_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'PENDING_ACCEPTANCE', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'TERMINATED', name='freelance_contracts_status', native_enum=False, create_constraint=True, length=40), server_default='DRAFT', nullable=False),
    sa.Column('effective_version_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('activated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('closed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('closure_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['freelance_applications.id'], name=op.f('fk_freelance_contracts_application_id_freelance_applications'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['client_user_id'], ['users.id'], name=op.f('fk_freelance_contracts_client_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], name=op.f('fk_freelance_contracts_company_id_companies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['freelancer_student_id'], ['students.id'], name=op.f('fk_freelance_contracts_freelancer_student_id_students'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['id', 'effective_version_id'], ['contract_versions.contract_id', 'contract_versions.id'], name='fk_fc_effective_version', ondelete='RESTRICT', use_alter=True),
    sa.ForeignKeyConstraint(['project_id'], ['freelance_projects.id'], name=op.f('fk_freelance_contracts_project_id_freelance_projects'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_freelance_contracts')),
    sa.UniqueConstraint('application_id', name=op.f('uq_freelance_contracts_application_id')),
    sa.UniqueConstraint('project_id', 'freelancer_student_id', name=op.f('uq_freelance_contracts_project_id_freelancer_student_id')),
    sa.UniqueConstraint('project_id', 'id', name=op.f('uq_freelance_contracts_project_id_id'))
    )
    op.create_index('ix_freelance_contracts_application_id', 'freelance_contracts', ['application_id'], unique=False)
    op.create_index('ix_freelance_contracts_client_user_id', 'freelance_contracts', ['client_user_id'], unique=False)
    op.create_index('ix_freelance_contracts_client_user_id_status', 'freelance_contracts', ['client_user_id', 'status'], unique=False)
    op.create_index('ix_freelance_contracts_company_id', 'freelance_contracts', ['company_id'], unique=False)
    op.create_index('ix_freelance_contracts_freelancer_student_id', 'freelance_contracts', ['freelancer_student_id'], unique=False)
    op.create_index('ix_freelance_contracts_freelancer_student_id_status', 'freelance_contracts', ['freelancer_student_id', 'status'], unique=False)
    op.create_index('ix_freelance_contracts_project_id_status', 'freelance_contracts', ['project_id', 'status'], unique=False)
    op.create_table('contract_versions',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('contract_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('version_no', sa.Integer(), nullable=False),
    sa.Column('created_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'OFFERED', 'EFFECTIVE', 'DECLINED', 'WITHDRAWN', 'SUPERSEDED', 'EXPIRED', name='contract_versions_status', native_enum=False, create_constraint=True, length=40), server_default='DRAFT', nullable=False),
    sa.Column('total_amount', sa.BigInteger(), nullable=False),
    sa.Column('fee_rate_bp', sa.SmallInteger().with_variant(mysql.SMALLINT(unsigned=True), 'mariadb').with_variant(mysql.SMALLINT(unsigned=True), 'mysql'), nullable=False),
    sa.Column('review_period_seconds', sa.Integer(), nullable=False),
    sa.Column('max_revision_count', sa.Integer(), nullable=False),
    sa.Column('grace_period_seconds', sa.Integer(), nullable=False),
    sa.Column('funding_policy', sa.Enum('FULL', 'PER_MILESTONE', name='contract_versions_funding_policy', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('terms_json', sa.JSON(), nullable=False),
    sa.Column('content_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('offered_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('acceptance_deadline', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('client_accepted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('freelancer_accepted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('effective_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('response_note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('fee_rate_bp < 10000', name=op.f('ck_contract_versions_fee_below_gross')),
    sa.CheckConstraint('fee_rate_bp <= 10000', name=op.f('ck_contract_versions_fee_rate_bp_range')),
    sa.CheckConstraint('fee_rate_bp >= 0', name=op.f('ck_contract_versions_fee_rate_bp_nonnegative')),
    sa.CheckConstraint('grace_period_seconds >= 0', name=op.f('ck_contract_versions_grace_period_seconds_nonnegative')),
    sa.CheckConstraint('max_revision_count >= 0', name=op.f('ck_contract_versions_max_revision_count_nonnegative')),
    sa.CheckConstraint('review_period_seconds > 0', name=op.f('ck_contract_versions_review_period_seconds_nonnegative')),
    sa.CheckConstraint('total_amount > 0', name=op.f('ck_contract_versions_total_amount_amount')),
    sa.CheckConstraint('version_no > 0', name=op.f('ck_contract_versions_version_no_nonnegative')),
    sa.ForeignKeyConstraint(['contract_id'], ['freelance_contracts.id'], name=op.f('fk_contract_versions_contract_id_freelance_contracts'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_contract_versions_created_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_contract_versions')),
    sa.UniqueConstraint('contract_id', 'id', name=op.f('uq_contract_versions_contract_id_id')),
    sa.UniqueConstraint('contract_id', 'version_no', name=op.f('uq_contract_versions_contract_id_version_no'))
    )
    op.create_index('ix_contract_versions_created_by', 'contract_versions', ['created_by'], unique=False)
    op.create_table('freelance_reviews',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('contract_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('reviewer_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('reviewee_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('visibility', sa.Enum('VISIBLE', 'HIDDEN', name='freelance_reviews_visibility', native_enum=False, create_constraint=True, length=40), server_default='VISIBLE', nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('rating <= 5', name=op.f('ck_freelance_reviews_rating_range')),
    sa.CheckConstraint('rating > 0', name=op.f('ck_freelance_reviews_rating_nonnegative')),
    sa.CheckConstraint('reviewer_user_id <> reviewee_user_id', name=op.f('ck_freelance_reviews_distinct_reviewers')),
    sa.ForeignKeyConstraint(['contract_id'], ['freelance_contracts.id'], name=op.f('fk_freelance_reviews_contract_id_freelance_contracts'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewee_user_id'], ['users.id'], name=op.f('fk_freelance_reviews_reviewee_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewer_user_id'], ['users.id'], name=op.f('fk_freelance_reviews_reviewer_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_freelance_reviews')),
    sa.UniqueConstraint('contract_id', 'reviewer_user_id', name=op.f('uq_freelance_reviews_contract_id_reviewer_user_id'))
    )
    op.create_index('ix_freelance_reviews_reviewee_user_id', 'freelance_reviews', ['reviewee_user_id'], unique=False)
    op.create_index('ix_freelance_reviews_reviewer_user_id', 'freelance_reviews', ['reviewer_user_id'], unique=False)
    op.create_table('milestones',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('contract_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('sequence_no', sa.Integer(), nullable=False),
    sa.Column('effective_terms_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('status', sa.Enum('NOT_FUNDED', 'FUNDING_PENDING', 'FUNDED', 'IN_PROGRESS', 'SUBMITTED', 'REVISION_REQUESTED', 'ACCEPTED', 'SETTLEMENT_PENDING', 'PAID_OUT', 'DISPUTED', 'REFUNDED', 'PARTIALLY_RELEASED', 'CANCELLED', name='milestones_status', native_enum=False, create_constraint=True, length=40), server_default='NOT_FUNDED', nullable=False),
    sa.Column('started_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('submitted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('review_deadline', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('revision_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('accepted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('acceptance_source', sa.Enum('MANUAL', 'AUTO', 'DISPUTE', name='milestones_acceptance_source', native_enum=False, create_constraint=True, length=40), nullable=True),
    sa.Column('settled_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('revision_count >= 0', name=op.f('ck_milestones_revision_count_nonnegative')),
    sa.CheckConstraint('sequence_no > 0', name=op.f('ck_milestones_sequence_no_nonnegative')),
    sa.ForeignKeyConstraint(['contract_id'], ['freelance_contracts.id'], name=op.f('fk_milestones_contract_id_freelance_contracts'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['id', 'effective_terms_id'], ['contract_milestone_terms.milestone_id', 'contract_milestone_terms.id'], name='fk_ms_effective_terms', ondelete='RESTRICT', use_alter=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_milestones')),
    sa.UniqueConstraint('contract_id', 'id', name=op.f('uq_milestones_contract_id_id')),
    sa.UniqueConstraint('contract_id', 'sequence_no', name=op.f('uq_milestones_contract_id_sequence_no'))
    )
    op.create_index('ix_milestones_status_review_deadline', 'milestones', ['status', 'review_deadline'], unique=False)
    op.create_table('project_contract_budgets',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('project_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('contract_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('allocated_amount', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Enum('RESERVED', 'COMMITTED', 'RELEASED', name='project_contract_budgets_status', native_enum=False, create_constraint=True, length=40), server_default='RESERVED', nullable=False),
    sa.Column('committed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('released_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('allocated_amount > 0', name=op.f('ck_project_contract_budgets_allocated_amount_amount')),
    sa.ForeignKeyConstraint(['project_id', 'contract_id'], ['freelance_contracts.project_id', 'freelance_contracts.id'], name='fk_pcb_contract', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['project_id'], ['freelance_projects.id'], name='fk_pcb_project', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_project_contract_budgets')),
    sa.UniqueConstraint('contract_id', name=op.f('uq_project_contract_budgets_contract_id'))
    )
    op.create_index('ix_project_contract_budgets_project_id_status', 'project_contract_budgets', ['project_id', 'status'], unique=False)
    op.create_table('cancellation_agreements',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('requested_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('basis', sa.Enum('MUTUAL', 'BEFORE_START', 'OVERDUE', name='cancellation_agreements_basis', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('freelancer_gross', sa.BigInteger(), nullable=False),
    sa.Column('refund_amount', sa.BigInteger(), nullable=False),
    sa.Column('terms_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('status', sa.Enum('PROPOSED', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXECUTED', name='cancellation_agreements_status', native_enum=False, create_constraint=True, length=40), server_default='PROPOSED', nullable=False),
    sa.Column('client_accepted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('freelancer_accepted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('policy_snapshot', sa.JSON(), nullable=False),
    sa.Column('executed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('freelancer_gross >= 0', name=op.f('ck_cancellation_agreements_freelancer_gross_amount')),
    sa.CheckConstraint('refund_amount >= 0', name=op.f('ck_cancellation_agreements_refund_amount_amount')),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_cancellation_agreements_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['requested_by'], ['users.id'], name=op.f('fk_cancellation_agreements_requested_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cancellation_agreements'))
    )
    op.create_index('ix_cancellation_agreements_milestone_id', 'cancellation_agreements', ['milestone_id'], unique=False)
    op.create_index('ix_cancellation_agreements_milestone_id_status', 'cancellation_agreements', ['milestone_id', 'status'], unique=False)
    op.create_index('ix_cancellation_agreements_requested_by', 'cancellation_agreements', ['requested_by'], unique=False)
    op.create_table('contract_milestone_terms',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('contract_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('contract_version_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('acceptance_criteria', sa.Text(), nullable=False),
    sa.Column('due_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('included', sa.Boolean(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('amount > 0', name=op.f('ck_contract_milestone_terms_amount_amount')),
    sa.ForeignKeyConstraint(['contract_id', 'contract_version_id'], ['contract_versions.contract_id', 'contract_versions.id'], name='fk_cmt_version', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['contract_id', 'milestone_id'], ['milestones.contract_id', 'milestones.id'], name='fk_cmt_milestone', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_contract_milestone_terms')),
    sa.UniqueConstraint('contract_version_id', 'milestone_id', name=op.f('uq_contract_milestone_terms_contract_version_id_milestone_id')),
    sa.UniqueConstraint('milestone_id', 'id', name=op.f('uq_contract_milestone_terms_milestone_id_id'))
    )
    op.create_table('deliverables',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('submission_no', sa.Integer(), nullable=False),
    sa.Column('submitted_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('submitted_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('submission_no > 0', name=op.f('ck_deliverables_submission_no_nonnegative')),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_deliverables_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], name=op.f('fk_deliverables_submitted_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_deliverables')),
    sa.UniqueConstraint('milestone_id', 'id', name=op.f('uq_deliverables_milestone_id_id')),
    sa.UniqueConstraint('milestone_id', 'submission_no', name=op.f('uq_deliverables_milestone_id_submission_no'))
    )
    op.create_index('ix_deliverables_submitted_by', 'deliverables', ['submitted_by'], unique=False)
    op.create_table('disputes',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('opened_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('reason_code', sa.String(length=40), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('OPEN', 'EVIDENCE_COLLECTION', 'UNDER_REVIEW', 'ESCALATED', 'RESOLVED', 'WITHDRAWN', name='disputes_status', native_enum=False, create_constraint=True, length=40), server_default='OPEN', nullable=False),
    sa.Column('previous_milestone_status', sa.Enum('NOT_FUNDED', 'FUNDING_PENDING', 'FUNDED', 'IN_PROGRESS', 'SUBMITTED', 'REVISION_REQUESTED', 'ACCEPTED', 'SETTLEMENT_PENDING', 'PAID_OUT', 'DISPUTED', 'REFUNDED', 'PARTIALLY_RELEASED', 'CANCELLED', name='disputes_previous_milestone_status', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('remaining_review_seconds', sa.Integer(), nullable=True),
    sa.Column('evidence_deadline', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('assigned_admin_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('resolved_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('withdrawal_note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('remaining_review_seconds >= 0', name=op.f('ck_disputes_remaining_review_seconds_nonnegative')),
    sa.ForeignKeyConstraint(['assigned_admin_id'], ['users.id'], name=op.f('fk_disputes_assigned_admin_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_disputes_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['opened_by'], ['users.id'], name=op.f('fk_disputes_opened_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_disputes'))
    )
    op.create_index('ix_disputes_assigned_admin_id', 'disputes', ['assigned_admin_id'], unique=False)
    op.create_index('ix_disputes_milestone_id', 'disputes', ['milestone_id'], unique=False)
    op.create_index('ix_disputes_milestone_id_created_at', 'disputes', ['milestone_id', 'created_at'], unique=False)
    op.create_index('ix_disputes_opened_by', 'disputes', ['opened_by'], unique=False)
    op.create_index('ix_disputes_status_evidence_deadline', 'disputes', ['status', 'evidence_deadline'], unique=False)
    op.create_table('ledger_accounts',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=150).with_variant(sa.String(length=150, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=150, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('kind', sa.Enum('PLATFORM_BANK', 'PAYOUT_ACCOUNT', 'UNALLOCATED_RECEIPTS', 'ESCROW_HELD', 'FREELANCER_PAYABLE', 'CLIENT_REFUND_PAYABLE', 'PLATFORM_FEE_REVENUE', 'PROVIDER_FEE_EXPENSE', 'PLATFORM_EQUITY', name='ledger_accounts_kind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('normal_side', sa.Enum('D', 'C', name='ledger_accounts_normal_side', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('owner_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('currency', sa.String(length=3), server_default='VND', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("currency = 'VND'", name=op.f('ck_ledger_accounts_vnd_only')),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_ledger_accounts_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], name=op.f('fk_ledger_accounts_owner_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ledger_accounts')),
    sa.UniqueConstraint('code', name=op.f('uq_ledger_accounts_code'))
    )
    op.create_index('ix_ledger_accounts_milestone_id', 'ledger_accounts', ['milestone_id'], unique=False)
    op.create_index('ix_ledger_accounts_owner_user_id', 'ledger_accounts', ['owner_user_id'], unique=False)
    op.create_table('payment_orders',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('payer_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('expected_amount', sa.BigInteger(), nullable=False),
    sa.Column('order_code', sa.BigInteger(), nullable=False),
    sa.Column('payment_link_id', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('status', sa.Enum('CREATING', 'PENDING', 'PROCESSING', 'PAID', 'EXPIRED', 'CANCELLED', 'FAILED', 'NEEDS_REVIEW', 'UNKNOWN', name='payment_orders_status', native_enum=False, create_constraint=True, length=40), server_default='CREATING', nullable=False),
    sa.Column('request_key', sa.String(length=128).with_variant(sa.String(length=128, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=128, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('request_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('checkout_url', sa.String(length=1000), nullable=True),
    sa.Column('qr_payload', sa.Text(), nullable=True),
    sa.Column('receiving_account_snapshot', sa.JSON(), nullable=False),
    sa.Column('expires_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('paid_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('provider_response_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('expected_amount > 0', name=op.f('ck_payment_orders_expected_amount_amount')),
    sa.CheckConstraint('order_code > 0 AND order_code <= 9007199254740991', name=op.f('ck_payment_orders_safe_order_code')),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_payment_orders_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['payer_user_id'], ['users.id'], name=op.f('fk_payment_orders_payer_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payment_orders')),
    sa.UniqueConstraint('order_code', name=op.f('uq_payment_orders_order_code')),
    sa.UniqueConstraint('payer_user_id', 'request_key', name=op.f('uq_payment_orders_payer_user_id_request_key')),
    sa.UniqueConstraint('payment_link_id', name=op.f('uq_payment_orders_payment_link_id'))
    )
    op.create_index('ix_payment_orders_milestone_id', 'payment_orders', ['milestone_id'], unique=False)
    op.create_index('ix_payment_orders_milestone_id_created_at', 'payment_orders', ['milestone_id', 'created_at'], unique=False)
    op.create_index('ix_payment_orders_status_expires_at', 'payment_orders', ['status', 'expires_at'], unique=False)
    op.create_table('active_milestone_disputes',
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('dispute_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], name=op.f('fk_active_milestone_disputes_dispute_id_disputes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_active_milestone_disputes_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('milestone_id', name=op.f('pk_active_milestone_disputes')),
    sa.UniqueConstraint('dispute_id', name=op.f('uq_active_milestone_disputes_dispute_id'))
    )
    op.create_index('ix_active_milestone_disputes_dispute_id', 'active_milestone_disputes', ['dispute_id'], unique=False)
    op.create_index('ix_active_milestone_disputes_milestone_id', 'active_milestone_disputes', ['milestone_id'], unique=False)
    op.create_table('deliverable_files',
    sa.Column('deliverable_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['deliverable_id'], ['deliverables.id'], name=op.f('fk_deliverable_files_deliverable_id_deliverables'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['file_id'], ['stored_files.id'], name=op.f('fk_deliverable_files_file_id_stored_files'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('deliverable_id', 'file_id', name=op.f('pk_deliverable_files'))
    )
    op.create_index('ix_deliverable_files_deliverable_id', 'deliverable_files', ['deliverable_id'], unique=False)
    op.create_index('ix_deliverable_files_file_id', 'deliverable_files', ['file_id'], unique=False)
    op.create_table('dispute_decisions',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('dispute_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('revision_no', sa.Integer(), nullable=False),
    sa.Column('outcome', sa.Enum('PAYOUT', 'REFUND', 'SPLIT', name='dispute_decisions_outcome', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('freelancer_gross', sa.BigInteger(), nullable=False),
    sa.Column('refund_amount', sa.BigInteger(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTING', 'EXECUTED', 'SUPERSEDED', name='dispute_decisions_status', native_enum=False, create_constraint=True, length=40), server_default='PROPOSED', nullable=False),
    sa.Column('requires_second_approval', sa.Boolean(), nullable=False),
    sa.Column('approval_threshold_snapshot', sa.BigInteger(), nullable=False),
    sa.Column('proposed_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('approved_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('approved_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('executed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("(outcome = 'PAYOUT' AND freelancer_gross > 0 AND refund_amount = 0) OR (outcome = 'REFUND' AND freelancer_gross = 0 AND refund_amount > 0) OR (outcome = 'SPLIT' AND freelancer_gross > 0 AND refund_amount > 0)", name=op.f('ck_dispute_decisions_decision_amounts')),
    sa.CheckConstraint('approval_threshold_snapshot >= 0', name=op.f('ck_dispute_decisions_approval_threshold_snapshot_amount')),
    sa.CheckConstraint('approved_by IS NULL OR approved_by <> proposed_by', name=op.f('ck_dispute_decisions_distinct_approvers')),
    sa.CheckConstraint('freelancer_gross >= 0', name=op.f('ck_dispute_decisions_freelancer_gross_amount')),
    sa.CheckConstraint('refund_amount >= 0', name=op.f('ck_dispute_decisions_refund_amount_amount')),
    sa.CheckConstraint('revision_no > 0', name=op.f('ck_dispute_decisions_revision_no_nonnegative')),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name=op.f('fk_dispute_decisions_approved_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], name=op.f('fk_dispute_decisions_dispute_id_disputes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['proposed_by'], ['users.id'], name=op.f('fk_dispute_decisions_proposed_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_dispute_decisions')),
    sa.UniqueConstraint('dispute_id', 'revision_no', name=op.f('uq_dispute_decisions_dispute_id_revision_no'))
    )
    op.create_index('ix_dispute_decisions_approved_by', 'dispute_decisions', ['approved_by'], unique=False)
    op.create_index('ix_dispute_decisions_proposed_by', 'dispute_decisions', ['proposed_by'], unique=False)
    op.create_table('dispute_evidence',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('dispute_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('submitted_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('deliverable_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('file_id IS NOT NULL OR deliverable_id IS NOT NULL OR note IS NOT NULL', name=op.f('ck_dispute_evidence_has_evidence')),
    sa.ForeignKeyConstraint(['deliverable_id'], ['deliverables.id'], name=op.f('fk_dispute_evidence_deliverable_id_deliverables'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], name=op.f('fk_dispute_evidence_dispute_id_disputes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['file_id'], ['stored_files.id'], name=op.f('fk_dispute_evidence_file_id_stored_files'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], name=op.f('fk_dispute_evidence_submitted_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_dispute_evidence'))
    )
    op.create_index('ix_dispute_evidence_deliverable_id', 'dispute_evidence', ['deliverable_id'], unique=False)
    op.create_index('ix_dispute_evidence_dispute_id', 'dispute_evidence', ['dispute_id'], unique=False)
    op.create_index('ix_dispute_evidence_dispute_id_created_at', 'dispute_evidence', ['dispute_id', 'created_at'], unique=False)
    op.create_index('ix_dispute_evidence_file_id', 'dispute_evidence', ['file_id'], unique=False)
    op.create_index('ix_dispute_evidence_submitted_by', 'dispute_evidence', ['submitted_by'], unique=False)
    op.create_table('escrow_accounts',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('ledger_account_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('funded_amount', sa.BigInteger(), nullable=False),
    sa.Column('reserved_amount', sa.BigInteger(), server_default='0', nullable=False),
    sa.Column('released_gross', sa.BigInteger(), server_default='0', nullable=False),
    sa.Column('refunded_amount', sa.BigInteger(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('funded_amount > 0', name=op.f('ck_escrow_accounts_funded_amount_amount')),
    sa.CheckConstraint('refunded_amount >= 0', name=op.f('ck_escrow_accounts_refunded_amount_amount')),
    sa.CheckConstraint('released_gross + refunded_amount + reserved_amount <= funded_amount', name=op.f('ck_escrow_accounts_escrow_conservation')),
    sa.CheckConstraint('released_gross >= 0', name=op.f('ck_escrow_accounts_released_gross_amount')),
    sa.CheckConstraint('reserved_amount >= 0', name=op.f('ck_escrow_accounts_reserved_amount_amount')),
    sa.ForeignKeyConstraint(['ledger_account_id'], ['ledger_accounts.id'], name=op.f('fk_escrow_accounts_ledger_account_id_ledger_accounts'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_escrow_accounts_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_escrow_accounts')),
    sa.UniqueConstraint('ledger_account_id', name=op.f('uq_escrow_accounts_ledger_account_id')),
    sa.UniqueConstraint('milestone_id', name=op.f('uq_escrow_accounts_milestone_id'))
    )
    op.create_index('ix_escrow_accounts_ledger_account_id', 'escrow_accounts', ['ledger_account_id'], unique=False)
    op.create_index('ix_escrow_accounts_milestone_id', 'escrow_accounts', ['milestone_id'], unique=False)
    op.create_table('ledger_postings',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('journal_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('line_no', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('side', sa.Enum('D', 'C', name='ledger_postings_side', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('amount > 0', name=op.f('ck_ledger_postings_amount_amount')),
    sa.CheckConstraint('line_no > 0', name=op.f('ck_ledger_postings_line_no_nonnegative')),
    sa.ForeignKeyConstraint(['account_id'], ['ledger_accounts.id'], name=op.f('fk_ledger_postings_account_id_ledger_accounts'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['journal_id'], ['ledger_journals.id'], name=op.f('fk_ledger_postings_journal_id_ledger_journals'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ledger_postings')),
    sa.UniqueConstraint('journal_id', 'line_no', name=op.f('uq_ledger_postings_journal_id_line_no'))
    )
    op.create_index('ix_ledger_postings_account_id', 'ledger_postings', ['account_id'], unique=False)
    op.create_index('ix_ledger_postings_account_id_journal_id', 'ledger_postings', ['account_id', 'journal_id'], unique=False)
    op.create_table('milestone_funding_guards',
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('payment_order_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_milestone_funding_guards_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['payment_order_id'], ['payment_orders.id'], name=op.f('fk_milestone_funding_guards_payment_order_id_payment_orders'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('milestone_id', name=op.f('pk_milestone_funding_guards')),
    sa.UniqueConstraint('payment_order_id', name=op.f('uq_milestone_funding_guards_payment_order_id'))
    )
    op.create_index('ix_milestone_funding_guards_milestone_id', 'milestone_funding_guards', ['milestone_id'], unique=False)
    op.create_index('ix_milestone_funding_guards_payment_order_id', 'milestone_funding_guards', ['payment_order_id'], unique=False)
    op.create_table('milestone_holds',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('reason_type', sa.Enum('DISPUTE', 'COMPANY_SUSPENSION', 'ADMIN_REVIEW', name='milestone_holds_reason_type', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reason_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('dispute_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('placed_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('note', sa.Text(), nullable=False),
    sa.Column('placed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('released_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('released_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('release_note', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], name=op.f('fk_milestone_holds_dispute_id_disputes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_milestone_holds_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['placed_by'], ['users.id'], name=op.f('fk_milestone_holds_placed_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['released_by'], ['users.id'], name=op.f('fk_milestone_holds_released_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_milestone_holds')),
    sa.UniqueConstraint('reason_key', name=op.f('uq_milestone_holds_reason_key'))
    )
    op.create_index('ix_milestone_holds_dispute_id', 'milestone_holds', ['dispute_id'], unique=False)
    op.create_index('ix_milestone_holds_milestone_id', 'milestone_holds', ['milestone_id'], unique=False)
    op.create_index('ix_milestone_holds_milestone_id_released_at', 'milestone_holds', ['milestone_id', 'released_at'], unique=False)
    op.create_index('ix_milestone_holds_placed_by', 'milestone_holds', ['placed_by'], unique=False)
    op.create_index('ix_milestone_holds_released_by', 'milestone_holds', ['released_by'], unique=False)
    op.create_table('milestone_reviews',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('deliverable_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('reviewed_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('action', sa.Enum('ACCEPT', 'REQUEST_REVISION', 'AUTO_ACCEPT', name='milestone_reviews_action', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['milestone_id', 'deliverable_id'], ['deliverables.milestone_id', 'deliverables.id'], name='fk_mr_deliverable', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name=op.f('fk_milestone_reviews_reviewed_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_milestone_reviews'))
    )
    op.create_index('ix_milestone_reviews_milestone_id_created_at', 'milestone_reviews', ['milestone_id', 'created_at'], unique=False)
    op.create_index('ix_milestone_reviews_reviewed_by', 'milestone_reviews', ['reviewed_by'], unique=False)
    op.create_table('payment_transactions',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('payment_order_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('provider_event_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('channel_key', sa.String(length=100).with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=100, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('external_ref', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('currency', sa.String(length=3), server_default='VND', nullable=False),
    sa.Column('receiving_account_ref', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('received_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('received_time_raw', sa.String(length=100), nullable=True),
    sa.Column('allocation_status', sa.Enum('UNALLOCATED', 'ALLOCATED', 'PARTIALLY_RETURNED', 'RETURNED', name='payment_transactions_allocation_status', native_enum=False, create_constraint=True, length=40), server_default='UNALLOCATED', nullable=False),
    sa.Column('receipt_journal_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('raw_payload_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("currency = 'VND'", name=op.f('ck_payment_transactions_vnd_only')),
    sa.CheckConstraint('amount > 0', name=op.f('ck_payment_transactions_amount_amount')),
    sa.ForeignKeyConstraint(['payment_order_id'], ['payment_orders.id'], name=op.f('fk_payment_transactions_payment_order_id_payment_orders'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['provider_event_id'], ['provider_events.id'], name=op.f('fk_payment_transactions_provider_event_id_provider_events'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['receipt_journal_id'], ['ledger_journals.id'], name=op.f('fk_payment_transactions_receipt_journal_id_ledger_journals'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payment_transactions')),
    sa.UniqueConstraint('channel_key', 'external_ref', name=op.f('uq_payment_transactions_channel_key_external_ref')),
    sa.UniqueConstraint('receipt_journal_id', name=op.f('uq_payment_transactions_receipt_journal_id'))
    )
    op.create_index('ix_payment_transactions_allocation_status_created_at', 'payment_transactions', ['allocation_status', 'created_at'], unique=False)
    op.create_index('ix_payment_transactions_payment_order_id', 'payment_transactions', ['payment_order_id'], unique=False)
    op.create_index('ix_payment_transactions_provider_event_id', 'payment_transactions', ['provider_event_id'], unique=False)
    op.create_index('ix_payment_transactions_receipt_journal_id', 'payment_transactions', ['receipt_journal_id'], unique=False)
    op.create_table('milestone_fundings',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('payment_transaction_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('funding_journal_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('amount > 0', name=op.f('ck_milestone_fundings_amount_amount')),
    sa.ForeignKeyConstraint(['funding_journal_id'], ['ledger_journals.id'], name=op.f('fk_milestone_fundings_funding_journal_id_ledger_journals'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_milestone_fundings_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['payment_transaction_id'], ['payment_transactions.id'], name=op.f('fk_milestone_fundings_payment_transaction_id_payment_transactions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_milestone_fundings')),
    sa.UniqueConstraint('funding_journal_id', name=op.f('uq_milestone_fundings_funding_journal_id')),
    sa.UniqueConstraint('milestone_id', name=op.f('uq_milestone_fundings_milestone_id')),
    sa.UniqueConstraint('payment_transaction_id', name=op.f('uq_milestone_fundings_payment_transaction_id'))
    )
    op.create_index('ix_milestone_fundings_funding_journal_id', 'milestone_fundings', ['funding_journal_id'], unique=False)
    op.create_index('ix_milestone_fundings_milestone_id', 'milestone_fundings', ['milestone_id'], unique=False)
    op.create_index('ix_milestone_fundings_payment_transaction_id', 'milestone_fundings', ['payment_transaction_id'], unique=False)
    op.create_table('payment_review_cases',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('payment_transaction_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('reason', sa.Enum('UNMATCHED', 'UNDERPAID', 'OVERPAID', 'LATE', 'WRONG_ACCOUNT', 'DUPLICATE_PAYMENT', name='payment_review_cases_reason', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('status', sa.Enum('OPEN', 'UNDER_REVIEW', 'RESOLVED', name='payment_review_cases_status', native_enum=False, create_constraint=True, length=40), server_default='OPEN', nullable=False),
    sa.Column('assigned_to', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('resolution', sa.Enum('ALLOCATE', 'RETURN', 'PARTIAL_RETURN', name='payment_review_cases_resolution', native_enum=False, create_constraint=True, length=40), nullable=True),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('resolved_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('resolved_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name=op.f('fk_payment_review_cases_assigned_to_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['payment_transaction_id'], ['payment_transactions.id'], name=op.f('fk_payment_review_cases_payment_transaction_id_payment_transactions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], name=op.f('fk_payment_review_cases_resolved_by_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payment_review_cases')),
    sa.UniqueConstraint('payment_transaction_id', name=op.f('uq_payment_review_cases_payment_transaction_id'))
    )
    op.create_index('ix_payment_review_cases_assigned_to', 'payment_review_cases', ['assigned_to'], unique=False)
    op.create_index('ix_payment_review_cases_payment_transaction_id', 'payment_review_cases', ['payment_transaction_id'], unique=False)
    op.create_index('ix_payment_review_cases_resolved_by', 'payment_review_cases', ['resolved_by'], unique=False)
    op.create_index('ix_payment_review_cases_status_created_at', 'payment_review_cases', ['status', 'created_at'], unique=False)
    op.create_table('settlements',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('milestone_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('sequence_no', sa.Integer(), nullable=False),
    sa.Column('kind', sa.Enum('RELEASE', 'REFUND', 'SPLIT', name='settlements_kind', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('source', sa.Enum('ACCEPTANCE', 'AUTO_ACCEPT', 'CANCELLATION', 'DISPUTE', name='settlements_source', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('source_review_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('source_cancellation_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('source_decision_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('freelancer_gross', sa.BigInteger(), nullable=False),
    sa.Column('refund_amount', sa.BigInteger(), nullable=False),
    sa.Column('fee_rate_bp', sa.SmallInteger().with_variant(mysql.SMALLINT(unsigned=True), 'mariadb').with_variant(mysql.SMALLINT(unsigned=True), 'mysql'), nullable=False),
    sa.Column('fee_amount', sa.BigInteger(), nullable=False),
    sa.Column('net_amount', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Enum('PREPARED', 'PROCESSING', 'PARTIALLY_SUCCEEDED', 'SUCCEEDED', 'FAILED', 'CANCELLED', name='settlements_status', native_enum=False, create_constraint=True, length=40), server_default='PREPARED', nullable=False),
    sa.Column('request_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('requested_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('completed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("(kind = 'RELEASE' AND refund_amount = 0 AND freelancer_gross > 0) OR (kind = 'REFUND' AND freelancer_gross = 0 AND refund_amount > 0) OR (kind = 'SPLIT' AND freelancer_gross > 0 AND refund_amount > 0)", name=op.f('ck_settlements_settlement_kind_amounts')),
    sa.CheckConstraint("(source IN ('ACCEPTANCE','AUTO_ACCEPT') AND source_review_id IS NOT NULL AND source_cancellation_id IS NULL AND source_decision_id IS NULL) OR (source = 'CANCELLATION' AND source_review_id IS NULL AND source_cancellation_id IS NOT NULL AND source_decision_id IS NULL) OR (source = 'DISPUTE' AND source_review_id IS NULL AND source_cancellation_id IS NULL AND source_decision_id IS NOT NULL)", name=op.f('ck_settlements_settlement_source')),
    sa.CheckConstraint('amount > 0', name=op.f('ck_settlements_amount_amount')),
    sa.CheckConstraint('fee_amount + net_amount = freelancer_gross', name=op.f('ck_settlements_settlement_fee')),
    sa.CheckConstraint('fee_amount >= 0', name=op.f('ck_settlements_fee_amount_amount')),
    sa.CheckConstraint('fee_rate_bp <= 10000', name=op.f('ck_settlements_fee_rate_bp_range')),
    sa.CheckConstraint('fee_rate_bp >= 0', name=op.f('ck_settlements_fee_rate_bp_nonnegative')),
    sa.CheckConstraint('freelancer_gross + refund_amount = amount', name=op.f('ck_settlements_settlement_total')),
    sa.CheckConstraint('freelancer_gross >= 0', name=op.f('ck_settlements_freelancer_gross_amount')),
    sa.CheckConstraint('net_amount >= 0', name=op.f('ck_settlements_net_amount_amount')),
    sa.CheckConstraint('refund_amount >= 0', name=op.f('ck_settlements_refund_amount_amount')),
    sa.CheckConstraint('sequence_no > 0', name=op.f('ck_settlements_sequence_no_nonnegative')),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], name=op.f('fk_settlements_milestone_id_milestones'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['requested_by'], ['users.id'], name=op.f('fk_settlements_requested_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_cancellation_id'], ['cancellation_agreements.id'], name=op.f('fk_settlements_source_cancellation_id_cancellation_agreements'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_decision_id'], ['dispute_decisions.id'], name=op.f('fk_settlements_source_decision_id_dispute_decisions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['source_review_id'], ['milestone_reviews.id'], name=op.f('fk_settlements_source_review_id_milestone_reviews'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_settlements')),
    sa.UniqueConstraint('milestone_id', 'sequence_no', name=op.f('uq_settlements_milestone_id_sequence_no')),
    sa.UniqueConstraint('request_key', name=op.f('uq_settlements_request_key')),
    sa.UniqueConstraint('source_cancellation_id', name=op.f('uq_settlements_source_cancellation_id')),
    sa.UniqueConstraint('source_decision_id', name=op.f('uq_settlements_source_decision_id')),
    sa.UniqueConstraint('source_review_id', name=op.f('uq_settlements_source_review_id'))
    )
    op.create_index('ix_settlements_requested_by', 'settlements', ['requested_by'], unique=False)
    op.create_index('ix_settlements_source_cancellation_id', 'settlements', ['source_cancellation_id'], unique=False)
    op.create_index('ix_settlements_source_decision_id', 'settlements', ['source_decision_id'], unique=False)
    op.create_index('ix_settlements_source_review_id', 'settlements', ['source_review_id'], unique=False)
    op.create_table('money_transfers',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('settlement_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('payment_transaction_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('purpose', sa.Enum('RELEASE', 'REFUND', 'UNALLOCATED_REFUND', name='money_transfers_purpose', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('recipient_user_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('destination_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('destination_snapshot', sa.JSON(), nullable=False),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Enum('READY', 'PROCESSING', 'UNKNOWN', 'SUCCEEDED', 'FAILED', 'CANCELLED', name='money_transfers_status', native_enum=False, create_constraint=True, length=40), server_default='READY', nullable=False),
    sa.Column('idempotency_key', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('provider_reference_id', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('payos_payout_id', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('payos_transaction_id', sa.String(length=191).with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=191, collation='utf8mb4_bin'), 'mysql'), nullable=True),
    sa.Column('provider_approval_state', sa.String(length=40), nullable=True),
    sa.Column('provider_transaction_state', sa.String(length=40), nullable=True),
    sa.Column('obligation_journal_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('disbursement_journal_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('provider_fee_amount', sa.BigInteger(), nullable=True),
    sa.Column('fee_journal_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('succeeded_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('reserved_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('reservation_released_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint("(purpose IN ('RELEASE','REFUND') AND settlement_id IS NOT NULL AND payment_transaction_id IS NULL) OR (purpose = 'UNALLOCATED_REFUND' AND settlement_id IS NULL AND payment_transaction_id IS NOT NULL)", name=op.f('ck_money_transfers_transfer_source')),
    sa.CheckConstraint('amount > 0', name=op.f('ck_money_transfers_amount_amount')),
    sa.CheckConstraint('provider_fee_amount >= 0', name=op.f('ck_money_transfers_provider_fee_amount_amount')),
    sa.ForeignKeyConstraint(['destination_id'], ['bank_destinations.id'], name=op.f('fk_money_transfers_destination_id_bank_destinations'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['disbursement_journal_id'], ['ledger_journals.id'], name=op.f('fk_money_transfers_disbursement_journal_id_ledger_journals'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['fee_journal_id'], ['ledger_journals.id'], name=op.f('fk_money_transfers_fee_journal_id_ledger_journals'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['obligation_journal_id'], ['ledger_journals.id'], name=op.f('fk_money_transfers_obligation_journal_id_ledger_journals'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['payment_transaction_id'], ['payment_transactions.id'], name=op.f('fk_money_transfers_payment_transaction_id_payment_transactions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id'], name=op.f('fk_money_transfers_recipient_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['settlement_id'], ['settlements.id'], name=op.f('fk_money_transfers_settlement_id_settlements'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_money_transfers')),
    sa.UniqueConstraint('disbursement_journal_id', name=op.f('uq_money_transfers_disbursement_journal_id')),
    sa.UniqueConstraint('fee_journal_id', name=op.f('uq_money_transfers_fee_journal_id')),
    sa.UniqueConstraint('idempotency_key', name=op.f('uq_money_transfers_idempotency_key')),
    sa.UniqueConstraint('obligation_journal_id', name=op.f('uq_money_transfers_obligation_journal_id')),
    sa.UniqueConstraint('payos_payout_id', name=op.f('uq_money_transfers_payos_payout_id')),
    sa.UniqueConstraint('payos_transaction_id', name=op.f('uq_money_transfers_payos_transaction_id')),
    sa.UniqueConstraint('provider_reference_id', name=op.f('uq_money_transfers_provider_reference_id')),
    sa.UniqueConstraint('settlement_id', 'purpose', name=op.f('uq_money_transfers_settlement_id_purpose'))
    )
    op.create_index('ix_money_transfers_destination_id', 'money_transfers', ['destination_id'], unique=False)
    op.create_index('ix_money_transfers_disbursement_journal_id', 'money_transfers', ['disbursement_journal_id'], unique=False)
    op.create_index('ix_money_transfers_fee_journal_id', 'money_transfers', ['fee_journal_id'], unique=False)
    op.create_index('ix_money_transfers_obligation_journal_id', 'money_transfers', ['obligation_journal_id'], unique=False)
    op.create_index('ix_money_transfers_payment_transaction_id', 'money_transfers', ['payment_transaction_id'], unique=False)
    op.create_index('ix_money_transfers_recipient_user_id', 'money_transfers', ['recipient_user_id'], unique=False)
    op.create_table('daily_limit_reservations',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('bucket_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('payment_order_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('money_transfer_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Enum('RESERVED', 'CONSUMED', 'RELEASED', name='daily_limit_reservations_status', native_enum=False, create_constraint=True, length=40), server_default='RESERVED', nullable=False),
    sa.Column('consumed_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('released_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('(payment_order_id IS NOT NULL AND money_transfer_id IS NULL) OR (payment_order_id IS NULL AND money_transfer_id IS NOT NULL)', name=op.f('ck_daily_limit_reservations_limit_source')),
    sa.CheckConstraint('amount > 0', name=op.f('ck_daily_limit_reservations_amount_amount')),
    sa.ForeignKeyConstraint(['bucket_id'], ['daily_limit_buckets.id'], name=op.f('fk_daily_limit_reservations_bucket_id_daily_limit_buckets'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['money_transfer_id'], ['money_transfers.id'], name=op.f('fk_daily_limit_reservations_money_transfer_id_money_transfers'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['payment_order_id'], ['payment_orders.id'], name=op.f('fk_daily_limit_reservations_payment_order_id_payment_orders'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_daily_limit_reservations')),
    sa.UniqueConstraint('bucket_id', 'money_transfer_id', name=op.f('uq_daily_limit_reservations_bucket_id_money_transfer_id')),
    sa.UniqueConstraint('bucket_id', 'payment_order_id', name=op.f('uq_daily_limit_reservations_bucket_id_payment_order_id'))
    )
    op.create_index('ix_daily_limit_reservations_money_transfer_id', 'daily_limit_reservations', ['money_transfer_id'], unique=False)
    op.create_index('ix_daily_limit_reservations_payment_order_id', 'daily_limit_reservations', ['payment_order_id'], unique=False)
    op.create_table('transfer_attempts',
    sa.Column('id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('transfer_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('attempt_no', sa.Integer(), nullable=False),
    sa.Column('operation', sa.Enum('CREATE', 'QUERY', name='transfer_attempts_operation', native_enum=False, create_constraint=True, length=40), nullable=False),
    sa.Column('status', sa.Enum('STARTED', 'CONFIRMED_SUCCESS', 'CONFIRMED_FAILURE', 'UNKNOWN', name='transfer_attempts_status', native_enum=False, create_constraint=True, length=40), server_default='STARTED', nullable=False),
    sa.Column('request_hash', sa.String(length=64).with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mariadb').with_variant(sa.String(length=64, collation='utf8mb4_bin'), 'mysql'), nullable=False),
    sa.Column('provider_response_json', sa.JSON(), nullable=True),
    sa.Column('error_code', sa.String(length=100), nullable=True),
    sa.Column('started_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('finished_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('next_check_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.Column('created_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('attempt_no > 0', name=op.f('ck_transfer_attempts_attempt_no_nonnegative')),
    sa.ForeignKeyConstraint(['transfer_id'], ['money_transfers.id'], name=op.f('fk_transfer_attempts_transfer_id_money_transfers'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_transfer_attempts')),
    sa.UniqueConstraint('transfer_id', 'attempt_no', name=op.f('uq_transfer_attempts_transfer_id_attempt_no'))
    )
    with op.batch_alter_table('companies') as batch:
        batch.add_column(sa.Column('legal_name', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('representative_name', sa.String(length=255), nullable=True))
        batch.add_column(sa.Column('representative_position', sa.String(length=100), nullable=True))
        batch.add_column(sa.Column('is_legal_representative', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('authorization_file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True))
        batch.add_column(sa.Column('business_status', sa.Enum('UNVERIFIED', 'PENDING_VERIFICATION', 'NEEDS_REVISION', 'VERIFIED', 'REJECTED', 'REVOKED', name='companies_business_status', native_enum=False, create_constraint=True, length=40), server_default='UNVERIFIED', nullable=False))
        batch.add_column(sa.Column('business_verified_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True))
        batch.add_column(sa.Column('business_verified_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True))
        batch.add_column(sa.Column('operation_status', sa.Enum('ENABLED', 'SUSPENDED', name='companies_operation_status', native_enum=False, create_constraint=True, length=40), server_default='ENABLED', nullable=False))
        batch.add_column(sa.Column('suspension_reason', sa.Text(), nullable=True))
        batch.add_column(sa.Column('suspended_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True))
        batch.add_column(sa.Column('suspended_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True))
        batch.create_index('ix_companies_business_status_created_at', ['business_status', 'created_at'], unique=False)
        batch.create_foreign_key(op.f('fk_companies_suspended_by_users'), 'users', ['suspended_by'], ['id'], ondelete='RESTRICT')
        batch.create_foreign_key(op.f('fk_companies_authorization_file_id_stored_files'), 'stored_files', ['authorization_file_id'], ['id'], ondelete='RESTRICT')
        batch.create_foreign_key(op.f('fk_companies_business_verified_by_users'), 'users', ['business_verified_by'], ['id'], ondelete='RESTRICT')

    with op.batch_alter_table('company_documents') as batch:
        batch.add_column(sa.Column('stored_file_id', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True))
        batch.add_column(sa.Column('uploaded_by', sa.BigInteger().with_variant(mysql.BIGINT(unsigned=True), 'mariadb').with_variant(mysql.BIGINT(unsigned=True), 'mysql').with_variant(sa.Integer(), 'sqlite'), nullable=True))
        batch.create_foreign_key(op.f('fk_company_documents_uploaded_by_users'), 'users', ['uploaded_by'], ['id'], ondelete='RESTRICT')
        batch.create_foreign_key(op.f('fk_company_documents_stored_file_id_stored_files'), 'stored_files', ['stored_file_id'], ['id'], ondelete='RESTRICT')

    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('email_verified_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True))
        batch.add_column(sa.Column('phone_verified_at', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mariadb').with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True))
    if op.get_bind().dialect.name in ("mysql", "mariadb"):
        op.alter_column("users", "role", existing_type=sa.Enum("STUDENT", "COMPANY", "ADMIN", name="userrole"),
                        type_=sa.Enum("STUDENT", "COMPANY", "ADMIN", "CLIENT", name="userrole"), existing_nullable=False)
        op.create_foreign_key("fk_fc_effective_version", "freelance_contracts", "contract_versions",
                              ["id", "effective_version_id"], ["contract_id", "id"], ondelete="RESTRICT")
        op.create_foreign_key("fk_ms_effective_terms", "milestones", "contract_milestone_terms",
                              ["id", "effective_terms_id"], ["milestone_id", "id"], ondelete="RESTRICT")
    op.execute(sa.text("UPDATE companies SET legal_name = name WHERE legal_name IS NULL"))
    _install_append_only_guards()
    # ### end Alembic commands ###


def downgrade() -> None:
    bind = op.get_bind()
    for table in NEW_TABLES:
        if bind.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first():
            raise RuntimeError("Refusing downgrade: Freelancer data exists. Use a forward migration.")
    if bind.execute(sa.text("SELECT 1 FROM users WHERE role = 'CLIENT' LIMIT 1")).first():
        raise RuntimeError("Refusing downgrade: CLIENT accounts exist.")
    if bind.execute(sa.text("SELECT 1 FROM users WHERE phone IS NOT NULL OR email_verified_at IS NOT NULL OR phone_verified_at IS NOT NULL LIMIT 1")).first():
        raise RuntimeError("Refusing downgrade: Freelancer account data exists.")
    if bind.execute(sa.text("SELECT 1 FROM companies WHERE business_status <> 'UNVERIFIED' OR operation_status <> 'ENABLED' OR representative_name IS NOT NULL OR representative_position IS NOT NULL OR is_legal_representative IS NOT NULL OR authorization_file_id IS NOT NULL OR business_verified_at IS NOT NULL OR business_verified_by IS NOT NULL OR suspension_reason IS NOT NULL OR suspended_at IS NOT NULL OR suspended_by IS NOT NULL OR (legal_name IS NOT NULL AND legal_name <> name) LIMIT 1")).first():
        raise RuntimeError("Refusing downgrade: Freelancer company data exists.")
    if bind.execute(sa.text("SELECT 1 FROM company_documents WHERE stored_file_id IS NOT NULL OR uploaded_by IS NOT NULL LIMIT 1")).first():
        raise RuntimeError("Refusing downgrade: Freelancer document data exists.")
    _drop_append_only_guards()
    if bind.dialect.name in ("mysql", "mariadb"):
        op.drop_constraint("fk_fc_effective_version", "freelance_contracts", type_="foreignkey")
        op.drop_constraint("fk_ms_effective_terms", "milestones", type_="foreignkey")
        op.alter_column("users", "role", existing_type=sa.Enum("STUDENT", "COMPANY", "ADMIN", "CLIENT", name="userrole"),
                        type_=sa.Enum("STUDENT", "COMPANY", "ADMIN", name="userrole"), existing_nullable=False)
    # Frozen schema; deliberately independent of live application models.
    with op.batch_alter_table('users') as batch:
        batch.drop_column('phone_verified_at')
        batch.drop_column('email_verified_at')
        batch.drop_column('phone')

    with op.batch_alter_table('company_documents') as batch:
        batch.drop_constraint(op.f('fk_company_documents_stored_file_id_stored_files'), type_='foreignkey')
        batch.drop_constraint(op.f('fk_company_documents_uploaded_by_users'), type_='foreignkey')
        batch.drop_column('uploaded_by')
        batch.drop_column('stored_file_id')

    with op.batch_alter_table('companies') as batch:
        # SQLite reflection can retain both the Enum name and the convention name.
        for constraint in sa.inspect(bind).get_check_constraints("companies"):
            if constraint.get("name") and any(column in constraint["sqltext"] for column in ("business_status", "operation_status")):
                batch.drop_constraint(op.f(constraint["name"]), type_="check")
        batch.drop_constraint(op.f('fk_companies_business_verified_by_users'), type_='foreignkey')
        batch.drop_constraint(op.f('fk_companies_authorization_file_id_stored_files'), type_='foreignkey')
        batch.drop_constraint(op.f('fk_companies_suspended_by_users'), type_='foreignkey')
        batch.drop_index('ix_companies_business_status_created_at')
        batch.drop_column('suspended_by')
        batch.drop_column('suspended_at')
        batch.drop_column('suspension_reason')
        batch.drop_column('operation_status')
        batch.drop_column('business_verified_by')
        batch.drop_column('business_verified_at')
        batch.drop_column('business_status')
        batch.drop_column('authorization_file_id')
        batch.drop_column('is_legal_representative')
        batch.drop_column('representative_position')
        batch.drop_column('representative_name')
        batch.drop_column('legal_name')
    op.drop_table('transfer_attempts')
    op.drop_index('ix_daily_limit_reservations_payment_order_id', table_name='daily_limit_reservations')
    op.drop_index('ix_daily_limit_reservations_money_transfer_id', table_name='daily_limit_reservations')
    op.drop_table('daily_limit_reservations')
    op.drop_index('ix_money_transfers_recipient_user_id', table_name='money_transfers')
    op.drop_index('ix_money_transfers_payment_transaction_id', table_name='money_transfers')
    op.drop_index('ix_money_transfers_obligation_journal_id', table_name='money_transfers')
    op.drop_index('ix_money_transfers_fee_journal_id', table_name='money_transfers')
    op.drop_index('ix_money_transfers_disbursement_journal_id', table_name='money_transfers')
    op.drop_index('ix_money_transfers_destination_id', table_name='money_transfers')
    op.drop_table('money_transfers')
    op.drop_index('ix_settlements_source_review_id', table_name='settlements')
    op.drop_index('ix_settlements_source_decision_id', table_name='settlements')
    op.drop_index('ix_settlements_source_cancellation_id', table_name='settlements')
    op.drop_index('ix_settlements_requested_by', table_name='settlements')
    op.drop_table('settlements')
    op.drop_index('ix_payment_review_cases_status_created_at', table_name='payment_review_cases')
    op.drop_index('ix_payment_review_cases_resolved_by', table_name='payment_review_cases')
    op.drop_index('ix_payment_review_cases_payment_transaction_id', table_name='payment_review_cases')
    op.drop_index('ix_payment_review_cases_assigned_to', table_name='payment_review_cases')
    op.drop_table('payment_review_cases')
    op.drop_index('ix_milestone_fundings_payment_transaction_id', table_name='milestone_fundings')
    op.drop_index('ix_milestone_fundings_milestone_id', table_name='milestone_fundings')
    op.drop_index('ix_milestone_fundings_funding_journal_id', table_name='milestone_fundings')
    op.drop_table('milestone_fundings')
    op.drop_index('ix_payment_transactions_receipt_journal_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_provider_event_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_payment_order_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_allocation_status_created_at', table_name='payment_transactions')
    op.drop_table('payment_transactions')
    op.drop_index('ix_milestone_reviews_reviewed_by', table_name='milestone_reviews')
    op.drop_index('ix_milestone_reviews_milestone_id_created_at', table_name='milestone_reviews')
    op.drop_table('milestone_reviews')
    op.drop_index('ix_milestone_holds_released_by', table_name='milestone_holds')
    op.drop_index('ix_milestone_holds_placed_by', table_name='milestone_holds')
    op.drop_index('ix_milestone_holds_milestone_id_released_at', table_name='milestone_holds')
    op.drop_index('ix_milestone_holds_milestone_id', table_name='milestone_holds')
    op.drop_index('ix_milestone_holds_dispute_id', table_name='milestone_holds')
    op.drop_table('milestone_holds')
    op.drop_index('ix_milestone_funding_guards_payment_order_id', table_name='milestone_funding_guards')
    op.drop_index('ix_milestone_funding_guards_milestone_id', table_name='milestone_funding_guards')
    op.drop_table('milestone_funding_guards')
    op.drop_index('ix_ledger_postings_account_id_journal_id', table_name='ledger_postings')
    op.drop_index('ix_ledger_postings_account_id', table_name='ledger_postings')
    op.drop_table('ledger_postings')
    op.drop_index('ix_escrow_accounts_milestone_id', table_name='escrow_accounts')
    op.drop_index('ix_escrow_accounts_ledger_account_id', table_name='escrow_accounts')
    op.drop_table('escrow_accounts')
    op.drop_index('ix_dispute_evidence_submitted_by', table_name='dispute_evidence')
    op.drop_index('ix_dispute_evidence_file_id', table_name='dispute_evidence')
    op.drop_index('ix_dispute_evidence_dispute_id_created_at', table_name='dispute_evidence')
    op.drop_index('ix_dispute_evidence_dispute_id', table_name='dispute_evidence')
    op.drop_index('ix_dispute_evidence_deliverable_id', table_name='dispute_evidence')
    op.drop_table('dispute_evidence')
    op.drop_index('ix_dispute_decisions_proposed_by', table_name='dispute_decisions')
    op.drop_index('ix_dispute_decisions_approved_by', table_name='dispute_decisions')
    op.drop_table('dispute_decisions')
    op.drop_index('ix_deliverable_files_file_id', table_name='deliverable_files')
    op.drop_index('ix_deliverable_files_deliverable_id', table_name='deliverable_files')
    op.drop_table('deliverable_files')
    op.drop_index('ix_active_milestone_disputes_milestone_id', table_name='active_milestone_disputes')
    op.drop_index('ix_active_milestone_disputes_dispute_id', table_name='active_milestone_disputes')
    op.drop_table('active_milestone_disputes')
    op.drop_index('ix_payment_orders_status_expires_at', table_name='payment_orders')
    op.drop_index('ix_payment_orders_milestone_id_created_at', table_name='payment_orders')
    op.drop_index('ix_payment_orders_milestone_id', table_name='payment_orders')
    op.drop_table('payment_orders')
    op.drop_index('ix_ledger_accounts_owner_user_id', table_name='ledger_accounts')
    op.drop_index('ix_ledger_accounts_milestone_id', table_name='ledger_accounts')
    op.drop_table('ledger_accounts')
    op.drop_index('ix_disputes_status_evidence_deadline', table_name='disputes')
    op.drop_index('ix_disputes_opened_by', table_name='disputes')
    op.drop_index('ix_disputes_milestone_id_created_at', table_name='disputes')
    op.drop_index('ix_disputes_milestone_id', table_name='disputes')
    op.drop_index('ix_disputes_assigned_admin_id', table_name='disputes')
    op.drop_table('disputes')
    op.drop_index('ix_deliverables_submitted_by', table_name='deliverables')
    op.drop_table('deliverables')
    op.drop_table('contract_milestone_terms')
    op.drop_index('ix_cancellation_agreements_requested_by', table_name='cancellation_agreements')
    op.drop_index('ix_cancellation_agreements_milestone_id_status', table_name='cancellation_agreements')
    op.drop_index('ix_cancellation_agreements_milestone_id', table_name='cancellation_agreements')
    op.drop_table('cancellation_agreements')
    op.drop_index('ix_project_contract_budgets_project_id_status', table_name='project_contract_budgets')
    op.drop_table('project_contract_budgets')
    op.drop_index('ix_milestones_status_review_deadline', table_name='milestones')
    op.drop_table('milestones')
    op.drop_index('ix_freelance_reviews_reviewer_user_id', table_name='freelance_reviews')
    op.drop_index('ix_freelance_reviews_reviewee_user_id', table_name='freelance_reviews')
    op.drop_table('freelance_reviews')
    op.drop_index('ix_contract_versions_created_by', table_name='contract_versions')
    op.drop_table('contract_versions')
    op.drop_index('ix_freelance_contracts_project_id_status', table_name='freelance_contracts')
    op.drop_index('ix_freelance_contracts_freelancer_student_id_status', table_name='freelance_contracts')
    op.drop_index('ix_freelance_contracts_freelancer_student_id', table_name='freelance_contracts')
    op.drop_index('ix_freelance_contracts_company_id', table_name='freelance_contracts')
    op.drop_index('ix_freelance_contracts_client_user_id_status', table_name='freelance_contracts')
    op.drop_index('ix_freelance_contracts_client_user_id', table_name='freelance_contracts')
    op.drop_index('ix_freelance_contracts_application_id', table_name='freelance_contracts')
    op.drop_table('freelance_contracts')
    op.drop_table('project_milestone_proposals')
    op.drop_index('ix_freelance_project_skills_skill_id', table_name='freelance_project_skills')
    op.drop_index('ix_freelance_project_skills_project_id', table_name='freelance_project_skills')
    op.drop_table('freelance_project_skills')
    op.drop_index('ix_freelance_project_reviews_reviewed_by', table_name='freelance_project_reviews')
    op.drop_index('ix_freelance_project_reviews_project_id_created_at', table_name='freelance_project_reviews')
    op.drop_index('ix_freelance_project_reviews_project_id', table_name='freelance_project_reviews')
    op.drop_table('freelance_project_reviews')
    op.drop_index('ix_freelance_applications_student_id_status_created_at', table_name='freelance_applications')
    op.drop_index('ix_freelance_applications_student_id', table_name='freelance_applications')
    op.drop_index('ix_freelance_applications_project_id_status', table_name='freelance_applications')
    op.drop_index('ix_freelance_applications_cv_snapshot_file_id', table_name='freelance_applications')
    op.drop_index('ix_freelance_applications_cv_id', table_name='freelance_applications')
    op.drop_table('freelance_applications')
    op.drop_index('ix_business_verification_files_verification_id', table_name='business_verification_files')
    op.drop_index('ix_business_verification_files_file_id', table_name='business_verification_files')
    op.drop_table('business_verification_files')
    op.drop_index('ix_mou_agreements_status_effective_until', table_name='mou_agreements')
    op.drop_index('ix_mou_agreements_school_authority_file_id', table_name='mou_agreements')
    op.drop_index('ix_mou_agreements_reviewed_by', table_name='mou_agreements')
    op.drop_index('ix_mou_agreements_document_file_id', table_name='mou_agreements')
    op.drop_index('ix_mou_agreements_company_id_status_effective_until', table_name='mou_agreements')
    op.drop_index('ix_mou_agreements_company_id', table_name='mou_agreements')
    op.drop_index('ix_mou_agreements_company_authority_file_id', table_name='mou_agreements')
    op.drop_table('mou_agreements')
    op.drop_index('ix_freelance_projects_status_recruitment_status_created_at', table_name='freelance_projects')
    op.drop_index('ix_freelance_projects_reviewed_by', table_name='freelance_projects')
    op.drop_index('ix_freelance_projects_company_id_status', table_name='freelance_projects')
    op.drop_index('ix_freelance_projects_company_id', table_name='freelance_projects')
    op.drop_index('ix_freelance_projects_client_user_id_status', table_name='freelance_projects')
    op.drop_index('ix_freelance_projects_client_user_id', table_name='freelance_projects')
    op.drop_table('freelance_projects')
    op.drop_index('ix_company_limits_set_by', table_name='company_limits')
    op.drop_index('ix_company_limits_company_id', table_name='company_limits')
    op.drop_table('company_limits')
    op.drop_index('ix_business_verifications_submitted_by', table_name='business_verifications')
    op.drop_index('ix_business_verifications_status_created_at', table_name='business_verifications')
    op.drop_index('ix_business_verifications_decided_by', table_name='business_verifications')
    op.drop_table('business_verifications')
    op.drop_index('ix_user_verifications_user_id_channel_created_at', table_name='user_verifications')
    op.drop_index('ix_user_verifications_user_id', table_name='user_verifications')
    op.drop_index('ix_user_verifications_status_expires_at', table_name='user_verifications')
    op.drop_table('user_verifications')
    op.drop_index('ix_stored_files_uploaded_by_created_at', table_name='stored_files')
    op.drop_index('ix_stored_files_uploaded_by', table_name='stored_files')
    op.drop_index('ix_stored_files_checksum_sha256', table_name='stored_files')
    op.drop_table('stored_files')
    op.drop_index('ix_reconciliation_items_status_created_at', table_name='reconciliation_items')
    op.drop_index('ix_reconciliation_items_resolved_by', table_name='reconciliation_items')
    op.drop_table('reconciliation_items')
    op.drop_index('ix_ledger_journals_reversal_of_id', table_name='ledger_journals')
    op.drop_index('ix_ledger_journals_reference_type_reference_id', table_name='ledger_journals')
    op.drop_index('ix_ledger_journals_posted_at', table_name='ledger_journals')
    op.drop_index('ix_ledger_journals_actor_user_id', table_name='ledger_journals')
    op.drop_table('ledger_journals')
    op.drop_table('command_requests')
    op.drop_index('ix_client_profiles_user_id', table_name='client_profiles')
    op.drop_table('client_profiles')
    op.drop_index('ix_bank_destinations_verified_by', table_name='bank_destinations')
    op.drop_table('bank_destinations')
    op.drop_index('ix_audit_logs_entity_type_entity_id_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_actor_user_id_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_actor_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_scheduled_jobs_status_run_at_lease_until', table_name='scheduled_jobs')
    op.drop_table('scheduled_jobs')
    op.drop_table('reconciliation_runs')
    op.drop_index('ix_provider_events_status_available_at_lease_until', table_name='provider_events')
    op.drop_table('provider_events')
    op.drop_index('ix_outbox_events_status_available_at_lease_until', table_name='outbox_events')
    op.drop_table('outbox_events')
    op.drop_table('daily_limit_buckets')
    # ### end Alembic commands ###
