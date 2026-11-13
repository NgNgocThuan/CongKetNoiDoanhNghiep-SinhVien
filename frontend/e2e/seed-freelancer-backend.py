"""Create a NEW disposable local SQLite database for browser integration tests.

Run from backend. Never seeds the team's DATABASE_URL, never enables money I/O.
"""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

root = Path(__file__).resolve().parents[2]
backend = root / "backend"
target = root / "tmp" / ("student_connect_ui_test_" + uuid4().hex + ".sqlite")
target.parent.mkdir(parents=True, exist_ok=True)
assert target.resolve().is_relative_to((root / "tmp").resolve()) and not target.exists()
url = "sqlite:///" + target.as_posix()
os.environ.update(
    DATABASE_URL=url,
    DEBUG="false",
    FREELANCER_FINANCE_ENABLED="false",
    PAYOS_COLLECTION_ENABLED="false",
    PAYOS_PAYOUT_ENABLED="false",
)
sys.path.insert(0, str(backend))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from app.core.enums import UserRole, UserStatus  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import User, ClientProfile, Skill  # noqa: E402
from tests.freelancer.test_group_c_milestones_deliverables import active_contract_fixtures  # noqa: E402

config = Config(str(backend / "alembic.ini"))
config.set_main_option("script_location", str(backend / "alembic"))
command.upgrade(config, "head")
engine = create_engine(url)
with Session(engine, expire_on_commit=False) as db:
    f = active_contract_fixtures.__wrapped__(db)
    db.add(Skill(name="Thiết kế đồ họa"))
    f["client"].password_hash = hash_password("UiTestOnly@2026")
    f["student"].password_hash = hash_password("UiTestOnly@2026")
    db.add(ClientProfile(user_id=f["client"].id, full_name="Người thuê kiểm thử local"))
    db.add(
        User(
            id=901,
            email="ui-admin@test.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            password_hash=hash_password("UiTestOnly@2026"),
        )
    )
    db.commit()
engine.dispose()
(root / "tmp" / "freelancer-ui-backend.json").write_text(
    json.dumps({"database_url": url, "database_file": str(target)}, indent=2), encoding="utf-8"
)
print("Disposable UI test database created; connection metadata saved under worktree tmp/.")
