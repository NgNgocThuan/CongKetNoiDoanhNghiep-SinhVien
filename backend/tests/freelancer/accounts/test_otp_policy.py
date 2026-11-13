import unittest
from datetime import datetime, timedelta, timezone

from app.services.freelancer_accounts import otp_policy as otp

SECRET = b"unit-test-secret"
PURPOSE = "client.register"
SUBJECT = "user:42"
T0 = datetime(2026, 11, 4, 8, 0, 0, tzinfo=timezone.utc)
CFG = otp.OtpConfig()


def issue(now=T0):
    return otp.issue_challenge(CFG, SECRET, PURPOSE, SUBJECT, now)


def verify(challenge, code, now):
    return otp.verify_challenge(CFG, SECRET, PURPOSE, SUBJECT, challenge, code, now)


class GenerateAndHash(unittest.TestCase):
    def test_code_format_keeps_leading_zeros(self):
        for _ in range(200):
            code = otp.generate_code(6)
            self.assertEqual(len(code), 6)
            self.assertTrue(code.isdigit())

    def test_hash_bound_to_purpose_and_subject(self):
        base = otp.hash_code(SECRET, PURPOSE, SUBJECT, "123456")
        self.assertNotEqual(base, otp.hash_code(SECRET, "other", SUBJECT, "123456"))
        self.assertNotEqual(base, otp.hash_code(SECRET, PURPOSE, "user:43", "123456"))
        self.assertNotEqual(base, otp.hash_code(b"other-secret", PURPOSE, SUBJECT, "123456"))

    def test_empty_secret_rejected(self):
        with self.assertRaises(ValueError):
            otp.hash_code(b"", PURPOSE, SUBJECT, "123456")

    def test_challenge_does_not_store_plain_code(self):
        code, ch = issue()
        self.assertNotIn(code, ch.code_hash)
        self.assertEqual(ch.expires_at, T0 + CFG.ttl)


class SendLimits(unittest.TestCase):
    def test_first_send_allowed(self):
        self.assertTrue(otp.check_send_allowed(CFG, T0, []).allowed)

    def test_cooldown_blocks_and_reports_retry(self):
        d = otp.check_send_allowed(CFG, T0 + timedelta(seconds=20), [T0])
        self.assertEqual(d.outcome, otp.SendOutcome.COOLDOWN)
        self.assertEqual(d.retry_after_seconds, 40)

    def test_after_cooldown_allowed(self):
        d = otp.check_send_allowed(CFG, T0 + timedelta(seconds=61), [T0])
        self.assertTrue(d.allowed)

    def test_window_rate_limit(self):
        sends = [T0 + timedelta(minutes=5 * i) for i in range(5)]  # 5 lần trong 20 phút
        now = T0 + timedelta(minutes=30)
        d = otp.check_send_allowed(CFG, now, sends)
        self.assertEqual(d.outcome, otp.SendOutcome.RATE_LIMITED)
        # lần cũ nhất (T0) rời cửa sổ 1h tại T0+60'
        self.assertEqual(d.retry_after_seconds, 30 * 60)

    def test_old_sends_outside_window_do_not_count(self):
        sends = [T0 - timedelta(hours=2, minutes=i) for i in range(10)]
        self.assertTrue(otp.check_send_allowed(CFG, T0, sends).allowed)

    def test_naive_datetimes_treated_as_utc(self):
        naive_last = T0.replace(tzinfo=None)
        d = otp.check_send_allowed(CFG, T0 + timedelta(seconds=10), [naive_last])
        self.assertEqual(d.outcome, otp.SendOutcome.COOLDOWN)


class Verify(unittest.TestCase):
    def test_correct_code_ok_and_consumed(self):
        code, ch = issue()
        r = verify(ch, code, T0 + timedelta(minutes=1))
        self.assertTrue(r.ok)
        self.assertIsNotNone(r.challenge.consumed_at)

    def test_cannot_reuse_after_success(self):
        code, ch = issue()
        r = verify(ch, code, T0 + timedelta(minutes=1))
        again = verify(r.challenge, code, T0 + timedelta(minutes=2))
        self.assertEqual(again.outcome, otp.VerifyOutcome.ALREADY_USED)

    def test_expired(self):
        code, ch = issue()
        r = verify(ch, code, T0 + CFG.ttl)  # đúng thời điểm hết hạn là hết hạn
        self.assertEqual(r.outcome, otp.VerifyOutcome.EXPIRED)

    def test_wrong_code_counts_attempts(self):
        code, ch = issue()
        wrong = "000000" if code != "000000" else "111111"
        r = verify(ch, wrong, T0 + timedelta(seconds=5))
        self.assertEqual(r.outcome, otp.VerifyOutcome.INVALID)
        self.assertEqual(r.challenge.attempts, 1)
        self.assertEqual(r.attempts_left, CFG.max_attempts - 1)

    def test_lockout_even_with_correct_code(self):
        code, ch = issue()
        wrong = "000000" if code != "000000" else "111111"
        now = T0 + timedelta(seconds=5)
        for _ in range(CFG.max_attempts):
            r = verify(ch, wrong, now)
            ch = r.challenge
        self.assertEqual(r.outcome, otp.VerifyOutcome.TOO_MANY_ATTEMPTS)
        after = verify(ch, code, now)
        self.assertEqual(after.outcome, otp.VerifyOutcome.TOO_MANY_ATTEMPTS)

    def test_bad_format_counts_as_attempt_and_never_matches(self):
        code, ch = issue()
        for bad in ["", "12345", "1234567", "abcdef", "１２３４５６", " "]:
            r = verify(ch, bad, T0 + timedelta(seconds=1))
            self.assertEqual(r.outcome, otp.VerifyOutcome.INVALID, bad)
            self.assertEqual(r.challenge.attempts, 1)

    def test_whitespace_around_code_tolerated(self):
        code, ch = issue()
        self.assertTrue(verify(ch, f" {code}\n", T0 + timedelta(seconds=1)).ok)

    def test_code_for_other_subject_rejected(self):
        code, ch = issue()
        r = otp.verify_challenge(
            CFG, SECRET, PURPOSE, "user:43", ch, code, T0 + timedelta(seconds=1)
        )
        self.assertEqual(r.outcome, otp.VerifyOutcome.INVALID)


class Config(unittest.TestCase):
    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            otp.OtpConfig(length=3)
        with self.assertRaises(ValueError):
            otp.OtpConfig(max_attempts=0)
        with self.assertRaises(ValueError):
            otp.OtpConfig(ttl=timedelta(0))


if __name__ == "__main__":
    unittest.main()
