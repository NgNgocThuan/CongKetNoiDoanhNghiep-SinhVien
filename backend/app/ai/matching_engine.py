"""Deterministic recommendation scoring; callers supply fully loaded domain data."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

ALGO_VERSION = "1.0"
WEIGHTS = {"skill": 0.5, "experience": 0.2, "semantic": 0.3}


@dataclass
class MatchBreakdown:
    passed_rules: bool
    failed_rules: list[str] = field(default_factory=list)
    score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    semantic_score: float = 0.0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    explanation: str = ""


def check_hard_rules(student, job, *, in_term: bool) -> list[str]:
    """Return stable failure codes using official academic fields only."""
    failed = []
    if job.majors and student.major_id not in {major.major_id for major in job.majors}:
        failed.append("MAJOR_MISMATCH")
    if job.min_gpa is not None and (student.gpa is None or student.gpa < job.min_gpa):
        failed.append("GPA_TOO_LOW")
    if job.term_id is not None and not in_term:
        failed.append("NOT_IN_TERM")
    if job.status != "APPROVED":
        failed.append("JOB_NOT_APPROVED")
    if job.deadline < datetime.now(timezone.utc).date():
        failed.append("JOB_EXPIRED")
    return failed


def _names(values: list[str]) -> dict[str, str]:
    return {name.strip().casefold(): name.strip() for name in values if name.strip()}


def _keywords(data: dict) -> set[str]:
    text = " ".join(data.get("keywords", []) + data.get("domains", []))
    return set(re.findall(r"[\w.+#]+", text.casefold()))


def compute_match(
    student, job, cv_parsed: dict | None, job_parsed: dict | None, *, in_term: bool
) -> MatchBreakdown:
    """Score skills 50%, experience 20%, lexical relevance 30%; no API/DB calls."""
    failed = check_hard_rules(student, job, in_term=in_term)
    if failed:
        return MatchBreakdown(False, failed, explanation="Failed rules: " + ", ".join(failed))
    cv, parsed_job = cv_parsed or {}, job_parsed or {}
    available = _names(cv.get("skills", []))
    for item in student.skills:
        available.update(_names([item.skill.name]))
    required = _names(parsed_job.get("required_skills", []))
    preferred = _names(parsed_job.get("preferred_skills", []))
    for item in job.skills:
        target = required if item.is_required else preferred
        target.update(_names([item.skill.name]))
    preferred = {key: value for key, value in preferred.items() if key not in required}
    requirements = required | preferred
    denominator = 2 * len(required) + len(preferred)
    numerator = 2 * len(required.keys() & available.keys()) + len(
        preferred.keys() & available.keys()
    )
    skill_score = 100 * numerator / denominator if denominator else 100.0
    months = job.min_experience_months
    if months is None:
        months = parsed_job.get("min_experience_months", 0)
    experience_score = 100 * min(cv.get("experience_months", 0) / months, 1) if months else 100.0
    expected, actual = _keywords(parsed_job), _keywords(cv)
    semantic_score = 100 * len(expected & actual) / len(expected) if expected else 0.0
    matched = sorted(requirements[key] for key in requirements.keys() & available.keys())
    missing = sorted(requirements[key] for key in requirements.keys() - available.keys())
    score = (
        skill_score * WEIGHTS["skill"]
        + experience_score * WEIGHTS["experience"]
        + semantic_score * WEIGHTS["semantic"]
    )
    return MatchBreakdown(
        passed_rules=True,
        score=round(score, 2),
        skill_score=round(skill_score, 2),
        experience_score=round(experience_score, 2),
        semantic_score=round(semantic_score, 2),
        matched_skills=matched,
        missing_skills=missing,
        explanation=f"Matched {len(matched)}/{len(requirements)} skills. Recommendation only.",
    )
