"""Opt-in real MariaDB tests. Never use a team or production database URL."""
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from alembic import command
from app.core.config import settings

pytestmark = pytest.mark.mariadb


@pytest.fixture
def mariadb_db(monkeypatch):
    raw = os.environ.get("FREELANCER_TEST_DATABASE_URL")
    if not raw:
        pytest.skip("Set FREELANCER_TEST_DATABASE_URL for disposable local MariaDB tests")
    url = make_url(raw)
    if (
        url.get_backend_name() not in ("mysql", "mariadb")
        or url.host not in ("127.0.0.1", "localhost")
        or not (url.database or "").startswith("student_connect_test_")
    ):
        pytest.fail("Refusing URL: only local student_connect_test_* databases are allowed")
    name = "student_connect_test_fl_" + uuid.uuid4().hex
    assert re.fullmatch(r"student_connect_test_fl_[a-f0-9]{32}", name)
    admin = create_engine(url)
    engine = None
    created = False
    try:
        with admin.begin() as conn:
            conn.execute(text(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        created = True
        case_url = url.set(database=name)
        monkeypatch.setattr(settings, "DATABASE_URL", case_url.render_as_string(hide_password=False))
        config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "alembic"))
        command.upgrade(config, "head")
        engine = create_engine(case_url)
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            # Only the exact randomly named database created by this fixture.
            with admin.begin() as conn:
                conn.execute(text(f"DROP DATABASE `{name}`"))
        admin.dispose()


def test_mariadb_revision_and_native_client_role(mariadb_db):
    engine = mariadb_db
    fks = inspect(engine).get_foreign_keys("freelance_contracts")
    assert any(fk["name"] == "fk_fc_effective_version" for fk in fks)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users (email,role,status) VALUES ('client@test.invalid','CLIENT','ACTIVE')"))
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"
        assert conn.execute(text("SELECT role FROM users")).scalar() == "CLIENT"


def test_mariadb_append_only_and_conservation(mariadb_db):
    with mariadb_db.begin() as conn:
        conn.execute(text("INSERT INTO audit_logs (actor_type,action,entity_type) VALUES ('SYSTEM','TEST','test')"))
    with pytest.raises(DBAPIError, match="append-only"):
        with mariadb_db.begin() as conn:
            conn.execute(text("DELETE FROM audit_logs"))
    with pytest.raises(DBAPIError):
        with mariadb_db.begin() as conn:
            conn.execute(text("INSERT INTO daily_limit_buckets (scope_key,local_date,limit_amount,reserved_amount,consumed_amount) VALUES ('PLATFORM:OUTBOUND','2026-11-04',100,60,50)"))


def test_mariadb_row_lock_prevents_over_reservation(mariadb_db):
    with mariadb_db.begin() as conn:
        conn.execute(text("INSERT INTO daily_limit_buckets (scope_key,local_date,limit_amount) VALUES ('PLATFORM:OUTBOUND','2026-11-04',100)"))
    first_locked, second_started, release_first = Event(), Event(), Event()

    def reserve_first():
        with mariadb_db.begin() as conn:
            conn.execute(text("SELECT id FROM daily_limit_buckets FOR UPDATE")).one()
            first_locked.set()
            if not release_first.wait(10):
                raise RuntimeError("Test synchronization timed out")
            conn.execute(text("UPDATE daily_limit_buckets SET reserved_amount=60"))

    def reserve_second():
        if not first_locked.wait(10):
            raise RuntimeError("First worker did not acquire its lock")
        with mariadb_db.begin() as conn:
            second_started.set()
            row = conn.execute(text("SELECT limit_amount,reserved_amount FROM daily_limit_buckets FOR UPDATE")).one()
            if row.reserved_amount + 60 > row.limit_amount:
                return False
            conn.execute(text("UPDATE daily_limit_buckets SET reserved_amount=reserved_amount+60"))
            return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(reserve_first)
        second = pool.submit(reserve_second)
        try:
            assert first_locked.wait(10) and second_started.wait(10)
            # The second connection cannot finish while the first owns the lock.
            assert not second.done()
        finally:
            release_first.set()
        first.result(timeout=15)
        assert second.result(timeout=15) is False
    with mariadb_db.connect() as conn:
        assert conn.execute(text("SELECT reserved_amount FROM daily_limit_buckets")).scalar() == 60
