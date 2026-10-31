# Hoàn thiện frontend trên nhánh tích hợp local

Ngày cập nhật: 31/10/2026. Nhánh: integration/frontend-local.
Không đẩy lên GitHub hoặc gộp main trong đợt thay đổi này.

## Quy ước giao diện

Giữ StudentLayout, CompanyLayout và AdminLayout; dùng màu theo actor, font, khoảng cách,
header/sidebar từ khung chung. Không thêm router/AuthProvider/QueryClient mới.
Form dùng React Hook Form + Zod; HTTP có token/refresh dùng chung. Các bảng có trạng thái
tải/rỗng/lỗi, phân trang backend, lỗi validate theo trường. Thao tác quan trọng có xác nhận.
CSS các màn mới nằm trong components/common/workspace.css và dùng design tokens sẵn có.

## Trang và API

| Khu vực | Trang | API chính |
|---|---|---|
| Admin | users | /admin/users, /admin/users/admins, /{id}/lock, /{id}/unlock |
| Admin | companies | /admin/companies, /{id}, /{id}/approve, /{id}/reject |
| Admin | jobs | /admin/jobs, /{id}, /{id}/approve, /{id}/reject, /{id}/close |
| Admin | reports | /reports, /{id}, /{id}/handle |
| Admin | email-logs | /admin/users/email-logs, /email-logs/retry |
| Admin | analytics | /admin/dashboard/*, /admin/exports/*, /matching/recompute |
| Sinh viên | jobs, jobs/:jobId, companies/:companyId | GET /jobs, /jobs/{id}, /companies/{id}; POST /reports |
| Sinh viên | saved-jobs | /saved-jobs và nút lưu dùng chung matching |
| Sinh viên | profile | /students/me, /me/profile, /me/skills, /me/experiences, /me/projects, /me/certificates |
| Sinh viên | cvs | GET /cvs/me, POST /cvs/online, PUT/DELETE /cvs/{id}, /set-default, /download, /analyze |
| Sinh viên | applications, applications/:applicationId | /applications/me, /{id}, /{id}/withdraw |
| Sinh viên | invitations | /invitations/me, /{id}/decline; ứng tuyển kèm invitation_id |
| Sinh viên | internships | /students/me/internship |
| Doanh nghiệp | profile | /companies/me và /documents |
| Doanh nghiệp | jobs, jobs/:jobId/stats | /jobs/me, POST /jobs, PUT /jobs/{id}, /submit, /close, /stats |
| Doanh nghiệp | applications | /company/applications, /{id}, /{id}/status, tải cv_download_url |
| Doanh nghiệp | invitations | /invitations/company; gửi từ matching |
| Doanh nghiệp | evaluations/:resultId | PUT /internship-terms/results/{id}/evaluation |

Các đường dẫn API trong bảng đều dưới /api/v1. Trường payload bám schema backend;
GPA 0 được giữ nguyên, null ở khu vực doanh nghiệp hiển thị không chia sẻ.
Không tải CV gợi ý ứng viên khi chưa có đơn; tải CV ứng tuyển bằng URL snapshot của đơn.
Kanban tải và phân trang độc lập từng cột, chuyển trạng thái qua drawer có xác nhận,
không giả lập kéo thả hoặc lịch phỏng vấn riêng.

## CV online theo yêu cầu mới

- Không có chọn tệp hoặc POST /cvs/upload trong các trang đang dùng.
- Dữ liệu nhà trường hiển thị chỉ đọc. Backend tự chèn official khi tạo/sửa CV;
  frontend chỉ gửi các trường bổ sung, không gửi GPA/ngành/khoa/họ tên thay thế.
- Gợi sẵn nội dung từ hồ sơ tự khai, cho bổ sung mục tiêu, kỹ năng, kinh nghiệm,
  dự án và liên hệ; thay đổi tại CV không sửa hồ sơ gốc.
- Có xem trước bản CV đã lưu, đặt mặc định, sửa, xóa, phân tích và tải dữ liệu JSON.
- Danh sách CV và ApplyDialog chỉ hiển thị ONLINE, kể cả khi database còn CV tải lên cũ.
- API upload backend được giữ nguyên để tương thích; đây là thay đổi luồng frontend.
- Chưa có API xuất PDF cho CV online. Không quảng cáo tải CV PDF.

## Giới hạn backend được giữ rõ

- Chưa có API tải giấy tờ doanh nghiệp có kiểm soát quyền; hiển thị metadata/tham chiếu,
  không mở đường dẫn filesystem như một URL công khai.
- Chưa có API danh sách kết quả dành cho công ty; admin sao chép link đánh giá từ kết quả
  đã gắn doanh nghiệp. Backend vẫn quyết định công ty nào được ghi và kết quả đã khóa.
- Chưa bổ sung LECTURER, tài khoản giảng viên hoặc bảng điểm thực tập của sinh viên.
- Matching recompute chỉ thông báo xếp hàng, không có tiến độ giả.
- Dashboard dùng số liệu thật; biểu đồ trên phần dữ liệu đang phân trang, không suy luận
  tăng trưởng, phần trăm tuyển thành công hoặc số liệu ngoài response.

## Chạy kiểm tra

Trong frontend:

```powershell
npm run lint
npm run build
npm test
npm run test:e2e
```

Với backend demo local do start-local.ps1 khởi động:

```powershell
npm run test:live
```

Script tạo công ty/tin/CV/đơn/báo cáo thử trên database demo local và giữ dữ liệu để xem.
Không chạy script live với database dùng chung hoặc production. Không mock API trong
script này; bộ test:e2e dùng fixture để kiểm tra hồi quy, phân quyền và các trường hợp lỗi.
Ảnh desktop/mobile ở ../tmp/local-runtime/completion/ tính từ frontend.

MariaDB/SMTP/AI thật chưa được xác nhận trong đợt frontend này: demo dùng FastAPI + SQLite,
SMTP và khóa AI để trống. Phân tích CV có thông báo lỗi nếu chưa cấu hình nhà cung cấp.
