# Khu vực sinh viên — Việt Anh

Nhánh: feature/fe-vietanh-student. Dựa trên main, không sửa backend/model/migration.
Thiết kế: [Stitch Student Connect Portal](https://stitch.withgoogle.com/projects/14789408940184842057).
Ảnh nguồn S05–S10: student-designs/. Đánh giá và brief: STUDENT-DESIGN.md.

## Các trang

| Route | Chức năng |
|---|---|
| /student/jobs | Tìm kiếm, bộ lọc theo API, kỹ năng, phân trang, lưu/bỏ lưu |
| /student/jobs/:id | Chi tiết, hồ sơ doanh nghiệp, ứng tuyển, báo cáo tin |
| /student/companies/:id | Dữ liệu công khai của doanh nghiệp |
| /student/saved-jobs | Tin đã lưu, bỏ lưu, trạng thái tin không còn nhận hồ sơ |
| /student/profile | Dữ liệu trường chỉ đọc; thông tin tự khai và quyền riêng tư; CRUD kỹ năng, kinh nghiệm, dự án, chứng chỉ SELF |
| /student/cvs | Upload PDF/DOCX, tạo/sửa online, mặc định, tải JSON/file, xóa mềm, phân tích |
| /student/applications | Danh sách phân trang và lọc trạng thái |
| /student/applications/:id | Chi tiết và timeline thật; rút khi APPLIED/SCREENING/SHORTLISTED/INTERVIEW |
| /student/invitations | Lời mời; từ chối có xác nhận hoặc ứng tuyển kèm invitation_id |
| /student/internships | Đợt, giảng viên và tin theo đợt; không tạo bảng điểm/nhật ký |

## Hợp đồng chia sẻ

- JobCard({job, saved?}), SaveJobButton({jobId, saved?}), CompanyPublicProfile({companyId})
  xuất từ features/student-jobs/index.ts.
- ApplyDialog({open, jobId, invitationId?, onClose, onSuccess?}) xuất từ
  features/student-applications/index.ts; onSuccess nhận ApplicationDetail.
- Không tạo endpoint accept riêng. CV mặc định được chọn ban đầu.
- downloadFile dùng đường API bảo vệ; CV online ghi rõ tải JSON.
- Chỉ thêm route vào feature-routes và chuyển ready cho menu của Việt Anh.
  Package, HTTP/auth, layout và theme chung được giữ theo scaffold.

## Phụ thuộc component chung

main tại thời điểm triển khai chưa có ReportDialog của Quang hoặc CVAnalysisPanel
của Thuận. Để các luồng có thể chạy độc lập, có hai adapter cục bộ:
ReportJobDialog trong student-jobs và CVAnalysis trong student-cvs.
Chúng chỉ gọi API backend, không tính điểm hoặc gọi LLM từ frontend.
Khi module chủ sở hữu được merge, thay adapter tại JobDetailPage/CVsPage bằng
export chung đã thống nhất; không sao chép nhánh nghiệp vụ của người khác vào PR này.
Trang gợi ý matching vẫn thuộc Thuận, không thay placeholder bằng dữ liệu giả.

Danh mục đọc qua adapter của student-jobs vì main hiện chỉ xuất API khoa trong
features/catalog. API luôn phân trang; selector cho phép tìm tên khi có nhiều mục.
Khi Phong xuất API/selector đầy đủ, có thể đổi adapter mà không đổi form nghiệp vụ.

## Kiểm tra

- npm run lint, npm run build, npm run test.
- Test mới: chọn CV mặc định, bảo toàn invitation_id/thư giới thiệu, lỗi ứng tuyển
  trùng, không có CV, payload chỉ chứa thông tin tự khai/cờ riêng tư, điều kiện rút
  đơn, lương chưa công bố không biến thành 0.
- Đã chạy backend với database demo SQLite cục bộ, đăng nhập tài khoản seed,
  tạo CV online, lưu tin, nộp đơn từ modal và xem timeline/thư giới thiệu thành công.
- Đã xem giao diện 390px; document scrollWidth 373px trong viewport 390px,
  không tràn ngang ở màn chi tiết đơn. Ảnh thực tế được lưu cùng ảnh tham chiếu.
- Upload, AI provider và gửi email thực tế còn phụ thuộc cấu hình máy chủ;
  UI hiển thị lỗi backend, không mô phỏng kết quả thành công.

## Chạy cục bộ

Chạy backend tại 127.0.0.1:8000 rồi chạy npm ci và npm run dev trong frontend.
Frontend: http://127.0.0.1:5173. Vite proxy API theo cấu hình đã có.
Tài khoản demo dùng dữ liệu seed cục bộ; không có mock mặc định trong sản phẩm.
Không commit database demo, uploads, token, .env, node_modules hoặc dist.
