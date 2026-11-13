"""Validated request contracts mapped to the shared Freelancer schema."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.freelancer_enums import MouSignatureMethod, VerificationChannel, VerificationPurpose
from app.schemas.freelancer_common import EntityId, MoneyVnd
from app.schemas.terms import TermsAcceptance

Text = Annotated[str, Field(min_length=1, max_length=255)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OtpRequestSchema(Input):
    identifier: Text
    channel: Literal[VerificationChannel.EMAIL] = VerificationChannel.EMAIL
    purpose: VerificationPurpose = VerificationPurpose.VERIFY_CONTACT


class OtpVerifySchema(OtpRequestSchema):
    code: str = Field(pattern=r"^[0-9]{6}$")



class MouAgreementSchema(Input):
    company_id: EntityId
    mou_code: str = Field(min_length=1, max_length=100)
    document_file_id: EntityId
    school_name: Text
    school_signer_name: Text
    company_signer_name: Text
    school_signer_position: str = Field(min_length=1, max_length=100)
    company_signer_position: str = Field(min_length=1, max_length=100)
    school_authority_file_id: EntityId | None = None
    company_authority_file_id: EntityId | None = None
    signature_method: MouSignatureMethod = MouSignatureMethod.SCANNED_SIGNED_DOCUMENT
    signed_at: datetime
    effective_from: datetime
    effective_until: datetime
    scope_json: dict = Field(min_length=1)


class RegisterClient(Input):
    terms_acceptance: TermsAcceptance
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    phone: str | None = Field(default=None, pattern=r"^\+[1-9][0-9]{7,14}$")
    full_name: Text
    address: str | None = Field(default=None, max_length=500)


class ClientProfileUpdate(Input):
    full_name: Text
    address: str | None = Field(default=None, max_length=500)


class ContactChange(Input):
    password: str
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^\+[1-9][0-9]{7,14}$")



class MouReview(Input):
    reason: str = Field(default="", max_length=2000)
    school_authority_checked: bool = False
    company_authority_checked: bool = False
    signed_document_checked: bool = False


class CompanyLimitUpdate(Input):
    max_open_projects: int = Field(ge=1, le=1000)
    max_project_amount: MoneyVnd
    max_daily_funding: MoneyVnd
    full_prefunding_required: bool = True
    reason: str = Field(min_length=1, max_length=2000)
