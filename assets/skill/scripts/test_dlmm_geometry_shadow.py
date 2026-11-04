"""Shadow coverage study: 0.35 (live) vs 0.40 (candidate). Synthetic fixtures only."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import dlmm_geometry_shadow as geo
import dlmm_geometry_shadow_report as report
import dlmm_monitor as monitor
from dlmm_pipeline import sol_bidask_bins, SOL_BIDASK_COVERAGE

POS = "P" * 32
POOL = "L" * 32


def rows(path):
    with open(path) as stream:
        return [json.loads(line) for line in stream if line.strip()]


class ArmTests(unittest.TestCase):
    def test_default_coverage_unchanged(self):
        self.assertEqual(SOL_BIDASK_COVERAGE, 0.35)
        for step in (30, 80, 100, 125, 200):
            self.assertEqual(sol_bidask_bins(step), sol_bidask_bins(step, 0.35))

    def test_arms_match_codex_table(self):
        # results/shared-pool-geometry-20261104.md: inclusive bins per step.
        for step, base, cand in [(80, 54, 54), (100, 45, 53), (125, 36, 43)]:
            a = geo.arms(0, step, False, sol_bidask_bins)
            self.assertEqual((a["baseline"]["bins"], a["candidate"]["bins"]), (base, cand), step)

    def test_orientation(self):
        below = geo.arms(1000, 100, False, sol_bidask_bins)["baseline"]
        above = geo.arms(1000, 100, True, sol_bidask_bins)["baseline"]
        self.assertEqual((below["lower_bin"], below["upper_bin"]), (956, 1000))
        self.assertEqual((above["lower_bin"], above["upper_bin"]), (1000, 1044))
        self.assertAlmostEqual(below["span_pct"], 35.46, places=1)


class WriterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile = self.tmp.name
        self.mem = os.path.join(self.profile, "memories")

    def tearDown(self):
        self.tmp.cleanup()

    def entry(self, **kw):
        args = dict(position=POS, pool=POOL, mode="pulse", strategy="sol_bidask", bin_step=100,
                    active_bin=1000, anchor="executor_entry_bin", sol_is_x=False, size_sol=0.1,
                    live_bins_below=44, live_bins_above=0, dry_run=False, bins_fn=sol_bidask_bins, now=100.0)
        args.update(kw)
        return geo.record_entry(self.profile, **args)

    def test_entry_row(self):
        row = self.entry()
        self.assertTrue(row["live_matches_baseline"])
        self.assertFalse(row["arms_identical"])
        written = rows(os.path.join(self.mem, geo.ENTRY_FILE))
        self.assertEqual(written, [json.loads(json.dumps(row))])
        self.assertEqual(written[0]["arms"]["candidate"]["lower_bin"], 1000 - 52)

    def test_live_mismatch_is_journaled_not_hidden(self):
        self.assertFalse(self.entry(live_bins_below=40)["live_matches_baseline"])

    def test_entry_skips_other_strategies_and_bad_input(self):
        self.assertIsNone(self.entry(strategy="balanced_tight"))
        self.assertIsNone(self.entry(active_bin=None))
        self.assertIsNone(self.entry(position="../evil"))
        self.assertFalse(os.path.exists(os.path.join(self.mem, geo.ENTRY_FILE)))

    def test_entry_never_raises(self):
        def boom(*_):
            raise RuntimeError("x")
        with redirect_stdout(io.StringIO()) as out:
            self.assertIsNone(self.entry(bins_fn=boom))
        self.assertIn("GEOMETRY_SHADOW_ENTRY_ERROR", out.getvalue())

    def test_kill_switch(self):
        with patch.dict(os.environ, {"DLMM_GEOMETRY_SHADOW": "0"}):
            self.assertIsNone(self.entry())
            self.assertFalse(geo.observe(self.profile, POS, POOL, 1000, 100.0))

    def test_observe_rate_limited_per_position(self):
        self.assertTrue(geo.observe(self.profile, POS, POOL, 1000, 1000.0))
        self.assertFalse(geo.observe(self.profile, POS, POOL, 999, 1030.0))
        self.assertTrue(geo.observe(self.profile, "Q" * 32, POOL, 5, 1030.0))
        self.assertTrue(geo.observe(self.profile, POS, POOL, 998, 1061.0))
        got = [(r["position"][0], r["active_bin"]) for r in rows(os.path.join(self.mem, geo.OBS_FILE))]
        self.assertEqual(got, [("P", 1000), ("Q", 5), ("P", 998)])

    def test_observe_rejects_non_int_bin(self):
        for bad in (None, True, 1.0, "1"):
            self.assertFalse(geo.observe(self.profile, POS, POOL, bad, 1000.0))

    def test_monitor_flush_dispatches_geometry(self):
        with patch.object(monitor, "PROFILE_DIR", self.profile):
            monitor.flush_tick_observers([("geometry", (POS, POOL, 1000, 1000.0))])
        self.assertEqual(len(rows(os.path.join(self.mem, geo.OBS_FILE))), 1)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mem = os.path.join(self.tmp.name, "memories")
        os.makedirs(self.mem)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, items):
        with open(os.path.join(self.mem, name), "a") as f:
            for r in items:
                f.write(json.dumps(r) + "\n")

    def add_position(self, pos, pool, day, path, step=100):
        """path: list of (seconds after entry, active bin offset); closes 60s after last point."""
        t0 = day * 86400 + 1000.0
        a = geo.arms(0, step, False, sol_bidask_bins)
        self.write(geo.ENTRY_FILE, [dict(kind="entry", schema=1, ts=t0, position=pos, pool=pool, mode="pulse",
                                         strategy="sol_bidask", bin_step=step, active_bin=0, dry_run=False, arms=a,
                                         arms_identical=a["baseline"]["bins"] == a["candidate"]["bins"],
                                         live_matches_baseline=True)])
        self.write(geo.OBS_FILE, [dict(kind="obs", schema=1, ts=t0 + dt, position=pos, pool=pool, active_bin=b)
                                  for dt, b in path])
        self.write("dlmm_closes.jsonl", [dict(ts=t0 + path[-1][0] + 60, position=pos, event="exit")])

    def test_score_position_counts_beyond_baseline_edge(self):
        a = geo.arms(0, 100, False, sol_bidask_bins)
        e = dict(ts=0.0, active_bin=0, arms=a)
        obs = [dict(ts=60.0, active_bin=-10), dict(ts=120.0, active_bin=-48), dict(ts=180.0, active_bin=10)]
        s = report.score_position(e, obs, 240.0)
        # -48 is past baseline lower (-44) but inside candidate (-52); +10 is above both.
        self.assertEqual(s["arms"]["baseline"]["time_in_range_s"], 120.0)
        self.assertEqual(s["arms"]["candidate"]["time_in_range_s"], 180.0)
        self.assertEqual(s["unobserved_s"], 0.0)

    def test_gap_is_unobserved_not_in_range(self):
        a = geo.arms(0, 100, False, sol_bidask_bins)
        s = report.score_position(dict(ts=0.0, active_bin=0, arms=a), [], 1000.0)
        self.assertEqual(s["arms"]["baseline"]["time_in_range_s"], report.MAX_GAP_S)
        self.assertEqual(s["unobserved_s"], 1000.0 - report.MAX_GAP_S)

    def test_weight_sums_to_one(self):
        arm = geo.arms(0, 100, False, sol_bidask_bins)["baseline"]
        total = sum(report.bidask_weight(arm, 0, b) for b in range(arm["lower_bin"], arm["upper_bin"] + 1))
        self.assertAlmostEqual(total, 1.0)

    def test_need_data_below_gate(self):
        self.add_position(POS, POOL, 1, [(60, -5), (120, -48)])
        r = report.build(self.mem)
        self.assertEqual((r["verdict"], r["treated"], r["closed"]), ("NEED-DATA", 1, 1))

    def test_identical_arms_excluded_and_open_counted(self):
        self.add_position("A" * 32, POOL, 1, [(60, -5)], step=80)
        self.write(geo.ENTRY_FILE, [dict(kind="entry", schema=1, ts=5.0, position="O" * 32, pool=POOL,
                                         mode="pulse", dry_run=False, active_bin=0,
                                         arms=geo.arms(0, 100, False, sol_bidask_bins))])
        r = report.build(self.mem)
        self.assertEqual((r["identical_arms"], r["treated"], r["open_positions"]), (1, 0, 1))

    def test_gate_met_gives_directional_verdict(self):
        # 30 positions, 10 pools, 10 days, every one dips past the baseline edge.
        for i in range(30):
            self.add_position(f"{i:032d}", f"pool{i % 10}", i % 10, [(60, -20), (120, -48), (180, -49)])
        r = report.build(self.mem)
        self.assertEqual(r["treated"], 30)
        self.assertEqual(r["verdict"], "PROPOSE-CANARY")
        self.assertGreater(r["d_time_in_range_s"]["mean"], 0)

    def test_gate_met_inside_baseline_kills(self):
        # Price never leaves the baseline range: the wider arm only thins per-bin weight.
        for i in range(30):
            self.add_position(f"{i:032d}", f"pool{i % 10}", i % 10, [(60, -10), (120, -20)])
        r = report.build(self.mem)
        self.assertEqual(r["verdict"], "KILL")
        self.assertEqual(r["d_time_in_range_s"]["mean"], 0)

    def test_corrupt_journal_is_counted(self):
        with open(os.path.join(self.mem, geo.OBS_FILE), "w") as f:
            f.write("{not json\n")
        r = report.build(self.mem)
        self.assertEqual(r["corrupt_rows"]["obs"], 1)


if __name__ == "__main__":
    unittest.main()
