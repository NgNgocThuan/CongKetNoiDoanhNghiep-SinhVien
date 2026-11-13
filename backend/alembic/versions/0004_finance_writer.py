"""Serialize financial writers and allocate globally unique payOS order codes.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    table = op.create_table(
        "finance_counters",
        sa.Column("name", sa.String(50), primary_key=True),
        sa.Column("next_value", sa.BigInteger(), nullable=False),
    )
    op.bulk_insert(table, [{"name": "writer", "next_value": 1000000000}])
    op.execute(
        "UPDATE finance_counters SET next_value = (SELECT CASE WHEN MAX(order_code) >= 1000000000 THEN MAX(order_code) + 1 ELSE 1000000000 END FROM payment_orders) WHERE name='writer'"
    )
    id_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
    from sqlalchemy.dialects import mysql

    id_type = id_type.with_variant(mysql.BIGINT(unsigned=True), "mysql").with_variant(
        mysql.BIGINT(unsigned=True), "mariadb"
    )
    table = op.create_table(
        "treasury_entries",
        sa.Column("id", id_type, primary_key=True, autoincrement=True),
        sa.Column(
            "external_reference",
            sa.String(150)
            .with_variant(mysql.VARCHAR(150, collation="utf8mb4_bin"), "mysql")
            .with_variant(mysql.VARCHAR(150, collation="utf8mb4_bin"), "mariadb"),
            nullable=False,
            unique=True,
        ),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column(
            "evidence_file_id",
            id_type,
            sa.ForeignKey("stored_files.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "proposed_by", id_type, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "approved_by", id_type, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PROPOSED"),
        sa.Column(
            "journal_id",
            id_type,
            sa.ForeignKey("ledger_journals.id", ondelete="RESTRICT"),
            nullable=True,
            unique=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql", "mariadb"),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "posted_at",
            sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql", "mariadb"),
            nullable=True,
        ),
        sa.CheckConstraint("amount > 0", name="positive_amount"),
        sa.CheckConstraint(
            "kind IN ('TRANSFER_TO_PAYOUT','EQUITY_BANK','EQUITY_PAYOUT','FEE_BANK','FEE_PAYOUT')",
            name="valid_kind",
        ),
        sa.CheckConstraint("status IN ('PROPOSED','POSTED','REJECTED')", name="valid_status"),
        sa.CheckConstraint(
            "approved_by IS NULL OR approved_by <> proposed_by", name="distinct_approvers"
        ),
    )
    for field in ("evidence_file_id", "proposed_by", "approved_by"):
        op.create_index(f"ix_treasury_entries_{field}", "treasury_entries", [field])


def downgrade():
    connection = op.get_bind()
    value = connection.execute(
        sa.text("SELECT next_value FROM finance_counters WHERE name='writer'")
    ).scalar()
    used = connection.execute(sa.text("SELECT COUNT(*) FROM ledger_journals")).scalar()
    treasury = connection.execute(sa.text("SELECT COUNT(*) FROM treasury_entries")).scalar()
    if value != 1000000000 or used or treasury:
        raise RuntimeError("Freelancer data exists; financial sequence cannot be reset")
    op.drop_table("treasury_entries")
    op.drop_table("finance_counters")
