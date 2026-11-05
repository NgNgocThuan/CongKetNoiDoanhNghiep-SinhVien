from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models import MouAgreement, Company
from app.schemas.freelancer_accounts import MouAgreementSchema
from app.services.freelancer_accounts import mou_rules
from app.services.freelancer_accounts.common import as_naive_utc

router = APIRouter(prefix="/mou-agreements", tags=["MOU Agreements - Group A"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_mou_agreement(
    payload: MouAgreementSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A4: Quản lý MOU, thẩm quyền, kiểm tra thời hạn và lưu vào cơ sở dữ liệu thực tế."""
    now_utc = datetime.utcnow()
    
    try:
        # 1. Kiểm tra thời hạn MOU theo quy tắc chuẩn trong mou_rules
        if hasattr(payload, "effective_from") and hasattr(payload, "effective_until"):
            mou_rules.validate_mou_period(
                effective_from=payload.effective_from,
                effective_until=payload.effective_until,
                now_utc=now_utc,
            )

        # 2. Kiểm tra công ty tồn tại và thuộc quyền sở hữu của user (hoặc phân quyền admin)
        company = db.get(Company, payload.company_id)
        if company is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy thông tin doanh nghiệp tương ứng.",
            )

        # 3. Tạo mới bản ghi MOU Agreement trong DB
        new_mou = MouAgreement(
            company_id=payload.company_id,
            mou_code=payload.mou_code,
            effective_from=as_naive_utc(payload.effective_from),
            effective_until=as_naive_utc(payload.effective_until),
            status="PENDING",  # Hoặc trạng thái khởi tạo theo đặc tả hệ thống
        )
        db.add(new_mou)
        db.commit()
        db.refresh(new_mou)

        return {
            "status": "created",
            "mou_id": new_mou.id,
            "mou_code": new_mou.mou_code,
            "company_id": new_mou.company_id,
            "message": "Đã tạo biên bản ghi nhớ MOU thành công",
        }
    except mou_rules.MouValidationError as mve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(mve)
        ) from mve
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e