"""Graduation paper-trader: paper rule, rate limiting, rotation, collector flow."""
import gzip
import io
import json
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import grad_paper as gp

T0 = 1_800_000_000
DAY = 86400


def c(minute, o, h=None, low=None, close=None):
    """A 1m candle `minute` minutes after T0."""
    h = o if h is None else h
    low = o if low is None else low
    return (T0 + 60 * minute, o, h, low, o if close is None else close)


class PaperRuleTests(unittest.TestCase):
    def test_entry_is_open_of_first_candle_at_or_after_t0_plus_3m(self):
        path = [c(1, 5.0), c(2, 9.0), c(4, 1.0), c(5, 1.0)]
        r = gp.simulate(path, T0, T0 + 600)
        self.assertEqual(r["status"], "open")
        self.assertEqual((r["entry_ts"], r["entry_px"]), (T0 + 240, 1.0))

    def test_trailing_stop_fills_at_25pct_below_peak(self):
        path = [c(3, 1.0), c(4, 1.5, h=2.0), c(5, 1.9, low=1.4)]
        r = gp.simulate(path, T0, T0 + 600)
        self.assertEqual((r["status"], r["reason"]), ("closed", "trail"))
        self.assertAlmostEqual(r["exit_px"], 1.5)
        self.assertAlmostEqual(r["net_ret"], 0.5 - 0.08)
        self.assertEqual(r["peak_px"], 2.0)

    def test_first_drawdown_exits_at_minus_25pct_not_minus_30(self):
        # The 25% trail from an entry-level peak (0.75) sits above the -30% floor.
        r = gp.simulate([c(3, 1.0), c(4, 0.9, low=0.6)], T0, T0 + 600)
        self.assertEqual(r["reason"], "stop")
        self.assertAlmostEqual(r["exit_px"], 0.75)
        self.assertAlmostEqual(r["net_ret"], -0.25 - 0.08)

    def test_gap_through_stop_fills_at_the_open(self):
        r = gp.simulate([c(3, 1.0), c(4, 0.5, h=0.55, low=0.4)], T0, T0 + 600)
        self.assertEqual(r["reason"], "stop")
        self.assertAlmostEqual(r["exit_px"], 0.5)

    def test_one_candle_spike_then_dump_assumes_high_then_low(self):
        r = gp.simulate([c(3, 1.0), c(4, 1.0, h=2.0, low=1.2)], T0, T0 + 600)
        self.assertEqual(r["reason"], "trail")
        self.assertAlmostEqual(r["exit_px"], 1.5)

    def test_time_stop_exits_at_last_close_before_entry_plus_24h(self):
        path = [c(3, 1.0)] + [c(m, 1.1, close=1.2) for m in range(10, 24 * 60 + 3, 60)] + [c(24 * 60 + 3, 9.0)]
        still_open = gp.simulate(path, T0, T0 + 180 + DAY - 1)
        self.assertEqual(still_open["status"], "open")
        r = gp.simulate(path, T0, T0 + 180 + DAY)
        self.assertEqual((r["status"], r["reason"]), ("closed", "time"))
        self.assertAlmostEqual(r["exit_px"], 1.2)  # the 9.0 candle is past the hold
        self.assertAlmostEqual(r["net_ret"], 0.2 - 0.08)

    def test_no_candle_in_entry_window(self):
        self.assertEqual(gp.simulate([c(1, 1.0)], T0, T0 + 600)["status"], "open")
        self.assertEqual(gp.simulate([c(1, 1.0)], T0, T0 + 180 + DAY)["status"], "no_entry")

    def test_trail_never_sits_below_the_hard_stop(self):
        # Peak 1.2 -> trail level 0.9 is above the 0.7 floor, so a dip to 0.85 trails.
        r = gp.simulate([c(3, 1.0), c(4, 1.1, h=1.2), c(5, 1.0, low=0.85)], T0, T0 + 600)
        self.assertEqual(r["reason"], "trail")
        self.assertAlmostEqual(r["exit_px"], 0.9)


class FakeClock:
    def __init__(self, t=T0):
        self.t = t
        self.slept = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


class GateTests(unittest.TestCase):
    def test_requests_are_spaced(self):
        clk = FakeClock()
        g = gp.Gate(6, clock=clk, sleep=clk.sleep)  # 10s apart
        g.acquire()
        g.acquire()
        g.acquire()
        self.assertEqual(clk.slept, [10.0, 10.0])
        self.assertEqual(g.requests, 3)

    def test_429_backs_off_exponentially_and_success_resets(self):
        clk = FakeClock()
        g = gp.Gate(60, cooldown_s=75, max_cooldown_s=200, clock=clk, sleep=clk.sleep)
        self.assertEqual(g.penalize(), 75)
        self.assertEqual(g.penalize(), 150)
        self.assertEqual(g.penalize(), 200)  # capped
        g.acquire()
        self.assertAlmostEqual(clk.slept[-1], 200)
        g.ok()
        self.assertEqual(g.penalize(), 75)

    def test_http_429_penalizes_and_returns_none(self):
        clk = FakeClock()
        g = gp.Gate(60, clock=clk, sleep=clk.sleep)

        def opener(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, io.BytesIO(b""))

        self.assertIsNone(gp.http_json("https://api.example/x", g, "ua", opener))
        self.assertEqual(g.rate_limited, 1)
        self.assertGreater(g.cool_until, clk.t)


class RotationTests(unittest.TestCase):
    def test_rotate_gzips_aside_keeps_newest_and_reads_back(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "trades.jsonl"
            for i in range(4):
                gp.append(path, {"i": i, "pad": "x" * 100})
                self.assertIsNotNone(gp.rotate(path, max_bytes=10, keep=2, now=T0 + i))
            gp.append(path, {"i": 4})
            self.assertIsNone(gp.rotate(path, max_bytes=10_000, keep=2, now=T0 + 9))
            archives = sorted(Path(d).glob("trades.*.jsonl.gz"))
            self.assertEqual(len(archives), 2)
            with gzip.open(archives[0], "rt") as f:
                self.assertEqual(json.loads(f.readline())["i"], 2)
            self.assertEqual([r["i"] for r in gp.read_rows(path, with_archives=True)], [2, 3, 4])
            self.assertEqual([r["i"] for r in gp.read_rows(path)], [4])


def gt_pool(addr, dex, mint, reserve, created=T0 - 60, quote=gp.WSOL):
    iso = datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"type": "pool", "attributes": {
        "address": addr, "name": "X / SOL", "pool_created_at": iso,
        "reserve_in_usd": str(reserve), "fdv_usd": "90000", "market_cap_usd": None,
        "transactions": {"m5": {"buys": 9, "sells": 1}}},
        "relationships": {"base_token": {"data": {"id": "solana_" + mint}},
                          "quote_token": {"data": {"id": "solana_" + quote}},
                          "dex": {"data": {"id": dex}}}}


class FakeAPI:
    """Routes the collector's GETs to canned JSON; records every URL."""

    def __init__(self, new_pools, jup, candles):
        self.new_pools, self.jup, self.candles = new_pools, jup, candles
        self.urls = []

    def __call__(self, req, timeout):
        url = req.full_url
        self.urls.append(url)
        if "/new_pools" in url:
            body = {"data": self.new_pools if "page=1" in url else [], "included": []}
        elif "datapi.jup.ag" in url:
            body = self.jup
        elif "/ohlcv/" in url:
            body = {"data": {"attributes": {"ohlcv_list": [list(x) + [1.0] for x in self.candles]}}}
        else:
            raise AssertionError(url)
        return io.BytesIO(json.dumps(body).encode())


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.clk = FakeClock()
        grad, dust, curve = "G" * 43, "D" * 43, "B" * 43
        self.grad = grad
        self.api = FakeAPI(
            new_pools=[gt_pool(grad, "pumpswap", "gradmintpump", 21000),
                       gt_pool(dust, "pumpswap", "dustmint", 0.01),
                       gt_pool(curve, "pump-fun", "curvemintpump", 4000)],
            jup=[{"id": "gradmintpump", "launchpad": "pump.fun", "graduatedPool": grad,
                  "audit": {"mintAuthorityDisabled": True, "freezeAuthorityDisabled": True,
                            "botHoldersPercentage": 1.0}}],
            candles=[c(3, 1.0), c(10, 0.9, low=0.6)])
        self.col = gp.Collector(self.tmp.name, clock=self.clk, sleep=self.clk.sleep, opener=self.api)

    def test_poll_keeps_only_graduations_and_journals_safety(self):
        self.col.step()
        self.assertEqual(list(self.col.tracked), [self.grad])
        rows = list(gp.read_rows(self.col.pools_path))
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["safety_pass"])
        self.assertTrue(rows[0]["jupiter"]["graduated_pool_match"])
        self.assertEqual(self.col.counters["excluded"], {"reserve": 1, "dex": 1})
        self.assertTrue(all("geckoterminal" in u or "datapi.jup.ag" in u for u in self.api.urls))

    def test_refresh_closes_both_arms_and_restore_skips_closed(self):
        self.col.step()
        self.clk.t = T0 - 60 + gp.FIRST_FETCH_S + 1
        self.col.next_poll = self.clk.t + 1_000  # no poll this step
        self.col.step()
        trades = list(gp.read_rows(self.col.trades_path))
        self.assertEqual(sorted(t["arm"] for t in trades), ["all", "safety"])
        self.assertTrue(all(t["reason"] == "stop" and abs(t["exit_px"] - 0.75) < 1e-9 for t in trades))
        again = gp.Collector(self.tmp.name, clock=self.clk, sleep=self.clk.sleep, opener=self.api)
        again.restore()
        self.assertEqual(again.tracked, {})

    def test_late_sighting_is_not_admitted_to_the_safety_arm(self):
        verdict = gp.safety({"audit": {}}, "P", sighted_at=T0 + 200, created_at=T0)
        self.assertFalse(verdict["pass"])
        self.assertIn("sighted_after_entry", verdict["failed"])
        self.assertEqual(len(verdict["unknown"]), 4)


class ReportTests(unittest.TestCase):
    def rows(self, n, ret, days=8):
        return [{"pool": f"p{i}", "mint": f"m{i}", "entry_ts": T0 + i * days * DAY / n, "net_ret": ret}
                for i in range(n)]

    def test_promote_needs_n_days_ci_and_second_half(self):
        self.assertEqual(gp.evaluate(self.rows(1000, 0.05))["verdict"], "PROMOTE")
        self.assertEqual(gp.evaluate(self.rows(999, 0.05))["verdict"], "CONTINUE")
        self.assertEqual(gp.evaluate(self.rows(1000, 0.05, days=6))["verdict"], "CONTINUE")

    def test_early_kill_and_budget_kill(self):
        self.assertTrue(gp.evaluate(self.rows(500, -0.05))["verdict"].startswith("KILL (mean"))
        self.assertTrue(gp.evaluate(self.rows(100, 0.0, days=15))["verdict"].startswith("KILL (14d"))

    def test_clusters_share_one_resample_unit(self):
        rows = [{"pool": "a", "mint": "same", "net_ret": 1.0}, {"pool": "b", "mint": "same", "net_ret": 1.0},
                {"pool": "c", "mint": "other", "net_ret": -1.0}]
        lo, hi = gp.cluster_bootstrap(rows, n_boot=500)
        self.assertGreaterEqual(lo, -1.0)
        self.assertLessEqual(hi, 1.0)
        self.assertEqual(gp.cluster_bootstrap(rows[:2]), (None, None))


if __name__ == "__main__":
    unittest.main()
