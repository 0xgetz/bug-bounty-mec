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
