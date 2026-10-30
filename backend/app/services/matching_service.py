"""Deterministic matching with database cache, current eligibility and privacy."""

from dataclasses import asdict

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai import cv_parser, job_parser
from app.ai.errors import LLMError
from app.ai.matching_engine import ALGO_VERSION, check_hard_rules, compute_match
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import JobStatus, UserStatus
from app.core.exceptions import BadRequestError, NotFoundError
from app.models import (
    CV,
    Job,
    JobSkill,
    MatchingResult,
    Student,
    StudentProfile,
    StudentSkill,
    TermStudent,
    User,
)
from app.services.internship_service import is_student_in_term
from app.utils.datetime_utils import utcnow
from app.utils.hashing import sha256_json
from app.utils.pagination import paginate

STUDENT_LOADS = (
    selectinload(Student.skills).selectinload(StudentSkill.skill),
    selectinload(Student.profile),
    selectinload(Student.achievements),
    selectinload(Student.user),
)
JOB_LOADS = (selectinload(Job.skills).selectinload(JobSkill.skill), selectinload(Job.majors))


def get_job(db: Session, job_id, *, company_id=None, student=None):
    stmt = select(Job).where(Job.id == job_id).options(*JOB_LOADS)
    if company_id is not None:
        stmt = stmt.where(Job.company_id == company_id)
    else:
        stmt = stmt.where(Job.status == JobStatus.APPROVED, Job.deadline >= utcnow().date())
    job = db.scalar(stmt)
    if job is None:
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    if (
        student is not None
        and job.term_id is not None
        and not is_student_in_term(db, student.id, job.term_id)
    ):
        raise NotFoundError("Không tìm thấy tin tuyển dụng")
    return job


def build_input_hash(cv, job, student, *, in_term=True):
    return sha256_json(
        {
            "algorithm": ALGO_VERSION,
            "today": utcnow().date(),
            "in_term": in_term,
            "student": [
                student.id,
                student.major_id,
                student.gpa,
                sorted((s.skill_id, s.skill.name) for s in student.skills),
            ],
            "cv": None
            if cv is None
            else [cv.id, cv.content_hash, cv.parsed_json, cv.content_json, cv.file_url],
            "job": [
                job.id,
                job.title,
                job.position,
                job.description,
                job.requirements,
                job.status,
                job.deadline,
                job.term_id,
                job.min_gpa,
                job.min_experience_months,
                sorted(m.major_id for m in job.majors),
                sorted((s.skill_id, s.skill.name, s.is_required) for s in job.skills),
                job.content_hash,
                job.parsed_json,
            ],
        }
    )


def get_or_compute_match(db: Session, student, job):
    student = db.scalar(select(Student).where(Student.id == student.id).options(*STUDENT_LOADS))
    job = db.scalar(select(Job).where(Job.id == job.id).options(*JOB_LOADS))
    cv = db.scalar(
        select(CV)
        .where(CV.student_id == student.id, CV.deleted_at.is_(None))
        .order_by(CV.is_default.desc(), CV.id.desc())
        .limit(1)
    )
    in_term = job.term_id is None or is_student_in_term(db, student.id, job.term_id)
    # Reuse parsers' content hashes before considering the matching cache.
    # Without credentials and parsed data, manual catalog skills still work.
    eligible = not check_hard_rules(student, job, in_term=in_term)
    try:
        cv_data = (
            cv_parser.parse_cv(db, cv)
            if eligible and cv and (settings.AI_API_KEY or cv.parsed_json is not None)
            else None
        )
        job_data = (
            job_parser.parse_job(db, job)
            if eligible and (settings.AI_API_KEY or job.parsed_json is not None)
            else None
        )
    except LLMError as exc:
        # Parsers validate before changing their cached data. Preserve the failed
        # request log rather than letting request-session close roll it back.
        db.commit()
        raise BadRequestError(
            "Không thể phân tích dữ liệu AI; kiểm tra cấu hình hoặc phân tích lại",
            code="AI_UNAVAILABLE",
        ) from exc
    digest = build_input_hash(cv, job, student, in_term=in_term)
    cached = db.scalar(
        select(MatchingResult).where(
            MatchingResult.student_id == student.id, MatchingResult.job_id == job.id
        )
    )
    if cached is not None and cached.input_hash == digest:
        return cached
    breakdown = asdict(compute_match(student, job, cv_data, job_data, in_term=in_term))
    breakdown.pop("failed_rules")
    if not settings.AI_API_KEY and cv_data is None and job_data is None:
        breakdown["explanation"] += " Based on declared skills; AI extraction unavailable."
    if cached is None:
        cached = MatchingResult(student_id=student.id, job_id=job.id)
        db.add(cached)
    for key, value in breakdown.items():
        setattr(cached, key, value)
    cached.cv_id = cv.id if cv else None
    cached.input_hash, cached.algo_version, cached.computed_at = digest, ALGO_VERSION, utcnow()
    db.commit()
    db.refresh(cached)
    return cached


def score_for_student(db: Session, student, job_id):
    return get_or_compute_match(db, student, get_job(db, job_id, student=student))


def _eligible_jobs(student):
    membership = select(TermStudent.term_id).where(TermStudent.student_id == student.id)
    return select(Job).where(
        Job.status == JobStatus.APPROVED,
        Job.deadline >= utcnow().date(),
        or_(Job.term_id.is_(None), Job.term_id.in_(membership)),
    )


def _compute_jobs(db: Session, student):
    cursor = 0
    while True:
        jobs = db.scalars(
            _eligible_jobs(student)
            .where(Job.id > cursor)
            .order_by(Job.id)
            .limit(100)
            .options(*JOB_LOADS)
        ).all()
        if not jobs:
            break
        for job in jobs:
            get_or_compute_match(db, student, job)
        cursor = jobs[-1].id


def recommend_jobs_for_student(db: Session, student, params):
    _compute_jobs(db, student)
    stmt = (
        select(MatchingResult)
        .join(Job)
        .where(
            MatchingResult.student_id == student.id,
            MatchingResult.passed_rules.is_(True),
            Job.id.in_(_eligible_jobs(student).with_only_columns(Job.id)),
        )
        .order_by(MatchingResult.score.desc(), MatchingResult.job_id)
    )
    page = paginate(db, stmt, params)
    ids = [m.job_id for m in page["items"]]
    jobs = {j.id: j for j in db.scalars(select(Job).where(Job.id.in_(ids)))}
    page["items"] = [
        {
            "job_id": m.job_id,
            "title": jobs[m.job_id].title,
            "company_id": jobs[m.job_id].company_id,
            "match": m,
        }
        for m in page["items"]
    ]
    return page


def _candidate_query(job):
    stmt = (
        select(Student)
        .join(StudentProfile)
        .join(User)
        .where(StudentProfile.is_open_to_work.is_(True), User.status == UserStatus.ACTIVE)
    )
    if job.term_id is not None:
        stmt = stmt.where(
            Student.id.in_(select(TermStudent.student_id).where(TermStudent.term_id == job.term_id))
        )
    return stmt


def recommend_candidates_for_job(db: Session, company, job_id, params):
    job = get_job(db, job_id, company_id=company.id)
    cursor = 0
    while True:
        students = db.scalars(
            _candidate_query(job)
            .where(Student.id > cursor)
            .order_by(Student.id)
            .limit(100)
            .options(*STUDENT_LOADS)
        ).all()
        if not students:
            break
        for student in students:
            get_or_compute_match(db, student, job)
        cursor = students[-1].id
    stmt = (
        select(MatchingResult)
        .where(
            MatchingResult.job_id == job.id,
            MatchingResult.passed_rules.is_(True),
            MatchingResult.student_id.in_(_candidate_query(job).with_only_columns(Student.id)),
        )
        .order_by(MatchingResult.score.desc(), MatchingResult.student_id)
    )
    page = paginate(db, stmt, params)
    ids = [m.student_id for m in page["items"]]
    students = {
        s.id: s
        for s in db.scalars(select(Student).where(Student.id.in_(ids)).options(*STUDENT_LOADS))
    }
    items = []
    for match in page["items"]:
        student = students[match.student_id]
        profile = student.profile
        items.append(
            {
                "student_id": student.id,
                "full_name": student.full_name,
                "major_id": student.major_id,
                "gpa": student.gpa if profile.show_gpa else None,
                "contact_email": (profile.contact_email or student.user.email)
                if profile.show_contact
                else None,
                "contact_phone": (profile.contact_phone or student.phone)
                if profile.show_contact
                else None,
                "achievements": student.achievements if profile.show_achievements else [],
                "match": match,
            }
        )
    page["items"] = items
    return page


def recompute_all(db: Session):
    cursor = 0
    while True:
        students = db.scalars(
            select(Student)
            .join(User)
            .where(Student.id > cursor, User.status == UserStatus.ACTIVE)
            .order_by(Student.id)
            .limit(100)
        ).all()
        if not students:
            break
        for student in students:
            _compute_jobs(db, student)
        cursor = students[-1].id


def recompute_in_background():
    with SessionLocal() as db:
        recompute_all(db)
