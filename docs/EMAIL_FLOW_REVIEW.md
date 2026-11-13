# Rà soát email — 13/11/2026

Phạm vi: nhánh `fix/freelancer-backend-a-d-local-20261107`.

## Các luồng hiện có

| Luồng | Người nhận | Cách gửi |
| --- | --- | --- |
| Cấp/gửi lại tài khoản sinh viên | Sinh viên được cấp | BackgroundTasks, worker khôi phục khi bị gián đoạn |
| Quên mật khẩu | Chủ tài khoản đủ điều kiện | BackgroundTasks; không tiết lộ tài khoản có tồn tại hay không |
| OTP xác minh email | Email hiện tại của chính người yêu cầu | Gửi đồng bộ sau commit; lỗi gửi làm mã mất hiệu lực; chỉ lưu metadata nhật ký, không lưu OTP thô |
| Duyệt/từ chối doanh nghiệp và pháp nhân | Doanh nghiệp tương ứng | BackgroundTasks hoặc hàng email của worker |
| Duyệt/từ chối tin tuyển dụng | Doanh nghiệp sở hữu tin | BackgroundTasks |
| Ứng tuyển tuyển dụng | Sinh viên xác nhận nộp + doanh nghiệp nhận ứng viên | BackgroundTasks |
| Mời ứng tuyển | Sinh viên được mời | BackgroundTasks |
| Chuyển trạng thái/phỏng vấn | Sinh viên của đơn ứng tuyển | BackgroundTasks; trạng thái tiếng Việt, lịch giờ Việt Nam, địa điểm và hướng dẫn |
| Khóa/mở khóa tài khoản | Chủ tài khoản | BackgroundTasks |
| Xử lý báo cáo | Người báo cáo; chủ tài khoản bị khóa nếu có | BackgroundTasks |
| Các sự kiện freelancer có gọi `freelancer_domain.notify` | Người nhận đúng của thông báo web | Email và thông báo web được tạo cùng transaction; worker gửi email sau commit |
| MOU ký số kích hoạt/nhắc hết hạn/hết hạn | Doanh nghiệp sở hữu MOU | Hàng email worker |
| Ví chi thiếu tiền | Admin đang hoạt động | Email + thông báo web; giữ giới hạn một thông báo mỗi admin mỗi giờ |

Nhóm freelancer bao gồm gửi duyệt/kết quả duyệt dự án, ứng tuyển/kết quả lựa chọn, hợp đồng được gửi/chấp nhận, yêu cầu ký quỹ, nộp/nghiệm thu/chỉnh sửa bàn giao, thỏa thuận hủy, tranh chấp/quyết định và kết quả chuyển tiền. Khoản chi thiếu ngân hàng gửi yêu cầu bổ sung cho người nhận; khi thêm ngân hàng thành công gửi thông báo tiếp tục xử lý. Chỉ thông báo chuyển tiền thành công sau xác nhận của PayOS.

## Sửa lỗi độ tin cậy

- Bỏ cache nội dung email trong RAM. `email_logs.body_encrypted` lưu nội dung gốc đã mã hóa bằng khóa dẫn xuất riêng từ `SECRET_KEY`. API nhật ký không trả nội dung này. Giữ ổn định `SECRET_KEY` khi restart/deploy; đổi khóa sẽ không đọc được các thư đang chờ.
- `expires_at` ngăn gửi lại liên kết kích hoạt/reset hết hạn. Nội dung chứa token được xóa sau khi gửi thành công hoặc phát hiện hết hạn. Email cũ trước migration không có nội dung gốc sẽ không được gửi lại bằng nội dung chung sai lệch; cần tạo lại yêu cầu nghiệp vụ tương ứng.
- `next_attempt_at` đặt lịch thử lại sau 2 và 4 phút; tối đa 3 lần gửi. Admin có thể yêu cầu thử lại sớm với thư chưa hết giới hạn. OTP dùng luồng yêu cầu mã mới có chống spam, không tự gửi lại mã cũ.
- BackgroundTasks dùng session riêng; worker xử lý các thư chờ/lỗi khi backend restart hoặc tác vụ nền chưa chạy. Khóa bản ghi trên MariaDB và bỏ qua trạng thái SENT hạn chế gửi trùng giữa worker và tác vụ nền. SMTP không bảo đảm exactly-once: mất kết nối sau khi máy chủ đã nhận thư vẫn có khả năng gửi trùng khi thử lại.
- SMTP chưa cấu hình/nhận lỗi sẽ ghi FAILED, không giả lập SENT. SENT nghĩa là máy chủ SMTP đã chấp nhận, không chứng minh email vào Inbox; thư vẫn có thể bị đánh dấu spam hoặc bounce về sau.
- Hỗ trợ STARTTLS mặc định và TLS trực tiếp bằng `SMTP_SSL=true` (thường cổng 465). Nội dung tên, lời nhắn, lý do và các trường người dùng nhập được escape; tiêu đề loại bỏ xuống dòng và giới hạn 255 ký tự.
- OTP thành công/thất bại có nhật ký metadata, không lộ mã. Đã loại bỏ thông báo kết quả pháp nhân trùng giữa notify và outbox riêng.

## Vận hành

Migration mới: `python -m alembic upgrade head` (0011). Backend và worker đều cần khởi động lại sau cập nhật.

```powershell
cd B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c\backend
python -m scripts.freelancer_worker
```

Các email freelancer và việc khôi phục/thử lại email cần worker hoạt động. SMTP dùng `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_SSL` trong `backend/.env`. `FRONTEND_URL` cần trỏ đúng tên miền frontend khi triển khai. Không chạy worker trên database thật để kiểm thử: worker còn xử lý lệnh chi.

Kiểm tra cấu hình tại máy: DNS SMTP thành công, STARTTLS thành công, xác thực SMTP trả mã 235; phép kiểm tra này không gửi email. Kiểm thử tự động vô hiệu hóa SMTP thật và dùng mock để kiểm tra gửi lỗi, gửi lại, mã hóa, hết hạn, không gửi trùng, quyền xem nhật ký và các luồng nghiệp vụ. Chưa xác nhận việc đến Inbox bằng một email thử do người dùng chỉ định.

Kết quả: 116 kiểm thử email/tài khoản/tuyển dụng/OTP/worker/migration và 73 kiểm thử hợp đồng, bàn giao, tài chính, tranh chấp đều đạt (189 tổng cộng). Migration 0011 đã áp dụng vào MariaDB local. Kiểm thử scanner lỗi được giả lập rõ ràng để không phụ thuộc Windows Defender của máy.
