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
        scope["run_command_json"] = lambda _: (result, None)
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


class SuspectRiskTests(unittest.TestCase):
    def mark(self, *, pct=-20.0, **changes):
        deposit = 100000000
        value = round(deposit * (1 + pct/100))
        return dict(success=True, source="onchain_sol_inventory", pool=POOL, position=POSITION,
                    pnl_currency="SOL", observed_at=time.time(), pnl_pct=pct, pnl_sol=(value-deposit)/1e9,
                    deposit_lamports=str(deposit), value_lamports_upper=str(value),
                    active_bin=-470, lower_bin=-465, upper_bin=-430, in_range=False, **changes)

    def replay(self, verify, *, age=1, prior=False, indexed=-100, portfolio=True, adopted=False):
        source = Path(monitor.__file__).read_text()
        code = textwrap.dedent(source[source.index("        # SUSPECT-READ GUARD"):
                                      source.index("        # Pool aggregates do not include")])
        calls = []
        scope = dict(vars(monitor), now=time.time(), meta=dict(deployed_at=time.time()-age*60,
                     adopted=adopted), pair="TEST-SOL", pool=POOL, pos_addr=POSITION,
                     is_dry_run_stored=False, api_available=portfolio, bp={} if not portfolio else {"pnl_pct": indexed},
                     pnl_pct=indexed, pnl_sol_actual=-.1, in_range=True, active_bin=-430,
                     pnl_data=None, stop_loss_pct=-8, fee_per_tvl_24h=1)
        def read(command, *, timeout):
            self.assertIn(" pnl-onchain ", command)
            self.assertEqual(timeout, 8)
            calls.append(command)
            return verify, "RPC timeout" if verify is None else None
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
                        dict(observed_at=time.time()-60), dict(in_range=True), dict(active_bin=None)]:
            proof = self.mark(); proof.update(changes)
            self.assertFalse(monitor.verified_risk_mark(proof, POOL, POSITION, time.time()))
            state, _ = self.replay(proof)
            self.assertFalse(state.get("guard_passed"))
            self.assertEqual(state["pnl_sol_actual"], -.1)
        for malformed in ([], "bad", None):
            state, _ = self.replay(malformed)
            self.assertFalse(state.get("guard_passed"))


if __name__ == "__main__":
    unittest.main()
