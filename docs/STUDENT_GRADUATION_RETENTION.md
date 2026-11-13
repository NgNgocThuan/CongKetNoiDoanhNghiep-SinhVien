# Tài khoản sau tốt nghiệp

## Thôi học

- WITHDRAWN bắt buộc có `withdrawn_at` (ngày thôi học), không ở tương lai.
  Có thể import cột `withdrawn_at` / `ngay thoi hoc` hoặc nhập ở form học thuật.
- Ngừng ứng tuyển, nhận lời mời và ký hợp đồng mới ngay khi xác nhận thôi học;
  loại khỏi gợi ý ứng viên. Giữ quyền tải dữ liệu và giải quyết nghĩa vụ tồn đọng.
- Worker gửi email thông báo riêng, không chúc mừng tốt nghiệp. Cho ít nhất
  30 ngày từ thông báo đầu tiên để lưu dữ liệu, nhắc khi còn 7 ngày.
- Dùng chung kiểm tra hợp đồng, khoản chi, tranh chấp và ràng buộc lịch sử
  trước khi dọn. Bảo lưu không kích hoạt thời hạn này.
- Hồ sơ WITHDRAWN cũ chưa có ngày thôi học không tự bị xóa; admin cần bổ sung
  ngày chính thức. Import lại cùng dữ liệu không gia hạn hoặc gửi trùng email.

- Import CSV/XLSX hoặc sửa dữ liệu học thuật: `academic_status` nhận STUDYING,
  GRADUATED, SUSPENDED, WITHDRAWN. GRADUATED bắt buộc có `graduated_at`, không ở tương lai.
- Ô trống khi import giữ nguyên dữ liệu. Không suy ra tốt nghiệp từ khóa học hay
  việc sinh viên vắng mặt trong file. Sinh viên đang học không bị dọn vì ít đăng nhập.
- Worker hiện có xử lý tối đa một batch mỗi lượt; từng sinh viên được kiểm tra
  một lần mỗi ngày. Cần chạy `python -m scripts.freelancer_worker` trong backend.
- Worker gửi thông báo và xếp email bền vững: chúc mừng tốt nghiệp, hạn dùng
  12 tháng theo lịch, nhắc khi còn 30 và 7 ngày. Import lại không gửi trùng hoặc
  kéo dài thời hạn. Import muộn được tối thiểu 30 ngày báo trước.
- Hết hạn chặn tham gia công việc mới. Nếu còn hợp đồng chưa đóng hoặc khoản
  chi chưa hoàn tất thì hoãn dọn, giữ khả năng giải quyết nghĩa vụ và báo admin.
- Không còn nghĩa vụ: xóa hồ sơ và tài khoản khi không có ràng buộc lịch sử;
  nếu có ràng buộc thì khóa đăng nhập, tắt tìm việc và báo admin giữ hồ sơ lịch sử.
  Không vô hiệu hóa foreign key, không xóa dây chuyền giao dịch tài chính.
- Lưu dấu băm mã sinh viên đã dọn để import file cũ không tạo lại tài khoản.
  Dấu này không chứa email, họ tên hay CV. Tái nhập học cần quy trình admin riêng.
- Việc dọn hiện xử lý dữ liệu database; tệp vật lý trên ổ đĩa không tự động xóa
  trong lượt này để tránh mất tệp đang được tham chiếu trong lịch sử.
- Cấu hình SMTP hợp lệ để nhận email thật. Thông báo được lưu cùng giao dịch;
  email được gửi qua hàng đợi và có cơ chế thử lại hiện có.

## CV

Hồ sơ đã có chứng chỉ tự khai. Trình tạo CV nay có ô Chứng chỉ riêng,
lấy sẵn chứng chỉ hồ sơ khi tạo mới; có thể ghi TOEIC/IELTS, điểm,
đơn vị cấp, ngày cấp và ngày hết hạn. CV đã lưu giữ nội dung phiên bản riêng.
