"""Lời mời ứng tuyển. Người phụ trách: Khôi."""
from fastapi import APIRouter, BackgroundTasks

from app.dependencies import CurrentCompany, CurrentStudent, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.invitations import InvitationCreate, InvitationRead
from app.services import invitation_service

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post("", response_model=InvitationRead, status_code=201, summary="Doanh nghiệp mời sinh viên ứng tuyển")
def send_invitation(
    data: InvitationCreate,
    db: DbSession,
    company: CurrentCompany,
    background_tasks: BackgroundTasks,
):
    return invitation_service.send_invitation(
        db, background_tasks, company, data.job_id, data.student_id, data.message
    )


@router.get("/company", response_model=Page[InvitationRead], summary="Danh sách lời mời đã gửi (Doanh nghiệp)")
def list_company_invitations(db: DbSession, company: CurrentCompany, pagination: Pagination):
    return invitation_service.list_for_company(db, company, pagination)


@router.get("/me", response_model=Page[InvitationRead], summary="Danh sách lời mời nhận được (Sinh viên)")
def list_my_invitations(db: DbSession, student: CurrentStudent, pagination: Pagination):
    return invitation_service.list_for_student(db, student, pagination)


@router.post("/{invitation_id}/decline", response_model=InvitationRead, summary="Sinh viên từ chối lời mời")
def decline_invitation(invitation_id: int, db: DbSession, student: CurrentStudent):
    return invitation_service.decline(db, student, invitation_id)