from datetime import date
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.school_common import SchoolInput


class DashboardFilter(SchoolInput):
    model_config = ConfigDict(extra="ignore")
    group_by: Literal["major", "faculty", "cohort", "term"] = "major"
    date_from: date | None = None
    date_to: date | None = None
    faculty_id: int | None = Field(None, gt=0)
    major_id: int | None = Field(None, gt=0)
    cohort: str | None = None
    term_id: int | None = Field(None, gt=0)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("Khoảng ngày không hợp lệ")
        return self


class OverviewStats(ORMModel):
    students: int
    companies: int
    jobs: int
    applications: int
    interviews: int
    hired: int


class BreakdownRow(ORMModel):
    group: str
    count: int


class SkillStat(ORMModel):
    skill_id: int
    name: str
    required_jobs: int


class SkillGapRow(SkillStat):
    students_with_skill: int
    students_missing_skill: int


class MatchRateRow(ORMModel):
    major_id: int
    major_name: str
    students: int
    matched_students: int
    match_rate: float
    average_score: float


class TrendPoint(ORMModel):
    period: str
    jobs: int
    applications: int
    skills: list[SkillStat]


class FlowComparison(ORMModel):
    flow: Literal["free", "term"]
    jobs: int
    applications: int
    hired: int
