"""Toàn bộ enum dùng chung. Giá trị phải khớp ENUM trong database/schema.sql."""
from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


# ---- Auth ----
class UserRole(StrEnum):
    STUDENT = "STUDENT"
    COMPANY = "COMPANY"
    ADMIN = "ADMIN"


class UserStatus(StrEnum):
    PENDING_ACTIVATION = "PENDING_ACTIVATION"  # sinh viên import, chưa kích hoạt
    PENDING_APPROVAL = "PENDING_APPROVAL"  # doanh nghiệp chờ trường duyệt
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"


# ---- Sinh viên ----
class SkillLevel(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class SkillSource(StrEnum):
    SELF = "SELF"
    CV_AI = "CV_AI"
    SCHOOL = "SCHOOL"


class CertificateSource(StrEnum):
    SCHOOL = "SCHOOL"
    SELF = "SELF"


class AchievementType(StrEnum):
    RESEARCH = "RESEARCH"
    ACHIEVEMENT = "ACHIEVEMENT"
    OTHER = "OTHER"


class CVType(StrEnum):
    UPLOADED = "UPLOADED"
    ONLINE = "ONLINE"


# ---- Doanh nghiệp ----
class CompanySize(StrEnum):
    S_1_10 = "1-10"
    S_11_50 = "11-50"
    S_51_200 = "51-200"
    S_201_500 = "201-500"
    S_501_1000 = "501-1000"
    S_1000_PLUS = "1000+"


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CompanyDocType(StrEnum):
    BUSINESS_LICENSE = "BUSINESS_LICENSE"
    TAX_CERTIFICATE = "TAX_CERTIFICATE"
    AUTHORIZATION_LETTER = "AUTHORIZATION_LETTER"
    OTHER = "OTHER"


# ---- Nhà trường / thực tập ----
class ImportType(StrEnum):
    STUDENTS = "STUDENTS"
    TERM_STUDENTS = "TERM_STUDENTS"
    SYNC = "SYNC"


class TermStatus(StrEnum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    ONGOING = "ONGOING"
    CLOSED = "CLOSED"


class InternshipResultStatus(StrEnum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


# ---- Tuyển dụng ----
class WorkMode(StrEnum):
    ONSITE = "ONSITE"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"


class JobStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"  # chỉ trạng thái này mới hiển thị cho sinh viên
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class InvitationStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class ApplicationStatus(StrEnum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


# ---- AI ----
class AIPurpose(StrEnum):
    PARSE_CV = "PARSE_CV"
    PARSE_JOB = "PARSE_JOB"
    MATCH_EXPLAIN = "MATCH_EXPLAIN"
    OTHER = "OTHER"


class AIRequestStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ---- Thông báo / báo cáo ----
class EmailStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class ReportTargetType(StrEnum):
    JOB = "JOB"
    COMPANY = "COMPANY"
    STUDENT = "STUDENT"


class ReportStatus(StrEnum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
