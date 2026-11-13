"""Persist explicit registration and escrow terms acceptance."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import DATETIME

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    for prefix in ("registration", "escrow"):
        timestamp = sa.DateTime().with_variant(DATETIME(fsp=6), "mysql", "mariadb")
        op.add_column("users", sa.Column(f"{prefix}_terms_accepted_at", timestamp, nullable=True))
        op.add_column("users", sa.Column(f"{prefix}_terms_version", sa.String(32), nullable=True))


def downgrade():
    for prefix in ("escrow", "registration"):
        op.drop_column("users", f"{prefix}_terms_version")
        op.drop_column("users", f"{prefix}_terms_accepted_at")
