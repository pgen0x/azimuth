"""PULSE_MAX_TICKET_SOL: a per-entry ticket ceiling that only ever lowers a ticket."""
import contextlib
import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_pipeline as pipeline

MINIMUM = pipeline.CASH_POLICY["minimum_entry_lamports"] / 1e9


@contextlib.contextmanager
def env(cap=None, liq=None):
    values = {k: v for k, v in os.environ.items() if k not in ("PULSE_MAX_TICKET_SOL", "PULSE_LIQ_HALF_USD")}
    if cap is not None:
        values["PULSE_MAX_TICKET_SOL"] = cap
    if liq is not None:
        values["PULSE_LIQ_HALF_USD"] = liq
    with patch.dict(os.environ, values, clear=True):
        yield


class CeilingTests(unittest.TestCase):
    def test_cap_applies_at_big_wallet(self):
        with env("1.0"):
            self.assertEqual(pipeline.max_ticket_sol(), 1.0)
            self.assertEqual(pipeline.compute_deploy_amount(3.65), 1.0)   # 45% would be ~1.63
            self.assertEqual(pipeline.compute_deploy_amount(20.0), 1.0)

    def test_unset_is_unchanged(self):
        with env():
            self.assertEqual(pipeline.max_ticket_sol(), 5.0)
            self.assertEqual(pipeline.compute_deploy_amount(3.65), 1.63)
            self.assertEqual(pipeline.compute_deploy_amount(20.0), 5.0)
            self.assertEqual(pipeline.compute_deploy_amount(0.8), 0.35)

    def test_malformed_falls_back(self):
        for raw in ("abc", "", " ", "0", "-1", "nan", "inf", "-inf"):
            with env(raw):
                self.assertEqual(pipeline.max_ticket_sol(), 5.0, raw)
                self.assertEqual(pipeline.compute_deploy_amount(3.65), 1.63, raw)

    def test_cap_never_below_minimum_and_never_raises(self):
        with env("0.05"):
            self.assertEqual(pipeline.max_ticket_sol(), MINIMUM)
            self.assertEqual(pipeline.compute_deploy_amount(3.65), MINIMUM)
        with env("1.0"):
            # Small wallets keep their own (smaller) ticket; the cap never raises it.
            self.assertEqual(pipeline.compute_deploy_amount(0.8), 0.35)
            self.assertEqual(pipeline.compute_deploy_amount(0.4), MINIMUM)
            self.assertEqual(pipeline.compute_deploy_amount(0.1), 0.0)

    def test_explicit_ceil_overrides_env(self):
        with env("1.0"):
            self.assertEqual(pipeline.compute_deploy_amount(3.65, ceil=5.0), 1.63)


class MainTailTests(unittest.TestCase):
    """Runs the real main() tail: R1 liquidity halving, then the final ceiling."""
    START = "    # Pulse liquidity-scaled ticket"
    END = '    print(f"\\n🚀 WINNING CANDIDATE'

    @classmethod
    def setUpClass(cls):
        source = Path(pipeline.__file__).read_text(encoding="utf-8")
        start = source.index(cls.START)
        cls.snippet = "\n".join(line[4:] for line in source[start:source.index(cls.END, start)].splitlines())
        cls.source = source

    def run_tail(self, deploy_sol, liquidity, cap, mode="pulse", sizing=True):
        winner = {"name": "TEST-SOL", "base_symbol": "TEST", "pool": "Pool",
                  "entry_live_gates": {"pool_liquidity_usd": liquidity}}
        rs = {"accepted_ticket_sol": deploy_sol, "ticket_cap_sol": cap, "ticket_capped": False} if sizing else None
        ns = {"liquidity_scaled_ticket": pipeline.liquidity_scaled_ticket, "mode": mode, "winner": winner,
              "risk_sizing": rs, "deploy_sol": deploy_sol, "ticket_cap": cap}
        with env(), contextlib.redirect_stdout(io.StringIO()):
            exec(self.snippet, ns)
        return ns["deploy_sol"], ns["risk_sizing"]

    def test_composes_with_r1_halving(self):
        # A capped 1.0 base halved by R1 is 0.5; a 1.2 base halved to 0.6 stays 0.6 under a 1.0 cap.
        self.assertEqual(self.run_tail(1.0, 9000.0, 1.0)[0], 0.5)
        ticket, rs = self.run_tail(1.2, 9000.0, 1.0)
        self.assertEqual(ticket, 0.6)
        self.assertFalse(rs["ticket_capped"])

    def test_final_guard_lowers_only(self):
        ticket, rs = self.run_tail(1.6, 50000.0, 1.0)      # deep pool, R1 leaves it, cap lowers it
        self.assertEqual(ticket, 1.0)
        self.assertTrue(rs["ticket_capped"])
        self.assertEqual(rs["accepted_ticket_sol"], 1.0)
        self.assertEqual(self.run_tail(0.35, 50000.0, 1.0)[0], 0.35)  # never raised

    def test_guard_applies_without_risk_sizing_and_other_modes(self):
        self.assertEqual(self.run_tail(1.6, 50000.0, 1.0, sizing=False)[0], 1.0)
        self.assertEqual(self.run_tail(1.6, 50000.0, 1.0, mode="turnover")[0], 1.0)

    def test_journal_and_single_env_read(self):
        self.assertIn("ticket_cap = max_ticket_sol()", self.source)
        self.assertIn("compute_deploy_amount(sol_balance, ceil=ticket_cap)", self.source)
        self.assertIn("ticket_capped=uncapped_base > ticket_cap", self.source)


if __name__ == "__main__":
    unittest.main()
