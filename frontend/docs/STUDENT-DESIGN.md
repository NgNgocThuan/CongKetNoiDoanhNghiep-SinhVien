# Thiết kế khu vực sinh viên — Việt Anh

## Trạng thái

> Bản brief gốc dưới đây được giữ để tham khảo. Bản code 7a023d4 đã được tích hợp
> vào integration/frontend-local, thay student-workspace. Yêu cầu mới: chỉ CV ONLINE,
> không tải PDF/DOCX lên. Xem FRONTEND_COMPLETION.md để biết trạng thái tích hợp hiện tại.

Đã đọc frontend.md, docs/TASKS.md, docs/CONVENTIONS.md, docs/DESIGN.md và bộ
Stitch được cung cấp tại E:/Project01/stitch_custom_interface_design_builder.
Đã tạo nhánh feature/fe-vietanh-student từ origin/main.

Chưa triển khai UI: yêu cầu thiết kế trên Google Stitch trước khi code.
Brief bên dưới đã được nhập và bấm Generate designs trên Google Stitch nhưng trang
chuyển sang https://stitch.withgoogle.com/?pli=1 và chỉ hiện màn hình trống.
Chưa xác nhận tạo project hoặc có ảnh thiết kế mới. Không coi brief là bản thiết kế đã duyệt.

## Đánh giá mẫu hiện có

- Giữ primary navy #1E40AF, teal #0F766E, nền sáng #F8FAFC, thẻ trắng viền #E2E8F0.
- Giữ nhịp khoảng cách 8px, card 16px, nút pill; form 14–16px và font Be Vietnam Pro.
- Ảnh S01 hiện hiển thị font serif, cần xác nhận font tiếng Việt đã tải đúng khi triển khai.
- Sidebar sinh viên chỉ hiện mục sinh viên; không hiển thị vai trò admin hoặc menu cả ba role.
- Loại tên field kỹ thuật khỏi nhãn người dùng; không dùng thống kê minh họa như số liệu thật.
- Lời mời ứng tuyển không phải lịch phỏng vấn. Ghi chú trạng thái được xem trong timeline.
- CV online tải JSON theo backend; không hứa xuất PDF.
- Màu và layout chung vẫn thuộc Thuận; không sửa theme/router chung trước khi thống nhất.

## Màn bổ sung cần có trước khi code

| Màn | Nội dung và tương tác | API |
|---|---|---|
| S05 CV của tôi | Thẻ CV, upload PDF/DOCX, tạo/sửa online, mặc định, tải, xóa có xác nhận; vùng gắn panel AI của Thuận | /cvs/* |
| S06 Ứng tuyển | Modal chọn CV mặc định, thư giới thiệu, gửi; giữ invitation_id và xử lý lỗi nghiệp vụ | POST /applications |
| S07 Đơn ứng tuyển | Lọc trạng thái, phân trang, chi tiết và timeline; rút có xác nhận khi được phép | /applications/me, /applications/{id}, /withdraw |
| S08 Lời mời | Lời nhắn, trạng thái, mở S06 hoặc từ chối; fallback rõ khi chưa tải được tên tin/công ty | /invitations/me, /invitations/{id}/decline |
| S09 Thực tập của tôi | Đợt, học kỳ, thời gian, giảng viên, tin thuộc đợt; không bảng điểm | /students/me/internship và API tin theo đợt |
| S10 Việc đã lưu | Thẻ tin, bỏ lưu, chi tiết, trạng thái tin không còn khả dụng | /saved-jobs/* |

Mẫu S01 tìm việc, S02 chi tiết tin và S04 hồ sơ đã có trong thư mục tham chiếu.
Mỗi màn bổ sung cần desktop 1440px, mobile 390px, loading/empty/error/focus/disabled.
Hồ sơ công khai doanh nghiệp dùng dữ liệu public; không lộ tài liệu xác thực.

## Brief đã gửi Google Stitch

Thiết kế bộ màn hình web tiếng Việt Student Connect, khu vực SINH VIÊN, desktop
1440px và mobile 390px. Giữ design system: primary navy #1E40AF, accent teal
#0F766E, nền #F8FAFC hơi lavender, thẻ trắng viền #E2E8F0 bo 16px, nút pill,
font Be Vietnam Pro (không serif). Sidebar chỉ sinh viên: Tìm việc, Gợi ý phù hợp,
Việc đã lưu, Hồ sơ của tôi, CV của tôi, Đơn ứng tuyển, Lời mời, Thực tập của tôi.
Header gọn với chuông, tên sinh viên.

Tạo 6 màn hình bổ sung nhất quán: S05 CV của tôi (thẻ CV online/upload PDF DOCX,
mặc định duy nhất, sửa, tải JSON cho CV online, xóa mềm, panel phân tích AI);
S06 modal ứng tuyển (chọn CV mặc định, thư giới thiệu, gửi đơn); S07 đơn ứng tuyển
và timeline (đã ứng tuyển/sàng lọc/phỏng vấn/đề nghị/đã tuyển, rút có xác nhận);
S08 lời mời (tin, công ty, lời nhắn, ứng tuyển theo lời mời/từ chối); S09 thực tập
của tôi (đợt, học kỳ, thời gian, giảng viên, xem tin theo đợt, không bảng điểm);
S10 việc đã lưu. Ví dụ dữ liệu giả FPT Software và sinh viên Nguyễn Văn An.

Không thêm chat, calendar, payment, PDF generator, dashboard số liệu giả.
Không hiển thị tên field API hay ID kỹ thuật trong UI. Hiển thị loading/rỗng/lỗi
và focus rõ. Ưu tiên thiết kế trước để nhóm review rồi mới code.

## Hợp đồng tích hợp khi triển khai

- Dùng http của Quang, TanStack Query và component có sẵn; không thêm thư viện riêng.
- Xuất JobCard, CompanyPublicProfile, SaveJobButton và ApplyDialog cho matching.
- ApplyDialog nhận open, jobId, invitationId?, onClose, onSuccess; lấy CV thật.
- Trang CV nhận panel AI từ Thuận; không viết lại module AI.
- ReportDialog và selector danh mục cần dùng export công khai từ module chủ sở hữu.
- Sau khi có thiết kế: triển khai các feature sinh viên, xác minh API thật,
  lint/build/test và desktop/mobile, commit/push thường xuyên, mở PR main chờ review.
