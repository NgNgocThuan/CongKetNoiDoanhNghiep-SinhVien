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
            conn.execute(
                text(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            )
        created = True
        case_url = url.set(database=name)
        monkeypatch.setattr(
            settings, "DATABASE_URL", case_url.render_as_string(hide_password=False)
        )
        config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        config.set_main_option(
            "script_location", str(Path(__file__).resolve().parents[2] / "alembic")
        )
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
        conn.execute(
            text(
                "INSERT INTO users (email,role,status) VALUES ('client@test.invalid','CLIENT','ACTIVE')"
            )
        )
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0004"
        assert conn.execute(text("SELECT role FROM users")).scalar() == "CLIENT"


def test_mariadb_append_only_and_conservation(mariadb_db):
    with mariadb_db.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO audit_logs (actor_type,action,entity_type) VALUES ('SYSTEM','TEST','test')"
            )
        )
    with pytest.raises(DBAPIError, match="append-only"):
        with mariadb_db.begin() as conn:
            conn.execute(text("DELETE FROM audit_logs"))
    with pytest.raises(DBAPIError):
        with mariadb_db.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO daily_limit_buckets (scope_key,local_date,limit_amount,reserved_amount,consumed_amount) VALUES ('PLATFORM:OUTBOUND','2026-11-04',100,60,50)"
                )
            )


def test_mariadb_row_lock_prevents_over_reservation(mariadb_db):
    with mariadb_db.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO daily_limit_buckets (scope_key,local_date,limit_amount) VALUES ('PLATFORM:OUTBOUND','2026-11-04',100)"
            )
        )
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
            row = conn.execute(
                text("SELECT limit_amount,reserved_amount FROM daily_limit_buckets FOR UPDATE")
            ).one()
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


def test_cancel_waits_for_activation_and_rechecks_stale_contract(mariadb_db):
    """A stale identity-map DRAFT must not overwrite a concurrently activated contract."""
    from datetime import datetime

    from sqlalchemy.orm import Session

    from app.contracts.freelancer.types import CommandContext
    from app.core.exceptions import ConflictError
    from app.core.freelancer_enums import ActorType
    from app.models import FreelanceContract, FreelanceProject, ProjectContractBudget
    from app.services.freelance_closure_service import FreelanceClosureService
    from tests.freelancer.conftest import two_contract_project

    with Session(mariadb_db, expire_on_commit=False) as seed:
        project, contracts = two_contract_project.__wrapped__(seed)
        project_id, contract_id, owner_id = project.id, contracts[0].id, project.client_user_id
    loaded, activated, allow_commit, attempting = Event(), Event(), Event(), Event()

    def activate():
        assert loaded.wait(10)
        with Session(mariadb_db) as first:
            first.query(FreelanceProject).filter_by(id=project_id).with_for_update().one()
            c = first.get(FreelanceContract, contract_id)
            c.status = "ACTIVE"
            first.query(ProjectContractBudget).filter_by(
                contract_id=contract_id
            ).one().status = "COMMITTED"
            first.flush()
            activated.set()
            assert allow_commit.wait(10)
            first.commit()

    def cancel():
        with Session(mariadb_db, expire_on_commit=False) as second:
            stale = second.get(FreelanceContract, contract_id)
            assert stale.status == "DRAFT"
            loaded.set()
            assert activated.wait(10)
            attempting.set()
            ctx = CommandContext(
                actor_user_id=owner_id,
                actor_type=ActorType.USER,
                request_id="cancel-race",
                idempotency_key=None,
                now_utc=datetime(2026, 11, 7),
            )
            with pytest.raises(ConflictError):
                FreelanceClosureService().cancel_draft_contract(
                    second, ctx=ctx, contract_id=contract_id
                )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(activate), pool.submit(cancel)
        try:
            assert attempting.wait(10)
            assert not second.done()
        finally:
            allow_commit.set()
        first.result(timeout=15)
        second.result(timeout=15)
    with Session(mariadb_db) as check:
        assert check.get(FreelanceContract, contract_id).status == "ACTIVE"
        assert (
            check.query(ProjectContractBudget).filter_by(contract_id=contract_id).one().status
            == "COMMITTED"
        )


def _selection_seed(engine, *, budget=5000000, capacity=2):
    from sqlalchemy.orm import Session

    from tests.freelancer.test_group_c_contracts import contract_fixtures

    with Session(engine) as db:
        f = contract_fixtures.__wrapped__(db)
        f["project"].recruitment_status = "OPEN"
        f["project"].budget_amount = budget
        f["project"].max_students = capacity
        result = f["project"].id, f["client"].id, f["app1"].id, f["app2"].id
        db.commit()
        return result


@pytest.mark.parametrize("capacity,budget", [(2, 3000000), (1, 5000000)])
def test_concurrent_selection_cannot_exceed_budget(mariadb_db, capacity, budget):
    from threading import Barrier

    from sqlalchemy.orm import Session

    from app.core.exceptions import ConflictError
    from app.models import FreelanceContract, ProjectContractBudget
    from app.schemas.freelance_projects import SelectStudent
    from app.services.freelance_project_service import select_in_tx
    from app.services.freelancer_commands import run_command

    pid, uid, a, b = _selection_seed(mariadb_db, budget=budget, capacity=capacity)
    start = Barrier(2)

    def select_one(aid):
        with Session(mariadb_db, autoflush=False) as db:
            start.wait(timeout=10)
            try:
                run_command(
                    db,
                    lambda: select_in_tx(
                        db,
                        user_id=uid,
                        project_id=pid,
                        payload=SelectStudent(application_id=aid, allocated_amount=2000000),
                        key=f"select:{aid}",
                    ),
                )
                return True
            except ConflictError:
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(select_one, [a, b]))
    assert sorted(outcomes) == [False, True]
    with Session(mariadb_db) as db:
        assert db.query(FreelanceContract).count() == 1
        assert sum(x.allocated_amount for x in db.query(ProjectContractBudget)) == 2000000


def test_same_candidate_and_key_replay_across_connections(mariadb_db):
    from threading import Barrier

    from sqlalchemy.orm import Session

    from app.models import CommandRequest, FreelanceContract
    from app.schemas.freelance_projects import SelectStudent
    from app.services.freelance_project_service import select_in_tx
    from app.services.freelancer_commands import run_command

    pid, uid, aid, _ = _selection_seed(mariadb_db)
    start = Barrier(2)

    def select_one(_):
        with Session(mariadb_db, autoflush=False) as db:
            start.wait(timeout=10)
            return run_command(
                db,
                lambda: select_in_tx(
                    db,
                    user_id=uid,
                    project_id=pid,
                    payload=SelectStudent(application_id=aid, allocated_amount=2000000),
                    key="same-candidate",
                ),
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(select_one, range(2)))
    assert responses[0] == responses[1]
    with Session(mariadb_db) as db:
        assert db.query(FreelanceContract).count() == 1 and db.query(CommandRequest).count() == 1


def test_two_workers_claim_distinct_rows(mariadb_db):
    from datetime import datetime, timedelta, timezone
    from threading import Barrier

    from sqlalchemy.orm import Session

    from app.models import OutboxEvent
    from app.services.freelancer_worker import claim

    with Session(mariadb_db) as db:
        for i in range(2):
            db.add(
                OutboxEvent(
                    event_key=f"worker:{i}",
                    event_type="notification",
                    entity_type="test",
                    entity_id=i + 1,
                    payload_json={},
                    available_at=datetime.now(timezone.utc).replace(tzinfo=None)
                    - timedelta(seconds=1),
                )
            )
        db.commit()
    start = Barrier(2)

    def claim_one(number):
        with Session(mariadb_db) as db:
            start.wait(timeout=10)
            return claim(db, OutboxEvent, f"worker-{number}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(claim_one, range(2)))
    assert None not in ids and len(set(ids)) == 2


def test_accept_vs_dispute_serializes_domain_transition(mariadb_db):
    """Explicit finance doubles; proves domain serialization, not ledger correctness."""
    from datetime import datetime, timedelta, timezone
    from threading import Barrier

    from sqlalchemy.orm import Session

    from app.core.exceptions import ConflictError
    from app.models import Deliverable, EscrowAccount, LedgerAccount, Milestone
    from app.schemas.freelancer_disputes import DisputeCreate
    from app.services.deliverable_service import DeliverableWorkService
    from app.services.dispute_service import open_in_tx
    from app.services.freelancer_commands import accept_milestone, run_command
    from app.services.freelancer_domain import ctx
    from tests.freelancer.fakes import FakeFinancePort
    from tests.freelancer.test_group_c_milestones_deliverables import active_contract_fixtures

    at = datetime.now(timezone.utc).replace(tzinfo=None)
    with Session(mariadb_db, expire_on_commit=False) as db:
        f = active_contract_fixtures.__wrapped__(db)
        m = f["ms1"]
        m.status = "SUBMITTED"
        m.review_deadline = at + timedelta(days=2)
        la = LedgerAccount(
            code="RACE:ESCROW", kind="ESCROW_HELD", normal_side="C", milestone_id=m.id
        )
        db.add(la)
        db.flush()
        db.add(EscrowAccount(milestone_id=m.id, ledger_account_id=la.id, funded_amount=1500000))
        d = Deliverable(
            milestone_id=m.id,
            submission_no=1,
            submitted_by=f["student"].id,
            note="Finished",
            submitted_at=at,
        )
        db.add(d)
        db.flush()
        mid, uid, sid, did = m.id, f["client"].id, f["student"].id, d.id
        db.commit()
    start = Barrier(2)

    def action(kind):
        with Session(mariadb_db, autoflush=False) as db:
            start.wait(timeout=10)
            try:
                if kind == "accept":
                    accept_milestone(
                        db,
                        ctx=ctx(uid),
                        milestone_id=mid,
                        deliverable_id=did,
                        work=DeliverableWorkService(),
                        finance=FakeFinancePort(funded=True),
                    )
                else:
                    run_command(
                        db,
                        lambda: open_in_tx(
                            db,
                            user_id=sid,
                            milestone_id=mid,
                            payload=DisputeCreate(reason_code="QUALITY", description="Disagree"),
                            finance=FakeFinancePort(funded=True),
                        ),
                    )
                return True
            except ConflictError:
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(action, ["accept", "dispute"]))
    assert sorted(outcomes) == [False, True]
    with Session(mariadb_db) as db:
        assert db.get(Milestone, mid).status in ("ACCEPTED", "DISPUTED")
