# Đối chiếu kiến trúc và giao diện — 11/11/2026

## Phạm vi và kết luận

Worktree: `tmp/fix-freelancer-a-c`, nhánh `fix/freelancer-backend-a-d-local-20261107`. Đối chiếu `SYSTEM_ARCHITECTURE_REVIEW.md`, đặc biệt các mục 2, 5–10, 13–15, 19 và 21, với mã đang có trong worktree. Giữ các thay đổi chưa commit có sẵn. Không chuyển nhánh, commit, push, chạy migration trên DB đang dùng hay thực hiện thu/chi thật.

**Mã ban đầu chưa khớp thiết kế.** Có lỗi hợp đồng API khiến xác minh và MOU không dùng được, đường xác minh chữ ký có thể chấp nhận giả, quyền tuyển dụng chưa thống nhất, lịch phỏng vấn bị bỏ qua và retry tài chính tạo khóa mới sau timeout. Các điểm dưới đây đã được sửa và kiểm thử. Kết quả này không phải chứng nhận toàn bộ hệ thống sẵn sàng production.

## Những điểm đã sửa

| Nhóm | Sai lệch tìm thấy | Kết quả sửa |
| --- | --- | --- |
| OTP doanh nghiệp | Hai cơ chế OTP riêng; giao diện gửi `code` thay vì `otp_code`, đọc sai tên trạng thái; cơ chế mới lưu nội dung email chứa OTP | Endpoint tương thích dùng dịch vụ OTP chung; giao diện dùng `ContactVerification`; trạng thái dựa trên `User.email_verified_at`. OTP 6 số, 15 phút, giới hạn gửi/thử và xác minh đúng email hiện tại. Không ghi OTP vào email log/outbox |
| Nộp pháp nhân | Gửi `business_license_file` trong khi API nhận `license_file`; biểu mẫu cho nộp lại khi đang chờ; chưa kiểm tra tệp sạch trước duyệt | Đồng bộ DTO/multipart, điền sẵn dữ liệu, giới hạn 10 MB, chặn nộp lặp, kiểm tra MST đăng ký, trạng thái email, tệp CLEAN/AVAILABLE; kiểm tra quyết định/lý do, khóa bản ghi và ghi audit |
| Quyền dùng chung | Luồng tuyển dụng chỉ đọc trạng thái duyệt cũ, Freelancer cho công ty chưa xác minh email gửi dự án | Điều kiện pháp nhân + email hiện tại + không đình chỉ; tuyển dụng dùng điều kiện pháp nhân chung, giữ lịch sử duyệt cũ; Freelancer yêu cầu cả hai bước |
| MOU Hybrid | Fallback chấp nhận chữ ký khi thiếu pyHanko; không thực sự validate; PDF chỉ vẽ dấu “SIGNATURE VALID” | Loại fallback và dấu giả. Ký PDF thật bằng PKCS#12; yêu cầu hai bên ký khác nhau, đúng chứng thư trường, tin cậy CA, tính toàn vẹn, DocMDP, MST chính xác và metadata gắn đúng công ty. Đọc bằng chứng CRL/OCSP trong DSS, không tự tải từ mạng. Thiếu cấu hình trả 503 |
| MOU vòng đời | API mới bỏ qua điều kiện pháp nhân, ghi cứng hạn mức khác policy; chưa tạo job hết hạn; UI gửi sai tên tệp/người ký và đọc sai `is_partner` | Kiểm tra doanh nghiệp đủ điều kiện, sửa `mou_file`/`signer_name`/`signed_pdf`, đọc `is_mou_partner`; không cấp quyền bằng hạn mức ghi cứng; dùng policy hiện có. Duyệt giấy bắt buộc tệp đã quét; Hybrid cũng cần quét sạch. Nhắc 30/14/7/1 ngày và hết hạn qua worker chung; chống duyệt lặp, audit |
| Tuyển dụng | API `/job-board` cho đọc chi tiết tin nháp; CV chỉ tham chiếu tệp hiện tại; chuyển trạng thái bỏ qua quy tắc chung | Chỉ công khai tin đã duyệt; tạo tin kiểm tra pháp nhân, deadline, lương, danh mục. Ứng tuyển dùng dịch vụ chụp CV snapshot sẵn có. Dùng chung dịch vụ chuyển trạng thái và thông báo |
| MOU trên tin tuyển dụng | API chính chưa auto-approve MOU khi gửi duyệt và chưa trả trường để hiển thị huy hiệu | Gửi tin của đối tác có MOU hiệu lực được duyệt tự động. Trả `is_featured` và `is_mou_partner` theo hiệu lực hiện tại; thẻ việc làm không gắn huy hiệu MOU chỉ dựa vào cờ ưu tiên lưu cũ |
| Phỏng vấn và liên hệ | Frontend PATCH sang route không có rồi thử PUT; backend bỏ qua thời gian và địa điểm; biểu mẫu chỉ nhập ngày | Hỗ trợ PATCH/PUT qua một service; bỏ retry bằng phương thức khác; nhập ngày giờ, kiểm tra lịch tương lai, lưu và hiển thị lịch, thông báo ứng viên. Chỉ mở liên hệ khi đã mời phỏng vấn và sinh viên cho chia sẻ |
| Luồng học thuật | Còn menu/router giảng viên, đợt thực tập và gắn tin mới với đợt | Gỡ các menu/router đang hoạt động tương ứng và endpoint sinh viên xem phân công; không cho tin mới gắn đợt học thuật. Giữ bảng và helper dữ liệu lịch sử, không xóa dữ liệu |
| Tệp riêng tư | Download có quyền và kiểm tra scanner nhưng chưa so lại hash nội dung | Kiểm tra kích thước và SHA-256 trước trả tệp; giao diện preview dùng blob qua API có quyền, không công khai đường dẫn lưu trữ |
| Retry tài chính | `command()` xóa khóa idempotency sau mọi lỗi, kể cả timeout | Giữ khóa khi kết quả chưa biết hoặc server lỗi; lỗi 4xx xác định được có thể thử lại. Giữ chống bấm gửi đồng thời |
| Modal và lỗi | Cần xử lý 409 nhưng không được đổi điều kiện cấp vốn hoặc tạo lệnh tiền mới để “hết kẹt” | Giữ lỗi tại form/toast và cho thử lại; có fallback thông báo lỗi Query/Mutation; đọc được lỗi JSON của API download blob |
| Migration | Downgrade SQLite còn CHECK constraint tham chiếu cột bị xóa | Gỡ đúng các constraint phản chiếu trước xóa cột; kiểm thử downgrade/re-upgrade đã đạt trên SQLite |

`allocate_in_tx` đã ghi milestone thành `FUNDED` sau khoản thu hợp lệ. `start_milestone_in_tx` đã kiểm tra đủ vốn của các mốc thuộc hợp đồng FULL. Giữ các điều kiện này; không đánh dấu đã cấp vốn khi chưa có bằng chứng thu. Bộ test tài chính/contract/milestone hiện có đã được chạy lại.

## Giao diện

- Xác minh doanh nghiệp có hai bước rõ ràng, trạng thái email được lưu qua tải lại, biểu mẫu có nhãn và khóa thực sự bằng `fieldset`, trạng thái chờ duyệt riêng.
- Dùng màu xanh của giao diện hiện có, nút chính/phụ thống nhất, bố cục một cột trên điện thoại và hai cột khi đủ chỗ. Đã sửa xung đột tên CSS khiến bước xác minh bị co thành thanh nhỏ.
- MOU có hai lựa chọn ký giấy/ký số, hướng dẫn theo bước, tệp đính kèm và xem trước PDF/ảnh. Không cho chọn ký số khi backend chưa cấu hình chứng thư.
- Admin có hàng đợi riêng cho hồ sơ mới và MOU, xem tài liệu qua API riêng tư, link tra cứu, xác nhận đã đối chiếu và lý do từ chối/bổ sung. Lịch sử/hàng đợi cũ được giữ để không mất khả năng xử lý hồ sơ đã có.
- Khi lỗi 409, không xóa nội dung biểu mẫu; nút hết trạng thái chờ, người dùng có thể thử lại. Ngăn gửi lại sau thành công.

Ảnh kiểm thử với dữ liệu fixture: [desktop](architecture-ui-previews/company-verification-desktop.png), [mobile 390px](architecture-ui-previews/company-verification-mobile.png). Ảnh thể hiện cả thông báo lỗi có thể khôi phục. Nội dung PDF fixture không phải văn bản thật.

## Kiểm chứng

| Kiểm tra | Kết quả |
| --- | --- |
| Backend: `test_architecture_review`, `tests/freelancer`, `test_company_applications`, `test_jobs` | **252 passed, 11 skipped** |
| Kiểm tra lại riêng các API/chữ ký sau dọn cơ chế OTP cũ | **9 passed** |
| Unit test frontend | **69 passed / 16 files** |
| TypeScript + production build | **Đạt** |
| Playwright Freelancer, gồm 2 kịch bản mới xác minh/MOU | **22 passed** |
| Playwright chạy lại riêng 2 màn hình sau sửa CSS | **2 passed** |

Kiểm thử backend dùng SQLite cô lập. Test chữ ký sinh chứng thư thử và ký PDF thật, có cả ca thành công, thiếu chữ ký, sai công ty/MST và sửa tài liệu. Playwright dùng API fixture; không khẳng định đó là kiểm thử toàn luồng với SMTP, scanner hoặc payOS thật. 11 test MariaDB/provider tùy cấu hình đã được skip. Ruff không được cài trong Python hiện tại; không ghi nhận đã đạt lint Python.

## Cách hiểu những điểm mâu thuẫn trong tài liệu

- Mục 2/6/8/19 là định hướng mới về email-only và Job Board. Các đoạn cũ nhắc SMS/eKYC/giảng viên không được dùng để thêm lại những luồng này.
- Mục 21 mô tả cột OTP thô; triển khai dùng HMAC của cơ chế chung để đáp ứng yêu cầu không lưu/log OTP thô ở mục 15.
- Mục 21.4 yêu cầu mock local, nhưng mục 2 yêu cầu mock chỉ trong test. Giữ mô phỏng trong test/fixture, không thêm endpoint có thể tạo tiền giả trong database nghiệp vụ chỉ vì `PAYOS_COLLECTION_ENABLED=false`.
- Hạn mức mục 7 và khoảng đề xuất mục 19 không thống nhất. Giữ policy hiện có, loại bỏ số ghi cứng 50 triệu trong router MOU; chưa tự chốt hạn mức mới.
- Xác thực chữ ký offline phải có trust roots và bằng chứng hiệu lực chứng thư; sự hiện diện của hai chữ ký hoặc dòng chữ “đã ký” không đủ. Không cam kết tự động duyệt trong 1 giây khi còn cần quét tệp và kiểm tra mật mã.

## Điều kiện còn phải nghiệm thu ở môi trường triển khai

1. Database đang chạy phải có schema hiện hành đến **0006**. Đợt này chỉ chạy migration trên database thử, chưa chạy trên database của người dùng. Cần nghiệm thu migration/concurrency MariaDB riêng.
2. SMTP và `FREELANCER_OTP_SECRET` phải được cấu hình; scanner phải hoạt động. Không mặc định tài liệu CLEAN để vượt bước.
3. Hybrid cần `MOU_SCHOOL_PFX_PATH`, `MOU_SCHOOL_PFX_PASSWORD`, `MOU_TRUST_ROOT_PATH` (đã thêm tên biến vào `.env.example`). Private key chỉ ở backend. Cần chứng thư trường/CA thật, tài liệu đã ký có bằng chứng hiệu lực phù hợp và mẫu thỏa thuận chính thức của trường. Mẫu PDF sinh hiện tại cần trường nghiệm thu nội dung trước phát hành.
4. Cần thử thu/chi payOS và đối soát bằng tài khoản đã được cấp quyền; các test đạt không xác nhận vận hành tiền thật. Worker phải được chạy riêng để xử lý quét, nhắc hạn và tài chính.
5. MFA/phân quyền nhân sự admin chi tiết, backup/monitoring và nghiệm thu production vẫn là các hạng mục triển khai được tài liệu kiến trúc nêu; không được suy ra là hoàn tất từ đợt sửa mã nguồn/giao diện này.
