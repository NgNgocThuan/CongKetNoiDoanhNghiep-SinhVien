# PROMPT THIẾT KẾ GIAO DIỆN STUDENT CONNECT

Bạn là UI/UX designer thiết kế một ứng dụng web tiếng Việt mang tên Student Connect:
cổng kết nối Sinh viên – Doanh nghiệp – Nhà trường.

Mục tiêu: tạo bản thiết kế giao diện và prototype để nhóm duyệt trước khi viết frontend.
Thiết kế phải bám backend hiện có, không tự thêm chức năng để làm giao diện phong phú hơn.
Đây là sản phẩm quản lý và tuyển dụng sử dụng hằng ngày, cần rõ ràng, dễ đọc, nhất quán.
Không biến toàn bộ sản phẩm thành landing page quảng cáo.

## 1. Phạm vi, người dùng và dữ liệu

Backend có ba vai trò:
- STUDENT: sinh viên được nhà trường cấp tài khoản.
- COMPANY: doanh nghiệp đăng ký tài khoản và chờ nhà trường duyệt.
- ADMIN: cán bộ/quản trị nhà trường.

Cùng một trang đăng nhập email + mật khẩu. Sau đăng nhập, chuyển giao diện theo role
backend trả về; không cho người dùng tự chọn role để vượt quyền. Trong prototype có
thể tạo ba điểm bắt đầu riêng để nhóm review, nhưng không trình bày chúng thành tính
năng đổi vai trò của tài khoản thật.

Sinh viên không tự đăng ký. Admin không có trang đăng ký công khai. Doanh nghiệp có
trang đăng ký. Không có tài khoản giảng viên đăng nhập riêng trong phiên bản này.

Ngôn ngữ giao diện: tiếng Việt tự nhiên, đầy đủ dấu. Dữ liệu ví dụ là dữ liệu giả,
nhất quán giữa các màn hình: cùng tên công ty, mã sinh viên, tin tuyển dụng, trạng thái.
Điểm GPA dùng thang 4, điểm đánh giá thực tập dùng thang 10, điểm phù hợp dùng thang 100.
Tất cả số liệu trong prototype chỉ là ví dụ, không mô tả là số liệu đang lấy từ hệ thống.

## 2. Định hướng thị giác

- Phong cách chuyên nghiệp, thân thiện với sinh viên, gọn gàng, ưu tiên nội dung.
- Nền chính #F8FAFC; thẻ trắng; chữ chính #0F172A; chữ phụ #64748B.
- Màu thương hiệu #2563EB; hover #1D4ED8; điểm nhấn xanh ngọc #0F766E.
- Thành công xanh lá, chờ xử lý hổ phách, lỗi/từ chối đỏ; luôn có nhãn chữ hoặc icon
  để người dùng không phải phân biệt trạng thái chỉ bằng màu.
- Font hỗ trợ tiếng Việt như Inter hoặc Be Vietnam Pro; cỡ nội dung khoảng 14–16px.
- Lưới khoảng cách 8px; góc bo 10–12px; đổ bóng nhẹ; đường phân cách rõ.
- Desktop khung 1440px, mobile khung 390px. Form tối đa chiều rộng vừa đọc;
  bảng dữ liệu có thanh cuộn ngang hoặc dạng thẻ trên mobile.
- Không dùng gradient lòe loẹt, hình minh họa lớn lấn nội dung hay emoji làm icon chính.
- Thiết kế focus, hover, disabled, loading; tương phản và nhãn form dễ tiếp cận.

Tạo hệ thống thành phần dùng lại: nút, trường nhập, select/autocomplete, checkbox,
switch, badge trạng thái, thẻ việc làm, thẻ điểm phù hợp, bảng phân trang, tabs,
modal xác nhận, drawer chi tiết, vùng upload, thông báo lỗi, toast và trạng thái rỗng.

## 3. Bố cục và điều hướng

Mọi khu vực đăng nhập có tên sản phẩm, tên/vai trò người dùng, chuông thông báo và menu
tài khoản gồm Đổi mật khẩu, Đăng xuất. Sidebar thể hiện mục đang chọn; desktop có thể
thu gọn, mobile chuyển thành drawer. Sidebar theo role, không hiện mục không có quyền.

Sinh viên: Tìm việc, Gợi ý phù hợp, Việc đã lưu, Hồ sơ của tôi, CV của tôi,
Đơn ứng tuyển, Lời mời, Thực tập của tôi.

Doanh nghiệp: Tin tuyển dụng, Quản lý ứng viên, Gợi ý ứng viên, Lời mời đã gửi,
Hồ sơ doanh nghiệp. Màn hình đầu là danh sách tin của doanh nghiệp, không tạo
business dashboard tổng hợp vì backend chỉ có thống kê theo từng tin.

Admin: Tổng quan, Sinh viên, Giảng viên, Doanh nghiệp, Kiểm duyệt tin,
Đợt thực tập, Danh mục, Tài khoản, Báo cáo vi phạm, Nhật ký email.
Xuất báo cáo đặt trong khu vực thống kê hoặc thanh thao tác của danh sách phù hợp.

Thông báo là drawer chung và trang danh sách dùng cùng component.
Không tạo một dashboard số liệu riêng cho sinh viên nếu dữ liệu không có API.

## 4. Các màn hình xác thực và dùng chung

A01. Đăng nhập: email, mật khẩu, hiện/ẩn mật khẩu, Quên mật khẩu, liên kết Đăng ký
 doanh nghiệp. Có lỗi sai thông tin, tài khoản bị khóa, chưa kích hoạt, chờ duyệt
 và giới hạn số lần thử. Không có nút Đăng nhập Google/LMS/SSO.

A02. Đăng ký doanh nghiệp: email, mật khẩu, tên công ty, mã số thuế bắt buộc;
 lĩnh vực, địa chỉ, website, tên và điện thoại liên hệ tùy chọn. Sau gửi hiển thị
 trạng thái Chờ nhà trường phê duyệt, không chuyển ngay sang giao diện đã được duyệt.
 Chưa có đăng nhập cho tài khoản PENDING_APPROVAL.

A03. Quên mật khẩu: email; sau gửi luôn hiển thị thông báo trung lập
 “Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi”, không lộ tài khoản.

A04. Đặt lại mật khẩu từ link email có token: mật khẩu mới, xác nhận mật khẩu ở UI;
 biến thể token hết hạn, đã sử dụng, không hợp lệ, thành công.

A05. Kích hoạt sinh viên từ link email có token: đặt mật khẩu mới và xác nhận;
 trạng thái thành công/hết hạn/đã kích hoạt. Không cho tự nhập lại dữ liệu học thuật.

A06. Đổi mật khẩu: mật khẩu hiện tại, mật khẩu mới, xác nhận; yêu cầu tối thiểu
 theo schema API (hiện tại 8 ký tự), không tự gán yêu cầu OTP chưa được backend hỗ trợ.

A07. Thông báo: số chưa đọc, danh sách phân trang, đánh dấu một thông báo đã đọc,
 đánh dấu tất cả đã đọc. Nội dung có thể dẫn tới tin, đơn, lời mời hoặc đợt khi có
 ref_type/ref_id phù hợp và người dùng có quyền. Không thiết kế chat hoặc gắn nhãn realtime.

A08. Modal báo cáo vi phạm: chọn/nhận đối tượng JOB, COMPANY hoặc STUDENT và nhập lý do.
 Người dùng có thể gửi báo cáo, nhưng chưa có API lịch sử báo cáo riêng của người gửi.
 Không tạo trang “Báo cáo của tôi” có dữ liệu không được backend cung cấp.

API: /auth/login, /auth/register-company, /auth/forgot-password, /auth/reset-password,
/auth/activate, /auth/change-password, /auth/logout, /auth/me, /auth/refresh;
/notifications, /notifications/unread-count, /notifications/{id}/read,
/notifications/read-all; POST /reports.

## 5. Khu vực sinh viên

S01. Tìm việc
- Thanh tìm kiếm; bộ lọc từ API: vị trí, địa điểm, ngành học, lĩnh vực tuyển dụng,
  loại hình công việc, ONSITE/REMOTE/HYBRID, kỹ năng, khoảng lương và luồng tự do/theo đợt.
- Thẻ tin: tên vị trí, công ty, địa điểm, loại hình, mức lương/thỏa thuận, hạn nộp;
  đánh dấu đã lưu. Danh sách có phân trang và trạng thái không tìm thấy kết quả.
- Chỉ hiển thị tin APPROVED còn hạn; tin theo đợt chỉ dành cho sinh viên thuộc đợt.
  Không tạo bộ lọc điều kiện mà API tìm kiếm không hỗ trợ, như GPA tối thiểu.
- Không hiển thị điểm AI trên mọi thẻ tìm kiếm nếu chưa lấy kết quả matching.

S02. Chi tiết tin
- Nội dung mô tả, yêu cầu, quyền lợi; vị trí, số lượng, mức lương, địa điểm,
  hình thức làm việc, ngành học yêu cầu, kỹ năng bắt buộc/ưu tiên, hạn nộp và đợt.
- Khối công ty dẫn sang hồ sơ công khai của công ty đã duyệt.
- CTA Ứng tuyển, Lưu tin, Báo cáo tin; có trạng thái hết hạn/không còn nhận đơn.
- Panel “Mức độ phù hợp” lấy API score riêng, hiển thị tổng điểm, thành phần điểm,
  kỹ năng đáp ứng/còn thiếu, giải thích. Không có kết quả thì hiện trạng thái chưa có.

S03. Gợi ý việc làm phù hợp
- Danh sách xếp theo score backend trả về; hiển thị matched_skills, missing_skills,
  explanation. Nhắc ngắn “Điểm phù hợp mang tính tham khảo”.
- Có loading, chưa có kết quả, lỗi phân tích AI và gợi ý hoàn thiện hồ sơ/CV.
- Không tự tăng điểm hoặc kết luận đậu/trượt; AI không tự quyết định tuyển dụng.

S04. Hồ sơ của tôi
- Tabs hoặc các phần rõ ràng: Dữ liệu nhà trường, Thông tin tự khai, Quyền riêng tư.
- Dữ liệu nhà trường chỉ đọc: mã sinh viên, họ tên, ngày sinh, lớp, khoa, ngành,
  khóa, GPA, xếp loại, thành tích và chứng chỉ nguồn SCHOOL. Hiển thị badge nguồn.
- Thông tin tự khai: giới thiệu, mục tiêu nghề nghiệp, email/điện thoại liên hệ,
  địa chỉ, LinkedIn/GitHub; URL ảnh đại diện. Không tạo upload avatar vì API chỉ nhận URL.
- CRUD kỹ năng tự khai với mức độ; kinh nghiệm (công ty, vị trí, thời gian, mô tả),
  dự án (tên, vai trò, mô tả, công nghệ, URL, thời gian), chứng chỉ tự khai.
- Chứng chỉ có nhãn tự khai/chờ xác thực/đã xác thực. Sửa chứng chỉ tự khai đã
  xác thực thì cần xác thực lại. Không sửa/xóa chứng chỉ SCHOOL hoặc thành tích trường.
- Switch is_open_to_work, show_gpa, show_contact, show_achievements. Nêu rõ ảnh hưởng
  đến gợi ý ứng viên và dữ liệu doanh nghiệp được phép thấy; không tự bịa quyền khác.

S05. CV của tôi
- Danh sách nhiều CV; tiêu đề, loại ONLINE/UPLOADED, mặc định, thời điểm cập nhật,
  trạng thái phân tích. Upload PDF/DOCX hoặc tạo CV online.
- CV online gồm nội dung tự khai có cấu trúc và phần học thuật do backend tự điền,
  không cho chỉnh dữ liệu trường. Dùng một form nội dung nhất quán cho content_json.
- Đổi tiêu đề; chỉnh nội dung CV online; đặt mặc định; tải CV; xóa mềm có xác nhận.
  Chỉ một CV mặc định. CV upload không có trình sửa nội dung trực tiếp.
- Nút Phân tích AI, kết quả kỹ năng, kinh nghiệm, dự án/lĩnh vực khi API có dữ liệu.
- CV online hiện tải dữ liệu JSON; không hứa tải PDF/template thiết kế CV nếu chưa có API.
  Có thể thiết kế bản xem trước từ JSON để đọc, nhưng không trình bày như file PDF đã tạo.

S06. Ứng tuyển
- Modal chọn một CV của chính sinh viên, mặc định chọn CV mặc định; thư giới thiệu
  tùy chọn, tên tin/công ty và xác nhận nộp. Nếu đến từ lời mời, giữ invitation_id.
- Báo lỗi đã nộp, CV không hợp lệ, không thuộc đợt, tin hết hạn/không nhận hồ sơ.
- Thành công dẫn tới chi tiết đơn, không hiển thị trạng thái trúng tuyển ngay.

S07. Đơn ứng tuyển
- Danh sách theo trạng thái; tin, công ty, ngày nộp, trạng thái hiện tại.
- Chi tiết: tin, CV đã chọn, thư giới thiệu, dòng thời gian trạng thái và ghi chú.
- Rút đơn có xác nhận; chỉ cho phép khi backend cho phép. Không cho rút khi đã
  OFFER/HIRED/REJECTED/WITHDRAWN. Không có nút tự sửa CV snapshot của đơn đã nộp.

S08. Lời mời ứng tuyển
- Tin, công ty, thời gian, lời nhắn và trạng thái. API danh sách hiện chủ yếu trả ID;
  tên/chi tiết chỉ hiện khi các API chi tiết theo quyền đã tải được, có fallback rõ ràng.
- “Ứng tuyển theo lời mời” mở modal chọn CV rồi POST /applications kèm invitation_id.
  Không có endpoint chấp nhận lời mời riêng. “Từ chối” gọi API decline.

S09. Thực tập của tôi
- Xem đợt được phân công: tên, năm học, học kỳ, thời gian, trạng thái, giảng viên hướng
  dẫn và thông tin liên hệ khi API trả về; xem tin thuộc đợt có quyền truy cập.
- Không tạo bảng điểm/kết quả PASSED/FAILED cho sinh viên vì API hiện chỉ trả đợt
  và giảng viên, chưa có endpoint đọc kết quả riêng cho sinh viên.

S10. Việc đã lưu và hồ sơ công ty
- Danh sách việc đã lưu có bỏ lưu và mở chi tiết; thông báo tin không còn khả dụng.
- Hồ sơ công ty công khai chỉ các trường API public trả về: giới thiệu, lĩnh vực,
  quy mô, địa chỉ, website, công nghệ, quyền lợi/logo khi có. Không lộ giấy tờ xác thực.

API chính: /jobs, /jobs/{id}, /companies/{id}, /matching/jobs/recommended,
/matching/jobs/{id}/score, /students/me và các đường con skills/experiences/projects/
certificates/achievements/internship, /cvs/*, /saved-jobs/*, /applications/*,
/invitations/me, /invitations/{id}/decline, /internship-terms và /{id}/jobs.

## 6. Khu vực doanh nghiệp

C01. Hồ sơ doanh nghiệp
- Tên công ty và mã số thuế chỉ đọc sau đăng ký. Sửa lĩnh vực, quy mô, địa chỉ,
  website, URL logo, giới thiệu, công nghệ, quyền lợi và liên hệ.
- Vùng giấy tờ: upload PDF/JPG/JPEG/PNG, loại giấy tờ, tên/định danh và thời gian;
  xóa giấy tờ có xác nhận. Không tự thêm API sửa giấy tờ hoặc tải logo từ máy.
- Hiển thị trạng thái xác thực và lý do từ chối khi có.
- Tài khoản chưa duyệt chưa đăng nhập được; trạng thái này ở trang đăng ký/đăng nhập,
  không thiết kế dashboard hoạt động đầy đủ cho tài khoản chưa được phép vào.

C02. Quản lý tin tuyển dụng
- Bảng/thẻ: tin, trạng thái, thời gian tạo/hạn nộp, lượt xem, số đơn; lọc trạng thái.
- Form tạo/sửa gồm đúng các nhóm: tiêu đề, vị trí, loại hình, lĩnh vực, đợt tùy chọn,
  mô tả, yêu cầu, quyền lợi, số lượng, khoảng lương/thỏa thuận, địa điểm,
  ONSITE/REMOTE/HYBRID, GPA tối thiểu, kinh nghiệm tối thiểu, hạn nộp,
  kỹ năng bắt buộc/ưu tiên và ngành học.
- Tạo là DRAFT; lưu và gửi duyệt là hai thao tác. Không có nút tự phê duyệt.
- Chỉ tin DRAFT/REJECTED được gửi duyệt; sửa tin APPROVED sẽ trở về PENDING_APPROVAL.
  CLOSED/EXPIRED không chỉnh sửa. Đóng tin có xác nhận.
- Dùng preview nội dung tin trên form, không giả định cần API preview riêng.

C03. Thống kê từng tin
- Tổng lượt xem, lượt xem theo ngày và số đơn theo trạng thái; chọn số ngày trong
  giới hạn API. Không tạo biểu đồ doanh thu, thanh toán hoặc dashboard toàn công ty.

C04. Quản lý ứng viên theo tin
- Bắt buộc chọn job_id trước khi hiển thị bảng hoặc Kanban. Bộ lọc: trạng thái,
  ngành, GPA khi được chia sẻ, kỹ năng và số tháng kinh nghiệm tối thiểu.
- Bảng phân trang; tên sinh viên, ngành khi ánh xạ được, thời gian nộp, kinh nghiệm,
  kỹ năng và trạng thái. GPA/liên hệ bị ẩn hiển thị “Không chia sẻ”, không hiện 0.
- Kanban dùng dữ liệu API theo từng trạng thái và phân trang/tải thêm từng cột;
  không coi một trang API là toàn bộ ứng viên hay tự tạo endpoint Kanban board.
- Kéo thả chỉ tới trạng thái hợp lệ, mở modal ghi chú rồi xác nhận cập nhật.
  Có cách đổi trạng thái bằng nút/menu cho mobile và người dùng bàn phím.
- Drawer chi tiết: thông tin ứng viên được phép thấy, thư giới thiệu, kỹ năng,
  kinh nghiệm, lịch sử trạng thái; nút tải đúng CV đã nộp từ cv_download_url.
  Không tải CV theo cv_id nếu cần phân biệt từng đơn; không hiển thị CV sửa mới thay snapshot.
- Chỉ thấy đơn thuộc tin công ty mình. Không có thêm ghi chú nội bộ tách biệt vì
  backend hiện chỉ lưu note trong lịch sử đổi trạng thái.

C05. Gợi ý ứng viên theo tin
- Chọn tin công ty mình; xếp theo điểm backend; hiển thị kỹ năng đáp ứng/còn thiếu,
  giải thích và các trường được API cho phép. Chỉ sinh viên bật tìm việc, tài khoản hoạt động.
- GPA, liên hệ, thành tích theo show_*; null nghĩa là không chia sẻ, không suy đoán.
- Nút Mời ứng tuyển với lời nhắn tùy chọn. Không cho tải CV hay xem toàn bộ hồ sơ
  sinh viên chưa ứng tuyển vì API gợi ý không cung cấp quyền đó.

C06. Lời mời đã gửi
- Danh sách phân trang, tin, sinh viên theo dữ liệu trả về/tra cứu được theo quyền,
  lời nhắn, trạng thái PENDING/ACCEPTED/DECLINED/EXPIRED. Không có nút thu hồi/sửa lời mời.

C07. Đánh giá thực tập — form theo ngữ cảnh
- Nhận xét evaluation và điểm score 0–10, xác nhận gửi; trạng thái đã chốt thì chỉ đọc.
- Chỉ công ty có đơn HIRED đúng đợt được gửi, đợt ONGOING/CLOSED.
- API có PUT /internship-terms/results/{result_id}/evaluation nhưng chưa có danh sách
  result_id dành cho doanh nghiệp. Vì vậy thiết kế form có điều kiện khi đã được
  cung cấp result_id, đánh dấu điểm tích hợp cần bổ sung; KHÔNG tạo menu danh sách
  “Kết quả thực tập của công ty” hoạt động giả. Không giả định application_id=result_id.

API chính: /companies/me, /companies/me/documents, /jobs/me, POST /jobs,
/jobs/{id}/submit, /jobs/{id}/close, /jobs/{id}/stats, /company/applications,
/company/applications/{id}, /{id}/status, /{id}/history, /{id}/cv,
/matching/jobs/{id}/candidates, /invitations, /invitations/company.

## 7. Khu vực quản trị nhà trường

D01. Tổng quan và phân tích
- Cards số sinh viên, doanh nghiệp, tin, đơn, phỏng vấn hiện tại, trúng tuyển.
- Bộ lọc thời gian, khoa, ngành, khóa, đợt theo API. Biểu đồ breakdown theo khoa/
  ngành/khóa/đợt; kỹ năng được yêu cầu; thiếu hụt kỹ năng; tỷ lệ đáp ứng và điểm trung
  bình; xu hướng theo ngày; so sánh luồng tự do và theo đợt.
- Nhãn giải thích ngắn: tỷ lệ phù hợp dựa kết quả matching đã tính; số phỏng vấn là
  đơn đang INTERVIEW, không phải tổng lần phỏng vấn trong lịch sử.
- Tính lại matching là tác vụ nền; sau gửi hiển thị “Đã xếp hàng”, không vẽ phần trăm
  tiến độ hay hứa thời điểm xong vì chưa có API theo dõi tiến độ.
- Xuất Excel sinh viên/công ty/tin/đơn/kỹ năng và PDF tổng quan; không có Excel Kanban
  hoặc xuất PDF CV nếu backend chưa hỗ trợ.

D02. Quản lý sinh viên
- Bảng lọc tên/mã/email, khoa, ngành, khóa, trạng thái tài khoản.
- Chi tiết tách rõ official và self_declared, hiển thị nguồn dữ liệu.
- Sửa dữ liệu học thuật: họ tên, ngày sinh, lớp, khoa/ngành, khóa, GPA, xếp loại,
  điện thoại; không tạo form tự đổi email/tài khoản nếu endpoint không hỗ trợ.
- Thêm/xóa thành tích; xác thực chứng chỉ tự khai; gửi lại email kích hoạt chỉ cho
  tài khoản PENDING_ACTIVATION.
- Import Excel/CSV: upload -> kiểm tra/gửi -> báo cáo tổng dòng, thành công, thất bại,
  số dòng lỗi/lý do; lịch sử import và chi tiết. Không cần màn mapping cột tùy ý vì
  API chưa có mapping. Không hứa tải file lỗi nếu chưa có endpoint; có thể xem bảng lỗi.
- Cột bắt buộc: student_code, full_name, email, faculty, major, cohort.
  faculty/major nhận mã hoặc tên; hỗ trợ tiêu đề tiếng Việt thông dụng. Cột tùy chọn:
  date_of_birth, class_name, gpa, academic_result, phone. GPA 0–4.
- Không có nút thêm sinh viên thủ công riêng vì tài khoản sinh viên được tạo qua import.

D03. Giảng viên
- Danh sách theo khoa/tên; tạo, sửa, ngừng hoạt động. Form mã tùy chọn, họ tên,
  khoa bắt buộc, email, điện thoại. Không tạo tài khoản/đăng nhập giảng viên.

D04. Kiểm duyệt doanh nghiệp
- Danh sách theo trạng thái, tìm tên/mã số thuế; drawer/trang chi tiết công ty,
  giấy tờ và trạng thái. Duyệt hoặc từ chối với lý do bắt buộc; xác nhận thao tác.
- Khi API chỉ trả metadata/file_url của giấy tờ, không giả định có sẵn endpoint
  preview/tải file xác thực; thiết kế khu metadata và đánh dấu tích hợp file cần kiểm tra.

D05. Kiểm duyệt tin
- Danh sách lọc trạng thái, công ty, đợt, từ khóa; mặc định chờ duyệt.
- Chi tiết đầy đủ, duyệt, từ chối có lý do bắt buộc, đóng tin vi phạm có ghi chú.
- Không hiển thị “AI phân tích xong” ngay khi bấm duyệt vì phân tích chạy nền.

D06. Đợt thực tập
- Danh sách theo năm học/học kỳ/trạng thái; tạo/sửa với tên, học kỳ, năm học,
  ngày bắt đầu/kết thúc. Chuyển DRAFT → OPEN → ONGOING → CLOSED từng bước.
- Chi tiết tabs: Tổng quan, Sinh viên, Tin thuộc đợt, Kết quả.
- Thêm sinh viên bằng chọn nhiều student_ids; import thành viên theo student_code;
  danh sách thành viên, xóa thành viên khi backend cho phép.
- Phân công một giảng viên cho nhiều sinh viên, hoặc bỏ phân công bằng lecturer_id=null.
- Kết quả: lọc trạng thái/giảng viên, đánh giá doanh nghiệp, nhận xét/điểm nhà trường,
  xác nhận PASSED/FAILED. Admin nhập thay giảng viên ở phiên bản này.
- Đã chốt thì khóa các thao tác backend không cho phép; doanh nghiệp đã đánh giá thì
  không cho xóa sinh viên khỏi đợt nếu backend từ chối. Không có quản lý điểm danh/
  nhật ký thực tập/báo cáo tuần vì chưa có API.

D07. Danh mục
- Tabs khoa, ngành, lĩnh vực, loại hình công việc, kỹ năng.
- Tạo/xem/sửa/ngừng hoạt động, lọc và phân trang; ngành phải gắn khoa.
- Kỹ năng có category và các tên gọi khác (alias): xem, thêm, xóa alias.
  Không có sửa alias trực tiếp vì API hiện chỉ thêm/xóa mapping.
- Dùng “Ngừng hoạt động” thay “Xóa vĩnh viễn” cho danh mục.

D08. Tài khoản
- Danh sách lọc role/trạng thái/từ khóa, chi tiết, khóa tài khoản có lý do, mở khóa,
  tạo admin (email, mật khẩu, họ tên; khoa/chức vụ/điện thoại tùy chọn).
- Không có thao tác tự đổi role hoặc xóa vĩnh viễn tài khoản.

D09. Báo cáo vi phạm
- Danh sách theo trạng thái và loại đối tượng; chi tiết lý do, người gửi, thời gian.
- Xử lý RESOLVED hoặc REJECTED và ghi chú. Với RESOLVED có lựa chọn khóa tài khoản
  liên quan hoặc đóng tin nếu đúng loại đối tượng. Xác nhận rõ tác động trước khi gửi.
- Không mở tính năng kiểm duyệt bài đăng/mạng xã hội ngoài các đối tượng JOB/COMPANY/STUDENT.

D10. Nhật ký email
- Danh sách theo trạng thái và loại; người nhận, tiêu đề, thời gian gửi, lỗi,
  số lần thử lại theo schema. Nút xếp hàng gửi lại email FAILED.
- API retry hiện là thao tác hàng loạt, không tạo nút gửi lại từng dòng nếu chưa có API.
- Không có giao diện sửa SMTP, nhập API key hoặc soạn chiến dịch email marketing.

API chính: /admin/dashboard/*, /admin/exports/*, /matching/recompute,
/admin/students/*, /admin/lecturers/*, /admin/companies/*, /admin/jobs/*,
/internship-terms/*, /catalog/*, /admin/users/*, /reports/*.

## 8. Trạng thái và nguyên tắc tương tác

Trạng thái tin:
- DRAFT: Nháp; PENDING_APPROVAL: Chờ duyệt; APPROVED: Đã duyệt;
  REJECTED: Bị từ chối; CLOSED: Đã đóng; EXPIRED: Hết hạn.

Trạng thái đơn:
- APPLIED: Đã ứng tuyển → SCREENING: Sàng lọc → SHORTLISTED: Danh sách ngắn
  → INTERVIEW: Phỏng vấn → OFFER: Đề nghị tuyển dụng → HIRED: Đã tuyển.
- REJECTED: Bị từ chối; WITHDRAWN: Đã rút. Backend quyết định chuyển trạng thái hợp lệ.
- Các trạng thái kết thúc không tiếp tục kéo thả. Không thêm “Đặt lịch phỏng vấn”;
  note ở INTERVIEW/OFFER có thể chứa giờ, địa điểm/link và được đưa vào email.

Mọi danh sách cần loading skeleton, có dữ liệu, rỗng, không có kết quả lọc và lỗi.
Form có lỗi từng trường, nút đang gửi và chống bấm lặp. Thao tác nhạy cảm có xác nhận.
Không dùng spinner vô hạn hoặc progress giả cho tác vụ không có API tiến độ.
Ngày hiển thị dd/MM/yyyy, giờ theo địa phương; lương dùng định dạng VNĐ.
Không tự mặc định giá trị 0 cho dữ liệu bị ẩn/null; không tạo thêm nút không hoạt động.

Thiết kế prototype nối được các luồng:
1. Kích hoạt sinh viên → đăng nhập → hoàn thiện hồ sơ → CV → tìm việc → ứng tuyển → theo dõi đơn.
2. Đăng ký doanh nghiệp → chờ duyệt → đăng nhập → tạo tin → gửi duyệt → quản lý ứng viên → HIRED.
3. Admin import sinh viên → duyệt doanh nghiệp/tin → tạo đợt → phân công → xác nhận kết quả → xuất báo cáo.
4. Gợi ý ứng viên → lời mời → sinh viên ứng tuyển theo lời mời → lịch sử trạng thái.

## 9. Giới hạn bắt buộc

Không tự thêm: chat; SMS/OTP điện thoại; đăng nhập Google/LMS; thanh toán/gói dịch vụ;
lịch phỏng vấn dạng lịch; video call; khóa học; chứng chỉ tự động; điểm danh;
CV PDF generator; email marketing; dashboard doanh thu; quản lý role giảng viên;
đồng bộ hệ thống đào tạo như chức năng đang hoạt động. API sync hiện trả 501 nên
không đưa nút đồng bộ vào luồng chính.

Khi một màn hình thiếu dữ liệu hoặc endpoint, hãy ghi chú cho nhóm trong annotation
thiết kế thay vì tự tạo API hoặc hiển thị một chức năng giả đang hoạt động.
Tên endpoint, ID, token và cấu trúc kỹ thuật chỉ nằm trong annotation bàn giao,
không đưa vào nội dung giao diện cho sinh viên/doanh nghiệp.

## 10. Cách thực hiện và đầu ra

Trước tiên đọc toàn bộ mô tả và lập sơ đồ màn hình theo ba role. Chỉ thiết kế trước
ba màn hình để nhóm chọn phong cách:
- S01 Tìm việc của sinh viên (desktop + mobile).
- C04 Kanban doanh nghiệp (desktop + mobile, có drawer chi tiết và trạng thái GPA bị ẩn).
- D01 Tổng quan admin (desktop + mobile).

Giữ cùng design system. Sau khi nhóm duyệt phong cách, thiết kế tiếp theo từng nhóm:
A01–A08, S01–S10, C01–C07, D01–D10. Một mã có thể gồm nhiều tab/modal/biến thể,
không bắt buộc biến tất cả thành các trang độc lập.

Với mỗi màn hình, bàn giao: mã/tên màn hình, role, bố cục, component chính,
trạng thái dữ liệu, hành động, prototype nối màn liên quan và annotation API.
Tạo các thành phần có thể chỉnh sửa và tái sử dụng; giữ tên màn hình/component rõ ràng.
Ưu tiên thiết kế hoàn chỉnh, nhất quán từng nhóm thay vì tạo mọi màn hình sơ sài một lượt.

Tài liệu API bổ sung đi kèm: API_SCREEN_MAP.md và openapi.json.
Trong trường hợp mô tả thiết kế mâu thuẫn dữ liệu backend, dùng OpenAPI cho tên
trường/phương thức và ghi chú khác biệt để nhóm xác nhận, không tự mở rộng chức năng.
