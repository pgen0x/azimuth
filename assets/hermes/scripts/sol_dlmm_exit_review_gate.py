#!/usr/bin/env python3
"""Pre-run script for the `sol_dlmm_ai_exit_review` cron job.

Emits the position report, then a wake-gate line the Hermes scheduler reads
(`_parse_wake_gate`): `{"wakeAgent": false}` on the last stdout line skips the
LLM run entirely — no model call, no delivery.

WHY A GATE AT ALL. The review has to run on a short cadence to be useful, and
a short cadence over open positions is otherwise a few hundred model calls a
day, nearly all of them on positions in no danger.

WHY THE BANDS SIT *BEFORE* THE RULE, NOT ON IT. The authoritative loop
(`dlmm_monitor_loop.sh`) evaluates every 20 seconds and closes on the same
tick a rule fires. A review that woke only on `triggered_rules` would always
arrive after the close. So the hold has to be placed while the position is
still merely APPROACHING a rule — these bands are deliberately wider than the
rules in `dlmm_monitor.py`, and each names the rule it front-runs.

Only rules an AI hold can actually suppress are worth waking for. The
emergency floor, the rug-velocity dump, the thin-liquidity exit, a trailing
drop >= 3%, the peak-giveback stop and the underwater fast-out all bypass
holds outright (see the AI HOLD CHECK in dlmm_monitor.py), so a position in one
of those states is not the review's business — the rules have already decided.
The last two are also why no band front-runs a ~-1% position: deferring a speed
rule turns it back into the -3% close it was written to pre-empt.
"""
import json
import os
import subprocess
import sys

SKILL_SCRIPTS = "__PROFILE__/skills/solana-dlmm/scripts"

# Each band front-runs one suppressible rule. Keep the rule's own threshold in
# the comment: when SOUL.md retunes a rule, the band has to move with it or the
# review goes back to arriving late.
YIELD_CHECK_AGE_MIN = 45.0    # rule: low-yield check arms at age 60m
# ...except pulse, whose grace dropped 60m -> 30m on 2026-08-13. Left at 45 the
# band sat BEHIND the rule it front-runs: the 20s loop closes the position at 30m
# and the review would first look at it fifteen minutes later, i.e. never. 20m
# keeps two 5-minute review cycles between waking and the close, which is the
# minimum for a hold to be placed at all.
YIELD_CHECK_AGE_MIN_PULSE = 20.0
YIELD_BAND_FEE_TVL = 1.3      # rule: closes under 1.0% fee/TVL
OOR_BAND_MINUTES = 2.0        # rule: 30m limit, 5m on turnover — 2m catches both
TRAILING_ARM_PCT = 4.0        # rule: trailing arms at peak +5%
DRAWDOWN_BAND_PCT = -5.0      # rule: SL -8%, emergency floor below that


def wants_review(p):
    """The band this position sits in, or None if an AI hold placed now could
    not matter."""
    if p.get("hard_rule"):
        return None  # stop-loss / pumped-away: holds do not apply
    if p.get("ai_hold_active"):
        return None  # already held; re-asking every 5m only re-spends tokens
    if p.get("triggered_rules"):
        return "rule-firing"
    if not p.get("in_range") and p.get("oor_minutes", 0) >= OOR_BAND_MINUTES:
        return "oor"
    yield_age_min = (YIELD_CHECK_AGE_MIN_PULSE if p.get("mode") == "pulse"
                     else YIELD_CHECK_AGE_MIN)
    if (p.get("age_minutes", 0) >= yield_age_min
            and p.get("fee_per_tvl_24h", 0) < YIELD_BAND_FEE_TVL):
        return "low-yield"
    if p.get("trailing_active") or p.get("peak_pnl", 0) >= TRAILING_ARM_PCT:
        return "trailing"
    if p.get("pnl_pct", 0) <= DRAWDOWN_BAND_PCT:
        return "drawdown"
    return None


def main():
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SKILL_SCRIPTS, "dlmm_monitor.py"),
             "--report-only", "--no-enforce"],
            capture_output=True, text=True, timeout=180, cwd=SKILL_SCRIPTS,
        )
        out = proc.stdout or ""
    except Exception as exc:
        # Report the failure and wake nobody — a review with no data is worse
        # than no review, and the 20s rules loop is unaffected either way.
        print(f"exit-review gate: monitor run failed: {exc}")
        print(json.dumps({"wakeAgent": False}))
        return

    print(out.rstrip())

    report = None
    for line in out.splitlines():
        if line.startswith("MONITOR_REPORT:"):
            try:
                report = json.loads(line[len("MONITOR_REPORT:"):])
            except json.JSONDecodeError:
                report = None
    if report is None:
        print("exit-review gate: no MONITOR_REPORT line — skipping review.")
        print(json.dumps({"wakeAgent": False}))
        return

    bands = {}
    for p in report.get("positions", []):
        band = wants_review(p)
        if band:
            bands[p.get("pair", p.get("position", "?"))] = band

    if not bands:
        print("exit-review gate: no position within a reviewable band.")
        print(json.dumps({"wakeAgent": False}))
        return

    print("exit-review gate: " + ", ".join(f"{k} [{v}]" for k, v in bands.items()))
    print(json.dumps({"wakeAgent": True}))


if __name__ == "__main__":
    main()
