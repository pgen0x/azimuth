"""S2 evaluator: trade rule, sanity guards, baseline construction, cache, verdicts."""
import io
import json
import tempfile
import unittest
from pathlib import Path

import grad_paper as gp
import s2_eval as s2

T0 = 1_795_000_200  # mid-day, 5m aligned
MINT = "MINTpump"


def c(minute, o, h=None, low=None, close=None):
    h = o if h is None else h
    low = o if low is None else low
    return (T0 + 60 * minute, o, h, low, o if close is None else close)


def flat_path(px=1.0, minutes=24 * 60 + 30, start=0):
    return [c(m, px) for m in range(start, minutes, 5)]


def entry(ts=T0, pool="P1", mint=MINT, arm="s2"):
    return {"arm": arm, "pool": pool, "mint": mint, "ts": ts}


Q = ({s2.WSOL}, {MINT})


class TradeRuleTests(unittest.TestCase):
    def ev(self, path, now=T0 + 2 * s2.DAY, e=None):
        return s2.evaluate_entry(e or entry(), path, *Q, now)

    def test_entry_is_first_candle_at_or_after_row_time(self):
        path = [c(-5, 9.0)] + flat_path(1.0)
        r = self.ev(path, e=entry(ts=T0 - 60))
        self.assertEqual((r["entry_ts"], r["entry_px"]), (T0, 1.0))

    def test_stop_at_minus_25_and_cost_2pct(self):
        path = flat_path(1.0, 30) + [c(30, 0.9, low=0.5)]
        r = self.ev(path)
        self.assertEqual((r["status"], r["reason"]), ("closed", "stop"))
        self.assertAlmostEqual(r["net_ret"], -0.25 - 0.02)

    def test_trail_25_from_peak(self):
        path = flat_path(1.0, 30) + [c(30, 1.5, h=2.0, close=1.9), c(35, 1.9, low=1.0)]
        r = self.ev(path)
        self.assertEqual(r["reason"], "trail")
        self.assertAlmostEqual(r["exit_px"], 1.5)
        self.assertAlmostEqual(r["net_ret"], 0.5 - 0.02)

    def test_time_stop_after_24h_and_open_before(self):
        path = flat_path(1.0, 24 * 60 + 30)
        self.assertEqual(self.ev(path, now=T0 + 3600)["status"], "open")
        r = self.ev(path)
        self.assertEqual(r["reason"], "time")
        self.assertAlmostEqual(r["net_ret"], -0.02)


class GuardTests(unittest.TestCase):
    def test_non_sol_quote_is_rejected(self):
        r = s2.evaluate_entry(entry(), flat_path(), {"USDCmint"}, {MINT}, T0 + 2 * s2.DAY)
        self.assertEqual(r.get("guard"), "not_sol_quoted")
        r = s2.evaluate_entry(entry(), flat_path(), {s2.WSOL}, {"OTHER"}, T0 + 2 * s2.DAY)
        self.assertEqual(r.get("guard"), "not_sol_quoted")

    def test_dust_entry_print_is_rejected(self):
        path = [c(0, 1e-9)] + flat_path(1.0, start=5)
        r = s2.evaluate_entry(entry(), path, *Q, T0 + 2 * s2.DAY)
        self.assertEqual(r.get("guard"), "dust_entry")
        r = s2.evaluate_entry(entry(), flat_path(1e-13), *Q, T0 + 2 * s2.DAY)
        self.assertEqual(r.get("guard"), "dust_entry")

    def test_upward_impossible_jump_is_rejected(self):
        path = flat_path(1.0, 30) + [c(30, 1.0, h=50.0, close=1.0)] + flat_path(1.0, start=35)
        r = s2.evaluate_entry(entry(), path, *Q, T0 + 2 * s2.DAY)
        self.assertEqual(r.get("guard"), "impossible_jump")

    def test_a_real_rug_is_kept_as_a_loss(self):
        path = flat_path(1.0, 30) + [c(30, 0.01, h=0.01, low=0.005)]
        r = s2.evaluate_entry(entry(), path, *Q, T0 + 2 * s2.DAY)
        self.assertNotIn("guard", r)
        self.assertAlmostEqual(r["exit_px"], 0.01)  # gap through the stop fills at the open
        self.assertLess(r["net_ret"], -0.9)

    def test_a_jump_after_exit_does_not_reject(self):
        path = flat_path(1.0, 30) + [c(30, 0.9, low=0.5)] + [c(40, 1.0, h=99.0)]
        r = s2.evaluate_entry(entry(), path, *Q, T0 + 2 * s2.DAY)
        self.assertNotIn("guard", r)


class BaselineTests(unittest.TestCase):
    def test_baseline_excludes_inflow_pools_and_dedups_reoffers(self):
        with tempfile.TemporaryDirectory() as d:
            mem, state = Path(d) / "memories", Path(d) / "state"
            gp.append(mem / "dlmm_smart_inflow_shadow.jsonl", {"ts": T0, "pool": "P1", "mint": "M1"})
            gp.append(mem / "dlmm_smart_inflow_shadow.jsonl", {"ts": T0 + 20000, "pool": "P9", "mint": "M9"})
            w = state / "solana_candidate_watch.jsonl"

            def watch(ts, pool, mode="pulse", source="scanner_before_routing"):
                gp.append(w, {"ts": ts, "pool": pool, "mode": mode, "source": source,
                              "candidate": {"base_mint": "B" + pool}})
            watch(T0, "P1")                 # the inflow re-offer itself
            watch(T0 + 1000, "P2")
            watch(T0 + 2000, "P2")          # same 2h re-offer window
            watch(T0 + 9000, "P2")
            watch(T0 + 1000, "P3", mode="turnover")
            watch(T0 + 1000, "P4", source="smart_inflow_shadow")
            watch(T0 - 10, "P5")            # before the first S2 row
            watch(T0 + 10000, "P1")         # same pool, later and outside +-1h
            rows, base = s2.load_entries(d, state)
            self.assertEqual(len(rows), 2)
            self.assertEqual([(b["pool"], b["ts"]) for b in base],
                             [("P2", T0 + 1000), ("P2", T0 + 9000), ("P1", T0 + 10000)])


class FakeGT:
    def __init__(self, quote=s2.WSOL):
        self.urls, self.quote = [], quote

    def __call__(self, req, timeout):
        self.urls.append(req.full_url)
        before = int(req.full_url.split("before_timestamp=")[1])
        day = before + 1 - s2.DAY
        rows = [[t, 1.0, 1.0, 1.0, 1.0, 5.0] for t in range(day, day + s2.DAY, 300)]
        body = {"data": {"attributes": {"ohlcv_list": rows[::-1]}},
                "meta": {"base": {"address": MINT}, "quote": {"address": self.quote}}}
        return io.BytesIO(json.dumps(body).encode())


class CacheTests(unittest.TestCase):
    def test_each_finished_pool_day_is_fetched_once(self):
        with tempfile.TemporaryDirectory() as d:
            api = FakeGT()
            now = T0 + 3 * s2.DAY
            gate = gp.Gate(600, clock=lambda: now, sleep=lambda s: None)
            cache = s2.Cache(d, gate=gate, opener=api, clock=lambda: now)
            candles, quotes, bases, missing = cache.path_for(entry())
            self.assertFalse(missing)
            self.assertEqual(len(api.urls), 2)          # row day and the next
            self.assertTrue(all("aggregate=5" in u and f"token={MINT}" in u for u in api.urls))
            cache.path_for(entry(ts=T0 + 600))
            self.assertEqual(len(api.urls), 2)          # cache hit
            self.assertEqual(quotes, {s2.WSOL})
            off = s2.Cache(d, offline=True, clock=lambda: now)
            self.assertEqual(len(off.path_for(entry())[0]), len(candles))

    def test_today_is_refetched_and_failed_day_is_missing(self):
        with tempfile.TemporaryDirectory() as d:
            api = FakeGT()
            now = T0 + 600
            gate = gp.Gate(600, clock=lambda: now, sleep=lambda s: None)
            cache = s2.Cache(d, gate=gate, opener=api, clock=lambda: now)
            cache.path_for(entry())
            cache.path_for(entry())
            self.assertEqual(len(api.urls), 2)          # incomplete day fetched again; tomorrow never
            fail = s2.Cache(d + "/x", gate=gate, opener=lambda r, timeout: (_ for _ in ()).throw(OSError()),
                            clock=lambda: now)
            self.assertTrue(fail.path_for(entry())[3])


class StatsTests(unittest.TestCase):
    def trades(self, n, ret, pools=10, start=T0):
        return [{"pool": f"p{i % pools}", "entry_ts": start + i * 600, "net_ret": ret(i)} for i in range(n)]

    def test_winsorized_mean_clips_the_tails(self):
        xs = [0.0] * 98 + [1000.0, -1.0]
        self.assertLess(s2.winsorized_mean(xs), 1.0)

    def test_verdicts(self):
        good = s2.summarize(self.trades(200, lambda i: 0.05 + (i % 3) * 0.01))
        p_good = {"n": 200, "mean": 0.05, "lo": 0.01, "hi": 0.1}
        self.assertTrue(s2.verdict(good, p_good, 5).startswith("PROMOTE"))
        self.assertTrue(s2.verdict(good, {"n": 200, "lo": -0.01}, 5).startswith("CONTINUE"))
        bad = s2.summarize(self.trades(100, lambda i: -0.1 + (i % 3) * 0.01))
        self.assertTrue(s2.verdict(bad, {"n": 0}, 5).startswith("KILL (mean"))
        small = s2.summarize(self.trades(20, lambda i: 0.0))
        self.assertTrue(s2.verdict(small, {"n": 0}, 21).startswith("KILL (21"))
        self.assertTrue(s2.verdict(small, {"n": 0}, 3).startswith("CONTINUE"))

    def test_paired_uses_other_pools_within_3h(self):
        a = [{"pool": "a", "entry_ts": T0, "net_ret": 0.1}, {"pool": "b", "entry_ts": T0, "net_ret": 0.3}]
        base = [{"pool": "a", "entry_ts": T0, "net_ret": -5.0},   # same pool: ignored
                {"pool": "x", "entry_ts": T0 + 3600, "net_ret": 0.0},
                {"pool": "y", "entry_ts": T0 + 4 * 3600, "net_ret": 9.0}]  # outside the window
        p = s2.paired(a, base)
        self.assertEqual(p["n"], 2)
        # a: peers {x} -> 0.1 - 0.0; b: peers {a, x} -> 0.3 - (-2.5)
        self.assertAlmostEqual(p["mean"], (0.1 + 2.8) / 2)


if __name__ == "__main__":
    unittest.main()
