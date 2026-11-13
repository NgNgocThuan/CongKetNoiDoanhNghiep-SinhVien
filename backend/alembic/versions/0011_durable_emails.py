"""Persist encrypted email payloads and retry scheduling."""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("email_logs", sa.Column("body_encrypted", sa.Text(), nullable=True))
    op.add_column("email_logs", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("email_logs", sa.Column("next_attempt_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("email_logs", "next_attempt_at")
    op.drop_column("email_logs", "expires_at")
    op.drop_column("email_logs", "body_encrypted")
