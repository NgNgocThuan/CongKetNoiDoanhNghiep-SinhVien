"""Separate recruitment dates, enrich project posts and allow incomplete drafts.

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    timestamp = sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql", "mariadb")
    with op.batch_alter_table("freelance_projects") as batch:
        batch.alter_column("budget_amount", existing_type=sa.BigInteger(), nullable=True)
        batch.alter_column("deadline", existing_type=timestamp, nullable=True)
        batch.add_column(sa.Column("recruitment_deadline", timestamp, nullable=True))
        batch.add_column(sa.Column("category", sa.String(30), nullable=True))
        batch.add_column(sa.Column("experience_level", sa.String(20), nullable=True))
        batch.create_index("ix_freelance_projects_category_status", ["category", "status"])
    # Preserve the old recruitment cutoff, which previously used the project deadline.
    op.execute("UPDATE freelance_projects SET recruitment_deadline = deadline, category = 'OTHER'")
    identifier = (
        sa.BigInteger()
        .with_variant(sa.Integer(), "sqlite")
        .with_variant(mysql.BIGINT(unsigned=True), "mysql", "mariadb")
    )
    op.create_table(
        "freelance_project_attachments",
        sa.Column(
            "project_id",
            identifier,
            sa.ForeignKey("freelance_projects.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "file_id",
            identifier,
            sa.ForeignKey("stored_files.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_freelance_project_attachments_file_id", "freelance_project_attachments", ["file_id"]
    )


def downgrade():
    connection = op.get_bind()
    # Refuse a downgrade that would discard new user data or require invented values.
    incomplete = connection.scalar(
        sa.text(
            "SELECT COUNT(*) FROM freelance_projects WHERE budget_amount IS NULL OR deadline IS NULL"
        )
    )
    attachments = connection.scalar(sa.text("SELECT COUNT(*) FROM freelance_project_attachments"))
    changed = connection.scalar(
        sa.text(
            "SELECT COUNT(*) FROM freelance_projects WHERE experience_level IS NOT NULL OR (category IS NOT NULL AND category <> 'OTHER') OR recruitment_deadline <> deadline"
        )
    )
    if incomplete or attachments or changed:
        raise RuntimeError("Project posting data exists; export/resolve it before downgrading 0005")
    op.drop_table("freelance_project_attachments")
    timestamp = sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql", "mariadb")
    with op.batch_alter_table("freelance_projects") as batch:
        batch.drop_index("ix_freelance_projects_category_status")
        batch.drop_column("experience_level")
        batch.drop_column("category")
        batch.drop_column("recruitment_deadline")
        batch.alter_column("deadline", existing_type=timestamp, nullable=False)
        batch.alter_column("budget_amount", existing_type=sa.BigInteger(), nullable=False)
