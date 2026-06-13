"""Bug #2 — HIGH | x/megroup | JoinGroup & procKycRegionChange
Issue: https://github.com/openmetaearth/me-hub/issues/1241

After GlobalDAO full unstake -> UnBondRegion, group.Admin becomes "".
sdk.MustAccAddressFromBech32("") panics with "empty address string is
not allowed", halting the chain when any user calls MsgJoinGroup.

Vulnerable pattern (msg_server_join_group.go:71):
    sdk.MustAccAddressFromBech32(groupInfo.Admin)  // Admin == "" -> PANIC

Fix: guard len(groupInfo.Admin) == 0 before calling MustAccAddressFromBech32.
"""

import pytest


# -- Simulated SDK helpers --------------------------------------------------

def must_acc_address_from_bech32(address: str) -> str:
    """Simulates sdk.MustAccAddressFromBech32 — panics on empty string."""
    if not address:
        raise ValueError("empty address string is not allowed")
    if not address.startswith("me1"):
        raise ValueError(f"invalid bech32 address: {address}")
    return address


# -- Buggy vs fixed implementations ----------------------------------------

def join_group_send_reward_buggy(group_admin: str, region_addr: str) -> str:
    """Buggy: no guard on empty admin."""
    from_addr = must_acc_address_from_bech32(region_addr)
    to_addr = must_acc_address_from_bech32(group_admin)  # PANICS if ""
    return f"sent from {from_addr} to {to_addr}"


def join_group_send_reward_fixed(group_admin: str, region_addr: str) -> str | None:
    """Fixed: returns None (error) if admin is empty."""
    if len(group_admin) == 0:
        return None  # ErrGroupNoAdmin
    from_addr = must_acc_address_from_bech32(region_addr)
    to_addr = must_acc_address_from_bech32(group_admin)
    return f"sent from {from_addr} to {to_addr}"


# -- Simulate UnBondRegion flow ---------------------------------------------

class GroupInfo:
    def __init__(self, admin: str, region_id: str):
        self.admin = admin
        self.region_id = region_id


def unbond_region(group: GroupInfo, stake_shares_zero: bool) -> GroupInfo:
    """When stake shares go to zero, UnBondRegion clears the admin."""
    if stake_shares_zero:
        group.admin = ""
    return group


# -- Tests -----------------------------------------------------------------

class TestBug02EmptyAdminPanic:
    """Validate that empty group admin causes panic in JoinGroup."""

    def test_normal_join_group(self):
        """With a valid admin, JoinGroup succeeds."""
        result = join_group_send_reward_buggy(
            "me1validadminaddr",
            "me1regiontreasureaddr",
        )
        assert "sent from" in result

    def test_empty_admin_panics_buggy(self):
        """After UnBondRegion, admin="" causes panic."""
        group = GroupInfo(admin="me1originaladmin", region_id="region-1")
        group = unbond_region(group, stake_shares_zero=True)
        assert group.admin == ""

        with pytest.raises(ValueError, match="empty address string"):
            join_group_send_reward_buggy(group.admin, "me1regionaddr")

    def test_empty_admin_handled_fixed(self):
        """Fixed version returns error instead of panicking."""
        group = GroupInfo(admin="me1originaladmin", region_id="region-1")
        group = unbond_region(group, stake_shares_zero=True)

        result = join_group_send_reward_fixed(group.admin, "me1regionaddr")
        assert result is None  # graceful error

    def test_proc_kyc_region_change_same_vulnerability(self):
        """procKycRegionChange has the same bug with newGrpInfo.Admin."""
        new_group = GroupInfo(admin="", region_id="region-2")

        with pytest.raises(ValueError, match="empty address string"):
            join_group_send_reward_buggy(new_group.admin, "me1treasureaddr")

        result = join_group_send_reward_fixed(new_group.admin, "me1treasureaddr")
        assert result is None

    def test_non_empty_admin_fixed_still_works(self):
        """Fixed version works normally when admin is present."""
        result = join_group_send_reward_fixed(
            "me1validadmin",
            "me1regionaddr",
        )
        assert result is not None
        assert "sent from" in result
