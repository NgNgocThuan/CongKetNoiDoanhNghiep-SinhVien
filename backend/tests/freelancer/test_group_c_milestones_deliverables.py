"""Tests for Group C: Tickets C3, C4, C5 (Milestones, Deliverables, WorkPort, Acceptance)."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.core.freelancer_enums import (
    AcceptanceSource,
    ActorType,
    ContractBudgetStatus,
    ContractStatus,
    ContractVersionStatus,
    FileAvailability,
    FileScanStatus,
    FundingPolicy,
    MilestoneReviewAction,
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
    ContractMilestoneTerm,
    ContractVersion,
    DeliverableFile,
    Milestone,
    MilestoneReview,
)
from app.models.freelancer_disputes import ActiveMilestoneDispute, Dispute, MilestoneHold
from app.models.freelancer_identity import StoredFile
from app.models.freelancer_operations import ScheduledJob
from app.services.deliverable_service import (
    DeliverableService,
    DeliverableWorkService,
    accept_milestone_command,
)
from app.services.freelancer_finance import FinanceNotReadyError, UnavailableFinancePort
from app.services.milestone_service import MilestoneService
from tests.freelancer.fakes import FakeFinancePort


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
def active_contract_fixtures(db_session):
    db = db_session
    client_user = User(
        id=1,
        email="client@test.com",
        role=UserRole.CLIENT,
        status=UserStatus.ACTIVE,
        email_verified_at=datetime(2026, 1, 1),
        phone_verified_at=datetime(2026, 1, 1),
    )
    student_user = User(
        id=2, email="student@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE
    )
    outsider_user = User(
        id=3, email="outsider@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE
    )
    db.add_all([client_user, student_user, outsider_user])
    db.flush()

    faculty = Faculty(code="CS", name="Computer Science")
    db.add(faculty)
    db.flush()
    major = Major(code="SE", name="Software Engineering", faculty_id=faculty.id)
    db.add(major)
    db.flush()

    student = Student(
        id=10,
        user_id=student_user.id,
        student_code="SV001",
        full_name="Student",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="2026",
    )
    outsider_student = Student(
        id=20,
        user_id=outsider_user.id,
        student_code="SV002",
        full_name="Outsider",
        faculty_id=faculty.id,
        major_id=major.id,
        cohort="2026",
    )
    db.add_all([student, outsider_student])
    db.flush()

    project = FreelanceProject(
        id=100,
        client_user_id=client_user.id,
        title="Web App",
        description="Build app",
        budget_amount=3000000,
        max_students=2,
        deadline=datetime(2026, 12, 31),
        acceptance_criteria="Works",
        deliverables_description="Code",
        funding_policy=FundingPolicy.PER_MILESTONE,
        status=ProjectStatus.IN_PROGRESS,
    )
    db.add(project)
    db.flush()

    app = FreelanceApplication(
        id=1001,
        project_id=project.id,
        student_id=student.id,
        proposal="Let's do it",
        quoted_amount=3000000,
        estimated_days=15,
        status="SELECTED",
    )
    db.add(app)
    db.flush()

    contract = FreelanceContract(
        id=500,
        project_id=project.id,
        application_id=app.id,
        client_user_id=client_user.id,
        freelancer_student_id=student.id,
        status=ContractStatus.ACTIVE,
    )
    db.add(contract)
    db.flush()

    db.add(
        ProjectContractBudget(
            project_id=project.id,
            contract_id=contract.id,
            allocated_amount=3000000,
            status=ContractBudgetStatus.COMMITTED,
        )
    )
    db.flush()

    # Create Effective Version with 2 Milestones
    version = ContractVersion(
        id=200,
        contract_id=contract.id,
        version_no=1,
        created_by=client_user.id,
        status=ContractVersionStatus.EFFECTIVE,
        total_amount=3000000,
        fee_rate_bp=500,
        review_period_seconds=604800,  # 7 days
        max_revision_count=2,
        grace_period_seconds=259200,
        funding_policy=FundingPolicy.PER_MILESTONE,
        terms_json={},
        content_hash="canonical-hash-1",
    )
    db.add(version)
    db.flush()
    contract.effective_version_id = version.id

    ms1 = Milestone(
        id=601,
        contract_id=contract.id,
        sequence_no=1,
        status=MilestoneStatus.FUNDED,
    )
    ms2 = Milestone(
        id=602,
        contract_id=contract.id,
        sequence_no=2,
        status=MilestoneStatus.NOT_FUNDED,
    )
    db.add_all([ms1, ms2])
    db.flush()

    t1 = ContractMilestoneTerm(
        id=701,
        contract_id=contract.id,
        contract_version_id=version.id,
        milestone_id=ms1.id,
        title="Frontend",
        amount=1500000,
        acceptance_criteria="Pass UI test",
        due_at=datetime(2026, 11, 20),
        included=True,
    )
    t2 = ContractMilestoneTerm(
        id=702,
        contract_id=contract.id,
        contract_version_id=version.id,
        milestone_id=ms2.id,
        title="Backend",
        amount=1500000,
        acceptance_criteria="Pass API test",
        due_at=datetime(2026, 12, 10),
        included=True,
    )
    db.add_all([t1, t2])
    db.flush()

    ms1.effective_terms_id = t1.id
    ms2.effective_terms_id = t2.id
    db.commit()

    return {
        "client": client_user,
        "student": student_user,
        "outsider": outsider_user,
        "contract": contract,
        "version": version,
        "ms1": ms1,
        "ms2": ms2,
        "t1": t1,
        "t2": t2,
    }


def make_ctx(
    actor_user_id: int | None, actor_type=ActorType.USER, now_utc=None, key=None, job_key=None
) -> CommandContext:
    return CommandContext(
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        request_id="req-ms",
        idempotency_key=key,
        now_utc=now_utc or datetime(2026, 11, 4, 12, 0, 0),
        job_key=job_key,
    )


# =============================================================================
# Ticket C3 Tests: Milestone Start Guards
# =============================================================================


def test_c3_start_milestone_success_per_milestone(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    service = MilestoneService()
    ctx_student = make_ctx(f["student"].id)
    fake_finance = FakeFinancePort(funded=True)

    ms = service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=fake_finance,
    )
    assert ms.status == MilestoneStatus.IN_PROGRESS
    assert ms.started_at is not None


def test_c3_start_milestone_full_funding_policy_guard(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    service = MilestoneService()
    ctx_student = make_ctx(f["student"].id)

    # Change policy to FULL on version
    f["version"].funding_policy = FundingPolicy.FULL
    db_session.flush()

    fake_finance = FakeFinancePort(funded=True)
    # ms2 is NOT_FUNDED -> should block starting ms1 with MILESTONE_NOT_FUNDED
    with pytest.raises(ConflictError) as exc:
        service.start_milestone_in_tx(
            db_session,
            ctx=ctx_student,
            milestone_id=f["ms1"].id,
            finance_port=fake_finance,
        )
    assert exc.value.code == "MILESTONE_NOT_FUNDED"
    assert "Full contract funding required" in exc.value.message


def test_c3_start_milestone_hold_and_dispute_guard(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    service = MilestoneService()
    ctx_student = make_ctx(f["student"].id)
    fake_finance = FakeFinancePort(funded=True)

    # 1. Place a hold on ms1
    hold = MilestoneHold(
        milestone_id=f["ms1"].id,
        reason_type="ADMIN_REVIEW",
        reason_key="review-1",
        note="Investigation",
        placed_at=datetime(2026, 11, 4),
    )
    db_session.add(hold)
    db_session.flush()

    with pytest.raises(ConflictError) as exc:
        service.start_milestone_in_tx(
            db_session,
            ctx=ctx_student,
            milestone_id=f["ms1"].id,
            finance_port=fake_finance,
        )
    assert exc.value.code == "FUNDS_ON_HOLD"

    # Release hold
    hold.released_at = datetime(2026, 11, 4)
    db_session.flush()

    # 2. Add an active dispute on ms1
    disp = Dispute(
        milestone_id=f["ms1"].id,
        opened_by=f["client"].id,
        reason_code="QUALITY",
        description="Bad design",
        previous_milestone_status=MilestoneStatus.FUNDED,
        evidence_deadline=datetime(2026, 11, 10),
    )
    db_session.add(disp)
    db_session.flush()
    active_disp = ActiveMilestoneDispute(milestone_id=f["ms1"].id, dispute_id=disp.id)
    db_session.add(active_disp)
    db_session.flush()

    with pytest.raises(ConflictError) as exc:
        service.start_milestone_in_tx(
            db_session,
            ctx=ctx_student,
            milestone_id=f["ms1"].id,
            finance_port=fake_finance,
        )
    assert exc.value.code == "FUNDS_ON_HOLD"


def test_c3_start_milestone_permissions_zero_leak(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    service = MilestoneService()
    fake_finance = FakeFinancePort(funded=True)

    # Client tries to start -> 403 Forbidden
    with pytest.raises(ForbiddenError) as exc:
        service.start_milestone_in_tx(
            db_session,
            ctx=make_ctx(f["client"].id),
            milestone_id=f["ms1"].id,
            finance_port=fake_finance,
        )
    assert exc.value.code == "FORBIDDEN"

    # Outsider tries to start -> 404 NOT_FOUND
    with pytest.raises(NotFoundError) as exc:
        service.start_milestone_in_tx(
            db_session,
            ctx=make_ctx(f["outsider"].id),
            milestone_id=f["ms1"].id,
            finance_port=fake_finance,
        )
    assert exc.value.code == "NOT_FOUND"


# =============================================================================
# Ticket C4 Tests: Deliverables, Files, Revisions
# =============================================================================


def test_c4_submit_deliverable_with_files(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    ms_service = MilestoneService()
    del_service = DeliverableService()
    ctx_student = make_ctx(f["student"].id)

    # Start milestone
    ms_service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=FakeFinancePort(funded=True),
    )

    # Create stored files
    clean_file = StoredFile(
        uploaded_by=f["student"].id,
        storage_key="clean-file-key",
        original_name="app.zip",
        content_type="application/zip",
        size_bytes=1024,
        checksum_sha256="hash-clean",
        category="deliverable",
        scan_status=FileScanStatus.CLEAN,
        availability_status=FileAvailability.AVAILABLE,
    )
    dirty_file = StoredFile(
        uploaded_by=f["student"].id,
        storage_key="dirty-file-key",
        original_name="virus.exe",
        content_type="application/octet-stream",
        size_bytes=1024,
        checksum_sha256="hash-dirty",
        category="deliverable",
        scan_status=FileScanStatus.REJECTED,
        availability_status=FileAvailability.QUARANTINED,
    )
    db_session.add_all([clean_file, dirty_file])
    db_session.flush()

    # Attempt submit with uncleaned file -> 409 VALIDATION_ERROR
    with pytest.raises(ConflictError) as exc:
        del_service.submit_deliverable_in_tx(
            db_session,
            ctx=ctx_student,
            milestone_id=f["ms1"].id,
            file_ids=[dirty_file.id],
            note="Here is virus",
        )
    assert exc.value.code == "VALIDATION_ERROR"

    # Submit successfully with clean file
    deliv = del_service.submit_deliverable_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        file_ids=[clean_file.id],
        note="First release",
    )
    assert deliv.submission_no == 1
    assert deliv.submitted_by == f["student"].id

    # Verify deliverable file mapped
    df = (
        db_session.query(DeliverableFile)
        .filter_by(deliverable_id=deliv.id, file_id=clean_file.id)
        .first()
    )
    assert df is not None

    # Verify milestone transitioned to SUBMITTED
    db_session.refresh(f["ms1"])
    assert f["ms1"].status == MilestoneStatus.SUBMITTED
    assert f["ms1"].review_deadline is not None

    # Verify scheduled job for auto-accept
    job = (
        db_session.query(ScheduledJob)
        .filter_by(job_key=f"milestone.auto_accept:{f['ms1'].id}:1")
        .first()
    )
    assert job is not None
    assert job.status == ScheduledJobStatus.PENDING


def test_c4_request_revision_flow_and_limit(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    ms_service = MilestoneService()
    del_service = DeliverableService()
    ctx_student = make_ctx(f["student"].id)
    ctx_client = make_ctx(f["client"].id)

    # Start and submit 1st deliverable
    ms_service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=FakeFinancePort(funded=True),
    )
    d1 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Submission 1"
    )

    # Client requests revision 1
    rev1 = del_service.request_revision_in_tx(
        db_session,
        ctx=ctx_client,
        milestone_id=f["ms1"].id,
        deliverable_id=d1.id,
        reason="Button is wrong color",
    )
    assert rev1.action == MilestoneReviewAction.REQUEST_REVISION
    db_session.refresh(f["ms1"])
    assert f["ms1"].status == MilestoneStatus.REVISION_REQUESTED
    assert f["ms1"].revision_count == 1
    assert f["ms1"].review_deadline is None

    # Student submits 2nd deliverable
    d2 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Submission 2"
    )
    assert d2.submission_no == 2
    db_session.refresh(f["ms1"])
    assert f["ms1"].status == MilestoneStatus.SUBMITTED

    # Client requests revision 2 (max_revision_count is 2 on version)
    del_service.request_revision_in_tx(
        db_session,
        ctx=ctx_client,
        milestone_id=f["ms1"].id,
        deliverable_id=d2.id,
        reason="Font too small",
    )
    db_session.refresh(f["ms1"])
    assert f["ms1"].revision_count == 2

    # Student submits 3rd deliverable
    d3 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Submission 3"
    )

    # Client tries to request revision 3 -> Exceeds max revisions -> 409 REVISION_LIMIT_EXCEEDED
    with pytest.raises(ConflictError) as exc:
        del_service.request_revision_in_tx(
            db_session,
            ctx=ctx_client,
            milestone_id=f["ms1"].id,
            deliverable_id=d3.id,
            reason="Another fix",
        )
    assert exc.value.code == "REVISION_LIMIT_EXCEEDED"


# =============================================================================
# Ticket C5 Tests: Atomic Acceptance & Auto Accept
# =============================================================================


def test_c5_manual_acceptance_atomic_with_finance(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    ms_service = MilestoneService()
    del_service = DeliverableService()
    ctx_student = make_ctx(f["student"].id)
    ctx_client = make_ctx(f["client"].id, key="accept-cmd-1")

    # Start and submit
    ms_service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=FakeFinancePort(funded=True),
    )
    d1 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Final code"
    )

    fake_finance = FakeFinancePort(funded=True)

    # Accept milestone via accept_milestone_command
    settlement_ref = accept_milestone_command(
        db_session,
        ctx=ctx_client,
        milestone_id=f["ms1"].id,
        deliverable_id=d1.id,
        finance_port=fake_finance,
        automatic=False,
    )
    assert settlement_ref is not None

    db_session.refresh(f["ms1"])
    assert f["ms1"].status == MilestoneStatus.ACCEPTED
    assert f["ms1"].acceptance_source == AcceptanceSource.MANUAL
    assert f["ms1"].accepted_at is not None

    # Verify review record
    review = (
        db_session.query(MilestoneReview)
        .filter_by(milestone_id=f["ms1"].id, action=MilestoneReviewAction.ACCEPT)
        .first()
    )
    assert review is not None
    assert review.reviewed_by == f["client"].id


def test_c5_acceptance_rollback_on_finance_failure(db_session, active_contract_fixtures):
    """When finance writer is unavailable, acceptance must roll back cleanly."""
    f = active_contract_fixtures
    ms_service = MilestoneService()
    del_service = DeliverableService()
    ctx_student = make_ctx(f["student"].id)
    ctx_client = make_ctx(f["client"].id)

    # Start with fake, submit, and commit baseline
    ms_service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=FakeFinancePort(funded=True),
    )
    d1 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Final code"
    )
    db_session.commit()

    # Now call accept with UnavailableFinancePort
    with pytest.raises(FinanceNotReadyError):
        accept_milestone_command(
            db_session,
            ctx=ctx_client,
            milestone_id=f["ms1"].id,
            deliverable_id=d1.id,
            finance_port=UnavailableFinancePort(),
            automatic=False,
        )

    # Verify milestone remains SUBMITTED (no partial state)
    db_session.refresh(f["ms1"])
    assert f["ms1"].status == MilestoneStatus.SUBMITTED
    assert f["ms1"].accepted_at is None


def test_c5_auto_acceptance_by_system(db_session, active_contract_fixtures):
    f = active_contract_fixtures
    ms_service = MilestoneService()
    del_service = DeliverableService()
    work = DeliverableWorkService()
    ctx_student = make_ctx(f["student"].id)

    ms_service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=FakeFinancePort(funded=True),
    )
    d1 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Submission"
    )

    job_key = f"milestone.auto_accept:{f['ms1'].id}:1"

    # Attempt auto-accept before deadline -> 409 INVALID_STATE_TRANSITION
    ctx_sys_early = make_ctx(
        actor_user_id=None,
        actor_type=ActorType.SYSTEM,
        now_utc=datetime(2026, 11, 5),
        job_key=job_key,
    )
    with pytest.raises(ConflictError) as exc:
        work.record_acceptance_in_tx(
            db_session,
            ctx=ctx_sys_early,
            milestone_id=f["ms1"].id,
            deliverable_id=d1.id,
            source="AUTO",
        )
    assert exc.value.code == "INVALID_STATE_TRANSITION"

    # Auto-accept after review deadline passed (8 days later)
    ctx_sys_passed = make_ctx(
        actor_user_id=None,
        actor_type=ActorType.SYSTEM,
        now_utc=datetime(2026, 11, 15),
        job_key=job_key,
    )
    ref = work.record_acceptance_in_tx(
        db_session,
        ctx=ctx_sys_passed,
        milestone_id=f["ms1"].id,
        deliverable_id=d1.id,
        source="AUTO",
    )
    assert ref.source == "AUTO"

    db_session.refresh(f["ms1"])
    assert f["ms1"].status == MilestoneStatus.ACCEPTED
    assert f["ms1"].acceptance_source == AcceptanceSource.AUTO

    # ScheduledJob marked SUCCEEDED
    job = db_session.query(ScheduledJob).filter_by(job_key=job_key).first()
    assert job.status == ScheduledJobStatus.SUCCEEDED


def test_c5_acceptance_idempotency_and_permission(db_session, active_contract_fixtures):
    """CommandRequest idempotency replay and zero-leak permission checks."""
    f = active_contract_fixtures
    ms_service = MilestoneService()
    del_service = DeliverableService()
    ctx_student = make_ctx(f["student"].id)
    ctx_client = make_ctx(f["client"].id, key="idemp-key-c5-1")
    ctx_outsider = make_ctx(f["outsider"].id, key="idemp-key-c5-1")

    # Start milestone and submit deliverables with a revision cycle
    ms_service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=FakeFinancePort(funded=True),
    )
    d1 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Submission 1"
    )
    del_service.request_revision_in_tx(
        db_session,
        ctx=ctx_client,
        milestone_id=f["ms1"].id,
        deliverable_id=d1.id,
        reason="Needs polish",
    )
    d2 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Submission 2"
    )
    db_session.commit()

    # 1. Outsider attempts acceptance -> Zero-Leak 404
    with pytest.raises(NotFoundError) as exc:
        accept_milestone_command(
            db_session,
            ctx=ctx_outsider,
            milestone_id=f["ms1"].id,
            deliverable_id=d2.id,
            finance_port=FakeFinancePort(funded=True),
            automatic=False,
        )
    assert exc.value.code == "NOT_FOUND"

    # 2. Student attempts acceptance -> 403 Forbidden
    with pytest.raises(ForbiddenError) as exc:
        accept_milestone_command(
            db_session,
            ctx=ctx_student,
            milestone_id=f["ms1"].id,
            deliverable_id=d2.id,
            finance_port=FakeFinancePort(funded=True),
            automatic=False,
        )
    assert exc.value.code == "FORBIDDEN"

    # 3. Client executes first acceptance with idempotency key
    res1 = accept_milestone_command(
        db_session,
        ctx=ctx_client,
        milestone_id=f["ms1"].id,
        deliverable_id=d2.id,
        finance_port=FakeFinancePort(funded=True),
        automatic=False,
    )
    assert res1.settlement_id is not None

    # 4. Replay identical request with same key
    res2 = accept_milestone_command(
        db_session,
        ctx=ctx_client,
        milestone_id=f["ms1"].id,
        deliverable_id=d2.id,
        finance_port=FakeFinancePort(funded=True),
        automatic=False,
    )
    assert res1.settlement_id == res2.settlement_id

    # 5. Replay with different payload (d1 instead of d2) -> IDEMPOTENCY_CONFLICT
    with pytest.raises(ConflictError) as exc:
        accept_milestone_command(
            db_session,
            ctx=ctx_client,
            milestone_id=f["ms1"].id,
            deliverable_id=d1.id,
            finance_port=FakeFinancePort(funded=True),
            automatic=False,
        )
    assert exc.value.code == "IDEMPOTENCY_CONFLICT"


def test_c5_accept_endpoint_http_returns_settlement_id(db_session, active_contract_fixtures):
    """HTTP acceptance endpoint returns settlement_id in response."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.core.exceptions import register_exception_handlers
    from app.dependencies import get_current_user, get_db
    from app.routers.milestones import router as milestones_router
    from app.services.freelancer_finance import get_finance_port

    f = active_contract_fixtures
    ms_service = MilestoneService()
    del_service = DeliverableService()
    ctx_student = make_ctx(f["student"].id)

    ms_service.start_milestone_in_tx(
        db_session,
        ctx=ctx_student,
        milestone_id=f["ms1"].id,
        finance_port=FakeFinancePort(funded=True),
    )
    d1 = del_service.submit_deliverable_in_tx(
        db_session, ctx=ctx_student, milestone_id=f["ms1"].id, note="Ready for review"
    )
    db_session.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(milestones_router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: f["client"]
    app.dependency_overrides[get_finance_port] = lambda: FakeFinancePort(funded=True)

    client = TestClient(app)
    resp = client.post(f"/milestones/{f['ms1'].id}/accept", json={"deliverable_id": str(d1.id)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(f["ms1"].id)
    assert data["status"] == "ACCEPTED"
    assert data["settlement_id"] is not None
    assert int(data["settlement_id"]) > 0


def test_review_policy_uses_milestone_snapshot_after_contract_amendment(
    db_session, active_contract_fixtures
):
    from datetime import timedelta

    f = active_contract_fixtures
    old = f["version"]
    newer = ContractVersion(
        contract_id=f["contract"].id,
        version_no=2,
        created_by=f["client"].id,
        status="EFFECTIVE",
        total_amount=3000000,
        fee_rate_bp=500,
        review_period_seconds=1,
        max_revision_count=0,
        grace_period_seconds=0,
        funding_policy="PER_MILESTONE",
        terms_json={},
    )
    db_session.add(newer)
    db_session.flush()
    f["contract"].effective_version_id = newer.id
    f["ms1"].status = MilestoneStatus.IN_PROGRESS
    db_session.flush()
    now = datetime(2026, 11, 7)
    service = DeliverableService()
    d = service.submit_deliverable_in_tx(
        db_session,
        ctx=make_ctx(f["student"].id, now_utc=now),
        milestone_id=f["ms1"].id,
        note="Completed work",
    )
    assert f["ms1"].review_deadline == now + timedelta(seconds=old.review_period_seconds)
    service.request_revision_in_tx(
        db_session,
        ctx=make_ctx(f["client"].id, now_utc=now),
        milestone_id=f["ms1"].id,
        deliverable_id=d.id,
        reason="Please revise",
    )
    assert f["ms1"].revision_count == 1
