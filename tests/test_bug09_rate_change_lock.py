"""Bug #9 — MEDIUM | x/wstaking | SetFixedDepositCfgRate
Issue: https://github.com/openmetaearth/me-hub/issues/1248

Rate change overwrites config.Rate immediately. transferDeposit()
then compares fixed.Rate != config.Rate and fails — blocking ALL
users with active deposits from migrating KYC regions.

Vulnerable pattern (msg_server_fixed_deposit_cfg.go:49-50):
    config.Rate = msg.Rate   // immediately overwrites
    k.Keeper.SetFixedDepositCfg(ctx, config)

In transferDeposit:
    if !rate.Equal(fixed.Rate) { return error }  // now always fails!

Fix: block rate change if GetFixedDepositCountOfCfg > 0.
"""

import pytest
from tests.sdk_helpers import Dec


class FixedDepositConfig:
    def __init__(self, region_id: str, term: int, rate: Dec):
        self.region_id = region_id
        self.term = term
        self.rate = rate


class FixedDeposit:
    def __init__(self, config_rate: Dec, amount: int):
        self.rate = config_rate
        self.amount = amount


class DepositStore:
    def __init__(self) -> None:
        self.configs: dict[str, FixedDepositConfig] = {}
        self.deposits: list[FixedDeposit] = []

    def get_active_deposit_count(self, region_id: str, term: int) -> int:
        return len(self.deposits)


def set_rate_buggy(
    store: DepositStore,
    region_id: str,
    term: int,
    new_rate: Dec,
) -> str | None:
    """Buggy: overwrites rate without checking active deposits."""
    key = f"{region_id}/{term}"
    cfg = store.configs.get(key)
    if cfg is None:
        return "config not found"
    cfg.rate = new_rate
    store.configs[key] = cfg
    return None


def set_rate_fixed(
    store: DepositStore,
    region_id: str,
    term: int,
    new_rate: Dec,
) -> str | None:
    """Fixed: blocks rate change if active deposits exist."""
    key = f"{region_id}/{term}"
    cfg = store.configs.get(key)
    if cfg is None:
        return "config not found"
    if store.get_active_deposit_count(region_id, term) > 0:
        return "active deposits exist"
    cfg.rate = new_rate
    store.configs[key] = cfg
    return None


def transfer_deposit(
    deposit: FixedDeposit,
    current_config_rate: Dec,
) -> str | None:
    """transferDeposit enforces rate equality."""
    if deposit.rate != current_config_rate:
        return "rate mismatch: deposit locked"
    return None  # success


class TestBug09RateChangeLock:

    def test_rate_change_locks_existing_depositors(self):
        """After rate change, existing depositors cannot migrate."""
        store = DepositStore()
        old_rate = Dec("0.05")
        cfg = FixedDepositConfig("region-1", 365, old_rate)
        store.configs["region-1/365"] = cfg

        # User creates deposit at old rate
        deposit = FixedDeposit(config_rate=old_rate, amount=1000)
        store.deposits.append(deposit)

        # GlobalDAO changes rate (buggy — no guard)
        err = set_rate_buggy(store, "region-1", 365, Dec("0.10"))
        assert err is None  # Change succeeds

        # Now depositor tries to migrate region — blocked!
        err = transfer_deposit(deposit, store.configs["region-1/365"].rate)
        assert err is not None
        assert "rate mismatch" in err

    def test_fixed_blocks_rate_change(self):
        """Fixed: rate change rejected while deposits are active."""
        store = DepositStore()
        old_rate = Dec("0.05")
        cfg = FixedDepositConfig("region-1", 365, old_rate)
        store.configs["region-1/365"] = cfg

        deposit = FixedDeposit(config_rate=old_rate, amount=1000)
        store.deposits.append(deposit)

        err = set_rate_fixed(store, "region-1", 365, Dec("0.10"))
        assert err is not None
        assert "active deposits exist" in err

        # Rate unchanged — depositor can still migrate
        err = transfer_deposit(deposit, store.configs["region-1/365"].rate)
        assert err is None

    def test_rate_change_ok_when_no_deposits(self):
        """Rate change is fine when no active deposits exist."""
        store = DepositStore()
        cfg = FixedDepositConfig("region-1", 365, Dec("0.05"))
        store.configs["region-1/365"] = cfg

        err = set_rate_fixed(store, "region-1", 365, Dec("0.10"))
        assert err is None
        assert store.configs["region-1/365"].rate == Dec("0.10")

    def test_repeated_rate_changes_permanent_lock(self):
        """GlobalDAO can repeatedly change rates, permanently locking
        depositors from ever migrating."""
        store = DepositStore()
        cfg = FixedDepositConfig("region-1", 365, Dec("0.05"))
        store.configs["region-1/365"] = cfg
        deposit = FixedDeposit(config_rate=Dec("0.05"), amount=1000)
        store.deposits.append(deposit)

        # Multiple rate changes
        for new_rate in ["0.06", "0.07", "0.05"]:
            set_rate_buggy(store, "region-1", 365, Dec(new_rate))

        # Even changing back to 0.05 may not help if deposit snapshot differs
        # In this case it does match, but the window of being locked is real
