# Xác minh doanh nghiệp và quyền đại diện (0012)

Doanh nghiệp xác thực email, nộp giấy đăng ký doanh nghiệp, tên/chức vụ/điện thoại người đăng ký, tư cách đại diện và tệp bằng chứng. Cho phép Gmail; không tự tin cậy tên miền riêng hoặc website tự khai. Người đại diện cung cấp bằng chứng để đối chiếu danh tính; người được ủy quyền cung cấp giấy giới thiệu/ủy quyền xác định email và phạm vi tuyển dụng.

Admin xem giấy phép và bằng chứng, đối chiếu pháp nhân, xác minh quyền tuyển dụng qua nguồn độc lập. Duyệt bắt buộc hai xác nhận riêng, phương thức, nguồn đối chiếu và tham chiếu xác nhận (đầu mối/thời điểm/biên bản). Đây là hồ sơ chứng minh, không phải lý do phê duyệt. Từ chối/yêu cầu bổ sung bắt buộc lý do. Chỉ đối chiếu danh tính không đủ để duyệt người được ủy quyền. Hồ sơ cũ thiếu bằng chứng phải được yêu cầu bổ sung.

Phê duyệt không yêu cầu MOU. MOU vẫn là thỏa thuận hợp tác riêng. Không tự động thu hồi quyền các doanh nghiệp đã được duyệt trước migration; không tự tạo bằng chứng xác minh cho họ. Cần yêu cầu bổ sung/thẩm định lại các hồ sơ cũ khi cần. Đổi email qua luồng liên hệ sẽ yêu cầu nộp lại xác minh quyền đại diện.

UI doanh nghiệp trong workspace và phiên onboarding cùng dùng CompanyVerificationFlow. Phiên onboarding chỉ được xem/nộp hồ sơ của chính doanh nghiệp; không mở quyền tuyển dụng. Các API nộp/đọc/duyệt BusinessVerification cũ, schema, service và bảng giao diện tương ứng đã được gỡ. Dữ liệu lịch sử và migration tạo bảng vẫn được giữ. Migration 0013 chuyển hồ sơ cũ đang chờ sang cần bổ sung, mở lại khả năng nộp theo luồng mới mà không ảnh hưởng hồ sơ đã duyệt hoặc hồ sơ đang chạy ở luồng mới.

Lưu trong company_verifications.authority_data; tệp bằng chứng là stored_files category AUTHORIZATION và liên kết companies.authorization_file_id. Người sở hữu và admin được tải theo kiểm tra quyền hiện có. Khi nộp/duyệt lưu snapshot vào audit_logs để bảo toàn dấu vết qua lần nộp bổ sung. Gửi thông báo web/email khi nộp và có kết quả. Không gửi giấy tờ nhạy cảm trong email.

Migration 0012 đã được áp dụng. Khởi động lại backend và worker; frontend cần tải bản mới. Nguồn xác nhận vẫn phải do admin kiểm tra thực tế: checkbox không thay thế việc thẩm định, hệ thống không tự xác nhận hotline hoặc chứng thực tài liệu.
