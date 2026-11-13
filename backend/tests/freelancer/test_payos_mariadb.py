"""Real MariaDB serialization for the financial writer, never the team DB."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole, UserStatus
from app.core.exceptions import ConflictError
from app.models import (
    Deliverable,
    Dispute,
    EscrowAccount,
    LedgerJournal,
    MoneyTransfer,
    PaymentOrder,
    PaymentTransaction,
    User,
)
from app.services import dispute_service
from app.services import freelancer_bank_service as banks
from app.services import freelancer_collection_service as collection
from app.services.deliverable_service import DeliverableWorkService
from app.services.freelancer_commands import run_command
from app.services.freelancer_domain import ctx, now
from app.services.freelancer_financial_writer import DatabaseFinancePort
from tests.freelancer.test_group_c_milestones_deliverables import (
    active_contract_fixtures as _active,
)
from tests.freelancer.test_mariadb import mariadb_db as _mariadb
from tests.freelancer.test_payos_finance import configured as _configured
from tests.freelancer.test_payos_finance import receipt_data

pytestmark = pytest.mark.mariadb


@pytest.fixture
def mariadb_db(monkeypatch):
    yield from _mariadb.__wrapped__(monkeypatch)


@pytest.fixture
def money_db(mariadb_db, monkeypatch):
    _configured.__wrapped__(monkeypatch)
    with Session(mariadb_db, expire_on_commit=False) as db:
        f = _active.__wrapped__(db)
        f["ms1"].status = "NOT_FUNDED"
        db.add(
            User(
                id=901,
                email="admin-money@example.test",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
            )
        )
        db.commit()
        for uid in (f["client"].id, f["student"].id):
            result = run_command(
                db,
                lambda uid=uid: banks.add_in_tx(
                    db,
                    user_id=uid,
                    bank_bin="970422",
                    account_number="111111" + str(uid),
                    account_name="Verified recipient",
                ),
            )
        result = run_command(
            db,
            lambda: collection.create_in_tx(db, user_id=1, milestone_id=601, key="mariadb-money"),
        )
        return mariadb_db, int(result["id"])


def test_duplicate_receipt_race_posts_exactly_once(money_db):
    engine, order_id = money_db
    barrier = Barrier(2)

    def receive():
        with Session(engine) as db:
            # Both begin with an older REPEATABLE READ snapshot before the gate.
            row = db.get(PaymentOrder, order_id)
            data = receipt_data(row)
            barrier.wait(timeout=10)
            return run_command(db, lambda: collection.apply_receipt_in_tx(db, data=data)).id

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: receive(), range(2)))
    assert results[0] == results[1]
    with Session(engine) as db:
        assert db.query(PaymentTransaction).count() == 1
        assert db.query(EscrowAccount).one().funded_amount == 1500000
        assert db.query(LedgerJournal).count() == 2


def test_real_acceptance_and_dispute_cannot_both_reserve(money_db):
    from app.models import Milestone
    from app.schemas.freelancer_disputes import DisputeCreate

    engine, order_id = money_db
    with Session(engine, expire_on_commit=False) as db:
        order = db.get(PaymentOrder, order_id)
        data = receipt_data(order)
        run_command(db, lambda: collection.apply_receipt_in_tx(db, data=data))
        m = db.get(Milestone, 601)
        m.status = "SUBMITTED"
        from datetime import timedelta

        m.review_deadline = now() + timedelta(days=7)
        delivery = Deliverable(
            milestone_id=m.id, submission_no=1, submitted_by=2, note="Ready", submitted_at=now()
        )
        db.add(delivery)
        db.commit()
        delivery_id = delivery.id
    barrier = Barrier(2)

    def compete(kind):
        with Session(engine) as db:
            db.scalar(select(Milestone.id))
            barrier.wait(timeout=10)

            def operation():
                if kind == "accept":
                    review = DeliverableWorkService().record_acceptance_in_tx(
                        db,
                        ctx=ctx(1),
                        milestone_id=601,
                        deliverable_id=delivery_id,
                        source="MANUAL",
                    )
                    return DatabaseFinancePort().prepare_acceptance_settlement_in_tx(
                        db, ctx=ctx(1), review_id=review.review_id
                    )
                return dispute_service.open_in_tx(
                    db,
                    user_id=1,
                    milestone_id=601,
                    payload=DisputeCreate(
                        reason_code="QUALITY", description="Needs dispute review"
                    ),
                )

            try:
                run_command(db, operation)
                return True
            except ConflictError:
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, ("accept", "dispute")))
    assert sum(results) == 1
    with Session(engine) as db:
        assert db.query(Dispute).count() + db.query(MoneyTransfer).count() == 1
