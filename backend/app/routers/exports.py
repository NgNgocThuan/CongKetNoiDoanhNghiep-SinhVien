from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.dependencies import AdminUser, DbSession
from app.schemas.dashboard import DashboardFilter
from app.services import export_service as service

router = APIRouter(prefix="/admin/exports", tags=["Admin - Exports"])
Filters = Annotated[DashboardFilter, Query()]
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get(
    "/students.xlsx",
    response_class=Response,
    response_model=None,
    summary="Xuất Excel students",
    responses={200: {"content": {XLSX: {"schema": {"type": "string", "format": "binary"}}}}},
)
def export_students(db: DbSession, _: AdminUser, filters: Filters):
    content = service.export_excel(db, "students", filters)
    return Response(
        content,
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="students.xlsx"'},
    )


@router.get(
    "/companies.xlsx",
    response_class=Response,
    response_model=None,
    summary="Xuất Excel companies",
    responses={200: {"content": {XLSX: {"schema": {"type": "string", "format": "binary"}}}}},
)
def export_companies(db: DbSession, _: AdminUser, filters: Filters):
    content = service.export_excel(db, "companies", filters)
    return Response(
        content,
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="companies.xlsx"'},
    )


@router.get(
    "/jobs.xlsx",
    response_class=Response,
    response_model=None,
    summary="Xuất Excel jobs",
    responses={200: {"content": {XLSX: {"schema": {"type": "string", "format": "binary"}}}}},
)
def export_jobs(db: DbSession, _: AdminUser, filters: Filters):
    content = service.export_excel(db, "jobs", filters)
    return Response(
        content,
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="jobs.xlsx"'},
    )


@router.get(
    "/applications.xlsx",
    response_class=Response,
    response_model=None,
    summary="Xuất Excel applications",
    responses={200: {"content": {XLSX: {"schema": {"type": "string", "format": "binary"}}}}},
)
def export_applications(db: DbSession, _: AdminUser, filters: Filters):
    content = service.export_excel(db, "applications", filters)
    return Response(
        content,
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="applications.xlsx"'},
    )


@router.get(
    "/skill-report.xlsx",
    response_class=Response,
    response_model=None,
    summary="Xuất Excel skill-report",
    responses={200: {"content": {XLSX: {"schema": {"type": "string", "format": "binary"}}}}},
)
def export_skill_report(db: DbSession, _: AdminUser, filters: Filters):
    content = service.export_excel(db, "skill-report", filters)
    return Response(
        content,
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="skill-report.xlsx"'},
    )


@router.get(
    "/dashboard.pdf",
    response_class=Response,
    response_model=None,
    summary="Xuất PDF tổng quan và biểu đồ",
    responses={
        200: {"content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}}
    },
)
def export_dashboard(db: DbSession, _: AdminUser, filters: Filters):
    return Response(
        service.export_dashboard_pdf(db, filters),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="dashboard.pdf"'},
    )
