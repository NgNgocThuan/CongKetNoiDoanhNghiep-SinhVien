# Cổng kết nối Sinh viên – Doanh nghiệp – Nhà trường

- Backend: Python FastAPI, SQLAlchemy 2.x và Alembic; cấu hình dự án hướng tới Python 3.11+.
- Frontend: React + TypeScript + Vite. Xem [hướng dẫn frontend](frontend/README.md).
- Database: MariaDB, kết nối qua PyMySQL. Docker Compose hiện dùng MariaDB 10.11.

## Chạy bản demo 31/10/2026 trên máy

Từ thư mục gốc repository sau khi cập nhật `main`:

```powershell
cd frontend
npm ci
cd ../backend
python -m pip install -r requirements.txt
cd ..
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-local.ps1
```

Mở http://127.0.0.1:5173. Các tài khoản demo và cách tắt/khởi động lại ở
[README_LOCAL.md](README_LOCAL.md). Script dùng SQLite riêng trong `tmp/local-runtime`,
không thay đổi database MariaDB hoặc `.env` cá nhân; SMTP/AI thật được tắt trong bản demo.
Để chạy bằng MariaDB và cấu hình SMTP/AI của bạn, dùng quy trình backend bên dưới và
`npm run dev` trong frontend thay cho script demo.

## Cấu trúc

```text
CongKetNoiDoanhNghiep-SinhVien/
├── .github/workflows/backend-ci.yml
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── scripts/
│   ├── tests/
│   ├── uploads/.gitkeep
│   ├── database/schema.sql
│   ├── docs/
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── README.md
├── frontend/
├── .gitignore
└── README.md
```

Mã Backend được giữ nguyên. README ban đầu được lưu tại `backend/README.md`; tài liệu nhóm nằm trong `backend/docs/`. Workflow nằm ở gốc để GitHub Actions nhận diện.

## Cài đặt và chạy Backend trên Windows (PowerShell)

Cần Python 3.11+ và Docker Compose để chạy database theo cấu hình có sẵn. Từ thư mục gốc repository:

```powershell
cd backend
docker compose up -d db
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

Chỉnh `backend/.env`: đặt `SECRET_KEY` riêng, kiểm tra `DATABASE_URL` và thông tin SMTP/AI nếu sử dụng. Các mật khẩu `app`/`root` trong Compose và tài khoản trong script seed là dữ liệu mẫu cho môi trường phát triển.

Khi MariaDB đã sẵn sàng, tiếp tục trong `backend/`:

```powershell
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

Script seed là tùy chọn, tạo dữ liệu mẫu phục vụ phát triển. Swagger: http://localhost:8000/docs.

Các lệnh Backend phải chạy từ `backend/` để đường dẫn `.env`, `alembic` và `uploads` khớp cấu hình. Compose đã chuyển vào cùng thư mục; không chạy lệnh Compose cũ từ gốc. `database/schema.sql` là tài liệu tham chiếu; migration nằm trong `alembic/versions/`.

## Kiểm tra

Chạy trong `backend/` sau khi cài dependencies:

```powershell
pytest -q
ruff check .
```

Test hiện có dùng SQLite trong bộ nhớ. Không commit `.env`, thông tin xác thực, dữ liệu upload thật, môi trường ảo hoặc file cache. `.env.example` chỉ chứa giá trị mẫu.
