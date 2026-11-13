from datetime import datetime

from sqlalchemy import select

from app.core.enums import UserRole
from app.models import CompanyVerification, EmailLog, Notification
from tests.freelancer.test_group_a_api import company, stored


def test_retired_verification_routes_are_not_exposed(client):
    paths = client.get('/api/v1/openapi.json').json()['paths']
    assert '/api/v1/company/verification/submit-legal-docs' in paths
    assert '/api/v1/admin/verifications/{verification_id}/review' in paths
    assert not any('business-verifications' in p or p.endswith('/companies/me/verifications') for p in paths)


def pending(db, make_user, capacity='AUTHORIZED_RECRUITER'):
    user = make_user(UserRole.COMPANY)
    user.email_verified_at = datetime.now()
    c = company(db, user, business_status='PENDING_VERIFICATION')
    license = stored(db, user)
    license.category = 'BUSINESS_LICENSE'
    from app.models import StoredFile
    authority = StoredFile(uploaded_by=user.id, storage_key='authority.pdf', original_name='authority.pdf',
        content_type='application/pdf', size_bytes=10, checksum_sha256='b'*64, category='AUTHORIZATION', scan_status='CLEAN', availability_status='AVAILABLE')
    db.add(authority)
    db.flush()
    authority.category = 'AUTHORIZATION'
    row = CompanyVerification(company_id=c.id, company_name=c.name, tax_code=c.tax_code,
        legal_representative='Director', business_address='Address', license_file_id=license.id,
        authority_data=dict(applicant_name='Recruiter', applicant_email=user.email,
                            applicant_capacity=capacity, authority_file_id=authority.id))
    db.add(row)
    db.commit()
    return user, c, row


def test_requires_separate_checks_and_independent_source(client, db, make_user, auth_headers):
    _, c, row = pending(db, make_user)
    admin = make_user(UserRole.ADMIN)
    url = f'/api/v1/admin/verifications/{row.id}/review'
    headers = auth_headers(admin)
    assert client.post(url, headers=headers, json={'status':'VERIFIED'}).status_code == 400
    valid = dict(status='VERIFIED', legal_identity_checked=True, representative_authority_checked=True,
                 verification_method='INDEPENDENT_CALLBACK', independent_source='Official directory checked independently',
                 confirmation_reference='Director confirmed recruiter by callback 13/11')
    for field in ('independent_source', 'confirmation_reference'):
        assert client.post(url, headers=headers, json={**valid, field:''}).status_code == 400
    assert client.post(url, headers=headers, json={**valid, 'verification_method':'IDENTITY_MATCH'}).status_code == 400
    assert client.post(url, headers=headers, json=valid).status_code == 200
    db.refresh(c)
    db.refresh(row)
    assert c.business_status == 'VERIFIED' and row.authority_data['verification_method'] == 'INDEPENDENT_CALLBACK'
    assert db.scalar(select(Notification).where(Notification.user_id==c.user_id))
    assert db.scalar(select(EmailLog).where(EmailLog.user_id==c.user_id))
    assert client.post(url, headers=headers, json=valid).status_code == 409


def test_revision_needs_reason_and_old_data_cannot_be_approved(client, db, make_user, auth_headers):
    _, c, row = pending(db, make_user)
    row.authority_data = None
    db.commit()
    admin = make_user(UserRole.ADMIN)
    url = f'/api/v1/admin/verifications/{row.id}/review'
    headers = auth_headers(admin)
    assert client.post(url, headers=headers, json={'status':'NEEDS_REVISION'}).status_code == 400
    assert client.post(url, headers=headers, json=dict(status='VERIFIED', legal_identity_checked=True,
        representative_authority_checked=True, verification_method='IN_PERSON', independent_source='School', confirmation_reference='Visit')).status_code == 400
    assert client.post(url, headers=headers, json={'status':'NEEDS_REVISION','reason':'Bổ sung quyền đại diện'}).status_code == 200
    db.refresh(c)
    assert c.business_status == 'NEEDS_REVISION'


def test_email_changed_and_other_company_cannot_review(client, db, make_user, auth_headers):
    user, _, row = pending(db, make_user)
    other = make_user(UserRole.COMPANY)
    admin = make_user(UserRole.ADMIN)
    data = dict(status='VERIFIED', legal_identity_checked=True, representative_authority_checked=True,
                verification_method='OFFICIAL_EMAIL', independent_source='Official site', confirmation_reference='Email confirmation')
    url = f'/api/v1/admin/verifications/{row.id}/review'
    assert client.post(url, headers=auth_headers(other), json=data).status_code == 403
    user.email = 'changed@example.test'
    db.commit()
    assert client.post(url, headers=auth_headers(admin), json=data).status_code == 400


def test_submit_new_files_and_pending_account_can_follow_status(client, db, make_user, auth_headers, monkeypatch, tmp_path):
    from app.core.config import settings
    from app.core.enums import UserStatus
    from app.core.security import _create_token
    monkeypatch.setattr(settings, 'UPLOAD_DIR', str(tmp_path))
    monkeypatch.setattr(settings, 'FREELANCER_FILE_SCAN_ENABLED', False)
    u = make_user(UserRole.COMPANY, status=UserStatus.PENDING_APPROVAL)
    u.email_verified_at = datetime.now()
    c = company(db, u, business_status='UNVERIFIED')
    db.commit()
    headers = {'Authorization': 'Bearer ' + _create_token(str(u.id), 'onboarding', __import__('datetime').timedelta(minutes=15))}
    assert client.get('/api/v1/company/verification/status', headers=headers).status_code == 200
    data = dict(tax_code=c.tax_code, company_name=c.name, legal_representative='Director', business_address='Address',
                applicant_name='Recruiter', applicant_position='HR', applicant_phone='0912345678', applicant_capacity='AUTHORIZED_RECRUITER')
    files = {'license_file': ('license.pdf', b'%PDF-1.4\nlicense', 'application/pdf'),
             'authority_file': ('authority.pdf', b'%PDF-1.4\nauthority', 'application/pdf')}
    response = client.post('/api/v1/company/verification/submit-legal-docs', headers=headers, data=data, files=files)
    assert response.status_code == 200, response.text
    row = db.scalar(select(CompanyVerification).where(CompanyVerification.company_id==c.id))
    assert row.authority_data['applicant_email'] == u.email
    assert client.post('/api/v1/company/verification/submit-legal-docs', headers=headers, data=data, files=files).status_code == 409
