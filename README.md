# 🐛 Bug Bounty MEC — META EARTH HUB Security Research

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue)
![Bugs Found](https://img.shields.io/badge/bugs%20found-10-red)
![Critical](https://img.shields.io/badge/critical-1-darkred)
![High](https://img.shields.io/badge/high-4-orange)
![Medium](https://img.shields.io/badge/medium-5-yellow)
![Reward](https://img.shields.io/badge/estimated%20reward-$5.8K–$15K%20MEC-green)

</div>

---

## 📋 Overview

This repository contains an original security research report for the **META EARTH HUB Bug Bounty Phase I** program, covering the ME Hub Settlement Layer.

- **Target Repository:** [openmetaearth/me-hub](https://github.com/openmetaearth/me-hub)
- **Bug Bounty Program:** [mec.me/en-US/bug-bounty](https://www.mec.me/en-US/bug-bounty)
- **Scope:** ME Hub (Settlement Layer) — Phase I
- **Total Bugs Found:** 10 original, non-duplicate vulnerabilities
- **Submitted Issues:** [#1240–#1249](https://github.com/openmetaearth/me-hub/issues)

---

## 📄 Report

📥 **[Download Full Report (DOCX)](./ME_Hub_Bug_Bounty_Report.docx)**

The report includes for each bug:
- Root cause analysis with vulnerable code
- Panic log / exploit scenario
- Step-by-step reproduction guide
- Specific fix with corrected code

---

## 🔍 Vulnerability Summary

| # | Severity | Module | Function | Title | Issue |
|---|----------|--------|----------|-------|-------|
| 1 | 🔴 **Critical** | `x/wdistri` | `AllocateBlockReward()` | `sdkmath.Int.Int64()` overflow → EndBlocker panic → chain halt | [#1240](https://github.com/openmetaearth/me-hub/issues/1240) |
| 2 | 🟠 **High** | `x/megroup` | `JoinGroup()`, `procKycRegionChange()` | Empty group admin panic after `UnBondRegion` → chain halt | [#1241](https://github.com/openmetaearth/me-hub/issues/1241) |
| 3 | 🟡 **Medium** | `x/wstaking` | `sendKycRewards()` | Silent `DelegateInterest` accounting skip → treasury divergence | [#1242](https://github.com/openmetaearth/me-hub/issues/1242) |
| 4 | 🟠 **High** | `x/wstaking` | `getRewardsByHeight()` | Off-by-one at halving boundaries → inflated reward payments | [#1243](https://github.com/openmetaearth/me-hub/issues/1243) |
| 5 | 🟠 **High** | `x/wstaking` | `WithdrawFromRegion()` | No solvency check → GlobalDAO can drain treasury | [#1244](https://github.com/openmetaearth/me-hub/issues/1244) |
| 6 | 🟡 **Medium** | `x/wstaking` | `DoFixedDeposit()` | Wrong solvency formula → deposits accepted on insolvent treasury | [#1245](https://github.com/openmetaearth/me-hub/issues/1245) |
| 7 | 🟠 **High** | `x/wstaking` | `IbcTransferFromRegionTreasure()` | Receiver hardcoded as sender → funds permanently burned on destination chain | [#1246](https://github.com/openmetaearth/me-hub/issues/1246) |
| 8 | 🟡 **Medium** | `x/wstaking` | `RemoveMeidNFT()` | Wrong store key prefix → regional index never cleaned, storage leak | [#1247](https://github.com/openmetaearth/me-hub/issues/1247) |
| 9 | 🟡 **Medium** | `x/wstaking` | `SetFixedDepositCfgRate()` | Rate change silently locks existing depositors from KYC region migration | [#1248](https://github.com/openmetaearth/me-hub/issues/1248) |
| 10 | 🟡 **Medium** | `x/wstaking` | `UpdateValidatorPubKey()` | Old slashing `SigningInfo` never deleted → slashing module storage leak | [#1249](https://github.com/openmetaearth/me-hub/issues/1249) |

---

## 💰 Reward Breakdown

| Severity | Count | Range per Bug | Total Range |
|----------|-------|--------------|-------------|
| 🔴 Critical | 1 | $2,000 – $5,000 MEC | $2,000 – $5,000 |
| 🟠 High | 4 | $1,000 – $2,000 MEC | $4,000 – $8,000 |
| 🟡 Medium | 5 | $100 – $1,000 MEC | $500 – $5,000 |
| **Total** | **10** | — | **$5,800 – $15,000 MEC** |

---


---

## 📸 Bug Screenshots — Code Evidence

> Visual proof for each vulnerability with highlighted vulnerable code, root cause, and fix.

### 🔴 Bug #1 — CRITICAL
**AllocateBlockReward — sdkmath.Int.Int64() Overflow → EndBloc**

![Bug #1](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug01_wdistri_int64_overflow.png)

### 🟠 Bug #2 — HIGH
**JoinGroup & procKycRegionChange — Empty Admin Panic After Un**

![Bug #2](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug02_joingroup_empty_admin_panic.png)

### 🟡 Bug #3 — MEDIUM
**sendKycRewards — Silent DelegateInterest Skip Causes Treasur**

![Bug #3](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug03_sendkycrewards_silent_skip.png)

### 🟠 Bug #4 — HIGH
**getRewardsByHeight — Off-by-One at Halving Boundaries → Infl**

![Bug #4](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug04_getrewardheight_offbyone.png)

### 🟠 Bug #5 — HIGH
**WithdrawFromRegion — No Solvency Check Allows GlobalDAO to D**

![Bug #5](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug05_withdrawfromregion_nosolvency.png)

### 🟡 Bug #6 — MEDIUM
**DoFixedDeposit — Wrong Solvency Formula Accepts Deposits on **

![Bug #6](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug06_dofixeddeposit_wrong_formula.png)

### 🟠 Bug #7 — HIGH
**IbcTransferFromRegionTreasure — Receiver Hardcoded as Sender**

![Bug #7](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug07_ibc_receiver_hardcoded.png)

### 🟡 Bug #8 — MEDIUM
**RemoveMeidNFT — Wrong Store Key Prefix → Regional Index Neve**

![Bug #8](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug08_removemeidnft_wrong_prefix.png)

### 🟡 Bug #9 — MEDIUM
**SetFixedDepositCfgRate — Rate Change Silently Locks Deposito**

![Bug #9](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug09_setfixeddepositcfgrate_lock.png)

### 🟡 Bug #10 — MEDIUM
**UpdateValidatorPubKey — Old SlashingInfo Never Deleted → Sla**

![Bug #10](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug10_updatevalidatorpubkey_leak.png)

### 🔴 Bug #11 — CRITICAL
**MsgUpdate Same RegionId → TransferKycRegion Self-Transfer In**

![Bug #11](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug11_msgupdate_same_region_inflation.png)

### 🟠 Bug #12 — HIGH
**Gravity: cleanupTimedOutBatches & OutgoingTxBatchExecuted Mu**

![Bug #12](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug12_gravity_iterator_mutation.png)

### 🟠 Bug #13 — HIGH
**GetCurrentRelayerSet — uint64 Overflow in totalPower Corrupt**

![Bug #13](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug13_gravity_uint64_overflow.png)

### 🟡 Bug #14 — MEDIUM
**Delegate — Returns Wrong newShares for Experience Region → M**

![Bug #14](https://raw.githubusercontent.com/0xgetz/bug-bounty-mec/main/screenshots/bug14_delegate_wrong_newshares.png)

## 🔴 Bug #1 — CRITICAL: AllocateBlockReward Int64 Overflow

**File:** `x/wdistri/keeper/keeper.go`

```go
// VULNERABLE
regionCoins := sdk.NewCoins(sdk.NewCoin(params.BaseDenom, sdk.NewInt(regionAmount.Int64())))
// ↑ .Int64() PANICS if regionAmount > 9,223,372,036,854,775,807

// FIXED
regionCoins := sdk.NewCoins(sdk.NewCoin(params.BaseDenom, regionAmount))
```

**Impact:** When daily FeeCollector balance exceeds `math.MaxInt64` (~9.22×10¹⁸ umec), `EndBlocker` panics → **permanent chain halt**.

---

## 🟠 Bug #2 — HIGH: Empty Admin Panic After UnBondRegion

**File:** `x/megroup/keeper/msg_server_join_group.go`

```go
// When GlobalDAO fully unstakes → UnBondRegion → group.Admin = ""
// Then any JoinGroup call:
sdk.MustAccAddressFromBech32(groupInfo.Admin) // ← PANIC: "empty address string is not allowed"
```

**Impact:** Any user can unknowingly trigger chain halt after GlobalDAO unstake.

---

## 🟠 Bug #4 — HIGH: Off-by-One at Halving Boundaries

**File:** `x/wstaking/keeper/alias_functions.go`

```go
// BUG A (start period overcounts +1):
blockCount = int64(N)*(lowMul+1) - fromHeight + 1  // ← +1 wrong

// BUG B (end period undercounts -1):
blockCount = toHeight - int64(N)*i - 1              // ← -1 wrong

// FIX:
blockCount = int64(N)*(lowMul+1) - fromHeight  // Bug A fixed
blockCount = toHeight - int64(N)*i             // Bug B fixed
```

**Impact:** Users earn `+0.5R` per halving boundary crossed → systematic treasury drain violating emission schedule.

---

## 🟠 Bug #7 — HIGH: IBC Transfer Funds Burned

**File:** `x/wstaking/keeper/msg_server_ibc_transfer_from_region_treasure.go`

```go
// VULNERABLE: both sender and receiver = treasureAddress
_, err := k.IbcTransferKeeper.Transfer(ctx, ibctransfertypes.NewMsgTransfer(
    msg.SourcePort, msg.SourceChannel, msg.Token,
    treasureAddress,   // sender
    treasureAddress,   // receiver ← BUG: funds go to uncontrolled address on dest chain
    ...
))

// FIXED:
receiver := msg.Receiver  // use intended destination
```

**Impact:** All IBC transfers from region treasury are effectively burned — funds permanently lost on destination chain.

---

## 📁 Repository Structure

```
bug-bounty-mec/
├── README.md                        ← This file
└── ME_Hub_Bug_Bounty_Report.docx   ← Full report (all 10 bugs)
```

---


---


---

## 🆕 Round 2 — Additional Bugs Found (#1251–#1254)

| # | Severity | Issue | Title |
|---|----------|-------|-------|
| 11 | 🔴 Critical | [#1251](https://github.com/openmetaearth/me-hub/issues/1251) | MsgUpdate with Same RegionId Calls TransferKycRegion Self-Transfer — F |
| 12 | 🟠 High | [#1252](https://github.com/openmetaearth/me-hub/issues/1252) | cleanupTimedOutBatches and OutgoingTxBatchExecuted Mutate KV Store Ins |
| 13 | 🟠 High | [#1253](https://github.com/openmetaearth/me-hub/issues/1253) | GetCurrentRelayerSet uint64 Overflow in totalPower Accumulation Produc |
| 14 | 🟡 Medium | [#1254](https://github.com/openmetaearth/me-hub/issues/1254) | Delegate Returns Wrong newShares for Experience Region — Misleading Ev |


*All Round 2 bugs verified non-duplicate against issues #1–#1253*
## 💳 MEC Reward Wallet Address

> Semua reward dari program Bug Bounty Phase I harap dikirimkan ke alamat wallet berikut:



| Field | Detail |
|-------|--------|
| **Network** | ME Hub (Settlement Layer) |
| **Denom** | $MEC (umec) |
| **Address** | me1fs6l6vrwhmqykn4wtvjsswpsy0j0ggm2jmywyj |
| **Researcher** | [@0xgetz](https://github.com/0xgetz) |

*Address generated via ME Pass — reward can be exchanged to USDT and withdrawn anytime.*

## 🔗 References

- [Bug Bounty Program](https://www.mec.me/en-US/bug-bounty)
- [ME Hub Repository](https://github.com/openmetaearth/me-hub)
- [Submitted Issues #1240–#1249](https://github.com/openmetaearth/me-hub/issues?q=is%3Aissue+author%3A0xgetz)
- [MetaEarth Developer Twitter](https://twitter.com/MetaEarthDevs)

---

<div align="center">

*All vulnerabilities are original findings, verified non-duplicate against issues #1–#1239.*

*Submitted under the META EARTH Bug Bounty Phase I program — Prize Pool: $100,000 MEC*

</div>
