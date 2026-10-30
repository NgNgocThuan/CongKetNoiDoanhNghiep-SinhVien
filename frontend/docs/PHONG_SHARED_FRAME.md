# Bàn giao frontend Phong trên khung chung

## Nhánh và nguồn

- Nhánh tích hợp: feature/fe-phong-shared-frame.
- Nền: main tại a961ded; module nghiệp vụ lấy từ feature/phong-backend tại 873b87a.
- Nhánh cũ của Phong được giữ nguyên để bảo toàn lịch sử và phần backend.
- Nhánh mới chỉ thay đổi frontend; dùng backend đã tích hợp trên main.
- Không cần dùng backend/scripts/dev_server.py hoặc auth tạm để chạy frontend này.

## Đã thống nhất

1. AuthProvider, useAuth, role guards và refresh-token: dùng trực tiếp bộ khung chung.
2. HTTP: mọi API của Phong dùng cùng instance @/lib/http.
   school-shared/http.ts chỉ chuyển lỗi thành message/status cho giao diện có sẵn,
   không tạo axios instance, token store hay interceptor thứ hai.
3. App, router, QueryClient, sidebar, header, thông báo: dùng khung hiện có.
   SchoolWorkspace chỉ bọc ConfigProvider/App của Ant Design để cung cấp theme và thông báo UI.
4. Ant Design 6.6.8, icons 6.3.4 và dayjs 1.11.23 được giữ cho các form/bảng nghiệp vụ
   của Phong; không import bộ reset CSS hay thay stylesheet toàn cục.
   Theme theo tokens Admin; tiêu đề trang dùng PageHeader chung.
5. Route nghiệp vụ nằm trong feature/routes.tsx, được tổng hợp vào app/feature-routes.ts.
6. Menu Sinh viên, Giảng viên, Danh mục, Đợt thực tập mở các trang thật.
   Header giữ đúng tên khu vực khi vào trang chi tiết/import.

## Các đường dẫn

| Trang | URL |
|---|---|
| Danh mục đầy đủ | /admin/catalog |
| Sinh viên | /admin/students |
| Chi tiết sinh viên | /admin/students/:studentId |
| Import và lịch sử | /admin/students/import |
| Giảng viên | /admin/lecturers |
| Đợt thực tập | /admin/internships |
| Chi tiết đợt, sinh viên, tin, kết quả | /admin/internships/:termId |

/admin/internship-terms và /admin/internship-terms/:termId chuyển hướng sang
/admin/internships để giữ liên kết cũ. URL API backend vẫn là /internship-terms,
không đổi theo URL giao diện.

## Lỗi nhận xét/điểm đã sửa

ResultDrawer tạo một component chứa Form.useForm riêng theo result.id.
Đóng drawer hoặc đổi sinh viên sẽ bỏ form cũ. Việc gõ vào A không còn giữ dữ liệu để gửi vào B.

Có hai unit regression test: đổi A → B trực tiếp và A → đóng → B.
Browser test kiểm tra mở A, đóng, mở B, lưu đúng result_id, comment và score của B.

Các hàm chuyển dữ liệu form và constants đã tách khỏi file component để đạt quy tắc
Fast Refresh/lint chung, không tắt quy tắc cho cả module.

## Tiếp tục làm việc

Từ repository đã lưu phần đang làm:

~~~powershell
git fetch origin
git switch --track origin/feature/fe-phong-shared-frame
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
~~~

Nếu đã có nhánh này trên máy thì chỉ git switch feature/fe-phong-shared-frame.
Chạy backend theo backend/README.md, mặc định http://127.0.0.1:8000.
Đăng nhập bằng tài khoản ADMIN của database backend.

Đọc docs/CONVENTIONS.md và docs/TASKS.md để thêm tính năng, không đưa bộ auth/router tạm trở lại.

## API/hooks cho các bạn

- Hook useFaculties(params) cũ ở catalog/index.ts được giữ để tương thích.
- useFacultyOptions(), useMajors(facultyId), useIndustries(), useJobTypes(),
  useSkillSearch(q) và các selector được xuất thêm ở catalog/index.ts.
- Selector khoa/ngành/giảng viên hiện đọc tối đa 100 bản ghi như bản gốc;
  cần thêm phân trang/tìm kiếm nếu dữ liệu vượt giới hạn này.
- InternshipResult và useTermResults tiếp tục nằm trong features/internship-admin.
- school-shared chứa adapter trình bày, định dạng và helper lỗi cho các module nhà trường.
  Không chứa đăng nhập, router độc lập hoặc QueryClient riêng.
- Các trang mẫu catalog cũ không còn là route chính; public hook cũ được giữ cho tương thích.

## Kiểm tra

- npm run build
- npm run lint
- npm test: 33 bài, gồm bộ auth/HTTP chung, nghiệp vụ của Phong và regression form kết quả.
- npm run test:e2e: 6 kiểm tra khung + 9 kiểm tra module nhà trường trên Chrome.
  Có đăng nhập, menu/layout, danh mục, sinh viên, giảng viên, thực tập, route cũ,
  refresh-token, role sai, lỗi 404 và mobile.
- Đã chạy browser với backend FastAPI và SQLite tạm: đăng nhập ADMIN thật,
  tạo khoa, đọc hồ sơ sinh viên, tạo giảng viên, lưu nhận xét/điểm và tải lại kiểm tra.
  Database xác nhận đã ghi đúng dữ liệu.
- Chưa kiểm thử MariaDB hoặc gửi SMTP/AI thật trong lượt này.

Khi tích hợp nhánh khác, giữ route SchoolWorkspace cho module nhà trường và giữ các route
STUDENT/COMPANY do thành viên phụ trách thêm. Không ghi đè cả router hoặc package.json.
