from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.company import Company
from app.models.user import User
from app.schemas.freelancer_accounts import CompanyVerificationSubmitSchema

router = APIRouter(prefix="/business-verifications", tags=["Business Verifications - Group A"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_company_verification(
    payload: CompanyVerificationSubmitSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A3: Nộp hồ sơ mã số thuế và doanh nghiệp để chờ duyệt với dữ liệu thực tế trong DB."""
    try:
        # Kiểm tra xem user hiện tại đã có bản ghi Company nào chưa
        existing_company = db.scalars(
            select(Company).where(Company.user_id == current_user.id)
        ).first()

        if existing_company:
            # Cập nhật thông tin công ty và chuyển trạng thái về chờ duyệt (PENDING)
            existing_company.name = payload.company_name
            existing_company.tax_code = payload.tax_code
            existing_company.business_status = "PENDING"
            db.commit()
            db.refresh(existing_company)
            company_obj = existing_company
        else:
            # Tạo mới bản ghi Company gắn với user
            new_company = Company(
                user_id=current_user.id,
                name=payload.company_name,
                tax_code=payload.tax_code,
                business_status="PENDING",
            )
            db.add(new_company)
            db.commit()
            db.refresh(new_company)
            company_obj = new_company

        return {
            "status": "submitted",
            "company_id": company_obj.id,
            "tax_code": company_obj.tax_code,
            "company_name": company_obj.name,
            "business_status": getattr(company_obj, "business_status", "PENDING"),
            "message": "Đã nộp hồ sơ xác minh doanh nghiệp thành công",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e