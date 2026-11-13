# Ngân hàng tự khai báo và khoản chi chờ bổ sung tài khoản

## Quy tắc sử dụng

- Tài khoản mới hợp lệ có trạng thái `ACTIVE`, dùng ngay, không có bước admin duyệt.
- `ACTIVE` không có nghĩa là đã xác minh chính chủ. Nguồn được ghi là `SELF_DECLARED`;
  không tự điền người duyệt hoặc thời điểm xác minh.
- Giữ hỗ trợ tài khoản `VERIFIED` lịch sử. Tài khoản `DISABLED` và `REJECTED`
  không được dùng để lập lệnh chi mới.
- Ngân hàng, số tài khoản, tên chủ tài khoản được kiểm tra ở backend. Số tài khoản
  được mã hóa; danh sách chỉ hiển thị bốn số cuối.
- Admin xem tên/email/vai trò người dùng và tài khoản tương ứng; có thể ngừng sử
  dụng tài khoản khi có vấn đề. Lượt xem số tài khoản đầy đủ vẫn được ghi audit.

## Thiếu ngân hàng khi giải ngân hoặc hoàn tiền

1. Vẫn lưu quyết toán, giữ khoản tiền tương ứng và tạo một `money_transfers`
   ở trạng thái `WAITING_BANK`. Chưa có tài khoản đích và chưa gửi yêu cầu PayOS.
2. Thông báo trên web cho đúng người nhận, dẫn tới **Ngân hàng nhận tiền**.
   Tạo lại quyết toán từ cùng nguồn không tạo thêm lệnh hoặc thông báo trùng.
3. Khi người nhận thêm tài khoản, trong cùng transaction: gán tài khoản và snapshot
   cho các lệnh `WAITING_BANK` của người đó, đổi sang `READY`, tạo outbox `finance.transfer`.
4. Worker nhận lại lệnh, giữ nguyên mã tham chiếu/idempotency key, kiểm tra số dư,
   hạn mức và các điều kiện chi trả hiện hành rồi gọi PayOS.
5. Chỉ khi PayOS xác nhận thành công mới ghi nhận đã giải ngân, doanh thu phí và
   hoàn thành nghĩa vụ tài chính. Một quyết toán chia hai bên có thể hoàn tất
   một nhánh trước, giữ nhánh còn lại chờ ngân hàng.

Thêm tài khoản khác không thay đổi đích của lệnh đã gán ngân hàng hoặc đã gửi.
Khoản chi chưa gửi vẫn kiểm tra tài khoản có bị ngừng sử dụng hay không.

Worker phải chạy để xử lý outbox. Nếu thêm tài khoản khi worker đang tắt,
lệnh vẫn được lưu và xử lý khi worker chạy lại; không cần bấm giải ngân lần nữa.

## Triển khai

```powershell
cd B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c\backend
python -m alembic upgrade head
python -m scripts.freelancer_worker
```

Migration `0010` cho phép trạng thái mới và chuyển ngân hàng `PENDING` cũ sang
`ACTIVE` theo cơ chế tự khai báo. Không đổi lệnh chi đã gửi, không tự gọi PayOS.
Không downgrade khi vẫn còn lệnh `WAITING_BANK` chưa được xử lý.
