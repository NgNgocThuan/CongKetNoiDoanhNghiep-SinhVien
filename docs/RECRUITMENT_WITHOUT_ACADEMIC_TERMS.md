# Tuyển dụng không phụ thuộc kỳ thực tập

Matching, tìm tin và ứng tuyển dùng một luồng tuyển dụng chung. Công việc
thực tập vẫn là một **loại hình công việc** hợp lệ; không cần đăng ký kỳ,
thuộc danh sách sinh viên của trường hoặc phân công giảng viên.

- Matching chỉ xét ngành học phù hợp, GPA nếu nhà tuyển dụng yêu cầu, trạng thái
  và hạn tin, sau đó đối chiếu kỹ năng/kinh nghiệm/nội dung. Không còn điều kiện
  `NOT_IN_TERM`. Phiên bản thuật toán mới làm các kết quả đã lưu được tính lại
  khi người dùng mở gợi ý.
- Tin cũ có metadata kỳ vẫn được tìm thấy, xem chi tiết, gợi ý và ứng tuyển
  theo cùng điều kiện với tin khác. Không cần chỉnh sửa dữ liệu thủ công.
- Schema tạo/sửa tin, bộ lọc API, thẻ việc và giao diện tìm việc không còn
  trường kỳ hay lựa chọn tuyển tự do/theo kỳ.
- Báo cáo admin không lọc/phân nhóm theo kỳ, không so sánh hai luồng và không
  xuất mã kỳ trong Excel.
- Gỡ trang đánh giá thực tập theo mã kết quả của doanh nghiệp. Thông báo lịch sử
  về kỳ quay về trang thông báo, không dẫn tới trang đã ngừng sử dụng.

Các bảng dữ liệu học thuật và các module cũ không được đăng ký vào ứng dụng
được giữ để bảo toàn lịch sử. Chúng không tham gia quyết định quyền truy cập,
gợi ý hoặc ứng tuyển hiện tại. Không xóa dữ liệu cũ và không cần migration.
