#!/usr/bin/env python3
"""DLMM fast-cycle scoreboard — the metlex.io/portfolio card for this bot.

Computes the metrics rival bot screenshots brag about (positions/24h, avg
hold, realized profit, volume churned) plus the ones that actually decide
whether the fast-cycle rules earn: fees vs principal change, win rate, per-mode
breakdown, and rebalance-chain PnL per pool (the circuit-breaker's view).

Sources (all ground truth, no LLM):
  * memories/dlmm_realized.jsonl — per-position LP flows, filtered by close time
  * memories/dlmm_closes.jsonl — per-close hold times, modes, reasons
  * Redis                   — open positions, rebalance counters + PnL tallies

Usage:
  python3 dlmm_stats.py [--hours 24] [--send]
"""
import argparse
import json
import os
import subprocess
import time

from dlmm_realized import apply_realized, load_realized
from tz_util import local_time_str

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))


def redis_get(key):
    try:
        out = subprocess.run(["redis-cli", "get", key], capture_output=True,
                             text=True, timeout=5).stdout.strip()
        return None if out in ("", "(nil)") else out
    except Exception:
        return None


def redis_keys(pattern):
    try:
        out = subprocess.run(["redis-cli", "keys", pattern], capture_output=True,
                             text=True, timeout=5).stdout.strip()
        return [k for k in out.splitlines() if k]
    except Exception:
        return []


def redis_scard(key):
    try:
        out = subprocess.run(["redis-cli", "scard", key], capture_output=True,
                             text=True, timeout=5).stdout.strip()
        return int(out) if out.isdigit() else 0
    except Exception:
        return 0


def load_closes(cutoff_ts):
    """Live (non-dry-run) journal closes since cutoff, uniform schema only —
    legacy free-text entries predate the fast-cycle work and lack hold times."""
    path = os.path.join(PROFILE_DIR, "memories", "dlmm_closes.jsonl")
    closes = []
    if not os.path.exists(path):
        return closes
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("dry_run") or rec.get("ts", 0) < cutoff_ts:
                continue
            if rec.get("pnl_sol") is None and rec.get("pnl_pct") is None:
                continue
            closes.append(rec)
    # The journal's pnl_sol is a mark, and a mark can be pure fiction: three
    # closes in the 2026-08-17..18 window booked -1.41 SOL that the chain shows
    # was never lost. Prefer the reconciled on-chain flows wherever they exist
    # (dlmm_realized.py); rows it hasn't fetched keep the mark.
    return apply_realized(closes, os.path.join(PROFILE_DIR, "memories", "dlmm_realized.jsonl"))


def fmt_hold(minutes):
    if minutes is None:
        return "n/a"
    if minutes < 90:
        return f"{minutes:.0f}m"
    return f"{minutes / 60:.1f}h"


def build_card(hours):
    now = time.time()
    cutoff = now - hours * 3600
    closes = load_closes(cutoff)

    f = lambda x: float(x or 0)
    # Portfolio pool totals are lifetime aggregates even with daysBack. A
    # recent lastClosedAt does not put every deposit in that pool in this window.
    flows = [r for r in load_realized(os.path.join(PROFILE_DIR, "memories", "dlmm_realized.jsonl")).values()
             if cutoff <= f(r.get("closed_at")) <= now]
    api_pnl = sum(f(r.get("realized_sol")) for r in flows)
    api_fee = sum(f(r.get("fee_sol")) for r in flows)
    api_dep = sum(f(r.get("deposit_sol")) for r in flows)

    # Say which basis the number is on: "chain" once every close in the window
    # has been reconciled to on-chain flows, otherwise how many are still marks.
    on_chain = sum(1 for c in closes if c.get("pnl_basis") == "realized")
    basis_label = ("chain" if closes and on_chain == len(closes)
                   else f"{on_chain}/{len(closes)} chain" if closes else "journal")

    wins = [c for c in closes if f(c.get("pnl_sol")) > 0]
    losses = [c for c in closes if f(c.get("pnl_sol")) <= 0]
    realized = sum(f(c.get("pnl_sol")) for c in closes)
    holds = [f(c.get("age_min")) for c in closes if c.get("age_min") is not None]
    avg_hold = sum(holds) / len(holds) if holds else None
    win_rate = 100.0 * len(wins) / len(closes) if closes else 0.0

    by_mode = {}
    for c in closes:
        m = c.get("mode") or "unknown"
        d = by_mode.setdefault(m, {"n": 0, "w": 0, "pnl": 0.0, "holds": []})
        d["n"] += 1
        d["w"] += 1 if f(c.get("pnl_sol")) > 0 else 0
        d["pnl"] += f(c.get("pnl_sol"))
        if c.get("age_min") is not None:
            d["holds"].append(f(c.get("age_min")))

    # Rebalance chains: one line per pool that re-centered recently (the count
    # key's 24h rolling TTL bounds this view regardless of --hours).
    chains = []
    for key in redis_keys("sol:dlmm:rebalance_count:*"):
        pool = key.rsplit(":", 1)[-1]
        cnt = redis_get(key)
        pnl = redis_get(f"sol:dlmm:rebalance_pnl:{pool}")
        chains.append((pool, int(cnt) if cnt and cnt.isdigit() else 0,
                       float(pnl) if pnl else 0.0))
    chains.sort(key=lambda c: c[2])

    open_positions = redis_scard("sol:dlmm:active_positions")

    ts_str = local_time_str("%d %b %H:%M %Z")
    lines = [
        f"📊 DLMM Scoreboard — last {hours}h · {ts_str}",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Closes | {len(closes)} ({len(wins)}W/{len(losses)}L · {win_rate:.0f}% win) |",
        f"| Avg hold | {fmt_hold(avg_hold)} |",
        f"| Journal LP PnL ({basis_label}) | {realized:+.4f} SOL |",
    ]
    if flows:
        lines += [
            f"| Cached LP PnL / fees / principal change | {api_pnl:+.4f} / {api_fee:+.4f} / {api_pnl - api_fee:+.4f} SOL |",
            f"| Deposits recycled | {api_dep:.2f} SOL across {len(flows)} cached closes |",
            "| Basis | Position flows; excludes wallet swap/gas costs; principal change is not HODL-relative IL |",
        ]
    else:
        lines.append("| Cached LP flows | n/a (run dlmm_realized.py to reconcile this window) |")
    lines.append("| Portfolio NAV / net ROI | Unmeasured: wallet-wide settlement coverage and asset marks not verified |")
    lines.append(f"| Open positions | {open_positions} |")

    for m in ("turnover", "pulse", "casual", "multiday", "unknown"):
        d = by_mode.get(m)
        if not d:
            continue
        mh = sum(d["holds"]) / len(d["holds"]) if d["holds"] else None
        lines.append(f"| {m} | {d['n']} closes · {d['w']}W · {d['pnl']:+.4f} SOL · hold {fmt_hold(mh)} |")

    if chains:
        lines.append("")
        lines.append("♻️ Pool rebalance counters (rolling TTL; LP marks, not root-chain net PnL):")
        for pool, cnt, pnl in chains:
            lines.append(f"- {pool[:8]}… ×{cnt} · {pnl:+.4f} SOL")
    if not closes and not chains:
        lines.append("")
        lines.append("No closes in window — nothing traded or everything still open.")
    return "\n".join(lines)


def send_card(text):
    """Deliver via `hermes send` (same contract as dlmm_monitor.send_event_alert:
    script-side platform delivery, zero LLM, DLMM_ALERT_TARGET from profile .env)."""
    target = os.environ.get("DLMM_ALERT_TARGET", "telegram")
    if not target:
        return
    import tempfile
    path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
            tf.write(text)
            path = tf.name
        subprocess.run(["hermes", "send", "-t", target, "-f", path, "-q"],
                       timeout=30, capture_output=True)
    except Exception as e:
        print(f"⚠️ Scoreboard delivery failed (non-fatal): {e}")
    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=24, help="Lookback window (default 24)")
    ap.add_argument("--send", action="store_true", help="Also deliver the card via `hermes send`")
    cli = ap.parse_args()

    card = build_card(cli.hours)
    print(card)
    if cli.send:
        send_card(card)


if __name__ == "__main__":
    main()
