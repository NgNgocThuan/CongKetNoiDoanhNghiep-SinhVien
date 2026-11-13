"""Regression checks for architecture boundaries, using an isolated SQLite database."""

from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.api.v1.endpoints.company_verification import AdminReviewRequest, review_verification
from app.core.config import settings
from app.core.enums import CompanyVerificationStatus, UserRole
from app.core.exceptions import AppException, BadRequestError, ConflictError, ForbiddenError
from app.models import Company, CompanyVerification
from app.services import mou_signing
from app.services.company_eligibility import require_verified_company
from app.utils.datetime_utils import utcnow


def company(db, make_user, *, verified=True):
    user = make_user(UserRole.COMPANY)
    user.email_verified_at = utcnow() if verified else None
    row = Company(
        user_id=user.id,
        name="Company",
        tax_code="0123456789",
        business_status="VERIFIED",
        verification_status="APPROVED",
    )
    db.add(row)
    db.commit()
    return row


def test_recruitment_requires_current_email_and_enabled_business(db, make_user):
    row = company(db, make_user, verified=False)
    with pytest.raises(ForbiddenError):
        require_verified_company(row)
    row.user.email_verified_at = utcnow()
    require_verified_company(row)
    row.operation_status = "SUSPENDED"
    with pytest.raises(ForbiddenError):
        require_verified_company(row)


def test_verification_status_reads_shared_email_fact(client, db, make_user, auth_headers):
    row = company(db, make_user)
    response = client.get("/api/v1/company/verification/status", headers=auth_headers(row.user))
    assert response.status_code == 200
    assert response.json()["email_otp_verified"] is True


def test_admin_cannot_approve_empty_verification(db, make_user):
    row = company(db, make_user)
    verif = CompanyVerification(
        company_id=row.id,
        tax_code=row.tax_code,
        company_name=row.name,
        legal_representative="A",
        business_address="B",
    )
    db.add(verif)
    db.commit()
    with pytest.raises(ConflictError):
        review_verification(
            verif.id,
            AdminReviewRequest(status="VERIFIED"),
            make_user(UserRole.ADMIN),
            db,
            BackgroundTasks(),
        )
    assert row.business_status == "VERIFIED"
    assert verif.verification_status == CompanyVerificationStatus.PENDING


def test_unconfigured_hybrid_never_generates_fake_signed_pdf(monkeypatch):
    monkeypatch.setattr(settings, "MOU_SCHOOL_PFX_PATH", "")
    with pytest.raises(AppException) as error:
        mou_signing.signing_material()
    assert error.value.status_code == 503


@pytest.fixture
def certificates(tmp_path, monkeypatch):
    from datetime import datetime, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID

    paths = []
    for name, tax in [("School", "school"), ("Company", "0123456789")]:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, name),
                x509.NameAttribute(NameOID.SERIAL_NUMBER, tax),
            ]
        )
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=10))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=True,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(key, hashes.SHA256())
        )
        pfx = tmp_path / f"{name}.pfx"
        pem = tmp_path / f"{name}.pem"
        pfx.write_bytes(
            pkcs12.serialize_key_and_certificates(
                name.encode(), key, cert, None, serialization.NoEncryption()
            )
        )
        pem.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        paths.append((pfx, pem))
    monkeypatch.setattr(settings, "MOU_SCHOOL_PFX_PATH", str(paths[0][0]))
    monkeypatch.setattr(settings, "MOU_SCHOOL_PFX_PASSWORD", "")
    monkeypatch.setattr(settings, "MOU_TRUST_ROOT_PATH", str(paths[1][1]))
    return paths


def test_real_school_signature_and_company_identity(certificates):
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign import signers

    from app.api.v1.endpoints.company_mou import _generate_mou_pdf

    row = SimpleNamespace(id=12, tax_code="0123456789")
    pdf = _generate_mou_pdf("Company", row.tax_code, "Representative")
    school_pdf = mou_signing.sign_template(pdf, row)
    assert len(PdfFileReader(BytesIO(school_pdf)).embedded_signatures) == 1
    with pytest.raises(BadRequestError):
        mou_signing.validate_company_pdf(school_pdf, row)
    signer = signers.SimpleSigner.load_pkcs12(str(certificates[1][0]))
    signed = signers.sign_pdf(
        IncrementalPdfFileWriter(BytesIO(school_pdf)),
        signers.PdfSignatureMetadata(field_name="CompanySignature"),
        signer=signer,
    ).getvalue()
    assert mou_signing.validate_company_pdf(signed, row)[1] == row.tax_code
    with pytest.raises(BadRequestError):
        mou_signing.validate_company_pdf(signed.replace(b"StudentConnect", b"StudentConnecX"), row)
    with pytest.raises(BadRequestError):
        mou_signing.validate_company_pdf(b"%PDF /ByteRange /Contents", row)
    with pytest.raises(BadRequestError):
        mou_signing.validate_company_pdf(signed, SimpleNamespace(id=99, tax_code=row.tax_code))
    with pytest.raises(BadRequestError):
        mou_signing.validate_company_pdf(signed, SimpleNamespace(id=12, tax_code="9999999999"))


def test_new_job_board_hides_unapproved_jobs(client, db, make_user, auth_headers):
    # An active account alone cannot publish via the new parallel API.
    row = company(db, make_user, verified=False)
    response = client.post(
        "/api/v1/job-board/jobs",
        headers=auth_headers(row.user),
        json={
            "title": "Test",
            "position": "Developer",
            "description": "Test",
            "deadline": "2027-12-31",
        },
    )
    assert response.status_code == 403


def test_public_job_detail_cannot_read_drafts(client, db, make_user):
    from app.models import Job, JobType

    row = company(db, make_user)
    kind = JobType(code="FULL_TIME", name="Full time")
    db.add(kind)
    db.flush()
    job = Job(
        company_id=row.id,
        job_type_id=kind.id,
        title="Private draft",
        position="Dev",
        description="Private",
        deadline=utcnow().date() + timedelta(days=20),
        status="DRAFT",
    )
    db.add(job)
    db.commit()
    assert client.get(f"/api/v1/job-board/jobs/{job.id}").status_code == 404
    job.status = "APPROVED"
    db.commit()
    assert client.get(f"/api/v1/job-board/jobs/{job.id}").status_code == 200


def test_company_legal_upload_accepts_actual_frontend_contract(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    row = company(db, make_user)
    row.business_status = "UNVERIFIED"
    db.commit()
    fields = {
        "tax_code": row.tax_code,
        "company_name": row.name,
        "legal_representative": "Representative",
        "business_address": "Address",
        "applicant_name": "Representative",
        "applicant_position": "Director",
        "applicant_phone": "0912345678",
        "applicant_capacity": "LEGAL_REPRESENTATIVE",
    }
    files = {
        "license_file": ("license.pdf", b"%PDF-test", "application/pdf"),
        "authority_file": ("authority.pdf", b"%PDF-proof", "application/pdf"),
    }
    response = client.post(
        "/api/v1/company/verification/submit-legal-docs",
        headers=auth_headers(row.user),
        data=fields,
        files=files,
    )
    assert response.status_code == 200, response.text
    again = client.post(
        "/api/v1/company/verification/submit-legal-docs",
        headers=auth_headers(row.user),
        data=fields,
        files=files,
    )
    assert again.status_code == 409
    verif = db.query(CompanyVerification).one()
    with pytest.raises(BadRequestError):
        review_verification(
            verif.id,
            AdminReviewRequest(status="VERIFIED"),
            make_user(UserRole.ADMIN),
            db,
            BackgroundTasks(),
        )


def test_paper_mou_review_requires_scan_and_schedules_expiry(
    client, db, make_user, auth_headers, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "FREELANCER_FILE_SCAN_ENABLED", True)
    from app.api.v1.endpoints import company_mou
    from app.models import MouAgreement, ScheduledJob, StoredFile

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(company_mou, "queue_email", lambda *args, **kwargs: None)
    row = company(db, make_user)
    admin = make_user(UserRole.ADMIN)
    response = client.post(
        "/api/v1/company/mou/submit-paper-scan",
        headers=auth_headers(row.user),
        data={"signer_name": "Representative", "signer_position": "Director"},
        files={"mou_file": ("mou.pdf", b"%PDF-test", "application/pdf")},
    )
    assert response.status_code == 200, response.text
    mou = db.query(MouAgreement).one()
    url = f"/api/v1/admin/mou/agreements/{mou.id}/review"
    assert (
        client.post(url, headers=auth_headers(admin), json={"action": "APPROVE"}).status_code == 409
    )
    file = db.get(StoredFile, mou.document_file_id)
    file.scan_status = "CLEAN"
    db.commit()
    response = client.post(url, headers=auth_headers(admin), json={"action": "APPROVE"})
    assert response.status_code == 200, response.text
    assert db.query(ScheduledJob).filter_by(job_key=f"mou.expire:{mou.id}").count() == 1
    assert db.query(ScheduledJob).filter_by(job_type="mou.reminder").count() == 4
    assert (
        client.post(url, headers=auth_headers(admin), json={"action": "APPROVE"}).status_code == 409
    )
