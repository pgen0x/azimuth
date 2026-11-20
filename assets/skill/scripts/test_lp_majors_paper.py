"""LP majors paper-trader: position model, session tags, collector flow, verdicts."""
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import lp_majors_paper as lp

HOUR = 1_795_140_000  # 2026-11-20T02:00Z, a Friday, 21:00 ET Thursday


def utc(*args):
    return int(datetime(*args, tzinfo=timezone.utc).timestamp())


def candle(ts, o, h=None, low=None, c=None):
    h = o if h is None else h
    low = o if low is None else low
    return {"ts": ts, "open": o, "high": h, "low": low, "close": o if c is None else c}


class PositionTests(unittest.TestCase):
    def test_bins_follow_the_pool_step_and_width(self):
        self.assertEqual(lp.Position(100.0, 0.05, 80, 1.0).k, 6)   # ln1.05/ln1.008 = 6.1
        self.assertEqual(lp.Position(100.0, 0.10, 10, 1.0).k, 95)
        pos = lp.Position(100.0, 0.05, 100, 1.0)
        self.assertAlmostEqual(pos.lo, 100.0 / 1.01 ** 4)
        self.assertAlmostEqual(pos.hi, 100.0 * 1.01 ** 4)

    def test_markout_is_zero_at_open_and_negative_either_way(self):
        pos = lp.Position(100.0, 0.05, 100, 9.0)
        self.assertAlmostEqual(pos.value(100.0), 9.0)
        self.assertAlmostEqual(pos.markout(100.0), 0.0)
        for p in (90.0, 97.0, 103.0, 120.0):
            self.assertLess(pos.markout(p), 0.0, p)

    def test_above_range_the_position_is_all_quote(self):
        pos = lp.Position(100.0, 0.05, 100, 9.0)
        far = pos.value(200.0)
        self.assertAlmostEqual(far, pos.value(150.0))  # nothing left to sell
        self.assertGreater(far, 9.0)                   # sold base above the open price
        self.assertLess(far, pos.hold(200.0))

    def test_below_range_the_position_is_all_base(self):
        pos = lp.Position(100.0, 0.05, 100, 9.0)
        x_total = sum(y / px for px, x, y in pos.bins if not x) + sum(x for px, x, y in pos.bins if x)
        self.assertAlmostEqual(pos.value(50.0), x_total * 50.0)

    def test_state_round_trip(self):
        pos = lp.Position(3.5, 0.10, 20, 4.0)
        again = lp.Position.from_state(json.loads(json.dumps(pos.to_state())))
        self.assertEqual((again.k, again.lo, again.hi), (pos.k, pos.lo, pos.hi))


class InRangeTests(unittest.TestCase):
    def test_overlap_share_of_each_candle(self):
        cs = [candle(0, 100, h=104, low=100), candle(300, 100, h=110, low=100), candle(600, 120, h=120, low=120)]
        self.assertAlmostEqual(lp.in_range_fraction(cs, 95, 105), (1.0 + 0.5 + 0.0) / 3)
        self.assertIsNone(lp.in_range_fraction([], 1, 2))


class StepHourTests(unittest.TestCase):
    def step(self, path, fees=100.0, tvl=10_000.0, base_fee=0.1):
        pos = lp.Position(100.0, 0.05, 100, 50.0)  # Y=USDC, SOL at 100 -> 0.5 SOL
        return pos, lp.step_hour(pos, 100.0, path, fees, tvl, y_usd=1.0, sol_usd=100.0,
                                 base_fee_pct=base_fee, notional_sol=0.5, tx_cost_sol=0.001)

    def test_in_range_hour_earns_fee_share_and_no_cost(self):
        _, (row, nxt) = self.step([candle(HOUR, 100.0, h=103, low=99, c=102.5)])
        self.assertAlmostEqual(row["fee_sol"], 100.0 * 1.0 * (50.0 / 10_000.0) / 100.0)
        self.assertEqual((row["cost_sol"], row["recentered"]), (0.0, False))
        self.assertLess(row["markout_sol"], 0.0)
        self.assertAlmostEqual(row["net_sol"], row["fee_sol"] + row["markout_sol"])

    def test_out_of_range_recenters_and_charges_two_txs_plus_half_swap(self):
        pos, (row, nxt) = self.step([candle(HOUR, 100.0, h=110, low=100, c=110.0)])
        self.assertTrue(row["recentered"])
        self.assertAlmostEqual(row["cost_sol"], 2 * 0.001 + 0.5 * 0.5 * (0.001 + lp.SWAP_SLIP))
        self.assertLess(row["markout_sol"], 0.0)
        self.assertAlmostEqual(nxt.p0, 110.0)
        self.assertAlmostEqual(nxt.value_y, 50.0)
        self.assertLess(row["in_range_frac"], 1.0)

    def test_wide_positions_pay_one_tx_per_70_bins(self):
        self.assertEqual(lp.tx_chunks(13), 1)
        self.assertEqual(lp.tx_chunks(71), 2)
        self.assertEqual(lp.tx_chunks(975), 14)

    def test_quiet_hour_holds_price_and_stays_in_range(self):
        _, (row, nxt) = self.step([], fees=0.0)
        self.assertEqual((row["price_end"], row["in_range_frac"], row["net_sol"]), (100.0, 1.0, 0.0))

    def test_usd_route_per_quote(self):
        sol_x = {"x_mint": lp.WSOL, "y_mint": "HYPE"}
        self.assertAlmostEqual(lp.y_usd_for(sol_x, 2.0, 100.0), 50.0)
        self.assertEqual(lp.y_usd_for({"x_mint": "A", "y_mint": lp.USDC}, 2.0, 100.0), 1.0)
        self.assertEqual(lp.y_usd_for({"x_mint": "A", "y_mint": lp.WSOL}, 2.0, 100.0), 100.0)


class SessionTests(unittest.TestCase):
    def test_regular_hours_and_dst(self):
        self.assertEqual(lp.session_tag(utc(2026, 11, 19, 15)), "open")    # 10:00-11:00 EST
        self.assertEqual(lp.session_tag(utc(2026, 11, 19, 14)), "open")    # 09:00-10:00, mid 09:30
        self.assertEqual(lp.session_tag(utc(2026, 11, 19, 13)), "closed")  # 08:00-09:00
        self.assertEqual(lp.session_tag(utc(2026, 11, 19, 21)), "closed")  # 16:00-17:00
        self.assertEqual(lp.session_tag(utc(2026, 7, 15, 19)), "open")     # 15:00-16:00 EDT
        self.assertEqual(lp.session_tag(utc(2026, 7, 15, 20)), "closed")

    def test_weekend_holiday_and_early_close(self):
        self.assertEqual(lp.session_tag(utc(2026, 11, 21, 16)), "weekend")
        self.assertEqual(lp.session_tag(utc(2026, 11, 26, 16)), "closed")  # Thanksgiving
        self.assertEqual(lp.session_tag(utc(2026, 11, 27, 17)), "open")    # 12:00-13:00
        self.assertEqual(lp.session_tag(utc(2026, 11, 27, 18)), "closed")  # early close 13:00
        self.assertIn(datetime(2026, 4, 3).date(), lp.nyse_holidays(2026))  # Good Friday
        self.assertIn(datetime(2026, 7, 3).date(), lp.nyse_holidays(2026))  # Jul 4 is a Saturday
        self.assertNotIn(datetime(2027, 12, 31).date(), lp.nyse_holidays(2027))  # Sat New Year

    def test_gap_hour_is_closures_plus_the_first_open_hour(self):
        self.assertTrue(lp.is_gap_hour(utc(2026, 11, 23, 14)))   # Monday open after a weekend
        self.assertFalse(lp.is_gap_hour(utc(2026, 11, 23, 15)))
        self.assertTrue(lp.is_gap_hour(utc(2026, 11, 23, 22)))


class FakeClock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


POOLS = [
    {"label": "SOL-USDC/4", "arm": "A", "address": "ANCHOR", "x_mint": lp.WSOL, "y_mint": lp.USDC,
     "sol_usd_anchor": True},
    {"label": "STK-USDC/10", "arm": "B", "address": "STOCK", "x_mint": "STKmint", "y_mint": lp.USDC},
]


class FakeAPI:
    def __init__(self, x_mint_override=None):
        self.urls = []
        self.x_override = x_mint_override

    def __call__(self, req, timeout):
        url = req.full_url
        self.urls.append(url)
        addr = url.split("/pools/")[1].split("/")[0].split("?")[0]
        pool = next(p for p in POOLS if p["address"] == addr)
        price = 100.0 if addr == "ANCHOR" else 20.0
        if "/ohlcv" in url:
            body = {"data": [{"timestamp": HOUR + 300 * i, "open": price, "high": price * 1.002,
                              "low": price * 0.998, "close": price} for i in range(12)]}
        elif "/volume/history" in url:
            body = {"data": [{"timestamp": HOUR, "fees": 110.0, "protocol_fees": 10.0},
                             {"timestamp": HOUR + 3600, "fees": 1.0, "protocol_fees": 0.0}]}
        else:
            x = self.x_override if (self.x_override and addr == "STOCK") else pool["x_mint"]
            body = {"token_x": {"address": x, "price": price}, "token_y": {"address": pool["y_mint"], "price": 1.0},
                    "pool_config": {"bin_step": 4 if addr == "ANCHOR" else 10, "base_fee_pct": 0.04},
                    "current_price": price, "tvl": 1_000_000.0, "dynamic_fee_pct": 0.0,
                    "fees": {"1h": 100.0}, "volume": {"1h": 1.0}}
        return io.BytesIO(json.dumps(body).encode())


class CollectorTests(unittest.TestCase):
    def make(self, api):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        clk = FakeClock(HOUR + 3600 + lp.EVAL_GRACE_S + 30)
        return lp.Collector(self.tmp.name, pools=POOLS, clock=clk, sleep=clk.sleep, opener=api, rpm=600)

    def test_one_cycle_samples_and_evaluates_every_width(self):
        api = FakeAPI()
        col = self.make(api)
        col.step()
        rows = list(lp.read_rows(col.hours_path))
        self.assertEqual(len(rows), len(POOLS) * len(lp.WIDTHS))
        self.assertTrue(all(r["hour"] == HOUR and r["fees_row"] for r in rows))
        self.assertEqual(col.state["sol_usd"][str(HOUR)], 100.0)
        stock = [r for r in rows if r["arm"] == "B"]
        self.assertEqual({r["session"] for r in stock}, {"closed"})
        self.assertTrue(all("geckoterminal" not in u for u in api.urls))
        self.assertTrue(all(f"end_time={HOUR + 3600}" in u for u in api.urls if "start_time" in u))
        anchor = next(r for r in rows if r["pool"] == "ANCHOR" and r["width"] == 0.05)
        share = (0.5 * 100.0) / 1_000_000.0
        self.assertAlmostEqual(anchor["fee_sol"], 100.0 * share / 100.0)
        self.assertTrue(anchor["opened"])
        self.assertGreater(anchor["cost_sol"], 0.0)

    def test_restart_resumes_without_reopening(self):
        api = FakeAPI()
        col = self.make(api)
        col.step()
        col.save_state()
        again = lp.Collector(self.tmp.name, pools=POOLS, clock=col.clock, sleep=col.sleep, opener=api, rpm=600)
        again.restore()
        self.assertEqual(again.state["next_hour"]["ANCHOR"], HOUR + 3600)
        self.assertTrue(again.snaps["ANCHOR"])
        again.clock.t += 3600
        again.step()
        later = [r for r in lp.read_rows(again.hours_path) if r["hour"] == HOUR + 3600]
        self.assertEqual(len(later), len(POOLS) * len(lp.WIDTHS))
        self.assertFalse(any(r["opened"] for r in later))

    def test_mint_mismatch_disables_the_pool(self):
        col = self.make(FakeAPI(x_mint_override="IMPOSTOR"))
        col.step()
        self.assertEqual(col.disabled, {"STOCK": "identity_mismatch"})
        self.assertTrue(all(r["pool"] == "ANCHOR" for r in lp.read_rows(col.hours_path)))

    def test_day_roll_writes_summary_and_rotates(self):
        col = self.make(FakeAPI())
        col.step()
        col.clock.t += 86400
        col.roll_day()
        summary = list(lp.read_rows(col.summary_path))
        self.assertEqual(len(summary), 1)
        self.assertGreater(summary[0]["requests"], 0)
        self.assertEqual(col.gate.requests, 0)

    def test_rotation_keeps_rows_readable(self):
        col = self.make(FakeAPI())
        col.step()
        lp.rotate(col.hours_path, max_bytes=10, keep=2, now=col.clock())
        self.assertFalse(col.hours_path.exists())
        self.assertEqual(len(list(lp.read_rows(col.hours_path, with_archives=True))), 4)


def hour_rows(n, net, arm="A", pools=("p1", "p2", "p3"), start=HOUR, gap_every=None):
    rows = []
    for i in range(n):
        h = start + i * 3600
        rows.append({"hour": h, "pool": pools[i % len(pools)], "label": pools[i % len(pools)], "arm": arm,
                     "width": 0.05, "notional_sol": 0.5, "net_sol": net(i), "fee_sol": 0.0,
                     "markout_sol": 0.0, "cost_sol": 0.0, "in_range_frac": 1.0, "recentered": False,
                     "session": "open", "gap_hour": bool(gap_every and i % gap_every == 0)})
    return rows


class VerdictTests(unittest.TestCase):
    def s(self, rows):
        return lp.summarize(rows, lambda r: r["pool"])

    def test_no_decision_before_14_days_and_300_hours(self):
        s = self.s(hour_rows(299, lambda i: 0.001 + (i % 3) * 1e-4))
        self.assertTrue(lp.verdict(s, "A", 0.0).startswith("CONTINUE"))

    def test_promote_kill_and_hold(self):
        good = self.s(hour_rows(400, lambda i: 0.001 + (i % 3) * 1e-4))
        self.assertGreater(good["days"], 14)
        self.assertTrue(lp.verdict(good, "A", 0.0).startswith("PROMOTE"))
        self.assertTrue(lp.verdict(good, "A", 1.0).startswith("HOLD"))
        self.assertTrue(lp.verdict(good, "A", None).startswith("HOLD"))
        bad = self.s(hour_rows(400, lambda i: -0.001 + (i % 3) * 1e-4))
        self.assertTrue(lp.verdict(bad, "A", 0.0).startswith("KILL (lower"))

    def test_arm_b_gap_kill(self):
        rows = hour_rows(400, lambda i: -0.01 if i % 4 == 0 else 0.002, arm="B", gap_every=4)
        s = self.s(rows)
        self.assertGreater(s["gap_loss_share"], 0.5)
        self.assertTrue(lp.verdict(s, "B", 0.0).startswith("KILL (closed-market"))
        self.assertFalse(lp.verdict(s, "A", -1.0).startswith("KILL (closed"))

    def test_report_reads_journal_and_pulse_baseline(self):
        with tempfile.TemporaryDirectory() as d:
            mem = Path(d) / "memories"
            for r in hour_rows(10, lambda i: 0.0001):
                r["rule_version"] = lp.RULE_VERSION
                lp.append(mem / "lp_majors_paper" / "hours.jsonl", r)
            lp.append(mem / "dlmm_closes.jsonl", {"position": "P1", "mode": "pulse"})
            lp.append(mem / "dlmm_closes.jsonl", {"position": "P2", "mode": "turnover"})
            lp.append(mem / "dlmm_realized.jsonl", {"position": "P1", "created_at": HOUR, "closed_at": HOUR + 43200,
                                                     "deposit_sol": 1.0, "realized_sol": 0.01})
            lp.append(mem / "dlmm_realized.jsonl", {"position": "P2", "created_at": HOUR, "closed_at": HOUR + 43200,
                                                     "deposit_sol": 1.0, "realized_sol": 5.0})
            pulse, n = lp.pulse_per_sol_day(mem, HOUR + 86400)
            self.assertEqual(n, 1)
            self.assertAlmostEqual(pulse, 0.02)
            out = []
            res = lp.report(d, out=out.append, now=HOUR + 86400)
            self.assertIn(("arm", "A", 0.05), res)
            self.assertTrue(any("pulse bar: +0.02000" in line for line in out))


if __name__ == "__main__":
    unittest.main()
