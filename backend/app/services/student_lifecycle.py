"""Graduation and withdrawal retention based on school-confirmed dates."""
import calendar
import hashlib
from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.core.enums import UserStatus
from app.core.exceptions import BadRequestError, ForbiddenError
from app.models import Dispute, FreelanceContract, Milestone, MoneyTransfer, Student, User
from app.models.base import Base
from app.models.student import RetiredStudent
from app.services.freelancer_domain import notify, notify_admins


def anniversary(value: date) -> date:
    return value.replace(year=value.year + 1, day=min(value.day, calendar.monthrange(value.year + 1, value.month)[1]))


def code_hash(code):
    return hashlib.sha256(code.strip().lower().encode()).hexdigest()


def validate_academic(status, graduated_at, withdrawn_at=None):
    if status not in ("STUDYING", "GRADUATED", "SUSPENDED", "WITHDRAWN"):
        raise BadRequestError("Trạng thái học tập không hợp lệ")
    if status == "GRADUATED" and (not graduated_at or graduated_at > date.today()):
        raise BadRequestError("Đã tốt nghiệp cần ngày tốt nghiệp hợp lệ, không ở tương lai")
    if status == "WITHDRAWN" and (not withdrawn_at or withdrawn_at > date.today()):
        raise BadRequestError("Thôi học cần ngày thôi học hợp lệ, không ở tương lai")


def reset_lifecycle(student, changes):
    if any(key in changes and changes[key] != getattr(student, key) for key in ("academic_status", "graduated_at", "withdrawn_at")):
        # Re-importing identical records must not extend expiry or repeat emails.
        student.lifecycle_stage = "NONE"
        student.lifecycle_check_on = None
        student.account_expires_on = None


def require_new_activity(student):
    if student.academic_status == "WITHDRAWN":
        raise ForbiddenError("Nhà trường đã xác nhận thôi học. Chỉ được tải dữ liệu và giải quyết nghĩa vụ còn tồn đọng.", code="STUDENT_WITHDRAWN")
    if student.academic_status == "GRADUATED" and student.account_expires_on and student.account_expires_on <= date.today():
        raise ForbiddenError("Tài khoản đã hết hạn 12 tháng sau tốt nghiệp. Chỉ được giải quyết nghĩa vụ còn tồn đọng.", code="GRADUATE_ACCOUNT_EXPIRED")


def has_obligations(db, student):
    if db.scalar(select(Dispute.id).join(Milestone, Dispute.milestone_id == Milestone.id)
                 .join(FreelanceContract, Milestone.contract_id == FreelanceContract.id).where(
                     FreelanceContract.freelancer_student_id == student.id,
                     Dispute.status.not_in(("RESOLVED", "WITHDRAWN")),
                 ).limit(1)):
        return True
    # Closed_at is set by the domain closure workflow, after settlement handling.
    if db.scalar(select(FreelanceContract.id).where(
        FreelanceContract.freelancer_student_id == student.id,
        FreelanceContract.closed_at.is_(None),
    ).limit(1)):
        return True
    return bool(db.scalar(select(MoneyTransfer.id).where(
        MoneyTransfer.recipient_user_id == student.user_id,
        MoneyTransfer.status.not_in(("SUCCEEDED", "CANCELLED")),
    ).limit(1)))


def has_history(db, student):
    # Include all RESTRICT foreign keys, even new domain tables added later.
    for table in Base.metadata.tables.values():
        for fk in table.foreign_keys:
            target = fk.target_fullname
            if target not in ("users.id", "students.id") or (fk.ondelete or "RESTRICT").upper() not in ("RESTRICT", "NO ACTION"):
                continue
            value = student.user_id if target == "users.id" else student.id
            if db.scalar(select(fk.parent).where(fk.parent == value).limit(1)) is not None:
                return True
    return False


def process_graduates(db, *, today=None, limit=50):
    today = today or date.today()
    ids = list(db.scalars(select(Student.id).where(
        Student.academic_status.in_(("GRADUATED", "WITHDRAWN")),
        Student.lifecycle_stage != "RETAINED",
        or_(Student.lifecycle_check_on.is_(None), Student.lifecycle_check_on <= today),
    ).order_by(Student.id).limit(limit)))
    for ident in ids:
        student = db.scalar(select(Student).where(Student.id == ident).with_for_update())
        if not student or student.academic_status not in ("GRADUATED", "WITHDRAWN") or student.lifecycle_stage == "RETAINED":
            db.rollback()
            continue
        if student.lifecycle_check_on and student.lifecycle_check_on > today:
            db.rollback()
            continue
        withdrawn = student.academic_status == "WITHDRAWN"
        ref_type = "WITHDRAWAL" if withdrawn else "GRADUATION"
        label = "thôi học" if withdrawn else "tốt nghiệp"
        school_date = student.withdrawn_at if withdrawn else student.graduated_at
        if not school_date:
            db.rollback()
            continue
        welcomed = student.lifecycle_stage == "NONE"
        if welcomed:
            policy_date = school_date + timedelta(days=30) if withdrawn else anniversary(school_date)
            student.account_expires_on = max(policy_date, today + timedelta(days=30))
            if withdrawn:
                if student.profile:
                    student.profile.is_open_to_work = False
                notify(db, student.user_id, "Thông báo tài khoản sau khi thôi học",
                       f"Nhà trường đã xác nhận bạn thôi học ngày {school_date:%d/%m/%Y}. "
                       f"Bạn có 30 ngày để tải CV, tài liệu và giải quyết nghĩa vụ. Hạn dọn tài khoản: {student.account_expires_on:%d/%m/%Y}. "
                       "Bạn không thể ứng tuyển hoặc nhận hợp đồng mới. Nếu còn hợp đồng, tiền hoặc tranh chấp chưa hoàn tất, hệ thống sẽ hoãn xóa.", ref_type=ref_type)
            else:
                notify(db, student.user_id, "Chúc mừng bạn đã tốt nghiệp!",
                   f"Chúc bạn thành công trên chặng đường mới. Tài khoản được hỗ trợ 12 tháng sau tốt nghiệp, "
                   f"hết hạn ngày {student.account_expires_on:%d/%m/%Y}. Hãy tải CV và tài liệu cần giữ. "
                   "Dữ liệu cá nhân sẽ được dọn sau thời hạn này nếu không còn nghĩa vụ tồn đọng. "
                   "Nếu hồ sơ được cập nhật muộn, bạn có tối thiểu 30 ngày để chuẩn bị.", ref_type=ref_type)
            student.lifecycle_stage = "REMINDER30" if withdrawn else "WELCOME"
        remaining = (student.account_expires_on - today).days
        if remaining <= 0:
            if has_obligations(db, student):
                if student.lifecycle_stage != "DEFERRED":
                    notify_admins(db, f"Hoãn dọn tài khoản {label}",
                                  f"Sinh viên #{ident} còn hợp đồng hoặc khoản chi chưa hoàn tất.", ref_type=ref_type)
                student.lifecycle_stage = "DEFERRED"
            else:
                user_id = student.user_id
                # RESTRICT references retain history. A savepoint rolls back ALL
                # cascades if deletion cannot safely complete.
                try:
                    with db.begin_nested():
                        if has_history(db, student):
                            raise IntegrityError("retained history", {}, Exception("history"))
                        db.merge(RetiredStudent(code_hash=code_hash(student.student_code), retired_on=today))
                        db.delete(student)
                        db.flush()
                        db.delete(db.get(User, user_id))
                        db.flush()
                except IntegrityError:
                    student = db.get(Student, ident)
                    student.user.status = UserStatus.LOCKED
                    student.user.locked_reason = f"Hết hạn tài khoản sau {label}; giữ hồ sơ tham chiếu lịch sử."
                    student.user.password_hash = None
                    if student.profile:
                        student.profile.is_open_to_work = False
                    student.lifecycle_stage = "RETAINED"
                    notify_admins(db, f"Tài khoản {label} hết hạn, có lịch sử cần giữ",
                                  f"Sinh viên #{ident}: đã khóa đăng nhập; không xóa dây chuyền dữ liệu lịch sử.", ref_type=ref_type)
                else:
                    db.commit()
                    continue
        elif remaining <= 7 and student.lifecycle_stage != "REMINDER7":
            notify(db, student.user_id, "Tài khoản sắp hết hạn",
                   f"Tài khoản hết hạn ngày {student.account_expires_on:%d/%m/%Y}. Hãy tải CV và tài liệu cần giữ.", ref_type=ref_type)
            student.lifecycle_stage = "REMINDER7"
        elif remaining <= 30 and student.lifecycle_stage == "WELCOME" and not welcomed:
            notify(db, student.user_id, f"Nhắc hạn tài khoản sau {label}",
                   f"Tài khoản hết hạn ngày {student.account_expires_on:%d/%m/%Y}. Vui lòng lưu lại dữ liệu cần thiết.", ref_type=ref_type)
            student.lifecycle_stage = "REMINDER30"
        student.lifecycle_check_on = today + timedelta(days=1)
        db.commit()
    return len(ids)
