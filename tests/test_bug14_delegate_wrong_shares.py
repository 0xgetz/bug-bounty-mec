"""Bug #14 — MEDIUM | x/wstaking | Delegate
Issue: https://github.com/openmetaearth/me-hub/issues/1254

For experience region delegations, the function updates
delegation.UnMeidAmount but returns delegation.Amount (unchanged)
instead of bondAmt. This emits wrong newShares in EventTypeDelegate,
causing off-chain indexers to show incorrect balances.

Vulnerable pattern (delegation.go:148-154):
    if validator.Description.RegionID == types.ExperienceRegionId {
        delegation.UnMeidAmount = delegation.UnMeidAmount.Add(bondAmt)
    } else {
        delegation.Amount = delegation.Amount.Add(bondAmt)
    }
    k.SetDelegation(ctx, delegation)
    return sdk.NewDecFromInt(delegation.Amount), nil  // WRONG for exp region

Fix: return sdk.NewDecFromInt(bondAmt) — the actually added amount.
"""

import pytest
from tests.sdk_helpers import Int, Dec


EXPERIENCE_REGION_ID = "experience"


def delegate_buggy(
    region_id: str,
    existing_amount: Int,
    existing_un_meid_amount: Int,
    bond_amt: Int,
) -> tuple[Int, Int, Dec]:
    """Buggy: returns delegation.Amount even for experience region.
    Returns (amount, un_meid_amount, newShares).
    """
    amount = existing_amount
    un_meid_amount = existing_un_meid_amount

    if region_id == EXPERIENCE_REGION_ID:
        un_meid_amount = un_meid_amount.add(bond_amt)  # updated
    else:
        amount = amount.add(bond_amt)

    # BUG: always returns amount, which is UNCHANGED for experience region
    new_shares = Dec(str(amount._v))
    return amount, un_meid_amount, new_shares


def delegate_fixed(
    region_id: str,
    existing_amount: Int,
    existing_un_meid_amount: Int,
    bond_amt: Int,
) -> tuple[Int, Int, Dec]:
    """Fixed: returns bondAmt for experience region.
    Returns (amount, un_meid_amount, newShares).
    """
    amount = existing_amount
    un_meid_amount = existing_un_meid_amount

    if region_id == EXPERIENCE_REGION_ID:
        un_meid_amount = un_meid_amount.add(bond_amt)
    else:
        amount = amount.add(bond_amt)

    # FIXED: return the actual amount added
    new_shares = Dec(str(bond_amt._v))
    return amount, un_meid_amount, new_shares


class TestBug14WrongNewShares:

    def test_normal_region_both_correct(self):
        """For normal regions, both implementations return correct shares."""
        amount, un_meid, shares_b = delegate_buggy(
            "normal-region", Int(1000), Int(0), Int(500)
        )
        _, _, shares_f = delegate_fixed(
            "normal-region", Int(1000), Int(0), Int(500)
        )
        assert amount == Int(1500)
        # Buggy returns delegation.Amount=1500, fixed returns bondAmt=500
        # For normal region, delegation.Amount includes the new bond,
        # but the "newShares" should be bondAmt (what was newly added)
        assert shares_f == Dec("500")

    def test_experience_region_buggy_wrong_shares(self):
        """Buggy: returns pre-existing Amount (unchanged) as newShares."""
        amount, un_meid, shares = delegate_buggy(
            EXPERIENCE_REGION_ID, Int(1000), Int(200), Int(500)
        )
        assert un_meid == Int(700)  # correctly updated
        assert amount == Int(1000)  # unchanged for exp region
        assert shares == Dec("1000")  # WRONG — should be 500

    def test_experience_region_fixed_correct_shares(self):
        """Fixed: returns bondAmt as newShares."""
        amount, un_meid, shares = delegate_fixed(
            EXPERIENCE_REGION_ID, Int(1000), Int(200), Int(500)
        )
        assert un_meid == Int(700)
        assert amount == Int(1000)
        assert shares == Dec("500")  # CORRECT

    def test_first_delegation_returns_zero_buggy(self):
        """First-ever delegation to experience region: Amount=0 → shares=0."""
        _, _, shares = delegate_buggy(
            EXPERIENCE_REGION_ID, Int(0), Int(0), Int(1000)
        )
        assert shares == Dec("0")  # Returns 0 instead of 1000!

    def test_first_delegation_returns_correct_fixed(self):
        """Fixed: first delegation correctly reports 1000 shares."""
        _, _, shares = delegate_fixed(
            EXPERIENCE_REGION_ID, Int(0), Int(0), Int(1000)
        )
        assert shares == Dec("1000")

    def test_indexer_inconsistency(self):
        """Demonstrates how wrong shares propagate to indexers.
        EventTypeDelegate with AttributeKeyNewShares = wrong value.
        """
        # Simulate multiple delegations
        amount = Int(0)
        un_meid = Int(0)
        total_shares_buggy = 0
        total_shares_fixed = 0

        for bond in [100, 200, 300]:
            _, un_meid_b, shares_b = delegate_buggy(
                EXPERIENCE_REGION_ID, amount, un_meid, Int(bond)
            )
            _, un_meid_f, shares_f = delegate_fixed(
                EXPERIENCE_REGION_ID, amount, un_meid, Int(bond)
            )
            total_shares_buggy += int(shares_b._v)
            total_shares_fixed += int(shares_f._v)
            un_meid = un_meid_b

        # Buggy: reports 0+0+0 = 0 total shares (all wrong)
        assert total_shares_buggy == 0
        # Fixed: reports 100+200+300 = 600
        assert total_shares_fixed == 600
