"""Pulse liquidity-scaled ticket: half size on thin or unknown entry depth, never a skip."""
import contextlib
import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_pipeline as pipeline

MINIMUM = pipeline.CASH_POLICY["minimum_entry_lamports"] / 1e9


def candidate(liquidity="missing"):
    c = {"name": "TEST-SOL", "base_symbol": "TEST", "pool": "Pool"}
    if liquidity != "missing":
        c["entry_live_gates"] = {"pool_liquidity_usd": liquidity, "exit_liquidity_floor_usd": 7000.0}
    return c


@contextlib.contextmanager
def threshold(value):
    env = dict(os.environ)
    env.pop("PULSE_LIQ_HALF_USD", None)
    if value is not None:
        env["PULSE_LIQ_HALF_USD"] = value
    with patch.dict(os.environ, env, clear=True):
        yield


class LiquidityScaledTicketTests(unittest.TestCase):
    def test_thin_pool_halves(self):
        with threshold(None):
            ticket, ev = pipeline.liquidity_scaled_ticket(0.36, candidate(9000.0), "pulse")
        self.assertEqual(ticket, 0.18)
        self.assertTrue(ev["liquidity_scaled"])
        self.assertEqual(ev["liquidity_usd"], 9000.0)
        self.assertEqual(ev["liq_half_usd"], 15000.0)
        self.assertEqual(ev["liquidity_multiplier"], 0.5)
        self.assertFalse(ev["liquidity_clamped"])
        self.assertEqual(ev["pre_liquidity_ticket_sol"], 0.36)

    def test_deep_pool_and_boundary_unchanged(self):
        with threshold(None):
            for depth in (15000.0, 15000, 80000.0):
                ticket, ev = pipeline.liquidity_scaled_ticket(0.36, candidate(depth), "pulse")
                self.assertEqual(ticket, 0.36)
                self.assertFalse(ev["liquidity_scaled"])
                self.assertEqual(ev["liquidity_multiplier"], 1.0)
                self.assertEqual(ev["liquidity_usd"], float(depth))

    def test_unknown_liquidity_halves(self):
        with threshold(None):
            for c in (candidate(), candidate(None), candidate(float("nan")), candidate(True),
                      candidate("12000"), candidate(-1.0), {"entry_live_gates": "bad"}):
                ticket, ev = pipeline.liquidity_scaled_ticket(0.36, c, "pulse")
                self.assertEqual(ticket, 0.18, c)
                self.assertTrue(ev["liquidity_scaled"])
                self.assertIsNone(ev["liquidity_usd"])

    def test_clamped_to_minimum_never_a_skip(self):
        with threshold(None):
            ticket, ev = pipeline.liquidity_scaled_ticket(0.15, candidate(5000.0), "pulse")
            self.assertEqual(ticket, MINIMUM)
            self.assertTrue(ev["liquidity_clamped"])
            ticket, ev = pipeline.liquidity_scaled_ticket(MINIMUM, candidate(), "pulse")
            self.assertEqual(ticket, MINIMUM)
            self.assertTrue(ev["liquidity_scaled"] and ev["liquidity_clamped"])
            ticket, ev = pipeline.liquidity_scaled_ticket(0.20, candidate(5000.0), "pulse")
            self.assertEqual(ticket, MINIMUM)  # half lands exactly on the minimum: no clamp
            self.assertFalse(ev["liquidity_clamped"])
        self.assertGreater(ticket, 0)

    def test_zero_disables(self):
        with threshold("0"):
            self.assertEqual(pipeline.liquidity_scaled_ticket(0.36, candidate(5000.0), "pulse"), (0.36, None))
            self.assertEqual(pipeline.liquidity_scaled_ticket(0.36, candidate(), "pulse"), (0.36, None))

    def test_threshold_from_env_and_malformed_falls_back(self):
        with threshold("30000"):
            ticket, ev = pipeline.liquidity_scaled_ticket(0.36, candidate(20000.0), "pulse")
            self.assertEqual((ticket, ev["liq_half_usd"]), (0.18, 30000.0))
        for bad in ("abc", "-5", "nan", "inf", " "):
            with threshold(bad):
                self.assertEqual(pipeline.pulse_liq_half_usd(), 15000.0, bad)

    def test_other_modes_unaffected(self):
        with threshold(None):
            for mode in ("turnover", "casual", "multiday"):
                self.assertEqual(pipeline.liquidity_scaled_ticket(0.36, candidate(5000.0), mode), (0.36, None))
                self.assertEqual(pipeline.liquidity_scaled_ticket(0.36, candidate(), mode), (0.36, None))


class MainCallSiteTests(unittest.TestCase):
    """Executes the real main() block that applies the rule after the live gate."""
    START = "    # Pulse liquidity-scaled ticket"
    END = '    print(f"\\n🚀 WINNING CANDIDATE'

    @classmethod
    def setUpClass(cls):
        source = Path(pipeline.__file__).read_text(encoding="utf-8")
        start = source.index(cls.START)
        end = source.index(cls.END, start)
        cls.snippet = "\n".join(line[4:] for line in source[start:end].splitlines())
        # The rule must run after the live gate that measures the depth.
        cls.gate_offset = source.rfind("predeploy_live_gate_reject(winner", 0, start)
        cls.sizing_offset = source.rfind("risk_scaled_ticket(deploy_sol, winner", 0, start)

    def run_block(self, mode, winner, risk_sizing, deploy_sol=0.36):
        ns = {"liquidity_scaled_ticket": pipeline.liquidity_scaled_ticket, "mode": mode,
              "winner": winner, "risk_sizing": risk_sizing, "deploy_sol": deploy_sol,
              "ticket_cap": pipeline.MAX_TICKET_SOL_DEFAULT}
        out = io.StringIO()
        with threshold(None), contextlib.redirect_stdout(out):
            exec(self.snippet, ns)
        return ns, out.getvalue()

    def sizing(self):
        return {"version": 1, "multiplier": 1.0, "requested_ticket_sol": 0.36, "accepted_ticket_sol": 0.36}

    def test_runs_after_risk_sizing_and_live_gate(self):
        self.assertGreater(self.gate_offset, self.sizing_offset)
        self.assertGreater(self.sizing_offset, 0)

    def test_pulse_thin_pool_journals_and_halves(self):
        ns, out = self.run_block("pulse", candidate(9000.0), self.sizing())
        self.assertEqual(ns["deploy_sol"], 0.18)
        rs = ns["risk_sizing"]
        self.assertEqual(rs["accepted_ticket_sol"], 0.18)
        self.assertEqual(rs["multiplier"], 1.0)  # conviction multiplier stays separate
        self.assertTrue(rs["liquidity_scaled"])
        self.assertEqual((rs["liquidity_usd"], rs["liq_half_usd"]), (9000.0, 15000.0))
        self.assertIn("Liquidity-scaled ticket", out)

    def test_pulse_unknown_depth_clamped_still_deploys(self):
        ns, out = self.run_block("pulse", candidate(), self.sizing(), deploy_sol=0.15)
        self.assertEqual(ns["deploy_sol"], MINIMUM)
        self.assertTrue(ns["risk_sizing"]["liquidity_clamped"])
        self.assertIn("unknown", out)
        self.assertIn("clamped to minimum", out)

    def test_pulse_deep_pool_journals_unscaled(self):
        ns, out = self.run_block("pulse", candidate(50000.0), self.sizing())
        self.assertEqual(ns["deploy_sol"], 0.36)
        self.assertFalse(ns["risk_sizing"]["liquidity_scaled"])
        self.assertEqual(out, "")

    def test_non_pulse_and_unsized_paths_untouched(self):
        ns, _ = self.run_block("turnover", candidate(5000.0), self.sizing())
        self.assertEqual(ns["deploy_sol"], 0.36)
        self.assertNotIn("liquidity_scaled", ns["risk_sizing"])
        ns, _ = self.run_block("pulse", candidate(5000.0), None)
        self.assertEqual(ns["deploy_sol"], 0.36)


if __name__ == "__main__":
    unittest.main()
