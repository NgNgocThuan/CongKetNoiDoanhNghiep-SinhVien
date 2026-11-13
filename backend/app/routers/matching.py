from fastapi import APIRouter, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

from app.dependencies import AdminUser, CurrentCompany, CurrentStudent, DbSession, Pagination
from app.schemas.common import Message, Page
from app.schemas.matching import CandidateRecommendation, JobRecommendation, MatchResult
from app.services import matching_service as service

router = APIRouter(prefix="/matching", tags=["AI Matching"])


@router.get("/jobs/{job_id}/candidates/{student_id}/profile", summary="Hồ sơ nghề nghiệp của ứng viên được gợi ý")
def candidate_profile(job_id: int, student_id: int, db: DbSession, company: CurrentCompany):
    data, _ = service.candidate_profile(db, company, job_id, student_id)
    return data


@router.get("/jobs/{job_id}/candidates/{student_id}/cv", summary="Xem CV ứng viên cho phép chia sẻ trước lời mời")
def candidate_cv(job_id: int, student_id: int, db: DbSession, company: CurrentCompany):
    from pathlib import Path

    from app.core.config import settings
    from app.core.exceptions import NotFoundError
    from app.utils.file_storage import absolute_path

    data, cv = service.candidate_profile(db, company, job_id, student_id)
    if cv is None:
        raise NotFoundError("Sinh viên chưa có CV khả dụng")
    if cv.type == "ONLINE":
        content = dict(cv.content_json or {})
        content["skills"] = [item["name"] for item in data["skills"]]
        content["official"] = {key: data[key] for key in ("full_name", "major_name", "cohort", "gpa")}
        return JSONResponse(jsonable_encoder({"title": cv.title, "content": content}), headers={"Cache-Control": "no-store"})
    path = absolute_path(cv.file_url or "").resolve()
    if not path.is_relative_to(Path(settings.UPLOAD_DIR).resolve()) or not path.is_file() or path.suffix.lower() not in {".pdf", ".docx"}:
        raise NotFoundError("Tệp CV không còn khả dụng")
    pdf = path.suffix.lower() == ".pdf"
    return FileResponse(path, media_type="application/pdf" if pdf else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        filename=f"cv-{student_id}{path.suffix.lower()}", content_disposition_type="inline" if pdf else "attachment",
                        headers={"Cache-Control": "private, no-store"})


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
