"""Business rules for data that a student may manage themselves."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.enums import CertificateSource, SkillSource
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models import (
    Skill,
    Student,
    StudentCertificate,
    StudentExperience,
    StudentProfile,
    StudentProject,
    StudentSkill,
    TermStudent,
)
from app.schemas.students import (
    CertificateCreate,
    CertificateUpdate,
    ExperienceCreate,
    ExperienceUpdate,
    ProfileUpdate,
    ProjectCreate,
    ProjectUpdate,
    SkillCreate,
    SkillUpdate,
)
from app.utils.datetime_utils import utcnow


def _profile_query(student_id: int):
    return (
        select(Student)
        .where(Student.id == student_id)
        .options(
            joinedload(Student.faculty),
            joinedload(Student.major),
            selectinload(Student.skills).joinedload(StudentSkill.skill),
            selectinload(Student.experiences),
            selectinload(Student.projects),
            selectinload(Student.certificates),
            selectinload(Student.achievements),
        )
    )


def _profile_payload(profile: StudentProfile | None, student_id: int) -> dict:
    if profile is not None:
        return {
            "student_id": profile.student_id,
            "avatar_url": profile.avatar_url,
            "bio": profile.bio,
            "career_goal": profile.career_goal,
            "contact_email": profile.contact_email,
            "contact_phone": profile.contact_phone,
            "address": profile.address,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "is_open_to_work": profile.is_open_to_work,
            "show_gpa": profile.show_gpa,
            "show_contact": profile.show_contact,
            "show_achievements": profile.show_achievements,
            "updated_at": profile.updated_at,
        }
    return {
        "student_id": student_id,
        "avatar_url": None,
        "bio": None,
        "career_goal": None,
        "contact_email": None,
        "contact_phone": None,
        "address": None,
        "linkedin_url": None,
        "github_url": None,
        "is_open_to_work": False,
        "show_gpa": False,
        "show_contact": False,
        "show_achievements": True,
        "updated_at": utcnow(),
    }


def _skill_payload(item: StudentSkill) -> dict:
    return {
        "skill_id": item.skill_id,
        "name": item.skill.name,
        "level": item.level,
        "source": item.source,
        "created_at": item.created_at,
    }


def get_my_profile(db: Session, student: Student) -> dict:
    current = db.scalar(_profile_query(student.id))
    if current is None:
        raise NotFoundError("Không tìm thấy hồ sơ sinh viên")

    school_certificates = [
        item for item in current.certificates if item.source == CertificateSource.SCHOOL
    ]
    self_certificates = [
        item for item in current.certificates if item.source == CertificateSource.SELF
    ]
    self_skills = [item for item in current.skills if item.source == SkillSource.SELF]

    return {
        "official": {
            "id": current.id,
            "student_code": current.student_code,
            "full_name": current.full_name,
            "date_of_birth": current.date_of_birth,
            "class_name": current.class_name,
            "cohort": current.cohort,
            "gpa": current.gpa,
            "academic_result": current.academic_result,
            "phone": current.phone,
            "faculty": current.faculty,
            "major": current.major,
            "synced_at": current.synced_at,
            "certificates": school_certificates,
            "achievements": current.achievements,
        },
        "self_declared": {
            "profile": _profile_payload(current.profile, current.id),
            "skills": [_skill_payload(item) for item in self_skills],
            "experiences": current.experiences,
            "projects": current.projects,
            "certificates": self_certificates,
        },
    }


def update_profile(db: Session, student: Student, data: ProfileUpdate) -> StudentProfile:
    profile = db.get(StudentProfile, student.id)
    if profile is None:
        profile = StudentProfile(student_id=student.id)
        db.add(profile)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    profile.updated_at = utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def list_skills(db: Session, student: Student) -> list[dict]:
    stmt = (
        select(StudentSkill)
        .where(StudentSkill.student_id == student.id, StudentSkill.source == SkillSource.SELF)
        .options(joinedload(StudentSkill.skill))
        .order_by(StudentSkill.skill_id)
    )
    return [_skill_payload(item) for item in db.scalars(stmt).all()]


def create_skill(db: Session, student: Student, data: SkillCreate) -> dict:
    skill = db.get(Skill, data.skill_id)
    if skill is None or not skill.is_active:
        raise NotFoundError("Không tìm thấy kỹ năng")
    existing = db.get(StudentSkill, (student.id, data.skill_id))
    if existing is not None:
        raise ConflictError("Kỹ năng đã có trong hồ sơ")
    item = StudentSkill(
        student_id=student.id,
        skill_id=data.skill_id,
        level=data.level,
        source=SkillSource.SELF,
    )
    db.add(item)
    db.commit()
    stmt = (
        select(StudentSkill)
        .where(StudentSkill.student_id == student.id, StudentSkill.skill_id == data.skill_id)
        .options(joinedload(StudentSkill.skill))
    )
    return _skill_payload(db.scalar(stmt))


def _get_self_skill(db: Session, student: Student, skill_id: int) -> StudentSkill:
    item = db.get(StudentSkill, (student.id, skill_id))
    if item is None or item.source != SkillSource.SELF:
        raise NotFoundError("Không tìm thấy kỹ năng tự khai")
    return item


def update_skill(db: Session, student: Student, skill_id: int, data: SkillUpdate) -> dict:
    item = _get_self_skill(db, student, skill_id)
    item.level = data.level
    db.commit()
    stmt = (
        select(StudentSkill)
        .where(StudentSkill.student_id == student.id, StudentSkill.skill_id == skill_id)
        .options(joinedload(StudentSkill.skill))
    )
    return _skill_payload(db.scalar(stmt))


def delete_skill(db: Session, student: Student, skill_id: int) -> None:
    db.delete(_get_self_skill(db, student, skill_id))
    db.commit()


def list_experiences(db: Session, student: Student) -> list[StudentExperience]:
    stmt = (
        select(StudentExperience)
        .where(StudentExperience.student_id == student.id)
        .order_by(StudentExperience.start_date.desc(), StudentExperience.id.desc())
    )
    return list(db.scalars(stmt).all())


def _get_experience(db: Session, student: Student, item_id: int) -> StudentExperience:
    item = db.get(StudentExperience, item_id)
    if item is None or item.student_id != student.id:
        raise NotFoundError("Không tìm thấy kinh nghiệm")
    return item


def create_experience(
    db: Session, student: Student, data: ExperienceCreate
) -> StudentExperience:
    item = StudentExperience(student_id=student.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _validate_date_range(start_date: date | None, end_date: date | None) -> None:
    if start_date and end_date and end_date < start_date:
        raise BadRequestError("Ngày kết thúc không được trước ngày bắt đầu")


def update_experience(
    db: Session, student: Student, item_id: int, data: ExperienceUpdate
) -> StudentExperience:
    item = _get_experience(db, student, item_id)
    changes = data.model_dump(exclude_unset=True)
    _validate_date_range(
        changes.get("start_date", item.start_date), changes.get("end_date", item.end_date)
    )
    for field, value in changes.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_experience(db: Session, student: Student, item_id: int) -> None:
    db.delete(_get_experience(db, student, item_id))
    db.commit()


def list_projects(db: Session, student: Student) -> list[StudentProject]:
    stmt = (
        select(StudentProject)
        .where(StudentProject.student_id == student.id)
        .order_by(StudentProject.start_date.desc(), StudentProject.id.desc())
    )
    return list(db.scalars(stmt).all())


def _get_project(db: Session, student: Student, item_id: int) -> StudentProject:
    item = db.get(StudentProject, item_id)
    if item is None or item.student_id != student.id:
        raise NotFoundError("Không tìm thấy dự án")
    return item


def create_project(db: Session, student: Student, data: ProjectCreate) -> StudentProject:
    item = StudentProject(student_id=student.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_project(
    db: Session, student: Student, item_id: int, data: ProjectUpdate
) -> StudentProject:
    item = _get_project(db, student, item_id)
    changes = data.model_dump(exclude_unset=True)
    _validate_date_range(
        changes.get("start_date", item.start_date), changes.get("end_date", item.end_date)
    )
    for field, value in changes.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_project(db: Session, student: Student, item_id: int) -> None:
    db.delete(_get_project(db, student, item_id))
    db.commit()


def list_certificates(db: Session, student: Student) -> list[StudentCertificate]:
    stmt = (
        select(StudentCertificate)
        .where(StudentCertificate.student_id == student.id)
        .order_by(StudentCertificate.issued_at.desc(), StudentCertificate.id.desc())
    )
    return list(db.scalars(stmt).all())


def _get_self_certificate(
    db: Session, student: Student, item_id: int
) -> StudentCertificate:
    item = db.get(StudentCertificate, item_id)
    if (
        item is None
        or item.student_id != student.id
        or item.source != CertificateSource.SELF
    ):
        raise NotFoundError("Không tìm thấy chứng chỉ tự khai")
    return item


def create_certificate(
    db: Session, student: Student, data: CertificateCreate
) -> StudentCertificate:
    item = StudentCertificate(
        student_id=student.id,
        source=CertificateSource.SELF,
        is_verified=False,
        **data.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_certificate(
    db: Session, student: Student, item_id: int, data: CertificateUpdate
) -> StudentCertificate:
    item = _get_self_certificate(db, student, item_id)
    changes = data.model_dump(exclude_unset=True)
    _validate_date_range(
        changes.get("issued_at", item.issued_at), changes.get("expires_at", item.expires_at)
    )
    for field, value in changes.items():
        setattr(item, field, value)
    # Nội dung tự khai thay đổi thì nhà trường phải xác thực lại.
    item.is_verified = False
    item.verified_by = None
    item.verified_at = None
    db.commit()
    db.refresh(item)
    return item


def delete_certificate(db: Session, student: Student, item_id: int) -> None:
    db.delete(_get_self_certificate(db, student, item_id))
    db.commit()


def list_achievements(db: Session, student: Student):
    current = db.scalar(
        select(Student)
        .where(Student.id == student.id)
        .options(selectinload(Student.achievements))
    )
    if current is None:
        raise NotFoundError("Không tìm thấy hồ sơ sinh viên")
    return current.achievements


def list_internship_assignments(db: Session, student: Student) -> list[TermStudent]:
    stmt = (
        select(TermStudent)
        .where(TermStudent.student_id == student.id)
        .options(joinedload(TermStudent.term), joinedload(TermStudent.lecturer))
        .order_by(TermStudent.created_at.desc(), TermStudent.id.desc())
    )
    return list(db.scalars(stmt).all())
