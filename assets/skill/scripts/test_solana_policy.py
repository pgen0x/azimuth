"""Offline regression check: python3 assets/skill/scripts/test_solana_policy.py."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import dlmm_pipeline as pipeline
import dlmm_stats as stats
from dlmm_realized import apply_realized


def main():
    # Same token, different fee tiers: pool economics choose the primary;
    # every mint's primary stays ahead of sibling fallbacks.
    pools = [
        {"pool": "thin", "name": "TOKEN-SOL 5%", "base_mint": "token", "base_symbol": "TOKEN",
         "score": 95, "fee_active_tvl_ratio": 1.53, "active_tvl": 30_000, "fee_tvl_ratio": 1.0, "tvl": 50_000},
        {"pool": "yield", "name": "TOKEN-SOL 1%", "base_mint": "token", "base_symbol": "TOKEN",
         "score": 80, "fee_active_tvl_ratio": 2.33, "active_tvl": 40_000, "fee_tvl_ratio": 1.4, "tvl": 70_000},
        {"pool": "other", "name": "OTHER-SOL", "base_mint": "other", "base_symbol": "OTHER",
         "score": 85, "fee_active_tvl_ratio": 1.0, "active_tvl": 50_000, "fee_tvl_ratio": 0.8, "tvl": 80_000},
    ]
    ranked = sorted(pipeline.rank_cross_pool_candidates(pools),
                    key=pipeline.candidate_pick_key, reverse=True)
    assert [c["pool"] for c in ranked] == ["other", "yield", "thin"]

    candidate = {"pool": "yield", "name": "TOKEN-SOL", "base_mint": "token",
                 "fee_tvl_ratio": 2.0}
    with patch.object(pipeline, "get_momentum", return_value=(-6.0, 0, 0, 0)):
        assert "dumping" in pipeline.predeploy_live_gate_reject(candidate, 0.1, "30m")
    with patch.object(pipeline, "get_momentum", return_value=(0, 0, 0, 0)), \
         patch.object(pipeline, "fetch_live_fee_tvl", return_value=0.5):
        assert "fee/TVL" in pipeline.predeploy_live_gate_reject(candidate, 0.1, "30m")
    with patch.object(pipeline, "get_momentum", return_value=(0, 0, 0, 0)), \
         patch.object(pipeline, "fetch_live_fee_tvl", return_value=2.0), \
         patch.object(pipeline, "get_price_impact_sol_to_token", return_value=6.0):
        assert "price impact" in pipeline.predeploy_live_gate_reject(candidate, 0.1, "30m")

    # Exercise the real CLI entry path, stopping at its slot gate before any
    # wallet/network work. Neither a stale prompt nor SOUL can override signals.
    for mode in ("turnover", "pulse", "casual", "multiday"):
        for source in ("from_signal", "from_batch", None):
            args = argparse.Namespace(mode=mode, strategy="balanced_tight",
                                      from_signal=None, from_batch=None,
                                      analyze_only=False)
            if source:
                setattr(args, source, "{}")
            with patch.object(argparse.ArgumentParser, "parse_args", return_value=args), \
                    patch.object(pipeline, "reconcile_redis_vs_meteora"), \
                    patch.object(pipeline, "get_active_positions_count_for_mode", return_value=999), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    pipeline.main()
                except SystemExit as exc:
                    assert exc.code == 0
            assert args.strategy == ("sol_bidask" if source else "balanced_tight")

    # Two journal attempts for one position must contribute one lifetime PnL.
    with tempfile.TemporaryDirectory() as tmp:
        realized = Path(tmp) / "realized.jsonl"
        realized.write_text(json.dumps({"position": "p", "realized_sol": 0.2,
                                        "realized_pct": 2.0}) + "\n")
        records = [{"position": "p", "pnl_sol": -1, "reason": "first"},
                   {"position": "p", "pnl_sol": -2, "reason": "retry"},
                   {"position": "unindexed", "pnl_sol": -0.1},
                   {"pnl_sol": 0.01}, {"pnl_sol": 0.02}]
        result = apply_realized(records, str(realized))
        assert result is records and len(result) == 4
        assert result[0]["reason"] == "retry" and result[0]["pnl_sol"] == 0.2
        assert result[1]["pnl_basis"] == "mark" and result[1]["pnl_sol"] == -0.1

        brief_path = Path(__file__).resolve().parents[2] / "hermes/scripts/sol_dlmm_proposal_brief.py"
        spec = importlib.util.spec_from_file_location("brief", brief_path)
        brief = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(brief)
        closes = Path(tmp) / "closes.jsonl"
        closes.write_text("\n".join(json.dumps(dict(r, ts=100)) for r in [
            {"position": "p", "pnl_sol": -1}, {"position": "p", "pnl_sol": -2},
            {"position": "unindexed", "pnl_sol": -0.1},
        ]))
        with patch.object(brief, "CLOSES_PATH", str(closes)), \
                patch.object(brief, "REALIZED_PATH", str(realized)), \
                patch.object(brief.time, "time", return_value=101):
            result = brief.load_closes()
        assert len(result) == 2 and abs(sum(r["pnl_sol"] for r in result) - 0.1) < 1e-9

    # A pool touched this week also has older closes. Only position close times
    # belong in a window card, and pulse must appear in the mode breakdown.
    with patch.object(stats, "load_closes", return_value=[{
        "mode": "pulse", "pnl_sol": 0.2, "pnl_basis": "realized", "age_min": 10,
    }]), patch.object(stats, "load_realized", return_value={
        "recent": {"closed_at": 90_000, "realized_sol": 0.2, "fee_sol": 0.3, "deposit_sol": 1},
        "old": {"closed_at": 1, "realized_sol": 99, "fee_sol": 100, "deposit_sol": 1000},
        "future": {"closed_at": 200_000, "realized_sol": 99},
    }), patch.object(stats.time, "time", return_value=100_000), \
            patch.object(stats, "redis_keys", return_value=[]), \
            patch.object(stats, "redis_scard", return_value=0):
        card = stats.build_card(24)
    assert "+0.2000 / +0.3000 / -0.1000 SOL" in card
    assert "1.00 SOL across 1 cached closes" in card and "| pulse | 1 closes" in card
    print("Solana policy and journal regression checks passed")


if __name__ == "__main__":
    main()
