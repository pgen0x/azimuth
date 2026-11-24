#!/usr/bin/env python3
"""Pulse bot-holder bar: the pipeline's half of PULSE_MAX_BOT_HOLDERS_PCT, plus
the band journal and the report that decides whether a raised bar stays.

The daemon's audit gate (internal/meteora/audit.go) rejects a pulse candidate
whose Jupiter bot-holder share is ABOVE the bar. It ships the bar it used on
each pulse candidate (`pulse_bot_bar_pct`), so the pipeline judges with the
daemon's number even when it runs in another process environment (the Hermes
agent path). Without that field the pipeline reads the same env var, then the
default. Parsing matches the Go side: unset, malformed or out of range
(<= 0 or > 100) means 25.

Penalty: every mode but pulse keeps `bots-15` above 20%. For pulse the gate
IS the bot policy, so the penalty applies only above the bar. A pulse
candidate the gate admitted carries no bot penalty, otherwise a raised bar
would admit 25-30% pools only for `bots-15` to sink them under
`conviction_floor`.

Band journal: pulse entries carry `signal.audit = {bot_pct, bot_band,
bot_bar_pct}`; the monitor copies `signal` onto the close row. Bands are
fixed ("<25", "25-30", ">=30", "unknown") so rows stay comparable whatever
the bar was.

Report (`dlmm_stats.py --bot-band [--since YYYY-MM-DD]`): per band, closes,
realized and wallet-cash SOL, mean per close and its pool-clustered bootstrap
CI, then the kill-rule verdict for the 25-30 band. A re-center child carries
no audit of its own and inherits its root entry's band through
`root_chain_id`.
"""
import json
import math
import os
import random
import statistics
from datetime import datetime, timezone

DEFAULT_PULSE_BAR = 25.0
OTHER_MODES_PENALTY_ABOVE = 20.0
ENV_KEY = "PULSE_MAX_BOT_HOLDERS_PCT"
BANDS = ("<25", "25-30", ">=30", "unknown")
KILL_BAND = "25-30"
KILL_MIN_CLOSES = 15
KILL_SINGLE_LOSS_SOL = -0.03
BOOT = 2000


def parse_bar(value):
    """A bar in (0, 100], else None. Same rule as config.go."""
    try:
        bar = float(value)
    except (TypeError, ValueError):
        return None
    return bar if math.isfinite(bar) and 0 < bar <= 100 else None


def pulse_bot_bar(candidate=None, env=None):
    """The daemon's bar for this candidate, else the env var, else 25."""
    if isinstance(candidate, dict):
        bar = parse_bar(candidate.get("pulse_bot_bar_pct"))
        if bar is not None:
            return bar
    env = os.environ if env is None else env
    bar = parse_bar(env.get(ENV_KEY))
    return DEFAULT_PULSE_BAR if bar is None else bar


def _pct(value):
    if isinstance(value, bool):
        return None
    try:
        pct = float(value)
    except (TypeError, ValueError):
        return None
    return pct if math.isfinite(pct) else None


def bots_penalty(candidate, mode, env=None):
    """True when the candidate takes `bots-15`. Missing data never does (fail-open)."""
    pct = _pct(candidate.get("bot_holders_pct"))
    if pct is None:
        return False
    limit = pulse_bot_bar(candidate, env) if mode == "pulse" else OTHER_MODES_PENALTY_ABOVE
    return pct > limit


def bot_band(pct):
    pct = _pct(pct)
    if pct is None:
        return "unknown"
    if pct < 25:
        return "<25"
    return "25-30" if pct < 30 else ">=30"


def audit_tag(candidate, env=None):
    """The `signal.audit` block journaled on a pulse entry."""
    pct = _pct(candidate.get("bot_holders_pct"))
    return {"bot_pct": pct, "bot_band": bot_band(pct), "bot_bar_pct": pulse_bot_bar(candidate, env)}


# ------------------------------------------------------------------ report

def _rows(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    rows.append(rec)
    except OSError:
        pass
    return rows


def band_of(rec):
    signal = rec.get("signal")
    audit = signal.get("audit") if isinstance(signal, dict) else None
    band = audit.get("bot_band") if isinstance(audit, dict) else None
    return band if band in BANDS else None


def tag_bands(closes):
    """Attach `_bot_band` to each pulse close: its own, else its root entry's."""
    root_band = {}
    for rec in closes:
        band = band_of(rec)
        if band and rec.get("position"):
            root_band[rec["position"]] = band
    out = []
    for rec in closes:
        band = band_of(rec) or root_band.get(rec.get("root_chain_id"))
        if band:
            rec["_bot_band"] = band
            out.append(rec)
    return out


def _finite(v):
    return type(v) in (int, float) and math.isfinite(v)


def cluster_ci(rows, key="pnl_sol", n_boot=BOOT, seed=7):
    """95% CI of the mean per close, resampling whole pools (closes in one pool
    are not independent). None when fewer than two pools."""
    groups = {}
    for r in rows:
        groups.setdefault(r.get("pool") or r.get("position"), []).append(r[key])
    groups = list(groups.values())
    if len(groups) < 2:
        return None
    rng = random.Random(seed)
    means = sorted(statistics.fmean([x for _ in groups for x in rng.choice(groups)]) for _ in range(n_boot))
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1]


def summarize(rows):
    measured = [r for r in rows if r.get("pnl_basis") == "realized" and _finite(r.get("pnl_sol"))]
    cash = [r["cash_realized_sol"] for r in rows
            if r.get("cash_basis") == "wallet" and _finite(r.get("cash_realized_sol"))]
    vals = [r["pnl_sol"] for r in measured]
    return {
        "closes": len(rows),
        "pools": len({r.get("pool") for r in rows}),
        "realized_n": len(vals),
        "unmeasured": len(rows) - len(vals),
        "realized_sol": sum(vals) if vals else None,
        "mean_sol": statistics.fmean(vals) if vals else None,
        "ci": cluster_ci(measured) if vals else None,
        "worst_sol": min(vals) if vals else None,
        "cash_n": len(cash),
        "cash_sol": sum(cash) if cash else None,
    }


def kill_verdict(s):
    """The PR's kill rule for the 25-30 band, on realized SOL."""
    if s["worst_sol"] is not None and s["worst_sol"] < KILL_SINGLE_LOSS_SOL:
        return "REVERT", f"a single close lost {s['worst_sol']:+.4f} SOL (< {KILL_SINGLE_LOSS_SOL})"
    if s["realized_n"] < KILL_MIN_CLOSES:
        return "WAIT", f"{s['realized_n']} realized closes, rule needs {KILL_MIN_CLOSES}"
    if s["realized_sol"] < 0:
        return "REVERT", f"band realized {s['realized_sol']:+.4f} SOL < 0"
    if s["ci"] and s["ci"][1] < 0:
        return "REVERT", f"CI upper bound of mean per close {s['ci'][1]:+.5f} < 0"
    return "KEEP", "no revert condition met"


def since_ts(since):
    if not since:
        return 0
    return int(datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def report(profile_dir, since=None, apply_realized=None):
    """Text report. `apply_realized` is injected by the caller so the realized
    join reads the caller's own profile path (see dlmm_realized.apply_realized)."""
    memories = os.path.join(profile_dir, "memories")
    cutoff = since_ts(since)
    closes = [r for r in _rows(os.path.join(memories, "dlmm_closes.jsonl"))
              if r.get("mode") == "pulse" and not r.get("dry_run") and (r.get("ts") or 0) >= cutoff]
    if apply_realized is not None:
        apply_realized(closes, os.path.join(memories, "dlmm_realized.jsonl"))
    tagged = tag_bands(closes)
    lines = [f"Pulse bot-holder bands since {since or 'the start of the journal'} (UTC): {len(tagged)} tagged "
             f"closes, {len(closes) - len(tagged)} pulse closes without a band (entries before the tag)."]
    lines.append("band     closes pools realized(n)  realized SOL   mean/close  pool-clustered 95% CI     cash(n)   cash SOL")

    def fmt(v, w=12, p=4):
        return f"{v:+{w}.{p}f}" if v is not None else f"{'n/a':>{w}}"

    by_band = {b: summarize([r for r in tagged if r["_bot_band"] == b]) for b in BANDS}
    for band in BANDS:
        s = by_band[band]
        ci = f"[{s['ci'][0]:+.5f}, {s['ci'][1]:+.5f}]" if s["ci"] else "n/a (< 2 pools)"
        lines.append(f"{band:<8} {s['closes']:>6} {s['pools']:>5} {s['realized_n']:>11} {fmt(s['realized_sol'])} "
                     f"{fmt(s['mean_sol'], 12, 5)}  {ci:<24} {s['cash_n']:>7} {fmt(s['cash_sol'], 10)}")
    verdict, why = kill_verdict(by_band[KILL_BAND])
    lines.append(f"Kill rule ({KILL_BAND}): {verdict}: {why}.")
    lines.append(f"Rule: after >= {KILL_MIN_CLOSES} realized closes, revert to 25 if band realized SOL < 0 or the CI "
                 f"upper bound of the mean per close < 0; revert on any single close < {KILL_SINGLE_LOSS_SOL} SOL. "
                 "Unmeasured closes are counted, never read as 0.")
    return "\n".join(lines)
