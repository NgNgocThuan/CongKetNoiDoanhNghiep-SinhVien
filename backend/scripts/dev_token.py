"""Tạo access token để test API khi chưa có endpoint đăng nhập:

    python -m scripts.dev_token --email admin@school.edu.vn

Dán token vào nút "Authorize" của Swagger (http://localhost:8000/docs).
"""
import argparse

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo access token cho user (chỉ dùng ở dev)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email")
    group.add_argument("--user-id", type=int)
    args = parser.parse_args()

    with SessionLocal() as db:
        stmt = select(User).where(User.email == args.email) if args.email else select(User).where(User.id == args.user_id)
        user = db.scalar(stmt)
        if user is None:
            raise SystemExit("Không tìm thấy user")
        print(create_access_token(user.id, user.role.value))


if __name__ == "__main__":
    main()
