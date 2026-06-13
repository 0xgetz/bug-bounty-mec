"""Bug #4 — HIGH | x/wstaking | getRewardsByHeight
Issue: https://github.com/openmetaearth/me-hub/issues/1243

Off-by-one errors at halving boundaries inflate delegation interest.

Bug A (start period, line 47-48):
    blockCount = N*(lowMul+1) - fromHeight + 1  // +1 overcounts
    Should be: N*(lowMul+1) - fromHeight          (no +1)

Bug B (end period, line 52-53):
    blockCount = toHeight - N*i - 1               // -1 undercounts
    Should be: toHeight - N*i                      (no -1)

Net: 1 block reward calculated at wrong rate per halving boundary.
Proof: fromH=50, toH=150, N=100 -> Code=75.5R, Expected=75R (+0.5R each)
"""

import pytest


ONE_YEAR_TOTAL_BLOCKS = 100  # simplified


def get_rewards_by_height_buggy(
    from_height: int,
    to_height: int,
    n: int,
    rates: list[float],
) -> float:
    """Buggy implementation with off-by-one errors."""
    low_mul = from_height // n
    high_mul = to_height // n
    total = 0.0

    for i in range(low_mul, high_mul + 1):
        if i == low_mul and i == high_mul:
            block_count = to_height - from_height
            total += block_count * rates[min(i, len(rates) - 1)]
        elif i == low_mul:
            # BUG A: +1 overcounts start period
            block_count = n * (low_mul + 1) - from_height + 1
            total += block_count * rates[min(i, len(rates) - 1)]
        elif i == high_mul:
            # BUG B: -1 undercounts end period
            block_count = to_height - n * i - 1
            total += block_count * rates[min(i, len(rates) - 1)]
        else:
            total += n * rates[min(i, len(rates) - 1)]

    return total


def get_rewards_by_height_fixed(
    from_height: int,
    to_height: int,
    n: int,
    rates: list[float],
) -> float:
    """Fixed: correct block count at boundaries."""
    low_mul = from_height // n
    high_mul = to_height // n
    total = 0.0

    for i in range(low_mul, high_mul + 1):
        if i == low_mul and i == high_mul:
            block_count = to_height - from_height
            total += block_count * rates[min(i, len(rates) - 1)]
        elif i == low_mul:
            # FIXED: no +1
            block_count = n * (low_mul + 1) - from_height
            total += block_count * rates[min(i, len(rates) - 1)]
        elif i == high_mul:
            # FIXED: no -1
            block_count = to_height - n * i
            total += block_count * rates[min(i, len(rates) - 1)]
        else:
            total += n * rates[min(i, len(rates) - 1)]

    return total


class TestBug04OffByOne:

    def test_within_single_period_no_bug(self):
        """No boundary crossing — both implementations agree."""
        rates = [1.0, 0.5, 0.25]
        result_b = get_rewards_by_height_buggy(10, 90, 100, rates)
        result_f = get_rewards_by_height_fixed(10, 90, 100, rates)
        assert result_b == result_f == 80.0

    def test_crossing_one_boundary_inflation(self):
        """fromH=50, toH=150, N=100: buggy inflates by 0.5R per boundary.
        Period 0 (rate=1.0): blocks 50..99 = 50 blocks (correct)
            Buggy: 100*1 - 50 + 1 = 51 blocks (+1)
        Period 1 (rate=0.5): blocks 100..149 = 50 blocks (correct)
            Buggy: 150 - 100 - 1 = 49 blocks (-1)
        """
        rates = [1.0, 0.5]
        expected = 50 * 1.0 + 50 * 0.5  # 75.0
        buggy = get_rewards_by_height_buggy(50, 150, 100, rates)
        fixed = get_rewards_by_height_fixed(50, 150, 100, rates)

        assert fixed == expected  # 75.0
        # Buggy: 51*1.0 + 49*0.5 = 51.0 + 24.5 = 75.5
        assert buggy == pytest.approx(75.5)
        assert buggy > expected  # inflated!

    def test_crossing_two_boundaries(self):
        """Multiple boundaries amplify the error."""
        rates = [1.0, 0.5, 0.25]
        # fromH=50, toH=250, N=100
        # Correct: 50*1.0 + 100*0.5 + 50*0.25 = 50 + 50 + 12.5 = 112.5
        fixed = get_rewards_by_height_fixed(50, 250, 100, rates)
        buggy = get_rewards_by_height_buggy(50, 250, 100, rates)

        assert fixed == pytest.approx(112.5)
        # Buggy start period: +1 block at rate 1.0 = +1.0
        # Buggy end period: -1 block at rate 0.25 = -0.25
        # Net: +0.75
        assert buggy == pytest.approx(113.25)

    def test_affects_delegate_undelegate_withdraw(self):
        """The off-by-one affects Delegate, Undelegate,
        WithdrawDelegatorReward, and KYC approve/remove."""
        rates = [1.0, 0.5]
        # Each operation calls getRewardsByHeight — all inflated
        for from_h, to_h in [(0, 150), (30, 120), (99, 200)]:
            buggy = get_rewards_by_height_buggy(from_h, to_h, 100, rates)
            fixed = get_rewards_by_height_fixed(from_h, to_h, 100, rates)
            low = from_h // 100
            high = to_h // 100
            if low != high:
                assert buggy > fixed, (
                    f"Expected inflation for range [{from_h}, {to_h})"
                )

    def test_no_error_within_period(self):
        """When from and to are in the same period, no off-by-one."""
        rates = [1.0, 0.5]
        buggy = get_rewards_by_height_buggy(10, 50, 100, rates)
        fixed = get_rewards_by_height_fixed(10, 50, 100, rates)
        assert buggy == fixed
