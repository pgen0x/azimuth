#!/usr/bin/env python3
"""Rebuild close rows the monitor never wrote, from finalized close evidence.

A close can land on-chain while the process that sent it dies before
log_close (2026-11-08: the kernel OOM killer, seconds after a close
confirmed). dlmm_accounting.report() already proves those closes: a recorded
close transaction that finalized and deleted the position account, with no row
in dlmm_closes.jsonl (`recovered_closes`). This turns each of them into the
missing journal row, using only facts we hold:

  - the finalized close signature and its block time (the close itself)
  - the entry file (pair, mint, mode, size, strategy, signal, risk sizing)
  - dlmm_realized.jsonl when the reconciler has measured the position

Anything not measured stays null; nothing is guessed from a mark. Rows carry
`recovered_from_evidence: true` and `source: "evidence_backfill"` so every
consumer can tell them apart.

Dry run by default: prints the rows it would append. `--apply` appends each
missing row once; the position address is the idempotency key and is re-read
from the journal immediately before writing. Run it with the profile's own
scripts path, never a repo checkout (see dlmm_realized.apply_realized).
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys

from dlmm_accounting import report
from dlmm_realized import load_realized

SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if __name__ == "__main__" else __file__))
DEFAULT_PROFILE = Path(SCRIPT_DIR).parent.parent.parent
REASON = "Recovered from finalized close evidence (close row lost before journaling)"


def journaled_positions(closes_path):
    seen = set()
    try:
        with open(closes_path, encoding="utf-8") as f:
            for line in f:
                try:
                    position = json.loads(line).get("position")
                except ValueError:
                    continue
                if position:
                    seen.add(position)
    except FileNotFoundError:
        pass
    return seen


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def evidence_rows(profile, as_of=None):
    """Rows for every proved close that dlmm_closes.jsonl does not have."""
    profile = Path(profile)
    memories = profile / "memories"
    ledger = report(profile, as_of=as_of)
    journaled = journaled_positions(memories / "dlmm_closes.jsonl")
    realized = load_realized(str(memories / "dlmm_realized.jsonl"))
    rows = []
    for close in sorted(ledger.get("recovered_closes", []), key=lambda c: (c["ts"], c["position"])):
        position = close["position"]
        if position in journaled:
            continue
        try:
            entry = json.loads((memories / "dlmm_entries" / (position + ".json")).read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(entry, dict) or entry.get("position") != position or entry.get("pool") != close["pool"]:
            continue
        stamp = close["ts"]
        deployed = _number(entry.get("deployed_at"))
        measured = realized.get(position) or {}
        realized_sol = _number(measured.get("realized_sol"))
        rows.append({
            "ts": int(stamp),
            "timestamp": datetime.datetime.fromtimestamp(stamp, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "evidence_backfill",
            "pool": close["pool"],
            "pair": entry.get("pair"),
            "position": position,
            "base_mint": entry.get("base_mint"),
            "mode": entry.get("mode"),
            "pnl_pct": _number(measured.get("realized_pct")) if realized_sol is not None else None,
            "pnl_sol": realized_sol,
            "fee_per_tvl_24h": None,
            "age_min": round((stamp - deployed) / 60.0, 1) if deployed and stamp >= deployed else None,
            "hold_canary_arm": None,
            "reason": REASON,
            "txs": [close["signature"]],
            "dry_run": False,
            "ai_holds": None,
            "signal": entry.get("signal"),
            "event": "exit",
            "peak_pnl": None,
            "trailing_armed": None,
            "unclaimed_fees_sol": None,
            "fee_pace_pct_30m": None,
            "size_sol": entry.get("size_sol"),
            "strategy": entry.get("strategy"),
            "recenter_of": entry.get("recenter_of"),
            "root_chain_id": close.get("root_chain_id") or entry.get("root_chain_id") or position,
            "risk_sizing": entry.get("risk_sizing"),
            "pnl_basis": "realized" if realized_sol is not None else "unmeasured",
            "pnl_currency": "SOL",
            "recovered_from_evidence": True,
        })
    return rows


def apply_rows(profile, rows):
    """Append rows whose position the journal still lacks. Returns the appended rows."""
    closes = Path(profile) / "memories" / "dlmm_closes.jsonl"
    written = []
    for row in rows:
        if row["position"] in journaled_positions(closes):
            continue
        with open(closes, "a", encoding="utf-8") as out:
            out.write(json.dumps(row) + "\n")
            out.flush()
            os.fsync(out.fileno())
        written.append(row)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--position", action="append", help="limit to these positions (repeatable)")
    parser.add_argument("--apply", action="store_true", help="append the rows; default is a dry run")
    args = parser.parse_args(argv)
    rows = evidence_rows(args.profile)
    if args.position:
        rows = [r for r in rows if r["position"] in set(args.position)]
    if not args.apply:
        for row in rows:
            print(json.dumps(row))
        print(f"dry run: {len(rows)} missing close row(s); pass --apply to append", file=sys.stderr)
        return 0
    written = apply_rows(args.profile, rows)
    for row in written:
        print(json.dumps(row))
    print(f"appended {len(written)} close row(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
