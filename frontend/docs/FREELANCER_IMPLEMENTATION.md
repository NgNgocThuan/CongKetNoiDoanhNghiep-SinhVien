# Frontend Freelancer — bản local để xem và kiểm thử

**Cập nhật đăng công việc ngày 10/11/2026:** [cấu trúc mới và migration 0005](../../backend/docs/freelancer/PROJECT_POSTING_0005.md). Biểu mẫu đã có danh mục, hai hạn, trình độ, tài liệu tham khảo; bản nháp chỉ cần tên. Cần nâng schema backend lên 0005 trước khi chạy bản code mới.

Cập nhật rà soát ngày 10/11/2026: [các lỗi đã sửa, kết quả kiểm thử và cách chạy ở cổng 9000](UI_REVIEW_20261110.md).

Ngày 08/11/2026. Triển khai dựa trên 21 màn hình trong hai ZIP `(3)` và `(4)` người dùng cung cấp. Code cùng backend ở nhánh `fix/freelancer-backend-a-d-local-20261107`, worktree:

```text
B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c
```

Chưa commit/push/merge. Các chỉnh sửa chưa commit trong thư mục dự án gốc được giữ nguyên. Không chạy migration lên database dự án hoặc gửi giao dịch tiền thật trong đợt frontend này.

## 1. Mở đúng bản

```powershell
code B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c
```

Backend và frontend cần chạy từ **cùng worktree**. Nếu chạy backend cũ ở main, các API Freelancer mới sẽ chưa có.

Sau khi cấu hình backend với database được phép sử dụng và đã có migration đến 0004:

```powershell
cd B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở terminal khác:

```powershell
cd B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c\frontend
npm run dev
```

Máy mới cần cài dependencies theo package-lock bằng `npm ci` trước. Máy hiện tại dùng lại node_modules qua junction local; junction không thuộc source phát hành.

Frontend dùng biến môi trường hiện có. Nếu cần đổi backend, tạo/sửa `.env.local` trong `frontend`:

```dotenv
VITE_API_BASE_URL=/api/v1
BACKEND_PROXY_TARGET=http://127.0.0.1:8000
```

Mở `http://127.0.0.1:5173`. Nếu cổng đang có bản frontend khác, dùng `npm run dev -- --port 5188` và mở cổng 5188. Không đưa khóa payOS vào biến `VITE_*`; khóa chỉ nằm ở `.env` backend.

## 2. Các điểm vào giao diện

| Người dùng | Đường dẫn sau đăng nhập |
|---|---|
| Người thuê cá nhân | `/client/freelancer` |
| Doanh nghiệp | `/company/freelancer` |
| Sinh viên | `/student/freelancer` |
| Admin | `/admin/freelancer` |

Menu Freelancer được thêm vào khung trang hiện có. Trong khu vực Freelancer, các mục Freelancer được đưa lên trước để dễ truy cập; khu vực tuyển dụng, CV, thực tập và quản trị cũ vẫn có đường dẫn riêng.

- Đăng ký người thuê cá nhân: `/register-client`.
- Doanh nghiệp đang chờ duyệt, chưa đăng nhập thông thường được: `/onboarding`.
- Trang `/onboarding` dùng token hạn chế 15 phút trong bộ nhớ trang; không lưu token đó làm phiên đăng nhập/refresh thông thường.
- Người thuê/doanh nghiệp đang hoạt động hoàn thiện liên hệ, pháp nhân và MOU qua `freelancer/onboarding` trong không gian của mình.

## 3. Đối chiếu các bản thiết kế

Các đường dẫn tương đối dưới đây đặt sau `/{role}/freelancer`, với role là client/company/student/admin phù hợp.

| Thiết kế | Giao diện đã nối |
|---|---|
| H01 | Tổng quan: `/`; số liệu thật theo phạm vi tài khoản, việc đang làm và liên kết xử lý |
| H02 | `/projects`: dự án người thuê; tìm theo tên trong trang đang xem, phân trang |
| H03 | `/projects/new`, `/projects/:id/edit`: một/nhiều mốc, kỹ năng, ngân sách tổng, lưu nháp/gửi duyệt |
| H04 | `/projects/:id`: thông tin, ứng viên/CV, chọn sinh viên và hợp đồng riêng, mở rộng/đóng tuyển |
| S01 | `/projects` dưới student: tìm dự án được phép xem |
| S02 | `/projects/:id` dưới student: chi tiết, đính kèm CV hợp lệ, gửi đề xuất |
| S03 | `/work`: hợp đồng và tab đơn ứng tuyển; rút đơn khi được phép |
| W01 | `/contracts/:id`: mốc, điều khoản/phiên bản, ký quỹ/thanh toán và đánh giá |
| W03 | `/milestones/:id`: các lần bàn giao, tệp, yêu cầu sửa, nghiệm thu, trạng thái tiền |
| W07 | Khu vực hủy/thỏa thuận trong `/milestones/:id`: đề xuất phân chia, xác nhận/từ chối/rút/thực hiện |
| W08 | `/disputes/:id`: bằng chứng, hạn, đề nghị rút có hai bên xác nhận, kết quả được phép xem |
| G03 | `/banks`: khai báo, theo dõi xác minh và ngừng sử dụng tài khoản nhận tiền |
| W05 | `/payments/:id`: QR/link payOS, kiểm tra lại, hủy yêu cầu và các kết quả chờ/thành công/cần kiểm tra |
| A01 | `/` dưới admin: số lượng hồ sơ chờ và điểm vào các hàng đợi |
| A02 | `/admin/business`: hồ sơ pháp nhân/MOU, chứng cứ, duyệt/từ chối/bổ sung/thu hồi, đình chỉ/khôi phục |
| A03 | `/admin/projects`: danh sách dự án và yêu cầu mở rộng; mở hồ sơ dự án để thẩm định |
| A04 | `/admin/banks`: duyệt ngân hàng, ghi nhận đối chiếu chứng cứ và lý do |
| A05 | `/admin/receipts`: khoản thu cần kiểm tra và giao dịch thực nhận; phân bổ/hoàn khi đủ điều kiện |
| A06 | `/admin/transfers`, `/settlements/:id`: theo dõi từng nhánh giải ngân/hoàn, yêu cầu tra cứu kết quả |
| A08 | `/admin/disputes` → `/disputes/:id`: phân công, đề xuất/duyệt/thực hiện quyết định theo quyền |
| A09 | `/admin/reconciliation`: các lần đối soát, sổ cái, tác vụ lịch/outbox, đưa tác vụ lỗi lại vào hàng đợi |

Các điểm nối bổ sung để quy trình chạy được: `/milestones/:id/fund`, `/finance` (tiền theo hợp đồng), `/admin/treasury` (nguồn tiền chi, chứng từ và duyệt bởi Admin thứ hai), đăng ký CLIENT và hoàn thiện hồ sơ.

Admin có thể mở số tài khoản đầy đủ để đối chiếu sau khi nhập lý do. Lượt xem được ghi audit, phản hồi không cache; dữ liệu chỉ nằm trong trạng thái trang đang mở và có nút ẩn. Các danh sách và màn hình người dùng vẫn che số tài khoản, không trả ciphertext.

Các khối tĩnh của mẫu được thay bằng dữ liệu API hoặc trạng thái chưa có dữ liệu. Những chỉ số như điểm AI phù hợp, tỷ lệ thành công hay biểu đồ chưa có nguồn dữ liệu không được hiển thị bằng số mẫu. Hồ sơ cần xem tài liệu sử dụng tải tệp có xác thực. Tài liệu gốc được giữ tại `design-reference/freelancer`, chỉ làm tham chiếu thiết kế.

## 4. Các quy tắc đã giữ trên frontend

- Một dự án có nhiều sinh viên, mỗi người có hợp đồng, ký quỹ và quyết toán riêng.
- Dự án nhỏ hỗ trợ một mốc; không ép tạo nhiều giai đoạn. Ký quỹ toàn bộ hợp đồng vẫn theo từng yêu cầu cho từng mốc, không tự gộp nhiều mốc vào một đơn thu.
- Ngân sách phân bổ không được hiển thị như tiền đã nhận. Số tiền dùng chuỗi số nguyên VND; hiển thị bằng BigInt để giữ chính xác cả số lớn.
- Gửi đề nghị điều khoản đã ghi nhận sự chấp nhận của người gửi; bên còn lại xác nhận để có hiệu lực. Nội dung phiên bản, phí và điều kiện được hiển thị trước xác nhận.
- Nghiệm thu chuyển sang chuẩn bị/quá trình quyết toán, không tự đánh dấu đã trả tiền.
- Hộp xác nhận nghiệm thu hiển thị tiền gốc, phí và thực nhận lấy từ điều khoản của đúng mốc trên backend; chưa lấy được số liệu thì chưa cho xác nhận.
- Chỉ trạng thái backend xác minh được dùng để thông báo nhận tiền/chi tiền thành công. Không tin `status`, `code`, `cancel` từ query string payOS.
- Mỗi command dùng Idempotency-Key. Bấm lặp khi đang gửi dùng cùng một request; lỗi chưa rõ kết quả giữ key để thử lại cùng yêu cầu. Phản hồi từ phiên tài khoản cũ không được chuyển vào phiên mới.
- Admin tra cứu lại giao dịch không phát lệnh chi mới. Không có nút xác nhận tiền đã chi bằng tay, sửa ledger hoặc rút tiền từ ví.
- Tài liệu chờ scan hoặc không còn khả dụng chưa được sử dụng để nộp hồ sơ/bàn giao.
- Quyết định/chứng từ cần hai Admin được kiểm tra ở backend; giao diện cũng không đưa nút tự duyệt cho người đề xuất.
- Frontend được thêm vai trò CLIENT; các route Admin riêng chỉ đăng ký trong cây route Admin, backend vẫn kiểm tra quyền độc lập.

## 5. Return/cancel URL của payOS

Sau khi triển khai frontend, đặt trong `.env` backend, thay tên miền bằng tên miền thực:

```dotenv
PAYOS_RETURN_URL=https://app.ten-mien-cua-ban.vn/payments/return
PAYOS_CANCEL_URL=https://app.ten-mien-cua-ban.vn/payments/cancel
```

Frontend đọc `orderCode`, yêu cầu backend tìm đơn thuộc quyền truy cập, rồi mở trang trạng thái của đơn. Nếu phiên đăng nhập đã hết hạn, người dùng đăng nhập lại và được đưa về luồng xem kết quả. Không xác nhận đã thanh toán chỉ từ URL.

Webhook, khóa kênh thu/chi, nguồn tiền chi và worker vẫn cấu hình theo [hướng dẫn payOS backend](../../backend/docs/freelancer/PAYOS_IMPLEMENTATION.md). Trước tiền thật cần xác minh tài khoản thực và phạm vi thử; đợt này không gửi lệnh tiền thật.

## 6. Kiểm thử

Các lệnh từ `frontend`:

```powershell
npm run typecheck
npm run lint
npm test
npm run build
npm run test:e2e:freelancer
```

Bộ browser test dùng cổng riêng 5188 và HTTP fixture trong tests. Không thêm chế độ giả lập thanh toán vào sản phẩm. Có kiểm tra desktop/mobile, một mốc, ứng tuyển, nghiệm thu, giả mạo kết quả payOS, quyền Admin, xác minh ngân hàng và ngăn tự duyệt chứng từ.

Đã chạy thêm một kịch bản với backend thật trên SQLite local riêng: đăng nhập CLIENT → tạo dự án một mốc → gửi duyệt → Admin duyệt → sinh viên ứng tuyển → người thuê chọn sinh viên → soạn/gửi phiên bản → sinh viên chấp nhận → hợp đồng có hiệu lực với đúng một mốc chưa ký quỹ. Các cờ thu/chi đều tắt trong kịch bản này.

Muốn chạy lại kịch bản đó, tạo database mới bằng `e2e/seed-freelancer-backend.py` từ backend. Script không dùng DATABASE_URL dự án mà tạo file `tmp/student_connect_ui_test_<uuid>.sqlite`; metadata kết nối nằm trong `tmp/freelancer-ui-backend.json`. Chạy backend riêng trên 18765 với database mới, `DEBUG=false` và cả ba cờ tài chính/thu/chi bằng `false`. Frontend test đặt `BACKEND_PROXY_TARGET=http://127.0.0.1:18765`, `FREELANCER_LIVE_TEST=1`, rồi chạy `npm run test:e2e:freelancer`.

Mỗi lần thử lại nên tạo database mới để không tích lũy dự án vượt hạn mức tài khoản. Không seed dữ liệu thử vào DB nhóm. Chứng chỉ/kênh SMS, scan tệp và payOS thật cần được cấu hình khi kiểm thử các bước có dịch vụ bên ngoài.

Kết quả đã kiểm chứng: **67 unit test frontend**, **9 browser test**, **1 kịch bản backend thật**, **413 test backend gồm 11 MariaDB**. TypeScript, ESLint, Ruff và production build đạt. Một số thư viện có cảnh báo deprecation/jsdom như baseline.

## 7. Ảnh xem trước

- [Hợp đồng trên backend local thật](freelancer-previews/contract-live.png).
- [Giao diện mobile](freelancer-previews/mobile.png).
- [Đối soát Admin](freelancer-previews/admin.png).

Ảnh từ browser fixture dùng dữ liệu kiểm thử để xem bố cục; không phải chứng cứ giao dịch tiền thật.
