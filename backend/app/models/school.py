"""Phía nhà trường: quản trị viên, giảng viên, lịch sử import dữ liệu."""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ImportType
from app.models.base import Base, CreatedAtMixin, UInt, db_enum, fk, pk
from app.models.catalog import Faculty

if TYPE_CHECKING:
    from app.models.user import User


class Admin(Base):
    """Hồ sơ cán bộ nhà trường (user.role = ADMIN)."""

    __tablename__ = "admins"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE", unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty_id: Mapped[Optional[int]] = fk("faculties.id", nullable=True)  # NULL = quản trị toàn trường
    position: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    user: Mapped["User"] = relationship(back_populates="admin")
    faculty: Mapped[Optional["Faculty"]] = relationship()


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[int] = pk()
    code: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty_id: Mapped[int] = fk("faculties.id")
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="1")

    faculty: Mapped["Faculty"] = relationship()

    __table_args__ = (Index("idx_lecturers_faculty", "faculty_id"),)


class ImportBatch(CreatedAtMixin, Base):
    """Mỗi lần import/đồng bộ dữ liệu từ nhà trường."""

    __tablename__ = "import_batches"

    id: Mapped[int] = pk()
    type: Mapped[ImportType] = mapped_column(db_enum(ImportType), nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    total_rows: Mapped[int] = mapped_column(UInt, nullable=False, default=0, server_default="0")
    success_rows: Mapped[int] = mapped_column(UInt, nullable=False, default=0, server_default="0")
    failed_rows: Mapped[int] = mapped_column(UInt, nullable=False, default=0, server_default="0")
    error_report: Mapped[Optional[dict]] = mapped_column(JSON)  # danh sách dòng lỗi + lý do
    imported_by: Mapped[int] = fk("users.id")

    __table_args__ = (Index("idx_import_batches_user", "imported_by"),)

