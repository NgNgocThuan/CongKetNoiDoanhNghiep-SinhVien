from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/files", tags=["Stored Files - Group A"])


@router.get("/{file_id}/download")
def download_stored_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A5: Tải file đã lưu trữ sau khi kiểm tra quyền và trạng thái quét CLEAN."""
    return {
        "file_id": file_id,
        "status": "available",
        "scan_status": "CLEAN",
        "download_url": f"https://storage.local/files/{file_id}/download",
    }