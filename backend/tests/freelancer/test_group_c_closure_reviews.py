"""Tests for Group C: Ticket C6 (ClosurePort, Multi-contract Invariants, Two-way Reviews)."""
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole, UserStatus
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnprocessableError,
)
from app.core.freelancer_enums import (
    ActorType,
    ContractBudgetStatus,
    ContractStatus,
    ContractVersionStatus,
    FundingPolicy,
    MilestoneStatus,
    ProjectStatus,
    RecruitmentStatus,
    ReviewVisibility,
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
    Milestone,
)
from app.services.freelance_closure_service import FreelanceClosureService
from app.services.freelance_review_service import FreelanceReviewService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def multi_contract_fixtures(db_session):
    db = db_session
    client = User(id=1, email="client@test.com", role=UserRole.CLIENT, status=UserStatus.ACTIVE)
    student1_user = User(id=2, email="s1@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE)
    student2_user = User(id=3, email="s2@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE)
    outsider_user = User(id=4, email="out@test.com", role=UserRole.STUDENT, status=UserStatus.ACTIVE)
    admin_user = User(id=5, email="admin@test.com", role=UserRole.ADMIN, status=UserStatus.ACTIVE)
    db.add_all([client, student1_user, student2_user, outsider_user, admin_user])
    db.flush()

    faculty = Faculty(code="CS", name="Computer Science")
    db.add(faculty)
    db.flush()
    major = Major(code="SE", name="Software Engineering", faculty_id=faculty.id)
    db.add(major)
    db.flush()

    s1 = Student(id=10, user_id=student1_user.id, student_code="SV001", full_name="Student 1", faculty_id=faculty.id, major_id=major.id, cohort="2026")
    s2 = Student(id=20, user_id=student2_user.id, student_code="SV002", full_name="Student 2", faculty_id=faculty.id, major_id=major.id, cohort="2026")
    s_out = Student(id=30, user_id=outsider_user.id, student_code="SV003", full_name="Student Out", faculty_id=faculty.id, major_id=major.id, cohort="2026")
    db.add_all([s1, s2, s_out])
    db.flush()

    project = FreelanceProject(
        id=100,
        client_user_id=client.id,
        title="Multi-contract Project",
        description="Complex project",
        budget_amount=5000000,
        max_students=2,
        recruitment_status=RecruitmentStatus.OPEN,
        deadline=datetime(2026, 12, 31),
        acceptance_criteria="Criteria",
        deliverables_description="Deliverables",
        funding_policy=FundingPolicy.PER_MILESTONE,
        status=ProjectStatus.IN_PROGRESS,
    )
    db.add(project)
    db.flush()

    # Contract 1 setup
    app1 = FreelanceApplication(id=101, project_id=project.id, student_id=s1.id, proposal="P1", quoted_amount=2000000, estimated_days=10, status="SELECTED")
    db.add(app1)
    db.flush()
    c1 = FreelanceContract(id=201, project_id=project.id, application_id=app1.id, client_user_id=client.id, freelancer_student_id=s1.id, status=ContractStatus.ACTIVE)
    db.add(c1)
    db.flush()
    b1 = ProjectContractBudget(project_id=project.id, contract_id=c1.id, allocated_amount=2000000, status=ContractBudgetStatus.COMMITTED)
    v1 = ContractVersion(id=301, contract_id=c1.id, version_no=1, created_by=client.id, status=ContractVersionStatus.EFFECTIVE, total_amount=2000000, fee_rate_bp=500, review_period_seconds=604800, max_revision_count=3, grace_period_seconds=259200, funding_policy=FundingPolicy.PER_MILESTONE, terms_json={})
    db.add_all([b1, v1])
    db.flush()
    c1.effective_version_id = v1.id

    m1_1 = Milestone(id=401, contract_id=c1.id, sequence_no=1, status=MilestoneStatus.PAID_OUT)
    m1_2 = Milestone(id=402, contract_id=c1.id, sequence_no=2, status=MilestoneStatus.PAID_OUT)
    db.add_all([m1_1, m1_2])
    db.flush()
    t1_1 = ContractMilestoneTerm(id=501, contract_id=c1.id, contract_version_id=v1.id, milestone_id=m1_1.id, title="Frontend", amount=1000000, acceptance_criteria="OK", due_at=datetime(2026, 11, 20), included=True)
    t1_2 = ContractMilestoneTerm(id=502, contract_id=c1.id, contract_version_id=v1.id, milestone_id=m1_2.id, title="Backend", amount=1000000, acceptance_criteria="OK", due_at=datetime(2026, 12, 1), included=True)
    db.add_all([t1_1, t1_2])
    db.flush()
    m1_1.effective_terms_id = t1_1.id
    m1_2.effective_terms_id = t1_2.id

    # Contract 2 setup
    app2 = FreelanceApplication(id=102, project_id=project.id, student_id=s2.id, proposal="P2", quoted_amount=3000000, estimated_days=15, status="SELECTED")
    db.add(app2)
    db.flush()
    c2 = FreelanceContract(id=202, project_id=project.id, application_id=app2.id, client_user_id=client.id, freelancer_student_id=s2.id, status=ContractStatus.ACTIVE)
    db.add(c2)
    db.flush()
    b2 = ProjectContractBudget(project_id=project.id, contract_id=c2.id, allocated_amount=3000000, status=ContractBudgetStatus.COMMITTED)
    v2 = ContractVersion(id=302, contract_id=c2.id, version_no=1, created_by=client.id, status=ContractVersionStatus.EFFECTIVE, total_amount=3000000, fee_rate_bp=500, review_period_seconds=604800, max_revision_count=3, grace_period_seconds=259200, funding_policy=FundingPolicy.PER_MILESTONE, terms_json={})
    db.add_all([b2, v2])
    db.flush()
    c2.effective_version_id = v2.id

    m2_1 = Milestone(id=403, contract_id=c2.id, sequence_no=1, status=MilestoneStatus.IN_PROGRESS)
    db.add(m2_1)
    db.flush()
    t2_1 = ContractMilestoneTerm(id=503, contract_id=c2.id, contract_version_id=v2.id, milestone_id=m2_1.id, title="Mobile App", amount=3000000, acceptance_criteria="OK", due_at=datetime(2026, 12, 10), included=True)
    db.add(t2_1)
    db.flush()
    m2_1.effective_terms_id = t2_1.id

    db.commit()

    return {
        "client": client,
        "s1_user": student1_user,
        "s2_user": student2_user,
        "outsider": outsider_user,
        "admin": admin_user,
        "project": project,
        "c1": c1,
        "c2": c2,
        "b1": b1,
        "b2": b2,
        "m1_1": m1_1,
        "m1_2": m1_2,
        "m2_1": m2_1,
    }


def make_ctx(actor_user_id: int | None = None) -> CommandContext:
    return CommandContext(
        actor_user_id=actor_user_id or 1,
        actor_type=ActorType.USER,
        request_id="req-close",
        idempotency_key=None,
        now_utc=datetime(2026, 11, 4, 12, 0, 0),
    )


# =============================================================================
# Ticket C6 Tests: Contract Closure & Budget Invariant
# =============================================================================

def test_c6_contract_closure_completed(db_session, multi_contract_fixtures):
    f = multi_contract_fixtures
    service = FreelanceClosureService()
    ctx = make_ctx(f["client"].id)

    # c1 milestones are all PAID_OUT -> should transition to COMPLETED
    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c1"].id)

    db_session.refresh(f["c1"])
    assert f["c1"].status == ContractStatus.COMPLETED
    assert f["c1"].closed_at is not None
    assert f["c1"].closure_reason == "All milestones paid out"

    # Invariant from spec section 6.6: Budget status must remain COMMITTED, not RELEASED!
    db_session.refresh(f["b1"])
    assert f["b1"].status == ContractBudgetStatus.COMMITTED


def test_c6_contract_closure_terminated(db_session, multi_contract_fixtures):
    f = multi_contract_fixtures
    service = FreelanceClosureService()
    ctx = make_ctx(f["client"].id)

    # c2 milestone set to REFUNDED
    f["m2_1"].status = MilestoneStatus.REFUNDED
    db_session.flush()

    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c2"].id)

    db_session.refresh(f["c2"])
    assert f["c2"].status == ContractStatus.TERMINATED
    assert f["c2"].closure_reason == "Contract terminated after partial release or refund"


def test_c6_contract_cancellation_pre_activation(db_session, multi_contract_fixtures):
    f = multi_contract_fixtures
    service = FreelanceClosureService()
    ctx = make_ctx(f["client"].id)

    # 1. Chiều 1: Hợp đồng DRAFT đang bình thường (dự án đang OPEN tuyển, milestone NOT_FUNDED, version DRAFT)
    # Khi gọi recompute_contract_closure_in_tx thì KHÔNG bị tự hủy (vẫn giữ nguyên DRAFT và budget vẫn RESERVED)!
    f["c2"].status = ContractStatus.DRAFT
    f["c2"].effective_version_id = None
    v2 = db_session.get(ContractVersion, 302)
    v2.status = ContractVersionStatus.DRAFT
    f["m2_1"].status = MilestoneStatus.NOT_FUNDED
    f["b2"].status = ContractBudgetStatus.RESERVED
    db_session.flush()

    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c2"].id)

    db_session.refresh(f["c2"])
    db_session.refresh(f["b2"])
    assert f["c2"].status == ContractStatus.DRAFT
    assert f["b2"].status == ContractBudgetStatus.RESERVED

    # 2. Chiều 2: Khi các milestone của hợp đồng nháp đã chuyển sang CANCELLED và version thất bại
    # lúc đó recompute_contract_closure_in_tx mới chuyển hợp đồng sang CANCELLED và giải phóng budget sang RELEASED!
    f["m2_1"].status = MilestoneStatus.CANCELLED
    v2.status = ContractVersionStatus.DECLINED
    db_session.flush()

    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c2"].id)

    db_session.refresh(f["c2"])
    assert f["c2"].status == ContractStatus.CANCELLED
    assert f["c2"].closure_reason == "Cancelled before activation"

    # Pre-activation cancellation DOES release budget
    db_session.refresh(f["b2"])
    assert f["b2"].status == ContractBudgetStatus.RELEASED
    assert f["b2"].released_at is not None


def test_c6_contract_cancellation_when_project_closed(db_session, multi_contract_fixtures):
    """When project recruitment is closed and no active offered version, draft contract is cancelled."""
    f = multi_contract_fixtures
    service = FreelanceClosureService()
    ctx = make_ctx(f["client"].id)

    f["c2"].status = ContractStatus.DRAFT
    f["c2"].effective_version_id = None
    v2 = db_session.get(ContractVersion, 302)
    v2.status = ContractVersionStatus.DRAFT
    f["m2_1"].status = MilestoneStatus.NOT_FUNDED
    f["b2"].status = ContractBudgetStatus.RESERVED
    f["project"].recruitment_status = RecruitmentStatus.CLOSED
    db_session.flush()

    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c2"].id)

    db_session.refresh(f["c2"])
    assert f["c2"].status == ContractStatus.CANCELLED
    db_session.refresh(f["b2"])
    assert f["b2"].status == ContractBudgetStatus.RELEASED


def test_c6_explicit_cancel_draft_contract(db_session, multi_contract_fixtures):
    """Explicitly cancelling a draft contract releases budget and marks milestones cancelled."""
    f = multi_contract_fixtures
    service = FreelanceClosureService()
    ctx = make_ctx(f["client"].id)

    f["c2"].status = ContractStatus.DRAFT
    f["c2"].effective_version_id = None
    f["m2_1"].status = MilestoneStatus.NOT_FUNDED
    f["b2"].status = ContractBudgetStatus.RESERVED
    db_session.flush()

    service.cancel_draft_contract_in_tx(db_session, ctx=ctx, contract_id=f["c2"].id, reason="Client withdrew post")

    db_session.refresh(f["c2"])
    assert f["c2"].status == ContractStatus.CANCELLED
    assert f["c2"].closure_reason == "Client withdrew post"
    db_session.refresh(f["m2_1"])
    assert f["m2_1"].status == MilestoneStatus.CANCELLED
    db_session.refresh(f["b2"])
    assert f["b2"].status == ContractBudgetStatus.RELEASED


# =============================================================================
# Ticket C6 Tests: Multi-Contract Project Invariants
# =============================================================================

def test_c6_project_closure_invariants(db_session, multi_contract_fixtures):
    f = multi_contract_fixtures
    service = FreelanceClosureService()
    ctx = make_ctx(f["client"].id)

    # 1. Close c1 to COMPLETED
    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c1"].id)

    # Project recruitment is still OPEN, and c2 is still ACTIVE -> eligible must be None
    state = service.get_project_closure_state(db_session, project_id=f["project"].id)
    assert state.has_open_obligations is True
    assert state.eligible_terminal_status is None

    # 2. Close recruitment to CLOSED
    f["project"].recruitment_status = RecruitmentStatus.CLOSED
    db_session.flush()

    # Still cannot close because c2 is ACTIVE
    state = service.get_project_closure_state(db_session, project_id=f["project"].id)
    assert state.eligible_terminal_status is None

    # 3. Complete c2 as well (m2_1 -> PAID_OUT)
    f["m2_1"].status = MilestoneStatus.PAID_OUT
    db_session.flush()
    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c2"].id)

    # Now all obligations clear and recruitment CLOSED -> COMPLETED!
    state = service.get_project_closure_state(db_session, project_id=f["project"].id)
    assert state.has_open_obligations is False
    assert state.eligible_terminal_status == ProjectStatus.COMPLETED

    # Apply project closure
    service.recompute_project_closure_in_tx(db_session, ctx=ctx, project_id=f["project"].id)
    db_session.refresh(f["project"])
    assert f["project"].status == ProjectStatus.COMPLETED
    assert f["project"].closed_at is not None


def test_c6_project_closed_when_contract_terminated(db_session, multi_contract_fixtures):
    f = multi_contract_fixtures
    service = FreelanceClosureService()
    ctx = make_ctx(f["client"].id)

    f["project"].recruitment_status = RecruitmentStatus.CLOSED

    # c1 completed
    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c1"].id)

    # c2 terminated (partial refund)
    f["m2_1"].status = MilestoneStatus.REFUNDED
    db_session.flush()
    service.recompute_contract_closure_in_tx(db_session, ctx=ctx, contract_id=f["c2"].id)

    state = service.get_project_closure_state(db_session, project_id=f["project"].id)
    # When any active contract is TERMINATED -> Project is CLOSED (not COMPLETED)
    assert state.eligible_terminal_status == ProjectStatus.CLOSED

    service.recompute_project_closure_in_tx(db_session, ctx=ctx, project_id=f["project"].id)
    db_session.refresh(f["project"])
    assert f["project"].status == ProjectStatus.CLOSED


# =============================================================================
# Ticket C6 Tests: Two-Way Reviews
# =============================================================================

def test_c6_mutual_reviews_success(db_session, multi_contract_fixtures):
    f = multi_contract_fixtures
    closure_service = FreelanceClosureService()
    review_service = FreelanceReviewService()
    ctx_client = make_ctx(f["client"].id)
    ctx_s1 = make_ctx(f["s1_user"].id)

    # Close c1
    closure_service.recompute_contract_closure_in_tx(db_session, ctx=ctx_client, contract_id=f["c1"].id)

    # 1. Client reviews Student 1
    r_client = review_service.create_review_in_tx(
        db_session, ctx=ctx_client, contract_id=f["c1"].id, rating=5, comment="Great student!",
    )
    assert r_client.reviewer_user_id == f["client"].id
    assert r_client.reviewee_user_id == f["s1_user"].id
    assert r_client.rating == 5
    assert r_client.visibility == ReviewVisibility.VISIBLE

    # 2. Student 1 reviews Client
    r_student = review_service.create_review_in_tx(
        db_session, ctx=ctx_s1, contract_id=f["c1"].id, rating=4, comment="Clear instructions",
    )
    assert r_student.reviewer_user_id == f["s1_user"].id
    assert r_student.reviewee_user_id == f["client"].id
    assert r_student.rating == 4

    # 3. Client tries to review again -> 409 INVALID_STATE_TRANSITION
    with pytest.raises(ConflictError) as exc:
        review_service.create_review_in_tx(
            db_session, ctx=ctx_client, contract_id=f["c1"].id, rating=5, comment="Duplicate review",
        )
    assert exc.value.code == "INVALID_STATE_TRANSITION"


def test_c6_review_invariants(db_session, multi_contract_fixtures):
    f = multi_contract_fixtures
    review_service = FreelanceReviewService()
    ctx_client = make_ctx(f["client"].id)

    # 1. Contract c2 is ACTIVE (not terminal) -> review rejected
    with pytest.raises(ConflictError) as exc:
        review_service.create_review_in_tx(
            db_session, ctx=ctx_client, contract_id=f["c2"].id, rating=5, comment="Premature",
        )
    assert exc.value.code == "INVALID_STATE_TRANSITION"

    # 2. Zero-Leak: Outsider tries to review c1 -> 404 NOT_FOUND
    with pytest.raises(NotFoundError) as exc:
        review_service.create_review_in_tx(
            db_session, ctx=make_ctx(f["outsider"].id), contract_id=f["c1"].id, rating=5,
        )
    assert exc.value.code == "NOT_FOUND"

    # 3. Rating out of range -> 422 VALIDATION_ERROR
    # Complete c1 first
    FreelanceClosureService().recompute_contract_closure_in_tx(db_session, ctx=ctx_client, contract_id=f["c1"].id)
    with pytest.raises(UnprocessableError) as exc:
        review_service.create_review_in_tx(
            db_session, ctx=ctx_client, contract_id=f["c1"].id, rating=6,
        )
    assert exc.value.code == "VALIDATION_ERROR"
