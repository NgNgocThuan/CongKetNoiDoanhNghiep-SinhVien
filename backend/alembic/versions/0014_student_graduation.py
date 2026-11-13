"""School graduation status and retention processing."""
import sqlalchemy as sa

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("academic_status", sa.String(20), nullable=False, server_default="STUDYING"))
    op.add_column("students", sa.Column("graduated_at", sa.Date()))
    op.add_column("students", sa.Column("account_expires_on", sa.Date()))
    op.add_column("students", sa.Column("lifecycle_stage", sa.String(30), nullable=False, server_default="NONE"))
    op.add_column("students", sa.Column("lifecycle_check_on", sa.Date()))
    op.create_index("ix_students_account_expires_on", "students", ["account_expires_on"])
    op.create_index("ix_students_lifecycle_check_on", "students", ["lifecycle_check_on"])


def downgrade():
    op.drop_index("ix_students_lifecycle_check_on", table_name="students")
    op.drop_index("ix_students_account_expires_on", table_name="students")
    for field in ("lifecycle_check_on", "lifecycle_stage", "account_expires_on", "graduated_at", "academic_status"):
        op.drop_column("students", field)
