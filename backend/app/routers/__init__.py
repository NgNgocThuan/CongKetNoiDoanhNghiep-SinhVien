"""Gom toàn bộ router. MỌI router đã được đăng ký sẵn ở đây,
nên các thành viên chỉ làm việc trong file router của mình, không cần sửa file này
(tránh xung đột merge). Chỉ sửa khi thêm router MỚI hoàn toàn."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    client_accounts,
    company_mou,
    company_verification,
    files,
    job_board,
    mou_agreements,
)
from app.routers import (
    admin_companies,
    admin_disputes,
    admin_jobs,
    admin_students,
    applications,
    auth,
    cancellations,
    catalog,
    companies,
    company_applications,
    cvs,
    dashboard,
    deliverables,
    disputes,
    exports,
    freelance_applications,
    freelance_contracts,
    freelance_projects,
    freelance_reviews,
    freelancer_finance,
    freelancer_onboarding,
    freelancer_operations,
    freelancer_workspace,
    invitations,
    jobs,
    matching,
    milestones,
    notifications,
    reports,
    saved_jobs,
    students,
    users,
)

api_router = APIRouter()

for _module in (
    auth,
    users,
    catalog,
    students,
    cvs,
    saved_jobs,
    invitations,
    companies,
    jobs,
    applications,
    company_applications,
    admin_students,
    admin_companies,
    admin_jobs,
    reports,
    matching,
    dashboard,
    exports,
    notifications,
    deliverables,
    freelance_contracts,
    freelance_reviews,
    milestones,
):
    api_router.include_router(_module.router)

# Group A uses the same app/router registry as all other backend modules.

for _module in (
    client_accounts,
    files,
    mou_agreements,
    company_verification,
    company_mou,
    job_board,
):
    api_router.include_router(_module.router)

for _module in (
    freelance_projects,
    freelance_applications,
    freelancer_onboarding,
    cancellations,
    disputes,
    admin_disputes,
):
    api_router.include_router(_module.router)


api_router.include_router(freelancer_operations.router)

api_router.include_router(freelancer_finance.router)


api_router.include_router(freelancer_workspace.router)
