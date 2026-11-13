# Bản sửa local phần Khôi và Quang — 07/11/2026

## Vị trí và phạm vi

- Nhánh local: `fix/freelancer-a-c-local-20261107`.
- Worktree: `B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c`.
- Nền: commit `aa1defe` của Quang (đã có lịch sử chung với main).
- Lấy riêng schema, endpoint, service và test nhóm A từ `4d804fb` của Khôi. Không lấy `app/main.py` hoặc thay thế bộ nền bằng cây thư mục thiếu của nhóm A.
- Chưa commit, chưa push, chưa merge vào main. Không sửa model/migration, không migrate database dự án.

## Lỗi đã sửa

### Quang

1. Hủy nháp chưa khóa dữ liệu và có thể ghi đè một hợp đồng vừa được kích hoạt: dùng cùng thứ tự khóa project → contract → budget → milestones; đọc lại ORM state dưới khóa MariaDB.
2. Phiên bản OFFERED còn chấp nhận được sau khi hợp đồng bị hủy: hủy nháp thu hồi các bản DRAFT/OFFERED; offer/accept kiểm tra trạng thái hợp đồng và ngân sách.
3. Hủy nháp bỏ qua payment order đang chưa đối soát: chặn các trạng thái đang xử lý/không rõ/đã nhận tiền trước khi giải phóng ngân sách.
4. Đóng tuyển có thể tự hủy hợp đồng đang thương lượng: đóng tuyển độc lập với vòng đời hợp đồng; chỉ kết thúc dự án hoặc căn cứ hủy hợp lệ mới cho đóng hợp đồng.
5. Sau sửa đổi hợp đồng, nghiệm thu lấy thời gian review/số lần sửa từ bản hợp đồng mới thay vì snapshot của milestone cũ: lấy policy từ version gắn với effective terms của milestone.

### Khôi

1. OTP trả thành công giả: lưu challenge HMAC, target, nonce, hạn dùng, lịch sử gửi, số lần thử và trạng thái trong `user_verifications`.
2. Sai OTP bị rollback mất số lần thử: commit kết quả xác minh trước khi trả lỗi; chặn dùng lại, hết hạn, vượt số lần thử; resend vô hiệu challenge cũ.
3. Khóa HMAC hardcode và chưa gửi mã thật: dùng `FREELANCER_OTP_SECRET` riêng, bắt buộc SMTP thật; gửi sau commit, lỗi gửi vô hiệu challenge. Không trả/log/lưu mã OTP thô.
4. Eligibility gọi kiểu/hàm không tồn tại và sai policy người thuê cá nhân: thống nhất rule/service theo đặc tả 2.2; CLIENT xác minh email được tạo nháp, thêm điện thoại mới gửi duyệt/cấp vốn. COMPANY dựa trên pháp nhân và đình chỉ. MOU hiệu lực tính theo thời gian và không bị bản tương lai che khuất.
5. Hồ sơ doanh nghiệp dùng enum sai và thiếu bản ghi nộp: lưu snapshot và liên kết file, số thứ tự submission, thông tin đại diện, audit; chặn nộp trùng/chưa có file sạch/sai quyền/đình chỉ.
6. MOU sai tên cột và thiếu trường bắt buộc: map `mou_code` sang `agreement_code`, bổ sung file/người ký/chức vụ/phạm vi/thời hạn; kiểm tra ownership và pháp nhân; lưu `PENDING_REVIEW`, chữ ký `NOT_CHECKED`.
7. File giả CLEAN/URL mẫu: đọc file thật trong upload root, kiểm tra ownership hoặc quyền admin/bên hợp đồng có deliverable liên kết, trạng thái quét/khả dụng và đường dẫn. File không có nội dung trả 404.
8. Các endpoint được đăng ký vào ứng dụng gốc; giữ dependency onboarding riêng, không nới quyền router tuyển dụng cũ. Không trả chi tiết exception/SQL cho client.

## Kiểm thử

- Có regression test qua ứng dụng thật cho OTP, hồ sơ doanh nghiệp, MOU, eligibility và file.
- Có regression test đóng tuyển, hủy nháp, payment chưa đối soát và snapshot nghiệm thu.
- MariaDB chạy trong container test riêng, database tên ngẫu nhiên được tạo/xóa bởi fixture. Có hai kết nối đồng thời kiểm tra hủy nháp gặp kích hoạt hợp đồng và dữ liệu ORM cũ.
- Toàn bộ backend: **336 passed**, gồm **4 test MariaDB**, không skip. Ruff và `git diff --check` đều đạt. Có cảnh báo deprecation từ thư viện, không có test thất bại trong lượt chạy cuối.
- Lượt chạy toàn bộ đầu tiên gặp 4 lỗi kết nối do Docker Engine chưa mở. Sau khi khởi động Docker và container test, lượt chạy toàn bộ tiếp theo đạt kết quả trên. Container/network test đã được dọn.

## Các phần vẫn cần triển khai/cấu hình trước production

- Đây là bản sửa phần đã có của hai thành viên, không phải tuyên bố hoàn tất toàn bộ ticket nhóm A/C hoặc nền tảng freelancer.
- Email OTP yêu cầu SMTP và secret ngẫu nhiên tối thiểu 32 ký tự trong môi trường local/server. Không đặt secret thật vào `.env.example` hoặc Git.
- Chưa có adapter SMS: yêu cầu gửi PHONE trả `503 OTP_NOT_READY`. Không có mã giả để vượt xác minh điện thoại. Luồng đổi liên hệ chưa được mở qua endpoint này.
- Có cooldown/rate limit lưu DB theo user; cần cấu hình thêm rate limit theo IP ở gateway/kho chia sẻ trước khi mở OTP công khai.
- Chưa bổ sung bộ quét/upload/worker mới hoặc quy trình admin duyệt hồ sơ/MOU còn thiếu ở nhánh gốc. Endpoint dùng các file đã được lưu và quét bởi quy trình đáng tin cậy; không tự đặt CLEAN.
- MOU nộp lên chưa tự được kích hoạt hoặc xác thực chữ ký số; vẫn cần quy trình duyệt thủ công theo thiết kế đã chốt.
- payOS/finance vẫn trả FINANCE_NOT_READY khi chưa có adapter; không gửi tiền thật trong lượt sửa này.

## Mở để duyệt

Mở worktree riêng trong VS Code:

```powershell
code B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c
```

Xem các file sửa và file mới:

```powershell
git -C B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c status --short
git -C B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c diff
```

`git diff` chưa liệt kê nội dung file mới chưa track; mở thêm các đường dẫn `??` trong `git status`. Chưa checkout nhánh này trong thư mục gốc vì nhánh đang được mở ở worktree riêng và thư mục gốc có thay đổi chưa commit của chủ dự án.
