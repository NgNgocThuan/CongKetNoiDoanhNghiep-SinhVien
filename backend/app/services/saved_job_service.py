"""Business rules for saving and unsaving jobs."""
import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import JobStatus
from app.core.exceptions import NotFoundError
from app.models import Job, SavedJob, Student
from app.schemas.common import PageParams
from app.utils.datetime_utils import today


def _payload(saved: SavedJob, job: Job) -> dict:
    return {"saved_at": saved.saved_at, "job": job}


def list_saved_jobs(db: Session, student: Student, params: PageParams) -> dict:
    condition = SavedJob.student_id == student.id
    total = db.scalar(select(func.count()).select_from(SavedJob).where(condition)) or 0
    stmt = (
        select(SavedJob, Job)
        .join(Job, Job.id == SavedJob.job_id)
        .where(condition)
        .options(joinedload(Job.company), joinedload(Job.job_type))
        .order_by(SavedJob.saved_at.desc(), SavedJob.job_id.desc())
        .offset(params.offset)
        .limit(params.size)
    )
    rows = db.execute(stmt).all()
    return {
        "items": [_payload(saved, job) for saved, job in rows],
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": math.ceil(total / params.size) if total else 0,
    }


def save_job(db: Session, student: Student, job_id: int) -> dict:
    existing = db.get(SavedJob, (student.id, job_id))
    if existing is not None:
        job = db.scalar(
            select(Job)
            .where(Job.id == job_id)
            .options(joinedload(Job.company), joinedload(Job.job_type))
        )
        return _payload(existing, job)

    job = db.scalar(
        select(Job)
        .where(
            Job.id == job_id,
            Job.status == JobStatus.APPROVED,
            Job.deadline >= today(),
        )
        .options(joinedload(Job.company), joinedload(Job.job_type))
    )
    if job is None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng đang hiển thị")
    saved = SavedJob(student_id=student.id, job_id=job.id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return _payload(saved, job)


def unsave_job(db: Session, student: Student, job_id: int) -> None:
    saved = db.get(SavedJob, (student.id, job_id))
    if saved is not None:
        db.delete(saved)
        db.commit()
