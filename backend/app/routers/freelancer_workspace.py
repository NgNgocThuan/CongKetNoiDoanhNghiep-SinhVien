"""Read models needed by Freelancer screens; scope every row to its viewer."""

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.enums import UserRole
from app.core.exceptions import NotFoundError
from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models import (
    BankDestination,
    BusinessVerification,
    CancellationAgreement,
    Company,
    Dispute,
    DisputeDecision,
    DisputeWithdrawal,
    EscrowAccount,
    FreelanceContract,
    FreelanceProject,
    LedgerAccount,
    LedgerJournal,
    LedgerPosting,
    Milestone,
    MoneyTransfer,
    MouAgreement,
    PaymentOrder,
    PaymentReviewCase,
    PaymentTransaction,
    ProjectExpansion,
    Settlement,
    Student,
    User,
)
from app.schemas.freelance_projects import Resource, ResourcePage
from app.services.freelancer_domain import milestone_scope, page, record

router = APIRouter(tags=["Freelancer workspace"])


@router.get("/freelancer/overview", response_model=Resource)
def overview(db: DbSession, u: CurrentUser):
    contract_ids = select(FreelanceContract.id)
    if u.role == UserRole.STUDENT:
        contract_ids = contract_ids.join(
            Student, Student.id == FreelanceContract.freelancer_student_id
        ).where(Student.user_id == u.id)
    elif u.role != UserRole.ADMIN:
        contract_ids = contract_ids.where(FreelanceContract.client_user_id == u.id)

    def count(model, *conditions):
        return db.scalar(select(func.count()).select_from(model).where(*conditions))

    active = contract_ids.where(FreelanceContract.status == "ACTIVE")
    money_rows = db.execute(
        select(
            EscrowAccount.funded_amount,
            EscrowAccount.reserved_amount,
            EscrowAccount.released_gross,
            EscrowAccount.refunded_amount,
        )
        .join(Milestone, Milestone.id == EscrowAccount.milestone_id)
        .where(Milestone.contract_id.in_(contract_ids))
    ).all()
    funded = sum(r.funded_amount for r in money_rows)
    released = sum(r.released_gross for r in money_rows)
    refunded = sum(r.refunded_amount for r in money_rows)
    result = {
        "project_count": count(FreelanceProject, FreelanceProject.client_user_id == u.id)
        if u.role not in (UserRole.ADMIN, UserRole.STUDENT)
        else count(
            FreelanceProject,
            FreelanceProject.id.in_(
                select(FreelanceContract.project_id).where(FreelanceContract.id.in_(contract_ids))
            ),
        )
        if u.role == UserRole.STUDENT
        else count(FreelanceProject),
        "active_contracts": db.scalar(select(func.count()).select_from(active.subquery())),
        "unfunded_milestones": count(
            Milestone, Milestone.contract_id.in_(active), Milestone.status == "NOT_FUNDED"
        ),
        "review_milestones": count(
            Milestone, Milestone.contract_id.in_(active), Milestone.status == "SUBMITTED"
        ),
        "work_milestones": count(
            Milestone,
            Milestone.contract_id.in_(active),
            Milestone.status.in_(("IN_PROGRESS", "REVISION_REQUESTED")),
        ),
        "usable_banks": count(
            BankDestination,
            BankDestination.user_id == u.id,
            BankDestination.verification_status.in_(("ACTIVE", "VERIFIED")),
        ),
        "waiting_bank_transfers": count(MoneyTransfer, MoneyTransfer.recipient_user_id == u.id, MoneyTransfer.status == "WAITING_BANK"),
        "funded_amount": str(funded),
        "held_amount": str(funded - released - refunded),
        "reserved_amount": str(sum(r.reserved_amount for r in money_rows)),
        "released_gross": str(released),
        "refunded_amount": str(refunded),
    }
    if u.role == UserRole.ADMIN:
        result.update(
            pending_verifications=count(
                BusinessVerification, BusinessVerification.status == "PENDING"
            ),
            pending_projects=count(FreelanceProject, FreelanceProject.status == "PENDING_REVIEW"),
            waiting_bank_transfers=count(MoneyTransfer, MoneyTransfer.status == "WAITING_BANK"),
            open_disputes=count(Dispute, Dispute.status.not_in(("RESOLVED", "WITHDRAWN"))),
            open_payment_reviews=count(PaymentReviewCase, PaymentReviewCase.status != "RESOLVED"),
            unresolved_transfers=count(
                MoneyTransfer, MoneyTransfer.status.in_(("WAITING_BANK", "PROCESSING", "UNKNOWN", "FAILED"))
            ),
        )
    return {"data": result}


@router.get("/payment-orders/by-code/{order_code}", response_model=Resource)
def order_by_code(order_code: int, db: DbSession, u: CurrentUser):
    row = db.scalar(select(PaymentOrder).where(PaymentOrder.order_code == order_code))
    if row is None:
        raise NotFoundError("Payment order not found")
    milestone_scope(db, row.milestone_id, u.id, allow_admin=True)
    from app.services.freelancer_collection_service import order_public

    return {"data": order_public(row)}


@router.get("/freelancer/contracts", response_model=ResourcePage)
def contracts(
    db: DbSession, u: CurrentUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    stmt = select(FreelanceContract)
    if u.role == UserRole.STUDENT:
        stmt = stmt.join(Student, Student.id == FreelanceContract.freelancer_student_id).where(
            Student.user_id == u.id
        )
    elif u.role != UserRole.ADMIN:
        stmt = stmt.where(FreelanceContract.client_user_id == u.id)

    def view(c):
        p, s = db.get(FreelanceProject, c.project_id), db.get(Student, c.freelancer_student_id)
        data = record(c)
        data.update(
            project_title=p.title,
            student_name=s.full_name,
            client_email=db.get(User, c.client_user_id).email,
        )
        return data

    return page(db, stmt.order_by(FreelanceContract.id.desc()), number, size, project=view)


@router.get("/milestones/{milestone_id}/activity", response_model=Resource)
def activity(milestone_id: int, db: DbSession, u: CurrentUser):
    milestone_scope(db, milestone_id, u.id, allow_admin=True)
    cancellations = db.scalars(
        select(CancellationAgreement)
        .where(CancellationAgreement.milestone_id == milestone_id)
        .order_by(CancellationAgreement.id.desc())
    ).all()
    disputes = db.scalars(
        select(Dispute).where(Dispute.milestone_id == milestone_id).order_by(Dispute.id.desc())
    ).all()
    data = []
    for d in disputes:
        v = record(d)
        w = db.scalar(select(DisputeWithdrawal).where(DisputeWithdrawal.dispute_id == d.id))
        v["withdrawal"] = record(w) if w else None
        # Parties may see only the approved/executing/executed outcome, never internal drafts.
        stmt = select(DisputeDecision).where(DisputeDecision.dispute_id == d.id)
        if u.role != UserRole.ADMIN:
            stmt = stmt.where(DisputeDecision.status.in_(("APPROVED", "EXECUTING", "EXECUTED")))
        v["decisions"] = [
            record(x) for x in db.scalars(stmt.order_by(DisputeDecision.revision_no.desc())).all()
        ]
        data.append(v)
    return {"data": {"cancellations": [record(x) for x in cancellations], "disputes": data}}


@router.get("/admin/mou-agreements", response_model=ResourcePage)
def mous(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return page(db, select(MouAgreement).order_by(MouAgreement.id.desc()), number, size)


@router.get("/admin/freelance-expansions", response_model=ResourcePage)
def expansions(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    return page(db, select(ProjectExpansion).order_by(ProjectExpansion.id.desc()), number, size)


@router.get("/admin/finance/journals", response_model=ResourcePage)
def journals(
    db: DbSession, u: AdminUser, number: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)
):
    def view(j):
        data = record(j)
        postings = db.scalars(
                select(LedgerPosting)
                .where(LedgerPosting.journal_id == j.id)
                .order_by(LedgerPosting.line_no)
            ).all()
        data["postings"] = [dict(
            record(p),
            account_code=db.get(LedgerAccount, p.account_id).code,
            account_kind=str(db.get(LedgerAccount, p.account_id).kind),
        ) for p in postings]
        debit = sum(p.amount for p in postings if str(p.side) == "D")
        credit = sum(p.amount for p in postings if str(p.side) == "C")
        data.update(total_debit=str(debit), total_credit=str(credit), is_balanced=debit == credit)

        milestone = None
        if j.reference_type == "milestones":
            milestone = db.get(Milestone, j.reference_id)
        elif j.reference_type == "payment_orders":
            order = db.get(PaymentOrder, j.reference_id)
            milestone = db.get(Milestone, order.milestone_id) if order else None
        elif j.reference_type == "payment_transactions":
            tx = db.get(PaymentTransaction, j.reference_id)
            order = db.get(PaymentOrder, tx.payment_order_id) if tx and tx.payment_order_id else None
            milestone = db.get(Milestone, order.milestone_id) if order else None
        elif j.reference_type == "settlements":
            settlement = db.get(Settlement, j.reference_id)
            milestone = db.get(Milestone, settlement.milestone_id) if settlement else None
        elif j.reference_type == "money_transfers":
            transfer = db.get(MoneyTransfer, j.reference_id)
            settlement = db.get(Settlement, transfer.settlement_id) if transfer and transfer.settlement_id else None
            milestone = db.get(Milestone, settlement.milestone_id) if settlement else None
        if milestone:
            contract = db.get(FreelanceContract, milestone.contract_id)
            project = db.get(FreelanceProject, contract.project_id) if contract else None
            student = db.get(Student, contract.freelancer_student_id) if contract else None
            company = db.get(Company, contract.company_id) if contract and contract.company_id else None
            client = db.get(User, contract.client_user_id) if contract else None
            data.update(
                milestone_id=str(milestone.id), milestone_no=milestone.sequence_no,
                contract_id=str(contract.id) if contract else None,
                project_id=str(project.id) if project else None,
                project_title=project.title if project else None,
                student_name=student.full_name if student else None,
                client_name=company.name if company else client.email if client else None,
            )
        return data

    return page(
        db, select(LedgerJournal).order_by(LedgerJournal.id.desc()), number, size, project=view
    )
