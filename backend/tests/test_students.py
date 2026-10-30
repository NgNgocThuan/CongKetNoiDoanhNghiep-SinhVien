from app.core.enums import CertificateSource, SkillSource, UserRole
from app.models import (
    Faculty,
    Major,
    Skill,
    Student,
    StudentCertificate,
    StudentProfile,
)

BASE = "/api/v1/students/me"


def make_student(db, make_user, *, code="SV001"):
    user = make_user(UserRole.STUDENT, email=f"{code.lower()}@test.com")
    faculty = Faculty(code=f"F-{code}", name=f"Faculty {code}")
    db.add(faculty)
    db.flush()
    major = Major(faculty_id=faculty.id, code=f"M-{code}", name=f"Major {code}")
    db.add(major)
    db.flush()
    student = Student(
        user_id=user.id,
        student_code=code,
        full_name=f"Student {code}",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="K65",
        gpa=3.4,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return user, student


def test_profile_separates_official_and_self_declared(client, db, make_user, auth_headers):
    user, student = make_student(db, make_user)
    db.add(StudentProfile(student_id=student.id, bio="Backend developer"))
    db.add(
        StudentCertificate(
            student_id=student.id,
            name="School certificate",
            source=CertificateSource.SCHOOL,
            is_verified=True,
        )
    )
    db.add(
        StudentCertificate(
            student_id=student.id,
            name="Self certificate",
            source=CertificateSource.SELF,
            is_verified=False,
        )
    )
    db.commit()

    response = client.get(BASE, headers=auth_headers(user))
    assert response.status_code == 200
    body = response.json()
    assert body["official"]["student_code"] == "SV001"
    assert [item["name"] for item in body["official"]["certificates"]] == [
        "School certificate"
    ]
    assert [item["name"] for item in body["self_declared"]["certificates"]] == [
        "Self certificate"
    ]
    assert body["self_declared"]["profile"]["bio"] == "Backend developer"


def test_update_privacy_and_crud_self_data(client, db, make_user, auth_headers):
    user, student = make_student(db, make_user)
    skill = Skill(name="Python")
    db.add(skill)
    db.commit()
    headers = auth_headers(user)

    profile = client.put(
        f"{BASE}/profile",
        json={
            "bio": "API engineer",
            "contact_email": "student@example.com",
            "is_open_to_work": True,
            "show_contact": True,
        },
        headers=headers,
    )
    assert profile.status_code == 200
    assert profile.json()["is_open_to_work"] is True

    created_skill = client.post(
        f"{BASE}/skills",
        json={"skill_id": skill.id, "level": "INTERMEDIATE"},
        headers=headers,
    )
    assert created_skill.status_code == 201
    assert created_skill.json()["source"] == SkillSource.SELF.value
    duplicate = client.post(
        f"{BASE}/skills", json={"skill_id": skill.id}, headers=headers
    )
    assert duplicate.status_code == 409
    updated_skill = client.put(
        f"{BASE}/skills/{skill.id}", json={"level": "ADVANCED"}, headers=headers
    )
    assert updated_skill.json()["level"] == "ADVANCED"

    experience = client.post(
        f"{BASE}/experiences",
        json={"company_name": "Acme", "position": "Intern", "start_date": "2026-01-01"},
        headers=headers,
    )
    assert experience.status_code == 201
    exp_id = experience.json()["id"]
    assert client.put(
        f"{BASE}/experiences/{exp_id}",
        json={"position": "Backend Intern"},
        headers=headers,
    ).json()["position"] == "Backend Intern"

    project = client.post(
        f"{BASE}/projects", json={"name": "Student Connect"}, headers=headers
    )
    assert project.status_code == 201
    certificate = client.post(
        f"{BASE}/certificates", json={"name": "AWS Cloud"}, headers=headers
    )
    assert certificate.status_code == 201
    assert certificate.json()["is_verified"] is False

    assert client.delete(f"{BASE}/skills/{skill.id}", headers=headers).status_code == 204
    assert client.delete(f"{BASE}/experiences/{exp_id}", headers=headers).status_code == 204
    assert client.delete(
        f"{BASE}/projects/{project.json()['id']}", headers=headers
    ).status_code == 204


def test_cannot_modify_school_certificate_or_another_students_data(
    client, db, make_user, auth_headers
):
    user, student = make_student(db, make_user, code="SV001")
    _, other = make_student(db, make_user, code="SV002")
    school_certificate = StudentCertificate(
        student_id=student.id,
        name="Official",
        source=CertificateSource.SCHOOL,
        is_verified=True,
    )
    other_certificate = StudentCertificate(
        student_id=other.id,
        name="Other private cert",
        source=CertificateSource.SELF,
        is_verified=False,
    )
    db.add_all([school_certificate, other_certificate])
    db.commit()
    headers = auth_headers(user)

    assert client.put(
        f"{BASE}/certificates/{school_certificate.id}",
        json={"name": "Changed"},
        headers=headers,
    ).status_code == 404
    assert client.delete(
        f"{BASE}/certificates/{school_certificate.id}", headers=headers
    ).status_code == 404
    assert client.delete(
        f"{BASE}/certificates/{other_certificate.id}", headers=headers
    ).status_code == 404


def test_non_student_cannot_access_student_profile(client, make_user, auth_headers):
    company_user = make_user(UserRole.COMPANY)
    assert client.get(BASE, headers=auth_headers(company_user)).status_code == 403
