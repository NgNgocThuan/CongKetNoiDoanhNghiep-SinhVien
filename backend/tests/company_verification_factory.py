"""Create submitted proof metadata and exercise the real admin authority decision."""
from uuid import uuid4

from app.models import Company, CompanyVerification, StoredFile
from app.utils.datetime_utils import utcnow


def approve_submitted_company(client, db, company_id, admin_headers):
    company = db.get(Company, company_id)
    company.user.email_verified_at = utcnow()
    company.business_status = 'PENDING_VERIFICATION'
    files = []
    for category in ('BUSINESS_LICENSE', 'AUTHORIZATION'):
        file = StoredFile(uploaded_by=company.user_id, storage_key=uuid4().hex,
            original_name='proof.pdf', content_type='application/pdf', size_bytes=10,
            checksum_sha256='a'*64, category=category, scan_status='CLEAN', availability_status='AVAILABLE')
        db.add(file)
        db.flush()
        files.append(file)
    row = CompanyVerification(company_id=company.id, tax_code=company.tax_code, company_name=company.name,
        legal_representative='Director', business_address='Office', license_file_id=files[0].id,
        authority_data=dict(applicant_email=company.user.email, applicant_name='Director',
                            applicant_capacity='LEGAL_REPRESENTATIVE', authority_file_id=files[1].id))
    db.add(row)
    db.commit()
    response = client.post(f'/api/v1/admin/verifications/{row.id}/review', headers=admin_headers,
        json=dict(status='VERIFIED', legal_identity_checked=True, representative_authority_checked=True,
                  verification_method='IN_PERSON', independent_source='School identity check',
                  confirmation_reference='Identity matched to registered director'))
    assert response.status_code == 200, response.text
    return response
