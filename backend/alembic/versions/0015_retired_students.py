"""Prevent accidental recreation of expired graduates on subsequent imports."""
import sqlalchemy as sa

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("retired_students", sa.Column("code_hash", sa.String(64), primary_key=True), sa.Column("retired_on", sa.Date(), nullable=False))


def downgrade():
    op.drop_table("retired_students")
