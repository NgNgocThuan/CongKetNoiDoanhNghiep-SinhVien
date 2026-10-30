# Bản tích hợp chạy local — 31/10/2026

## Mở ngay

- Frontend: http://127.0.0.1:5173
- Backend FastAPI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Nhánh local: integration/frontend-local. Không có upstream và chưa đẩy lên GitHub.
- Thư mục: B:/project/student-connect/student-connect/tmp/frontend-local

| Vai trò | Email demo | Mật khẩu |
|---|---|---|
| Nhà trường/Admin | admin@school.edu.vn | Password@123 |
| Sinh viên | sv001@school.edu.vn | Password@123 |
| Doanh nghiệp | hr@acme.vn | Password@123 |

Đây là các tài khoản và dữ liệu demo do scripts.seed tạo trong database local riêng,
không phải tài khoản thật của thành viên. Các thao tác trên UI gọi API và lưu dữ liệu thật
vào database demo.

## Khởi động lại / tắt

Từ thư mục bản tích hợp:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\stop-local.ps1
~~~

Chạy lệnh tắt trước khi khởi động lại. Script không tự dừng ứng dụng khác đang chiếm cổng.
Nếu chưa có thư viện frontend, chạy npm ci trong frontend trước.
Python dùng thư viện đã có trên máy và .codex-deps của repository gốc.

Database, file upload, log và PID nằm trong tmp/local-runtime/ (được Git bỏ qua).
Không xóa thư mục này nếu muốn giữ dữ liệu vừa thao tác.

## Nhánh nguồn

- main a961ded: backend đã tích hợp và bộ khung frontend.
- feature/fe-thuan-matching a49d70d.
- feature/fe-phong-shared-frame 3459e21.
- feature/fe-quang-auth c7ad6af (đã có các bản sửa sau review).
- feature/fe-khoi-company b7d00d3.

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

Bản local bổ sung features/company-live làm adapter kiểm thử API:
- Hồ sơ: đọc/lưu các trường backend cho phép.
- Tin: đọc danh sách, tạo nháp tối thiểu, gửi duyệt, đóng tin.
- Ứng viên: bắt buộc chọn tin, đọc đơn, tải CV snapshot và chuyển trạng thái theo backend.
- Lời mời đã gửi: đọc danh sách thật; gửi lời mời từ trang matching.

Đây chưa phải bản hoàn thiện Kanban, chỉnh sửa tin, upload giấy tờ hoặc đánh giá thực tập
theo thiết kế Khôi. Chọn tin trong màn kiểm tra đơn hiện lấy 20 tin đầu tiên.
Các API dữ liệu thật đều đi qua HTTP/auth chung; không hiển thị thống kê tự tạo.

Chưa có frontend sinh viên đầy đủ của Việt Anh trong các nhánh hiện có:
hồ sơ/CV/đơn ứng tuyển đầy đủ vẫn là placeholder. Trang matching đã có dialog chọn CV,
nộp đơn và lưu việc độc lập. Dashboard phân tích Admin cũng chưa được triển khai UI đầy đủ.

## Backend và dịch vụ ngoài

MariaDB cấu hình localhost:3306 chưa kết nối được trên máy tại thời điểm kiểm tra.
Bản chạy này dùng FastAPI thật + SQLite riêng:
tmp/local-runtime/student-connect.sqlite3.

Không thay đổi database hoặc .env của bản dự án cũ. SMTP_HOST, AI_API_KEY và AI_MODEL
được để trống trong tiến trình demo để không gửi email hoặc gọi dịch vụ AI bên ngoài.
Matching vẫn chạy theo kỹ năng khai báo và công thức backend; không phải lượt kiểm tra
trích xuất AI thật. Gửi mail/AI thật và MariaDB cần được cấu hình, kiểm tra riêng.

## Đã kiểm tra

- Build thành công; lint không lỗi; 59 unit test đạt.
- 25 kiểm tra trình duyệt cho khung chung, matching và nhà trường đạt.
- Smoke bằng Chrome KHÔNG mock API, với backend đang chạy trên cổng 8000:
  - Đăng nhập ba vai trò.
  - Sinh viên đọc matching, lưu việc, chọn CV và nộp đơn.
  - Doanh nghiệp lưu hồ sơ rồi tải lại xác nhận.
  - Tạo tin nháp qua API.
  - Đọc đơn vừa nộp và chuyển sang SCREENING.
  - Gợi ý ứng viên theo tin, gửi lời mời; xem danh sách lời mời thật.
  - Sinh viên nhận thông báo từ backend.
  - Admin đọc danh sách sinh viên, khoa và đợt thực tập.
  - Không có lỗi JavaScript pageerror trong smoke.
- Database xác nhận có 1 đơn SCREENING, 1 lời mời, 3 thông báo sau smoke.
  Tin nháp tạo khi thử được giữ để bạn kiểm tra tiếp.
- Báo cáo/ảnh smoke nằm trong tmp/local-runtime/.
