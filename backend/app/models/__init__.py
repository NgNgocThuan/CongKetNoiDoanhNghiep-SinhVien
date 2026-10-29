"""Import toàn bộ models để đăng ký vào Base.metadata (Alembic và mapper cần điều này).

Khi thêm model mới: tạo trong file domain tương ứng rồi thêm tên vào đây.
"""
from app.models.application import Application, ApplicationStatusLog, Invitation
from app.models.base import Base
from app.models.catalog import Faculty, Industry, JobType, Major, Skill, SkillAlias
from app.models.communication import EmailLog, Notification, Report
from app.models.company import Company, CompanyDocument
from app.models.internship import InternshipResult, InternshipTerm, TermStudent
from app.models.job import Job, JobMajor, JobSkill, JobView, SavedJob
from app.models.matching import AIRequestLog, MatchingResult
from app.models.school import Admin, ImportBatch, Lecturer
from app.models.student import (
    CV,
    Student,
    StudentAchievement,
    StudentCertificate,
    StudentExperience,
    StudentProfile,
    StudentProject,
    StudentSkill,
)
from app.models.user import PasswordResetToken, User

__all__ = [
    "Base",
    # user
    "User",
    "PasswordResetToken",
    # catalog
    "Faculty",
    "Major",
    "Industry",
    "JobType",
    "Skill",
    "SkillAlias",
    # school
    "Admin",
    "Lecturer",
    "ImportBatch",
    # student
    "Student",
    "StudentProfile",
    "StudentSkill",
    "StudentExperience",
    "StudentProject",
    "StudentCertificate",
    "StudentAchievement",
    "CV",
    # company
    "Company",
    "CompanyDocument",
    # internship
    "InternshipTerm",
    "TermStudent",
    "InternshipResult",
    # job
    "Job",
    "JobMajor",
    "JobSkill",
    "JobView",
    "SavedJob",
    # application
    "Invitation",
    "Application",
    "ApplicationStatusLog",
    # matching
    "MatchingResult",
    "AIRequestLog",
    # communication
    "Notification",
    "EmailLog",
    "Report",
]
