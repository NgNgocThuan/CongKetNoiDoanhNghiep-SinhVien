"""A4 - Quy tắc MOU thuần: hiệu lực theo thời điểm, kiểm tra thời hạn, mốc nhắc hạn.

MOU hết hạn chỉ làm policy hạng về VERIFIED; hợp đồng/funding đã có không bị
ảnh hưởng (việc đó nằm ngoài module này, module chỉ trả kết quả đọc).

Trạng thái lưu trong DB (approved_by_admin) được truyền vào dưới dạng bool để
module không phụ thuộc enum chưa xem. Service ánh xạ enum thật -> bool.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Collection

from .time_utils import ensure_utc


class MouPhase(str, Enum):
    NOT_APPROVED = "NOT_APPROVED"  # chưa được Admin duyệt (hoặc bị từ chối/thu hồi)
    NOT_STARTED = "NOT_STARTED"    # đã duyệt nhưng chưa tới ngày hiệu lực
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class MouSnapshot:
    approved: bool
    effective_from: datetime
    effective_until: datetime  # thời điểm hết hạn, không bao gồm (>= là hết hạn)


@dataclass(frozen=True)
class MouEvaluation:
    phase: MouPhase
    is_active: bool
    seconds_remaining: int | None  # chỉ có khi ACTIVE


class MouValidationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def evaluate_mou(snapshot: MouSnapshot, now_utc: datetime) -> MouEvaluation:
    now = ensure_utc(now_utc)
    start = ensure_utc(snapshot.effective_from)
    end = ensure_utc(snapshot.effective_until)

    if not snapshot.approved:
        return MouEvaluation(MouPhase.NOT_APPROVED, False, None)
    if now < start:
        return MouEvaluation(MouPhase.NOT_STARTED, False, None)
    if now >= end:
        return MouEvaluation(MouPhase.EXPIRED, False, None)
    return MouEvaluation(MouPhase.ACTIVE, True, int((end - now).total_seconds()))


def validate_mou_period(
    effective_from: datetime,
    effective_until: datetime,
    now_utc: datetime,
    *,
    max_term_days: int = 5 * 365,
    allow_backdate_days: int = 0,
) -> None:
    """Kiểm tra thời hạn MOU khi nộp/duyệt. Ném MouValidationError.

    max_term_days và allow_backdate_days là mặc định tạm; chỉnh theo đặc tả.
    """
    start = ensure_utc(effective_from)
    end = ensure_utc(effective_until)
    now = ensure_utc(now_utc)

    if end <= start:
        raise MouValidationError("MOU_PERIOD_INVALID", "Ngày hết hạn phải sau ngày hiệu lực.")
    if end <= now:
        raise MouValidationError("MOU_ALREADY_EXPIRED", "MOU đã hết hạn tại thời điểm nộp.")
    if start < now - timedelta(days=allow_backdate_days):
        raise MouValidationError("MOU_BACKDATED", "Ngày hiệu lực không được lùi quá giới hạn cho phép.")
    if end - start > timedelta(days=max_term_days):
        raise MouValidationError("MOU_TERM_TOO_LONG", "Thời hạn MOU vượt quá giới hạn cho phép.")


def next_reminder_threshold(
    snapshot: MouSnapshot,
    now_utc: datetime,
    already_sent_days: Collection[int],
    thresholds_days: tuple[int, ...] = (30, 14, 7, 1),
) -> int | None:
    """Mốc nhắc (số ngày còn lại) cần gửi bây giờ, hoặc None.

    Chỉ nhắc khi MOU đang ACTIVE. Nếu đã trễ nhiều mốc thì gửi mốc gần hạn nhất
    chưa gửi (không dồn nhiều email một lúc). Mỗi mốc gửi tối đa một lần.
    """
    evaluation = evaluate_mou(snapshot, now_utc)
    if not evaluation.is_active or evaluation.seconds_remaining is None:
        return None

    remaining = timedelta(seconds=evaluation.seconds_remaining)
    reached = [d for d in thresholds_days if remaining <= timedelta(days=d)]
    if not reached:
        return None
    candidate = min(reached)  # mốc nhỏ nhất đã chạm = gần hạn nhất
    return candidate if candidate not in already_sent_days else None
