"""Thực tập theo đợt: đợt thực tập, danh sách sinh viên thuộc đợt, kết quả thực tập."""
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InternshipResultStatus, TermStatus
from app.models.base import Base, CreatedAtMixin, db_enum, fk, pk

if TYPE_CHECKING:
    from app.models.school import Lecturer
    from app.models.student import Student


class InternshipTerm(CreatedAtMixin, Base):
    __tablename__ = "internship_terms"

    id: Mapped[int] = pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    semester: Mapped[str] = mapped_column(String(20), nullable=False)  # vd: HK1
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)  # vd: 2025-2026
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[TermStatus] = mapped_column(
        db_enum(TermStatus), nullable=False, default=TermStatus.DRAFT, server_default=TermStatus.DRAFT.value
    )
    created_by: Mapped[int] = fk("users.id")

    students: Mapped[list["TermStudent"]] = relationship(
        back_populates="term", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_terms_year", "academic_year", "semester"),
        CheckConstraint("start_date <= end_date", name="dates"),
    )


class TermStudent(CreatedAtMixin, Base):
    """Sinh viên thuộc một đợt thực tập + giảng viên hướng dẫn."""

    __tablename__ = "term_students"

    id: Mapped[int] = pk()
    term_id: Mapped[int] = fk("internship_terms.id", ondelete="CASCADE")
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    lecturer_id: Mapped[Optional[int]] = fk("lecturers.id", ondelete="SET NULL", nullable=True)

    term: Mapped["InternshipTerm"] = relationship(back_populates="students")
    student: Mapped["Student"] = relationship()
    lecturer: Mapped[Optional["Lecturer"]] = relationship()
    result: Mapped[Optional["InternshipResult"]] = relationship(
        back_populates="term_student", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("term_id", "student_id", name="uq_term_students"),
        Index("idx_term_students_student", "student_id"),
        Index("idx_term_students_lecturer", "lecturer_id"),
    )


class InternshipResult(Base):
    """Kết quả thực tập: gắn với (sinh viên, đợt); application chỉ là liên kết tùy chọn."""

    __tablename__ = "internship_results"

    id: Mapped[int] = pk()
    term_student_id: Mapped[int] = fk("term_students.id", ondelete="CASCADE", unique=True)
    application_id: Mapped[Optional[int]] = fk("applications.id", ondelete="SET NULL", nullable=True)
    company_id: Mapped[Optional[int]] = fk("companies.id", ondelete="SET NULL", nullable=True)
    company_evaluation: Mapped[Optional[str]] = mapped_column(Text)
    company_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    lecturer_comment: Mapped[Optional[str]] = mapped_column(Text)
    lecturer_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    result: Mapped[InternshipResultStatus] = mapped_column(
        db_enum(InternshipResultStatus),
        nullable=False,
        default=InternshipResultStatus.PENDING,
        server_default=InternshipResultStatus.PENDING.value,
    )
    confirmed_by: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    term_student: Mapped["TermStudent"] = relationship(back_populates="result")

    __table_args__ = (Index("idx_ir_company", "company_id"),)
