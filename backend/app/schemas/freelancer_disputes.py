from pydantic import Field

from app.core.freelancer_enums import CancellationBasis, DisputeOutcome, HoldReason
from app.schemas.freelance_projects import Input
from app.schemas.freelancer_common import EntityId, MoneyVnd


class CancellationCreate(Input):
    basis: CancellationBasis
    reason: str = Field(min_length=1, max_length=10000)
    freelancer_gross: MoneyVnd
    refund_amount: MoneyVnd


class HashConfirm(Input):
    content_hash: str = Field(min_length=64, max_length=64)


class Reason(Input):
    reason: str = Field(min_length=1, max_length=10000)


class DisputeCreate(Input):
    reason_code: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=20000)


class EvidenceCreate(Input):
    file_id: EntityId | None = None
    deliverable_id: EntityId | None = None
    note: str | None = Field(default=None, min_length=1, max_length=20000)


class DecisionCreate(Input):
    outcome: DisputeOutcome
    freelancer_gross: MoneyVnd
    refund_amount: MoneyVnd
    reason: str = Field(min_length=1, max_length=10000)


class HoldCreate(Input):
    reason_type: HoldReason = HoldReason.ADMIN_REVIEW
    reason_key: str = Field(min_length=1, max_length=150)
    note: str = Field(min_length=1, max_length=10000)


class Assignment(Input):
    admin_id: EntityId
