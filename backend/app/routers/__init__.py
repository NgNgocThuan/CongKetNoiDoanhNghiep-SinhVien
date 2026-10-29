"""Gom toàn bộ router. MỌI router đã được đăng ký sẵn ở đây,
nên các thành viên chỉ làm việc trong file router của mình, không cần sửa file này
(tránh xung đột merge). Chỉ sửa khi thêm router MỚI hoàn toàn."""
from fastapi import APIRouter

from app.routers import (
    admin_companies,
    admin_jobs,
    admin_lecturers,
    admin_students,
    applications,
    auth,
    catalog,
    companies,
    company_applications,
    cvs,
    dashboard,
    exports,
    internship_terms,
    invitations,
    jobs,
    matching,
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
    admin_lecturers,
    admin_companies,
    admin_jobs,
    reports,
    internship_terms,
    matching,
    dashboard,
    exports,
    notifications,
):
    api_router.include_router(_module.router)
