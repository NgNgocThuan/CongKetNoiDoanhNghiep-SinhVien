# Hợp đồng nội bộ giữa các module backend

**Bổ sung ngày 10/11/2026:** API đăng việc và schema revision **0005** được mô tả trong [PROJECT_POSTING_0005.md](PROJECT_POSTING_0005.md). Cập nhật frontend/backend cùng phiên bản; OpenAPI snapshot đã cập nhật.

Phiên bản: 1.1. DTO/ports, transaction helper, coordinator acceptance và unavailable finance đã được tạo theo contract này. Protocol không phải service nghiệp vụ hoàn chỉnh. Các entrypoint khác còn thuộc nhiệm vụ A–D/chủ dự án. Thay chữ ký cần cập nhật tài liệu và review bên gọi.

## 1. Nơi đặt các phần dùng chung

| File dự kiến | Nội dung | Người tích hợp |
|---|---|---|
| `app/contracts/freelancer/types.py` | CommandContext, các DTO và enum contract | Người nền tảng + chủ dự án |
| `app/contracts/freelancer/ports.py` | Protocol/interface nội bộ | Người nền tảng + chủ dự án |
| `app/core/freelancer_enums.py` | Enum trạng thái mới; core/enums.py chỉ thêm role CLIENT | Người nền tảng |
| `app/dependencies_freelancer.py` | OnboardingUser, ClientUser, FreelanceClientUser; không nới dependency cũ | Người nền tảng phối hợp nhóm tài khoản |
| `app/models/*.py`, `app/models/__init__.py` | Model/relationship dùng chung | Người nền tảng |
| `alembic/versions/*` | Một chuỗi revision đã review | Người nền tảng |
| `app/services/freelancer_commands.py` | Điều phối lệnh qua nhiều module và transaction | Người nền tảng phối hợp chủ module |
| `app/services/finance_service.py` | Writer tiền thực thi về sau; hiện freelancer_finance.py cung cấp UnavailableFinancePort | Chủ dự án |
| `app/routers/__init__.py`, `app/main.py` | Đăng ký router/lifecycle | Người nền tảng |
| `tests/freelancer/fakes.py`, `conftest.py` | Fake/fixtures dùng chung | Người nền tảng phối hợp các nhóm |

Tên schema mới tiền tố theo domain khi cần, không ghi đè ApplicationRead/Contract của AI hiện có. Không import router hoặc schema HTTP vào service contract. `contracts` ở đây là giao diện Python, không phải bảng hợp đồng.

## 2. Kiểu dữ liệu chuẩn

Trong Python, IDs và tiền đều int; tiền không âm, các command cần dương phải validate. Không truyền tiền bằng float. Datetime nội bộ theo quy ước UTC thống nhất với helper hiện có; serializer trả UTC ISO 8601. ORM có thể trả naive UTC từ MariaDB, không được trộn với aware datetime khi so sánh; dùng helper chuyển đổi thống nhất, không thay toàn repo trong PR Freelancer.

JSON của API mới dùng chuỗi số cho ID và tiền; DTO service vẫn int. Rate là int basis point. Danh sách trả phân trang. UUID/string key chỉ dùng cho request_key và trace, không thay PK bảng hiện có.

```python
@dataclass(frozen=True)
class CommandContext:
    actor_user_id: int | None
    actor_type: Literal["USER", "SYSTEM", "PROVIDER"]
    request_id: str
    idempotency_key: str | None
    now_utc: datetime
    job_key: str | None = None
```

Context phải do backend tạo sau xác thực, không nhận actor_type/actor_user_id từ body khách hàng. Lệnh ghi do USER phải có actor_user_id; SYSTEM/PROVIDER chỉ được tạo từ entrypoint nội bộ đáng tin. Đây không phải quyền ADMIN tự động. Hành động tài chính phải có căn cứ hợp đồng/source và kiểm tra quyền của actor hoặc loại job hợp lệ.

DTO tối thiểu, tất cả là immutable dataclass/Pydantic nội bộ:

| DTO | Trường |
|---|---|
| `ClientEligibility` | user_id:int, company_id:int\|None, tier:str, can_draft:bool, can_submit:bool, can_fund:bool, reason_codes:tuple[str,...] |
| `ContractRef` | contract_id:int, project_id:int, student_id:int, status:ContractStatus, allocated_amount:int |
| `MilestoneFinancialTerms` | milestone_id:int, contract_id:int, client_user_id:int, student_user_id:int, amount:int, fee_rate_bp:int, funding_policy:FundingPolicy, terms_id:int |
| `FundingState` | milestone_id:int, funded_amount:int, held_amount:int, reserved_amount:int, active_hold_ids:tuple[int,...], is_fully_funded:bool |
| `AcceptanceRef` | review_id:int, milestone_id:int, deliverable_id:int, source:MANUAL\|AUTO, accepted_at:datetime |
| `SettlementRef` | settlement_id:int, milestone_id:int, kind:SettlementKind, status:SettlementStatus |
| `DisputeRef` | dispute_id:int, milestone_id:int, status:DisputeStatus, evidence_deadline:datetime |
| `ProjectClosureState` | project_id:int, recruitment_status:RecruitmentStatus, contract_counts:tuple[tuple[str,int],...], has_open_obligations:bool, eligible_terminal_status:ProjectStatus\|None |

Enum giữ nguyên value trong đặc tả database 2.1. Không dùng một chuỗi `status` chung cho mọi thực thể; tài chính chưa có escrow trả amounts=0 thay vì dựng một escrow giả. Dữ liệu về giao dịch chưa phân bổ luôn tách khỏi funded.

## 3. Transaction và thứ tự khóa

- Router gọi một command entrypoint/service ngoài cùng. Entry đó sở hữu commit/rollback; router không query hoặc commit.
- Hàm nội bộ được đánh dấu `*_in_tx` chỉ add/flush/query, **không commit**, không tạo session mới và không gọi mạng.
- Caller có thể đã có transaction do SQLAlchemy autobegin khi dependency đọc user. Dùng một cách quản lý unit-of-work thống nhất; không bọc `db.begin()` lồng mù rồi lỗi “transaction already begun”. Lỗi bất kỳ phải rollback toàn lệnh.
- Thứ tự: limit scopes → company → project → contract → milestone tăng dần → escrow → nguồn thu/settlement/transfer → dispute. Tìm ID trước, khóa đúng thứ tự, re-read và kiểm tra trạng thái sau lock.
- Khóa project khi chọn người, đổi ngân sách hoặc đồng bộ trạng thái dự án. Chưa có tiền B không cho A bắt đầu nếu policy FULL của **hợp đồng A** chưa đủ; không kiểm tra FULL toàn dự án.
- Gọi payOS/OTP/email sau commit hoặc qua outbox. Không gửi lệnh ngoài hệ thống rồi rollback DB như thể tiền chưa đi.
- Audit/outbox của một lệnh được ghi cùng TX. Subservice không dùng các helper cũ có `commit=True` mặc định nếu không truyền rõ commit=False hoặc chưa được refactor an toàn.

Quy ước này chỉ áp dụng phần Freelancer mới; không tự sửa tất cả service cũ. Khi merge code mới, thêm phụ lục ở CONVENTIONS.md để người đọc biết ngoại lệ transaction và test MariaDB. Tài liệu cũ không được dùng để hợp thức commit từng phần một lệnh tiền.

## 4. Ma trận quyền ghi

| Dữ liệu | Writer duy nhất | Module khác được làm |
|---|---|---|
| Xác minh user/company/MOU | Tài khoản/doanh nghiệp | Gọi eligibility, không tự set VERIFIED. |
| Project/applications/recruitment | Dự án | Các module yêu cầu recompute qua entrypoint. |
| Contract versions/terms/budget allocation | Hợp đồng phối hợp dự án dưới TX chung | Không tự tăng allocation ngoài khóa project. |
| Milestone làm việc, deliverables/reviews | Công việc | Gọi command phù hợp, không set status tùy ý. |
| Funding/escrow/reserve/settlement/transfer/ledger | Tài chính | Gọi finance port; không ghi tiền hoặc PAID_OUT/REFUNDED. |
| Dispute/evidence/decision/holds | Tranh chấp phối hợp tài chính | Không tự chi tiền sau quyết định. |
| Trạng thái milestone terminal do tiền | Tài chính qua command điều phối | Nhóm công việc định nghĩa transition, không có writer thứ hai. |
| Trạng thái terminal contract/project | Closure coordinator | Module nguồn phát event/request, không tự hoàn tất cả dự án. |

Mỗi sinh viên chỉ xem hợp đồng/file/tiền của mình. Cùng project_id không cho quyền xem hợp đồng người khác. Chủ dự án/Admin đúng quyền xem tổng dự án. Admin không mặc nhiên được sửa ledger hoặc phê duyệt quyết định do chính mình đề xuất.

## 5. Chữ ký hàm nội bộ cần cố định

Các chữ ký thể hiện contract, không phải yêu cầu tạo stub trả thành công. Mọi method nhận `db: Session`; `ctx: CommandContext` khi có actor/thời gian. Kiểu DTO không phải ORM object đã detach.

### 5.1. Tài khoản, điều kiện tham gia và quyền sở hữu

```python
get_client_eligibility(db, *, user_id: int, now_utc: datetime) -> ClientEligibility
assert_student_eligible(db, *, student_id: int, now_utc: datetime) -> None
assert_contract_party(db, *, contract_id: int, actor_user_id: int) -> None
assert_project_owner(db, *, project_id: int, actor_user_id: int) -> None
```

Eligibility chỉ đọc, không tự tạo tài khoản hoặc thay status. Các assert phải truy đúng FK và dữ liệu hiện tại, không chỉ role từ JWT. `assert_contract_party` không tự cho Admin quyền đọc; entrypoint Admin kiểm tra quyền chuyên biệt riêng.

### 5.2. Dự án và hợp đồng

```python
# Entry điều phối, sở hữu một TX cho cả chọn người và tạo hợp đồng.
select_student(db, *, ctx, project_id: int,
               application_id: int, allocated_amount: int) -> ContractRef

# Nội bộ, caller đã giữ project lock theo thứ tự.
create_contract_for_selected_application_in_tx(
    db, *, ctx, project_id: int,
    application_id: int, allocated_amount: int
) -> ContractRef

get_milestone_financial_terms(db, *, milestone_id: int) -> MilestoneFinancialTerms
```

`select_student` gọi chung dự án và hợp đồng, tạo SELECTED + contract + allocation + audit/outbox trong một TX. Bất kỳ lỗi nào rollback tất cả. Không để application SELECTED nhưng hợp đồng thiếu. Cùng ứng viên/key/body trả hợp đồng cũ, key khác nội dung 409. Chọn ứng viên khác cho hợp đồng khác nếu còn trần người/ngân sách. Terms phải lấy từ milestone.effective_terms_id, không lấy version mới nhất chưa được chấp nhận.

### 5.3. Công việc và tài chính

```python
get_funding_state(db, *, milestone_id: int) -> FundingState

assert_can_start_in_tx(db, *, ctx, milestone_id: int) -> None

record_acceptance_in_tx(db, *, ctx, milestone_id: int,
                        deliverable_id: int,
                        source: Literal["MANUAL", "AUTO"]) -> AcceptanceRef

prepare_acceptance_settlement_in_tx(db, *, ctx,
                                   review_id: int) -> SettlementRef
```

`get_funding_state` chỉ đọc; không dùng kết quả đọc cũ như quyền cho phép bắt đầu. Command start giữ lock và gọi assert_can_start_in_tx để kiểm tra lại vốn, FULL, hold, contract và actor.

Command accept điều phối `record_acceptance_in_tx` + `prepare_acceptance_settlement_in_tx` cùng một TX. Finance tái kiểm tra review hợp lệ, dispute/holds, số tiền chưa reserve và nguồn tài khoản nhận. Nếu finance chưa có, **toàn lệnh fail và rollback**, không để ACCEPTED rồi trả như đã tạo payout. Auto-accept dùng cùng pipeline với source AUTO, không đi đường tắt.

Chưa có tài khoản nhận VERIFIED: trả lỗi rõ và không tạo settlement; job tự nghiệm thu chuyển retry/cảnh báo, không mất quyền xử lý của hai bên. Có thể chuẩn bị ngân hàng trước khi freelancer nhận việc; quy tắc này không tự coi profile name là xác minh ngân hàng.

### 5.4. Tranh chấp, hủy và tài chính

```python
open_dispute(db, *, ctx, milestone_id: int,
             reason_code: str, description: str) -> DisputeRef

assert_disputable_in_tx(db, *, ctx, milestone_id: int) -> None

place_hold_in_tx(db, *, ctx, milestone_id: int,
                 reason_type: str, reason_key: str,
                 dispute_id: int | None, note: str) -> int

release_hold_in_tx(db, *, ctx, hold_id: int, note: str) -> None

prepare_decision_settlement_in_tx(db, *, ctx,
                                 decision_id: int) -> SettlementRef

prepare_cancellation_settlement_in_tx(db, *, ctx,
                                     cancellation_id: int) -> SettlementRef
```

open_dispute là entry chung khóa project/contract/milestone/escrow trước rồi gọi assert_disputable, tạo dispute + active guard + hold. Finance kiểm tra chưa reserve/chi. Gỡ một hold không được xóa hold khác. `release_hold_in_tx` chỉ gỡ đúng hold với quyền/căn cứ, không có hàm unfreeze_all tiện dụng.

Quyết định APPROVED và chuyển EXECUTING phải gắn đúng settlement; nếu hold khác ngăn chi, giữ quyết định APPROVED và báo trạng thái bị chặn, không tuyên bố đã reserve/chi. Không cho caller truyền gross/net để override decision: finance tự đọc quyết định đã duyệt và tính fee snapshot.

### 5.5. Kết thúc và tổng hợp

```python
recompute_contract_closure_in_tx(db, *, ctx, contract_id: int) -> None
get_project_closure_state(db, *, project_id: int) -> ProjectClosureState
recompute_project_closure_in_tx(db, *, ctx, project_id: int) -> None
```

Closure coordinator sở hữu logic ở mục 12 đặc tả. Finance xác nhận chi xong yêu cầu coordinator chạy cùng TX hoặc qua outbox có retry; nếu outbox thì trạng thái tổng có thể chậm nhưng không được hiển thị hoàn thành trước. Không chờ network để tính closure. Dự án còn OPEN tuyển hoặc hợp đồng B đang làm thì A hoàn tất không đóng dự án.

Để tránh vòng import: điều phối import các service một chiều; service nghiệp vụ không import ngược command coordinator. Module giao tiếp qua ports/DTO; endpoint chỉ gọi coordinator/entrypoint công khai.

## 6. Hành vi khi phần payOS làm sau

Tách hai khả năng: **service nghiệp vụ tài chính** và **adapter mạng payOS**. Service kiểm tra reserve/ledger có thể triển khai, kiểm thử trước; adapter không sẵn sàng thì các command cần nó phải báo unavailable, không ghi tiền giả.

- Production/default: chưa cấu hình finance dùng `UnavailableFinancePort`, trả lỗi `FINANCE_NOT_READY`, không trả funded=True hoặc settlement thành công.
- Test: dependency injection `FakeFinancePort`, fixture tường minh theo từng case. Fake mô phỏng port, không phải chứng minh tính đúng của ledger/locks. Test tích hợp tài chính phải chạy writer thật với provider stub.
- Phần đăng dự án/ứng tuyển/đàm phán hợp đồng/bàn giao có thể test riêng với trạng thái tài chính test được chuẩn bị hợp lệ.
- Chưa có finance service thì command start/accept/dispute tài chính không được coi là tích hợp xong chỉ vì test fake pass. Ghi rõ giới hạn trong PR.
- Không mount endpoint `/dev/simulate-payment` trên app production. Không để fake làm default nếu thiếu key.

## 7. Lỗi dùng chung

Giữ format hiện tại `{"error":{"code":"...","message":"..."}}`. Ưu tiên lỗi có sẵn trong core/exceptions; code mới thêm có kiểm soát, không raise HTTPException từ service.

| HTTP | Code | Ý nghĩa |
|---|---|---|
| 401 | UNAUTHORIZED | Chưa xác thực/hết phiên. |
| 403 | FORBIDDEN / CLIENT_NOT_ELIGIBLE / STUDENT_NOT_ELIGIBLE | Role/điều kiện không đủ. |
| 404 | NOT_FOUND | Không có hoặc không sở hữu đối tượng cần thao tác. |
| 409 | INVALID_STATE_TRANSITION | Sai thứ tự nghiệp vụ. |
| 409 | IDEMPOTENCY_CONFLICT | Cùng key nhưng khác command/body. |
| 409 | PROJECT_CAPACITY_EXCEEDED / PROJECT_BUDGET_EXCEEDED | Vượt trần người/ngân sách. |
| 409 | CONTRACT_VERSION_CONFLICT | Bản chấp nhận đã thay/khác hash/hết hiệu lực. |
| 409 | MILESTONE_NOT_FUNDED / FUNDS_RESERVED / FUNDS_ON_HOLD | Không đủ điều kiện dùng tiền. |
| 409 | DESTINATION_NOT_VERIFIED | Chưa có đích nhận hợp lệ. |
| 409 | SECOND_APPROVER_REQUIRED / SAME_APPROVER_NOT_ALLOWED | Phê duyệt tài chính chưa hợp lệ. |
| 503 | FINANCE_NOT_READY / PROVIDER_UNAVAILABLE | Thành phần chưa sẵn sàng; không đồng nghĩa lệnh trước chắc chắn thất bại. |
| 422 | VALIDATION_ERROR hoặc format validation chung hiện hành | Body không hợp lệ; không tự đổi toàn bộ handler cũ. |

Nếu provider timeout sau gửi lệnh, tài nguyên transfer giữ UNKNOWN; response phải cho phép tra cứu lệnh cũ, không khuyến khích client thử key mới. Không biến timeout thành lỗi 409 “chưa có tiền” rồi giải phóng reserve.

## 8. Idempotency lệnh HTTP — đề xuất bổ sung cần duyệt

Đặc tả có key riêng cho payment_orders, settlements và transfers; bộ nền bổ sung **`command_requests`** cho replay chọn ứng viên/accept/decision theo yêu cầu triển khai phần dùng chung:

`id ID PK`, `actor_user_id FK users`, `operation VARCHAR(80)`, `idempotency_key VARCHAR(128)`, `request_hash HASH`, `result_entity_type VARCHAR(50)?`, `result_entity_id ID?`, `response_json JSON?`, `completed_at DT?`, `created_at DT`.

UQ `(actor_user_id,operation,idempotency_key)`. Chỉ entrypoint USER cần bảng này; job dùng job_key/source unique; provider dùng external_ref/event key. request_hash tính từ command canonical gồm resource ID và dữ liệu nghiệp vụ, không hash secret hoặc timestamp ngẫu nhiên. Operation có scope rõ, ví dụ `freelance.select_student`; project_id nằm trong hash để cùng key khác dự án bị conflict.

INSERT record, thay đổi nghiệp vụ và hoàn tất result trong **cùng một TX**; không commit record IN_PROGRESS rồi chết khiến key bị kẹt. Request đồng thời chờ unique/TX và đọc kết quả đã commit; deadlock/unique xử lý bằng rollback và mở TX đọc lại an toàn. Lệnh validation/ownership thất bại rollback, không lưu kết quả thành công. Replay vẫn kiểm tra user/quyền hiện tại, không lộ dữ liệu của tài khoản đã mất quyền. response_json chỉ lưu payload nhỏ không nhạy cảm, ưu tiên result reference.

Các key provider phải bền vững độc lập với thời gian lưu command_requests. Không xóa record replay để cho phép tạo lại payout; unique chứng từ/source tài chính vẫn giữ lâu dài. Đây là thay đổi schema cần ghi vào đặc tả trước khi tạo migration nếu được duyệt.
