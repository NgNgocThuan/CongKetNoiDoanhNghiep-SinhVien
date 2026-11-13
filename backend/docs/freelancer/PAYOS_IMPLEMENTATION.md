# Tích hợp payOS và bộ xử lý tài chính

Ngày 07/11/2026. Code nằm trong worktree `tmp/fix-freelancer-a-c`, nhánh local `fix/freelancer-backend-a-d-local-20261107`. Chưa commit/push, chưa migrate database dự án và chưa gửi lệnh tiền thật. Đọc tài liệu này cùng [BACKEND_IMPLEMENTATION.md](BACKEND_IMPLEMENTATION.md).

## Cấu hình một lần

Chạy trong thư mục `backend` của worktree:

```powershell
python scripts/configure_payos.py
```

Lệnh chuẩn bị `.env`, bổ sung biến còn thiếu và sinh khóa mã hóa/HMAC ngân hàng nếu chưa có. Giữ nguyên giá trị đã điền và khóa đã sinh khi chạy lại. Không gọi payOS, không sửa database. `.env` không được commit; `.env.example` là mẫu dùng chung. API và worker phải dùng cùng file cấu hình, chạy từ `backend` và khởi động lại sau khi sửa `.env`.

Điền các biến sau trong `.env`:

| Nhóm | Biến |
|---|---|
| API payOS | `PAYOS_API_BASE_URL` đã có mặc định chính thức; đổi bằng biến môi trường khi cần |
| Khóa kênh thu | `PAYOS_COLLECTION_CLIENT_ID`, `PAYOS_COLLECTION_API_KEY`, `PAYOS_COLLECTION_CHECKSUM_KEY` |
| Tài khoản thu đã liên kết | `PAYOS_COLLECTION_BANK_BIN` là mã BIN 6 chữ số, `PAYOS_COLLECTION_ACCOUNT_NUMBER` là số tài khoản đúng của kênh thu |
| Khóa kênh chi | `PAYOS_PAYOUT_CLIENT_ID`, `PAYOS_PAYOUT_API_KEY`, `PAYOS_PAYOUT_CHECKSUM_KEY` |
| Trang frontend sau thanh toán/hủy | `PAYOS_RETURN_URL`, `PAYOS_CANCEL_URL`: URL đầy đủ, có thể điền khi triển khai frontend |
| Webhook backend | `PAYOS_WEBHOOK_URL`, ví dụ `https://api.ten-mien-cua-ban.vn/api/v1/webhooks/payos/collection` |
| Mã hóa ngân hàng | `FREELANCER_BANK_ENCRYPTION_KEY`, `FREELANCER_BANK_FINGERPRINT_KEY`, `FREELANCER_BANK_KEY_VERSION`; công cụ trên sinh khóa, phải sao lưu cùng dữ liệu |
| Nguồn chi | `PAYOS_PAYOUT_TREASURY_SEPARATE=true` khi tài khoản chi riêng; chỉ đặt `false` nếu thực tế chi trực tiếp từ cùng tài khoản ngân hàng thu |
| Vận hành | `PAYOS_TIMEOUT_SECONDS`, `PAYOS_ORDER_TTL_SECONDS`, hai biến `FREELANCER_DAILY_*_LIMIT`, cấu hình lease/retry worker |

Như vậy URL và khóa đều thay qua `.env`, không cần sửa code. Chỉ dán URL chưa đủ: cần bộ khóa tương ứng từng kênh, tài khoản liên kết, endpoint công khai và nguồn tiền chi thực tế. Không đổi `PAYOS_COLLECTION_CHANNEL` sau khi có giao dịch vì đây là một phần khóa chống ghi trùng. Không đổi khóa mã hóa/HMAC tùy tiện sau khi có tài khoản ngân hàng; việc xoay khóa cần kế hoạch riêng để giữ khả năng giải mã dữ liệu cũ.

## Bật và chạy

Sau khi kiểm tra `DATABASE_URL` trỏ đúng database được phép cập nhật, sao lưu và áp dụng migration qua quy trình triển khai của nhóm:

```powershell
alembic upgrade head
```

Head mới là **0004**. Không sửa 0002/0003. 0004 thêm `finance_counters` và `treasury_entries`; tổng 92 bảng ứng dụng, 93 tính cả Alembic. Sequence cấp `orderCode` dưới khóa DB, kế tiếp mã đã có; không tái sử dụng mã sau khôi phục/downgrade. Downgrade bị từ chối khi sequence hoặc sổ tài chính đã được sử dụng.

Điền đủ cấu hình rồi bật theo nhu cầu:

```dotenv
FREELANCER_FINANCE_ENABLED=true
PAYOS_COLLECTION_ENABLED=true
PAYOS_PAYOUT_ENABLED=true
```

Ba cờ mặc định `false`. Tắt riêng `PAYOS_PAYOUT_ENABLED` dừng gửi lệnh chi mới nhưng vẫn cho tra cứu các lệnh đã gửi. Tắt riêng collection dừng tạo đơn mới, vẫn xác minh webhook/tra cứu bằng bộ khóa đã cấu hình. Không tắt toàn bộ finance khi còn giao dịch đang cần nhận callback hoặc đối soát.

Chạy API theo hướng dẫn backend hiện có và worker:

```powershell
python -m scripts.freelancer_worker --interval 3
```

Worker có thể gọi API tiền thật khi bật cờ và có nhiệm vụ trong DB. Công cụ cấu hình không tự khởi chạy worker. Sau khi backend đã truy cập được qua URL HTTPS công khai, đăng ký webhook:

```powershell
python scripts/payos_webhook.py
```

Đây là thao tác chủ động đăng ký URL với payOS. Probe ký hợp lệ được ghi `PROBE`, không tạo tiền. Proxy phải chuyển tiếp nguyên JSON và chữ ký; endpoint webhook không yêu cầu JWT.

## Các luồng đã nối

- Tạo đơn trả `202` và trạng thái `CREATING`; worker tạo link, frontend lấy lại đơn để nhận checkout URL/QR. Một milestone có một đơn đang hoạt động, mỗi hợp đồng sinh viên có luồng riêng. Payer/amount/fee không lấy từ dữ liệu tiền do frontend tự gửi.
- Webhook được kiểm tra HMAC trước khi lưu bền vững và ACK. Worker tra cứu đơn qua API, đối chiếu giao dịch rồi mới ghi sổ. Return/cancel URL của trình duyệt chỉ hiển thị kết quả đọc từ backend.
- Thực thu ghi Nợ ngân hàng/Có tiền chưa phân bổ. Chỉ khoản chính xác và hợp lệ mới phân bổ sang escrow. Thiếu/thừa/muộn/sai tài khoản/trùng/chưa nhận diện vào review; không cộng hai khoản thiếu thành một khoản đủ.
- Nghiệm thu, thỏa thuận hủy và quyết định tranh chấp gọi cùng `FinancePort`. Settlement giữ chỗ toàn bộ tiền; phí theo phiên bản điều khoản đã ký. Chưa ghi doanh thu hoặc chi tiền ở bước chuẩn bị.
- Lệnh chi có reference/idempotency cố định và attempt lưu trước HTTP. Phản hồi ký hợp lệ phải có giao dịch đúng số tiền, ngân hàng, tài khoản đích và trạng thái `SUCCEEDED`. HTTP 200 hoặc approvalState không tự hoàn tất quyết toán.
- Timeout/crash dẫn tới tra cứu reference cũ, không tự POST lại. Chữ ký sai hoặc phản hồi lệch không được ghi thành công. `UNKNOWN`/`FAILED` giữ khoản dự phòng để xử lý; API refresh chỉ tra cứu, không tạo lệnh thay thế.
- SPLIT có hai lệnh riêng: nhánh thành công tiêu thụ đúng phần gross/refund của nó, nhánh còn lại giữ reserve. Chỉ sau đủ các nhánh thành công mới hoàn tất hủy/tranh chấp và tính đóng hợp đồng/dự án.
- Sổ kép được kiểm tra cân bằng và chống replay; journal/posting không sửa/xóa. Khi bật finance, command lấy khóa writer trước khóa nghiệp vụ để có cùng thứ tự khóa với worker. Cách này ưu tiên tính đúng cho quy mô hiện tại; cần thiết kế phân vùng khóa nếu tăng tải đáng kể.

## Tài khoản nhận và nguồn tiền chi

Sinh viên/người thuê tạo tài khoản nhận; số tài khoản được mã hóa, fingerprint dùng HMAC. Admin đối chiếu chứng cứ sở hữu, pháp nhân/danh tính và ghi lý do trước khi duyệt; tên tự khai hoặc OTP không được coi là bằng chứng tài khoản ngân hàng. Tài khoản đã xác minh chỉ disable hoặc tạo bản mới, không sửa đích của lệnh đã chuẩn bị.

**Cập nhật 12/11/2026:** bỏ tải chứng từ và hai admin duyệt nguồn chi theo yêu cầu đơn giản hóa demo. Admin nạp ví qua nhà cung cấp; backend không tự chuyển tiền giữa kênh thu và chi. Trước lần POST đầu tiên, worker kiểm tra số dư PayOS, không chặn theo số dư nguồn chi trên sổ nội bộ.

Thiếu tiền thì thông báo admin trên web và chờ kiểm tra lại mỗi phút, không chuyển DEAD vì chờ nạp. Cảnh báo thêm khi số dư dưới `PAYOS_PAYOUT_LOW_BALANCE_THRESHOLD` (mặc định 100.000 VND); tối đa một thông báo/admin/giờ. Kiểm tra diễn ra khi có lệnh cần gửi. Hạn mức ngày, xác minh người nhận và chống gửi trùng vẫn giữ nguyên.

Sổ vẫn ghi các giao dịch hệ thống xác nhận, không tự suy diễn khoản nạp hoặc phí ngoài hệ thống. Vì vậy số dư sổ nguồn chi không đại diện số dư ví thực; không dùng mô hình này như sổ kế toán tiền mặt đầy đủ. Xem [quy trình và giới hạn](../../../docs/PAYOUT_BALANCE_WORKFLOW.md).

## API cho frontend và vận hành

Mọi đường dưới đây có tiền tố `/api/v1`. API ghi tài chính yêu cầu `Idempotency-Key`, trừ webhook xác thực bằng chữ ký. IDs/tiền trả JSON string. Danh sách nhận `number`/`size` có giới hạn.

| Nhóm | API chính |
|---|---|
| Đích ngân hàng | `POST/GET /bank-destinations`, `POST /bank-destinations/{id}/disable`; Admin list/review dưới `/admin/bank-destinations` |
| Thu | `POST /milestones/{id}/payment-orders`, `GET /payment-orders/{id}`, `POST /payment-orders/{id}/refresh` hoặc `/cancel` |
| Xem tiền | `GET /contracts/{id}/finance`, `/contracts/{id}/payment-orders`, `/milestones/{id}/finance`, `/payment-orders/{id}/transactions` |
| Quyết toán/chi | `GET /milestones/{id}/settlements`, `/settlements/{id}/money-transfers`, `/money-transfers/{id}`; Admin refresh dưới `/admin/money-transfers/{id}/refresh` |
| Thu bất thường | `GET /admin/payment-reviews`, `POST /admin/payment-reviews/{id}/resolve` với `ALLOCATE` hoặc `RETURN` |
| Tra cứu vận hành | `GET /admin/payment-transactions`, `/admin/payment-transactions/{id}`, `/admin/money-transfers`; không trả bank ciphertext hoặc raw provider payload |
| Lịch sử nguồn vốn cũ | `GET /admin/finance/treasury-entries`; đã gỡ API POST tạo/duyệt |
| Kiểm tra/đối soát | `GET /admin/finance/readiness`, `POST/GET /admin/finance/reconciliations`, `GET /admin/finance/reconciliations/{id}/items` |

`openapi.json` là snapshot chung mới; `/docs` trên backend là tài liệu tương tác. Endpoint readiness chỉ trả tên biến còn thiếu và cờ trạng thái, không trả khóa.

Đối soát kiểm tra ledger/escrow/reserve, liệt kê khoản thu chờ review, lệnh chi chưa rõ và đưa truy vấn provider vào outbox. Kết quả nội bộ thành công không có nghĩa ngân hàng/provider đã đối soát xong. Vẫn cần đối chiếu sao kê thực, chứng từ vốn/phí và hàng đợi DEAD. Khoản thu chưa xác định đơn/người trả không tự gán người nhận hoàn; phải tra soát với provider. Lệnh đã xác nhận thất bại không tự đổi người nhận hoặc tạo reference mới; việc phát lệnh thay thế cần xác minh kết quả cũ và quy trình vận hành riêng.

## Kiểm chứng và giới hạn hiện tại

Kiểm thử dùng HTTP transport giả **chỉ trong tests**, cùng writer/ledger thật trên SQLite và MariaDB disposable. Có kiểm tra chữ ký khác nhau giữa thu/chi, callback trùng, probe, khoản thu bất thường, không cộng khoản thiếu, reserve, SPLIT, sai đích, timeout-query, quyền truy cập, cấu hình `.env`, chứng cứ nguồn vốn và tranh chấp/nghiệm thu đồng thời.

Kết quả: **400 passed**, không skip, gồm **11 bài MariaDB**. Ruff và `git diff --check` đạt; Alembic có một head `0004`. Sau sửa cuối về khóa journal/tham chiếu audit, bộ 25 bài tài chính cũng được chạy lại đạt. Cảnh báo deprecation Starlette/httpx và Alembic là cảnh báo thư viện hiện có.

Chưa dùng khóa của bạn để gọi tài khoản thật, chưa đăng ký webhook thật, chưa gửi lệnh nhận/chi tiền thật. Sau khi điền cấu hình, cần kiểm thử tích hợp trên tài khoản được phép và kiểm tra cấu hình ngân hàng/đích nhận thực tế trước vận hành.

Đối chiếu giao thức: [tài liệu API payOS](https://payos.vn/docs/api/), [webhook payOS](https://payos.vn/docs/du-lieu-tra-ve/webhook/), [SDK Python chính thức](https://github.com/payOSHQ/payos-lib-python) phiên bản tham chiếu 1.1.0. Adapter HTTP dùng các phụ thuộc có sẵn (`httpx`, `cryptography`), không thêm SDK hoặc chế độ thanh toán mô phỏng vào sản phẩm.
