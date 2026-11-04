from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.freelancer_accounts import MouAgreementSchema

router = APIRouter(prefix="/mou-agreements", tags=["MOU Agreements - Group A"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_mou_agreement(
    payload: MouAgreementSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A4: Quản lý MOU, thẩm quyền và hiệu lực."""
    return {
        "status": "created",
        "mou_code": payload.mou_code,
        "company_id": payload.company_id,
        "message": "Đã tạo biên bản ghi nhớ MOU thành công",
    }