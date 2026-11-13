# Kỹ năng có một nguồn quản lý chính

Matching sử dụng kỹ năng trong `student_skills`, không tự cộng kỹ năng AI đọc
được từ CV. Kỹ năng tự khai do sinh viên lưu và kỹ năng đã được nhà trường ghi
nhận tiếp tục có hiệu lực. Phiên bản thuật toán mới làm cache matching cũ được
tính lại khi người dùng tải gợi ý.

## Luồng từ CV đến hồ sơ

1. Sinh viên tải CV PDF/DOCX lên hoặc chọn CV online trong **CV của tôi**.
2. Chọn **Phân tích CV**. Kết quả chỉ là gợi ý, chưa thay đổi hồ sơ/matching.
3. Tích những kỹ năng thực sự có và bấm **Xác nhận & thêm vào hồ sơ**.
4. Backend kiểm tra quyền sở hữu CV và đối chiếu với kết quả phân tích hiện tại.
   Chỉ các kỹ năng được chọn mới được thêm; giữ nguyên kỹ năng, nguồn và trình độ
   đã có, không tự xóa kỹ năng khác.
5. Matching đối chiếu lại danh sách kỹ năng trong hồ sơ. Kinh nghiệm và độ liên
   quan nội dung vẫn dùng dữ liệu phân tích CV theo thuật toán hiện tại.

Không có migration hoặc tự động xác nhận hàng loạt dữ liệu trích xuất cũ.
Không cần AI khi sinh viên chưa có kỹ năng nào trong hồ sơ để đối chiếu.

## CV online và CV đã nộp

CV online lấy kỹ năng từ hồ sơ. Trình sửa CV không có ô nhập kỹ năng độc lập;
có đường dẫn đến quản lý kỹ năng. Thêm/xóa kỹ năng trong hồ sơ đồng bộ các CV
online đang hoạt động; danh sách CV, bản xem và tệp tải xuống cũng dùng nguồn này.
Tệp PDF/DOCX gốc được giữ nguyên; thay đổi kỹ năng hồ sơ không sửa tệp tải lên.
Các bản chụp CV đã nộp trong đơn ứng tuyển không bị thay đổi.

## Xem CV

Nhà tuyển dụng mở hồ sơ/CV bằng hộp thoại có hai tab **Hồ sơ nghề nghiệp** và
**CV giới thiệu**. CV online được trình bày như tài liệu hai cột, dùng chung
component với phần xem trước CV của sinh viên. PDF có vùng đọc riêng và nút tải;
Word được tải nguyên bản để mở bằng ứng dụng đọc tài liệu. Quyền xem tiếp tục
phụ thuộc trạng thái tìm việc, doanh nghiệp đã xác minh và tin tuyển dụng thuộc
doanh nghiệp đang xem.
