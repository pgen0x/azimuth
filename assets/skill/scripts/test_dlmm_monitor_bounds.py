"""Offline regression for range exits with portfolio aggregates lacking bounds."""
import contextlib
import io
import json
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


if __name__ == "__main__":
    unittest.main()
