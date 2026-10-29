"""Dữ liệu mẫu cho môi trường dev:  python -m scripts.seed   (chạy trong thư mục backend/)

Idempotent: chạy nhiều lần không tạo trùng. Mật khẩu mọi tài khoản mẫu: Password@123
  admin@school.edu.vn  (ADMIN)   |   sv001@school.edu.vn (STUDENT)   |   hr@acme.vn (COMPANY)
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.enums import UserRole, UserStatus, VerificationStatus
from app.core.security import hash_password
from app.models import (
    Admin,
    Company,
    Faculty,
    Industry,
    JobType,
    Major,
    Skill,
    SkillAlias,
    Student,
    StudentProfile,
    User,
)

PASSWORD = "Password@123"

JOB_TYPES = [("INTERN", "Thực tập"), ("FRESHER", "Fresher"), ("PART_TIME", "Bán thời gian"), ("FULL_TIME", "Toàn thời gian")]
INDUSTRIES = ["Phần mềm", "Giao thông vận tải", "Tài chính - Ngân hàng", "Thương mại điện tử"]
SKILLS = {
    "Python": ("Backend", []),
    "FastAPI": ("Backend", []),
    "React": ("Frontend", ["ReactJS", "React.js"]),
    "TypeScript": ("Frontend", ["TS"]),
    "MySQL": ("Database", ["MariaDB"]),
    "Docker": ("DevOps", []),
    "Giao tiếp": ("Soft skill", []),
}


def get_or_create_user(db: Session, email: str, role: UserRole) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(PASSWORD), role=role, status=UserStatus.ACTIVE)
        db.add(user)
        db.flush()
    return user


def seed(db: Session) -> None:
    for code, name in JOB_TYPES:
        if not db.scalar(select(JobType).where(JobType.code == code)):
            db.add(JobType(code=code, name=name))
    for name in INDUSTRIES:
        if not db.scalar(select(Industry).where(Industry.name == name)):
            db.add(Industry(name=name))
    for name, (category, aliases) in SKILLS.items():
        skill = db.scalar(select(Skill).where(Skill.name == name))
        if skill is None:
            skill = Skill(name=name, category=category)
            db.add(skill)
            db.flush()
            for alias in aliases:
                db.add(SkillAlias(skill_id=skill.id, alias=alias))

    faculty = db.scalar(select(Faculty).where(Faculty.code == "CNTT"))
    if faculty is None:
        faculty = Faculty(code="CNTT", name="Công nghệ thông tin")
        db.add(faculty)
        db.flush()
    major = db.scalar(select(Major).where(Major.code == "7480201"))
    if major is None:
        major = Major(faculty_id=faculty.id, code="7480201", name="Công nghệ thông tin")
        db.add(major)
        db.flush()

    # Admin
    admin_user = get_or_create_user(db, "admin@school.edu.vn", UserRole.ADMIN)
    if not db.scalar(select(Admin).where(Admin.user_id == admin_user.id)):
        db.add(Admin(user_id=admin_user.id, full_name="Quản trị nhà trường", position="Phòng đào tạo"))

    # Sinh viên
    student_user = get_or_create_user(db, "sv001@school.edu.vn", UserRole.STUDENT)
    if not db.scalar(select(Student).where(Student.user_id == student_user.id)):
        student = Student(
            user_id=student_user.id,
            student_code="SV001",
            full_name="Nguyễn Văn A",
            class_name="CNTT1",
            faculty_id=faculty.id,
            major_id=major.id,
            cohort="K65",
            gpa=3.2,
        )
        db.add(student)
        db.flush()
        db.add(StudentProfile(student_id=student.id, is_open_to_work=True))

    # Doanh nghiệp (đã được duyệt)
    company_user = get_or_create_user(db, "hr@acme.vn", UserRole.COMPANY)
    if not db.scalar(select(Company).where(Company.user_id == company_user.id)):
        db.add(
            Company(
                user_id=company_user.id,
                name="ACME Software",
                tax_code="0123456789",
                verification_status=VerificationStatus.APPROVED,
            )
        )

    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("Seed xong. Mật khẩu các tài khoản mẫu:", PASSWORD)
