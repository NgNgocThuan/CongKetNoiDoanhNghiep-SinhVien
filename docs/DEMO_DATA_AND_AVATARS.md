# Dữ liệu mẫu và ảnh đại diện

Chạy trong thư mục `backend`:

```powershell
python -m alembic upgrade head
python -m scripts.prepare_defense_jobs
```

Script bổ sung 8 loại hình công việc, 70 nhóm lĩnh vực và 12 tin tuyển dụng
đầy đủ cho các tình huống trình bày đề án. Danh mục mang tính bao quát thực hành; admin có thể thêm
chuyên ngành mới trong trang Danh mục. Đây không phải danh sách cố định của mọi
ngành nghề có thể tồn tại.

Script nâng cấp 12 tin `[DEMO]` cũ tại chỗ, giữ nguyên ID và gắn vào tài khoản
doanh nghiệp tương ứng. Không sửa các tin khác. Nếu một tin cũ đã có ứng viên,
script dừng để tránh thay đổi quyền quản lý hồ sơ của ứng viên khi chuyển doanh nghiệp.
Chạy lại không tạo trùng, không tự mở lại tin đã đóng và không gia hạn tin cũ.
Tin mới được chuẩn bị với hạn ứng tuyển 45 ngày; các trường bắt buộc, lương,
địa điểm, thời gian làm việc, yêu cầu, quyền lợi và kỹ năng đều có nội dung cụ thể.

Các công ty và tin do script bổ sung là tình huống được biên soạn cho đề án,
không phải quảng cáo tuyển dụng bên ngoài đã được xác nhận. Trạng thái xác minh
được thiết lập trong môi trường đề án để thử quy trình; mã pháp nhân có tiền tố
`SC-` là mã dữ liệu tình huống, không phải mã số thuế pháp lý.

| Doanh nghiệp | Tài khoản |
| --- | --- |
| TechCorp | Tái sử dụng tài khoản TechCorp hiện có; không đổi mật khẩu/hồ sơ |
| Truyền thông Lam Sáng | `careers@lamsang.example` |
| Dịch vụ Kết Nối | `careers@ketnoiservices.example` (kế thừa tài khoản cũ `recruiter@demo.example`) |
| Giáo dục Minh Tri | `careers@minhtriedu.example` |

Tài khoản được tạo mới có mật khẩu ban đầu `Password@123`. Các tài khoản đã có
giữ nguyên mật khẩu. Địa chỉ `.example` phục vụ đăng nhập tình huống, không nhận email thực.
Trên database mới chưa có TechCorp, script tạo `careers@techcorp.example`.
Lệnh `python -m scripts.seed_demo_catalog` cũ vẫn được hỗ trợ và chuyển sang bộ dữ liệu mới.

Mọi vai trò có tài khoản đang hoạt động có thể vào **Tài khoản & bảo mật →
Ảnh đại diện** để chọn file JPG/PNG/WebP tối đa 2 MB, xem trước và bấm lưu.
Sinh viên cũng có thể thay ảnh trong form hồ sơ. Không cần nhập URL.

Backend xác thực nội dung ảnh, chuẩn hóa thành JPEG vuông 384 × 384,
loại bỏ metadata và lưu trong bảng `user_avatars` (migration `0008`).
API đọc ảnh yêu cầu đăng nhập. Tải ảnh mới sẽ cập nhật ảnh ở các vị trí dùng chung.

Bảng bằng chứng hiển thị tên hồ sơ (hoặc email khi chưa có tên), vai trò và
ảnh đại diện của người gửi. Quyền đọc bằng chứng vẫn giới hạn trong các bên
của tranh chấp và admin.
