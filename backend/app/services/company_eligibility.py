"""Shared publication gate for recruitment and company partnerships."""
from app.core.exceptions import ForbiddenError
from app.core.freelancer_enums import BusinessStatus, CompanyOperationStatus


def require_verified_company(company):
    if (
        company.business_status != BusinessStatus.VERIFIED
        or company.operation_status != CompanyOperationStatus.ENABLED
        or not company.user.email_verified_at
    ):
        raise ForbiddenError(
            "Doanh nghiệp cần xác minh email, được duyệt pháp nhân và không bị đình chỉ.",
            code="COMPANY_NOT_ELIGIBLE",
        )
