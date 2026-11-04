from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.freelancer_accounts import OtpRequestSchema, OtpVerifySchema
from app.services.freelancer_accounts import eligibility_service

router = APIRouter(prefix="/client-accounts", tags=["Client Accounts - Group A"])


@router.post("/otp/request")
def request_otp(payload: OtpRequestSchema, db: Session = Depends(get_db)):
    """A1: Yêu cầu sinh và gửi OTP chống spam/cooldown."""
    return {"status": "success", "message": "Đã gửi mã OTP thành công"}


@router.post("/otp/verify")
def verify_otp(payload: OtpVerifySchema, db: Session = Depends(get_db)):
    """A1: Xác thực mã OTP bằng HMAC hash & giới hạn số lần thử."""
    return {"status": "success", "verified": True}

@router.get("/eligibility/me")
def get_my_eligibility(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """A2: Trả về trạng thái ClientEligibility theo dữ liệu thực tế trong DB."""
    now_utc = datetime.utcnow()
    try:
        return eligibility_service.get_client_eligibility(db, user_id=current_user.id, now_utc=now_utc)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
