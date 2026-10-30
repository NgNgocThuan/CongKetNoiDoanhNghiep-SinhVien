# Backend tích hợp — integration/backend

Bản này được tạo từ origin/main trong worktree riêng:
B:/project/student-connect/student-connect/tmp/backend-integration.
Thư mục làm việc ban đầu và các thay đổi chưa commit được giữ nguyên. Bản sao lưu:
tmp/backups/before-backend-integration-20261030.zip (tính từ workspace ban đầu).

## Các phần đã tích hợp

- TV1: auth-notifications 2f21ab4, users-moderation f408190, reports 59604b5.
- Phong: phong-backend 2385e42.
- TV4: companies-profile b120152, jobs 1b49f95, quan-ly-ung-vien-clean 8af335e.
- TV3: tv3-student-backend 3c746bd.
- Thuận: thuan-backend b1cf8a9.

Nhánh tv4-applications-invitations ca626cb là bản gần trùng chức năng với clean;
đã chọn clean để tích hợp thay vì đưa lại cùng tính năng từ hai lịch sử độc lập.
Các merge và bản sửa chỉ nằm trên integration/backend, chưa push và chưa merge main.

## Xung đột và lỗi đã xử lý

- Giữ schemas/applications.py cho phía sinh viên. Schema doanh nghiệp đặt ở
  schemas/company_applications.py; router Kanban sử dụng schema riêng này.
- Phân quyền/ẩn dữ liệu nằm trong company_application_service, không nằm trong
  schema và không sửa thuộc tính ORM khi serialize. GPA và liên hệ bị ẩn khi cờ
  riêng tư tương ứng tắt hoặc chưa có profile. Bộ lọc GPA chỉ xét hồ sơ cho phép xem GPA.
- Lọc kinh nghiệm bằng biểu thức SQL trước phân trang; total và pages được tính
  trên cùng tập dữ liệu đã lọc. Giữ cách tính tháng theo chênh lệch năm/tháng của
  code cũ, chưa gộp các khoảng kinh nghiệm chồng lấn.
- Bổ sung GET /api/v1/company/applications/{application_id}/cv: kiểm tra đúng công
  ty sở hữu đơn và trả đúng cv_snapshot_url của đơn đó. Response Kanban có
  cv_download_url trỏ endpoint này.
- GET /cvs/{cv_id}/download vẫn hỗ trợ công ty khi chỉ có một snapshot phân biệt.
  Nếu có nhiều snapshot cho cùng CV tại công ty, trả 409 APPLICATION_REQUIRED;
  frontend phải chuyển sang đường tải theo đơn để không lấy nhầm phiên bản.
- GPA NaN/Infinity bị báo lỗi theo dòng; các dòng hợp lệ tiếp tục được import.
- Danh mục, giảng viên, profile, CV và các mục tự khai chặn null ở các trường DB
  bắt buộc; trường nullable vẫn có thể xóa bằng null, trường không gửi được giữ nguyên.
- File Excel/CSV hỏng trả 400; giữ số dòng vật lý trong báo cáo kể cả có dòng trống.
  Dòng thừa ô bị báo lỗi riêng, không làm mất các dòng hợp lệ. Router đọc tối đa
  MAX_UPLOAD_MB + 1 byte trước khi từ chối file lớn.
- Sinh viên không còn thấy tin hết hạn trong danh sách tin của đợt; admin vẫn thấy.
- Lời mời dùng hàm utcnow dùng chung, bỏ datetime.utcnow đã deprecated.

Không thay đổi cấu trúc DB nên không thêm migration.

## Chạy trên máy

Mở terminal tại worktree backend, không phải thư mục backend cũ:

~~~powershell
cd B:\project\student-connect\student-connect\tmp\backend-integration\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
~~~

Tạo .env từ .env.example nếu chưa có; cấu hình DATABASE_URL và SECRET_KEY theo môi
trường của bạn. Với MariaDB phát triển theo Compose trong repo:

~~~powershell
docker compose up -d db
alembic upgrade head
python -m scripts.seed
$env:DEBUG = 'false'
uvicorn app.main:app --reload
~~~

Swagger: http://127.0.0.1:8000/docs. Seed chỉ dùng cho môi trường phát triển.
Dùng app.main:app vì bản tích hợp đã có auth thật; không cần dev_server đăng nhập tạm.

## Kiểm tra

~~~powershell
$env:DEBUG = 'false'
python -m pytest -q
python -m ruff check .
~~~

Đã bổ sung tests/test_integration_regressions.py, gồm regression cho các lỗi trên
và một luồng xuyên module: import -> kích hoạt -> đăng ký/duyệt công ty -> tạo/duyệt
job theo đợt -> matching -> mời -> CV -> ứng tuyển -> Kanban HIRED -> đánh giá/xác nhận
thực tập -> dashboard/export. Email và AI bên ngoài được giả lập trong test.

Smoke test server Uvicorn trên localhost: /health, /docs, /api/v1/openapi.json đều
HTTP 200; OpenAPI có 132 đường dẫn. Server kiểm tra đã dừng, không để chạy nền.

Chưa xác nhận MariaDB, SMTP hoặc dịch vụ AI thật. Unit/integration test dùng SQLite;
cần smoke test trên môi trường triển khai trước khi xem xét đưa vào main.

## Git và mở worktree

Thư mục workspace ban đầu vẫn ở feature/thuan-backend với thay đổi chưa commit.
Mở worktree ở đường dẫn trên để xem integration/backend. Không switch cùng nhánh
integration/backend ở workspace cũ vì nhánh đang được worktree sử dụng.

Khi nhóm đã review và bạn muốn đưa bản tích hợp lên GitHub, chạy trong worktree:

~~~powershell
git push -u origin integration/backend
~~~

Lệnh push chưa được thực hiện. Việc tạo PR/merge main cần được review theo quy ước nhóm.

Kết quả kiểm tra cuối: **204 passed** (93.34 giây), **Ruff: All checks passed**.
