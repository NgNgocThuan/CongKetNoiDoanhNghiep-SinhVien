# Student Connect — Frontend

Khung React + TypeScript + Vite dùng chung cho 5 thành viên. Ba khu vực STUDENT,
COMPANY, ADMIN có layout, menu và bảo vệ quyền riêng.

## Chạy trên máy

Dùng Node.js 24.14.1 (xem .nvmrc). Từ thư mục frontend:

```powershell
npm ci
Copy-Item .env.example .env
npm run dev
```

Mở http://127.0.0.1:5173. Chạy backend theo [hướng dẫn backend](../backend/README.md)
ở http://127.0.0.1:8000. Có thể đổi BACKEND_PROXY_TARGET trong .env.
Vite chuyển tiếp /api/v1 sang backend; frontend không chứa mật khẩu AI/SMTP.
Tài khoản đăng nhập là tài khoản thật trong database backend, không có chế độ giả lập
trong ứng dụng.

## Đã có và phần cần làm tiếp

- Layout desktop/mobile, điều hướng riêng ba vai trò, tokens và component chung.
- Luồng đăng nhập, khôi phục phiên, đăng xuất, đăng ký doanh nghiệp, mật khẩu.
<<<<<<< HEAD
- Thông báo và một trang mẫu danh sách khoa gọi API thật.
- Hai trang gợi ý việc/ứng viên đã nối API và thao tác lưu, ứng tuyển, gửi lời mời.
  Xem [bàn giao matching](docs/MATCHING.md).
=======
- Thông báo và các module nhà trường của Phong: danh mục, sinh viên/import, giảng viên,
  đợt thực tập và kết quả. Xem [bàn giao tích hợp](docs/PHONG_SHARED_FRAME.md).
>>>>>>> origin/feature/fe-phong-shared-frame
- Menu nghiệp vụ còn lại hiện trang “Đang phát triển” để thành viên tiếp tục làm.
  Danh mục mẫu mới có danh sách khoa, chưa phải toàn bộ chức năng danh mục.
- Kiểm tra trình duyệt dùng API giả lập trong thư mục e2e; chưa xác nhận dịch vụ
  MariaDB, email hay AI thực tế qua các bài kiểm tra frontend này.

## Cấu trúc

```text
src/
  app/                 # providers, router, registry route nghiệp vụ
  layouts/             # khung theo vai trò, Header, Sidebar
  components/
    ui/                # Button, Input, Card, Dialog...
    common/            # Table, phân trang, trạng thái, hộp xác nhận...
  features/            # module nghiệp vụ tự quản lý API/hooks/pages/types
    auth/
    catalog/           # mẫu cách nối module vào khung
    notifications/
    shared/            # trang chủ, placeholder, 403, 404
  config/              # env, danh sách menu và phân công
  lib/                 # HTTP, chuẩn hóa lỗi, QueryClient
  hooks/               # hook độc lập nghiệp vụ
  types/               # hợp đồng API dùng chung
  utils/               # định dạng, tải file
  styles/              # tokens, CSS nền
```

Đọc [quy ước phát triển](docs/CONVENTIONS.md), [thiết kế và phân quyền](docs/DESIGN.md),
[phân công 5 thành viên](docs/TASKS.md).

## Kiểm tra trước khi tạo Pull Request

```powershell
npm run lint
npm run build
npm test
npx playwright install chromium
npm run test:e2e
```

Nếu đã cài Chrome, có thể dùng `$env:PLAYWRIGHT_CHANNEL='chrome'` trước lệnh
test:e2e. CI tự chạy lint, build và unit test. E2E chạy riêng theo các lệnh trên.

Mỗi tính năng làm trên nhánh riêng từ bản khung được nhóm thống nhất. PR ghi
chức năng, API đã nối và cách kiểm tra; nhờ review trước khi merge.
