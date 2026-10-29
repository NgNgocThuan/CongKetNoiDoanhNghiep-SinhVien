"""Saved-job endpoints."""
from fastapi import APIRouter, Response

from app.dependencies import CurrentStudent, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.saved_jobs import SavedJobRead
from app.services import saved_job_service

router = APIRouter(prefix="/saved-jobs", tags=["Saved Jobs"])


@router.get("", response_model=Page[SavedJobRead], summary="Danh sách việc làm đã lưu")
def list_saved_jobs(db: DbSession, student: CurrentStudent, pagination: Pagination):
    return saved_job_service.list_saved_jobs(db, student, pagination)


@router.post(
    "/{job_id}", response_model=SavedJobRead, status_code=201, summary="Lưu việc làm"
)
def save_job(job_id: int, db: DbSession, student: CurrentStudent):
    return saved_job_service.save_job(db, student, job_id)


@router.delete("/{job_id}", status_code=204, summary="Bỏ lưu việc làm")
def unsave_job(job_id: int, db: DbSession, student: CurrentStudent):
    saved_job_service.unsave_job(db, student, job_id)
    return Response(status_code=204)
