# 🐛 Bug Bounty MEC — META EARTH HUB Security Research

<div align="center">

![Bugs Found](https://img.shields.io/badge/Total%20Bugs-14-critical?style=for-the-badge)
![Critical](https://img.shields.io/badge/Critical-2-red?style=for-the-badge)
![High](https://img.shields.io/badge/High-6-orange?style=for-the-badge)
![Medium](https://img.shields.io/badge/Medium-6-yellow?style=for-the-badge)
![Reward](https://img.shields.io/badge/Estimated%20Reward-%248.8K%E2%80%9322K%20MEC-brightgreen?style=for-the-badge)

</div>

---

## 📋 Overview

Original security research report for the **META EARTH HUB Bug Bounty Phase I** program.  
All bugs are independently discovered, deeply analyzed, and verified non-duplicate.

| Field | Detail |
|-------|--------|
| **Target** | [openmetaearth/me-hub](https://github.com/openmetaearth/me-hub) |
| **Program** | [mec.me/en-US/bug-bounty](https://www.mec.me/en-US/bug-bounty) |
| **Scope** | ME Hub — Settlement Layer (Phase I) |
| **Total Bugs** | 14 original vulnerabilities |
| **Issues Submitted** | [#1240–#1254](https://github.com/openmetaearth/me-hub/issues?q=is%3Aissue+author%3A0xgetz) |
| **Researcher** | [@0xgetz](https://github.com/0xgetz) |
| **Reward Wallet** | `me1fs6l6vrwhmqykn4wtvjsswpsy0j0ggm2jmywyj` |

---

## 📥 Full Report

📄 **[Download Complete Bug Report (DOCX)](./ME_Hub_Bug_Bounty_Report.docx)**

Each report contains: vulnerable code, root cause analysis, exploit scenario, panic log / reproduction steps, and specific code fix.

---

## 💳 Reward Wallet Address

All `$MEC` rewards should be sent to:

```
me1fs6l6vrwhmqykn4wtvjsswpsy0j0ggm2jmywyj
```

*Generated via ME Pass — as per Bug Bounty program Rule 5. Freely exchangeable to USDT.*

---

## 🔍 Complete Vulnerability Summary

### Round 1 — Issues #1240–#1249

| # | Severity | Module | Function | Title | Issue |
|---|----------|--------|----------|-------|-------|
| 1 | 🔴 Critical | `x/wdistri` | `AllocateBlockReward()` | `sdkmath.Int.Int64()` overflow → EndBlocker panics → chain halt | [#1240](https://github.com/openmetaearth/me-hub/issues/1240) |
| 2 | 🟠 High | `x/megroup` | `JoinGroup()`, `procKycRegionChange()` | Empty group admin panic after `UnBondRegion` → chain halt | [#1241](https://github.com/openmetaearth/me-hub/issues/1241) |
| 3 | 🟡 Medium | `x/wstaking` | `sendKycRewards()` | Silent `DelegateInterest` deduction skip → treasury accounting divergence | [#1242](https://github.com/openmetaearth/me-hub/issues/1242) |
| 4 | 🟠 High | `x/wstaking` | `getRewardsByHeight()` | Off-by-one at halving boundaries → inflated delegation interest payments | [#1243](https://github.com/openmetaearth/me-hub/issues/1243) |
| 5 | 🟠 High | `x/wstaking` | `WithdrawFromRegion()` | No solvency check → GlobalDAO can drain treasury below `DelegateInterest` | [#1244](https://github.com/openmetaearth/me-hub/issues/1244) |
| 6 | 🟡 Medium | `x/wstaking` | `DoFixedDeposit()` | Wrong solvency formula → deposits accepted on insolvent treasury | [#1245](https://github.com/openmetaearth/me-hub/issues/1245) |
| 7 | 🟠 High | `x/wstaking` | `IbcTransferFromRegionTreasure()` | Receiver hardcoded as sender address → funds permanently burned on destination chain | [#1246](https://github.com/openmetaearth/me-hub/issues/1246) |
| 8 | 🟡 Medium | `x/wstaking` | `RemoveMeidNFT()` | Wrong store key prefix → regional index never deleted, persistent storage leak | [#1247](https://github.com/openmetaearth/me-hub/issues/1247) |
| 9 | 🟡 Medium | `x/wstaking` | `SetFixedDepositCfgRate()` | Rate change silently locks existing depositors from KYC region migration | [#1248](https://github.com/openmetaearth/me-hub/issues/1248) |
| 10 | 🟡 Medium | `x/wstaking` | `UpdateValidatorPubKey()` | Old consensus address `SigningInfo` never deleted → slashing module storage leak | [#1249](https://github.com/openmetaearth/me-hub/issues/1249) |

### Round 2 — Issues #1251–#1254

| # | Severity | Module | Function | Title | Issue |
|---|----------|--------|----------|-------|-------|
| 11 | 🔴 Critical | `x/kyc`, `x/wstaking` | `Update()`, `transferDeposit()` | Same-region `MsgUpdate` inflates `FixedDepositAmount` indefinitely via self-transfer overwrite | [#1251](https://github.com/openmetaearth/me-hub/issues/1251) |
| 12 | 🟠 High | `x/gravity` | `cleanupTimedOutBatches()`, `OutgoingTxBatchExecuted()` | Store mutation inside active batch iterator → skipped cancellations or chain panic | [#1252](https://github.com/openmetaearth/me-hub/issues/1252) |
| 13 | 🟠 High | `x/gravity` | `GetCurrentRelayerSet()` | `uint64` overflow in `totalPower` accumulation corrupts bridge validator normalization | [#1253](https://github.com/openmetaearth/me-hub/issues/1253) |
| 14 | 🟡 Medium | `x/wstaking` | `Delegate()` | Returns wrong `newShares` for experience region → misleading events, indexer inconsistency | [#1254](https://github.com/openmetaearth/me-hub/issues/1254) |

---

## 💰 Reward Estimate

| Severity | Count | Per Bug | Subtotal |
|----------|-------|---------|----------|
| 🔴 Critical | 2 | $2,000 – $5,000 MEC | $4,000 – $10,000 |
| 🟠 High | 6 | $1,000 – $2,000 MEC | $6,000 – $12,000 |
| 🟡 Medium | 6 | $100 – $1,000 MEC | $600 – $6,000 |
| **Total** | **14** | — | **$8,800 – $22,000 MEC** |

---

## 📸 Bug Screenshots — Code Evidence

> Each screenshot shows: vulnerable code highlighted in red, suggested fix in green,  
> root cause analysis panel, linked GitHub issue, and reward wallet address.

---

### 🔴 Bug #1 — CRITICAL | `x/wdistri` | [Issue #1240](https://github.com/openmetaearth/me-hub/issues/1240)
**`AllocateBlockReward` — `sdkmath.Int.Int64()` overflow in EndBlocker → permanent chain halt**

![Bug #1 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug01_wdistri_int64_overflow.png)

---

### 🟠 Bug #2 — HIGH | `x/megroup` | [Issue #1241](https://github.com/openmetaearth/me-hub/issues/1241)
**`JoinGroup` & `procKycRegionChange` — empty group admin panic after `UnBondRegion` → chain halt**

![Bug #2 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug02_joingroup_empty_admin_panic.png)

---

### 🟡 Bug #3 — MEDIUM | `x/wstaking` | [Issue #1242](https://github.com/openmetaearth/me-hub/issues/1242)
**`sendKycRewards` — silent `DelegateInterest` deduction skip → treasury accounting divergence**

![Bug #3 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug03_sendkycrewards_silent_skip.png)

---

### 🟠 Bug #4 — HIGH | `x/wstaking` | [Issue #1243](https://github.com/openmetaearth/me-hub/issues/1243)
**`getRewardsByHeight` — off-by-one errors at halving boundaries → inflated delegation interest payments**

![Bug #4 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug04_getrewardheight_offbyone.png)

---

### 🟠 Bug #5 — HIGH | `x/wstaking` | [Issue #1244](https://github.com/openmetaearth/me-hub/issues/1244)
**`WithdrawFromRegion` — no solvency check allows GlobalDAO to drain treasury below `DelegateInterest` obligations**

![Bug #5 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug05_withdrawfromregion_nosolvency.png)

---

### 🟡 Bug #6 — MEDIUM | `x/wstaking` | [Issue #1245](https://github.com/openmetaearth/me-hub/issues/1245)
**`DoFixedDeposit` — wrong solvency formula uses `regionShare` and `initAllocationFunds` not in actual interest calculation**

![Bug #6 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug06_dofixeddeposit_wrong_formula.png)

---

### 🟠 Bug #7 — HIGH | `x/wstaking` | [Issue #1246](https://github.com/openmetaearth/me-hub/issues/1246)
**`IbcTransferFromRegionTreasure` — receiver hardcoded as treasury address → funds sent to uncontrolled address, permanently burned**

![Bug #7 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug07_ibc_receiver_hardcoded.png)

---

### 🟡 Bug #8 — MEDIUM | `x/wstaking` | [Issue #1247](https://github.com/openmetaearth/me-hub/issues/1247)
**`RemoveMeidNFT` — uses `account` instead of `regionId` as store prefix → regional index never cleaned, storage leak grows unboundedly**

![Bug #8 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug08_removemeidnft_wrong_prefix.png)

---

### 🟡 Bug #9 — MEDIUM | `x/wstaking` | [Issue #1248](https://github.com/openmetaearth/me-hub/issues/1248)
**`SetFixedDepositCfgRate` — rate change when active deposits exist silently locks all depositors from KYC region migration**

![Bug #9 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug09_setfixeddepositcfgrate_lock.png)

---

### 🟡 Bug #10 — MEDIUM | `x/wstaking` | [Issue #1249](https://github.com/openmetaearth/me-hub/issues/1249)
**`UpdateValidatorPubKey` — old consensus address `ValidatorSigningInfo` never deleted from slashing module → persistent storage leak**

![Bug #10 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug10_updatevalidatorpubkey_leak.png)

---

### 🔴 Bug #11 — CRITICAL | `x/kyc` + `x/wstaking` | [Issue #1251](https://github.com/openmetaearth/me-hub/issues/1251)
**`MsgUpdate` same `regionId` — `transferDeposit` self-transfer inflates `FixedDepositAmount` by deposit principal per call, indefinitely**

![Bug #11 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug11_msgupdate_same_region_inflation.png)

---

### 🟠 Bug #12 — HIGH | `x/gravity` | [Issue #1252](https://github.com/openmetaearth/me-hub/issues/1252)
**`cleanupTimedOutBatches` & `OutgoingTxBatchExecuted` — `DeleteBatch` called inside active `IterateOutgoingTxBatches` iterator → skipped cancellations or chain panic**

![Bug #12 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug12_gravity_iterator_mutation.png)

---

### 🟠 Bug #13 — HIGH | `x/gravity` | [Issue #1253](https://github.com/openmetaearth/me-hub/issues/1253)
**`GetCurrentRelayerSet` — `uint64` silent overflow when total relayer power exceeds `MaxUint64` → bridge validator powers inflated → single-relayer quorum exploit**

![Bug #13 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug13_gravity_uint64_overflow.png)

---

### 🟡 Bug #14 — MEDIUM | `x/wstaking` | [Issue #1254](https://github.com/openmetaearth/me-hub/issues/1254)
**`Delegate` — returns `delegation.Amount` (unchanged) instead of `bondAmt` for experience region delegations → wrong `newShares` emitted in events**

![Bug #14 Screenshot](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug14_delegate_wrong_newshares.png)

---

## 📁 Repository Structure

```
bug-bounty-mec/
├── README.md                          ← Generated from bugs.json
├── bugs.json                          ← Single source of truth for all bug data
├── generate_readme.py                 ← README generator script
├── ME_Hub_Bug_Bounty_Report.docx     ← Full DOCX report (all 14 bugs)
└── screenshots/
    ├── bug01_wdistri_int64_overflow.png
    ├── bug02_joingroup_empty_admin_panic.png
    ├── bug03_sendkycrewards_silent_skip.png
    ├── bug04_getrewardheight_offbyone.png
    ├── bug05_withdrawfromregion_nosolvency.png
    ├── bug06_dofixeddeposit_wrong_formula.png
    ├── bug07_ibc_receiver_hardcoded.png
    ├── bug08_removemeidnft_wrong_prefix.png
    ├── bug09_setfixeddepositcfgrate_lock.png
    ├── bug10_updatevalidatorpubkey_leak.png
    ├── bug11_msgupdate_same_region_inflation.png
    ├── bug12_gravity_iterator_mutation.png
    ├── bug13_gravity_uint64_overflow.png
    └── bug14_delegate_wrong_newshares.png
```

---

## 🔗 References

- 🌐 [Bug Bounty Program](https://www.mec.me/en-US/bug-bounty)
- 💻 [ME Hub Source Repository](https://github.com/openmetaearth/me-hub)
- 🐛 [All Submitted Issues by @0xgetz](https://github.com/openmetaearth/me-hub/issues?q=is%3Aissue+author%3A0xgetz)
- 🐦 [MetaEarth Developers Twitter](https://twitter.com/MetaEarthDevs)
- 💬 [MetaEarth Developer Telegram](https://t.me/metaearthdevs)

---

<div align="center">

*All 14 vulnerabilities are original findings, verified non-duplicate against issues #1–#1250.*

*Submitted under the META EARTH Bug Bounty Phase I — Prize Pool: $100,000 MEC*

</div>
