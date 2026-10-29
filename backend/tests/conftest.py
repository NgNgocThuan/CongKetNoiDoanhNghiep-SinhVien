"""Fixture dùng chung: DB SQLite in-memory (không cần MariaDB để chạy test), client, tạo user, header đăng nhập."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.enums import UserRole, UserStatus
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import Base, User


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    """Tạo user nhanh:  admin = make_user(UserRole.ADMIN)"""
    counter = {"n": 0}

    def _make(role: UserRole = UserRole.STUDENT, status: UserStatus = UserStatus.ACTIVE, email: str | None = None) -> User:
        counter["n"] += 1
        user = User(
            email=email or f"user{counter['n']}@test.com",
            password_hash=hash_password("Password@123"),
            role=role,
            status=status,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_headers():
    """Header Bearer cho một user:  client.get(url, headers=auth_headers(user))"""

    def _headers(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}

    return _headers
