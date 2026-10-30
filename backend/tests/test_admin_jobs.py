"""Test toàn diện phân hệ Kiểm duyệt Tin tuyển dụng. Người phụ trách: TV1."""
from datetime import date, timedelta

from app.core.enums import JobStatus, UserRole, UserStatus, VerificationStatus, WorkMode
from app.models import Company, Job, JobType


def _setup_job(db, make_user, *, status=JobStatus.PENDING_APPROVAL):
    company_user = make_user(UserRole.COMPANY, UserStatus.ACTIVE, email="company_poster@test.com")
    company = Company(
        user_id=company_user.id,
        name="Công ty Tuyển Dụng",
        tax_code="0333444555",
        verification_status=VerificationStatus.APPROVED,
    )
    db.add(company)

    job_type = JobType(code="FULL_TIME", name="Toàn thời gian")
    db.add(job_type)
    db.commit()

    job = Job(
        company_id=company.id,
        title="Kỹ sư phần mềm Backend Python",
        position="Backend Engineer",
        job_type_id=job_type.id,
        description="Mô tả công việc chi tiết...",
        deadline=date.today() + timedelta(days=30),
        status=status,
        work_mode=WorkMode.HYBRID,
    )
    db.add(job)
    db.commit()
    return company, job


def test_list_and_get_job(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)
    company, job = _setup_job(db, make_user)

    # 1. Danh sách tin chờ duyệt
    list_res = client.get("/api/v1/admin/jobs?status=PENDING_APPROVAL", headers=admin_headers)
    assert list_res.status_code == 200
    assert any(j["id"] == job.id for j in list_res.json()["items"])

    # 2. Chi tiết tin tuyển dụng
    detail_res = client.get(f"/api/v1/admin/jobs/{job.id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Kỹ sư phần mềm Backend Python"

    # Tin không tồn tại -> 404
    assert client.get("/api/v1/admin/jobs/99999", headers=admin_headers).status_code == 404


def test_approve_job_with_background_parser(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)
    company, job = _setup_job(db, make_user)

    # Phê duyệt tin (sẽ chạy parse_job nền một cách an toàn)
    approve_res = client.post(f"/api/v1/admin/jobs/{job.id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200
    body = approve_res.json()
    assert body["status"] == JobStatus.APPROVED.value
    assert body["approved_by"] == admin.id
    assert body["approved_at"] is not None

    # Phê duyệt lại tin đã duyệt -> 409
    reapprove = client.post(f"/api/v1/admin/jobs/{job.id}/approve", headers=admin_headers)
    assert reapprove.status_code == 409


def test_reject_and_close_job(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)
    company, job = _setup_job(db, make_user)

    # 1. Từ chối duyệt tin
    reject_res = client.post(
        f"/api/v1/admin/jobs/{job.id}/reject",
        json={"reject_reason": "Tin tuyển dụng thiếu mô tả đãi ngộ cụ thể"},
        headers=admin_headers,
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == JobStatus.REJECTED.value
    assert reject_res.json()["reject_reason"] == "Tin tuyển dụng thiếu mô tả đãi ngộ cụ thể"

    # 2. Đóng tin vi phạm
    close_res = client.post(
        f"/api/v1/admin/jobs/{job.id}/close",
        json={"reason": "Tin có dấu hiệu lừa đảo"},
        headers=admin_headers,
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == JobStatus.CLOSED.value

    # Đóng lại tin đã đóng -> 409
    reclose = client.post(f"/api/v1/admin/jobs/{job.id}/close", headers=admin_headers)
    assert reclose.status_code == 409


def test_admin_jobs_forbidden_for_student(client, make_user, auth_headers):
    student = make_user(UserRole.STUDENT)
    res = client.get("/api/v1/admin/jobs", headers=auth_headers(student))
    assert res.status_code == 403


def test_approve_job_company_preconditions(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)

    job_type = JobType(code="INTERN_2", name="Thực tập 2")
    db.add(job_type)
    db.commit()

    # 1. Doanh nghiệp chưa được APPROVED -> 400
    u_pending = make_user(UserRole.COMPANY, UserStatus.PENDING_APPROVAL, email="u_pending@comp.vn")
    c_pending = Company(
        user_id=u_pending.id,
        name="Pending Comp",
        tax_code="0399111222",
        verification_status=VerificationStatus.PENDING,
    )
    db.add(c_pending)
    db.commit()

    job_pending = Job(
        company_id=c_pending.id,
        title="Intern Test 1",
        position="Intern",
        job_type_id=job_type.id,
        description="Mô tả công việc thực tập",
        deadline=date.today() + timedelta(days=30),
        status=JobStatus.PENDING_APPROVAL,
    )
    db.add(job_pending)
    db.commit()

    res1 = client.post(f"/api/v1/admin/jobs/{job_pending.id}/approve", headers=admin_headers)
    assert res1.status_code == 400
    assert "chưa được phê duyệt" in res1.json()["error"]["message"]

    # 2. Doanh nghiệp APPROVED nhưng user bị LOCKED -> 400
    u_locked = make_user(UserRole.COMPANY, UserStatus.LOCKED, email="u_locked@comp.vn")
    c_locked = Company(
        user_id=u_locked.id,
        name="Locked Comp",
        tax_code="0399111223",
        verification_status=VerificationStatus.APPROVED,
    )
    db.add(c_locked)
    db.commit()

    job_locked = Job(
        company_id=c_locked.id,
        title="Intern Test 2",
        position="Intern",
        job_type_id=job_type.id,
        description="Mô tả công việc thực tập 2",
        deadline=date.today() + timedelta(days=30),
        status=JobStatus.PENDING_APPROVAL,
    )
    db.add(job_locked)
    db.commit()

    res2 = client.post(f"/api/v1/admin/jobs/{job_locked.id}/approve", headers=admin_headers)
    assert res2.status_code == 400
    assert "khóa" in res2.json()["error"]["message"]


def test_reject_job_edge_cases(client, make_user, auth_headers, db):
    admin = make_user(UserRole.ADMIN)
    admin_headers = auth_headers(admin)

    job_type = JobType(code="PART_TIME", name="Bán thời gian")
    db.add(job_type)
    db.commit()

    u = make_user(UserRole.COMPANY, UserStatus.ACTIVE, email="u_rej@comp.vn")
    c = Company(
        user_id=u.id,
        name="Rej Comp",
        tax_code="0399111224",
        verification_status=VerificationStatus.APPROVED,
    )
    db.add(c)
    db.commit()

    # Tin đã bị từ chối
    j_rejected = Job(
        company_id=c.id,
        title="Part-time Rej",
        position="Dev",
        job_type_id=job_type.id,
        description="Mô tả bán thời gian rej",
        deadline=date.today() + timedelta(days=30),
        status=JobStatus.REJECTED,
    )
    db.add(j_rejected)

    # Tin CLOSED
    j_closed = Job(
        company_id=c.id,
        title="Part-time Closed",
        position="Dev",
        job_type_id=job_type.id,
        description="Mô tả bán thời gian closed",
        deadline=date.today() + timedelta(days=30),
        status=JobStatus.CLOSED,
    )
    db.add(j_closed)
    db.commit()

    # Reject tin đã bị từ chối -> 409
    res_rej = client.post(
        f"/api/v1/admin/jobs/{j_rejected.id}/reject",
        json={"reject_reason": "No"},
        headers=admin_headers,
    )
    assert res_rej.status_code == 409
    assert "từ chối trước đó" in res_rej.json()["error"]["message"]

    # Reject tin CLOSED -> 400
    res_closed = client.post(
        f"/api/v1/admin/jobs/{j_closed.id}/reject",
        json={"reject_reason": "No"},
        headers=admin_headers,
    )
    assert res_closed.status_code == 400
    assert "chờ duyệt" in res_closed.json()["error"]["message"]
