"""Thực tập theo đợt & kết quả thực tập. Người phụ trách: TV2.

Endpoints:
  - GET /internship-terms — danh sách đợt (admin: tất cả; student: đợt của mình), lọc năm học/học kỳ/status
  - POST /internship-terms — tạo đợt (admin)
  - GET/PUT /internship-terms/{id} — xem/sửa; POST /{id}/status — chuyển DRAFT->OPEN->ONGOING->CLOSED
  - GET /internship-terms/{id}/students — danh sách sinh viên của đợt (admin)
  - POST /internship-terms/{id}/students — chọn/thêm sinh viên vào đợt; DELETE /{id}/students/{student_id}
  - POST /internship-terms/{id}/students/import — import danh sách sinh viên của đợt từ Excel/CSV (theo student_code)
  - POST /internship-terms/{id}/assign-lecturers — phân công giảng viên hướng dẫn (hàng loạt)
  - GET /internship-terms/{id}/jobs — các tin tuyển dụng thuộc đợt
  - GET /internship-terms/{id}/results — kết quả thực tập của cả đợt
  - PUT /internship-terms/results/{result_id}/evaluation — DOANH NGHIỆP gửi đánh giá (company_evaluation, company_score); thông báo nhà trường
  - PUT /internship-terms/results/{result_id}/lecturer-review — giảng viên/admin nhập nhận xét, điểm
  - POST /internship-terms/results/{result_id}/confirm — admin xác nhận kết quả (PASSED/FAILED)

Khuôn mẫu: xem app/routers/catalog.py (router mỏng) + app/services/catalog_service.py (nghiệp vụ).
Router chỉ khai báo endpoint + quyền + response_model, gọi service, KHÔNG truy vấn DB trực tiếp.
"""
from fastapi import APIRouter, File, Response, UploadFile

from app.core.config import settings
from app.core.enums import InternshipResultStatus, TermStatus
from app.core.exceptions import BadRequestError
from app.dependencies import AdminUser, CurrentCompany, CurrentUser, DbSession, Pagination
from app.schemas.common import Page
from app.schemas.internship_terms import (
    AssignLecturers,
    AssignLecturersResult,
    CompanyEvaluation,
    InternshipResultRead,
    LecturerReview,
    ResultConfirm,
    TermCreate,
    TermImportResult,
    TermJobRead,
    TermRead,
    TermStatusChange,
    TermStudentAdd,
    TermStudentAddResult,
    TermStudentRead,
    TermUpdate,
)
from app.services import internship_service

router = APIRouter(prefix="/internship-terms", tags=["Internship Terms"])


# ---------------------------------------------------------------- Kết quả thực tập (khai báo trước /{term_id})
@router.put(
    "/results/{result_id}/evaluation",
    response_model=InternshipResultRead,
    summary="Doanh nghiệp gửi đánh giá sinh viên thực tập",
)
def submit_evaluation(result_id: int, data: CompanyEvaluation, db: DbSession, company: CurrentCompany):
    return internship_service.submit_company_evaluation(db, company, result_id, data)


@router.put(
    "/results/{result_id}/lecturer-review",
    response_model=InternshipResultRead,
    summary="Giảng viên/nhà trường nhập nhận xét và điểm",
)
def lecturer_review(result_id: int, data: LecturerReview, db: DbSession, _: AdminUser):
    return internship_service.lecturer_review(db, result_id, data)


@router.post(
    "/results/{result_id}/confirm",
    response_model=InternshipResultRead,
    summary="Nhà trường xác nhận kết quả (PASSED/FAILED)",
)
def confirm_result(result_id: int, data: ResultConfirm, db: DbSession, admin: AdminUser):
    return internship_service.confirm_result(db, admin, result_id, data.result)


# ---------------------------------------------------------------- Đợt thực tập
@router.get("", response_model=Page[TermRead], summary="Danh sách đợt thực tập")
def list_terms(
    db: DbSession,
    user: CurrentUser,
    pagination: Pagination,
    academic_year: str | None = None,
    semester: str | None = None,
    status: TermStatus | None = None,
):
    return internship_service.list_terms(
        db, user, pagination, academic_year=academic_year, semester=semester, status=status
    )


@router.post("", response_model=TermRead, status_code=201, summary="Tạo đợt thực tập")
def create_term(data: TermCreate, db: DbSession, admin: AdminUser):
    return internship_service.create_term(db, admin, data)


@router.get("/{term_id}", response_model=TermRead, summary="Chi tiết đợt thực tập")
def get_term(term_id: int, db: DbSession, user: CurrentUser):
    return internship_service.get_term_detail(db, user, term_id)


@router.put("/{term_id}", response_model=TermRead, summary="Cập nhật đợt thực tập")
def update_term(term_id: int, data: TermUpdate, db: DbSession, _: AdminUser):
    return internship_service.update_term(db, term_id, data)


@router.post("/{term_id}/status", response_model=TermRead, summary="Chuyển trạng thái đợt (DRAFT→OPEN→ONGOING→CLOSED)")
def change_term_status(term_id: int, data: TermStatusChange, db: DbSession, _: AdminUser):
    return internship_service.change_status(db, term_id, data.status)


# ---------------------------------------------------------------- Sinh viên trong đợt
@router.get("/{term_id}/students", response_model=Page[TermStudentRead], summary="Danh sách sinh viên của đợt")
def list_term_students(
    term_id: int,
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    q: str | None = None,
    lecturer_id: int | None = None,
):
    return internship_service.list_term_students(db, term_id, pagination, q=q, lecturer_id=lecturer_id)


@router.post(
    "/{term_id}/students", response_model=TermStudentAddResult, status_code=201, summary="Thêm sinh viên vào đợt"
)
def add_term_students(term_id: int, data: TermStudentAdd, db: DbSession, _: AdminUser):
    return internship_service.add_students(db, term_id, data.student_ids)


@router.post(
    "/{term_id}/students/import",
    response_model=TermImportResult,
    status_code=201,
    summary="Import danh sách sinh viên của đợt từ Excel/CSV (theo student_code)",
)
def import_term_students(
    term_id: int,
    db: DbSession,
    admin: AdminUser,
    file: UploadFile = File(description="File .xlsx hoặc .csv có cột student_code"),
):
    content = file.file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise BadRequestError(f"File vượt quá {settings.MAX_UPLOAD_MB}MB")
    return internship_service.import_term_students(db, admin, term_id, file.filename or "", content)


@router.delete("/{term_id}/students/{student_id}", status_code=204, summary="Xóa sinh viên khỏi đợt")
def remove_term_student(term_id: int, student_id: int, db: DbSession, _: AdminUser):
    internship_service.remove_student(db, term_id, student_id)
    return Response(status_code=204)


@router.post(
    "/{term_id}/assign-lecturers",
    response_model=AssignLecturersResult,
    summary="Phân công giảng viên hướng dẫn hàng loạt",
)
def assign_lecturers(term_id: int, data: AssignLecturers, db: DbSession, _: AdminUser):
    return internship_service.assign_lecturers(db, term_id, data.lecturer_id, data.student_ids)


# ---------------------------------------------------------------- Tin và kết quả của đợt
@router.get("/{term_id}/jobs", response_model=Page[TermJobRead], summary="Tin tuyển dụng thuộc đợt")
def list_term_jobs(term_id: int, db: DbSession, user: CurrentUser, pagination: Pagination):
    return internship_service.list_term_jobs(db, user, term_id, pagination)


@router.get("/{term_id}/results", response_model=Page[InternshipResultRead], summary="Kết quả thực tập của cả đợt")
def list_term_results(
    term_id: int,
    db: DbSession,
    _: AdminUser,
    pagination: Pagination,
    result: InternshipResultStatus | None = None,
    lecturer_id: int | None = None,
):
    return internship_service.list_results(
        db, term_id, pagination, result_status=result, lecturer_id=lecturer_id
    )
