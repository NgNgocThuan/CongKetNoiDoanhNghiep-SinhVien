from datetime import datetime
from decimal import Decimal

from app.schemas.common import ORMModel


class MatchResult(ORMModel):
    id: int
    student_id: int
    job_id: int
    cv_id: int | None
    passed_rules: bool
    score: Decimal
    skill_score: Decimal | None
    experience_score: Decimal | None
    semantic_score: Decimal | None
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: str
    computed_at: datetime


class JobRecommendation(ORMModel):
    job_id: int
    title: str
    company_id: int
    match: MatchResult


class CandidateAchievement(ORMModel):
    title: str
    description: str | None


class CandidateRecommendation(ORMModel):
    student_id: int
    full_name: str
    major_id: int
    gpa: Decimal | None
    contact_email: str | None
    contact_phone: str | None
    achievements: list[CandidateAchievement]
    match: MatchResult
