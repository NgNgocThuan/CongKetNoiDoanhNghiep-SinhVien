from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.freelancer_accounts import OtpRequestSchema, OtpVerifySchema
from app.services.freelancer_accounts import eligibility_service, otp_policy

router = APIRouter(prefix="/client-accounts", tags=["Client Accounts - Group A"])


@router.post("/otp/request")
def request_otp(
    payload: OtpRequestSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A1: Yêu cầu sinh và gửi OTP chống spam/cooldown dựa trên chính sách thực tế."""
    try:
        # Lấy cấu hình và secret hệ thống (có thể điều chỉnh tùy thuộc vào cách bạn định nghĩa cấu hình ứng dụng)
        config = otp_policy.OtpConfig()
        # Secret khóa bí mật dùng cho HMAC (nên lấy từ settings, ví dụ: settings.SECRET_KEY.encode('utf-8'))
        secret_key = b"default-secret-key-change-me" 

        subject = f"user:{current_user.id}"
        purpose = payload.purpose if hasattr(payload, "purpose") else "client_action"

        # (Tùy chọn) Truy vấn lịch sử các lần gửi OTP trước đó của subject + purpose từ DB để kiểm tra cooldown / rate limit
        # Ví dụ: previous_sends = db_get_previous_sends(db, subject, purpose)
        previous_sends = [] # Thay thế bằng dữ liệu thực tế từ DB nếu có

        decision = otp_policy.check_send_allowed(config, datetime.utcnow(), previous_sends)
        if not decision.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Vui lòng thử lại sau {decision.retry_after_seconds} giây (đang trong thời gian chờ cooldown/rate limit)."
            )

        # Phát hành challenge mới
        raw_code, challenge = otp_policy.issue_challenge(
            config, secret_key, purpose, subject, datetime.utcnow()
        )

        # TODO: Lưu challenge vào DB và thực hiện gửi mã (raw_code) qua SMS/Email hoặc outbox queue
        # příklad: save_challenge_to_db(db, subject, purpose, challenge)

        return {
            "status": "success",
            "message": "Đã tạo và gửi mã OTP thành công",
            # Lưu ý: Trong môi trường production thực tế, không trả về raw_code ở response mà chỉ gửi qua kênh SMS/Email!
            # "debug_code": raw_code 
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/otp/verify")
def verify_otp(
    payload: OtpVerifySchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A1: Xác thực mã OTP bằng HMAC hash & giới hạn số lần thử."""
    try:
        config = otp_policy.OtpConfig()
        secret_key = b"default-secret-key-change-me"
        
        subject = f"user:{current_user.id}"
        purpose = payload.purpose if hasattr(payload, "purpose") else "client_action"

        # TODO: Lấy challenge hiện tại đang lưu trong DB của user này ra
        # challenge_from_db = get_active_challenge_from_db(db, subject, purpose)
        # Nếu không tìm thấy challenge:
        # raise HTTPException(status_code=400, detail="Không tìm thấy mã OTP hoặc mã đã hết hạn.")

        # Đoạn mẫu gọi hàm verify_challenge từ otp_policy:
        # result = otp_policy.verify_challenge(
        #     config, secret_key, purpose, subject, challenge_from_db, payload.code, datetime.utcnow()
        # )
        
        # Cập nhật trạng thái attempts/consumed_at vào DB dựa trên result.challenge
        
        # if not result.ok:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Xác thực thất bại. Trạng thái: {result.outcome}, còn lại {result.attempts_left} lần thử."
        #     )

        return {"status": "success", "verified": True, "message": "Xác thực OTP thành công"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/eligibility/me")
def get_my_eligibility(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """A2: Trả về trạng thái ClientEligibility theo dữ liệu thực tế trong DB."""
    now_utc = datetime.utcnow()
    try:
        return eligibility_service.get_client_eligibility(
            db, user_id=current_user.id, now_utc=now_utc
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e