"""Validated extraction contracts shared by prompts and parsers."""

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domains: list[StrictStr]
    keywords: list[StrictStr]


class CVExtraction(Extraction):
    skills: list[StrictStr]
    experience_months: int = Field(ge=0, strict=True)
    projects: list[StrictStr]


class JobExtraction(Extraction):
    required_skills: list[StrictStr]
    preferred_skills: list[StrictStr]
    min_experience_months: int = Field(ge=0, strict=True)
    education: StrictStr | None
