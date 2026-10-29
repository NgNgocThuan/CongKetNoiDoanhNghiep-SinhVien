from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pytest

from app.ai.matching_engine import check_hard_rules, compute_match


def inputs():
    student = NS(major_id=1, gpa=3.0, skills=[])
    job = NS(
        majors=[],
        min_gpa=None,
        term_id=None,
        status="APPROVED",
        deadline=datetime.now(timezone.utc).date(),
        skills=[],
        min_experience_months=None,
    )
    return student, job


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("majors", [NS(major_id=2)], "MAJOR_MISMATCH"),
        ("min_gpa", 3.5, "GPA_TOO_LOW"),
        ("term_id", 1, "NOT_IN_TERM"),
        ("status", "DRAFT", "JOB_NOT_APPROVED"),
        ("deadline", datetime.now(timezone.utc).date() - timedelta(days=1), "JOB_EXPIRED"),
    ],
)
def test_hard_rules(field, value, code):
    student, job = inputs()
    setattr(job, field, value)
    result = compute_match(student, job, {}, {}, in_term=False)
    assert result.failed_rules == [code]
    assert result.score == 0
    assert not result.passed_rules


def test_missing_official_gpa_is_not_inferred_from_cv():
    student, job = inputs()
    student.gpa, job.min_gpa = None, 2
    assert check_hard_rules(student, job, in_term=True) == ["GPA_TOO_LOW"]


def test_weighted_skills_and_bounded_experience():
    student, job = inputs()
    result = compute_match(
        student,
        job,
        {"skills": [" python ", "PYTHON"], "experience_months": 24, "keywords": ["backend"]},
        {
            "required_skills": ["Python"],
            "preferred_skills": ["SQL", "python"],
            "min_experience_months": 12,
            "keywords": ["backend"],
        },
        in_term=True,
    )
    assert result.skill_score == 66.67
    assert result.experience_score == result.semantic_score == 100
    assert result.score == 83.33
    assert result.matched_skills == ["Python"]
    assert result.missing_skills == ["SQL"]


def test_full_and_missing_skill_match():
    student, job = inputs()
    parsed = {"required_skills": ["Python"], "keywords": ["API"]}
    full = compute_match(
        student, job, {"skills": ["Python"], "keywords": ["API"]}, parsed, in_term=True
    )
    missing = compute_match(student, job, None, parsed, in_term=True)
    assert full.score == 100
    assert missing.skill_score == 0
    assert missing.missing_skills == ["Python"]


def test_manual_skills_are_used_without_ai():
    student, job = inputs()
    student.skills = [NS(skill=NS(name="C++"))]
    job.skills = [NS(skill=NS(name="C++"), is_required=True)]
    assert compute_match(student, job, None, None, in_term=True).skill_score == 100
