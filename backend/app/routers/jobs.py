"""Tin tuyển dụng. Người phụ trách: Đỗ Hồng Khôi.

Phân quyền:
  - Sinh viên (CurrentStudent): tìm kiếm tin.
  - Doanh nghiệp (CurrentCompany): tạo, sửa, gửi duyệt, đóng, xem tin của mình, thống kê.
  - GET /jobs/{id}: mọi user đăng nhập; service kiểm tra theo vai trò (sinh viên / doanh nghiệp / admin).

Lưu ý: route cố định (/jobs/me) phải khai báo TRƯỚC route có tham số (/jobs/{job_id}).
"""
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.core.enums import JobStatus, WorkMode
from app.dependencies import CurrentCompany, CurrentStudent, CurrentUser, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.jobs import (
    JobCreate,
    JobFilter,
    JobListItem,
    JobMyItem,
    JobRead,
    JobStats,
    JobUpdate,
)
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def job_filter_params(
    q: Annotated[Optional[str], Query(description="Từ khóa trong tiêu đề, vị trí, mô tả")] = None,
    position: Optional[str] = None,
    location: Optional[str] = None,
    major_id: Annotated[Optional[int], Query(description="Tin dành cho ngành này hoặc mọi ngành")] = None,
    industry_id: Optional[int] = None,
    job_type_id: Optional[int] = None,
    work_mode: Optional[WorkMode] = None,
    flow: Annotated[Optional[Literal["free", "term"]], Query(description="free = tự do, term = theo đợt")] = None,
    skill_ids: Annotated[Optional[list[int]], Query(description="Lọc theo ít nhất một kỹ năng")] = None,
    salary_from: Annotated[Optional[int], Query(ge=0, description="Lương tối đa của tin >= giá trị này")] = None,
    salary_to: Annotated[Optional[int], Query(ge=0, description="Lương tối thiểu của tin <= giá trị này")] = None,
) -> JobFilter:
    return JobFilter(
        q=q,
        position=position,
        location=location,
        major_id=major_id,
        industry_id=industry_id,
        job_type_id=job_type_id,
        work_mode=work_mode,
        flow=flow,
        skill_ids=skill_ids or [],
        salary_from=salary_from,
        salary_to=salary_to,
    )


JobFilters = Annotated[JobFilter, Depends(job_filter_params)]


# ---------------------------------------------------------------- Sinh viên
@router.get("", response_model=Page[JobListItem], summary="Tìm kiếm tin tuyển dụng (sinh viên)")
def search_jobs(db: DbSession, student: CurrentStudent, pagination: Pagination, filters: JobFilters):
    return job_service.search_jobs(db, student, pagination, filters)


# ---------------------------------------------------------------- Doanh nghiệp
@router.get("/me", response_model=Page[JobMyItem], summary="Tin của doanh nghiệp (kèm lượt xem, số đơn)")
def list_my_jobs(
    db: DbSession,
    company: CurrentCompany,
    pagination: Pagination,
    status: Optional[JobStatus] = None,
):
    return job_service.list_my_jobs(db, company, pagination, status=status)


@router.post("", response_model=JobRead, status_code=201, summary="Tạo tin tuyển dụng (nháp)")
def create_job(data: JobCreate, db: DbSession, company: CurrentCompany):
    return job_service.create_job(db, company, data)


# ---------------------------------------------------------------- Theo từng tin
@router.get("/{job_id}", response_model=JobRead, summary="Chi tiết tin tuyển dụng")
def get_job(job_id: int, db: DbSession, user: CurrentUser):
    return job_service.get_job_detail(db, job_id, user)


@router.put("/{job_id}", response_model=JobRead, summary="Sửa tin (tin đã duyệt sẽ phải duyệt lại)")
def update_job(job_id: int, data: JobUpdate, db: DbSession, company: CurrentCompany):
    return job_service.update_job(db, company, job_id, data)


@router.post("/{job_id}/submit", response_model=JobRead, summary="Gửi nhà trường kiểm duyệt")
def submit_job(job_id: int, db: DbSession, company: CurrentCompany):
    return job_service.submit_for_approval(db, company, job_id)


@router.post("/{job_id}/close", response_model=JobRead, summary="Đóng tin tuyển dụng")
def close_job(job_id: int, db: DbSession, company: CurrentCompany):
    return job_service.close_job(db, company, job_id)


@router.get("/{job_id}/stats", response_model=JobStats, summary="Thống kê lượt xem và số đơn của tin")
def get_job_stats(
    job_id: int,
    db: DbSession,
    company: CurrentCompany,
    days: Annotated[int, Query(ge=1, le=365, description="Số ngày gần nhất để thống kê lượt xem")] = 30,
):
    return job_service.get_job_stats(db, company, job_id, days=days)
