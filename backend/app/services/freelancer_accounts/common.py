from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any


def as_naive_utc(dt: datetime | None) -> datetime | None:
    """Chuyển đổi datetime sang dạng naive UTC để so sánh an toàn."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def enum_value(val: Any) -> Any:
    """Trích xuất giá trị nguyên thủy từ Enum nếu có, ngược lại giữ nguyên."""
    if isinstance(val, Enum):
        return val.value
    return val