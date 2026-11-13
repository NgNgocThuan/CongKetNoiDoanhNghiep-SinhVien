"""Company verification 2-step, MOU hybrid signing and job board upgrades.

Nhiệm vụ 1: bảng company_verifications (OTP email + GPKD).
Nhiệm vụ 2: cột hybrid e-sign trên mou_agreements.
Nhiệm vụ 3: is_featured trên jobs, cột mời phỏng vấn trên applications.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def _dt():
    return sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql", "mariadb")


def _identifier():
    return (
        sa.BigInteger()
        .with_variant(sa.Integer(), "sqlite")
        .with_variant(mysql.BIGINT(unsigned=True), "mysql", "mariadb")
    )


def upgrade():
    op.create_table(
        "company_verifications",
        sa.Column("id", _identifier(), autoincrement=True, nullable=False),
        sa.Column("company_id", _identifier(), nullable=False),
        sa.Column("tax_code", sa.String(length=20), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("legal_representative", sa.String(length=100), nullable=False),
        sa.Column("business_address", sa.String(length=255), nullable=False),
        sa.Column("license_file_id", _identifier(), nullable=True),
        sa.Column("email_otp_verified", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("email_otp_code_hash", sa.String(length=255), nullable=True),
        sa.Column("email_otp_expires_at", _dt(), nullable=True),
        sa.Column("email_otp_attempts", mysql.INTEGER(unsigned=True), server_default="0", nullable=False),
        sa.Column("email_otp_resend_after", _dt(), nullable=True),
        sa.Column(
            "verification_status",
            sa.Enum("PENDING", "VERIFIED", "REJECTED", "NEEDS_REVISION", name="company_verifications_verification_status", native_enum=False, create_constraint=True, length=40),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("reviewer_user_id", _identifier(), nullable=True),
        sa.Column("reviewed_at", _dt(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", _dt(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", _dt(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.CheckConstraint("email_otp_attempts >= 0", name="email_otp_attempts_nonnegative"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name="fk_company_verifications_company_id_companies", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["license_file_id"], ["stored_files.id"], name="fk_company_verifications_license_file_id_stored_files", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], name="fk_company_verifications_reviewer_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_company_verifications"),
        sa.UniqueConstraint("company_id", name="uq_company_verifications_company_id"),
    )
    op.create_index(
        "ix_company_verifications_verification_status_created_at",
        "company_verifications",
        ["verification_status", "created_at"],
    )
    op.create_index(
        "ix_company_verifications_reviewer_user_id",
        "company_verifications",
        ["reviewer_user_id"],
    )

    with op.batch_alter_table("mou_agreements") as batch:
        batch.add_column(sa.Column("mou_type", sa.String(30), server_default="PAPER_SCAN", nullable=False))
        batch.add_column(sa.Column("sha256_hash", sa.String(length=64).with_variant(sa.String(length=64, collation="utf8mb4_bin"), "mysql", "mariadb"), nullable=True))
        batch.add_column(sa.Column("signer_tax_code", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("signer_common_name", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("certificate_issuer", sa.String(length=255), nullable=True))
        batch.create_index("ix_mou_agreements_company_id_mou_type", ["company_id", "mou_type"])

    with op.batch_alter_table("jobs") as batch:
        batch.add_column(sa.Column("is_featured", sa.Boolean(), server_default=sa.text("0"), nullable=False))
        batch.create_index("ix_jobs_is_featured_status", ["is_featured", "status"])

    with op.batch_alter_table("applications") as batch:
        batch.add_column(sa.Column("interview_time", _dt(), nullable=True))
        batch.add_column(sa.Column("interview_location", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("interview_notes", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("applications") as batch:
        batch.drop_column("interview_notes")
        batch.drop_column("interview_location")
        batch.drop_column("interview_time")
    with op.batch_alter_table("jobs") as batch:
        batch.drop_index("ix_jobs_is_featured_status")
        batch.drop_column("is_featured")
    with op.batch_alter_table("mou_agreements") as batch:
        batch.drop_index("ix_mou_agreements_company_id_mou_type")
        batch.drop_column("certificate_issuer")
        batch.drop_column("signer_common_name")
        batch.drop_column("signer_tax_code")
        batch.drop_column("sha256_hash")
        batch.drop_column("mou_type")
    op.drop_index("ix_company_verifications_reviewer_user_id", table_name="company_verifications")
    op.drop_index("ix_company_verifications_verification_status_created_at", table_name="company_verifications")
    op.drop_table("company_verifications")
