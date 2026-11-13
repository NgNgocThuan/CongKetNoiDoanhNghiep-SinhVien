from sqlalchemy import func, select

from app.models import Company, Job, JobSkill, User
from scripts.prepare_defense_jobs import prepare


def test_complete_recruitment_dataset_preserves_status_and_ids(db):
    assert prepare(db) == 12
    jobs = db.scalars(select(Job).order_by(Job.id)).all()
    ids = [job.id for job in jobs]
    assert db.scalar(select(func.count(Company.id))) == 4
    for job in jobs:
        assert not job.title.startswith("[DEMO]")
        assert job.position and job.industry_id and job.job_type_id
        assert len(job.description) > 300
        assert len(job.requirements) > 150
        assert len(job.benefits) > 200
        assert 0 < job.salary_min <= job.salary_max
        assert job.quantity > 0 and job.location
        assert job.min_experience_months == 0
        assert db.scalar(select(func.count(JobSkill.skill_id)).where(JobSkill.job_id == job.id, JobSkill.is_required.is_(True))) >= 2
        company = db.get(Company, job.company_id)
        account = db.get(User, company.user_id)
        assert account.role == "COMPANY" and account.email_verified_at
        assert company.business_status == "VERIFIED"
    original_deadline = jobs[0].deadline
    jobs[0].status = "CLOSED"
    db.commit()
    prepare(db)
    assert [job.id for job in db.scalars(select(Job).order_by(Job.id))] == ids
    db.refresh(jobs[0])
    assert jobs[0].status == "CLOSED"
    assert jobs[0].deadline == original_deadline
