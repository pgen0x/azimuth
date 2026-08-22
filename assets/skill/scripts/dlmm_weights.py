#!/usr/bin/env python3
"""Darwinian signal weighting — learn which entry signals predict winners.

Reads the close journal (memories/dlmm_closes.jsonl), splits closed positions
into wins/losses, and computes each entry signal's predictive lift (normalized
win-mean minus loss-mean). Each signal's weight is then pulled part-way toward
a target derived from that lift, clamped to [0.3, 2.5]. Weights persist to
memories/signal_weights.json and to Redis (sol:dlmm:signal_weights) where the
deploy pick reads them to prioritize candidates whose strongest attributes
carry high weights.

Runs from the tail of dlmm_monitor.py on every cycle; self-guards so a real
recalc happens at most every RECALC_GUARD_SECS and only with enough samples.

Two design choices, both corrections of the original scheme (audited
2026-08-13, after 108 recalcs had left 10 of 14 weights sitting exactly on a
clamp):

1. **A weight is a function of the current lift, not of its own history.** The
   original applied a x1.05 / x0.95 ratchet to the top and bottom quartile of
   each recalc. Compounding over stable quartile membership has exactly one
   destination — the rails — after which the learner is a frozen preference
   list that no amount of new evidence can move. Here the lift names a TARGET
   and the weight steps SMOOTHING of the way toward it, so every weight is
   mean-reverting: evidence that fades returns the weight to neutral, and
   saturation would need |lift| to hold above (CEILING-1)/LIFT_GAIN forever.

2. **Only signals the pick actually applies are learned.** The scored set here
   must equal WEIGHTED_SIGNALS_HIGHER_IS_BETTER in dlmm_pipeline.py. Six
   non-directional signals (volatility, mcap, tvl, fee_pct, swap_count,
   bot_holders_pct) used to be ranked here and skipped there — and because
   their lift was passed through abs(), it was never negative, so they
   systematically crowded the boost quartile and pushed the signals that DO
   score toward the floor. They are retired below and pruned from stored
   state. Re-adding a signal here means teaching the pipeline to apply it, not
   just appending a name.
"""
import argparse
import json
import os
import subprocess
import time

from dlmm_realized import apply_realized

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
CLOSES_PATH = os.path.join(PROFILE_DIR, "memories", "dlmm_closes.jsonl")
WEIGHTS_PATH = os.path.join(PROFILE_DIR, "memories", "signal_weights.json")
REDIS_WEIGHTS_KEY = "sol:dlmm:signal_weights"

WINDOW_DAYS = 60
MIN_SAMPLES = 10
WEIGHT_FLOOR = 0.3
WEIGHT_CEILING = 2.5
RECALC_GUARD_SECS = 6 * 3600

# lift -> weight target: target = 1.0 + LIFT_GAIN * lift, then clamped. Lift is
# a difference of two min-max-normalized means, so it lives in [-1, 1] but in
# practice runs +/-0.3; a gain of 3 turns that working range into roughly
# [0.1, 1.9] and reserves the clamps for genuinely extreme separation.
LIFT_GAIN = 3.0
# Fraction of the distance to the target taken per recalc. Below 1.0 so a
# single unlucky window cannot reprice a signal, and so the series is an EMA
# over recent lifts rather than a step function.
SMOOTHING = 0.35

# Must stay equal to WEIGHTED_SIGNALS_HIGHER_IS_BETTER in dlmm_pipeline.py —
# every name here is applied by the deploy pick, and every name it applies is
# learned here. All are directional (higher = better candidate), so lift keeps
# its sign throughout; there is no abs() anywhere in this file.
SIGNAL_NAMES = [
    "score", "organic_score", "fee_tvl_ratio", "fee_active_tvl_ratio",
    "holders", "volume_tvl_ratio", "unique_traders", "global_fees_sol",
]

# Learned and stored until 2026-08-13, applied by nothing. Pruned from state on
# the next recalc so `--show` stops implying the pick reads them — notably
# `bot_holders_pct: 2.5` never made the bot prefer bot-heavy pools, but read
# exactly like it did.
RETIRED_SIGNALS = [
    "volatility", "mcap", "tvl", "fee_pct", "swap_count", "bot_holders_pct",
]


def run_command(cmd, timeout=10):
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return out.stdout.strip()
    except Exception:
        return ""


def load_weights():
    if os.path.exists(WEIGHTS_PATH):
        try:
            with open(WEIGHTS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"weights": {}, "last_recalc": None, "last_recalc_ts": 0, "recalc_count": 0, "history": []}


def save_weights(data):
    os.makedirs(os.path.dirname(WEIGHTS_PATH), exist_ok=True)
    with open(WEIGHTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # Best-effort Redis mirror — this is what the deploy pick reads.
    compact = json.dumps({
        "weights": data["weights"],
        "lifts": data.get("lifts") or {},
        "last_recalc": data["last_recalc"],
    })
    run_command(f"redis-cli set \"{REDIS_WEIGHTS_KEY}\" '{compact}'")


def load_recent_closes():
    if not os.path.exists(CLOSES_PATH):
        return []
    cutoff = time.time() - WINDOW_DAYS * 86400
    records = []
    with open(CLOSES_PATH, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("dry_run"):
                continue
            if not isinstance(rec.get("signal"), dict):
                continue  # pre-snapshot records can't be attributed
            if (rec.get("ts") or 0) < cutoff:
                continue
            records.append(rec)
    # Learn against money, not against the monitor's last mark — a phantom
    # -100% close would otherwise teach the weights that whatever signals that
    # position carried predict a total loss (dlmm_realized.py).
    return apply_realized(records, os.path.join(PROFILE_DIR, "memories", "dlmm_realized.jsonl"))


def outcome_sol(rec):
    if rec.get("pnl_sol") is not None:
        return float(rec["pnl_sol"])
    return float(rec.get("pnl_pct") or 0)


def numeric_lift(signal, wins, losses):
    """Signed separation between winners and losers on one signal, in [-1, 1].

    Positive = winners carried a higher value, which for every signal in
    SIGNAL_NAMES is the direction the pick already rewards. Negative is a real
    and useful answer (the attribute anti-predicts), so the sign is never
    discarded. Returns None when the window cannot support a read."""
    win_vals = [float(r["signal"][signal]) for r in wins
                if isinstance(r["signal"].get(signal), (int, float))]
    loss_vals = [float(r["signal"][signal]) for r in losses
                 if isinstance(r["signal"].get(signal), (int, float))]
    if not win_vals or not loss_vals or len(win_vals) + len(loss_vals) < MIN_SAMPLES:
        return None
    all_vals = win_vals + loss_vals
    lo, hi = min(all_vals), max(all_vals)
    if hi == lo:
        return 0.0
    norm = lambda v: (v - lo) / (hi - lo)
    win_mean = sum(map(norm, win_vals)) / len(win_vals)
    loss_mean = sum(map(norm, loss_vals)) / len(loss_vals)
    return win_mean - loss_mean


def target_weight(lift):
    """Where this lift says the weight belongs, independent of where it is now.

    `lift is None` means the window produced no read for that signal, which is
    evidence of nothing rather than evidence against — so the target is
    neutral and the weight drifts back to 1.0 instead of holding whatever it
    last happened to reach."""
    target = 1.0 if lift is None else 1.0 + LIFT_GAIN * lift
    return max(WEIGHT_FLOOR, min(WEIGHT_CEILING, target))


def recalculate(quiet=False):
    data = load_weights()
    weights = data.get("weights") or {}
    dropped = [name for name in RETIRED_SIGNALS if name in weights]
    for name in dropped:
        del weights[name]
    for name in SIGNAL_NAMES:
        weights.setdefault(name, 1.0)

    recent = load_recent_closes()
    wins = [r for r in recent if outcome_sol(r) > 0]
    losses = [r for r in recent if outcome_sol(r) <= 0]
    if len(recent) < MIN_SAMPLES or not wins or not losses:
        if not quiet:
            print(f"Skipping recalc: {len(recent)} attributable closes in {WINDOW_DAYS}d "
                  f"(need >= {MIN_SAMPLES} with both wins and losses)")
        return False

    lifts = {signal: numeric_lift(signal, wins, losses) for signal in SIGNAL_NAMES}
    if all(v is None for v in lifts.values()):
        # A total read failure is an outage, not a verdict — decaying every
        # weight to neutral here would let one bad window erase the learning.
        if not quiet:
            print("Skipping recalc: no signal had enough samples")
        return False

    changes = []
    for signal in SIGNAL_NAMES:
        lift = lifts[signal]
        prev = weights[signal]
        nxt = round(prev + SMOOTHING * (target_weight(lift) - prev), 3)
        if nxt != prev:
            changes.append({
                "signal": signal, "from": prev, "to": nxt,
                "lift": None if lift is None else round(lift, 3),
            })
            weights[signal] = nxt

    now = time.time()
    data["weights"] = weights
    # Published so the daily proposal job can read WHY a weight sits where it
    # does. A weight alone cannot distinguish "no evidence" from "evidence of
    # no effect" — both land near 1.0 — and an agent proposing thresholds off
    # that ambiguity proposes noise.
    data["lifts"] = {k: (None if v is None else round(v, 4)) for k, v in lifts.items()}
    data["last_recalc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    data["last_recalc_ts"] = int(now)
    data["recalc_count"] = (data.get("recalc_count") or 0) + 1
    if changes or dropped:
        entry = {
            "timestamp": data["last_recalc"],
            "changes": changes,
            "window_size": len(recent),
            "wins": len(wins),
            "losses": len(losses),
        }
        if dropped:
            entry["retired"] = dropped
        data.setdefault("history", []).append(entry)
        data["history"] = data["history"][-20:]
    save_weights(data)

    if not quiet:
        if dropped:
            print(f"Retired {len(dropped)} unapplied signal(s): {', '.join(dropped)}")
        print(f"Recalculated from {len(recent)} closes ({len(wins)}W/{len(losses)}L): "
              f"{len(changes)} weight(s) adjusted")
        for c in changes:
            lift = "no read" if c["lift"] is None else f"lift {c['lift']:+.3f}"
            print(f"  {c['signal']}: {c['from']} -> {c['to']} ({lift})")
    return True


def main():
    parser = argparse.ArgumentParser(description="Recalculate darwinian signal weights")
    parser.add_argument("--quiet", action="store_true", help="suppress output (cron mode)")
    parser.add_argument("--force", action="store_true", help="ignore the recalc-interval guard")
    parser.add_argument("--show", action="store_true", help="print current weights and exit")
    cli = parser.parse_args()

    if cli.show:
        data = load_weights()
        weights = data.get("weights") or {}
        lifts = data.get("lifts") or {}
        # Weight and lift side by side: a weight near 1.0 is either an
        # unmeasured signal or a measured-and-irrelevant one, and only the lift
        # column separates the two.
        for name in sorted(weights):
            lift = lifts.get(name)
            shown = "  (no read)" if lift is None else f"  (lift {lift:+.4f})"
            retired = "  [RETIRED — not applied by the pick]" if name in RETIRED_SIGNALS else ""
            print(f"{name:<24} {weights[name]:>6.3f}{shown}{retired}")
        print(f"last_recalc: {data.get('last_recalc') or 'never'} "
              f"(recalc_count {data.get('recalc_count') or 0})")
        return

    if not cli.force:
        last = load_weights().get("last_recalc_ts") or 0
        if time.time() - last < RECALC_GUARD_SECS:
            if not cli.quiet:
                print(f"Recalc guard: last run {int((time.time() - last) / 60)}m ago "
                      f"(interval {RECALC_GUARD_SECS // 3600}h). Use --force to override.")
            return

    recalculate(quiet=cli.quiet)


if __name__ == "__main__":
    main()
