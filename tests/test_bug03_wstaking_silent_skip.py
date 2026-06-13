"""Bug #3 — MEDIUM | x/wstaking | sendKycRewards
Issue: https://github.com/openmetaearth/me-hub/issues/1242

When DelegateInterest < interest payment, the deduction is silently
skipped — user receives payment but DelegateInterest is NOT decremented.
This overstates treasury balance and authorises future payouts incorrectly.

Vulnerable pattern (kyc_reward.go:120-124):
    if experienceRegion.DelegateInterest.GTE(interest) {
        experienceRegion.DelegateInterest =
            experienceRegion.DelegateInterest.Sub(interest)
    }  // if false: payment done but DelegateInterest NOT decremented!

Fix: add else { return error } branch.
"""

import pytest
from tests.sdk_helpers import Dec


# -- Buggy vs fixed ---------------------------------------------------------

def send_kyc_rewards_buggy(
    delegate_interest: Dec,
    interest: Dec,
) -> tuple[Dec, bool]:
    """Buggy: silently skips deduction when insufficient.
    Returns (updated delegate_interest, payment_sent).
    """
    payment_sent = False
    if interest.gt(Dec("0")):
        # Payment is always sent
        payment_sent = True
        # But deduction only happens if GTE
        if delegate_interest.gte(interest):
            delegate_interest = Dec(str(delegate_interest._v - interest._v))
        # else: SILENT SKIP — no error, no deduction
    return delegate_interest, payment_sent


def send_kyc_rewards_fixed(
    delegate_interest: Dec,
    interest: Dec,
) -> tuple[Dec, bool, str | None]:
    """Fixed: returns error when DelegateInterest insufficient.
    Returns (updated delegate_interest, payment_sent, error).
    """
    if interest.gt(Dec("0")):
        if delegate_interest.gte(interest):
            new_di = Dec(str(delegate_interest._v - interest._v))
            return new_di, True, None
        else:
            return delegate_interest, False, (
                f"DelegateInterest insufficient: "
                f"need {interest} have {delegate_interest}"
            )
    return delegate_interest, False, None


# -- Tests -----------------------------------------------------------------

class TestBug03SilentDelegateInterestSkip:

    def test_sufficient_interest_deducted(self):
        """When DelegateInterest >= interest, deduction works normally."""
        di = Dec("1000")
        interest = Dec("500")

        new_di, sent = send_kyc_rewards_buggy(di, interest)
        assert sent is True
        assert new_di == Dec("500")

    def test_insufficient_interest_silent_skip_buggy(self):
        """Buggy: payment sent but DelegateInterest unchanged."""
        di = Dec("100")
        interest = Dec("500")

        new_di, sent = send_kyc_rewards_buggy(di, interest)
        assert sent is True  # Payment went through!
        assert new_di == Dec("100")  # But DI was NOT decremented

    def test_insufficient_interest_returns_error_fixed(self):
        """Fixed: returns error, blocks payment."""
        di = Dec("100")
        interest = Dec("500")

        new_di, sent, err = send_kyc_rewards_fixed(di, interest)
        assert sent is False
        assert err is not None
        assert "insufficient" in err
        assert new_di == Dec("100")  # DI preserved correctly

    def test_treasury_divergence_accumulates(self):
        """Repeated silent skips cause DelegateInterest to diverge
        further and further from actual treasury balance."""
        di = Dec("50")
        total_paid = 0

        for _ in range(10):
            interest = Dec("100")
            new_di, sent = send_kyc_rewards_buggy(di, interest)
            if sent:
                total_paid += 100
            di = new_di

        # Buggy: paid 1000 but DelegateInterest still shows 50
        assert total_paid == 1000
        assert di == Dec("50")  # Never decremented!

    def test_zero_interest_no_action(self):
        """Zero interest should cause no payment and no deduction."""
        di = Dec("1000")
        interest = Dec("0")

        new_di, sent = send_kyc_rewards_buggy(di, interest)
        assert sent is False
        assert new_di == Dec("1000")
