"""API-level integration for project review, multiple students and atomic selection."""

from datetime import datetime, timedelta, timezone

import pytest

from app.core.enums import UserRole
from app.models import (
    Faculty,
    FreelanceContract,
    Major,
    ProjectContractBudget,
    Skill,
    Student,
)

B = "/api/v1"


@pytest.fixture
def people(db, make_user, auth_headers):
    owner = make_user(UserRole.CLIENT)
    owner.email_verified_at = datetime(2026, 1, 1)
    owner.escrow_terms_accepted_at = datetime(2026, 1, 1)
    owner.escrow_terms_version = "2026-11-12"
    admin = make_user(UserRole.ADMIN)
    outsider = make_user(UserRole.CLIENT)
    outsider.escrow_terms_accepted_at = datetime(2026, 1, 1)
    outsider.escrow_terms_version = "2026-11-12"
    faculty = Faculty(code="BTEST", name="School")
    db.add(faculty)
    db.add(Skill(id=880001, name="Project test skill"))
    db.flush()
    major = Major(code="BTEST", name="Major", faculty_id=faculty.id)
    db.add(major)
    db.flush()
    students = []
    for i in range(3):
        u = make_user(UserRole.STUDENT)
        s = Student(
            user_id=u.id,
            student_code=f"B{i}",
            full_name=f"Student {i}",
            faculty_id=faculty.id,
            major_id=major.id,
            cohort="2026",
        )
        db.add(s)
        db.flush()
        students.append((u, s))
    db.commit()
    return owner, admin, outsider, students


def payload(**kw):
    end = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=60)).isoformat()
    p = dict(
        title="Website",
        description="Build a portal",
        budget_amount="6000000",
        max_students=2,
        deadline=end,
        recruitment_deadline=end,
        category="DEVELOPMENT",
        skill_ids=[880001],
        acceptance_criteria="Review complete",
        deliverables_description="Sources",
        funding_policy="FULL",
        proposals=[dict(title="Build", amount="6000000", acceptance_criteria="Pass", due_at=end)],
    )
    p.update(kw)
    return p


def live(client, auth_headers, people):
    owner, admin, _, _ = people
    r = client.post(B + "/freelance-projects", headers=auth_headers(owner), json=payload())
    assert r.status_code == 201, r.text
    pid = r.json()["data"]["id"]
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/submit", headers=auth_headers(owner)
        ).status_code
        == 200
    )
    r = client.post(
        B + f"/admin/freelance-projects/{pid}/approve",
        headers=auth_headers(admin),
        json={"reason": "Approved scope"},
    )
    assert r.status_code == 200, r.text
    return pid


def test_project_search_filters_before_pagination_without_exposing_drafts(
    client, auth_headers, people
):
    owner, _, _, students = people
    live(client, auth_headers, people)
    response = client.post(
        B + "/freelance-projects", headers=auth_headers(owner), json=payload(title="Private design")
    )
    assert response.status_code == 201
    own = client.get(
        B + "/freelance-projects?mine=true&q=design&size=1", headers=auth_headers(owner)
    ).json()
    assert own["total"] == 1 and own["items"][0]["title"] == "Private design"
    public = client.get(
        B + "/freelance-projects?q=design&size=1", headers=auth_headers(students[0][0])
    ).json()
    assert public["total"] == 0
    match = client.get(
        B + "/freelance-projects?q=WEBSITE&size=1", headers=auth_headers(students[0][0])
    ).json()
    assert match["total"] == 1


def test_draft_visibility_and_contact_eligibility(client, db, auth_headers, people):
    owner, admin, other, students = people
    owner.phone_verified_at = None
    db.commit()
    r = client.post(B + "/freelance-projects", headers=auth_headers(owner), json=payload())
    assert r.status_code == 201, r.text
    pid = r.json()["data"]["id"]
    assert (
        client.get(B + f"/freelance-projects/{pid}", headers=auth_headers(other)).status_code == 404
    )
    owner.email_verified_at = None
    db.commit()
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/submit", headers=auth_headers(owner)
        ).status_code
        == 403
    )
    assert (
        client.post(
            B + "/freelance-projects", headers=auth_headers(students[0][0]), json=payload()
        ).status_code
        == 403
    )


def test_review_recruit_apply_select_two_and_replay(client, db, auth_headers, people):
    owner, admin, _, students = people
    pid = live(client, auth_headers, people)
    ids = []
    for _i, (u, _) in enumerate(students):
        r = client.post(
            B + f"/freelance-projects/{pid}/applications",
            headers=auth_headers(u),
            json={"proposal": "My scope", "quoted_amount": "2500000", "estimated_days": 15},
        )
        assert r.status_code == 201, r.text
        ids.append(r.json()["data"]["id"])
        own_read = client.get(B + f"/freelance-projects/{pid}", headers=auth_headers(u))
        assert own_read.json()["data"]["my_application"]["id"] == ids[-1]
        assert (
            "my_application"
            not in client.get(B + f"/freelance-projects/{pid}", headers=auth_headers(owner)).json()[
                "data"
            ]
        )
    h = {**auth_headers(owner), "Idempotency-Key": "select-1"}
    first = client.post(
        B + f"/freelance-projects/{pid}/select",
        headers=h,
        json={"application_id": ids[0], "allocated_amount": "2500000"},
    )
    assert first.status_code == 200, first.text
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/select",
            headers=h,
            json={"application_id": ids[0], "allocated_amount": "2500000"},
        ).json()
        == first.json()
    )
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/select",
            headers=h,
            json={"application_id": ids[0], "allocated_amount": "2000000"},
        ).status_code
        == 409
    )
    for i, expected in [(1, 200), (2, 409)]:
        r = client.post(
            B + f"/freelance-projects/{pid}/select",
            headers={**auth_headers(owner), "Idempotency-Key": f"select-{i + 1}"},
            json={"application_id": ids[i], "allocated_amount": "2500000"},
        )
        assert r.status_code == expected, r.text
    assert db.query(FreelanceContract).count() == 2 and db.query(ProjectContractBudget).count() == 2
    assert sum(x.allocated_amount for x in db.query(ProjectContractBudget)) == 5000000
    # Selecting one student never closes recruitment or grants access to the other contract.
    assert (
        client.get(B + f"/freelance-projects/{pid}", headers=auth_headers(owner)).json()["data"][
            "recruitment_status"
        ]
        == "OPEN"
    )
    contract = db.query(FreelanceContract).filter_by(freelancer_student_id=students[0][1].id).one()
    assert (
        client.get(
            B + f"/freelance-contracts/{contract.id}", headers=auth_headers(students[1][0])
        ).status_code
        == 404
    )


def test_invalid_budget_proposals_and_recruitment_close(client, auth_headers, people):
    owner, _, _, students = people
    bad = payload()
    bad["proposals"][0]["amount"] = "1"
    assert (
        client.post(B + "/freelance-projects", headers=auth_headers(owner), json=bad).status_code
        == 400
    )
    pid = live(client, auth_headers, people)
    discovery_url = B + "/freelance-projects?page=1&size=100"
    visible_ids = {
        row["id"]
        for row in client.get(
            discovery_url, headers=auth_headers(students[0][0])
        ).json()["items"]
    }
    assert str(pid) in visible_ids
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/close-recruitment", headers=auth_headers(owner)
        ).status_code
        == 200
    )
    hidden_ids = {
        row["id"]
        for row in client.get(
            discovery_url, headers=auth_headers(students[0][0])
        ).json()["items"]
    }
    assert str(pid) not in hidden_ids
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/applications",
            headers=auth_headers(students[0][0]),
            json={"proposal": "Work", "quoted_amount": "1", "estimated_days": 1},
        ).status_code
        == 409
    )
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/reopen-recruitment", headers=auth_headers(owner)
        ).status_code
        == 200
    )
    reopened_ids = {
        row["id"]
        for row in client.get(
            discovery_url, headers=auth_headers(students[0][0])
        ).json()["items"]
    }
    assert str(pid) in reopened_ids


def test_withdraw_is_permanent_and_privacy_isolated(client, auth_headers, people):
    owner, _, other, students = people
    pid = live(client, auth_headers, people)
    u = students[0][0]
    data = {"proposal": "Work", "quoted_amount": "1000000", "estimated_days": 5}
    aid = client.post(
        B + f"/freelance-projects/{pid}/applications", headers=auth_headers(u), json=data
    ).json()["data"]["id"]
    assert (
        client.get(
            B + f"/freelance-projects/{pid}/applications", headers=auth_headers(other)
        ).status_code
        == 404
    )
    assert (
        client.post(
            B + f"/freelance-applications/{aid}/withdraw", headers=auth_headers(students[1][0])
        ).status_code
        == 404
    )
    assert (
        client.post(
            B + f"/freelance-applications/{aid}/withdraw", headers=auth_headers(u)
        ).status_code
        == 200
    )
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/applications", headers=auth_headers(u), json=data
        ).status_code
        == 409
    )


def test_expansion_requires_admin_approval(client, auth_headers, people):
    owner, admin, _, _ = people
    pid = live(client, auth_headers, people)
    r = client.post(
        B + f"/freelance-projects/{pid}/expansions",
        headers={**auth_headers(owner), "Idempotency-Key": "expand"},
        json={"budget_amount": "8000000", "max_students": 3, "reason": "More scope"},
    )
    assert r.status_code == 201, r.text
    assert (
        client.get(B + f"/freelance-projects/{pid}", headers=auth_headers(owner)).json()["data"][
            "budget_amount"
        ]
        == "6000000"
    )
    r = client.post(
        B + f"/admin/freelance-projects/{pid}/expansions/expand/approve",
        headers=auth_headers(admin),
        json={"reason": "Approved increase"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["budget_amount"] == "8000000"


def test_minimal_draft_can_be_completed_without_proposed_milestones(client, auth_headers, people):
    owner, admin, _, _ = people
    headers = auth_headers(owner)
    response = client.post(B + "/freelance-projects", headers=headers, json={"title": "Draft idea"})
    assert response.status_code == 201, response.text
    draft = response.json()["data"]
    pid = draft["id"]
    assert draft["budget_amount"] is None and draft["deadline"] is None
    assert draft["proposals"] == []
    rejected = client.post(B + f"/freelance-projects/{pid}/submit", headers=headers)
    assert rejected.status_code == 400 and "PROJECT_INCOMPLETE" in rejected.text
    complete = payload(proposals=[], experience_level="ENTRY")
    assert (
        client.patch(B + f"/freelance-projects/{pid}", headers=headers, json=complete).status_code
        == 200
    )
    assert client.post(B + f"/freelance-projects/{pid}/submit", headers=headers).status_code == 200
    approved = client.post(
        B + f"/admin/freelance-projects/{pid}/approve",
        headers=auth_headers(admin),
        json={"reason": "Complete brief"},
    )
    assert approved.status_code == 200, approved.text


def test_submission_requires_skills_and_recruitment_dates_are_independent(
    client, db, auth_headers, people
):
    from app.models import FreelanceProject

    owner, _, _, students = people
    headers = auth_headers(owner)
    incomplete = payload(proposals=[], skill_ids=[])
    response = client.post(B + "/freelance-projects", headers=headers, json=incomplete)
    pid = response.json()["data"]["id"]
    assert client.post(B + f"/freelance-projects/{pid}/submit", headers=headers).status_code == 400
    invalid = payload(
        recruitment_deadline=(datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    )
    assert (
        client.patch(B + f"/freelance-projects/{pid}", headers=headers, json=invalid).status_code
        == 400
    )
    pid = live(client, auth_headers, people)
    project = db.get(FreelanceProject, int(pid))
    project.recruitment_deadline = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        seconds=1
    )
    db.commit()
    response = client.post(
        B + f"/freelance-projects/{pid}/applications",
        headers=auth_headers(students[0][0]),
        json={"proposal": "Work", "quoted_amount": "1000000", "estimated_days": 3},
    )
    assert response.status_code == 409 and "Recruitment deadline" in response.text
    assert (
        client.get(B + "/freelance-projects?category=DESIGN", headers=headers).json()["total"] == 0
    )
    assert (
        client.get(B + "/freelance-projects?category=DEVELOPMENT", headers=headers).json()["total"]
        == 1
    )


def test_reference_files_require_ownership_clean_scan_and_post_visibility(
    client, db, auth_headers, people, tmp_path, monkeypatch
):
    from app.core.config import settings
    from app.models import FreelanceProject, StoredFile

    owner, admin, other, students = people
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    other.email_verified_at = datetime(2026, 1, 1)
    import hashlib
    (tmp_path / "brief.pdf").write_bytes(b"%PDF-test-brief")
    file = StoredFile(
        uploaded_by=owner.id,
        storage_key="brief.pdf",
        original_name="brief.pdf",
        content_type="application/pdf",
        size_bytes=len(b"%PDF-test-brief"),
        checksum_sha256=hashlib.sha256(b"%PDF-test-brief").hexdigest(),
        category="PROJECT_REFERENCE",
        scan_status="PENDING",
        availability_status="AVAILABLE",
    )
    db.add(file)
    db.commit()
    body = payload(attachment_file_ids=[file.id])
    response = client.post(B + "/freelance-projects", headers=auth_headers(owner), json=body)
    assert response.status_code == 409
    file.scan_status = "CLEAN"
    db.commit()
    assert (
        client.post(B + "/freelance-projects", headers=auth_headers(other), json=body).status_code
        == 404
    )
    created = client.post(B + "/freelance-projects", headers=auth_headers(owner), json=body)
    assert created.status_code == 201, created.text
    pid = created.json()["data"]["id"]
    download = B + f"/files/{file.id}/download"
    student_headers = auth_headers(students[0][0])
    assert client.get(download, headers=student_headers).status_code == 404
    assert (
        client.post(
            B + f"/freelance-projects/{pid}/submit", headers=auth_headers(owner)
        ).status_code
        == 200
    )
    assert (
        client.post(
            B + f"/admin/freelance-projects/{pid}/approve",
            headers=auth_headers(admin),
            json={"reason": "Safe reference"},
        ).status_code
        == 200
    )
    assert client.get(download, headers=student_headers).status_code == 200
    file.scan_status = "REJECTED"
    db.commit()
    assert client.get(download, headers=student_headers).status_code == 409
    file.scan_status = "CLEAN"
    project = db.get(FreelanceProject, int(pid))
    project.status = "CANCELLED"
    db.commit()
    assert client.get(download, headers=student_headers).status_code == 404
