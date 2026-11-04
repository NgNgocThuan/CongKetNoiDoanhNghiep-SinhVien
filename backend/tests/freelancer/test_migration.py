"""Real revision tests on disposable SQLite, not a substitute for MariaDB tests."""
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.core.config import settings
from app.models import Base


@pytest.fixture
def migration_db(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "migration.sqlite").as_posix()
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "alembic"))
    engine = create_engine(url)
    yield config, engine
    engine.dispose()


def test_upgrade_preserves_legacy_data_and_installs_guards(migration_db):
    config, engine = migration_db
    command.upgrade(config, "0001")
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users (id,email,role,status) VALUES (1,'legacy@test.invalid','COMPANY','ACTIVE')"))
        conn.execute(text("INSERT INTO companies (user_id,name,tax_code,verification_status) VALUES (1,'Legacy Company','1234567890','APPROVED')"))
    command.upgrade(config, "head")
    with engine.connect() as conn:
        row = conn.execute(text("SELECT legal_name,business_status,verification_status FROM companies")).one()
        assert tuple(row) == ("Legacy Company", "UNVERIFIED", "APPROVED")
        assert conn.execute(text("SELECT email_verified_at FROM users")).scalar() is None
        assert conn.execute(text("SELECT COUNT(*) FROM mou_agreements")).scalar() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM ledger_journals")).scalar() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'trg_%_blocked'")).scalar() == 6
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO audit_logs (actor_type,action,entity_type) VALUES ('SYSTEM','TEST','test')"))
    with pytest.raises(IntegrityError, match="append-only"):
        with engine.begin() as conn:
            conn.execute(text("UPDATE audit_logs SET action='changed'"))
    with pytest.raises(IntegrityError, match="append-only"):
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM audit_logs"))
    with pytest.raises(RuntimeError, match="Freelancer data exists"):
        command.downgrade(config, "0001")


def test_empty_schema_can_downgrade_and_reupgrade(migration_db):
    config, engine = migration_db
    command.upgrade(config, "head")
    assert "freelance_contracts" in inspect(engine).get_table_names()
    command.downgrade(config, "0001")
    assert "freelance_contracts" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    assert len(inspect(engine).get_table_names()) == 87  # 86 application + Alembic version


def test_revision_matches_models_and_index_names_are_unambiguous(migration_db):
    config, engine = migration_db
    command.upgrade(config, "head")
    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []
    # MariaDB index names share a table namespace, unlike SQLite's lenient UQs.
    from sqlalchemy import UniqueConstraint

    for table in Base.metadata.tables.values():
        names = [c.name for c in table.constraints if isinstance(c, UniqueConstraint)]
        names.extend(index.name for index in table.indexes)
        assert len(names) == len(set(names)), table.name
