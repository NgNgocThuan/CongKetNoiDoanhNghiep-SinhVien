from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import AdminUser, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.dashboard import (
    BreakdownRow,
    DashboardFilter,
    FlowComparison,
    MatchRateRow,
    OverviewStats,
    SkillGapRow,
    SkillStat,
    TrendPoint,
)
from app.services import dashboard_service as service

router = APIRouter(prefix="/admin/dashboard", tags=["Admin - Dashboard"])
Filters = Annotated[DashboardFilter, Query()]


@router.get("/overview", response_model=OverviewStats, summary="Tổng quan nhà trường")
def overview(db: DbSession, _: AdminUser, filters: Filters):
    return service.overview(db, filters)


@router.get(
    "/breakdown", response_model=Page[BreakdownRow], summary="Thống kê theo khoa ngành khóa đợt"
)
def breakdown(db: DbSession, _: AdminUser, filters: Filters, pagination: Pagination):
    return service.breakdown(db, filters, pagination, filters.group_by)


@router.get("/top-skills", response_model=Page[SkillStat], summary="Kỹ năng được yêu cầu")
def top_skills(db: DbSession, _: AdminUser, filters: Filters, pagination: Pagination):
    return service.top_skills(db, filters, pagination)


@router.get("/skill-gap", response_model=Page[SkillGapRow], summary="Khoảng thiếu kỹ năng")
def skill_gap(db: DbSession, _: AdminUser, filters: Filters, pagination: Pagination):
    return service.skill_gap(db, filters, pagination)


@router.get("/match-rate", response_model=Page[MatchRateRow], summary="Tỷ lệ đáp ứng theo ngành")
def match_rate(db: DbSession, _: AdminUser, filters: Filters, pagination: Pagination):
    return service.match_rate(db, filters, pagination)


@router.get("/trends", response_model=Page[TrendPoint], summary="Xu hướng tuyển dụng theo ngày")
def trends(db: DbSession, _: AdminUser, filters: Filters, pagination: Pagination):
    return service.trends(db, filters, pagination)


@router.get(
    "/flow-comparison",
    response_model=Page[FlowComparison],
    summary="So sánh tuyển tự do và theo đợt",
)
def flow_comparison(db: DbSession, _: AdminUser, filters: Filters, pagination: Pagination):
    return service.flow_comparison(db, filters, pagination)
