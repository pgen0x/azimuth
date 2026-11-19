"""Graduation paper-trader (experiment S1). Read-only: never signs, sends or routes.

Collects freshly graduated Solana memecoin pools (bonding curve -> AMM) from the
public GeckoTerminal `new_pools` feed, fetches each pool's 1-minute candles for
24h, and closes a PAPER trade per pool under a pre-registered rule. It runs
outside the trading path: nothing here reads a wallet, a key, an env file, the
daemon's dedup store or the pipeline.

Graduation filter (pre-registered; every field is recorded so it can be audited):
  * GT dex id in GRADUATION_DEXES — the AMM venues launchpads migrate INTO
    (pump.fun -> pumpswap; Meteora DBC launchpads -> meteora-damm-v2/meteora-damm;
    Raydium LaunchLab -> raydium-cpmm; legacy pump.fun -> raydium). Bonding-curve
    venues (pump-fun, meteora-dbc, raydium-launchlab, ...) are counted, not kept.
  * quote token is wrapped SOL;
  * reserve_in_usd >= MIN_RESERVE_USD — anyone can open a PumpSwap/DAMM pool by
    hand, and those are dust (a real graduation seeds tens of SOL of liquidity);
  * first sighted within MAX_SIGHTING_AGE_S of pool creation.
  Jupiter's `graduatedPool == this pool` is journaled as a confirmation field,
  not required (keyless lookups fail; the rule must not depend on them).

Paper rule (pre-registered, RULE_VERSION):
  enter at the OPEN of the first 1m candle at or after T0+3m (T0 = pool
  creation); exit on whichever comes first of a 25% trailing stop from the peak
  high, a -30% stop from entry, or 24h after entry (close of the last candle
  before entry+24h). Net return = exit/entry - 1 - 8% round-trip cost.
  Intra-candle order is unknown, so each candle is tested against the stop set by
  the PREVIOUS peak first (gap through a stop fills at the open), then the peak
  is raised to the candle's high and its low is tested against the new trail
  (high-then-low). Prices are in SOL (GT `currency=token`).
  NOTE: a 25% trail measured from a peak that starts at the entry price is
  never below entry*0.75, so it always sits above the -30% floor: the first
  drawdown exits at -25%, and the -30% stop binds only as a gap fill. The rule is
  kept literal (it was pre-registered); reason "stop" marks an exit whose peak
  never rose above entry, "trail" one that gave back a gain.

Arms: "all" (every pool passing the filter) and "safety" (pulse-style safety
gates where Jupiter has the data: mint and freeze authority disabled, bot
holders <= 25% (the pulse audit cap), and not contradicted as a graduation).
Unknown fields pass (the repo's fail-open rule) and are recorded. Safety data is
read at sighting, which must precede entry, so arm "safety" admits only pools
sighted before T0+3m: a later read would be look-ahead.

Rate limits: one process-wide gate for GeckoTerminal (default 8 req/min, the
keyless tier's documented ~10 less headroom for other GT callers on this host —
see internal/robinhood/gtlimit.go), cooldown on 429 with exponential backoff,
and a separate 1 req/s gate for Jupiter.

Journals (append-only JSONL, size-rotated to .gz): <profile>/memories/grad_paper/
{pools,trades,summary}.jsonl. `--report` evaluates trades against the S1 rules.
"""
import argparse
import gzip
import json
import math
import random
import shutil
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RULE_VERSION = 1
GT_BASE = "https://api.geckoterminal.com/api/v2"
JUP_SEARCH = "https://datapi.jup.ag/v1/assets/search"
GT_USER_AGENT = "Mozilla/5.0 (compatible; research-client)"
JUP_USER_AGENT = "curl/8.5.0"  # Jupiter's Cloudflare 403s urllib's default UA
WSOL = "So11111111111111111111111111111111111111112"
GRADUATION_DEXES = frozenset({
    "pumpswap", "meteora-damm-v2", "meteora-damm", "raydium", "raydium-cpmm", "raydium-cp",
})
MIN_RESERVE_USD = 5000.0
MAX_SIGHTING_AGE_S = 600

ENTRY_DELAY_S = 180
TRAIL_PCT = 0.25
STOP_PCT = 0.30
HOLD_S = 24 * 3600
COST = 0.08
SAFETY_MAX_BOT_PCT = 25.0

POLL_EVERY_S = 60
FIRST_FETCH_S = 20 * 60          # first candle read, T0 + 20m
REFRESH_S = 2 * 3600             # then every 2h (early exits close early)
FINAL_GRACE_S = 5 * 60           # final read once entry+24h candles have settled
DATA_GAP_AFTER_S = 6 * 3600      # give up on a pool whose final read keeps failing
FAIL_RETRY_S = 10 * 60
MAX_TRACKED = 150
GT_LIMIT = 1000                  # GT's max candles per OHLCV request

ROTATE_BYTES = 32 * 1024 * 1024
ROTATE_KEEP = 12

# S1 registry rules (.orchestra/experiments.md row S1).
PROMOTE_MIN_N = 1000
PROMOTE_MIN_DAYS = 7
KILL_MAX_DAYS = 14
KILL_MAX_N = 1500
KILL_EARLY_N = 500
KILL_EARLY_MEAN = -0.03


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- rate limiting

class Gate:
    """Serializes requests at least `interval` apart; a 429 pauses all requests.

    Consecutive 429s double the pause (capped); any success resets it. Clock and
    sleep are injectable so tests never wait.
    """

    def __init__(self, per_minute, cooldown_s=75.0, max_cooldown_s=600.0, clock=time.time, sleep=time.sleep):
        self.interval = 60.0 / per_minute
        self.cooldown_s = cooldown_s
        self.max_cooldown_s = max_cooldown_s
        self.clock, self.sleep = clock, sleep
        self.next_at = 0.0
        self.cool_until = 0.0
        self.strikes = 0
        self.requests = 0
        self.rate_limited = 0

    def acquire(self):
        now = self.clock()
        wake = max(self.next_at, self.cool_until)
        if wake > now:
            self.sleep(wake - now)
            now = wake
        self.next_at = now + self.interval
        self.requests += 1

    def penalize(self):
        self.strikes += 1
        self.rate_limited += 1
        pause = min(self.max_cooldown_s, self.cooldown_s * 2 ** (self.strikes - 1))
        self.cool_until = max(self.cool_until, self.clock() + pause)
        return pause

    def ok(self):
        self.strikes = 0


def http_json(url, gate, user_agent, opener=urllib.request.urlopen, timeout=20):
    """GET url through `gate`. Returns parsed JSON, or None on any failure."""
    gate.acquire()
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    try:
        with opener(req, timeout=timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            log(f"grad-paper: 429 from {url.split('?')[0]} — pausing {gate.penalize():.0f}s")
        return None
    except (urllib.error.URLError, OSError, ValueError):
        return None
    gate.ok()
    return data


# ---------------------------------------------------------------- journals

def rotate(path, max_bytes=ROTATE_BYTES, keep=ROTATE_KEEP, now=None):
    """gzip `path` aside once it exceeds max_bytes; keep the newest `keep` archives."""
    path = Path(path)
    try:
        if path.stat().st_size <= max_bytes:
            return None
    except FileNotFoundError:
        return None
    stamp = datetime.fromtimestamp(now if now is not None else time.time(), timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = path.with_name(f"{path.stem}.{stamp}.jsonl.gz")
    with open(path, "rb") as src, gzip.open(archive, "wb") as dst:
        shutil.copyfileobj(src, dst)
    path.unlink()
    archives = sorted(path.parent.glob(f"{path.stem}.*.jsonl.gz"))
    for old in archives[:-keep] if keep > 0 else archives:
        old.unlink()
    return archive


def append(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def read_rows(path, with_archives=False):
    """Rows of a journal, oldest archive first; unreadable lines are skipped."""
    path = Path(path)
    files = sorted(path.parent.glob(f"{path.stem}.*.jsonl.gz")) if with_archives else []
    files.append(path)
    for file in files:
        if not file.exists():
            continue
        opener = gzip.open if file.suffix == ".gz" else open
        with opener(file, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


# ---------------------------------------------------------------- paper rule

def simulate(candles, t0, now, entry_delay=ENTRY_DELAY_S, trail=TRAIL_PCT, stop=STOP_PCT,
             hold=HOLD_S, cost=COST):
    """Apply the paper rule to 1m candles [(ts, open, high, low, close), ...].

    Returns a dict whose `status` is "open" (no exit yet and the path is not
    complete), "closed", or "no_entry" (no candle in the entry window by the
    time the window ended).
    """
    candles = sorted(c for c in candles if c[0] >= t0)
    entry_from = t0 + entry_delay
    entry = next((c for c in candles if entry_from <= c[0] < entry_from + hold), None)
    if entry is None or not entry[1] or entry[1] <= 0:
        return {"status": "no_entry" if now >= entry_from + hold else "open"}
    entry_ts, entry_px = entry[0], entry[1]
    end_ts = entry_ts + hold
    floor = entry_px * (1 - stop)
    peak = entry_px
    last = entry
    for ts, o, h, low, c in (x for x in candles if entry_ts <= x[0] < end_ts):
        level = max(floor, peak * (1 - trail))
        reason = "trail" if peak > entry_px else "stop"
        if ts > entry_ts and o <= level:
            return _closed(entry_ts, entry_px, ts, o, reason, peak, cost)
        if low <= level:
            return _closed(entry_ts, entry_px, ts, level, reason, peak, cost)
        if h > peak:
            peak = h
            level = max(floor, peak * (1 - trail))
            if low <= level:
                return _closed(entry_ts, entry_px, ts, level, "trail", peak, cost)
        last = (ts, o, h, low, c)
    if now < end_ts:
        return {"status": "open", "entry_ts": entry_ts, "entry_px": entry_px, "peak_px": peak}
    return _closed(entry_ts, entry_px, last[0], last[4], "time", peak, cost)


def _closed(entry_ts, entry_px, exit_ts, exit_px, reason, peak, cost):
    gross = exit_px / entry_px - 1
    return {"status": "closed", "entry_ts": entry_ts, "entry_px": entry_px, "exit_ts": exit_ts,
            "exit_px": exit_px, "reason": reason, "peak_px": peak, "gross_ret": gross,
            "net_ret": gross - cost, "hold_min": (exit_ts - entry_ts) / 60}


# ---------------------------------------------------------------- feed parsing

def parse_ts(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def parse_new_pools(payload):
    """GT new_pools page -> list of plain pool dicts (all dexes, unfiltered)."""
    tokens = {i["id"]: i.get("attributes", {}) for i in (payload or {}).get("included", []) if i.get("type") == "token"}
    out = []
    for p in (payload or {}).get("data", []):
        a, r = p.get("attributes", {}), p.get("relationships", {})

        def rid(k):
            return ((r.get(k) or {}).get("data") or {}).get("id") or ""

        base_id, quote_id = rid("base_token"), rid("quote_token")
        out.append({
            "pool": a.get("address"), "dex": rid("dex"), "name": a.get("name"),
            "created_at": parse_ts(a.get("pool_created_at")),
            "mint": base_id.split("_", 1)[-1], "quote": quote_id.split("_", 1)[-1],
            "symbol": tokens.get(base_id, {}).get("symbol"),
            "reserve_usd": num(a.get("reserve_in_usd")), "fdv_usd": num(a.get("fdv_usd")),
            "mcap_usd": num(a.get("market_cap_usd")),
            "tx_m5": ((a.get("transactions") or {}).get("m5") or {}),
        })
    return out


def graduation_reason(p, now):
    """'' when the pool passes the graduation filter, else why it does not."""
    if p["dex"] not in GRADUATION_DEXES:
        return "dex"
    if p["quote"] != WSOL:
        return "quote"
    if p["reserve_usd"] is None or p["reserve_usd"] < MIN_RESERVE_USD:
        return "reserve"
    if p["created_at"] is None or now - p["created_at"] > MAX_SIGHTING_AGE_S:
        return "late"
    if not p["pool"] or not p["mint"]:
        return "identity"
    return ""


def safety(jup, pool, sighted_at, created_at):
    """Arm-B verdict from a Jupiter asset (or None). Unknown fields pass."""
    audit = (jup or {}).get("audit") or {}
    unknown, failed = [], []

    def check(name, value, good):
        if value is None:
            unknown.append(name)
        elif not good(value):
            failed.append(name)

    check("mint_authority_disabled", audit.get("mintAuthorityDisabled"), lambda v: v is True)
    check("freeze_authority_disabled", audit.get("freezeAuthorityDisabled"), lambda v: v is True)
    check("bot_holders_pct", num(audit.get("botHoldersPercentage")), lambda v: v <= SAFETY_MAX_BOT_PCT)
    check("graduated_pool", (jup or {}).get("graduatedPool"), lambda v: v == pool)
    if sighted_at >= created_at + ENTRY_DELAY_S:
        failed.append("sighted_after_entry")
    return {"pass": not failed, "failed": failed, "unknown": unknown}


def jup_fields(jup, pool):
    if not jup:
        return None
    audit = jup.get("audit") or {}
    graduated = jup.get("graduatedPool")
    return {
        "launchpad": jup.get("launchpad"), "graduated_pool_match": (graduated == pool) if graduated else None,
        "graduated_at": jup.get("graduatedAt"), "holders": jup.get("holderCount"),
        "organic_score": jup.get("organicScore"), "mcap": num(jup.get("mcap")),
        "liquidity": num(jup.get("liquidity")),
        "mint_authority_disabled": audit.get("mintAuthorityDisabled"),
        "freeze_authority_disabled": audit.get("freezeAuthorityDisabled"),
        "bot_holders_pct": num(audit.get("botHoldersPercentage")),
        "top_holders_pct": num(audit.get("topHoldersPercentage")),
        "insider_pct": num(audit.get("insiderPct")), "sniper_pct": num(audit.get("sniperPct")),
    }


def parse_ohlcv(payload):
    rows = (((payload or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    out = []
    for r in rows:
        vals = [num(v) for v in r[:5]]
        if len(vals) == 5 and None not in vals:
            out.append((int(vals[0]), vals[1], vals[2], vals[3], vals[4]))
    return out


# ---------------------------------------------------------------- collector

class Collector:
    def __init__(self, profile, gt_rpm=8.0, max_tracked=MAX_TRACKED, clock=time.time, sleep=time.sleep,
                 opener=urllib.request.urlopen):
        self.dir = Path(profile) / "memories" / "grad_paper"
        self.pools_path = self.dir / "pools.jsonl"
        self.trades_path = self.dir / "trades.jsonl"
        self.summary_path = self.dir / "summary.jsonl"
        self.clock, self.sleep, self.opener = clock, sleep, opener
        self.gt = Gate(gt_rpm, clock=clock, sleep=sleep)
        self.jup = Gate(60.0, clock=clock, sleep=sleep)
        self.max_tracked = max_tracked
        self.tracked = {}       # pool -> state
        self.seen = set()       # pools already sighted (filter-pass or not) this process
        self.next_poll = 0.0
        self.last_poll = None
        self.counters = self._fresh_counters()
        self.day = self._day(clock())

    @staticmethod
    def _day(ts):
        return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def _fresh_counters():
        return {"polls": 0, "sighted": 0, "kept": 0, "dropped_capacity": 0, "possible_gap_polls": 0,
                "excluded": {}, "dex_seen": {}}

    # -- restart
    def restore(self):
        """Rebuild the tracked set from the journals: sighted, not yet closed."""
        now = self.clock()
        done = {r.get("pool") for r in read_rows(self.trades_path, with_archives=True) if r.get("arm") == "all"}
        horizon = now - (ENTRY_DELAY_S + HOLD_S + DATA_GAP_AFTER_S + FINAL_GRACE_S)
        for r in read_rows(self.pools_path, with_archives=True):
            pool = r.get("pool")
            if not pool:
                continue
            self.seen.add(pool)
            if r.get("event") == "dropped":
                self.tracked.pop(pool, None)
            elif r.get("event") == "sighted" and pool not in done and (r.get("created_at") or 0) >= horizon:
                self.tracked[pool] = self._state(r, max(now, r["created_at"] + FIRST_FETCH_S))
        log(f"grad-paper: restored {len(self.tracked)} tracked pool(s)")

    @staticmethod
    def _state(row, due):
        return {"row": row, "due": due, "failed_since": None}

    # -- poll
    def poll(self):
        now = self.clock()
        pools = []
        for page in (1, 2):
            payload = http_json(f"{GT_BASE}/networks/solana/new_pools?page={page}&include=base_token,quote_token,dex",
                                self.gt, GT_USER_AGENT, self.opener)
            got = parse_new_pools(payload)
            pools += got
            oldest = min((p["created_at"] for p in got if p["created_at"]), default=None)
            # Page 2 only when page 1 does not reach back to the previous poll.
            if page == 1 and (oldest is None or self.last_poll is None or oldest <= self.last_poll):
                break
            if page == 2 and oldest is not None and oldest > self.last_poll:
                self.counters["possible_gap_polls"] += 1
        self.counters["polls"] += 1
        self.last_poll = now
        for p in pools:
            if not p["pool"] or p["pool"] in self.seen:
                continue
            self.seen.add(p["pool"])
            dex = self.counters["dex_seen"]
            dex[p["dex"]] = dex.get(p["dex"], 0) + 1
            why = graduation_reason(p, now)
            if why:
                ex = self.counters["excluded"]
                ex[why] = ex.get(why, 0) + 1
                continue
            self._admit(p, now)

    def _admit(self, p, now):
        jup = http_json(f"{JUP_SEARCH}?query={p['mint']}", self.jup, JUP_USER_AGENT, self.opener)
        asset = next((a for a in jup or [] if isinstance(a, dict) and a.get("id") == p["mint"]), None)
        verdict = safety(asset, p["pool"], now, p["created_at"])
        row = {"event": "sighted", "ts": now, "rule_version": RULE_VERSION, **p,
               "age_at_sighting_s": now - p["created_at"], "jupiter": jup_fields(asset, p["pool"]),
               "safety_pass": verdict["pass"], "safety_failed": verdict["failed"], "safety_unknown": verdict["unknown"]}
        append(self.pools_path, row)
        self.counters["sighted"] += 1
        if len(self.tracked) >= self.max_tracked:
            oldest = min(self.tracked, key=lambda k: self.tracked[k]["row"]["created_at"])
            append(self.pools_path, {"event": "dropped", "ts": now, "pool": oldest, "reason": "capacity"})
            del self.tracked[oldest]
            self.counters["dropped_capacity"] += 1
        self.tracked[p["pool"]] = self._state(row, p["created_at"] + FIRST_FETCH_S)
        self.counters["kept"] += 1
        log(f"grad-paper: tracking {p.get('symbol')} {p['pool'][:8]} dex={p['dex']} "
            f"reserve=${p['reserve_usd']:.0f} safety={'pass' if verdict['pass'] else ','.join(verdict['failed'])}")

    # -- candles
    def candles(self, pool, t0, end):
        """1m candles covering [t0, end], at most two requests. None on failure."""
        out, before = [], int(end)
        for _ in range(2):
            payload = http_json(f"{GT_BASE}/networks/solana/pools/{pool}/ohlcv/minute?aggregate=1&limit={GT_LIMIT}"
                                f"&currency=token&token=base&before_timestamp={before}", self.gt, GT_USER_AGENT,
                                self.opener)
            if payload is None:
                return None
            got = parse_ohlcv(payload)
            out += got
            if len(got) < GT_LIMIT or min(c[0] for c in got) <= t0:
                break
            before = min(c[0] for c in got)
        return sorted(set(out))

    def refresh(self, pool):
        now = self.clock()
        st = self.tracked[pool]
        t0 = st["row"]["created_at"]
        deadline = t0 + ENTRY_DELAY_S + HOLD_S + FINAL_GRACE_S
        got = self.candles(pool, t0, min(now, deadline))
        if got is None:
            st["failed_since"] = st["failed_since"] or now
            if now >= deadline + DATA_GAP_AFTER_S:
                self.close(pool, {"status": "data_gap"})
            else:
                st["due"] = now + FAIL_RETRY_S
            return
        st["failed_since"] = None
        result = simulate(got, t0, now)
        if result["status"] == "open":
            if now >= deadline:
                # The final read is in but the 24h window is not covered: the
                # entry candle came late. Keep reading until it is, then give up.
                if now >= deadline + DATA_GAP_AFTER_S:
                    self.close(pool, {"status": "data_gap"})
                    return
                st["due"] = now + FAIL_RETRY_S
            else:
                st["due"] = min(now + REFRESH_S, deadline)
            return
        self.close(pool, result)

    def close(self, pool, result):
        row = self.tracked.pop(pool)["row"]
        arms = ["all"] + (["safety"] if row.get("safety_pass") else [])
        for arm in arms:
            append(self.trades_path, {"ts": self.clock(), "arm": arm, "rule_version": RULE_VERSION,
                                      "pool": pool, "mint": row["mint"], "symbol": row.get("symbol"),
                                      "dex": row["dex"], "t0": row["created_at"], **result})
        log(f"grad-paper: closed {row.get('symbol')} {pool[:8]} {result['status']} "
            f"{result.get('reason', '')} net={result.get('net_ret')}")

    # -- summary
    def maybe_summarize(self):
        today = self._day(self.clock())
        if today == self.day:
            return
        self.summarize(self.day)
        self.day = today
        self.counters = self._fresh_counters()
        for path in (self.pools_path, self.trades_path, self.summary_path):
            rotate(path, now=self.clock())

    def summarize(self, day):
        arms = {}
        for r in read_rows(self.trades_path):
            if self._day(r.get("ts", 0)) != day:
                continue
            a = arms.setdefault(r["arm"], {"closed": [], "no_entry": 0, "data_gap": 0})
            if r.get("status") == "closed":
                a["closed"].append(r["net_ret"])
            elif r.get("status") in ("no_entry", "data_gap"):
                a[r["status"]] += 1
        out = {"day": day, "rule_version": RULE_VERSION, **self.counters, "tracked_now": len(self.tracked),
               "gt_requests": self.gt.requests, "gt_429": self.gt.rate_limited, "arms": {}}
        for arm, a in arms.items():
            xs = a["closed"]
            out["arms"][arm] = {"n": len(xs), "mean_net": statistics.fmean(xs) if xs else None,
                                "median_net": statistics.median(xs) if xs else None,
                                "win_rate": sum(x > 0 for x in xs) / len(xs) if xs else None,
                                "no_entry": a["no_entry"], "data_gap": a["data_gap"]}
        append(self.summary_path, out)

    # -- loop
    def step(self):
        """One scheduler action. Returns seconds to sleep before the next step."""
        now = self.clock()
        self.maybe_summarize()
        if now >= self.next_poll:
            self.next_poll = now + POLL_EVERY_S
            self.poll()
            return 0.0
        due = [p for p, st in self.tracked.items() if st["due"] <= now]
        if due:
            # Newest first: when the budget is short, fresh paths win over old ones.
            self.refresh(max(due, key=lambda p: self.tracked[p]["row"]["created_at"]))
            return 0.0
        nxt = min([self.next_poll] + [st["due"] for st in self.tracked.values()])
        return max(0.0, nxt - now)

    def run(self):
        self.restore()
        while True:
            wait = self.step()
            if wait:
                self.sleep(min(wait, POLL_EVERY_S))


# ---------------------------------------------------------------- report

def cluster_bootstrap(rows, key="mint", n_boot=2000, seed=7):
    """95% CI of the mean net return, resampling clusters (one token can graduate
    into more than one pool, and those paths are not independent)."""
    clusters = {}
    for r in rows:
        clusters.setdefault(r.get(key) or r["pool"], []).append(r["net_ret"])
    groups = list(clusters.values())
    if len(groups) < 2:
        return None, None
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        pick = [x for _ in groups for x in rng.choice(groups)]
        means.append(statistics.fmean(pick))
    means.sort()
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1]


def evaluate(rows):
    """S1 registry verdict for one arm's closed rows."""
    rows = sorted(rows, key=lambda r: r["entry_ts"])
    n = len(rows)
    if n == 0:
        return {"n": 0, "verdict": "CONTINUE"}
    xs = [r["net_ret"] for r in rows]
    lo, hi = cluster_bootstrap(rows)
    days = (rows[-1]["entry_ts"] - rows[0]["entry_ts"]) / 86400
    second = xs[n // 2:]
    second_mean = statistics.fmean(second) if second else None
    mean = statistics.fmean(xs)
    out = {"n": n, "mean": mean, "ci_low": lo, "ci_high": hi, "days": days, "second_half_mean": second_mean,
           "win_rate": sum(x > 0 for x in xs) / n, "median": statistics.median(xs)}
    if (n >= PROMOTE_MIN_N and days >= PROMOTE_MIN_DAYS and mean > 0 and lo is not None and lo > 0
            and second_mean is not None and second_mean > 0):
        out["verdict"] = "PROMOTE"
    elif n >= KILL_EARLY_N and mean < KILL_EARLY_MEAN and hi is not None and hi < 0:
        out["verdict"] = "KILL (mean below -3% with CI upper < 0)"
    elif days >= KILL_MAX_DAYS or n >= KILL_MAX_N:
        out["verdict"] = "KILL (14d / 1500 trades without promote)"
    else:
        out["verdict"] = "CONTINUE"
    return out


def report(profile, as_json=False):
    path = Path(profile) / "memories" / "grad_paper" / "trades.jsonl"
    arms, other = {}, {}
    for r in read_rows(path, with_archives=True):
        if r.get("status") == "closed" and r.get("net_ret") is not None:
            arms.setdefault(r["arm"], []).append(r)
        else:
            key = (r.get("arm"), r.get("status"))
            other[key] = other.get(key, 0) + 1
    result = {arm: evaluate(rows) for arm, rows in sorted(arms.items())}
    for (arm, status), count in other.items():
        result.setdefault(arm, {"n": 0, "verdict": "CONTINUE"})[status] = count
    if as_json:
        print(json.dumps(result, indent=2))
        return result
    if not result:
        print("grad-paper: no trades yet")

    def fmt(v):
        return "n/a" if v is None else f"{100 * v:+.2f}%"

    for arm, r in result.items():
        if not r.get("n"):
            print(f"[{arm}] n=0 {r['verdict']}")
            continue
        print(f"[{arm}] n={r['n']} over {r['days']:.1f}d  mean {fmt(r['mean'])} "
              f"CI [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}] (mint-clustered)  "
              f"median {fmt(r['median'])}  win {100 * r['win_rate']:.0f}%  "
              f"second half {fmt(r['second_half_mean'])}  -> {r['verdict']}"
              + (f"  no_entry={r['no_entry']}" if r.get("no_entry") else "")
              + (f"  data_gap={r['data_gap']}" if r.get("data_gap") else ""))
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--profile", type=Path, required=True)
    ap.add_argument("--report", action="store_true", help="evaluate trades against the S1 rules and exit")
    ap.add_argument("--json", action="store_true", help="with --report, print JSON")
    ap.add_argument("--gt-rpm", type=float, default=8.0, help="GeckoTerminal requests per minute (default 8)")
    ap.add_argument("--max-tracked", type=int, default=MAX_TRACKED)
    a = ap.parse_args(argv)
    if a.report:
        report(a.profile, a.json)
        return 0
    if not 0 < a.gt_rpm <= 25:
        ap.error("--gt-rpm must be in (0, 25]")
    Collector(a.profile, gt_rpm=a.gt_rpm, max_tracked=a.max_tracked).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
