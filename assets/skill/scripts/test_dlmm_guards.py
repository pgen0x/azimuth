"""Offline replay: python3 assets/skill/scripts/test_dlmm_guards.py."""
import ast
import contextlib
import io
import json
from pathlib import Path
import tempfile
import textwrap
from types import SimpleNamespace
from unittest.mock import patch
import dlmm_monitor as monitor
import dlmm_pipeline as pipeline


def main():
    # Replay production eligibility and both profitable-exit cooldown shortcuts.
    tree = ast.parse(Path(monitor.__file__).read_text())
    churn = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "is_turnover_churn" for t in n.targets))
    shortcuts = [n.test for n in ast.walk(tree) if isinstance(n, ast.If)
                 and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                         and c.func.id == "adverse_exit" for c in ast.walk(n.test))]
    assert len(shortcuts) == 2
    ns = dict(mode_cd="turnover", strategy="sol_bidask", emergency_close=False,
              realized_sol=0.0015, rebalance_budget_ok=True, adverse_exit=monitor.adverse_exit)
    for reason, allowed in [("Fast-out dump exit (5m -8.6%, PnL +1.29%)", False),
                            ("Fast-out dump exit (5m -4.2%, PnL +16.50%)", False),
                            ("RUG velocity dump", False), ("Peak-giveback stop", False),
                            ("Sell pressure exit", False), ("Momentum exit", False),
                            ("Downtrend exit", False), ("Stop-loss", False),
                            ("Trailing take-profit", True), ("Take-profit", True),
                            ("Out of Range (above)", True)]:
        ns["reason_lower"] = reason.lower()
        for expression in [churn, *shortcuts]:
            assert eval(compile(ast.Expression(expression), "exit-policy", "eval"), ns) is allowed, reason
    for reason in ("Low yield", "Fee pace death"):
        ns["reason_lower"] = reason.lower()
        assert not eval(compile(ast.Expression(churn), "exit-policy", "eval"), ns)

    cli = SimpleNamespace(mode="turnover", from_batch=json.dumps([{"pool": "A"*32}]), from_signal=None)
    with patch.object(pipeline, "run_command", return_value=("1", "", 0)) as command:
        pipeline.defer_capacity_signals(cli)
        assert "turnover:" + "A"*32 in command.call_args.args[0]
        assert "sol:dlmm:capacity:wallet" in command.call_args.args[0]
        pipeline.defer_capacity_signals(cli, wallet=False)
        assert "sol:dlmm:capacity:turnover" in command.call_args.args[0]
        assert "sol:dlmm:capacity:wallet" not in command.call_args.args[0]
        assert "EXPIRE" in command.call_args.args[0] and "300" in command.call_args.args[0]
    cli.from_batch = None
    cli.from_signal = json.dumps({"pool": "B"*32})
    with patch.object(pipeline, "run_command", return_value=("1", "", 0)) as command:
        pipeline.defer_capacity_signals(cli)
        assert "turnover:" + "B"*32 in command.call_args.args[0]
    for payload in (None, "bad-json", "[]", '{"pool":"bad"}', '{"pool":"$(id)"}'):
        cli.from_signal = payload
        with patch.object(pipeline, "run_command") as command:
            pipeline.defer_capacity_signals(cli)
            command.assert_not_called()
    tree_pipeline = ast.parse(Path(pipeline.__file__).read_text())
    assert sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "defer_capacity_signals" for n in ast.walk(tree_pipeline)) == 4

    meta={}
    state=dict(updated_at=1000,unclaimed_fees_sol=0.001,balances_sol=0.1)
    assert monitor.observe_root_fee_pace(meta,state,1000)
    assert 'fee_pace_pct_30m' not in meta
    assert not monitor.observe_root_fee_pace(meta,dict(state,updated_at=1100),1100)
    assert monitor.observe_root_fee_pace(meta,dict(state,updated_at=2800,unclaimed_fees_sol=0.002),2800)
    assert abs(meta['fee_pace_pct_30m']-1)<1e-10
    assert not monitor.observe_root_fee_pace(meta,dict(state,updated_at=2800),3100)  # stale API sample
    assert monitor.observe_root_fee_pace(meta,dict(state,updated_at=2900,unclaimed_fees_sol=0),2900)
    assert 'fee_pace_pct_30m' not in meta  # claimed fees reset observation

    assert monitor.downside_floor_bins(100) == 23
    assert monitor.hold_block_reason({}, {"in_range": True, "unclaimed_fees_sol": 1})
    assert "out of range" in monitor.hold_block_reason(
        {"pool": "pool"}, {"in_range": False, "unclaimed_fees_sol": 1})
    assert monitor.hold_block_reason(
        {"pool": "pool"}, {"in_range": True, "unclaimed_fees_sol": 0})
    assert monitor.hold_block_reason(
        {"pool": "pool"}, {"in_range": True, "unclaimed_fees_sol": 0.001}) is None

    payload = {"solPrice": 150, "pools": [{"poolAddress": "pool", "binStep": 80, "listPositions": ["position"],
        "pnlPctChange": -30, "pnlSolPctChange": 2, "pnlSol": 0.02,
        "totalDepositSol": 1, "unclaimedFeesSol": 0.001}]}
    class Response:
        def read(self): return json.dumps(payload).encode()
        def __enter__(self): return self
        def __exit__(self, *args): return False
    response = Response()
    with patch.object(monitor.urllib.request, "urlopen", return_value=response):
        portfolio, error = monitor.get_meteora_portfolio_positions("wallet")
    assert error is None and portfolio["position"]["pnl_pct"] == 2
    assert portfolio["position"]["pnl_currency"] == "SOL"
    assert portfolio["position"]["bin_step"] == 80

    with patch.object(monitor, "run_command_json", return_value=({"success": True}, None)), \
         patch.object(monitor, "position_live_onchain", return_value=True), \
         patch.object(monitor, "position_residual_sol", return_value=0.1):
        close_result, _ = monitor.close_position("position", wallet_address="wallet")
    assert close_result["success"] is False and close_result["unsettled"] is True
    with patch.object(monitor, "run_command_json", return_value=({"success": True}, None)), \
         patch.object(monitor, "position_live_onchain", return_value=False):
        close_result, _ = monitor.close_position("position", wallet_address="wallet")
    assert close_result["success"] is True

    # A stale/empty portfolio response must never turn a failed close into success.
    for live in (True, None, False):
        with patch.object(monitor, "queue_settlement"), \
             patch.object(monitor, "run_command_json", return_value=({"success": False}, "timeout")), \
             patch.object(monitor, "position_live_onchain", return_value=live), \
             patch.object(monitor, "position_gone_onchain", return_value=True) as indexer:
            closed, _ = monitor.close_position("position", wallet_address="wallet")
        assert closed["success"] is (live is False)
        indexer.assert_not_called()

    # A failed swap remains queued across worker runs and clears only after a zero balance read.
    with tempfile.TemporaryDirectory() as tmp, patch.object(monitor, "SETTLEMENT_DIR", tmp), \
         patch.object(monitor, "get_position_metadata", return_value={"base_mint": "TOKEN"}), \
         patch.object(monitor, "get_wallet_address", return_value="wallet"), \
         patch.object(monitor, "position_live_onchain", return_value=False), \
         patch.object(monitor, "get_meteora_portfolio_positions", return_value=({}, None)):
        monitor.queue_settlement("position")
        path = Path(tmp) / "position.json"
        with patch.object(monitor, "run_command_json", side_effect=[({"balance": 10}, None), ({"success": False}, "slippage")]):
            monitor.settle_pending()
        assert path.exists()
        with patch.object(monitor, "run_command_json", side_effect=[({"balance": 10}, None), ({"success": True}, None), ({"balance": 0}, None)]):
            monitor.settle_pending()
        assert not path.exists()
        # Route/fee failures remain inventory, with backoff and no global entry
        # block. Unknown RPC failures must remain pending instead.
        for reason in ("swap_no_route", "net_recovery_below_floor", "net_recovery_unmeasured"):
            monitor.queue_settlement("position")
            with patch.object(monitor, "run_command_json", side_effect=[({"balance": 0.000001}, None), ({"success": False, "reason": reason}, None)]) as run:
                monitor.settle_pending()
            assert run.call_args_list[1].args[0].endswith(" 15 300 1")
            item = json.loads(path.read_text())
            assert item["state"] == ("pending" if reason == "net_recovery_unmeasured" else "deferred")
            if item["state"] == "deferred":
                with patch.object(monitor, "run_command_json") as run:
                    monitor.settle_pending()
                    run.assert_not_called()
                item["last_attempt"] = 0
                path.write_text(json.dumps(item))
                with patch.object(monitor, "run_command_json", return_value=({"balance": 0}, None)):
                    monitor.settle_pending()
                assert not path.exists()
            else:
                path.unlink()

    # Empty indexer results never authorize deletion of a live/unknown position,
    # including orphan metadata and its risk-state keys.
    class EmptyPortfolio:
        def read(self): return b'{"pools": []}'
        def __enter__(self): return self
        def __exit__(self, *args): return False
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, ".env").write_text("SOLANA_PUBLIC_KEY=wallet\n")
        for live in (True, None, False):
            commands = []
            def redis(cmd):
                commands.append(cmd)
                if "smembers" in cmd: return "active", "", 0
                if " keys " in cmd: return "sol:dlmm:position:orphan\nsol:dlmm:position:orphan:oor_since\nsol:dlmm:position:orphan:ai_hold_until", "", 0
                if " get " in cmd: return '{"deployed_at": 1}', "", 0
                return "", "", 0
            with patch.object(pipeline, "PROFILE_DIR", tmp), patch.object(pipeline, "run_command", side_effect=redis), \
                 patch.object(pipeline.urllib.request, "urlopen", return_value=EmptyPortfolio()), \
                 patch.object(pipeline, "position_live_onchain", return_value=live) as chain:
                pipeline.reconcile_redis_vs_meteora()
            writes = [c for c in commands if " srem " in c or " del " in c]
            assert bool(writes) is (live is False)
            assert chain.call_count == 2  # one read per position, shared with risk keys

    # Run the actual monitor missing-position branch with the same three RPC verdicts.
    tree = ast.parse(Path(monitor.__file__).read_text())
    branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                  and ast.unparse(n.test) == "not bp and (not is_dry_run_stored)")
    wrapper = ast.Module(body=[ast.For(target=ast.Name(id="tick",ctx=ast.Store()),
        iter=ast.List(elts=[ast.Constant(1)],ctx=ast.Load()),body=[branch],orelse=[])],type_ignores=[])
    for live in (True, None, False):
        commands=[]
        ns=dict(bp=None,is_dry_run_stored=False,api_available=True,meta={"deployed_at":1},
                now=10000,pos_addr="position",pair="TOKEN-SOL",position_live_onchain=lambda _:live,
                run_command=commands.append,print=lambda *args:None)
        exec(compile(ast.fix_missing_locations(wrapper),"monitor-prune","exec"),ns)
        assert bool(commands) is (live is False)

    # Execute startup through reconciliation: an empty active set must still discover
    # funded positions, and a lost set member must not reset existing trailing state.
    main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    start = next(i for i,n in enumerate(main_node.body) if isinstance(n, ast.Assign)
                 and ast.unparse(n) == "active_positions = get_active_positions()")
    end = next(i for i,n in enumerate(main_node.body[start:], start) if isinstance(n, ast.For)
               and ast.unparse(n.target) == "pos_addr")
    recovery = ast.Module(body=main_node.body[start:end], type_ignores=[])
    for initial in ([], ["position"]):
        for existing in (None, {"peak_pnl": 20, "deployed_at": 1}):
            for report_only in (False, True):
                commands=[]
                ns=dict(get_active_positions=lambda:initial,
                    get_position_metadata=lambda _:existing,
                    get_wallet_address=lambda:"wallet",
                    get_meteora_portfolio_positions=lambda _:({"position": {
                        "pool":"pool", "balances_sol":0.11}}, None),
                    recover_position_metadata=lambda *_:{"pair":"TOKEN-SOL", "mode":"turnover",
                        "deployed_at":1,"size_sol":0.1,"entry_price":2},
                    run_command=commands.append, cli=SimpleNamespace(report_only=report_only),
                    print=lambda *a:None, time=SimpleNamespace(time=lambda:10000), json=json)
                exec(compile(recovery,"monitor-recovery","exec"),ns)
                sets=[c for c in commands if " set " in c]
                adds=[c for c in commands if " sadd " in c]
                assert bool(sets) is (not report_only and existing is None)
                assert bool(adds) is (not report_only and (not initial or existing is None))
                if sets:
                    assert '"deployed_at": 1' in sets[0] and '"size_sol": 0.1' in sets[0]

    out, error, code = monitor.run_command("sleep 5", timeout=0.02)
    assert code == -1 and "process group terminated" in error

    pos = "2G6rKc9ssZZxVagZpfKKfph8UARmAbh9GjpV9R3uxGGe"
    commands = []
    with patch.object(monitor, "get_position_metadata", return_value={"pool": "pool"}), \
         patch.object(monitor, "run_command_json", return_value=({"success": True, "in_range": True, "unclaimed_fees_sol": 0.001}, None)), \
         patch.object(monitor, "run_command", side_effect=lambda cmd: (commands.append(cmd) or ("1", "", 0))), \
         patch.object(monitor, "log_hold") as journal:
        monitor.set_ai_hold(pos, 30, "productive LP")
    assert "EVAL" in commands[0]
    journal.assert_called_once()

    # Execute the production hold/indicator section, not a mirrored decision.
    source = Path(monitor.__file__).read_text()
    start = source.index("        close_reason, protected_risk_exit =")
    stop = source.index("        # Execute close if triggered", start)
    section = "for _ in [0]:\n" + textwrap.indent(textwrap.dedent(source[start:stop]), "    ")
    trailing = "Trailing Take-Profit hit (Peak: 2.79%, Current: 1.84%)"
    for mode in ("turnover", "pulse"):
        for pnl, h1, expected in [(1.84, 0, "Trailing"), (-3.38, None, "Downtrend"),
                                   (-3.38, -10, "Sustained"), (-9.23, -10, "Hard Stop-Loss")]:
            reason = "Hard Stop-Loss hit (-9.23%)" if pnl == -9.23 else trailing
            def forbidden(*args, **kwargs):
                raise AssertionError("Risk exit reached a discretionary veto")
            ns = dict(vars(monitor), close_reason=reason, meta={"mode": mode}, pnl_pct=pnl,
                      price_change_h1=h1, emergency_close=False, params={"INDICATORS_ENABLED": True},
                      cli=SimpleNamespace(report_only=False, no_enforce=True),
                      run_command=forbidden, check_local_indicators=forbidden)
            exec(compile(section, monitor.__file__, "exec"), ns)
            assert ns["protected_risk_exit"] and ns["close_reason"].startswith(expected)
    # Discretionary thesis-mode trailing still honors a rejecting indicator.
    ns.update(meta={"mode": "multiday"}, pnl_pct=1.84, close_reason=trailing,
              is_tight_tp_pos=False, pair="TEST", pool="pool", pos_addr="position", now=100,
              run_command=lambda *args, **kwargs: ("", "", 0),
              check_local_indicators=lambda *args: False)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(section, monitor.__file__, "exec"), ns)
    assert ns["close_reason"] is None
    assert monitor.protect_tight_exit("RUG velocity dump", "pulse", -20, -30, True) == ("RUG velocity dump", True)
    # Missing profit signal above the risk floor must not invent an exit.
    assert monitor.protect_tight_exit(None, "pulse", 0.2, None) == (None, False)
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / "memories/dlmm_entries"
        folder.mkdir(parents=True)
        context = dict(position=pos, pool="pool", mode="turnover", strategy="turnover_rebalance",
                       recenter_of="root", deployed_at=100, size_sol=0.1)
        (folder / (pos + ".json")).write_text(json.dumps(context))
        with patch.object(monitor, "PROFILE_DIR", tmp):
            assert monitor.recover_position_metadata(pos, "pool") == context
    print("PERPSPAD exit precedence, discretionary holds and timeout provenance passed")


if __name__ == "__main__":
    main()
