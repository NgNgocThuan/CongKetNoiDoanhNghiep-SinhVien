"""Sinh viên.

Phân biệt rõ hai nguồn dữ liệu:
  * Dữ liệu CHÍNH THỨC từ nhà trường (chỉ đọc với sinh viên): Student, StudentAchievement,
    StudentCertificate(source=SCHOOL).
  * Dữ liệu TỰ KHAI: StudentProfile, StudentExperience, StudentProject, StudentCertificate(source=SELF),
    StudentSkill(source=SELF/CV_AI).
"""
from datetime import date, datetime
from decimal import Decimal
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

from app.core.enums import AchievementType, CertificateSource, CVType, SkillLevel, SkillSource
from app.models.base import ID, Base, LongText, TimestampMixin, db_enum, fk, pk
from app.models.catalog import Faculty, Major, Skill

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.user import User


class Student(TimestampMixin, Base):
    """Dữ liệu chính thức từ nhà trường."""

    __tablename__ = "students"

    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE", unique=True)
    student_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    class_name: Mapped[Optional[str]] = mapped_column(String(50))
    faculty_id: Mapped[int] = fk("faculties.id")
    major_id: Mapped[int] = fk("majors.id")
    cohort: Mapped[str] = mapped_column(String(20), nullable=False)  # khóa học, vd: K65
    gpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    academic_result: Mapped[Optional[str]] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    import_batch_id: Mapped[Optional[int]] = fk("import_batches.id", ondelete="SET NULL", nullable=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    user: Mapped["User"] = relationship(back_populates="student")
    faculty: Mapped["Faculty"] = relationship()
    major: Mapped["Major"] = relationship()
    profile: Mapped[Optional["StudentProfile"]] = relationship(
        back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
    skills: Mapped[list["StudentSkill"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    experiences: Mapped[list["StudentExperience"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    projects: Mapped[list["StudentProject"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    certificates: Mapped[list["StudentCertificate"]] = relationship(
        back_populates="student", cascade="all, delete-orphan", foreign_keys="StudentCertificate.student_id"
    )
    achievements: Mapped[list["StudentAchievement"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    cvs: Mapped[list["CV"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")

    __table_args__ = (
        Index("idx_students_faculty_major", "faculty_id", "major_id"),
        Index("idx_students_cohort", "cohort"),
        CheckConstraint("gpa IS NULL OR (gpa >= 0 AND gpa <= 4)", name="gpa_range"),
    )


class StudentAchievement(Base):
    """Nghiên cứu khoa học, thành tích do nhà trường xác nhận."""

    __tablename__ = "student_achievements"

    id: Mapped[int] = pk()
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    type: Mapped[AchievementType] = mapped_column(db_enum(AchievementType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    achieved_at: Mapped[Optional[date]] = mapped_column(Date)
    import_batch_id: Mapped[Optional[int]] = fk("import_batches.id", ondelete="SET NULL", nullable=True)

    student: Mapped["Student"] = relationship(back_populates="achievements")

    __table_args__ = (Index("idx_sach_student", "student_id"),)


class StudentProfile(Base):
    """Dữ liệu tự khai + cài đặt quyền riêng tư (cho gợi ý ứng viên)."""

    __tablename__ = "student_profiles"

    student_id: Mapped[int] = mapped_column(
        ID, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True, autoincrement=False
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    career_goal: Mapped[Optional[str]] = mapped_column(Text)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    github_url: Mapped[Optional[str]] = mapped_column(String(500))
    # Quyền riêng tư
    is_open_to_work: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    show_gpa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    show_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    show_achievements: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="profile")


class StudentSkill(Base):
    __tablename__ = "student_skills"

    student_id: Mapped[int] = mapped_column(
        ID, ForeignKey("students.id", ondelete="CASCADE"), primary_key=True, autoincrement=False
    )
    skill_id: Mapped[int] = mapped_column(
        ID, ForeignKey("skills.id"), primary_key=True, autoincrement=False
    )
    level: Mapped[SkillLevel] = mapped_column(
        db_enum(SkillLevel), nullable=False, default=SkillLevel.BEGINNER, server_default=SkillLevel.BEGINNER.value
    )
    source: Mapped[SkillSource] = mapped_column(
        db_enum(SkillSource), nullable=False, default=SkillSource.SELF, server_default=SkillSource.SELF.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    student: Mapped["Student"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship()

    __table_args__ = (Index("idx_sskills_skill", "skill_id"),)


class StudentExperience(Base):
    __tablename__ = "student_experiences"

    id: Mapped[int] = pk()
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)

    student: Mapped["Student"] = relationship(back_populates="experiences")

    __table_args__ = (Index("idx_sexp_student", "student_id"),)


class StudentProject(Base):
    __tablename__ = "student_projects"

    id: Mapped[int] = pk()
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    tech_stack: Mapped[Optional[str]] = mapped_column(String(500))
    project_url: Mapped[Optional[str]] = mapped_column(String(500))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    student: Mapped["Student"] = relationship(back_populates="projects")

    __table_args__ = (Index("idx_sproj_student", "student_id"),)


class StudentCertificate(Base):
    """source=SCHOOL: do trường xác nhận; source=SELF: sinh viên tự khai (is_verified để trường duyệt)."""

    __tablename__ = "student_certificates"

    id: Mapped[int] = pk()
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[Optional[str]] = mapped_column(String(255))
    issued_at: Mapped[Optional[date]] = mapped_column(Date)
    expires_at: Mapped[Optional[date]] = mapped_column(Date)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500))
    source: Mapped[CertificateSource] = mapped_column(
        db_enum(CertificateSource),
        nullable=False,
        default=CertificateSource.SELF,
        server_default=CertificateSource.SELF.value,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    verified_by: Mapped[Optional[int]] = fk("users.id", ondelete="SET NULL", nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    student: Mapped["Student"] = relationship(back_populates="certificates", foreign_keys=[student_id])

    __table_args__ = (Index("idx_scert_student", "student_id"),)


class CV(TimestampMixin, Base):
    __tablename__ = "cvs"

    id: Mapped[int] = pk()
    student_id: Mapped[int] = fk("students.id", ondelete="CASCADE")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[CVType] = mapped_column(db_enum(CVType), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))  # UPLOADED: bắt buộc (PDF/DOCX)
    content_json: Mapped[Optional[dict]] = mapped_column(JSON)  # nội dung CV tạo trực tuyến
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    # Kết quả phân tích AI (cache, không gọi lại API nếu content_hash không đổi)
    extracted_text: Mapped[Optional[str]] = mapped_column(LongText)
    parsed_json: Mapped[Optional[dict]] = mapped_column(JSON)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)  # xóa mềm

    student: Mapped["Student"] = relationship(back_populates="cvs")

    __table_args__ = (Index("idx_cvs_student", "student_id", "is_default"),)

