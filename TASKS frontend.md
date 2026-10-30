# Phân công frontend — Student Connect (5 thành viên)

## 1. Mục tiêu và phạm vi

Làm frontend cho backend đã tích hợp trên main, mốc kiểm tra 80fd94b. Có ba vai trò:
STUDENT, COMPANY, ADMIN. Mỗi người phụ trách trọn luồng: trang, component nghiệp vụ,
gọi API, kiểu dữ liệu, trạng thái giao diện và kiểm thử phần mình.

Giữ phân công gần với backend để tận dụng hiểu biết nghiệp vụ. Thiết kế tham chiếu
bản mô tả Stitch đã chuẩn bị. Thiết kế được duyệt quyết định cách trình bày; OpenAPI
quyết định tên trường, dữ liệu, phương thức và quyền thao tác.

Không đưa các file .env cá nhân, API key AI hoặc mật khẩu SMTP vào frontend/Git.
Các dịch vụ AI và email được gọi qua backend, không gọi trực tiếp từ trình duyệt.

## 2. Tổng quan phân công

| Thành viên | Phụ trách chính | Đầu ra |
|---|---|---|
| Quang | Xác thực, tài khoản, thông báo và kiểm duyệt | Đăng nhập thật, phân quyền, admin duyệt, nhật ký email và báo cáo vi phạm |
| Phong | Quản trị dữ liệu nhà trường và thực tập | Danh mục, sinh viên/import, giảng viên, đợt và kết quả thực tập |
| Việt Anh | Toàn bộ trải nghiệm sinh viên | Tìm việc, hồ sơ, CV, lưu tin, ứng tuyển, lời mời, thực tập của tôi |
| Khôi | Toàn bộ trải nghiệm doanh nghiệp | Hồ sơ, tin tuyển dụng, thống kê tin, Kanban, chi tiết ứng viên và lời mời |
| Thuận | Khung frontend, thiết kế dùng chung, matching và phân tích | App shell/design tokens, gợi ý việc/ứng viên, dashboard, xuất báo cáo và tích hợp |

Thuận không viết thay các trang nghiệp vụ của thành viên khác. Mỗi người tự tích
hợp trang mình với khung và component chung; kiểm thử toàn dự án là trách nhiệm cả nhóm.

## 3. Phân công chi tiết

### Quang — Xác thực, tài khoản, thông báo, kiểm duyệt

**Các màn hình**

- Đăng nhập email/mật khẩu, quên mật khẩu, đặt lại mật khẩu từ link email,
  kích hoạt sinh viên từ link, đổi mật khẩu, đăng xuất.
- Đăng ký doanh nghiệp; trang/thông báo chờ duyệt, tài khoản chưa kích hoạt/bị khóa.
- Drawer và trang thông báo: số chưa đọc, đánh dấu một/tất cả đã đọc.
- Admin quản lý tài khoản: tìm/lọc, chi tiết, khóa có lý do, mở khóa, tạo admin.
- Admin duyệt doanh nghiệp: danh sách, chi tiết, giấy tờ theo dữ liệu backend,
  duyệt/từ chối có lý do. Trang này riêng với hồ sơ công ty do Khôi làm.
- Admin duyệt tin: danh sách, chi tiết, duyệt/từ chối/đóng tin.
- Admin báo cáo vi phạm: danh sách, chi tiết, giải quyết/từ chối, tùy chọn khóa
  tài khoản hoặc đóng tin đúng loại đối tượng.
- Nhật ký email và xếp hàng gửi lại các email lỗi.

**Phần dùng chung Quang cung cấp sớm**

- AuthProvider/useAuth: user, role, trạng thái tải, login, logout.
- RequireAuth và RequireRole; điều hướng theo role do backend trả về.
- HTTP client chung, gắn access token, xử lý refresh token, 401/403 và phiên hết hạn.
  Refresh đồng thời phải dùng một yêu cầu chung, không lặp vô hạn.
- NotificationBell dùng trong mọi layout và ReportDialog dùng từ trang tin/công ty.
- Lỗi nghiệp vụ {error:{code,message}} và lỗi validate 422 {detail:...} được xử lý chung.

**API:** /auth/*, /notifications/*, /admin/users/*, /admin/companies/*,
/admin/jobs/*, /reports/*.

**Hoàn thành khi:** đăng nhập ba role dẫn đúng khu vực; tải lại trang vẫn xác định
phiên đúng; không truy cập trái role; hết phiên xử lý rõ ràng; duyệt và từ chối
thực sự thay đổi dữ liệu backend. Không tạo đăng ký sinh viên/admin công khai.

### Phong — Dữ liệu nhà trường, danh mục và thực tập

**Các màn hình**

- Admin danh mục: khoa, ngành, lĩnh vực, loại hình công việc, kỹ năng; CRUD và
  ngừng hoạt động. Alias kỹ năng chỉ xem/thêm/xóa theo API hiện có.
- Admin sinh viên: danh sách lọc, chi tiết tách dữ liệu trường và tự khai,
  sửa học thuật, thêm/xóa thành tích, xác thực chứng chỉ tự khai,
  gửi lại email kích hoạt khi tài khoản còn chờ kích hoạt.
- Import sinh viên Excel/CSV: chọn file, hướng dẫn cột, gửi, tổng kết thành công/
  thất bại, bảng lỗi theo số dòng, lịch sử import và chi tiết từng lần.
- Admin giảng viên: danh sách, tạo/sửa/ngừng hoạt động.
- Admin đợt thực tập: danh sách, tạo/sửa/chuyển trạng thái; tabs sinh viên,
  tin thuộc đợt và kết quả; thêm/import sinh viên, xóa khi được phép,
  phân công/bỏ phân công giảng viên hàng loạt.
- Admin xem đánh giá doanh nghiệp, nhập nhận xét/điểm nhà trường và xác nhận
  PASSED/FAILED. Chưa có role giảng viên riêng nên admin nhập thay.

**Phần Phong cung cấp cho các bạn**

- API/hooks và types đọc danh mục trong src/features/catalog; selector khoa/ngành,
  kỹ năng và loại hình có thể tái sử dụng, không mặc định chỉ admin mới dùng được.
- Hàm đọc chi tiết kết quả thực tập và types tương ứng để thống nhất với form Khôi.

**API:** /catalog/*, /admin/students/*, /admin/lecturers/*, /internship-terms/*.

**Hoàn thành khi:** import file có dòng sai vẫn hiển thị đúng các dòng thành công,
lỗi không làm mất ngữ cảnh; khoa/ngành khớp nhau; số liệu sau lưu cập nhật đúng;
đợt chuyển trạng thái đúng luồng; thao tác đã khóa không có nút thực thi sai.
Không tạo nút đồng bộ hệ thống đào tạo đang hoạt động vì API sync còn trả 501.

### Việt Anh — Khu vực sinh viên

**Các màn hình**

- Tìm việc và chi tiết tin: bộ lọc đúng API, phân trang, lưu/bỏ lưu,
  mở hồ sơ công ty công khai và gọi ReportDialog của Quang.
- Hồ sơ của tôi: dữ liệu trường chỉ đọc, thông tin tự khai, kỹ năng, kinh nghiệm,
  dự án, chứng chỉ và các cờ quyền riêng tư/tìm việc.
- CV của tôi: upload PDF/DOCX, tạo CV online, sửa, đặt mặc định, tải, xóa mềm;
  gắn nút phân tích và panel kết quả do Thuận cung cấp.
- Modal ứng tuyển: chọn CV, thư giới thiệu, xử lý trùng/hết hạn/sai đợt;
  nhận invitation_id khi đi từ lời mời hoặc trang gợi ý của Thuận.
- Đơn ứng tuyển: danh sách, chi tiết, timeline và rút đơn khi được phép.
- Việc đã lưu; lời mời nhận được, từ chối hoặc mở modal ứng tuyển theo lời mời.
- Thực tập của tôi: đợt và giảng viên hướng dẫn, xem tin đúng đợt.

**Phần Việt Anh cung cấp cho các bạn**

- JobCard, CompanyPublicProfile, SaveJobButton, ApplyDialog dùng lại được từ trang matching.
- ApplyDialog nhận jobId và invitationId tùy chọn; tự lấy CV của sinh viên.
- Khung CV quản lý quyền sở hữu; phần gọi AI đi qua hook/module của Thuận.

**API:** GET /jobs và /jobs/{id}, GET /companies/{id}, /students/me/*, /cvs/*,
/saved-jobs/*, /applications/*, GET /invitations/me,
POST /invitations/{id}/decline, API đợt sinh viên được xem.

**Hoàn thành khi:** sinh viên thật tạo CV, tìm tin và nộp đơn được; dữ liệu trường
không bị đưa vào form sửa; cờ riêng tư lưu được; lời mời được chấp nhận bằng cách
nộp đơn kèm invitation_id, không tự tạo endpoint accept riêng.
Không hứa tạo/tải CV PDF từ CV online vì backend hiện trả JSON; không làm bảng điểm
thực tập của sinh viên khi API hiện chỉ trả đợt và giảng viên.

### Khôi — Khu vực doanh nghiệp

**Các màn hình**

- Hồ sơ doanh nghiệp: xem/sửa trường cho phép, trạng thái xác thực,
  upload/xóa giấy tờ. Tên và mã số thuế chỉ đọc sau đăng ký.
- Tin của tôi: danh sách/lọc, tạo/sửa, lưu nháp, gửi duyệt, đóng và thống kê từng tin.
- Quản lý ứng viên: bắt buộc chọn tin; bộ lọc, bảng phân trang, Kanban có tải thêm
  theo cột, drawer chi tiết, lịch sử và tải đúng snapshot CV của từng đơn.
- Chuyển trạng thái hợp lệ qua menu/modal hoặc kéo thả có xác nhận; note cho
  INTERVIEW/OFFER là nơi nhập thông tin lịch/link phỏng vấn, không tạo lịch riêng.
- Gửi lời mời: modal nhận jobId/studentId, lời nhắn; danh sách lời mời đã gửi.
- Form đánh giá thực tập theo result_id: evaluation và score 0–10. Chỉ mở form
  khi có result_id và quyền hợp lệ; phối hợp Phong/Thuận về điểm thiếu API bên dưới.

**Phần Khôi cung cấp cho các bạn**

- InviteDialog dùng lại ở trang gợi ý ứng viên của Thuận.
- Query/hook tin thuộc công ty để Thuận chọn tin ở trang gợi ý ứng viên.
- ApplicationDrawer và đường tải cv_download_url từ response; không chọn CV snapshot
  theo cv_id khi một CV có nhiều phiên bản đã nộp.

**API:** /companies/me/*, POST /jobs, /jobs/me, PUT /jobs/{id},
/jobs/{id}/submit, /jobs/{id}/close, /jobs/{id}/stats,
/company/applications/*, POST /invitations, GET /invitations/company,
PUT /internship-terms/results/{result_id}/evaluation.

**Hoàn thành khi:** doanh nghiệp tạo tin và gửi duyệt, xem đơn thuộc công ty mình,
chuyển Kanban đến HIRED, lịch sử/ghi chú cập nhật đúng. GPA/liên hệ bị ẩn phải hiển
thị là không chia sẻ, không biến null thành 0. Không tự suy đoán quyền hoặc số liệu.

### Thuận — Khung ứng dụng, AI matching, dashboard và báo cáo

**Nền tảng làm trước**

- Khởi tạo frontend React + TypeScript theo stack đã thống nhất; tổ chức source,
  cấu hình build/lint/test, tài liệu chạy và .env.example chỉ chứa địa chỉ backend.
- Chốt thư viện giao diện, routing, form và quản lý dữ liệu cùng cả nhóm ngay đầu;
  sau đó không để mỗi module dùng một bộ thư viện riêng.
- Tổng hợp ba màn Stitch mẫu, chốt màu/font/khoảng cách và component dùng chung.
- StudentLayout, CompanyLayout, AdminLayout, sidebar/menu theo role; nơi gắn
  AuthProvider/guard/NotificationBell của Quang.
- Router tổng, trang không có quyền/không tìm thấy, component loading/rỗng/lỗi,
  modal xác nhận và phân trang. Không viết lại nghiệp vụ của từng module.

**Các màn hình nghiệp vụ**

- Gợi ý việc làm cho sinh viên: xếp theo score, matched/missing skills và giải thích;
  dùng JobCard/ApplyDialog của Việt Anh.
- Gợi ý ứng viên theo tin công ty: điểm, thông tin được chia sẻ, mời ứng tuyển qua
  InviteDialog của Khôi; chưa có quyền tải CV của người chưa nộp đơn.
- MatchScorePanel và CVAnalysisPanel; có loading, lỗi AI, chưa có dữ liệu.
- Admin dashboard: tổng quan, breakdown, top kỹ năng, khoảng thiếu kỹ năng,
  tỷ lệ phù hợp, xu hướng và so sánh luồng.
- ExportButton/helpers tải Excel/PDF từ backend, dùng lại ở các trang admin.
- Nút tính lại matching chỉ thông báo đã xếp hàng; không vẽ tiến độ giả.

**API:** /matching/*, POST /cvs/{id}/analyze (qua panel trong luồng Việt Anh),
/admin/dashboard/*, /admin/exports/*; dùng API đọc danh mục của Phong.

**Hoàn thành khi:** layout ba role thống nhất; gợi ý dẫn tới ứng tuyển/lời mời thật;
không lộ trường ẩn; biểu đồ tuân theo bộ lọc; export tải đúng file. Điểm matching
luôn được mô tả là tham khảo, không kết luận tuyển dụng tự động.

## 4. Ranh giới tránh làm trùng

| Giao điểm | Chủ sở hữu | Người tích hợp |
|---|---|---|
| Auth, refresh token, HTTP client | Quang | Tất cả |
| Layout, design tokens, router tổng, package.json | Thuận | Tất cả |
| Danh mục và selector dùng chung | Phong | Việt Anh, Khôi, Thuận |
| JobCard, lưu tin, modal ứng tuyển | Việt Anh | Thuận |
| InviteDialog, dữ liệu tin thuộc công ty | Khôi | Thuận |
| CVAnalysisPanel, MatchScorePanel | Thuận | Việt Anh, Khôi nếu đúng API |
| NotificationBell, ReportDialog | Quang | Các layout và trang có đối tượng báo cáo |
| ExportButton/hàm tải báo cáo | Thuận | Phong và các trang admin được cấp quyền |

Phân tích CV: Việt Anh sở hữu trang/quyền thao tác CV; Thuận sở hữu hook gọi phân tích
và panel kết quả. Tìm việc: Việt Anh sở hữu tìm kiếm thường; Thuận sở hữu trang gợi ý.
Ứng viên: Khôi sở hữu đơn đã nộp/Kanban; Thuận sở hữu ứng viên được gợi ý.

## 5. Cấu trúc source đề xuất

~~~text
frontend/
  src/
    app/                  # Thuận: router, providers, bố cục gắn module
    layouts/              # Thuận: ba layout
    components/ui/        # Thuận: component trình bày dùng chung
    styles/               # Thuận: tokens, theme, CSS nền
    lib/http.ts           # Quang: HTTP client và refresh
    features/
      auth/               # Quang
      notifications/      # Quang
      account-admin/      # Quang
      moderation/         # Quang: duyệt công ty/tin
      reports/            # Quang
      email-logs/         # Quang
      catalog/            # Phong: admin + API/hooks đọc dùng chung
      school-students/    # Phong
      lecturers/          # Phong
      internship-admin/   # Phong
      student-profile/    # Việt Anh
      student-jobs/       # Việt Anh
      student-cvs/        # Việt Anh
      student-applications/ # Việt Anh
      student-invitations/  # Việt Anh
      student-internships/  # Việt Anh
      company-profile/    # Khôi
      company-jobs/       # Khôi
      company-applications/ # Khôi
      company-invitations/  # Khôi
      company-evaluations/  # Khôi, form theo ngữ cảnh
      matching/           # Thuận
      analytics/          # Thuận
      exports/            # Thuận
  docs/
~~~

Mỗi feature tự chứa pages, components, api, types và test cần thiết. Tách theo
nghiệp vụ, không để tất cả API/types/page của mọi người trong một file khổng lồ.
Không sửa file thành viên khác nếu chưa thống nhất; khi cần đổi hợp đồng component,
báo người gọi và cập nhật các chỗ phụ thuộc trong cùng PR.

## 6. Việc phải chốt ở mốc khởi động

1. Cả nhóm duyệt ba mẫu màn Stitch và danh sách màn hình; Thuận ghi design tokens.
2. Thuận tạo scaffold, script build/lint/test, layout và quy tắc route.
3. Quang tạo HTTP client/auth/guard trước để các bạn gọi API thống nhất.
4. Phong xuất API/hooks đọc danh mục; Việt Anh và Khôi chốt props các modal dùng chung.
5. Mỗi người khai báo route trong feature mình, Thuận nối vào router tổng qua PR.
6. Trước khi có module phụ thuộc, có thể dùng mock lúc phát triển; phải đánh dấu rõ
   và bỏ khỏi luồng thật trước khi coi chức năng hoàn thành.

Gợi ý hợp đồng (thống nhất kiểu dữ liệu trước khi viết):
- ApplyDialog({open, jobId, invitationId?, onClose, onSuccess}).
- InviteDialog({open, jobId, studentId, onClose, onSuccess}).
- MatchScorePanel({match, loading, error}).
- CVAnalysisPanel({cvId, canAnalyze}).
- ExportButton({reportType, filters}).

Không tự ý truyền dữ liệu nhạy cảm vào component nếu response backend không có quyền
trả về. Frontend ẩn nút để hướng dẫn thao tác; backend mới là nơi quyết định quyền.

## 7. Thứ tự thực hiện

Không chốt số ngày khi nhóm chưa thống nhất thời hạn. Dùng bốn mốc theo đầu ra:

### Mốc 0 — Thiết kế và nền tảng

Thuận scaffold/layout/theme; Quang auth/HTTP client; Phong catalog đọc; Việt Anh và
Khôi dựng một màn chính bằng dữ liệu mẫu. Chốt 3 mẫu desktop/mobile trước khi mở rộng.

### Mốc 1 — Luồng cơ bản nối API thật

- Quang: đăng nhập/quên/kích hoạt, guard, thông báo và duyệt doanh nghiệp/tin.
- Phong: danh mục, danh sách/chi tiết sinh viên, giảng viên.
- Việt Anh: tìm việc, hồ sơ, CV.
- Khôi: hồ sơ công ty, CRUD/gửi duyệt tin.
- Thuận: gợi ý việc/ứng viên, panel AI và tổng quan admin.

### Mốc 2 — Luồng nghiệp vụ hoàn chỉnh

- Quang: quản lý tài khoản, báo cáo vi phạm, nhật ký email.
- Phong: import, thực tập, phân công và xác nhận kết quả.
- Việt Anh: ứng tuyển, lời mời, lưu tin, theo dõi/rút đơn, đợt của tôi.
- Khôi: Kanban, snapshot CV, lời mời, thống kê tin; form đánh giá theo ngữ cảnh.
- Thuận: toàn bộ biểu đồ/bộ lọc, xuất file, nối các modal dùng chung.

### Mốc 3 — Tích hợp và bàn giao

Cả nhóm kiểm tra desktop/mobile và các luồng xuyên role, xóa dữ liệu giả trong
luồng thật, xử lý lỗi API, rà soát quyền riêng tư, tài liệu và bản demo. Thuận điều
phối checklist tích hợp; người sở hữu module chịu trách nhiệm sửa lỗi của module đó.

## 8. Quy trình Git

Lấy main mới nhất sau khi đã lưu code riêng, rồi tạo nhánh theo công việc:

- Quang: feature/fe-quang-auth, feature/fe-quang-moderation.
- Phong: feature/fe-phong-catalog, feature/fe-phong-school.
- Việt Anh: feature/fe-vietanh-student.
- Khôi: feature/fe-khoi-company.
- Thuận: feature/fe-thuan-foundation, feature/fe-thuan-matching-analytics.

Không cần một nhánh mới cho mỗi lần push; có thể nhiều commit/push trên nhánh của
một tính năng. PR theo từng tính năng, một người khác review, kiểm tra lint/build
và test liên quan trước khi merge. Không push thẳng main. Chỉ người điều phối sửa
package.json/router/theme dùng chung; trường hợp cần sửa phải thống nhất trước.

Nếu chưa có frontend/develop, mở PR vào main theo quy trình nhóm đang dùng; nếu cả
nhóm thống nhất một nhánh tích hợp frontend thì đổi đích PR cho tất cả thành viên,
không để mỗi người tự chọn một chiến lược khác nhau.

## 9. Định nghĩa hoàn thành

Một tính năng chỉ được coi là xong khi:
- Đúng thiết kế đã duyệt, responsive ít nhất desktop và mobile.
- Gọi API thật thành công, không dùng dữ liệu giả trong luồng hoàn chỉnh.
- Có loading, empty, lỗi API/validate và trạng thái không đủ quyền.
- Các hành động phải có thật trong API; thao tác nhạy cảm có xác nhận, chống gửi lặp.
- Dữ liệu sau thêm/sửa/xóa cập nhật đúng; bộ lọc và phân trang không mất ngữ cảnh.
- Các kiểu response khớp OpenAPI; null không tự đổi thành 0 hoặc dữ liệu suy đoán.
- Có kiểm tra phù hợp: form/guard/component cho logic quan trọng và thử luồng API;
  không chỉ chụp ảnh màn hình để kết luận tính năng chạy đúng.
- npm run lint, npm run build và test theo script nhóm chốt đều đạt.
- PR có mô tả việc đã làm, cách thử, ảnh desktop/mobile và vấn đề còn lại; được review.

## 10. Kịch bản test chung

1. Import sinh viên -> email -> kích hoạt -> đăng nhập -> hoàn thiện hồ sơ -> CV.
2. Đăng ký công ty -> admin duyệt -> công ty tạo tin -> admin duyệt -> sinh viên tìm thấy.
3. Gợi ý -> lưu tin -> nộp đơn -> doanh nghiệp xem đúng snapshot -> Kanban đến HIRED.
4. Gợi ý ứng viên -> gửi lời mời -> sinh viên nộp đơn theo lời mời -> trạng thái cập nhật.
5. Tắt chia sẻ GPA/liên hệ -> kiểm tra giao diện doanh nghiệp và dữ liệu thực nhận.
6. Đợt -> sinh viên thuộc đợt thấy tin; ngoài đợt bị chặn -> phân công -> xác nhận kết quả.
7. Lỗi token/hết phiên, 403/404/422, mạng lỗi, upload sai loại/quá lớn, bảng rỗng.
8. Bộ lọc thống kê -> xuất báo cáo đúng; mobile không tràn màn hình hoặc mất hành động.

## 11. Các giới hạn cần biết trước khi thiết kế

- API có form đánh giá doanh nghiệp theo result_id, nhưng chưa có API danh sách
  kết quả dành cho doanh nghiệp. Khôi/Phong/Thuận phải chốt bổ sung API hoặc điểm
  cung cấp result_id trước khi cam kết luồng này hoàn chỉnh; không suy đoán ID.
- Sinh viên xem được đợt/giảng viên nhưng chưa có endpoint xem bảng điểm thực tập riêng.
- Chưa có chat, đăng nhập LMS/SSO, lịch phỏng vấn riêng, SMS/OTP, thanh toán hoặc
  tạo CV PDF. Không đưa các tính năng này vào nhiệm vụ mặc định.
- Avatar/logo đang nhận URL; chưa có API upload ảnh riêng.
- Giấy tờ doanh nghiệp có metadata/file_url; cần xác nhận cách phân phối file trước
  khi triển khai preview/tải, không giả định đường file trong DB là URL truy cập được.
- Các link email phụ thuộc FRONTEND_URL; frontend phải có route /activate và
  /reset-password đọc token từ query đúng hợp đồng.
- Backend mặc định CORS cho http://localhost:5173; dùng origin khác phải cấu hình
  backend. VITE_API_BASE_URL chỉ chứa địa chỉ API, không chứa bí mật.

## 12. Theo dõi công việc

Mỗi người cập nhật bảng này trong PR hoặc công cụ theo dõi chung:

| Tính năng | Người phụ trách | Thiết kế duyệt | UI | API thật | Test | PR | Vướng mắc |
|---|---|---|---|---|---|---|---|
| Ví dụ: đăng nhập | Quang | Chưa | Chưa | Chưa | Chưa | — | — |

Không đánh dấu hoàn thành chỉ vì đã dựng xong giao diện. Báo sớm khi thiếu API,
đổi schema, phụ thuộc component hoặc không rõ quy tắc nghiệp vụ.
