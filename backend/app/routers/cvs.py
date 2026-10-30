"""CV endpoints."""
from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile
from fastapi.responses import FileResponse

from app.dependencies import CurrentStudent, CurrentUser, DbSession
from app.schemas.cvs import CVAnalysisRead, CVOnlineCreate, CVRead, CVUpdate
from app.services import cv_service

router = APIRouter(prefix="/cvs", tags=["CVs"])


@router.get("/me", response_model=list[CVRead], summary="Danh sách CV của tôi")
def list_my_cvs(db: DbSession, student: CurrentStudent):
    return cv_service.list_my_cvs(db, student)


@router.post("/upload", response_model=CVRead, status_code=201, summary="Tải CV PDF hoặc DOCX")
def upload_cv(
    db: DbSession,
    student: CurrentStudent,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    file: Annotated[UploadFile, File()],
):
    return cv_service.upload_cv(db, student, title, file)


@router.post("/online", response_model=CVRead, status_code=201, summary="Tạo CV trực tuyến")
def create_online_cv(data: CVOnlineCreate, db: DbSession, student: CurrentStudent):
    return cv_service.create_online_cv(db, student, data)


@router.put("/{cv_id}", response_model=CVRead, summary="Cập nhật CV")
def update_cv(cv_id: int, data: CVUpdate, db: DbSession, student: CurrentStudent):
    return cv_service.update_cv(db, student, cv_id, data)


@router.delete("/{cv_id}", status_code=204, summary="Xóa mềm CV")
def delete_cv(cv_id: int, db: DbSession, student: CurrentStudent):
    cv_service.soft_delete_cv(db, student, cv_id)
    return Response(status_code=204)


@router.post("/{cv_id}/set-default", response_model=CVRead, summary="Đặt CV mặc định")
def set_default(cv_id: int, db: DbSession, student: CurrentStudent):
    return cv_service.set_default(db, student, cv_id)


@router.get("/{cv_id}/download", response_class=FileResponse, summary="Tải CV theo quyền truy cập")
def download_cv(cv_id: int, db: DbSession, user: CurrentUser):
    path, filename, media_type = cv_service.get_downloadable_path(db, cv_id, user)
    return FileResponse(path=path, filename=filename, media_type=media_type)


@router.post("/{cv_id}/analyze", response_model=CVAnalysisRead, summary="Phân tích CV bằng AI")
def analyze_cv(cv_id: int, db: DbSession, student: CurrentStudent):
    return cv_service.analyze_cv(db, student, cv_id)
