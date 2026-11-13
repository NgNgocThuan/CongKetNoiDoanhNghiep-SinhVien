# TÀI LIỆU YÊU CẦU KỸ THUẬT VÀ THIẾT KẾ CẢI TIẾN TRẢI NGHIỆM (UX/SPEC)
## Phân hệ: Tuyển dụng & Dự án Freelancer (Student Connect)

Tài liệu này tổng hợp toàn bộ các yêu cầu kỹ thuật và quyết định thiết kế đã chốt để AI/Kỹ sư triển khai cập nhật hệ thống, bao gồm cả Frontend (UX/UI) và Backend (API, Data Model).

---

### MỤC LỤC
1. [Module 1: Nhập Kỹ năng Tự do (Dynamic / Free-text Skill Tagging)](#module-1-nhập-kỹ-năng-tự-do-dynamic--free-text-skill-tagging)
2. [Module 2: Chọn Ngân hàng Chuẩn VietQR (Thay thế Nhập Mã BIN Thủ công)](#module-2-chọn-ngân-hàng-chuẩn-vietqr-thay-thế-nhập-mã-bin-thủ-công)
3. [Module 3: Modal Điều khoản Ký quỹ & Tranh chấp Lần đầu (Scroll-to-Bottom Enforcement)](#module-3-modal-điều-khoản-ký-quỹ--tranh-chấp-lần-đầu-scroll-to-bottom-enforcement)
4. [Module 4: Bộ Dự án Mẫu Tham khảo (Project Reference Guides)](#module-4-bộ-dự-án-mẫu-tham-khảo-project-reference-guides)
5. [Module 5: Chuẩn hóa & Cố định Menu Trái (Sidebar Navigation & Visual Hierarchy)](#module-5-chuẩn-hóa--cố-định-menu-trái-sidebar-navigation--visual-hierarchy)
6. [Module 6: Điều khoản Dịch vụ & Cam kết Pháp lý khi Đăng ký Tài khoản (Registration Terms & Compliance)](#module-6-điều-khoản-dịch-vụ--cam-kết-pháp-lý-khi-đăng-ký-tài-khoản-registration-terms--compliance)

---

### MODULE 1: NHẬP KỸ NĂNG TỰ DO (DYNAMIC / FREE-TEXT SKILL TAGGING)

#### 1. Mục tiêu & Quyết định thiết kế
* **Bỏ tư duy danh mục tĩnh**: Không giới hạn người dùng chỉ được tick chọn những kỹ năng có sẵn. Cho phép nhập text tự do bất kỳ kỹ năng ngành nghề nào (ví dụ: *Prompt Engineering, Figma Auto-layout, Golang, Photoshop, Dịch thuật Nhật - Việt*...).
* **Bỏ hoàn toàn bước phê duyệt của Admin**: Ai gõ kỹ năng mới là kỹ năng đó được tạo và sử dụng ngay lập tức. Không tạo hàng đợi duyệt (không làm phiền cán bộ nhà trường, không làm trễ tiến độ đăng tin).
* **Tự động làm giàu từ điển**: Kỹ năng sau khi được một người tạo sẽ tự động xuất hiện trong gợi ý (autocomplete) cho những người dùng sau.

#### 2. Thiết kế Frontend (`SkillPicker.tsx` hoặc Component thay thế)
* **Dạng Component**: `Creatable Multi-Select / Tag Input`.
* **Hành vi**:
  * Khi gõ text: Lọc các kỹ năng có sẵn từ backend catalog.
  * Nếu không có kết quả trùng khớp: Hiển thị dòng gợi ý `+ Thêm mới "[kỹ năng vừa gõ]"`.
  * Nhấn `Enter` hoặc phím dấu phẩy `,`: Tạo một thẻ Tag (Pill) màu sắc có icon `x` để xóa.
  * Dữ liệu trả ra cho Form: Mảng danh sách tên kỹ năng (string array) hoặc mảng `skill_ids` kèm các chuỗi mới.

#### 3. Thiết kế Backend (API & Database)
* **Xử lý tại Service**:
  * Chuẩn hóa chuỗi (trim khoảng trắng, loại bỏ ký tự đặc biệt nguy hiểm).
  * Tra cứu trong bảng `skills` (không phân biệt hoa thường).
  * Nếu đã tồn tại -> Lấy `id` sẵn có.
  * Nếu chưa tồn tại -> Tự động `INSERT` vào bảng `skills` với `name` = tên mới, `category` = `'OTHER'` (hoặc `'GENERAL'`).
  * Gán vào liên kết bảng (ví dụ `freelance_project_skills` hoặc `student_skills`).
* **Lợi ích**: Giữ toàn vẹn quan hệ khóa ngoại (Foreign Key) trong MariaDB, thuật toán Matching vẫn tính toán độ tương đồng kỹ năng chính xác.

---

### MODULE 2: CHỌN NGÂN HÀNG CHUẨN VIETQR (THAY THẾ NHẬP MÃ BIN THỦ CÔNG)

#### 1. Mục tiêu & Quyết định thiết kế
* **Triệt tiêu rào cản tra cứu**: Người dùng không biết và không cần biết mã BIN 6 số chuẩn Napas (ví dụ `970436`, `970422`).
* **Tránh nhầm lẫn nguy hiểm**: Loại bỏ việc người dùng nhầm "Mã BIN ngân hàng" thành "Mã PIN thẻ ATM".
* **Đồng bộ chuẩn quốc gia**: Sử dụng danh mục hơn 54 ngân hàng của VietQR / Napas 247.

#### 2. Thiết kế Frontend (`Accounts.tsx` - Form Thêm tài khoản ngân hàng)
* **Thay thế ô input `bank_bin`**: Chuyển thành **Searchable Select Dropdown** có kèm Logo và Tên viết tắt.
* **Tương tác**:
  * Người dùng bấm vào -> Danh sách ngân hàng hiện ra kèm Logo nhận diện.
  * Có ô tìm kiếm: Gõ từ khóa ngắn (ví dụ: `vcb`, `vietcom`, `mb`, `tech`, `bidv`, `tpbank`...) -> Bộ lọc hiển thị ngay ngân hàng mong muốn.
  * Khi click chọn (ví dụ: *MBBank*): Giao diện tự động gán ngầm mã BIN `970422` vào state `bank_bin` của form.
* **Form hiển thị cuối cùng chỉ gồm 3 trường thân thiện**:
  1. **Ngân hàng**: Dropdown chọn kèm Logo và Tìm kiếm.
  2. **Số tài khoản**: Ô nhập số tài khoản.
  3. **Tên chủ tài khoản**: Ô nhập họ tên in hoa không dấu (vd: `NGUYEN VAN A`).

#### 3. Thiết kế Backend & Dữ liệu
* **Endpoint cung cấp danh sách ngân hàng**: `GET /api/v1/finance/banks`
  * Trả về danh sách tĩnh chuẩn VietQR: `[{ "bin": "970436", "name": "Ngân hàng TMCP Ngoại thương Việt Nam", "shortName": "Vietcombank", "code": "VCB", "logo": "..." }, ...]`
  * Dữ liệu này tĩnh, nhẹ (< 15KB), backend cache memory hoặc frontend lưu trữ cục bộ.
* **Endpoint tạo tài khoản**: `POST /api/v1/bank-destinations` giữ nguyên cấu trúc schema hiện tại, nhận payload `{ bank_bin, account_number, account_name }` -> Không ảnh hưởng đến core thanh toán PayOS.

---

### MODULE 3: MODAL ĐIỀU KHOẢN KÝ QUỸ & TRANH CHẤP LẦN ĐẦU (SCROLL-TO-BOTTOM ENFORCEMENT)

#### 1. Mục tiêu & Quyết định thiết kế
* Đảm bảo 100% người thuê (Client) hiểu rõ mô hình bảo vệ tài chính trước khi tạo hợp đồng.
* Triệt tiêu tình trạng tranh cãi *"Tôi không biết phải nạp tiền trước"* hoặc *"Tôi tưởng trả tiền ngoài trực tiếp"*.

#### 2. Cơ chế kích hoạt & Tương tác (UX Enforcement)
* **Kích hoạt**: Xuất hiện dạng Modal chặn khi Client bấm nút *"Tạo dự án mới"* lần đầu tiên (kiểm tra thuộc tính `has_accepted_escrow_terms` trên tài khoản).
* **Cơ chế khóa nút**:
  * Nút bấm **"Tôi đã đọc, hiểu rõ và đồng ý với điều khoản"** ban đầu ở trạng thái **DISABLED**.
  * Khung nội dung điều khoản có thanh cuộn riêng biệt.
  * Bắt sự kiện cuộn chuột (`onScroll`): Chỉ khi thanh cuộn chạm đáy (`scrollHeight - scrollTop <= clientHeight + 5px`) thì nút bấm mới chuyển sang trạng thái **ENABLED**.
  * Khi bấm đồng ý: Gọi API lưu cờ `accepted_at`, các lần tạo dự án sau không hiện lại nữa.

#### 3. Nội dung 4 trụ cột bắt buộc trong Điều khoản
1. **Bản chất Ký quỹ (Escrow Model)**:
   * Tiền của khách hàng được giữ an toàn tại tài khoản trung gian hệ thống (qua cổng PayOS). Sinh viên chưa nhận được tiền ngay khi bắt đầu.
2. **Hình thức Ký quỹ (Milestone vs Full Funding)**:
   * **Ký quỹ toàn bộ (Full)**: Nạp đủ 100% tiền dự án cho công việc ngắn hạn / đơn giản.
   * **Ký quỹ theo từng mốc (Milestone)**: Dự án chia làm nhiều giai đoạn. Làm đến mốc nào thì nạp cọc mốc đó. Sinh viên chỉ bắt đầu làm việc khi mốc đó đã hiển thị trạng thái `FUNDED` (Đã ký quỹ).
3. **Quy tắc Giải ngân (Payout Approval)**:
   * Hệ thống chỉ chuyển tiền cho sinh viên khi Client bấm **"Nghiệm thu đạt yêu cầu"** cho sản phẩm nộp (Deliverable).
   * Cơ chế tự động giải ngân sau 7 ngày nếu Client không phản hồi để bảo vệ quyền lợi sinh viên.
4. **Cơ chế Phân xử Tranh chấp (Dispute Resolution)**:
   * Nếu sinh viên giao hàng sai cam kết hoặc bỏ dở: Client có quyền bấm **"Mở tranh chấp"**.
   * Tiền ký quỹ mốc đó bị đóng băng tức thì. Admin nhà trường đóng vai trò trọng tài căn cứ hợp đồng và bằng chứng nộp để ra phán quyết (hoàn tiền cho Client hoặc thanh toán theo tỷ lệ).

---

### MODULE 4: BỘ DỰ ÁN MẪU THAM KHẢO (PROJECT REFERENCE GUIDES)

#### 1. Mục tiêu & Quyết định thiết kế
* **Mục đích duy nhất**: Đóng vai trò là tài liệu hướng dẫn trực quan để người tuyển dụng lần đầu **đọc và tham khảo** cách viết bản mô tả công việc (Scope of Work), cách chia mốc nghiệm thu (Milestones) và tiêu chí bàn giao (Deliverables).
* **Quyết định loại bỏ tính năng Tự động áp dụng (No Auto-fill)**: **Không** đưa tính năng tự động ghi đè form vào hệ thống. Việc này tránh nguy cơ:
  * Ghi đè làm mất dữ liệu người dùng đang nhập dở.
  * Tình trạng đăng bài rập khuôn, người dùng quên không chỉnh sửa các trường giữ chỗ `[...]` gây hiểu lầm cho sinh viên.
* Người dùng chỉ mở lên đọc để nắm được tiêu chuẩn của một bài đăng chuyên nghiệp, sau đó tự tay nhập theo đúng nhu cầu thực tế của mình.

#### 2. Thiết kế Giao diện (Trong màn hình `Projects.tsx` - Tạo dự án mới)
* Đặt nút bấm tinh tế ngay đầu form hoặc bên cạnh tiêu đề:  
  👉 **`💡 Xem hướng dẫn & dự án mẫu tham khảo`**.
* Khi click, hiển thị **Modal Tham Khảo** (Reference Modal) với thanh điều hướng chọn theo từng ngành nghề:
  1. **Lập trình / Công nghệ**: Ví dụ xây dựng Landing Page, Viết API, Cắt HTML/CSS.
  2. **Thiết kế / Sáng tạo**: Ví dụ thiết kế Bộ nhận diện, Banner quảng cáo, UI/UX Mobile App.
  3. **Văn phòng / Dữ liệu**: Ví dụ nhập liệu Excel, Thu thập dữ liệu web, Xử lý tài liệu hợp đồng.
  4. **Nội dung / Dịch thuật**: Ví dụ dịch thuật tài liệu kỹ thuật, Viết bài chuẩn SEO.

#### 3. Cấu trúc một Dự án Mẫu Tham khảo chuẩn
Mỗi mẫu được trình bày rõ ràng, dễ đọc gồm 4 phần:
* **Tiêu đề mẫu chuẩn**: Thể hiện rõ tên công việc và phạm vi (vd: *Nhập liệu & chuẩn hóa 2.000 dòng dữ liệu sản phẩm từ file scan vào Excel*).
* **Mô tả công việc (Context & Scope)**: Nêu rõ bối cảnh, công cụ sử dụng và trách nhiệm của sinh viên.
* **Sản phẩm bàn giao cụ thể (Deliverables Checklist)**:
  * Định dạng file bàn giao (`.xlsx`, `.figma`, repo GitHub...).
  * Yêu cầu kiểm tra chất lượng (ví dụ: không lỗi chính tả, đúng định dạng ngày tháng).
* **Gợi ý phân chia Mốc nghiệm thu (Milestones Structure)**:
  * **Mốc 1 (Làm nháp / 30-50%)**: Kiểm tra 200 bản ghi đầu tiên để chốt chuẩn chất lượng (Ký quỹ 30-40%).
  * **Mốc 2 (Hoàn thiện / 100%)**: Bàn giao toàn bộ dữ liệu sạch + biên bản nghiệm thu (Ký quỹ phần còn lại).

#### 4. Trải nghiệm tương tác của Modal
* Modal có nút **"Đã hiểu & Đóng"** ở góc phải và cuối modal.
* Cho phép người dùng dễ dàng bật lên xem rồi tắt đi để tiếp tục điền form mà không làm ảnh hưởng đến bất kỳ trường dữ liệu nào đang nhập.

---

### MODULE 5: CHUẨN HÓA & CỐ ĐỊNH MENU TRÁI (SIDEBAR NAVIGATION & VISUAL HIERARCHY)

#### 1. Thực trạng & Nguyên nhân lỗi hiện tại
* **Lỗi nhảy vị trí menu (Jumping Items)**:
  * Trong `Sidebar.tsx`, logic hiện tại đang tráo đổi thứ tự động theo URL:
    ```tsx
    const items = pathname.includes('/freelancer')
      ? [...features[role].filter(f => f.path.startsWith('freelancer')), ...features[role].filter(f => !f.path.startsWith('freelancer'))]
      : features[role]
    ```
  * Hậu quả: Khi người dùng bấm vào trang Freelancer, các mục Freelancer nhảy lên đầu trang; khi sang trang Tuyển dụng/Hồ sơ, thứ tự menu bị đảo ngược trở lại làm người dùng hoa mắt, mất phương hướng.
* **Lỗi thiếu phân cấp Cha - Con (Flat List)**:
  * Toàn bộ mục menu đang hiển thị cùng 1 cấp phẳng lì, không có thụt lề, không có gom nhóm, khiến người dùng không phân biệt được mục nào là mục chính, mục nào là tính năng con bên trong.
* **Lỗi không đồng nhất màu sắc (Inconsistent Design & Palette)**:
  * Menu giữa các vai trò (Admin, Doanh nghiệp, Sinh viên) đang dùng class CSS phân tán (`freelancer.css` đè lên layout shell), màu nền, màu chữ và màu active không đồng bộ.

#### 2. Yêu cầu & Quyết định thiết kế mới

##### A. Cố định thứ tự hiển thị (Deterministic Static Order)
* **Xóa bỏ hoàn toàn** logic đảo mảng theo URL `pathname.includes('/freelancer')`.
* Thứ tự menu của từng Role được **cố định 100%** từ trên xuống dưới theo luồng nghiệp vụ logic:
  1. `Trang chủ (Dashboard)`
  2. **Nhóm Tuyển dụng / Công việc chính**
  3. **Nhóm Dự án Freelancer**
  4. **Nhóm Quản lý & Báo cáo**
  5. `Phần đáy: Thông báo, Cài đặt tài khoản`

##### B. Cấu trúc Phân cấp Trực quan (Collapsible Accordion / Indented Hierarchy)
* Hỗ trợ cấu trúc Menu 2 cấp: **Menu Cha (Parent Group)** và **Menu Con (Sub-items)**.
* **Cơ chế hiển thị (Visual Tree)**:
  * **Dropdown thu gọn / mở rộng (Collapsible)**: Menu cha có icon mũi tên `ChevronDown` (khi mở) và `ChevronRight` (khi đóng). Click vào Menu cha sẽ thu gọn/xổ ra các menu con tương ứng.
  * **Thụt đầu dòng rõ ràng (Visual Indentation)**:
    * Menu con thụt lề trái rõ rệt: `padding-left: 2.25rem` (36px).
    * Có vạch kẻ dọc mảnh (Tree guide line) hoặc chấm tròn nhỏ (bullet dot) phía trước menu con để thể hiện mối quan hệ cha - con trực quan.
  * **Tự động mở (Auto-expand on Active Route)**: Khi người dùng đang ở đường dẫn con nào (vd: `/company/freelancer/finance`), Menu cha tương ứng tự động mở ra và sáng đèn.

##### C. Đồng nhất Hệ màu & Trạng thái (Unified Design System Palette)
* Áp dụng chung một bảng màu chuẩn cho toàn bộ các Role (Admin, Doanh nghiệp, Sinh viên, Khách hàng):
  * **Màu nền Menu (Sidebar Background)**: Màu trung tính cao cấp (Light Neutral `#F8FAFC` hoặc Clean Slate), không dùng màu chói hoặc lai tạp.
  * **Trạng thái Mặc định (Default State)**: Chữ màu xám đậm dễ đọc (`text-slate-600`), icon xám (`text-slate-400`).
  * **Trạng thái Rê chuột (Hover State)**: Nền xám nhạt mịn (`hover:bg-slate-100 hover:text-slate-900`), icon sáng màu.
  * **Trạng thái Đang chọn (Active State)**:
    * Nền màu xanh thương hiệu nhạt (`bg-blue-50/80` hoặc `bg-indigo-50/80`).
    * Chữ và Icon chuyển sang màu thương hiệu đậm (`text-blue-700 font-semibold`).
    * Có vạch chỉ thị bên trái (Left Border Indicator: `border-l-4 border-blue-600`) để định vị điểm nhìn tức thì.
  * **Tiêu đề Nhóm (Section Header)**: Chữ in hoa nhỏ, nét thanh (`text-[11px] font-bold tracking-wider uppercase text-slate-400 px-3 py-2`).

---

### MODULE 6: ĐIỀU KHOẢN DỊCH VỤ & CAM KẾT PHÁP LÝ KHI ĐĂNG KÝ TÀI KHOẢN (REGISTRATION TERMS & COMPLIANCE)

#### 1. Thực trạng & Lỗ hổng hiện tại
* Tại trang Đăng ký doanh nghiệp (`RegisterCompanyPage.tsx`), phần cam kết chỉ là một dòng checkbox đơn giản, nội dung còn dính chữ cũ: *"Doanh nghiệp tuân thủ đúng quy định tiếp nhận thực tập sinh..."*.
* Người dùng không có cách nào xem được toàn văn **Điều khoản Dịch vụ nền tảng (Terms of Service)** và **Chính sách Bảo mật dữ liệu cá nhân (Privacy Policy)**.
* Chưa có chế tài pháp lý rõ ràng về: Cấm thu phí trái phép của sinh viên, cam kết thanh toán đúng hạn cho dự án Freelancer, và tuân thủ Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu sinh viên.

#### 2. Thiết kế Khu vực Điều khoản tại Form Đăng ký (`RegisterCompanyPage.tsx` / `RegisterClient`)
* **Checkbox cam kết bắt buộc**:
  ```text
  [x] Tôi đã đọc, hiểu rõ và đồng ý với [Điều khoản Dịch vụ & Tuyển dụng] và [Chính sách Bảo mật Dữ liệu Cá nhân] của Student Connect.
  ```
  * Cụm từ trong ngoặc vuông hiển thị dạng liên kết nổi bật (màu xanh thương hiệu, hover gạch chân), bấm vào sẽ mở Modal xem toàn văn.
* **Nút bấm gửi hồ sơ**: Ở trạng thái **Disabled** nếu chưa tích chọn ô checkbox này.

#### 3. Thiết kế Modal Toàn văn Điều khoản Đăng ký (Terms of Service & Privacy Modal)
Khi bấm vào liên kết, Modal mở ra với 2 Tab nội dung chi tiết:

##### Tab 1: Điều khoản Dịch vụ & Tuyển dụng (Terms of Service)
1. **Tính chính xác của Pháp nhân & Mã số thuế**:
   * Doanh nghiệp/Người thuê cam kết MST, tên công ty và người đại diện pháp luật là hoàn toàn có thật và đang hoạt động hợp pháp.
   * Mọi hành vi mạo danh pháp nhân để đăng tin sẽ bị khóa tài khoản vĩnh viễn và chuyển giao cơ quan thẩm quyền.
2. **Quy tắc Tuyển dụng Nhân đạo & Minh bạch (Nghiêm cấm Thu phí)**:
   * **Tuyệt đối nghiêm cấm thu bất kỳ khoản phí nào của sinh viên** dưới mọi hình thức (phí xét hồ sơ, phí giữ chỗ, phí cọc tài liệu/thiết bị, phí đào tạo đầu vào...).
   * Mọi vị trí tuyển dụng phải mô tả rõ ràng chế độ đãi ngộ và quyền lợi của sinh viên.
3. **Cam kết Thù lao & Thanh toán Freelancer**:
   * Đối với các công việc Freelancer: Bắt buộc thực hiện ký quỹ đảm bảo (Escrow) qua cổng thanh toán PayOS trước khi sinh viên bắt đầu làm việc.
   * Nghiêm cấm ép sinh viên làm việc ngoài nền tảng để trốn tránh trách nhiệm nghiệm thu và thanh toán.
4. **Quyền Chế tài của Nhà trường**:
   * Ban quản trị Nhà trường có toàn quyền đình chỉ, từ chối duyệt hoặc xóa tài khoản nếu nhận được phản ánh có bằng chứng về việc nợ lương, lừa đảo, hoặc xúc phạm sinh viên.

##### Tab 2: Chính sách Bảo mật & Quyền riêng tư (Privacy Policy - Nghị định 13/2023/NĐ-CP)
1. **Mục đích sử dụng dữ liệu**:
   * Thông tin sinh viên (Họ tên, MSSV, Email trường, Số điện thoại, Điểm GPA, CV) chỉ được sử dụng cho mục đích liên hệ phỏng vấn, tuyển dụng và thực hiện hợp đồng công việc.
2. **Nghiêm cấm chia sẻ dữ liệu cho bên thứ ba**:
   * Doanh nghiệp/Người thuê tuyệt đối không được sao chép, mua bán, chuyển giao hoặc sử dụng dữ liệu sinh viên cho các chiến dịch quảng cáo, telesale ngoài phạm vi nền tảng.
3. **Lưu trữ & Xóa dữ liệu**:
   * Dữ liệu sinh viên được bảo vệ theo tiêu chuẩn mã hóa dữ liệu. Doanh nghiệp có trách nhiệm tiêu hủy các bản sao lưu CV sau khi kỳ tuyển dụng kết thúc nếu không tiếp nhận ứng viên.

#### 4. Cơ chế Xác nhận Nhanh từ Modal
* Ở cuối Modal có nút: **"Tôi đã đọc và Đồng ý"**.
* Khi bấm nút này: Modal tự động đóng lại và hệ thống tự động đánh dấu tích xanh `[x]` vào ô checkbox ngoài form đăng ký, giúp trải nghiệm liền mạch và tôn trọng tính pháp lý.

---

### MODULE 7: TẠO MÃ VIETQR PAYOS TỨC THÌ & QUẢN LÝ VÒNG ĐỜI THANH TOÁN (PAYOS REALTIME QR & LIFECYCLE)

#### 1. Mục tiêu & Nguyên nhân điều chỉnh
* **Vấn đề cũ**:
  * Khi Client bấm "Tạo yêu cầu ký quỹ", backend chỉ ghi `PaymentOrder` vào database ở trạng thái `CREATING` rồi đẩy sự kiện vào hàng đợi outbox (`finance.order`).
  * Để lấy được mã QR, hệ thống yêu cầu một tiến trình chạy ngầm (`freelancer_worker.py`) liên tục quét outbox và gọi PayOS. Do môi trường dev/local chỉ chạy `uvicorn`, worker không chạy dẫn đến `qr_payload` luôn bằng `null`, frontend không hiển thị được mã QR VietQR.
* **Giải pháp chuẩn hóa**:
  * **Loại bỏ tiến trình nền cho việc sinh mã QR**: Khi bấm ký quỹ, API `POST /milestones/{milestone_id}/payment-orders` gọi trực tiếp cổng PayOS đồng bộ ngay trong request để sinh mã QR và URL thanh toán tức thì.
  * **Giữ nguyên các tiến trình nền khác**: Các tác vụ xử lý giải ngân (`finance.transfer`), chia tiền quyết toán, chi trả ngân hàng và đối soát định kỳ vẫn duy trì qua worker.
  * **Xử lý trọn vẹn các trạng thái vòng đời trên Frontend**:
    * **Đang tạo mã**: Hiển thị spinner quay (`<Spin size="large" />`) kèm thông báo *"Đang khởi tạo mã QR thanh toán PayOS..."*.
    * **Đã có mã QR**: Hiển thị khung VietQR sắc nét, mã thanh toán, số tiền và hướng dẫn quét mã bằng app ngân hàng bất kỳ.
    * **Tự động nhận diện Đã thanh toán (PAID)**: Frontend tự động poll mỗi 3 giây; backend kiểm tra PayOS trong thời gian thực. Khi khách hàng quét mã xong trên điện thoại, giao diện tự động nhảy sang thẻ xanh xác nhận thành công mà không cần F5.
    * **Quá hạn thanh toán (EXPIRED - 15 phút)**: Hiển thị thông báo đỏ cảnh báo mã QR đã hết hạn bảo mật, kèm nút *"Tạo lại yêu cầu ký quỹ"* để tạo mã mới an toàn.
    * **Đã hủy (CANCELLED)**: Hiển thị thông báo đơn đã được hủy theo yêu cầu.

---

### BẢNG TỔNG HỢP NHIỆM VỤ TRIỂN KHAI (IMPLEMENTATION CHECKLIST)

| STT | Phân hệ | Nhiệm vụ kỹ thuật | File tác động |
| :---: | :--- | :--- | :--- |
| **1** | **Skill Tagging** | Chuyển `SkillPicker` sang `Creatable Tag Input`, cho phép gõ text tự do; Backend tự động upsert vào `skills` mà không qua Admin. | `frontend/.../SkillPicker.tsx`<br>`backend/.../freelance_project_service.py` |
| **2** | **Bank Select** | Cung cấp danh mục VietQR; đổi input `bank_bin` thành Searchable Dropdown có Logo & Tên viết tắt, auto-map BIN ngầm. | `frontend/.../Accounts.tsx`<br>`backend/.../freelancer_finance.py` |
| **3** | **Terms Modal** | Tạo Modal điều khoản ký quỹ/tranh chấp khi tạo dự án lần đầu, chặn click nút cho đến khi cuộn xuống đáy. | `frontend/.../Projects.tsx`<br>`frontend/.../EscrowTermsModal.tsx` |
| **4** | **Project Guides** | Thêm nút "💡 Xem dự án mẫu tham khảo", mở Modal hiển thị các mẫu chuẩn (Lập trình, Thiết kế, Dữ liệu, Nội dung) chỉ để đọc tham khảo. | `frontend/.../projectGuides.ts`<br>`frontend/.../Projects.tsx` |
| **5** | **Sidebar Hierarchy** | Cố định thứ tự menu (xóa đảo mảng động), thiết kế Menu cha - con có Accordion thu gọn/mở rộng, thụt lề rõ ràng, đồng nhất bảng màu chuẩn. | `frontend/.../Sidebar.tsx`<br>`frontend/.../navigation.ts`<br>`frontend/src/layouts/AppShell.css` |
| **6** | **Register Terms** | Thiết kế Modal toàn văn Điều khoản Dịch vụ & Bảo vệ dữ liệu (Nghị định 13) có 2 Tab, liên kết mở trực tiếp từ form Đăng ký Doanh nghiệp / Client. | `frontend/.../RegisterCompanyPage.tsx`<br>`frontend/.../RegisterTermsModal.tsx` |
| **7** | **PayOS Realtime QR** | Sinh mã QR VietQR đồng bộ ngay khi bấm ký quỹ (bỏ background worker cho QR); xử lý đầy đủ các trạng thái Frontend: đang tải (spinner), đã thanh toán (auto update), hết hạn (cảnh báo 15 phút). | `backend/.../freelancer_collection_service.py`<br>`backend/.../freelancer_finance.py`<br>`frontend/.../Contracts.tsx`<br>`frontend/.../hooks.ts` |
