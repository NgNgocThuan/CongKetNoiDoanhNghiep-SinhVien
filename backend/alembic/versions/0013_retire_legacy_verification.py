"""Release pending legacy submissions so applicants can use authority verification."""
from alembic import op

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None

def upgrade():
    # Preserve approved companies and submissions in the new workflow.
    op.execute("""UPDATE companies SET business_status='NEEDS_REVISION'
        WHERE business_status='PENDING_VERIFICATION'
        AND id IN (SELECT company_id FROM business_verifications WHERE status='PENDING')
        AND NOT EXISTS (SELECT 1 FROM company_verifications cv WHERE cv.company_id=companies.id
            AND cv.verification_status IN ('PENDING','VERIFIED') AND cv.license_file_id IS NOT NULL)""")
    op.execute("""UPDATE business_verifications SET status='NEEDS_REVISION',
        reason='Luồng cũ đã ngừng nhận. Vui lòng nộp hồ sơ xác minh pháp nhân và quyền đại diện theo luồng mới.'
        WHERE status='PENDING'""")

def downgrade():
    # Never silently reopen retired approval requests.
    pass
