"""Group B: project moderation, recruiting, selection and budget under parent locks."""

from sqlalchemy import func, select

from app.core.enums import UserRole
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.freelancer_enums import (
    ContractBudgetStatus,
    ContractStatus,
    ContractVersionStatus,
    FreelanceApplicationStatus,
    FundingPolicy,
    ProjectStatus,
    RecruitmentStatus,
)
from app.models import (
    CV,
    ClientProfile,
    Company,
    FreelanceApplication,
    FreelanceContract,
    FreelanceProject,
    FreelanceProjectAttachment,
    FreelanceProjectReview,
    FreelanceProjectSkill,
    ProjectContractBudget,
    ProjectMilestoneProposal,
    Skill,
    StoredFile,
    Student,
    User,
)
from app.services.freelance_contract_service import FreelanceContractService
from app.services.freelancer_accounts.eligibility_service import get_client_eligibility
from app.services.freelancer_domain import (
    audit,
    ctx,
    lock,
    now,
    owner,
    page,
    record,
    replay,
    student,
    user,
)
from app.services.freelancer_policy_service import company_limits, read_policy

LIVE = (ProjectStatus.APPROVED, ProjectStatus.IN_PROGRESS)
EDITABLE = (ProjectStatus.DRAFT, ProjectStatus.NEEDS_REVISION)


def project_view(db, p, *, private=True):
    data = record(p, exclude=("reviewed_by",))
    company = db.get(Company, p.company_id) if p.company_id else None
    client = (
        db.scalar(select(ClientProfile).where(ClientProfile.user_id == p.client_user_id))
        if not company
        else None
    )
    data["client_display_name"] = (
        company.name if company else client.full_name if client else "Người thuê"
    )
    data["proposals"] = [
        record(x)
        for x in db.scalars(
            select(ProjectMilestoneProposal)
            .where(ProjectMilestoneProposal.project_id == p.id)
            .order_by(ProjectMilestoneProposal.sequence_no)
        ).all()
    ]
    data["skill_ids"] = [
        str(x)
        for x in db.scalars(
            select(FreelanceProjectSkill.skill_id).where(FreelanceProjectSkill.project_id == p.id)
        ).all()
    ]
    data["attachments"] = [
        {
            "file_id": str(f.id),
            "original_name": f.original_name,
            "size_bytes": f.size_bytes,
            "scan_status": f.scan_status,
            "availability_status": f.availability_status,
        }
        for f in db.scalars(
            select(StoredFile)
            .join(FreelanceProjectAttachment, FreelanceProjectAttachment.file_id == StoredFile.id)
            .where(FreelanceProjectAttachment.project_id == p.id)
        ).all()
    ]
    data["skills"] = [
        {"id": str(s.id), "name": s.name}
        for s in db.scalars(
            select(Skill)
            .join(FreelanceProjectSkill, FreelanceProjectSkill.skill_id == Skill.id)
            .where(FreelanceProjectSkill.project_id == p.id)
            .order_by(Skill.name)
        ).all()
    ]
    if not private:
        data.pop("review_reason", None)
    return data


def _eligible(db, user_id, cap):
    user(db, user_id, UserRole.CLIENT, UserRole.COMPANY)
    e = get_client_eligibility(db, user_id=user_id, now_utc=now())
    if not getattr(e, cap):
        raise ForbiddenError("Client is not eligible", code="CLIENT_NOT_ELIGIBLE")
    return e


def _company_lock(db, user_id):
    c = db.scalar(select(Company).where(Company.user_id == user_id))
    return lock(db, Company, id=c.id) if c else None


def _validate(db, payload):
    if (payload.budget_amount is not None and payload.budget_amount <= 0) or any(
        t.amount <= 0 for t in payload.proposals
    ):
        raise BadRequestError("Amounts must be positive")
    if (
        payload.proposals
        and payload.budget_amount is not None
        and sum(t.amount for t in payload.proposals) != payload.budget_amount
    ):
        raise BadRequestError("Proposal total must equal project budget")
    if payload.deadline and any(t.due_at > payload.deadline for t in payload.proposals):
        raise BadRequestError("Milestone dates must be within project deadline")
    if (
        payload.deadline
        and payload.recruitment_deadline
        and payload.recruitment_deadline > payload.deadline
    ):
        raise BadRequestError("Recruitment deadline cannot exceed completion deadline")
    if len(set(payload.skill_ids)) != len(payload.skill_ids):
        raise BadRequestError("Duplicate skills")
    if payload.skill_ids:
        found = db.scalars(
            select(Skill.id).where(Skill.id.in_(payload.skill_ids), Skill.is_active.is_(True))
        ).all()
        if len(found) != len(payload.skill_ids):
            raise BadRequestError("Unknown or inactive skill")
    if len(set(payload.attachment_file_ids)) != len(payload.attachment_file_ids):
        raise BadRequestError("Duplicate attachments")


def _ready(db, p):
    """Drafts may be incomplete; moderation must receive a complete, current post."""
    data = project_view(db, p)
    missing = [
        key
        for key in (
            "description",
            "budget_amount",
            "deadline",
            "recruitment_deadline",
            "category",
            "acceptance_criteria",
            "deliverables_description",
        )
        if not data.get(key)
    ]
    if not data["skill_ids"]:
        missing.append("skill_ids")
    if missing:
        raise BadRequestError(
            "Complete required project fields: " + ", ".join(missing), code="PROJECT_INCOMPLETE"
        )
    if p.deadline <= now() or p.recruitment_deadline <= now():
        raise BadRequestError("Project and recruitment deadlines must be in the future")
    if p.recruitment_deadline > p.deadline:
        raise BadRequestError("Recruitment deadline cannot exceed completion deadline")
    proposals = db.scalars(
        select(ProjectMilestoneProposal).where(ProjectMilestoneProposal.project_id == p.id)
    ).all()
    if proposals and (
        sum(t.amount for t in proposals) != p.budget_amount
        or any(t.due_at <= now() or t.due_at > p.deadline for t in proposals)
    ):
        raise BadRequestError("Check proposal amounts and milestone deadlines")
    active_skills = db.scalars(
        select(Skill.id).where(
            Skill.id.in_([int(i) for i in data["skill_ids"]]), Skill.is_active.is_(True)
        )
    ).all()
    if len(active_skills) != len(data["skill_ids"]):
        raise BadRequestError("Unknown or inactive skill")
    from app.services.freelancer_accounts.identity_service import checked_file

    for f in data["attachments"]:
        checked_file(db, int(f["file_id"]), p.client_user_id, category="PROJECT_REFERENCE")


def _policy(db, p, company):
    policy, revision = read_policy(db)
    if p.budget_amount <= policy.small_project_threshold and p.funding_policy != FundingPolicy.FULL:
        raise BadRequestError("Small projects require FULL funding")
    if company:
        limits = company_limits(db, company)
        max_amount = (
            limits["max_project_amount"] if isinstance(limits, dict) else limits.max_project_amount
        )
        max_open = (
            limits["max_open_projects"] if isinstance(limits, dict) else limits.max_open_projects
        )
        full = (
            limits["full_prefunding_required"]
            if isinstance(limits, dict)
            else limits.full_prefunding_required
        )
        if full and p.funding_policy != FundingPolicy.FULL:
            raise BadRequestError("Company policy requires FULL funding")
    else:
        max_amount, max_open = policy.client_max_project_amount, policy.client_max_open_projects
    count = db.scalar(
        select(func.count())
        .select_from(FreelanceProject)
        .where(
            FreelanceProject.client_user_id == p.client_user_id,
            FreelanceProject.id != p.id,
            FreelanceProject.status.in_([ProjectStatus.PENDING_REVIEW, *LIVE]),
        )
        .with_for_update()
    )
    if p.budget_amount > max_amount or count >= max_open:
        raise ConflictError("Project policy limit exceeded", code="PROJECT_LIMIT_EXCEEDED")
    return revision


def create_in_tx(db, *, user_id, payload):
    from app.services.ux_terms import require_escrow_terms
    e = _eligible(db, user_id, "can_draft")
    require_escrow_terms(db, user_id)
    _validate(db, payload)
    p = FreelanceProject(
        client_user_id=user_id,
        company_id=e.company_id,
        **payload.model_dump(exclude={"proposals", "skill_ids", "attachment_file_ids"}),
    )
    db.add(p)
    db.flush()
    _parts(db, p, payload)
    audit(db, user_id, "project.created", "freelance_projects", p.id)
    return project_view(db, p)


def _parts(db, p, payload):
    from app.services.freelancer_accounts.identity_service import checked_file

    for file_id in sorted(payload.attachment_file_ids):
        checked_file(db, file_id, p.client_user_id, category="PROJECT_REFERENCE")
        db.add(FreelanceProjectAttachment(project_id=p.id, file_id=file_id))
    for i, t in enumerate(payload.proposals, 1):
        db.add(ProjectMilestoneProposal(project_id=p.id, sequence_no=i, **t.model_dump()))
    for skill_id in payload.skill_ids:
        db.add(FreelanceProjectSkill(project_id=p.id, skill_id=skill_id))
    db.flush()


def update_in_tx(db, *, user_id, project_id, payload):
    _eligible(db, user_id, "can_draft")
    p = owner(db, project_id, user_id, write=True)
    if p.status not in EDITABLE:
        raise ConflictError("Only draft projects may be edited")
    _validate(db, payload)
    for k, v in payload.model_dump(
        exclude={"proposals", "skill_ids", "attachment_file_ids"}
    ).items():
        setattr(p, k, v)
    for row in db.scalars(
        select(ProjectMilestoneProposal).where(ProjectMilestoneProposal.project_id == p.id)
    ).all():
        db.delete(row)
    for row in db.scalars(
        select(FreelanceProjectSkill).where(FreelanceProjectSkill.project_id == p.id)
    ).all():
        db.delete(row)
    for row in db.scalars(
        select(FreelanceProjectAttachment).where(FreelanceProjectAttachment.project_id == p.id)
    ).all():
        db.delete(row)
    db.flush()
    _parts(db, p, payload)
    p.status = ProjectStatus.DRAFT
    audit(db, user_id, "project.updated", "freelance_projects", p.id)
    return project_view(db, p)


def submit_in_tx(db, *, user_id, project_id):
    e = _eligible(db, user_id, "can_submit")
    c = _company_lock(db, user_id)
    # User parent serializes individual-client concurrent submissions too.
    if not c:
        lock(db, User, id=user_id)
    p = owner(db, project_id, user_id, write=True)
    if p.status not in EDITABLE:
        raise ConflictError("Project cannot be submitted")
    if p.company_id != e.company_id:
        raise ConflictError("Company ownership changed")
    _ready(db, p)
    revision = _policy(db, p, c)
    p.status = ProjectStatus.PENDING_REVIEW
    p.submitted_at = now()
    audit(
        db,
        user_id,
        "project.submitted",
        "freelance_projects",
        p.id,
        after={"policy_revision": revision},
    )
    from app.services.freelancer_domain import notify_admins

    notify_admins(
        db,
        "Dự án Freelancer mới chờ duyệt",
        f'Người thuê vừa gửi dự án "{p.title}" để xét duyệt.',
        ref_type="FREELANCE_PROJECT",
        ref_id=p.id,
    )
    return project_view(db, p)


def review_in_tx(db, *, user_id, project_id, decision, reason):
    from app.services.freelancer_domain import admin

    admin(db, user_id)
    raw = db.get(FreelanceProject, project_id)
    if raw and raw.company_id:
        lock(db, Company, id=raw.company_id)
    p = lock(db, FreelanceProject, id=project_id)
    if not p:
        raise NotFoundError("Project not found")
    if p.client_user_id == user_id:
        raise ForbiddenError("Cannot review your own project")
    if p.status != ProjectStatus.PENDING_REVIEW:
        raise ConflictError("Project is not pending review")
    reason = (reason or "").strip()
    if decision != "APPROVED" and not reason:
        raise BadRequestError("Reason is required when the project is not approved")
    if decision == "APPROVED":
        _eligible(db, p.client_user_id, "can_submit")
        _ready(db, p)
        _policy(db, p, db.get(Company, p.company_id) if p.company_id else None)
    snapshot = project_view(db, p)
    db.add(
        FreelanceProjectReview(
            project_id=p.id,
            reviewed_by=user_id,
            decision=decision,
            reason=reason,
            project_snapshot=snapshot,
        )
    )
    p.status = ProjectStatus(decision)
    p.reviewed_by = user_id
    p.reviewed_at = now()
    p.review_reason = reason
    if decision == "APPROVED":
        p.recruitment_status = RecruitmentStatus.OPEN
    audit(
        db,
        user_id,
        "project.reviewed",
        "freelance_projects",
        p.id,
        after={"decision": decision},
        reason=reason,
    )
    from app.services.freelancer_domain import notify

    notify(
        db,
        p.client_user_id,
        "Kết quả duyệt dự án Freelancer",
        reason or f'Dự án "{p.title}" đã được phê duyệt và mở nhận ứng tuyển.',
        ref_type="FREELANCE_PROJECT",
        ref_id=p.id,
    )
    return project_view(db, p)


def get_project(db, *, user_id, project_id):
    u = user(db, user_id)
    p = db.get(FreelanceProject, project_id)
    if not p or (p.status not in LIVE and u.role != UserRole.ADMIN and p.client_user_id != user_id):
        raise NotFoundError("Project not found")
    result = project_view(db, p, private=u.role == UserRole.ADMIN or p.client_user_id == user_id)
    if u.role == UserRole.STUDENT:
        application = db.scalar(
            select(FreelanceApplication)
            .join(Student, Student.id == FreelanceApplication.student_id)
            .where(Student.user_id == user_id, FreelanceApplication.project_id == p.id)
        )
        result["my_application"] = record(application) if application else None
    return result


def list_projects(db, *, user_id, mine=False, number=1, size=20, search=None, category=None):
    u = user(db, user_id)
    stmt = select(FreelanceProject)
    if category:
        stmt = stmt.where(FreelanceProject.category == category)
    if mine:
        stmt = stmt.where(FreelanceProject.client_user_id == user_id)
    elif u.role == UserRole.STUDENT:
        # The student discovery page is a recruiting marketplace, not project
        # history.  Closed recruitment must disappear immediately even while a
        # project/contract closure is being reconciled in a separate workflow.
        stmt = stmt.where(
            FreelanceProject.status.in_(LIVE),
            FreelanceProject.recruitment_status == RecruitmentStatus.OPEN,
            func.coalesce(
                FreelanceProject.recruitment_deadline,
                FreelanceProject.deadline,
            )
            > now(),
        )
    elif u.role != UserRole.ADMIN:
        stmt = stmt.where(FreelanceProject.status.in_(LIVE))
    if search and search.strip():
        stmt = stmt.where(
            func.lower(FreelanceProject.title).contains(search.strip().lower(), autoescape=True)
        )
    return page(
        db,
        stmt.order_by(FreelanceProject.id.desc()),
        number,
        size,
        project=lambda p: project_view(
            db, p, private=u.role == UserRole.ADMIN or p.client_user_id == user_id
        ),
    )


def apply_in_tx(db, *, user_id, project_id, payload):
    s = student(db, user_id)
    from app.services.student_lifecycle import require_new_activity
    require_new_activity(s)
    p = lock(db, FreelanceProject, id=project_id)
    if not p or p.status not in LIVE or p.recruitment_status != RecruitmentStatus.OPEN:
        raise ConflictError("Project is not recruiting")
    if p.client_user_id == user_id:
        raise ForbiddenError("Cannot apply to own project")
    if (p.recruitment_deadline or p.deadline) <= now():
        raise ConflictError("Recruitment deadline has passed")
    if payload.quoted_amount <= 0 or payload.quoted_amount > p.budget_amount:
        raise BadRequestError("Quote exceeds project budget")
    if db.scalar(
        select(FreelanceApplication.id).where(
            FreelanceApplication.project_id == p.id, FreelanceApplication.student_id == s.id
        )
    ):
        raise ConflictError("An application already exists, including withdrawn applications")
    if payload.cv_id:
        cv = db.get(CV, payload.cv_id)
        if not cv or cv.student_id != s.id or cv.deleted_at is not None:
            raise NotFoundError("CV not found")
    if payload.cv_snapshot_file_id:
        from app.services.freelancer_accounts.identity_service import checked_file

        checked_file(db, payload.cv_snapshot_file_id, user_id, category="CV")
    a = FreelanceApplication(project_id=p.id, student_id=s.id, **payload.model_dump())
    db.add(a)
    db.flush()
    audit(db, user_id, "application.created", "freelance_applications", a.id)
    from app.services.freelancer_domain import notify

    notify(
        db,
        p.client_user_id,
        "Có sinh viên ứng tuyển dự án",
        f'{s.full_name} vừa gửi đề xuất cho dự án "{p.title}".',
        ref_type="FREELANCE_APPLICATION",
        ref_id=a.id,
    )
    return record(a)


def application_action_in_tx(db, *, user_id, application_id, action):
    a = db.get(FreelanceApplication, application_id)
    if not a:
        raise NotFoundError("Application not found")
    p = lock(db, FreelanceProject, id=a.project_id)
    a = lock(db, FreelanceApplication, id=a.id)
    if action == "withdraw":
        s = student(db, user_id)
        if a.student_id != s.id:
            raise NotFoundError("Application not found")
    else:
        owner(db, p.id, user_id)
    if a.status not in (
        FreelanceApplicationStatus.SUBMITTED,
        FreelanceApplicationStatus.SHORTLISTED,
    ):
        raise ConflictError("Application cannot transition")
    a.status = {"withdraw": "WITHDRAWN", "shortlist": "SHORTLISTED", "reject": "REJECTED"}[action]
    audit(db, user_id, "application." + action, "freelance_applications", a.id)
    from app.services.freelancer_domain import notify

    recipient = db.get(Student, a.student_id)
    if action != "withdraw" and recipient:
        notify(
            db,
            recipient.user_id,
            "Cập nhật đơn ứng tuyển Freelancer",
            "Đề xuất của bạn đã được đưa vào danh sách cân nhắc." if action == "shortlist" else "Người thuê đã từ chối đề xuất của bạn.",
            ref_type="FREELANCE_APPLICATION",
            ref_id=a.id,
        )
    return record(a)


def select_in_tx(db, *, user_id, project_id, payload, key):
    _eligible(db, user_id, "can_submit")
    _company_lock(db, user_id)
    p = owner(db, project_id, user_id, write=True)

    def action():
        if p.status not in LIVE or p.recruitment_status != RecruitmentStatus.OPEN:
            raise ConflictError("Project is not recruiting")
        a = db.get(FreelanceApplication, payload.application_id)
        if not a or a.project_id != p.id:
            raise NotFoundError("Application not found")
        s = db.get(Student, a.student_id)
        if not s:
            raise NotFoundError("Student not found")
        student(db, s.user_id)
        ref = FreelanceContractService().create_contract_for_selected_application_in_tx(
            db,
            ctx=ctx(user_id, key),
            project_id=p.id,
            application_id=a.id,
            allocated_amount=payload.allocated_amount,
        )
        audit(db, user_id, "project.student_selected", "freelance_contracts", ref.contract_id)
        return {
            "contract_id": str(ref.contract_id),
            "project_id": str(p.id),
            "allocated_amount": str(ref.allocated_amount),
            "status": ref.status.value,
        }

    return replay(
        db,
        actor_id=user_id,
        operation="freelance.select_student",
        key=key,
        body={"project_id": str(p.id), **payload.model_dump(mode="json")},
        action=action,
    )


def recruitment_in_tx(db, *, user_id, project_id, reopen):
    _company_lock(db, user_id)
    p = owner(db, project_id, user_id, write=True)
    if p.status not in LIVE:
        raise ConflictError("Project cannot change recruitment")
    if reopen:
        _eligible(db, user_id, "can_submit")
        count = db.scalar(
            select(func.count())
            .select_from(FreelanceContract)
            .where(
                FreelanceContract.project_id == p.id,
                FreelanceContract.status != ContractStatus.CANCELLED,
            )
            .with_for_update()
        )
        amount = db.scalar(
            select(func.coalesce(func.sum(ProjectContractBudget.allocated_amount), 0))
            .where(
                ProjectContractBudget.project_id == p.id,
                ProjectContractBudget.status != ContractBudgetStatus.RELEASED,
            )
            .with_for_update()
        )
        if (
            count >= p.max_students
            or amount >= p.budget_amount
            or (p.recruitment_deadline or p.deadline) <= now()
        ):
            raise ConflictError("No recruitment capacity remains")
        p.recruitment_status = RecruitmentStatus.OPEN
        p.recruitment_closed_at = None
    else:
        p.recruitment_status = RecruitmentStatus.CLOSED
        p.recruitment_closed_at = now()
    audit(db, user_id, "project.recruitment_changed", "freelance_projects", p.id)
    return project_view(db, p)


def budget_in_tx(db, *, user_id, contract_id, amount):
    from app.models import ContractVersion

    c = db.get(FreelanceContract, contract_id)
    if not c:
        raise NotFoundError("Contract not found")
    p = owner(db, c.project_id, user_id, write=True)
    c = lock(db, FreelanceContract, id=c.id)
    b = lock(db, ProjectContractBudget, contract_id=c.id)
    if not b or b.status == ContractBudgetStatus.RELEASED or amount <= 0:
        raise ConflictError("Budget cannot be changed")
    if b.status == ContractBudgetStatus.COMMITTED and amount < b.allocated_amount:
        raise ConflictError("Committed budget cannot be reclaimed")
    protected = db.scalars(
        select(ContractVersion).where(
            ContractVersion.contract_id == c.id,
            ContractVersion.status.in_(
                [ContractVersionStatus.OFFERED, ContractVersionStatus.EFFECTIVE]
            ),
        )
    ).all()
    if amount < b.allocated_amount and any(
        v.status == ContractVersionStatus.OFFERED for v in protected
    ):
        raise ConflictError("Withdraw offered version before reducing allocation")
    if any(v.total_amount > amount for v in protected):
        raise ConflictError("Budget cannot be below offered/effective obligations")
    used = db.scalar(
        select(func.coalesce(func.sum(ProjectContractBudget.allocated_amount), 0))
        .where(
            ProjectContractBudget.project_id == p.id,
            ProjectContractBudget.contract_id != c.id,
            ProjectContractBudget.status != ContractBudgetStatus.RELEASED,
        )
        .with_for_update()
    )
    if used + amount > p.budget_amount:
        raise ConflictError("Project budget exceeded", code="PROJECT_BUDGET_EXCEEDED")
    before = record(b)
    b.allocated_amount = amount
    audit(
        db,
        user_id,
        "budget.changed",
        "project_contract_budgets",
        b.id,
        before=before,
        after={"allocated_amount": str(amount)},
    )
    return record(b)


def applications(db, *, user_id, project_id=None, number=1, size=20):
    u = user(db, user_id)
    stmt = select(FreelanceApplication)
    if project_id is not None:
        owner(db, project_id, user_id)
        stmt = stmt.where(FreelanceApplication.project_id == project_id)
    elif u.role == UserRole.STUDENT:
        stmt = stmt.where(FreelanceApplication.student_id == student(db, user_id).id)
    else:
        raise ForbiddenError("Use a specific project")
    return page(
        db,
        stmt.order_by(FreelanceApplication.id.desc()),
        number,
        size,
        project=lambda a: {
            **record(a, exclude=("cv_snapshot_file_id",)),
            "student_name": db.get(Student, a.student_id).full_name,
            "student_user_id": str(db.get(Student, a.student_id).user_id),
            "cv_download_url": (
                f"/api/v1/files/{a.cv_snapshot_file_id}/download"
                if a.cv_snapshot_file_id
                else f"/api/v1/cvs/{a.cv_id}/download" if a.cv_id else None
            ),
        },
    )


def expand_in_tx(db, *, user_id, project_id, payload, key):
    from app.models import ProjectExpansion

    p = owner(db, project_id, user_id, write=True)
    if p.status not in LIVE:
        raise ConflictError("Only live projects may request expansion")
    if payload.budget_amount < p.budget_amount or payload.max_students < p.max_students:
        raise BadRequestError("Expansion cannot reduce approved ceilings")
    old = db.scalar(
        select(ProjectExpansion).where(
            ProjectExpansion.project_id == p.id, ProjectExpansion.request_key == key
        )
    )
    if old:
        if (
            old.budget_amount != payload.budget_amount
            or old.max_students != payload.max_students
            or old.reason != payload.reason
        ):
            raise ConflictError("Key used for another expansion", code="IDEMPOTENCY_CONFLICT")
        return record(old)
    if db.scalar(
        select(ProjectExpansion.id).where(
            ProjectExpansion.project_id == p.id, ProjectExpansion.status == "PENDING"
        )
    ):
        raise ConflictError("An expansion is already pending")
    row = ProjectExpansion(
        project_id=p.id, requested_by=user_id, request_key=key, **payload.model_dump()
    )
    db.add(row)
    db.flush()
    audit(db, user_id, "project.expansion_requested", "project_expansions", row.id)
    from app.services.freelancer_domain import notify_admins

    notify_admins(
        db,
        "Yêu cầu mở rộng dự án Freelancer",
        f'Người thuê yêu cầu tăng ngân sách hoặc số vị trí cho dự án "{p.title}".',
        ref_type="FREELANCE_PROJECT",
        ref_id=p.id,
    )
    return record(row)


def decide_expansion_in_tx(db, *, user_id, project_id, request_key, approve, reason):
    from app.models import ProjectExpansion
    from app.services.freelancer_domain import admin

    admin(db, user_id)
    raw = db.get(FreelanceProject, project_id)
    if raw and raw.company_id:
        lock(db, Company, id=raw.company_id)
    p = lock(db, FreelanceProject, id=project_id)
    if not p:
        raise NotFoundError("Project not found")
    row = lock(db, ProjectExpansion, project_id=p.id, request_key=request_key)
    if not row:
        raise NotFoundError("Expansion request not found")
    if row.status != "PENDING":
        raise ConflictError("Expansion already decided")
    reason = (reason or "").strip()
    if not approve and not reason:
        raise BadRequestError("Reason is required when rejecting an expansion request")
    if approve:
        if p.status not in LIVE:
            raise ConflictError("Project is no longer live")
        if p.client_user_id == user_id:
            raise ForbiddenError("Cannot approve own project")
        _eligible(db, p.client_user_id, "can_submit")
        # Validate proposed limit without changing any contract or published scope.
        old_amount, old_max = p.budget_amount, p.max_students
        p.budget_amount = max(old_amount, row.budget_amount)
        p.max_students = max(old_max, row.max_students)
        _policy(db, p, db.get(Company, p.company_id) if p.company_id else None)
    row.status = "APPROVED" if approve else "REJECTED"
    row.reviewed_by = user_id
    row.reviewed_at = now()
    row.review_reason = reason
    audit(db, user_id, "project.expansion_decided", "project_expansions", row.id, reason=reason)
    from app.services.freelancer_domain import notify

    notify(
        db,
        p.client_user_id,
        "Kết quả yêu cầu mở rộng dự án",
        "Yêu cầu mở rộng dự án đã được duyệt."
        if approve
        else f"Yêu cầu mở rộng dự án bị từ chối: {reason}",
        ref_type="FREELANCE_PROJECT",
        ref_id=p.id,
    )
    return project_view(db, p)


def contracts(db, *, user_id, project_id, number=1, size=20):
    u = user(db, user_id)
    p = db.get(FreelanceProject, project_id)
    if not p:
        raise NotFoundError("Project not found")
    stmt = select(FreelanceContract).where(FreelanceContract.project_id == p.id)
    if u.id != p.client_user_id and u.role != UserRole.ADMIN:
        s = student(db, user_id)
        stmt = stmt.where(FreelanceContract.freelancer_student_id == s.id)

    def view(c):
        data = record(c)
        data["student_name"] = db.get(Student, c.freelancer_student_id).full_name
        b = db.scalar(
            select(ProjectContractBudget).where(ProjectContractBudget.contract_id == c.id)
        )
        data["allocated_amount"] = str(b.allocated_amount) if b else "0"
        return data

    return page(db, stmt.order_by(FreelanceContract.id), number, size, project=view)


def summary(db, *, user_id, project_id):
    p = owner(db, project_id, user_id)
    allocated = db.scalar(
        select(func.coalesce(func.sum(ProjectContractBudget.allocated_amount), 0))
        .where(ProjectContractBudget.project_id == p.id, ProjectContractBudget.status != "RELEASED")
        .with_for_update()
    )
    count = db.scalar(
        select(func.count())
        .select_from(FreelanceContract)
        .where(FreelanceContract.project_id == p.id, FreelanceContract.status != "CANCELLED")
        .with_for_update()
    )
    return {
        "project_id": str(p.id),
        "budget_amount": str(p.budget_amount),
        "allocated_total": str(allocated),
        "remaining_budget_to_allocate": str(p.budget_amount - allocated),
        "contract_count": count,
        "max_students": p.max_students,
    }


def close_in_tx(db, *, user_id, project_id, cancel=False):
    p = owner(db, project_id, user_id, write=True)
    from app.services.freelance_closure_service import FreelanceClosureService

    service = FreelanceClosureService()
    if cancel and p.status not in (ProjectStatus.DRAFT, ProjectStatus.APPROVED):
        raise ConflictError("Project cannot be cancelled from this state")
    p.recruitment_status = RecruitmentStatus.CLOSED
    p.recruitment_closed_at = now()
    db.flush()
    if cancel:
        state = service.get_project_closure_state(db, project_id=p.id)
        if state.has_open_obligations:
            raise ConflictError("Resolve contract obligations before cancelling project")
        p.status = ProjectStatus.CANCELLED
        p.closed_at = now()
    else:
        service.recompute_project_closure_in_tx(db, ctx=ctx(user_id), project_id=p.id)
    audit(
        db,
        user_id,
        "project.cancelled" if cancel else "project.closure_requested",
        "freelance_projects",
        p.id,
    )
    return project_view(db, p)
