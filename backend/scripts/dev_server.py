"""Chạy API kèm endpoint đăng nhập TẠM để nút Authorize của Swagger dùng được khi TV1 chưa viết xong /auth/token.

    uvicorn scripts.dev_server:app --reload

Rồi mở http://127.0.0.1:8000/docs, bấm Authorize và nhập username = email, password = Password@123
(tài khoản mẫu từ `python -m scripts.seed`), các ô client_id / client_secret để trống.

Chỉ dùng cho dev. Khi TV1 đã có POST /auth/token thật thì endpoint tạm này tự không được thêm vào.
"""
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.dependencies import DbSession
from app.main import app
from app.models import User

TOKEN_PATH = f"{settings.API_V1_PREFIX}/auth/token"

if not any(getattr(route, "path", None) == TOKEN_PATH for route in app.routes):

    @app.post(TOKEN_PATH, include_in_schema=False)
    def dev_login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
        user = db.scalar(select(User).where(User.email == form.username))
        if user is None or not verify_password(form.password, user.password_hash):
            raise UnauthorizedError("Sai email hoặc mật khẩu")
        return {"access_token": create_access_token(user.id, user.role.value), "token_type": "bearer"}
