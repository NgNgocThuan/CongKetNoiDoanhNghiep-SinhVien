from fastapi import APIRouter, Request

from app.dependencies import DbSession
from app.dependencies_freelancer import OnboardingUser
from app.schemas.freelancer_accounts import OtpRequestSchema, OtpVerifySchema
from app.services.freelancer_accounts import eligibility_service, otp_service
from app.services.freelancer_accounts.identity_service import now_utc

router = APIRouter(prefix="/client-accounts", tags=["Freelancer accounts"])


@router.post("/otp/request")
def request_otp(
    payload: OtpRequestSchema, request: Request, current_user: OnboardingUser, db: DbSession
):
    return otp_service.request_otp(
        db,
        user_id=current_user.id,
        payload=payload,
        ip_key=request.client.host if request.client else "unknown",
    )


@router.post("/otp/verify")
def verify_otp(payload: OtpVerifySchema, current_user: OnboardingUser, db: DbSession):
    return otp_service.verify_otp(db, user_id=current_user.id, payload=payload)


@router.get("/eligibility/me")
def get_my_eligibility(current_user: OnboardingUser, db: DbSession):
    decision = eligibility_service.get_client_eligibility(
        db, user_id=current_user.id, now_utc=now_utc()
    )
    from dataclasses import asdict

    result = asdict(decision)
    result["user_id"] = str(decision.user_id)
    result["company_id"] = str(decision.company_id) if decision.company_id else None
    if decision.company_id:
        from app.models import Company

        company = db.get(Company, decision.company_id)
        result["business_status"] = company.business_status
        result["operation_status"] = company.operation_status
    return result
