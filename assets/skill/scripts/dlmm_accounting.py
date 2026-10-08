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


def unvalued_token_inflows(facts, first_slot, last_slot):
    """Unknown transfer-time token/ATA value cannot be subtracted from wealth."""
    return [r["signature"] for r in facts if r.get("classification") == "external_token_inflow"
            and r.get("landed") is not False and not r.get("failed")
            and (r.get("slot") is None or first_slot < r["slot"] <= last_slot)]


def cleanup_owner(event, fact, chains, closes, coverage, inflows, unresolved_since, as_of):
    """Attribute only an exact full-inventory sale with one proven closed owner.

    Never allocate a shared balance pro rata or infer ownership from matching
    amounts alone. This consumes transaction-time balances, not today's marks.
    """
    if (event.get("kind") != "swap" or not fact or fact.get("failed")
            or fact.get("landed") is False or fact.get("wallet") != event.get("wallet")
            or not coverage.get("wallet_history_complete") or coverage.get("unclassified_transactions")
            or as_of-coverage.get("ts", 0)>600 or fact.get("slot", float("inf"))>coverage.get("end_slot", 0)
            or unresolved_since <= event.get("ts", 0)):
        return None
    deltas = {m:int(v) for m,v in fact.get("token_deltas_raw", {}).items() if int(v)}
    if len(deltas) != 1:
        return None
    mint, delta = next(iter(deltas.items()))
    if (delta >= 0 or int(fact.get("token_pre_balances_raw", {}).get(mint, -1)) != -delta
            or int(fact.get("token_post_balances_raw", {}).get(mint, 0)) != 0):
        return None
    owners = [c for c in chains.values() if int(c["token_deltas_raw"].get(mint, 0)) != 0]
    if len(owners) != 1:
        return None
    c = owners[0]
    if (c["root_chain_id"] == "unattributed" or not c["positions"] or c["pending_signatures"]
            or int(c["token_deltas_raw"][mint]) != -delta
            or c["first_activity"] < coverage.get("coverage_since", float("inf"))
            or any(p not in closes or closes[p].get("ts", float("inf"))>event.get("ts", 0) for p in c["positions"])
            or any(int(r.get("token_deltas_raw", {}).get(mint, 0))>0
                   and (r.get("block_time") is None or c["first_activity"]<=r["block_time"]<=event.get("ts", 0)) for r in inflows)):
        return None
    return c["root_chain_id"]


def pooled_settlements(chains):
    """Measure closed groups with cancelling inventory, never allocate root PnL."""
    pending = {c["root_chain_id"]: c for c in chains if c["token_deltas_raw"]}
    groups = []
    while pending:
        _, first = pending.popitem()
        members = [first]
        mints = set(first["token_deltas_raw"])
        # A shared residual mint connects all owners, including incomplete ones.
        # ponytail: scan owners; index by mint if journal growth makes this costly.
        while True:
            linked = [key for key, c in pending.items() if mints.intersection(c["token_deltas_raw"])]
            if not linked:
                break
            for key in linked:
                c = pending.pop(key)
                members.append(c)
                mints.update(c["token_deltas_raw"])
        if len(members) < 2 or any(set(c["reasons"]) != {"token_inventory_requires_valuation"} for c in members):
            continue
        if any(sum(int(c["token_deltas_raw"].get(mint, 0)) for c in members) for mint in mints):
            continue
        groups.append({
            "root_chain_ids": sorted(c["root_chain_id"] for c in members),
            "first_activity": min(c["first_activity"] for c in members),
            "last_activity": max(c["last_activity"] for c in members),
            "settled_cash_pnl_sol": sum(c["wallet_delta_lamports"] for c in members) / 1e9,
            "network_fee_sol": sum(c["network_fee_lamports"] for c in members) / 1e9,
            "basis": "combined_wallet_cash_after_fees_and_rent; no_per_root_allocation; not_NAV",
        })
    return sorted(groups, key=lambda g: g["root_chain_ids"])


def rent_refund_groups(chains, facts, histories, as_of):
    """Combine settled account users and proved funding refunds; charge fees once."""
    by_root = {c["root_chain_id"]: c for c in chains}
    owners = {}
    for c in chains:
        for signature in c["recorded_signatures"]:
            owners.setdefault(signature, set()).add(c["root_chain_id"])
    evidence = {(r.get("refund_signature"), r.get("account")): r for r in histories
                if r.get("observed_at", float("inf")) <= as_of}
    groups, components = [], {}
    for signature, refund in facts.items():
        items = refund.get("token_rent_evidence", {}).get("refunded", [])
        if (not items or refund.get("failed") or refund.get("landed") is False
                or owners.get(signature) != {"unattributed"}
                or not isinstance(refund.get("block_time"), (int, float))
                or refund["block_time"] > as_of
                or len({i["account"] for i in items}) != len(items)
                or sum(i["lamports"] for i in items)-refund["fee_lamports"] != refund["wallet_delta_lamports"]):
            continue
        roots, gross_by_root = set(), {}
        for item in items:
            proof = evidence.get((signature, item["account"]), {})
            history = proof.get("history_signatures", [])
            funding = facts.get(proof.get("funding_signature"), {})
            if (proof.get("complete") is not True or proof.get("version") != 1
                    or proof.get("wallet") != refund.get("wallet")
                    or any(proof.get(k) != item[k] for k in ("account", "mint", "lamports"))
                    or not history or history[-1] != proof.get("funding_signature")
                    or signature in history or len(set(history)) != len(history)
                    or funding.get("wallet") != refund.get("wallet") or funding.get("failed")
                    or item not in funding.get("token_rent_evidence", {}).get("funded", [])):
                break
            root_owners = set()
            for s in history:
                f = facts.get(s, {})
                if (len(owners.get(s, set())) != 1 or f.get("wallet") != refund.get("wallet")
                        or f.get("landed") is False or not isinstance(f.get("slot"), int)
                        or not funding.get("slot", float("inf")) <= f["slot"] <= refund.get("slot", -1)):
                    break
                root_owners.update(owners[s])
            else:
                if root_owners and "unattributed" not in root_owners:
                    if all(by_root[r]["accounting_status"] == "settled_cash" and by_root[r]["positions"]
                           and by_root[r]["last_activity"] <= as_of for r in root_owners):
                        roots.update(root_owners)
                        # Rent returns to its proved funder; all users share the fee bounds.
                        for r in root_owners:
                            gross_by_root.setdefault(r, 0)
                        root = next(iter(owners[proof["funding_signature"]]))
                        gross_by_root[root] = gross_by_root.get(root, 0) + item["lamports"]
                        continue
            break
        else:
            components[signature] = dict(signature=signature, gross_by_root=gross_by_root,
                                         fee_lamports=refund["fee_lamports"])
            # Connected refunds share roots; include each root's cash only once.
            group = dict(roots=roots, refunds={signature})
            linked = [g for g in groups if g["roots"] & roots]
            for g in linked:
                group["roots"].update(g["roots"])
                group["refunds"].update(g["refunds"])
                groups.remove(g)
            groups.append(group)
    return [dict(root_chain_ids=sorted(g["roots"]), refund_signatures=sorted(g["refunds"]),
                 refund_components=[components[s] for s in sorted(g["refunds"])],
                 first_activity=min(by_root[r]["first_activity"] for r in g["roots"]),
                 last_activity=max([facts[s]["block_time"] for s in g["refunds"]]
                                   + [by_root[r]["last_activity"] for r in g["roots"]]),
                 cash_with_matched_refunds_sol=(sum(by_root[r]["wallet_delta_lamports"] for r in g["roots"])
                     + sum(facts[s]["wallet_delta_lamports"] for s in g["refunds"]))/1e9,
                 network_fee_sol=(sum(by_root[r]["network_fee_lamports"] for r in g["roots"])
                     + sum(facts[s]["fee_lamports"] for s in g["refunds"]))/1e9,
                 basis="root_cash_plus_matched_refunds; shared_fees_once; overlaps_root_cash; not_NAV_or_per_root_win_rate")
            for g in groups]


def report(profile, as_of=None):
    replay = as_of is not None
    as_of = time.time() if as_of is None else as_of
    memories = Path(profile) / "memories"
    events = [r for r in rows(memories / "dlmm_transactions.jsonl") if r.get("ts", 0) <= as_of]
    facts = {r["signature"]: r for r in rows(memories / "dlmm_transaction_facts.jsonl") if r.get("observed_at", float("inf") if replay else 0) <= as_of}
    wallet_facts = {r["signature"]: r for r in rows(memories / "dlmm_wallet_transactions.jsonl") if r.get("observed_at", float("inf") if replay else 0) <= as_of}
    facts.update(wallet_facts)
    token_inflows = [r for r in wallet_facts.values() if r.get("classification") == "external_token_inflow"]
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
            "recorded_signatures": set(), "pending_signatures": [], "expired_unlanded_signatures": [], "cleanup_settlements": [], "wallet_delta_lamports": 0,
            "network_fee_lamports": 0, "reconciled_transactions": 0, "failed_transactions": 0, "token_deltas_raw": {}, "touched_mints": set(),
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
    unresolved_since = min((e.get("ts", 0) for e in events
                            if e.get("ts", 0)>=coverage.get("coverage_since", 0)
                            and (e["signature"] not in facts or facts[e["signature"]].get("wallet") != e.get("wallet"))), default=float("inf"))
    # Settlements can only consume inventory established by earlier finalized
    # transactions. Missing facts remain unresolved and cannot supply inventory.
    events = sorted(events, key=lambda e:(facts.get(e["signature"], {}).get("slot", float("inf")), e.get("ts", 0)))
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
        fact = facts.get(signature)
        owner = cleanup_owner(event, fact, chains, closes, coverage, token_inflows, unresolved_since, as_of) if root == "unattributed" else None
        if owner:
            root = owner
        c = chain(root)
        if owner:
            c["cleanup_settlements"].append(dict(signature=signature, basis="unique_closed_inventory_exact_full_balance_sale", observed_at=fact["observed_at"]))
        c["recorded_signatures"].add(signature)
        c["last_activity"] = max(c["last_activity"], event.get("ts") or 0)
        c["first_activity"] = min(c["first_activity"], event.get("ts") or 0)
        if event.get("position"):
            c["positions"].add(event["position"])
        if fact is None or fact.get("wallet") != event.get("wallet"):
            c["pending_signatures"].append(signature)
            continue
        if fact.get("landed") is False and fact.get("classification") == "expired_unlanded":
            c["expired_unlanded_signatures"].append(signature)
            continue
        c["reconciled_transactions"] += 1
        c["wallet_delta_lamports"] += fact["wallet_delta_lamports"]
        c["network_fee_lamports"] += fact["fee_lamports"]
        c["failed_transactions"] += int(fact["failed"])
        c["nonrefundable_account_cost_lamports"] += fact.get("nonrefundable_account_cost_lamports", 0)
        if event.get("kind") == "swap":
            c["swap_delta_lamports"] += fact["wallet_delta_lamports"]
        for mint, amount in fact["token_deltas_raw"].items():
            c["touched_mints"].add(mint)
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
        c["touched_mints"] = sorted(c["touched_mints"])
        c["token_deltas_raw"] = {m: str(v) for m, v in c["token_deltas_raw"].items() if v}
        if any((r.get("block_time") is None or c["first_activity"] <= r["block_time"] <= c["last_activity"])
               and any(m in c["touched_mints"] and int(v)>0 for m,v in r.get("token_deltas_raw", {}).items())
               for r in token_inflows):
            c["reasons"].append("external_token_inflow_requires_attribution")
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
            kinds = {e.get("kind") for e in events if e.get("position") == position and e.get("signature") in facts
                     and facts[e["signature"]].get("landed") is not False and not facts[e["signature"]].get("failed")}
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
    # A gifted token (and externally funded ATA rent) increases wallet wealth,
    # but its transfer-time value is not known. Never count it as trading profit.
    unvalued_inflows = unvalued_token_inflows(wallet_facts.values(), first["end_slot"], latest.get("end_slot", 0)) if first else []
    if nav is not None and first and latest.get("wallet_history_complete") and not latest.get("unclassified_transactions") and not unvalued_inflows:
        external = sum(r.get("external_flow_lamports") or 0 for r in wallet_facts.values()
                       if first["end_slot"] < r.get("slot", 0) <= latest.get("end_slot", 0)) / 1e9
        change = nav - first["nav_sol"] - external
    return {"basis": "recorded_finalized_wallet_cash_flows", "nav_sol": nav,
            "nav_snapshot": latest, "flow_adjusted_wealth_change_sol": change,
            "unvalued_external_token_inflows": unvalued_inflows,
            "note": "Wallet delta already includes network fees and net account rent movements; do not subtract fees again. LP PnL uses Meteora valuations. Neither is portfolio NAV. Rent, inventory drift and swap attribution require further reconciliation.",
            "pooled_settlements": pooled_settlements(chains.values()),
            "rent_refund_groups": rent_refund_groups(list(chains.values()), facts,
                rows(memories / "dlmm_rent_history.jsonl"), as_of),
            "chains": sorted(chains.values(), key=lambda c: c["root_chain_id"])}



def settlement_inventory(profile, position, mint, wallet):
    """Authorize only finalized closed-root inventory, never the wallet balance."""
    ledger = report(profile)
    matches = [c for c in ledger["chains"] if position in c["positions"]]
    refusal = {"success": False, "reason": "settlement_inventory_unproven"}
    if len(matches) != 1:
        return refusal
    c = matches[0]
    if c["pending_signatures"]:
        return dict(refusal, pending_signatures=c["pending_signatures"])
    if set(c["reasons"]) - {"token_inventory_requires_valuation", "wallet_wide_coverage_not_verified"}:
        return refusal
    memories = Path(profile) / "memories"
    entry = json.loads((memories / "dlmm_entries" / (position + ".json")).read_text())
    if entry.get("base_mint") != mint:
        return refusal
    events = [e for e in rows(memories / "dlmm_transactions.jsonl") if e["signature"] in c["recorded_signatures"]]
    if any(e.get("wallet") != wallet for e in events):
        return refusal
    facts = {r["signature"]: r for name in ("dlmm_transaction_facts.jsonl", "dlmm_wallet_transactions.jsonl")
             for r in rows(memories / name)}
    raw = int(c["token_deltas_raw"].get(mint, 0))
    if raw < 0:
        return refusal
    # Zero owned inventory completes settlement without touching legacy tokens.
    if raw == 0:
        return {"success": True, "amount_raw": "0"}
    if any(r.get("classification") == "external_token_inflow" and not r.get("failed")
           and r.get("landed") is not False and int(r.get("token_deltas_raw", {}).get(mint, 0)) > 0
           and (r.get("block_time") is None or r["block_time"] >= c["first_activity"])
           for r in facts.values()):
        return refusal
    landed = [facts[s] for s in c["recorded_signatures"]
              if facts[s].get("landed") is not False and not facts[s].get("failed")]
    if any(type(f.get("slot")) is not int
           or any(not isinstance(f.get(k), dict) for k in ("token_pre_balances_raw", "token_post_balances_raw"))
           or int(f["token_post_balances_raw"].get(mint, 0))-int(f["token_pre_balances_raw"].get(mint, 0))
                != int(f.get("token_deltas_raw", {}).get(mint, 0))
           for f in landed):
        return refusal
    first = min(landed, key=lambda f: f["slot"])
    initial = int(first["token_pre_balances_raw"].get(mint, 0))
    last_slot = max(f["slot"] for f in landed)
    # Preserve the transaction-time legacy balance, not historical ledger debts.
    # Claim and close can share a slot; only the conserved terminal balance fits.
    terminal = [f for f in landed if f["slot"] == last_slot
                and int(f["token_post_balances_raw"].get(mint, 0)) == initial+raw]
    if initial < 0 or not terminal:
        return refusal
    if any(s not in c["recorded_signatures"] and f.get("wallet") == wallet
           and f.get("landed") is not False and not f.get("failed")
           and int(f.get("token_deltas_raw", {}).get(mint, 0))
           and (f.get("slot") is None or f["slot"] >= first["slot"])
           for s, f in facts.items()):
        return refusal
    return {"success": True, "amount_raw": str(raw), "wallet_balance_raw": str(initial+raw), "slot": last_slot}


def refund_cash_bounds(group, chains, selected):
    """Project validated refund cash; charge a shared TX fee fully or not at all.

    Bounds from different pools cannot be summed: their shared fee ranges overlap.
    """
    ids = set(group["root_chain_ids"])
    pieces = group.get("refund_components")
    if (not selected or not selected <= ids or not isinstance(pieces, list) or not pieces
            or any(r not in chains or chains[r].get("accounting_status") != "settled_cash"
                   or type(chains[r].get("wallet_delta_lamports")) is not int for r in ids)):
        return None
    seen, touched = set(), set()
    total = sum(chains[r]["wallet_delta_lamports"] for r in ids)
    lower = upper = sum(chains[r]["wallet_delta_lamports"] for r in selected)
    for piece in pieces:
        if not isinstance(piece, dict):
            return None
        signature, gross, fee = piece.get("signature"), piece.get("gross_by_root"), piece.get("fee_lamports")
        if (not isinstance(signature, str) or signature in seen or not isinstance(gross, dict)
                or not gross or not set(gross) <= ids or type(fee) is not int or fee < 0
                or any(type(v) is not int or v < 0 for v in gross.values())):
            return None
        seen.add(signature); touched.update(gross)
        total += sum(gross.values()) - fee
        chosen = set(gross) & selected
        if chosen:
            value = sum(gross[r] for r in chosen)
            lower += value - fee
            upper += value - (fee if set(gross) <= selected else 0)
    value = group.get("cash_with_matched_refunds_sol")
    if (seen != set(group.get("refund_signatures", [])) or touched != ids
            or isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or total != round(value * 1e9)):
        return None
    return lower, upper


def pool_cash_history(closes, ledger, as_of):
    """Last ten closes per pool; net cash only when whole roots/refunds match.

    Keep marks separate. Cross-pool cleanup fees produce a conservative range,
    never an invented split. This does not change the mark-based risk floor.
    """
    by_pool = {}
    for row in closes:
        if (row.get("dry_run") or not row.get("pool") or not row.get("position")
                or not as_of - 30 * 86400 <= row.get("ts", 0) <= as_of):
            continue
        by_pool.setdefault(row["pool"], {})[row["position"]] = row
    chains = {c["root_chain_id"]: c for c in ledger["chains"]}
    result = {}
    for pool, records in by_pool.items():
        selected = sorted(records.values(), key=lambda r: r["ts"], reverse=True)[:10]
        positions = {r["position"] for r in selected}
        roots = {r.get("root_chain_id") or r.get("recenter_of") or r["position"] for r in selected}
        covered, lower, upper = set(), 0.0, 0.0
        for group in ledger["rent_refund_groups"]:
            ids = set(group["root_chain_ids"])
            chosen = ids & roots
            if not chosen or chosen & covered or group.get("last_activity", as_of) > as_of:
                continue
            if any(r not in chains or chains[r]["accounting_status"] != "settled_cash"
                   or not set(chains[r]["positions"]) <= positions for r in chosen):
                continue
            if ids <= roots:
                value = group.get("cash_with_matched_refunds_sol")
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    continue
                lo = hi = value
            else:
                bounds = refund_cash_bounds(group, chains, chosen)
                if bounds is None:
                    continue
                lo, hi = (v / 1e9 for v in bounds)
            covered.update(chosen)
            lower += lo; upper += hi
        complete = covered == roots
        exact = complete and round(lower, 9) == round(upper, 9)
        marks = [r.get("pnl_sol") for r in selected]
        valid_marks = all(not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) for v in marks)
        result[pool] = {
            "prior_closes": len(selected), "last_close_ts": selected[0]["ts"],
            "prior_mark_pnl_sol": sum(marks) if valid_marks else None,
            "prior_net_pnl_sol": round(lower, 9) if exact else None,
            "prior_cash_lower_sol": round(lower, 9) if complete else None,
            "prior_cash_upper_sol": round(upper, 9) if complete else None,
            "prior_cash_roots": len(covered), "prior_roots": len(roots),
            "prior_pnl_basis": "matched_refund_cash" if exact else "matched_refund_cash_bounds" if complete else "pre_swap_mark_only",
            "observed_at": as_of,
        }
    return result


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
    elif opportunity_sol is None or not math.isfinite(opportunity_sol):
        result["reason"] = "fee_opportunity_unavailable"
    elif opportunity_sol <= max(0, -net)+next_cost:
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
    parser.add_argument("--sync-pool-memory", action="store_true", help="Publish local reconciled pool history to Redis; no RPC")
    parser.add_argument("--hours", type=int, default=24, help="Select chains active in this window; include all their recorded legs")
    parser.add_argument("--check-root")
    parser.add_argument("--settlement-inventory", nargs=3, metavar=("POSITION", "MINT", "WALLET"))
    parser.add_argument("--opportunity", type=float)
    parser.add_argument("--floor", type=float, default=-0.015)
    parser.add_argument("--strike-cap", type=int, default=3)
    args = parser.parse_args()
    if args.settlement_inventory:
        print(json.dumps(settlement_inventory(args.profile, *args.settlement_inventory)))
        return
    if args.sync_pool_memory:
        now = time.time()
        summary = pool_cash_history(rows(args.profile / "memories/dlmm_closes.jsonl"), report(args.profile), now)
        response = subprocess.run(["redis-cli", "--raw", "-x", "eval", "return redis.call('SET', KEYS[1], ARGV[1], 'EX', 900)", "1", "sol:dlmm:cash_history"],
                                  input=json.dumps(summary, allow_nan=False), text=True,
                                  capture_output=True, timeout=10, check=True)
        if response.stdout.strip() != "OK":
            raise RuntimeError("Pool cash history Redis write failed")
        print(json.dumps({"pools": len(summary), "observed_at": now}))
        return
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
    result["pooled_settlements"] = [g for g in result["pooled_settlements"] if g["last_activity"] >= time.time() - args.hours * 3600]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
