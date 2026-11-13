# Rà soát hoàn thiện backend A–D

Ngày: 07/11/2026. Đây là ảnh chụp kiểm kê **trước triển khai**. Chủ dự án đã duyệt cách hoàn thiện A–D; xem [BACKEND_IMPLEMENTATION.md](BACKEND_IMPLEMENTATION.md) cho bản code và kết quả kiểm thử hiện tại. Ba câu hỏi ở dưới đã được giải quyết theo phê duyệt trong phiên chat, không còn là yêu cầu dừng công việc.

Nhánh hiện tại đã đổi tên thành `fix/freelancer-backend-a-d-local-20261107`; đường dẫn worktree giữ nguyên. Những trạng thái “chưa có” trong bảng dưới là lịch sử tại thời điểm kiểm kê, không dùng thay báo cáo triển khai mới.

## Nguồn và phạm vi

Nguồn hiện hành: `FREELANCER_BACKEND_SPEC_PAYOS.md` v2.2, `freelancer/SHARED_CONTRACTS.md`, `TEAM_TASKS.md`, `INTEGRATION_CHECKLIST.md`, `FOUNDATION_STATUS.md`, cùng kiến trúc router → service → model trong `CONVENTIONS.md`.

Tài liệu TASKS/INTEGRATION cũ mô tả tuyển dụng/thực tập, dùng cho hồi quy, không thay phân công Freelancer mới. Bản thiết kế HTML/Markdown cũ không còn là nguồn nghiệp vụ hiện hành. Các ghi chú phê duyệt cũ trong markdown không phủ nhận các quyết định chủ dự án đã duyệt trong phiên chat.

Tiếp tục trên worktree local `tmp/fix-freelancer-a-c`, nhánh `fix/freelancer-a-c-local-20261107`; giữ các bản sửa A/C và thay đổi ngoài phạm vi ở thư mục gốc. Chưa commit/push hoặc migrate database dự án. Remote đã được fetch lại, chưa thấy bản Freelancer B/D mới.

Phần F của Thuận tiếp tục là ranh giới riêng: không tự viết thêm writer ledger/payOS cạnh tranh với finance port; không lấy allocation làm tiền ký quỹ. Command cần finance phải rollback và trả FINANCE_NOT_READY khi writer chưa sẵn sàng. Việc hoàn thiện A–D không đồng nghĩa vận hành tiền thật end-to-end.

## Kiểm kê 24 ticket

| Ticket | Hiện trạng sơ bộ | Cần hoàn thiện/kiểm chứng |
|---|---|---|
| A1 Khôi | Có OTP email lưu DB trong bản sửa local | Đăng ký CLIENT/profile; phiên onboarding đúng luồng login/refresh; đổi liên hệ; SMS; rate limit bền vững theo IP/target/user |
| A2 | Có eligibility đọc DB, đã sửa policy cá nhân | Hoàn thiện EligibilityPort và ownership assertions; hồi quy auth cũ; chặn role ở endpoint và kiểm tra lại ở service |
| A3 | Có nộp hồ sơ doanh nghiệp | Danh sách/lịch sử; Admin approve/reject/request-revision; snapshot/files/đại diện/audit; tái nộp đúng trạng thái |
| A4 | Có lưu MOU PENDING_REVIEW | Chuẩn hóa quyền và URL theo mục 15.1: Admin tạo/duyệt/thu hồi, đại diện chỉ xem; authority review; expiry/reminder; giữ lịch sử |
| A5 | Có download file thật và quy tắc thuần | Upload/checksum; scanner adapter; quét bất đồng bộ; quyền file hồ sơ/deliverable/evidence; không giả CLEAN |
| A6 | Có model company_limits/đình chỉ | Chính sách hạng/hạn mức; audit override; đình chỉ/khôi phục với hold riêng; không tự chạm escrow |
| B1 Phong | Có model, chưa có service/router mới | CRUD nháp, proposal/skills, submit và eligibility |
| B2 | Có model lịch sử review | Admin review, snapshot bất biến, visibility, đề nghị tăng budget/max_students sau duyệt |
| B3 | Có model application | Apply/shortlist/withdraw/reject; privacy CV; không nộp lại WITHDRAWN |
| B4 | C đã có phần kiểm tra allocation | Service ngân sách dùng chung; tăng/giảm đúng trạng thái; MariaDB race với chọn người/offer |
| B5 | C có entry tạo contract | Coordinator chọn ứng viên nguyên tử + replay; đóng/mở tuyển độc lập; trần người/ngân sách |
| B6 | C có truy vấn contract cơ bản | Project/application/contract read models phân trang và đúng quyền; không hiển thị allocation thành funding |
| C1 Quang | Đã có tạo hợp đồng | Tích hợp với coordinator B; eligibility và idempotency đồng thời |
| C2 | Đã có version/offer/accept/hash/expiry | Rà soát điều khoản snapshot, quyền, tái kiểm tra ngân sách/eligibility và expiry qua worker |
| C3 | Đã có milestone/start/terms | Kiểm chứng FULL từng hợp đồng, policy/snapshot, finance guard và race |
| C4 | Đã có deliverable/revision | Tích hợp file A5, privacy, lịch sử, review snapshot, schema/response/pagination |
| C5 | Đã có acceptance gọi finance | Worker auto-accept dùng cùng pipeline; job cũ phải no-op; finance lỗi rollback |
| C6 | Đã có closure/reviews | Tích hợp B/D/jobs; kiểm tra mọi nghĩa vụ mở; Admin ẩn review có lý do/audit |
| D1 Việt Anh | Chưa có service/router mới | Hủy theo hash, xác nhận/từ chối/rút; căn cứ MUTUAL/BEFORE_START/OVERDUE theo terms; finance execution |
| D2 | Chỉ có model | Dispute/evidence/deadline/quyền; active guard; rút và khôi phục review timer |
| D3 | Chỉ có model | Hold theo từng reason_key; race với reserve; gỡ đúng hold; không gỡ hold khác |
| D4 | Chỉ có model | Decision version; threshold snapshot; SPLIT hai Admin; execution qua finance; chỉ resolved sau SUCCEEDED |
| D5 | Chỉ có schema và một số producer của C | Worker claim/lease/retry; audit/outbox helpers; expiry/reminder/auto-accept; payload bền vững, không lưu OTP thô |
| D6 | Chưa có API mới | Admin APIs, phân trang, quyết định/hold/evidence/audit, kịch bản xuyên A–D |

336 test đã đạt của bản sửa trước là baseline hồi quy, không phải chứng nhận 24 ticket đã hoàn tất.

## Các quyết định còn thiếu cần hỏi chủ dự án

### Q1 — Hạn mức và thời hạn vận hành

Đặc tả quy định có policy nhưng không chốt giá trị: ngưỡng dự án nhỏ bắt buộc FULL, hạn mức VERIFIED/OFFICIAL_PARTNER, hạn nộp bằng chứng, ngưỡng cần Admin thứ hai cho PAYOUT/REFUND. SPLIT luôn cần hai Admin đã được chốt, không hỏi lại.

Phương án đề xuất để duyệt: triển khai policy cấu hình có kiểm tra/audit, bắt buộc cung cấp giá trị trước khi bật hành động phụ thuộc; không tự đặt con số thương mại. Chủ dự án có thể gửi bảng giá trị ngay thay cho phương án này. Cách lưu policy bền vững/có version sẽ được cụ thể hóa trước nếu cần migration mới, không sửa revision 0002 đã phát hành.

### Q2 — SMS và bộ quét file

Tài liệu yêu cầu adapter nhưng chưa chọn dịch vụ và chưa có cấu hình. Cần biết đã có dịch vụ SMS/bộ quét nào, hoặc chủ dự án đồng ý hoàn thiện interface, adapter có cấu hình và test contract trước, giữ tính năng chưa có provider ở trạng thái chưa sẵn sàng. Không trả OTP giả, không tự đánh file CLEAN.

Không gửi credential qua chat hoặc commit. Việc thực hiện cuộc gọi SMS/email thật không nằm trong test mặc định.

### Q3 — Hủy một phía và rút tranh chấp

Mục 11.1 cho BEFORE_START/OVERDUE chỉ khi terms cho phép nhưng chưa có policy cụ thể về quyền một phía/khoản được hoàn. Mục 11.2 yêu cầu rút tranh chấp có thỏa thuận/căn cứ nhưng chưa chốt ai xác nhận. Các lựa chọn này ảnh hưởng quyền và chứng từ, không được suy ra chỉ từ enum hoặc tự đặt vào terms_json.

Phương án đề xuất để duyệt: hủy có tiền mặc định cần hai bên; chỉ cho một phía khi hợp đồng đã chấp nhận có điều khoản tương ứng và service kiểm chứng đầy đủ. Rút tranh chấp trước quyết định cần hai bên xác nhận; sau khi có quyết định chuyển xử lý Admin, không tự rút để bỏ hold/settlement. Nếu cần lưu xác nhận hai bên, chuẩn bị migration mới để review, giữ nguyên migration cũ.

## Các quyết định đã rõ, không hỏi lại

- Một doanh nghiệp một đại diện; nhiều sinh viên/hợp đồng/tài chính riêng.
- Tổng ngân sách dự án; RESERVED/COMMITTED/RELEASED; không tái dùng phần COMMITTED sau ACTIVE trong bản đầu.
- MOU upload/duyệt thủ công, chưa ký số trên web.
- Không ví người dùng, không giả lập production; finance unavailable mặc định.
- Một journal writer, khóa đúng thứ tự, command đa tác động cùng transaction; API mới ID/tiền dạng chuỗi số.
- Giữ luồng tuyển dụng/thực tập và quyền cũ; dependency onboarding không nới toàn bộ ứng dụng.

## Kiểm chứng bắt buộc cho đợt hoàn thiện

1. Router/schema/service/test/OpenAPI cho từng ticket; lỗi quyền/state/ownership được test qua app thật.
2. Hồi quy backend cũ; không gọi dịch vụ trả phí hoặc chuyển tiền trong pytest.
3. MariaDB: race chọn người/ngân sách; accept vs dispute/hold; worker claim/lease; schema mới nếu có được thử trên DB disposable.
4. Kịch bản nhiều sinh viên không lộ contract/file/CV/thu nhập của nhau; closure không hoàn tất dự án sớm.
5. Tài liệu bàn giao ghi rõ phần A–D hoàn tất, các adapter còn thiếu và phần F chờ tích hợp; không tự đánh toàn bộ checklist tiền thật là hoàn thành.
