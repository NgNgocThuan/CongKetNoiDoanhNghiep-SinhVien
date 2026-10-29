"""Hồ sơ doanh nghiệp. Người phụ trách: Đỗ Hồng Khôi."""
from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile

from app.core.enums import CompanyDocType
from app.dependencies import CurrentCompany, CurrentUser, DbSession
from app.schemas.companies import (
    CompanyDocumentRead,
    CompanyPublicRead,
    CompanyRead,
    CompanyUpdate,
)
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/me", response_model=CompanyRead, summary="Hồ sơ và trạng thái xác thực của tôi")
def get_my_company(db: DbSession, company: CurrentCompany):
    return company_service.get_my_company(db, company)


@router.put("/me", response_model=CompanyRead, summary="Cập nhật hồ sơ doanh nghiệp")
def update_my_company(data: CompanyUpdate, db: DbSession, company: CurrentCompany):
    return company_service.update_company(db, company, data)


@router.post(
    "/me/documents",
    response_model=CompanyDocumentRead,
    status_code=201,
    summary="Upload giấy tờ xác thực (pdf, jpg, png)",
)
def upload_document(
    doc_type: Annotated[CompanyDocType, Form()],
    file: Annotated[UploadFile, File()],
    db: DbSession,
    company: CurrentCompany,
):
    return company_service.add_document(db, company, doc_type, file)


@router.delete("/me/documents/{document_id}", status_code=204, summary="Xóa giấy tờ xác thực")
def delete_document(document_id: int, db: DbSession, company: CurrentCompany):
    company_service.remove_document(db, company, document_id)
    return Response(status_code=204)


# Đặt SAU các route /me để "me" không bị hiểu là company_id
@router.get("/{company_id}", response_model=CompanyPublicRead, summary="Hồ sơ công khai của doanh nghiệp")
def get_public_company(company_id: int, db: DbSession, _: CurrentUser):
    return company_service.get_public_company(db, company_id)