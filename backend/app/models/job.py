"""Tin tuyển dụng và dữ liệu đi kèm (kỹ năng, ngành yêu cầu, lượt xem, tin đã lưu).

Luồng tuyển dụng suy ra từ term_id:  NULL = ứng tuyển tự do;  có giá trị = thuộc đợt thực tập.
Chỉ tin status=APPROVED mới hiển thị cho sinh viên.

Lưu ý: chỉ mục FULLTEXT (title, position, description) không khai báo ở model; thêm bằng
migration:  op.execute("ALTER TABLE jobs ADD FULLTEXT ft_jobs_search (title, position, description)")
"""
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    false,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import JobStatus, WorkMode
from app.models.base import ID, Base, LongText, TimestampMixin, UInt, USmallInt, db_enum, fk, pk
from app.models.catalog import Industry, JobType, Major, Skill

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.company import Company
    from app.models.internship import InternshipTerm


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[int] = pk()
    company_id: Mapped[int] = fk("companies.id", ondelete="CASCADE")
    term_id: Mapped[Optional[int]] = fk("internship_terms.id", ondelete="SET NULL", nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    job_type_id: Mapped[int] = fk("job_types.id")
    industry_id: Mapped[Optional[int]] = fk("industries.id", nullable=True)
    description: Mapped[str] = mapped_column(LongText, nullable=False)
    requirements: Mapped[Optional[str]] = mapped_column(LongText)
    benefits: Mapped[Optional[str]] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(UInt, nullable=False, default=1, server_default="1")
    salary_min: Mapped[Optional[int]] = mapped_column(UInt)
    salary_max: Mapped[Optional[int]] = mapped_column(UInt)
    is_salary_negotiable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    location: Mapped[Optional[str]] = mapped_column(String(255))
    work_mode: Mapped[WorkMode] = mapped_column(
        db_enum(WorkMode), nullable=False, default=WorkMode.ONSITE, server_default=WorkMode.ONSITE.value
    )
    min_gpa: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    min_experience_months: Mapped[Optional[int]] = mapped_column(USmallInt)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        db_enum(JobStatus), nullable=False, default=JobStatus.DRAFT, server_default=JobStatus.DRAFT.value
    )
    approved_by: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reject_reason: Mapped[Optional[str]] = mapped_column(String(500))
    view_count: Mapped[int] = mapped_column(UInt, nullable=False, default=0, server_default="0")
    # Kết quả phân tích AI (cache)
    parsed_json: Mapped[Optional[dict]] = mapped_column(JSON)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    company: Mapped["Company"] = relationship(back_populates="jobs")
    term: Mapped[Optional["InternshipTerm"]] = relationship()
    job_type: Mapped["JobType"] = relationship()
    industry: Mapped[Optional["Industry"]] = relationship()
    skills: Mapped[list["JobSkill"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    majors: Mapped[list["JobMajor"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")

    __table_args__ = (
        Index("idx_jobs_company", "company_id"),
        Index("idx_jobs_term", "term_id"),
        Index("idx_jobs_status_deadline", "status", "deadline"),
        Index("idx_jobs_type", "job_type_id"),
        Index("idx_jobs_industry", "industry_id"),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max", name="salary_range"
        ),
        CheckConstraint("min_gpa IS NULL OR (min_gpa >= 0 AND min_gpa <= 4)", name="gpa_range"),
    )


class JobMajor(Base):
    """Ngành học được phép ứng tuyển. Không có dòng nào = mọi ngành."""

    __tablename__ = "job_majors"

    job_id: Mapped[int] = mapped_column(
        ID, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True, autoincrement=False
    )
    major_id: Mapped[int] = mapped_column(
        ID, ForeignKey("majors.id"), primary_key=True, autoincrement=False
    )

    job: Mapped["Job"] = relationship(back_populates="majors")
    major: Mapped["Major"] = relationship()

    __table_args__ = (Index("idx_job_majors_major", "major_id"),)


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[int] = mapped_column(
        ID, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True, autoincrement=False
    )
    skill_id: Mapped[int] = mapped_column(
        ID, ForeignKey("skills.id"), primary_key=True, autoincrement=False
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    job: Mapped["Job"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship()

    __table_args__ = (Index("idx_job_skills_skill", "skill_id"),)


class JobView(Base):
    __tablename__ = "job_views"

    id: Mapped[int] = pk()
    job_id: Mapped[int] = fk("jobs.id", ondelete="CASCADE")
    user_id: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (Index("idx_job_views_job_time", "job_id", "viewed_at"),)


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    student_id: Mapped[int] = mapped_column(
        ID, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True, autoincrement=False
    )
    job_id: Mapped[int] = mapped_column(
        ID, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True, autoincrement=False
    )
    saved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (Index("idx_saved_jobs_job", "job_id"),)
