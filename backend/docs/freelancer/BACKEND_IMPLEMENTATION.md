# Backend Freelancer A–D — bản triển khai local

**Cập nhật đăng việc ngày 10/11/2026:** [PROJECT_POSTING_0005.md](PROJECT_POSTING_0005.md). Migration mới nhất là **0005**; cần nâng schema trước khi chạy bản code mới.

**Bổ sung F/payOS:** xem [PAYOS_IMPLEMENTATION.md](PAYOS_IMPLEMENTATION.md). Bộ xử lý tài chính, API thu/chi, ledger, webhook, nguồn vốn có chứng cứ và migration **0004** đã được thêm cùng worktree. Các mục A–D và số liệu 373 test bên dưới mô tả mốc trước khi bổ sung F; hướng dẫn mới là tài liệu vận hành tài chính hiện tại. Chưa gọi tiền thật hoặc migrate DB dự án.

Ngày 07/11/2026. Tiếp tục đặc tả đã duyệt và các bản sửa của Khôi/Quang; bổ sung phần Phong/Việt Anh. Đây là backend nghiệp vụ và các điểm tích hợp, không phải xác nhận nền tảng đã chạy thu/chi tiền thật.

## 1. Mở đúng bản để xem

- Nhánh: `fix/freelancer-backend-a-d-local-20261107`.
- Worktree: `B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c`.
- Tên thư mục giữ nguyên từ lượt sửa A/C; phạm vi hiện tại đã mở rộng thành A–D.
- Chưa commit/push/merge main; chưa migrate database dự án. Các thay đổi trong thư mục gốc được giữ nguyên.

```powershell
code B:\project\student-connect\student-connect\tmp\fix-freelancer-a-c
```

Trong worktree này, backend nằm ở `backend`. Không checkout nhánh đó ở thư mục gốc vì nó đã được mở trong worktree riêng.

## 2. Những phần đã triển khai

| Nhóm | Backend đã có |
|---|---|
| A — Khôi | Đăng ký CLIENT, profile, token onboarding riêng, đổi liên hệ có kiểm tra mật khẩu, OTP lưu DB/attempt/cooldown/rate limit theo user/target/IP; nộp/duyệt/từ chối/yêu cầu bổ sung hồ sơ pháp nhân; MOU Admin tạo/duyệt/thu hồi; upload/checksum/scan queue/download đúng quyền; limits và đình chỉ/khôi phục doanh nghiệp. |
| B — Phong | CRUD nháp và proposal/skills, gửi duyệt, lịch sử review, visibility, ứng tuyển/shortlist/rút/từ chối; chọn người và tạo hợp đồng cùng TX, replay; allocation và trần người/ngân sách; đóng/mở tuyển; đề nghị tăng trần qua Admin; danh sách hợp đồng đúng quyền và tổng hợp allocation. |
| C — Quang | Contract/version/hash/offer/accept/decline/withdraw/expiry; snapshot chính sách/danh tính/phí; terms bất biến; start qua finance guard; bàn giao và revision có lịch sử; acceptance/auto-accept cùng TX finance; hủy nháp; closure nhiều hợp đồng; đánh giá hai bên và Admin ẩn có audit. |
| D — Việt Anh | Cancellation proposals/hash/xác nhận; căn cứ hủy một phía theo điều khoản đã ký; dispute/active guard/evidence/deadline; rút tranh chấp có hai bên xác nhận và khôi phục thời gian review; holds độc lập; quyết định phiên bản, SPLIT hai Admin; execution qua finance; callback hoàn tất sau settlement thành công; worker lease/retry/DEAD và API theo dõi/retry/audit. |

Các luồng gọi finance vẫn từ chối rõ khi phần F chưa sẵn sàng. Không có đường API đánh dấu giao dịch chi tiền thật thành công bằng tay và không có endpoint giả lập thanh toán.

## 3. Kiến trúc và transaction

- Giữ FastAPI → service/coordinator → SQLAlchemy, MariaDB 10.11 và Alembic. Router chỉ nhận input, xác thực, gọi service và trả schema.
- `run_command` sở hữu commit/rollback cho toàn lệnh; retry giới hạn khi MariaDB báo deadlock/lock timeout. Hàm `*_in_tx` không commit và không gọi dịch vụ mạng.
- Chọn ứng viên giữ parent project lock, sau đó đọc **current rows** để kiểm tra số hợp đồng và tổng allocation. Không dùng tổng từ snapshot cũ của InnoDB REPEATABLE READ sau khi đã chờ khóa.
- Cùng key/body trả kết quả cũ sau khi kiểm tra quyền hiện tại; khác key/body/resource conflict. Các lệnh mới chọn người, đề xuất hủy, mở tranh chấp và tạo quyết định dùng `Idempotency-Key`.
- Acceptance của C đã dùng command replay; header chuẩn là `Idempotency-Key`. Các endpoint C lịch sử còn cho phép không truyền header, nhưng client mới phải truyền cho các command có nhiều tác động.
- Một dự án có nhiều sinh viên; mỗi sinh viên chỉ thấy hợp đồng, báo giá, file và tài chính của chính mình. Allocation là ngân sách thương lượng, không phải tiền đã nhận.
- Lịch sử version và delivery được phân trang ở SQL. Milestones của một phiên bản bị giới hạn 100; hai đánh giá của hợp đồng là collection có giới hạn.

## 4. Chính sách mặc định

Đây là giá trị khởi tạo của Student Connect, có thể sửa bằng API Admin; không phải các hạn mức do Upwork/Freelancer hoặc payOS quy định.

| Cấu hình | Mặc định |
|---|---:|
| Dự án nhỏ phải FULL | ≤ 2.000.000đ |
| CLIENT: số dự án mở / trần một dự án | 3 / 20.000.000đ |
| COMPANY VERIFIED: số dự án mở / trần một dự án / trần cấp vốn ngày | 5 / 20.000.000đ / 50.000.000đ |
| OFFICIAL_PARTNER: các trần tương ứng | 20 / 100.000.000đ / 200.000.000đ |
| COMPANY VERIFIED phải FULL | Có; đối tác theo policy và ngưỡng dự án nhỏ |
| Thời gian nộp bằng chứng | 7 ngày |
| PAYOUT/REFUND cần Admin thứ hai | Từ 5.000.000đ |
| SPLIT cần Admin thứ hai | Luôn luôn |
| Review mặc định cho hợp đồng mới | 14 ngày |
| Offer mặc định | 7 ngày |
| Grace mặc định | 3 ngày |
| Số lần yêu cầu sửa mặc định | 3 |
| Phí nền tảng | 500 bp, tức 5% |
| Hủy một phía theo mặc định | Tắt; chỉ dùng khi điều khoản EFFECTIVE cho phép rõ |

`GET/PUT /api/v1/admin/freelancer-policy` đọc/sửa policy. PUT yêu cầu `expected_revision` và `reason`; thay đổi có audit. Mỗi contract version lưu `policy_revision` và các giá trị đã áp dụng. Thay policy không tự sửa hợp đồng đã ký; phí được giữ theo bản hiệu lực của hợp đồng và không nhận mức phí tự giảm từ frontend. COMPANY có thể có override riêng có audit.

Trần cấp vốn ngày được cung cấp cho phần F để kiểm tra/reserve; module A/B không tự tạo tiền hoặc thay writer hạn mức tài chính. Giới hạn số dự án và ngân sách được kiểm tra ở các command nộp/duyệt/chọn người.

## 5. Schema và migration mới

Giữ nguyên revision `0002`. Revision **`0003`** bổ sung:

| Bảng | Mục đích |
|---|---|
| `freelancer_policies` | Policy hiện tại, revision, người cập nhật; lịch sử được ghi audit append-only. |
| `otp_rate_buckets` | Counter bền vững theo scope HMAC cho OTP, onboarding login và đăng ký; không lưu IP/OTP thô. |
| `dispute_withdrawals` | Người yêu cầu, nội dung/hash, người phía còn lại xác nhận và thời điểm; ngăn tự xác nhận. |
| `project_expansions` | Đề nghị tăng budget/max_students, trạng thái kiểm duyệt, người duyệt và lý do; tiền/ngân sách có cột riêng. |

Tổng 90 bảng ứng dụng. Downgrade `0003` từ chối khi đã có dữ liệu runtime. SQL trong `database/freelancer_schema.sql` chỉ là bản tham chiếu; không dùng nó để thay Alembic.

Đã thử migration trên DB disposable, không áp dụng lên DB local đang dùng hoặc DB nhóm. Chỉ chạy `alembic upgrade head` trên database được xác nhận sau khi review/backup theo quy trình dự án.

## 6. SMS, email và quét file

### OTP

- `FREELANCER_OTP_SECRET` cần secret ngẫu nhiên ít nhất 32 ký tự, cấu hình ngoài Git.
- EMAIL dùng SMTP hiện có, gửi sau commit challenge. Chưa có SMTP thì từ chối; không dùng cơ chế dev email để giả gửi OTP thành công.
- PHONE dùng adapter gateway được cấu hình. Challenge chỉ lưu HMAC gắn user/target/nonce; mã thô chỉ tồn tại trong RAM để gửi đi.
- Nhập sai được lưu số lần thử trước khi trả lỗi. Mã hết hạn/đã dùng/bị thay thế/bị khóa không dùng lại được. Đổi liên hệ xóa xác minh tương ứng và vô hiệu challenge cũ.
- Token onboarding có `type=onboarding`, không dùng được ở router cũ yêu cầu access token. Chờ duyệt không được tự mở quyền tuyển dụng cũ.

### Hợp đồng gateway

Đây là protocol adapter của dự án, **không phải endpoint của một nhà cung cấp SMS/antivirus cụ thể**. Nhà cung cấp được chọn sau cần mapping vào protocol này hoặc thay adapter tương ứng. Không thể dán một URL bất kỳ rồi mặc định tương thích.

| Adapter | Request | Response thành công |
|---|---|---|
| SMS | HTTPS POST, Bearer token, `Idempotency-Key`; JSON `to`, `code`, `purpose` | JSON `accepted: true` |
| Scan | HTTPS POST, Bearer token; multipart `file`, trường `sha256` | JSON `sha256` do bộ quét tính lại, `verdict: CLEAN` hoặc `REJECTED` |

HTTP chỉ được dùng với localhost ở môi trường development; không tự follow redirect. Adapter có timeout và không lưu response chứa credential/mã OTP vào audit. File lỗi checksum hoặc scanner chưa cấu hình không được tự đánh CLEAN.

Các biến cấu hình mẫu trong `.env.example`:

```dotenv
FREELANCER_OTP_SECRET=
FREELANCER_SMS_GATEWAY_URL=
FREELANCER_SMS_GATEWAY_TOKEN=
FREELANCER_SCAN_GATEWAY_URL=
FREELANCER_SCAN_GATEWAY_TOKEN=
FREELANCER_WORKER_LEASE_SECONDS=120
FREELANCER_WORKER_MAX_ATTEMPTS=12
```

Upload trả file `PENDING` và tạo scan outbox. Chỉ file CLEAN/AVAILABLE mới được nộp làm hồ sơ/bằng chứng hoặc tải. Quyền đọc xét liên kết business/MOU, deliverable, evidence hoặc CV snapshot; biết file_id không tạo quyền đọc. Không sửa nội dung file đã dùng.

Email thông báo có outbox payload bền vững; SMTP chạy ngoài TX và có thể retry. Email/SMS không được giả định là exactly-once khi nhà cung cấp chưa xác nhận kết quả mạng.

## 7. Chạy worker

Sau khi cấu hình DB local và áp dụng migration được phép, chạy từ backend:

```powershell
python -m scripts.freelancer_worker --once
python -m scripts.freelancer_worker --interval 3
```

Không chạy worker này vào DB nhóm/production từ checkout chưa review. Worker: payOS I/O is now enabled only by explicit configuration; see PAYOS_IMPLEMENTATION.md. No automatic migration/seed.

Worker claim lease ngắn và commit trước khi gọi mạng; lease hết hạn có thể được nhận lại, lỗi có backoff/RETRY/DEAD. Xem/requeue qua `/admin/freelancer/jobs`, `/admin/freelancer/outbox`; thao tác retry cần Admin và lý do. Retry không thay thế đối soát tài chính của phần F.

Auto-accept kiểm tra lại bản nộp hiện tại, status, deadline, hold/dispute và gọi cùng acceptance + finance port trong một TX. Finance lỗi thì review/milestone rollback, job retry. MOU hết hạn chỉ thay hạng/policy, không tự hủy hợp đồng hoặc tạo hold.

## 8. Điểm nối phần F của Thuận

1. Giữ `FinancePort`/`UnavailableFinancePort`. F triển khai `assert_can_start_in_tx`, `assert_disputable_in_tx` và ba hàm chuẩn bị settlement theo source review/decision/cancellation.
2. F đọc terms từ milestone effective terms, policy/limits tương ứng; kiểm tra vốn, destination và holds; không dùng allocation làm funding.
3. Dispute hold của quyết định đang được thực thi chỉ có thể được F xử lý theo đúng source decision; hold khác vẫn chặn chi.
4. Sau khi F xác nhận settlement thực sự SUCCEEDED và cập nhật escrow/milestone đúng trạng thái terminal, gọi `dispute_service.finalize_settlement_in_tx` trong cùng TX, hoặc tạo outbox `event_type=settlement.completed`, payload `settlement_id`.
5. Hook này chỉ hoàn tất cancellation/decision/dispute và gọi closure. Không tự set transfer/escrow/milestone thành đã trả. Một nhánh SPLIT thành công chưa đủ để đóng dispute.
6. API thu/chi/finance summary, bank destinations, ledger, payOS webhook và đối soát vẫn là phần F. Các test dùng FakeFinancePort được ghi rõ là test nghiệp vụ/contract, không chứng minh ledger hay chuyển tiền thật.

## 9. Tài liệu API và kiểm thử

- Chạy app bằng `uvicorn app.main:app --reload`, mở `/docs` trên cổng đã chọn.
- Snapshot OpenAPI Freelancer: [openapi.json](openapi.json). Đây là schema API; không chứa keys hoặc payload giao dịch thật.
- API mới serialize ID/tiền thành chuỗi số. Request dùng schema có validation; lỗi theo format chung. Danh sách có page/size, tối đa 100, trừ collection nhỏ có giới hạn như milestones/reviews.
- Test qua app thật: đăng ký/onboarding, quyền cũ không bị nới, OTP, review hồ sơ/MOU, upload, policy revision, dự án/ứng tuyển/select/replay/privacy, dispute API.
- Test domain: hủy có thỏa thuận, hủy một phía, bằng chứng/hạn nộp, hold độc lập, hai Admin, finance rollback, snapshot review và closure.
- Test worker: lease/recovery, notification idempotency, scanner chưa có cấu hình, gateway contract, finance unavailable, MOU expiry.
- Test MariaDB: migration, append-only/CHECK, hai kết nối giữ ngân sách, chọn người vượt trần ngân sách/chỗ, replay, hai worker, accept vs dispute. Test thu/chi tiền thật không nằm trong pytest.

Kết quả cuối: **373 passed**, không skip, gồm **9 test MariaDB**; Ruff và `git diff --check` đạt, Alembic chỉ có head `0003`. Cảnh báo deprecation Starlette/httpx và Alembic là cảnh báo thư viện hiện hữu. Test MariaDB đầu tiên đã bắt được lỗi đọc snapshot ngân sách cũ; code đã sửa thành current locking reads và chạy lại đạt.

Trên Windows có biến môi trường `DEBUG=release`, đặt `$env:DEBUG='false'` trong terminal chạy backend/test. Đây là cấu hình process, không phải thay đổi dữ liệu nghiệp vụ. Trong phiên kiểm thử, pytest dùng thư mục tạm riêng và workaround quyền mkdir chỉ trong process test, không sửa quyền máy hoặc code ứng dụng.

## 10. Cơ sở đối chiếu nghiệp vụ

[Upwork mô tả nộp bài chính thức để bắt đầu thời gian review milestone 14 ngày](https://support.upwork.com/hc/en-us/articles/211063718-How-payments-for-milestones-and-fixed-price-contracts-work). Bản này áp dụng nguyên tắc có thao tác nộp bài và thời hạn review được lưu rõ; hợp đồng hiện hữu giữ snapshot riêng.

[Freelancer hướng dẫn yêu cầu bên freelancer hủy milestone hoặc dùng giải quyết tranh chấp khi không đạt thỏa thuận](https://www.freelancer.com/support/Payments/can-an-employer-cancel-a-milestone-payment?w=f). Bản này dùng nguyên tắc thỏa thuận trước khi xử lý tiền, nhưng hoàn trực tiếp qua phần F theo thiết kế không ví của Student Connect. Không sao chép mô hình số dư tài khoản của nền tảng khác.

Các con số thương mại ở mục 4, quy trình hai Admin và chính sách hủy/rút tranh chấp là thiết kế riêng đã được chủ dự án cho triển khai; không được mô tả như tiêu chuẩn bắt buộc của mọi nền tảng.
