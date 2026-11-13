"""Account avatars for every role."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from app.models.base import ID

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_avatars",
        sa.Column("user_id", ID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("image", sa.LargeBinary().with_variant(MEDIUMBLOB(), "mysql", "mariadb"), nullable=False),
    )


def downgrade():
    op.drop_table("user_avatars")
