# Checklist bộ khung và bàn giao tích hợp

Phiên bản 1.1. Bộ nền đã có code và kết quả kiểm tra tại [FOUNDATION_STATUS.md](FOUNDATION_STATUS.md). Checklist dưới đây tiếp tục dùng để review/merge/tích hợp; không tự đánh hoàn tất nghiệp vụ A–D hoặc MariaDB chỉ vì unit tests pass. Ô trống nghĩa tiêu chí review/bàn giao đó chưa được xác nhận đầy đủ.

## 1. PR tài liệu — có thể đưa lên Git sau duyệt

- [ ] Chủ dự án duyệt README/SHARED_CONTRACTS/TEAM_TASKS và chi tiết allocation mục 6.6 của đặc tả.
- [ ] Chốt tên người nhận A/B/C/D/NỀN; không tự gán theo tên trong TASKS.md cũ.
- [ ] Duyệt bổ sung command_requests; cập nhật từ điển dữ liệu đặc tả nếu chấp nhận.
- [ ] Chỉ đưa đặc tả hiện hành và bộ tài liệu mới vào PR; tài liệu cũ được nhận diện là lịch sử, tránh nhóm dùng nhầm HTML cũ.
- [ ] Kiểm tra relative links, phiên bản, trạng thái duyệt và phạm vi thay đổi.

PR này đủ để anh em nhận việc, đọc quy tắc và chuẩn bị thiết kế module. Muốn viết service DB chung ít phải làm lại thì cần PR nền tảng tiếp theo.

## 2. PR nền tảng thực thi — phải làm sau khi được yêu cầu triển khai

### 2.1. Database

- [ ] Danh sách model/column/FK/UQ/CHECK/index khớp đặc tả, gồm nhiều contracts/project.
- [ ] Tạo composite FK contract/version, milestone/terms, project/contract budgets và deliverable/review đúng cùng cha.
- [ ] One company/user; UQ(project_id,student_id) cho contracts; không UQ project_id riêng.
- [ ] Cycle FK được thêm sau tạo bảng, delete RESTRICT bảo vệ chứng từ và không bị ORM cascade xóa ngoài ý muốn.
- [ ] Tất cả model được đăng ký vào Base.metadata; một Alembic head, không sửa migration đã dùng.
- [ ] Fresh DB và upgrade bản có dữ liệu chạy được trên MariaDB; schema.sql tham chiếu cập nhật sau schema thực thi.
- [ ] Backfill không tự xác minh người dùng/doanh nghiệp, không tự tạo MOU hoặc tiền.
- [ ] Trigger/quyền runtime chặn sửa/xóa ledger/audit; migration dùng quyền riêng phù hợp.
- [ ] Không chạy migration trên DB thật của nhóm khi chưa có thông báo/ủy quyền áp dụng.

### 2.2. Contract và thành phần chung

- [ ] Có DTO/enum/protocol signatures theo SHARED_CONTRACTS và test validate chúng.
- [ ] Ownership và onboarding dependencies không nới quyền router cũ.
- [ ] Service ngoài cùng sở hữu TX; in_tx không commit hoặc gọi mạng.
- [ ] Command coordinator chọn người/accept/dispute không tạo vòng import.
- [ ] UnavailableFinancePort là mặc định nếu chưa tích hợp; không có fake tự bật production.
- [ ] Request replay/hash/source unique có xử lý đồng thời rõ ràng.
- [ ] Clock helper/fake clock thống nhất để test expiry, không dùng sleep chờ ngày thật.
- [ ] Cấu hình mới chỉ giá trị mẫu; keys lấy từ env và không in log.

### 2.3. Fixtures chung

- [ ] CLIENT đủ/chưa đủ liên hệ, COMPANY VERIFIED/chờ duyệt/đình chỉ, MOU active/expired, ADMIN A/B, STUDENT A/B/C và user ngoài.
- [ ] Một project có hai contract riêng, terms và budgets khác nhau.
- [ ] Case đủ/hết ngân sách, hết chỗ, đóng/mở tuyển, hợp đồng draft/effective/terminated.
- [ ] File sạch/bị cách ly, deliverable nhiều phiên bản và review deadline.
- [ ] Financial fixtures đi qua writer/pipeline hợp lệ; không tạo escrow balance rời mà không có ledger tương ứng.
- [ ] FakeFinancePort/fake provider có scenario funded/unfunded/hold/reserved/unknown/failure và ghi nhận lời gọi để assert.

## 3. Lệnh kiểm tra sau khi có code

Chạy tại backend, trên checkout đã có dependencies. Đây là lệnh hướng dẫn, chưa chạy trong đợt viết tài liệu:

```powershell
python -m ruff check .
python -m pytest -q
python -m alembic heads
```

Test MariaDB mới phải có cấu hình DATABASE_URL test riêng và marker riêng khi triển khai. Không đặt URL DB phát triển/production làm fallback cho test. Migration chỉ chạy trên DB test/disposable đã xác nhận; không copy lệnh upgrade rồi vô tình tác động DB nhóm. Chốt lệnh cụ thể trong README test MariaDB của PR nền tảng.

SQLite không chứng minh SELECT FOR UPDATE, trigger và concurrency tài chính. Hai session DB độc lập với barrier đồng bộ mới là test race; gọi hai hàm tuần tự không thay thế được.

## 4. Kịch bản tích hợp trọng tâm

| Kịch bản | Điều kiện phải chứng minh |
|---|---|
| Chọn A/B cùng dự án | Hai contract riêng, tổng allocation không vượt budget/max_students. |
| Chọn A hai lần đồng thời | Một application/contract/allocation; replay đúng key. |
| A không nhìn B | 404 khi truy hợp đồng/file/tiền không sở hữu dù cùng dự án. |
| FULL riêng từng contract | A chỉ được bắt đầu khi hợp đồng A đủ, không chờ funding B và không lấy tiền B bù A. |
| Accept bình thường | Acceptance + settlement reserve cùng TX, transfer chưa success thì chưa PAID_OUT. |
| Finance chưa có | FINANCE_NOT_READY, rollback, không tạo trạng thái đã nghiệm thu/đã trả giả. |
| Accept vs dispute | Chỉ một bên reserve hoặc freeze thành công theo trạng thái dưới lock. |
| SPLIT | Một nhánh thành công, nhánh kia unknown giữ reserve; retry không trả trùng. |
| Multiple holds | Gỡ dispute hold không gỡ company suspension hold. |
| Probe/trùng webhook | Không tạo receipt từ probe; cùng external_ref chỉ một lần ghi tiền. |
| Timeout/crash | Có thể recover sau gửi lệnh nhưng trước lưu response mà không chi lần hai. |
| Closing | A xong, B chưa xong hoặc còn tuyển thì project chưa COMPLETED. |
| MOU hết hạn | Policy về VERIFIED, hợp đồng/funding cũ không tự mất. |
| Regression | Tuyển dụng/thực tập/auth/CV hiện có không hỏng. |

Test fake thành công chỉ chứng minh contract/module. Test writer thật với provider stub chứng minh tiền trong DB. Kiểm thử tài khoản payOS thật là lớp khác, chỉ chạy khi được phép; không trộn test tiền thật vào `pytest` mặc định.

## 5. Definition of Done cho PR thành viên

- [ ] Router mỏng, schema rõ, service kiểm tra role + ownership + state.
- [ ] Có case thành công, sai quyền, sai trạng thái và invariant quan trọng của module.
- [ ] Không import service người khác vòng tròn, không duplicate model/service tài chính.
- [ ] Không tự set FUNDED/PAID_OUT/SUCCEEDED hoặc tạo ledger ngoài writer.
- [ ] Nêu rõ fake/adapter nào còn thiếu; không gọi module đã end-to-end nếu chưa tích hợp thật.
- [ ] Ruff + tests phù hợp pass; thêm MariaDB test nếu chạm locks/money/constraints.
- [ ] Shared change cập nhật contract/tài liệu và có người sở hữu review.
- [ ] Không secrets/OTP/bank account thô trong log/fixtures commit; không .env/upload thật.

## 6. Quy trình Git để nhóm cùng bắt đầu

1. Sau duyệt, kiểm tra git status/branch/remotes và nhánh tích hợp thực tế; chọn đúng file tài liệu hoặc bộ khung, không lẫn thay đổi đang dở khác.
2. Tạo nhánh tài liệu riêng từ commit nền thích hợp; commit đúng phạm vi, review diff rồi push nhánh đó khi được phép. Chưa merge main chỉ vì tài liệu đã được duyệt.
3. Tạo PR tài liệu; tạo PR bộ khung riêng sau yêu cầu triển khai và sau khi test. Kiểm tra nhánh đích thực tế thay vì mặc định develop tồn tại.
4. Khi PR bộ khung được merge, ghi rõ commit nền, revision Alembic, lệnh cài dependencies/test và những phần vẫn unavailable.
5. Thành viên commit/stash công việc cá nhân theo lựa chọn của họ trước khi đổi nhánh, cập nhật nhánh đích và tạo nhánh module từ **cùng commit nền đã công bố**.
6. Chỉ upgrade DB local của mình theo README mới sau backup phù hợp; không tự chạy trên database dùng chung của nhóm.

Bộ nền được phát hành trực tiếp main theo yêu cầu riêng của chủ dự án. Xác định commit nền bằng git log sau khi cập nhật; không bịa mã commit. MariaDB test riêng đã pass, nhưng không đồng nghĩa đã migrate DB local của thành viên hoặc DB nhóm. Các module tiếp theo tiếp tục làm nhánh riêng.
