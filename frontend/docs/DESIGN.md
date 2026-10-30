# Thiết kế và ba vai trò

## Nơi quy định

| Nội dung | File |
|---|---|
| Vai trò và đích sau đăng nhập | src/features/auth/types/auth.types.ts, components/guards.tsx |
| Khung từng actor | src/layouts/StudentLayout.tsx, CompanyLayout.tsx, AdminLayout.tsx |
| Sidebar, header dùng chung | src/layouts/components/ |
| Menu, mô tả chức năng, người phụ trách | src/config/navigation.ts |
| Route chức năng theo vai trò | src/app/feature-routes.ts |
| Màu, khoảng cách, bo góc | src/styles/tokens.css |
| Bố cục và responsive | src/styles/globals.css |

Student dùng điểm nhấn xanh dương, Company xanh ngọc, Admin xanh navy.
Các layout dùng AppShell chung để đồng nhất hành vi; từng module tự trình bày nội dung
nghiệp vụ theo actor. Layout không quyết định quyền backend.

## Nguyên tắc

Khung hiện tại là thiết kế nền để nhóm phát triển, có thể tinh chỉnh theo bản Stitch
được duyệt. Giữ tokens và component chung làm nguồn thống nhất.
Sidebar desktop chuyển thành dialog trên mobile; có nhãn, nút đóng và hỗ trợ Escape.
Form có label, lỗi trường và trạng thái đang gửi. Hành động nguy hiểm dùng ConfirmDialog.
Không bịa thống kê: trang chủ hiện liên kết chức năng; phần chưa phát triển ghi rõ trạng thái.
Không hiển thị tên thành viên, nhánh Git hay chi tiết triển khai trong trải nghiệm nghiệp vụ.

## Kiểm tra thủ công với backend thật

1. Chạy backend và frontend, đăng nhập mỗi role bằng tài khoản hợp lệ.
2. Tải lại trang, chuyển URL trái role, đăng xuất rồi dùng Back.
3. Xem thông báo, danh sách khoa ADMIN; kiểm tra lỗi mạng và trạng thái không có dữ liệu.
4. Thử yêu cầu email/đổi mật khẩu với dữ liệu demo được phép.
5. Kiểm tra desktop và mobile; các module nghiệp vụ chưa làm sẽ hiện placeholder.

Test tự động e2e dùng hợp đồng API giả lập để kiểm tra UI ổn định. Việc gửi email,
AI thật và database triển khai cần một lượt kiểm thử tích hợp riêng.
