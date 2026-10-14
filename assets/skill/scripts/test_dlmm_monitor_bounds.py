"""Offline regression for range exits with portfolio aggregates lacking bounds."""
import contextlib
import io
import json
import time
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch

import dlmm_monitor as monitor


POSITION = "AeEqD9BwdPtYt7fpvo8q6U7KBvyEaMUZAnhTmZZc5CB8"
POOL = "3BCeknAQpHELGfKhUb9mnKuLC3Eg3qjJrZ5B7fqC1xSW"


class CloseBinObservationTests(unittest.TestCase):
    def mark(self):
        return dict(success=True, source="onchain_sol_inventory", pool=POOL, position=POSITION,
                    pnl_currency="SOL", observed_at=100, pnl_pct=-8, pnl_sol=-.008,
                    deposit_lamports="100000000", value_lamports_upper="92000000", funding_signature="funding",
                    active_bin=0, lower_bin=0, upper_bin=0, in_range=True, unclaimed_fees_sol=.002,
                    bin_observation=dict(version=1, bin_step=100, sol_is_x=False,
                        bins=[dict(id=0,liquidity_raw="100",x_raw="10000000",y_raw="80000000",
                                   fee_x_raw="1000000",fee_y_raw="1000000")]))

    def test_observation_preserves_raw_bins_and_both_times_after_slow_close(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(monitor,"PROFILE_DIR",directory), \
             patch.object(monitor.time,"time",return_value=200):
            self.assertTrue(monitor.record_close_bin_observation(self.mark(),POOL,POSITION,"risk exit",101))
            row=json.loads((Path(directory)/'memories/dlmm_close_bin_observations.jsonl').read_text())
            self.assertEqual((row['observed_at'],row['decision_at'],row['recorded_at']),(100,101,200))
            self.assertEqual(row['bin_observation'],self.mark()['bin_observation'])
            self.assertIn('not_finalized_exit',row['basis'])

    def test_missing_stale_foreign_or_malformed_data_and_disk_failure_are_nonfatal(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(monitor,"PROFILE_DIR",directory):
            for mark in [None,dict(self.mark(),pool='foreign'),dict(self.mark(),observed_at=50),
                         dict(self.mark(),bin_observation={}),dict(self.mark(),funding_signature=None)]:
                if isinstance(mark,dict) and mark.get('funding_signature') is None:
                    mark.pop('funding_signature',None)
                self.assertFalse(monitor.record_close_bin_observation(mark,POOL,POSITION,'exit',101))
            malformed=self.mark();malformed['bin_observation']['bins'][0]['x_raw']='NaN'
            self.assertFalse(monitor.record_close_bin_observation(malformed,POOL,POSITION,'exit',101))
            self.assertFalse((Path(directory)/'memories/dlmm_close_bin_observations.jsonl').exists())
            with patch('builtins.open',side_effect=OSError('disk unavailable')):
                self.assertFalse(monitor.record_close_bin_observation(self.mark(),POOL,POSITION,'exit',101))

    def test_production_records_after_close_attempt_and_skips_dry_run(self):
        source=Path(monitor.__file__).read_text()
        code=textwrap.dedent(source[source.index('        # Execute close if triggered'):
                                  source.index('            if close_res and close_res.get("success"):',
                                               source.index('        # Execute close if triggered'))])
        for dry in (True,False):
            calls=[]
            scope=dict(vars(monitor),close_reason='risk exit',pair='TEST-SOL',is_dry_run_stored=dry,
                       pos_addr=POSITION,pool=POOL,native_mark=self.mark(),wallet_address='wallet',emergency_close=True)
            scope['close_position']=lambda *a,**k:(calls.append('close') or (dict(success=False),None))
            scope['record_close_bin_observation']=lambda *a:calls.append('observation')
            with contextlib.redirect_stdout(io.StringIO()):exec(code,scope)
            self.assertEqual(calls,['close'] if dry else ['close','observation'])


class PositionBoundsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profile = patch.object(monitor, "PROFILE_DIR", self.tmp.name)
        self.profile.start()
        self.addCleanup(self.profile.stop)
        self.path = Path(self.tmp.name) / "memories" / "dlmm_entries" / (POSITION + ".json")
        self.path.parent.mkdir(parents=True)
        self.entry = dict(position=POSITION, pool=POOL, entry_bin=-430, bins_below=35, bins_above=0)
        self.path.write_text(json.dumps(self.entry))

    def test_executor_range_and_position_response(self):
        self.assertEqual(monitor.position_bin_bounds(POSITION, POOL), (-465, -430))
        self.assertEqual(monitor.position_bin_bounds(POSITION, POOL,
                         dict(success=True, lower_bin=-460, upper_bin=-420)), (-460, -420))
        self.assertEqual(monitor.position_bin_bounds(POSITION, POOL,
                         dict(success=False, lower_bin=-460, upper_bin=-420)), (-465, -430))
        self.path.write_text(json.dumps(dict(self.entry, bins_below=0, bins_above=35)))
        self.assertEqual(monitor.position_bin_bounds(POSITION, POOL), (-430, -395))

    def test_unknown_or_mismatched_provenance_never_invents_bounds(self):
        for entry in [[], None, {}, dict(self.entry, position="parent"),
                      dict(self.entry, pool="another-pool"), dict(self.entry, entry_bin=None),
                      dict(self.entry, entry_bin=False), dict(self.entry, bins_below=-1),
                      dict(self.entry, bins_above="0")]:
            with self.subTest(entry=entry):
                self.path.write_text(json.dumps(entry))
                self.assertEqual(monitor.position_bin_bounds(POSITION, POOL), (None, None))
        self.path.write_text("{broken")
        self.assertEqual(monitor.position_bin_bounds(POSITION, POOL), (None, None))
        self.path.unlink()
        self.assertEqual(monitor.position_bin_bounds(POSITION, POOL), (None, None))
        self.assertEqual(monitor.position_bin_bounds("../parent", POOL), (None, None))

    def replay(self, active_bin, *, indexed_in_range=True, sol_is_x=False, missing=False):
        """Run production source blocks, including the portfolio fast path and exits."""
        source = Path(monitor.__file__).read_text()
        def block(start, end):
            return textwrap.dedent(source[source.index(start):source.index(end)])
        market = block("        # Get current pool price", "        # SUSPECT-READ GUARD")
        geometry = block("        # Pool aggregates do not include", "        # Old peaks can be USD returns")
        pump = block("        # 3. Pumped Far Above", "        # 3b. DexScreener")
        direction = block("        sol_is_x_pos =", "        # 3d. Gap-through")
        gap = block("        if (not close_reason and active_bin", '        if meta.get("mode") == "turnover":')
        if missing:
            self.path.unlink()
        elif sol_is_x:
            self.path.write_text(json.dumps(dict(self.entry, bins_below=0, bins_above=35)))
        scope = dict(vars(monitor), entry_price=1.0, meta=dict(entry_bin=999, bins_below=0,
                     bins_above=0, sol_is_x=sol_is_x), bins_below=0,
                     pos_addr=POSITION, pool=POOL, api_available=True, is_dry_run_stored=False,
                     bp=dict(pnl_pct=0.0, pool_price=1.0, is_out_of_range=not indexed_in_range),
                     close_reason=None, max_bins_pumped_above=5)
        # None represents the active-bin RPC failing; stale Redis entry_bin=999
        # must never masquerade as the current bin or a position boundary.
        result = None if active_bin is None else dict(binId=active_bin, price=1.0)
        scope["run_command_json"] = lambda command, **_: ((None, "unavailable")
            if " pnl-onchain " in command else (result, None))
        with contextlib.redirect_stdout(io.StringIO()):
            for code in (market, geometry, pump, direction, gap):
                exec(compile("for _ in [None]:\n" + textwrap.indent(code, "    "),
                             monitor.__file__, "exec"), scope)
        return scope

    def test_dump_gap_restores_token_side_exit_despite_stale_indexer(self):
        state = self.replay(-471)
        self.assertFalse(state["in_range"])
        self.assertTrue(state["oor_token_side"])
        self.assertIn("Gap-through dump exit", state["close_reason"])

    def test_pump_and_inclusive_range_edges(self):
        self.assertIn("Pumped far above", self.replay(-424)["close_reason"])
        for bin_id in (-465, -430):
            state = self.replay(bin_id, indexed_in_range=False)
            self.assertTrue(state["in_range"])
            self.assertIsNone(state["close_reason"])
        state = self.replay(-466)
        self.assertFalse(state["in_range"])
        self.assertIsNone(state["close_reason"])

    def test_sol_x_range_uses_bins_above(self):
        state = self.replay(-396, sol_is_x=True, indexed_in_range=False)
        self.assertTrue(state["in_range"])
        self.assertIsNone(state["close_reason"])
        self.assertTrue(self.replay(-394, sol_is_x=True)["oor_token_side"])
        self.assertTrue(self.replay(-431, sol_is_x=True)["oor_sol_side"])

    def test_missing_geometry_or_current_bin_preserves_indexed_flag(self):
        state = self.replay(-471, missing=True)
        self.assertTrue(state["in_range"])
        self.assertIsNone(state["close_reason"])
        self.path.write_text(json.dumps(self.entry))
        for active in (None, "-471", False):
            state = self.replay(active, indexed_in_range=False)
            self.assertFalse(state["in_range"])
            self.assertIsNone(state["active_bin"])
            self.assertIsNone(state["close_reason"])


class NativeFeeObservationTests(unittest.TestCase):
    def mark(self, **changes):
        deposit, value = 119999981, 119429877
        result = dict(success=True, source="onchain_sol_inventory", pool=POOL, position=POSITION,
                      pnl_currency="SOL", observed_at=2001, pnl_sol=(value-deposit)/1e9,
                      pnl_pct=(value-deposit)/deposit*100, deposit_lamports=str(deposit),
                      value_lamports_upper=str(value), unclaimed_fees_sol=.000889575,
                      active_bin=-523, lower_bin=-548, upper_bin=-504, in_range=True, pool_price=1)
        return result | changes

    def replay(self, mark, indexed, meta=None):
        source = Path(monitor.__file__).read_text()
        start = min(source.index("        # Get current pool price"),
                    source.index("        if not is_dry_run_stored and observe_root_fee_pace"))
        code = textwrap.dedent(source[start:
                                      source.index("        # SUSPECT-READ GUARD")])
        calls = []
        scope = dict(vars(monitor), now=1999, entry_price=1, api_available=True,
                     is_dry_run_stored=False, pos_addr=POSITION, pool=POOL, bp=indexed,
                     meta=meta if meta is not None else dict(root_fee_baseline=dict(fees=0, ts=201)))
        scope['run_command_json'] = lambda command, **kwargs: (
            calls.append(command) or ((mark, None) if " pnl-onchain " in command
                                     else (dict(binId=-523, price=1), None)))
        scope['run_command'] = lambda command: (calls.append(command) or ('', '', 0))
        with patch.object(monitor.time, 'time', return_value=2001), contextlib.redirect_stdout(io.StringIO()):
            exec(compile("for _ in [None]:\n" + textwrap.indent(code, "    "),
                         monitor.__file__, "exec"), scope)
        return scope, calls

    def indexed(self, **changes):
        return dict(pnl_pct=-1.1753, pnl_sol=-.001410375, pool_price=1,
                    fee_per_tvl_24h=24.44, balances_sol=.117700031,
                    unclaimed_fees_sol=.000889575, updated_at=1696) | changes

    def test_fresh_native_fees_replace_stale_indexed_time_and_value(self):
        state, calls = self.replay(self.mark(), self.indexed())
        self.assertAlmostEqual(state['bp']['balances_sol'], .118540302)
        self.assertEqual(state['bp']['updated_at'], 2001)
        self.assertEqual(state['meta']['fee_pace_observed_at'], 2001)
        self.assertAlmostEqual(state['meta']['fee_pace_pct_30m'], .000889575/.118540302*100)
        self.assertEqual(state['bp']['fee_per_tvl_24h'], 24.44)
        self.assertEqual(sum(' pnl-onchain ' in c for c in calls), 1)
        self.assertFalse(any(' active-bin ' in c for c in calls))

    def test_unverified_native_never_refreshes_stale_indexed_fees(self):
        for mark in (None, self.mark(observed_at=1900), self.mark(pool='foreign')):
            state, _ = self.replay(mark, self.indexed())
            self.assertNotIn('fee_pace_observed_at', state['meta'])
            self.assertEqual(state['meta']['root_fee_baseline']['ts'], 201)
            self.assertEqual(state['bp']['updated_at'], 1696)

    def test_fresh_indexed_fallback_still_measures_full_window(self):
        state, _ = self.replay(None, self.indexed(updated_at=2000),
                               dict(root_fee_baseline=dict(fees=0, ts=200)))
        self.assertEqual(state['meta']['fee_pace_observed_at'], 2000)
        self.assertAlmostEqual(state['meta']['fee_pace_pct_30m'],
                               .000889575/.117700031*100)
        # At least 30 minutes are required before a pace is published.
        self.assertNotIn('fee_pace_observed_at', self.replay(None, self.indexed(updated_at=2000))[0]['meta'])

    def test_fee_stall_uses_verified_principal_when_indexed_value_is_missing(self):
        source = Path(monitor.__file__).read_text()
        code = textwrap.dedent(source[source.index('        # 5e. Fee-pace-death exit'):
                                      source.index('        # 5f. Stale-ticket re-pin')])
        for growth, stalled in ((.00001, True), (.0001, False)):
            meta = dict(fee_snap_at=2001-1800, fee_snap_sol=.000889575-growth)
            state, _ = self.replay(self.mark(), self.indexed(balances_sol=0), meta)
            state.update(now=2001, age_minutes=75, trailing_active=False, close_reason=None)
            exec(code, state)
            self.assertEqual(bool(state['close_reason']), stalled)


class SuspectRiskTests(unittest.TestCase):
    def mark(self, *, pct=-20.0, **changes):
        deposit = 100000000
        value = round(deposit * (1 + pct/100))
        return dict(success=True, source="onchain_sol_inventory", pool=POOL, position=POSITION,
                    pnl_currency="SOL", observed_at=time.time(), pnl_pct=pct, pnl_sol=(value-deposit)/1e9,
                    deposit_lamports=str(deposit), value_lamports_upper=str(value),
                    active_bin=-470, lower_bin=-465, upper_bin=-430, in_range=False,
                    unclaimed_fees_sol=.001, pool_price=.9, **changes)

    def replay(self, verify, *, age=1, prior=False, indexed=-100, portfolio=True, adopted=False, indexed_failure=False):
        source = Path(monitor.__file__).read_text()
        code = textwrap.dedent(source[source.index("        # Get current pool price"):
                                      source.index("        # Pool aggregates do not include")])
        calls = []
        scope = dict(vars(monitor), now=time.time(), meta=dict(deployed_at=time.time()-age*60,
                     adopted=adopted), pair="TEST-SOL", pool=POOL, pos_addr=POSITION,
                     is_dry_run_stored=False, api_available=portfolio,
                     bp={} if not portfolio else {"pnl_pct": indexed, "pnl_sol": indexed*.001,
                         "fee_per_tvl_24h":10.0, "unclaimed_fees_sol":.02, "pool_price":1.0},
                     entry_price=1.0, bins_below=35,
                     pnl_pct=indexed, pnl_sol_actual=-.1, in_range=True, active_bin=-430,
                     pnl_data=None, stop_loss_pct=-8, fee_per_tvl_24h=1)
        def read(command, **kwargs):
            calls.append(command)
            if " pnl-onchain " in command:
                self.assertEqual(kwargs["timeout"], 3)
                return verify, "RPC timeout" if verify is None else None
            if " active-bin " in command:
                return {"binId":-430,"price":1.0},None
            self.assertIn(" pnl ", command)
            if indexed_failure:
                return None, "indexer unavailable"
            return {"success":True,"pnl_pct":indexed,"pnl_sol":indexed*.001,
                    "fee_per_tvl_24h":10.0,"in_range":True},None
        def redis(command):
            calls.append(command)
            return ("100" if prior else "", "", 0)
        scope.update(run_command_json=read, run_command=redis)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile("for _ in [None]:\n" + textwrap.indent(code + "guard_passed = True\n", "    "),
                         monitor.__file__, "exec"), scope)
            if scope.get("guard_passed"):
                scope.update(close_reason=None, emergency_close=False, emergency_reason=None)
                risk = textwrap.dedent(source[source.index("        # 2. Hard Stop-Loss Check"):
                                              source.index("        # 3. Pumped Far Above")])
                exec(compile(risk, monitor.__file__, "exec"), scope)
        return scope, calls

    def test_native_emergency_skips_optional_market_fetch_but_keeps_rug_detection(self):
        source = Path(monitor.__file__).read_text()
        code = textwrap.dedent(source[source.index("        # 3b. DexScreener liquidity"):
                                      source.index("        # 4. Out of Range (OOR)")])
        emergency, _ = self.replay(self.mark(pct=-60), portfolio=False)
        def unavailable(*args):
            self.fail("Emergency exit waited for optional DexScreener request")
        emergency['get_pool_liquidity_usd'] = unavailable
        reason = emergency['emergency_reason']
        exec(compile(code, monitor.__file__, 'exec'), emergency)
        self.assertEqual(emergency['emergency_reason'], reason)
        self.assertTrue(emergency['emergency_close'])
        self.assertIsNone(emergency['pool_liquidity_usd'])
        self.assertIsNone(emergency['price_change_m5'])
        healthy, _ = self.replay(self.mark(pct=.1), indexed=.1)
        calls = []
        def rug_data(*args):
            calls.append(args)
            return 100000, -25, -30
        healthy['get_pool_liquidity_usd'] = rug_data
        exec(compile(code, monitor.__file__, 'exec'), healthy)
        self.assertEqual(len(calls), 1)
        self.assertTrue(healthy['emergency_close'])
        self.assertIn('RUG velocity dump', healthy['emergency_reason'])

    def test_verified_native_loss_does_not_wait_for_indexed_fallback(self):
        state, calls = self.replay(self.mark(pct=-60), portfolio=False)
        self.assertTrue(state["emergency_close"])
        self.assertFalse(any(" pnl " in command for command in calls))
        self.assertFalse(any(" active-bin " in command for command in calls))

    def test_failed_native_read_retains_indexed_fallback_in_order(self):
        state, calls = self.replay(None, portfolio=False, indexed=-5)
        self.assertTrue(state.get("guard_passed"))
        self.assertEqual(state["pnl_pct"], -5)
        native = next(i for i, command in enumerate(calls) if " pnl-onchain " in command)
        indexed = next(i for i, command in enumerate(calls) if " pnl " in command)
        self.assertLess(native, indexed)

    def test_indexer_outage_cannot_skip_native_emergency_exit(self):
        state, calls = self.replay(self.mark(pct=-60), portfolio=False, indexed_failure=True)
        self.assertTrue(state.get("guard_passed"))
        self.assertEqual(state["pnl_pct"], -60)
        self.assertTrue(state["emergency_close"])
        self.assertEqual(sum(" pnl-onchain " in c for c in calls), 1)

    def test_both_value_sources_unavailable_cannot_use_default_zero(self):
        for native in (None, self.mark() | {"pool": "wrong-pool"}):
            state, calls = self.replay(native, portfolio=False, indexed_failure=True)
            self.assertFalse(state.get("guard_passed", False))
            self.assertEqual(sum(" pnl-onchain " in c for c in calls), 1)

    def test_real_native_young_loss_reaches_risk_rules(self):
        for portfolio in (True, False):
            state, _ = self.replay(self.mark(), portfolio=portfolio)
            self.assertTrue(state.get("guard_passed"))
            self.assertEqual(state["pnl_pct"], -20)
            self.assertEqual(state["pnl_sol_actual"], -.02)
            self.assertEqual(state["active_bin"], -470)
            self.assertFalse(state["in_range"])
            self.assertTrue(state["emergency_close"])
            self.assertIn("EMERGENCY Stop-Loss", state["close_reason"])

    def test_indexer_false_loss_uses_native_sol_mark_and_bounds(self):
        state, calls = self.replay(self.mark(pct=2))
        self.assertTrue(state.get("guard_passed"))
        self.assertEqual(state["pnl_pct"], 2)
        self.assertEqual(state["pnl_sol_actual"], .002)
        self.assertEqual(state["pnl_data"]["lower_bin"], -465)
        self.assertIsNone(state["close_reason"])
        self.assertTrue(any("redis-cli del" in call for call in calls))

    def test_unavailable_young_and_mature_retry_behavior(self):
        for age, prior, passed in [(1, False, False), (1, True, False), (5, False, False),
                                   (5, True, True)]:
            state, _ = self.replay(None, age=age, prior=prior)
            self.assertEqual(bool(state.get("guard_passed")), passed)
        state, _ = self.replay(None, adopted=True, prior=True)
        self.assertTrue(state.get("guard_passed"))  # unknown adoption age is not newborn

    def test_malformed_or_stale_native_proof_never_becomes_zero(self):
        for changes in [dict(source="indexed_pnl"), dict(success=False), dict(position="other"),
                        dict(pool="other"), dict(pnl_sol=None), dict(pnl_pct=float("nan")),
                        dict(pnl_pct=True), dict(value_lamports_upper="0"), dict(deposit_lamports="0"),
                        dict(unclaimed_fees_sol=None), dict(unclaimed_fees_sol=-.001),
                        dict(unclaimed_fees_sol=float("nan")), dict(unclaimed_fees_sol=1),
                        dict(observed_at=time.time()-60), dict(in_range=True), dict(active_bin=None)]:
            proof = self.mark(); proof.update(changes)
            self.assertFalse(monitor.verified_risk_mark(proof, POOL, POSITION, time.time()))
            state, _ = self.replay(proof)
            self.assertFalse(state.get("guard_passed"))
            self.assertEqual(state["pnl_sol_actual"], -.1)
        for malformed in ([], "bad", None):
            state, _ = self.replay(malformed)
            self.assertFalse(state.get("guard_passed"))

    def test_ordinary_hidden_loss_reaches_existing_tight_floor(self):
        for portfolio in (True, False):
            state, calls = self.replay(self.mark(pct=-4), indexed=-1, age=10, portfolio=portfolio)
            self.assertTrue(state.get("guard_passed"))
            self.assertEqual(state["pnl_pct"], -4)
            self.assertEqual(state["pnl_sol_actual"], -.004)
            self.assertEqual(state["active_price"], .9)
            reason, protected = monitor.protect_tight_exit(None,"turnover",state["pnl_pct"],None)
            self.assertTrue(protected)
            self.assertIn("risk floor", reason)
            self.assertFalse(state["emergency_close"])
            self.assertEqual(sum(" pnl-onchain " in c for c in calls),1)
            self.assertFalse(any(" active-bin " in c for c in calls))
            if portfolio:
                self.assertEqual(state["bp"]["unclaimed_fees_sol"],.001)
                self.assertEqual(state["fee_per_tvl_24h"],10.0)

    def test_hidden_young_emergency_uses_native_mark_once(self):
        state, calls = self.replay(self.mark(pct=-12), indexed=.5)
        self.assertTrue(state.get("guard_passed"))
        self.assertTrue(state["emergency_close"])
        self.assertEqual(sum(" pnl-onchain " in c for c in calls),1)
        self.assertFalse(any(" active-bin " in c for c in calls))

    def test_native_gain_avoids_indexed_floor_and_false_peak(self):
        state,_ = self.replay(self.mark(pct=.1),indexed=-3)
        reason,protected=monitor.protect_tight_exit(None,"pulse",state["pnl_pct"],None)
        self.assertIsNone(reason)
        self.assertFalse(protected)
        state,_ = self.replay(self.mark(pct=.1),indexed=2)
        source=Path(monitor.__file__).read_text()
        peak=textwrap.dedent(source[source.index("        # Old peaks can be USD returns"):
                                    source.index("        close_reason = None",source.index("        # Old peaks can be USD returns"))])
        state.update(turnover_trailing_trigger_pct=1.2,turnover_trailing_drop_pct=.6,
                     trailing_drop_pct=1.5,trailing_trigger_pct=3.0)
        state["meta"].update(mode="turnover",pnl_currency="SOL",peak_pnl=0)
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(peak,monitor.__file__,"exec"),state)
        self.assertEqual(state["peak_pnl"],.1)
        self.assertFalse(state["trailing_active"])

    def test_unavailable_native_retains_indexed_mark_and_current_bin(self):
        for verify in (None,{"success":False},self.mark(pct=-4)|{"observed_at":time.time()-60}):
            state,calls=self.replay(verify,indexed=-1)
            self.assertTrue(state.get("guard_passed"))
            self.assertEqual(state["pnl_pct"],-1)
            self.assertEqual(state["pnl_sol_actual"],-.001)
            self.assertEqual(state["active_bin"],-430)
            self.assertEqual(sum(" pnl-onchain " in c for c in calls),1)
            self.assertEqual(sum(" active-bin " in c for c in calls),1)

    def test_old_executor_without_price_preserves_native_risk_bin(self):
        proof=self.mark(pct=-4);proof.pop("pool_price")
        state,calls=self.replay(proof,indexed=-1)
        self.assertEqual(state["pnl_pct"],-4)
        self.assertEqual(state["active_bin"],-470)
        self.assertEqual(state["active_price"],1)
        self.assertEqual(sum(" active-bin " in c for c in calls),1)


if __name__ == "__main__":
    unittest.main()
