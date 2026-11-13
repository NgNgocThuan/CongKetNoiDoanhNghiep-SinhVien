"""Explicit sharing of the default CV before an invitation."""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("student_profiles", sa.Column("show_cv", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column("student_profiles", "show_cv")
