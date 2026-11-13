"""Deterministic recommendation scoring; callers supply fully loaded domain data."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

ALGO_VERSION = "4.0-confirmed-skills"
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


def check_hard_rules(student, job) -> list[str]:
    """Return stable failure codes using official academic fields only."""
    failed = []
    if job.majors and student.major_id not in {major.major_id for major in job.majors}:
        failed.append("MAJOR_MISMATCH")
    if job.min_gpa is not None and (student.gpa is None or student.gpa < job.min_gpa):
        failed.append("GPA_TOO_LOW")
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
    student, job, cv_parsed: dict | None, job_parsed: dict | None
) -> MatchBreakdown:
    """Score declared evidence; missing requirements never grant free points."""
    failed = check_hard_rules(student, job)
    if failed:
        return MatchBreakdown(False, failed, explanation="Failed rules: " + ", ".join(failed))
    cv, parsed_job = cv_parsed or {}, job_parsed or {}
    # The profile is the confirmed source; extracted CV skills require student approval.
    available = {}
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
    skill_score = 100 * numerator / denominator if denominator else 0.0
    months = job.min_experience_months
    if months is None:
        months = parsed_job.get("min_experience_months", 0)
    experience_score = 100 * min(cv.get("experience_months", 0) / months, 1) if months else 0.0
    expected, actual = _keywords(parsed_job), _keywords(cv)
    semantic_score = 100 * len(expected & actual) / len(expected) if expected else 0.0
    matched = sorted(requirements[key] for key in requirements.keys() & available.keys())
    missing = sorted(requirements[key] for key in requirements.keys() - available.keys())
    # Only criteria actually requested by the job contribute to the denominator.
    # Some shared vocabulary or experience alone cannot establish skill relevance.
    active_weights = {"skill": WEIGHTS["skill"]} if denominator else {}
    if months:
        active_weights["experience"] = WEIGHTS["experience"]
    if expected:
        active_weights["semantic"] = WEIGHTS["semantic"]
    components = {"skill": skill_score, "experience": experience_score, "semantic": semantic_score}
    score = (
        sum(components[key] * weight for key, weight in active_weights.items())
        / sum(active_weights.values())
        if matched else 0.0
    )
    if not requirements:
        explanation = "Tin chưa khai báo kỹ năng để đối chiếu; chưa đủ dữ liệu đánh giá mức độ phù hợp."
    elif not matched:
        explanation = "Chưa có kỹ năng trùng khớp giữa hồ sơ và yêu cầu của công việc."
    else:
        explanation = f"Khớp {len(matched)}/{len(requirements)} kỹ năng. Chỉ tính các tiêu chí có dữ liệu yêu cầu; kết quả mang tính tham khảo."
    return MatchBreakdown(
        passed_rules=True,
        score=round(score, 2),
        skill_score=round(skill_score, 2),
        experience_score=round(experience_score, 2),
        semantic_score=round(semantic_score, 2),
        matched_skills=matched,
        missing_skills=missing,
        explanation=explanation,
    )
