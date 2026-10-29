"""Nghiệp vụ: Quản lý ứng viên (Kanban). Người phụ trách: Khôi."""
from datetime import date
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import ApplicationStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import Application, ApplicationStatusLog, Company, Job, Student
from app.schemas.common import PageParams
from app.services.email_service import queue_email
from app.services.notification_service import create_notification
from app.utils.pagination import paginate

# Quy tắc chuyển trạng thái hợp lệ
_VALID_TRANSITIONS = {
    ApplicationStatus.APPLIED: {ApplicationStatus.SCREENING, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN},
    ApplicationStatus.SCREENING: {ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN},
    ApplicationStatus.SHORTLISTED: {ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN},
    ApplicationStatus.INTERVIEW: {ApplicationStatus.OFFER, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN},
    ApplicationStatus.OFFER: {ApplicationStatus.HIRED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN},
}


def _get_owned_application(db: Session, company: Company, application_id: int) -> Application:
    stmt = (
        select(Application)
        .join(Application.job)
        .where(Application.id == application_id, Job.company_id == company.id)
        .options(
            selectinload(Application.job),
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.profile),
            selectinload(Application.student).selectinload(Student.experiences),
            selectinload(Application.student).selectinload(Student.skills),
            selectinload(Application.cv),
            selectinload(Application.status_logs),
        )
    )
    app = db.scalars(stmt).first()
    if not app:
        raise NotFoundError("Không tìm thấy đơn ứng tuyển thuộc tin của doanh nghiệp")
    return app


def list_applications(
    db: Session,
    company: Company,
    job_id: int,
    params: PageParams,
    status: Optional[ApplicationStatus] = None,
    major_id: Optional[int] = None,
    min_gpa: Optional[float] = None,
    skill_id: Optional[int] = None,
    min_experience_months: Optional[int] = None,
) -> dict:
    """Danh sách đơn theo job_id; lọc ngành, GPA, kỹ năng, kinh nghiệm; hỗ trợ Kanban."""
    job = db.get(Job, job_id)
    if not job or job.company_id != company.id:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")

    stmt = (
        select(Application)
        .join(Application.student)
        .where(Application.job_id == job_id)
        .options(
            selectinload(Application.student).selectinload(Student.user),
            selectinload(Application.student).selectinload(Student.major),
            selectinload(Application.student).selectinload(Student.profile),
            selectinload(Application.student).selectinload(Student.experiences),
            selectinload(Application.student).selectinload(Student.skills),
            selectinload(Application.cv),
        )
    )

    if status is not None:
        stmt = stmt.where(Application.current_status == status)
    if major_id is not None:
        stmt = stmt.where(Student.major_id == major_id)
    if min_gpa is not None:
        stmt = stmt.where(Student.gpa >= min_gpa)
    if skill_id is not None:
        from app.models import StudentSkill
        stmt = stmt.where(Application.student_id.in_(select(StudentSkill.student_id).where(StudentSkill.skill_id == skill_id)))

    stmt = stmt.order_by(Application.applied_at.desc())
    result = paginate(db, stmt, params)

    if min_experience_months is not None or "items" in result:
        today = date.today()
        filtered_items = []
        
        for app in result.get("items", []):
            student = app.student
            total_exp = 0
            if hasattr(student, "experiences") and student.experiences:
                for exp in student.experiences:
                    if getattr(exp, "start_date", None):
                        end = getattr(exp, "end_date", None) or today
                        total_exp += max(0, (end.year - exp.start_date.year) * 12 + (end.month - exp.start_date.month))
            
            if min_experience_months is not None and total_exp < min_experience_months:
                continue
                
            filtered_items.append(app)
            
        if min_experience_months is not None:
            result["items"] = filtered_items
            result["total"] = len(filtered_items)

    return result


def get_application(db: Session, company: Company, application_id: int) -> Application:
    return _get_owned_application(db, company, application_id)


def log_status_change(
    db: Session,
    background_tasks: BackgroundTasks,
    company: Company,
    application_id: int,
    new_status: ApplicationStatus,
    note: Optional[str] = None,
) -> Application:
    app = _get_owned_application(db, company, application_id)
    old_status = app.current_status

    if old_status in (ApplicationStatus.HIRED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN):
        raise ConflictError("Đơn đã ở trạng thái kết thúc, không thể thay đổi", code="APPLICATION_CLOSED")

    if new_status != old_status:
        allowed = _VALID_TRANSITIONS.get(old_status, set())
        if new_status != ApplicationStatus.REJECTED and new_status not in allowed:
            raise BadRequestError(f"Không thể chuyển trạng thái từ {old_status.value} sang {new_status.value}")

    app.current_status = new_status

    status_log = ApplicationStatusLog(
        application_id=app.id,
        old_status=old_status.value if isinstance(old_status, ApplicationStatus) else old_status,
        new_status=new_status.value if isinstance(new_status, ApplicationStatus) else new_status,
        changed_by=company.user_id,
        note=note,
    )
    db.add(status_log)
    db.commit()
    db.refresh(app)

    student_user = app.student.user
    if student_user:
        title = "Cập nhật trạng thái đơn ứng tuyển"
        content = f"Đơn ứng tuyển vào vị trí '{app.job.title}' đã chuyển sang trạng thái: {new_status.value}."
        if note:
            content += f" Ghi chú: {note}"

        create_notification(
            db,
            user_id=student_user.id,
            type="APPLICATION_STATUS",
            title=title,
            content=content,
            ref_type="APPLICATION",
            ref_id=app.id,
        )

        email_body = f"<p>Xin chào {app.student.full_name},</p><p>{content}</p>"
        queue_email(
            db,
            background_tasks,
            to_email=student_user.email,
            subject="Cập nhật trạng thái đơn ứng tuyển",
            body_html=email_body,
            type="STATUS_CHANGED",
            user_id=student_user.id,
            ref_type="APPLICATION",
            ref_id=app.id,
        )

    return app


def get_history(db: Session, company: Company, application_id: int) -> list[ApplicationStatusLog]:
    app = _get_owned_application(db, company, application_id)
    return app.status_logs