"""A2 - Quy tắc eligibility thuần cho CLIENT.

Service đọc DB -> dựng ClientFacts -> gọi evaluate_client_eligibility ->
đóng gói kết quả thành ClientEligibility (app.contracts.freelancer.types).

GIẢ ĐỊNH CẦN ĐỐI CHIẾU VỚI ĐẶC TẢ 2.2 (tôi chưa được xem mục này):
- can_draft : tài khoản hoạt động, liên hệ đã xác minh, doanh nghiệp không bị đình chỉ.
- can_submit: can_draft + có doanh nghiệp đã VERIFIED.
- can_fund  : can_submit (MOU chỉ nâng hạng/hạn mức, không là điều kiện bắt buộc).
- tier      : UNVERIFIED -> VERIFIED -> MOU.
Nếu đặc tả khác, chỉ cần sửa file này và test tương ứng.
"""
from __future__ import annotations

from dataclasses import dataclass

TIER_UNVERIFIED = "UNVERIFIED"
TIER_VERIFIED = "VERIFIED"
TIER_MOU = "MOU"

R_USER_INACTIVE = "USER_INACTIVE"
R_CONTACT_NOT_VERIFIED = "CONTACT_NOT_VERIFIED"
R_NO_COMPANY = "NO_COMPANY"
R_COMPANY_NOT_VERIFIED = "COMPANY_NOT_VERIFIED"
R_COMPANY_SUSPENDED = "COMPANY_SUSPENDED"


@dataclass(frozen=True)
class ClientFacts:
    user_id: int
    user_active: bool
    email_verified: bool
    phone_verified: bool
    company_id: int | None
    company_verified: bool = False
    company_suspended: bool = False
    mou_active: bool = False  # đã tính theo thời điểm hiện tại (xem mou_rules)


@dataclass(frozen=True)
class EligibilityDecision:
    tier: str
    can_draft: bool
    can_submit: bool
    can_fund: bool
    reason_codes: tuple[str, ...]


def evaluate_client_eligibility(facts: ClientFacts) -> EligibilityDecision:
    reasons: list[str] = []

    if not facts.user_active:
        reasons.append(R_USER_INACTIVE)
    if not (facts.email_verified and facts.phone_verified):
        reasons.append(R_CONTACT_NOT_VERIFIED)
    if facts.company_id is None:
        reasons.append(R_NO_COMPANY)
    else:
        if facts.company_suspended:
            reasons.append(R_COMPANY_SUSPENDED)
        if not facts.company_verified:
            reasons.append(R_COMPANY_NOT_VERIFIED)

    can_draft = not (
        {R_USER_INACTIVE, R_CONTACT_NOT_VERIFIED, R_COMPANY_SUSPENDED} & set(reasons)
    )
    can_submit = can_draft and facts.company_id is not None and facts.company_verified
    can_fund = can_submit

    if facts.company_suspended or facts.company_id is None or not facts.company_verified:
        tier = TIER_UNVERIFIED
    elif facts.mou_active:
        tier = TIER_MOU
    else:
        tier = TIER_VERIFIED

    return EligibilityDecision(
        tier=tier,
        can_draft=can_draft,
        can_submit=can_submit,
        can_fund=can_fund,
        reason_codes=tuple(reasons),
    )
