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
        ("status", "DRAFT", "JOB_NOT_APPROVED"),
        ("deadline", datetime.now(timezone.utc).date() - timedelta(days=1), "JOB_EXPIRED"),
    ],
)
def test_hard_rules(field, value, code):
    student, job = inputs()
    setattr(job, field, value)
    result = compute_match(student, job, {}, {})
    assert result.failed_rules == [code]
    assert result.score == 0
    assert not result.passed_rules


def test_missing_official_gpa_is_not_inferred_from_cv():
    student, job = inputs()
    student.gpa, job.min_gpa = None, 2
    assert check_hard_rules(student, job) == ["GPA_TOO_LOW"]


def test_weighted_skills_and_bounded_experience():
    student, job = inputs()
    student.skills = [NS(skill=NS(name="Python"))]
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
    )
    assert result.skill_score == 66.67
    assert result.experience_score == result.semantic_score == 100
    assert result.score == 83.33
    assert result.matched_skills == ["Python"]
    assert result.missing_skills == ["SQL"]


def test_full_and_missing_skill_match():
    student, job = inputs()
    student.skills = [NS(skill=NS(name="Python"))]
    parsed = {"required_skills": ["Python"], "keywords": ["API"]}
    full = compute_match(
        student, job, {"skills": ["Python"], "keywords": ["API"]}, parsed
    )
    student.skills = []
    missing = compute_match(student, job, None, parsed)
    assert full.score == 100
    assert missing.skill_score == 0
    assert missing.missing_skills == ["Python"]


def test_manual_skills_are_used_without_ai():
    student, job = inputs()
    student.skills = [NS(skill=NS(name="C++"))]
    job.skills = [NS(skill=NS(name="C++"), is_required=True)]
    assert compute_match(student, job, None, None).skill_score == 100


def test_empty_requirements_do_not_receive_seventy_percent():
    student, job = inputs()
    result = compute_match(student, job, None, None)
    assert result.score == result.skill_score == result.experience_score == 0
    assert result.matched_skills == []


def test_unrelated_skills_do_not_gain_points_from_experience_or_keywords():
    student, job = inputs()
    result = compute_match(
        student, job,
        {"skills": ["Accounting"], "experience_months": 48, "keywords": ["team"]},
        {"required_skills": ["React"], "min_experience_months": 12, "keywords": ["team"]},
    )
    assert result.experience_score == result.semantic_score == 100
    assert result.skill_score == result.score == 0


def test_unspecified_criteria_are_not_awarded_or_penalized():
    student, job = inputs()
    student.skills = [NS(skill=NS(name="Python"))]
    result = compute_match(student, job, {"skills": ["Python"]}, {"required_skills": ["Python", "SQL"]})
    assert result.skill_score == result.score == 50
    assert result.experience_score == result.semantic_score == 0


def test_unconfirmed_cv_skills_do_not_change_profile_matching():
    student, job = inputs()
    result = compute_match(student, job, {"skills": ["React"]}, {"required_skills": ["React"]})
    assert result.score == result.skill_score == 0
    assert result.matched_skills == []
    assert result.missing_skills == ["React"]
