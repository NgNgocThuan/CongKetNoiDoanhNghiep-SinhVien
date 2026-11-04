"""Import toàn bộ models để đăng ký vào Base.metadata (Alembic và mapper cần điều này).

Khi thêm model mới: tạo trong file domain tương ứng rồi thêm tên vào đây.
"""
from app.models.application import Application, ApplicationStatusLog, Invitation
from app.models.base import Base
from app.models.catalog import Faculty, Industry, JobType, Major, Skill, SkillAlias
from app.models.communication import EmailLog, Notification, Report
from app.models.company import Company, CompanyDocument
from app.models.freelancer_contracts import (
    ContractMilestoneTerm,
    ContractVersion,
    Deliverable,
    DeliverableFile,
    FreelanceContract,
    FreelanceReview,
    Milestone,
    MilestoneReview,
    ProjectContractBudget,
)
from app.models.freelancer_disputes import (
    ActiveMilestoneDispute,
    CancellationAgreement,
    Dispute,
    DisputeDecision,
    DisputeEvidence,
    MilestoneHold,
)
from app.models.freelancer_finance import (
    BankDestination,
    DailyLimitBucket,
    DailyLimitReservation,
    MoneyTransfer,
    Settlement,
    TransferAttempt,
)
from app.models.freelancer_identity import (
    BusinessVerification,
    BusinessVerificationFile,
    ClientProfile,
    CompanyLimit,
    MouAgreement,
    StoredFile,
    UserVerification,
)
from app.models.freelancer_ledger import (
    LedgerAccount,
    LedgerJournal,
    LedgerPosting,
)
from app.models.freelancer_operations import (
    AuditLog,
    CommandRequest,
    OutboxEvent,
    ReconciliationItem,
    ReconciliationRun,
    ScheduledJob,
)
from app.models.freelancer_payments import (
    EscrowAccount,
    MilestoneFunding,
    MilestoneFundingGuard,
    PaymentOrder,
    PaymentReviewCase,
    PaymentTransaction,
    ProviderEvent,
)
from app.models.freelancer_projects import (
    FreelanceApplication,
    FreelanceProject,
    FreelanceProjectReview,
    FreelanceProjectSkill,
    ProjectMilestoneProposal,
)
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


__all__ += ['StoredFile', 'ClientProfile', 'UserVerification', 'BusinessVerification', 'BusinessVerificationFile', 'CompanyLimit', 'MouAgreement', 'FreelanceProject', 'ProjectMilestoneProposal', 'FreelanceProjectSkill', 'FreelanceProjectReview', 'FreelanceApplication', 'FreelanceContract', 'ProjectContractBudget', 'ContractVersion', 'Milestone', 'ContractMilestoneTerm', 'Deliverable', 'DeliverableFile', 'MilestoneReview', 'FreelanceReview', 'LedgerAccount', 'LedgerJournal', 'LedgerPosting', 'PaymentOrder', 'MilestoneFundingGuard', 'ProviderEvent', 'PaymentTransaction', 'MilestoneFunding', 'PaymentReviewCase', 'EscrowAccount', 'CancellationAgreement', 'Dispute', 'ActiveMilestoneDispute', 'MilestoneHold', 'DisputeEvidence', 'DisputeDecision', 'BankDestination', 'Settlement', 'MoneyTransfer', 'TransferAttempt', 'DailyLimitBucket', 'DailyLimitReservation', 'AuditLog', 'OutboxEvent', 'ScheduledJob', 'ReconciliationRun', 'ReconciliationItem', 'CommandRequest']
