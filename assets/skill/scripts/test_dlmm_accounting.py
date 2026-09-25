#!/usr/bin/env python3
"""Offline: python3 assets/skill/scripts/test_dlmm_accounting.py"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from dlmm_accounting import report

with TemporaryDirectory() as root:
    memories = Path(root) / "memories"
    (memories / "dlmm_entries").mkdir(parents=True)
    def write(name, records):
        (memories / name).write_text("".join(json.dumps(r) + "\n" for r in records))
    (memories / "dlmm_entries/child.json").write_text(json.dumps(
        dict(position="child", root_chain_id="root", parent_position="root")))
    write("dlmm_closes.jsonl", [dict(position="root"), dict(position="root"),
                               dict(position="child", recenter_of="root")])
    write("dlmm_realized.jsonl", [dict(position="root", realized_sol=0.01),
                                 dict(position="child", realized_sol=-0.02)])
    event = dict(signature="a", position="root", root_chain_id="root", wallet="wallet")
    write("dlmm_transactions.jsonl", [event, event,
        dict(signature="b", position="child", root_chain_id="root", wallet="wallet"),
        dict(signature="c", position="child", root_chain_id="root", wallet="wallet"),
        dict(signature="pending", position="child", root_chain_id="root", wallet="wallet")])
    write("dlmm_transaction_facts.jsonl", [
        dict(signature="a", wallet="wallet", wallet_delta_lamports=-100000000,
             fee_lamports=5000, failed=False, token_deltas_raw={"TOKEN": "9007199254740993"}),
        dict(signature="b", wallet="wallet", wallet_delta_lamports=90000000,
             fee_lamports=6000, failed=False, token_deltas_raw={}),
        dict(signature="c", wallet="wallet", wallet_delta_lamports=-7000,
             fee_lamports=7000, failed=True, token_deltas_raw={})])
    historical = report(root, 100)
    assert historical["chains"][0]["wallet_delta_lamports"] is None  # undated facts are not historical evidence
    result = report(root)
    assert result["nav_sol"] is None
    c, = result["chains"]
    assert c["positions"] == ["child", "root"]
    assert c["lp_pnl_sol"] == -0.01
    assert c["wallet_delta_lamports"] == -10007000  # fees already inside wallet delta
    assert c["network_fee_lamports"] == 18000  # failed transactions still cost fees
    assert c["pending_signatures"] == ["pending"]
    assert c["token_deltas_raw"]["TOKEN"] == "9007199254740993"
    assert c["net_pnl_sol"] is None
    assert c["accounting_status"] == "incomplete"
    write("dlmm_transaction_facts.jsonl", [])
    assert len(report(root)["chains"][0]["pending_signatures"]) == 4
    assert report(root)["chains"][0]["wallet_delta_lamports"] is None
    write("dlmm_transactions.jsonl", [event, dict(event, position="other")])
    try:
        report(root)
    except ValueError:
        pass
    else:
        raise AssertionError("conflicting attribution accepted")
print("Root-chain cash flows, deduplication, missing data and fee accounting passed")
