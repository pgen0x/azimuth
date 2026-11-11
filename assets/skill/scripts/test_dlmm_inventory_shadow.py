"""Shadow inventory-share exit. Synthetic fixtures only — no real positions or pools."""
import io
import json
import math
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import dlmm_inventory_shadow as inv
import dlmm_monitor as monitor

POS = "P" * 32
POS2 = "Q" * 32
POOL = "L" * 32
ON = {}  # empty env: defaults, shadow on


def mark(token_raw, sol_raw, pnl_pct=-3.0, active=0, step=100, sol_is_x=False, total=None, fee_token=0, fee_sol=0):
    """A verified-shape native mark. At active=0 the bin price is exactly 1 raw/raw."""
    price = math.exp(active * math.log1p(step / 10000.0))
    t, s = token_raw + fee_token, sol_raw + fee_sol
    value = (t / price + s) if sol_is_x else (t * price + s)
    x, y, fx, fy = (sol_raw, token_raw, fee_sol, fee_token) if sol_is_x else (token_raw, sol_raw, fee_token, fee_sol)
    deposit = round(value / (1 + pnl_pct / 100.0))
    upper = round(value) if total is None else total
    return {"pnl_pct": pnl_pct, "pnl_sol": (upper - deposit) / 1e9, "active_bin": active,
            "deposit_lamports": str(deposit), "value_lamports_upper": str(upper),
            "inventory": {"net_x_raw": str(x), "net_y_raw": str(y), "net_fee_x_raw": str(fx), "net_fee_y_raw": str(fy)},
            "bin_observation": {"version": 1, "bin_step": step, "sol_is_x": sol_is_x, "bins": []}}


def meta(liq=10000.0, mode="pulse", strategy="sol_bidask", deployed_at=1000.0):
    gates = {} if liq is None else {"pool_liquidity_usd": liq}
    return {"mode": mode, "strategy": strategy, "deployed_at": deployed_at,
            "signal": {"entry_live_gates": gates}}


def rows(path):
    with open(path) as stream:
        return [json.loads(line) for line in stream if line.strip()]


class ShareTests(unittest.TestCase):
    def test_share_sol_y(self):
        self.assertAlmostEqual(inv.token_share(mark(600_000_000, 400_000_000)), 0.6, places=6)

    def test_share_sol_x_orientation(self):
        # SOL=X: the token is Y, quoted in raw Y per raw X, so its SOL value is raw / price.
        self.assertAlmostEqual(inv.token_share(mark(700_000_000, 300_000_000, sol_is_x=True)), 0.7, places=6)
        token = 700_000_000 / 1.01 ** 37
        self.assertAlmostEqual(inv.token_share(mark(700_000_000, 300_000_000, sol_is_x=True, active=37)),
                               token / (token + 300_000_000), places=6)

    def test_share_includes_fees_and_off_par_price(self):
        m = mark(500_000_000, 500_000_000, active=-120, fee_token=50_000_000, fee_sol=10_000_000)
        price = 1.01 ** -120
        token = 550_000_000 * price
        self.assertAlmostEqual(inv.token_share(m), token / (token + 510_000_000), places=6)

    def test_inconsistent_value_is_unmeasured(self):
        self.assertIsNone(inv.token_share(mark(600_000_000, 400_000_000, total=2_000_000_000)))

    def test_malformed_is_unmeasured(self):
        for broken in ({}, None, dict(mark(1, 1), inventory={"net_x_raw": "-1"}),
                       dict(mark(1, 1), bin_observation={"bin_step": 100, "sol_is_x": "no"})):
            self.assertIsNone(inv.token_share(broken))


class EvaluateTests(unittest.TestCase):
    def fire(self, m=None, mt=None, env=ON):
        return inv.evaluate(POS, POOL, meta() if mt is None else mt,
                            mark(600_000_000, 400_000_000) if m is None else m, 1600.0, env)

    def test_fires_when_all_hold(self):
        row = self.fire()
        self.assertIsNotNone(row)
        self.assertEqual((row["position"], row["pool"], row["mode"]), (POS, POOL, "pulse"))
        self.assertAlmostEqual(row["token_share"], 0.6, places=6)
        self.assertEqual((row["entry_liq_usd"], row["age_min"]), (10000.0, 10.0))
        self.assertAlmostEqual(row["mark_value_sol"], 1.0)
        for key in ("ts", "pnl_pct", "mark_pnl_sol", "deposit_sol", "thresholds", "basis"):
            self.assertIn(key, row)

    def test_no_fire_share_below(self):
        self.assertIsNone(self.fire(m=mark(400_000_000, 600_000_000)))

    def test_share_boundary_inclusive(self):
        self.assertIsNotNone(self.fire(m=mark(500_000_000, 500_000_000)))

    def test_no_fire_pnl_above(self):
        self.assertIsNone(self.fire(m=mark(600_000_000, 400_000_000, pnl_pct=-1.0)))

    def test_no_fire_liquidity_at_or_above_cap(self):
        self.assertIsNone(self.fire(mt=meta(liq=25000.0)))
        self.assertIsNone(self.fire(mt=meta(liq=40000.0)))

    def test_unknown_liquidity_never_fires(self):
        self.assertIsNone(self.fire(mt=meta(liq=None)))
        self.assertIsNone(self.fire(mt={"mode": "pulse", "strategy": "sol_bidask"}))
        self.assertIsNone(self.fire(mt=meta(liq=float("nan"))))

    def test_unmeasured_share_never_fires(self):
        self.assertIsNone(self.fire(m=mark(600_000_000, 400_000_000, total=5_000_000_000)))

    def test_scope_pulse_sol_bidask_only(self):
        self.assertIsNone(self.fire(mt=meta(mode="turnover")))
        self.assertIsNone(self.fire(mt=meta(strategy="balanced_tight")))

    def test_kill_switch(self):
        for off in ("false", "0", "off", "FALSE"):
            self.assertIsNone(self.fire(env={"INV_SHARE_SHADOW": off}))
        self.assertIsNotNone(self.fire(env={"INV_SHARE_SHADOW": "true"}))

    def test_env_thresholds(self):
        self.assertIsNone(self.fire(env={"INV_SHARE_PCT": "70"}))
        self.assertIsNone(self.fire(env={"INV_SHARE_PNL_PCT": "-5"}))
        self.assertIsNone(self.fire(env={"INV_SHARE_MAX_LIQ_USD": "5000"}))
        self.assertEqual(inv.thresholds({"INV_SHARE_PCT": "garbage"})["INV_SHARE_PCT"], 50.0)
        self.assertEqual(inv.thresholds({"INV_SHARE_PCT": "nan"})["INV_SHARE_PCT"], 50.0)


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile = self.tmp.name
        self.path = os.path.join(self.profile, "memories", inv.SHADOW_FILE)

    def tearDown(self):
        self.tmp.cleanup()

    def row(self, position=POS, pnl=-3.0):
        r = inv.evaluate(position, POOL, meta(), mark(600_000_000, 400_000_000, pnl_pct=pnl), 1600.0, ON)
        self.assertIsNotNone(r)
        return r

    def test_one_row_per_position(self):
        self.assertTrue(inv.record(self.profile, self.row()))
        self.assertFalse(inv.record(self.profile, self.row(pnl=-6.0)))   # later, deeper tick
        self.assertTrue(inv.record(self.profile, self.row(POS2)))
        got = rows(self.path)
        self.assertEqual([r["position"] for r in got], [POS, POS2])
        self.assertAlmostEqual(got[0]["pnl_pct"], -3.0, places=4)       # the FIRST fire is kept

    def test_flush_writes_through_monitor(self):
        with patch.object(monitor, "PROFILE_DIR", self.profile), redirect_stdout(io.StringIO()):
            monitor.flush_tick_observers([("inventory", (self.row(),)), ("inventory", (self.row(),))])
        self.assertEqual(len(rows(self.path)), 1)

    def test_record_never_raises(self):
        with open(os.path.join(self.profile, "memories"), "w") as blocker:   # memories is a file
            blocker.write("x")
        with redirect_stdout(io.StringIO()) as out:
            self.assertFalse(inv.record(self.profile, self.row()))
        self.assertIn("INVENTORY_SHADOW_ERROR", out.getvalue())


class JoinReportTests(unittest.TestCase):
    def test_join_and_report(self):
        shadow = {POS: {"position": POS, "mark_pnl_sol": -0.010},
                  POS2: {"position": POS2, "mark_pnl_sol": -0.008},
                  "R" * 32: {"position": "R" * 32, "mark_pnl_sol": -0.005}}
        cash = {POS: {"cash_basis": "wallet", "cash_realized_sol": -0.030},
                POS2: {"cash_basis": "wallet", "cash_realized_sol": 0.004},
                "R" * 32: {"cash_basis": "partial", "cash_realized_sol": None}}
        measured, unmeasured = inv.join(shadow, cash)
        self.assertEqual((len(measured), unmeasured), (2, 1))
        by = {m["position"]: m for m in measured}
        self.assertAlmostEqual(by[POS]["delta_sol"], 0.020)
        self.assertTrue(by[POS2]["closed_positive"])

        with tempfile.TemporaryDirectory() as profile:
            mem = os.path.join(profile, "memories")
            os.makedirs(mem)
            with open(os.path.join(mem, inv.SHADOW_FILE), "w") as f:
                for r in shadow.values():
                    f.write(json.dumps(r) + "\n")
                f.write(json.dumps({"position": POS, "mark_pnl_sol": 9.0}) + "\n")   # duplicate ignored
            with open(os.path.join(mem, "dlmm_realized_cash.jsonl"), "w") as f:
                for p, c in cash.items():
                    f.write(json.dumps(dict(c, position=p)) + "\n")
            text = inv.report(profile)
        self.assertIn("3 would-fire", text)
        self.assertIn("2 joined to wallet cash, 1 unmeasured", text)
        self.assertIn("+0.004000", text)            # mean of (+0.020, -0.012)
        self.assertIn("closed positive: 1/2", text)


if __name__ == "__main__":
    unittest.main()
