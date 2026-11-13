"""New dependencies do not relax access checks on existing recruitment routes."""

from typing import Annotated

from fastapi import Depends

from app.core.enums import UserRole, UserStatus
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.dependencies import DbSession, oauth2_scheme, require_roles
from app.models import User


def get_onboarding_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    try:
        payload = decode_token(token, expected_type="access", db=db)
    except UnauthorizedError as exc:
        if exc.code != "TOKEN_INVALID":
            raise
        payload = decode_token(token, expected_type="onboarding", db=db)
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise UnauthorizedError("Account does not exist")
    if user.status not in (UserStatus.ACTIVE, UserStatus.PENDING_APPROVAL):
        raise ForbiddenError("Account cannot access onboarding", code="ACCOUNT_NOT_ACTIVE")
    return user


OnboardingUser = Annotated[User, Depends(get_onboarding_user)]
ClientUser = Annotated[User, Depends(require_roles(UserRole.CLIENT))]
FreelanceClientUser = Annotated[User, Depends(require_roles(UserRole.CLIENT, UserRole.COMPANY))]
