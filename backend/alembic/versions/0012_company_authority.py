"""Record applicant identity and independent authority verification."""
from alembic import op
import sqlalchemy as sa
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('company_verifications', sa.Column('authority_data', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('company_verifications', 'authority_data')
