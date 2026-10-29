"""Nghiệp vụ: Tin tuyển dụng. Người phụ trách: Khôi.

Vòng đời tin:
    DRAFT --submit--> PENDING_APPROVAL --(TV1 duyệt)--> APPROVED --(quá hạn)--> EXPIRED
                                        \\--(TV1 từ chối)--> REJECTED --submit--> PENDING_APPROVAL
    Sửa tin APPROVED -> quay lại PENDING_APPROVAL.   Đóng tin -> CLOSED.

Hàm dành cho module khác:
    list_jobs_by_term(db, term_id, params, status=None)   (TV2: liệt kê tin theo đợt)
    expire_overdue_jobs(db)                               (job định kỳ)
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, exists, func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ApplicationStatus, JobStatus, TermStatus, UserRole, VerificationStatus
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models import (
    Application,
    Company,
    Industry,
    InternshipTerm,
    Job,
    JobMajor,
    JobSkill,
    JobType,
    JobView,
    Major,
    Skill,
    Student,
    TermStudent,
    User,
)
from app.schemas.common import PageParams
from app.schemas.jobs import JobCreate, JobFilter, JobMyItem, JobUpdate
from app.utils.datetime_utils import today, utcnow
from app.utils.pagination import paginate

_LIST_OPTIONS = (selectinload(Job.company), selectinload(Job.job_type))
_DETAIL_OPTIONS = (
    selectinload(Job.company),
    selectinload(Job.job_type),
    selectinload(Job.industry),
    selectinload(Job.skills).selectinload(JobSkill.skill),
    selectinload(Job.majors).selectinload(JobMajor.major),
)

# Cột NOT NULL: client gửi null tường minh thì báo lỗi 400 thay vì để DB báo lỗi 500
_NOT_NULL_FIELDS = {
    "title",
    "position",
    "job_type_id",
    "description",
    "quantity",
    "is_salary_negotiable",
    "work_mode",
    "deadline",
}


# ---------------------------------------------------------------- Truy vấn nội bộ
def _load_job(db: Session, job_id: int) -> Job | None:
    """Tải tin kèm quan hệ. populate_existing để luôn lấy dữ liệu mới nhất, không bị cache session."""
    stmt = (
        select(Job)
        .where(Job.id == job_id)
        .options(*_DETAIL_OPTIONS)
        .execution_options(populate_existing=True)
    )
    return db.scalars(stmt).first()


def _get_owned_job(db: Session, company: Company, job_id: int) -> Job:
    job = _load_job(db, job_id)
    # Tin của công ty khác -> 404 để không lộ sự tồn tại
    if job is None or job.company_id != company.id:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    return job


def _visible_to_student(student_id: int):
    """Điều kiện tin được hiển thị cho sinh viên.

    * status = APPROVED và còn hạn (deadline >= hôm nay)
    * tin tự do (term_id NULL) hiện với mọi sinh viên; tin thuộc đợt chỉ hiện với sinh viên nằm trong đợt đó
    """
    student_terms = select(TermStudent.term_id).where(TermStudent.student_id == student_id)
    return and_(
        Job.status == JobStatus.APPROVED,
        Job.deadline >= today(),
        or_(Job.term_id.is_(None), Job.term_id.in_(student_terms)),
    )


# ---------------------------------------------------------------- Kiểm tra dữ liệu đầu vào
def _check_deadline(deadline: date) -> None:
    if deadline < today():
        raise BadRequestError("Hạn nộp hồ sơ không được ở quá khứ")


def _check_salary(salary_min: Optional[int], salary_max: Optional[int]) -> None:
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise BadRequestError("Lương tối thiểu không được lớn hơn lương tối đa")


def _validate_refs(
    db: Session,
    *,
    job_type_id: Optional[int] = None,
    industry_id: Optional[int] = None,
    term_id: Optional[int] = None,
    skill_ids: Optional[list[int]] = None,
    major_ids: Optional[list[int]] = None,
) -> None:
    if job_type_id is not None:
        job_type = db.get(JobType, job_type_id)
        if job_type is None or not job_type.is_active:
            raise BadRequestError("Loại hình công việc không tồn tại")
    if industry_id is not None and db.get(Industry, industry_id) is None:
        raise BadRequestError("Lĩnh vực không tồn tại")
    if term_id is not None:
        term = db.get(InternshipTerm, term_id)
        if term is None:
            raise BadRequestError("Đợt thực tập không tồn tại")
        if term.status == TermStatus.CLOSED:
            raise BadRequestError("Đợt thực tập đã đóng")
    if skill_ids:
        found = db.scalars(select(Skill.id).where(Skill.id.in_(skill_ids), Skill.is_active.is_(True))).all()
        if len(set(found)) != len(set(skill_ids)):
            raise BadRequestError("Có kỹ năng không tồn tại hoặc đã ngừng sử dụng")
    if major_ids:
        found = db.scalars(select(Major.id).where(Major.id.in_(major_ids), Major.is_active.is_(True))).all()
        if len(set(found)) != len(set(major_ids)):
            raise BadRequestError("Có ngành học không tồn tại hoặc đã ngừng sử dụng")


def _require_approved_company(company: Company) -> None:
    if company.verification_status != VerificationStatus.APPROVED:
        raise ForbiddenError(
            "Doanh nghiệp chưa được nhà trường xác thực nên chưa thể đăng tin", code="COMPANY_NOT_APPROVED"
        )


def _replace_skills(db: Session, job: Job, skills) -> None:
    job.skills.clear()
    db.flush()  # xóa dòng cũ trước khi thêm dòng mới để không trùng khóa chính
    job.skills.extend(JobSkill(skill_id=item.skill_id, is_required=item.is_required) for item in skills)


def _replace_majors(db: Session, job: Job, major_ids: list[int]) -> None:
    job.majors.clear()
    db.flush()
    job.majors.extend(JobMajor(major_id=major_id) for major_id in major_ids)


# ---------------------------------------------------------------- Doanh nghiệp: quản lý tin
def create_job(db: Session, company: Company, data: JobCreate) -> Job:
    _require_approved_company(company)
    _check_deadline(data.deadline)
    _check_salary(data.salary_min, data.salary_max)
    _validate_refs(
        db,
        job_type_id=data.job_type_id,
        industry_id=data.industry_id,
        term_id=data.term_id,
        skill_ids=[item.skill_id for item in data.skills],
        major_ids=data.major_ids,
    )
    fields = data.model_dump(exclude={"skills", "major_ids"})
    job = Job(company_id=company.id, status=JobStatus.DRAFT, **fields)
    job.skills = [JobSkill(skill_id=item.skill_id, is_required=item.is_required) for item in data.skills]
    job.majors = [JobMajor(major_id=major_id) for major_id in data.major_ids]
    db.add(job)
    db.commit()
    return _load_job(db, job.id)


def update_job(db: Session, company: Company, job_id: int, data: JobUpdate) -> Job:
    job = _get_owned_job(db, company, job_id)
    if job.status in (JobStatus.CLOSED, JobStatus.EXPIRED):
        raise ConflictError("Tin đã đóng hoặc hết hạn, không thể chỉnh sửa", code="JOB_NOT_EDITABLE")

    changes = data.model_dump(exclude_unset=True, exclude={"skills", "major_ids"})
    for field in _NOT_NULL_FIELDS & changes.keys():
        if changes[field] is None:
            raise BadRequestError(f"Trường '{field}' không được để trống")
    new_skills = data.skills
    new_major_ids = data.major_ids
    if not changes and new_skills is None and new_major_ids is None:
        return job

    if "deadline" in changes:
        _check_deadline(changes["deadline"])
    _check_salary(changes.get("salary_min", job.salary_min), changes.get("salary_max", job.salary_max))
    _validate_refs(
        db,
        job_type_id=changes.get("job_type_id"),
        industry_id=changes.get("industry_id"),
        term_id=changes.get("term_id"),
        skill_ids=[item.skill_id for item in new_skills] if new_skills is not None else None,
        major_ids=new_major_ids,
    )

    for field, value in changes.items():
        setattr(job, field, value)
    if new_skills is not None:
        _replace_skills(db, job, new_skills)
    if new_major_ids is not None:
        _replace_majors(db, job, new_major_ids)

    # Tin đã duyệt mà bị sửa nội dung thì phải được nhà trường duyệt lại
    if job.status == JobStatus.APPROVED:
        job.status = JobStatus.PENDING_APPROVAL
        job.approved_by = None
        job.approved_at = None
    db.commit()
    return _load_job(db, job.id)


def submit_for_approval(db: Session, company: Company, job_id: int) -> Job:
    job = _get_owned_job(db, company, job_id)
    if job.status not in (JobStatus.DRAFT, JobStatus.REJECTED):
        raise ConflictError("Chỉ tin nháp hoặc tin bị từ chối mới được gửi duyệt", code="INVALID_JOB_STATUS")
    _require_approved_company(company)
    if job.deadline < today():
        raise BadRequestError("Hạn nộp đã qua, hãy cập nhật hạn nộp trước khi gửi duyệt")
    job.status = JobStatus.PENDING_APPROVAL
    job.reject_reason = None
    db.commit()
    return _load_job(db, job.id)


def close_job(db: Session, company: Company, job_id: int) -> Job:
    job = _get_owned_job(db, company, job_id)
    if job.status in (JobStatus.CLOSED, JobStatus.EXPIRED):
        raise ConflictError("Tin đã đóng hoặc hết hạn", code="INVALID_JOB_STATUS")
    job.status = JobStatus.CLOSED
    db.commit()
    return _load_job(db, job.id)


def list_my_jobs(db: Session, company: Company, params: PageParams, *, status: Optional[JobStatus] = None) -> dict:
    """Tin của doanh nghiệp (mọi trạng thái) kèm số lượt xem và số đơn ứng tuyển."""
    stmt = select(Job).where(Job.company_id == company.id).options(*_LIST_OPTIONS)
    if status is not None:
        stmt = stmt.where(Job.status == status)
    stmt = stmt.order_by(Job.created_at.desc(), Job.id.desc())
    result = paginate(db, stmt, params)

    job_ids = [job.id for job in result["items"]]
    counts: dict[int, int] = {}
    if job_ids:
        rows = db.execute(
            select(Application.job_id, func.count()).where(Application.job_id.in_(job_ids)).group_by(Application.job_id)
        ).all()
        counts = {job_id: total for job_id, total in rows}
    result["items"] = [
        JobMyItem.model_validate(job).model_copy(update={"application_count": counts.get(job.id, 0)})
        for job in result["items"]
    ]
    return result


def get_job_stats(db: Session, company: Company, job_id: int, *, days: int = 30) -> dict:
    """Lượt xem theo ngày (trong `days` ngày gần nhất) và số đơn theo trạng thái."""
    job = _get_owned_job(db, company, job_id)
    since = utcnow() - timedelta(days=days)
    day_col = func.date(JobView.viewed_at)
    view_rows = db.execute(
        select(day_col, func.count())
        .where(JobView.job_id == job.id, JobView.viewed_at >= since)
        .group_by(day_col)
        .order_by(day_col)
    ).all()
    status_rows = db.execute(
        select(Application.current_status, func.count())
        .where(Application.job_id == job.id)
        .group_by(Application.current_status)
    ).all()
    by_status = {status: 0 for status in ApplicationStatus}
    for status, total in status_rows:
        by_status[ApplicationStatus(status)] = total
    return {
        "job_id": job.id,
        "total_views": job.view_count,
        "total_applications": sum(by_status.values()),
        # func.date trả chuỗi trên SQLite, trả date trên MariaDB -> chuẩn hóa qua str()
        "views_by_day": [{"day": date.fromisoformat(str(day)), "views": total} for day, total in view_rows],
        "applications_by_status": by_status,
    }


# ---------------------------------------------------------------- Sinh viên: tìm kiếm và xem tin
def search_jobs(db: Session, student: Student, params: PageParams, filters: JobFilter) -> dict:
    """Tìm tin cho sinh viên: chỉ APPROVED + còn hạn; tin thuộc đợt chỉ hiện với sinh viên trong đợt đó."""
    stmt = select(Job).where(_visible_to_student(student.id)).options(*_LIST_OPTIONS)

    if filters.q:
        like = f"%{filters.q.strip()}%"
        stmt = stmt.where(or_(Job.title.ilike(like), Job.position.ilike(like), Job.description.ilike(like)))
    if filters.position:
        stmt = stmt.where(Job.position.ilike(f"%{filters.position.strip()}%"))
    if filters.location:
        stmt = stmt.where(Job.location.ilike(f"%{filters.location.strip()}%"))
    if filters.industry_id is not None:
        stmt = stmt.where(Job.industry_id == filters.industry_id)
    if filters.job_type_id is not None:
        stmt = stmt.where(Job.job_type_id == filters.job_type_id)
    if filters.work_mode is not None:
        stmt = stmt.where(Job.work_mode == filters.work_mode)
    if filters.flow == "free":
        stmt = stmt.where(Job.term_id.is_(None))
    elif filters.flow == "term":
        stmt = stmt.where(Job.term_id.is_not(None))
    if filters.major_id is not None:
        # Tin không khai báo ngành nào = mọi ngành đều được ứng tuyển
        has_any_major = exists().where(JobMajor.job_id == Job.id)
        has_this_major = exists().where(JobMajor.job_id == Job.id, JobMajor.major_id == filters.major_id)
        stmt = stmt.where(or_(~has_any_major, has_this_major))
    if filters.skill_ids:
        stmt = stmt.where(Job.id.in_(select(JobSkill.job_id).where(JobSkill.skill_id.in_(filters.skill_ids))))
    if filters.salary_from is not None:
        stmt = stmt.where(func.coalesce(Job.salary_max, Job.salary_min) >= filters.salary_from)
    if filters.salary_to is not None:
        stmt = stmt.where(func.coalesce(Job.salary_min, Job.salary_max) <= filters.salary_to)

    stmt = stmt.order_by(Job.created_at.desc(), Job.id.desc())
    return paginate(db, stmt, params)


def record_view(db: Session, job_id: int, user_id: int) -> None:
    """Ghi một dòng job_views và tăng view_count."""
    db.add(JobView(job_id=job_id, user_id=user_id))
    # Gán updated_at = chính nó để lượt xem không làm đổi "ngày cập nhật" của tin
    db.execute(
        update(Job).where(Job.id == job_id).values(view_count=Job.view_count + 1, updated_at=Job.updated_at)
    )
    db.commit()


def get_job_detail(db: Session, job_id: int, user: User) -> Job:
    """Chi tiết tin theo vai trò.

    * Sinh viên: chỉ thấy tin hợp lệ theo quy tắc hiển thị; mỗi lần xem được ghi lượt xem.
    * Doanh nghiệp: chỉ xem tin của mình (mọi trạng thái); không tính lượt xem.
    * Admin: xem mọi tin; không tính lượt xem.
    """
    job = _load_job(db, job_id)
    if job is None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")

    if user.role == UserRole.ADMIN:
        return job
    if user.role == UserRole.COMPANY:
        if user.company is None or job.company_id != user.company.id:
            raise NotFoundError("Không tìm thấy tin tuyển dụng")
        return job

    student = user.student
    if student is None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    visible = db.scalar(select(Job.id).where(Job.id == job_id, _visible_to_student(student.id)))
    if visible is None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    record_view(db, job_id, user.id)
    return _load_job(db, job_id)


# ---------------------------------------------------------------- Dùng cho module khác / job định kỳ
def list_jobs_by_term(
    db: Session, term_id: int, params: PageParams, *, status: Optional[JobStatus] = None
) -> dict:
    """Liệt kê tin thuộc một đợt thực tập (TV2 dùng cho phía nhà trường)."""
    stmt = select(Job).where(Job.term_id == term_id).options(*_LIST_OPTIONS)
    if status is not None:
        stmt = stmt.where(Job.status == status)
    stmt = stmt.order_by(Job.created_at.desc(), Job.id.desc())
    return paginate(db, stmt, params)


def expire_overdue_jobs(db: Session) -> int:
    """Chuyển tin APPROVED đã quá hạn (deadline < hôm nay) sang EXPIRED. Trả về số tin đã chuyển."""
    result = db.execute(
        update(Job).where(Job.status == JobStatus.APPROVED, Job.deadline < today()).values(status=JobStatus.EXPIRED)
    )
    db.commit()
    return result.rowcount or 0
