from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.dependencies import DbSession
from app.dependencies_freelancer import OnboardingUser
from app.services.freelancer_accounts.identity_service import download_file

router = APIRouter(prefix="/files", tags=["Freelancer files"])


@router.get("/{file_id}/download")
def download_stored_file(file_id: int, current_user: OnboardingUser, db: DbSession):
    path, name, media_type = download_file(db, user_id=current_user.id, file_id=file_id)
    return FileResponse(path, filename=name, media_type=media_type)
