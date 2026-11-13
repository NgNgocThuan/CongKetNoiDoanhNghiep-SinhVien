"""Nhiệm vụ 3: Job Board tinh gọn (tin công khai + ứng tuyển + mời phỏng vấn).

Endpoints theo Mục 21.3 của docs/SYSTEM_ARCHITECTURE_REVIEW.md:
  - POST  /api/v1/job-board/jobs                       (Doanh nghiệp tạo tin, MOU được auto-approve & is_featured=1)
  - GET   /api/v1/job-board/jobs                       (Danh sách việc làm, tin is_featured nổi bật lên đầu)
  - GET   /api/v1/job-board/jobs/{job_id}              (Chi tiết tin tuyển dụng)
  - POST  /api/v1/job-board/jobs/{job_id}/apply        (Sinh viên nộp CV ứng tuyển)
  - GET   /api/v1/job-board/company/jobs/{id}/applications (Doanh nghiệp xem danh sách ứng viên)
  - PATCH /api/v1/job-board/company/applications/{id}/status (Cập nhật trạng thái + mời phỏng vấn)

Bỏ hoàn toàn việc quản lý thực tập theo đợt, báo cáo định kỳ và sự tham gia của Giảng viên.
"""
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

import app.core.freelancer_enums as fe
from app.core.enums import ApplicationStatus, JobStatus, WorkMode
from app.core.exceptions import NotFoundError
from app.dependencies import CurrentCompany, CurrentStudent, DbSession
from app.models import Company, Student
from app.models.application import Application
from app.models.job import Job
from app.models.student import CV
from app.services.company_eligibility import require_verified_company
from app.services.freelancer_accounts.eligibility_service import company_has_valid_mou
from app.utils.datetime_utils import utcnow

router = APIRouter(prefix="/job-board", tags=["Job board"])


# ---------------- Schemas ----------------
class JobCreatePayload(BaseModel):
    title: str = Field(..., max_length=255, description="Tiêu đề tin tuyển dụng")
    position: str = Field(..., max_length=255, description="Vị trí tuyển dụng")
    job_type_id: int = Field(default=1, description="1: Thực tập sinh, 2: Bán thời gian, 3: Toàn thời gian")
    industry_id: Optional[int] = None
    description: str = Field(..., description="Mô tả công việc chi tiết")
    requirements: Optional[str] = Field(None, description="Yêu cầu năng lực & kỹ năng")
    benefits: Optional[str] = Field(None, description="Quyền lợi & chế độ đãi ngộ")
    quantity: int = Field(default=1, ge=1, description="Số lượng cần tuyển")
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    is_salary_negotiable: bool = False
    location: Optional[str] = Field(None, max_length=255)
    work_mode: WorkMode = WorkMode.ONSITE
    deadline: date = Field(..., description="Hạn nộp hồ sơ (YYYY-MM-DD)")


class JobItemRead(BaseModel):
    id: int
    company_id: int
    company_name: str
    company_logo_url: Optional[str] = None
    title: str
    position: str
    job_type_id: int
    industry_id: Optional[int] = None
    description: str
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    quantity: int
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    is_salary_negotiable: bool
    location: Optional[str] = None
    work_mode: WorkMode
    deadline: date
    status: JobStatus
    is_featured: bool
    is_mou_partner: bool
    view_count: int
    created_at: datetime


class ApplyJobPayload(BaseModel):
    cv_id: int = Field(..., description="ID của CV sinh viên")
    cover_letter: Optional[str] = Field(None, description="Thư giới thiệu / Động lực ứng tuyển")


class UpdateApplicationStatusPayload(BaseModel):
    status: ApplicationStatus = Field(..., description="Trạng thái mới: SCREENING, SHORTLISTED, INTERVIEW, OFFER, HIRED, REJECTED")
    interview_time: Optional[datetime] = Field(None, description="Thời gian phỏng vấn")
    interview_location: Optional[str] = Field(None, description="Địa điểm hoặc link Google Meet / Zoom")
    interview_notes: Optional[str] = Field(None, description="Ghi chú thêm cho ứng viên")


class ApplicantRead(BaseModel):
    application_id: int
    student_id: int
    student_name: str
    student_email: Optional[str] = None
    cv_id: int
    cv_title: Optional[str] = None
    cv_file_url: Optional[str] = None
    cover_letter: Optional[str] = None
    current_status: ApplicationStatus
    applied_at: datetime
    interview_time: Optional[datetime] = None
    interview_location: Optional[str] = None
    interview_notes: Optional[str] = None


# ---------------- Helpers ----------------
def _is_active_mou(db: DbSession, company_id: int) -> bool:
    return company_has_valid_mou(db, company_id, utcnow())


# ---------------- Endpoints ----------------
@router.post("/jobs", response_model=JobItemRead)
def create_job(
    payload: JobCreatePayload,
    company: CurrentCompany,
    db: DbSession,
):
    """Doanh nghiệp đăng tin tuyển dụng.

    - Nếu là Đối tác MOU: Tự động duyệt (is_featured=1, status=APPROVED).
    - Nếu là Doanh nghiệp thường: Chờ Admin duyệt (is_featured=0, status=PENDING_APPROVAL).
    """
    require_verified_company(company)
    from app.services.job_service import _check_deadline, _check_salary, _validate_refs
    _check_deadline(payload.deadline)
    _check_salary(payload.salary_min, payload.salary_max)
    _validate_refs(db, job_type_id=payload.job_type_id, industry_id=payload.industry_id)
    now = utcnow()
    is_partner = _is_active_mou(db, company.id)

    initial_status = JobStatus.APPROVED if is_partner else JobStatus.PENDING_APPROVAL
    is_featured = True if is_partner else False
    approved_at = now if is_partner else None

    job = Job(
        company_id=company.id,
        title=payload.title.strip(),
        position=payload.position.strip(),
        job_type_id=payload.job_type_id,
        industry_id=payload.industry_id,
        description=payload.description.strip(),
        requirements=payload.requirements.strip() if payload.requirements else None,
        benefits=payload.benefits.strip() if payload.benefits else None,
        quantity=payload.quantity,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        is_salary_negotiable=payload.is_salary_negotiable,
        location=payload.location.strip() if payload.location else company.address,
        work_mode=payload.work_mode,
        deadline=payload.deadline,
        status=initial_status,
        is_featured=is_featured,
        approved_at=approved_at,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return JobItemRead(
        id=job.id,
        company_id=job.company_id,
        company_name=company.name,
        company_logo_url=company.logo_url,
        title=job.title,
        position=job.position,
        job_type_id=job.job_type_id,
        industry_id=job.industry_id,
        description=job.description,
        requirements=job.requirements,
        benefits=job.benefits,
        quantity=job.quantity,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        is_salary_negotiable=job.is_salary_negotiable,
        location=job.location,
        work_mode=job.work_mode,
        deadline=job.deadline,
        status=job.status,
        is_featured=job.is_featured,
        is_mou_partner=is_partner,
        view_count=job.view_count,
        created_at=job.created_at,
    )


@router.get("/jobs", response_model=List[JobItemRead])
def list_jobs(
    db: DbSession,
    q: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề hoặc vị trí"),
    location: Optional[str] = None,
    work_mode: Optional[WorkMode] = None,
    job_type_id: Optional[int] = None,
    is_featured_only: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Danh sách tin tuyển dụng công khai.

    Ưu tiên ghim các tin có is_featured=1 (Đối tác MOU) lên đầu trang.
    """
    stmt = (
        select(Job, Company)
        .join(Company, Job.company_id == Company.id)
        .where(Job.status == JobStatus.APPROVED, Job.deadline >= date.today(), Company.business_status == fe.BusinessStatus.VERIFIED, Company.operation_status == fe.CompanyOperationStatus.ENABLED)
    )

    if q:
        kw = f"%{q.strip()}%"
        stmt = stmt.where((Job.title.ilike(kw)) | (Job.position.ilike(kw)))
    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location.strip()}%"))
    if work_mode:
        stmt = stmt.where(Job.work_mode == work_mode)
    if job_type_id:
        stmt = stmt.where(Job.job_type_id == job_type_id)
    if is_featured_only:
        stmt = stmt.where(Job.is_featured.is_(True))

    # Ưu tiên ghim tin is_featured lên trước, sau đó sắp xếp theo ngày đăng mới nhất
    stmt = stmt.order_by(desc(Job.is_featured), desc(Job.created_at)).limit(limit).offset(offset)

    rows = db.execute(stmt).all()
    results = []
    for job, comp in rows:
        results.append(
            JobItemRead(
                id=job.id,
                company_id=job.company_id,
                company_name=comp.name,
                company_logo_url=comp.logo_url,
                title=job.title,
                position=job.position,
                job_type_id=job.job_type_id,
                industry_id=job.industry_id,
                description=job.description,
                requirements=job.requirements,
                benefits=job.benefits,
                quantity=job.quantity,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                is_salary_negotiable=job.is_salary_negotiable,
                location=job.location,
                work_mode=job.work_mode,
                deadline=job.deadline,
                status=job.status,
                is_featured=job.is_featured,
                is_mou_partner=_is_active_mou(db, job.company_id),
                view_count=job.view_count,
                created_at=job.created_at,
            )
        )
    return results


@router.get("/jobs/{job_id}", response_model=JobItemRead)
def get_job_detail(
    job_id: int,
    db: DbSession,
):
    """Xem chi tiết tin tuyển dụng."""
    row = db.execute(
        select(Job, Company).join(Company, Job.company_id == Company.id).where(Job.id == job_id, Job.status == JobStatus.APPROVED, Company.operation_status == fe.CompanyOperationStatus.ENABLED)
    ).first()
    if not row:
        raise NotFoundError("Tin tuyển dụng không tồn tại.")

    job, comp = row
    job.view_count += 1
    db.commit()

    return JobItemRead(
        id=job.id,
        company_id=job.company_id,
        company_name=comp.name,
        company_logo_url=comp.logo_url,
        title=job.title,
        position=job.position,
        job_type_id=job.job_type_id,
        industry_id=job.industry_id,
        description=job.description,
        requirements=job.requirements,
        benefits=job.benefits,
        quantity=job.quantity,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        is_salary_negotiable=job.is_salary_negotiable,
        location=job.location,
        work_mode=job.work_mode,
        deadline=job.deadline,
        status=job.status,
        is_featured=job.is_featured,
        is_mou_partner=_is_active_mou(db, job.company_id),
        view_count=job.view_count,
        created_at=job.created_at,
    )


@router.post("/jobs/{job_id}/apply")
def apply_job(
    job_id: int,
    payload: ApplyJobPayload,
    student: CurrentStudent,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    """Sinh viên nộp hồ sơ ứng tuyển vào tin tuyển dụng."""
    from app.schemas.applications import ApplicationCreate
    from app.services.application_service import apply
    job = db.get(Job, job_id)
    if not job:
        raise NotFoundError("Tin tuyển dụng không tồn tại.")
    require_verified_company(db.get(Company, job.company_id))
    application = apply(db, background_tasks, student, ApplicationCreate(job_id=job_id, cv_id=payload.cv_id, cover_letter=payload.cover_letter))
    return {"application_id": application.id, "status": application.current_status.value}


@router.get("/company/jobs/{job_id}/applications", response_model=List[ApplicantRead])
def list_job_applications_for_company(
    job_id: int,
    company: CurrentCompany,
    db: DbSession,
):
    """Doanh nghiệp xem danh sách ứng viên của tin tuyển dụng mình đăng."""
    job = db.get(Job, job_id)
    if not job or job.company_id != company.id:
        raise NotFoundError("Tin tuyển dụng không tồn tại hoặc không thuộc quyền quản lý của bạn.")

    stmt = (
        select(Application, Student, CV)
        .join(Student, Application.student_id == Student.id)
        .outerjoin(CV, Application.cv_id == CV.id)
        .where(Application.job_id == job_id)
        .order_by(desc(Application.applied_at))
    )
    rows = db.execute(stmt).all()

    results = []
    for app, stu, cv in rows:
        results.append(
            ApplicantRead(
                application_id=app.id,
                student_id=stu.id,
                student_name=stu.full_name,
                student_email=stu.user.email if stu.user and app.current_status in (ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER, ApplicationStatus.HIRED) else None,
                cv_id=app.cv_id,
                cv_title=cv.title if cv else None,
                cv_file_url=f"/api/v1/company/applications/{app.id}/cv",
                cover_letter=app.cover_letter,
                current_status=app.current_status,
                applied_at=app.applied_at,
                interview_time=app.interview_time,
                interview_location=app.interview_location,
                interview_notes=app.interview_notes,
            )
        )
    return results


@router.patch("/company/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    payload: UpdateApplicationStatusPayload,
    company: CurrentCompany,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    """Doanh nghiệp cập nhật trạng thái ứng viên & lên lịch phỏng vấn."""
    from app.services.company_application_service import log_status_change
    return log_status_change(db, background_tasks, company, application_id, payload.status,
                             interview_time=payload.interview_time,
                             interview_location=payload.interview_location,
                             interview_notes=payload.interview_notes)
