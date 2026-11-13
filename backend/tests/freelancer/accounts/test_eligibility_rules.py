import unittest

from app.services.freelancer_accounts import eligibility_rules as er


def facts(**kw):
    base = dict(
        user_id=1,
        user_active=True,
        email_verified=True,
        company_id=10,
        company_verified=True,
        company_suspended=False,
        mou_active=False,
    )
    base.update(kw)
    return er.ClientFacts(**base)


class Eligibility(unittest.TestCase):
    def test_verified_company_can_do_everything(self):
        d = er.evaluate_client_eligibility(facts())
        self.assertEqual(
            (d.tier, d.can_draft, d.can_submit, d.can_fund), ("VERIFIED", True, True, True)
        )
        self.assertEqual(d.reason_codes, ())

    def test_mou_active_upgrades_tier_only(self):
        d = er.evaluate_client_eligibility(facts(mou_active=True))
        self.assertEqual(d.tier, "OFFICIAL_PARTNER")
        self.assertTrue(d.can_fund)

    def test_mou_expired_falls_back_to_verified_and_keeps_rights(self):
        d = er.evaluate_client_eligibility(facts(mou_active=False))
        self.assertEqual(d.tier, "VERIFIED")
        self.assertTrue(d.can_submit)

    def test_pending_company_can_draft_but_not_submit(self):
        d = er.evaluate_client_eligibility(facts(company_verified=False))
        self.assertTrue(d.can_draft)
        self.assertFalse(d.can_submit)
        self.assertFalse(d.can_fund)
        self.assertEqual(d.tier, "UNVERIFIED")
        self.assertIn(er.R_COMPANY_NOT_VERIFIED, d.reason_codes)

    def test_company_requires_both_legal_verification_and_current_email(self):
        d = er.evaluate_client_eligibility(facts(email_verified=False))
        self.assertFalse(d.can_submit)
        self.assertFalse(d.can_fund)
        self.assertIn("EMAIL_NOT_VERIFIED", d.reason_codes)

    def test_individual_client_can_draft_submit_and_fund_with_email_only(self):
        d = er.evaluate_client_eligibility(
            facts(role="CLIENT", company_id=None)
        )
        self.assertTrue(d.can_draft)
        self.assertTrue(d.can_submit)
        self.assertTrue(d.can_fund)

    def test_suspended_company_blocked_even_if_verified_and_mou(self):
        d = er.evaluate_client_eligibility(facts(company_suspended=True, mou_active=True))
        self.assertFalse(d.can_draft)
        self.assertFalse(d.can_submit)
        self.assertFalse(d.can_fund)
        self.assertEqual(d.tier, "UNVERIFIED")
        self.assertIn(er.R_COMPANY_SUSPENDED, d.reason_codes)

    def test_inactive_user(self):
        d = er.evaluate_client_eligibility(facts(user_active=False))
        self.assertFalse(d.can_draft)
        self.assertIn(er.R_USER_INACTIVE, d.reason_codes)

    def test_no_company(self):
        d = er.evaluate_client_eligibility(
            facts(role="CLIENT", company_id=None, company_verified=False)
        )
        self.assertTrue(d.can_draft)
        self.assertTrue(d.can_submit)
        self.assertEqual(d.tier, "CONTACT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
