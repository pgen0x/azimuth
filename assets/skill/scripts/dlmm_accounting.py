#!/usr/bin/env python3
"""Read recorded cash flows by root chain; never promote partial flows to NAV.

Run through the profile symlink so its memories directory is selected:
  python3 .../skills/solana-dlmm/scripts/dlmm_accounting.py --refresh
Only --refresh calls RPC (read-only). Historical unrecorded costs stay unknown.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from dlmm_realized import load_realized

SCRIPT_DIR = Path(os.path.abspath(__file__)).parent
PROFILE_DIR = SCRIPT_DIR.parent.parent.parent


def rows(path):
    if not path.exists():
        return []
    # Corruption must be visible; silently skipping it understates cash flows.
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def report(profile):
    memories = Path(profile) / "memories"
    events = rows(memories / "dlmm_transactions.jsonl")
    facts = {r["signature"]: r for r in rows(memories / "dlmm_transaction_facts.jsonl")}
    closes = {r["position"]: r for r in rows(memories / "dlmm_closes.jsonl")
              if r.get("position") and not r.get("dry_run")}
    entries = {}
    for file in (memories / "dlmm_entries").glob("*.json"):
        entry = json.loads(file.read_text())
        entries[entry["position"]] = entry
    realized = load_realized(str(memories / "dlmm_realized.jsonl"))
    chains = {}

    def chain(root):
        return chains.setdefault(root, {"root_chain_id": root, "positions": set(),
            "recorded_signatures": set(), "pending_signatures": [], "wallet_delta_lamports": 0,
            "network_fee_lamports": 0, "reconciled_transactions": 0, "failed_transactions": 0, "token_deltas_raw": {},
            "last_activity": 0, "lp_pnl_sol": 0.0, "lp_unmeasured_positions": [], "reasons": []})

    position_roots = {}
    for position in entries.keys() | closes.keys():
        metadata = {**closes.get(position, {}), **entries.get(position, {})}
        root = metadata.get("root_chain_id") or metadata.get("recenter_of") or position
        position_roots[position] = root
        c = chain(root)
        c["positions"].add(position)
        c["last_activity"] = max(c["last_activity"], metadata.get("ts") or 0, metadata.get("deployed_at") or 0)

    seen = {}
    for event in events:
        signature = event["signature"]
        # A retry can repeat a journal line. Conflicting attribution is an error.
        identity = (event.get("wallet"), event.get("position"), event.get("root_chain_id"))
        if signature in seen:
            if seen[signature] != identity:
                raise ValueError("Conflicting signature attribution: " + signature)
            continue
        seen[signature] = identity
        root = position_roots.get(event.get("position")) or event.get("root_chain_id") or "unattributed"
        c = chain(root)
        c["recorded_signatures"].add(signature)
        c["last_activity"] = max(c["last_activity"], event.get("ts") or 0)
        if event.get("position"):
            c["positions"].add(event["position"])
        fact = facts.get(signature)
        if fact is None or fact.get("wallet") != event.get("wallet"):
            c["pending_signatures"].append(signature)
            continue
        c["reconciled_transactions"] += 1
        c["wallet_delta_lamports"] += fact["wallet_delta_lamports"]
        c["network_fee_lamports"] += fact["fee_lamports"]
        c["failed_transactions"] += int(fact["failed"])
        for mint, amount in fact["token_deltas_raw"].items():
            c["token_deltas_raw"][mint] = c["token_deltas_raw"].get(mint, 0) + int(amount)

    for c in chains.values():
        for position in sorted(c["positions"]):
            lp = realized.get(position)
            if lp is not None and lp.get("realized_sol") is not None:
                c["lp_pnl_sol"] += lp["realized_sol"]
            else:
                c["lp_unmeasured_positions"].append(position)
        c["positions"] = sorted(c["positions"])
        c["recorded_signatures"] = sorted(c["recorded_signatures"])
        c["token_deltas_raw"] = {m: str(v) for m, v in c["token_deltas_raw"].items() if v}
        if c["pending_signatures"]:
            c["reasons"].append("unresolved_transactions")
        if any(p not in closes for p in c["positions"]):
            c["reasons"].append("open_or_unjournaled_positions")
        if c["token_deltas_raw"]:
            c["reasons"].append("token_inventory_requires_valuation")
        if not c["recorded_signatures"]:
            c["reasons"].append("historical_transaction_coverage_missing")
        # Wallet transfers, pre-existing inventory and unrecorded/manual actions
        # require a wallet-wide reconciliation before this can become NAV/PnL.
        c["reasons"].append("wallet_wide_coverage_and_asset_marks_not_verified")
        if not c["reconciled_transactions"]:
            c["wallet_delta_lamports"] = c["network_fee_lamports"] = None
        if len(c["lp_unmeasured_positions"]) == len(c["positions"]):
            c["lp_pnl_sol"] = None
        c["net_pnl_sol"] = None
        c["accounting_status"] = "incomplete"
    return {"basis": "recorded_finalized_wallet_cash_flows", "nav_sol": None,
            "note": "Wallet delta already includes network fees and net account rent movements; do not subtract fees again. LP PnL uses Meteora valuations. Neither is portfolio NAV. Rent, inventory drift and swap attribution require further reconciliation.",
            "chains": sorted(chains.values(), key=lambda c: c["root_chain_id"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=PROFILE_DIR)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--hours", type=int, default=24, help="Select chains active in this window; include all their recorded legs")
    args = parser.parse_args()
    if args.refresh:
        executor = args.profile / "skills/solana-dlmm/scripts/dlmm_executor.js"
        subprocess.run(["node", str(executor), "accounting"], check=True,
                       stdout=subprocess.DEVNULL)
    if args.hours <= 0:
        parser.error("--hours must be positive")
    result = report(args.profile)
    result["chains"] = [c for c in result["chains"] if c["last_activity"] >= time.time() - args.hours * 3600]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
