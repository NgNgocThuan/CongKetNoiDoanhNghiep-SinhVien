from datetime import datetime

import pytest
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.contracts.freelancer.types import AcceptanceRef, CommandContext
from app.core.freelancer_enums import ActorType
from app.models import (
    CommandRequest,
    ContractVersion,
    EscrowAccount,
    FreelanceContract,
    FreelanceProject,
    LedgerAccount,
)
from app.schemas.freelancer_common import EntityId, MoneyVnd
from app.services.freelancer_commands import accept_milestone, run_command
from app.services.freelancer_finance import FinanceNotReadyError, get_finance_port


def test_two_contracts_are_allowed_but_same_student_is_not(foundation_db, two_contract_project):
    project, contracts = two_contract_project
    assert contracts[0].id != contracts[1].id
    assert foundation_db.scalar(select(func.count()).select_from(FreelanceContract)) == 2
    foundation_db.add(FreelanceContract(
        project_id=project.id, application_id=contracts[1].application_id,
        client_user_id=project.client_user_id,
        freelancer_student_id=contracts[0].freelancer_student_id,
    ))
    with pytest.raises(IntegrityError):
        foundation_db.flush()
    foundation_db.rollback()


def test_effective_version_cannot_belong_to_other_contract(foundation_db, two_contract_project):
    project, (first, second) = two_contract_project
    version = ContractVersion(
        contract_id=second.id, version_no=1, created_by=project.client_user_id,
        total_amount=2000000, fee_rate_bp=500, review_period_seconds=3600,
        max_revision_count=2, grace_period_seconds=3600, funding_policy="FULL", terms_json={},
    )
    foundation_db.add(version)
    foundation_db.commit()
    first.effective_version_id = version.id
    with pytest.raises(IntegrityError):
        foundation_db.flush()
    foundation_db.rollback()


def test_escrow_cannot_spend_more_than_funding(foundation_db, two_contract_project):
    from app.models import Milestone

    _, (contract, _) = two_contract_project
    milestone = Milestone(contract_id=contract.id, sequence_no=1)
    foundation_db.add(milestone)
    foundation_db.flush()
    account = LedgerAccount(code="ESCROW:1", kind="ESCROW_HELD", normal_side="C", milestone_id=milestone.id)
    foundation_db.add(account)
    foundation_db.flush()
    foundation_db.add(EscrowAccount(
        milestone_id=milestone.id, ledger_account_id=account.id,
        funded_amount=100, reserved_amount=40, released_gross=61,
    ))
    with pytest.raises(IntegrityError):
        foundation_db.flush()
    foundation_db.rollback()


def test_acceptance_rolls_back_when_finance_unavailable(foundation_db, two_contract_project, command_context):
    project, _ = two_contract_project

    class Work:
        def record_acceptance_in_tx(self, db, **kwargs):
            # A flushed module change must be rolled back with financial failure.
            db.get(FreelanceProject, project.id).title = "Should roll back"
            db.flush()
            return AcceptanceRef(
                review_id=1, milestone_id=1, deliverable_id=1, source="MANUAL",
                accepted_at=command_context.now_utc,
            )

    with pytest.raises(FinanceNotReadyError):
        accept_milestone(
            foundation_db, ctx=command_context, milestone_id=1, deliverable_id=1,
            work=Work(), finance=get_finance_port(),
        )
    assert foundation_db.get(FreelanceProject, project.id).title == "Two students"


def test_command_handles_read_autobegin(foundation_db, two_contract_project):
    project, _ = two_contract_project
    foundation_db.execute(select(FreelanceProject))
    assert foundation_db.in_transaction()

    def operation():
        foundation_db.get(FreelanceProject, project.id).title = "Committed"
        return project.id

    assert run_command(foundation_db, operation) == project.id
    foundation_db.expire_all()
    assert foundation_db.get(FreelanceProject, project.id).title == "Committed"


def test_command_rejects_unrelated_pending_changes(foundation_db, two_contract_project):
    project, _ = two_contract_project
    project.title = "Someone else's write"
    with pytest.raises(ValueError, match="exclusive session"):
        run_command(foundation_db, lambda: None)
    foundation_db.rollback()


def test_request_key_is_unique_per_actor_operation(foundation_db, two_contract_project):
    project, _ = two_contract_project
    for _ in range(2):
        foundation_db.add(CommandRequest(
            actor_user_id=project.client_user_id, operation="select_student",
            idempotency_key="same", request_hash="a" * 64,
        ))
    with pytest.raises(IntegrityError):
        foundation_db.flush()
    foundation_db.rollback()


@pytest.mark.parametrize("value", [True, 1.5, "1.5", "-1", -1, 2**63])
def test_money_rejects_non_integer_or_out_of_range(value):
    with pytest.raises(ValidationError):
        TypeAdapter(MoneyVnd).validate_python(value)


def test_money_and_ids_preserve_large_integers_in_json():
    value = 9007199254740993
    assert TypeAdapter(MoneyVnd).dump_json(value) == b'"9007199254740993"'
    assert TypeAdapter(EntityId).validate_python(str(value)) == value


def test_context_requires_authenticated_user_and_utc():
    with pytest.raises(ValueError, match="authenticated actor"):
        CommandContext(actor_user_id=None, actor_type=ActorType.USER,
                       request_id="x", idempotency_key=None, now_utc=datetime(2026, 11, 4))
