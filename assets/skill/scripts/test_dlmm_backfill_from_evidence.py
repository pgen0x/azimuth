"""Evidence backfill: dry run by default, one row per proved close, never a guess."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import dlmm_backfill_from_evidence as backfill

POOL = "P" * 40
LOST = "L" * 40
UNMEASURED = "U" * 40
KEPT = "K" * 40
STAMP = 1_790_000_000


def proved(position, pool=POOL, ts=STAMP):
    return dict(position=position, pool=pool, root_chain_id=position, ts=ts, pnl_sol=None,
                source="finalized_close_evidence", signature="sig-" + position[:4])


class EvidenceBackfillTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.profile = Path(tmp.name)
        self.memory = self.profile / "memories"
        (self.memory / "dlmm_entries").mkdir(parents=True)
        for position, mode in ((LOST, "pulse"), (UNMEASURED, "turnover"), (KEPT, "pulse")):
            (self.memory / "dlmm_entries" / (position + ".json")).write_text(json.dumps(dict(
                position=position, pool=POOL, pair="T-SOL", base_mint="MINT", mode=mode, size_sol=.1,
                strategy="sol_bidask", deployed_at=STAMP - 402, signal={"score": 70},
                risk_sizing={"entry_route": "hermes_ai"})))
        (self.memory / "dlmm_realized.jsonl").write_text(json.dumps(dict(
            position=LOST, realized_sol=-.0012, realized_pct=-1.2, fetched_at=STAMP + 60)) + "\n")
        self.closes = self.memory / "dlmm_closes.jsonl"
        self.closes.write_text(json.dumps(dict(position=KEPT, event="exit", reason="already journaled")) + "\n")
        ledger = dict(recovered_closes=[proved(UNMEASURED, ts=STAMP + 5), proved(LOST), proved(KEPT)])
        patcher = patch.object(backfill, "report", return_value=ledger)
        patcher.start()
        self.addCleanup(patcher.stop)

    def journal(self):
        return [json.loads(l) for l in self.closes.read_text().splitlines()]

    def test_rows_join_entry_and_realized_and_skip_journaled(self):
        rows = backfill.evidence_rows(self.profile)
        self.assertEqual([r["position"] for r in rows], [LOST, UNMEASURED])  # oldest first, KEPT skipped
        lost, unmeasured = rows
        self.assertEqual((lost["ts"], lost["timestamp"], lost["pair"], lost["mode"], lost["txs"]),
                         (STAMP, "2026-09-21T14:13:20Z", "T-SOL", "pulse", ["sig-LLLL"]))
        self.assertEqual((lost["pnl_sol"], lost["pnl_pct"], lost["pnl_basis"]), (-.0012, -1.2, "realized"))
        self.assertEqual((lost["age_min"], lost["event"], lost["dry_run"], lost["source"]), (6.7, "exit", False, "evidence_backfill"))
        self.assertEqual(lost["risk_sizing"], {"entry_route": "hermes_ai"})
        self.assertIs(lost["recovered_from_evidence"], True)
        # Unmeasured stays null: no mark is promoted to a result.
        self.assertEqual((unmeasured["pnl_sol"], unmeasured["pnl_pct"], unmeasured["pnl_basis"]), (None, None, "unmeasured"))
        for field in ("fee_per_tvl_24h", "peak_pnl", "ai_holds", "unclaimed_fees_sol"):
            self.assertIsNone(lost[field])

    def test_dry_run_writes_nothing_and_apply_is_idempotent(self):
        before = self.closes.read_text()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            backfill.main(["--profile", str(self.profile)])
        self.assertEqual(self.closes.read_text(), before)
        self.assertEqual(len(out.getvalue().splitlines()), 2)
        self.assertIn("dry run: 2", err.getvalue())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            backfill.main(["--profile", str(self.profile), "--position", LOST, "--apply"])
            backfill.main(["--profile", str(self.profile), "--position", LOST, "--apply"])
        self.assertEqual([r["position"] for r in self.journal()], [KEPT, LOST])
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            backfill.main(["--profile", str(self.profile), "--apply"])
            backfill.main(["--profile", str(self.profile), "--apply"])
        self.assertEqual([r["position"] for r in self.journal()], [KEPT, LOST, UNMEASURED])

    def test_mismatched_or_missing_entry_is_never_invented(self):
        (self.memory / "dlmm_entries" / (UNMEASURED + ".json")).write_text(json.dumps(dict(position=UNMEASURED, pool="other")))
        (self.memory / "dlmm_entries" / (LOST + ".json")).unlink()
        self.assertEqual(backfill.evidence_rows(self.profile), [])


class SpawnerHeapCapTests(unittest.TestCase):
    """Every Python helper that spawns dlmm_executor.js caps its node children at import."""
    def test_each_spawner_caps_node_options(self):
        env = {k: v for k, v in os.environ.items() if k != "NODE_OPTIONS"}
        here = os.path.dirname(os.path.abspath(__file__))
        for module in ("dlmm_monitor", "dlmm_pipeline", "dlmm_accounting", "dlmm_candidate_paper",
                       "dlmm_price_path", "dlmm_shadow"):
            with self.subTest(module=module):
                out = subprocess.run([sys.executable, "-c", f"import os,sys; sys.argv=['x']; import {module}; "
                                      "print(os.environ['NODE_OPTIONS'])"],
                                     cwd=here, env=env, capture_output=True, text=True, timeout=120)
                self.assertEqual(out.returncode, 0, out.stderr[-500:])
                self.assertEqual(out.stdout.strip().splitlines()[-1], "--max-old-space-size=768")
        env["NODE_OPTIONS"] = "--max-old-space-size=2048"
        out = subprocess.run([sys.executable, "-c", "import os; import dlmm_pipeline; print(os.environ['NODE_OPTIONS'])"],
                             cwd=here, env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(out.stdout.strip().splitlines()[-1], "--max-old-space-size=2048")


if __name__ == "__main__":
    unittest.main()
