# Quy ước dự án (Backend)

Mục tiêu: 5 người làm song song mà code vẫn đồng nhất, ít xung đột, dễ review.

## 1. Kiến trúc phân lớp

```
HTTP request
  └─ routers/      khai báo endpoint, quyền (Depends), response_model. KHÔNG có nghiệp vụ.
       └─ services/    toàn bộ nghiệp vụ + truy vấn DB. KHÔNG biết Request/Response.
            └─ models/     bảng + quan hệ. KHÔNG có nghiệp vụ.
schemas/   Pydantic cho dữ liệu vào/ra (tách riêng khỏi models)
utils/     hàm thuần dùng chung (không phụ thuộc domain)
ai/        gọi LLM, parse, tính điểm matching
tasks/     tác vụ chạy nền
core/      cấu hình, bảo mật, enum, exception (ít khi sửa)
```

Quy tắc cứng:
- Router **không** import `Session` để query; chỉ gọi `xxx_service.hàm(db, ...)`.
- Service **không** import từ `app.routers`; **không** raise `HTTPException` (dùng exception trong `core/exceptions.py`).
- Service tự `commit()` khi ghi. Router không gọi `db.commit()`.
- Response luôn là schema Pydantic (`response_model=`), không trả thẳng model SQLAlchemy.
- Enum dùng từ `core/enums.py`, giá trị phải khớp ENUM trong DB.
- Mỗi module = 1 router + 1 service + 1 schema (+ test). Tên file theo module; xem `docs/TASKS.md`.

## 2. Phân quyền (RBAC)

Dùng dependency ở `app/dependencies.py`, khai báo ngay trong tham số endpoint:

| Dependency | Ý nghĩa |
|---|---|
| `CurrentUser` | bất kỳ user đã đăng nhập và ACTIVE |
| `AdminUser` / `StudentUser` / `CompanyUser` | giới hạn theo role |
| `CurrentStudent` / `CurrentCompany` | lấy luôn hồ sơ Student / Company của user |

Hai lớp kiểm tra, **cả hai đều bắt buộc**:
1. **Role** ở router (dependency ở trên).
2. **Quyền sở hữu** ở service: sinh viên chỉ thao tác dữ liệu của mình; doanh nghiệp chỉ thao tác tin/đơn thuộc công ty mình. Sai quyền sở hữu: trả `NotFoundError` (404) thay vì 403 để không lộ sự tồn tại của dữ liệu.

## 3. Định dạng API

- Prefix: `/api/v1`. Đường dẫn dạng danh từ số nhiều, kebab-case: `/internship-terms`, `/saved-jobs`.
- Danh sách dùng phân trang: query `page` (từ 1), `size` (mặc định 20, tối đa 100). Response:
  `{"items": [...], "total": 120, "page": 1, "size": 20, "pages": 6}` (schema `Page[T]`, hàm `utils.pagination.paginate`).
- Lỗi luôn có dạng: `{"error": {"code": "NOT_FOUND", "message": "Không tìm thấy khoa"}}`.
  Mã HTTP: 400 dữ liệu sai · 401 chưa đăng nhập · 403 không đủ quyền · 404 không thấy · 409 trùng/xung đột · 422 sai định dạng (FastAPI tự sinh).
- Tạo mới trả `201`; xóa trả `204` (không body). Xóa dữ liệu danh mục/tài khoản dùng **xóa mềm** (`is_active`, `deleted_at`, `status`).
- Thời gian lưu **UTC** (`utils.datetime_utils.utcnow()`), trả về dạng ISO 8601.
- Mỗi endpoint phải có `summary=` tiếng Việt ngắn gọn để Swagger dễ đọc (Swagger chính là tài liệu API cho frontend).

## 4. Đặt tên

| Thứ | Quy ước | Ví dụ |
|---|---|---|
| File, hàm, biến | snake_case | `application_service.py`, `list_my_applications` |
| Class | PascalCase | `ApplicationStatusLog` |
| Bảng DB | snake_case, số nhiều | `application_status_logs` |
| Schema | `XCreate`, `XUpdate`, `XRead`, `XFilter` | `JobCreate`, `JobRead` |
| Service function | động từ + đối tượng | `create_job`, `approve_company`, `list_jobs` |
| Index/constraint | đặt tên rõ: `idx_`, `uq_`, `chk_` | `uq_applications_student_job` |

## 5. Git

Nhánh:
- `main`: ổn định, chỉ merge từ `develop` khi xong mốc.
- `develop`: nhánh tích hợp. **Không push trực tiếp**, chỉ merge qua Pull Request.
- Nhánh tính năng: `feature/<tv>-<module>-<mô-tả>` ví dụ `feature/tv3-applications-apply`. Sửa lỗi: `fix/<mô-tả>`.

Quy trình mỗi tính năng:
1. `git checkout develop && git pull` → tạo nhánh mới từ `develop`.
2. Commit nhỏ, thường xuyên. Trước khi mở PR: `git pull --rebase origin develop`, chạy `ruff check .` và `pytest`.
3. Mở PR vào `develop`, **ít nhất 1 người khác review** (ưu tiên người có module phụ thuộc). Squash merge.
4. PR nhỏ (dưới ~400 dòng) để review kịp. Một PR = một chức năng.

Commit message (Conventional Commits, tiếng Việt hoặc Anh đều được):
`feat(applications): ứng tuyển kèm chụp snapshot CV` · `fix(auth): chặn user bị khóa đăng nhập` · `test(jobs): ...` · `docs: ...` · `refactor: ...`

Tuyệt đối **không commit**: `.env`, file upload, mật khẩu/API key, `__pycache__`. Nếu lỡ commit bí mật: đổi key ngay, rồi báo nhóm.

## 6. File dùng chung (dễ gây xung đột)

Các file sau nhiều người cùng đụng. Quy tắc: sửa nhỏ, PR riêng, báo nhóm trước khi merge.

| File | Ai được sửa |
|---|---|
| `app/models/*.py` | người sở hữu domain đó; đổi cột/bảng phải kèm migration và báo cả nhóm |
| `app/core/*`, `app/dependencies.py` | TV1 (hoặc thống nhất cả nhóm) |
| `app/routers/__init__.py` | gần như không phải sửa: mọi router đã được đăng ký sẵn |
| `requirements.txt` | thêm thư viện thì ghi lý do trong PR |
| `database/schema.sql` | chỉ là tài liệu tham chiếu; nguồn sự thật của DB là **models + migration** |

## 7. Database & Migration (Alembic)

Nguồn sự thật = `app/models` + `alembic/versions`. `database/schema.sql` chỉ để đọc.

- Dựng DB: `alembic upgrade head` (migration `0001` đã chứa toàn bộ 37 bảng).
- Cần đổi cấu trúc (thêm cột/bảng): sửa model, rồi
  `alembic revision --autogenerate -m "mô tả ngắn"`, **đọc lại file sinh ra** (autogenerate không hoàn hảo), chạy `alembic upgrade head` thử.
- **Không** sửa migration đã merge. Muốn sửa tiếp thì tạo migration mới.
- Hai người cùng tạo migration một lúc sẽ ra 2 "head". Cách xử lý: người merge sau chạy `alembic merge heads -m "merge"`, hoặc rebase để `down_revision` nối tiếp.
- Tạo bảng/cột mới nhớ thêm vào `app/models/__init__.py` (nếu là model mới) và **báo nhóm** vì mọi người phải `alembic upgrade head` sau khi pull.
- Dữ liệu danh mục khởi tạo (loại hình công việc, kỹ năng...) đặt ở `scripts/seed.py`, không đặt trong migration.

## 8. Test

- Mỗi endpoint có ít nhất: 1 test chạy đúng (happy path), 1 test sai quyền, 1 test lỗi nghiệp vụ chính (trùng, không tìm thấy, sai trạng thái).
- Test dùng SQLite in-memory (`tests/conftest.py`), không cần MariaDB. Fixture: `client`, `db`, `make_user(role)`, `auth_headers(user)`. Xem mẫu `tests/test_catalog_faculty.py`.
- Một file test cho mỗi module: `tests/test_<module>.py`.
- Logic thuần (như `ai/matching_engine.py`) viết unit test không cần DB.
- Lưu ý khác biệt SQLite và MariaDB: không dùng cú pháp riêng của MariaDB (FULLTEXT, `ON DUPLICATE KEY`...) trong code mà test phải chạy qua; nếu bắt buộc, tách hàm để test riêng.

## 9. Hiệu năng và an toàn

- Tránh N+1: danh sách kèm quan hệ dùng `selectinload` / `joinedload`.
- Mọi danh sách phải phân trang; không `SELECT` toàn bảng.
- Không log mật khẩu, token, nội dung CV. Mật khẩu chỉ băm bằng `core.security.hash_password`.
- Dữ liệu cá nhân sinh viên khi trả cho doanh nghiệp/xuất báo cáo phải qua kiểm tra quyền riêng tư (`student_profiles.show_*`).
- Gọi API AI: luôn kiểm tra cache bằng `content_hash` trước; không gọi lặp cho dữ liệu không đổi.

## 10. Checklist trước khi mở Pull Request

- [ ] `ruff check .` sạch, `pytest` xanh
- [ ] Router mỏng, nghiệp vụ nằm ở service
- [ ] Có kiểm tra role **và** quyền sở hữu
- [ ] Có `response_model`, `summary`, mã trạng thái đúng
- [ ] Có test (đúng, sai quyền, lỗi nghiệp vụ)
- [ ] Nếu đổi model: có migration và đã báo nhóm
- [ ] Không có bí mật/`print` debug trong code
