"""LP majors paper-trader: modelled two-sided DLMM spot positions in deep pools.

Research only. It reads Meteora's public datapi and writes
<profile>/memories/lp_majors_paper/{samples,hours,summary}.jsonl plus a state
file. No wallet, no key, no env file, no transaction, no GeckoTerminal. The only
RPC use is a keyless public-endpoint read of bin arrays (v2, below).

Arms (fixed pools, `lp_majors_pools.json`, mint identity checked every sample):
  A  majors: SOL-USDC (two bin steps), cbBTC-SOL, SOL/HYPE (two pools), JUP-SOL
  B  tokenized stocks: NVDAx-USDC, SPCX-SOL, SPCX-USDC, TTWO-USDC
     every hour is tagged open / closed / weekend against the US equity session

Sampling: one GET /pools/<address> per pool every 5 minutes (TVL, prices,
dynamic fee). Evaluation: once an hour has closed (plus a 10-minute grace) each
pool costs two more GETs: 5m OHLCV and the 1h fee history for that hour.
About 11 requests per minute at peak, all on Meteora's datapi, so the
shared GeckoTerminal budget and the candidate-watch sampler (30/run, 64 pools)
are never touched.

Position model (RULE_VERSION 1), per pool and per width (+-5% and +-10%):
  * a DLMM `spot` shape: 2k+1 bins of the pool's own bin step around the open
    price, k = floor(ln(1+w)/ln(1+step)); bins at and below the open price
    hold quote (Y), bins above hold base (X), equal value per bin
  * a bin converts at its own price once the market crosses it, so the
    position value depends only on the current price (fees are kept apart)
  * markout = LP value - value of holding the opening inventory; always <= 0
  * fees = pool LP fees for the hour (fees - protocol_fees, USD)
           x in-range share of the hour (5m candle high/low overlap)
           x our value / pool TVL (TVL from the nearest 5m sample)
    v2: our value / pool TVL is replaced, where possible, by a BIN-LEVEL share
    (`fee_basis: "bin"`): once per pool per clock hour the bin arrays within
    +-21% of price are read over keyless public Solana RPC (getMultipleAccounts,
    PDAs derived locally, no key), and for each 5m candle our liquidity in the
    bins it traded through is divided by all liquidity there (pool + ours),
    volume-weighted over the hour (dlmm_bin_liquidity.bin_fee_share). Narrow
    widths put more value per bin and so earn more per in-range hour. When the
    RPC read fails or is older than 2h the hour falls back to the v1 TVL share
    (`fee_basis: "tvl"`); both figures are journaled (fee_sol_bin, fee_sol_tvl).
  * notional 0.5 SOL at every open. An hour that ends out of range re-centers:
    2 x tx cost (close + open, one tx per 70-bin chunk) + swapping half the
    notional at the pool base fee + 5 bp slip. The first open pays the open
    txs + the same half swap. Position/bin-array rent is not charged.
  * net = fees + markout - costs, all in SOL at the hour's SOL/USD close
    (from the SOL-USDC/4 pool's own candles).

`--report` prints modelled net per SOL-day by arm/width and pool/width with a
clustered bootstrap CI (pools within an arm, UTC days within a pool), session
slices for arm B, and the pre-registered verdicts:
  * decisions only after >= 14 days and >= 300 position-hours per width
  * KILL if the lower 95% CI <= 0
  * arm B also KILLs if more than 50% of its modelled loss came from
    closed-market hours (closed, weekend, holiday, or the first open hour
    after a closure, which carries the reopen gap)
  * PROMOTE to a 0.1 SOL live canary (under the 30% drawdown pause) if the
    mean beats pulse's realized SOL per deployed SOL-day (last 30 days,
    from the profile's own realized + close journals) AND the lower CI > 0
"""
import argparse
import json
import math
import os
import statistics
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grad_paper import Gate, append, cluster_bootstrap, http_json, read_rows, rotate  # noqa: E402
from dlmm_bin_liquidity import PUBLIC_RPC, BinReader, bin_fee_share, bin_id_for  # noqa: E402

RULE_VERSION = 2          # v2 (2026-11-25): fee share from bin liquidity where RPC answers;
                          # positions, markout, costs and verdict rules are unchanged from v1
REPORT_VERSIONS = (1, 2)  # v1 rows are fee_basis "tvl" by construction
API = "https://dlmm.datapi.meteora.ag/pools"
USER_AGENT = "Mozilla/5.0 (compatible; research-client)"
WSOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
POOLS_FILE = Path(__file__).resolve().with_name("lp_majors_pools.json")

WIDTHS = (0.05, 0.10)
NOTIONAL_SOL = 0.5
TX_COST_SOL = 0.0002      # per DLMM tx incl. priority fee; a multi-bin add is CU-heavy
BINS_PER_TX = 70          # one add/remove tx covers at most this many bins
SWAP_SLIP = 0.0005        # on top of the pool base fee when re-balancing inventory
SAMPLE_EVERY_S = 300
EVAL_GRACE_S = 600        # let the datapi settle the last 5m candle and the hour's fee row
CHUNK_H = 12              # hours per OHLCV/fee-history request
MAX_BACKLOG_H = 72        # longer outages skip ahead; the skipped move lands as one gap hour
SNAPSHOT_KEEP_S = 96 * 3600
TVL_NEAR_S = 6 * 3600
RPM = 30
RPC_RPM = 20              # keyless public RPC: ~2 calls per pool per hour
BIN_SNAPSHOT_MAX_AGE_S = 2 * 3600
BIN_ATTEMPTS_PER_HOUR = 3
BIN_REPORT_MIN_HOURS = 24
ROTATE_BYTES = 16 * 1024 * 1024
ROTATE_KEEP = 12

DECIDE_MIN_DAYS = 14
DECIDE_MIN_N = 300
GAP_LOSS_SHARE_MAX = 0.5
PULSE_WINDOW_D = 30

ET = ZoneInfo("America/New_York")


def log(msg):
    print(msg, flush=True)


def hour_floor(ts):
    return int(ts) // 3600 * 3600


# ---------------------------------------------------------------- US equity session

def _nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last_weekday(year, month, weekday):
    d = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _easter(year):
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    return date(year, month, (h + l - 7 * m + 114) % 31 + 1)


def _observed(d):
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def nyse_holidays(year):
    """Full-day NYSE closures. A Saturday New Year's Day is not observed."""
    days = {
        _nth_weekday(year, 1, 0, 3), _nth_weekday(year, 2, 0, 3),
        _easter(year) - timedelta(days=2), _last_weekday(year, 5, 0),
        _observed(date(year, 6, 19)), _observed(date(year, 7, 4)),
        _nth_weekday(year, 9, 0, 1), _nth_weekday(year, 11, 3, 4),
        _observed(date(year, 12, 25)),
    }
    ny = date(year, 1, 1)
    if ny.weekday() != 5:
        days.add(_observed(ny))
    return days


def nyse_early_closes(year):
    """13:00 ET closes: Jul 3, the day after Thanksgiving, Christmas Eve (weekdays only)."""
    hol = nyse_holidays(year)
    cands = {date(year, 7, 3), _nth_weekday(year, 11, 3, 4) + timedelta(days=1), date(year, 12, 24)}
    return {d for d in cands if d.weekday() < 5 and d not in hol}


def session_tag(hour_start):
    """'open' / 'closed' / 'weekend' for the UTC hour starting at hour_start,
    judged at its midpoint in New York time (DST-aware). Holidays are 'closed'."""
    t = datetime.fromtimestamp(hour_start + 1800, timezone.utc).astimezone(ET)
    d = t.date()
    if d.weekday() >= 5:
        return "weekend"
    if d in nyse_holidays(d.year):
        return "closed"
    close = 13 * 60 if d in nyse_early_closes(d.year) else 16 * 60
    minute = t.hour * 60 + t.minute
    return "open" if 9 * 60 + 30 <= minute < close else "closed"


def is_gap_hour(hour_start):
    """An hour that can carry a closed-market gap: any non-open hour, or the
    first open hour after one (where the reopen print lands)."""
    tag = session_tag(hour_start)
    return tag != "open" or session_tag(hour_start - 3600) != "open"


# ---------------------------------------------------------------- position model

class Position:
    """A DLMM spot position: equal value per bin, bins at/below the open price in Y."""

    def __init__(self, p0, width, bin_step_bps, value_y):
        if p0 <= 0 or value_y <= 0 or bin_step_bps <= 0:
            raise ValueError("position needs positive price, value and bin step")
        self.p0, self.width, self.bin_step_bps, self.value_y = p0, width, bin_step_bps, value_y
        step = bin_step_bps / 1e4
        self.k = max(1, int(math.floor(math.log1p(width) / math.log1p(step) + 1e-9)))
        per_bin = value_y / (2 * self.k + 1)
        self.bins = []  # (price, x_amount, y_amount) at open
        for i in range(-self.k, self.k + 1):
            px = p0 * (1 + step) ** i
            self.bins.append((px, 0.0, per_bin) if i <= 0 else (px, per_bin / p0, 0.0))
        self.lo, self.hi = self.bins[0][0], self.bins[-1][0]
        self.x0 = sum(b[1] for b in self.bins)
        self.y0 = sum(b[2] for b in self.bins)

    def in_range(self, p):
        return self.lo <= p <= self.hi

    def value(self, p):
        """Position value in Y at price p (Y per X)."""
        total = 0.0
        for px, x, y in self.bins:
            if x:  # base bin: sold to Y at its own price once the market is above it
                total += x * px if p > px else x * p
            else:  # quote bin: bought X at its own price once the market is below it
                total += y / px * p if p < px else y
        return total

    def hold(self, p):
        return self.x0 * p + self.y0

    def markout(self, p):
        return self.value(p) - self.hold(p)

    def to_state(self):
        return {"p0": self.p0, "width": self.width, "bin_step_bps": self.bin_step_bps, "value_y": self.value_y}

    @classmethod
    def from_state(cls, s):
        return cls(s["p0"], s["width"], s["bin_step_bps"], s["value_y"])


def in_range_fraction(candles, lo, hi):
    """Share of the hour inside [lo, hi], from 5m candle high/low overlap."""
    if not candles:
        return None
    parts = []
    for c in candles:
        low, high = min(c["low"], c["high"]), max(c["low"], c["high"])
        if high <= low:
            parts.append(1.0 if lo <= c["close"] <= hi else 0.0)
        else:
            parts.append(max(0.0, min(high, hi) - max(low, lo)) / (high - low))
    return sum(parts) / len(parts)


def tx_chunks(bins):
    return max(1, math.ceil(bins / BINS_PER_TX))


def open_cost_sol(base_fee_pct, notional_sol, tx_cost_sol, txs):
    """Txs plus swapping half the notional into the other token."""
    return txs * tx_cost_sol + 0.5 * notional_sol * (base_fee_pct / 100.0 + SWAP_SLIP)


def step_hour(pos, p_start, candles, lp_fees_usd, tvl_usd, y_usd, sol_usd,
              base_fee_pct, notional_sol=NOTIONAL_SOL, tx_cost_sol=TX_COST_SOL, bins=None):
    """Advance one position by one hour. Returns (row, position_for_next_hour).

    `bins` = {"liq": <BinReader.liquidity result>, "dec_x", "dec_y"} switches the
    fee share to bin level; without it (or if it cannot cover the hour) the TVL
    share is used."""
    p_end = candles[-1]["close"] if candles else p_start
    frac = in_range_fraction(candles, pos.lo, pos.hi)
    if frac is None:  # no trade printed: price sat at p_start all hour
        frac = 1.0 if pos.in_range(p_start) else 0.0
    value_usd = pos.value(p_start) * y_usd
    share = value_usd / tvl_usd if tvl_usd and tvl_usd > 0 else 0.0
    fee_tvl = max(0.0, lp_fees_usd) * frac * share / sol_usd
    fee_bin, bin_share = None, None
    if bins:
        step = pos.bin_step_bps
        center = bin_id_for(pos.p0, step, bins["dec_x"], bins["dec_y"])
        per_bin = pos.value(p_start) / (2 * pos.k + 1)
        bin_share = bin_fee_share(candles, bins["liq"], center - pos.k, center + pos.k, per_bin,
                                  step, bins["dec_x"], bins["dec_y"], p_start)
        if bin_share is not None:
            fee_bin = max(0.0, lp_fees_usd) * bin_share / sol_usd
    fee_sol = fee_bin if fee_bin is not None else fee_tvl
    markout_sol = (pos.markout(p_end) - pos.markout(p_start)) * y_usd / sol_usd
    cost_sol, nxt, recentered = 0.0, pos, False
    if not pos.in_range(p_end):
        recentered = True
        # close + open, each one tx per 70-bin chunk
        cost_sol = open_cost_sol(base_fee_pct, notional_sol, tx_cost_sol, txs=2 * tx_chunks(2 * pos.k + 1))
        nxt = Position(p_end, pos.width, pos.bin_step_bps, notional_sol * sol_usd / y_usd)
    row = {
        "price_start": p_start, "price_end": p_end, "lo": pos.lo, "hi": pos.hi,
        "in_range_frac": round(frac, 6), "liq_share": share,
        "fee_basis": "bin" if fee_bin is not None else "tvl", "bin_share": bin_share,
        "fee_sol_tvl": fee_tvl, "fee_sol_bin": fee_bin,
        "fee_sol": fee_sol, "markout_sol": markout_sol, "cost_sol": cost_sol,
        "net_sol": fee_sol + markout_sol - cost_sol, "recentered": recentered,
    }
    return row, nxt


def y_usd_for(pool, price, sol_usd):
    if pool["y_mint"] == USDC:
        return 1.0
    if pool["y_mint"] == WSOL:
        return sol_usd
    if pool["x_mint"] == WSOL:
        return sol_usd / price
    raise ValueError(f"no USD route for {pool['label']}")


# ---------------------------------------------------------------- collector

class Collector:
    def __init__(self, profile, pools=None, clock=time.time, sleep=time.sleep, opener=None,
                 rpm=RPM, notional_sol=NOTIONAL_SOL, tx_cost_sol=TX_COST_SOL,
                 rpc_url=PUBLIC_RPC, rpc_opener=None):
        self.dir = Path(profile) / "memories" / "lp_majors_paper"
        self.samples_path = self.dir / "samples.jsonl"
        self.hours_path = self.dir / "hours.jsonl"
        self.summary_path = self.dir / "summary.jsonl"
        self.state_path = self.dir / "state.json"
        self.pools = pools if pools is not None else json.loads(POOLS_FILE.read_text())["pools"]
        self.clock, self.sleep = clock, sleep
        self.opener = opener
        self.gate = Gate(rpm, clock=clock, sleep=sleep)
        rpc_gate = Gate(RPC_RPM, clock=clock, sleep=sleep)
        self.bin_reader = (BinReader(rpc_gate, rpc_url, opener=rpc_opener) if rpc_opener
                           else BinReader(rpc_gate, rpc_url)) if rpc_url else None
        self.bin_snaps = {p["address"]: [] for p in self.pools}
        self.bin_tries = {}
        self.notional_sol, self.tx_cost_sol = notional_sol, tx_cost_sol
        self.snaps = {p["address"]: [] for p in self.pools}
        self.disabled = {}
        self.state = {"next_hour": {}, "positions": {}, "sol_usd": {}}
        self.next_sample = 0.0
        self.counters = self._fresh_counters()
        self.day = None

    @staticmethod
    def _fresh_counters():
        return {"samples": 0, "sample_failures": 0, "hours": 0, "fetch_failures": 0,
                "skipped_hours": 0, "identity_mismatch": 0, "bin_reads": 0, "bin_failures": 0,
                "hours_bin": 0, "hours_tvl": 0}

    # --- io
    def get(self, url):
        kw = {"opener": self.opener} if self.opener else {}
        return http_json(url, self.gate, USER_AGENT, **kw)

    def save_state(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, separators=(",", ":")))
        os.replace(tmp, self.state_path)

    def restore(self):
        if self.state_path.exists():
            try:
                self.state.update(json.loads(self.state_path.read_text()))
            except ValueError:
                log("lp-paper: state unreadable, starting fresh")
        cutoff = self.clock() - SNAPSHOT_KEEP_S
        for r in read_rows(self.samples_path):
            if r.get("status") == "ok" and r.get("ts", 0) >= cutoff and r.get("pool") in self.snaps:
                self.snaps[r["pool"]].append(r)

    # --- sampling
    def sample(self):
        now = self.clock()
        for pool in self.pools:
            addr = pool["address"]
            data = self.get(f"{API}/{addr}")
            row = {"ts": round(now, 3), "pool": addr, "label": pool["label"], "arm": pool["arm"]}
            if not isinstance(data, dict) or "token_x" not in data:
                self.counters["sample_failures"] += 1
                append(self.samples_path, dict(row, status="unavailable"))
                continue
            x, y = data["token_x"].get("address"), data["token_y"].get("address")
            if (x, y) != (pool["x_mint"], pool["y_mint"]):
                self.counters["identity_mismatch"] += 1
                self.disabled[addr] = "identity_mismatch"
                append(self.samples_path, dict(row, status="identity_mismatch", x=x, y=y))
                continue
            cfg = data.get("pool_config") or {}
            row.update(status="ok", price=data.get("current_price"), tvl=data.get("tvl"),
                       x_usd=data["token_x"].get("price"), y_usd=data["token_y"].get("price"),
                       bin_step=cfg.get("bin_step"), base_fee_pct=cfg.get("base_fee_pct"),
                       dynamic_fee_pct=data.get("dynamic_fee_pct"),
                       fees_1h=(data.get("fees") or {}).get("1h"),
                       volume_1h=(data.get("volume") or {}).get("1h"),
                       dec_x=data["token_x"].get("decimals"), dec_y=data["token_y"].get("decimals"))
            self.counters["samples"] += 1
            append(self.samples_path, row)
            snaps = self.snaps[addr]
            snaps.append(row)
            while snaps and snaps[0]["ts"] < now - SNAPSHOT_KEEP_S:
                snaps.pop(0)
            self.read_bins(addr, row, now)

    def read_bins(self, addr, row, now):
        """One bin-liquidity read per pool per clock hour (up to 3 tries)."""
        if self.bin_reader is None:
            return
        hour = hour_floor(now)
        snaps = self.bin_snaps[addr]
        if snaps and snaps[-1]["hour"] == hour:
            return
        tries = self.bin_tries.get((addr, hour), 0)
        if tries >= BIN_ATTEMPTS_PER_HOUR:
            return
        self.bin_tries = {k: v for k, v in self.bin_tries.items() if k[1] >= hour - 3600}
        self.bin_tries[(addr, hour)] = tries + 1
        try:
            price, step = float(row["price"]), int(row["bin_step"])
            dec_x, dec_y = int(row["dec_x"]), int(row["dec_y"])
        except (KeyError, TypeError, ValueError):
            return
        liq = self.bin_reader.liquidity(addr, price, step, dec_x, dec_y)
        status = {"ts": round(now, 3), "pool": addr, "kind": "bins"}
        if liq is None:
            self.counters["bin_failures"] += 1
            append(self.samples_path, dict(status, status="unavailable"))
            return
        self.counters["bin_reads"] += 1
        snaps.append({"ts": now, "hour": hour, "liq": liq, "dec_x": dec_x, "dec_y": dec_y, "bin_step": step})
        del snaps[:-6]
        near = sum(v for b, v in liq["liq"].items() if abs(b - liq["center"]) <= 2)
        append(self.samples_path, dict(status, status="ok", center=liq["center"], bins=len(liq["liq"]),
                                       liq_y_active5=near, liq_y_total=sum(liq["liq"].values())))

    def bins_for(self, addr, hour, bin_step):
        """The bin snapshot read during `hour`, else the nearest within 2h."""
        snaps = [s for s in self.bin_snaps.get(addr, []) if s["bin_step"] == bin_step]
        if not snaps:
            return None
        best = min(snaps, key=lambda s: (s["hour"] != hour, abs(s["ts"] - (hour + 1800))))
        if best["hour"] != hour and abs(best["ts"] - (hour + 1800)) > BIN_SNAPSHOT_MAX_AGE_S:
            return None
        return best

    def tvl_for(self, addr, hour):
        snaps = [s for s in self.snaps.get(addr, []) if s.get("tvl")]
        if not snaps:
            return None, None
        inside = [s for s in snaps if hour <= s["ts"] < hour + 3600]
        if inside:
            return statistics.fmean(s["tvl"] for s in inside), inside[-1]
        near = min(snaps, key=lambda s: abs(s["ts"] - (hour + 1800)))
        return near["tvl"], near

    # --- evaluation
    def ready_hour(self):
        """Start of the newest hour whose candles are final."""
        return hour_floor(self.clock() - EVAL_GRACE_S) - 3600

    def evaluate(self):
        last = self.ready_hour()
        order = sorted(self.pools, key=lambda p: not p.get("sol_usd_anchor"))
        for pool in order:
            addr = pool["address"]
            if addr in self.disabled:
                continue
            nxt = self.state["next_hour"].get(addr)
            if nxt is None:
                nxt = self.state["next_hour"][addr] = last  # paper starts at deploy, no backfill
            if nxt < last - MAX_BACKLOG_H * 3600:
                self.counters["skipped_hours"] += (last - MAX_BACKLOG_H * 3600 - nxt) // 3600
                nxt = last - MAX_BACKLOG_H * 3600
            while nxt <= last:
                end = min(last, nxt + (CHUNK_H - 1) * 3600)
                done = self._evaluate_chunk(pool, nxt, end)
                if done is None:
                    break
                nxt = done + 3600
                self.state["next_hour"][addr] = nxt
                self.save_state()
        keep = str(hour_floor(self.clock()) - SNAPSHOT_KEEP_S)
        self.state["sol_usd"] = {h: v for h, v in self.state["sol_usd"].items() if h >= keep}

    def _evaluate_chunk(self, pool, first, last):
        """Evaluate hours [first, last]; returns the last hour done, or None."""
        addr = pool["address"]
        # end_time is a bucket start: a range that starts and ends in the same
        # hour comes back as zeros, so ask through the next bucket and drop it.
        q = f"start_time={first}&end_time={last + 3600}"
        ohlcv = self.get(f"{API}/{addr}/ohlcv?timeframe=5m&{q}")
        hist = self.get(f"{API}/{addr}/volume/history?timeframe=1h&{q}")
        if not isinstance(ohlcv, dict) or not isinstance(hist, dict):
            self.counters["fetch_failures"] += 1
            return None
        candles = {}
        for c in ohlcv.get("data") or []:
            try:
                ts = int(c["timestamp"])
                candles.setdefault(hour_floor(ts), []).append(
                    {"ts": ts, "open": float(c["open"]), "high": float(c["high"]),
                     "low": float(c["low"]), "close": float(c["close"]),
                     "volume": float(c.get("volume") or 0.0)})
            except (KeyError, TypeError, ValueError):
                continue
        fees = {}
        for r in hist.get("data") or []:
            try:
                fees[int(r["timestamp"])] = float(r.get("fees") or 0) - float(r.get("protocol_fees") or 0)
            except (KeyError, TypeError, ValueError):
                continue
        done = None
        for hour in range(first, last + 1, 3600):
            cs = sorted(candles.get(hour, []), key=lambda c: c["ts"])
            if not self._evaluate_hour(pool, hour, cs, fees.get(hour)):
                break
            done = hour
        return done

    def _evaluate_hour(self, pool, hour, candles, lp_fees_usd):
        addr = pool["address"]
        tvl, snap = self.tvl_for(addr, hour)
        if tvl is None:
            return False  # sampler has not seen this pool yet
        key = str(hour)
        if pool.get("sol_usd_anchor"):
            if candles:
                self.state["sol_usd"][key] = candles[-1]["close"]
            elif snap and snap.get("x_usd"):
                self.state["sol_usd"][key] = snap["x_usd"]
        sol_usd = self.state["sol_usd"].get(key)
        if not sol_usd:
            return False  # wait for the anchor's hour
        bin_step = snap.get("bin_step") or 0
        base_fee = snap.get("base_fee_pct") or 0.0
        session = session_tag(hour)
        gap = is_gap_hour(hour)
        bsnap = self.bins_for(addr, hour, bin_step)
        bins = {"liq": bsnap["liq"], "dec_x": bsnap["dec_x"], "dec_y": bsnap["dec_y"]} if bsnap else None
        starts = {}
        for width in WIDTHS:
            st = self.state["positions"].get(f"{addr}:{width}")
            starts[width] = st["last_price"] if st else (candles[0]["open"] if candles else snap.get("price"))
        if not bin_step or not all(starts.values()):
            return False  # nothing written: every width of an hour lands together or not at all
        for width in WIDTHS:
            pkey = f"{addr}:{width}"
            st = self.state["positions"].get(pkey)
            p_start = starts[width]
            y_usd = y_usd_for(pool, p_start, sol_usd)
            opened = st is None
            if opened:
                pos = Position(p_start, width, bin_step, self.notional_sol * sol_usd / y_usd)
            else:
                pos = Position.from_state(st["pos"])
            y_usd_end = y_usd_for(pool, candles[-1]["close"] if candles else p_start, sol_usd)
            row, nxt = step_hour(pos, p_start, candles, lp_fees_usd or 0.0, tvl, y_usd_end, sol_usd,
                                 base_fee, self.notional_sol, self.tx_cost_sol, bins=bins)
            if bsnap:
                row["bin_age_s"] = round(abs(bsnap["ts"] - (hour + 1800)))
            self.counters["hours_" + row["fee_basis"]] += 1
            if opened:
                c0 = open_cost_sol(base_fee, self.notional_sol, self.tx_cost_sol, txs=tx_chunks(2 * pos.k + 1))
                row["cost_sol"] += c0
                row["net_sol"] -= c0
            row.update(rule_version=RULE_VERSION, hour=hour, pool=addr, label=pool["label"],
                       arm=pool["arm"], width=width, notional_sol=self.notional_sol,
                       session=session, gap_hour=gap, opened=opened, sol_usd=sol_usd,
                       candles=len(candles), fees_row=lp_fees_usd is not None,
                       tvl_age_s=round(abs(snap["ts"] - (hour + 1800))),
                       bins=2 * pos.k + 1, basis="paper_model_not_realized")
            append(self.hours_path, row)
            self.counters["hours"] += 1
            self.state["positions"][pkey] = {"pos": nxt.to_state(), "last_price": row["price_end"]}
        return True

    # --- housekeeping
    def roll_day(self):
        today = datetime.fromtimestamp(self.clock(), timezone.utc).strftime("%Y-%m-%d")
        if self.day is None:
            self.day = today
        if today != self.day:
            append(self.summary_path, dict(self.counters, day=self.day, requests=self.gate.requests,
                                           rate_limited=self.gate.rate_limited,
                                           disabled=dict(self.disabled), rule_version=RULE_VERSION))
            self.counters = self._fresh_counters()
            self.gate.requests = self.gate.rate_limited = 0
            self.day = today
            for path in (self.samples_path, self.hours_path):
                rotate(path, ROTATE_BYTES, ROTATE_KEEP, now=self.clock())

    def step(self):
        if self.clock() >= self.next_sample:
            self.sample()
            self.next_sample = self.clock() + SAMPLE_EVERY_S
        self.evaluate()
        self.roll_day()

    def run(self):
        self.restore()
        log(f"lp-paper: tracking {len(self.pools)} pools x {len(WIDTHS)} widths, "
            f"notional {self.notional_sol} SOL, tx {self.tx_cost_sol} SOL")
        while True:
            try:
                self.step()
            except Exception as exc:  # a bad payload must not kill a long soak
                log(f"lp-paper: cycle error {type(exc).__name__}: {exc}")
            self.sleep(max(5.0, self.next_sample - self.clock()))


# ---------------------------------------------------------------- report

def pulse_per_sol_day(memories, now, days=PULSE_WINDOW_D):
    """Pulse's realized SOL per deployed SOL-day over the window, from the
    profile's realized flows joined to close modes. Idle capital is not
    counted, which flatters pulse: the bar is set high on purpose."""
    modes = {r.get("position"): r.get("mode") for r in read_rows(Path(memories) / "dlmm_closes.jsonl")
             if r.get("position")}
    latest = {}
    for r in read_rows(Path(memories) / "dlmm_realized.jsonl"):
        if r.get("position"):
            latest[r["position"]] = r
    num = den = 0.0
    n = 0
    for pos, r in latest.items():
        try:
            closed, created = float(r["closed_at"]), float(r["created_at"])
            dep, real = float(r["deposit_sol"]), float(r["realized_sol"])
        except (KeyError, TypeError, ValueError):
            continue
        if modes.get(pos) != "pulse" or closed < now - days * 86400 or dep <= 0 or closed <= created:
            continue
        num += real
        den += dep * (closed - created) / 86400
        n += 1
    return (num / den if den > 0 else None), n


def summarize(rows, cluster_key):
    per_day = [r["net_sol"] / r["notional_sol"] * 24 for r in rows]
    hours = [r["hour"] for r in rows]
    lo, hi = cluster_bootstrap([{"mint": cluster_key(r), "pool": r["pool"], "net_ret": v}
                                for r, v in zip(rows, per_day)])
    neg = [r for r in rows if r["net_sol"] < 0]
    loss = -sum(r["net_sol"] for r in neg)
    gap_loss = -sum(r["net_sol"] for r in neg if r.get("gap_hour"))

    def comp(k):
        return statistics.fmean(r[k] / r["notional_sol"] * 24 for r in rows)

    return {
        "n": len(rows), "days": (max(hours) - min(hours) + 3600) / 86400,
        "mean": statistics.fmean(per_day), "lo": lo, "hi": hi,
        "fee": comp("fee_sol"), "markout": comp("markout_sol"), "cost": comp("cost_sol"),
        "in_range": statistics.fmean(r["in_range_frac"] for r in rows),
        "recenters": sum(1 for r in rows if r.get("recentered")),
        "gap_loss_share": gap_loss / loss if loss > 0 else 0.0,
    }


def verdict(s, arm, pulse):
    if s["n"] < DECIDE_MIN_N or s["days"] < DECIDE_MIN_DAYS:
        return f"CONTINUE (n {s['n']}/{DECIDE_MIN_N}, {s['days']:.1f}/{DECIDE_MIN_DAYS}d)"
    if arm == "B" and s["gap_loss_share"] > GAP_LOSS_SHARE_MAX:
        return f"KILL (closed-market gaps {s['gap_loss_share']:.0%} of loss)"
    if s["lo"] is None or s["lo"] <= 0:
        return "KILL (lower 95% CI <= 0)"
    if pulse is None:
        return "HOLD (lower CI > 0; pulse baseline unmeasured)"
    if s["mean"] > pulse:
        return "PROMOTE (0.1 SOL canary under the 30% DD pause)"
    return "HOLD (lower CI > 0 but mean <= pulse)"


def _fmt(v):
    return "   n/a  " if v is None else f"{v:+.5f}"


_HEAD = (f"{'group':<26}{'n':>6}{'days':>6}{'net':>10}{'ci_lo':>10}{'ci_hi':>10}{'fee':>10}"
         f"{'markout':>10}{'cost':>10}{'inrng':>7}{'rec':>5}")


def _line(name, s):
    return (f"{name:<26}{s['n']:>6}{s['days']:>6.1f}{_fmt(s['mean']):>10}{_fmt(s['lo']):>10}{_fmt(s['hi']):>10}"
            f"{_fmt(s['fee']):>10}{_fmt(s['markout']):>10}{_fmt(s['cost']):>10}{s['in_range']:>7.2f}"
            f"{s['recenters']:>5}")


def _day(r):
    return datetime.fromtimestamp(r["hour"], timezone.utc).strftime("%Y-%m-%d")


def _name(key):
    head = "/".join(str(k) for k in key[:-1])
    return (head + " " if head else "all pools ") + f"±{key[-1]:.0%}"


def _table(rows, out, results, tag, levels, pulse=None):
    for level, keyf, cluster in levels:
        out("")
        title = "width" if level == "width" else f"{level} x width"
        out(f"{tag}by {title} (CI clusters: {'pools' if level != 'pool' else 'UTC days'})")
        out(_HEAD + ("  verdict" if pulse is not False else ""))
        groups = {}
        for r in rows:
            groups.setdefault(keyf(r), []).append(r)
        for key in sorted(groups):
            s = summarize(groups[key], cluster)
            if pulse is False:
                results[(tag + level,) + key] = s
                out(_line(_name(key), s))
            else:
                arm = key[0] if level != "width" else None
                v = verdict(s, arm, pulse)
                results[(tag + level,) + key] = dict(s, verdict=v)
                out(_line(_name(key), s) + f"  {v}")


LEVELS = (
    ("width", lambda r: (r["width"],), lambda r: r["pool"]),
    ("arm", lambda r: (r["arm"], r["width"]), lambda r: r["pool"]),
    ("pool", lambda r: (r["arm"], r["label"], r["width"]), _day),
)


def report(profile, out=print, now=None, pulse_override=None):
    memories = Path(profile) / "memories"
    rows = [r for r in read_rows(memories / "lp_majors_paper" / "hours.jsonl", with_archives=True)
            if r.get("rule_version") in REPORT_VERSIONS and r.get("notional_sol")]
    for r in rows:
        r.setdefault("fee_basis", "tvl")
    now = time.time() if now is None else now
    if pulse_override is not None:
        pulse, pulse_n = pulse_override, None
    else:
        pulse, pulse_n = pulse_per_sol_day(memories, now)
    out(f"LP majors paper (rule v{RULE_VERSION}: fee model updated to bin-level share where RPC "
        f"answered, TVL share otherwise; kill/promote rules unchanged); units: SOL per SOL-day, "
        f"modelled, not realized")
    out(f"pulse bar: {'unmeasured' if pulse is None else f'{pulse:+.5f}'}"
        + (f" (n={pulse_n} closes, {PULSE_WINDOW_D}d)" if pulse_n is not None else " (override)"))
    if not rows:
        out("no evaluated hours yet")
        return {}
    basis = {}
    for r in rows:
        basis[r["fee_basis"]] = basis.get(r["fee_basis"], 0) + 1
    out("fee basis (position-hours): " + ", ".join(f"{k} {v}" for k, v in sorted(basis.items())))
    results = {}
    _table(rows, out, results, "", LEVELS, pulse)
    b = [r for r in rows if r["arm"] == "B"]
    if b:
        out("")
        out("arm B by session (gap = first open hour after a closure)")
        out(_HEAD)
        slices = {}
        for r in b:
            tag = "open-gap" if r["session"] == "open" and r.get("gap_hour") else r["session"]
            slices.setdefault((tag, r["width"]), []).append(r)
        for key in sorted(slices):
            s = summarize(slices[key], lambda r: r["pool"])
            results[("session",) + key] = s
            out(_line(key[0] + f" ±{key[1]:.0%}", s))
    binrows = [r for r in rows if r["fee_basis"] == "bin"]
    if len(binrows) >= BIN_REPORT_MIN_HOURS:
        out("")
        out(f"--- bin-basis hours only ({len(binrows)}; informational, verdicts above are binding) ---")
        _table(binrows, out, results, "bin:", LEVELS, pulse=False)
        out("")
        out("same-hour fee per SOL-day, bin vs tvl share (rows with both)")
        out(f"{'group':<26}{'n':>6}{'fee_bin':>11}{'fee_tvl':>11}{'bin/tvl':>9}")
        groups = {}
        for r in binrows:
            if r.get("fee_sol_bin") is not None and r.get("fee_sol_tvl") is not None:
                groups.setdefault((r["arm"], r["label"], r["width"]), []).append(r)
        for key in sorted(groups):
            g = groups[key]
            fb = statistics.fmean(r["fee_sol_bin"] / r["notional_sol"] * 24 for r in g)
            ft = statistics.fmean(r["fee_sol_tvl"] / r["notional_sol"] * 24 for r in g)
            results[("fee_compare",) + key] = {"n": len(g), "fee_bin": fb, "fee_tvl": ft}
            ratio = f"{fb / ft:9.2f}" if ft > 0 else "      n/a"
            out(f"{_name(key):<26}{len(g):>6}{fb:>+11.5f}{ft:>+11.5f}{ratio}")
    elif binrows:
        out(f"\nbin-basis hours: {len(binrows)} (< {BIN_REPORT_MIN_HOURS}, separate tables withheld)")
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--profile", required=True)
    ap.add_argument("--report", action="store_true", help="print the evaluation and exit")
    ap.add_argument("--once", action="store_true", help="one sample + evaluation cycle, then exit")
    ap.add_argument("--rpm", type=float, default=RPM, help="datapi requests per minute (max 60)")
    ap.add_argument("--notional-sol", type=float, default=NOTIONAL_SOL)
    ap.add_argument("--tx-cost-sol", type=float, default=TX_COST_SOL)
    ap.add_argument("--rpc-url", default=PUBLIC_RPC,
                    help="keyless Solana RPC for bin reads; empty string disables (TVL share only)")
    ap.add_argument("--pulse-per-sol-day", type=float, default=None,
                    help="override the pulse bar instead of reading the profile journals")
    a = ap.parse_args(argv)
    if a.report:
        report(a.profile, pulse_override=a.pulse_per_sol_day)
        return 0
    col = Collector(a.profile, rpm=min(max(a.rpm, 1.0), 60.0),
                    notional_sol=a.notional_sol, tx_cost_sol=a.tx_cost_sol, rpc_url=a.rpc_url)
    if a.once:
        col.restore()
        col.step()
        col.save_state()
        log(json.dumps(dict(col.counters, requests=col.gate.requests,
                            rpc_calls=col.bin_reader.calls if col.bin_reader else 0)))
        return 0
    col.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
