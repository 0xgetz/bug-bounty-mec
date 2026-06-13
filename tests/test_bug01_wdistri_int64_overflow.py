"""Bug #1 — CRITICAL | x/wdistri | AllocateBlockReward
Issue: https://github.com/openmetaearth/me-hub/issues/1240

sdkmath.Int.Int64() panics when regionAmount > MaxInt64.
regionAmount = (regionShare / totalShare) * dailyFees and grows with
fee accumulation.  The EndBlocker calls AllocateBlockRewardEveryDay,
so any overflow causes a **permanent chain halt**.

Vulnerable pattern (keeper.go:96-97):
    regionCoins := sdk.NewCoins(sdk.NewCoin(params.BaseDenom,
        sdk.NewInt(regionAmount.Int64())))   // <-- Int64() PANICS

Fix: pass sdkmath.Int directly — sdk.NewCoin accepts it natively.
"""

import pytest
from tests.sdk_helpers import Dec, Int, MAX_INT64


# -- Reproduction of the vulnerable logic ----------------------------------

def allocate_block_reward_buggy(
    region_share: Dec,
    total_share: Dec,
    daily_fees: Int,
) -> Int:
    """Buggy: converts via .Int64() which panics on overflow."""
    amount_dec = Dec(str(daily_fees._v)).mul(region_share).quo(total_share)
    region_amount = amount_dec.truncate_int()
    # This is the vulnerable call:
    region_amount.int64()
    return region_amount


def allocate_block_reward_fixed(
    region_share: Dec,
    total_share: Dec,
    daily_fees: Int,
) -> Int:
    """Fixed: uses sdkmath.Int directly, no int64 cast."""
    amount_dec = Dec(str(daily_fees._v)).mul(region_share).quo(total_share)
    return amount_dec.truncate_int()


# -- Tests -----------------------------------------------------------------

class TestBug01Int64Overflow:
    """Validate that Int64() overflow causes panic in AllocateBlockReward."""

    def test_small_amount_succeeds(self):
        """Normal fee amounts work fine with both implementations."""
        share = Dec("1")
        total = Dec("10")
        fees = Int(1_000_000_000)  # 1e9 — well within int64

        result_buggy = allocate_block_reward_buggy(share, total, fees)
        result_fixed = allocate_block_reward_fixed(share, total, fees)
        assert result_buggy == result_fixed

    def test_max_int64_boundary(self):
        """Value exactly at MaxInt64 should not panic."""
        share = Dec("1")
        total = Dec("1")
        fees = Int(MAX_INT64)

        result = allocate_block_reward_buggy(share, total, fees)
        assert result == Int(MAX_INT64)

    def test_overflow_panics_buggy(self):
        """When regionAmount > MaxInt64, the buggy code panics."""
        share = Dec("1")
        total = Dec("1")
        fees = Int(MAX_INT64 + 1)

        with pytest.raises(OverflowError, match="Int64\\(\\) out of bound"):
            allocate_block_reward_buggy(share, total, fees)

    def test_overflow_succeeds_fixed(self):
        """The fixed version handles amounts > MaxInt64 without panic."""
        share = Dec("1")
        total = Dec("1")
        fees = Int(MAX_INT64 + 1)

        result = allocate_block_reward_fixed(share, total, fees)
        assert result == Int(MAX_INT64 + 1)

    def test_large_fee_accumulation_triggers_overflow(self):
        """Simulates fee accumulation over time crossing the threshold.
        Trigger: FeeCollector balance * regionShare/totalShare > 9.22e18 umec
        """
        share = Dec("500")
        total = Dec("1000")
        # 2e19 umec in FeeCollector — plausible after long accumulation
        fees = Int(20_000_000_000_000_000_000)

        # regionAmount = 0.5 * 2e19 = 1e19 > MaxInt64 (9.22e18)
        with pytest.raises(OverflowError):
            allocate_block_reward_buggy(share, total, fees)

        result = allocate_block_reward_fixed(share, total, fees)
        assert result == Int(10_000_000_000_000_000_000)

    def test_multiple_regions_one_overflows(self):
        """Only the region whose share pushes past MaxInt64 panics."""
        total = Dec("100")
        fees = Int(10 ** 19)

        # Region A: 5% share → 5e17 — safe
        assert allocate_block_reward_buggy(Dec("5"), total, fees) == Int(5 * 10**17)

        # Region B: 95% share → 9.5e18 — overflow
        with pytest.raises(OverflowError):
            allocate_block_reward_buggy(Dec("95"), total, fees)
