"""Bug #11 — CRITICAL | x/kyc + x/wstaking | MsgUpdate + transferDeposit
Issue: https://github.com/openmetaearth/me-hub/issues/1251

MsgUpdate allows same-region transfers (perRegionId == msg.RegionId).
In transferDeposit, fromRegion and toRegion are VALUE COPIES of the
same underlying Region. The function does:
    fromRegion.FixedDepositAmount -= X
    toRegion.FixedDepositAmount += X
    SetRegion(fromRegion)    // stores original - X
    SetRegion(toRegion)      // OVERWRITES with original + X  <- INFLATED

Each call inflates FixedDepositAmount by the deposit principal.
After N calls: FixedDepositAmount = original + N * principal.

Fix: guard against same-region by checking
    strings.EqualFold(perRegionId, msg.RegionId)
"""

import copy
import pytest
from tests.sdk_helpers import Int, Region


def transfer_deposit_buggy(
    regions: dict[str, Region],
    from_region_id: str,
    to_region_id: str,
    deposit_amount: int,
) -> dict[str, Region]:
    """Buggy: value copies of the same region, second SetRegion overwrites."""
    # VALUE copies (simulating Go struct copy behavior)
    from_region = copy.deepcopy(regions[from_region_id])
    to_region = copy.deepcopy(regions[to_region_id])

    # Modify copies
    from_region.fixed_deposit_amount = from_region.fixed_deposit_amount.sub(
        Int(deposit_amount)
    )
    to_region.fixed_deposit_amount = to_region.fixed_deposit_amount.add(
        Int(deposit_amount)
    )

    # Write back — second write OVERWRITES first when same region
    regions[from_region_id] = from_region   # stores original - X
    regions[to_region_id] = to_region       # stores original + X (OVERWRITES!)

    return regions


def transfer_deposit_fixed(
    regions: dict[str, Region],
    from_region_id: str,
    to_region_id: str,
    deposit_amount: int,
) -> tuple[dict[str, Region], str | None]:
    """Fixed: rejects same-region transfers."""
    if from_region_id.lower() == to_region_id.lower():
        return regions, "same region transfer not allowed"

    from_region = copy.deepcopy(regions[from_region_id])
    to_region = copy.deepcopy(regions[to_region_id])

    from_region.fixed_deposit_amount = from_region.fixed_deposit_amount.sub(
        Int(deposit_amount)
    )
    to_region.fixed_deposit_amount = to_region.fixed_deposit_amount.add(
        Int(deposit_amount)
    )

    regions[from_region_id] = from_region
    regions[to_region_id] = to_region

    return regions, None


class TestBug11SelfTransferInflation:

    def test_same_region_inflates_buggy(self):
        """Self-transfer inflates FixedDepositAmount by deposit amount."""
        regions = {
            "region-1": Region(
                region_id="region-1",
                fixed_deposit_amount=Int(1000),
            )
        }

        regions = transfer_deposit_buggy(regions, "region-1", "region-1", 500)

        # Expected: should stay 1000 (self-transfer is a no-op)
        # Actual: second SetRegion writes 1000+500 = 1500
        assert regions["region-1"].fixed_deposit_amount == Int(1500)

    def test_repeated_self_transfers_unbounded(self):
        """N calls => FixedDepositAmount = original + N * principal."""
        regions = {
            "region-1": Region(
                region_id="region-1",
                fixed_deposit_amount=Int(1000),
            )
        }
        deposit = 500
        n = 10

        for _ in range(n):
            regions = transfer_deposit_buggy(regions, "region-1", "region-1", deposit)

        # original(1000) + 10 * 500 = 6000
        assert regions["region-1"].fixed_deposit_amount == Int(1000 + n * deposit)

    def test_fixed_rejects_same_region(self):
        """Fixed: same-region transfer returns error."""
        regions = {
            "region-1": Region(
                region_id="region-1",
                fixed_deposit_amount=Int(1000),
            )
        }

        regions, err = transfer_deposit_fixed(regions, "region-1", "region-1", 500)
        assert err is not None
        assert "same region" in err
        assert regions["region-1"].fixed_deposit_amount == Int(1000)

    def test_cross_region_transfer_works(self):
        """Cross-region transfer works correctly in both versions."""
        regions = {
            "region-1": Region(
                region_id="region-1",
                fixed_deposit_amount=Int(1000),
            ),
            "region-2": Region(
                region_id="region-2",
                fixed_deposit_amount=Int(2000),
            ),
        }

        regions = transfer_deposit_buggy(regions, "region-1", "region-2", 300)
        assert regions["region-1"].fixed_deposit_amount == Int(700)
        assert regions["region-2"].fixed_deposit_amount == Int(2300)

    def test_inflation_breaks_solvency(self):
        """Inflated FixedDepositAmount breaks DoFixedDeposit solvency checks."""
        regions = {
            "region-1": Region(
                region_id="region-1",
                fixed_deposit_amount=Int(0),
            )
        }

        # User has 100 deposit, does 100 self-transfers
        for _ in range(100):
            regions = transfer_deposit_buggy(regions, "region-1", "region-1", 100)

        # FixedDepositAmount is now 10000 from thin air
        assert regions["region-1"].fixed_deposit_amount == Int(10000)

    def test_case_insensitive_guard(self):
        """Fixed version handles case-insensitive region ID comparison."""
        regions = {
            "Region-1": Region(
                region_id="Region-1",
                fixed_deposit_amount=Int(1000),
            )
        }

        regions, err = transfer_deposit_fixed(regions, "Region-1", "region-1", 500)
        assert err is not None
        assert "same region" in err
