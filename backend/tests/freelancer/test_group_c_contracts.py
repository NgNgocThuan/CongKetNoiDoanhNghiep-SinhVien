"""Tests for Group C: Tickets C1 and C2 (Contracts, Versions, Negotiations, Budget Locking)."""

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    register_exception_handlers,
)
from app.core.freelancer_enums import (
    ActorType,
    ContractBudgetStatus,
    ContractStatus,
    ContractVersionStatus,
    FreelanceApplicationStatus,
    FundingPolicy,
    MilestoneStatus,
    ProjectStatus,
    ScheduledJobStatus,
)
from app.models import (
    Base,
    Faculty,
    FreelanceApplication,
    FreelanceContract,
    FreelanceProject,
    Major,
    ProjectContractBudget,
    Student,
    User,
)
from app.models.freelancer_contracts import (
    ContractVersion,
    Milestone,
)
from app.models.freelancer_operations import AuditLog, ScheduledJob
from app.models.freelancer_payments import MilestoneFunding, MilestoneFundingGuard, PaymentOrder
from app.routers.freelance_contracts import router as contracts_router
from app.schemas.freelance_contracts import (
    ContractVersionCreate,
    MilestoneTermInput,
)
from app.services.freelance_contract_service import (
    FreelanceContractService,
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def contract_fixtures(db_session):
    db = db_session
    client_user = User(
        id=1,
        email="client@test.com",
        role=UserRole.CLIENT,
        status=UserStatus.ACTIVE,
        email_verified_at=datetime(2026, 1, 1),
        phone_verified_at=datetime(2026, 1, 1),
    )
    student1_user = User(
        id=2, email="student1@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE
    )
    student2_user = User(
        id=3, email="student2@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE
    )
    outsider_user = User(
        id=4, email="outsider@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE
    )
    admin_user = User(id=5, email="admin@test.com", role=UserRole.ADMIN, status=UserStatus.ACTIVE)
    db.add_all([client_user, student1_user, student2_user, outsider_user, admin_user])
    db.flush()

    faculty = Faculty(code="CS", name="Computer Science")
    db.add(faculty)
    db.flush()
    major = Major(code="SE", name="Software Engineering", faculty_id=faculty.id)
    db.add(major)
    db.flush()

    s1 = Student(
        id=10,
        user_id=student1_user.id,
        student_code="SV001",
        full_name="Student One",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="2026",
    )
    s2 = Student(
        id=20,
        user_id=student2_user.id,
        student_code="SV002",
        full_name="Student Two",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="2026",
    )
    s_out = Student(
        id=30,
        user_id=outsider_user.id,
        student_code="SV003",
        full_name="Outsider",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="2026",
    )
    db.add_all([s1, s2, s_out])
    db.flush()

    project = FreelanceProject(
        id=100,
        client_user_id=client_user.id,
        title="AI Chatbot",
        description="Build bot",
        budget_amount=5000000,
        max_students=2,
        deadline=datetime(2026, 12, 31),
        acceptance_criteria="Pass test",
        deliverables_description="Code and docs",
        funding_policy=FundingPolicy.PER_MILESTONE,
        status=ProjectStatus.APPROVED,
    )
    db.add(project)
    db.flush()

    app1 = FreelanceApplication(
        id=1001,
        project_id=project.id,
        student_id=s1.id,
        proposal="I can do it",
        quoted_amount=2000000,
        estimated_days=10,
        status=FreelanceApplicationStatus.SUBMITTED,
    )
    app2 = FreelanceApplication(
        id=1002,
        project_id=project.id,
        student_id=s2.id,
        proposal="Me too",
        quoted_amount=2500000,
        estimated_days=14,
        status=FreelanceApplicationStatus.SHORTLISTED,
    )
    db.add_all([app1, app2])
    db.commit()

    return {
        "client": client_user,
        "student1": student1_user,
        "student2": student2_user,
        "outsider": outsider_user,
        "admin": admin_user,
        "s1": s1,
        "s2": s2,
        "s_out": s_out,
        "project": project,
        "app1": app1,
        "app2": app2,
    }


def make_ctx(actor_user_id: int, request_id="req-1", key=None, now_utc=None) -> CommandContext:
    return CommandContext(
        actor_user_id=actor_user_id,
        actor_type=ActorType.USER,
        request_id=request_id,
        idempotency_key=key,
        now_utc=now_utc or datetime(2026, 11, 4, 12, 0, 0),
    )


# =============================================================================
# C1 Tests
# =============================================================================


def test_c1_create_contract_success(db_session, contract_fixtures):
    f = contract_fixtures
    service = FreelanceContractService()
    ctx = make_ctx(f["client"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    assert ref.contract_id is not None
    assert ref.project_id == f["project"].id
    assert ref.student_id == f["s1"].id
    assert ref.status == ContractStatus.DRAFT
    assert ref.allocated_amount == 2000000

    # Verify application status transition to SELECTED
    db_session.refresh(f["app1"])
    assert f["app1"].status == FreelanceApplicationStatus.SELECTED
    assert f["app1"].selected_at is not None

    # Verify ProjectContractBudget created
    budget = db_session.query(ProjectContractBudget).filter_by(contract_id=ref.contract_id).first()
    assert budget is not None
    assert budget.allocated_amount == 2000000
    assert budget.status == ContractBudgetStatus.RESERVED

    # Verify AuditLog
    audit = (
        db_session.query(AuditLog)
        .filter_by(entity_id=ref.contract_id, action="contract.created_from_selection")
        .first()
    )
    assert audit is not None


def test_c1_create_contract_idempotent_replay(db_session, contract_fixtures):
    f = contract_fixtures
    service = FreelanceContractService()
    ctx = make_ctx(f["client"].id)

    ref1 = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )
    # Replay identical
    ref2 = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )
    assert ref1.contract_id == ref2.contract_id

    # Replay with different amount raises IDEMPOTENCY_CONFLICT
    with pytest.raises(ConflictError) as exc:
        service.create_contract_for_selected_application_in_tx(
            db_session,
            ctx=ctx,
            project_id=f["project"].id,
            application_id=f["app1"].id,
            allocated_amount=2500000,
        )
    assert exc.value.code == "IDEMPOTENCY_CONFLICT"


def test_c1_capacity_and_budget_exceeded(db_session, contract_fixtures):
    f = contract_fixtures
    service = FreelanceContractService()
    ctx = make_ctx(f["client"].id)

    # 1. Budget exceeded
    with pytest.raises(ConflictError) as exc:
        service.create_contract_for_selected_application_in_tx(
            db_session,
            ctx=ctx,
            project_id=f["project"].id,
            application_id=f["app1"].id,
            allocated_amount=6000000,
        )
    assert exc.value.code == "PROJECT_BUDGET_EXCEEDED"

    # Contract 1: 3,000,000
    service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=3000000,
    )
    # Contract 2: 2,000,000 (total = 5,000,000 = max budget, max_students = 2)
    service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx,
        project_id=f["project"].id,
        application_id=f["app2"].id,
        allocated_amount=2000000,
    )

    # Attempt 3rd contract with a 3rd student -> Capacity exceeded
    app3 = FreelanceApplication(
        project_id=f["project"].id,
        student_id=f["s_out"].id,
        proposal="Third",
        quoted_amount=100000,
        estimated_days=2,
        status=FreelanceApplicationStatus.SUBMITTED,
    )
    db_session.add(app3)
    db_session.flush()

    with pytest.raises(ConflictError) as exc:
        service.create_contract_for_selected_application_in_tx(
            db_session,
            ctx=ctx,
            project_id=f["project"].id,
            application_id=app3.id,
            allocated_amount=100000,
        )
    assert exc.value.code == "PROJECT_CAPACITY_EXCEEDED"


# =============================================================================
# C2 Tests: Versioning, Negotiations, Content Hash, Offers, Acceptances
# =============================================================================


def test_c2_version_lifecycle_and_content_hash(db_session, contract_fixtures):
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)
    ctx_student = make_ctx(f["student1"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    # 1. Create version DRAFT by Student
    terms_payload = ContractVersionCreate(
        total_amount=2000000,
        fee_rate_bp=500,
        review_period_seconds=604800,
        max_revision_count=3,
        grace_period_seconds=259200,
        funding_policy=FundingPolicy.PER_MILESTONE,
        milestone_terms=[
            MilestoneTermInput(
                title="Design",
                amount=800000,
                acceptance_criteria="Figma approved",
                due_at=datetime(2026, 11, 20),
                included=True,
            ),
            MilestoneTermInput(
                title="Implementation",
                amount=1200000,
                acceptance_criteria="Working code",
                due_at=datetime(2026, 12, 10),
                included=True,
            ),
        ],
    )

    v1 = service.create_version_in_tx(
        db_session, ctx=ctx_student, contract_id=ref.contract_id, payload=terms_payload
    )
    assert v1.version_no == 1
    assert v1.status == ContractVersionStatus.DRAFT
    assert v1.content_hash is not None

    # Check milestone count created
    milestones = db_session.query(Milestone).filter_by(contract_id=ref.contract_id).all()
    assert len(milestones) == 2

    # 2. Student offers version 1
    v1_offered = service.offer_version_in_tx(db_session, ctx=ctx_student, version_id=v1.id)
    assert v1_offered.status == ContractVersionStatus.OFFERED
    assert v1_offered.freelancer_accepted_at is not None
    assert v1_offered.client_accepted_at is None

    contract = db_session.get(FreelanceContract, ref.contract_id)
    assert contract.status == ContractStatus.PENDING_ACCEPTANCE

    # Check ScheduledJob created for expire
    job = (
        db_session.query(ScheduledJob).filter_by(job_key=f"contract_version.expire:{v1.id}").first()
    )
    assert job is not None
    assert job.status == ScheduledJobStatus.PENDING

    # 3. Client accepts with wrong hash -> Fail
    with pytest.raises(ConflictError) as exc:
        service.accept_version_in_tx(
            db_session, ctx=ctx_client, version_id=v1.id, content_hash="wrong-hash"
        )
    assert exc.value.code == "CONTRACT_VERSION_CONFLICT"

    # 4. Client accepts with exact content_hash
    v1_effective = service.accept_version_in_tx(
        db_session, ctx=ctx_client, version_id=v1.id, content_hash=v1.content_hash
    )
    assert v1_effective.status == ContractVersionStatus.EFFECTIVE
    assert v1_effective.client_accepted_at is not None
    assert v1_effective.effective_at is not None

    contract = db_session.get(FreelanceContract, ref.contract_id)
    assert contract.status == ContractStatus.ACTIVE
    assert contract.effective_version_id == v1.id

    # Verify ProjectContractBudget is COMMITTED
    budget = db_session.query(ProjectContractBudget).filter_by(contract_id=contract.id).first()
    assert budget.status == ContractBudgetStatus.COMMITTED

    # Verify project transitioned to IN_PROGRESS (first active contract)
    proj = db_session.get(FreelanceProject, contract.project_id)
    assert proj.status == ProjectStatus.IN_PROGRESS

    # Verify milestones have effective_terms_id assigned
    ms1 = db_session.query(Milestone).filter_by(contract_id=contract.id, sequence_no=1).first()
    assert ms1.effective_terms_id is not None

    # Verify financial terms retrieval (C1)
    # Leaving school must not block settlement of an existing obligation.
    from app.models import Student
    departing_student = db_session.get(Student, contract.freelancer_student_id)
    departing_student.academic_status = "WITHDRAWN"
    db_session.flush()
    fin_terms = service.get_milestone_financial_terms(db_session, milestone_id=ms1.id)
    assert fin_terms.amount == 800000
    assert fin_terms.fee_rate_bp == 500
    assert fin_terms.funding_policy == FundingPolicy.PER_MILESTONE


def test_c2_immutable_terms_guard(db_session, contract_fixtures):
    """Funded, guarded, or started milestone terms cannot be mutated in newer versions."""
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)
    ctx_student = make_ctx(f["student1"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    # v1 with 1 milestone
    v1 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="Phase 1",
                    amount=2000000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 1),
                    included=True,
                )
            ],
        ),
    )
    service.offer_version_in_tx(db_session, ctx=ctx_client, version_id=v1.id)
    service.accept_version_in_tx(
        db_session, ctx=ctx_student, version_id=v1.id, content_hash=v1.content_hash
    )

    # Simulate milestone funded guard installed
    ms1 = db_session.query(Milestone).filter_by(contract_id=ref.contract_id, sequence_no=1).first()
    po = PaymentOrder(
        milestone_id=ms1.id,
        payer_user_id=f["client"].id,
        expected_amount=2000000,
        order_code=123456,
        request_key="test-order",
        request_hash="hash",
        receiving_account_snapshot={},
        expires_at=datetime(2026, 12, 1),
    )
    db_session.add(po)
    db_session.flush()
    guard = MilestoneFundingGuard(milestone_id=ms1.id, payment_order_id=po.id)
    db_session.add(guard)
    db_session.flush()

    # Now attempt to propose v2 changing Phase 1 amount to 1,500,000 -> must raise TERMS_IMMUTABLE
    with pytest.raises(ConflictError) as exc:
        service.create_version_in_tx(
            db_session,
            ctx=ctx_client,
            contract_id=ref.contract_id,
            payload=ContractVersionCreate(
                total_amount=1500000,
                funding_policy=FundingPolicy.PER_MILESTONE,
                milestone_terms=[
                    MilestoneTermInput(
                        title="Phase 1",
                        amount=1500000,
                        acceptance_criteria="All done",
                        due_at=datetime(2026, 12, 1),
                        included=True,
                    )
                ],
            ),
        )
    assert exc.value.code == "TERMS_IMMUTABLE"


def test_c2_immutable_terms_rechecked_on_offer_and_accept(db_session, contract_fixtures):
    """Terms are rechecked during offer_version_in_tx and accept_version_in_tx against funded milestones."""
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)
    ctx_student = make_ctx(f["student1"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    # v1 with 2 milestones
    v1 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="Phase 1",
                    amount=1000000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 1),
                    included=True,
                ),
                MilestoneTermInput(
                    title="Phase 2",
                    amount=1000000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 15),
                    included=True,
                ),
            ],
        ),
    )
    service.offer_version_in_tx(db_session, ctx=ctx_client, version_id=v1.id)
    service.accept_version_in_tx(
        db_session, ctx=ctx_student, version_id=v1.id, content_hash=v1.content_hash
    )

    # 1. Test offer re-check: Create v2 DRAFT modifying Phase 1 BEFORE milestone is funded
    v2 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="Phase 1 Modified",
                    amount=1200000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 1),
                    included=True,
                ),
                MilestoneTermInput(
                    title="Phase 2",
                    amount=800000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 15),
                    included=True,
                ),
            ],
        ),
    )
    assert v2.status == ContractVersionStatus.DRAFT

    # Now Phase 1 is funded after v2 was created
    ms1 = db_session.query(Milestone).filter_by(contract_id=ref.contract_id, sequence_no=1).first()
    ms1.status = MilestoneStatus.FUNDED
    db_session.flush()

    # Calling offer_version_in_tx must catch this and reject
    with pytest.raises(ConflictError) as exc:
        service.offer_version_in_tx(db_session, ctx=ctx_client, version_id=v2.id)
    assert exc.value.code == "TERMS_IMMUTABLE"

    # Reset ms1 to NOT_FUNDED temporarily to create and offer v3
    ms1.status = MilestoneStatus.NOT_FUNDED
    db_session.flush()

    v3 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="Phase 1 Changed Again",
                    amount=1100000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 1),
                    included=True,
                ),
                MilestoneTermInput(
                    title="Phase 2",
                    amount=900000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 15),
                    included=True,
                ),
            ],
        ),
    )
    service.offer_version_in_tx(db_session, ctx=ctx_client, version_id=v3.id)
    assert v3.status == ContractVersionStatus.OFFERED

    # Now Phase 1 gets funded while v3 is OFFERED before student accepts
    ms1.status = MilestoneStatus.FUNDED
    db_session.flush()

    # Student attempting to accept v3 must be blocked by accept_version_in_tx recheck
    with pytest.raises(ConflictError) as exc_acc:
        service.accept_version_in_tx(
            db_session, ctx=ctx_student, version_id=v3.id, content_hash=v3.content_hash
        )
    assert exc_acc.value.code == "TERMS_IMMUTABLE"


def test_c2_immutable_terms_with_milestone_funding(db_session, contract_fixtures):
    """Milestone with MilestoneFunding record cannot have its terms modified."""
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)
    ctx_student = make_ctx(f["student1"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    v1 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="Phase 1",
                    amount=2000000,
                    acceptance_criteria="All done",
                    due_at=datetime(2026, 12, 1),
                    included=True,
                )
            ],
        ),
    )
    service.offer_version_in_tx(db_session, ctx=ctx_client, version_id=v1.id)
    service.accept_version_in_tx(
        db_session, ctx=ctx_student, version_id=v1.id, content_hash=v1.content_hash
    )

    ms1 = db_session.query(Milestone).filter_by(contract_id=ref.contract_id, sequence_no=1).first()
    # Add MilestoneFunding record with valid parent FK rows
    from app.core.freelancer_enums import PaymentAllocationStatus
    from app.models.freelancer_ledger import LedgerJournal
    from app.models.freelancer_payments import PaymentTransaction

    lj1 = LedgerJournal(
        reference_type="PAYMENT",
        reference_id=1,
        idempotency_key="key-test-1",
        description="receipt journal",
        posted_at=datetime(2026, 12, 1),
    )
    db_session.add(lj1)
    db_session.flush()

    pt = PaymentTransaction(
        channel_key="test-channel",
        external_ref="ext-ref-1",
        amount=2000000,
        currency="VND",
        receiving_account_ref="acc-1",
        received_at=datetime(2026, 12, 1),
        allocation_status=PaymentAllocationStatus.UNALLOCATED,
        receipt_journal_id=lj1.id,
        raw_payload_json={},
    )
    db_session.add(pt)
    db_session.flush()

    lj2 = LedgerJournal(
        reference_type="FUNDING",
        reference_id=1,
        idempotency_key="key-test-2",
        description="funding journal",
        posted_at=datetime(2026, 12, 1),
    )
    db_session.add(lj2)
    db_session.flush()

    mf = MilestoneFunding(
        milestone_id=ms1.id,
        payment_transaction_id=pt.id,
        amount=2000000,
        funding_journal_id=lj2.id,
    )
    db_session.add(mf)
    db_session.flush()

    with pytest.raises(ConflictError) as exc:
        service.create_version_in_tx(
            db_session,
            ctx=ctx_client,
            contract_id=ref.contract_id,
            payload=ContractVersionCreate(
                total_amount=1500000,
                funding_policy=FundingPolicy.PER_MILESTONE,
                milestone_terms=[
                    MilestoneTermInput(
                        title="Phase 1",
                        amount=1500000,
                        acceptance_criteria="Modified",
                        due_at=datetime(2026, 12, 1),
                        included=True,
                    )
                ],
            ),
        )
    assert exc.value.code == "TERMS_IMMUTABLE"


def test_c2_zero_leak_ownership(db_session, contract_fixtures):
    """Outsider user accessing contract or version receives 404 NOT_FOUND."""
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)
    ctx_outsider = make_ctx(f["outsider"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    # Outsider viewing contract -> 404
    with pytest.raises(NotFoundError) as exc:
        service.get_contract(
            db_session, contract_id=ref.contract_id, actor_user_id=ctx_outsider.actor_user_id
        )
    assert exc.value.code == "NOT_FOUND"

    # Outsider creating version -> 404
    with pytest.raises(NotFoundError) as exc:
        service.create_version_in_tx(
            db_session,
            ctx=ctx_outsider,
            contract_id=ref.contract_id,
            payload=ContractVersionCreate(
                total_amount=2000000,
                funding_policy=FundingPolicy.PER_MILESTONE,
                milestone_terms=[
                    MilestoneTermInput(
                        title="T",
                        amount=2000000,
                        acceptance_criteria="C",
                        due_at=datetime(2026, 12, 1),
                    )
                ],
            ),
        )
    assert exc.value.code == "NOT_FOUND"

    # Admin CAN view
    admin_view = service.get_contract(
        db_session, contract_id=ref.contract_id, actor_user_id=f["admin"].id, is_admin=True
    )
    assert admin_view.id == ref.contract_id


def test_c2_decline_and_withdraw_flow(db_session, contract_fixtures):
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)
    ctx_student = make_ctx(f["student1"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    # 1. Withdraw draft
    v1 = service.create_version_in_tx(
        db_session,
        ctx=ctx_student,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="T1",
                    amount=2000000,
                    acceptance_criteria="C1",
                    due_at=datetime(2026, 12, 1),
                )
            ],
        ),
    )
    v1_withdrawn = service.withdraw_version_in_tx(db_session, ctx=ctx_student, version_id=v1.id)
    assert v1_withdrawn.status == ContractVersionStatus.WITHDRAWN

    # 2. Offer and Decline
    v2 = service.create_version_in_tx(
        db_session,
        ctx=ctx_student,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="T2",
                    amount=2000000,
                    acceptance_criteria="C2",
                    due_at=datetime(2026, 12, 1),
                )
            ],
        ),
    )
    service.offer_version_in_tx(db_session, ctx=ctx_student, version_id=v2.id)

    # Client declines with note
    v2_declined = service.decline_version_in_tx(
        db_session, ctx=ctx_client, version_id=v2.id, response_note="Price too high"
    )
    assert v2_declined.status == ContractVersionStatus.DECLINED
    assert v2_declined.response_note == "Price too high"

    # Contract returns to DRAFT
    contract = db_session.get(FreelanceContract, ref.contract_id)
    assert contract.status == ContractStatus.DRAFT


def test_c2_contracts_router_http(db_session, contract_fixtures):
    """Test HTTP API endpoints for contract and version operations."""
    from app.dependencies import get_current_user, get_db

    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )
    db_session.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(contracts_router)

    current_actor = f["client"]

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: current_actor

    client = TestClient(app)

    # 1. GET contract
    resp = client.get(f"/freelance-contracts/{ref.contract_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(ref.contract_id)
    assert data["status"] == "DRAFT"
    assert data["allocated_amount"] == "2000000"

    # 2. POST create version DRAFT
    version_payload = {
        "total_amount": "2000000",
        "funding_policy": "PER_MILESTONE",
        "milestone_terms": [
            {
                "title": "Phase 1",
                "amount": "2000000",
                "acceptance_criteria": "Acceptance criteria 1",
                "due_at": "2026-12-01T00:00:00Z",
                "included": True,
            }
        ],
    }
    resp = client.post(f"/freelance-contracts/{ref.contract_id}/versions", json=version_payload)
    assert resp.status_code == 201
    v_data = resp.json()
    version_id = int(v_data["id"])
    content_hash = v_data["content_hash"]
    assert v_data["version_no"] == 1
    assert v_data["status"] == "DRAFT"

    # 3. GET versions
    resp = client.get(f"/freelance-contracts/{ref.contract_id}/versions")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1

    # 4. POST offer
    resp = client.post(f"/contract-versions/{version_id}/offer")
    assert resp.status_code == 200
    assert resp.json()["status"] == "OFFERED"

    # 5. Switch to student and POST accept
    current_actor = f["student1"]
    resp = client.post(
        f"/contract-versions/{version_id}/accept", json={"content_hash": content_hash}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "EFFECTIVE"

    # Verify contract is now ACTIVE
    resp = client.get(f"/freelance-contracts/{ref.contract_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"


def test_c2_version_expiration_and_persistence(db_session, contract_fixtures):
    """Expired offer raises 409 and persists EXPIRED status and DRAFT contract."""
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id, now_utc=datetime(2026, 11, 4))
    ctx_student_late = make_ctx(f["student1"].id, now_utc=datetime(2026, 11, 10))

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    v1 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="T1",
                    amount=2000000,
                    acceptance_criteria="C1",
                    due_at=datetime(2026, 12, 1),
                )
            ],
        ),
    )

    # Offer with deadline on 2026-11-06
    service.offer_version_in_tx(
        db_session, ctx=ctx_client, version_id=v1.id, acceptance_deadline=datetime(2026, 11, 6)
    )
    db_session.commit()

    # Student accepts after deadline
    with pytest.raises(ConflictError) as exc:
        service.accept_version(
            db_session,
            ctx=ctx_student_late,
            version_id=v1.id,
            content_hash=v1.content_hash,
        )
    assert exc.value.code == "CONTRACT_VERSION_CONFLICT"
    assert "expired" in exc.value.message.lower()

    # Verify version is persisted as EXPIRED and contract reverted to DRAFT
    v1_fresh = db_session.get(ContractVersion, v1.id)
    assert v1_fresh.status == ContractVersionStatus.EXPIRED

    contract_fresh = db_session.get(FreelanceContract, ref.contract_id)
    assert contract_fresh.status == ContractStatus.DRAFT


def test_c2_duplicate_accept_prevented(db_session, contract_fixtures):
    """A party cannot accept the same version twice."""
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    v1 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="T1",
                    amount=2000000,
                    acceptance_criteria="C1",
                    due_at=datetime(2026, 12, 1),
                )
            ],
        ),
    )
    # Client offers: client_accepted_at is set automatically
    service.offer_version_in_tx(db_session, ctx=ctx_client, version_id=v1.id)

    # Client tries to accept again
    with pytest.raises(ConflictError) as exc:
        service.accept_version_in_tx(
            db_session,
            ctx=ctx_client,
            version_id=v1.id,
            content_hash=v1.content_hash,
        )
    assert exc.value.code == "INVALID_STATE_TRANSITION"
    assert "already accepted" in exc.value.message.lower()


def test_c2_cannot_omit_or_modify_funded_milestone(db_session, contract_fixtures):
    """Cannot omit or alter terms of funded/guarded milestones in new version drafts."""
    f = contract_fixtures
    service = FreelanceContractService()
    ctx_client = make_ctx(f["client"].id)
    ctx_student = make_ctx(f["student1"].id)

    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=ctx_client,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )

    v1 = service.create_version_in_tx(
        db_session,
        ctx=ctx_client,
        contract_id=ref.contract_id,
        payload=ContractVersionCreate(
            total_amount=2000000,
            funding_policy=FundingPolicy.PER_MILESTONE,
            milestone_terms=[
                MilestoneTermInput(
                    title="M1",
                    amount=1000000,
                    acceptance_criteria="C1",
                    due_at=datetime(2026, 12, 1),
                ),
                MilestoneTermInput(
                    title="M2",
                    amount=1000000,
                    acceptance_criteria="C2",
                    due_at=datetime(2026, 12, 15),
                ),
            ],
        ),
    )
    service.offer_version_in_tx(db_session, ctx=ctx_client, version_id=v1.id)
    service.accept_version_in_tx(
        db_session, ctx=ctx_student, version_id=v1.id, content_hash=v1.content_hash
    )

    # Fund milestone 1 and milestone 2
    ms1 = db_session.query(Milestone).filter_by(contract_id=ref.contract_id, sequence_no=1).first()
    ms2 = db_session.query(Milestone).filter_by(contract_id=ref.contract_id, sequence_no=2).first()
    ms1.status = MilestoneStatus.FUNDED
    ms2.status = MilestoneStatus.FUNDED
    db_session.flush()

    # Attempt to create V2 omitting M2 (only 1 term given) -> TERMS_IMMUTABLE
    with pytest.raises(ConflictError) as exc:
        service.create_version_in_tx(
            db_session,
            ctx=ctx_client,
            contract_id=ref.contract_id,
            payload=ContractVersionCreate(
                total_amount=1000000,
                funding_policy=FundingPolicy.PER_MILESTONE,
                milestone_terms=[
                    MilestoneTermInput(
                        title="M1",
                        amount=1000000,
                        acceptance_criteria="C1",
                        due_at=datetime(2026, 12, 1),
                    ),
                ],
            ),
        )
    assert exc.value.code == "TERMS_IMMUTABLE"

    # Attempt to modify M1's title -> TERMS_IMMUTABLE
    with pytest.raises(ConflictError) as exc:
        service.create_version_in_tx(
            db_session,
            ctx=ctx_client,
            contract_id=ref.contract_id,
            payload=ContractVersionCreate(
                total_amount=2000000,
                funding_policy=FundingPolicy.PER_MILESTONE,
                milestone_terms=[
                    MilestoneTermInput(
                        title="M1 Modified",
                        amount=1000000,
                        acceptance_criteria="C1",
                        due_at=datetime(2026, 12, 1),
                    ),
                    MilestoneTermInput(
                        title="M2",
                        amount=1000000,
                        acceptance_criteria="C2",
                        due_at=datetime(2026, 12, 15),
                    ),
                ],
            ),
        )
    assert exc.value.code == "TERMS_IMMUTABLE"


@pytest.mark.parametrize("case", ["fee", "full"])
def test_server_policy_cannot_be_bypassed_in_contract_terms(db_session, contract_fixtures, case):
    f = contract_fixtures
    service = FreelanceContractService()
    context = make_ctx(f["client"].id)
    ref = service.create_contract_for_selected_application_in_tx(
        db_session,
        ctx=context,
        project_id=f["project"].id,
        application_id=f["app1"].id,
        allocated_amount=2000000,
    )
    if case == "full":
        f["project"].funding_policy = FundingPolicy.FULL
    db_session.commit()
    payload = ContractVersionCreate(
        total_amount=2000000,
        fee_rate_bp=0 if case == "fee" else 500,
        funding_policy=FundingPolicy.PER_MILESTONE,
        milestone_terms=[
            MilestoneTermInput(
                title="Scope",
                amount=2000000,
                acceptance_criteria="Pass review",
                due_at=datetime(2026, 12, 1),
            )
        ],
    )
    with pytest.raises(ConflictError):
        service.create_version(
            db_session, ctx=context, contract_id=ref.contract_id, payload=payload
        )
    assert db_session.query(ContractVersion).filter_by(contract_id=ref.contract_id).count() == 0
