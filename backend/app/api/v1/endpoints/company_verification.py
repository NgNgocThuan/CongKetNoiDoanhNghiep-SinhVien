"""Xác minh email, pháp nhân và quyền đại diện tuyển dụng, độc lập với MOU.

Endpoints theo Mục 21.1 của docs/SYSTEM_ARCHITECTURE_REVIEW.md:
  - POST /api/v1/company/verification/request-email-otp
  - POST /api/v1/company/verification/verify-email-otp
  - POST /api/v1/company/verification/submit-legal-docs
  - GET  /api/v1/company/verification/status
  - GET  /api/v1/admin/verifications            (hàng đợi Admin + link tra cứu MST)
  - POST /api/v1/admin/verifications/{id}/review

OTP chỉ được gửi qua EMAIL (quy tắc bất di bất dịch #1 — không SMS), lưu HASH.
"""
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

from app.core.enums import CompanyVerificationStatus, UserRole, VerificationStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.freelancer_enums import BusinessStatus
from app.dependencies import AdminUser, DbSession
from app.dependencies_freelancer import OnboardingUser
from app.models import Company, CompanyVerification
from app.services.stored_file_service import upload_in_tx
from app.utils.datetime_utils import utcnow


def onboarding_company(user: OnboardingUser):
    if user.role != UserRole.COMPANY or user.company is None:
        raise ForbiddenError('Chỉ tài khoản doanh nghiệp được truy cập hồ sơ này.')
    return user.company

CurrentCompany = Annotated[Company, Depends(onboarding_company)]

router = APIRouter(tags=["Company verification"])

# Link tra cứu nhanh dành cho Admin (Mục 21.1.B.4)
BUSINESS_REGISTRY_URL = "https://dangkykinhdoanh.gov.vn/vn/Pages/Trangchu.aspx"


def _lookup_url(tax_code: str) -> str:
    return f"{BUSINESS_REGISTRY_URL}?tax_code={tax_code}"


# ---------------- Schema DTOs ----------------
class VerifyOtpRequest(BaseModel):
    otp_code: str = Field(..., pattern=r"^[0-9]{6}$", description="Mã OTP 6 chữ số")


class CompanyVerificationStatusRead(BaseModel):
    authority_data: Optional[dict] = None
    company_id: int
    company_name: Optional[str] = None
    tax_code: Optional[str] = None
    legal_representative: Optional[str] = None
    business_address: Optional[str] = None
    email_otp_verified: bool = False
    verification_status: CompanyVerificationStatus
    license_file_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None


class AdminReviewRequest(BaseModel):
    legal_identity_checked: bool = False
    representative_authority_checked: bool = False
    verification_method: Optional[str] = None
    independent_source: Optional[str] = Field(None, max_length=1000)
    confirmation_reference: Optional[str] = Field(None, max_length=1000)
    status: CompanyVerificationStatus = Field(..., description="VERIFIED, REJECTED hoặc NEEDS_REVISION")
    reason: Optional[str] = Field(None, description="Lý do nếu từ chối hoặc yêu cầu sửa đổi")


class AdminVerificationItemRead(BaseModel):
    authority_data: Optional[dict] = None
    applicant_email: Optional[str] = None
    id: int
    company_id: int
    company_name: str
    tax_code: str
    legal_representative: str
    business_address: str
    license_file_id: Optional[int] = None
    email_otp_verified: bool
    verification_status: CompanyVerificationStatus
    rejection_reason: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_user_id: Optional[int] = None
    registry_lookup_url: str


# ---------------- Endpoints: Company ----------------
@router.post("/company/verification/request-email-otp")
def request_email_otp(company: CurrentCompany, db: DbSession):
    from app.schemas.freelancer_accounts import OtpRequestSchema
    from app.services.freelancer_accounts.otp_service import request_otp
    return request_otp(db, user_id=company.user_id, payload=OtpRequestSchema(identifier=company.user.email))


@router.post("/company/verification/verify-email-otp")
def verify_email_otp(payload: VerifyOtpRequest, company: CurrentCompany, db: DbSession):
    from app.schemas.freelancer_accounts import OtpVerifySchema
    from app.services.freelancer_accounts.otp_service import verify_otp
    return verify_otp(db, user_id=company.user_id, payload=OtpVerifySchema(identifier=company.user.email, code=payload.otp_code))


@router.post("/company/verification/submit-legal-docs")
async def submit_legal_docs(
    company: CurrentCompany,
    db: DbSession,
    tax_code: str = Form(..., description="Mã số thuế doanh nghiệp"),
    company_name: str = Form(..., description="Tên công ty theo ĐKKD"),
    legal_representative: str = Form(..., description="Người đại diện theo pháp luật"),
    business_address: str = Form(..., description="Địa chỉ trụ sở chính"),
    license_file: UploadFile = File(..., description="Ảnh chụp hoặc scan Giấy phép kinh doanh (PDF/JPG/PNG)"),
    applicant_name: str = Form(..., min_length=2, max_length=100),
    applicant_position: str = Form(..., min_length=2, max_length=100),
    applicant_phone: str = Form(..., min_length=8, max_length=20),
    applicant_capacity: str = Form(...),
    authority_file: UploadFile = File(..., description="Bằng chứng danh tính người đại diện hoặc giấy ủy quyền tuyển dụng"),
):
    """Bước 2: Nộp thông tin pháp nhân và tải lên Giấy phép kinh doanh (GPKD)."""
    clean_tax_code = tax_code.strip()
    clean_company_name = company_name.strip()
    clean_rep = legal_representative.strip()
    clean_addr = business_address.strip()
    if applicant_capacity not in ('LEGAL_REPRESENTATIVE', 'AUTHORIZED_RECRUITER'):
        raise BadRequestError('Vui lòng chọn tư cách người đăng ký.')
    if not all((applicant_name.strip(), applicant_position.strip(), applicant_phone.strip())):
        raise BadRequestError('Vui lòng điền thông tin người đăng ký.')

    company = db.scalar(select(Company).where(Company.id == company.id).with_for_update())
    if clean_tax_code.replace("-", "") != (company.tax_code or "").replace("-", ""):
        raise BadRequestError("Mã số thuế phải khớp với doanh nghiệp đã đăng ký.")
    if len(clean_company_name) > 255 or len(clean_rep) > 100 or len(clean_addr) > 255:
        raise BadRequestError("Thông tin hồ sơ vượt quá độ dài cho phép.")

    import re
    if not re.fullmatch(r"[0-9]{10}(-?[0-9]{3})?", clean_tax_code) or not all((clean_company_name, clean_rep, clean_addr)):
        raise BadRequestError("Mã số thuế và tên doanh nghiệp không được để trống.")

    verif = db.scalar(
        select(CompanyVerification).where(CompanyVerification.company_id == company.id)
    )
    if not company.user.email_verified_at:
        raise BadRequestError("Vui lòng hoàn thành xác thực mã OTP email trước khi nộp hồ sơ pháp nhân.")
    if company.business_status not in (BusinessStatus.UNVERIFIED, BusinessStatus.NEEDS_REVISION, BusinessStatus.REJECTED):
        raise ConflictError("Doanh nghiệp đã được duyệt hoặc có hồ sơ đang chờ duyệt.")

    if verif and (verif.verification_status == CompanyVerificationStatus.VERIFIED or
                  (verif.verification_status == CompanyVerificationStatus.PENDING and verif.license_file_id)):
        raise ConflictError("Hồ sơ đã được duyệt hoặc đang chờ duyệt.")
    if not verif:
        verif = CompanyVerification(
            company_id=company.id, tax_code=clean_tax_code, company_name=clean_company_name,
            legal_representative=clean_rep, business_address=clean_addr,
        )
        db.add(verif)
    verif.email_otp_verified = True

    # Đọc tệp và lưu vào storage an toàn qua upload_in_tx
    data = await license_file.read(10 * 1024 * 1024 + 1)
    if len(data) == 0:
        raise BadRequestError("Tệp tải lên không có dữ liệu.")
    if len(data) > 10 * 1024 * 1024:
        raise BadRequestError("Dung lượng tệp không được vượt quá 10MB.")

    file_rec = upload_in_tx(
        db,
        user_id=company.user_id,
        data=data,
        filename=license_file.filename or "business_license.pdf",
        mime=license_file.content_type or "application/pdf",
        category="BUSINESS_LICENSE",
    )

    verif.tax_code = clean_tax_code
    authority_rec = upload_in_tx(db, user_id=company.user_id,
        data=await authority_file.read(10 * 1024 * 1024 + 1),
        filename=authority_file.filename or 'authority.pdf',
        mime=authority_file.content_type or 'application/pdf', category='AUTHORIZATION')
    verif.authority_data = dict(applicant_name=applicant_name.strip(),
        applicant_position=applicant_position.strip(), applicant_phone=applicant_phone.strip(),
        applicant_capacity=applicant_capacity, applicant_email=company.user.email,
        authority_file_id=int(authority_rec['id']))
    company.authorization_file_id = int(authority_rec['id'])
    verif.company_name = clean_company_name
    verif.legal_representative = clean_rep
    verif.business_address = clean_addr
    verif.license_file_id = file_rec["id"]
    verif.verification_status = CompanyVerificationStatus.PENDING
    verif.rejection_reason = None
    verif.reviewed_at = None
    verif.reviewer_user_id = None

    # Đồng bộ sang Company model
    company.tax_code = clean_tax_code
    company.name = clean_company_name
    company.address = clean_addr
    company.contact_name = clean_rep
    company.legal_name = clean_company_name
    company.representative_name = clean_rep
    company.business_status = BusinessStatus.PENDING_VERIFICATION

    from app.services.freelancer_domain import audit, notify_admins
    notify_admins(db, 'Hồ sơ doanh nghiệp cần xác minh',
                  f'{clean_company_name} đã gửi hồ sơ pháp nhân và quyền đại diện tuyển dụng.',
                  ref_type='BUSINESS_VERIFICATION', ref_id=verif.id)
    audit(db, company.user_id, "company_verification.submitted", "company_verifications", company.id,
          after={"license_file_id": file_rec["id"], "tax_code": clean_tax_code, "authority_data": verif.authority_data})

    db.commit()
    db.refresh(verif)

    return {
        "message": "Hồ sơ pháp nhân đã được nộp thành công và đang chờ Nhà trường phê duyệt.",
        "verification_status": verif.verification_status,
        "company_id": company.id,
    }


@router.get("/company/verification/status", response_model=CompanyVerificationStatusRead)
def get_verification_status(
    company: CurrentCompany,
    db: DbSession,
):
    """Xem tiến trình và trạng thái xác minh hiện tại của doanh nghiệp."""
    verif = db.scalar(
        select(CompanyVerification).where(CompanyVerification.company_id == company.id)
    )
    if not verif:
        return CompanyVerificationStatusRead(
            company_id=company.id,
            company_name=company.name,
            tax_code=company.tax_code,
            email_otp_verified=company.user.email_verified_at is not None,
            verification_status=CompanyVerificationStatus.VERIFIED if company.business_status == BusinessStatus.VERIFIED else CompanyVerificationStatus.PENDING,
        )

    return CompanyVerificationStatusRead(
        authority_data={k: v for k, v in (verif.authority_data or {}).items() if k in ('applicant_name', 'applicant_position', 'applicant_phone', 'applicant_capacity')},
        company_id=verif.company_id,
        company_name=verif.company_name,
        tax_code=verif.tax_code,
        legal_representative=verif.legal_representative,
        business_address=verif.business_address,
        email_otp_verified=company.user.email_verified_at is not None,
        verification_status=verif.verification_status,
        license_file_id=verif.license_file_id,
        rejection_reason=verif.rejection_reason,
        reviewed_at=verif.reviewed_at,
    )


# ---------------- Endpoints: Admin ----------------
@router.get("/admin/verifications", response_model=List[AdminVerificationItemRead])
def list_verifications_for_admin(
    admin: AdminUser,
    db: DbSession,
    status: Optional[CompanyVerificationStatus] = Query(None, description="Lọc theo trạng thái"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Hàng đợi xét duyệt hồ sơ doanh nghiệp dành cho Admin Nhà trường (có link tra cứu mã số thuế)."""
    stmt = select(CompanyVerification)
    if status:
        stmt = stmt.where(CompanyVerification.verification_status == status)
    stmt = stmt.order_by(desc(CompanyVerification.created_at)).limit(limit).offset(offset)

    rows = db.scalars(stmt).all()
    results = []
    for r in rows:
        results.append(
            AdminVerificationItemRead(
                authority_data=r.authority_data,
                applicant_email=r.company.user.email,
                id=r.id,
                company_id=r.company_id,
                company_name=r.company_name,
                tax_code=r.tax_code,
                legal_representative=r.legal_representative,
                business_address=r.business_address,
                license_file_id=r.license_file_id,
                email_otp_verified=r.email_otp_verified,
                verification_status=r.verification_status,
                rejection_reason=r.rejection_reason,
                created_at=r.created_at,
                reviewed_at=r.reviewed_at,
                reviewer_user_id=r.reviewer_user_id,
                registry_lookup_url=_lookup_url(r.tax_code),
            )
        )
    return results


@router.post("/admin/verifications/{verification_id}/review")
def review_verification(
    verification_id: int,
    payload: AdminReviewRequest,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    """Admin duyệt hoặc từ chối hồ sơ doanh nghiệp."""
    verif = db.get(CompanyVerification, verification_id)
    if not verif:
        raise NotFoundError("Không tìm thấy hồ sơ xác minh.")

    company = db.get(Company, verif.company_id)
    if not company:
        raise NotFoundError("Không tìm thấy doanh nghiệp tương ứng.")

    company = db.scalar(select(Company).where(Company.id == company.id).with_for_update())
    verif = db.scalar(select(CompanyVerification).where(CompanyVerification.id == verification_id).with_for_update().execution_options(populate_existing=True))

    if payload.status not in (CompanyVerificationStatus.VERIFIED, CompanyVerificationStatus.REJECTED, CompanyVerificationStatus.NEEDS_REVISION):
        raise BadRequestError("Quyết định thẩm định không hợp lệ.")
    if verif.verification_status != CompanyVerificationStatus.PENDING or not verif.license_file_id:
        raise ConflictError("Chỉ có thể duyệt hồ sơ đã nộp và đang chờ duyệt.")
    if payload.status != CompanyVerificationStatus.VERIFIED and not (payload.reason or "").strip():
        raise BadRequestError("Vui lòng ghi rõ lý do.")
    if payload.status == CompanyVerificationStatus.VERIFIED:
        from app.services.freelancer_accounts.identity_service import checked_file
        details = verif.authority_data or {}
        if not (payload.legal_identity_checked and payload.representative_authority_checked):
            raise BadRequestError('Cần xác nhận riêng pháp nhân và quyền đại diện tuyển dụng.')
        if not details.get('authority_file_id') or details.get('applicant_email') != company.user.email:
            raise BadRequestError('Hồ sơ thiếu bằng chứng quyền đại diện hoặc email đã thay đổi. Yêu cầu doanh nghiệp bổ sung.')
        methods = ('IDENTITY_MATCH', 'OFFICIAL_EMAIL', 'INDEPENDENT_CALLBACK', 'IN_PERSON')
        if payload.verification_method not in methods or not (payload.independent_source or '').strip() or not (payload.confirmation_reference or '').strip():
            raise BadRequestError('Cần chọn phương thức, nguồn đối chiếu độc lập và thông tin xác nhận.')
        if details.get('applicant_capacity') == 'AUTHORIZED_RECRUITER' and payload.verification_method == 'IDENTITY_MATCH':
            raise BadRequestError('Nhân viên cần xác nhận quyền tuyển dụng từ doanh nghiệp; xác minh danh tính cá nhân chưa đủ.')
        checked_file(db, details['authority_file_id'], company.user_id, category='AUTHORIZATION')
        verif.authority_data = {**details, 'verification_method': payload.verification_method,
            'independent_source': payload.independent_source.strip(),
            'confirmation_reference': payload.confirmation_reference.strip(),
            'legal_identity_checked': True, 'representative_authority_checked': True}
        if not company.user.email_verified_at:
            raise ConflictError("Email hiện tại chưa được xác minh.")
        checked_file(db, verif.license_file_id, company.user_id, category="BUSINESS_LICENSE")
    now = utcnow()
    verif.verification_status = payload.status
    verif.reviewer_user_id = admin.id
    verif.reviewed_at = now
    verif.rejection_reason = payload.reason if payload.status != CompanyVerificationStatus.VERIFIED else None

    # Cập nhật Company model
    if payload.status == CompanyVerificationStatus.VERIFIED:
        company.verification_status = VerificationStatus.APPROVED
        company.business_status = BusinessStatus.VERIFIED
        company.verified_at = now
        company.verified_by = admin.id
        company.business_verified_by = admin.id
        company.business_verified_at = now
        from app.core.enums import UserStatus
        if company.user.status == UserStatus.PENDING_APPROVAL:
            company.user.status = UserStatus.ACTIVE
        company.reject_reason = None
        # Đồng bộ thông tin chuẩn hóa
        company.tax_code = verif.tax_code
        company.name = verif.company_name
        company.address = verif.business_address
        company.contact_name = verif.legal_representative
    elif payload.status == CompanyVerificationStatus.REJECTED:
        company.verification_status = VerificationStatus.REJECTED
        company.business_status = BusinessStatus.REJECTED
        company.reject_reason = payload.reason
    elif payload.status == CompanyVerificationStatus.NEEDS_REVISION:
        company.verification_status = VerificationStatus.PENDING
        company.business_status = BusinessStatus.NEEDS_REVISION
        company.reject_reason = payload.reason

    from app.services.freelancer_domain import audit, notify
    notify(db, company.user_id, 'Kết quả xác minh doanh nghiệp',
           'Doanh nghiệp và quyền đại diện tuyển dụng đã được xác minh. Không bắt buộc ký MOU.' if payload.status == CompanyVerificationStatus.VERIFIED else f'Hồ sơ cần xử lý: {payload.reason}',
           ref_type='BUSINESS_VERIFICATION', ref_id=verif.id)
    audit(db, admin.id, "company_verification.reviewed", "company_verifications", verif.id,
          reason=payload.reason, after={"decision": payload.status.value, "license_file_id": verif.license_file_id, "authority_data": verif.authority_data})


    db.commit()
    return {
        "message": "Đã cập nhật kết quả thẩm định hồ sơ thành công.",
        "status": verif.verification_status,
        "company_id": company.id,
    }
