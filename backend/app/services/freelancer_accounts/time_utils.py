"""Chuẩn hóa datetime: nội bộ luôn là UTC aware khi so sánh.

MariaDB có thể trả naive UTC; không được so sánh naive với aware.
Nếu repo đã có helper chung, thay thế hàm này bằng helper đó.
"""
from __future__ import annotations

from datetime import datetime, timezone


def ensure_utc(value: datetime) -> datetime:
    """Naive được coi là UTC; aware được đổi sang UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
