# Bàn giao phần TV2 (Phong)

Phần việc của TV2 theo `TASKS.md`: danh mục, quản lý sinh viên + import, giảng viên, đợt thực tập + kết quả thực tập.
Trạng thái lúc bàn giao: `pytest` **35 test xanh**, `ruff check .` sạch. Chưa commit gì; tất cả đang ở working tree.

## 1. Danh sách file đã làm

### Sửa (file stub của TV2, đã viết đầy đủ)

| File                                            | Nội dung                                                                                                                            |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `backend/app/schemas/catalog.py`                | Thêm schema Major, Industry, JobType, Skill, SkillAlias                                                                             |
| `backend/app/services/catalog_service.py`       | CRUD + xóa mềm cho 4 loại danh mục, tìm kiếm kỹ năng, alias, **`normalize_skill_names`**                                            |
| `backend/app/routers/catalog.py`                | Endpoint `/catalog/majors`, `industries`, `job-types`, `skills`, `skills/search`, `skills/{id}/aliases`                             |
| `backend/app/schemas/admin_lecturers.py`        | Schema giảng viên                                                                                                                   |
| `backend/app/services/lecturer_service.py`      | CRUD giảng viên, ngừng hoạt động thay vì xóa                                                                                        |
| `backend/app/routers/admin_lecturers.py`        | Endpoint `/admin/lecturers`                                                                                                         |
| `backend/app/schemas/admin_students.py`         | Schema sinh viên (danh sách, chi tiết tách official/self_declared), import, thành tích, chứng chỉ                                   |
| `backend/app/services/admin_student_service.py` | Danh sách/lọc, chi tiết, sửa học thuật, **import Excel/CSV**, cấp tài khoản + email kích hoạt, thành tích, xác thực chứng chỉ       |
| `backend/app/routers/admin_students.py`         | Endpoint `/admin/students/...` (gồm `/import`, `/imports`, `/sync` trả 501)                                                         |
| `backend/app/schemas/internship_terms.py`       | Schema đợt, sinh viên trong đợt, kết quả, đánh giá                                                                                  |
| `backend/app/services/internship_service.py`    | Đợt + chuyển trạng thái, thêm/xóa/import sinh viên, phân công giảng viên, tin thuộc đợt, kết quả thực tập, **`is_student_in_term`** |
| `backend/app/routers/internship_terms.py`       | Endpoint `/internship-terms/...`                                                                                                    |

### Thêm mới

| File                                     | Nội dung                                                                                                                                                                                                               |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/tests/test_catalog.py`          | Test ngành, lĩnh vực, loại hình, kỹ năng, alias, `normalize_skill_names`                                                                                                                                               |
| `backend/tests/test_admin_lecturers.py`  | Test giảng viên                                                                                                                                                                                                        |
| `backend/tests/test_admin_students.py`   | Test import (9 dòng, 7 dòng lỗi cố ý), upsert, Excel tiêu đề tiếng Việt, danh sách, sửa, cấp tài khoản, thành tích, chứng chỉ                                                                                          |
| `backend/tests/test_internship_terms.py` | Test đợt, chuyển trạng thái, sinh viên trong đợt, import, phân công, tin theo đợt, đánh giá/xác nhận kết quả, quyền                                                                                                    |
| `backend/scripts/dev_server.py`          | **Ngoài phạm vi TV2**: server dev, thêm endpoint đăng nhập tạm để nút Authorize của Swagger dùng được khi TV1 chưa xong. Chạy bằng `uvicorn scripts.dev_server:app --reload`. Tự tắt khi `/auth/token` thật xuất hiện. |
| `backend/tests/test_dev_server.py`       | Test cho file trên                                                                                                                                                                                                     |
| `backend/docs/BAN_GIAO_TV2.md`           | File này                                                                                                                                                                                                               |

Không sửa: model, migration, `conftest.py`, `main.py`, file của TV1/TV3/TV4/TV5. Không có file nào khác bị thay đổi.

## 2. Hàm cung cấp cho người khác (chữ ký đúng như `TASKS.md` mục 4)

- `catalog_service.normalize_skill_names(db, names) -> list[Skill]` (TV5 dùng). Tra tên và alias không phân biệt hoa thường, chỉ lấy kỹ năng đang hoạt động, bỏ trùng, bỏ tên lạ.
- `internship_service.is_student_in_term(db, student_id, term_id) -> bool` (TV3, TV4, TV5 dùng).

## 3. Quy tắc nghiệp vụ đã cài

- **Danh mục:** đọc cho mọi user đăng nhập, ghi chỉ admin; xóa mềm bằng `is_active`; tên kỹ năng và alias không được trùng nhau (không phân biệt hoa thường); ngành phải thuộc một khoa có thật.
- **Import sinh viên:** upsert theo `student_code`; mỗi dòng lưu độc lập (savepoint), dòng lỗi ghi vào `ImportBatch.error_report`; ô trống khi cập nhật thì giữ dữ liệu cũ; `faculty`/`major` ghi mã hoặc tên; nhận tiêu đề cột tiếng Việt; sinh viên mới ở trạng thái `PENDING_ACTIVATION`, có `StudentProfile` rỗng, được gửi email kích hoạt.
- **Đợt thực tập:** chỉ chuyển tiến một bước `DRAFT→OPEN→ONGOING→CLOSED`; đợt `CLOSED` không sửa được, không đổi danh sách sinh viên; mỗi sinh viên thêm vào đợt có sẵn một `InternshipResult` trạng thái `PENDING`.
- **Kết quả thực tập:** doanh nghiệp chỉ đánh giá được khi có đơn `HIRED` vào tin của công ty đó thuộc đúng đợt, và đợt đang `ONGOING`/`CLOSED`; điểm 0 đến 10; admin nhận thông báo khi có đánh giá; sau khi admin xác nhận PASSED/FAILED thì khóa sửa và sinh viên được thông báo.

## 4. Điểm cần Phong xác nhận hoặc nối với module khác

1. **Link kích hoạt** gửi trong email là `{FRONTEND_URL}/activate?token=...`, hạn 7 ngày, token lưu hash trong `PasswordResetToken`. Cần khớp với `POST /auth/activate` của TV1 và trang kích hoạt của frontend.
2. **Giảng viên chưa có tài khoản** (chỉ có 3 role), nên "giảng viên nhận xét" do admin nhập (`PUT /internship-terms/results/{id}/lecturer-review`).
3. **`GET /internship-terms/{id}/jobs`** tự truy vấn bảng `jobs` vì `job_service` của TV4 chưa có; khi TV4 xong có thể đổi sang gọi hàm của họ.
4. Thêm hai endpoint ngoài danh sách gốc: `GET /internship-terms/{id}/students` và `GET /admin/students/imports` (lịch sử import).
5. `POST /admin/students/sync` trả 501 vì chưa có nguồn đồng bộ.
6. Test chạy trên SQLite trong bộ nhớ; đã thử thủ công trên MariaDB thật (Docker) một phần (xem danh mục, đăng nhập dev). Nên chạy thử đầy đủ import và đợt thực tập trên MariaDB trước khi merge.
7. Test `test_admin_students.py` có fixture tắt tác vụ gửi email nền (vì tác vụ này mở session riêng tới MariaDB thật). Nên bổ sung fixture dùng chung trong `conftest.py` khi cả nhóm thống nhất.

## 5. Cách chạy lại

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
$env:PYTHONUTF8=1
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
ruff check .
```

Chạy thử trên Swagger bằng MariaDB thật: `docker compose up -d db`, `alembic upgrade head`, `python -m scripts.seed`, rồi `uvicorn scripts.dev_server:app --reload`, mở `http://127.0.0.1:8000/docs` (dùng `127.0.0.1`, không dùng `localhost`, nếu máy đang có ứng dụng khác chiếm cổng 8000 bên IPv6). Đăng nhập bằng nút Authorize: `admin@school.edu.vn` / `Password@123`.
