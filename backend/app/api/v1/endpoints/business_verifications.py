from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.freelancer_accounts import CompanyVerificationSubmitSchema

router = APIRouter(prefix="/business-verifications", tags=["Business Verifications - Group A"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_company_verification(
    payload: CompanyVerificationSubmitSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A3: Nộp hồ sơ mã số thuế và doanh nghiệp để chờ duyệt."""
    return {
        "status": "submitted",
        "tax_code": payload.tax_code,
        "company_name": payload.company_name,
        "message": "Đã nộp hồ sơ xác minh doanh nghiệp thành công",
    }