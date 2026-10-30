"""Nhà trường: quản lý dữ liệu sinh viên. Người phụ trách: TV2.

Endpoints (chỉ admin):
  - GET /admin/students — danh sách, lọc faculty/major/cohort/q
  - GET /admin/students/{id} — chi tiết (dữ liệu trường + hồ sơ tự khai, phân biệt rõ nguồn)
  - PUT /admin/students/{id} — cập nhật dữ liệu học thuật (GPA, lớp, ngành, khóa...)
  - POST /admin/students/import — upload Excel/CSV (utils.spreadsheet): tạo/cập nhật Student + User(PENDING_ACTIVATION), ghi ImportBatch + error_report từng dòng
  - GET /admin/students/imports — lịch sử import; GET /admin/students/imports/{id} — chi tiết + dòng lỗi
  - POST /admin/students/{id}/issue-account — cấp/gửi lại email kích hoạt tài khoản (sinh token, dùng email_service)
  - POST /admin/students/{id}/achievements — thêm nghiên cứu khoa học/thành tích; DELETE .../achievements/{aid}
  - POST /admin/students/certificates/{cert_id}/verify — xác thực chứng chỉ tự khai (is_verified, verified_by/at)
  - POST /admin/students/sync — (tùy chọn) đồng bộ từ hệ thống đào tạo; chưa có nguồn nên trả 501

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""

from fastapi import APIRouter, BackgroundTasks, File, Response, UploadFile

from app.core.config import settings
from app.core.enums import ImportType, UserStatus
from app.core.exceptions import BadRequestError
from app.dependencies import AdminUser, DbSession, Pagination
from app.schemas.admin_students import (
    AchievementCreate,
    AchievementRead,
    AdminStudentDetail,
    AdminStudentRead,
    CertificateRead,
    ImportBatchDetail,
    ImportBatchRead,
    ImportResult,
    StudentAcademicUpdate,
)
from app.schemas.common import Message, Page
from app.services import admin_student_service

router = APIRouter(prefix="/admin/students", tags=["Admin - Students"])


@router.get("", response_model=Page[AdminStudentRead], summary="Danh sách sinh viên")
def list_students(
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    q: str | None = None,
    faculty_id: int | None = None,
    major_id: int | None = None,
    cohort: str | None = None,
    account_status: UserStatus | None = None,
):
    return admin_student_service.list_students(
        db,
        pagination,
        q=q,
        faculty_id=faculty_id,
        major_id=major_id,
        cohort=cohort,
        account_status=account_status,
    )


# ---- Import (khai báo trước /{student_id} để "imports" không bị hiểu là student_id)
@router.post(
    "/import",
    response_model=ImportResult,
    status_code=201,
    summary="Import sinh viên từ Excel/CSV (dòng lỗi được báo cáo, không làm hỏng cả file)",
)
def import_students(
    background_tasks: BackgroundTasks,
    db: DbSession,
    admin: AdminUser,
    file: UploadFile = File(description="File .xlsx hoặc .csv, dòng đầu là tiêu đề cột"),
):
    content = file.file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise BadRequestError(f"File vượt quá {settings.MAX_UPLOAD_MB}MB")
    return admin_student_service.import_students(
        db, background_tasks, admin, file.filename or "", content
    )


@router.get("/imports", response_model=Page[ImportBatchRead], summary="Lịch sử import")
def list_imports(
    db: DbSession, _: AdminUser, pagination: Pagination, type: ImportType | None = None
):
    return admin_student_service.list_import_batches(db, pagination, type=type)


@router.get(
    "/imports/{batch_id}",
    response_model=ImportBatchDetail,
    summary="Chi tiết lần import và các dòng lỗi",
)
def get_import(batch_id: int, db: DbSession, _: AdminUser):
    return admin_student_service.get_import_batch(db, batch_id)


@router.post(
    "/certificates/{certificate_id}/verify",
    response_model=CertificateRead,
    summary="Xác thực chứng chỉ tự khai",
)
def verify_certificate(certificate_id: int, db: DbSession, admin: AdminUser):
    return admin_student_service.verify_certificate(db, certificate_id, admin)


@router.post("/sync", status_code=501, summary="Đồng bộ từ hệ thống đào tạo (chưa hỗ trợ)")
def sync_students(db: DbSession, _: AdminUser):
    admin_student_service.sync_students(db)


# ---- Theo từng sinh viên
@router.get(
    "/{student_id}",
    response_model=AdminStudentDetail,
    summary="Chi tiết sinh viên (tách dữ liệu trường / tự khai)",
)
def get_student(student_id: int, db: DbSession, _: AdminUser):
    return admin_student_service.get_student_detail(db, student_id)


@router.put("/{student_id}", response_model=AdminStudentRead, summary="Cập nhật dữ liệu học thuật")
def update_student(student_id: int, data: StudentAcademicUpdate, db: DbSession, _: AdminUser):
    return admin_student_service.update_academic_data(db, student_id, data)


@router.post(
    "/{student_id}/issue-account",
    response_model=Message,
    summary="Cấp / gửi lại email kích hoạt tài khoản",
)
def issue_account(student_id: int, background_tasks: BackgroundTasks, db: DbSession, _: AdminUser):
    admin_student_service.issue_account(db, background_tasks, student_id)
    return Message(message="Đã gửi email kích hoạt")


@router.post(
    "/{student_id}/achievements",
    response_model=AchievementRead,
    status_code=201,
    summary="Thêm nghiên cứu khoa học / thành tích",
)
def add_achievement(student_id: int, data: AchievementCreate, db: DbSession, _: AdminUser):
    return admin_student_service.add_achievement(db, student_id, data)


@router.delete(
    "/{student_id}/achievements/{achievement_id}", status_code=204, summary="Xóa thành tích"
)
def delete_achievement(student_id: int, achievement_id: int, db: DbSession, _: AdminUser):
    admin_student_service.delete_achievement(db, student_id, achievement_id)
    return Response(status_code=204)
