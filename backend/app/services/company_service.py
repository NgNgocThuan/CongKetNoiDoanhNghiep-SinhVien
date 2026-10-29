"""Nghiệp vụ: Hồ sơ doanh nghiệp. Người phụ trách: Đỗ Hồng Khôi."""
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.enums import CompanyDocType, VerificationStatus
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.catalog import Industry
from app.models.company import Company, CompanyDocument
from app.schemas.companies import CompanyUpdate
from app.utils.file_storage import DOCUMENT_EXTENSIONS, absolute_path, save_upload


def get_my_company(db: Session, company: Company) -> Company:
    """Hồ sơ của chính doanh nghiệp đang đăng nhập (kèm giấy tờ, trạng thái xác thực)."""
    db.refresh(company)
    return company


def update_company(db: Session, company: Company, data: CompanyUpdate) -> Company:
    changes = data.model_dump(exclude_unset=True)
    industry_id = changes.get("industry_id")
    if industry_id is not None and db.get(Industry, industry_id) is None:
        raise BadRequestError("Lĩnh vực không tồn tại")
    for field, value in changes.items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


def add_document(db: Session, company: Company, doc_type: CompanyDocType, file: UploadFile) -> CompanyDocument:
    file_url = save_upload(file, f"companies/{company.id}", DOCUMENT_EXTENSIONS)
    document = CompanyDocument(company_id=company.id, doc_type=doc_type, file_url=file_url)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def remove_document(db: Session, company: Company, document_id: int) -> None:
    document = db.get(CompanyDocument, document_id)
    # Giấy tờ của công ty khác -> 404 để không lộ sự tồn tại
    if document is None or document.company_id != company.id:
        raise NotFoundError("Không tìm thấy giấy tờ")
    file_url = document.file_url
    db.delete(document)
    db.commit()
    absolute_path(file_url).unlink(missing_ok=True)


def get_public_company(db: Session, company_id: int) -> Company:
    """Hồ sơ công khai: chỉ công ty đã được nhà trường duyệt (APPROVED)."""
    company = db.get(Company, company_id)
    if company is None or company.verification_status != VerificationStatus.APPROVED:
        raise NotFoundError("Không tìm thấy doanh nghiệp")
    return company