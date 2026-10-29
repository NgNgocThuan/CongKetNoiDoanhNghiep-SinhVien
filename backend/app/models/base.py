"""Base declarative, kiểu dữ liệu dùng chung, mixin và helper cho toàn bộ models.

Quy ước:
  * Mỗi domain một file (user.py, student.py, job.py, ...). Model CHỈ mô tả bảng + quan hệ,
    không chứa nghiệp vụ (nghiệp vụ nằm ở app/services).
  * Khóa chính dùng `pk()`, khóa ngoại dùng `fk()` để kiểu BIGINT UNSIGNED luôn khớp nhau.
  * Enum dùng `db_enum(EnumClass)` với enum khai báo ở app/core/enums.py.
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, MetaData, SmallInteger, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, MEDIUMTEXT, SMALLINT, TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column

# Đặt tên constraint ổn định để Alembic sinh migration nhất quán
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

_MYSQL = ("mysql", "mariadb")

# BIGINT UNSIGNED trên MariaDB; INTEGER trên SQLite (để chạy test với autoincrement)
ID = BigInteger().with_variant(BIGINT(unsigned=True), *_MYSQL).with_variant(Integer(), "sqlite")
UInt = Integer().with_variant(INTEGER(unsigned=True), *_MYSQL)
USmallInt = SmallInteger().with_variant(SMALLINT(unsigned=True), *_MYSQL)
UTinyInt = SmallInteger().with_variant(TINYINT(unsigned=True), *_MYSQL)
LongText = Text().with_variant(MEDIUMTEXT(), *_MYSQL)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def pk() -> MappedColumn:
    return mapped_column(ID, primary_key=True, autoincrement=True)


def fk(
    target: str, *, ondelete: str | None = None, nullable: bool = False, unique: bool = False
) -> MappedColumn:
    """Cột khóa ngoại. target dạng "users.id"."""
    return mapped_column(ID, ForeignKey(target, ondelete=ondelete), nullable=nullable, unique=unique)


def db_enum(enum_cls: type) -> SAEnum:
    """ENUM native của MariaDB, lưu theo *value* của enum Python."""
    return SAEnum(
        enum_cls,
        values_callable=lambda e: [m.value for m in e],
        native_enum=True,
        validate_strings=True,
        name=enum_cls.__name__.lower(),
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
