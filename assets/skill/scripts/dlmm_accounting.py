#!/usr/bin/env python3
"""Read recorded cash flows by root chain; never promote partial flows to NAV.

Run through the profile symlink so its memories directory is selected:
  python3 .../skills/solana-dlmm/scripts/dlmm_accounting.py --refresh
Only --refresh calls RPC (read-only). Historical unrecorded costs stay unknown.
"""
import argparse
import json
import math
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


def report(profile, as_of=None):
    replay = as_of is not None
    as_of = time.time() if as_of is None else as_of
    memories = Path(profile) / "memories"
    events = [r for r in rows(memories / "dlmm_transactions.jsonl") if r.get("ts", 0) <= as_of]
    facts = {r["signature"]: r for r in rows(memories / "dlmm_transaction_facts.jsonl") if r.get("observed_at", float("inf") if replay else 0) <= as_of}
    wallet_facts = {r["signature"]: r for r in rows(memories / "dlmm_wallet_transactions.jsonl") if r.get("observed_at", float("inf") if replay else 0) <= as_of}
    facts.update(wallet_facts)
    snapshots = [r for r in rows(memories / "dlmm_nav.jsonl") if r["ts"] <= as_of]
    latest = snapshots[-1] if snapshots else {}
    coverages = [r for r in rows(memories / "dlmm_wallet_coverage.jsonl") if r["ts"] <= as_of]
    coverage = coverages[-1] if coverages else latest
    closes = {r["position"]: r for r in rows(memories / "dlmm_closes.jsonl")
              if r.get("position") and not r.get("dry_run") and r.get("ts", 0) <= as_of}
    entries = {}
    for file in (memories / "dlmm_entries").glob("*.json"):
        entry = json.loads(file.read_text())
        if entry.get("deployed_at", 0) <= as_of:
            entries[entry["position"]] = entry
    realized = {p:r for p,r in load_realized(str(memories / "dlmm_realized.jsonl")).items()
                if r.get("fetched_at", float("inf") if replay else 0) <= as_of}
    chains = {}

    def chain(root):
        return chains.setdefault(root, {"root_chain_id": root, "positions": set(),
            "recorded_signatures": set(), "pending_signatures": [], "wallet_delta_lamports": 0,
            "network_fee_lamports": 0, "reconciled_transactions": 0, "failed_transactions": 0, "token_deltas_raw": {},
            "first_activity": float("inf"), "swap_delta_lamports": 0, "nonrefundable_account_cost_lamports": 0, "last_activity": 0, "lp_pnl_sol": 0.0, "lp_unmeasured_positions": [], "reasons": []})

    position_roots = {}
    for position in entries.keys() | closes.keys():
        metadata = {**closes.get(position, {}), **entries.get(position, {})}
        root = metadata.get("root_chain_id") or metadata.get("recenter_of") or position
        position_roots[position] = root
        c = chain(root)
        c["positions"].add(position)
        c["last_activity"] = max(c["last_activity"], metadata.get("ts") or 0, metadata.get("deployed_at") or 0)
        c["first_activity"] = min(c["first_activity"], metadata.get("deployed_at") or 0)

    entry_roots = {e["entry_id"]: position_roots[p] for p,e in entries.items() if e.get("entry_id")}
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
        root = position_roots.get(event.get("position")) or entry_roots.get(event.get("entry_id")) or event.get("root_chain_id") or "unattributed"
        c = chain(root)
        c["recorded_signatures"].add(signature)
        c["last_activity"] = max(c["last_activity"], event.get("ts") or 0)
        c["first_activity"] = min(c["first_activity"], event.get("ts") or 0)
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
        c["nonrefundable_account_cost_lamports"] += fact.get("nonrefundable_account_cost_lamports", 0)
        if event.get("kind") == "swap":
            c["swap_delta_lamports"] += fact["wallet_delta_lamports"]
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
        if (not coverage.get("wallet_history_complete") or coverage.get("unclassified_transactions")
                or c["first_activity"] < coverage.get("coverage_since", float("inf"))
                or any(facts[s].get("slot", 0) > coverage.get("end_slot", 0) for s in c["recorded_signatures"] if s in facts)
                or as_of - coverage.get("ts", 0) > 600):
            c["reasons"].append("wallet_wide_coverage_not_verified")
        for position in c["positions"]:
            kinds = {e.get("kind") for e in events if e.get("position") == position and e.get("signature") in facts}
            if not {"deploy", "close"} <= kinds or not any(
                    facts[e["signature"]].get("position_account_closed") for e in events
                    if e.get("position") == position and e.get("signature") in facts):
                c["reasons"].append("entry_or_close_evidence_missing")
                break
        if c["root_chain_id"] == "unattributed":
            c["reasons"].append("unattributed")
        if c["first_activity"] == float("inf"):
            c["first_activity"] = None
        if not c["reconciled_transactions"]:
            c["wallet_delta_lamports"] = c["network_fee_lamports"] = None
        if len(c["lp_unmeasured_positions"]) == len(c["positions"]):
            c["lp_pnl_sol"] = None
        c["settled_cash_pnl_sol"] = c["wallet_delta_lamports"] / 1e9 if not c["reasons"] else None
        c["net_pnl_sol"] = c["settled_cash_pnl_sol"]
        c["accounting_status"] = "settled_cash" if not c["reasons"] else "incomplete"
        c["net_basis"] = "wallet_cash_after_fees_and_rent; recoverable_account_reserves_excluded"
        c["lp_to_cash_difference_sol"] = (c["net_pnl_sol"] - c["lp_pnl_sol"]
            if c["net_pnl_sol"] is not None and c["lp_pnl_sol"] is not None else None)
    nav = latest.get("nav_sol") if as_of - latest.get("ts", 0) <= 600 else None
    first = next((r for r in snapshots if r.get("nav_sol") is not None), {})
    change = None
    if nav is not None and first and latest.get("wallet_history_complete") and not latest.get("unclassified_transactions"):
        external = sum(r.get("external_flow_lamports") or 0 for r in wallet_facts.values()
                       if first["end_slot"] < r.get("slot", 0) <= latest.get("end_slot", 0)) / 1e9
        change = nav - first["nav_sol"] - external
    return {"basis": "recorded_finalized_wallet_cash_flows", "nav_sol": nav,
            "nav_snapshot": latest, "flow_adjusted_wealth_change_sol": change,
            "note": "Wallet delta already includes network fees and net account rent movements; do not subtract fees again. LP PnL uses Meteora valuations. Neither is portfolio NAV. Rent, inventory drift and swap attribution require further reconciliation.",
            "chains": sorted(chains.values(), key=lambda c: c["root_chain_id"])}


def root_decision(chain, opportunity_sol, floor_sol=-0.015, strike_cap=3):
    """Conservative gate: projected 30m fees must repay cumulative cash loss + next observed cycle cost."""
    result = dict(allow=False, reason="incomplete_chain", chain=chain, opportunity_sol=opportunity_sol,
                  floor_sol=floor_sol, strike_cap=strike_cap)
    if not chain or chain.get("accounting_status") != "settled_cash":
        return result
    legs = len(chain["positions"])
    strikes = max(0, legs-1)
    cost = (chain["network_fee_lamports"]+chain.get("nonrefundable_account_cost_lamports", 0))/1e9
    next_cost = cost/max(1, legs)
    net = chain["settled_cash_pnl_sol"]
    result.update(strikes=strikes, cumulative_net_sol=net, cumulative_cost_sol=cost, next_cycle_cost_sol=next_cost)
    if strikes >= strike_cap:
        result["reason"] = "root_strike_cap"
    elif net <= floor_sol:
        result["reason"] = "root_loss_floor"
    elif opportunity_sol is None or not math.isfinite(opportunity_sol) or opportunity_sol <= max(0, -net)+next_cost:
        result["reason"] = "fee_opportunity_below_loss_and_cost"
    else:
        result.update(allow=True, reason="root_cost_budget_pass")
    return result


def check_root(profile, root, opportunity, floor, cap):
    result = report(profile)
    chain = next((c for c in result["chains"] if c["root_chain_id"] == root), None)
    decision = root_decision(chain, opportunity, floor, cap)
    decision.update(ts=int(time.time()), root_chain_id=root)
    with (Path(profile)/"memories/dlmm_root_decisions.jsonl").open("a") as stream:
        stream.write(json.dumps(decision, allow_nan=False)+"\n")
    return decision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=PROFILE_DIR)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--hours", type=int, default=24, help="Select chains active in this window; include all their recorded legs")
    parser.add_argument("--check-root")
    parser.add_argument("--opportunity", type=float)
    parser.add_argument("--floor", type=float, default=-0.015)
    parser.add_argument("--strike-cap", type=int, default=3)
    args = parser.parse_args()
    if args.check_root:
        print(json.dumps(check_root(args.profile, args.check_root, args.opportunity, args.floor, args.strike_cap)))
        return
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
