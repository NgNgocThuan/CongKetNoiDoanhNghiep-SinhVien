"""School-confirmed withdrawal date."""
import sqlalchemy as sa

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("withdrawn_at", sa.Date()))


def downgrade():
    op.drop_column("students", "withdrawn_at")
