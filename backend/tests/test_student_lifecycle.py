from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from app.core.exceptions import BadRequestError, ForbiddenError
from app.models import EmailLog, Student, User
from app.models.student import RetiredStudent
from app.services.student_lifecycle import (
    anniversary,
    code_hash,
    process_graduates,
    require_new_activity,
    reset_lifecycle,
    validate_academic,
)
from tests.test_admin_students import _make_student, _school


def test_calendar_anniversary_and_validation():
    assert anniversary(date(2024, 2, 29)) == date(2025, 2, 28)
    with pytest.raises(BadRequestError):
        validate_academic('GRADUATED', None)
    with pytest.raises(BadRequestError):
        validate_academic('GRADUATED', date.today() + timedelta(days=1))


def test_current_students_never_expire(db, make_user):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    assert process_graduates(db) == 0
    assert db.get(Student, student.id) is not None


def test_welcome_reminders_and_expiry(db, make_user):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    student.academic_status = 'GRADUATED'
    student.graduated_at = date(2025, 6, 30)
    db.commit()
    process_graduates(db, today=date(2025, 6, 30))
    assert student.account_expires_on == date(2026, 6, 30)
    assert db.scalar(select(func.count()).select_from(EmailLog)) == 1
    reset_lifecycle(student, {'academic_status': 'GRADUATED', 'graduated_at': date(2025, 6, 30)})
    process_graduates(db, today=date(2025, 7, 1))
    assert db.scalar(select(func.count()).select_from(EmailLog)) == 1
    process_graduates(db, today=date(2026, 6, 1))
    assert student.lifecycle_stage == 'REMINDER30'
    process_graduates(db, today=date(2026, 6, 23))
    assert student.lifecycle_stage == 'REMINDER7'
    ident, user_id = student.id, student.user_id
    process_graduates(db, today=date(2026, 6, 30))
    assert db.get(Student, ident) is None
    assert db.get(User, user_id) is None
    assert db.get(RetiredStudent, code_hash('SV001')) is not None


def test_late_import_gets_notice_period(db, make_user):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    student.academic_status = 'GRADUATED'
    student.graduated_at = date(2020, 1, 1)
    db.commit()
    process_graduates(db, today=date(2026, 11, 13))
    assert student.account_expires_on == date(2026, 12, 13)


def test_obligations_defer_deletion(db, make_user, monkeypatch):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    student.academic_status = 'GRADUATED'
    student.graduated_at = date(2020, 1, 1)
    student.account_expires_on = date(2021, 1, 1)
    student.lifecycle_stage = 'REMINDER7'
    db.commit()
    monkeypatch.setattr('app.services.student_lifecycle.has_obligations', lambda *args: True)
    process_graduates(db)
    assert student.lifecycle_stage == 'DEFERRED'
    assert str(student.user.status) == 'ACTIVE'


def test_history_retained_without_cascade(db, make_user, monkeypatch):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    student.academic_status = 'GRADUATED'
    student.graduated_at = date(2020, 1, 1)
    student.account_expires_on = date(2021, 1, 1)
    student.lifecycle_stage = 'REMINDER7'
    db.commit()
    monkeypatch.setattr('app.services.student_lifecycle.has_history', lambda *args: True)
    process_graduates(db)
    assert db.get(Student, student.id) is not None
    assert student.lifecycle_stage == 'RETAINED'
    assert str(student.user.status) == 'LOCKED'


def test_expired_graduate_cannot_start_new_work():
    student = Student(academic_status='GRADUATED', account_expires_on=date.today())
    with pytest.raises(ForbiddenError):
        require_new_activity(student)
    student.academic_status = 'STUDYING'
    require_new_activity(student)


def test_withdrawal_validation_and_immediate_restriction():
    with pytest.raises(BadRequestError):
        validate_academic('WITHDRAWN', None)
    with pytest.raises(BadRequestError):
        validate_academic('WITHDRAWN', None, date.today() + timedelta(days=1))
    validate_academic('WITHDRAWN', None, date.today())
    with pytest.raises(ForbiddenError):
        require_new_activity(Student(academic_status='WITHDRAWN'))
    require_new_activity(Student(academic_status='SUSPENDED'))


def test_withdrawal_notice_reminder_and_delete(db, make_user):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    student.academic_status = 'WITHDRAWN'
    student.withdrawn_at = date(2025, 1, 1)
    student.profile.is_open_to_work = True
    db.commit()
    process_graduates(db, today=date(2025, 1, 1))
    assert student.account_expires_on == date(2025, 1, 31)
    assert not student.profile.is_open_to_work
    mails = list(db.scalars(select(EmailLog)))
    assert len(mails) == 1
    assert mails[0].ref_type == 'WITHDRAWAL'
    assert 'Chúc mừng' not in mails[0].subject
    reset_lifecycle(student, {'academic_status': 'WITHDRAWN', 'withdrawn_at': date(2025, 1, 1)})
    process_graduates(db, today=date(2025, 1, 2))
    assert db.scalar(select(func.count()).select_from(EmailLog)) == 1
    process_graduates(db, today=date(2025, 1, 24))
    assert student.lifecycle_stage == 'REMINDER7'
    ident = student.id
    process_graduates(db, today=date(2025, 1, 31))
    assert db.get(Student, ident) is None


def test_withdrawal_late_import_and_pending_obligation(db, make_user, monkeypatch):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    student.academic_status = 'WITHDRAWN'
    student.withdrawn_at = date(2020, 1, 1)
    db.commit()
    process_graduates(db, today=date(2026, 1, 1))
    assert student.account_expires_on == date(2026, 1, 31)
    monkeypatch.setattr('app.services.student_lifecycle.has_obligations', lambda *args: True)
    process_graduates(db, today=date(2026, 1, 31))
    assert student.lifecycle_stage == 'DEFERRED'
    assert str(student.user.status) == 'ACTIVE'


def test_suspension_is_not_a_retention_trigger(db, make_user):
    faculty, major = _school(db)
    student = _make_student(db, make_user, faculty, major)
    student.academic_status = 'SUSPENDED'
    db.commit()
    assert process_graduates(db) == 0
    assert student.account_expires_on is None
