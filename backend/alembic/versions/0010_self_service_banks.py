"""Self-service bank destinations and durable payouts waiting for bank details."""
from alembic import op
import sqlalchemy as sa
from app.models.base import ID

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("bank_destinations") as batch:
        batch.drop_constraint(op.f("ck_bank_destinations_bank_destinations_verification_status"), type_="check")
        batch.create_check_constraint(op.f("ck_bank_destinations_bank_destinations_verification_status"), "verification_status IN ('ACTIVE','PENDING','VERIFIED','REJECTED','DISABLED')")
        batch.alter_column("verification_status", existing_type=sa.String(40), existing_nullable=False, server_default="ACTIVE")
    op.execute("UPDATE bank_destinations SET verification_status='ACTIVE', verification_source='SELF_DECLARED', verified_by=NULL, verified_at=NULL WHERE verification_status='PENDING'")
    with op.batch_alter_table("money_transfers") as batch:
        batch.drop_constraint(op.f("ck_money_transfers_money_transfers_status"), type_="check")
        batch.create_check_constraint(op.f("ck_money_transfers_money_transfers_status"), "status IN ('WAITING_BANK','READY','PROCESSING','UNKNOWN','SUCCEEDED','FAILED','CANCELLED')")
        batch.alter_column("destination_id", existing_type=ID, existing_nullable=False, nullable=True)
        batch.create_check_constraint(op.f("ck_money_transfers_transfer_bank_state"), "(status = 'WAITING_BANK' AND destination_id IS NULL) OR (status <> 'WAITING_BANK' AND destination_id IS NOT NULL)")


def downgrade():
    count = op.get_bind().execute(sa.text("SELECT COUNT(*) FROM money_transfers WHERE status='WAITING_BANK'")).scalar()
    if count:
        raise RuntimeError("Resolve WAITING_BANK transfers before downgrading; pending financial obligations must be preserved")
    with op.batch_alter_table("money_transfers") as batch:
        batch.drop_constraint(op.f("ck_money_transfers_transfer_bank_state"), type_="check")
        batch.drop_constraint(op.f("ck_money_transfers_money_transfers_status"), type_="check")
        batch.create_check_constraint(op.f("ck_money_transfers_money_transfers_status"), "status IN ('READY','PROCESSING','UNKNOWN','SUCCEEDED','FAILED','CANCELLED')")
        batch.alter_column("destination_id", existing_type=ID, existing_nullable=True, nullable=False)
    op.execute("UPDATE bank_destinations SET verification_status='PENDING' WHERE verification_status='ACTIVE'")
    with op.batch_alter_table("bank_destinations") as batch:
        batch.drop_constraint(op.f("ck_bank_destinations_bank_destinations_verification_status"), type_="check")
        batch.create_check_constraint(op.f("ck_bank_destinations_bank_destinations_verification_status"), "verification_status IN ('PENDING','VERIFIED','REJECTED','DISABLED')")
        batch.alter_column("verification_status", existing_type=sa.String(40), existing_nullable=False, server_default="PENDING")
