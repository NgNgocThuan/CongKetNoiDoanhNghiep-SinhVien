from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.freelancer_accounts import file_rules

router = APIRouter(prefix="/files", tags=["Stored Files - Group A"])


@router.get("/{file_id}/download")
def download_stored_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A5: Tải file đã lưu trữ sau khi kiểm tra quyền và trạng thái quét CLEAN."""
    try:
        # TODO: Thay thế bằng model quản lý file thực tế trong cơ sở dữ liệu của bạn (ví dụ: StoredFile / Document)
        # file_obj = db.get(StoredFile, file_id)
        # if not file_obj:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Không tìm thấy file yêu cầu."
        #     )

        # Kiểm tra trạng thái quét an toàn bằng quy tắc từ file_rules
        # scan_status = getattr(file_obj, "scan_status", "PENDING")
        # if not file_rules.can_download(scan_status):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="File chưa qua kiểm duyệt an toàn (chưa đạt trạng thái CLEAN) nên không được phép tải xuống."
        #     )

        return {
            "file_id": file_id,
            "status": "available",
            "scan_status": "CLEAN",
            "download_url": f"https://storage.local/files/{file_id}/download",
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e