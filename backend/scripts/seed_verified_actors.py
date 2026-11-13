"""Script khởi tạo (seed) tài khoản mẫu cho từng Actor với trạng thái ĐÃ XÁC THỰC 100%.

Các Actor được tạo:
1. ADMIN: admin@school.edu.vn (Quản trị viên nhà trường)
2. COMPANY: company@techcorp.vn (Doanh nghiệp tuyển dụng - Đã duyệt OTP + xác thực MST + MOU số hóa)
3. STUDENT: student@school.edu.vn (Sinh viên / Freelancer - Đã xác thực email trường + có hồ sơ & CV)
4. CLIENT: client@clientcorp.vn (Khách hàng thuê Freelancer - Đã xác thực tài khoản & hồ sơ)

Mật khẩu chung cho tất cả các tài khoản: Password@123

Cách chạy:
    cd backend
    python -m scripts.seed_verified_actors
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.enums import (
    CVType,
    UserRole,
    UserStatus,
)
from app.core.security import hash_password
from app.models import (
    CV,
    Admin,
    ClientProfile,
    Company,
    CompanyVerification,
    Faculty,
    Major,
    MouAgreement,
    Skill,
    StoredFile,
    Student,
    StudentProfile,
    StudentSkill,
    User,
)

PASSWORD = "Password@123"
NOW = datetime.now(timezone.utc)


def get_or_create_user(db: Session, email: str, role: UserRole) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(PASSWORD),
            role=role,
            status=UserStatus.ACTIVE,
            email_verified_at=NOW,
            phone_verified_at=NOW,
        )
        db.add(user)
        db.flush()
    else:
        user.role = role
        user.status = UserStatus.ACTIVE
        user.password_hash = hash_password(PASSWORD)
        user.email_verified_at = NOW
        db.flush()
    return user


def seed_actors(db: Session) -> None:
    # 0. Khởi tạo Kỹ năng & Khoa / Ngành cơ bản
    faculty = db.scalar(select(Faculty).where(Faculty.code == "CNTT"))
    if not faculty:
        faculty = Faculty(code="CNTT", name="Khoa Công nghệ thông tin")
        db.add(faculty)
        db.flush()

    major = db.scalar(select(Major).where(Major.code == "7480201"))
    if not major:
        major = Major(faculty_id=faculty.id, code="7480201", name="Kỹ thuật Phần mềm")
        db.add(major)
        db.flush()

    for skill_name, category in [
        ("Python", "Backend"),
        ("FastAPI", "Backend"),
        ("React", "Frontend"),
        ("TypeScript", "Frontend"),
        ("MariaDB", "Database"),
        ("Figma", "Design"),
    ]:
        if not db.scalar(select(Skill).where(Skill.name == skill_name)):
            db.add(Skill(name=skill_name, category=category))
    db.flush()

    # =========================================================================
    # 1. ACTOR: ADMIN (Quản trị viên nhà trường)
    # =========================================================================
    admin_user = get_or_create_user(db, "admin@school.edu.vn", UserRole.ADMIN)
    admin_profile = db.scalar(select(Admin).where(Admin.user_id == admin_user.id))
    if not admin_profile:
        admin_profile = Admin(
            user_id=admin_user.id,
            full_name="Quản trị viên Nhà trường",
            position="Phòng Hợp tác Doanh nghiệp & Đào tạo",
        )
        db.add(admin_profile)
        db.flush()

    # =========================================================================
    # 2. ACTOR: COMPANY (Doanh nghiệp tuyển dụng - Xác thực đầy đủ)
    # =========================================================================
    company_user = get_or_create_user(db, "company@techcorp.vn", UserRole.COMPANY)
    company = db.scalar(select(Company).where(Company.user_id == company_user.id))
    if not company:
        company = Company(
            user_id=company_user.id,
            name="Công ty Cổ phần Công nghệ TechCorp",
            tax_code="0109998888",
            contact_name="Nguyễn Văn Giám Đốc",
            contact_phone="02439998888",
            website="https://techcorp.vn",
            address="Tầng 10, Keangnam Landmark 72, Hà Nội",
            description="Doanh nghiệp phần mềm và giải pháp chuyển đổi số.",
            verification_status="APPROVED",
            business_status="VERIFIED",
            operation_status="ENABLED",
        )
        db.add(company)
        db.flush()
    else:
        company.verification_status = "APPROVED"
        company.business_status = "VERIFIED"
        company.operation_status = "ENABLED"
        db.flush()

    # Xác thực doanh nghiệp (CompanyVerification)
    comp_verif = db.scalar(select(CompanyVerification).where(CompanyVerification.company_id == company.id))
    if not comp_verif:
        comp_verif = CompanyVerification(
            company_id=company.id,
            tax_code="0109998888",
            company_name="Công ty Cổ phần Công nghệ TechCorp",
            legal_representative="Nguyễn Văn Giám Đốc",
            business_address="Tầng 10, Keangnam Landmark 72, Hà Nội",
            email_otp_verified=True,
            verification_status="VERIFIED",
            reviewer_user_id=admin_user.id,
            reviewed_at=NOW,
        )
        db.add(comp_verif)
        db.flush()
    else:
        comp_verif.email_otp_verified = True
        comp_verif.verification_status = "VERIFIED"
        comp_verif.reviewer_user_id = admin_user.id
        comp_verif.reviewed_at = NOW
        db.flush()

    # Thỏa thuận hợp tác MOU (MouAgreement - Digital Signature)
    mou_file = db.scalar(select(StoredFile).where(StoredFile.storage_key == "mou_techcorp_2026.pdf"))
    if not mou_file:
        mou_file = StoredFile(
            uploaded_by=company_user.id,
            storage_key="mou_techcorp_2026.pdf",
            original_name="mou_techcorp_2026.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            category="MOU_DOCUMENT",
            scan_status="CLEAN",
            availability_status="AVAILABLE",
        )
        db.add(mou_file)
        db.flush()

    mou = db.scalar(select(MouAgreement).where(MouAgreement.company_id == company.id))
    if not mou:
        mou = MouAgreement(
            company_id=company.id,
            agreement_code="MOU-TECHCORP-2026",
            document_file_id=mou_file.id,
            school_name="Trường Đại học Công nghệ",
            school_signer_name="PGS.TS. Trần Hiệu Trưởng",
            school_signer_position="Hiệu trưởng",
            company_signer_name="Nguyễn Văn Giám Đốc",
            company_signer_position="Tổng Giám Đốc",
            mou_type="DIGITAL_SIGNATURE",
            signature_method="EXTERNALLY_DIGITALLY_SIGNED",
            signature_verification_status="CRYPTOGRAPHICALLY_VERIFIED",
            status="ACTIVE",
            signer_tax_code="0109998888",
            signer_common_name="CONG TY CO PHAN CONG NGHE TECHCORP",
            certificate_issuer="VNPT-CA",
            signed_at=NOW,
            effective_from=NOW.date(),
            effective_until=(NOW + timedelta(days=365)).date(),
            scope_json={"internship": True, "recruitment": True, "sponsorship": True},
            reviewed_by=admin_user.id,
            reviewed_at=NOW,
            review_note="MOU số hóa đã được nhà trường xác thực chữ ký số hợp lệ.",
        )
        db.add(mou)
        db.flush()

    # =========================================================================
    # 3. ACTOR: STUDENT (Sinh viên / Freelancer)
    # =========================================================================
    student_user = get_or_create_user(db, "student@school.edu.vn", UserRole.STUDENT)
    student = db.scalar(select(Student).where(Student.user_id == student_user.id))
    if not student:
        student = Student(
            user_id=student_user.id,
            student_code="SV2026001",
            full_name="Nguyễn Văn Sinh Viên",
            class_name="CNTT1-K65",
            cohort="K65",
            faculty_id=faculty.id,
            major_id=major.id,
            gpa=3.65,
            phone="0912345678",
            date_of_birth=datetime(2003, 5, 20).date(),
        )
        db.add(student)
        db.flush()

    profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student.id))
    if not profile:
        profile = StudentProfile(
            student_id=student.id,
            is_open_to_work=True,
            show_gpa=True,
            show_contact=True,
            show_achievements=True,
            bio="Sinh viên năm 4 chuyên ngành Kỹ thuật Phần mềm, có kinh nghiệm làm Fullstack Web và Freelancer.",
        )
        db.add(profile)
        db.flush()

    # Kỹ năng sinh viên
    for sk_name in ["Python", "FastAPI", "React", "TypeScript"]:
        sk = db.scalar(select(Skill).where(Skill.name == sk_name))
        if sk and not db.scalar(select(StudentSkill).where(StudentSkill.student_id == student.id, StudentSkill.skill_id == sk.id)):
            db.add(StudentSkill(student_id=student.id, skill_id=sk.id))
    db.flush()

    # CV online mặc định
    cv = db.scalar(select(CV).where(CV.student_id == student.id, CV.deleted_at.is_(None)))
    if not cv:
        db.add(
            CV(
                student_id=student.id,
                title="CV Lập trình viên Fullstack",
                type=CVType.ONLINE,
                is_default=True,
                content_json={
                    "headline": "Fullstack Web Developer (FastAPI / React)",
                    "summary": "Thành thạo lập trình Backend FastAPI, MariaDB và Frontend React TypeScript.",
                    "skills": ["Python", "FastAPI", "React", "TypeScript", "MariaDB"],
                    "education": "Đại học Công nghệ - GPA: 3.65/4.0",
                },
            )
        )
        db.flush()

    # =========================================================================
    # 4. ACTOR: CLIENT (Khách hàng thuê Freelancer)
    # =========================================================================
    client_user = get_or_create_user(db, "client@clientcorp.vn", UserRole.CLIENT)
    client_profile = db.scalar(select(ClientProfile).where(ClientProfile.user_id == client_user.id))
    if not client_profile:
        client_profile = ClientProfile(
            user_id=client_user.id,
            full_name="Trần Thị Tuyển Dụng",
            address="Số 20 Duy Tân, Cầu Giấy, Hà Nội",
        )
        db.add(client_profile)
        db.flush()

    db.commit()
    print("=" * 60)
    print(">>> KHOI TAO THANH CONG CAC TAI KHOAN MAU (DA XAC THUC 100%):")
    print(f"1. ADMIN:   admin@school.edu.vn    | Pass: {PASSWORD}")
    print(f"2. COMPANY: company@techcorp.vn    | Pass: {PASSWORD}")
    print(f"3. STUDENT: student@school.edu.vn  | Pass: {PASSWORD}")
    print(f"4. CLIENT:  client@clientcorp.vn   | Pass: {PASSWORD}")
    print("=" * 60)


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_actors(session)
