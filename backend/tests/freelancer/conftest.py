from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.contracts.freelancer.types import CommandContext
from app.core.enums import UserRole, UserStatus
from app.core.freelancer_enums import ActorType
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


@pytest.fixture
def command_context():
    return CommandContext(
        actor_user_id=1, actor_type=ActorType.USER, request_id="test-request",
        idempotency_key="test-command", now_utc=datetime(2026, 11, 4),
    )


@pytest.fixture
def foundation_db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def two_contract_project(foundation_db):
    """One project, two students, separate contracts and budget allocations."""
    db = foundation_db
    owner = User(email="owner@example.test", role=UserRole.CLIENT, status=UserStatus.ACTIVE)
    faculty = Faculty(code="FL", name="Freelancer Faculty")
    db.add_all([owner, faculty])
    db.flush()
    major = Major(code="FL", name="Freelancer Major", faculty_id=faculty.id)
    db.add(major)
    db.flush()
    project = FreelanceProject(
        client_user_id=owner.id, title="Two students", description="Separate work",
        budget_amount=3000000, max_students=2, deadline=datetime(2026, 12, 1),
        acceptance_criteria="Pass review", deliverables_description="Files",
        funding_policy="PER_MILESTONE",
    )
    db.add(project)
    db.flush()
    contracts = []
    for number, amount in ((1, 1000000), (2, 2000000)):
        user = User(email=f"student{number}@example.test", role=UserRole.STUDENT, status=UserStatus.ACTIVE)
        db.add(user)
        db.flush()
        student = Student(
            user_id=user.id, student_code=f"FL{number}", full_name=f"Student {number}",
            faculty_id=faculty.id, major_id=major.id, cohort="2026",
        )
        db.add(student)
        db.flush()
        application = FreelanceApplication(
            project_id=project.id, student_id=student.id, proposal="My scope",
            quoted_amount=amount, estimated_days=5, status="SELECTED",
        )
        db.add(application)
        db.flush()
        contract = FreelanceContract(
            project_id=project.id, application_id=application.id,
            client_user_id=owner.id, freelancer_student_id=student.id,
        )
        db.add(contract)
        db.flush()
        db.add(ProjectContractBudget(
            project_id=project.id, contract_id=contract.id, allocated_amount=amount,
        ))
        db.flush()
        contracts.append(contract)
    db.commit()
    return project, tuple(contracts)
