#!/usr/bin/env python3
"""Generate README.md from bugs.json — single source of truth for all bug data.

Usage:
    python generate_readme.py          # writes README.md
    python generate_readme.py --check  # exits non-zero if README.md is stale
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).parent / "bugs.json"
OUTPUT_FILE = Path(__file__).parent / "README.md"

SEVERITY_EMOJI = {"critical": "\U0001f534", "high": "\U0001f7e0", "medium": "\U0001f7e1"}
SEVERITY_LABEL = {"critical": "Critical", "high": "High", "medium": "Medium"}
SEVERITY_BADGE_COLOR = {"critical": "red", "high": "orange", "medium": "yellow"}


# ---------------------------------------------------------------------------
# Shared rendering utilities
# ---------------------------------------------------------------------------


def badge(alt: str, label: str, value: str, color: str, style: str = "for-the-badge") -> str:
    """Render a shields.io badge."""
    safe_label = label.replace(" ", "%20")
    return f"![{alt}](https://img.shields.io/badge/{safe_label}-{value}-{color}?style={style})"


def issue_url(issue_number: int, base: str) -> str:
    return f"{base}/issues/{issue_number}"


def issue_link(issue_number: int, base: str) -> str:
    return f"[#{issue_number}]({issue_url(issue_number, base)})"


def screenshot_md(bug: dict, base_url: str) -> str:
    return f'![Bug #{bug["id"]} Screenshot]({base_url}/{bug["screenshot"]})'


def functions_md(funcs: list[str]) -> str:
    return ", ".join(f"`{f}`" for f in funcs)


def severity_icon(sev: str) -> str:
    return SEVERITY_EMOJI[sev]


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def build_header(meta: dict, counts: Counter) -> str:
    total = sum(counts.values())
    badges = "\n".join([
        badge("Bugs Found", "Total%20Bugs", str(total), "critical"),
        badge("Critical", "Critical", str(counts["critical"]), "red"),
        badge("High", "High", str(counts["high"]), "orange"),
        badge("Medium", "Medium", str(counts["medium"]), "yellow"),
        badge("Reward", "Estimated%20Reward", "%248.8K%E2%80%9322K%20MEC", "brightgreen"),
    ])
    return f"""# \U0001f41b Bug Bounty MEC \u2014 META EARTH HUB Security Research

<div align="center">

{badges}

</div>

---

## \U0001f4cb Overview

Original security research report for the **META EARTH HUB Bug Bounty Phase I** program.  
All bugs are independently discovered, deeply analyzed, and verified non-duplicate.

| Field | Detail |
|-------|--------|
| **Target** | [{meta["target_repo"]}]({meta["target_url"]}) |
| **Program** | [{meta["program_display"]}]({meta["program_url"]}) |
| **Scope** | {meta["scope"]} |
| **Total Bugs** | {total} original vulnerabilities |
| **Issues Submitted** | [{meta["issue_range"]}]({meta["issues_url"]}) |
| **Researcher** | [{meta["researcher"]}]({meta["researcher_url"]}) |
| **Reward Wallet** | `{meta["reward_wallet"]}` |

---

## \U0001f4e5 Full Report

\U0001f4c4 **[Download Complete Bug Report (DOCX)](./ME_Hub_Bug_Bounty_Report.docx)**

Each report contains: vulnerable code, root cause analysis, exploit scenario, panic log / reproduction steps, and specific code fix.

---

## \U0001f4b3 Reward Wallet Address

All `$MEC` rewards should be sent to:

```
{meta["reward_wallet"]}
```

*Generated via ME Pass \u2014 as per Bug Bounty program Rule 5. Freely exchangeable to USDT.*

---"""


def build_summary_table(round_info: dict, bugs: list[dict], base: str) -> str:
    rows = []
    for b in bugs:
        sev = b["severity"]
        rows.append(
            f'| {b["id"]} '
            f"| {severity_icon(sev)} {SEVERITY_LABEL[sev]} "
            f'| `{b["module"]}` '
            f"| {functions_md(b['functions'])} "
            f'| {b["title"]} '
            f"| {issue_link(b['issue_number'], base)} |"
        )
    table = "\n".join(rows)
    return f"""### {round_info["name"]} \u2014 {round_info["issue_range"]}

| # | Severity | Module | Function | Title | Issue |
|---|----------|--------|----------|-------|-------|
{table}"""


def build_detail_section(bug: dict, meta: dict) -> str:
    sev = bug["severity"]
    base = meta["target_url"]
    ss_base = meta["screenshot_base_url"]
    sev_label = SEVERITY_LABEL[sev].upper()
    module_display = bug["module"]
    # Bug 11 uses two modules separated by `, `
    if "`, `" in module_display:
        parts = module_display.split("`, `")
        module_display = "` + `".join(parts)
    module_md = f"`{module_display}`"
    return f"""### {severity_icon(sev)} Bug #{bug["id"]} \u2014 {sev_label} | {module_md} | [Issue #{bug["issue_number"]}]({issue_url(bug["issue_number"], base)})
**{bug["detail_title"]}**

{screenshot_md(bug, ss_base)}

---"""


def build_reward_table(counts: Counter, tiers: dict, meta: dict) -> str:
    rows = []
    for sev_key in ("critical", "high", "medium"):
        tier = tiers[sev_key]
        count = counts[sev_key]
        rows.append(
            f"| {tier['emoji']} {tier['label']} | {count} | {tier['per_bug']} | {tier['subtotal']} |"
        )
    rows.append(f"| **Total** | **{sum(counts.values())}** | \u2014 | **{meta['reward_total']}** |")
    table = "\n".join(rows)
    return f"""## \U0001f4b0 Reward Estimate

| Severity | Count | Per Bug | Subtotal |
|----------|-------|---------|----------|
{table}

---"""


def build_screenshot_section(bugs: list[dict], meta: dict) -> str:
    sections = []
    for bug in bugs:
        sections.append(build_detail_section(bug, meta))
    joined = "\n\n".join(sections)
    return f"""## \U0001f4f8 Bug Screenshots \u2014 Code Evidence

> Each screenshot shows: vulnerable code highlighted in red, suggested fix in green,  
> root cause analysis panel, linked GitHub issue, and reward wallet address.

---

{joined}"""


def build_repo_structure(bugs: list[dict]) -> str:
    file_list = "\n".join(f"    \u251c\u2500\u2500 {b['screenshot']}" for b in bugs[:-1])
    file_list += f"\n    \u2514\u2500\u2500 {bugs[-1]['screenshot']}"
    return f"""## \U0001f4c1 Repository Structure

```
bug-bounty-mec/
\u251c\u2500\u2500 README.md                          \u2190 Generated from bugs.json
\u251c\u2500\u2500 bugs.json                          \u2190 Single source of truth for all bug data
\u251c\u2500\u2500 generate_readme.py                 \u2190 README generator script
\u251c\u2500\u2500 ME_Hub_Bug_Bounty_Report.docx     \u2190 Full DOCX report (all {len(bugs)} bugs)
\u2514\u2500\u2500 screenshots/
{file_list}
```

---"""


def build_references(refs: list[dict]) -> str:
    lines = "\n".join(f'- {r["emoji"]} [{r["label"]}]({r["url"]})' for r in refs)
    return f"""## \U0001f517 References

{lines}

---"""


def build_footer(total: int, prize_pool: str) -> str:
    return f"""<div align="center">

*All {total} vulnerabilities are original findings, verified non-duplicate against issues #1\u2013#1250.*

*Submitted under the META EARTH Bug Bounty Phase I \u2014 Prize Pool: {prize_pool}*

</div>
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate() -> str:
    data = json.loads(DATA_FILE.read_text())
    meta = data["meta"]
    bugs = data["bugs"]
    rounds = data["rounds"]
    tiers = data["reward_tiers"]
    refs = data["references"]

    counts: Counter = Counter()
    for b in bugs:
        counts[b["severity"]] += 1

    round_bugs = {1: [], 2: []}
    for b in bugs:
        round_bugs[b["round"]].append(b)

    sections = [
        build_header(meta, counts),
        "",
        "## \U0001f50d Complete Vulnerability Summary",
        "",
    ]

    for r in rounds:
        idx = rounds.index(r) + 1
        sections.append(build_summary_table(r, round_bugs[idx], meta["target_url"]))
        sections.append("")

    sections.append("---")
    sections.append("")
    sections.append(build_reward_table(counts, tiers, meta))
    sections.append("")
    sections.append(build_screenshot_section(bugs, meta))
    sections.append("")
    sections.append(build_repo_structure(bugs))
    sections.append("")
    sections.append(build_references(refs))
    sections.append("")
    sections.append(build_footer(len(bugs), meta["prize_pool"]))

    return "\n".join(sections)


def main() -> None:
    readme = generate()

    if "--check" in sys.argv:
        if OUTPUT_FILE.exists() and OUTPUT_FILE.read_text() == readme:
            print("README.md is up to date.")
            raise SystemExit(0)
        print("README.md is stale. Run `python generate_readme.py` to regenerate.")
        raise SystemExit(1)

    OUTPUT_FILE.write_text(readme)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
