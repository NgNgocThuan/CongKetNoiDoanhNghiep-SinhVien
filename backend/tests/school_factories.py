"""Factories shared by school and analytics integration tests."""

from datetime import timedelta
from types import SimpleNamespace

from app.core.enums import CVType, JobStatus, UserRole, VerificationStatus
from app.models import (
    CV,
    Company,
    Faculty,
    Job,
    JobSkill,
    JobType,
    Major,
    Skill,
    Student,
    StudentProfile,
    StudentSkill,
)
from app.utils.datetime_utils import utcnow


def domain(db, make_user):
    admin = make_user(UserRole.ADMIN)
    student_user = make_user()
    company_user = make_user(UserRole.COMPANY)
    other_user = make_user(UserRole.COMPANY)
    faculty = Faculty(code="IT", name="Information Technology")
    db.add(faculty)
    db.flush()
    major = Major(code="CS", name="Computer Science", faculty_id=faculty.id)
    job_type = JobType(code="INTERN", name="Internship")
    skill = Skill(name="Python")
    db.add_all([major, job_type, skill])
    db.flush()
    student = Student(
        user_id=student_user.id,
        student_code="S001",
        full_name="Student One",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="K65",
        gpa=3.5,
        phone="0901234567",
    )
    company = Company(
        user_id=company_user.id,
        name="Company One",
        tax_code="TAX1",
        verification_status=VerificationStatus.APPROVED,
    )
    other_company = Company(user_id=other_user.id, name="Company Two", tax_code="TAX2")
    db.add_all([student, company, other_company])
    db.flush()
    profile = StudentProfile(
        student_id=student.id,
        is_open_to_work=True,
        show_gpa=False,
        show_contact=False,
        show_achievements=False,
        contact_email="private@test.com",
    )
    cv = CV(
        student_id=student.id,
        title="Online",
        type=CVType.ONLINE,
        content_json={"bio": "Python"},
        is_default=True,
    )
    job = Job(
        company_id=company.id,
        title="Python intern",
        position="Developer",
        job_type_id=job_type.id,
        description="Python backend",
        status=JobStatus.APPROVED,
        deadline=utcnow().date() + timedelta(days=30),
        min_gpa=2.0,
    )
    db.add_all([profile, cv, job])
    db.flush()
    db.add_all(
        [
            StudentSkill(student_id=student.id, skill_id=skill.id),
            JobSkill(job_id=job.id, skill_id=skill.id),
        ]
    )
    db.commit()
    return SimpleNamespace(**locals())
