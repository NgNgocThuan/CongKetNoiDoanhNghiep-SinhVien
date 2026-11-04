import unittest
from datetime import datetime, timedelta, timezone

from app.services.freelancer_accounts import mou_rules as m

NOW = datetime(2026, 11, 4, tzinfo=timezone.utc)


def snap(approved=True, start_days=-10, end_days=100):
    return m.MouSnapshot(approved, NOW + timedelta(days=start_days), NOW + timedelta(days=end_days))


class Evaluate(unittest.TestCase):
    def test_active(self):
        e = m.evaluate_mou(snap(), NOW)
        self.assertTrue(e.is_active)
        self.assertEqual(e.phase, m.MouPhase.ACTIVE)
        self.assertEqual(e.seconds_remaining, 100 * 86400)

    def test_not_approved_never_active(self):
        self.assertEqual(m.evaluate_mou(snap(approved=False), NOW).phase, m.MouPhase.NOT_APPROVED)

    def test_not_started(self):
        self.assertEqual(m.evaluate_mou(snap(start_days=1), NOW).phase, m.MouPhase.NOT_STARTED)

    def test_boundaries(self):
        s = snap(start_days=0, end_days=5)
        self.assertTrue(m.evaluate_mou(s, NOW).is_active)  # đúng ngày bắt đầu: hiệu lực
        self.assertEqual(m.evaluate_mou(s, NOW + timedelta(days=5)).phase, m.MouPhase.EXPIRED)

    def test_naive_inputs(self):
        s = m.MouSnapshot(True, (NOW - timedelta(days=1)).replace(tzinfo=None), (NOW + timedelta(days=1)).replace(tzinfo=None))
        self.assertTrue(m.evaluate_mou(s, NOW).is_active)


class Period(unittest.TestCase):
    def check(self, start, end, code, **kw):
        with self.assertRaises(m.MouValidationError) as ctx:
            m.validate_mou_period(NOW + timedelta(days=start), NOW + timedelta(days=end), NOW, **kw)
        self.assertEqual(ctx.exception.code, code)

    def test_valid(self):
        m.validate_mou_period(NOW, NOW + timedelta(days=365), NOW)

    def test_end_before_start(self):
        self.check(10, 5, "MOU_PERIOD_INVALID")

    def test_already_expired(self):
        self.check(-30, -1, "MOU_ALREADY_EXPIRED")

    def test_backdated(self):
        self.check(-3, 100, "MOU_BACKDATED")

    def test_backdate_allowance(self):
        m.validate_mou_period(NOW - timedelta(days=3), NOW + timedelta(days=100), NOW, allow_backdate_days=7)

    def test_too_long(self):
        self.check(0, 365 * 6, "MOU_TERM_TOO_LONG")


class Reminders(unittest.TestCase):
    def test_none_when_far(self):
        self.assertIsNone(m.next_reminder_threshold(snap(end_days=100), NOW, set()))

    def test_30_day_mark(self):
        self.assertEqual(m.next_reminder_threshold(snap(end_days=29), NOW, set()), 30)

    def test_not_sent_twice(self):
        self.assertIsNone(m.next_reminder_threshold(snap(end_days=29), NOW, {30}))

    def test_late_job_sends_only_closest_mark(self):
        self.assertEqual(m.next_reminder_threshold(snap(end_days=5), NOW, set()), 7)

    def test_next_mark_after_previous_sent(self):
        self.assertEqual(m.next_reminder_threshold(snap(end_days=10), NOW, {30}), 14)

    def test_no_reminder_when_expired_or_unapproved(self):
        self.assertIsNone(m.next_reminder_threshold(snap(end_days=-1, start_days=-50), NOW, set()))
        self.assertIsNone(m.next_reminder_threshold(snap(approved=False, end_days=3), NOW, set()))


if __name__ == "__main__":
    unittest.main()
