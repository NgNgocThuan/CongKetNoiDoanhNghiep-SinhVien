from fastapi import APIRouter
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.dependencies import DbSession
from app.dependencies_freelancer import OnboardingUser
from app.schemas.freelancer_accounts import MouAgreementSchema
from app.services.freelancer_accounts.identity_service import submit_mou_in_tx
from app.services.freelancer_commands import run_command

router = APIRouter(prefix="/mou-agreements", tags=["Freelancer onboarding"])


@router.post("/", status_code=201)
def submit(payload: MouAgreementSchema, current_user: OnboardingUser, db: DbSession):
    try:
        return run_command(
            db, lambda: submit_mou_in_tx(db, user_id=current_user.id, payload=payload)
        )
    except IntegrityError:
        raise ConflictError("Submission conflicts with existing records") from None
