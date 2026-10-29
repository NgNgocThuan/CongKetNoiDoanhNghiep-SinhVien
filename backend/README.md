# Student Connect

Nền tảng kết nối **Sinh viên – Doanh nghiệp – Nhà trường**: hồ sơ/CV sinh viên, đăng tin và tuyển dụng, thực tập theo đợt, gợi ý việc làm/ứng viên bằng AI, dashboard thống kê cho nhà trường.

- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, MariaDB 10.5+
- Frontend: React + TypeScript + Vite + Ant Design (làm sau khi backend ổn định)

## Cấu trúc thư mục

```
student-connect/
├── README.md
├── docker-compose.yml          # MariaDB cho môi trường dev
├── database/
│   └── schema.sql              # Thiết kế DB gốc (37 bảng) - để tham chiếu/đọc
├── docs/
│   ├── TASKS.md                # PHÂN CÔNG nhiệm vụ cho 5 thành viên  <-- đọc đầu tiên
│   └── CONVENTIONS.md          # Quy ước kiến trúc, đặt tên, git, migration, test
├── .github/workflows/          # CI: ruff + pytest
├── backend/
│   ├── app/
│   │   ├── main.py             # Điểm vào FastAPI
│   │   ├── dependencies.py     # DbSession, CurrentUser, AdminUser, CurrentStudent, Pagination...
│   │   ├── core/               # config, database, security (JWT/bcrypt), enums, exceptions
│   │   ├── models/             # SQLAlchemy models, mỗi domain một file
│   │   ├── schemas/            # Pydantic schemas (request/response)
│   │   ├── routers/            # Endpoint (mỏng: chỉ khai báo + quyền + gọi service)
│   │   ├── services/           # Nghiệp vụ (nơi viết logic, truy vấn DB)
│   │   ├── ai/                 # LLM client, parse CV/tin, matching engine
│   │   ├── tasks/              # Tác vụ nền (gửi email)
│   │   └── utils/              # Tiện ích dùng chung (phân trang, file, hash, Excel...)
│   ├── alembic/versions/       # Migration (0001 = toàn bộ schema ban đầu)
│   ├── scripts/                # seed.py, dev_token.py
│   └── tests/                  # pytest (SQLite in-memory, không cần MariaDB)
```

Luồng một request: `router` → `service` → `models` (DB). Router không chứa nghiệp vụ; service không biết gì về HTTP. Chi tiết ở [docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## Chạy dự án lần đầu

```bash
# 1. Database
docker compose up -d db

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env

# 3. Tạo bảng bằng migration + dữ liệu mẫu
alembic upgrade head
python -m scripts.seed

# 4. Chạy server
uvicorn app.main:app --reload
```

Mở http://localhost:8000/docs (Swagger). Tài khoản mẫu (mật khẩu `Password@123`):

| Role | Email |
|---|---|
| ADMIN (nhà trường) | `admin@school.edu.vn` |
| STUDENT | `sv001@school.edu.vn` |
| COMPANY | `hr@acme.vn` |

Khi chưa làm xong endpoint đăng nhập, lấy token để test bằng:
`python -m scripts.dev_token --email admin@school.edu.vn` rồi dán vào nút **Authorize** của Swagger.

## Test và lint

```bash
cd backend
pytest -q          # chạy trên SQLite in-memory
ruff check .       # lint (CI cũng chạy lệnh này)
```

## Làm việc nhóm

1. Đọc [docs/TASKS.md](docs/TASKS.md) để biết phần việc và ranh giới file của mình.
2. Đọc [docs/CONVENTIONS.md](docs/CONVENTIONS.md) (đặc biệt phần Git và Migration).
3. Xem module mẫu đã hoàn chỉnh: `routers/catalog.py` + `services/catalog_service.py` + `schemas/catalog.py` + `tests/test_catalog_faculty.py`. Mọi module khác làm theo khuôn này.
