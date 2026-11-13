# Giải ngân theo số dư ví chi — cập nhật 12/11/2026

Theo yêu cầu đơn giản hóa demo, quy trình tải chứng từ nguồn chi và hai admin duyệt được bỏ. Quyết định này thay thế phần tương ứng trong bản thiết kế cũ.

- Trước lần gửi lệnh chi đầu tiên, worker đọc số dư qua PayOS bằng gateway đang xác minh chữ ký. Chỉ số dư VND hợp lệ và lớn hơn hoặc bằng số tiền lệnh mới được gửi.
- Không còn chốt `TREASURY_EVIDENCE_REQUIRED`. Giữ xác minh ngân hàng người nhận, các khoản giữ/tranh chấp, hạn mức, idempotency và tra cứu kết quả khi chưa rõ giao dịch.
- Thiếu tiền: lệnh giữ trạng thái READY, chưa tạo lần gửi; worker kiểm tra lại sau 60 giây, không hết lượt thử vì chờ nạp tiền. Admin chỉ cần nạp vào ví chi qua kênh của nhà cung cấp.
- Khi kiểm tra lệnh, nếu ví thiếu tiền hoặc dưới `PAYOS_PAYOUT_LOW_BALANCE_THRESHOLD` (mặc định 100.000 VND), mọi admin ACTIVE nhận thông báo trên web. Tối đa một thông báo cho mỗi admin trong một giờ, dùng chung cho các lệnh để tránh spam. Bấm thông báo mở trang Giải ngân & hoàn tiền.
- Ngưỡng cảnh báo không chặn một lệnh đã đủ tiền. Đặt ngưỡng bằng 0 nếu chỉ muốn cảnh báo khi không đủ thực hiện lệnh. Việc kiểm tra hiện gắn với lệnh cần gửi, không quét ví định kỳ khi không có lệnh. Không gửi email hoặc push điện thoại trong thay đổi này.
- Lỗi API, chữ ký hoặc dữ liệu số dư không hợp lệ vẫn chặn gửi, theo cơ chế retry lỗi hiện có; không giả định số dư bằng 0 hoặc đã chuyển thành công.

## Giao diện và lịch sử

Đã bỏ menu, thẻ trang tổng quan, biểu mẫu tải chứng từ và thao tác duyệt nguồn chi. URL cũ `/admin/freelancer/admin/treasury` chuyển sang trang theo dõi giải ngân. API POST tạo/duyệt phiếu nguồn chi được gỡ; API GET giữ lại cho lịch sử cũ. Không xóa bảng, chứng từ hoặc bút toán đã lưu; không cần migration cho thay đổi này.

Sổ vẫn ghi nhận các khoản thu/chi mà hệ thống xác nhận và bảo toàn bút toán kép, nghĩa vụ ký quỹ, phí nền tảng. Không tự suy diễn khoản nạp từ chênh lệch số dư ví và không tạo bút toán nạp vốn giả. Vì nạp ví/phí ngoài hệ thống không được nhập nữa, số dư các tài khoản nguồn tiền trên sổ chỉ là tổng chuyển động đã ghi nhận, có thể âm và **không đại diện số dư thực tại ngân hàng/ví**. Mô hình demo này không phải sổ kế toán tiền mặt đầy đủ. Đối soát giao dịch/escrow vẫn hoạt động; đối chiếu toàn bộ nạp ví và phí cần dữ liệu nhà cung cấp riêng.

## Áp dụng

Khởi động lại backend và worker để nạp mã/cấu hình mới. Trong thư mục `backend`:

```powershell
python -m scripts.freelancer_worker
```

Giữ một tiến trình worker đang chạy. Lệnh RETRY cũ vẫn giữ lịch đã lưu; nếu muốn chạy lại ngay, dùng chức năng thử lại tác vụ tại Đối soát → Hàng đợi xử lý. Lệnh DEAD cũ cũng cần được đưa lại vào hàng đợi; không bấm tạo thêm lệnh giải ngân. Sau khi bật worker, lệnh đủ điều kiện có thể chuyển tiền thật.

Các kiểm thử dùng SQLite và PayOS giả lập; không chạy payout thật hoặc cập nhật dữ liệu tài chính đang dùng để kiểm thử thay đổi này.
