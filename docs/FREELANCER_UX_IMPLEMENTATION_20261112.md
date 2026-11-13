# Cập nhật UX Freelancer — 12/11/2026

Phạm vi: worktree `tmp/fix-freelancer-a-c`, theo `SPEC_FREELANCER_UX_IMPROVEMENTS.md`.

## Kết quả theo đặc tả

| Module | Đã triển khai |
| --- | --- |
| 1. Kỹ năng tự do | Tag input có tìm kiếm, thêm bằng Enter/dấu phẩy, xóa tag. `POST /catalog/skill-tags` chuẩn hóa Unicode/khoảng trắng/chữ hoa thường, tái sử dụng tên hoặc alias, tạo kỹ năng `OTHER` hoạt động ngay. Form gửi ID thật để giữ quan hệ khóa ngoại và matching. Không tạo hàng đợi admin. |
| 2. Chọn ngân hàng | `GET /finance/banks` trả snapshot 76 ngân hàng VietQR, cache trong bộ nhớ; JSON khoảng 11,8 KB. Dropdown tìm tên/tên viết tắt/mã, hiển thị logo; gửi ngầm `bank_bin`. Giữ nguyên API tài khoản ngân hàng và xử lý PayOS. |
| 3. Điều khoản ký quỹ | Chặn trang tạo dự án đầu tiên của CLIENT/COMPANY, kể cả vào URL trực tiếp; nút xác nhận khóa đến khi cuộn hết. API kiểm tra đồng ý, lưu thời điểm/phiên bản trên user và audit; gửi lại không ghi đè thời điểm đầu tiên. API tạo dự án trực tiếp cũng bị chặn nếu chưa đồng ý. |
| 4. Mẫu dự án | Modal 4 nhóm ngành với phạm vi, danh sách bàn giao, tiêu chí và tỷ lệ chia mốc. Chỉ tham khảo; không có thao tác ghi đè hay tự điền form. |
| 5. Menu trái | Nhóm cố định Tuyển dụng → Freelancer → Quản lý; Trang chủ ở đầu, Thông báo/Tài khoản ở cuối. Nhóm có thu gọn, tự mở khi vào trang con; thụt 36px, đường chỉ dẫn, nền slate và trạng thái xanh đồng nhất các role. |
| 6. Điều khoản đăng ký | Form doanh nghiệp/người thuê mặc định chưa tích đồng ý; có modal 2 tab và xác nhận nhanh. Nút đăng ký bị khóa khi chưa đồng ý. Backend bắt buộc `terms_acceptance: {accepted: true, version: "2026-11-12"}` và lưu thời điểm/phiên bản. Link bảo mật ở footer mở đúng nội dung. |

## API và migration

- API mới: `POST /api/v1/catalog/skill-tags`, `GET /api/v1/finance/banks`, `GET/POST /api/v1/auth/escrow-terms`.
- Migration `0007_ux_terms.py` thêm `registration_terms_accepted_at`, `registration_terms_version`, `escrow_terms_accepted_at`, `escrow_terms_version` vào `users`.
- Dữ liệu cũ để NULL; không suy diễn người dùng đã đồng ý. Lần tạo dự án tiếp theo yêu cầu đọc điều khoản nếu chưa có xác nhận.
- Snapshot cài mới `backend/database/student_connect_latest.sql` đã cập nhật đến 0007. Snapshot nền `freelancer_schema.sql` vẫn ở 0004; nếu dùng snapshot này phải chạy Alembic lên head như trước.
- Chưa chạy migration trên cơ sở dữ liệu đang sử dụng. Khi triển khai, chạy trong thư mục `backend`:

```powershell
python -m alembic upgrade head
```

## Những điểm đã đối chiếu với hệ thống thực tế

- Đổi thời hạn nghiệm thu mặc định từ 14 xuống 7 ngày. Không ghi đè chính sách admin đã lưu hoặc thời hạn đã chốt trong hợp đồng. Modal đọc thời hạn hiện hành từ API, giải thích tự động nghiệm thu/lập nghĩa vụ chi khác với tiền đã đến ngân hàng.
- Ký quỹ theo mốc vẫn phụ thuộc hạng tài khoản/chính sách hiện có; nội dung modal nêu rõ điều kiện này.
- Không thay đổi cơ chế hai admin duyệt hoặc quy trình xác minh tài khoản ngân hàng: đặc tả UX này không yêu cầu thay đổi những phần đó.
- Chính sách riêng tư dùng pháp luật hiện hành, có tham chiếu Luật 91/2025/QH15, tránh ghi Nghị định 13/2023 là căn cứ duy nhất và tránh cam kết kỹ thuật mã hóa chưa được chứng minh.

## Kiểm tra

- Build TypeScript + Vite: thành công.
- Vitest: 69 kiểm thử, 16 file, đều qua.
- Backend nhóm đăng ký, UX, dự án, migration: 44 kiểm thử qua.
- Backend hồi quy Freelancer + kiến trúc + UX: 219 qua, 11 bỏ qua do điều kiện môi trường của các bài MariaDB/provider. Không dùng kết quả SQLite thay cho xác nhận MariaDB thực tế.
- Playwright: 26 kịch bản đã qua, gồm 25 bài ở lượt chạy toàn bộ cuối và 1 bài admin qua khi chạy lại riêng. Bài admin gặp timeout trong lượt toàn bộ sau gián đoạn thời gian bất thường (runner báo 3,3 giờ); chạy riêng hoàn tất trong 7,6 giây. Bốn kịch bản UX mới cũng đã qua ở lượt chạy riêng.
- Kiểm thử migration chạy lại sau khi đồng bộ DATETIME(6) cho MariaDB: 4 bài qua. `git diff --check` không có lỗi khoảng trắng.
- Đã xem ảnh desktop/mobile tại `ux-improvements-previews/sidebar-desktop.png` và `ux-improvements-previews/project-mobile.png`.
- Các test backend dùng `DEBUG=false`, `FREELANCER_FINANCE_ENABLED=false` cho SQLite; những test tài chính chuyên biệt tự cấu hình fixture tương ứng. Không gọi thanh toán thật.

## Nguồn dữ liệu

- Danh mục công khai [VietQR](https://api.vietqr.io/v2/banks), lấy ngày 12/11/2026. Runtime không cần gọi API VietQR; logo tải theo URL công khai, vẫn giữ tên ngân hàng khi logo không tải được.
- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=).
