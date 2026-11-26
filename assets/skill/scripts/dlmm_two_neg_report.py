#!/usr/bin/env python3
"""Kill-rule report for the pool-cash two-loss materiality floor (rule V5).

Since 2026-11-26 `pool_cash_two_negative` counts a close as a loss only when
it lost at least 0.002 SOL or 0.5% of its deposit, and a proved streak blocks
for 7d after the newer loss (dlmm_pool_cash_gate.py). Entries the old rule
(any negative sign, no decay) would have refused carry
`signal.pool_cash_gate = {"v0_would_block": true}`. The monitor copies
`signal` onto the close row, and a re-center child inherits its root entry's
tag through `root_chain_id`.

Report (`dlmm_stats.py --two-neg [--since YYYY-MM-DD]`): pulse closes split
into the loosened cohort (v0_would_block) and every other pulse close, with
realized and wallet-cash SOL, mean per close and a pool-clustered bootstrap
CI. Kill rule on the cohort: REVERT on any single close below -0.03 SOL, or,
after >= 15 realized closes, when the mean per close is < 0 AND the CI upper
bound is < 0. Revert = set TWO_NEG_FLOOR_LAMPORTS = 1 and
TWO_NEG_FLOOR_DIV = 2**62 in dlmm_pool_cash_gate.py (any negative sign counts
again); the 7d decay stays.
"""
import os

from dlmm_bot_band import _rows, since_ts, summarize

KILL_MIN_CLOSES = 15
KILL_SINGLE_LOSS_SOL = -0.03
COHORTS = ("v0_would_block", "other")


def is_waived(rec):
    signal = rec.get("signal")
    gate = signal.get("pool_cash_gate") if isinstance(signal, dict) else None
    return isinstance(gate, dict) and gate.get("v0_would_block") is True


def tag_cohorts(closes):
    """Attach `_cohort` to each close: waived if it or its root entry was."""
    waived_roots = {rec["position"] for rec in closes if rec.get("position") and is_waived(rec)}
    for rec in closes:
        waived = is_waived(rec) or rec.get("root_chain_id") in waived_roots
        rec["_cohort"] = COHORTS[0] if waived else COHORTS[1]
    return closes


def kill_verdict(s):
    if s["worst_sol"] is not None and s["worst_sol"] < KILL_SINGLE_LOSS_SOL:
        return "REVERT", f"a single close lost {s['worst_sol']:+.4f} SOL (< {KILL_SINGLE_LOSS_SOL})"
    if s["realized_n"] < KILL_MIN_CLOSES:
        return "WAIT", f"{s['realized_n']} realized closes, rule needs {KILL_MIN_CLOSES}"
    if s["mean_sol"] < 0 and s["ci"] and s["ci"][1] < 0:
        return "REVERT", (f"mean per close {s['mean_sol']:+.5f} < 0 and CI upper bound "
                          f"{s['ci'][1]:+.5f} < 0")
    return "KEEP", "no revert condition met"


def report(profile_dir, since=None, apply_realized=None):
    """Text report. `apply_realized` is injected by the caller so the realized
    join reads the caller's own profile path (see dlmm_realized.apply_realized)."""
    memories = os.path.join(profile_dir, "memories")
    cutoff = since_ts(since)
    closes = [r for r in _rows(os.path.join(memories, "dlmm_closes.jsonl"))
              if r.get("mode") == "pulse" and not r.get("dry_run") and (r.get("ts") or 0) >= cutoff]
    if apply_realized is not None:
        apply_realized(closes, os.path.join(memories, "dlmm_realized.jsonl"))
    tag_cohorts(closes)
    lines = [f"Pool-cash two-loss floor (V5) since {since or 'the start of the journal'} (UTC): "
             f"{len(closes)} pulse closes."]
    lines.append("cohort          closes pools realized(n)  realized SOL   mean/close  pool-clustered 95% CI     cash(n)   cash SOL")

    def fmt(v, w=12, p=4):
        return f"{v:+{w}.{p}f}" if v is not None else f"{'n/a':>{w}}"

    stats = {c: summarize([r for r in closes if r["_cohort"] == c]) for c in COHORTS}
    for cohort in COHORTS:
        s = stats[cohort]
        ci = f"[{s['ci'][0]:+.5f}, {s['ci'][1]:+.5f}]" if s["ci"] else "n/a (< 2 pools)"
        lines.append(f"{cohort:<15} {s['closes']:>6} {s['pools']:>5} {s['realized_n']:>11} {fmt(s['realized_sol'])} "
                     f"{fmt(s['mean_sol'], 12, 5)}  {ci:<24} {s['cash_n']:>7} {fmt(s['cash_sol'], 10)}")
    verdict, why = kill_verdict(stats[COHORTS[0]])
    lines.append(f"Kill rule (v0_would_block): {verdict}: {why}.")
    lines.append(f"Rule: revert on any single close < {KILL_SINGLE_LOSS_SOL} SOL; after >= {KILL_MIN_CLOSES} realized "
                 "closes, revert when the mean per close < 0 and its pool-clustered CI upper bound < 0. "
                 "Unmeasured closes are counted, never read as 0.")
    return "\n".join(lines)
