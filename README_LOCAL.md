# Bản tích hợp chạy local — 31/10/2026

## Mở ngay

- Frontend: http://127.0.0.1:5173
- Backend FastAPI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Bản phát hành: `demo 31/10/2026` trên `main`.
- Chạy từ thư mục repository bạn clone/cập nhật về máy, không cần vào worktree `tmp/frontend-local`.

| Vai trò | Email demo | Mật khẩu |
|---|---|---|
| Nhà trường/Admin | admin@school.edu.vn | Password@123 |
| Sinh viên | sv001@school.edu.vn | Password@123 |
| Doanh nghiệp | hr@acme.vn | Password@123 |

Đây là các tài khoản và dữ liệu demo do scripts.seed tạo trong database local riêng,
không phải tài khoản thật của thành viên. Các thao tác trên UI gọi API và lưu dữ liệu thật
vào database demo.

## Khởi động lại / tắt

Từ thư mục gốc repository:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\stop-local.ps1
~~~

Chạy lệnh tắt trước khi khởi động lại. Script không tự dừng ứng dụng khác đang chiếm cổng.
Nếu chưa có thư viện frontend, chạy npm ci trong frontend trước.
Python cần được cài dependencies trong backend/requirements.txt; môi trường local có thể
dùng .venv đã kích hoạt. Script cũng hỗ trợ .codex-deps của repository gốc nếu đã có.

Database, file upload, log và PID nằm trong tmp/local-runtime/ (được Git bỏ qua).
Không xóa thư mục này nếu muốn giữ dữ liệu vừa thao tác.

## Nhánh nguồn

- main a961ded: backend đã tích hợp và bộ khung frontend.
- feature/fe-thuan-matching a49d70d.
- feature/fe-phong-shared-frame 3459e21.
- feature/fe-quang-auth c7ad6af (đã có các bản sửa sau review).
- feature/fe-khoi-company b7d00d3.
- feature/fe-vietanh-student 7a023d4: thay phần giao diện sinh viên do bản local tự tạo.

Không đưa feature/phong-backend cũ vào bản này vì phần frontend đã được chuyển về
khung chung trên nhánh fe-phong-shared-frame.

Đã ghép route, menu, providers, dependency lock và test setup. Giữ App/router chung,
không dùng App chuyển màn hình demo của nhánh Khôi. Tailwind được build bằng PostCSS,
không dùng Play CDN để chạy CSS.

## Phần doanh nghiệp và giới hạn

Nhánh Khôi hiện chủ yếu là giao diện mẫu:
- Nhiều dữ liệu ứng viên/tin/hồ sơ được viết cố định trong component.
- Có sidebar/header riêng và App chuyển màn hình thử.
- API helper dùng fetch chưa gắn token; nhiều thao tác chỉ đổi state hoặc hiện thông báo.
- Form đánh giá nhận RESULT-1001 mẫu, chưa có nguồn result_id thật.

Không chạy các dữ liệu mẫu này như kết quả backend. Mã gốc của Khôi được giữ trong
features/company-* để tiếp tục hoàn thiện theo thiết kế.

Bản local hiện đã bổ sung:
- Nhà trường: tài khoản/tạo admin/khóa/mở khóa; duyệt doanh nghiệp và tin;
  báo cáo vi phạm, nhật ký email, dashboard và xuất Excel/PDF.
- Sinh viên: tìm/lọc tin, hồ sơ công ty, lưu việc, hồ sơ chính thức chỉ đọc,
  thông tin tự khai, kỹ năng/kinh nghiệm/dự án/chứng chỉ; CV online và xem trước;
  ứng tuyển, lịch sử/rút đơn, lời mời, đợt thực tập và giảng viên.
- Doanh nghiệp: đầy đủ form hồ sơ, giấy tờ, tạo/sửa/gửi duyệt/đóng tin, thống kê;
  bảng/Kanban có tải thêm từng cột, chi tiết và lịch sử đơn, chuyển trạng thái
  có xác nhận, tải snapshot CV, danh sách lời mời.

Theo yêu cầu mới: chỉ tạo CV ONLINE từ dữ liệu trường và thông tin bổ sung.
Không có nút tải tệp CV lên; không dùng CV UPLOADED cũ trong danh sách ứng tuyển.
CV online tải dữ liệu JSON theo API, chưa xuất PDF. Không xóa dữ liệu CV cũ.

Giới hạn: giấy tờ chưa có endpoint tải an toàn; doanh nghiệp chưa có API danh sách
kết quả thực tập. Form đánh giá dùng /company/evaluations/:resultId qua link nhà
trường cung cấp. Chưa có tài khoản giảng viên riêng hoặc bảng điểm sinh viên.
Xem frontend/docs/FRONTEND_COMPLETION.md để biết danh sách API và cách kiểm tra.

## Backend và dịch vụ ngoài

MariaDB cấu hình localhost:3306 chưa kết nối được trên máy tại thời điểm kiểm tra.
Bản chạy này dùng FastAPI thật + SQLite riêng:
tmp/local-runtime/student-connect.sqlite3.

Không thay đổi database hoặc .env của bản dự án cũ. SMTP_HOST, AI_API_KEY và AI_MODEL
được để trống trong tiến trình demo để không gửi email hoặc gọi dịch vụ AI bên ngoài.
Matching vẫn chạy theo kỹ năng khai báo và công thức backend; không phải lượt kiểm tra
trích xuất AI thật. Gửi mail/AI thật và MariaDB cần được cấu hình, kiểm tra riêng.

## Kiểm tra

Trong frontend, chạy npm run lint, npm run build, npm test, npm run test:e2e.
Kiểm tra API thật: khởi động start-local.ps1 rồi chạy npm run test:live trong frontend.
Script live dùng Chrome và tạo dữ liệu thử trên database demo local, không mock API.
Đã thử duyệt doanh nghiệp/tin, khóa–mở tài khoản, tạo CV online, ứng tuyển,
chuyển trạng thái/tải snapshot/Kanban, báo cáo vi phạm, xuất PDF và ba layout mobile.
Ảnh kiểm tra ở tmp/local-runtime/completion/.
