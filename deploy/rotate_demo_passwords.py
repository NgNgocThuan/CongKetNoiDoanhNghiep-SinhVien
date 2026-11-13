"""Đổi mọi tài khoản còn dùng mật khẩu mẫu công khai (Password@123) sang mật khẩu ngẫu nhiên.

Chạy từ backend/ với biến môi trường của server:
    python ../deploy/rotate_demo_passwords.py ../tmp/server-runtime/demo-accounts.txt
File kết quả (trong tmp/, không commit) được cập nhật theo dạng "email  mật-khẩu  vai-trò".
"""

import secrets
import sys
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password
from app.models import User

PUBLIC_DEMO_PASSWORDS = ("Password@123",)


def main(out: Path) -> None:
    accounts: dict[str, str] = {}
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 2:
                accounts[parts[0]] = line.strip()
    rotated = 0
    with SessionLocal() as db:
        for user in db.scalars(select(User).where(User.password_hash.is_not(None))):
            if any(verify_password(p, user.password_hash) for p in PUBLIC_DEMO_PASSWORDS):
                pw = "Sc-" + secrets.token_urlsafe(9)
                user.password_hash = hash_password(pw)
                role = getattr(user.role, "value", user.role)
                accounts[user.email] = f"{user.email}  {pw}  {role}"
                rotated += 1
        db.commit()
    out.write_text("\n".join(accounts.values()) + "\n", encoding="utf-8", newline="\n")
    print(f"Rotated {rotated} public demo passwords; {len(accounts)} accounts listed.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
