"""Column types for the Freelancer schema; financial amounts are integer VND."""
from sqlalchemy import DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import DATETIME

# Keep timestamps compatible with the repository's UTC datetime helpers.
UTCDateTime = DateTime().with_variant(DATETIME(fsp=6), "mysql", "mariadb")


def state_type(enum_cls, name):
    return SAEnum(
        enum_cls, values_callable=lambda e: [v.value for v in e],
        native_enum=False, create_constraint=True, validate_strings=True,
        length=40, name=name,
    )


def binary_string(length: int) -> String:
    """Opaque keys must not inherit case-insensitive MariaDB text collation."""
    return String(length).with_variant(
        String(length, collation="utf8mb4_bin"), "mysql", "mariadb"
    )
