"""Freelance contract service: ContractPort implementation and version negotiations (C1, C2)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.contracts.freelancer.ports import ContractPort
from app.contracts.freelancer.types import (
    CommandContext,
    ContractRef,
    MilestoneFinancialTerms,
)
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableError,
)
from app.core.freelancer_enums import (
    ContractBudgetStatus,
    ContractStatus,
    ContractVersionStatus,
    FreelanceApplicationStatus,
    FundingPolicy,
    MilestoneStatus,
    PaymentOrderStatus,
    ProjectStatus,
    ScheduledJobStatus,
)
from app.models import FreelanceApplication, FreelanceProject, Student
from app.models.freelancer_contracts import (
    ContractMilestoneTerm,
    ContractVersion,
    FreelanceContract,
    Milestone,
    ProjectContractBudget,
)
from app.models.freelancer_operations import AuditLog, ScheduledJob
from app.models.freelancer_payments import (
    EscrowAccount,
    MilestoneFunding,
    MilestoneFundingGuard,
    PaymentOrder,
)
from app.schemas.freelance_contracts import ContractVersionCreate
from app.services.freelancer_commands import run_command
from app.utils.hashing import sha256_json


def _norm_utc(dt: datetime | None) -> datetime | None:
    """Normalize datetime to naive UTC for consistent DB storage and comparison."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _for_update(query, db: Session):
    """Apply with_for_update only on engines that support row-level locking."""
    bind = db.get_bind()
    if bind is not None and bind.dialect.name != "sqlite":
        return query.with_for_update()
    return query


def _lock_contract_hierarchy(
    db: Session,
    *,
    contract_id: int,
    version_id: int | None = None,
    lock_milestones: bool = False,
):
    """Enforce global lock ordering: project -> contract -> budget -> version -> milestones (id asc)."""
    contract_raw = db.get(FreelanceContract, contract_id)
    if not contract_raw:
        return None, None, None, None, []
    project = _for_update(db.query(FreelanceProject).filter_by(id=contract_raw.project_id), db).first()
    contract = _for_update(db.query(FreelanceContract).filter_by(id=contract_raw.id), db).first()
    budget = _for_update(db.query(ProjectContractBudget).filter_by(contract_id=contract_raw.id), db).first()
    version = None
    if version_id is not None:
        version = _for_update(db.query(ContractVersion).filter_by(id=version_id), db).first()
    milestones = []
    if lock_milestones:
        milestones = _for_update(
            db.query(Milestone).filter_by(contract_id=contract_raw.id).order_by(Milestone.id.asc()),
            db,
        ).all()
    return project, contract, budget, version, milestones


def compute_version_content_hash(
    *,
    contract_id: int,
    version_no: int,
    total_amount: int,
    fee_rate_bp: int,
    funding_policy: FundingPolicy | str,
    review_period_seconds: int,
    max_revision_count: int,
    grace_period_seconds: int,
    terms_json: dict,
    milestone_terms: list[dict],
) -> str:
    """Compute deterministic canonical sha256 hash of contract version terms."""
    policy_str = funding_policy.value if hasattr(funding_policy, "value") else str(funding_policy)
    canonical = {
        "contract_id": contract_id,
        "fee_rate_bp": fee_rate_bp,
        "funding_policy": policy_str,
        "grace_period_seconds": grace_period_seconds,
        "max_revision_count": max_revision_count,
        "milestone_terms": sorted(
            [
                {
                    "acceptance_criteria": t["acceptance_criteria"],
                    "amount": t["amount"],
                    "description": t.get("description"),
                    "due_at": t["due_at"].isoformat() if hasattr(t["due_at"], "isoformat") else str(t["due_at"]),
                    "included": bool(t.get("included", True)),
                    "milestone_id": t["milestone_id"],
                    "sequence_no": t["sequence_no"],
                    "title": t["title"],
                }
                for t in milestone_terms
            ],
            key=lambda x: x["sequence_no"],
        ),
        "review_period_seconds": review_period_seconds,
        "terms_json": terms_json,
        "total_amount": total_amount,
        "version_no": version_no,
    }
    return sha256_json(canonical)


class FreelanceContractService(ContractPort):
    """Handles contract creation from selected applications, version lifecycle, and budget locking."""

    # -------------------------------------------------------------------------
    # Ticket C1: ContractPort Implementation
    # -------------------------------------------------------------------------

    def create_contract_for_selected_application_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        project_id: int,
        application_id: int,
        allocated_amount: int,
    ) -> ContractRef:
        """Create a contract and reserve budget for a selected application under lock."""
        if allocated_amount <= 0:
            raise UnprocessableError("Allocated amount must be positive", code="VALIDATION_ERROR")

        # 1. Lock project row
        project = _for_update(db.query(FreelanceProject).filter_by(id=project_id), db).first()
        if not project:
            raise NotFoundError("Project not found", code="NOT_FOUND")

        # 2. Get application and validate ownership
        application = db.query(FreelanceApplication).filter_by(id=application_id).first()
        if not application or application.project_id != project_id:
            raise NotFoundError("Application not found for project", code="NOT_FOUND")

        # 3. Validate student and distinct parties
        student = db.query(Student).filter_by(id=application.student_id).first()
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        if project.client_user_id == student.user_id:
            raise ConflictError("Client and student must be distinct users", code="INVALID_STATE_TRANSITION")

        # 4. Check idempotency replay for same project and student
        existing_contract = db.query(FreelanceContract).filter_by(
            project_id=project.id,
            freelancer_student_id=student.id,
        ).first()

        if existing_contract:
            budget = db.query(ProjectContractBudget).filter_by(contract_id=existing_contract.id).first()
            if (
                existing_contract.application_id == application_id
                and budget is not None
                and budget.allocated_amount == allocated_amount
                and existing_contract.status != ContractStatus.CANCELLED
            ):
                return ContractRef(
                    contract_id=existing_contract.id,
                    project_id=project.id,
                    student_id=student.id,
                    status=ContractStatus(existing_contract.status),
                    allocated_amount=budget.allocated_amount,
                )
            raise ConflictError("Contract already exists for this student in project", code="IDEMPOTENCY_CONFLICT")

        # 5. Application state transition
        now = _norm_utc(ctx.now_utc)
        if application.status in (FreelanceApplicationStatus.SUBMITTED, FreelanceApplicationStatus.SHORTLISTED):
            application.status = FreelanceApplicationStatus.SELECTED
            application.selected_at = now
        elif application.status != FreelanceApplicationStatus.SELECTED:
            raise ConflictError("Application must be in SUBMITTED, SHORTLISTED, or SELECTED status", code="INVALID_STATE_TRANSITION")

        # 6. Check max_students capacity
        active_contract_count = db.query(func.count(FreelanceContract.id)).filter(
            FreelanceContract.project_id == project.id,
            FreelanceContract.status != ContractStatus.CANCELLED,
        ).scalar() or 0

        if active_contract_count >= project.max_students:
            raise ConflictError("Project student capacity exceeded", code="PROJECT_CAPACITY_EXCEEDED")

        # 7. Check project budget ceiling
        current_allocated = db.query(func.coalesce(func.sum(ProjectContractBudget.allocated_amount), 0)).filter(
            ProjectContractBudget.project_id == project.id,
            ProjectContractBudget.status.in_([ContractBudgetStatus.RESERVED, ContractBudgetStatus.COMMITTED]),
        ).scalar() or 0

        if current_allocated + allocated_amount > project.budget_amount:
            raise ConflictError("Project budget exceeded", code="PROJECT_BUDGET_EXCEEDED")

        # 8. Create contract
        contract = FreelanceContract(
            project_id=project.id,
            application_id=application.id,
            client_user_id=project.client_user_id,
            company_id=project.company_id,
            freelancer_student_id=student.id,
            status=ContractStatus.DRAFT,
        )
        db.add(contract)
        db.flush()

        # 9. Create budget reservation
        budget = ProjectContractBudget(
            project_id=project.id,
            contract_id=contract.id,
            allocated_amount=allocated_amount,
            status=ContractBudgetStatus.RESERVED,
        )
        db.add(budget)
        db.flush()

        # 10. Audit log
        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract.created_from_selection",
                entity_type="freelance_contracts",
                entity_id=contract.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return ContractRef(
            contract_id=contract.id,
            project_id=project.id,
            student_id=student.id,
            status=ContractStatus(contract.status),
            allocated_amount=allocated_amount,
        )

    def get_milestone_financial_terms(self, db: Session, *, milestone_id: int) -> MilestoneFinancialTerms:
        """Fetch immutable terms for an effective milestone."""
        milestone = db.get(Milestone, milestone_id)
        if not milestone or milestone.effective_terms_id is None:
            raise NotFoundError("Milestone effective terms not found", code="NOT_FOUND")

        term = db.get(ContractMilestoneTerm, milestone.effective_terms_id)
        if not term:
            raise NotFoundError("Milestone term not found", code="NOT_FOUND")

        contract = db.get(FreelanceContract, milestone.contract_id)
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        version = db.get(ContractVersion, term.contract_version_id)
        if not version:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        return MilestoneFinancialTerms(
            milestone_id=milestone.id,
            contract_id=contract.id,
            client_user_id=contract.client_user_id,
            student_user_id=student.user_id,
            amount=term.amount,
            fee_rate_bp=version.fee_rate_bp,
            funding_policy=FundingPolicy(version.funding_policy),
            terms_id=term.id,
        )

    # -------------------------------------------------------------------------
    # Ticket C2: Contract Negotiation & Versioning Lifecycle
    # -------------------------------------------------------------------------

    def _is_milestone_locked(self, db: Session, ms: Milestone) -> bool:
        """A milestone is locked if funded, guarded, started, or has open payment order/escrow."""
        if ms.status != MilestoneStatus.NOT_FUNDED:
            return True
        if db.query(MilestoneFunding).filter_by(milestone_id=ms.id).first() is not None:
            return True
        if db.query(EscrowAccount).filter_by(milestone_id=ms.id).first() is not None:
            return True
        if db.query(MilestoneFundingGuard).filter_by(milestone_id=ms.id).first() is not None:
            return True
        has_open_order = db.query(PaymentOrder).filter(
            PaymentOrder.milestone_id == ms.id,
            PaymentOrder.status.in_([
                PaymentOrderStatus.CREATING,
                PaymentOrderStatus.PENDING,
                PaymentOrderStatus.PROCESSING,
                PaymentOrderStatus.PAID,
                PaymentOrderStatus.NEEDS_REVIEW,
                PaymentOrderStatus.UNKNOWN,
            ]),
        ).first() is not None
        if has_open_order:
            return True
        return False

    def _assert_immutable_milestone_terms(
        self,
        db: Session,
        *,
        contract: FreelanceContract,
        fee_rate_bp: int,
        term_items: list[tuple[Milestone, object]],
    ) -> None:
        """Assert that milestones already funded, guarded, or started cannot be omitted or modified."""
        existing_milestones = db.query(Milestone).filter_by(contract_id=contract.id).order_by(Milestone.id.asc()).all()
        terms_by_ms_id = {ms.id: term for ms, term in term_items if ms is not None and ms.id is not None}
        terms_by_seq = {ms.sequence_no: term for ms, term in term_items if ms is not None}

        for ms in existing_milestones:
            if not self._is_milestone_locked(db, ms):
                continue

            new_term = terms_by_ms_id.get(ms.id)
            if new_term is None:
                new_term = terms_by_seq.get(ms.sequence_no)
            if new_term is None:
                raise ConflictError("Cannot omit a funded, guarded, or started milestone", code="TERMS_IMMUTABLE")

            if ms.effective_terms_id is not None:
                eff_term = db.get(ContractMilestoneTerm, ms.effective_terms_id)
                if eff_term is not None:
                    eff_ver = db.get(ContractVersion, eff_term.contract_version_id)
                    fee_changed = (eff_ver is not None and eff_ver.fee_rate_bp != fee_rate_bp)
                    if (
                        eff_term.title != new_term.title
                        or eff_term.description != getattr(new_term, "description", None)
                        or eff_term.amount != new_term.amount
                        or eff_term.acceptance_criteria != new_term.acceptance_criteria
                        or _norm_utc(eff_term.due_at) != _norm_utc(new_term.due_at)
                        or not new_term.included
                        or fee_changed
                    ):
                        raise ConflictError(
                            "Cannot modify terms of a funded, guarded, or started milestone",
                            code="TERMS_IMMUTABLE",
                        )

    def create_version_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
        payload: ContractVersionCreate,
    ) -> ContractVersion:
        """Create a new DRAFT version with milestone terms under lock."""
        # Lock in global order
        _project, contract, _budget, _version, _ = _lock_contract_hierarchy(
            db, contract_id=contract_id, lock_milestones=True,
        )
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check: Only contract parties
        if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        if contract.status in (ContractStatus.COMPLETED, ContractStatus.CANCELLED, ContractStatus.TERMINATED):
            raise ConflictError("Cannot create version for closed contract", code="INVALID_STATE_TRANSITION")

        # Validate total amount and fee rate
        if payload.total_amount <= 0:
            raise UnprocessableError("Total amount must be positive", code="VALIDATION_ERROR")

        fee_rate_bp = payload.fee_rate_bp if payload.fee_rate_bp is not None else 500
        if not (0 <= fee_rate_bp < 10000):
            raise UnprocessableError("Fee rate bp must be between 0 and 9999", code="VALIDATION_ERROR")

        review_period_seconds = payload.review_period_seconds if payload.review_period_seconds is not None else 604800
        max_revision_count = payload.max_revision_count if payload.max_revision_count is not None else 3
        grace_period_seconds = payload.grace_period_seconds if payload.grace_period_seconds is not None else 259200

        if review_period_seconds <= 0 or max_revision_count < 0 or grace_period_seconds < 0:
            raise UnprocessableError("Invalid review, revision, or grace period parameters", code="VALIDATION_ERROR")

        # Validate milestone terms
        included_terms = [t for t in payload.milestone_terms if t.included]
        if not included_terms:
            raise UnprocessableError("At least one included milestone is required", code="VALIDATION_ERROR")

        sum_included = sum(t.amount for t in included_terms)
        if sum_included != payload.total_amount:
            raise UnprocessableError("Sum of included milestone amounts must equal total_amount", code="VALIDATION_ERROR")

        for t in payload.milestone_terms:
            if t.amount <= 0:
                raise UnprocessableError("Milestone amount must be positive", code="VALIDATION_ERROR")

        # Invariant checks on existing milestones
        existing_milestones = {
            m.sequence_no: m
            for m in db.query(Milestone).filter_by(contract_id=contract.id).order_by(Milestone.id.asc()).all()
        }

        # Find or create Milestones for each term
        milestone_term_mappings = []
        for seq_idx, t in enumerate(payload.milestone_terms, start=1):
            ms = existing_milestones.get(seq_idx)
            if not ms:
                ms = Milestone(
                    contract_id=contract.id,
                    sequence_no=seq_idx,
                    status=MilestoneStatus.NOT_FUNDED,
                )
                db.add(ms)
                db.flush()
                existing_milestones[seq_idx] = ms

            milestone_term_mappings.append((ms, t))

        # Check immutable invariants on locked milestones
        self._assert_immutable_milestone_terms(
            db,
            contract=contract,
            fee_rate_bp=fee_rate_bp,
            term_items=milestone_term_mappings,
        )

        # Compute next version number
        max_ver = db.query(func.coalesce(func.max(ContractVersion.version_no), 0)).filter_by(
            contract_id=contract.id
        ).scalar() or 0
        version_no = max_ver + 1

        terms_json = payload.terms_json or {
            "client_user_id": contract.client_user_id,
            "freelancer_student_id": contract.freelancer_student_id,
            "created_at": _norm_utc(ctx.now_utc).isoformat(),
        }

        # Build term data for hash
        terms_data_for_hash = []
        for ms, t in milestone_term_mappings:
            terms_data_for_hash.append({
                "sequence_no": ms.sequence_no,
                "milestone_id": ms.id,
                "title": t.title,
                "description": t.description,
                "amount": t.amount,
                "acceptance_criteria": t.acceptance_criteria,
                "due_at": _norm_utc(t.due_at),
                "included": t.included,
            })

        content_hash = compute_version_content_hash(
            contract_id=contract.id,
            version_no=version_no,
            total_amount=payload.total_amount,
            fee_rate_bp=fee_rate_bp,
            funding_policy=payload.funding_policy,
            review_period_seconds=review_period_seconds,
            max_revision_count=max_revision_count,
            grace_period_seconds=grace_period_seconds,
            terms_json=terms_json,
            milestone_terms=terms_data_for_hash,
        )

        version = ContractVersion(
            contract_id=contract.id,
            version_no=version_no,
            created_by=ctx.actor_user_id,
            status=ContractVersionStatus.DRAFT,
            total_amount=payload.total_amount,
            fee_rate_bp=fee_rate_bp,
            review_period_seconds=review_period_seconds,
            max_revision_count=max_revision_count,
            grace_period_seconds=grace_period_seconds,
            funding_policy=payload.funding_policy,
            terms_json=terms_json,
            content_hash=content_hash,
        )
        db.add(version)
        db.flush()

        for ms, t in milestone_term_mappings:
            term = ContractMilestoneTerm(
                contract_id=contract.id,
                contract_version_id=version.id,
                milestone_id=ms.id,
                title=t.title,
                description=t.description,
                amount=t.amount,
                acceptance_criteria=t.acceptance_criteria,
                due_at=_norm_utc(t.due_at),
                included=t.included,
            )
            db.add(term)
        db.flush()

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract_version.created",
                entity_type="contract_versions",
                entity_id=version.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return version

    def offer_version_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
        acceptance_deadline: datetime | None = None,
    ) -> ContractVersion:
        """Offer a DRAFT version under project and contract locks."""
        version_raw = db.get(ContractVersion, version_id)
        if not version_raw:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        project, contract, budget, version, _ = _lock_contract_hierarchy(
            db, contract_id=version_raw.contract_id, version_id=version_raw.id,
        )
        if not version or not contract or not project or not budget:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check
        if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        if version.created_by != ctx.actor_user_id:
            raise ForbiddenError("Only creator can offer this version", code="FORBIDDEN")

        if version.status != ContractVersionStatus.DRAFT:
            raise ConflictError("Version is not draft", code="INVALID_STATE_TRANSITION")

        # Re-check immutable terms invariants before offering version
        version_terms = db.query(ContractMilestoneTerm).filter_by(contract_version_id=version.id).all()
        term_items = [(db.get(Milestone, t.milestone_id), t) for t in version_terms if t.milestone_id is not None]
        self._assert_immutable_milestone_terms(
            db,
            contract=contract,
            fee_rate_bp=version.fee_rate_bp,
            term_items=term_items,
        )

        now = _norm_utc(ctx.now_utc)

        # Check existing OFFERED versions on this contract
        active_offered = db.query(ContractVersion).filter(
            ContractVersion.contract_id == contract.id,
            ContractVersion.status == ContractVersionStatus.OFFERED,
            ContractVersion.id != version.id,
        ).all()

        for off in active_offered:
            if off.acceptance_deadline and now > off.acceptance_deadline:
                off.status = ContractVersionStatus.EXPIRED
            else:
                raise ConflictError("Another offered version is still active", code="CONTRACT_VERSION_CONFLICT")

        # Check and coordinate budget allocation
        if version.total_amount > budget.allocated_amount:
            if ctx.actor_user_id == contract.client_user_id:
                other_allocated = db.query(func.coalesce(func.sum(ProjectContractBudget.allocated_amount), 0)).filter(
                    ProjectContractBudget.project_id == project.id,
                    ProjectContractBudget.contract_id != contract.id,
                    ProjectContractBudget.status.in_([ContractBudgetStatus.RESERVED, ContractBudgetStatus.COMMITTED]),
                ).scalar() or 0

                if other_allocated + version.total_amount > project.budget_amount:
                    raise ConflictError("Version total amount exceeds project budget", code="PROJECT_BUDGET_EXCEEDED")
                budget.allocated_amount = version.total_amount
            else:
                raise ConflictError("Proposed total amount exceeds contract allocated budget", code="PROJECT_BUDGET_EXCEEDED")

        # Freeze deadline and mark OFFERED
        deadline = _norm_utc(acceptance_deadline) or (now + timedelta(days=7))
        version.status = ContractVersionStatus.OFFERED
        version.offered_at = now
        version.acceptance_deadline = deadline

        if ctx.actor_user_id == contract.client_user_id:
            version.client_accepted_at = now
        else:
            version.freelancer_accepted_at = now

        if contract.status == ContractStatus.DRAFT:
            contract.status = ContractStatus.PENDING_ACCEPTANCE

        # Schedule expiration job
        job_key = f"contract_version.expire:{version.id}"
        db.add(
            ScheduledJob(
                job_key=job_key,
                job_type="contract_version.expire",
                entity_type="contract_versions",
                entity_id=version.id,
                run_at=deadline,
                payload_json={"version_id": version.id, "contract_id": contract.id},
                status=ScheduledJobStatus.PENDING,
            )
        )

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract_version.offered",
                entity_type="contract_versions",
                entity_id=version.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return version

    def accept_version_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
        content_hash: str,
    ) -> ContractVersion:
        """Accept an offered version under lock and activate contract on mutual agreement."""
        version_raw = db.get(ContractVersion, version_id)
        if not version_raw:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        project, contract, budget, version, milestones = _lock_contract_hierarchy(
            db, contract_id=version_raw.contract_id, version_id=version_raw.id, lock_milestones=True,
        )
        if not version or not contract or not project or not budget:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check
        if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        if version.status != ContractVersionStatus.OFFERED:
            raise ConflictError("Version is not in OFFERED status", code="CONTRACT_VERSION_CONFLICT")

        # Re-check immutable terms invariants before accepting version
        version_terms = db.query(ContractMilestoneTerm).filter_by(contract_version_id=version.id).all()
        term_items = [(db.get(Milestone, t.milestone_id), t) for t in version_terms if t.milestone_id is not None]
        self._assert_immutable_milestone_terms(
            db,
            contract=contract,
            fee_rate_bp=version.fee_rate_bp,
            term_items=term_items,
        )

        now = _norm_utc(ctx.now_utc)
        if version.acceptance_deadline and now > version.acceptance_deadline:
            self.expire_version_in_tx(db, ctx=ctx, version_id=version.id)
            raise ConflictError("Contract version offer has expired", code="CONTRACT_VERSION_CONFLICT")

        # Prevent duplicate accept from same party
        if ctx.actor_user_id == contract.client_user_id and version.client_accepted_at is not None:
            raise ConflictError("Party has already accepted this version", code="INVALID_STATE_TRANSITION")
        if ctx.actor_user_id == student.user_id and version.freelancer_accepted_at is not None:
            raise ConflictError("Party has already accepted this version", code="INVALID_STATE_TRANSITION")

        if version.content_hash != content_hash:
            raise ConflictError("Content hash mismatch", code="CONTRACT_VERSION_CONFLICT")

        # Record accepting party timestamp
        if ctx.actor_user_id == contract.client_user_id:
            version.client_accepted_at = now
        else:
            version.freelancer_accepted_at = now

        # Mutual acceptance reached
        if version.client_accepted_at and version.freelancer_accepted_at:
            if contract.effective_version_id:
                old_ver = db.get(ContractVersion, contract.effective_version_id)
                if old_ver:
                    old_ver.status = ContractVersionStatus.SUPERSEDED

            version.status = ContractVersionStatus.EFFECTIVE
            version.effective_at = now
            contract.effective_version_id = version.id

            # Activate contract and commit budget if first time
            if contract.status in (ContractStatus.DRAFT, ContractStatus.PENDING_ACCEPTANCE):
                contract.status = ContractStatus.ACTIVE
                contract.activated_at = now

                if budget:
                    budget.status = ContractBudgetStatus.COMMITTED
                    budget.committed_at = now
                    # Tighten budget to total_amount on initial activation
                    if version.total_amount < budget.allocated_amount:
                        budget.allocated_amount = version.total_amount

                if project and project.status == ProjectStatus.APPROVED:
                    project.status = ProjectStatus.IN_PROGRESS

            # Update effective terms on contract milestones
            terms = db.query(ContractMilestoneTerm).filter_by(contract_version_id=version.id).all()
            for term in terms:
                ms = db.get(Milestone, term.milestone_id)
                if ms:
                    is_locked = self._is_milestone_locked(db, ms)
                    if not is_locked or ms.effective_terms_id is None:
                        ms.effective_terms_id = term.id
                    if not term.included and ms.status == MilestoneStatus.NOT_FUNDED:
                        ms.status = MilestoneStatus.CANCELLED

            # Cancel pending expiration job
            job = db.query(ScheduledJob).filter(
                ScheduledJob.job_key == f"contract_version.expire:{version.id}",
                ScheduledJob.status == ScheduledJobStatus.PENDING,
            ).first()
            if job:
                job.status = ScheduledJobStatus.CANCELLED

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract_version.accepted",
                entity_type="contract_versions",
                entity_id=version.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return version

    def decline_version_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
        response_note: str | None = None,
    ) -> ContractVersion:
        """Decline an offered version by the recipient."""
        version_raw = db.get(ContractVersion, version_id)
        if not version_raw:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        _project, contract, _budget, version, _ = _lock_contract_hierarchy(
            db, contract_id=version_raw.contract_id, version_id=version_raw.id,
        )
        if not version or not contract:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check
        if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        if version.created_by == ctx.actor_user_id:
            raise ForbiddenError("Creator cannot decline own offer, use withdraw", code="FORBIDDEN")

        if version.status != ContractVersionStatus.OFFERED:
            raise ConflictError("Version is not in OFFERED status", code="CONTRACT_VERSION_CONFLICT")

        now = _norm_utc(ctx.now_utc)
        if version.acceptance_deadline and now > version.acceptance_deadline:
            self.expire_version_in_tx(db, ctx=ctx, version_id=version.id)
            raise ConflictError("Contract version offer has expired", code="CONTRACT_VERSION_CONFLICT")

        version.status = ContractVersionStatus.DECLINED
        version.response_note = response_note

        # Revert contract status if pending first acceptance
        if contract.status == ContractStatus.PENDING_ACCEPTANCE and not contract.effective_version_id:
            remaining_offered = db.query(ContractVersion).filter(
                ContractVersion.contract_id == contract.id,
                ContractVersion.status == ContractVersionStatus.OFFERED,
                ContractVersion.id != version.id,
            ).first()
            if not remaining_offered:
                contract.status = ContractStatus.DRAFT

        # Cancel pending expire job
        job = db.query(ScheduledJob).filter(
            ScheduledJob.job_key == f"contract_version.expire:{version.id}",
            ScheduledJob.status == ScheduledJobStatus.PENDING,
        ).first()
        if job:
            job.status = ScheduledJobStatus.CANCELLED

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract_version.declined",
                entity_type="contract_versions",
                entity_id=version.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return version

    def withdraw_version_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
    ) -> ContractVersion:
        """Withdraw a DRAFT or OFFERED version by its creator."""
        version_raw = db.get(ContractVersion, version_id)
        if not version_raw:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        _project, contract, _budget, version, _ = _lock_contract_hierarchy(
            db, contract_id=version_raw.contract_id, version_id=version_raw.id,
        )
        if not version or not contract:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        student = db.get(Student, contract.freelancer_student_id)
        if not student:
            raise NotFoundError("Student not found", code="NOT_FOUND")

        # Zero-Leak check
        if ctx.actor_user_id not in (contract.client_user_id, student.user_id):
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        if version.created_by != ctx.actor_user_id:
            raise ForbiddenError("Only creator can withdraw this version", code="FORBIDDEN")

        if version.status == ContractVersionStatus.EFFECTIVE:
            raise ConflictError("Cannot withdraw effective version", code="INVALID_STATE_TRANSITION")

        if version.status not in (ContractVersionStatus.DRAFT, ContractVersionStatus.OFFERED):
            raise ConflictError("Version cannot be withdrawn", code="INVALID_STATE_TRANSITION")

        version.status = ContractVersionStatus.WITHDRAWN

        if contract.status == ContractStatus.PENDING_ACCEPTANCE and not contract.effective_version_id:
            remaining_offered = db.query(ContractVersion).filter(
                ContractVersion.contract_id == contract.id,
                ContractVersion.status == ContractVersionStatus.OFFERED,
                ContractVersion.id != version.id,
            ).first()
            if not remaining_offered:
                contract.status = ContractStatus.DRAFT

        # Cancel pending expire job
        job = db.query(ScheduledJob).filter(
            ScheduledJob.job_key == f"contract_version.expire:{version.id}",
            ScheduledJob.status == ScheduledJobStatus.PENDING,
        ).first()
        if job:
            job.status = ScheduledJobStatus.CANCELLED

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract_version.withdrawn",
                entity_type="contract_versions",
                entity_id=version.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return version

    def expire_version_in_tx(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
    ) -> ContractVersion:
        """Expire an OFFERED version under hierarchy lock."""
        version_raw = db.get(ContractVersion, version_id)
        if not version_raw:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        _project, contract, _budget, version, _ = _lock_contract_hierarchy(
            db, contract_id=version_raw.contract_id, version_id=version_raw.id,
        )
        if not version or not contract:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        if version.status == ContractVersionStatus.EXPIRED:
            return version

        version.status = ContractVersionStatus.EXPIRED

        if contract.status == ContractStatus.PENDING_ACCEPTANCE and not contract.effective_version_id:
            remaining_offered = db.query(ContractVersion).filter(
                ContractVersion.contract_id == contract.id,
                ContractVersion.status == ContractVersionStatus.OFFERED,
                ContractVersion.id != version.id,
            ).first()
            if not remaining_offered:
                contract.status = ContractStatus.DRAFT

        # Mark job completed if any
        job = db.query(ScheduledJob).filter(
            ScheduledJob.job_key == f"contract_version.expire:{version.id}",
            ScheduledJob.status == ScheduledJobStatus.PENDING,
        ).first()
        if job:
            job.status = ScheduledJobStatus.SUCCEEDED

        db.add(
            AuditLog(
                actor_user_id=ctx.actor_user_id,
                actor_type=ctx.actor_type,
                action="contract_version.expired",
                entity_type="contract_versions",
                entity_id=version.id,
                request_id=ctx.request_id,
            )
        )
        db.flush()

        return version

    # -------------------------------------------------------------------------
    # Zero-Leak Read Methods
    # -------------------------------------------------------------------------

    def get_contract(
        self,
        db: Session,
        *,
        contract_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> FreelanceContract:
        """Fetch contract ensuring strict zero-leak ownership rules."""
        contract = db.get(FreelanceContract, contract_id)
        if not contract:
            raise NotFoundError("Contract not found", code="NOT_FOUND")

        if not is_admin:
            student = db.get(Student, contract.freelancer_student_id)
            if not student or actor_user_id not in (contract.client_user_id, student.user_id):
                raise NotFoundError("Contract not found", code="NOT_FOUND")

        return contract

    def get_contract_versions(
        self,
        db: Session,
        *,
        contract_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> list[ContractVersion]:
        """List versions for a contract with zero-leak check."""
        self.get_contract(db, contract_id=contract_id, actor_user_id=actor_user_id, is_admin=is_admin)
        return (
            db.query(ContractVersion)
            .filter_by(contract_id=contract_id)
            .order_by(ContractVersion.version_no.desc())
            .all()
        )

    def get_contract_version(
        self,
        db: Session,
        *,
        version_id: int,
        actor_user_id: int | None = None,
        is_admin: bool = False,
    ) -> ContractVersion:
        """Fetch single version with zero-leak check."""
        version = db.get(ContractVersion, version_id)
        if not version:
            raise NotFoundError("Contract version not found", code="NOT_FOUND")

        self.get_contract(db, contract_id=version.contract_id, actor_user_id=actor_user_id, is_admin=is_admin)
        return version

    # -------------------------------------------------------------------------
    # Public Entrypoints wrapped with run_command
    # -------------------------------------------------------------------------

    def create_version(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        contract_id: int,
        payload: ContractVersionCreate,
    ) -> ContractVersion:
        return run_command(db, lambda: self.create_version_in_tx(db, ctx=ctx, contract_id=contract_id, payload=payload))

    def offer_version(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
        acceptance_deadline: datetime | None = None,
    ) -> ContractVersion:
        return run_command(db, lambda: self.offer_version_in_tx(db, ctx=ctx, version_id=version_id, acceptance_deadline=acceptance_deadline))

    def accept_version(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
        content_hash: str,
    ) -> ContractVersion:
        try:
            return run_command(
                db,
                lambda: self.accept_version_in_tx(
                    db, ctx=ctx, version_id=version_id, content_hash=content_hash
                ),
            )
        except ConflictError as exc:
            if exc.message == "Contract version offer has expired":
                try:
                    run_command(db, lambda: self.expire_version_in_tx(db, ctx=ctx, version_id=version_id))
                except Exception:
                    pass
            raise exc

    def decline_version(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
        response_note: str | None = None,
    ) -> ContractVersion:
        try:
            return run_command(
                db,
                lambda: self.decline_version_in_tx(
                    db, ctx=ctx, version_id=version_id, response_note=response_note
                ),
            )
        except ConflictError as exc:
            if exc.message == "Contract version offer has expired":
                try:
                    run_command(db, lambda: self.expire_version_in_tx(db, ctx=ctx, version_id=version_id))
                except Exception:
                    pass
            raise exc

    def withdraw_version(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
    ) -> ContractVersion:
        return run_command(db, lambda: self.withdraw_version_in_tx(db, ctx=ctx, version_id=version_id))

    def expire_version(
        self,
        db: Session,
        *,
        ctx: CommandContext,
        version_id: int,
    ) -> ContractVersion:
        return run_command(db, lambda: self.expire_version_in_tx(db, ctx=ctx, version_id=version_id))
