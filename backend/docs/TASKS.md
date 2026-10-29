# Phân công nhiệm vụ Backend: nhóm 5 người

> Ưu tiên hiện tại: **hoàn thiện backend trước**, frontend làm sau. Swagger (`/docs`) là tài liệu API cho frontend nên endpoint nào xong phải có `summary` và `response_model` rõ ràng.
>
> Điền tên thật vào cột "Thành viên" rồi mới bắt đầu. Các mã TV1–TV5 đã được ghi sẵn trong docstring của từng file stub (`routers/`, `services/`, `schemas/`).

## 1. Nguyên tắc chia việc

- Chia theo **module dọc** (router + service + schema + test cùng một người), không chia theo tầng. Mỗi người sở hữu trọn gói một mảng nghiệp vụ nên ít phải chờ nhau.
- **Mỗi người chỉ sửa file của mình.** File dùng chung xem mục 6 trong `CONVENTIONS.md`.
- Phần phụ thuộc chéo được chốt bằng **chữ ký hàm** (mục 4). Ngay ngày đầu, người cung cấp đẩy lên chữ ký hàm (thân hàm tạm `raise NotImplementedError`) để người gọi code song song.
- Mọi thứ đã có sẵn dùng được ngay: đăng nhập/phân quyền dependency, JWT, phân trang, upload file, đọc Excel/CSV, thông báo, gửi email nền, seed dữ liệu, 37 model, migration `0001`. **Module mẫu hoàn chỉnh: Catalog/Faculty**, hãy bắt chước nó.

## 2. Tổng quan phân công

| | Thành viên | Mảng | Module phụ trách | Độ khó |
|---|---|---|---|---|
| **TV1** | ........ | Nền tảng, bảo mật, kiểm duyệt | `auth`, `users`, `notifications` (+email), `reports`, `admin_companies`, `admin_jobs` | Trung bình, nhưng **chặn các bạn khác** nên làm trước |
| **TV2** | ........ | Dữ liệu nhà trường, danh mục, thực tập theo đợt | `catalog`, `admin_students` (import), `admin_lecturers`, `internship_terms` | Trung bình (import Excel là phần khó nhất) |
| **TV3** | ........ | Phía sinh viên | `students`, `cvs`, `saved_jobs`, `applications` | Trung bình đến khó (luồng ứng tuyển nhiều quy tắc) |
| **TV4** | ........ | Phía doanh nghiệp, tuyển dụng | `companies`, `jobs`, `company_applications` (Kanban), `invitations` | Khó (tìm kiếm tin, luồng trạng thái, quyền riêng tư) |
| **TV5** | ........ | AI và phân tích | `ai/*`, `matching`, `dashboard`, `exports` | Khó (thuật toán điểm, thống kê, xuất báo cáo) |

Bản đồ file của từng người (ví dụ TV3): `routers/{students,cvs,saved_jobs,applications}.py`, `services/{student,cv,saved_job,application}_service.py`, `schemas/{students,cvs,saved_jobs,applications}.py`, `tests/test_<module>.py`. Mỗi file stub đã ghi sẵn **danh sách endpoint và hàm cần viết**, đọc docstring đầu file là biết làm gì.

**Về lịch phỏng vấn:** hệ thống **không có bảng/chức năng lịch phỏng vấn**. Khi đơn chuyển sang `INTERVIEW`, doanh nghiệp tự gửi email lịch cho sinh viên. Hệ thống chỉ lưu trạng thái, ghi chú vào lịch sử trạng thái và gửi email/thông báo kèm ghi chú đó (nếu doanh nghiệp nhập).

---

## 3. Chi tiết từng thành viên

### TV1: Nền tảng, bảo mật, kiểm duyệt

**Vì sao làm trước:** cả nhóm cần đăng nhập thật và hàm thông báo/email. Trong lúc chờ, mọi người dùng `python -m scripts.dev_token` để test.

| Việc | File | Ghi chú nghiệp vụ quan trọng |
|---|---|---|
| Xác thực | `routers/auth.py`, `services/auth_service.py` | `POST /auth/token` (form OAuth2, để nút Authorize của Swagger chạy), `login`, `refresh`, `logout`, `me`, đổi mật khẩu. User `LOCKED` hoặc chưa kích hoạt không đăng nhập được. |
| Quên mật khẩu | cùng trên | Luôn trả 200 dù email không tồn tại (không lộ tài khoản). Chỉ lưu **hash** token (`core.security.generate_reset_token`), có hạn dùng, dùng một lần. |
| Kích hoạt tài khoản sinh viên | cùng trên | `POST /auth/activate`: token từ email + mật khẩu mới, `PENDING_ACTIVATION` → `ACTIVE`. TV2 sẽ sinh token khi import. |
| Đăng ký doanh nghiệp | cùng trên | Tạo `User(COMPANY, PENDING_APPROVAL)` + `Company(PENDING)`. Chờ nhà trường duyệt. |
| Quản lý tài khoản | `routers/users.py`, `services/user_service.py` | Danh sách/lọc, **khóa/mở khóa** (bắt buộc lý do), tạo tài khoản admin. |
| Thông báo | `routers/notifications.py`, `services/notification_service.py` | Hàm `create_notification` đã có. Làm thêm: danh sách, đếm chưa đọc, đánh dấu đã đọc. |
| Email | `services/email_service.py`, `tasks/email_tasks.py` | `queue_email` đã có (ghi `email_logs` + gửi nền). Làm thêm: template HTML cho từng loại email, thử lại email lỗi. |
| Báo cáo vi phạm | `routers/reports.py`, `services/report_service.py` | User gửi, admin xử lý (RESOLVED/REJECTED), có thể kèm khóa tài khoản/đóng tin. |
| Kiểm duyệt doanh nghiệp | `routers/admin_companies.py`, `services/admin_company_service.py` | Duyệt: `verification_status=APPROVED`, `user.status=ACTIVE`, ghi người duyệt/thời điểm. Từ chối: **bắt buộc lý do**. Cả hai gửi thông báo + email. |
| Kiểm duyệt tin tuyển dụng | `routers/admin_jobs.py`, `services/admin_job_service.py` | Duyệt tin → `APPROVED`, rồi chạy `ai.job_parser.parse_job` **ở nền** (TV5; bọc try/log vì lúc đầu hàm này chưa có). Từ chối: bắt buộc lý do, thông báo + email. |

Cung cấp cho người khác: `get_current_user` và các dependency (đã có), `notification_service.create_notification`, `email_service.queue_email`.

Hoàn thành khi: đăng nhập 3 role chạy trên Swagger; luồng "doanh nghiệp đăng ký → nhà trường duyệt → doanh nghiệp đăng nhập được" chạy trọn vẹn có test.

**Kiêm nhiệm: người gác migration.** Review mọi PR có đổi model/migration, giữ chuỗi migration một đường thẳng.

### TV2: Dữ liệu nhà trường, danh mục, thực tập theo đợt

| Việc | File | Ghi chú nghiệp vụ quan trọng |
|---|---|---|
| Danh mục | `routers/catalog.py`, `services/catalog_service.py`, `schemas/catalog.py` | **Faculty đã làm mẫu.** Làm tương tự: Major, Industry, JobType, Skill (+ tìm kiếm theo tên), SkillAlias. Đọc: mọi user; ghi: admin. Xóa mềm bằng `is_active`. |
| Chuẩn hóa kỹ năng | `catalog_service.py` | Viết `normalize_skill_names(db, names) -> list[Skill]` tra `Skill.name` và `SkillAlias.alias` (không phân biệt hoa thường). **TV5 phụ thuộc hàm này.** Làm sớm. |
| Quản lý sinh viên | `routers/admin_students.py`, `services/admin_student_service.py` | Danh sách/lọc, xem chi tiết (tách rõ dữ liệu trường và tự khai), sửa dữ liệu học thuật, thêm nghiên cứu khoa học/thành tích, **xác thực chứng chỉ** tự khai. |
| Import sinh viên | cùng trên | Upload Excel/CSV (dùng `utils.spreadsheet.read_rows`). Upsert theo `student_code`. Tạo `User(PENDING_ACTIVATION)` + `Student`. **Một dòng lỗi không làm hỏng cả file:** ghi lỗi từng dòng vào `ImportBatch.error_report`. Có lịch sử import. Gửi email kích hoạt (qua `email_service` của TV1). |
| Giảng viên | `routers/admin_lecturers.py`, `services/lecturer_service.py` | CRUD thông thường, ngừng hoạt động thay vì xóa. |
| Đợt thực tập | `routers/internship_terms.py`, `services/internship_service.py` | Tạo đợt, chuyển trạng thái hợp lệ (`DRAFT→OPEN→ONGOING→CLOSED`), thêm/import sinh viên vào đợt (theo mã sinh viên), phân công giảng viên hàng loạt, xem tin thuộc đợt. |
| Kết quả thực tập | cùng trên | Doanh nghiệp gửi đánh giá (**chỉ công ty nơi sinh viên thực tập** được gửi), giảng viên/admin nhận xét, admin xác nhận PASSED/FAILED, thông báo nhà trường khi có đánh giá. |

Cung cấp cho người khác: `normalize_skill_names` (→ TV5), `internship_service.is_student_in_term(db, student_id, term_id)` (→ TV3, TV4, TV5).

Hoàn thành khi: import file mẫu 50 sinh viên (có vài dòng lỗi cố ý) cho ra báo cáo lỗi đúng; tạo đợt → thêm sinh viên → phân công giảng viên → nhập kết quả chạy trọn vẹn có test.

### TV3: Phía sinh viên

| Việc | File | Ghi chú nghiệp vụ quan trọng |
|---|---|---|
| Hồ sơ | `routers/students.py`, `services/student_service.py` | `GET /students/me` trả **hai nhóm tách bạch**: `official` (từ trường, chỉ đọc) và `self_declared` (tự khai). Sinh viên **không sửa được** dữ liệu trường, không sửa/xóa chứng chỉ nguồn `SCHOOL`. |
| Dữ liệu tự khai | cùng trên | CRUD kỹ năng (nguồn `SELF`), kinh nghiệm, dự án, chứng chỉ (`SELF`, chưa xác thực), thông tin liên hệ bổ sung. |
| Quyền riêng tư | cùng trên | Cập nhật `is_open_to_work`, `show_gpa`, `show_contact`, `show_achievements`. **TV4 và TV5 dựa vào các cờ này** khi hiện ứng viên cho doanh nghiệp. |
| CV | `routers/cvs.py`, `services/cv_service.py` | Upload PDF/DOCX, tạo CV online (**tự điền dữ liệu học thuật từ trường**), nhiều CV, đặt mặc định (chỉ 1 CV mặc định/sinh viên), **xóa mềm** (đơn đã nộp vẫn phải xem được CV). Nút phân tích AI gọi `ai.cv_parser.parse_cv` của TV5. |
| Việc làm yêu thích | `routers/saved_jobs.py`, `services/saved_job_service.py` | Lưu/bỏ lưu (idempotent), danh sách. |
| Ứng tuyển | `routers/applications.py`, `services/application_service.py` | Xem quy tắc bên dưới. Theo dõi đơn, xem lịch sử trạng thái, rút đơn. |

**Quy tắc khi nộp đơn** (`POST /applications`), kiểm tra theo thứ tự:
1. Tin ở trạng thái `APPROVED` và còn hạn.
2. CV thuộc đúng sinh viên đó và chưa bị xóa.
3. Nếu tin thuộc đợt (`term_id` khác NULL): sinh viên phải nằm trong đợt (`internship_service.is_student_in_term`).
4. Không ứng tuyển trùng cùng một tin (trả 409).
5. Sao chép CV hiện tại vào `cv_snapshot_url` (doanh nghiệp xem bản này, kể cả khi sinh viên sửa CV sau).
6. Ghi `application_status_logs` (`old_status=None`, `new_status=APPLIED`).
7. Gửi email xác nhận cho sinh viên và thông báo cho doanh nghiệp.
8. Nếu ứng tuyển từ lời mời (`invitation_id`): chuyển lời mời sang `ACCEPTED`.

Cung cấp cho người khác: `application_service.log_status_change(db, application, new_status, changed_by, note)` (→ TV4 dùng khi kéo thả Kanban).

Hoàn thành khi: sinh viên tạo CV → ứng tuyển tin tự do và tin theo đợt (có cả trường hợp bị chặn đúng) → xem được trạng thái; có test cho từng quy tắc trên.

### TV4: Phía doanh nghiệp và tuyển dụng

| Việc | File | Ghi chú nghiệp vụ quan trọng |
|---|---|---|
| Hồ sơ doanh nghiệp | `routers/companies.py`, `services/company_service.py` | Cập nhật hồ sơ, upload giấy tờ xác thực, xem trạng thái xác thực. Hồ sơ công khai cho sinh viên chỉ hiện công ty đã `APPROVED`. |
| Tin tuyển dụng (doanh nghiệp) | `routers/jobs.py`, `services/job_service.py` | Tạo (`DRAFT`) → gửi duyệt (`PENDING_APPROVAL`) → nhà trường duyệt (TV1). Chỉ công ty đã `APPROVED` mới đăng được. Sửa tin đã `APPROVED` thì phải quay lại chờ duyệt. Đóng tin. Kèm kỹ năng (bắt buộc/ưu tiên) và ngành học yêu cầu. |
| Tìm kiếm tin (sinh viên) | cùng trên | Lọc theo ngành, kỹ năng, vị trí, địa điểm, mức lương, hình thức làm việc, loại hình, luồng (tự do/đợt). **Chỉ trả tin `APPROVED` còn hạn. Tin thuộc đợt chỉ hiện với sinh viên nằm trong đợt đó.** Xem chi tiết thì ghi `job_views` và tăng `view_count`. |
| Thống kê tin | cùng trên | Lượt xem theo ngày, số đơn theo trạng thái. Hàm `expire_overdue_jobs()` chuyển tin quá hạn sang `EXPIRED`. |
| Quản lý ứng viên (Kanban) | `routers/company_applications.py`, `services/company_application_service.py` | Danh sách đơn theo tin, lọc ngành/GPA/kỹ năng/kinh nghiệm. Xem hồ sơ + CV snapshot **chỉ của đơn thuộc tin công ty mình**. Kéo thả đổi trạng thái: kiểm tra chuyển hợp lệ (`APPLIED→SCREENING→SHORTLISTED→INTERVIEW→OFFER→HIRED`, được `REJECTED` từ bất kỳ bước nào). Mỗi lần đổi: ghi log + thông báo + email cho sinh viên. |
| Ghi chú khi đổi trạng thái | cùng trên | Khi chuyển `INTERVIEW`/`OFFER`, cho nhập `note` (thời gian, địa điểm/link...). Note được lưu vào lịch sử trạng thái và đưa vào email gửi sinh viên. Đây là cách thay cho bảng lịch phỏng vấn. |
| Lời mời ứng tuyển | `routers/invitations.py`, `services/invitation_service.py` | Chỉ mời sinh viên có `is_open_to_work = 1`; duy nhất theo (tin, sinh viên); thông báo + email. Sinh viên từ chối được; chấp nhận = nộp đơn với `invitation_id` (TV3). |

Cung cấp cho người khác: `JobRead`/`JobListItem` schema (→ TV3 dùng cho việc làm yêu thích), `job_service` (→ TV2 liệt kê tin theo đợt).

Hoàn thành khi: doanh nghiệp tạo tin → gửi duyệt → (TV1 duyệt) → sinh viên tìm thấy → ứng tuyển → doanh nghiệp kéo Kanban đến `HIRED`, mỗi bước có thông báo; có test cho quy tắc ẩn tin theo đợt và chuyển trạng thái hợp lệ.

### TV5: AI và phân tích

**Nguyên tắc từ đặc tả:** Matching Score chỉ là **gợi ý**, không phải kết luận tuyển dụng tự động. **Backend kiểm soát cách tính điểm**, LLM chỉ trích xuất dữ liệu và giải thích, không quyết định điểm.

| Việc | File | Ghi chú nghiệp vụ quan trọng |
|---|---|---|
| Client LLM | `ai/client.py`, `ai/prompts.py` | Một interface `LLMClient.complete_json(...)`, chọn provider qua `AI_PROVIDER` (Gemini/OpenAI/Anthropic) bằng `httpx`. Timeout, retry, **ghi `ai_request_logs`** (tokens, độ trễ, lỗi). Ép đầu ra JSON, có xử lý khi JSON hỏng. |
| Phân tích CV | `ai/cv_parser.py` | Lấy chữ từ PDF/DOCX hoặc CV online → LLM → JSON chuẩn hóa (kỹ năng, kinh nghiệm, dự án, lĩnh vực). Chuẩn hóa tên kỹ năng bằng `normalize_skill_names` (TV2). **Tính `content_hash`; không đổi thì không gọi API lại.** |
| Phân tích tin | `ai/job_parser.py` | Tương tự cho tin tuyển dụng (kỹ năng bắt buộc/ưu tiên, kinh nghiệm, trình độ). |
| Tính điểm | `ai/matching_engine.py` | **Thuần tính toán, không gọi DB/API** để unit test dễ. Bước 1: điều kiện bắt buộc (ngành, GPA tối thiểu, luồng/đợt, tin còn hiệu lực). Bước 2: điểm kỹ năng (bắt buộc nặng hơn ưu tiên), kinh nghiệm, ngữ nghĩa. Trả về điểm + kỹ năng đã đáp ứng/còn thiếu + lý do. |
| Dịch vụ matching | `routers/matching.py`, `services/matching_service.py` | `get_or_compute_match`: dùng lại `matching_results` nếu `input_hash` không đổi. Gợi ý việc làm cho sinh viên; gợi ý ứng viên cho doanh nghiệp. |
| Quyền riêng tư (rất quan trọng) | cùng trên | Gợi ý ứng viên: **chỉ lấy sinh viên `is_open_to_work = 1`** và **ẩn GPA/liên hệ/thành tích nếu `show_* = 0`**. Phải có test cho việc này. |
| Dashboard | `routers/dashboard.py`, `services/dashboard_service.py` | Tổng quan; thống kê theo ngành/khoa/khóa/đợt; top kỹ năng được yêu cầu; kỹ năng còn thiếu; tỷ lệ đáp ứng theo ngành; xu hướng; so sánh hai luồng. Ưu tiên một câu SQL `GROUP BY` thay vì lặp trong Python. |
| Xuất báo cáo | `routers/exports.py`, `services/export_service.py` | Excel (openpyxl) cho sinh viên/doanh nghiệp/tin/đơn/báo cáo kỹ năng; PDF thống kê tổng quan. **Không xuất thông tin cá nhân không cần thiết.** |

Hoàn thành khi: matching engine có unit test phủ các trường hợp (không đạt điều kiện bắt buộc, thiếu kỹ năng, đủ kỹ năng); gọi lại cùng cặp (sinh viên, tin) lần hai **không** gọi API; dashboard và export chạy trên dữ liệu seed.

> TV5 có lượng endpoint ít hơn nhưng khó hơn. Khi xong sớm, hỗ trợ viết **seed dữ liệu demo lớn hơn** và **test tích hợp end-to-end** (mục 5).

---

## 4. Hợp đồng giữa các module (chốt chữ ký hàm)

Người cung cấp đẩy chữ ký hàm lên `develop` trong **ngày đầu**. Người gọi code theo chữ ký này. Muốn đổi chữ ký phải báo nhóm.

| Hàm | Người viết | Người gọi |
|---|---|---|
| `dependencies`: `CurrentUser`, `AdminUser`, `CurrentStudent`, `CurrentCompany`, `Pagination` | (có sẵn) | tất cả |
| `notification_service.create_notification(db, *, user_id, type, title, content, ref_type, ref_id)` | (có sẵn) | tất cả |
| `email_service.queue_email(db, background_tasks, *, to_email, subject, body_html, type, ...)` | (có sẵn) | tất cả |
| `catalog_service.normalize_skill_names(db, names) -> list[Skill]` | TV2 | TV5 |
| `internship_service.is_student_in_term(db, student_id, term_id) -> bool` | TV2 | TV3, TV4, TV5 |
| `application_service.log_status_change(db, application, new_status, changed_by, note)` | TV3 | TV4 |
| `ai.cv_parser.parse_cv(db, cv) -> dict` | TV5 | TV3 |
| `ai.job_parser.parse_job(db, job) -> dict` | TV5 | TV1 (khi duyệt tin) |
| `job_service` (truy vấn tin theo đợt, thông tin tin cho danh sách) | TV4 | TV2, TV3 |

Chưa có hàm của người khác thì: gọi theo chữ ký đã chốt, và trong test tạm thời dùng `monkeypatch`/dữ liệu seed. **Không** copy-paste logic của người khác về module mình.

## 5. Lộ trình đề xuất

Điều chỉnh số tuần theo hạn nộp thực tế của nhóm.

**Giai đoạn 0 (1–2 ngày): chuẩn bị, cả nhóm.** Clone repo, chạy theo README (docker → `alembic upgrade head` → seed → chạy server → `pytest`). Đọc `CONVENTIONS.md`. Đọc module mẫu Catalog. Đẩy chữ ký hàm ở mục 4. Tạo nhánh `develop`.

**Giai đoạn 1 (tuần 1): nền tảng.**
- TV1: auth hoàn chỉnh (token, login, refresh, me, đổi/quên/đặt lại mật khẩu), notifications, email.
- TV2: catalog đầy đủ, `normalize_skill_names`, `is_student_in_term`, đợt thực tập cơ bản.
- TV3: hồ sơ sinh viên (official/self), CRUD kỹ năng/kinh nghiệm/dự án/chứng chỉ.
- TV4: hồ sơ doanh nghiệp, CRUD tin tuyển dụng (chưa cần tìm kiếm nâng cao).
- TV5: `matching_engine` thuần + unit test, thiết kế JSON đầu ra và prompt, `LLMClient`.

**Giai đoạn 2 (tuần 2): luồng nghiệp vụ chính.**
- TV1: kiểm duyệt doanh nghiệp và tin, quản lý tài khoản (khóa/mở).
- TV2: import sinh viên Excel/CSV, giảng viên, phân công đợt.
- TV3: CV, ứng tuyển (đủ 8 quy tắc), theo dõi đơn, việc làm yêu thích.
- TV4: tìm kiếm tin, Kanban + chuyển trạng thái, lời mời.
- TV5: `cv_parser`, `job_parser`, `matching_service` (có cache).

**Giai đoạn 3 (tuần 3): AI, thống kê, hoàn thiện.**
- TV1: báo cáo vi phạm; rà soát phân quyền toàn hệ thống.
- TV2: kết quả thực tập (đánh giá doanh nghiệp, xác nhận nhà trường).
- TV3 và TV4: tích hợp luồng ứng viên/lời mời với kết quả matching; bổ sung test.
- TV5: endpoint matching hoàn chỉnh, dashboard, export Excel/PDF.

**Giai đoạn 4 (tuần 4): kiểm thử và bàn giao cho frontend.** Test tích hợp end-to-end, sửa lỗi, seed dữ liệu demo, rà soát Swagger (mỗi endpoint có `summary`), chốt tài liệu API, đóng băng thay đổi breaking.

### Kịch bản kiểm thử end-to-end (cả nhóm cùng viết ở giai đoạn 4)

1. **Doanh nghiệp tham gia:** đăng ký → nhà trường duyệt → đăng nhập → tạo tin → gửi duyệt → nhà trường duyệt → tin hiển thị.
2. **Sinh viên được cấp tài khoản:** nhà trường import → email kích hoạt → sinh viên kích hoạt → đăng nhập → tạo CV → ứng tuyển.
3. **Thực tập theo đợt:** tạo đợt + thêm sinh viên + tin gắn đợt → sinh viên **trong** đợt ứng tuyển được, sinh viên **ngoài** đợt bị chặn → doanh nghiệp kéo Kanban đến `HIRED` → doanh nghiệp đánh giá → nhà trường xác nhận kết quả.
4. **AI:** sinh viên nhận gợi ý việc làm kèm kỹ năng thiếu; doanh nghiệp nhận gợi ý ứng viên và **không thấy** GPA/liên hệ của sinh viên đã tắt quyền xem.
5. **Thống kê:** dashboard và export chạy đúng trên dữ liệu vừa tạo.

## 6. Định nghĩa "xong" (Definition of Done)

Một chức năng chỉ được coi là xong khi: đúng đặc tả, có kiểm tra role **và** quyền sở hữu, có test (đúng / sai quyền / lỗi nghiệp vụ), `ruff` + `pytest` xanh, Swagger có `summary` + `response_model`, PR đã được ít nhất 1 người khác review và merge vào `develop`.

## 7. Cách làm việc hằng ngày

- Họp nhanh 10–15 phút mỗi ngày (hoặc cách ngày): hôm qua làm gì, hôm nay làm gì, đang bị chặn ở đâu.
- Bị chặn vì hàm của người khác: nhắn người đó ngay, đồng thời dùng chữ ký đã chốt để làm tiếp phần khác.
- Muốn đổi model/schema DB: báo nhóm **trước khi** làm, kèm migration (xem `CONVENTIONS.md` mục 7).
- Phát hiện thiếu sót đặc tả hoặc cần thêm bảng: ghi vào issue của repo, cả nhóm quyết một lần, đừng tự sửa riêng.
