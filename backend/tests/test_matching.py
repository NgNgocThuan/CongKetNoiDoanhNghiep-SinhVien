from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.core.config import settings
from app.core.enums import JobStatus
from app.services import matching_service as service
from tests.school_factories import domain

BASE = "/api/v1/matching"


def test_matching_cache_and_invalidations(client, db, make_user, auth_headers, monkeypatch):
    d = domain(db, make_user)
    monkeypatch.setattr(settings, "AI_API_KEY", "test-only")
    cv_llm = Mock(
        return_value={
            "skills": ["Python"],
            "experience_months": 0,
            "projects": [],
            "domains": [],
            "keywords": ["python"],
        }
    )
    job_llm = Mock(
        return_value={
            "required_skills": ["Python"],
            "preferred_skills": [],
            "min_experience_months": 0,
            "education": None,
            "domains": [],
            "keywords": ["python"],
        }
    )
    monkeypatch.setattr(
        service.cv_parser, "get_llm_client", lambda **kw: SimpleNamespace(complete_json=cv_llm)
    )
    monkeypatch.setattr(
        service.job_parser, "get_llm_client", lambda **kw: SimpleNamespace(complete_json=job_llm)
    )
    headers = auth_headers(d.student_user)
    first = client.get(f"{BASE}/jobs/{d.job.id}/score", headers=headers)
    assert first.status_code == 200, first.text
    assert float(first.json()["score"]) == 100
    second = client.get(f"{BASE}/jobs/{d.job.id}/score", headers=headers)
    assert second.json()["computed_at"] == first.json()["computed_at"]
    assert cv_llm.call_count == job_llm.call_count == 1
    d.student.gpa = 1
    db.commit()
    third = client.get(f"{BASE}/jobs/{d.job.id}/score", headers=headers)
    assert third.json()["passed_rules"] is False
    assert float(third.json()["score"]) == 0
    assert cv_llm.call_count == job_llm.call_count == 1
    d.student.gpa = 3.5
    d.job.min_gpa = 4
    db.commit()
    assert client.get(f"{BASE}/jobs/recommended", headers=headers).json()["total"] == 0


def test_candidate_privacy_and_ownership(client, db, make_user, auth_headers, monkeypatch):
    from app.core.enums import AchievementType
    from app.models import StudentAchievement

    d = domain(db, make_user)
    db.add(
        StudentAchievement(
            student_id=d.student.id, type=AchievementType.RESEARCH, title="Private paper"
        )
    )
    db.commit()
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    url = f"{BASE}/jobs/{d.job.id}/candidates"
    company = auth_headers(d.company_user)
    assert client.get(url, headers=auth_headers(d.other_user)).status_code == 404
    assert client.get(url, headers=auth_headers(d.student_user)).status_code == 403
    result = client.get(url, headers=company)
    assert result.status_code == 200, result.text
    item = result.json()["items"][0]
    assert item["gpa"] is None and item["contact_email"] is None and item["contact_phone"] is None
    assert item["achievements"] == []
    assert "private@test.com" not in result.text and "0901234567" not in result.text
    d.profile.show_contact = True
    d.profile.show_gpa = True
    d.profile.show_achievements = True
    db.commit()
    item = client.get(url, headers=company).json()["items"][0]
    assert item["contact_email"] == "private@test.com" and float(item["gpa"]) == 3.5
    assert item["achievements"][0]["title"] == "Private paper"
    d.profile.is_open_to_work = False
    db.commit()
    assert client.get(url, headers=company).json()["total"] == 0
    # New eligibility is checked even when a cached match exists.
    d.job.deadline -= timedelta(days=100)
    db.commit()
    assert (
        client.get(
            f"{BASE}/jobs/{d.job.id}/score", headers=auth_headers(d.student_user)
        ).status_code
        == 404
    )


def test_matching_recommendations_and_background(client, db, make_user, auth_headers, monkeypatch):
    d = domain(db, make_user)
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    response = client.get(f"{BASE}/jobs/recommended?size=1", headers=auth_headers(d.student_user))
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert (
        client.get(f"{BASE}/jobs/recommended", headers=auth_headers(d.company_user)).status_code
        == 403
    )
    assert (
        client.get(
            f"{BASE}/jobs/{d.job.id}/score", headers=auth_headers(d.company_user)
        ).status_code
        == 403
    )
    task = Mock()
    monkeypatch.setattr(service, "recompute_in_background", task)
    assert client.post(f"{BASE}/recompute", headers=auth_headers(d.admin)).status_code == 202
    task.assert_called_once()
    assert client.post(f"{BASE}/recompute", headers=auth_headers(d.student_user)).status_code == 403
    d.job.status = JobStatus.CLOSED
    db.commit()
    assert (
        client.get(f"{BASE}/jobs/recommended", headers=auth_headers(d.student_user)).json()["total"]
        == 0
    )


def test_matching_term_visibility(client, db, make_user, auth_headers, monkeypatch):
    from app.models import InternshipTerm, TermStudent
    from app.utils.datetime_utils import utcnow

    d = domain(db, make_user)
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    term = InternshipTerm(
        name="Private term",
        semester="1",
        academic_year="2026",
        start_date=utcnow().date(),
        end_date=utcnow().date(),
        created_by=d.admin.id,
    )
    db.add(term)
    db.flush()
    d.job.term_id = term.id
    db.commit()
    student_headers = auth_headers(d.student_user)
    assert client.get(f"{BASE}/jobs/{d.job.id}/score", headers=student_headers).status_code == 404
    assert client.get(f"{BASE}/jobs/recommended", headers=student_headers).json()["total"] == 0
    db.add(TermStudent(term_id=term.id, student_id=d.student.id))
    db.commit()
    assert client.get(f"{BASE}/jobs/{d.job.id}/score", headers=student_headers).status_code == 200


def test_failed_hard_rules_do_not_call_ai(db, make_user, monkeypatch):
    d = domain(db, make_user)
    d.student.gpa = 0
    db.commit()
    monkeypatch.setattr(settings, "AI_API_KEY", "test")
    cv_parse, job_parse = Mock(), Mock()
    monkeypatch.setattr(service.cv_parser, "parse_cv", cv_parse)
    monkeypatch.setattr(service.job_parser, "parse_job", job_parse)
    assert not service.get_or_compute_match(db, d.student, d.job).passed_rules
    cv_parse.assert_not_called()
    job_parse.assert_not_called()
