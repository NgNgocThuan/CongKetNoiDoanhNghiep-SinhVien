# Student Connect: Frontend

React 19 + TypeScript + Vite + Ant Design 6 + React Router 7 + TanStack Query.
Thiết kế tham chiếu: `stitch_custom_interface_design_builder/` (màu, font, bố cục). Tên trường và quyền thao tác bám `openapi.json` / backend.

## Chạy

```powershell
cd frontend
npm install
copy .env.example .env       # sửa VITE_API_BASE_URL nếu backend không ở 127.0.0.1:8000
npm run dev                  # http://localhost:5173
```

Backend cần chạy trước (xem `backend/README.md`). Backend mặc định cho phép CORS từ `http://localhost:5173`; nếu mở bằng origin khác phải sửa `CORS_ORIGINS` ở backend.

> Nếu máy có ứng dụng khác chiếm cổng 8000 bên IPv6 (vd Docker), dùng `127.0.0.1` thay cho `localhost` trong `VITE_API_BASE_URL`.

Khi `/auth/token` thật chưa có, chạy backend bằng `uvicorn scripts.dev_server:app --reload` (có endpoint đăng nhập tạm, tài khoản mẫu `admin@school.edu.vn` / `Password@123` sau khi chạy `python -m scripts.seed`).

## Lệnh

| Lệnh | Việc |
|---|---|
| `npm run dev` | Chạy dev server |
| `npm run build` | Kiểm tra kiểu (`tsc`) rồi build |
| `npm run lint` | ESLint |
| `npm test` | Vitest (quy tắc nghiệp vụ, xử lý lỗi, báo cáo import, phân quyền) |

## Phần của Phong (admin dữ liệu nhà trường)

| Màn hình | Route | Thư mục |
|---|---|---|
| Danh mục (khoa, ngành, lĩnh vực, loại hình, kỹ năng + tên gọi khác) | `/admin/catalog` | `src/features/catalog` |
| Danh sách / chi tiết / sửa sinh viên, thành tích, xác thực chứng chỉ, gửi lại email kích hoạt | `/admin/students`, `/admin/students/:id` | `src/features/school-students` |
| Import sinh viên Excel/CSV + lịch sử | `/admin/students/import` | `src/features/school-students` |
| Giảng viên | `/admin/lecturers` | `src/features/lecturers` |
| Đợt thực tập (tiến trình, sinh viên, tin, kết quả & đánh giá) | `/admin/internship-terms`, `/admin/internship-terms/:id` | `src/features/internship-admin` |

Không có nút "đồng bộ hệ thống đào tạo" vì API `/admin/students/sync` còn trả 501.

## Phần Phong cung cấp cho người khác

- `src/features/catalog/hooks.ts`: `useFaculties`, `useMajors(facultyId?)`, `useIndustries`, `useJobTypes`, `useSkillSearch(q)`. Mọi user đăng nhập đều đọc được (không chỉ admin).
- `src/features/catalog/selectors.tsx`: `FacultySelect`, `MajorSelect` (theo khoa), `IndustrySelect`, `JobTypeSelect`, `SkillSelect` (tìm theo tên hoặc alias). Giá trị là id; dùng trực tiếp trong `Form.Item`. Danh sách chọn lấy tối đa 100 mục (giới hạn của API).
- `src/features/internship-admin/api.ts` + `types.ts`: `useTermResults(termId, params)` và kiểu `InternshipResult`. `id` của từng dòng là `result_id` dùng cho form đánh giá của doanh nghiệp (Khôi). Hiện **chưa có API cho doanh nghiệp liệt kê result_id của mình** (xem `TASKS frontend.md` mục 11), nên form đánh giá phía doanh nghiệp chỉ nối được khi có nguồn `result_id`.

## Phần TẠM THỜI (người khác sẽ thay)

Dựng tối thiểu để chạy và kiểm thử trang của Phong; giữ nguyên tên để thay không phải sửa trang:

| File | Người thay | Ghi chú |
|---|---|---|
| `src/features/auth/AuthProvider.tsx`, `LoginPage.tsx` | Quang | Đăng nhập bằng `POST /auth/token` (form), đọc role từ JWT chỉ để chọn giao diện; chưa có refresh token. Giữ `useAuth` và `RequireRole`. |
| `src/lib/http.ts`, `src/lib/token.ts` | Quang | Gắn Bearer token, phát sự kiện khi 401. `getErrorMessage` xử lý `{error:{message}}`, 422 và lỗi mạng. |
| `src/layouts/AdminLayout.tsx` | Thuận | Chỉ có các mục admin đã có trang thật; chưa có chuông thông báo (của Quang). |
| `src/app/router.tsx`, `App.tsx`, `src/styles/*`, `package.json` | Thuận | Router tổng, theme (token lấy từ `DESIGN.md`). |
| `src/components/ui/*` | Thuận | `PageHeader`, `Badge`, `ItemList`, `QueryError` đang dùng chung. |

## Hành vi cần biết

- Danh mục không xóa vĩnh viễn: "Ngừng hoạt động" (xóa mềm) và có thể "Kích hoạt lại".
- Đợt thực tập chỉ chuyển tiến từng bước DRAFT→OPEN→ONGOING→CLOSED; đợt CLOSED ẩn mọi nút thay đổi.
- Kết quả đã xác nhận PASSED/FAILED thì khóa nhận xét, điểm và xác nhận.
- Giá trị rỗng/null hiển thị "—", không đổi thành 0.
- Giảng viên chưa có tài khoản nên nhà trường (admin) nhập nhận xét thay.
- Số liệu ở tab "Tổng quan" của đợt lấy thật từ API (số sinh viên, số kết quả theo trạng thái), không có số giả.
- Danh sách thả xuống (khoa, ngành, giảng viên) lấy tối đa 100 mục; nếu danh mục vượt mức này cần thêm tìm kiếm từ xa.
