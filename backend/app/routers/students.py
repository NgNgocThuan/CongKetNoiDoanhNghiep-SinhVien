"""Student-owned profile endpoints."""
from fastapi import APIRouter, Response

from app.dependencies import CurrentStudent, DbSession
from app.schemas.students import (
    AchievementRead,
    CertificateCreate,
    CertificateRead,
    CertificateUpdate,
    ExperienceCreate,
    ExperienceRead,
    ExperienceUpdate,
    InternshipAssignmentRead,
    ProfileRead,
    ProfileUpdate,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    SkillCreate,
    SkillItem,
    SkillUpdate,
    StudentFullProfile,
)
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentFullProfile, summary="Xem hồ sơ sinh viên của tôi")
def get_my_profile(db: DbSession, student: CurrentStudent):
    return student_service.get_my_profile(db, student)


@router.put(
    "/me/profile", response_model=ProfileRead, summary="Cập nhật thông tin tự khai và quyền riêng tư"
)
def update_profile(data: ProfileUpdate, db: DbSession, student: CurrentStudent):
    return student_service.update_profile(db, student, data)


@router.get("/me/skills", response_model=list[SkillItem], summary="Danh sách kỹ năng tự khai")
def list_skills(db: DbSession, student: CurrentStudent):
    return student_service.list_skills(db, student)


@router.post(
    "/me/skills", response_model=SkillItem, status_code=201, summary="Thêm kỹ năng tự khai"
)
def create_skill(data: SkillCreate, db: DbSession, student: CurrentStudent):
    return student_service.create_skill(db, student, data)


@router.put(
    "/me/skills/{skill_id}", response_model=SkillItem, summary="Cập nhật mức kỹ năng tự khai"
)
def update_skill(skill_id: int, data: SkillUpdate, db: DbSession, student: CurrentStudent):
    return student_service.update_skill(db, student, skill_id, data)


@router.delete("/me/skills/{skill_id}", status_code=204, summary="Xóa kỹ năng tự khai")
def delete_skill(skill_id: int, db: DbSession, student: CurrentStudent):
    student_service.delete_skill(db, student, skill_id)
    return Response(status_code=204)


@router.get(
    "/me/experiences", response_model=list[ExperienceRead], summary="Danh sách kinh nghiệm"
)
def list_experiences(db: DbSession, student: CurrentStudent):
    return student_service.list_experiences(db, student)


@router.post(
    "/me/experiences", response_model=ExperienceRead, status_code=201, summary="Thêm kinh nghiệm"
)
def create_experience(data: ExperienceCreate, db: DbSession, student: CurrentStudent):
    return student_service.create_experience(db, student, data)


@router.put(
    "/me/experiences/{experience_id}",
    response_model=ExperienceRead,
    summary="Cập nhật kinh nghiệm",
)
def update_experience(
    experience_id: int, data: ExperienceUpdate, db: DbSession, student: CurrentStudent
):
    return student_service.update_experience(db, student, experience_id, data)


@router.delete(
    "/me/experiences/{experience_id}", status_code=204, summary="Xóa kinh nghiệm"
)
def delete_experience(experience_id: int, db: DbSession, student: CurrentStudent):
    student_service.delete_experience(db, student, experience_id)
    return Response(status_code=204)


@router.get("/me/projects", response_model=list[ProjectRead], summary="Danh sách dự án cá nhân")
def list_projects(db: DbSession, student: CurrentStudent):
    return student_service.list_projects(db, student)


@router.post(
    "/me/projects", response_model=ProjectRead, status_code=201, summary="Thêm dự án cá nhân"
)
def create_project(data: ProjectCreate, db: DbSession, student: CurrentStudent):
    return student_service.create_project(db, student, data)


@router.put(
    "/me/projects/{project_id}", response_model=ProjectRead, summary="Cập nhật dự án cá nhân"
)
def update_project(
    project_id: int, data: ProjectUpdate, db: DbSession, student: CurrentStudent
):
    return student_service.update_project(db, student, project_id, data)


@router.delete("/me/projects/{project_id}", status_code=204, summary="Xóa dự án cá nhân")
def delete_project(project_id: int, db: DbSession, student: CurrentStudent):
    student_service.delete_project(db, student, project_id)
    return Response(status_code=204)


@router.get(
    "/me/certificates", response_model=list[CertificateRead], summary="Danh sách chứng chỉ"
)
def list_certificates(db: DbSession, student: CurrentStudent):
    return student_service.list_certificates(db, student)


@router.post(
    "/me/certificates",
    response_model=CertificateRead,
    status_code=201,
    summary="Thêm chứng chỉ tự khai",
)
def create_certificate(data: CertificateCreate, db: DbSession, student: CurrentStudent):
    return student_service.create_certificate(db, student, data)


@router.put(
    "/me/certificates/{certificate_id}",
    response_model=CertificateRead,
    summary="Cập nhật chứng chỉ tự khai",
)
def update_certificate(
    certificate_id: int, data: CertificateUpdate, db: DbSession, student: CurrentStudent
):
    return student_service.update_certificate(db, student, certificate_id, data)


@router.delete(
    "/me/certificates/{certificate_id}", status_code=204, summary="Xóa chứng chỉ tự khai"
)
def delete_certificate(certificate_id: int, db: DbSession, student: CurrentStudent):
    student_service.delete_certificate(db, student, certificate_id)
    return Response(status_code=204)


@router.get(
    "/me/achievements",
    response_model=list[AchievementRead],
    summary="Xem thành tích do nhà trường xác nhận",
)
def list_achievements(db: DbSession, student: CurrentStudent):
    return student_service.list_achievements(db, student)


@router.get(
    "/me/internship",
    response_model=list[InternshipAssignmentRead],
    summary="Xem đợt thực tập và giảng viên hướng dẫn",
)
def list_internships(db: DbSession, student: CurrentStudent):
    return student_service.list_internship_assignments(db, student)
