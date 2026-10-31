"""Idempotent local demo fixtures; run only via start-local.ps1 against its isolated DB."""

from datetime import timedelta

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.core.enums import CVType, JobStatus, TermStatus
from app.models import (
    CV,
    Base,
    Company,
    InternshipTerm,
    Job,
    JobSkill,
    JobType,
    Skill,
    Student,
    StudentSkill,
    TermStudent,
    User,
)
from app.utils.datetime_utils import today
from scripts.seed import seed

Base.metadata.create_all(engine)
with SessionLocal() as db:
    seed(db)
    student = db.scalar(select(Student))
    company = db.scalar(select(Company).where(Company.tax_code == "0123456789"))
    admin = db.scalar(select(User).where(User.email == "admin@school.edu.vn"))
    term = db.scalar(select(InternshipTerm).where(InternshipTerm.name == "Đợt thực tập demo local"))
    if term is None:
        term = InternshipTerm(
            name="Đợt thực tập demo local",
            semester="HK1",
            academic_year="2026-2027",
            start_date=today(),
            end_date=today() + timedelta(days=90),
            status=TermStatus.ONGOING,
            created_by=admin.id,
        )
        db.add(term)
        db.flush()
    if not db.scalar(
        select(TermStudent).where(
            TermStudent.term_id == term.id, TermStudent.student_id == student.id
        )
    ):
        db.add(TermStudent(term_id=term.id, student_id=student.id))
    job_type = db.scalar(select(JobType).where(JobType.code == "INTERN"))
    for title, position, skill_names in [
        ("Thực tập sinh Backend Python", "Backend Developer", ["Python", "FastAPI"]),
        ("Thực tập sinh Frontend React", "Frontend Developer", ["React", "TypeScript"]),
    ]:
        job = db.scalar(select(Job).where(Job.company_id == company.id, Job.title == title))
        if job is None:
            job = Job(
                company_id=company.id,
                title=title,
                position=position,
                job_type_id=job_type.id,
                description="Tham gia phát triển sản phẩm cùng đội ngũ kỹ thuật.",
                requirements="Kỹ năng phù hợp với vị trí.",
                status=JobStatus.APPROVED,
                deadline=today() + timedelta(days=60),
                location="Hà Nội",
                quantity=3,
                salary_min=3000000,
                salary_max=6000000,
            )
            db.add(job)
            db.flush()
            for name in skill_names:
                skill = db.scalar(select(Skill).where(Skill.name == name))
                db.add(JobSkill(job_id=job.id, skill_id=skill.id, is_required=True))
    for name in ["Python", "FastAPI", "React"]:
        skill = db.scalar(select(Skill).where(Skill.name == name))
        if not db.scalar(
            select(StudentSkill).where(
                StudentSkill.student_id == student.id, StudentSkill.skill_id == skill.id
            )
        ):
            db.add(StudentSkill(student_id=student.id, skill_id=skill.id))
    if not db.scalar(select(CV).where(CV.student_id == student.id, CV.deleted_at.is_(None))):
        db.add(
            CV(
                student_id=student.id,
                title="CV demo local",
                type=CVType.ONLINE,
                is_default=True,
                content_json={
                    "bio": "Sinh viên đang tìm cơ hội thực tập",
                    "skills": ["Python", "FastAPI", "React"],
                },
            )
        )
    db.commit()
print("Local demo database ready.")
