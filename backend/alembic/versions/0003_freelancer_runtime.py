"""Freelancer runtime policy, OTP rate limits and mutual withdrawal.
Revision ID: 0003; Revises: 0002. Frozen schema, no data backfill.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def ident():
    return (
        sa.BigInteger()
        .with_variant(mysql.BIGINT(unsigned=True), "mysql")
        .with_variant(mysql.BIGINT(unsigned=True), "mariadb")
        .with_variant(sa.Integer(), "sqlite")
    )


def binary(size):
    return (
        sa.String(size)
        .with_variant(sa.String(size, collation="utf8mb4_bin"), "mysql")
        .with_variant(sa.String(size, collation="utf8mb4_bin"), "mariadb")
    )


def dt():
    return (
        sa.DateTime()
        .with_variant(mysql.DATETIME(fsp=6), "mysql")
        .with_variant(mysql.DATETIME(fsp=6), "mariadb")
    )


def upgrade():
    op.create_table(
        "freelancer_policies",
        sa.Column("id", ident(), primary_key=True, autoincrement=True),
        sa.Column("policy_key", binary(50), nullable=False, unique=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("values_json", sa.JSON(), nullable=False),
        sa.Column("updated_by", ident(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("updated_at", dt(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("revision > 0", name="revision_positive"),
    )
    op.create_table(
        "otp_rate_buckets",
        sa.Column("id", ident(), primary_key=True, autoincrement=True),
        sa.Column("scope_hash", binary(64), nullable=False, unique=True),
        sa.Column("window_started_at", dt(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count >= 0", name="count_nonnegative"),
    )
    op.create_table(
        "dispute_withdrawals",
        sa.Column("id", ident(), primary_key=True, autoincrement=True),
        sa.Column(
            "dispute_id",
            ident(),
            sa.ForeignKey("disputes.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "requested_by", ident(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("terms_hash", binary(64), nullable=False),
        sa.Column("confirmed_by", ident(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("created_at", dt(), nullable=False),
        sa.Column("confirmed_at", dt()),
        sa.CheckConstraint(
            "confirmed_by IS NULL OR confirmed_by <> requested_by", name="distinct_confirmers"
        ),
    )

    op.create_table(
        "project_expansions",
        sa.Column("id", ident(), primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            ident(),
            sa.ForeignKey("freelance_projects.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "requested_by",
            ident(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("request_key", binary(128), nullable=False),
        sa.Column("budget_amount", sa.BigInteger(), nullable=False),
        sa.Column("max_students", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column(
            "reviewed_by", ident(), sa.ForeignKey("users.id", ondelete="RESTRICT"), index=True
        ),
        sa.Column("review_reason", sa.Text()),
        sa.Column("reviewed_at", dt()),
        sa.Column("created_at", dt(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "project_id", "request_key", name="uq_project_expansions_project_id_request_key"
        ),
        sa.CheckConstraint("budget_amount > 0 AND max_students > 0", name="positive_ceilings"),
        sa.CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name="status_values"),
    )

    op.create_index("ix_freelancer_policies_updated_by", "freelancer_policies", ["updated_by"])
    op.create_index("ix_dispute_withdrawals_requested_by", "dispute_withdrawals", ["requested_by"])
    op.create_index("ix_dispute_withdrawals_confirmed_by", "dispute_withdrawals", ["confirmed_by"])


def downgrade():
    for table in (
        "project_expansions",
        "dispute_withdrawals",
        "otp_rate_buckets",
        "freelancer_policies",
    ):
        if op.get_bind().execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar():
            raise RuntimeError("Freelancer runtime data exists; use a forward migration")
    for table in (
        "project_expansions",
        "dispute_withdrawals",
        "otp_rate_buckets",
        "freelancer_policies",
    ):
        op.drop_table(table)
