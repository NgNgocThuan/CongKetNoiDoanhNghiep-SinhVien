# Mô tả màn hình Freelancer để duyệt thiết kế

**Đã triển khai local theo hai bộ thiết kế ZIP ngày 08/11/2026:** xem [hướng dẫn frontend và ảnh xem trước](../../../frontend/docs/FREELANCER_IMPLEMENTATION.md). Tài liệu bên dưới là đầu vào thiết kế; bản triển khai đã có điểm nối API và kiểm thử tương ứng.

Ngày 08/11/2026. Đây là yêu cầu thiết kế đề xuất, chưa triển khai frontend. Đối chiếu backend local A–D và [PAYOS_IMPLEMENTATION.md](PAYOS_IMPLEMENTATION.md). Không coi các số liệu minh họa trong thiết kế là dữ liệu giao dịch thật.

## 1. Nguyên tắc chung

- Giữ AppShell hiện có: sidebar, header, thông báo, tài khoản và vùng nội dung. Giữ Inter/Be Vietnam Pro, nền `#f6f8fc`, thẻ trắng, bo góc 14px. Sinh viên xanh `#2563eb`, doanh nghiệp xanh ngọc `#087d71`, Admin xanh tím `#354d8b`. Người thuê cá nhân dùng chung cấu trúc nghiệp vụ với doanh nghiệp, màu xanh ngọc là đề xuất cần duyệt.
- Bổ sung nhóm menu Freelancer, giữ các khu vực tuyển dụng/thực tập hiện có. CLIENT là người thuê cá nhân; COMPANY là doanh nghiệp. Một doanh nghiệp chỉ có một tài khoản đại diện, không thêm màn hình mời thành viên/phân quyền nội bộ doanh nghiệp.
- Dự án chứa nhiều hợp đồng, mỗi hợp đồng gắn một sinh viên. Hợp đồng chứa các mốc công việc. Nút ký quỹ/nghiệm thu/hoàn tiền luôn ghi rõ hợp đồng, sinh viên và mốc tương ứng.
- Dùng từ “Mốc công việc” trên giao diện, có thể giải thích “milestone” lần đầu. Thể hiện riêng tiến độ công việc, trạng thái ký quỹ và trạng thái chi tiền.
- Hiển thị tiền dạng `1.500.000 ₫`, có nhãn tổng tiền, phí nền tảng và thực nhận. Không làm ví, số dư khả dụng để rút hoặc nút rút tiền.
- Không dùng nhãn “đã trả tiền” khi chỉ mới nghiệm thu hoặc gửi yêu cầu chi. Giao dịch chưa rõ kết quả phải hiện “Đang xác minh giao dịch” và cho xem lại trạng thái.
- MOU bản đầu là tài liệu đã ký ngoài hệ thống, được tải lên và Admin kiểm tra. Không thiết kế nút ký điện tử/OTP ký MOU khi chưa có nghiệp vụ đó.
- Dữ liệu tổng hợp chưa có API riêng có thể được bố trí trên wireframe nhưng phải ghi chú phụ thuộc, không tự hiển thị số liệu giả khi triển khai.

## 2. Menu đề xuất

| Vai trò | Các mục Freelancer |
|---|---|
| Người thuê cá nhân/doanh nghiệp | Tổng quan; Dự án của tôi; Hợp đồng; Ký quỹ & giao dịch; Tài khoản ngân hàng. Doanh nghiệp thêm Xác minh & MOU. |
| Sinh viên | Tìm dự án; Đơn ứng tuyển dự án; Công việc của tôi; Thanh toán; Tài khoản ngân hàng. |
| Admin | Tổng quan Freelancer; Xác minh doanh nghiệp & MOU; Duyệt dự án; Duyệt tài khoản ngân hàng; Thu & ký quỹ; Giải ngân & hoàn tiền; Nguồn tiền chi; Tranh chấp; Đối soát. |

Hủy và tranh chấp mở từ hợp đồng/mốc liên quan, không bắt người dùng tự tìm và nhập mã hợp đồng. Chưa thêm chat trực tiếp hoặc cuộc gọi vì backend hiện chưa cung cấp các tính năng đó.

## 3. Tài khoản và điều kiện sử dụng

### G01 — Đăng ký người thuê và xác minh liên hệ

**Người dùng:** người thuê cá nhân; doanh nghiệp dùng luồng đăng ký doanh nghiệp hiện có và bổ sung onboarding cần thiết.

**Bố cục:** form đăng ký, lựa chọn loại tài khoản; sau đăng ký là trang hoàn thiện hồ sơ với checklist email, điện thoại và điều kiện còn thiếu. Xác minh email/điện thoại bằng bước riêng: nhập thông tin, gửi mã, nhập OTP, kết quả.

**Thao tác:** đăng ký, gửi lại mã, xác minh, sửa liên hệ. Hiện thời gian chờ gửi lại, mã hết hạn, sai mã và đạt giới hạn thử. Cho lưu nháp khi đủ điều kiện; khi chưa được đăng/giao kết/ký quỹ, hiển thị lý do và đường dẫn hoàn thiện tương ứng. Không biến việc chưa xác minh thành một màn lỗi chung.

### G02 — Hồ sơ xác minh doanh nghiệp và MOU

**Bố cục:** hai tab “Xác minh doanh nghiệp” và “MOU”. Tab đầu gồm thông tin pháp nhân, mã số thuế, đại diện, giấy phép và chứng cứ thẩm quyền. Tab MOU hiển thị tài liệu, bên ký, thời hạn, phạm vi và kết quả kiểm tra.

**Thao tác:** lưu/nộp hồ sơ, xem lý do cần bổ sung, nộp bản mới, tải tài liệu được phép. MOU mới do Admin tạo; doanh nghiệp xem/được hướng dẫn cung cấp tài liệu theo quy trình hiện tại. Hiển thị riêng xác minh pháp nhân, hiệu lực MOU và trạng thái hoạt động. MOU sắp hết hạn có cảnh báo; hết hạn không tự hiển thị hợp đồng đang chạy là bị hủy.

### G03 — Tài khoản nhận giải ngân/hoàn tiền

**Người dùng:** sinh viên và người thuê cần nhận hoàn.

**Bố cục:** danh sách thẻ ngân hàng, tên chủ tài khoản, số tài khoản che bớt, trạng thái chờ duyệt/đã xác minh/từ chối/ngừng dùng. Form thêm gồm mã ngân hàng, số tài khoản, tên chủ tài khoản và hướng dẫn đối chiếu sở hữu.

**Thao tác:** thêm tài khoản, xem hướng dẫn xác minh, ngừng dùng. Bản đã xác minh không sửa trực tiếp; thêm bản mới để thay cho các lệnh tương lai. Giải thích tài khoản mới không tự thay đích của lệnh đang xử lý. Không gắn nhãn xác minh chỉ vì người dùng đã nhập đủ thông tin hoặc nhập OTP.

## 4. Không gian người thuê

### H01 — Tổng quan Freelancer

**Bố cục:** phần chào, nút “Tạo dự án”; thẻ dự án đang tuyển, hợp đồng đang làm, mốc cần ký quỹ, sản phẩm chờ nghiệm thu. Dưới là danh sách việc cần làm, mỗi hàng có tên dự án, sinh viên, hợp đồng/mốc và hành động tiếp theo.

**Trạng thái:** chưa có dự án có lời hướng dẫn tạo dự án; chưa đủ điều kiện có checklist. Các số tiền tổng hợp phải ghi rõ phạm vi/thời điểm và không được cộng tiền hoàn với tiền đã trả sinh viên thành một chỉ số “đã chi”. Các thẻ tổng hợp cần xác nhận API khi triển khai.

### H02 — Dự án của tôi

**Bố cục:** tìm kiếm và bộ lọc trạng thái; bảng tên dự án, tổng ngân sách, số sinh viên đã chọn/trần, hạn, trạng thái tuyển và trạng thái thực hiện. Nút tạo dự án ở đầu trang.

**Thao tác:** mở chi tiết, sửa nháp, gửi duyệt, đóng/mở tuyển khi được phép. Trạng thái “đóng tuyển” hiển thị độc lập với “đã hoàn thành dự án”. Không đánh dấu dự án hoàn thành chỉ vì một sinh viên đã làm xong.

### H03 — Tạo/chỉnh sửa dự án

**Bố cục:** form theo ba bước: thông tin và kỹ năng; ngân sách/số sinh viên/hạn; đề xuất mốc và tiêu chí bàn giao. Cột tóm tắt cho biết đây là tổng ngân sách của dự án, không phải ngân sách mặc định cho mỗi sinh viên.

**Thao tác:** lưu nháp, xem trước, gửi duyệt. Mỗi đề xuất mốc có tên, số tiền, hạn, tiêu chí nghiệm thu. Giải thích chính sách ký quỹ toàn bộ hợp đồng hoặc từng mốc theo điều kiện được backend cho phép. Hiện lỗi tại trường nhập và lý do không thể gửi, không cho tự bỏ qua hạn mức.

### H04 — Chi tiết dự án và lựa chọn sinh viên

**Bố cục:** đầu trang có ngân sách, phần đã phân bổ, phần còn lại, số chỗ, trạng thái. Các tab: tổng quan; ứng viên; hợp đồng; lịch sử duyệt. Ứng viên có đề xuất, mức giá, thời gian, CV được phép xem và trạng thái xét chọn.

**Thao tác:** đưa vào danh sách cân nhắc, từ chối, chọn sinh viên. Hộp xác nhận chọn ghi tên sinh viên và ngân sách phân bổ cho hợp đồng riêng. Sau khi chọn dẫn tới hợp đồng nháp của đúng sinh viên. Danh sách hợp đồng hiển thị riêng ngân sách, ký quỹ, tiến độ và thanh toán từng người. Phần ngân sách phân bổ không được gọi là tiền đã ký quỹ. Khi cần tăng trần ngân sách/số người, mở yêu cầu mở rộng để Admin xét thay vì cho sửa trực tiếp.

## 5. Không gian sinh viên

### S01 — Tìm dự án Freelancer

**Bố cục:** thanh tìm kiếm; lọc kỹ năng và các điều kiện backend hỗ trợ. Thẻ dự án có tên, người thuê, ngân sách tổng, số vị trí, hạn và kỹ năng. Trạng thái xác minh người thuê chỉ hiện từ dữ liệu được phép công khai.

**Thao tác:** xem dự án. Không biến tổng ngân sách dự án thành mức thu nhập hứa trả cho một sinh viên. Không đưa bộ lọc hoặc nhãn đánh giá/tỷ lệ thành công vào thiết kế mặc định khi chưa có dữ liệu/API.

### S02 — Chi tiết dự án và ứng tuyển

**Bố cục:** mô tả công việc, sản phẩm, tiêu chí, kỹ năng, hạn, số người và các mốc đề xuất. Cột bên là thông tin người thuê và nút ứng tuyển. Form ứng tuyển gồm lời đề xuất, mức giá, số ngày và CV/tệp hồ sơ hợp lệ.

**Thao tác:** gửi ứng tuyển, xem đơn đã gửi. Hiện riêng đã ứng tuyển, tuyển đã đóng, hồ sơ chưa đủ điều kiện. Giải thích đây là đề xuất ứng tuyển, điều khoản chính thức sẽ nằm trong hợp đồng được hai bên chấp nhận.

### S03 — Đơn ứng tuyển và công việc của tôi

**Bố cục:** hai tab hoặc hai trang cùng kiểu bảng: đơn đã gửi với trạng thái xét chọn; hợp đồng đã được tạo với dự án, người thuê, ngân sách riêng, mốc hiện tại và hạn tiếp theo.

**Thao tác:** xem/rút đơn khi được phép; mở hợp đồng; mở mốc cần xử lý. Khi được chọn nhưng hợp đồng chưa được hai bên chấp nhận, hiện “Chờ thống nhất hợp đồng”, không hiện “Đang thực hiện”. Không hiển thị hợp đồng của sinh viên khác trong cùng dự án.

## 6. Màn hình nghiệp vụ dùng chung

### W01 — Chi tiết hợp đồng

**Bố cục:** tên dự án, hai bên, mã hợp đồng, trạng thái; thẻ ngân sách riêng và phần tiền; các tab điều khoản, mốc công việc, bàn giao, thanh toán, hủy/tranh chấp, lịch sử. Desktop có tóm tắt bên phải; mobile đưa tóm tắt lên trước nội dung chi tiết.

**Thao tác theo vai trò:** người thuê đề xuất điều khoản/ký quỹ/nghiệm thu; sinh viên chấp nhận điều khoản/bắt đầu/nộp bài; hai bên xem lịch sử, đề nghị hủy, mở tranh chấp khi đủ điều kiện. Chỉ hiển thị nút phù hợp trạng thái hiện tại và giải thích khi bị chặn.

### W02 — Soạn và chấp nhận phiên bản điều khoản

**Bố cục:** bảng các mốc gồm tên, phạm vi, số tiền, hạn, tiêu chí; tổng tiền, phí, chính sách ký quỹ, thời hạn review, số lần sửa và điều kiện hủy. Có danh sách phiên bản và phần đối chiếu nội dung thay đổi.

**Thao tác:** lưu nháp, gửi đề nghị, xem/chấp nhận phiên bản đang đề nghị. Trước xác nhận hiển thị đầy đủ phiên bản và điều khoản. Bản đang có hiệu lực và bản mới đang chờ phải phân biệt rõ. Mốc đã bị khóa theo nghiệp vụ không cho sửa; thông báo đề nghị đã hết hạn hoặc có phiên bản khác thay thế. Thao tác này là chấp nhận điều khoản trên nền tảng, không quảng bá là chữ ký số được chứng thực.

### W03 — Không gian mốc công việc, bàn giao và nghiệm thu

**Bố cục:** đầu trang có tên mốc, số tiền, hạn, trạng thái công việc và tiền. Vùng chính có yêu cầu/tiêu chí, các lần nộp, ghi chú, tệp và lịch sử phản hồi. Một khối riêng thể hiện thời hạn phản hồi và số lần sửa còn lại.

**Sinh viên:** bắt đầu khi đủ điều kiện, tải tệp, nhập ghi chú, nộp bản đầu/bản sửa. Tệp đang kiểm tra cần hiện trạng thái và chưa được coi là tài liệu hợp lệ để nộp.

**Người thuê:** xem bản nộp và tệp, yêu cầu sửa kèm lý do, chấp nhận nghiệm thu. Hộp xác nhận nghiệm thu ghi tiền gốc, phí và thực nhận. Sau chấp nhận hiện “Đang xử lý giải ngân”; không hiện “Đã thanh toán” trước kết quả chi. Khi tiền bị giữ hoặc đang tranh chấp, hiện nguyên nhân và đường dẫn xử lý.

### W04 — Ký quỹ qua payOS

**Người dùng:** người thuê, mở từ một mốc/hợp đồng xác định.

**Bố cục:** hai cột. Bên trái tên dự án, sinh viên, hợp đồng, mốc, số tiền và hạn thanh toán. Bên phải trạng thái tạo yêu cầu; khi sẵn sàng hiển thị QR, thông tin chuyển khoản do hệ thống trả và nút “Mở trang thanh toán payOS”.

**Thao tác:** sao chép thông tin hợp lệ, mở payOS, kiểm tra trạng thái, yêu cầu hủy đơn khi được phép. Chờ tạo link có loading và nội dung rõ. Đếm ngược hết hạn không tự coi giao dịch chưa có tiền. Nếu chuyển sai/thiếu/thừa, hướng dẫn chờ kiểm tra, không khuyên chuyển thêm để cộng cho đủ. Với ký quỹ toàn bộ hợp đồng, thể hiện checklist các mốc cần được cấp vốn; không thiết kế một đơn thanh toán gộp cho nhiều mốc hoặc nhiều sinh viên.

### W05 — Kết quả sau thanh toán

**Bố cục:** trang gọn có biểu tượng, thông điệp, tóm tắt đơn và các nút về hợp đồng/xem giao dịch/kiểm tra lại. Dùng chung cấu trúc cho return và cancel.

**Các biến thể phải vẽ:** đang xác minh; đã xác nhận ký quỹ; chưa ghi nhận thanh toán; đơn hết hạn/hủy đã xác nhận; giao dịch cần kiểm tra; không tải được trạng thái. Quay về từ payOS hoặc đóng trang thanh toán không đủ để hiện thành công/thất bại. Lỗi mạng không được mô tả là tiền đã mất.

### W06 — Ký quỹ và lịch sử giao dịch

**Bố cục:** người thuê thấy tổng ký quỹ, tiền đang giữ, đang xử lý chi, đã giải ngân và đã hoàn; sinh viên thấy giá trị được nghiệm thu, phí, thực nhận theo hợp đồng và kết quả chi. Cần chốt API tổng hợp trước khi triển khai các số tổng toàn tài khoản.

**Chi tiết khả dụng:** theo dự án/hợp đồng/mốc, danh sách yêu cầu thu, tiền thực nhận, các lần quyết toán và chuyển tiền. Trang chi tiết ghi mã, thời gian, số tiền, phí, kết quả và lịch sử. Khoản chia vừa giải ngân vừa hoàn có hai hàng độc lập. Giải thích “đang xử lý” là một phần tiền đang giữ, tránh cộng hai chỉ số trùng nhau. Không có nút rút tiền từ ví.

### W07 — Đề nghị hủy và thỏa thuận phân chia

**Bố cục:** thông tin mốc, tiền đang giữ, lý do, đề nghị phần trả sinh viên/phần hoàn người thuê, tóm tắt phí và các xác nhận. Bản đề nghị hiển thị người tạo và trạng thái hai bên.

**Thao tác:** gửi đề nghị, bên còn lại chấp nhận/từ chối, người tạo rút đề nghị khi được phép. Không cho sửa nội dung một bản đã được bên kia xác nhận; thay đổi cần đề nghị mới. Chỉ trình bày quyền hủy đơn phương nếu điều khoản và backend thực sự cho phép. Hai bên đồng ý là bước xử lý tiếp theo; chỉ hiển thị “Đã hoàn tiền” sau xác nhận chuyển tiền.

### W08 — Hồ sơ tranh chấp của hai bên

**Bố cục:** thông tin mốc, tiền đang giữ, vấn đề/lý do, hạn nộp bằng chứng; timeline; danh sách tài liệu; kết quả xử lý được phép công khai và trạng thái giải ngân/hoàn sau quyết định.

**Thao tác:** mở tranh chấp, bổ sung tệp/ghi chú hợp lệ, đề nghị rút tranh chấp và bên còn lại xác nhận theo nghiệp vụ. Không thiết kế nút tự rút đơn ngay khi cần sự đồng thuận. Ẩn các thông tin Admin nội bộ. Có trạng thái hết hạn nộp bằng chứng và chờ kiểm tra tệp.

### W09 — Đánh giá sau hoàn thành

**Bố cục:** đối tác được đánh giá, hợp đồng, điểm sao và nội dung nhận xét; kèm trạng thái đã gửi.

**Thao tác:** gửi đánh giá khi đủ điều kiện, xem đánh giá được phép hiển thị. Không cho đánh giá khi chỉ mới ứng tuyển hoặc hợp đồng chưa đạt trạng thái cho phép. Không thiết kế sửa/xóa đánh giá nếu API chưa hỗ trợ.

## 7. Không gian Admin

### A01 — Tổng quan và danh sách chờ xử lý

**Bố cục:** các hàng đợi hồ sơ pháp nhân, MOU, dự án, ngân hàng, thu bất thường, chi chưa rõ, tranh chấp và đối soát. Ưu tiên danh sách có số ngày chờ, hạn và nút mở hồ sơ. Không gọi chỉ số thu/tiền đang giữ là doanh thu nền tảng. Dashboard thống kê hợp nhất cần API bổ sung; từng danh sách nghiệp vụ đã có điểm đọc riêng.

### A02 — Duyệt pháp nhân và MOU

**Bố cục:** danh sách lọc trạng thái, mở chi tiết hai cột tài liệu/thông tin và phiếu kiểm tra. Có lịch sử nộp/duyệt, đại diện, thẩm quyền; MOU có bên ký, thời hạn và phạm vi.

**Thao tác:** duyệt/từ chối/yêu cầu bổ sung hồ sơ theo loại; tạo, kiểm tra, duyệt hoặc thu hồi MOU theo quyền. Không có nút tự xác minh chữ ký số. Đình chỉ hoạt động và thu hồi MOU là hành động riêng, phải có lý do và mô tả ảnh hưởng. Không gộp trạng thái duyệt tuyển dụng cũ với xác minh pháp nhân Freelancer.

### A03 — Duyệt dự án và mở rộng

**Bố cục:** nội dung dự án, ngân sách, số sinh viên, các mốc đề xuất, điều kiện chủ dự án và lịch sử duyệt. Yêu cầu mở rộng có đối chiếu trần cũ/mới và lý do.

**Thao tác:** phê duyệt/từ chối theo API, nhập lý do; xét riêng yêu cầu tăng ngân sách/số người. Không đổi điều khoản hợp đồng đã ký trong trang duyệt dự án.

### A04 — Duyệt tài khoản ngân hàng

**Bố cục:** hàng đợi, chủ tài khoản/người dùng, ngân hàng, số tài khoản che bớt và trạng thái. Phiếu kiểm tra hướng dẫn đối chiếu chứng cứ sở hữu/danh tính; có nơi ghi kết quả và lý do.

**Thao tác:** duyệt/từ chối tài khoản đang chờ. Không tự điền kết quả “trùng tên ngân hàng” khi chưa tích hợp tra cứu. Nếu cần xem đầy đủ số tài khoản/chứng cứ ngay trong màn hình, ghi nhận là điểm API/quyền truy cập cần bổ sung; không lấy ciphertext để hiển thị. Không tự duyệt tài khoản của chính Admin đó.

### A05 — Khoản thu cần kiểm tra

**Bố cục:** bảng mã giao dịch, đơn/mốc liên quan nếu có, tiền yêu cầu và thực nhận, thời gian, lý do sai lệch, trạng thái. Chi tiết có thông tin đối chiếu và lịch sử xử lý.

**Thao tác:** phân bổ khi backend cho phép hoặc đề nghị hoàn về người trả đã xác định; cần lý do. Chưa xác định người trả thì hiển thị chờ tra soát, không có ô tùy ý chọn người nhận tiền. Hoàn tiền đang xử lý và đã hoàn phải khác nhau. Không cho sửa số tiền thực thu hoặc đánh dấu ngân hàng đã chuyển bằng tay.

### A06 — Giải ngân và hoàn tiền

**Bố cục:** danh sách các lệnh chi, hợp đồng/mốc, người nhận, mục đích, số tiền, trạng thái; chi tiết hiển thị kết quả kiểm tra và mốc thời gian. Settlement chia hai bên có hai nhánh dễ phân biệt.

**Thao tác:** xem, yêu cầu kiểm tra lại trạng thái kèm lý do. Không gắn nhãn “Chi lại” cho thao tác chỉ tra cứu; không có nút xác nhận đã trả tiền thủ công hoặc đổi đích của lệnh đang chạy. Trạng thái chưa rõ cần nổi bật nhưng không báo chắc chắn thất bại.

### A07 — Nguồn tiền chi và phí thực

**Bố cục:** danh sách chứng từ ghi nhận tiền chuyển sang kênh chi, vốn vận hành và phí provider. Form có loại, số tiền, tham chiếu thực tế, chứng cứ và lý do. Chi tiết có người đề xuất, người duyệt và trạng thái.

**Thao tác:** đề xuất ghi nhận; Admin khác xem chứng cứ, duyệt/từ chối. Nút ghi “Ghi nhận giao dịch đã thực hiện”, không ghi “Nạp tiền” nếu thao tác đó chỉ tạo bản ghi kế toán. Không thiết kế nút tự chuyển tiền giữa hai kênh khi backend chưa có chức năng đó.

### A08 — Xử lý tranh chấp

**Bố cục:** danh sách theo trạng thái/hạn, chi tiết có điều khoản, các lần bàn giao, bằng chứng hai bên, lịch sử quyết định. Form quyết định chia rõ tổng đang giữ, phần trả sinh viên, phí/thực nhận, phần hoàn người thuê và lý do.

**Thao tác:** phân công xử lý, đề xuất quyết định, Admin thứ hai duyệt khi bắt buộc, thực hiện quyết định đã được duyệt. Tổng chia phải khớp tiền theo backend. Hiện riêng “quyết định đã duyệt”, “đang thực hiện” và “đã giải quyết”; nhánh chuyển tiền còn lỗi/chưa rõ không được tô hoàn tất toàn bộ. Không cho người đề xuất tự duyệt quyết định cần hai Admin.

### A09 — Đối soát và tác vụ lỗi

**Bố cục:** danh sách lần kiểm tra, phạm vi/thời gian, vấn đề nội bộ và trạng thái các truy vấn bên ngoài; chi tiết các khoản cần kiểm tra, số mong đợi/thực tế khi có. Tab tác vụ lỗi hiển thị thông tin vận hành phù hợp quyền Admin.

**Thao tác:** tạo lần đối soát, xem sai lệch, mở giao dịch gốc; requeue tác vụ lỗi có lý do khi được phép. Một lần kiểm tra nội bộ thành công không được viết thành “Đã khớp ngân hàng” khi truy vấn hoặc sao kê chưa xong. Chưa thiết kế nút xóa/sửa ledger hoặc đóng sai lệch tùy ý nếu API không hỗ trợ.

## 8. Trạng thái và thành phần phải bàn giao cùng thiết kế

| Thành phần | Các biến thể tối thiểu |
|---|---|
| Danh sách | Loading; có dữ liệu; chưa có dữ liệu; tìm kiếm không có kết quả; lỗi tải; phân trang |
| Form | Chưa nhập; lỗi từng trường; lưu nháp; đang gửi; thành công; dữ liệu đã thay đổi/hết hạn cần tải lại |
| Upload | Đang tải; chờ kiểm tra; hợp lệ; bị từ chối/lỗi; file không còn truy cập được |
| Thanh toán | Đang tạo đơn; chờ thanh toán; đang xác minh; ký quỹ thành công; cần kiểm tra; hủy/hết hạn đã xác nhận |
| Chi tiền | Chờ xử lý; đang xử lý; đang xác minh; thành công; thất bại cần đối soát; hoàn tất một phần |
| Quyền/điều kiện | Chưa xác minh; tài khoản bị hạn chế; không đủ điều kiện; không tìm thấy tài nguyên được phép xem |
| Xác nhận | Đúng dự án/hợp đồng/mốc/người nhận; tiền và phí; lý do khi cần; đang gửi chống bấm lặp |

Desktop và mobile cần thiết kế cho toàn bộ luồng cốt lõi. Sidebar mobile dùng drawer hiện có; bảng chuyển thành thẻ hoặc hàng xếp dọc, QR đủ lớn để quét, các nút tài chính không bị che bởi bàn phím/footer. Trạng thái phải có chữ/biểu tượng, không chỉ phân biệt bằng màu. Không chèn thuật ngữ API, webhook, khóa bí mật hoặc thông báo lỗi SQL vào giao diện người dùng.

## 9. Phạm vi ưu tiên để kiểm thử

**Vòng 1 — luồng hoàn thành một hợp đồng:** G03 → A04; H04/S03 → W01 → W02 → W04/W05 → W03 → A07/A06 → W06. Bao gồm tài khoản thử của người thuê, sinh viên và hai Admin; các hợp đồng/mốc dùng để thử phải được tạo qua các luồng backend hợp lệ. Không cần làm dashboard thống kê để kiểm thử tiền.

**Vòng 2 — các tình huống tiền cần xử lý:** A05, W07, W08, A08, A09; vẽ và kiểm thử thiếu/thừa/muộn, callback chưa rõ, một nhánh giải ngân thành công/nhánh hoàn còn chờ và hủy đơn chưa thanh toán.

**Vòng 3 — mở đầy đủ quy trình sản phẩm:** G01/G02, H01–H04, S01–S03, A01–A03, W09 và các thống kê đã có API được xác nhận. Nếu chưa có dữ liệu thử hợp lệ thì cần làm các màn tạo dự án, ứng tuyển và chọn sinh viên sớm hơn trong vòng 1.

Trước khi code giao diện, cần duyệt: cấu trúc menu; các wireframe màn chính; trạng thái lỗi/chờ; cách phân biệt ngân sách và tiền thật; trang hợp đồng nhiều sinh viên; bản mobile. Danh mục này không tự phê duyệt thao tác tiền thật. Việc thử tiền thật cần cấu hình môi trường, nguồn tiền và phạm vi thực hiện riêng như hướng dẫn payOS.
