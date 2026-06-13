"""Bug #8 — MEDIUM | x/wstaking | RemoveMeidNFT
Issue: https://github.com/openmetaearth/me-hub/issues/1247

SetMeidNFT writes the regional index under:
    MeidNFTAccountKeyPrefix + regionId

RemoveMeidNFT deletes from:
    MeidNFTAccountKeyPrefix + account      // WRONG — should be regionId

Result: the regional index entry is never deleted, causing unbounded
storage growth. Region NFT queries return stale/phantom entries.

Fix: use regionId (not account) in the delete prefix.
"""

import pytest
from tests.sdk_helpers import KVStore


MEID_NFT_ACCOUNT_KEY_PREFIX = "meidNFTAccount/"
MEID_NFT_KEY_FMT = "meidNFT/{account}"


def set_meid_nft(store: KVStore, region_id: str, account: str) -> None:
    """Writes regional index under prefix+regionId (correct)."""
    prefix = MEID_NFT_ACCOUNT_KEY_PREFIX + region_id + "/"
    key = prefix + account
    store.set(key, account.encode())


def remove_meid_nft_buggy(store: KVStore, account: str) -> None:
    """Buggy: uses account instead of regionId for prefix."""
    prefix = MEID_NFT_ACCOUNT_KEY_PREFIX + account + "/"
    # This targets a WRONG prefix — nothing matches, nothing deleted
    for k, _ in store.iterate_prefix(prefix):
        store.delete(k)
    # Also deletes from MeidNFTKey — this part works
    store.delete(MEID_NFT_KEY_FMT.format(account=account))


def remove_meid_nft_fixed(store: KVStore, region_id: str, account: str) -> None:
    """Fixed: uses regionId for prefix (matches SetMeidNFT)."""
    prefix = MEID_NFT_ACCOUNT_KEY_PREFIX + region_id + "/"
    key = prefix + account
    store.delete(key)
    store.delete(MEID_NFT_KEY_FMT.format(account=account))


class TestBug08WrongStorePrefix:

    def test_set_and_remove_fixed(self):
        """Fixed: set then remove cleans up the index."""
        store = KVStore()
        set_meid_nft(store, "region-1", "me1alice")
        assert store.has("meidNFTAccount/region-1/me1alice")

        remove_meid_nft_fixed(store, "region-1", "me1alice")
        assert not store.has("meidNFTAccount/region-1/me1alice")

    def test_buggy_remove_leaves_index(self):
        """Buggy: regional index entry is never cleaned up."""
        store = KVStore()
        set_meid_nft(store, "region-1", "me1alice")
        assert store.has("meidNFTAccount/region-1/me1alice")

        remove_meid_nft_buggy(store, "me1alice")

        # The MeidNFTKey entry is removed
        assert not store.has("meidNFT/me1alice")
        # But the regional index is NOT removed — STORAGE LEAK
        assert store.has("meidNFTAccount/region-1/me1alice")

    def test_storage_leak_grows_unbounded(self):
        """Each NFT removal leaks one entry — grows over time."""
        store = KVStore()
        for i in range(100):
            account = f"me1user{i}"
            set_meid_nft(store, "region-1", account)
            remove_meid_nft_buggy(store, account)

        # All 100 regional index entries still present
        leaked = store.iterate_prefix("meidNFTAccount/region-1/")
        assert len(leaked) == 100

    def test_phantom_entries_in_queries(self):
        """Stale entries cause GetMeidNFTByRegion to return removed NFTs."""
        store = KVStore()
        set_meid_nft(store, "region-1", "me1alice")
        set_meid_nft(store, "region-1", "me1bob")

        remove_meid_nft_buggy(store, "me1alice")

        # Query region-1 NFTs — alice is still there (phantom)
        entries = store.iterate_prefix("meidNFTAccount/region-1/")
        accounts = [v.decode() for _, v in entries]
        assert "me1alice" in accounts  # phantom entry
        assert "me1bob" in accounts

    def test_fixed_no_phantom_entries(self):
        """Fixed version properly cleans up the index."""
        store = KVStore()
        set_meid_nft(store, "region-1", "me1alice")
        set_meid_nft(store, "region-1", "me1bob")

        remove_meid_nft_fixed(store, "region-1", "me1alice")

        entries = store.iterate_prefix("meidNFTAccount/region-1/")
        accounts = [v.decode() for _, v in entries]
        assert "me1alice" not in accounts
        assert "me1bob" in accounts
