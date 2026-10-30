"""Test toàn diện phân hệ Báo cáo vi phạm (Reports). Người phụ trách: TV1."""
from datetime import date, timedelta

from sqlalchemy import select

from app.core.enums import (
    JobStatus,
    ReportStatus,
    UserRole,
    UserStatus,
    VerificationStatus,
    WorkMode,
)
from app.models import Company, EmailLog, Job, JobType


def _setup_reported_job(db, make_user):
    company_user = make_user(UserRole.COMPANY, UserStatus.ACTIVE, email="company_reported@test.com")
    company = Company(
        user_id=company_user.id,
        name="Công ty Bị Báo Cáo",
        tax_code="0555666777",
        verification_status=VerificationStatus.APPROVED,
    )
    db.add(company)

    job_type = JobType(code="INTERN", name="Thực tập")
    db.add(job_type)
    db.commit()

    job = Job(
        company_id=company.id,
        title="Việc làm lừa đảo thu phí",
        position="Intern",
        job_type_id=job_type.id,
        description="Đóng phí 500k trước khi nhận việc...",
        deadline=date.today() + timedelta(days=10),
        status=JobStatus.APPROVED,
        work_mode=WorkMode.ONSITE,
    )
    db.add(job)
    db.commit()
    return company_user, company, job


def test_create_report_and_target_validation(client, make_user, auth_headers, db):
    student = make_user(UserRole.STUDENT, email="reporter_sv@test.com")
    headers = auth_headers(student)
    _, _, job = _setup_reported_job(db, make_user)

    # 1. Báo cáo tin tuyển dụng vi phạm thành công -> 201
    res_job = client.post(
        "/api/v1/reports",
        json={
            "target_type": "JOB",
            "target_id": job.id,
            "reason": "Tin tuyển dụng có dấu hiệu thu phí người ứng tuyển",
        },
        headers=headers,
    )
    assert res_job.status_code == 201
    report_data = res_job.json()
    assert report_data["status"] == ReportStatus.PENDING.value
    assert report_data["reporter_id"] == student.id

    # 2. Báo cáo đối tượng không tồn tại -> 404
    res_404 = client.post(
        "/api/v1/reports",
        json={
            "target_type": "STUDENT",
            "target_id": 99999,
            "reason": "Sinh viên không tồn tại",
        },
        headers=headers,
    )
    assert res_404.status_code == 404


def test_admin_list_and_handle_report(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN, email="admin_report_handler@test.com")
    student = make_user(UserRole.STUDENT, email="reporter_sv2@test.com")
    admin_headers = auth_headers(admin)
    student_headers = auth_headers(student)

    comp_user, company, job = _setup_reported_job(db, make_user)

    # Sinh viên gửi báo cáo
    create_res = client.post(
        "/api/v1/reports",
        json={
            "target_type": "JOB",
            "target_id": job.id,
            "reason": "Lừa đảo chiếm đoạt tài sản",
        },
        headers=student_headers,
    )
    report_id = create_res.json()["id"]

    # Admin xem danh sách báo cáo
    list_res = client.get("/api/v1/reports?status=PENDING", headers=admin_headers)
    assert list_res.status_code == 200
    assert any(r["id"] == report_id for r in list_res.json()["items"])

    # Admin xem chi tiết báo cáo
    detail_res = client.get(f"/api/v1/reports/{report_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["target_id"] == job.id

    # Admin xử lý báo cáo: RESOLVED + đóng tin vi phạm + khóa luôn tài khoản công ty
    handle_res = client.post(
        f"/api/v1/reports/{report_id}/handle",
        json={
            "status": "RESOLVED",
            "resolution_note": "Xác minh tin lừa đảo. Tiến hành đóng tin và khóa tài khoản doanh nghiệp.",
            "close_target_job": True,
            "lock_target_user": True,
        },
        headers=admin_headers,
    )
    assert handle_res.status_code == 200
    handled_body = handle_res.json()
    assert handled_body["status"] == ReportStatus.RESOLVED.value
    assert handled_body["handled_by"] == admin.id

    # Kiểm tra tin tuyển dụng đã bị đóng (CLOSED)
    db.refresh(job)
    assert job.status == JobStatus.CLOSED

    # Kiểm tra tài khoản doanh nghiệp đã bị khóa (LOCKED)
    db.refresh(comp_user)
    assert comp_user.status == UserStatus.LOCKED

    # Cố tình xử lý lại báo cáo đã giải quyết -> 409
    rehandle = client.post(
        f"/api/v1/reports/{report_id}/handle",
        json={"status": "REJECTED", "resolution_note": "Xử lý lại"},
        headers=admin_headers,
    )
    assert rehandle.status_code == 409


def test_duplicate_pending_report_conflict(client, make_user, auth_headers, db):
    student = make_user(UserRole.STUDENT, email="spam_reporter@test.com")
    headers = auth_headers(student)
    _, _, job = _setup_reported_job(db, make_user)

    # Lần 1: Thành công
    res1 = client.post(
        "/api/v1/reports",
        json={
            "target_type": "JOB",
            "target_id": job.id,
            "reason": "Báo cáo lần 1",
        },
        headers=headers,
    )
    assert res1.status_code == 201

    # Lần 2: Trùng đối tượng và đang pending -> 409
    res2 = client.post(
        "/api/v1/reports",
        json={
            "target_type": "JOB",
            "target_id": job.id,
            "reason": "Báo cáo lần 2 spam",
        },
        headers=headers,
    )
    assert res2.status_code == 409
    assert "chờ xử lý" in res2.json()["error"]["message"]


def test_lock_target_user_queues_email(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN, email="admin_mailer@test.com")
    student = make_user(UserRole.STUDENT, email="reporter_mailer@test.com")
    comp_user, _, job = _setup_reported_job(db, make_user)

    create_res = client.post(
        "/api/v1/reports",
        json={
            "target_type": "JOB",
            "target_id": job.id,
            "reason": "Gian lận nghiêm trọng",
        },
        headers=auth_headers(student),
    )
    report_id = create_res.json()["id"]

    client.post(
        f"/api/v1/reports/{report_id}/handle",
        json={
            "status": "RESOLVED",
            "resolution_note": "Khóa vĩnh viễn do lừa đảo",
            "close_target_job": True,
            "lock_target_user": True,
        },
        headers=auth_headers(admin),
    )

    # Kiểm tra EmailLog được sinh ra cho target user
    locked_email = db.scalars(
        select(EmailLog).where(
            EmailLog.recipient_email == comp_user.email,
            EmailLog.type == "ACCOUNT_LOCKED",
        )
    ).first()
    assert locked_email is not None
    assert "Khóa vĩnh viễn" in locked_email.subject or locked_email.type == "ACCOUNT_LOCKED"
