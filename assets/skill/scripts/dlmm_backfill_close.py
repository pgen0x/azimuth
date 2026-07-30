#!/usr/bin/env python3
"""Journal a close that the monitor executed but failed to record.

dlmm_monitor.py journals a close only on the success branch of the executor
call. When the executor's close chain outlives its subprocess budget the tx can
still land — the position is gone on-chain, the SOL is back, and nothing is
written: no dlmm_closes.jsonl entry, no pool memory, no daily counters. The
trade then under-reports winrate and the pipeline's "past losses" skip gate
never learns about that pool.

close_position() in dlmm_monitor.py now re-checks the chain before believing a
failure, which covers the common case. This script repairs what already slipped
through, and the case that check cannot cover (portfolio API unreachable during
verification, so the close stays unconfirmed).

Reconstruct the numbers from the monitor's own log — the MONITOR_REPORT JSON
line of the cycle that fired the exit carries every field this needs:

    journalctl --user -u azimuth-sol-monitor --since "<exit time>" \
      | grep MONITOR_REPORT | tail -1

Then, e.g.:

    python3 dlmm_backfill_close.py \
      --position HdBALwyq... --pool AeUfFU6L... --pair CHANCE-SOL \
      --base-mint JCKwsT8U... --mode turnover \
      --pnl-pct 0.4723 --pnl-sol -0.000204 \
      --fee-per-tvl 1.27 --age-min 41.1 \
      --closed-at 2026-07-30T02:15:47+07:00 \
      --reason "Trailing Take-Profit hit (Peak: 1.24%, Current: 0.47%)"

`--check-chain` refuses to write while the Meteora portfolio API still lists the
position. Re-running is safe: the position address is the idempotency key.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Three hops up from scripts/ is the profile, exactly like dlmm_monitor.py — but
# only when this file was invoked by its absolute profile-side path. A profile's
# skills/*/scripts/ is usually a SYMLINK into this repo, and os.getcwd() (which
# abspath falls back on for a relative argv[0]) returns the PHYSICAL path, so
# `cd <profile>/skills/solana-dlmm/scripts && python3 dlmm_backfill_close.py`
# derives the repo root instead and reads the wrong .env / journal. Hence
# --profile-dir, and a hard failure below rather than silent misfiling.
DEFAULT_PROFILE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
METEORA_PORTFOLIO_API = "https://dlmm.datapi.meteora.ag/portfolio/open"


def redis(*args):
    res = subprocess.run(["redis-cli", *args], capture_output=True, text=True)
    return res.stdout.strip()


def journal_path(profile_dir):
    return os.path.join(profile_dir, "memories", "dlmm_closes.jsonl")


def wallet_address(profile_dir):
    """Same source of truth as dlmm_monitor.py: the profile .env."""
    try:
        with open(os.path.join(profile_dir, ".env"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("SOLANA_PUBLIC_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return None


def still_open_onchain(pos_addr, profile_dir):
    """True/False when the API answers, None when it cannot be reached."""
    wallet = wallet_address(profile_dir)
    if not wallet:
        return None
    try:
        req = urllib.request.Request(f"{METEORA_PORTFOLIO_API}?user={wallet}",
                                     headers={"User-Agent": "dlmm-lp/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception:
        return None
    for pool_data in (data.get("pools") or []):
        if pos_addr in (pool_data.get("listPositions") or []):
            return True
    return False


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--position", required=True, help="position address (idempotency key)")
    p.add_argument("--pool", required=True)
    p.add_argument("--pair", required=True, help="e.g. CHANCE-SOL")
    p.add_argument("--base-mint", default=None)
    p.add_argument("--mode", default="multiday", help="casual | multiday | turnover")
    p.add_argument("--pnl-pct", type=float, required=True)
    p.add_argument("--pnl-sol", type=float, required=True)
    p.add_argument("--fee-per-tvl", type=float, default=0.0)
    p.add_argument("--age-min", type=float, default=0.0)
    p.add_argument("--reason", required=True)
    p.add_argument("--closed-at", required=True,
                   help="ISO-8601 close time; a bare timestamp is read as local "
                        "time (e.g. 2026-07-30T02:15:47+07:00)")
    p.add_argument("--txs", default="", help="comma-separated tx hashes, if known")
    p.add_argument("--source", default="monitor-backfill",
                   help="journal 'source' field (default monitor-backfill)")
    p.add_argument("--check-chain", action="store_true",
                   help="abort if the portfolio API still lists the position")
    p.add_argument("--profile-dir", default=DEFAULT_PROFILE_DIR,
                   help="Hermes profile dir owning the journal and .env "
                        f"(default {DEFAULT_PROFILE_DIR})")
    p.add_argument("--dry-run", action="store_true",
                   help="print the entry, write nothing")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    profile_dir = os.path.abspath(args.profile_dir)
    if not os.path.isfile(os.path.join(profile_dir, ".env")):
        print(f"❌ no .env under {profile_dir} — that is not a Hermes profile. "
              f"Pass --profile-dir explicitly (a symlinked scripts/ dir breaks "
              f"the default derivation).")
        return 2

    try:
        closed_at = datetime.datetime.fromisoformat(args.closed_at)
    except ValueError as e:
        print(f"❌ --closed-at is not ISO-8601: {e}")
        return 2
    if closed_at.tzinfo is None:
        closed_at = closed_at.astimezone()
    ts = int(closed_at.timestamp())

    if args.check_chain:
        state = still_open_onchain(args.position, profile_dir)
        if state is True:
            print(f"❌ {args.position} is STILL OPEN on-chain — refusing to journal a close.")
            return 3
        if state is None:
            print("⚠️ Portfolio API unreachable — position state unverified, continuing.")

    entry = {
        "ts": ts,
        "timestamp": datetime.datetime.fromtimestamp(
            ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": args.source,
        "pool": args.pool,
        "pair": args.pair,
        "position": args.position,
        "base_mint": args.base_mint,
        "mode": args.mode,
        "pnl_pct": round(args.pnl_pct, 4),
        "pnl_sol": round(args.pnl_sol, 6),
        "fee_per_tvl_24h": round(args.fee_per_tvl, 4),
        "age_min": round(args.age_min, 1),
        "reason": args.reason,
        "txs": [t.strip() for t in args.txs.split(",") if t.strip()],
        "dry_run": False,
        # The entry-time signal snapshot is unrecoverable after the fact; null
        # keeps dlmm_weights.py from learning against invented inputs.
        "signal": None,
    }

    if args.dry_run:
        print(json.dumps(entry, indent=2))
        print("(--dry-run: nothing written)")
        return 0

    # Idempotency: one journal row per position, ever.
    journal = journal_path(profile_dir)
    try:
        with open(journal, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if json.loads(line).get("position") == args.position:
                    print(f"already journaled — {args.position} present, nothing to do")
                    return 0
    except FileNotFoundError:
        os.makedirs(os.path.dirname(journal), exist_ok=True)

    with open(journal, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"journal += {entry['timestamp']} {entry['pair']} "
          f"{entry['pnl_pct']:+.4f}% ({entry['pnl_sol']:+.6f} SOL) — {entry['reason']}")

    # Pool memory — the pipeline's "past losses" skip gate reads this.
    hist_key = f"sol:dlmm:history:pool:{args.pool}"
    redis("lpush", hist_key, json.dumps({
        "ts": ts,
        "pnl_pct": entry["pnl_pct"],
        "pnl_sol": entry["pnl_sol"],
        "mode": entry["mode"],
        "reason": entry["reason"][:80],
    }))
    redis("ltrim", hist_key, "0", "9")
    redis("expire", hist_key, "2592000")
    print(f"pool memory {hist_key} -> len {redis('llen', hist_key)}")

    # Daily counters, keyed on the LOCAL close date like the monitor's own path.
    pnl_key = f"sol:dlmm:pnl:daily:{closed_at.astimezone().strftime('%Y-%m-%d')}"
    cur = redis("hget", pnl_key, "total_sol")
    cur_f = float(cur) if cur and cur != "(nil)" else 0.0
    redis("hset", pnl_key, "total_sol", str(cur_f + entry["pnl_sol"]))
    redis("hincrby", pnl_key, "count_exits", "1")
    if entry["pnl_sol"] < 0:
        redis("hincrby", pnl_key, "count_losses", "1")
    print(f"{pnl_key} -> {redis('hgetall', pnl_key)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
