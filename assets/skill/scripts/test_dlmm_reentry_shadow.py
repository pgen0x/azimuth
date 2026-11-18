"""Offline tests for the logging-only re-entry shadow journal."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_monitor as monitor
import dlmm_reentry_shadow as shadow

POOL = "3BCeknAQpHELGfKhUb9mnKuLC3Eg3qjJrZ5B7fqC1xSW"
META = {"base_mint": "MintAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}


class ReentryShadowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile = Path(self.tmp.name)
        (self.profile / "memories").mkdir()
        self.journal = self.profile / "memories" / "dlmm_reentry_shadow.jsonl"
        patcher = patch.object(monitor, "PROFILE_DIR", str(self.profile))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("REENTRY_SHADOW", None)
        monitor._REENTRY_SHADOW_WARNED = False

    def rows(self):
        if not self.journal.exists():
            return []
        return [json.loads(l) for l in self.journal.read_text().splitlines() if l.strip()]

    def record(self, reason, pnl_pct=1.0, active_bin=10, upper_bin=5):
        return monitor.record_reentry_shadow(POOL, META, reason, pnl_pct, 1_800_000_000.7,
                                             active_bin, upper_bin, 3600)

    def test_each_qualifying_reason_writes_exactly_one_row(self):
        cases = [
            ("Pumped far above range (Active bin 30 > Upper bin 5 + 20)", 2.0, 30, 5),
            ("Out of Range for 31.0m (limit 30m)", 0.4, 10, 5),
            ("Trailing Take-Profit hit (Peak: 4.00%, Current: 2.50% <= ratchet floor 2.60%)", 2.5, 3, 5),
            ("Fast-out dump exit (5m -6.0% <= -5.0%)", 0.3, 3, 5),
        ]
        for i, (reason, pnl, active, upper) in enumerate(cases, 1):
            with self.subTest(reason=reason):
                self.assertTrue(self.record(reason, pnl, active, upper))
                rows = self.rows()
                self.assertEqual(len(rows), i)
                row = rows[-1]
                self.assertEqual(set(row), {"kind", "ts", "pool", "mint", "reason", "pnl_pct",
                                            "closed_at", "active_bin", "upper_bin", "cooldown_secs"})
                self.assertEqual((row["kind"], row["pool"], row["mint"], row["reason"]),
                                 ("close", POOL, META["base_mint"], reason))
                self.assertEqual((row["pnl_pct"], row["closed_at"], row["active_bin"],
                                  row["upper_bin"], row["cooldown_secs"]),
                                 (pnl, 1_800_000_000, active, upper, 3600))

    def test_loss_downside_oor_and_sl_write_nothing(self):
        for reason, pnl, active, upper in [
            ("Fast-out dump exit (5m -6.0% <= -5.0%)", -1.2, 3, 5),       # loss fast-out
            ("Fast-out dump exit, underwater (5m -6.0%)", 0.0, 3, 5),      # not > 0
            ("Out of Range for 31.0m (limit 30m)", 0.4, 2, 5),             # downside OOR
            ("Out of Range for 31.0m (limit 30m)", 0.4, None, 5),          # unknown bins
            ("Stop-loss hit (-8.10% <= -8.0%)", -8.1, 3, 5),
            ("Low yield (fee/TVL 0.1% < 7%)", 0.2, 3, 5),
        ]:
            with self.subTest(reason=reason, active=active):
                self.assertFalse(self.record(reason, pnl, active, upper))
        self.assertEqual(self.rows(), [])

    def test_write_error_does_not_raise_and_warns_once(self):
        with patch.object(monitor, "PROFILE_DIR", str(self.profile / "missing" / "dir")), \
             patch("builtins.print") as printed:
            self.assertFalse(self.record("Trailing Take-Profit hit"))
            self.assertFalse(self.record("Trailing Take-Profit hit"))
        self.assertEqual(printed.call_count, 1)

    def test_disabled_by_env_writes_nothing(self):
        os.environ["REENTRY_SHADOW"] = "0"
        self.assertFalse(self.record("Pumped far above range (Active bin 30 > Upper bin 5 + 20)"))
        self.assertEqual(self.rows(), [])

    def test_close_path_call_site_is_logging_only(self):
        # The call must sit after the cooldown writes and its result must be unused,
        # so the close path's Redis writes and return values cannot change.
        src = Path(monitor.__file__).read_text()
        cooldown = src.index('print(f"🚫 Re-entry cooldown set for {base_symbol_cd}: {cd_label}')
        call = src.index("record_reentry_shadow(pool, meta, close_reason", cooldown)
        self.assertLess(cooldown, call)
        line = src[src.rindex("\n", 0, call) + 1:src.index("\n", call)]
        self.assertTrue(line.strip().startswith("record_reentry_shadow("), line)


class PipelineBlockedTests(unittest.TestCase):
    NOW = 1_800_000_000
    CAND = {"pool": POOL, "base_mint": META["base_mint"], "fee_active_tvl_ratio": 0.07, "active_tvl": 27400.0}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profile = Path(self.tmp.name)
        (self.profile / "memories").mkdir()
        self.journal = self.profile / "memories" / "dlmm_reentry_shadow.jsonl"
        env = patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("REENTRY_SHADOW", None)

    def close_row(self, closed_at, pool=POOL, mint=META["base_mint"]):
        with open(self.journal, "a") as f:
            f.write(json.dumps(dict(kind="close", ts=closed_at, pool=pool, mint=mint,
                                    reason="Trailing Take-Profit hit", pnl_pct=2.0,
                                    closed_at=closed_at, active_bin=3, upper_bin=5,
                                    cooldown_secs=7200)) + "\n")

    def blocked(self):
        return [json.loads(l) for l in self.journal.read_text().splitlines()
                if json.loads(l)["kind"] == "blocked"]

    def call(self, now, mode="pulse", h1=None, cand=None):
        return shadow.record_reentry_blocked(str(self.profile), mode, cand or self.CAND, h1=h1, now=now)

    def test_m5_dump_within_60m_of_close_writes_one_row_and_dedups(self):
        self.close_row(self.NOW - 1800)
        self.assertTrue(self.call(self.NOW))
        self.assertFalse(self.call(self.NOW + 300))   # inside 10m
        self.assertTrue(self.call(self.NOW + 601))    # dedup over, still < 60m after close
        rows = self.blocked()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], dict(kind="blocked", ts=self.NOW, pool=POOL, mint=META["base_mint"],
                                       block_reason="momentum_m5_dump", fee_active_tvl_5m=0.07,
                                       active_tvl=27400.0))

    def test_no_row_without_a_recent_matching_close(self):
        self.assertFalse(self.call(self.NOW))                    # no journal at all
        self.close_row(self.NOW - 3601)                          # too old
        self.close_row(self.NOW - 60, mint="OtherMint")          # other mint
        self.close_row(self.NOW - 60, pool="OtherPool")          # other pool
        self.assertFalse(self.call(self.NOW))
        self.assertEqual(self.blocked(), [])

    def test_second_gate_mode_and_env_write_nothing(self):
        self.close_row(self.NOW - 60)
        self.assertFalse(self.call(self.NOW, h1=-20.0))          # h1 gate fails too
        self.assertFalse(self.call(self.NOW, mode="turnover"))
        os.environ["REENTRY_SHADOW"] = "0"
        self.assertFalse(self.call(self.NOW))
        self.assertEqual(self.blocked(), [])

    def test_write_error_does_not_raise(self):
        self.close_row(self.NOW - 60)
        with patch("builtins.open", side_effect=OSError("disk full")):
            self.assertFalse(self.call(self.NOW))

    def test_pipeline_call_site_is_logging_only(self):
        src = (Path(shadow.__file__).parent / "dlmm_pipeline.py").read_text()
        # Inside the m5 reject branch, before its reject record and `continue`:
        # the branch still rejects, whatever the journal call does.
        branch = src.index("if m5 is not None and m5 < -5.0:")
        call = src.index("record_reentry_blocked(PROFILE_DIR, mode, c, h1=h1)", branch)
        reject = src.index('record_pipeline_reject(PROFILE_DIR, mode, "momentum_m5_dump"', branch)
        self.assertLess(call, reject)
        self.assertNotIn("continue", src[branch:call])
        self.assertIn("continue", src[reject:src.index("if h1 is not None and h1 < -15.0:", reject)])
        line = src[src.rindex("\n", 0, call) + 1:src.index("\n", call)]
        self.assertTrue(line.strip().startswith("record_reentry_blocked("), line)


if __name__ == "__main__":
    unittest.main()
