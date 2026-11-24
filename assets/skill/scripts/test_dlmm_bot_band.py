"""PULSE_MAX_BOT_HOLDERS_PCT on the Python side: the bots penalty, the band tag
and the kill-rule report. Synthetic journals only; nothing real is read."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dlmm_bot_band as bb  # noqa: E402
import dlmm_pipeline as pipeline  # noqa: E402
import dlmm_stats as stats  # noqa: E402


def notes_for(candidate, mode, env=None):
    c = dict(candidate, name="t", score=70)
    saved = os.environ.pop(bb.ENV_KEY, None)
    try:
        with patch.object(pipeline, "load_signal_weights", return_value={}), \
                patch.dict(os.environ, env or {}, clear=False):
            pipeline.apply_batch_conviction([c], mode)
    finally:
        if saved is not None:
            os.environ[bb.ENV_KEY] = saved
    return c.get("_conviction_notes", [])


class BarAndPenalty(unittest.TestCase):
    def test_bar_parsing_matches_go(self):
        self.assertEqual(bb.pulse_bot_bar(env={}), 25)
        self.assertEqual(bb.pulse_bot_bar(env={bb.ENV_KEY: "30"}), 30)
        self.assertEqual(bb.pulse_bot_bar(env={bb.ENV_KEY: "100"}), 100)
        for bad in ("", "thirty", "0", "-1", "100.1", "nan", "inf"):
            self.assertEqual(bb.pulse_bot_bar(env={bb.ENV_KEY: bad}), 25, bad)
        # The daemon's bar on the candidate wins over this process's env.
        self.assertEqual(bb.pulse_bot_bar({"pulse_bot_bar_pct": 30}, env={bb.ENV_KEY: "25"}), 30)
        self.assertEqual(bb.pulse_bot_bar({"pulse_bot_bar_pct": 0}, env={bb.ENV_KEY: "28"}), 28)

    def test_pulse_penalty_follows_the_env(self):
        self.assertIn("bots-15", notes_for({"bot_holders_pct": 25.1}, "pulse"))
        self.assertNotIn("bots-15", notes_for({"bot_holders_pct": 25.0}, "pulse"))
        self.assertNotIn("bots-15", notes_for({"bot_holders_pct": 22}, "pulse"))
        env = {bb.ENV_KEY: "30"}
        for pct in (24.9, 25.0, 29.9, 30.0):
            self.assertNotIn("bots-15", notes_for({"bot_holders_pct": pct}, "pulse", env), pct)
        self.assertIn("bots-15", notes_for({"bot_holders_pct": 30.1}, "pulse", env))

    def test_candidate_bar_beats_env(self):
        c = {"bot_holders_pct": 27, "pulse_bot_bar_pct": 30}
        self.assertNotIn("bots-15", notes_for(c, "pulse", {bb.ENV_KEY: "25"}))
        c = {"bot_holders_pct": 27, "pulse_bot_bar_pct": 25}
        self.assertIn("bots-15", notes_for(c, "pulse", {bb.ENV_KEY: "30"}))

    def test_other_modes_unchanged(self):
        for mode in ("turnover", "multiday", "casual"):
            for env in (None, {bb.ENV_KEY: "30"}, {bb.ENV_KEY: "10"}):
                self.assertIn("bots-15", notes_for({"bot_holders_pct": 20.1, "pulse_bot_bar_pct": 30}, mode, env))
                self.assertNotIn("bots-15", notes_for({"bot_holders_pct": 20.0}, mode, env))

    def test_missing_bot_data_is_never_penalized(self):
        for c in ({}, {"bot_holders_pct": None}, {"bot_holders_pct": "x"}, {"bot_holders_pct": True}):
            self.assertFalse(bb.bots_penalty(c, "pulse", {}))
            self.assertFalse(bb.bots_penalty(c, "turnover", {}))

    def test_band_tag(self):
        cases = [(24.99, "<25"), (0, "<25"), (25, "25-30"), (29.99, "25-30"), (30, ">=30"),
                 (55, ">=30"), (None, "unknown"), ("n/a", "unknown"), (float("nan"), "unknown")]
        for pct, band in cases:
            self.assertEqual(bb.bot_band(pct), band, pct)
        tag = bb.audit_tag({"bot_holders_pct": 26.6, "pulse_bot_bar_pct": 30}, env={})
        self.assertEqual(tag, {"bot_pct": 26.6, "bot_band": "25-30", "bot_bar_pct": 30})
        self.assertEqual(bb.audit_tag({}, env={})["bot_band"], "unknown")

    def test_pipeline_tags_pulse_entries_only(self):
        src = Path(pipeline.__file__).read_text()
        self.assertIn('    if mode == "pulse":\n', src)
        self.assertIn('entry_context["signal"]["audit"] = bot_audit_tag(winner)', src)


def close(pos, pool, band=None, ts=2_000_000_000, mode="pulse", root=None):
    signal = {"score": 70}
    if band:
        signal["audit"] = {"bot_pct": 26.0, "bot_band": band, "bot_bar_pct": 30}
    return {"ts": ts, "mode": mode, "pool": pool, "position": pos, "root_chain_id": root or pos,
            "pnl_sol": 0.5, "pnl_pct": 1.0, "dry_run": False, "signal": signal}


class Report(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile = Path(self.tmp.name)
        (self.profile / "memories").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, closes, realized, cash=()):
        mem = self.profile / "memories"
        for name, rows in (("dlmm_closes.jsonl", closes), ("dlmm_realized.jsonl", realized),
                           ("dlmm_realized_cash.jsonl", cash)):
            (mem / name).write_text("".join(json.dumps(r) + "\n" for r in rows))

    def run_report(self, since=None):
        from dlmm_realized import apply_realized
        return bb.report(str(self.profile), since, apply_realized)

    @staticmethod
    def realized(pos, sol):
        return {"position": pos, "realized_sol": sol, "realized_pct": 1.0}

    def test_band_summary_root_inheritance_and_unmeasured(self):
        closes = [close("p1", "A", "25-30"), close("p2", "B", "25-30"),
                  close("p2c", "B", root="p2"),             # re-center child: inherits 25-30
                  close("p3", "C", "<25"), close("p4", "D"),  # p4: entered before the tag
                  close("p5", "E", "25-30"),                 # never reconciled: unmeasured
                  close("t1", "F", "25-30", mode="turnover")]
        self.write(closes,
                   [self.realized("p1", 0.01), self.realized("p2", -0.002),
                    self.realized("p2c", 0.004), self.realized("p3", 0.001)],
                   [{"position": "p1", "cash_basis": "wallet", "cash_realized_sol": 0.009}])
        out = self.run_report()
        self.assertIn("5 tagged closes, 1 pulse closes without a band", out)
        line = next(l for l in out.splitlines() if l.startswith("25-30"))
        self.assertEqual(line.split()[1:4], ["4", "3", "3"])  # closes, pools, realized(n)
        self.assertIn("+0.0120", line)                         # 0.01 - 0.002 + 0.004
        self.assertIn("+0.0090", line)                         # wallet cash, p1 only
        self.assertIn("Kill rule (25-30): WAIT: 3 realized closes", out)

    def test_kill_rule(self):
        s = {"worst_sol": -0.031, "realized_n": 2, "realized_sol": 1.0, "ci": None}
        self.assertEqual(bb.kill_verdict(s)[0], "REVERT")
        s = {"worst_sol": -0.01, "realized_n": 14, "realized_sol": -1.0, "ci": (-1, -0.5)}
        self.assertEqual(bb.kill_verdict(s)[0], "WAIT")
        s.update(realized_n=15)
        self.assertEqual(bb.kill_verdict(s)[0], "REVERT")
        s.update(realized_sol=0.01, ci=(-0.002, -0.0001))
        self.assertEqual(bb.kill_verdict(s)[0], "REVERT")
        s.update(ci=(-0.002, 0.001))
        self.assertEqual(bb.kill_verdict(s)[0], "KEEP")
        s.update(ci=None)
        self.assertEqual(bb.kill_verdict(s)[0], "KEEP")

    def test_clustered_ci_resamples_pools(self):
        rows = [{"pool": "A", "pnl_sol": 1.0}] * 10 + [{"pool": "B", "pnl_sol": -1.0}]
        lo, _ = bb.cluster_ci(rows)
        self.assertLess(lo, 0)  # one pool of ten closes is one draw, not ten
        self.assertIsNone(bb.cluster_ci([{"pool": "A", "pnl_sol": 1.0}] * 3))

    def test_since_and_stats_cli(self):
        old = 1_700_000_000  # 2023-11-14 UTC
        self.write([close("p1", "A", "25-30", ts=old), close("p2", "B", "25-30")],
                   [self.realized("p1", -0.05), self.realized("p2", 0.01)])
        self.assertIn("REVERT", self.run_report())
        self.assertNotIn("REVERT", self.run_report("2024-01-01"))
        with patch.object(stats, "PROFILE_DIR", str(self.profile)), \
                patch.object(sys, "argv", ["dlmm_stats.py", "--bot-band", "--since", "2024-01-01"]), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            stats.main()
        self.assertIn("Pulse bot-holder bands since 2024-01-01", out.getvalue())
        self.assertIn("WAIT", out.getvalue())


if __name__ == "__main__":
    unittest.main()
