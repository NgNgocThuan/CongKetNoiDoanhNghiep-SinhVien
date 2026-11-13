from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError
from app.dependencies import AdminUser, CurrentUser, DbSession
from app.dependencies_freelancer import OnboardingUser
from app.schemas.auth import LoginRequest
from app.schemas.freelance_projects import Resource, ResourcePage
from app.schemas.freelancer_accounts import (
    ClientProfileUpdate,
    CompanyLimitUpdate,
    ContactChange,
    MouReview,
    OtpRequestSchema,
    OtpVerifySchema,
    RegisterClient,
)
from app.schemas.freelancer_disputes import Reason
from app.schemas.freelancer_policy import PolicyUpdate
from app.schemas.terms import TermsAcceptance
from app.services import business_verification_service as business
from app.services import client_account_service as accounts
from app.services import stored_file_service as files
from app.services.freelancer_accounts import otp_service
from app.services.freelancer_accounts.identity_service import download_file
from app.services.freelancer_commands import run_command
from app.services.freelancer_policy_service import read_policy, update_policy_in_tx

router = APIRouter(tags=["Freelancer onboarding and administration"])


@router.post(
    "/auth/register-client",
    response_model=Resource,
    status_code=201,
    summary="Register: /auth/register-client",
)
def register(payload: RegisterClient, request: Request, db: DbSession):
    try:
        return {
            "data": run_command(
                db,
                lambda: accounts.register_in_tx(
                    db, payload=payload, ip_key=request.client.host if request.client else "unknown"
                ),
            )
        }
    except IntegrityError:
        raise ConflictError("Account already exists") from None


@router.post(
    "/auth/onboarding-token", response_model=Resource, summary="Onboarding: /auth/onboarding-token"
)
def onboarding(payload: LoginRequest, request: Request, db: DbSession):
    return {
        "data": accounts.onboarding_login(
            db,
            email=str(payload.email),
            password=payload.password,
            ip_key=request.client.host if request.client else "unknown",
        )
    }


@router.patch(
    "/client-accounts/me", response_model=Resource, summary="Profile: /client-accounts/me"
)
def profile(payload: ClientProfileUpdate, db: DbSession, u: CurrentUser):
    return {
        "data": run_command(db, lambda: accounts.profile_in_tx(db, user_id=u.id, payload=payload))
    }


@router.get("/client-accounts/me", response_model=Resource)
def read_client_profile(db: DbSession, u: CurrentUser):
    from sqlalchemy import select

    from app.core.enums import UserRole
    from app.core.exceptions import NotFoundError
    from app.models import ClientProfile
    from app.services.freelancer_domain import record, user

    user(db, u.id, UserRole.CLIENT)
    row = db.scalar(select(ClientProfile).where(ClientProfile.user_id == u.id))
    if row is None:
        raise NotFoundError("Client profile is missing")
    return {"data": record(row)}


@router.patch("/auth/contacts", response_model=Resource, summary="Contact: /auth/contacts")
def contact(payload: ContactChange, db: DbSession, u: OnboardingUser):
    try:
        return {
            "data": run_command(
                db, lambda: accounts.change_contact_in_tx(db, user_id=u.id, payload=payload)
            )
        }
    except IntegrityError:
        raise ConflictError("Contact already in use") from None


@router.post(
    "/auth/verifications", response_model=Resource, summary="Otp request: /auth/verifications"
)
def otp_request(payload: OtpRequestSchema, request: Request, db: DbSession, u: OnboardingUser):
    return {
        "data": otp_service.request_otp(
            db,
            user_id=u.id,
            payload=payload,
            ip_key=request.client.host if request.client else "unknown",
        )
    }


@router.get("/auth/verification-status", response_model=Resource)
def contact_verification_status(db: DbSession, u: OnboardingUser):
    return {"data": otp_service.verification_status(db, user_id=u.id)}


@router.post(
    "/auth/verifications/{verification_id}/verify",
    response_model=Resource,
    summary="Otp verify: /auth/verifications/{verification_id}/verify",
)
def otp_verify(verification_id: int, payload: OtpVerifySchema, db: DbSession, u: OnboardingUser):
    return {
        "data": otp_service.verify_otp(
            db, user_id=u.id, payload=payload, verification_id=verification_id
        )
    }


@router.post("/files", response_model=Resource, status_code=201, summary="Upload: /files")
async def upload(
    db: DbSession, u: OnboardingUser, file: UploadFile = File(), category: str = Form()
):
    data = await file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise BadRequestError("File exceeds upload limit")
    return {
        "data": run_command(
            db,
            lambda: files.upload_in_tx(
                db,
                user_id=u.id,
                data=data,
                filename=file.filename or "",
                mime=file.content_type,
                category=category,
            ),
        )
    }


@router.get("/files/{file_id}", response_model=Resource, summary="File state: /files/{file_id}")
def file_state(file_id: int, db: DbSession, u: OnboardingUser):
    return {"data": files.get_file(db, user_id=u.id, file_id=file_id)}


@router.get(
    "/files/{file_id}/download",
    response_class=FileResponse,
    summary="Download an authorized stored file",
)
def file_download(file_id: int, db: DbSession, u: OnboardingUser):
    path, filename, content_type = download_file(db, user_id=u.id, file_id=file_id)
    return FileResponse(path=path, filename=filename, media_type=content_type)





@router.get(
    "/companies/me/mou-agreements",
    response_model=ResourcePage,
    summary="Company mous: /companies/me/mou-agreements",
)
def company_mous(
    db: DbSession,
    u: OnboardingUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return business.list_mous(db, user_id=u.id, number=page, size=size)


@router.get(
    "/admin/companies/{company_id}/mou-agreements",
    response_model=ResourcePage,
    summary="Admin mous: /admin/companies/{company_id}/mou-agreements",
)
def admin_mous(
    company_id: int,
    db: DbSession,
    u: AdminUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    return business.list_mous(db, user_id=u.id, company_id=company_id, number=page, size=size)


@router.get("/companies/me/limits", response_model=Resource, summary="Limits: /companies/me/limits")
def limits(db: DbSession, u: OnboardingUser):
    return {"data": business.limits(db, user_id=u.id)}


@router.put(
    "/admin/companies/{company_id}/limits",
    response_model=Resource,
    summary="Override limits: /admin/companies/{company_id}/limits",
)
def override_limits(company_id: int, payload: CompanyLimitUpdate, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: business.override_limits_in_tx(
                db, user_id=u.id, company_id=company_id, payload=payload
            ),
        )
    }


@router.get(
    "/admin/freelancer-policy", response_model=Resource, summary="Policy: /admin/freelancer-policy"
)
def policy(db: DbSession, u: AdminUser):
    values, revision = read_policy(db)
    return {"data": {"revision": revision, "values": values.model_dump(mode="json")}}


@router.put(
    "/admin/freelancer-policy",
    response_model=Resource,
    summary="Policy update: /admin/freelancer-policy",
)
def policy_update(payload: PolicyUpdate, db: DbSession, u: AdminUser):
    return {"data": run_command(db, lambda: update_policy_in_tx(db, user_id=u.id, payload=payload))}





@router.post(
    "/admin/mou-agreements/{mou_id}/approve",
    response_model=Resource,
    summary="Mou approve: /admin/mou-agreements/{mou_id}/approve",
)
def mou_approve(mou_id: int, payload: MouReview, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: business.review_mou_in_tx(
                db, user_id=u.id, mou_id=mou_id, action="approve", payload=payload
            ),
        )
    }


@router.post(
    "/admin/mou-agreements/{mou_id}/reject",
    response_model=Resource,
    summary="Mou reject: /admin/mou-agreements/{mou_id}/reject",
)
def mou_reject(mou_id: int, payload: MouReview, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: business.review_mou_in_tx(
                db, user_id=u.id, mou_id=mou_id, action="reject", payload=payload
            ),
        )
    }


@router.post(
    "/admin/mou-agreements/{mou_id}/revoke",
    response_model=Resource,
    summary="Mou revoke: /admin/mou-agreements/{mou_id}/revoke",
)
def mou_revoke(mou_id: int, payload: MouReview, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: business.review_mou_in_tx(
                db, user_id=u.id, mou_id=mou_id, action="revoke", payload=payload
            ),
        )
    }


@router.post(
    "/admin/companies/{company_id}/suspend-freelancer",
    response_model=Resource,
    summary="Suspend: /admin/companies/{company_id}/suspend-freelancer",
)
def suspend(company_id: int, payload: Reason, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: business.suspension_in_tx(
                db, user_id=u.id, company_id=company_id, suspend=True, reason=payload.reason
            ),
        )
    }


@router.post(
    "/admin/companies/{company_id}/resume-freelancer",
    response_model=Resource,
    summary="Resume: /admin/companies/{company_id}/resume-freelancer",
)
def resume(company_id: int, payload: Reason, db: DbSession, u: AdminUser):
    return {
        "data": run_command(
            db,
            lambda: business.suspension_in_tx(
                db, user_id=u.id, company_id=company_id, suspend=False, reason=payload.reason
            ),
        )
    }


@router.get("/client-accounts/me", response_model=Resource, summary="Read personal client profile")
def my_profile(db: DbSession, u: CurrentUser):
    return {"data": accounts.get_profile(db, user_id=u.id)}


@router.get("/auth/escrow-terms", response_model=Resource)
def escrow_terms(db: DbSession, u: CurrentUser):
    from app.services import ux_terms
    return {"data": ux_terms.status(db, u.id)}



@router.post("/auth/escrow-terms", response_model=Resource)
def accept_escrow_terms(payload: TermsAcceptance, db: DbSession, u: CurrentUser):
    from app.services import ux_terms
    return {"data": run_command(db, lambda: ux_terms.accept_in_tx(db, u.id, payload))}
