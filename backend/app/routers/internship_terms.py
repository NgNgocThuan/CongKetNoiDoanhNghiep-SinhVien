"""Thực tập theo đợt & kết quả thực tập. Người phụ trách: TV2.

Endpoints cần làm:
  - GET /internship-terms — danh sách đợt (admin: tất cả; student: đợt của mình), lọc năm học/học kỳ/status
  - POST /internship-terms — tạo đợt (admin)
  - GET/PUT /internship-terms/{id} — xem/sửa; POST /{id}/status — chuyển DRAFT->OPEN->ONGOING->CLOSED
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
from fastapi import APIRouter

router = APIRouter(prefix="/internship-terms", tags=["Internship Terms"])

# TODO(TV2): triển khai các endpoint ở docstring trên.
