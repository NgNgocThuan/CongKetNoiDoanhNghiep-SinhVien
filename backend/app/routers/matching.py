from fastapi import APIRouter, BackgroundTasks

from app.dependencies import AdminUser, CurrentCompany, CurrentStudent, DbSession, Pagination
from app.schemas.common import Message, Page
from app.schemas.matching import CandidateRecommendation, JobRecommendation, MatchResult
from app.services import matching_service as service

router = APIRouter(prefix="/matching", tags=["AI Matching"])


@router.get(
    "/jobs/recommended", response_model=Page[JobRecommendation], summary="Gợi ý việc làm phù hợp"
)
def recommend_jobs(db: DbSession, student: CurrentStudent, pagination: Pagination):
    return service.recommend_jobs_for_student(db, student, pagination)


@router.get(
    "/jobs/{job_id}/score", response_model=MatchResult, summary="Điểm phù hợp với tin tuyển dụng"
)
def score(job_id: int, db: DbSession, student: CurrentStudent):
    return service.score_for_student(db, student, job_id)


@router.get(
    "/jobs/{job_id}/candidates",
    response_model=Page[CandidateRecommendation],
    summary="Gợi ý ứng viên có bảo vệ quyền riêng tư",
)
def recommend_candidates(
    job_id: int, db: DbSession, company: CurrentCompany, pagination: Pagination
):
    return service.recommend_candidates_for_job(db, company, job_id, pagination)


@router.post(
    "/recompute", response_model=Message, status_code=202, summary="Tính lại matching ở nền"
)
def recompute(_: AdminUser, background_tasks: BackgroundTasks):
    background_tasks.add_task(service.recompute_in_background)
    return {"message": "Đã xếp hàng tính lại matching"}
