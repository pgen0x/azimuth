#!/usr/bin/env python3
"""Report for the shadow coverage study (0.35 live vs 0.40 candidate, pulse sol_bidask).

Joins ``dlmm_geometry_shadow.jsonl`` (entry arms) and
``dlmm_geometry_shadow_obs.jsonl`` (active-bin observations) to the close
journal. Per closed position and arm:

* time_in_range_s — observed seconds the active bin sat inside the arm's range.
  The state at an observation holds until the next one, capped at ``MAX_GAP_S``;
  the uncovered remainder is reported as unobserved, never as in or out.
* fee_proxy — sum of dt x the arm's own BidAsk weight of the active bin (a
  fraction of the ticket; linear weights rising away from the entry bin). A
  PROXY: it ignores pool depth and our own dilution, so it ranks arms, it is not
  SOL. Same pool, same ticks, so pool depth is common to both arms.

Paired diff = candidate - baseline over positions whose arms differ (at a capped
bin step both arms are identical and carry no treatment). The verdict follows
the pre-registration in .orchestra/exp/coverage-shadow-20261104.md.
"""
import argparse
import bisect
import json
import os
import random
import sys
from pathlib import Path

from dlmm_geometry_shadow import ENTRY_FILE, OBS_FILE

MAX_GAP_S = 180.0
MIN_N, MIN_POOLS, MIN_DAYS = 30, 10, 7
BOOT = 10000


def _rows(path):
    try:
        from dlmm_retention import archived_rows
    except ImportError:
        archived_rows = None
    if archived_rows is not None:
        yield from archived_rows(path)
        return
    if Path(path).exists():
        with open(path) as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)


def safe_rows(path):
    """Rows that parse; a corrupt journal is counted, not fatal."""
    out, bad = [], 0
    try:
        for row in _rows(path):
            if isinstance(row, dict):
                out.append(row)
            else:
                bad += 1
    except (ValueError, OSError):
        bad += 1
    return out, bad


def bidask_weight(arm, anchor, active_bin):
    """Own share of the ticket in ``active_bin`` under linear BidAsk weights."""
    lower, upper = arm["lower_bin"], arm["upper_bin"]
    if not lower <= active_bin <= upper:
        return 0.0
    n = upper - lower  # ladder bins; distances 0..n from the anchor
    d = abs(active_bin - anchor)
    return (d + 1) / ((n + 1) * (n + 2) / 2.0)


def score_position(entry, obs, close_ts):
    """Per-arm time-in-range / fee proxy over [entry ts, close ts]."""
    anchor = entry["active_bin"]
    points = [(entry["ts"], anchor)] + [(o["ts"], o["active_bin"]) for o in obs
                                        if entry["ts"] < o["ts"] <= close_ts]
    points.sort()
    out = {name: dict(time_in_range_s=0.0, fee_proxy=0.0) for name in entry["arms"]}
    observed = 0.0
    for i, (ts, active) in enumerate(points):
        end = points[i + 1][0] if i + 1 < len(points) else close_ts
        dt = max(0.0, min(end - ts, MAX_GAP_S))
        observed += dt
        for name, arm in entry["arms"].items():
            if arm["lower_bin"] <= active <= arm["upper_bin"]:
                out[name]["time_in_range_s"] += dt
            out[name]["fee_proxy"] += dt * bidask_weight(arm, anchor, active)
    life = max(0.0, close_ts - entry["ts"])
    return dict(arms=out, lifetime_s=life, observed_s=observed,
                unobserved_s=max(0.0, life - observed), n_obs=len(points) - 1)


def bootstrap_ci(values, seed=0, n=BOOT):
    if not values:
        return None, None, None
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, None, None
    rng = random.Random(seed)
    k = len(values)
    means = sorted(sum(values[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return mean, means[int(0.025 * n)], means[int(0.975 * n) - 1]


def build(memories, mode="pulse", closes_name="dlmm_closes.jsonl"):
    entries, bad_e = safe_rows(os.path.join(memories, ENTRY_FILE))
    obs, bad_o = safe_rows(os.path.join(memories, OBS_FILE))
    closes, bad_c = safe_rows(os.path.join(memories, closes_name))
    by_pos = {}
    for o in obs:
        if o.get("kind") == "obs" and type(o.get("active_bin")) is int and isinstance(o.get("ts"), (int, float)):
            by_pos.setdefault(o.get("position"), []).append(o)
    close_ts = {}
    for c in closes:
        # dlmm_closes.jsonl rows carry no success flag; compound rows are not closes.
        pos, ts = c.get("position"), c.get("ts")
        if c.get("event") in (None, "exit") and pos and isinstance(ts, (int, float)):
            close_ts.setdefault(pos, []).append(ts)
    for v in close_ts.values():
        v.sort()
    eligible = [e for e in entries if e.get("kind") == "entry" and e.get("schema") == 1
                and e.get("mode") == mode and not e.get("dry_run") and type(e.get("active_bin")) is int
                and isinstance(e.get("ts"), (int, float)) and isinstance(e.get("arms"), dict)]
    entry_pos = {e["position"] for e in eligible}
    rows, open_n = [], 0
    for e in eligible:
        times = close_ts.get(e["position"], [])
        i = bisect.bisect_left(times, e["ts"])
        if i == len(times):
            open_n += 1
            continue
        s = score_position(e, by_pos.get(e["position"], []), times[i])
        rows.append(dict(position=e["position"], pool=e.get("pool"), bin_step=e.get("bin_step"),
                         day=int(e["ts"] // 86400), arms_identical=bool(e.get("arms_identical")),
                         live_matches_baseline=e.get("live_matches_baseline"), anchor=e.get("anchor"), **s))
    treated = [r for r in rows if not r["arms_identical"]]
    d_fee = [r["arms"]["candidate"]["fee_proxy"] - r["arms"]["baseline"]["fee_proxy"] for r in treated]
    d_tir = [r["arms"]["candidate"]["time_in_range_s"] - r["arms"]["baseline"]["time_in_range_s"] for r in treated]
    n, pools, days = len(treated), len({r["pool"] for r in treated}), len({r["day"] for r in treated})
    fee = bootstrap_ci(d_fee)
    tir = bootstrap_ci(d_tir)
    if n < MIN_N or pools < MIN_POOLS or days < MIN_DAYS:
        verdict = "NEED-DATA"
    elif fee[1] is not None and fee[1] > 0 and tir[0] >= 0:
        verdict = "PROPOSE-CANARY"
    elif fee[2] is not None and fee[2] <= 0:
        verdict = "KILL"
    else:
        verdict = "NO-EVIDENCE"
    life = sum(r["lifetime_s"] for r in rows)
    return dict(
        mode=mode, verdict=verdict, gate=dict(min_n=MIN_N, min_pools=MIN_POOLS, min_days=MIN_DAYS),
        entries=len(eligible), open_positions=open_n, closed=len(rows), treated=n, pools=pools, days=days,
        identical_arms=len(rows) - n,
        live_mismatch=sum(1 for r in rows if r["live_matches_baseline"] is False),
        unanchored_obs_positions=len(set(by_pos) - entry_pos),
        unobserved_fraction=(sum(r["unobserved_s"] for r in rows) / life) if life else None,
        corrupt_rows=dict(entry=bad_e, obs=bad_o, closes=bad_c),
        d_fee_proxy=dict(mean=fee[0], ci95=[fee[1], fee[2]]),
        d_time_in_range_s=dict(mean=tir[0], ci95=[tir[1], tir[2]]),
        positions=rows)


def default_profile():
    # abspath, not realpath: the profile's scripts dir is a symlink into the repo.
    return os.environ.get("DLMM_PROFILE_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(sys.argv[0])))))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--profile", default=None, help="Hermes profile dir (default: derived from argv[0])")
    ap.add_argument("--mode", default="pulse")
    ap.add_argument("--json", action="store_true", help="full JSON incl. per-position rows")
    args = ap.parse_args(argv)
    report = build(os.path.join(args.profile or default_profile(), "memories"), mode=args.mode)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    print(json.dumps({k: v for k, v in report.items() if k != "positions"}, indent=2, sort_keys=True))
    if report["verdict"] == "NEED-DATA":
        print(f"NEED-DATA: treated n={report['treated']}/{MIN_N}, pools={report['pools']}/{MIN_POOLS}, "
              f"days={report['days']}/{MIN_DAYS} — CI is not evidence yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
