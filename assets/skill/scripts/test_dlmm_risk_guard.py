"""dlmm_risk_guard.py on synthetic NAV journals; nothing real is read or sent."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dlmm_risk_guard as g  # noqa: E402
import dlmm_pipeline as pipeline  # noqa: E402

T0 = 2_000_000_000
WALLET = "synthetic-wallet"


def row(ts, equity, flow_sol=0.0, lp=0.1, complete=True, since=1_000, wallet=WALLET):
    return {"ts": ts, "wallet": wallet, "coverage_since": since, "lp_mark_sol": lp,
            "wallet_history_complete": complete, "known_asset_subtotal_sol": equity,
            "external_flow_lamports": round(flow_sol * 1e9), "nav_sol": None}


class Guard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.profile = base / "profile"
        (self.profile / "memories").mkdir(parents=True)
        self.sd = base / "state"
        self.env = {"AZIMUTH_RISK_STATE_DIR": str(self.sd), "DLMM_ALERT_TARGET": "telegram"}
        self.nav = self.profile / "memories" / "dlmm_nav.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, *rows):
        with open(self.nav, "a") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def run_guard(self, now, write=True):
        return g.evaluate([str(self.profile)], now=now, env=self.env, write=write)

    def init(self, value="current", now=T0):
        return g.set_mark([str(self.profile)], value, now=now, env=self.env)

    def pause(self):
        obj, err = g._read_json(self.sd / "risk_pause.json")
        self.assertIsNone(err)
        return obj

    def alerts(self):
        outbox = self.profile / "memories" / "dlmm_alert_outbox"
        return [json.loads(p.read_text())["text"] for p in sorted(outbox.glob("*.json"))] if outbox.exists() else []

    # -------------------------------------------------- acceptance

    def test_equity_acceptance_rules(self):
        now = T0
        self.assertEqual(g.acceptable(row(now, 1.0), now), (1.0, 0.0))
        for bad in (row(now, 1.0, lp=None), row(now, 1.0, complete=False), row(now, 1.0, complete="true"),
                    row(now, None), row(now + 3600, 1.0), {**row(now, 1.0), "external_flow_lamports": None},
                    {**row(now, 1.0), "known_asset_subtotal_sol": float("nan")}, {**row(now, 1.0), "ts": "x"}):
            self.assertIsNone(g.acceptable(bad, now), bad)
        # nav_sol null (unquotable dust) does not blind the guard.
        self.assertIsNotNone(g.acceptable({**row(now, 1.0), "nav_sol": None}, now))
        # The newest ACCEPTABLE row wins over a newer unacceptable one.
        self.add(row(now - 600, 1.0), row(now - 60, 5.0, lp=None))
        obs = g.observe([str(self.profile)], now)
        self.assertEqual((obs["equity"], obs["oldest_ts"]), (1.0, now - 600))

    def test_no_mark_fails_closed(self):
        self.add(row(T0, 1.0))
        s = self.run_guard(T0)
        self.assertTrue(s["paused"])
        self.assertIn("no high-water mark", self.pause()["reason"])

    # -------------------------------------------------- flows

    def test_deposit_neither_trips_nor_inflates(self):
        self.add(row(T0, 1.0))
        self.init()
        # Lose 20%, then deposit 2.8 SOL: the loss stays a loss, the deposit is not profit.
        self.add(row(T0 + 600, 0.8))
        self.assertAlmostEqual(self.run_guard(T0 + 600)["dd"], 0.2)
        self.add(row(T0 + 1200, 3.6, flow_sol=2.8))
        s = self.run_guard(T0 + 1200)
        self.assertFalse(s["paused"])
        self.assertAlmostEqual(s["peak"], 3.8)              # 1.0 peak + 2.8 deposited
        self.assertAlmostEqual(s["dd"], 1 - 3.6 / 3.8)
        state, _ = g._read_json(self.sd / "risk_hwm.json")
        self.assertAlmostEqual(state["hwm_adj"], 1.0)       # the mark did not move
        # 30% of the enlarged capital trips; just under it does not.
        self.add(row(T0 + 1800, 3.8 * 0.7001, flow_sol=2.8))
        self.assertFalse(self.run_guard(T0 + 1800)["paused"])
        self.add(row(T0 + 2400, 3.8 * 0.70, flow_sol=2.8))
        self.assertTrue(self.run_guard(T0 + 2400)["paused"])

    def test_deposit_from_flat_with_prior_flows(self):
        # Cumulative flows were already non-zero when the mark was set: the literal
        # 1 - adj/hwm would be meaningless here (adj = -0.5), the guard is not.
        self.add(row(T0, 1.0, flow_sol=1.5))
        self.init()
        self.add(row(T0 + 600, 3.8, flow_sol=4.3))
        s = self.run_guard(T0 + 600)
        self.assertFalse(s["paused"])
        self.assertAlmostEqual(s["dd"], 0.0)
        self.assertEqual(self.alerts(), [])

    def test_withdrawal_is_not_a_drawdown(self):
        self.add(row(T0, 2.0))
        self.init()
        self.add(row(T0 + 600, 1.0, flow_sol=-1.0))
        s = self.run_guard(T0 + 600)
        self.assertFalse(s["paused"])
        self.assertAlmostEqual(s["dd"], 0.0)

    def test_mark_rises_with_profit(self):
        self.add(row(T0, 1.0))
        self.init()
        self.add(row(T0 + 600, 2.0))
        self.run_guard(T0 + 600)
        self.add(row(T0 + 1200, 1.41))
        self.assertFalse(self.run_guard(T0 + 1200)["paused"])
        self.add(row(T0 + 1800, 1.4))
        s = self.run_guard(T0 + 1800)
        self.assertTrue(s["paused"])
        self.assertAlmostEqual(s["peak"], 2.0)

    # -------------------------------------------------- trigger

    def test_trigger_at_exactly_thirty_percent_alerts_once(self):
        self.add(row(T0, 1.0))
        self.init()
        self.add(row(T0 + 600, 0.70))
        s = self.run_guard(T0 + 600)
        self.assertEqual((s["paused"], s["action"]), (True, "paused"))
        p = self.pause()
        self.assertEqual(p["paused"], True)
        self.assertAlmostEqual(p["dd"], 0.30)
        self.assertAlmostEqual(p["hwm"], 1.0)
        self.assertAlmostEqual(p["equity"], 0.70)
        self.assertIn("drawdown 30.0% >= 30%", p["reason"])
        self.assertEqual(len(self.alerts()), 1)
        self.assertIn("PAUSED new entries", self.alerts()[0])
        # Recovery does not unpause; only a manual resume does. No repeat alert.
        self.add(row(T0 + 1200, 1.0))
        self.assertEqual(self.run_guard(T0 + 1200)["action"], None)
        self.assertTrue(self.pause()["paused"])
        self.assertEqual(len(self.alerts()), 1)

    def test_threshold_env(self):
        self.assertEqual(g.max_drawdown({}), 0.30)
        self.assertEqual(g.max_drawdown({"RISK_MAX_DRAWDOWN": "0.2"}), 0.2)
        for bad in ("0", "1", "-0.1", "x", "nan", "30"):
            self.assertEqual(g.max_drawdown({"RISK_MAX_DRAWDOWN": bad}), 0.30, bad)
        self.add(row(T0, 1.0))
        self.init()
        self.env["RISK_MAX_DRAWDOWN"] = "0.2"
        self.add(row(T0 + 600, 0.8))
        self.assertTrue(self.run_guard(T0 + 600)["paused"])

    # -------------------------------------------------- blind

    def test_blind_two_hours_alerts_twelve_hours_pauses(self):
        self.add(row(T0, 1.0))
        self.init()
        self.add(row(T0 + 60, 9.0, lp=None))                 # unacceptable rows only from here
        self.assertFalse(self.run_guard(T0 + 2 * 3600 - 1)["paused"])
        self.assertEqual(self.alerts(), [])
        s = self.run_guard(T0 + 2 * 3600)
        self.assertFalse(s["paused"])
        self.assertEqual(len(self.alerts()), 1)
        self.assertIn("blind", self.alerts()[0])
        self.run_guard(T0 + 3 * 3600)
        self.assertEqual(len(self.alerts()), 1)               # one alert per blind episode
        s = self.run_guard(T0 + 12 * 3600)
        self.assertTrue(s["paused"])
        self.assertIn("blind 12.0h", self.pause()["reason"])

    def test_blind_with_no_rows_at_all_counts_from_first_look(self):
        self.add(row(T0, 1.0))
        self.init()
        self.nav.write_text("")
        self.assertFalse(self.run_guard(T0 + 100)["paused"])
        self.assertFalse(self.run_guard(T0 + 100 + 12 * 3600 - 1)["paused"])
        self.assertTrue(self.run_guard(T0 + 100 + 12 * 3600)["paused"])

    def test_basis_change_pauses(self):
        self.add(row(T0, 1.0))
        self.init()
        self.add(row(T0 + 600, 1.0, since=5_000))
        s = self.run_guard(T0 + 600)
        self.assertTrue(s["paused"])
        self.assertIn("basis changed", self.pause()["reason"])

    # -------------------------------------------------- resume, files

    def test_resume_resets_mark_and_journals(self):
        self.add(row(T0, 1.0))
        self.init()
        self.add(row(T0 + 600, 0.6))
        self.assertTrue(self.run_guard(T0 + 600)["paused"])
        event = g.set_mark([str(self.profile)], "current", now=T0 + 700, env=self.env, resume_note="reviewed")
        self.assertEqual((event["event"], event["note"]), ("resume", "reviewed"))
        self.assertEqual(self.pause()["paused"], False)
        state, _ = g._read_json(self.sd / "risk_hwm.json")
        self.assertAlmostEqual(state["hwm_adj"], 0.6)
        s = self.run_guard(T0 + 800)
        self.assertFalse(s["paused"])
        self.assertAlmostEqual(s["dd"], 0.0)
        journal = [json.loads(l) for l in (self.sd / "risk_guard.jsonl").read_text().splitlines()]
        self.assertEqual([e["event"] for e in journal], ["init_hwm", "pause", "resume"])

    def test_resume_cli_needs_a_note_and_rows(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            g.main(["--profile", str(self.profile), "--resume"])
        with self.assertRaises(SystemExit):  # no acceptable row: nothing to reset to
            g.set_mark([str(self.profile)], "current", now=T0, env=self.env, resume_note="x")

    def test_init_with_explicit_equity(self):
        self.add(row(T0, 0.9, flow_sol=0.5))
        self.init("1.0")
        s = self.run_guard(T0 + 1)
        self.assertAlmostEqual(s["peak"], 1.0)
        self.assertAlmostEqual(s["dd"], 0.1)
        for bad in ("0", "-1", "x", "nan"):
            with self.assertRaises(SystemExit):
                self.init(bad)

    def test_corrupt_files_fail_closed(self):
        self.add(row(T0, 1.0))
        self.init()
        (self.sd / "risk_hwm.json").write_text("{broken")
        s = self.run_guard(T0 + 1)
        self.assertTrue(s["paused"])
        self.assertIn("risk_hwm.json corrupt", self.pause()["reason"])
        self.assertEqual((self.sd / "risk_hwm.json").read_text(), "{broken")  # left for a human
        self.init()
        (self.sd / "risk_pause.json").write_text("[]")
        s = self.run_guard(T0 + 2, write=False)
        self.assertTrue(s["paused"])
        self.assertIn("corrupt", s["pause_reason"])

    def test_status_changes_nothing(self):
        self.add(row(T0, 1.0))
        self.init()
        self.add(row(T0 + 600, 0.5))
        before = sorted(p.name for p in self.sd.iterdir())
        s = self.run_guard(T0 + 600, write=False)
        self.assertFalse(s["paused"])
        self.assertIn("would pause", s["pause_reason"])
        self.assertEqual(sorted(p.name for p in self.sd.iterdir()), before)
        self.assertIn("would pause", g.format_status(s))

    def test_two_profiles_sum_and_any_missing_is_blind(self):
        other = Path(self.tmp.name) / "lpm"
        (other / "memories").mkdir(parents=True)
        self.add(row(T0, 1.0))
        (other / "memories" / "dlmm_nav.jsonl").write_text(json.dumps(row(T0, 0.5, wallet="w2")) + "\n")
        profiles = [str(self.profile), str(other)]
        g.set_mark(profiles, "current", now=T0, env=self.env)
        with open(other / "memories" / "dlmm_nav.jsonl", "a") as f:
            f.write(json.dumps(row(T0 + 600, 1.0, flow_sol=0.5, wallet="w2")) + "\n")  # funded
        s = g.evaluate(profiles, now=T0 + 600, env=self.env)
        self.assertAlmostEqual(s["equity"], 2.0)
        self.assertAlmostEqual(s["dd"], 0.0)
        (other / "memories" / "dlmm_nav.jsonl").write_text("")
        s = g.evaluate(profiles, now=T0 + 700, env=self.env)
        self.assertEqual(s["missing_profiles"], [str(other)])
        self.assertIsNone(s["dd"])


class PipelineEarlyCheck(unittest.TestCase):
    def test_same_rule_as_the_executor(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "risk_pause.json"
            self.assertIsNone(pipeline.risk_pause_refusal(str(p)))
            p.write_text(json.dumps({"paused": True, "dd": 0.31, "reason": "drawdown 31.0% >= 30%"}))
            self.assertEqual(pipeline.risk_pause_refusal(str(p)),
                             "ENTRY REFUSED: risk pause (dd=31.0%; drawdown 31.0% >= 30%)")
            p.write_text(json.dumps({"paused": False}))
            self.assertIsNone(pipeline.risk_pause_refusal(str(p)))
            for bad in ("{x", "[]", json.dumps({"paused": 1})):
                p.write_text(bad)
                self.assertIn("corrupt", pipeline.risk_pause_refusal(str(p)))
            p.unlink()
            p.mkdir()
            self.assertIn("unreadable", pipeline.risk_pause_refusal(str(p)))


class Cli(unittest.TestCase):
    def test_status_cli_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            prof = Path(d) / "p"
            (prof / "memories").mkdir(parents=True)
            (prof / "memories" / "dlmm_nav.jsonl").write_text(json.dumps(row(T0, 1.0)) + "\n")
            old = dict(os.environ)
            os.environ["AZIMUTH_RISK_STATE_DIR"] = str(Path(d) / "s")
            os.environ.pop("AZIMUTH_RISK_PAUSE_FILE", None)
            try:
                with redirect_stdout(io.StringIO()) as out:
                    g.main(["--profile", str(prof), "--status"])
            finally:
                os.environ.clear()
                os.environ.update(old)
            self.assertIn("risk guard:", out.getvalue())
            self.assertFalse((Path(d) / "s").exists())


if __name__ == "__main__":
    unittest.main()
