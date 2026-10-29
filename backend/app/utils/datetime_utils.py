"""Thời gian: toàn hệ thống lưu UTC, naive datetime trong DB."""
from datetime import date, datetime, timezone


def utcnow() -> datetime:
    """UTC hiện tại, không kèm tzinfo (khớp cột DATETIME của MariaDB)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def today() -> date:
    return utcnow().date()
