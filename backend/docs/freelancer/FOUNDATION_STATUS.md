# Bộ nền backend đã chuẩn bị và hướng dẫn bàn giao

Ngày 04/11/2026. Bộ nền phát hành trên main theo yêu cầu chủ dự án; dùng git log để xác định commit nền. Đã kiểm chứng trên MariaDB 10.11 chạy riêng bằng Docker ở cổng 3308; chưa áp dụng migration lên DB đang dùng hoặc thực hiện giao dịch payOS.

## 1. Phần đã có code

| Phần | File / nội dung |
|---|---|
| Schema | 49 bảng mới trong tám file `app/models/freelancer_*.py`; tổng 86 bảng ứng dụng khi cộng 37 bảng cũ. |
| Model cũ | `users` thêm liên hệ/xác minh; `companies` thêm xác minh pháp nhân/đình chỉ; company_documents thêm file/actor; không thay luồng duyệt cũ. |
| Role và enum | CLIENT trong core/enums.py; trạng thái mới trong core/freelancer_enums.py. |
| Migration | `alembic/versions/0002_freelancer_shared_foundation.py`, nối 0001; schema đóng băng, không import model hiện tại. |
| Tương thích | Backfill legal_name từ name, giữ APPROVED cũ, không tự VERIFIED/MOU ACTIVE, không seed tiền. |
| Bảo vệ DB | Composite FKs đúng cha, UQ từng cặp project/student, CHECK bảo toàn tiền; trigger append-only cho ledger/audit khi chạy migration. |
| DTO/ports | `app/contracts/freelancer/types.py`, `ports.py`; Python int, DTO immutable. |
| Transaction | `app/services/freelancer_commands.py`: run_command + acceptance coordinator; hỗ trợ read autobegin và rollback nguyên tử. |
| Finance chưa sẵn sàng | `app/services/freelancer_finance.py`: UnavailableFinancePort trả FINANCE_NOT_READY; không tự coi có vốn/chi thành công. |
| Dependency | `app/dependencies_freelancer.py`: onboarding có giới hạn, ClientUser, FreelanceClientUser; không nới auth router cũ. |
| JSON scalar | `app/schemas/freelancer_common.py`: EntityId/MoneyVnd truyền JSON chuỗi số, không nhận float/bool cho tiền. |
| Test chung | `tests/freelancer`: fixtures hai hợp đồng một dự án, context, fake, constraint/atomicity/migration tests. |
| SQL tham chiếu | `database/freelancer_schema.sql`, render offline từ 0001:0002; không dùng thay migration. |
| MariaDB test | `compose.freelancer-test.yml` + tests opt-in, tạo database riêng cho từng case. |

Model mới tập trung vào cấu trúc cột/FK/constraint; chưa thêm graph relationship ORM có cascade ghi/xóa tự động. Thành viên truy vấn theo FK và chỉ bổ sung relationship khi review, không tạo nguồn dữ liệu thứ hai. Không giao nhiệm vụ dựng lại các bảng này cho từng người.

## 2. Những gì chưa phải tính năng đã hoàn thành

- Chưa có router/service nghiệp vụ Freelancer đầy đủ cho A/B/C/D.
- Chưa có đăng nhập CLIENT/onboarding end-to-end mới; mới có role, cột và dependency để nhóm A triển khai.
- Chưa có finance writer/ledger posting service hoặc adapter payOS thực tế.
- Chưa có scheduler/worker claim/retry thật; mới có schema và contract để D/chủ dự án thực hiện.
- Chưa có flow request replay hoàn chỉnh; command_requests là schema nền, module coordinator cần triển khai dùng nó.
- Trigger không chứng minh tổng journal cân: writer phải kiểm tra tổng debit/credit trong TX và test đối soát.
- Chưa xác nhận DB runtime user đã bị thu hồi quyền UPDATE/DELETE/TRUNCATE/DDL. Trigger không thay thế phân quyền DB; tài khoản app không được quyền DROP/TRUNCATE/ALTER để vượt guard.
- Test fake không chứng minh chuyển tiền thật hoặc khả năng khóa MariaDB. Kết quả kiểm chứng được ghi riêng ở phần dưới.

### Kết quả kiểm tra trong phiên chuẩn bị

- Trước phát hành: xuất đúng index gồm bộ nền và source main sang checkout tách biệt, không lấy các thay đổi local ngoài phạm vi; chạy toàn bộ backend với MariaDB test thật: **225 passed**, Ruff sạch. Đây là kết quả cho bộ code phát hành, khác các lượt trước có thêm test/config local chưa commit.
- Backend toàn bộ ở lần hồi quy trước: **224 passed, 3 skipped**. Sau khi cài Docker, ba case từng skip đã được chạy riêng trên MariaDB thật: **3 passed**.
- Ruff: `ruff check backend` sạch, bao gồm app/tests/scripts theo cấu hình repo.
- Migration SQLite: fresh install, upgrade giữ dữ liệu doanh nghiệp cũ, downgrade DB chưa dùng, re-upgrade; schema sau migration khớp Base.metadata, không có diff autogenerate.
- SQL MySQL render offline: 49 CREATE TABLE, enum CLIENT, các FK vòng thêm sau, guard append-only; không mở kết nối database khi render.
- Đã chạy migration 0001 → 0002 trên database MariaDB 10.11 độc lập cho từng case; enum CLIENT/FK vòng, trigger append-only, CHECK bảo toàn hạn mức và khóa dòng hai kết nối đồng thời đều pass. Không dùng DB nhóm.
- Lần chạy MariaDB đầu phát hiện ba FK bị lặp sai trong batch ALTER users; đã loại bỏ khỏi revision 0002 chưa phát hành, chạy lại pass và đồng bộ SQL tham chiếu. Các FK đúng trên companies/company_documents vẫn giữ nguyên.
- Có cảnh báo thư viện hiện hữu về Starlette/httpx và Alembic path_separator; không phải lỗi test. Chưa thay thư viện hoặc cấu hình toàn dự án chỉ để bỏ cảnh báo.

## 3. Migration 0002 cần biết

Revision tạo bảng mới, mở role CLIENT và thêm cột/FK cho bảng cũ. Quan hệ vòng contract/version và milestone/terms dùng FK thêm sau tạo bảng trên MySQL/MariaDB; SQLite tạo FK inline. Company/company_documents/users dùng batch-alter để kiểm thử upgrade SQLite; trên MariaDB là ALTER thông thường.

Downgrade chỉ cho phép khi không có dữ liệu Freelancer, CLIENT hoặc dữ liệu mới trong bảng cũ. Có chứng từ thì bị từ chối; dùng forward migration để sửa. Không dùng downgrade để xóa giao dịch thật. MariaDB DDL có implicit commit: phải backup/thử trên DB riêng trước cập nhật DB nhóm.

Các FK mới dùng RESTRICT; các cascade cũ vẫn được giữ. ORM existing có thể còn cascade trước DB: không xóa cứng tài khoản/doanh nghiệp có hợp đồng/tài chính.

## 4. Kiểm tra và cập nhật trên máy thành viên

Sau khi chủ dự án review và merge **PR nền tảng**, cập nhật đúng nhánh/commit được công bố. Các lệnh sau chạy trong `backend`, không chạy từ root:

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
$env:DEBUG = 'false'
python -m alembic heads
python -m pytest -q
python -m ruff check .
```

Chỉ khi DATABASE_URL được xác nhận trỏ **DB local của chính bạn**, đã backup dữ liệu cần giữ và đã được thông báo revision:

```powershell
python -m alembic current
python -m alembic upgrade head
```

Không tạo migration lại bằng autogenerate cho cùng bộ bảng; dùng revision 0002 đã được review. Không chạy upgrade trên DB nhóm từ checkout đang dở.

### MariaDB kiểm chứng riêng

Cần Docker Compose và cổng local 3308 còn trống. File compose test không dùng volume DB dev hiện tại, dữ liệu nằm trong tmpfs và mất khi dừng container. Chỉ dùng mật khẩu mẫu bên dưới cho test local.

```powershell
docker compose -f compose.freelancer-test.yml up -d --wait
$env:FREELANCER_TEST_DATABASE_URL = 'mysql+pymysql://root:freelancer-test-only@127.0.0.1:3308/student_connect_test_admin?charset=utf8mb4'
$env:DEBUG = 'false'
python -m pytest tests/freelancer/test_mariadb.py -q
Remove-Item Env:FREELANCER_TEST_DATABASE_URL
docker compose -f compose.freelancer-test.yml down
```

Fixture chỉ chấp nhận host localhost/127.0.0.1 và DB có prefix student_connect_test_. Nó tạo database ngẫu nhiên mới, chạy migration rồi chỉ xóa đúng database nó tạo. Cần quyền CREATE/DROP DATABASE của root test; không dùng credential môi trường khác. Test mặc định không có URL thì skip ba case MariaDB, không fallback sang DB ứng dụng.

### Lưu ý môi trường chạy kiểm tra trong phiên chuẩn bị

Đã tìm thấy môi trường Python có đủ dependencies tại `tmp/backend-integration/backend/.venv`; dùng nó để kiểm tra mã của checkout hiện tại, không sửa source worktree kia. Python mặc định thiếu một số dependencies.

Sandbox Windows chặn thư mục pytest được tạo với mode 0700. Lần chạy kiểm tra dùng basetemp riêng trong workspace và wrapper mkdir mode 0777 **chỉ trong process chạy test**, tắt pytest cache; không sửa code ứng dụng hoặc cấu hình quyền máy người dùng. Thành viên chạy môi trường bình thường dùng lệnh pytest chuẩn ở trên.

## 5. Gói Git cần review

Chỉ stage các file thuộc nền Freelancer:

```text
backend/app/core/enums.py
backend/app/core/freelancer_enums.py
backend/app/models/__init__.py
backend/app/models/user.py
backend/app/models/company.py
backend/app/models/freelancer_*.py
backend/app/contracts/__init__.py
backend/app/contracts/freelancer/
backend/app/dependencies_freelancer.py
backend/app/schemas/freelancer_common.py
backend/app/services/freelancer_commands.py
backend/app/services/freelancer_finance.py
backend/alembic/versions/0002_freelancer_shared_foundation.py
backend/database/freelancer_schema.sql
backend/tests/freelancer/
backend/compose.freelancer-test.yml
backend/pyproject.toml
backend/docs/FREELANCER_BACKEND_SPEC_PAYOS.md
backend/docs/freelancer/
backend/docs/CONVENTIONS.md
backend/docs/TASKS.md
```

Không đưa tmp, DB SQLite test, credentials, upload thật, bản HTML/Markdown thiết kế đã cũ hoặc thay đổi frontend/seed/config đang dở khác vào commit nền. Không dùng `git add .`. Review git diff --cached trước commit. Đợt nền này chủ dự án cho phép phát hành trực tiếp main; module sau đi nhánh riêng.

## 6. Bàn giao task

Xem [TEAM_TASKS.md](TEAM_TASKS.md): A/B/C/D mỗi nhóm 24 điểm tương đối, chủ dự án giữ F tài chính/payOS. Mỗi người nhận ticket và nhánh riêng từ cùng commit nền. NỀN chỉ tiếp tục review shared files/migration, không để bốn người cùng sửa một revision.

Trước khi công bố “bắt đầu trên DB nhóm”, còn phải review diff model/migration, ghi rõ commit nền và người phụ trách migration; kiểm chứng MariaDB riêng đã pass. Anh em có thể nhận task và làm quy tắc/schema/module test trên DB local trước, chưa triển khai thu/chi thật.
