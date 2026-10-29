"""Danh mục dùng chung: khoa, ngành, lĩnh vực, loại hình công việc, kỹ năng."""
from typing import Optional

from sqlalchemy import Boolean, Index, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, fk, pk


class Faculty(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = pk()
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    majors: Mapped[list["Major"]] = relationship(back_populates="faculty")


class Major(Base):
    __tablename__ = "majors"

    id: Mapped[int] = pk()
    faculty_id: Mapped[int] = fk("faculties.id")
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    faculty: Mapped["Faculty"] = relationship(back_populates="majors")

    __table_args__ = (Index("idx_majors_faculty", "faculty_id"),)


class Industry(Base):
    """Lĩnh vực / ngành nghề tuyển dụng."""

    __tablename__ = "industries"

    id: Mapped[int] = pk()
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


class JobType(Base):
    """Loại hình công việc: INTERN, FRESHER, PART_TIME, FULL_TIME..."""

    __tablename__ = "job_types"

    id: Mapped[int] = pk()
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = pk()
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # tên đã chuẩn hóa
    category: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())

    aliases: Mapped[list["SkillAlias"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_skills_category", "category"),)


class SkillAlias(Base):
    """Tên gọi khác của kỹ năng ("ReactJS" -> React) để chuẩn hóa kết quả từ LLM."""

    __tablename__ = "skill_aliases"

    id: Mapped[int] = pk()
    skill_id: Mapped[int] = fk("skills.id", ondelete="CASCADE")
    alias: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    skill: Mapped["Skill"] = relationship(back_populates="aliases")

    __table_args__ = (Index("idx_skill_aliases_skill", "skill_id"),)

