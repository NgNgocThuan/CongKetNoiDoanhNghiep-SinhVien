from app.core.config import settings
from app.models import JobSkill, Skill, StudentSkill
from app.services import matching_service
from tests.school_factories import domain


def test_confirm_cv_skills_controls_matching_without_overwriting_existing_skills(client, db, make_user, auth_headers, monkeypatch):
    d = domain(db, make_user)
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    monkeypatch.setattr(matching_service.cv_parser, "parse_cv", lambda db, cv: cv.parsed_json)
    react, sql = Skill(name="React"), Skill(name="SQL")
    db.add_all([react, sql])
    db.flush()
    db.add(JobSkill(job_id=d.job.id, skill_id=react.id, is_required=True))
    original = db.get(StudentSkill, (d.student.id, d.skill.id))
    original.level = "ADVANCED"
    d.cv.parsed_json = {"skills": ["React", "SQL"]}
    db.commit()
    headers = auth_headers(d.student_user)
    score_url = f"/api/v1/matching/jobs/{d.job.id}/score"
    before = client.get(score_url, headers=headers).json()
    assert before["matched_skills"] == ["Python"]
    assert "React" in before["missing_skills"]
    url = f"/api/v1/cvs/{d.cv.id}/confirm-skills"
    assert client.post(url, headers=auth_headers(d.company_user), json={"skills": ["React"]}).status_code == 403
    assert client.post(url, headers=headers, json={"skills": ["Not in the CV"]}).status_code == 400
    response = client.post(url, headers=headers, json={"skills": ["React"]})
    assert response.status_code == 200, response.text
    assert response.json()["added_skills"] == ["React"]
    assert db.get(StudentSkill, (d.student.id, sql.id)) is None
    db.refresh(original)
    assert original.level == "ADVANCED"
    after = client.get(score_url, headers=headers).json()
    assert set(after["matched_skills"]) == {"Python", "React"}
    assert float(after["score"]) > float(before["score"])
    listed = client.get("/api/v1/cvs/me", headers=headers).json()
    assert set(listed[0]["content_json"]["skills"]) == {"Python", "React"}
    # Skill edits propagate to active online CVs but not immutable application snapshots.
    assert client.delete(f"/api/v1/students/me/skills/{react.id}", headers=headers).status_code == 204
    db.refresh(d.cv)
    assert d.cv.content_json["skills"] == ["Python"]


def test_cannot_confirm_someone_elses_or_deleted_cv(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    from app.core.enums import UserRole
    other_student = make_user(UserRole.STUDENT)
    # Ownership service also validates the student profile via CurrentStudent.
    assert client.post(f"/api/v1/cvs/{d.cv.id}/confirm-skills", headers=auth_headers(other_student), json={"skills": ["Python"]}).status_code in (403, 404)
    from app.utils.datetime_utils import utcnow
    d.cv.deleted_at = utcnow()
    db.commit()
    assert client.post(f"/api/v1/cvs/{d.cv.id}/confirm-skills", headers=auth_headers(d.student_user), json={"skills": ["Python"]}).status_code == 404


def test_online_cv_uses_profile_skills_instead_of_free_text(client, db, make_user, auth_headers):
    d = domain(db, make_user)
    response = client.post("/api/v1/cvs/online", headers=auth_headers(d.student_user), json={"title": "New CV", "content_json": {"skills": ["Unconfirmed"], "summary": "My profile"}})
    assert response.status_code == 201, response.text
    assert response.json()["content_json"]["skills"] == ["Python"]
