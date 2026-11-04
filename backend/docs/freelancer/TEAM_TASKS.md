# Phân công backend Freelancer — bản duyệt

Chưa gán tên thật. A–D tương ứng bốn thành viên nghiệp vụ; chủ dự án nhận tài chính/payOS. Có thể điền tên trực tiếp vào bảng mà không đổi ranh giới kỹ thuật. Không tự suy ra tên từ phân công tuyển dụng cũ. Một người có thể nhận nhiều nhóm nếu nhóm thực tế ít hơn năm người.

Đã có bộ nền model/migration/DTO/ports và test để phát hành trên main theo yêu cầu chủ dự án; chưa áp dụng lên DB đang dùng. Phân công dưới đây là phần việc **còn lại**, không giao lại cho thành viên dựng schema từ đầu.

## 1. Bảng phân công

| Mã | Người nhận | Phạm vi | Sản phẩm bàn giao |
|---|---|---|---|
| NỀN | Đã chuẩn bị; chủ dự án quản lý tích hợp | Model/migration chung, contracts/DTO, registry, fixture, command coordinator | Review/merge PR nền tảng, kiểm chứng MariaDB trước DB nhóm |
| A | Khôi | Tài khoản, OTP, doanh nghiệp, MOU, file | Schema/service/router/test, eligibility/ownership port |
| B | Phong | Dự án, duyệt, ứng tuyển, tuyển nhiều sinh viên, ngân sách | Schema/service/router/test, selection phối hợp C |
| C | Quang | Hợp đồng, version, milestone, bàn giao, nghiệm thu, closure | Schema/service/router/test, acceptance/terms port |
| D | Việt Anh | Hủy, tranh chấp, hold, evidence, quyết định Admin | Schema/service/router/test, decision/cancellation port |
| TÀI CHÍNH | Thuận | Ledger/escrow/payOS/webhook/settlement/transfer/đối soát | Service tài chính, API tài chính và adapter payOS; worker tài chính |

NỀN có thể do chủ dự án hoặc người được chỉ định thực hiện; người này không quyết định nghiệp vụ tiền một mình. D phối hợp tài chính về outbox/jobs/audit; không tạo worker riêng xử lý chi tiền ngoài writer chung.

### Chia tải tương đối: mỗi thành viên nghiệp vụ 24 điểm

Điểm là ước lượng độ phức tạp tương đối, không phải ngày công hay cam kết tuyệt đối. Mỗi gói bao gồm router/schema/service/test của chính nó. Sau vòng đầu điều chỉnh theo năng lực và kết quả thực tế; không cân bằng bằng số endpoint đơn thuần.

| Nhóm | Ticket | Đầu việc | Điểm | Phụ thuộc |
|---|---|---|---:|---|
| A | A1 | CLIENT/onboarding và OTP chống spam, hết hạn, attempts | 6 | Nền |
| A | A2 | Eligibility + ownership + phân quyền mới, regression auth cũ | 4 | A1 |
| A | A3 | Xác minh doanh nghiệp, nộp lại, duyệt/từ chối | 5 | Nền/file |
| A | A4 | MOU upload/thẩm quyền/hiệu lực và policy hạng | 4 | A3, D5 |
| A | A5 | Stored file upload/download/quyền/checksum/quét qua adapter | 3 | Nền |
| A | A6 | Limits theo hạng và phối hợp đình chỉ/hold | 2 | A3, D3 |
| B | B1 | Project CRUD/proposals/skills và gửi duyệt | 4 | Eligibility A |
| B | B2 | Kiểm duyệt/lịch sử duyệt và quyền hiển thị | 4 | B1 |
| B | B3 | Application/shortlist/rút/quyền ứng viên | 4 | B2 |
| B | B4 | Budget allocation + max_students + test cạnh tranh MariaDB | 5 | Nền, C1 |
| B | B5 | Select nguyên tử + đóng/mở tuyển | 4 | B3, B4, C1 |
| B | B6 | Truy vấn dự án/hợp đồng theo quyền và tích hợp tổng hợp | 3 | B5, finance read port |
| C | C1 | Tạo hợp đồng riêng in_tx, phối hợp select | 3 | Nền |
| C | C2 | Version/offer/accept/hash/expiry/khóa ngân sách thay đổi | 6 | C1, B4 |
| C | C3 | Terms milestone bất biến + start guard | 5 | C2, finance port |
| C | C4 | Bàn giao/file/lịch sử nộp/revision | 4 | C3, A5 |
| C | C5 | Acceptance/auto-accept cùng transaction finance | 3 | C4, D5, finance port |
| C | C6 | Closure nhiều hợp đồng + đánh giá hai bên | 3 | C5, D và finance state |
| D | D1 | Cancellation proposal/hash/căn cứ và xác nhận | 4 | C2, finance port |
| D | D2 | Dispute/evidence/deadline/quyền riêng tư | 4 | C4, A5 |
| D | D3 | Holds theo lý do, active guard và race với reserve | 5 | Finance port, A6 |
| D | D4 | Decision/phê duyệt kép/execution theo settlement | 4 | D2, D3, finance port |
| D | D5 | Audit/outbox/scheduled-job helpers + claim/lease/retry | 4 | Nền; ưu tiên làm sớm |
| D | D6 | API Admin và kịch bản xuyên hủy/tranh chấp/closure | 3 | D1–D5, C6 |

Chủ dự án giữ nhóm F: ledger/financial writer, bank destinations, payOS thu/chi/webhook, limits ngày, đối soát và API tài chính. Nhóm F có độ khó riêng, không tính như một nhóm 24 điểm để che khối lượng. A–D hỗ trợ F bằng test theo domain và DTO đã chốt; không nhận thay logic chuyển tiền.

Làm trước để giảm chờ: A1/A5, B1/B3 bằng eligibility fixture, C1/C2, D5; sau đó nối selection và workflow. Dependency vòng A6/D3 hoặc C2/B4 được giải bằng port/fake và review contract, không tạo hai bản logic cạnh tranh.

## 2. File ownership

Đường dẫn module nghiệp vụ dưới đây là kế hoạch; các model và phần shared thực tế được liệt kê trong FOUNDATION_STATUS.md.

| Nhóm | File module đề xuất |
|---|---|
| A | routers/schemas `client_accounts.py`, `business_verifications.py`, `mou_agreements.py`, `files.py`; services `client_account_service.py`, `business_verification_service.py`, `mou_service.py`, `stored_file_service.py` |
| B | routers/schemas `freelance_projects.py`, `freelance_applications.py`; services `freelance_project_service.py`, `freelance_application_service.py`, `project_budget_service.py` |
| C | routers/schemas `freelance_contracts.py`, `milestones.py`, `deliverables.py`, `freelance_reviews.py`; services `freelance_contract_service.py`, `milestone_service.py`, `deliverable_service.py`, `freelance_review_service.py`, `freelance_closure_service.py` |
| D | routers/schemas `cancellations.py`, `disputes.py`, `admin_disputes.py`; services `cancellation_service.py`, `dispute_service.py`, `dispute_decision_service.py`, `milestone_hold_service.py` |
| Chủ dự án | routers/schemas `payment_orders.py`, `bank_destinations.py`, `finance.py`, `payos_webhooks.py`, `admin_finance.py`; services `finance_service.py`, `ledger_service.py`, `payment_service.py`, `transfer_service.py`, `reconciliation_service.py`; `payments/payos_*`, worker tài chính |

Files models và enum do NỀN tạo cùng domain owners; domain owners đề xuất thay đổi qua PR riêng, không tạo bản model trùng. Các file auth/core/config/main/registry cũ sửa qua PR nhỏ có NỀN review. Tên `contracts` và `applications` không ghi đè module AI/tuyển dụng hiện tại.

## 3. Nhóm A — tài khoản, doanh nghiệp, MOU

Làm được trước payOS:

1. CLIENT registration, profile và OTP với bảo vệ hết hạn/attempt/cooldown; bảo toàn auth cũ.
2. Onboarding giới hạn cho COMPANY chờ duyệt, không mở quyền tuyển dụng/freelance trái phép.
3. Nộp hồ sơ doanh nghiệp, yêu cầu bổ sung, duyệt/từ chối có audit; một company một đại diện.
4. Upload/tải file có quyền, checksum và trạng thái quét; không giả đánh sạch khi chưa có cơ chế kiểm tra.
5. MOU upload, kiểm tra người ký/phạm vi/hiệu lực; hết hạn trở về policy VERIFIED; job nhắc hạn qua cơ chế chung.
6. Cung cấp ClientEligibility và assert ownership/student đúng SHARED_CONTRACTS.

Chờ tài chính: đình chỉ liên quan tiền phải tạo hold thông qua luồng chung; không trực tiếp sửa escrow. Bank destination/kiểm tra đích nhận thuộc chủ dự án, A cung cấp hồ sơ danh tính/đại diện để đối chiếu.

Xong khi: đăng ký → xác minh → gửi hồ sơ → duyệt → eligibility đúng; sai role/ownership bị chặn; MOU hết hạn không hủy hợp đồng cũ; regression auth/tuyển dụng cũ vẫn pass.

## 4. Nhóm B — dự án và tuyển nhiều sinh viên

1. CRUD nháp, proposal milestone toàn dự án, skills, gửi duyệt, lịch sử duyệt.
2. Ứng tuyển/shortlist/rút; báo giá ứng viên là phần việc riêng, không nhân giá toàn dự án cho mỗi người.
3. max_students, recruitment_status, đóng/mở tuyển; APPROVED/IN_PROGRESS đều có thể nhận ứng viên khi OPEN.
4. project_contract_budgets và kiểm tra tổng allocation; writer phối hợp C dưới cùng project lock.
5. Chọn ứng viên qua command coordinator: application SELECTED + hợp đồng + ngân sách nguyên tử. Không tự tạo hợp đồng bằng SQL copy logic nhóm C.
6. Danh sách hợp đồng dự án theo quyền, tổng hợp số người/ngân sách; tài chính thực trả lấy từ finance, không suy từ allocation.

Test bắt buộc: chọn A/B cùng dự án tạo hai hợp đồng, chọn A lặp chỉ một, cùng lúc vượt trần người/ngân sách bị chặn; application của dự án khác không dùng được; sinh viên không thấy hợp đồng người khác.

Chờ payOS: trang tài chính/backend read model thực tích hợp về sau. Trước đó làm truy vấn dữ liệu nghiệp vụ và test contract; không giả lấy funded=allocated_amount.

## 5. Nhóm C — hợp đồng và thực hiện

1. Tạo contract riêng từ application SELECTED bằng hàm in_tx dùng bởi command select.
2. Version đề xuất/gửi/chấp nhận/từ chối/rút/hết hạn; hai bên đúng hash, old effective giữ nguyên khi đang đàm phán.
3. Milestones và terms riêng từng contract; không cho sửa terms đã funded hoặc đang bị guard.
4. Start, deliverable nhiều lần/file, request revision, review deadline và lịch sử.
5. Command accept phối hợp finance; auto-accept cùng pipeline, không tự set PAID_OUT.
6. Review sau kết thúc, closure contract và project dựa toàn bộ hợp đồng + trạng thái tuyển + nghĩa vụ mở.

Chờ tài chính: `assert_can_start_in_tx`, get_funding_state, chuẩn bị quyết toán và source tài chính thật. Có thể viết/test với fake theo contract. Không có finance thì endpoint phải thất bại rõ hoặc chưa enable, không bypass điều kiện đủ vốn.

Test bắt buộc: sinh viên B không chạm contract A; FULL chỉ xét từng contract; offered cũ/hết hạn/khác hash bị từ chối; immutable terms; giao lại không mất lịch sử; A xong không đóng project khi B chưa xong/còn OPEN tuyển.

## 6. Nhóm D — hủy và tranh chấp

1. Cancellation proposal/hash/chấp nhận; căn cứ trước bắt đầu/quá hạn theo terms; không tự refund sau đề xuất chưa hợp lệ.
2. Open dispute, active guard, evidence, thời hạn và quyền hai bên.
3. Holds theo lý do riêng; giải quyết dispute không mở hold đình chỉ/Admin khác.
4. Decision versions, outcome/amount, ngưỡng snapshot, hai Admin khác nhau; nội dung APPROVED bất biến.
5. Command thực thi quyết định gọi finance tạo settlement; theo dõi EXECUTING đến EXECUTED qua kết quả tài chính, không đóng dispute sớm.
6. Audit, outbox/jobs schema dùng khung chung; phối hợp chủ dự án về lease/retry và scan đối soát.

Test trước payOS: quyền/hồ sơ/evidence/phê duyệt/hold với fake; test tài chính thật bổ sung sau. Không phát endpoint “Admin đánh dấu chi thành công” để thay tích hợp còn thiếu.

## 7. Phần chủ dự án — tài chính và payOS làm sau

Đầu tiên nên cung cấp service contract và unavailable implementation, sau đó writer tiền thuần DB để nhóm tích hợp. Adapter mạng có thể hoàn thiện cuối.

1. Ledger + account/journal/posting + immutability; monetary invariants.
2. Financial terms/funding state/start guard; lock/reserve; source review/decision/cancellation.
3. Payment order/guard, payOS tạo link và tra cứu sau timeout.
4. Webhook signature/probe/dedupe, receipt/funding/review case và đối soát thu.
5. Bank destination, settlement, money transfer, provider attempts, unknown/retry và hai nhánh SPLIT.
6. Limits/reservations, audit/outbox, worker và đối soát ngân hàng/chi phí.
7. API tài chính, tổng hợp contract/project đúng quyền, kiểm thử MariaDB đồng thời và end-to-end được cho phép.

Chưa hoàn thiện phần này thì các module A–D có thể đạt trạng thái “nghiệp vụ module đã test”, chưa phải “luồng freelancer end-to-end đã chạy tiền thật”.

## 8. Thứ tự bắt đầu

| Mốc | Việc | Nhóm làm được |
|---|---|---|
| M0 | Duyệt tài liệu, gán người, chốt schema/contract | Tất cả review; chưa tự dựng DB khác nhau |
| M1 | Review bộ khung đã chuẩn bị: models/migration/enum/DTO/ports/fakes/fixtures | NỀN + review domain; thêm kiểm chứng MariaDB trước merge schema chung |
| M2 | Module A/B/C/D làm song song trên cùng commit nền | Chủ dự án dựng writer finance trước adapter |
| M3 | Tích hợp DB qua coordinator, chạy test tranh chấp/accept/closure | Không cần gọi tiền thật cho test tự động |
| M4 | Kết nối payOS thật, kiểm thử nhỏ được phép và điều kiện go-live | Chủ dự án, các nhóm sửa tích hợp |

Không lấy mốc thời gian giả định làm cam kết. Mỗi PR chỉ sửa module của mình; shared changes đi PR nền tảng trước để tránh conflict.
