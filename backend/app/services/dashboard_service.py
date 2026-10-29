"""SQL aggregate reports; counts describe records in the requested creation period."""

from datetime import datetime, time, timedelta

from sqlalchemy import String, case, cast, distinct, func, select
from sqlalchemy.orm import Session

from app.core.enums import ApplicationStatus, JobStatus
from app.core.exceptions import BadRequestError
from app.models import (
    Application,
    Company,
    Job,
    Major,
    MatchingResult,
    Skill,
    Student,
    StudentSkill,
    TermStudent,
)
from app.utils.datetime_utils import utcnow


def time_conditions(column, filters):
    conditions = []
    if filters.date_from:
        conditions.append(column >= datetime.combine(filters.date_from, time.min))
    if filters.date_to:
        conditions.append(column < datetime.combine(filters.date_to + timedelta(days=1), time.min))
    return conditions


def student_conditions(filters, *, dates=True):
    conditions = []
    for key in ("faculty_id", "major_id", "cohort"):
        value = getattr(filters, key)
        if value is not None:
            conditions.append(getattr(Student, key) == value)
    if filters.term_id is not None:
        conditions.append(
            Student.id.in_(
                select(TermStudent.student_id).where(TermStudent.term_id == filters.term_id)
            )
        )
    if dates:
        conditions += time_conditions(Student.created_at, filters)
    return conditions


def job_conditions(filters, *, dates=True):
    conditions = []
    if filters.term_id is not None:
        conditions.append(Job.term_id == filters.term_id)
    # Academic filters select jobs explicitly targeting the requested majors,
    # plus unrestricted jobs. Cohort is only meaningful for student metrics.
    if filters.faculty_id is not None or filters.major_id is not None:
        from app.models import JobMajor

        majors = select(Major.id)
        if filters.faculty_id is not None:
            majors = majors.where(Major.faculty_id == filters.faculty_id)
        if filters.major_id is not None:
            majors = majors.where(Major.id == filters.major_id)
        conditions.append(
            (~select(JobMajor.job_id).where(JobMajor.job_id == Job.id).exists())
            | select(JobMajor.job_id)
            .where(JobMajor.job_id == Job.id, JobMajor.major_id.in_(majors))
            .exists()
        )
    if dates:
        conditions += time_conditions(Job.created_at, filters)
    return conditions


def application_conditions(filters):
    return (
        student_conditions(filters, dates=False)
        + job_conditions(filters, dates=False)
        + time_conditions(Application.applied_at, filters)
    )


def application_query(filters):
    return select(Application).join(Student).join(Job).where(*application_conditions(filters))


def overview(db: Session, filters):
    students = db.scalar(
        select(func.count()).select_from(Student).where(*student_conditions(filters))
    )
    jobs = db.scalar(select(func.count()).select_from(Job).where(*job_conditions(filters)))
    company_query = (
        select(func.count())
        .select_from(Company)
        .where(*time_conditions(Company.created_at, filters))
    )
    if (
        filters.term_id is not None
        or filters.faculty_id is not None
        or filters.major_id is not None
    ):
        company_query = company_query.where(
            Company.id.in_(select(Job.company_id).where(*job_conditions(filters, dates=False)))
        )
    companies = db.scalar(company_query)
    app_counts = db.execute(
        select(
            func.count(Application.id),
            func.sum(case((Application.current_status == ApplicationStatus.INTERVIEW, 1), else_=0)),
            func.sum(case((Application.current_status == ApplicationStatus.HIRED, 1), else_=0)),
        )
        .select_from(Application)
        .join(Student)
        .join(Job)
        .where(*application_conditions(filters))
    ).one()
    return dict(
        students=students,
        companies=companies,
        jobs=jobs,
        applications=app_counts[0],
        interviews=app_counts[1] or 0,
        hired=app_counts[2] or 0,
    )


def breakdown(db: Session, filters, params, group_by):
    if group_by not in {"major", "faculty", "cohort", "term"}:
        raise BadRequestError("group_by phải là major, faculty, cohort hoặc term")
    if group_by == "term":
        column = cast(TermStudent.term_id, String)
        stmt = select(column.label("group"), func.count(Student.id).label("count")).join(
            TermStudent, TermStudent.student_id == Student.id
        )
    else:
        column = getattr(
            Student, {"major": "major_id", "faculty": "faculty_id", "cohort": "cohort"}[group_by]
        )
        column = cast(column, String)
        stmt = select(column.label("group"), func.count(Student.id).label("count"))
    stmt = stmt.where(*student_conditions(filters)).group_by(column).order_by(column)
    if group_by == "term" and filters.term_id is not None:
        stmt = stmt.where(TermStudent.term_id == filters.term_id)
    return aggregate_page(db, stmt, params)


def aggregate_page(db: Session, stmt, params):
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = [
        dict(row) for row in db.execute(stmt.offset(params.offset).limit(params.size)).mappings()
    ]
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }


def skill_query(filters):
    from app.models import JobSkill

    return (
        select(
            Skill.id.label("skill_id"),
            Skill.name,
            func.count(distinct(Job.id)).label("required_jobs"),
        )
        .select_from(Skill)
        .join(JobSkill)
        .join(Job)
        .where(Job.status == JobStatus.APPROVED, *job_conditions(filters))
        .group_by(Skill.id, Skill.name)
    )


def top_skills(db: Session, filters, params):
    stmt = skill_query(filters)
    return aggregate_page(
        db, stmt.order_by(stmt.selected_columns.required_jobs.desc(), Skill.id), params
    )


def skill_gap(db: Session, filters, params):
    page = top_skills(db, filters, params)
    ids = [i["skill_id"] for i in page["items"]]
    counts = dict(
        db.execute(
            select(StudentSkill.skill_id, func.count(distinct(Student.id)))
            .join(Student, Student.id == StudentSkill.student_id)
            .where(StudentSkill.skill_id.in_(ids), *student_conditions(filters, dates=False))
            .group_by(StudentSkill.skill_id)
        ).all()
    )
    total_students = db.scalar(
        select(func.count(Student.id)).where(*student_conditions(filters, dates=False))
    )
    for item in page["items"]:
        item["students_with_skill"] = counts.get(item["skill_id"], 0)
        item["students_missing_skill"] = total_students - item["students_with_skill"]
    return page


def match_rate(db: Session, filters, params):
    eligible_jobs = select(Job.id).where(
        Job.status == JobStatus.APPROVED,
        Job.deadline >= utcnow().date(),
        *job_conditions(filters, dates=False),
    )
    matches = (
        select(
            MatchingResult.student_id.label("student_id"),
            func.max(case((MatchingResult.passed_rules.is_(True), 1), else_=0)).label("passed"),
            func.avg(MatchingResult.score).label("avg_score"),
        )
        .where(
            MatchingResult.job_id.in_(eligible_jobs),
            *time_conditions(MatchingResult.computed_at, filters),
        )
        .group_by(MatchingResult.student_id)
        .subquery()
    )
    stmt = (
        select(
            Major.id.label("major_id"),
            Major.name.label("major_name"),
            func.count(Student.id).label("students"),
            func.coalesce(func.sum(matches.c.passed), 0).label("matched_students"),
            func.coalesce(func.avg(matches.c.avg_score), 0).label("average_score"),
        )
        .select_from(Student)
        .join(Major)
        .outerjoin(matches, matches.c.student_id == Student.id)
        .where(*student_conditions(filters, dates=False))
        .group_by(Major.id, Major.name)
        .order_by(Major.id)
    )
    page = aggregate_page(db, stmt, params)
    for item in page["items"]:
        item["match_rate"] = (
            round(100 * item["matched_students"] / item["students"], 2) if item["students"] else 0
        )
        item["average_score"] = round(float(item["average_score"]), 2)
    return page


def trends(db: Session, filters, params):
    job_day = cast(func.date(Job.created_at), String)
    app_day = cast(func.date(Application.applied_at), String)
    jobs = (
        select(job_day.label("period"), func.count(Job.id).label("jobs"))
        .where(*job_conditions(filters))
        .group_by(job_day)
        .subquery()
    )
    apps = (
        select(app_day.label("period"), func.count(Application.id).label("applications"))
        .join(Student)
        .join(Job)
        .where(*application_conditions(filters))
        .group_by(app_day)
        .subquery()
    )
    periods = select(jobs.c.period).union(select(apps.c.period)).subquery()
    stmt = (
        select(
            periods.c.period,
            func.coalesce(jobs.c.jobs, 0).label("jobs"),
            func.coalesce(apps.c.applications, 0).label("applications"),
        )
        .select_from(periods)
        .outerjoin(jobs, jobs.c.period == periods.c.period)
        .outerjoin(apps, apps.c.period == periods.c.period)
        .order_by(periods.c.period)
    )
    page = aggregate_page(db, stmt, params)
    from app.models import JobSkill

    periods_on_page = [item["period"] for item in page["items"]]
    skills = db.execute(
        select(
            job_day.label("period"),
            Skill.id.label("skill_id"),
            Skill.name,
            func.count(distinct(Job.id)).label("required_jobs"),
        )
        .select_from(Job)
        .join(JobSkill)
        .join(Skill)
        .where(job_day.in_(periods_on_page), *job_conditions(filters))
        .group_by(job_day, Skill.id, Skill.name)
        .order_by(job_day, Skill.id)
    ).mappings()
    by_period = {}
    for row in skills:
        by_period.setdefault(row["period"], []).append(
            {k: row[k] for k in ("skill_id", "name", "required_jobs")}
        )
    for item in page["items"]:
        item["skills"] = by_period.get(item["period"], [])
    return page


def flow_comparison(db: Session, filters, params):
    flow = case((Job.term_id.is_(None), "free"), else_="term")
    job_counts = dict(
        db.execute(
            select(flow, func.count(Job.id)).where(*job_conditions(filters)).group_by(flow)
        ).all()
    )
    app_counts = {
        row[0]: row[1:]
        for row in db.execute(
            select(
                flow,
                func.count(Application.id),
                func.sum(case((Application.current_status == ApplicationStatus.HIRED, 1), else_=0)),
            )
            .select_from(Application)
            .join(Student)
            .join(Job)
            .where(*application_conditions(filters))
            .group_by(flow)
        )
    }
    items = [
        {
            "flow": f,
            "jobs": job_counts.get(f, 0),
            "applications": app_counts.get(f, (0, 0))[0],
            "hired": app_counts.get(f, (0, 0))[1] or 0,
        }
        for f in ("free", "term")
    ]
    return {
        "items": items[params.offset : params.offset + params.size],
        "total": 2,
        "page": params.page,
        "size": params.size,
        "pages": (2 + params.size - 1) // params.size,
    }
