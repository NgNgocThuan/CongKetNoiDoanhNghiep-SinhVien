# HƯỚNG DẪN DÀNH CHO CLAUDE CODE (CLAUDE.MD)

Tài liệu này là cẩm nang hướng dẫn thực thi dành cho Claude khi làm việc với dự án **Student Connect** (Hệ thống kết nối việc làm sinh viên, tuyển dụng và dự án Freelancer có bảo chứng tài chính).

---

## 1. Bản đồ Kiến trúc & Tài liệu Tham chiếu Cốt lõi

Trước khi thực hiện bất kỳ thay đổi nào về mã nguồn, **BẮT BUỘC** đọc kỹ tài liệu kiến trúc tổng thể:
- **Tài liệu kiến trúc chính thức:** `docs/SYSTEM_ARCHITECTURE_REVIEW.md` (Đặc biệt xem Mục 2, 6, 7, 8, 14, 19 và Mục 21).
- **Đặc tả Backend Freelancer:** `backend/docs/FREELANCER_BACKEND_SPEC_PAYOS.md`.
- **Báo cáo kiểm thử thực tế & Lỗi giao diện:** `../../BAO_CAO_TEST_LUONG_FREELANCER.md`.

---

## 2. Các Lệnh Vận hành & Kiểm thử (Commands)

### A. Backend (FastAPI + SQLAlchemy + MariaDB)
- **Thư mục làm việc:** `backend/`
- **Môi trường Python:** Python 3.11+
- **Chạy server phát triển:**
  ```bash
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Chạy Database Migration (Alembic):**
  ```bash
  python -m alembic -c alembic.ini upgrade head
  ```
- **Chạy Unit/Integration Tests:**
  ```bash
  pytest tests/freelancer/
  ```

### B. Frontend (React 18 + TypeScript + Vite + Tailwind CSS)
- **Thư mục làm việc:** `frontend/`
- **Cài đặt package:** `npm install`
- **Chạy frontend dev server:**
  ```bash
  npm run dev
  ```
- **Kiểm tra TypeScript & Lint:**
  ```bash
  npm run build
  ```
- **Chạy E2E Tests (Playwright):**
  ```bash
  node scripts/run-full-flow-test.mjs
  ```

---

## 3. Các Nguyên tắc Nghiệp vụ Bất di bất dịch (Ground Rules)

1. **Tuyệt đối không dùng SMS OTP:** Toàn bộ mã OTP được gửi qua Email thông qua giao thức SMTP (chi phí 0 đồng).
2. **Không thu thập CCCD cá nhân và không eKYC khuôn mặt:** Để tuân thủ Nghị định 13/2023/NĐ-CP và tránh rào cản người dùng.
3. **Phân hệ Tuyển dụng là Job Board tinh gọn:** Bỏ hoàn toàn phần báo cáo thực tập định kỳ, điểm số và sự tham gia của Giảng viên. Chỉ làm luồng: Đăng tin -> Duyệt tin -> Ứng tuyển với CV snapshot -> Mời phỏng vấn / Trúng tuyển. Tuyệt đối không giữ tiền ký quỹ trong luồng tuyển dụng.
4. **Phân hệ Freelancer giữ tiền 100% qua payOS:** Doanh nghiệp thường phải nộp đủ 100% tiền ký quỹ vào hệ thống trước khi sinh viên làm việc. Chỉ Đối tác MOU mới được cấp vốn linh hoạt theo từng Milestone.
5. **Ký số MOU theo luồng Hybrid (Không dùng API bên thứ ba):**
   - Hệ thống sinh file PDF MOU có sẵn chữ ký số của Trường.
   - Doanh nghiệp tải về máy tính tự ký offline (Adobe Acrobat / Foxit / USB Token).
   - Doanh nghiệp upload file đã ký lên web.
   - Backend sử dụng thư viện `pyHanko` để tự động kiểm tra tính hợp lệ của 2 chữ ký số X.509 và kích hoạt tài khoản `Verified` / `OFFICIAL_PARTNER` trong 1 giây mà không cần Admin duyệt tay.

---

## 4. Danh mục 4 Nhiệm vụ Trọng tâm cần Thực thi

### Nhiệm vụ 1: Triển khai Xác minh Doanh nghiệp 2 bước (Verification)
- **Backend:**
  - Viết Alembic migration tạo bảng `company_verifications` theo đặc tả tại **Mục 21.1 của `docs/SYSTEM_ARCHITECTURE_REVIEW.md`**.
  - Xây dựng Router `company_verification` với các endpoints: `request-email-otp`, `verify-email-otp`, `submit-legal-docs`.
  - Xây dựng hàng đợi Admin `GET /api/v1/admin/verifications` kèm link tra cứu nhanh sang `dangkykinhdoanh.gov.vn`.
- **Frontend:**
  - Nâng cấp giao diện trang Onboarding của Doanh nghiệp: Thanh tiến trình 2 bước trực quan, form nhập OTP email và ô tải file Giấy phép kinh doanh (kèm xem trước ảnh).

### Nhiệm vụ 2: Triển khai Xác minh Đối tác MOU luồng Hybrid
- **Backend:**
  - Tạo bảng `mou_agreements` theo **Mục 21.2 của `docs/SYSTEM_ARCHITECTURE_REVIEW.md`**.
  - Cài đặt thư viện `pyHanko>=0.20.0` và `cryptography` vào `backend/requirements.txt`.
  - Viết hàm `validate_mou_hybrid_file()`: Kiểm tra file có đủ 2 chữ ký số, tính toàn vẹn (intact) và đối soát Mã số thuế trong chứng thư số X.509 với doanh nghiệp.
  - Xây dựng API: `GET /template/paper` (mẫu giấy), `POST /submit-paper-scan` (upload giấy scan), `GET /template/hybrid-signed` (tải file trường đã ký), `POST /upload-hybrid-signed` (upload file ký số và kích hoạt tự động).
- **Frontend:**
  - Xây dựng Modal "Nâng cấp Đối tác MOU": Cho phép chọn giữa Phương án 1 (Ký giấy in scan) và Phương án 2 (Ký số Hybrid).
  - Nhúng PDF Viewer để doanh nghiệp xem trực tiếp văn bản MOU trên màn hình web.

### Nhiệm vụ 3: Hoàn thiện Phân hệ Tuyển dụng việc làm & Thực tập sinh (Job Board)
- **Backend:**
  - Tạo bảng `jobs` và `job_applications` theo **Mục 21.3 của `docs/SYSTEM_ARCHITECTURE_REVIEW.md`**.
  - Xây dựng Router quản lý tin tuyển dụng và nộp CV. MOU được Auto-approve (`is_featured = 1`), Doanh nghiệp thường phải qua Admin duyệt nội dung.
- **Frontend:**
  - Trang danh sách việc làm công khai cho Sinh viên: Tìm kiếm, lọc theo ngành nghề, nhãn huy hiệu "Đối tác MOU" nổi bật trên đầu trang.
  - Dashboard Doanh nghiệp quản lý ứng viên: Xem CV snapshot, nút bấm "Mời phỏng vấn" (mở modal nhập thời gian/link online), chuyển trạng thái "Nhận việc" / "Từ chối".

### Nhiệm vụ 4: Nâng cấp Giao diện & Sửa lỗi Toàn hệ thống (UI Polish & Bugfix)
- **Fix lỗi Modal bị kẹt (HTTP 409):** Rà soát các component Radix Dialog trong `frontend/src/features/freelancer/`, bắt mã lỗi 409 để hiển thị Toast đỏ thông báo và đóng/reset modal, không để bị kẹt spinner.
- **Mock payOS Local:** Trong router thanh toán, bổ sung endpoint mock webhook thành công khi `PAYOS_COLLECTION_ENABLED=false` để lập trình viên có thể test toàn bộ luồng tiền mà không bị lỗi 503 cấu hình payOS.
- **Toast thông báo thống nhất:** Tích hợp bộ interceptor thông báo lỗi tự động cho Axios/React Query để hiển thị lỗi thân thiện tới người dùng.

---

## 5. Phong cách Code & Tiêu chuẩn Kỹ thuật
- **Backend:** Tuân thủ cấu trúc FastAPI hiện tại (`routers/`, `services/`, `models/`, `schemas/`). Luôn sử dụng type hints đầy đủ, xử lý ngoại lệ bằng `HTTPException` có mã lỗi rõ ràng.
- **Frontend:** Sử dụng functional components, React Hooks, TanStack Query (React Query), Tailwind CSS. Thiết kế responsive, sạch sẽ, tone màu hiện đại.

