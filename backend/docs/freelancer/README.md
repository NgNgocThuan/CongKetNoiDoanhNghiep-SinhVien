# Bộ nền tảng chung cho nhóm backend Freelancer

**Cập nhật local ngày 07/11/2026:** backend A–D và bộ xử lý F/payOS đã được bổ sung trên nhánh riêng. Xem [BACKEND_IMPLEMENTATION.md](BACKEND_IMPLEMENTATION.md) và [PAYOS_IMPLEMENTATION.md](PAYOS_IMPLEMENTATION.md), migration mới nhất **0004**. Phần dưới là lịch sử phát hành bộ nền. Chưa push/merge, migrate DB dự án hoặc gửi lệnh tiền thật.

Phiên bản: 1.2, ngày 04/11/2026. Chủ dự án đã yêu cầu triển khai bộ dùng chung, phân công và xuất bản bộ nền trực tiếp lên main để nhóm cập nhật. **Migration chưa được áp dụng lên DB đang dùng.**

Tài liệu nghiệp vụ/database nền: [FREELANCER_BACKEND_SPEC_PAYOS.md](../FREELANCER_BACKEND_SPEC_PAYOS.md), phiên bản 2.2. Các quyết định mục 19 của đặc tả đã được duyệt. Bộ này cụ thể hóa cách các thành viên làm việc cùng nhau, không tự thay thế schema đã duyệt.

## Đọc theo thứ tự

| Tài liệu | Dùng để làm gì? |
|---|---|
| [Đặc tả database và nghiệp vụ](../FREELANCER_BACKEND_SPEC_PAYOS.md) | Tên bảng, cột, quan hệ, chính sách tiền và trạng thái. |
| [SHARED_CONTRACTS.md](SHARED_CONTRACTS.md) | Kiểu dữ liệu dùng chung, lỗi, chữ ký hàm nội bộ, transaction và quyền ghi. |
| [TEAM_TASKS.md](TEAM_TASKS.md) | Ai làm phần nào, file sở hữu, thứ tự triển khai và phần chờ payOS. |
| [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) | Bộ khung phải có trước, kịch bản tích hợp và cách bàn giao Git. |
| [FOUNDATION_STATUS.md](FOUNDATION_STATUS.md) | Phần code đã có, cách kiểm tra/cập nhật, giới hạn và file đưa lên Git. |

Ưu tiên hoàn thiện backend; không phân công frontend ở giai đoạn này. Mỗi thành viên làm theo module dọc: router/schema/service/test. Chủ dự án giữ phần tài chính, API tích hợp payOS, webhook, thu/chi và đối soát. Nếu chủ dự án muốn giữ toàn bộ router nghiệp vụ thì cần điều chỉnh phân công; phương án hiện tại để mỗi module sở hữu cả router nội bộ của nó.

## Các quyết định nền

- Một doanh nghiệp một tài khoản đại diện; một dự án nhiều sinh viên, mỗi người một hợp đồng và tài chính riêng.
- MOU tải bản đã ký lên, kiểm tra hồ sơ; không làm dịch vụ ký online.
- Chỉ payOS với tiền thật trong sản phẩm; không ví người dùng. Test dùng fake riêng, không đánh dấu giao dịch thật thành công bằng giả lập.
- Có service tài chính chung ngay từ lúc dựng bộ khung. Cài đặt payOS có thể làm sau, nhưng hàm tài chính chưa sẵn sàng phải từ chối rõ ràng, không trả thành công giả.
- Model và migration được tích hợp tập trung trước khi các thành viên viết service dựa DB mới. Chưa có model chung thì có thể làm quy tắc thuần, schema và test contract, chưa tuyên bố module tích hợp đã chạy được.
- Database thực thi là models + migration sau khi được triển khai, kiểm thử và merge. Tài liệu hiện tại chưa tạo các file đó.

## Mức sẵn sàng và phê duyệt

| Mốc | Được làm | Chưa được coi là xong |
|---|---|---|
| Hiện tại | Review bộ code nền, tài liệu và phân công; MariaDB test riêng đã pass | Còn gán tên thành viên và chuẩn bị PR/commit nền. |
| Sau review bộ nền | Chuẩn bị PR chứa model/migration/contracts/fixtures đã test | Chưa mở thu/chi tiền thật. |
| Sau PR nền tảng được merge | Anh em cập nhật cùng commit, làm module độc lập và kiểm thử bằng fake | Chưa coi fake là tích hợp payOS. |
| Sau tích hợp thật | Chạy kiểm thử trên tài khoản và môi trường được phép | Chưa go-live nếu điều kiện vận hành chưa xác nhận. |

Đã tạo model, revision 0002, enum/DTO/ports, khung transaction, dependency mới và fixtures. Migration đã được chạy trong SQLite và MariaDB 10.11 dành riêng cho kiểm thử; ba bài MariaDB đã pass. Chưa áp dụng lên DB đang dùng. Xem FOUNDATION_STATUS.md để phân biệt phần nền đã có với module chưa triển khai.

## Điều cần chủ dự án duyệt trong bộ này

1. Chia bốn nhóm nghiệp vụ cho anh em; chủ dự án giữ tài chính và tích hợp payOS.
2. Một người phụ trách model/migration và các file registry dùng chung; không giao mỗi người tự phát triển schema riêng.
3. Dùng service contract, transaction và trạng thái pending như SHARED_CONTRACTS.md.
4. Bảng `command_requests` đã được bổ sung ở đặc tả 2.2 và bộ model/migration để thống nhất idempotency các lệnh HTTP có nhiều tác động.
5. Dùng bản cập nhật của đặc tả 2.2 và bộ này để làm Freelancer; TASKS.md/INTEGRATION.md cũ tiếp tục mô tả luồng cũ, không dùng làm danh sách việc mới.

Ngân sách/chỗ tuyển nhiều sinh viên ở mục 6.6 của đặc tả là phương án cụ thể mới bổ sung: tổng trần dự án, allocation từng hợp đồng, không tái sử dụng phần COMMITTED sau ACTIVE trong bản đầu. Chủ dự án cần xác nhận cách này cùng bộ chung trước khi dựng model, vì ảnh hưởng việc chọn người thay và phân bổ ngân sách.

## Git sau khi được duyệt

Có thể đưa bộ nền tảng đã duyệt lên Git để nhóm cập nhật. Nên làm hai PR riêng: **tài liệu đã chốt** và **bộ khung thực thi/model/migration**. PR tài liệu cho phép phân công và chuẩn bị; PR bộ khung là mốc bắt đầu làm DB đồng bộ.

Khi chuẩn bị commit phải chọn đúng file, không dùng `git add .` hoặc đưa sửa đổi ngoài phạm vi vào commit. Đợt phát hành bộ nền này chủ dự án cho phép commit/push trực tiếp main; các module tiếp theo làm nhánh riêng và review theo quy trình nhóm. Không force-push hoặc chạy migration chỉ vì cập nhật Git. Không mặc định develop đã tồn tại hoặc đã đồng bộ.

Giữ bản thiết kế cũ để tham khảo lịch sử nhưng không dùng làm nguồn hiện hành. Khi xuất bản PR, mô tả PR phải chỉ rõ đường dẫn tài liệu hiện hành ở trên.
