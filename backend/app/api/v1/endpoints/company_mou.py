"""Nhiệm vụ 2: Xác minh Đối tác MOU luồng Hybrid (e-sign).

Endpoints theo Mục 21.2 của docs/SYSTEM_ARCHITECTURE_REVIEW.md:
  - GET  /api/v1/company/mou/status
  - GET  /api/v1/company/mou/template/paper
  - POST /api/v1/company/mou/submit-paper-scan
  - GET  /api/v1/company/mou/template/hybrid-signed
  - POST /api/v1/company/mou/upload-hybrid-signed
  - GET  /api/v1/admin/mou/agreements
  - POST /api/v1/admin/mou/agreements/{mou_id}/review

Không gọi API bên thứ ba. Chữ ký được thẩm định offline bằng pyHanko và kiểm tra tính toàn vẹn mã băm.
"""
import hashlib
from datetime import datetime, timedelta
from html import escape
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import case, desc, select

import app.core.freelancer_enums as fe
from app.core.enums import MouType
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.dependencies import AdminUser, CurrentCompany, DbSession
from app.models import Company
from app.models.freelancer_identity import MouAgreement
from app.services import mou_signing
from app.services.company_eligibility import require_verified_company
from app.services.email_service import queue_email
from app.services.stored_file_service import upload_in_tx
from app.utils.datetime_utils import utcnow

# Import pyHanko để đọc và thẩm định chữ ký số PAdES
try:
    from pyhanko.pdf_utils.reader import PdfFileReader  # noqa: F401 (optional dependency probe)
    from pyhanko.sign.validation import validate_pdf_signature  # noqa: F401
    HAS_PYHANKO = True
except ImportError:
    HAS_PYHANKO = False

# Import reportlab để sinh file PDF MOU động
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

router = APIRouter(prefix="", tags=["Company MOU"])


# ---------------- Schemas ----------------
class MouStatusRead(BaseModel):
    hybrid_available: bool = False
    is_mou_partner: bool
    status: Optional[str] = None
    mou_type: Optional[str] = None
    agreement_code: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    sha256_hash: Optional[str] = None
    signer_common_name: Optional[str] = None
    signer_tax_code: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None


class AdminMouItemRead(BaseModel):
    id: int
    document_file_id: int
    company_id: int
    company_name: str
    tax_code: str
    agreement_code: str
    mou_type: str
    signature_method: str
    signature_verification_status: str
    status: str
    effective_from: datetime
    effective_until: datetime
    sha256_hash: Optional[str] = None
    signer_tax_code: Optional[str] = None
    signer_common_name: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None


class AdminReviewMouRequest(BaseModel):
    action: str = Field(..., description="'APPROVE' hoặc 'REJECT'")
    note: Optional[str] = Field(None, description="Ghi chú thẩm định của Admin")


# ---------------- Helper Functions ----------------
def _generate_mou_pdf(company_name: str, tax_code: str, representative: str, is_school_signed: bool = False) -> bytes:
    """Sinh file PDF MOU mẫu chuẩn bị sẵn nội dung."""
    buffer = BytesIO()
    if not HAS_REPORTLAB:
        from app.core.exceptions import AppException
        raise AppException("Dịch vụ tạo PDF chưa sẵn sàng.", status_code=503)

    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 60, "CONG HOA XA HOI CHU NGHIA VIET NAM")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 80, "Doc lap - Tu do - Hanh phuc")
    c.setLineWidth(1)
    c.line(width / 2 - 100, height - 88, width / 2 + 100, height - 88)

    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(width / 2, height - 130, "BIEN BAN GHI NHO HOP TAC (MOU)")
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2, height - 148, "(Ve viec tiep nhan sinh vien thuc tap va hop tac freelancer)")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, height - 190, "BEN A: NHA TRUONG / BAN QUAN TRI NEN TANG")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 210, "Dai dien: Phong Quan he Doanh nghiep & Cong tac Sinh vien")
    c.drawString(70, height - 225, "Dia chi: Tru so chinh Nha truong")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, height - 260, "BEN B: DOANH NGHIEP DOI TAC")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 280, f"Ten doanh nghiep: {company_name}")
    c.drawString(70, height - 295, f"Ma so thue: {tax_code}")
    c.drawString(70, height - 310, f"Nguoi dai dien: {representative}")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, height - 345, "CAC DIEU KHOAN THOA THUAN:")
    c.setFont("Helvetica", 10)
    c.drawString(70, height - 365, "1. Ben B cam ket tiep nhan sinh vien thuc tap va tao dieu kien lam viec dung chuyen mon.")
    c.drawString(70, height - 380, "2. Ben B cam ket chi tra thu lao hop ly, khong thu bat ky khoan phi dat coc nao.")
    c.drawString(70, height - 395, "3. Thoa thuan co gia tri 01 nam ke tu ngay hai ben hoan tat ky ket.")
    c.drawString(70, height - 410, "4. Cac du an hop tac duoc huong chinh sach cap von theo Milestone va uu tien hien thi.")

    # Khung chữ ký
    c.setFont("Helvetica-Bold", 11)
    c.drawString(100, height - 480, "DAI DIEN NHA TRUONG")
    c.drawString(380, height - 480, "DAI DIEN DOANH NGHIEP")

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(100, height - 540, "(Ky ten, dong dau)")

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(380, height - 540, "(Ky ten, dong dau / Ky so)")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ---------------- Endpoints: Company ----------------
@router.get("/company/mou/status", response_model=MouStatusRead)
def get_mou_status(
    company: CurrentCompany,
    db: DbSession,
):
    """Xem trạng thái thỏa thuận MOU hiện tại của doanh nghiệp."""
    now = utcnow()
    mou = db.scalar(
        select(MouAgreement)
        .where(
            MouAgreement.company_id == company.id,
        )
        .order_by(case(((MouAgreement.status == fe.MouStatus.ACTIVE) & (MouAgreement.effective_from <= now) & (MouAgreement.effective_until > now), 0), else_=1), desc(MouAgreement.created_at))
    )
    if not mou:
        return MouStatusRead(
            is_mou_partner=False, hybrid_available=mou_signing.ready(),
            status="NOT_SUBMITTED",
        )

    is_active = mou.status == fe.MouStatus.ACTIVE and mou.effective_from <= now < mou.effective_until and company.business_status == fe.BusinessStatus.VERIFIED and company.operation_status == fe.CompanyOperationStatus.ENABLED
    return MouStatusRead(
        is_mou_partner=is_active, hybrid_available=mou_signing.ready(),
        status=mou.status.value if hasattr(mou.status, "value") else str(mou.status),
        mou_type=mou.mou_type,
        agreement_code=mou.agreement_code,
        effective_from=mou.effective_from,
        effective_until=mou.effective_until,
        sha256_hash=mou.sha256_hash,
        signer_common_name=mou.signer_common_name,
        signer_tax_code=mou.signer_tax_code,
        reviewed_at=mou.reviewed_at,
        review_note=mou.review_note,
    )


@router.get("/company/mou/template/paper")
def download_paper_template(
    company: CurrentCompany,
):
    """Phương án 1: Tải về file mẫu MOU văn bản giấy của Nhà trường để in ra ký đóng dấu đỏ."""
    pdf_bytes = _generate_mou_pdf(
        company_name=company.name or "Doanh nghiệp",
        tax_code=company.tax_code or "",
        representative=company.contact_name or "Đại diện pháp luật",
        is_school_signed=False,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=MOU_Mau_Giay_NhaTruong.pdf"},
    )


@router.post("/company/mou/submit-paper-scan")
async def submit_paper_scan(
    company: CurrentCompany,
    db: DbSession,
    signer_name: str = Form(..., description="Họ tên người ký đại diện doanh nghiệp"),
    signer_position: str = Form("Giám đốc", description="Chức vụ người ký"),
    mou_file: UploadFile = File(..., description="Bản scan MOU đã đóng dấu đỏ (PDF hoặc ảnh)"),
):
    """Phương án 1: Tải lên bản scan giấy đã ký tên đóng dấu đỏ để Admin duyệt thủ công."""
    require_verified_company(company)
    now = utcnow()
    company = db.scalar(select(Company).where(Company.id == company.id).with_for_update())
    if db.scalar(select(MouAgreement.id).where(MouAgreement.company_id == company.id, MouAgreement.status == fe.MouStatus.PENDING_REVIEW).limit(1)):
        raise ConflictError("Đã có thỏa thuận MOU đang chờ duyệt.")
    if not signer_name.strip() or len(signer_name) > 255 or not signer_position.strip() or len(signer_position) > 255:
        raise BadRequestError("Vui lòng nhập người ký và chức vụ hợp lệ.")
    data = await mou_file.read(15 * 1024 * 1024 + 1)
    if len(data) == 0:
        raise BadRequestError("Tệp tải lên không có dữ liệu.")

    sha256_hex = hashlib.sha256(data).hexdigest()

    file_rec = upload_in_tx(
        db,
        user_id=company.user_id,
        data=data,
        filename=mou_file.filename or "mou_scan.pdf",
        mime=mou_file.content_type or "application/pdf",
        category="MOU",
    )

    agreement_code = f"MOU-PAPER-{company.id}-{int(now.timestamp())}"
    mou = MouAgreement(
        company_id=company.id,
        agreement_code=agreement_code,
        document_file_id=file_rec["id"],
        school_name="Trường Đại học",
        school_signer_name="Trưởng phòng QHDN",
        school_signer_position="Trưởng phòng",
        company_signer_name=signer_name.strip(),
        company_signer_position=signer_position.strip(),
        mou_type=MouType.PAPER_SCAN.value,
        signature_method=fe.MouSignatureMethod.SCANNED_SIGNED_DOCUMENT,
        signature_verification_status=fe.SignatureVerificationStatus.NOT_CHECKED,
        status=fe.MouStatus.PENDING_REVIEW,
        signed_at=now,
        effective_from=now,
        effective_until=now + timedelta(days=365),
        sha256_hash=sha256_hex,
        scope_json={"type": "PAPER_SCAN", "uploaded_filename": mou_file.filename},
    )
    db.add(mou)
    db.flush()
    from app.services.freelancer_domain import audit
    audit(db, company.user_id, "mou.paper_submitted", "mou_agreements", mou.id)
    db.commit()
    db.refresh(mou)

    return {
        "message": "Bản scan MOU đã được tải lên thành công và chuyển vào hàng đợi Admin duyệt.",
        "mou_id": mou.id,
        "agreement_code": agreement_code,
        "status": mou.status.value,
    }


@router.get("/company/mou/template/hybrid-signed")
def download_hybrid_signed_template(
    company: CurrentCompany,
):
    """Phương án 2: Tải về file MOU đã có sẵn chữ ký số điện tử của Nhà trường để doanh nghiệp tự ký."""
    require_verified_company(company)
    mou_signing.signing_material()
    pdf_bytes = _generate_mou_pdf(
        company_name=company.name or "Doanh nghiệp đối tác",
        tax_code=company.tax_code or "",
        representative=company.contact_name or "Đại diện pháp luật",
        is_school_signed=False,
    )
    return Response(
        content=mou_signing.sign_template(pdf_bytes, company),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=MOU_SchoolSigned_{company.id}.pdf"},
    )


@router.post("/company/mou/upload-hybrid-signed")
async def upload_hybrid_signed(
    company: CurrentCompany,
    db: DbSession,
    signed_pdf: UploadFile = File(..., description="File PDF đã được doanh nghiệp ký số đè bằng công cụ riêng"),
):
    """Phương án 2 (Ký số Hybrid): Nhận file đã ký số, thẩm định pyHanko tự động và kích hoạt đối tác ngay lập tức."""
    require_verified_company(company)
    now = utcnow()
    content = await signed_pdf.read(15 * 1024 * 1024 + 1)
    if len(content) > 15 * 1024 * 1024:
        raise BadRequestError("MOU vượt quá 15MB.")
    if len(content) == 0:
        raise BadRequestError("Tệp PDF tải lên trống.")

    sha256_hex = hashlib.sha256(content).hexdigest()

    # Thẩm định chữ ký số PAdES bằng pyHanko
    from starlette.concurrency import run_in_threadpool
    signer_name, signer_tax, issuer = await run_in_threadpool(mou_signing.validate_company_pdf, content, company)

    # Lưu trữ file vào storage
    file_rec = upload_in_tx(
        db,
        user_id=company.user_id,
        data=content,
        filename=signed_pdf.filename or "mou_digitally_signed.pdf",
        mime="application/pdf",
        category="MOU",
    )

    from app.services.freelancer_accounts.identity_service import checked_file
    from app.services.stored_file_service import scan_outside_tx
    db.commit()
    scan_outside_tx(db, int(file_rec["id"]))
    db.commit()
    checked_file(db, int(file_rec["id"]), company.user_id, category="MOU")
    agreement_code = f"MOU-HYBRID-{company.id}-{int(now.timestamp())}"
    effective_from = now
    effective_until = now + timedelta(days=365)

    mou = MouAgreement(
        company_id=company.id,
        agreement_code=agreement_code,
        document_file_id=file_rec["id"],
        school_name="Trường Đại học",
        school_signer_name="Trưởng phòng QHDN",
        school_signer_position="Trưởng phòng",
        company_signer_name=signer_name or company.contact_name or "Đại diện ký số",
        company_signer_position="Người đại diện pháp luật",
        mou_type=MouType.HYBRID_DIGITAL_SIGN.value,
        signature_method=fe.MouSignatureMethod.EXTERNALLY_DIGITALLY_SIGNED,
        signature_verification_status=fe.SignatureVerificationStatus.CRYPTOGRAPHICALLY_VERIFIED,
        status=fe.MouStatus.ACTIVE,
        signed_at=now,
        effective_from=effective_from,
        effective_until=effective_until,
        sha256_hash=sha256_hex,
        signer_tax_code=signer_tax or company.tax_code,
        signer_common_name=signer_name,
        certificate_issuer=issuer,
        scope_json={"type": "HYBRID_DIGITAL_SIGN", "validation": "pyHanko_auto_pass"},
        reviewed_at=now,
        review_note="Tự động kích hoạt thành công qua thẩm định chữ ký số PAdES X.509.",
    )
    db.add(mou)

    db.flush()
    from app.services.freelancer_domain import audit
    audit(db, company.user_id, "mou.signature_verified", "mou_agreements", mou.id,
          after={"sha256": sha256_hex, "signer_tax_code": signer_tax})
    from app.services.mou_lifecycle import schedule_mou_lifecycle
    schedule_mou_lifecycle(db, mou)

    from app.services.freelancer_domain import notify
    notify(db, company.user_id, "Thỏa thuận MOU đã được kích hoạt",
           f"Thỏa thuận {agreement_code} đã được xác minh chữ ký số và có hiệu lực đến ngày {effective_until:%d/%m/%Y}.",
           ref_type="mou_agreements", ref_id=mou.id)
    db.commit()
    db.refresh(mou)

    return {
        "message": "Thẩm định chữ ký số thành công! Tài khoản doanh nghiệp đã được kích hoạt danh hiệu Đối tác MOU.",
        "mou_id": mou.id,
        "agreement_code": agreement_code,
        "status": "ACTIVE",
        "effective_until": effective_until,
        "signer_common_name": mou.signer_common_name,
    }


# ---------------- Endpoints: Admin ----------------
@router.get("/admin/mou/agreements", response_model=List[AdminMouItemRead])
def list_mous_for_admin(
    admin: AdminUser,
    db: DbSession,
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: PENDING_REVIEW, ACTIVE, REJECTED"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Hàng đợi quản lý thỏa thuận MOU dành cho Admin."""
    stmt = select(MouAgreement, Company).join(Company, MouAgreement.company_id == Company.id)
    if status:
        stmt = stmt.where(MouAgreement.status == status)
    stmt = stmt.order_by(desc(MouAgreement.created_at)).limit(limit).offset(offset)

    rows = db.execute(stmt).all()
    results = []
    for mou, comp in rows:
        results.append(
            AdminMouItemRead(
                id=mou.id,
                document_file_id=mou.document_file_id,
                company_id=mou.company_id,
                company_name=comp.name,
                tax_code=comp.tax_code or "",
                agreement_code=mou.agreement_code,
                mou_type=mou.mou_type,
                signature_method=mou.signature_method.value if hasattr(mou.signature_method, "value") else str(mou.signature_method),
                signature_verification_status=mou.signature_verification_status.value if hasattr(mou.signature_verification_status, "value") else str(mou.signature_verification_status),
                status=mou.status.value if hasattr(mou.status, "value") else str(mou.status),
                effective_from=mou.effective_from,
                effective_until=mou.effective_until,
                sha256_hash=mou.sha256_hash,
                signer_tax_code=mou.signer_tax_code,
                signer_common_name=mou.signer_common_name,
                created_at=mou.created_at,
                reviewed_at=mou.reviewed_at,
                review_note=mou.review_note,
            )
        )
    return results


@router.post("/admin/mou/agreements/{mou_id}/review")
def review_mou_agreement(
    mou_id: int,
    payload: AdminReviewMouRequest,
    admin: AdminUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    """Admin duyệt hoặc từ chối thỏa thuận MOU ký giấy scan."""
    mou = db.get(MouAgreement, mou_id)
    if not mou:
        raise NotFoundError("Không tìm thấy thỏa thuận MOU.")

    company = db.get(Company, mou.company_id)
    if not company:
        raise NotFoundError("Không tìm thấy doanh nghiệp tương ứng.")

    company = db.scalar(select(Company).where(Company.id == company.id).with_for_update())
    mou = db.scalar(select(MouAgreement).where(MouAgreement.id == mou_id).with_for_update().execution_options(populate_existing=True))

    require_verified_company(company)
    if mou.status != fe.MouStatus.PENDING_REVIEW or mou.mou_type != MouType.PAPER_SCAN.value:
        raise ConflictError("Chỉ duyệt bản scan đang chờ thẩm định.")
    now = utcnow()
    action = payload.action.upper()
    if action == "APPROVE":
        from app.services.freelancer_accounts.identity_service import checked_file
        checked_file(db, mou.document_file_id, company.user_id, category="MOU")
        mou.status = fe.MouStatus.ACTIVE
        mou.signature_verification_status = fe.SignatureVerificationStatus.MANUALLY_REVIEWED
        mou.reviewed_by = admin.id
        mou.reviewed_at = now
        mou.review_note = payload.note or "Admin phê duyệt bản scan MOU hợp lệ."
        from app.services.mou_lifecycle import schedule_mou_lifecycle
        schedule_mou_lifecycle(db, mou)

    elif action == "REJECT":
        if not (payload.note or "").strip():
            raise BadRequestError("Vui lòng ghi rõ lý do từ chối.")
        mou.status = fe.MouStatus.REJECTED
        mou.signature_verification_status = fe.SignatureVerificationStatus.FAILED
        mou.reviewed_by = admin.id
        mou.reviewed_at = now
        mou.review_note = payload.note or "Bản scan MOU không hợp lệ."
    else:
        raise BadRequestError("Action chỉ chấp nhận 'APPROVE' hoặc 'REJECT'.")

    from app.services.freelancer_domain import audit
    audit(db, admin.id, "mou.paper_reviewed", "mou_agreements", mou.id,
          reason=payload.note, after={"decision": action})

    # Bắn email thông báo
    if company.user and company.user.email:
        status_label = "ĐÃ ĐƯỢC DUYỆT THÀNH ĐỐI TÁC CHÍNH THỨC" if action == "APPROVE" else "BỊ TỪ CHỐI"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Kết quả thẩm định thỏa thuận MOU</h2>
            <p>Xin chào <strong>{escape(company.name)}</strong>,</p>
            <p>Biên bản thỏa thuận MOU mã <strong>{escape(mou.agreement_code)}</strong>: <span style="font-weight: bold; color: {'#16a34a' if action == 'APPROVE' else '#dc2626'};">{status_label}</span>.</p>
            {f'<p>Ghi chú: {escape(payload.note)}</p>' if payload.note else ''}
            <p>Trân trọng,<br/>Phòng Quan hệ Doanh nghiệp.</p>
        </div>
        """
        queue_email(
            db,
            background_tasks,
            to_email=company.user.email,
            subject=f"[StudentConnect] Kết quả thỏa thuận MOU: {status_label}",
            body_html=body_html,
            type="MOU_REVIEW_RESULT",
            user_id=company.user_id,
            ref_type="MOU_AGREEMENT",
            ref_id=mou.id,
        )

    db.commit()
    return {
        "message": f"Thỏa thuận MOU đã được {('phê duyệt' if action == 'APPROVE' else 'từ chối')}.",
        "status": mou.status.value,
        "mou_id": mou.id,
    }
