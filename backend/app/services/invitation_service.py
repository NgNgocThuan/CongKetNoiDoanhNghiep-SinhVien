"""Nghiệp vụ: Lời mời ứng tuyển. Người phụ trách: Khôi."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core.enums import InvitationStatus
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import Company, Invitation, Job, Student
from app.schemas.common import PageParams
from app.services.email_service import queue_email
from app.services.notification_service import create_notification
from app.utils.pagination import paginate


def send_invitation(
    db: Session,
    background_tasks: BackgroundTasks,
    company: Company,
    job_id: int,
    student_id: int,
    message: Optional[str] = None,
) -> Invitation:
    """Doanh nghiệp mời sinh viên (chỉ mời sinh viên có profile.is_open_to_work = True)."""
    job = db.get(Job, job_id)
    if not job or job.company_id != company.id:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")

    # Load sinh viên kèm theo profile
    stmt = select(Student).where(Student.id == student_id).options(selectinload(Student.profile))
    student = db.scalars(stmt).first()
    if not student:
        raise NotFoundError("Không tìm thấy hồ sơ sinh viên")

    # Kiểm tra profile và trạng thái tìm việc
    if not student.profile or not student.profile.show_contact and not getattr(student.profile, "is_open_to_work", True):
        # Kiểm tra chuẩn biến is_open_to_work nằm trong StudentProfile
        pass

    if not student.profile or not getattr(student.profile, "is_open_to_work", False):
        raise BadRequestError("Sinh viên hiện không bật trạng thái tìm việc (is_open_to_work)")

    existing = db.scalar(select(Invitation).where(Invitation.job_id == job_id, Invitation.student_id == student_id))
    if existing:
        raise ConflictError("Đã gửi lời mời cho sinh viên này với tin tuyển dụng này rồi", code="DUPLICATE_INVITATION")

    invitation = Invitation(
        job_id=job_id,
        student_id=student_id,
        company_id=company.id,
        message=message,
        status=InvitationStatus.PENDING,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    student_user = student.user
    if student_user:
        title = f"Lời mời ứng tuyển từ {company.name}"
        content = f"Công ty {company.name} mời bạn ứng tuyển vị trí: {job.title}."
        if message:
            content += f" Lời nhắn: {message}"

        create_notification(
            db,
            user_id=student_user.id,
            type="INVITATION",
            title=title,
            content=content,
            ref_type="INVITATION",
            ref_id=invitation.id,
        )

        email_body = f"<p>Xin chào {student.full_name},</p><p>{content}</p>"
        queue_email(
            db,
            background_tasks,
            to_email=student_user.email,
            subject="Lời mời ứng tuyển việc làm",
            body_html=email_body,
            type="INVITATION",
            user_id=student_user.id,
            ref_type="INVITATION",
            ref_id=invitation.id,
        )

    return invitation


def list_for_company(db: Session, company: Company, params: PageParams) -> dict:
    stmt = select(Invitation).where(Invitation.company_id == company.id).order_by(Invitation.created_at.desc())
    return paginate(db, stmt, params)


def list_for_student(db: Session, student: Student, params: PageParams) -> dict:
    stmt = select(Invitation).where(Invitation.student_id == student.id).order_by(Invitation.created_at.desc())
    return paginate(db, stmt, params)


def decline(db: Session, student: Student, invitation_id: int) -> Invitation:
    invitation = db.get(Invitation, invitation_id)
    if not invitation or invitation.student_id != student.id:
        raise NotFoundError("Không tìm thấy lời mời ứng tuyển")

    if invitation.status != InvitationStatus.PENDING:
        raise ConflictError("Lời mời đã được xử lý trước đó", code="INVITATION_PROCESSED")

    invitation.status = InvitationStatus.DECLINED
    invitation.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(invitation)
    return invitation


def expire_old_invitations(db: Session) -> int:
    """Hết hạn các lời mời cũ quá hạn (nếu cần chạy định kỳ)."""
    threshold = datetime.utcnow() - timedelta(days=30)
    result = db.execute(
        update(Invitation)
        .where(Invitation.status == InvitationStatus.PENDING, Invitation.created_at < threshold)
        .values(status=InvitationStatus.EXPIRED)
    )
    db.commit()
    return result.rowcount or 0