"""Bug #10 — MEDIUM | x/wstaking | UpdateValidatorPubKey
Issue: https://github.com/openmetaearth/me-hub/issues/1249

When a validator rotates their public key, the old consensus address's
ValidatorSigningInfo is never deleted from the slashing module.

Each key rotation leaks ~50-100 bytes. Stale entries accumulate
unboundedly and cause the slashing module iterator to encounter
phantom decommissioned consensus addresses.

Vulnerable pattern (update_pub_key.go:104-106):
    k.RemoveValidatorByConsAddr(ctx, sdk.ConsAddress(updateInfo.OldConsAddress))
    // MISSING: slashingKeeper.DeleteValidatorSigningInfo(ctx, oldConsAddr)
    k.DeleteReplaceConsensusPubKey(ctx)

Fix: call slashingKeeper.DeleteValidatorSigningInfo(ctx, oldConsAddr).
"""

import pytest
from tests.sdk_helpers import KVStore


SIGNING_INFO_PREFIX = "slashing/signingInfo/"
VALIDATOR_PREFIX = "staking/validator/"


class SlashingStore:
    def __init__(self) -> None:
        self.store = KVStore()

    def set_signing_info(self, cons_addr: str, info: dict) -> None:
        key = SIGNING_INFO_PREFIX + cons_addr
        self.store.set(key, str(info).encode())

    def delete_signing_info(self, cons_addr: str) -> None:
        key = SIGNING_INFO_PREFIX + cons_addr
        self.store.delete(key)

    def has_signing_info(self, cons_addr: str) -> bool:
        return self.store.has(SIGNING_INFO_PREFIX + cons_addr)

    def count_signing_infos(self) -> int:
        return len(self.store.iterate_prefix(SIGNING_INFO_PREFIX))


def update_validator_pubkey_buggy(
    slashing: SlashingStore,
    old_cons_addr: str,
    new_cons_addr: str,
) -> None:
    """Buggy: creates new signing info but never deletes old."""
    # At UpdateAtHeight: create new signing info
    slashing.set_signing_info(new_cons_addr, {"start_height": 100})

    # At UpdateAtHeight+2: remove from staking but NOT slashing
    # k.RemoveValidatorByConsAddr(ctx, oldConsAddr)  -- staking side
    # MISSING: slashing.delete_signing_info(old_cons_addr)


def update_validator_pubkey_fixed(
    slashing: SlashingStore,
    old_cons_addr: str,
    new_cons_addr: str,
) -> None:
    """Fixed: also deletes old signing info from slashing."""
    slashing.set_signing_info(new_cons_addr, {"start_height": 100})
    slashing.delete_signing_info(old_cons_addr)


class TestBug10SigningInfoLeak:

    def test_buggy_leaks_old_signing_info(self):
        """Old cons addr signing info persists after key rotation."""
        slashing = SlashingStore()
        slashing.set_signing_info("consA", {"start_height": 0})

        update_validator_pubkey_buggy(slashing, "consA", "consB")

        assert slashing.has_signing_info("consA")  # LEAKED
        assert slashing.has_signing_info("consB")  # new entry
        assert slashing.count_signing_infos() == 2

    def test_fixed_cleans_up(self):
        """Fixed: old signing info is removed."""
        slashing = SlashingStore()
        slashing.set_signing_info("consA", {"start_height": 0})

        update_validator_pubkey_fixed(slashing, "consA", "consB")

        assert not slashing.has_signing_info("consA")  # cleaned
        assert slashing.has_signing_info("consB")
        assert slashing.count_signing_infos() == 1

    def test_multiple_rotations_accumulate(self):
        """Each rotation leaks one entry — grows unboundedly."""
        slashing = SlashingStore()
        slashing.set_signing_info("cons0", {"start_height": 0})

        for i in range(20):
            old = f"cons{i}"
            new = f"cons{i + 1}"
            update_validator_pubkey_buggy(slashing, old, new)

        # 1 original + 20 new = 21, but 20 old ones are leaked
        assert slashing.count_signing_infos() == 21

    def test_fixed_multiple_rotations_no_leak(self):
        """Fixed version maintains exactly 1 entry per validator."""
        slashing = SlashingStore()
        slashing.set_signing_info("cons0", {"start_height": 0})

        for i in range(20):
            old = f"cons{i}"
            new = f"cons{i + 1}"
            update_validator_pubkey_fixed(slashing, old, new)

        assert slashing.count_signing_infos() == 1
        assert slashing.has_signing_info("cons20")

    def test_phantom_consensus_addresses(self):
        """Stale entries cause iterator to see phantom validators."""
        slashing = SlashingStore()
        slashing.set_signing_info("consOld", {"start_height": 0})
        update_validator_pubkey_buggy(slashing, "consOld", "consNew")

        entries = slashing.store.iterate_prefix(SIGNING_INFO_PREFIX)
        addrs = [k.replace(SIGNING_INFO_PREFIX, "") for k, _ in entries]
        assert "consOld" in addrs  # phantom — validator no longer uses this
