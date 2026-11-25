"""S2 evaluator: paper-trade smart-money inflow rows against a same-period baseline.

Read-only research. Inputs:
  * S2 rows: <profile>/memories/dlmm_smart_inflow_shadow.jsonl (one per inflow event)
  * baseline: pulse `scanner_before_routing` rows from the candidate watch journals
    (screen passes of the same period), minus any pool/time that carried an
    inflow row (+-1h), de-duplicated to one entry per pool per 2h re-offer
Path data: GeckoTerminal 5m OHLCV (price of the row's mint in its pool's quote,
`currency=token`), fetched one pool-UTC-day per request at <= 6 req/min and cached
under <profile>/memories/s2_ohlcv/<pool>/<YYYY-MM-DD>.json. A finished day is
fetched once; a day still in progress is re-fetched on the next run.

Paper rule (high-risk-strategy-20261119 §6 S2, pre-registered): enter at the
open of the first 5m candle starting at/after the row time; trail 25%, stop
-25%, 24h time stop, cost 2% round trip. The state machine is grad_paper.simulate
(stop set by the previous peak, gap fills at the open, high-then-low inside a candle).

Sanity guards (a trade failing one is excluded and counted, never scored):
  * not_sol_quoted - GT's quote token for the pool is not wrapped SOL, or the
    base is not the row's mint
  * dust_entry - entry price <= 1e-12 SOL, or more than 5x away from the median
    close of the first hour after entry (a stray print, not a price)
  * impossible_jump - any candle in the hold whose high is > 10x the larger of
    its open and the previous close. Only UPWARD jumps are rejected: a fake
    spike inflates the trail exit (S1's +2.6M% means), while a real rug is a
    loss the strategy must keep
Downward moves are never filtered. The report also shows a 5/95 winsorized mean.

Verdict (registry S2): PROMOTE at n >= 200 with mean > 0, lower 95% CI > 0 and
a paired difference vs baseline with lower CI > 0. KILL at n >= 100 if mean <
-3% and CI upper < 0, or at 21 days since the first row without a promote.
CI: bootstrap clustered by pool. Pairing: each S2 trade minus the mean of
baseline trades (other pools) entered within +-3h.
"""
import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grad_paper import Gate, cluster_bootstrap, http_json, num, read_rows, simulate  # noqa: E402

GT_BASE = "https://api.geckoterminal.com/api/v2"
USER_AGENT = "Mozilla/5.0 (compatible; research-client)"
WSOL = "So11111111111111111111111111111111111111112"
DAY = 86400
CANDLE_S = 300
GT_RPM = 6

TRAIL, STOP, HOLD_S, COST = 0.25, 0.25, 24 * 3600, 0.02
DUST_PX = 1e-12
DUST_RATIO = 5.0
JUMP_X = 10.0
BASELINE_DEDUP_S = 2 * 3600
INFLOW_EXCLUDE_S = 3600
PAIR_WINDOW_S = 3 * 3600

PROMOTE_N, KILL_N, KILL_MEAN, KILL_DAYS = 200, 100, -0.03, 21


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def day_key(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- entries

def load_entries(profile, state_dir):
    mem = Path(profile) / "memories"
    s2 = []
    for r in read_rows(mem / "dlmm_smart_inflow_shadow.jsonl"):
        if r.get("pool") and r.get("mint") and r.get("ts"):
            s2.append({"arm": "s2", "pool": r["pool"], "mint": r["mint"], "ts": int(r["ts"]),
                       "symbol": r.get("symbol")})
    s2.sort(key=lambda e: e["ts"])
    if not s2:
        return s2, []
    start, end = s2[0]["ts"], max(e["ts"] for e in s2)
    inflow = {}
    for e in s2:
        inflow.setdefault(e["pool"], []).append(e["ts"])
    raw = []
    for f in (Path(state_dir) / "solana_candidate_watch.jsonl", mem / "dlmm_candidate_watch.jsonl"):
        for r in read_rows(f):
            mint = (r.get("candidate") or {}).get("base_mint")
            if (r.get("source") == "scanner_before_routing" and r.get("mode") == "pulse" and mint
                    and r.get("pool") and start <= int(r.get("ts") or 0) <= end):
                raw.append({"arm": "baseline", "pool": r["pool"], "mint": mint, "ts": int(r["ts"])})
    raw.sort(key=lambda e: e["ts"])
    base, last = [], {}
    for e in raw:
        if any(abs(e["ts"] - t) <= INFLOW_EXCLUDE_S for t in inflow.get(e["pool"], ())):
            continue
        if e["ts"] - last.get(e["pool"], -10 ** 12) < BASELINE_DEDUP_S:
            continue
        last[e["pool"]] = e["ts"]
        base.append(e)
    return s2, base


# ---------------------------------------------------------------- OHLCV cache

class Cache:
    def __init__(self, profile, gate=None, opener=None, clock=time.time, offline=False):
        self.dir = Path(profile) / "memories" / "s2_ohlcv"
        self.gate = gate or Gate(GT_RPM)
        self.opener, self.clock, self.offline = opener, clock, offline
        self.fetched = self.failed = 0

    def day(self, pool, mint, day_start):
        path = self.dir / pool / f"{day_key(day_start)}.json"
        if path.exists():
            try:
                doc = json.loads(path.read_text())
                if doc.get("complete") and doc.get("mint") == mint:
                    return doc
                if self.offline:
                    return doc if doc.get("mint") == mint else None
            except ValueError:
                pass
        if self.offline or day_start > self.clock():
            return None
        url = (f"{GT_BASE}/networks/solana/pools/{pool}/ohlcv/minute?aggregate=5&limit=288"
               f"&currency=token&token={mint}&before_timestamp={day_start + DAY - 1}")
        kw = {"opener": self.opener} if self.opener else {}
        payload = http_json(url, self.gate, USER_AGENT, **kw)
        if payload is None:
            self.failed += 1
            return None
        self.fetched += 1
        rows = (((payload.get("data") or {}).get("attributes") or {}).get("ohlcv_list")) or []
        candles = []
        for r in rows:
            vals = [num(v) for v in r[:5]]
            if None not in vals and day_start <= vals[0] < day_start + DAY:
                candles.append([int(vals[0])] + vals[1:])
        meta = payload.get("meta") or {}
        doc = {"pool": pool, "mint": mint, "day": day_key(day_start),
               "base": (meta.get("base") or {}).get("address"),
               "quote": (meta.get("quote") or {}).get("address"),
               "candles": sorted(candles), "fetched_at": int(self.clock()),
               "complete": self.clock() >= day_start + DAY + 600}
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(doc, separators=(",", ":")))
        os.replace(tmp, path)
        return doc

    def path_for(self, entry):
        """Candles and quote identity covering [entry ts, ts + 24h + 1 candle]."""
        first = entry["ts"] // DAY * DAY
        last = (entry["ts"] + HOLD_S + CANDLE_S) // DAY * DAY
        candles, quotes, bases, missing = [], set(), set(), False
        for d in range(first, last + 1, DAY):
            doc = self.day(entry["pool"], entry["mint"], d)
            if doc is None:
                missing = missing or d <= self.clock()
                continue
            candles += [tuple(c) for c in doc["candles"]]
            quotes.add(doc.get("quote"))
            bases.add(doc.get("base"))
        return sorted(set(candles)), quotes, bases, missing


# ---------------------------------------------------------------- trade + guards

def evaluate_entry(entry, candles, quotes, bases, now):
    out = dict(entry)
    if quotes and (quotes != {WSOL} or bases != {entry["mint"]}):
        return dict(out, status="rejected", guard="not_sol_quoted")
    r = simulate(candles, entry["ts"], now, entry_delay=0, trail=TRAIL, stop=STOP, hold=HOLD_S, cost=COST)
    out.update(r)
    if r["status"] != "closed":
        return out
    if not quotes:
        return dict(out, status="rejected", guard="not_sol_quoted")
    px = r["entry_px"]
    first_hour = [c[4] for c in candles if r["entry_ts"] <= c[0] < r["entry_ts"] + 3600]
    med = statistics.median(first_hour) if first_hour else px
    if px <= DUST_PX or not (med / DUST_RATIO <= px <= med * DUST_RATIO):
        return dict(out, status="rejected", guard="dust_entry")
    prev = None
    for ts, o, h, low, c in candles:
        if ts < r["entry_ts"] or ts > r["exit_ts"]:
            prev = c
            continue
        ref = max(o, prev) if prev else o
        if ref > 0 and h > JUMP_X * ref:
            return dict(out, status="rejected", guard="impossible_jump")
        prev = c
    return out


# ---------------------------------------------------------------- stats

def winsorized_mean(xs, p=0.05):
    s = sorted(xs)
    lo, hi = s[int(p * (len(s) - 1))], s[int((1 - p) * (len(s) - 1))]
    return statistics.fmean(min(max(x, lo), hi) for x in s)


def summarize(trades):
    rets = [t["net_ret"] for t in trades]
    if not rets:
        return {"n": 0}
    lo, hi = cluster_bootstrap([{"mint": t["pool"], "pool": t["pool"], "net_ret": t["net_ret"]} for t in trades])
    return {"n": len(rets), "pools": len({t["pool"] for t in trades}), "mean": statistics.fmean(rets),
            "median": statistics.median(rets), "win": sum(x > 0 for x in rets) / len(rets),
            "wmean": winsorized_mean(rets), "lo": lo, "hi": hi}


def paired(s2, base):
    diffs = []
    for t in s2:
        peers = [b["net_ret"] for b in base
                 if b["pool"] != t["pool"] and abs(b["entry_ts"] - t["entry_ts"]) <= PAIR_WINDOW_S]
        if peers:
            diffs.append({"pool": t["pool"], "mint": t["pool"], "net_ret": t["net_ret"] - statistics.fmean(peers)})
    if not diffs:
        return {"n": 0}
    lo, hi = cluster_bootstrap(diffs)
    return {"n": len(diffs), "mean": statistics.fmean(d["net_ret"] for d in diffs), "lo": lo, "hi": hi}


def verdict(s, p, days):
    n = s.get("n", 0)
    if (n >= PROMOTE_N and s["mean"] > 0 and (s["lo"] or 0) > 0
            and p.get("n") and (p.get("lo") or 0) > 0):
        return "PROMOTE (S1 canary terms)"
    if n >= KILL_N and s["mean"] < KILL_MEAN and s["hi"] is not None and s["hi"] < 0:
        return "KILL (mean < -3% with CI upper < 0)"
    if days >= KILL_DAYS:
        return "KILL (21 days without a promote)"
    return f"CONTINUE (n {n}/{PROMOTE_N}, day {days:.1f}/{KILL_DAYS})"


# ---------------------------------------------------------------- driver

def run(profile, state_dir, now=None, cache=None, out=print):
    now = time.time() if now is None else now
    cache = cache or Cache(profile)
    s2, base = load_entries(profile, state_dir)
    results = {"s2": [], "baseline": []}
    for e in s2 + base:
        candles, quotes, bases, missing = cache.path_for(e)
        if missing:  # a past day failed to fetch: a partial path would fake a time exit
            results[e["arm"]].append(dict(e, status="unfetched"))
            continue
        results[e["arm"]].append(evaluate_entry(e, candles, quotes, bases, now))
    report(results, s2[0]["ts"] if s2 else now, now, out)
    return results


def fmt(v, pct=True):
    if v is None:
        return "n/a"
    return f"{v * 100:+.1f}%" if pct else f"{v:.2f}"


def report(results, first_ts, now, out=print):
    days = (now - first_ts) / DAY
    out(f"S2 evaluator: trail {TRAIL:.0%} / stop -{STOP:.0%} / {HOLD_S // 3600}h / cost {COST:.0%}; "
        f"day {days:.1f} since first row")
    stats = {}
    for arm in ("s2", "baseline"):
        rows = results[arm]
        closed = [t for t in rows if t.get("status") == "closed" and "guard" not in t]
        counts = {}
        for t in rows:
            k = t.get("guard") or t.get("status")
            counts[k] = counts.get(k, 0) + 1
        s = stats[arm] = summarize(closed)
        out(f"\n[{arm}] entries {len(rows)}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
        if s["n"]:
            out(f"  n {s['n']} (pools {s['pools']})  mean {fmt(s['mean'])}  median {fmt(s['median'])}  "
                f"win {s['win']:.0%}  wins.mean {fmt(s['wmean'])}  95% CI [{fmt(s['lo'])}, {fmt(s['hi'])}]")
            reasons = {}
            for t in closed:
                reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1
            out("  exits: " + ", ".join(f"{k} {v}" for k, v in sorted(reasons.items())))
    s2_closed = [t for t in results["s2"] if t.get("status") == "closed" and "guard" not in t]
    b_closed = [t for t in results["baseline"] if t.get("status") == "closed" and "guard" not in t]
    p = paired(s2_closed, b_closed)
    if p["n"]:
        out(f"\n[paired s2 - baseline, +-{PAIR_WINDOW_S // 3600}h] n {p['n']}  mean {fmt(p['mean'])}  "
            f"95% CI [{fmt(p['lo'])}, {fmt(p['hi'])}]")
    else:
        out("\n[paired] no overlapping baseline trades")
    v = verdict(stats["s2"], p, days)
    out(f"\nverdict: {v}")
    return {"stats": stats, "paired": p, "verdict": v}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--profile", required=True)
    ap.add_argument("--state-dir", default=str(Path.home() / ".local/state/azimuth"))
    ap.add_argument("--report", action="store_true", help="cache only: no GeckoTerminal requests")
    ap.add_argument("--gt-rpm", type=float, default=GT_RPM, help=f"max {GT_RPM}")
    ap.add_argument("--json", help="also write every evaluated entry to this file")
    ap.add_argument("--passes", type=int, default=3, help="fetch passes; later ones retry failed days")
    a = ap.parse_args(argv)
    cache = Cache(a.profile, gate=Gate(min(max(a.gt_rpm, 0.5), GT_RPM)), offline=a.report)
    # A 429 leaves a day unfetched; later passes retry only those (cached days are
    # free). The printed pass reads the cache only, so it costs no request.
    if not a.report:
        for _ in range(max(1, a.passes)):
            failed = cache.failed
            run(a.profile, a.state_dir, cache=cache, out=lambda *_: None)
            if cache.failed == failed:
                break
        cache.offline = True
    results = run(a.profile, a.state_dir, cache=cache)
    log(f"s2-eval: GT requests {cache.fetched}, failures {cache.failed}")
    if a.json:
        Path(a.json).write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
