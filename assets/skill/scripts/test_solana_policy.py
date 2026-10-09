"""Offline regression check: python3 assets/skill/scripts/test_solana_policy.py."""
import argparse
import ast
import shlex
import contextlib
import importlib.util
import io
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
import tempfile
import textwrap
from unittest.mock import patch

import dlmm_pipeline as pipeline
import dlmm_stats as stats
import dlmm_weights as weights_module
import dlmm_realized as realized_module
from dlmm_realized import apply_realized


def main():
    # Audit data outages are unknown; measured risk/concentration still rejects.
    spec = importlib.util.spec_from_file_location("token_audit", Path(__file__).resolve().parents[1] /
                                                 "solana-web3-scripts/audit_token.py")
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    mint = "1" * 32
    for risk, metrics, verdict in [
        (None, {}, "UNKNOWN"), (True, {}, "UNKNOWN"), (-1, {}, "UNKNOWN"),
        (0, {}, "PASS"), (1, {}, "PASS"), (3, {}, "PASS"), (4, {}, "FAIL"),
        (None, {"holdersDevPercent": 31, "holdersTop10Percent": "bad"}, "FAIL"),
        (0, {"holdersTop10Percent": 96}, "FAIL"),
        (0, {"holdersDevPercent": 30, "holdersTop10Percent": 95}, "PASS"),
        (0, {"holdersDevPercent": 0, "holdersTop10Percent": 0}, "PASS"),
        (0, {"holdersDevPercent": "NaN", "holdersTop10Percent": True}, "PASS"),
    ]:
        stdout = io.StringIO()
        responses = [(json.dumps({"success": True, "data": {
            "hasResult": True, "isSupported": True, "riskLevel": risk}}), ""),
            (json.dumps({"success": True, "data": [{"contractAddress": mint, **metrics}]}), "")]
        with patch.object(sys, "argv", ["audit_token.py", mint]), \
                patch.object(audit, "run_command", side_effect=responses) as reads, \
                contextlib.redirect_stdout(stdout):
            try:
                audit.main()
            except SystemExit as exc:
                assert exc.code == 0
        result = json.loads(stdout.getvalue())
        assert result["verdict"] == verdict, result
        if verdict != "FAIL":
            assert result["risk_level"] == (risk if type(risk) is int and risk >= 0 else None)
            if not metrics or "NaN" in str(metrics):
                assert result["dev_pct"] is None and result["top10_pct"] is None
        assert reads.call_count == (1 if risk == 4 else 2)
    assert audit.percentage(0) == 0 and audit.percentage("30.5") == 30.5
    assert all(audit.percentage(v) is None for v in [None, True, "NaN", "Infinity", -1, 101, "bad"])
    with patch.object(audit.subprocess, "run", side_effect=subprocess.TimeoutExpired("curl", 12)) as read:
        assert audit.run_command("curl")[1]
        assert read.call_args.kwargs["timeout"] == 12
    with patch.object(sys, "argv", ["audit_token.py", "bad'; echo injected"]), \
            patch.object(audit, "run_command") as read, contextlib.redirect_stdout(io.StringIO()):
        try:
            audit.main()
            raise AssertionError("invalid mint accepted")
        except SystemExit as exc:
            assert exc.code == 1
        read.assert_not_called()
    # AI ranking context must use local reads only, retain unknown metadata,
    # and return before any financial path or deterministic picker runs.
    address = "1" * 32
    replies = [([address], None), ([json.dumps({"weights":{"score":1.2}}),
                                  json.dumps({"pool":"pool", "mode":"pulse", "secret":"omit"})], None)]
    with patch.object(pipeline, "run_command_json", side_effect=replies) as reads:
        context = pipeline.ai_pick_context("pulse")
        assert context["open_mode_positions"] == 1 and context["positions_complete"]
        assert context["positions"] == [{"pool":"pool", "mode":"pulse"}]
        assert context["signal_weights"]["weights"]["score"] == 1.2
        assert len(reads.call_args_list) == 2
        assert all(shlex.split(c.args[0])[:3] == ["redis-cli", "-e", "--json"] for c in reads.call_args_list)
    with patch.object(pipeline, "run_command_json", side_effect=[([address],None),([None,None],None)]):
        context = pipeline.ai_pick_context("pulse")
        assert context["open_mode_positions"] is None and not context["positions_complete"]
        assert context["signal_weights"] is None
    with patch.object(pipeline, "run_command_json", side_effect=[([],None),([None],None)]):
        context = pipeline.ai_pick_context("pulse")
        assert context["open_mode_positions"] == 0 and context["positions_complete"]
    for replies in [[(None,"Redis error")], [([address],None),([],None)], [(["bad address"],None)]]:
        with patch.object(pipeline, "run_command_json", side_effect=replies):
            try: pipeline.ai_pick_context("pulse")
            except ValueError: pass
            else: raise AssertionError("Unmeasured context accepted")
    with patch.object(sys, "argv", ["dlmm_pipeline.py","--pick-context","--mode","pulse"]), \
            patch.object(pipeline, "ai_pick_context", return_value={"mode":"pulse"}), \
            patch.object(pipeline, "reconcile_redis_vs_meteora", side_effect=AssertionError("API called")), \
            patch.object(pipeline, "apply_batch_conviction", side_effect=AssertionError("AI pick replaced")), \
            contextlib.redirect_stdout(io.StringIO()) as output:
        pipeline.main()
        assert json.loads(output.getvalue()) == {"mode":"pulse"}
    from dlmm_evaluate import delivery_outcomes
    with tempfile.TemporaryDirectory() as directory:
        profile=Path(directory);db=sqlite3.connect(profile/"state.db")
        db.execute("CREATE TABLE sessions (id TEXT,source TEXT,chat_id TEXT,started_at REAL,ended_at REAL)")
        db.execute("INSERT INTO sessions VALUES ('session','webhook','webhook:dlmm-signal:delivery',101,120)");db.commit();db.close()
        journal=profile/"deliveries.jsonl"
        journal.write_text('\n'.join(json.dumps(r) for r in [
            {"delivery_id":"delivery","stage":"prepared","observed_at":100},
            {"delivery_id":"delivery","stage":"accepted","observed_at":102}])+"\n")
        before=delivery_outcomes(profile,journal,90,110)["deliveries"][0]
        assert before["session_state"]=="not_ended_at_cutoff" and before["transport"]=="accepted"
        after=delivery_outcomes(profile,journal,90,130)["deliveries"][0]
        assert after["session_state"]=="ended" and not after["execution_verified"]
        assert delivery_outcomes(profile,journal,90,101)["deliveries"][0]["transport"]=="unconfirmed"
    # Neither a mark nor realized LP PnL proves cash after swap fees and rent.
    for row in [
        {"pnl_basis":"pre_swap_mark","pnl_sol":.1},
        {"pnl_basis":"realized","pnl_sol":None,"pnl_pct":20},
        {"pnl_basis":"realized","pnl_sol":float("nan")},
        {"pnl_basis":"realized","pnl_sol":float("inf")},
        {"pnl_basis":"realized","pnl_sol":True},
        {"pnl_basis":"realized","pnl_sol":0},
        {"pnl_basis":"realized","pnl_sol":.1},
    ]:
        assert weights_module.outcome_sol(row) is None
    cash = lambda lo, hi: {"outcome_basis": weights_module.OUTCOME_BASIS,
                           "cash_pnl_lower_sol": lo, "cash_pnl_upper_sol": hi}
    assert weights_module.outcome_sol(cash(.001, .002)) == .001
    assert weights_module.outcome_sol(cash(-.002, -.001)) == -.001
    assert weights_module.outcome_sol(cash(0, 0)) == 0
    assert weights_module.outcome_sol(cash(-.001, 0)) == 0
    for lo, hi in [(-.001, .001), (0, .001), (.002, .001), (None, .1),
                   (True, .1), (0, False), (float("nan"), .1), (0, float("inf"))]:
        assert weights_module.outcome_sol(cash(lo, hi)) is None
    assert weights_module.outcome_sol({**cash(.001, .002), "outcome_basis":"realized"}) is None
    # Exercise the actual writer envelope through the fallback reader and ranker.
    for stored in [{"weights": {"holders": 1.4}, "lifts": {"holders": .2}}, {"holders": 1.4}]:
        with patch.object(pipeline, "run_command", return_value=(json.dumps(stored), "", 0)):
            assert pipeline.load_signal_weights() == {"holders": 1.4}
            candidates = [{"name":"lower", "score":70, "holders":1000},
                          {"name":"higher", "score":70, "holders":2000}]
            ranked = pipeline.apply_batch_conviction(candidates, "turnover")
            assert ranked[0]["score"] == 70 and abs(ranked[1]["score"] - 74) < 1e-9
    for stored in [None, [], {"weights": None}, {"weights": {
            "holders": True, "score": "1.4", "organic_score": float("nan"),
            "fee_tvl_ratio": float("inf"), "volume_tvl_ratio": 2.6,
            "global_fees_sol": .2, "ignored": 1.4}}]:
        with patch.object(pipeline, "run_command", return_value=(json.dumps(stored), "", 0)):
            assert pipeline.load_signal_weights() == {}
    # Equal evidence cannot favor whichever pool happens to arrive later.
    # Compare every input permutation, with both rewards and penalties.
    import itertools
    for weight in [1.4, .6]:
        with patch.object(pipeline,"load_signal_weights",return_value={"holders":weight}):
            records=[{"name":name,"score":70,"holders":holders}
                     for name,holders in [("low",100),("tie-a",200),("tie-b",200),("high",300)]]
            expected=None
            for order in itertools.permutations(records):
                result=pipeline.apply_batch_conviction([dict(c) for c in order],"turnover")
                scores={c["name"]:c["score"] for c in result}
                if expected is None: expected=scores
                assert scores==expected
                assert scores["tie-a"]==scores["tie-b"]
                assert abs(scores["tie-a"]-(70+(weight-1)*5))<1e-9
                assert scores["low"]==70 and abs(scores["high"]-(70+(weight-1)*10))<1e-9
            # Constant and unavailable values must not move conviction floors.
            for values in [[100,100,100],[100,None,True,float("nan"),float("inf"),"100"]]:
                result=pipeline.apply_batch_conviction([{"name":str(i),"score":70,"holders":v}
                                                       for i,v in enumerate(values)],"turnover")
                assert len(result)==len(values) and all(c["score"]==70 for c in result)
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);(root/"memories").mkdir()
        closes=root/"memories/dlmm_closes.jsonl"
        records=[{"position":p,"ts":time.time(),"signal":{"score":90},"pnl_sol":.1,"pnl_basis":"realized"}
                 for p in ["loss", "win", "ambiguous", "leg1", "leg2", "pending", "missing", "dry", "old"]]
        records[-2]["dry_run"] = True
        records[-1]["ts"] = time.time() - 61 * 86400
        records.append({**records[0], "signal":{"score":45}})
        closes.write_text("".join(json.dumps(r)+"\n" for r in records))
        chains=[{"root_chain_id":p,"positions": ["leg1","leg2"] if p=="recenter" else [p],
                 "accounting_status":"incomplete" if p=="pending" else "settled_cash",
                 "wallet_delta_lamports":amount} for p,amount in
                [("loss",-120),("win",-90),("ambiguous",-99),("recenter",-100),("pending",-100),("dry",-90),("old",-90)]]
        def refund_group(ids):
            selected=[c for c in chains if c["root_chain_id"] in ids]
            return {"root_chain_ids":ids, "refund_signatures":["refund-"+ids[0]],
                    "refund_components":[{"signature":"refund-"+ids[0],
                       "gross_by_root":{p:100 for p in ids},"fee_lamports":5}],
                    "cash_with_matched_refunds_sol":(sum(c["wallet_delta_lamports"] for c in selected)+100*len(ids)-5)/1e9}
        ledger={"chains":chains,"rent_refund_groups":[refund_group(["loss","win","ambiguous","recenter"]),
                 refund_group(["pending"]),refund_group(["dry"]),refund_group(["old"])]}
        with patch.object(weights_module,"PROFILE_DIR",str(root)), patch.object(weights_module,"CLOSES_PATH",str(closes)), \
                patch.object(weights_module,"report",return_value=ledger):
            eligible=weights_module.load_recent_closes()
        assert [r["position"] for r in eligible]==["loss","win"]
        assert weights_module.outcome_sol(eligible[0]) == -20/1e9
        assert weights_module.outcome_sol(eligible[1]) == 5/1e9
        assert eligible[0]["signal"]["score"] == 45  # One example per root, latest close.
        assert eligible[0]["pnl_sol"] == .1  # Preserve the separate LP evidence.
        output_path=root/"weights.json"
        with patch.object(weights_module,"load_recent_closes",return_value=eligible), \
                patch.object(weights_module,"WEIGHTS_PATH",str(output_path)), \
                patch.object(weights_module,"MIN_SAMPLES",2), \
                patch.object(weights_module,"run_command",return_value="OK") as publish:
            assert weights_module.recalculate(quiet=True)
        learned=json.loads(output_path.read_text())
        assert learned["outcome_basis"]==weights_module.OUTCOME_BASIS
        assert learned["history"][-1]["wins"]==learned["history"][-1]["losses"]==1
        assert learned["weights"]["score"] == 1.525
        assert json.loads(shlex.split(publish.call_args.args[0])[-1])["outcome_basis"]==weights_module.OUTCOME_BASIS
        assert closes.read_text()=="".join(json.dumps(r)+"\n" for r in records)
    # Re-label once on migration; the six-hour guard still applies afterwards.
    for basis, scope, called in [(None,None,True),(weights_module.OUTCOME_BASIS,None,True),
                                (weights_module.OUTCOME_BASIS,weights_module.WEIGHT_SCOPE,False)]:
        with patch.object(sys,"argv",["dlmm_weights.py","--quiet"]), \
                patch.object(weights_module,"load_weights",return_value={"last_recalc_ts":time.time(),"outcome_basis":basis,"weight_scope":scope}), \
                patch.object(weights_module,"recalculate") as recalc:
            weights_module.main()
            assert recalc.called == called
    # Opposite fee relationships must remain opposite after publication and
    # selection by both pickers; the larger turnover cohort cannot train pulse.
    independent=[]
    for mode, count in [("pulse",10),("turnover",30)]:
        for i in range(count):
            win=i%2==0
            value=10 if win == (mode=="turnover") else 1
            independent.append({**(cash(.001,.001) if win else cash(-.001,-.001)),
                                "mode":mode,"signal":{"fee_tvl_ratio":value}})
    grouped=weights_module.mode_weights(independent,{})
    assert grouped["pulse"]["weights"]["fee_tvl_ratio"] < 1
    assert grouped["turnover"]["weights"]["fee_tvl_ratio"] > 1
    assert grouped["casual"]["status"] == "insufficient_samples"
    pulse_only=[r for r in independent if r["mode"]=="pulse"]
    assert weights_module.mode_weights(pulse_only,{})["pulse"]==grouped["pulse"]
    scarce=weights_module.mode_weights(pulse_only[:9],grouped)
    assert scarce["pulse"]["status"]=="insufficient_samples" and not scarce["pulse"]["weights"]
    one_class=[dict(r,**cash(.001,.001)) for r in pulse_only]
    assert weights_module.mode_weights(one_class,{})["pulse"]["status"]=="insufficient_samples"
    assert weights_module.mode_weights(independent,grouped)["pulse"]["weights"]["fee_tvl_ratio"] < grouped["pulse"]["weights"]["fee_tvl_ratio"]
    # Malformed numeric values cannot poison a mode's finite weight envelope.
    for invalid in [True,float("nan"),float("inf")]:
        bad={**cash(.001,.001),"mode":"pulse","signal":{"fee_tvl_ratio":invalid}}
        assert weights_module.mode_weights(independent+[bad],{})["pulse"]["weights"] == grouped["pulse"]["weights"]
    envelope={"weights":{"fee_tvl_ratio":2.5},"weight_scope":weights_module.WEIGHT_SCOPE,
              "outcome_basis":weights_module.OUTCOME_BASIS,"by_mode":grouped}
    for mode in weights_module.MODES:
        with patch.object(pipeline,"run_command",return_value=(json.dumps(envelope),"",0)):
            selected=pipeline.load_signal_weights(mode)
            assert selected==grouped[mode]["weights"]
            candidates=[{"name":"low","score":70,"fee_tvl_ratio":1},
                        {"name":"high","score":70,"fee_tvl_ratio":10}]
            ranked=pipeline.apply_batch_conviction(candidates,mode)
            if mode=="pulse": assert ranked[1]["score"] < ranked[0]["score"]
            if mode=="turnover": assert ranked[1]["score"] > ranked[0]["score"]
        with patch.object(pipeline,"run_command_json",side_effect=[([],None),([json.dumps(envelope)],None)]):
            assert pipeline.ai_pick_context(mode)["signal_weights"]["weights"]==selected
    with patch.object(weights_module,"run_command",return_value="OK") as published, \
            tempfile.TemporaryDirectory() as directory, \
            patch.object(weights_module,"WEIGHTS_PATH",str(Path(directory)/"weights.json")):
        weights_module.save_weights(dict(envelope,last_recalc="now"))
        payload=json.loads(shlex.split(published.call_args.args[0])[-1])
        assert payload["by_mode"]==grouped and payload["weight_scope"]==weights_module.WEIGHT_SCOPE
    # Proved cash can disagree with the mark; legacy/unresolved marks retain
    # the existing conservative ranking penalty without being called cash.
    with patch.object(pipeline, "load_signal_weights", return_value={}):
        for fields, expected in [
            ({"prior_pnl_basis":"matched_refund_cash", "prior_net_pnl_sol":-.02, "prior_mark_pnl_sol":.01}, "prior_cash_loss-20"),
            ({"prior_pnl_basis":"pre_swap_mark_only", "prior_mark_pnl_sol":-.01}, "prior_mark_loss-20"),
            ({"prior_net_pnl_sol":-.01}, "prior_mark_loss-20"),
            ({"prior_pnl_basis":"matched_refund_cash", "prior_net_pnl_sol":0, "prior_mark_pnl_sol":-.01}, None),
            ({"prior_pnl_basis":"pre_swap_mark_only"}, None),
            ({"prior_pnl_basis":"matched_refund_cash_bounds", "prior_cash_lower_sol":-.02, "prior_cash_upper_sol":-.01, "prior_mark_pnl_sol":.01}, "prior_bounded_cash_loss-20"),
            ({"prior_pnl_basis":"matched_refund_cash_bounds", "prior_cash_lower_sol":.001, "prior_cash_upper_sol":.002, "prior_mark_pnl_sol":-.01}, None),
            ({"prior_pnl_basis":"matched_refund_cash_bounds", "prior_cash_lower_sol":-.01, "prior_cash_upper_sol":0, "prior_mark_pnl_sol":-.01}, "prior_mark_loss-20"),
            ({"prior_pnl_basis":"matched_refund_cash_bounds", "prior_cash_lower_sol":0, "prior_cash_upper_sol":.001, "prior_mark_pnl_sol":-.01}, None),
            ({"prior_pnl_basis":"matched_refund_cash_bounds", "prior_cash_lower_sol":True, "prior_cash_upper_sol":.001, "prior_mark_pnl_sol":-.01}, "prior_mark_loss-20"),
            ({"prior_pnl_basis":"matched_refund_cash_bounds", "prior_cash_lower_sol":float("nan"), "prior_cash_upper_sol":.001, "prior_mark_pnl_sol":-.01}, "prior_mark_loss-20"),
            ({"prior_pnl_basis":"matched_refund_cash_bounds", "prior_cash_lower_sol":.01, "prior_cash_upper_sol":-.01, "prior_mark_pnl_sol":-.01}, "prior_mark_loss-20"),
        ]:
            candidate = {"name":"P", "score":100, **fields}
            pipeline.apply_batch_conviction([candidate])
            losses = [n for n in candidate["_conviction_notes"] if n.startswith("prior_")]
            assert losses == ([expected] if expected else []), losses
    # Exercise the real shell loop: slow reconciliation must not stall risk
    # checks or launch a duplicate report worker on every tick.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        scripts = root / "profile/skills/solana-dlmm/scripts"
        scripts.mkdir(parents=True)
        (root / "profile/.env").write_text("DLMM_STATS_HOUR=09\n")
        source = Path(__file__).with_name("dlmm_monitor_loop.sh").read_text()
        loop = scripts / "loop.sh"
        loop.write_text(source.replace('STATS_STAMP="/tmp/dlmm_stats_last_sent"',
                                       f'STATS_STAMP="{root}/stamp"'))
        binaries = root / "bin"
        binaries.mkdir()
        log = root / "calls"
        commands = {
            "python3": f"#!{sys.executable}\n" + textwrap.dedent("""\
                import os, sys, time
                name = os.path.basename(sys.argv[1])
                kind = name + (' settlement' if '--settle-pending' in sys.argv else '')
                with open(os.environ['AZIMUTH_TEST_LOG'], 'a') as out:
                    print(kind, file=out)
                if name == 'dlmm_realized.py':
                    time.sleep(10)
                """),
            "sleep": "#!/bin/sh\nexec /bin/sleep 0.03\n",
            "date": "#!/bin/sh\ncase \"$*\" in *%H*) echo 09;; *) echo 2099-01-01;; esac\n",
        }
        for name, content in commands.items():
            command = binaries / name
            command.write_text(content)
            command.chmod(0o755)
        env = {**os.environ, "PATH": str(binaries) + ":" + os.environ['PATH'],
               "AZIMUTH_TEST_LOG": str(log)}
        process = subprocess.Popen(['bash', str(loop)], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   start_new_session=True)
        try:
            deadline = time.monotonic() + 3
            calls = []
            while time.monotonic() < deadline:
                calls = log.read_text().splitlines() if log.exists() else []
                if calls.count('dlmm_monitor.py') >= 3 and 'dlmm_realized.py' in calls:
                    break
                time.sleep(0.02)
            assert calls.count('dlmm_monitor.py') >= 3, calls
            assert calls.count('dlmm_realized.py') == 1, calls
            assert 'dlmm_stats.py' not in calls, calls
        finally:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()

    # The webhook consumes one context command; live holding/cooldown checks
    # still belong to the pipeline, with AI selection remaining from-signal.
    subscription = json.loads((Path(__file__).resolve().parents[2] /
                               "hermes/webhook_subscriptions.json").read_text())
    prompt = subscription['dlmm-signal']['prompt']
    assert subscription['dlmm-signal']['toolsets'] == ['terminal']
    assert '{payload_json}' in prompt and '__raw__' not in prompt
    assert 'set `workdir` to `__PROFILE__`' in prompt
    assert '--pick-context --mode MODE' in prompt and 'signal_weights from STEP 1' in prompt
    assert 'redis-cli' not in prompt and '--from-signal' in prompt

    # Missing/invalid API economics must be retried, while measured zero is valid.
    with tempfile.TemporaryDirectory() as directory:
        target = str(Path(directory) / "realized.jsonl")
        position = dict(positionAddress="p", closedAt=200, createdAt=100, isClosed=True,
                        pnlSol="0", pnlSolPctChange="0", allTimeDeposits={"total": {"sol": "0.1"}},
                        allTimeWithdrawals={"total": {"sol": "0.1"}}, allTimeFees={"total": {"sol": "0"}})
        with patch.object(realized_module, "REALIZED_PATH", target), \
             patch.object(realized_module, "load_realized", side_effect=lambda: {} if not Path(target).exists()
                          else {r["position"]: r for r in map(json.loads, Path(target).read_text().splitlines())}), \
             patch.object(realized_module.time, "time", return_value=300), \
             patch.object(realized_module, "fetch_pools", return_value=[dict(poolAddress="pool", lastClosedAt=200)]):
            invalid = [dict(position, pnlSol=v) for v in [None, "bad", "NaN", "Infinity", True]]
            invalid += [dict(position, pnlSolPctChange=None), dict(position, allTimeFees=None),
                        dict(position, allTimeWithdrawals={}), dict(position, isClosed=False),
                        dict(position, allTimeDeposits={"total": {"sol": "0"}})]
            for row in invalid:
                with patch.object(realized_module, "fetch_closed_positions", return_value=[row]):
                    assert realized_module.backfill("wallet", 1, quiet=True) == 0
            with patch.object(realized_module, "fetch_closed_positions", return_value=[position]):
                assert realized_module.backfill("wallet", 1, quiet=True) == 1
                assert realized_module.backfill("wallet", 1, quiet=True) == 0
            saved = json.loads(Path(target).read_text())
            assert saved["realized_sol"] == 0 and saved["fee_sol"] == 0

    # Pulse freshness must compare the same five-minute window as screening.
    for ratio, address, expected in [
        (0.05, "pool", 0.05), ({"5m": 0.05, "24h": 100}, "pool", 0.05),
        ({"24h": 100}, "pool", None), (0, "pool", 0),
        (float("nan"), "pool", None), (-1, "pool", None),
        (True, "pool", None), (0.05, "different-pool", None), (None, "pool", None),
    ]:
        payload = json.dumps({"data": [{"pool_address": address, "fee_tvl_ratio": ratio}]}).encode()
        with patch.object(pipeline.urllib.request, "urlopen", return_value=io.BytesIO(payload)) as fetch:
            assert pipeline.fetch_live_fee_tvl("pool", "5m") == expected
            query = pipeline.urllib.parse.parse_qs(pipeline.urllib.parse.urlparse(fetch.call_args.args[0].full_url).query)
            assert query["timeframe"] == ["5m"] and query["filter_by"] == ["pool_address=pool"]
    payload = json.dumps({"data": [{"pool_address": "pool", "fee_tvl_ratio": 0.05}]}).encode()
    with patch.dict(pipeline.os.environ, {"DRY_RUN": "false"}), \
         patch.object(pipeline.urllib.request, "urlopen", return_value=io.BytesIO(payload)), \
         patch.object(pipeline, "get_momentum", return_value=(0, 0, 0, 0)):
        assert "dropped 75.0%" in pipeline.predeploy_live_gate_reject(
            {"pool": "pool", "name": "test", "base_mint": "mint", "fee_tvl_ratio": 0.2}, 0.1, "5m")
    assert pipeline.compute_deploy_amount(0.30718357) == 0
    assert pipeline.compute_deploy_amount(0.349) == 0
    assert pipeline.compute_deploy_amount(0.35) == 0.1
    assert pipeline.compute_deploy_amount(0.461554584) == 0.12

    # The risk/override paths must never execute a token swap. Only the explicit
    # manual-cleanup branch may do so; pending settlement runs in its own worker.
    monitor = ast.parse(Path(__file__).with_name("dlmm_monitor.py").read_text())
    main_fn = next(n for n in monitor.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    main_fn.body = [n for n in main_fn.body if not (isinstance(n, ast.If) and ast.unparse(n.test) == "cli.cleanup_tokens")]
    for node in ast.walk(main_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run_command_json":
            assert " swap " not in ast.unparse(node)
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

    # Execute the actual shared gate before the legacy token-only entry swap.
    # A healthy first pair cannot hide a dumping deepest pair; explicit pool
    # overrides also retain the gate, including the batch CLI path.
    source = Path(pipeline.__file__).read_text()
    start = source.index("    # 6. Deploy Position")
    end = source.index("    entry_context =", start)
    entry = textwrap.dedent(source[start:end])
    dex = {"pairs": [{"liquidity":{"usd":100}, "priceChange":{"m5":0}},
                     {"liquidity":{"usd":46000}, "priceChange":{"m5":-6}}]}
    for batch, explicit_pool in [(False, None), (True, "yield")]:
        ns = dict(vars(pipeline), winner=dict(candidate, volatility=1, bin_step=100, base_symbol="TOKEN"),
                  batch_mode=batch, cli=argparse.Namespace(strategy="single_sided_reseed", pool=explicit_pool),
                  params={}, deploy_sol=0.1, timeframe="30m", mode="turnover")
        with patch.object(pipeline.urllib.request, "urlopen", return_value=contextlib.nullcontext(io.StringIO(json.dumps(dex)))), \
                patch.object(pipeline, "run_swap_with_retry", side_effect=AssertionError("swap before rejection")) as swap, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            ns["run_swap_with_retry"] = swap
            try: exec(compile(entry, pipeline.__file__, "exec"), ns)
            except SystemExit as exc: assert exc.code == 0
            else: raise AssertionError("dumping deepest pair accepted")
            assert "live gate rejected: dumping -6.00%" in output.getvalue()
            swap.assert_not_called()
    # Healthy deepest quotes pass even when pairs[0] is an illiquid corpse.
    dex["pairs"][0]["priceChange"]["m5"]=-99
    dex["pairs"][1]["priceChange"]["m5"]=0
    with patch.object(pipeline.urllib.request, "urlopen", return_value=contextlib.nullcontext(io.StringIO(json.dumps(dex)))), \
            patch.object(pipeline, "fetch_live_fee_tvl", return_value=2), \
            patch.object(pipeline, "get_price_impact_sol_to_token", return_value=0):
        assert pipeline.predeploy_live_gate_reject(candidate, .1, "30m") is None

    # Execute the actual selection loop, including its live gate and continue.
    source = Path(pipeline.__file__).read_text()
    start = source.index("        winner = None", source.index("# Auto-pick:"))
    end = source.index("    if batch_mode:", source.index("        if not winner:", start))
    section = textwrap.dedent(source[start:end])
    siblings = [dict(c, volatility=1, bin_step=100) for c in pools[:2]]
    ns = dict(vars(pipeline), valid_candidates=siblings, batch_mode=True,
              cli=argparse.Namespace(strategy="sol_bidask"), params={},
              mode="turnover", deploy_sol=0.1, timeframe="30m",
              check_bin_coverage=lambda *args: {"deployable": True})
    with patch.object(pipeline, "get_momentum", return_value=(0, 0, 0, 0)), \
         patch.object(pipeline, "fetch_live_fee_tvl", side_effect=[0.1, 1.4]), \
         patch.object(pipeline, "get_price_impact_sol_to_token", return_value=0.1):
        exec(compile(section, pipeline.__file__, "exec"), ns)
    assert ns["winner"]["pool"] == "yield"

    # Keep real zero, missing windows and invalid market numbers distinct.
    for changes, expected in [
        ({"m5":0,"h1":"1.2"},(0.0,1.2,None,None)),
        ({"m5":None,"h6":-15},(None,None,-15.0,None)),
        ({"m5":-99,"h24":-99},(None,None,None,-99.0)),
        ({"m5":True,"h1":"NaN","h6":"Infinity"},(None,None,None,None)),
    ]:
        response={"pairs":[{"liquidity":{"usd":100},"priceChange":changes}]}
        with patch.object(pipeline.urllib.request,"urlopen",return_value=contextlib.nullcontext(io.StringIO(json.dumps(response)))):
            assert pipeline.get_momentum("token")==expected
    with patch.object(pipeline,"get_momentum",return_value=(0,None,-2,3)) as momentum, \
         patch.object(pipeline,"fetch_live_fee_tvl",return_value=1.4) as fees, \
         patch.object(pipeline,"get_price_impact_sol_to_token",return_value=.1) as impact:
        winner=dict(candidate,base_symbol="TOKEN",sol_is_x=False,score=70,entry_live_gates={"forged":True})
        assert pipeline.predeploy_live_gate_reject(winner,.12,"5m") is None
        checks=winner["entry_live_gates"]
        assert checks["m5_pct"]==0 and checks["h1_pct"] is None
        assert checks["checked_deploy_sol"]==.12 and checks["fee_timeframe"]=="5m"
        assert checks["screened_fee_tvl_ratio"]==2 and checks["live_fee_tvl_ratio"]==1.4
        assert checks["price_impact_pct"]==.1 and "forged" not in checks
        assert momentum.call_count==fees.call_count==impact.call_count==1
    # Run the real context/Redis serialization, without invoking any executor.
    source=Path(pipeline.__file__).read_text()
    ns=dict(vars(pipeline),winner=winner,entry_id="entry",mode="pulse",strategy="sol_bidask",
            deploy_sol=.12,amount_x=0,amount_y=.12,bins_below=44,bins_above=0,
            strategy_type="bid_ask",slippage_bps=1000)
    start=source.index("    entry_context =");end=source.index('    print(f"Running deploy:',start)
    exec(compile(textwrap.dedent(source[start:end]),pipeline.__file__,"exec"),ns)
    encoded=shlex.split(ns["deploy_cmd"])[0].split("=",1)[1]
    assert json.loads(encoded)["signal"]["entry_live_gates"]==checks
    ns.update(active_price=1,active_bin=0,bin_step=100,sol_is_x=False,ts=1,tx_hash="tx")
    start=source.index("    tracking_data =");end=source.index("    if not is_dry_run:",start)
    exec(compile(textwrap.dedent(source[start:end]),pipeline.__file__,"exec"),ns)
    assert json.loads(json.dumps(ns["tracking_data"],allow_nan=False))["signal"]["entry_live_gates"]==checks
    with patch.dict(os.environ,DRY_RUN="true"),patch.object(pipeline,"get_momentum",side_effect=AssertionError("dry run fetched market")):
        dry=dict(candidate,entry_live_gates={"forged":True})
        assert pipeline.predeploy_live_gate_reject(dry,.1,"5m") is None
        assert "entry_live_gates" not in dry

    # Exercise the real CLI entry path, stopping at its slot gate before any
    # wallet/network work. Neither a stale prompt nor SOUL can override signals.
    for mode in ("turnover", "pulse", "casual", "multiday"):
        for source in ("from_signal", "from_batch", None):
            args = argparse.Namespace(mode=mode, strategy="balanced_tight",
                                      from_signal=None, from_batch=None,
                                      analyze_only=False, pick_context=False)
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
    }, {"mode": "pulse", "pnl_sol": 9, "pnl_basis": "pre_swap_mark", "age_min": 5}]), patch.object(stats, "load_realized", return_value={
        "recent": {"closed_at": 90_000, "realized_sol": 0.2, "fee_sol": 0.3, "deposit_sol": 1},
        "old": {"closed_at": 1, "realized_sol": 99, "fee_sol": 100, "deposit_sol": 1000},
        "future": {"closed_at": 200_000, "realized_sol": 99},
    }), patch.object(stats.time, "time", return_value=100_000), \
            patch.object(stats, "redis_keys", return_value=[]), \
            patch.object(stats, "redis_scard", return_value=0), \
            patch.object(stats, "accounting_report", return_value={"rent_refund_groups": [
                {"first_activity": 20_000, "last_activity": 90_000,
                 "root_chain_ids": ["one", "two", "three"], "cash_with_matched_refunds_sol": -0.003},
                {"first_activity": 30_000, "last_activity": 95_000,
                 "root_chain_ids": ["four"], "cash_with_matched_refunds_sol": 0.001},
                {"first_activity": 1, "last_activity": 90_000,
                 "root_chain_ids": ["carry-in"], "cash_with_matched_refunds_sol": 99},
                {"first_activity": 90_000, "last_activity": 100_001,
                 "root_chain_ids": ["future"], "cash_with_matched_refunds_sol": 99},
            ]}) as accounting:
        card = stats.build_card(24)
        accounting.assert_called_once_with(stats.PROFILE_DIR, 100_000)
        assert "-0.002000000 SOL · 4 roots" in card
        assert "Reconciled LP closes | 1 (1W/0L" in card  # LP positive can coexist with negative cash.
        assert "Closes / unreconciled | 2 / 1" in card
        assert "Reconciled journal LP PnL | +0.2000 SOL" in card
        assert "+9.2000" not in card
        with patch.object(stats, "load_closes", return_value=[{"pnl_sol": 9, "pnl_basis": "pre_swap_mark"}]):
            assert "Reconciled journal LP PnL | Unmeasured" in stats.build_card(24)
        assert "do not add" in card and "Not wallet-wide profit or win rate" in card
        accounting.return_value = {"rent_refund_groups": []}
        unknown = stats.build_card(24)
        assert "Unmeasured: no complete matched groups" in unknown
        assert "+0.000000000 SOL" not in unknown
        accounting.return_value = {"rent_refund_groups": [
            {"first_activity": 20_000, "last_activity": 90_000,
             "root_chain_ids": ["zero"], "cash_with_matched_refunds_sol": 0},
        ]}
        assert "+0.000000000 SOL · 1 roots" in stats.build_card(24)
        accounting.side_effect = OSError("unreadable facts")
        assert "Wallet cash / NAV | Unavailable" in stats.build_card(24)
    assert "+0.2000 / +0.3000 / -0.1000 SOL" in card
    assert "1.00 SOL across 1 cached closes" in card and "| pulse | 1 reconciled LP closes" in card
    print("Solana policy and journal regression checks passed")


if __name__ == "__main__":
    main()
