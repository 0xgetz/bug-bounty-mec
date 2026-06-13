"""Bug #5 — HIGH | x/wstaking | WithdrawFromRegion
Issue: https://github.com/openmetaearth/me-hub/issues/1244

No solvency check: GlobalDAO can drain treasury below DelegateInterest
obligations. Delegators earn rewards but can never claim them.

Vulnerable pattern (msg_server_region.go:77-78):
    err = k.bankKeeper.Extend().SendCoinsWithTag(
        ctx, fromAddr, toAddr, msg.Amount, ...)  // any amount allowed

Fix: validate msg.Amount <= treasuryBalance - DelegateInterest.
"""

import pytest
from tests.sdk_helpers import Int, Dec


class Treasury:
    def __init__(self, balance: int, delegate_interest: int, fixed_deposit: int):
        self.balance = Int(balance)
        self.delegate_interest = Dec(str(delegate_interest))
        self.fixed_deposit_amount = Int(fixed_deposit)

    def available_buggy(self) -> Int:
        """Buggy: no solvency check — full balance is withdrawable."""
        return self.balance

    def available_fixed(self) -> Int:
        """Fixed: reserves DelegateInterest + FixedDepositAmount."""
        committed = self.delegate_interest.truncate_int()
        total_reserved = committed.add(self.fixed_deposit_amount)
        avail = self.balance.sub(total_reserved)
        if avail._v < 0:
            return Int(0)
        return avail


def withdraw_buggy(treasury: Treasury, amount: int) -> tuple[bool, int]:
    """Buggy: allows any withdrawal amount."""
    avail = treasury.available_buggy()
    if Int(amount).gt(avail):
        return False, treasury.balance._v
    treasury.balance = treasury.balance.sub(Int(amount))
    return True, treasury.balance._v


def withdraw_fixed(treasury: Treasury, amount: int) -> tuple[bool, int]:
    """Fixed: blocks withdrawal that would breach solvency."""
    avail = treasury.available_fixed()
    if Int(amount).gt(avail):
        return False, treasury.balance._v
    treasury.balance = treasury.balance.sub(Int(amount))
    return True, treasury.balance._v


class TestBug05NoSolvencyCheck:

    def test_normal_withdrawal_both_succeed(self):
        """Small withdrawal within available balance succeeds."""
        t = Treasury(balance=10000, delegate_interest=2000, fixed_deposit=1000)
        ok, _ = withdraw_fixed(t, 5000)
        assert ok is True

    def test_buggy_allows_drain_below_obligations(self):
        """Buggy: GlobalDAO can drain entire treasury."""
        t = Treasury(balance=10000, delegate_interest=5000, fixed_deposit=3000)

        ok, remaining = withdraw_buggy(t, 10000)
        assert ok is True
        assert remaining == 0  # Treasury drained!
        # But DelegateInterest=5000 + FixedDeposit=3000 still owed

    def test_fixed_blocks_drain(self):
        """Fixed: withdrawal blocked when it would breach reserves."""
        t = Treasury(balance=10000, delegate_interest=5000, fixed_deposit=3000)

        # Available = 10000 - 5000 - 3000 = 2000
        ok, remaining = withdraw_fixed(t, 3000)
        assert ok is False
        assert remaining == 10000  # Nothing withdrawn

    def test_fixed_allows_up_to_available(self):
        """Fixed: can withdraw exactly the available amount."""
        t = Treasury(balance=10000, delegate_interest=5000, fixed_deposit=3000)

        ok, remaining = withdraw_fixed(t, 2000)
        assert ok is True
        assert remaining == 8000

    def test_delegators_cannot_claim_after_drain(self):
        """Demonstrates the consequence: delegators' rewards are unbacked."""
        t = Treasury(balance=10000, delegate_interest=5000, fixed_deposit=0)

        # GlobalDAO drains everything
        withdraw_buggy(t, 10000)

        # Delegator tries to claim 500 — treasury is empty
        assert t.balance._v == 0
        # Cannot pay the 5000 in DelegateInterest obligations

    def test_partial_drain_still_dangerous(self):
        """Even partial drain below DI threshold is problematic."""
        t = Treasury(balance=10000, delegate_interest=8000, fixed_deposit=0)

        # Withdraw 5000 — leaves 5000 but 8000 is owed
        ok, remaining = withdraw_buggy(t, 5000)
        assert ok is True
        assert remaining == 5000  # Under-collateralised by 3000

        t2 = Treasury(balance=10000, delegate_interest=8000, fixed_deposit=0)
        ok2, remaining2 = withdraw_fixed(t2, 5000)
        assert ok2 is False  # Available = 10000 - 8000 = 2000 < 5000
