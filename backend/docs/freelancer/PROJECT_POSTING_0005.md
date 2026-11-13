# Cập nhật đăng công việc Freelancer — migration 0005

Ngày 10/11/2026. Chủ dự án đã duyệt bổ sung danh mục, tách hạn ứng tuyển/hoàn thành, tài liệu tham khảo và đơn giản hóa bản nháp. Code tại worktree `tmp/fix-freelancer-a-c`, nhánh `fix/freelancer-backend-a-d-local-20261107`.

Tài liệu này cập nhật quy định tạo dự án trong đặc tả trước đó. Các quy tắc hợp đồng riêng cho mỗi sinh viên, trần ngân sách, ký quỹ và quyết toán tiếp tục áp dụng.

## Lưu nháp và gửi duyệt

POST `/api/v1/freelance-projects` và PATCH `/api/v1/freelance-projects/{id}` nhận cùng cấu trúc. PATCH hiện thay toàn bộ nội dung biểu mẫu; trường bỏ qua dùng giá trị mặc định, không phải cập nhật từng thuộc tính.

| Trường | Khi lưu nháp | Khi gửi duyệt |
| --- | --- | --- |
| `title` | Bắt buộc, 1–255 ký tự | Bắt buộc |
| `description` | Mặc định chuỗi rỗng | Bắt buộc |
| `budget_amount` | Có thể null | Số nguyên VNĐ dương |
| `max_students` | Mặc định 1, tối đa 1.000 | Tối thiểu 1 |
| `category` | Có thể null | Bắt buộc |
| `experience_level` | Có thể null | Tùy chọn |
| `recruitment_deadline` | Có thể null | Hạn nhận ứng tuyển, phải ở tương lai |
| `deadline` | Có thể null | Hạn hoàn thành, không trước hạn nhận ứng tuyển |
| `acceptance_criteria` | Mặc định chuỗi rỗng | Bắt buộc |
| `deliverables_description` | Mặc định chuỗi rỗng | Bắt buộc |
| `funding_policy` | Mặc định FULL | Theo policy tài khoản/dự án |
| `skill_ids` | Mặc định [] | Ít nhất một kỹ năng còn hoạt động |
| `proposals` | Mặc định [] | Tùy chọn; nếu có phải hợp lệ |
| `attachment_file_ids` | Mặc định [], tối đa 10 | Tùy chọn |

Danh mục: DEVELOPMENT, DESIGN, CONTENT, MARKETING, DATA, TRANSLATION, OTHER. Trình độ: ENTRY, INTERMEDIATE, ADVANCED.

Dữ liệu đã nhập trong bản nháp vẫn phải đúng kiểu và giới hạn: không nhận ngân sách 0/âm, ID kỹ năng không hợp lệ, hạn tuyển sau hạn hoàn thành hoặc tổng tiền mốc sai. Nếu thêm mốc, điền đầy đủ tên, tiền, hạn bàn giao và tiêu chí; có thể xóa toàn bộ mốc để lưu nháp đơn giản. Không dùng tiền 0 hoặc ngày giả thay thông tin thiếu.

POST `/freelance-projects/{id}/submit` kiểm tra độ đầy đủ và thời gian; thiếu thông tin trả HTTP 400, mã PROJECT_INCOMPLETE. Admin phê duyệt kiểm tra lại hồ sơ, hạn, kỹ năng và tệp. Nếu có đề xuất mốc, tổng tiền bằng ngân sách; hạn mốc phải ở tương lai và không vượt hạn hoàn thành. Hợp đồng vẫn cần mốc chính thức trước khi gửi đề nghị và chấp nhận.

## Tìm kiếm và tài liệu

- GET `/freelance-projects?category=DESIGN` lọc trước khi phân trang, kết hợp được với `q` và `mine`.
- Danh sách/chi tiết trả danh mục, trình độ, hai hạn, `skills` (id/name) và `attachments` (file_id/tên/dung lượng/trạng thái). Không trả storage key.
- Backend dùng hạn nhận ứng tuyển để chặn nộp hồ sơ và mở lại tuyển. Hạn hoàn thành tiếp tục giới hạn mốc hợp đồng. Đến hạn nhận hồ sơ không tự hủy ứng viên/hợp đồng; người thuê vẫn có thể chọn ứng viên đã nộp theo quy tắc tuyển hiện có.
- Upload tài liệu bằng category PROJECT_REFERENCE qua API tệp hiện có. Hỗ trợ PDF, PNG, JPG/JPEG, DOCX, ZIP theo giới hạn upload. Dùng scanner hiện tại, không thêm nhà cung cấp mới.
- Chỉ liên kết tệp của người tạo dự án đã CLEAN/AVAILABLE; kiểm tra lại trước khi gửi duyệt. Gỡ liên kết trong nháp không xóa tệp vật lý.
- Người tải lên và Admin tải theo quyền hiện hành. Người dùng ACTIVE khác chỉ được tải tham khảo khi dự án APPROVED/IN_PROGRESS, tương ứng quyền xem tin công khai trong hệ thống. Tệp nháp/chờ duyệt không được chia sẻ theo quyền này. Mọi lượt tải vẫn kiểm tra scan, availability và đường dẫn. Chỉ tải tài liệu được phép chia sẻ vào phần tham khảo.

## Database và vận hành

File riêng `backend/alembic/versions/0005_project_posting_details.py`: revision **0005**, down_revision **0004**. Không sửa migration cũ để gộp thay đổi.

- Thêm recruitment_deadline DATETIME(6), category VARCHAR(30), experience_level VARCHAR(20) vào freelance_projects; budget_amount/deadline nullable cho nháp.
- Thêm index (category, status) và bảng freelance_project_attachments, khóa chính (project_id, file_id), khóa ngoại RESTRICT và index file_id. Tổng 93 bảng ứng dụng.
- Backfill dự án cũ: recruitment_deadline = deadline, category = OTHER; giữ nguyên ngân sách/hợp đồng/lịch bàn giao.
- Dự án đã duyệt vẫn hoạt động. Nháp/hồ sơ chờ duyệt thiếu kỹ năng cần bổ sung; không tự gán kỹ năng giả.
- Downgrade từ chối nếu có dữ liệu mới cần bảo toàn: nháp null, liên kết tệp, trình độ/danh mục/hạn tuyển khác dữ liệu cũ. Không tự xóa dữ liệu để hạ phiên bản.

**Chưa chạy migration trên database đang dùng.** Sau khi sao lưu database, chạy trong backend đúng worktree, với DATABASE_URL của môi trường cần nâng cấp:

```powershell
python -m alembic current
python -m alembic upgrade head
python -m alembic current
```

Revision sau nâng cấp là 0005. Khởi động lại backend/frontend sau đó. Bản code mới cần schema 0005.

## Kiểm chứng

Migration SQLite đã được kiểm tra upgrade từ 0004 có dữ liệu, backfill, downgrade/re-upgrade, chặn downgrade mất dữ liệu và đối chiếu model. Đã sinh SQL dialect MySQL với DATETIME(6), BIGINT UNSIGNED và khóa ngoại tương ứng. Chưa chạy migration mới trên MariaDB vì Docker engine hiện không hoạt động.

Test API bao gồm nháp chỉ tên, chặn gửi thiếu thông tin, duyệt tin không có đề xuất mốc, kỹ năng bắt buộc, hai hạn, lọc danh mục và quyền tệp. Test trình duyệt dùng fixture; không gọi email/SMS/payOS/scanner thật.

Kết quả: 206 test backend Freelancer đạt, 11 test MariaDB bỏ qua; 69 unit test frontend đạt; 20 kịch bản Playwright đạt; lint, kiểm tra kiểu và build production đạt. Kiểm tra API dự án được chạy lại sau khi bổ sung tên kỹ năng vào dữ liệu trả về: 9/9 đạt.

Ảnh dữ liệu kiểm thử: [biểu mẫu desktop](../../../frontend/docs/freelancer-previews/project-posting-desktop.png), [biểu mẫu mobile](../../../frontend/docs/freelancer-previews/project-posting-mobile.png).
