# Quy ước phát triển frontend

## Ranh giới module

Tạo src/features/<module> với api/, hooks/, pages/, components/, types/, routes.tsx
và index.ts khi cần. Chỉ tạo thư mục có nội dung thực tế.
Code nghiệp vụ nằm trong module; component được nhiều module dùng mới đưa ra components/.
Tránh nhập sâu vào nội bộ module khác: xuất phần cần dùng qua index.ts.
Dùng alias @/ trỏ vào src. Không đưa API, quyền hay dữ liệu nghiệp vụ vào component UI.

## Nối một tính năng

1. Xem trang mẫu features/catalog: API có kiểu dữ liệu, hook truy vấn, trang và routes.
2. Dùng đường dẫn tương đối trong routes.tsx, ví dụ jobs và jobs/:id.
3. Đăng ký route đúng vai trò tại app/feature-routes.ts.
4. Đổi ready thành true của menu tương ứng trong config/navigation.ts khi đã có trang.
   Nếu chưa làm xong, giữ placeholder; không đăng ký hai route cùng đường dẫn.
5. Trang cần loading, empty, error, retry hợp lý và phản hồi sau thao tác.
   Dùng PageHeader, DataTable, Pagination và các trạng thái chung khi phù hợp.

app/router.tsx tự bọc route bằng RequireAuth/RequireRole và layout tương ứng.
Route lồng dùng Outlet. Không tạo router hoặc QueryClient thứ hai trong module.

## API và dữ liệu

- Import http từ @/lib/http; URL tương đối như /catalog/faculties.
  baseURL đã gồm /api/v1, không thêm tiền tố lần nữa.
- Kiểm tra hợp đồng trong backend/app/routers, schemas và /docs của backend đang chạy.
  Không tự đặt trường, trạng thái, bộ lọc hoặc quyền mà backend không có.
- TanStack Query quản lý dữ liệu server; query key phải bao gồm bộ lọc và phân trang.
  Sau mutation, invalidate query liên quan. Không sao chép cache server vào state toàn cục.
- useState cho state giao diện; search/page/filter nên dùng URL khi cần chia sẻ.
- Form dùng react-hook-form + zod. Xử lý cả lỗi 422 và lỗi nghiệp vụ đã chuẩn hóa.
- Dùng downloadFile trong utils/download.ts cho đường dẫn tải có bảo vệ.
- Không log token, mật khẩu hoặc nội dung CV nhạy cảm. Không đặt AI key hay SMTP
  vào VITE_* vì các biến này được đóng gói gửi tới trình duyệt.
- Không dùng dữ liệu giả làm kết quả API trong sản phẩm. Fixture chỉ ở test.

## Auth và lỗi

useAuth cung cấp user/status/login/logout. Backend quyết định role.
Access token ở bộ nhớ; refresh token ở sessionStorage theo tab, khôi phục bằng API.
HTTP xử lý refresh đồng thời và chỉ thử lại một lần khi 401; không tự viết lại ở module.
Cache được xóa khi đổi danh tính/đăng xuất. Bảo vệ frontend chỉ điều hướng giao diện;
backend vẫn phải kiểm tra quyền trên từng API.

Dùng trạng thái lỗi và getApiError có sẵn, không hiển thị stack trace.
Không tự retry mutation vì có thể tạo dữ liệu trùng.

## Chia việc và PR

Theo docs/TASKS.md. Bộ khung đã cung cấp phần nền auth, HTTP và thông báo để các
module dùng ngay; Quang tiếp nhận, kiểm tra và hoàn thiện các luồng nghiệp vụ còn lại.
Trang khoa là mẫu cho Phong tiếp tục CRUD và các danh mục khác.

Thuận điều phối file dùng chung app/, config/, layouts/, components/, styles/ và lockfile.
Các thành viên trao đổi khi cần sửa cùng file; không tự ý thay thư viện hoặc thiết kế
toàn cục trong một PR nghiệp vụ. Không commit .env, node_modules, dist hay kết quả test.

PR cần lint/build/test qua, kiểm tra role đúng/sai, lỗi API và giao diện mobile.
Test logic có rủi ro và luồng người dùng; tránh test chỉ lặp lại chi tiết triển khai.
