"""Kill-rule report for the pool-cash two-loss materiality floor (V5).
Synthetic journals only; nothing real is read."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dlmm_two_neg_report as tn  # noqa: E402
import dlmm_stats as stats  # noqa: E402


def close(pos, pool, waived=False, ts=2_000_000_000, mode="pulse", root=None):
    signal = {"score": 70}
    if waived:
        signal["pool_cash_gate"] = {"v0_would_block": True}
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
        return tn.report(str(self.profile), since, apply_realized)

    @staticmethod
    def realized(pos, sol):
        return {"position": pos, "realized_sol": sol, "realized_pct": 1.0}

    def test_cohorts_root_inheritance_and_unmeasured(self):
        closes = [close("p1", "A", True), close("p2", "B", True),
                  close("p2c", "B", root="p2"),          # re-center child inherits the waiver
                  close("p3", "C"), close("p4", "D", True),  # p4 never reconciled: unmeasured
                  close("t1", "E", True, mode="turnover")]
        self.write(closes, [self.realized("p1", 0.01), self.realized("p2", -0.002),
                            self.realized("p2c", 0.004), self.realized("p3", 0.001)],
                   [{"position": "p1", "cash_basis": "wallet", "cash_realized_sol": 0.009}])
        out = self.run_report()
        self.assertIn("5 pulse closes", out)
        line = next(l for l in out.splitlines() if l.startswith("v0_would_block"))
        self.assertEqual(line.split()[1:4], ["4", "3", "3"])  # closes, pools, realized(n)
        self.assertIn("+0.0120", line)
        self.assertIn("+0.0090", line)
        other = next(l for l in out.splitlines() if l.startswith("other"))
        self.assertEqual(other.split()[1:4], ["1", "1", "1"])
        self.assertIn("Kill rule (v0_would_block): WAIT: 3 realized closes", out)

    def test_kill_rule(self):
        s = {"worst_sol": -0.031, "realized_n": 2, "mean_sol": 1.0, "ci": None}
        self.assertEqual(tn.kill_verdict(s)[0], "REVERT")
        s = {"worst_sol": -0.01, "realized_n": 14, "mean_sol": -0.001, "ci": (-0.002, -0.0005)}
        self.assertEqual(tn.kill_verdict(s)[0], "WAIT")
        s.update(realized_n=15)
        self.assertEqual(tn.kill_verdict(s)[0], "REVERT")
        s.update(ci=(-0.002, 0.0001))          # mean < 0 but CI reaches 0: keep
        self.assertEqual(tn.kill_verdict(s)[0], "KEEP")
        s.update(mean_sol=0.0001, ci=(-0.002, -0.0001))  # both conditions are required
        self.assertEqual(tn.kill_verdict(s)[0], "KEEP")

    def test_since_and_stats_cli(self):
        self.write([close("p1", "A", True, ts=1_700_000_000)],
                   [self.realized("p1", -0.05)])
        self.assertIn("REVERT", self.run_report())
        self.assertNotIn("REVERT", self.run_report("2024-01-01"))
        out = io.StringIO()
        with patch.object(stats, "PROFILE_DIR", str(self.profile)), \
                patch.object(sys, "argv", ["dlmm_stats.py", "--two-neg"]), contextlib.redirect_stdout(out):
            stats.main()
        self.assertIn("Kill rule (v0_would_block): REVERT", out.getvalue())

    def test_pipeline_journals_the_tag(self):
        src = (Path(__file__).resolve().parent / "dlmm_pipeline.py").read_text()
        self.assertIn('c["pool_cash_gate"] = {"v0_would_block": True}', src)
        self.assertIn('"entry_live_gates", "pool_cash_gate")', src)


if __name__ == "__main__":
    unittest.main()
