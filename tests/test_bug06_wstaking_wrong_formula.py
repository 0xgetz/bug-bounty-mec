"""Bug #6 — MEDIUM | x/wstaking | DoFixedDeposit
Issue: https://github.com/openmetaearth/me-hub/issues/1245

Wrong solvency formula uses regionShare and initAllocationFunds —
variables NOT used in the actual interest calculation (Calculate()).
When regionShare is small, interestAmountDec ~ 0 and the solvency
check always passes, even when treasury cannot pay at maturity.

Vulnerable formula (msg_server_fixed_deposit.go:98-103):
    interestAmountDec = deAmount * regionShare * totalRewardsPerBlock
                        / totalSupply * initAllocationFunds  // WRONG

Correct formula from Calculate():
    rewards = blockRewards * (totalStaking/totalSupply) * 10^(-BaseDenomUnit)

Fix: use actual Calculate() function for interest estimation.
"""

import pytest
from tests.sdk_helpers import Dec


def solvency_check_buggy(
    deposit_amount: int,
    region_share: float,
    total_rewards_per_block: float,
    total_supply: float,
    init_allocation_funds: float,
    deposit_term_blocks: int,
    treasury_balance: int,
    current_delegate_interest: int,
) -> tuple[bool, float]:
    """Buggy: uses wrong formula with regionShare & initAllocationFunds."""
    interest_dec = (
        deposit_amount
        * region_share
        * total_rewards_per_block
        / total_supply
        * init_allocation_funds
    )
    estimated_obligation = interest_dec * deposit_term_blocks
    total_obligation = current_delegate_interest + estimated_obligation
    return total_obligation <= treasury_balance, estimated_obligation


def solvency_check_fixed(
    deposit_amount: int,
    total_staking: float,
    total_rewards_per_block: float,
    total_supply: float,
    base_denom_unit: int,
    deposit_term_blocks: int,
    treasury_balance: int,
    current_delegate_interest: int,
) -> tuple[bool, float]:
    """Fixed: uses actual Calculate() formula."""
    per_block_interest = (
        total_rewards_per_block
        * (total_staking / total_supply)
        * (10 ** (-base_denom_unit))
    )
    estimated_obligation = per_block_interest * deposit_amount * deposit_term_blocks
    total_obligation = current_delegate_interest + estimated_obligation
    return total_obligation <= treasury_balance, estimated_obligation


class TestBug06WrongSolvencyFormula:

    def test_small_region_share_bypasses_check(self):
        """When regionShare is tiny, buggy formula yields ~0 obligation."""
        ok, est = solvency_check_buggy(
            deposit_amount=1_000_000,
            region_share=1e-12,   # extremely tiny share (new region)
            total_rewards_per_block=10.0,
            total_supply=1_000_000_000.0,
            init_allocation_funds=1.0,  # small alloc funds
            deposit_term_blocks=100_000,
            treasury_balance=100,  # nearly empty treasury!
            current_delegate_interest=50,
        )
        # Buggy: estimated obligation is negligible, check passes
        assert ok is True
        assert est < 1  # Way too low

    def test_fixed_formula_rejects_insolvent(self):
        """Fixed formula correctly computes obligation and rejects."""
        ok, est = solvency_check_fixed(
            deposit_amount=1_000_000,
            total_staking=500_000_000.0,
            total_rewards_per_block=10.0,
            total_supply=1_000_000_000.0,
            base_denom_unit=6,
            deposit_term_blocks=100_000,
            treasury_balance=100,  # nearly empty
            current_delegate_interest=50,
        )
        assert ok is False

    def test_large_region_share_buggy_may_reject(self):
        """With large regionShare, even the buggy formula may reject."""
        ok, est = solvency_check_buggy(
            deposit_amount=1_000_000,
            region_share=0.5,
            total_rewards_per_block=10.0,
            total_supply=1_000_000_000.0,
            init_allocation_funds=1_000_000.0,
            deposit_term_blocks=100_000,
            treasury_balance=100,
            current_delegate_interest=50,
        )
        # With larger share the estimate grows, might reject
        # But formula is still wrong — just sometimes accidentally correct
        # The key is that for small shares it ALWAYS passes

    def test_new_regions_most_vulnerable(self):
        """New regions with small stake are most vulnerable because
        regionShare ~ 0 makes the buggy formula always pass."""
        ok, est = solvency_check_buggy(
            deposit_amount=10_000_000,
            region_share=1e-18,  # new region, essentially zero share
            total_rewards_per_block=100.0,
            total_supply=10_000_000_000.0,
            init_allocation_funds=1.0,
            deposit_term_blocks=500_000,
            treasury_balance=1,  # nearly empty treasury!
            current_delegate_interest=0,
        )
        # Treasury has almost nothing but deposit is accepted because est ~ 0
        assert est < 1e-10
        assert ok is True
