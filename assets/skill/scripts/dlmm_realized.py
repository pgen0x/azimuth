#!/usr/bin/env python3
"""Realized-PnL reconciliation for the Solana DLMM close journal.

WHY THIS EXISTS. `dlmm_closes.jsonl` records what the monitor BELIEVED at the
moment it closed — a Portfolio-API mark read one tick before the close tx. That
mark is not money, and it is sometimes not even close: three closes on
2026-08-17..18 were booked at -100.00% / -1.41 SOL while the on-chain flows show
every deposit returned in full (see SUSPECT_PNL_MIN_AGE_MINUTES in
dlmm_monitor.py). Everything downstream — the scoreboard, the weight learner,
the daily proposal brief — reads that number and inherits the lie.

This pass writes the arbiter next to the journal: per closed position, the
on-chain flows Meteora aggregates (deposit / withdrawal / fees, all in SOL), so
`realized_sol = withdrawal + fees - deposit` carries no price opinion of ours.

  memories/dlmm_realized.jsonl   one line per position address, append-only,
                                 idempotent (a position is fetched once)

Consumers join on `position` and prefer `realized_sol` over the journal's
`pnl_sol`; a position the API has not indexed yet is simply absent, which is
"unmeasurable", never 0.0.

Usage:
  python3 dlmm_realized.py                 # backfill the last 7 days
  python3 dlmm_realized.py --days 30
  python3 dlmm_realized.py --check         # report journal-vs-realized divergence
  python3 dlmm_realized.py --check --days 7
"""
import argparse
import json
import os
import time
import urllib.request

PORTFOLIO_API = "https://dlmm.datapi.meteora.ag/portfolio"
POSITIONS_API = "https://dlmm.datapi.meteora.ag/positions"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
CLOSES_PATH = os.path.join(PROFILE_DIR, "memories", "dlmm_closes.jsonl")
REALIZED_PATH = os.path.join(PROFILE_DIR, "memories", "dlmm_realized.jsonl")

# A journal row this far underwater is the not-yet-indexed API artifact until the
# on-chain flows say otherwise — same threshold the monitor guards on.
SUSPECT_PNL_PCT = -90.0


def get_wallet_address():
    try:
        with open(os.path.join(PROFILE_DIR, ".env")) as f:
            for line in f:
                if line.startswith("SOLANA_PUBLIC_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except Exception:
        pass
    return os.environ.get("SOLANA_PUBLIC_KEY")


def _get(url, tries=3):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dlmm-lp/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as exc:  # transient datapi 5xx/timeouts are the norm
            last = exc
            if attempt < tries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last


def _f(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_realized(path=REALIZED_PATH):
    """{position_address: record} — the join key every consumer uses."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pos = rec.get("position")
            if pos:
                out[pos] = rec  # a later line supersedes an earlier one
    return out


def apply_realized(records, path=None):
    """Rewrite journal closes in place onto on-chain flows where we have them.

    PASS `path` FROM THE CALLER. This module's own REALIZED_PATH is only correct
    when it is the __main__ script: the profile's `skills/solana-dlmm/scripts`
    is a SYMLINK into this repo, and Python resolves symlinks when it builds
    sys.path[0], so an IMPORTED copy computes PROFILE_DIR as the repo checkout
    and silently joins against a file that does not exist — every close comes
    back "mark" with no error anywhere. Callers are the __main__ script, so
    their own PROFILE_DIR is the honest one.

    `pnl_sol`/`pnl_pct` in the journal are the monitor's MARK one tick before the
    close; this swaps in what the position actually paid and stamps `pnl_basis`
    so a consumer can tell the two apart. Records with no realized row keep the
    mark and are stamped "mark" — unmeasured, not zero. Mutates and returns the
    same list, so callers can drop it into an existing load path.
    """
    realized = load_realized(path or REALIZED_PATH)
    for rec in records:
        got = realized.get(rec.get("position"))
        if not got:
            rec.setdefault("pnl_basis", "mark")
            continue
        rec["pnl_sol"] = got.get("realized_sol")
        rec["pnl_pct"] = got.get("realized_pct")
        rec["pnl_basis"] = "realized"
    return records


def fetch_pools(wallet):
    """Every pool the wallet has ever touched (daysBack is ignored by the API)."""
    pools, page = [], 1
    while True:
        data = _get(f"{PORTFOLIO_API}?user={wallet}&page={page}&pageSize=50")
        pools += data.get("pools") or []
        if not data.get("hasNext"):
            return pools
        page += 1


def fetch_closed_positions(wallet, pool):
    positions, page = [], 1
    while True:
        data = _get(f"{POSITIONS_API}/{pool}/pnl?user={wallet}&status=closed"
                    f"&pageSize=100&page={page}")
        positions += data.get("positions") or []
        if not data.get("hasNext"):
            return positions
        page += 1


def backfill(wallet, days, quiet=False):
    """Fetch every position closed inside the window that we have not stored yet."""
    cutoff = int(time.time()) - int(days * 86400)
    known = load_realized()
    pools = fetch_pools(wallet)
    # A pool whose LAST close predates the window cannot hold a close inside it.
    recent = [p for p in pools if int(p.get("lastClosedAt") or 0) >= cutoff]
    written = 0
    os.makedirs(os.path.dirname(REALIZED_PATH), exist_ok=True)
    with open(REALIZED_PATH, "a", encoding="utf-8") as out:
        for pool in recent:
            addr = pool.get("poolAddress")
            pair = f'{pool.get("tokenX")}-{pool.get("tokenY")}'
            try:
                positions = fetch_closed_positions(wallet, addr)
            except Exception as exc:
                if not quiet:
                    print(f"⚠️ {pair}: positions fetch failed ({exc}) — left unmeasured")
                continue
            for pos in positions:
                closed_at = int(pos.get("closedAt") or 0)
                pos_addr = pos.get("positionAddress")
                if closed_at < cutoff or not pos_addr or pos_addr in known:
                    continue
                dep = _f(pos.get("allTimeDeposits", {}).get("total", {}).get("sol"))
                wdr = _f(pos.get("allTimeWithdrawals", {}).get("total", {}).get("sol"))
                fee = _f(pos.get("allTimeFees", {}).get("total", {}).get("sol"))
                rec = {
                    "position": pos_addr,
                    "pool": addr,
                    "pair": pair,
                    "closed_at": closed_at,
                    "created_at": int(pos.get("createdAt") or 0),
                    "deposit_sol": round(dep, 9),
                    "withdrawal_sol": round(wdr, 9),
                    "fee_sol": round(fee, 9),
                    # The API's own figure; equals withdrawal + fees - deposit, so no
                    # price opinion of ours can enter it.
                    "realized_sol": round(_f(pos.get("pnlSol")), 9),
                    "realized_pct": round(_f(pos.get("pnlSolPctChange")), 4),
                    "source": "meteora_datapi_flows",
                    "fetched_at": int(time.time()),
                }
                out.write(json.dumps(rec) + "\n")
                known[pos_addr] = rec
                written += 1
    if not quiet:
        print(f"✅ realized: +{written} positions ({len(recent)} pools touched in {days}d, "
              f"{len(known)} stored total) → {REALIZED_PATH}")
    return written


def load_closes(days):
    cutoff = int(time.time()) - int(days * 86400)
    rows = []
    if not os.path.exists(CLOSES_PATH):
        return rows
    with open(CLOSES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event") != "exit" or rec.get("dry_run"):
                continue
            if int(rec.get("ts") or 0) >= cutoff:
                rows.append(rec)
    return rows


def check(days):
    """What the journal claims vs what the chain paid, over the window."""
    realized = load_realized()
    closes = load_closes(days)
    matched, unmatched = [], []
    for rec in closes:
        got = realized.get(rec.get("position"))
        (matched if got else unmatched).append((rec, got))
    j_sum = sum(_f(r.get("pnl_sol")) for r, _ in matched)
    r_sum = sum(_f(g.get("realized_sol")) for _, g in matched)
    print(f"window {days}d — {len(closes)} journal closes, {len(matched)} reconciled, "
          f"{len(unmatched)} not yet indexed")
    print(f"  journal  pnl_sol : {j_sum:+.4f} SOL")
    print(f"  realized (chain) : {r_sum:+.4f} SOL")
    print(f"  divergence       : {r_sum - j_sum:+.4f} SOL")
    worst = sorted(matched,
                   key=lambda m: abs(_f(m[1].get("realized_sol")) - _f(m[0].get("pnl_sol"))),
                   reverse=True)[:10]
    if worst:
        print("\n  biggest divergences (journal → realized):")
        for rec, got in worst:
            delta = _f(got.get("realized_sol")) - _f(rec.get("pnl_sol"))
            if abs(delta) < 1e-6:
                continue
            flag = " ⚠️ PHANTOM" if _f(rec.get("pnl_pct")) <= SUSPECT_PNL_PCT else ""
            print(f"   {rec.get('pair','?')[:18]:18} {_f(rec.get('pnl_sol')):+.4f} → "
                  f"{_f(got.get('realized_sol')):+.4f} SOL ({delta:+.4f}) "
                  f"{(rec.get('reason') or '')[:44]}{flag}")
    phantom = [(r, g) for r, g in matched if _f(r.get("pnl_pct")) <= SUSPECT_PNL_PCT]
    if phantom:
        fake = sum(_f(g.get("realized_sol")) - _f(r.get("pnl_sol")) for r, g in phantom)
        print(f"\n  {len(phantom)} suspect-read rows booked {fake:+.4f} SOL that never happened")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=7.0)
    ap.add_argument("--check", action="store_true", help="report divergence, no fetch")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.check:
        wallet = get_wallet_address()
        if not wallet:
            print("❌ no SOLANA_PUBLIC_KEY in profile .env or environment")
            return 1
        backfill(wallet, args.days, quiet=args.quiet)
    check(args.days)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
