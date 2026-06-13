"""Bug #13 — HIGH | x/gravity | GetCurrentRelayerSet
Issue: https://github.com/openmetaearth/me-hub/issues/1253

totalPower is a uint64 that silently wraps around on overflow.
When sum of relayer powers exceeds MaxUint64, totalPower wraps to
near-zero. Division by near-zero inflates each relayer's normalized
power by ~10^10x, allowing a single compromised relayer to hold
quorum for ALL attestations (e.g. MsgSendToMeClaim → mint tokens).

Vulnerable pattern (relayer_set.go:44-47):
    var totalPower uint64
    for _, relayer := range allRelayers {
        totalPower += power.Uint64()  // WRAPS AROUND on overflow
    }

Fix: use math/big.Int for totalPower accumulation.
"""

import pytest
from tests.sdk_helpers import MAX_UINT64


def get_current_relayer_set_buggy(powers: list[int]) -> list[float]:
    """Buggy: uint64 overflow wraps silently."""
    total_power = 0
    for p in powers:
        total_power = (total_power + p) & MAX_UINT64  # simulate uint64 wrap

    if total_power == 0:
        return [0.0] * len(powers)

    normalized = []
    for p in powers:
        normalized.append(p / total_power)
    return normalized


def get_current_relayer_set_fixed(powers: list[int]) -> list[float]:
    """Fixed: uses arbitrary-precision integer for accumulation."""
    total_power = sum(powers)  # Python int is arbitrary precision

    if total_power == 0:
        return [0.0] * len(powers)

    normalized = []
    for p in powers:
        normalized.append(p / total_power)
    return normalized


class TestBug13Uint64Overflow:

    def test_normal_powers_no_overflow(self):
        """Normal power values produce correct normalization."""
        powers = [100, 200, 300]
        buggy = get_current_relayer_set_buggy(powers)
        fixed = get_current_relayer_set_fixed(powers)

        assert buggy == pytest.approx(fixed)
        assert sum(fixed) == pytest.approx(1.0)

    def test_uint64_overflow_wraps(self):
        """When total exceeds MaxUint64, buggy version wraps around."""
        # Two relayers whose combined power exceeds MaxUint64
        # but wraps to a small non-zero value
        p1 = MAX_UINT64 // 2 + 100
        p2 = MAX_UINT64 // 2 + 100
        powers = [p1, p2]

        buggy = get_current_relayer_set_buggy(powers)
        fixed = get_current_relayer_set_fixed(powers)

        # Fixed: each relayer has ~50% power
        assert fixed[0] == pytest.approx(0.5, abs=0.01)
        assert fixed[1] == pytest.approx(0.5, abs=0.01)

        # Buggy: totalPower wrapped to a tiny value
        wrapped_total = (p1 + p2) & MAX_UINT64
        assert wrapped_total < p1  # confirms wrap-around
        assert wrapped_total > 0   # non-zero so division happens
        # Each relayer's power / wrapped_total >> 1.0
        assert buggy[0] > 1.0  # massively inflated!

    def test_single_relayer_quorum_exploit(self):
        """A single compromised relayer can appear to hold 100%+ power."""
        # 4 relayers whose combined power wraps to a small value
        # Craft powers so wrapped total is tiny but non-zero
        base = MAX_UINT64 // 4
        powers = [base, base, base, base + 100]

        buggy = get_current_relayer_set_buggy(powers)
        fixed = get_current_relayer_set_fixed(powers)

        # Fixed: each relayer has ~25% power
        assert all(p == pytest.approx(0.25, abs=0.01) for p in fixed)

        # Buggy: wrapped total is tiny, each relayer power / tiny is enormous
        wrapped = sum(powers) & MAX_UINT64
        assert wrapped < 1000  # wrapped to small value
        assert wrapped > 0
        assert buggy[0] > 1.0  # each relayer appears to hold >100% power

    def test_overflow_at_exact_boundary(self):
        """Overflow at exactly MaxUint64+1 wraps to 0."""
        p1 = MAX_UINT64
        p2 = 1
        powers = [p1, p2]

        buggy = get_current_relayer_set_buggy(powers)
        # totalPower = (MaxUint64 + 1) & MaxUint64 = 0
        # Division by zero
        assert buggy == [0.0, 0.0]  # or infinity/nan depending on impl

        fixed = get_current_relayer_set_fixed(powers)
        assert fixed[0] == pytest.approx(1.0, abs=0.001)

    def test_many_relayers_gradual_overflow(self):
        """Even moderate individual powers can overflow with many relayers."""
        # 1000 relayers with power 2^55 each
        power_each = 2 ** 55
        n = 1000
        powers = [power_each] * n

        total = power_each * n
        assert total > MAX_UINT64  # overflows

        fixed = get_current_relayer_set_fixed(powers)
        assert all(p == pytest.approx(1.0 / n) for p in fixed)

        buggy = get_current_relayer_set_buggy(powers)
        wrapped = (power_each * n) & MAX_UINT64
        if wrapped > 0:
            # Each relayer's apparent power is power_each / wrapped
            assert buggy[0] != pytest.approx(1.0 / n, rel=0.01)
