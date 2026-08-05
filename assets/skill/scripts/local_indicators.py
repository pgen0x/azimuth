#!/usr/bin/env python3
import urllib.request
import json
import math
import os
import re
import subprocess
import time

def _cache_key(network, pool_address, preset, timeframe, side):
    # Solana keeps its historical prefix so existing cache entries stay valid;
    # other networks (e.g. "robinhood") get their own namespace.
    prefix = "sol:dlmm:indicators" if network == "solana" else f"{network}:indicators"
    return f"{prefix}:{pool_address}:{preset}:{timeframe}:{side}"

def get_cached_indicator(pool_address, preset, timeframe, side, network="solana"):
    """
    Checks Redis for a cached indicator calculation result.
    Returns True, False, or None (if no cache exists).
    """
    key = _cache_key(network, pool_address, preset, timeframe, side)
    try:
        res = subprocess.run(f"redis-cli get \"{key}\"", shell=True, capture_output=True, text=True, timeout=5)
        out = res.stdout.strip()
        if not out or out == "(nil)":
            return None
        if out.lower() == "true":
            return True
        if out.lower() == "false":
            return False
    except Exception as e:
        print(f"Warning: Failed to read indicator cache: {e}")
    return None

def set_cached_indicator(pool_address, preset, timeframe, side, confirmed, ttl=270, network="solana"):
    """
    Saves the calculated indicator result to Redis with a TTL.
    """
    key = _cache_key(network, pool_address, preset, timeframe, side)
    confirmed_str = "true" if confirmed else "false"
    try:
        subprocess.run(f"redis-cli setex \"{key}\" {ttl} {confirmed_str}", shell=True, capture_output=True, timeout=5)
    except Exception as e:
        print(f"Warning: Failed to set indicator cache: {e}")

# --- Robinhood Chain on-chain candle fallback ------------------------------
# GeckoTerminal's public tier is ~10 req/min PER IP — measured 2026-08-05, not
# the ~30 the code assumed — and three consumers share this box's IP (the
# discovery daemon's Fresh/Mature/Ladder enrichers, uni_monitor.py's momentum
# prefetch, and this file). The daemon logged 82 `geckoterminal status 429` in
# six hours. When the OHLCV call is the one that loses that race, an exit that
# asked for indicator confirmation gets NOTHING back, and `check_local_indicators`
# fail-opens to None — which is safe, but it means the supertrend/RSI gate is
# silently absent exactly when the venue is busiest.
#
# Robinhood Chain hands the same candles over for free, so this is the fallback:
# reconstruct OHLC from the pool's own Swap logs. ROBINHOOD ONLY, and only after
# the GeckoTerminal path has already returned nothing — Solana has no equivalent
# and its path is byte-for-byte unchanged.
ROBINHOOD_RPC_URL = os.environ.get("ROBINHOOD_RPC_URL",
                                   "https://rpc.mainnet.chain.robinhood.com")
# The chain's RPC REJECTS default user-agents. This is the same trap USER_AGENT
# in uni_monitor.py documents for GeckoTerminal, and the Jupiter audit gate hit
# it before that: "Python-urllib/3.x" never reaches the node. Do not drop it.
RPC_USER_AGENT = "azimuth-local-indicators/1.0"

# Measured 2026-08-05: 10000 blocks spanned 1001s, i.e. 0.1s/block, and a log's
# own `blockTimestamp` field comes back as "0x0" on this node — useless. So
# timestamps are derived from block HEIGHT against a single head-block read.
# Drift is bounded by the chain's own block-time stability over the window and
# is irrelevant to 15-minute buckets.
ROBINHOOD_BLOCK_SECONDS = 0.1

# eth_getLogs here has no BLOCK-RANGE cap (900k blocks of one pool's Swap topic
# returned 8343 logs in 5.0s), but it does have two other ceilings, both hit
# live while building this:
#   * "logs matched by query exceeds limit of 10000" — a busy pool. CASHCAT/WETH
#     blew the cap at 900k blocks and returned 2800 logs at 300k.
#   * "log query timed out" — a busy v4 poolId at 900k.
# Both mean the same thing (the window is too wide for this pool) and both are
# fixed the same way, so the span is retried shorter rather than given up on.
# 300_000 blocks is 8.3h = ~33 fifteen-minute candles, which still clears
# check_local_indicators' 30-candle floor; halving further would produce a
# series too short to judge, so there is no third attempt.
ROBINHOOD_LOG_SPANS = (900_000, 300_000)

# Uniswap v3 Swap, verified live on this chain:
#   Swap(address,address,int256,int256,uint160,uint128,int24)
# 3 topics (topic0 + indexed sender/recipient), 5 data words.
V3_SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
# Uniswap v4 Swap:
#   Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)
# Verified against a real payload 2026-08-05, not just derived: filtering the
# PoolManager on this topic0 + a live poolId returned 5980 logs with 3 topics and
# 6 data words, and reading word 2 as sqrtPriceX96 implies a tick matching word
# 4's own int24 tick to within +0.2..+0.8 (pure sub-tick truncation). A wrong
# topic0 could not produce that agreement.
V4_SWAP_TOPIC = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
# A v4 "pool" on this chain is a 32-byte poolId (66 chars with 0x), not a
# contract: there is nothing to filter `address` on but the singleton, so the id
# goes in topic1.
V4_POOL_MANAGER = "0x8366a39cc670b4001a1121b8f6a443a643e40951"

# Both Swap layouts put sqrtPriceX96 in the SAME data word — v3's (amount0,
# amount1, sqrtPriceX96, ...) and v4's (amount0, amount1, sqrtPriceX96, ...)
# agree for the first three — so one decoder serves both protocols.
_SQRT_PRICE_WORD = 2

# Quote-asset addresses, for the orientation decision below when a caller passes
# only a symbol. Mirrors the executors' QUOTES maps — WETH from
# uni_executor.js:68, USDG from :80, and native ETH as address(0) from
# uni_v4_executor.js:72 (a v4 PoolKey may quote in native ETH, which sorts first
# by construction). Read from there, never invented.
ROBINHOOD_QUOTES = {
    "WETH": "0x0bd7d308f8e1639fab988df18a8011f41eacad73",
    "USDG": "0x5fc5360d0400a0fd4f2af552add042d716f1d168",
    "ETH": "0x0000000000000000000000000000000000000000",
}

# 15 minutes, matching the aggregate=15 the GeckoTerminal path requests, so the
# two sources are interchangeable to every caller downstream.
CANDLE_SECONDS = 900


def _rpc(method, params, timeout=30):
    """One keyless JSON-RPC POST to Robinhood Chain. Raises on transport or RPC
    error — every caller here is inside a fail-open try."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1,
                       "method": method, "params": params}).encode()
    req = urllib.request.Request(ROBINHOOD_RPC_URL, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": RPC_USER_AGENT,
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("error"):
        err = payload["error"]
        raise RuntimeError(str(err.get("message") or err) if isinstance(err, dict) else str(err))
    return payload.get("result")


def _data_words(data):
    """Split a log's `data` hex into 32-byte words."""
    h = data[2:] if data.startswith("0x") else data
    return [h[i:i + 64] for i in range(0, len(h), 64)]


def _signed(word):
    """Two's-complement int from a 32-byte word. Swap amounts are signed (one
    side of the trade is negative), and both int128 and int256 arrive
    sign-extended to the full word, so one decoder covers v3 and v4."""
    v = int(word, 16)
    return v - (1 << 256) if v >= (1 << 255) else v


def _swap_logs(pool_address):
    """(logs, head_block_number, head_block_timestamp) for one pool's Swap
    history. Exactly ONE eth_getBlockByNumber (the head, for the timestamp
    anchor) plus one eth_getLogs — a second eth_getLogs only when the first
    window was too wide for the node (see ROBINHOOD_LOG_SPANS)."""
    head = _rpc("eth_getBlockByNumber", ["latest", False])
    head_num, head_ts = int(head["number"], 16), int(head["timestamp"], 16)

    if len(pool_address) == 66:
        flt = {"address": V4_POOL_MANAGER,
               "topics": [V4_SWAP_TOPIC, pool_address.lower()]}
    else:
        flt = {"address": pool_address.lower(), "topics": [V3_SWAP_TOPIC]}

    last_err = None
    for i, span in enumerate(ROBINHOOD_LOG_SPANS):
        flt["fromBlock"], flt["toBlock"] = hex(max(0, head_num - span)), "latest"
        try:
            return _rpc("eth_getLogs", [flt]), head_num, head_ts
        except RuntimeError as e:
            msg = str(e).lower()
            # Only a too-wide-window error is worth narrowing. Anything else
            # (a malformed filter, a node fault) would fail identically at any
            # span, and retrying it just spends another request.
            if not ("exceeds" in msg or "limit" in msg or "timed out" in msg):
                raise
            last_err = e
            if i + 1 < len(ROBINHOOD_LOG_SPANS):
                # The node rate-limits too (HTTP 429 on back-to-back calls),
                # and this retry follows immediately on a failure. Space it.
                time.sleep(2.0)
    raise RuntimeError(f"swap logs too dense for every span: {last_err}")


def fetch_onchain_candles(pool_address, token_address=None,
                          quote_address=None, quote_symbol=None):
    """15-minute OHLCV candles rebuilt from Robinhood Chain's own Swap logs, in
    the SAME shape fetch_ohlcv_candles returns ([unix_seconds, o, h, l, c, v],
    oldest-first) so nothing downstream can tell the two sources apart.

    Returns [] on any failure, which is the caller's existing "no data" value —
    the fail-open branch in check_local_indicators is untouched.

    PRICE: price = (sqrtPriceX96 / 2**96)**2, which is token1 per token0 in RAW
    base units. Token decimals are deliberately NOT applied: RSI, ATR and
    Supertrend are all scale-invariant — every one of them reads only
    differences and ratios of the series — so a constant factor cannot move a
    verdict. Undecimalled is therefore not an approximation here, it is the same
    answer with less to get wrong.

    ORIENTATION, however, is NOT free. An inverted series turns a downtrend into
    a buy signal — the one error in this function that costs money rather than
    precision. Both v3 (PoolKey/token0-token1) and v4 (currency0 < currency1)
    sort the pair by ADDRESS as bytes, so the raw price is always "token1 per
    token0" and which of base/quote is which follows from comparing their
    addresses numerically:

        base  < quote  ->  base is token0, so price is quote-per-base already.
        base  > quote  ->  base is token1, so price is base-per-quote; invert.

    That is why this needs the ADDRESSES and not the symbols: `quote_symbol`
    only resolves through ROBINHOOD_QUOTES as a fallback. Native-ETH-quoted v4
    pools (currency0 == address(0)) fall out correctly for free, since address
    zero sorts below every token.
    """
    quote = quote_address or ROBINHOOD_QUOTES.get((quote_symbol or "").upper()) or ""
    base = token_address or ""
    if not (base.startswith("0x") and quote.startswith("0x")):
        # No orientation, no candles. Guessing the direction is strictly worse
        # than the no-data path, which merely skips the gate.
        return []
    invert = int(base, 16) > int(quote, 16)

    logs, head_num, head_ts = _swap_logs(pool_address)
    if not logs:
        return []

    # Volume is reported on the QUOTE side (raw base units), the one leg that is
    # comparable across pools. Nothing downstream reads index 5 — the indicators
    # use highs/lows/closes only — so this is for operators reading a dump.
    quote_word = 1 if invert else 0

    trades = []
    for lg in logs:
        w = _data_words(lg.get("data") or "")
        if len(w) <= _SQRT_PRICE_WORD:
            continue
        sqrt_price = int(w[_SQRT_PRICE_WORD], 16)
        if sqrt_price <= 0:
            continue
        price = (sqrt_price / 2 ** 96) ** 2
        if invert:
            if price == 0:
                continue
            price = 1.0 / price
        block = int(lg["blockNumber"], 16)
        # Height-derived, because this node returns blockTimestamp "0x0".
        ts = head_ts - (head_num - block) * ROBINHOOD_BLOCK_SECONDS
        trades.append((ts, price, abs(_signed(w[quote_word])) if len(w) > quote_word else 0))
    if not trades:
        return []

    # Logs arrive in chain order already, but sort rather than trust it: one
    # mis-ordered pair would fabricate a wick in the bucket it lands in.
    trades.sort(key=lambda t: t[0])

    buckets = {}
    for ts, price, vol in trades:
        b = int(ts) // CANDLE_SECONDS
        c = buckets.get(b)
        if c is None:
            buckets[b] = [price, price, price, price, float(vol)]
        else:
            c[1] = max(c[1], price)
            c[2] = min(c[2], price)
            c[3] = price
            c[4] += float(vol)

    # Walk EVERY bucket from the first trade to the head, not just the ones that
    # traded: a 15-minute window with no swaps is a FLAT candle, not a gap. ATR
    # and Supertrend are path-dependent — they carry state forward candle by
    # candle — so a series that silently skipped quiet windows would drift out
    # of step with the Go port in internal/robinhood/indicators.go reading the
    # same pool, and the two would disagree about the same market.
    first_bucket = int(trades[0][0]) // CANDLE_SECONDS
    last_bucket = int(head_ts) // CANDLE_SECONDS
    out, prev_close = [], None
    for b in range(first_bucket, last_bucket + 1):
        c = buckets.get(b)
        if c is None:
            if prev_close is None:
                continue    # nothing has traded yet; there is no price to carry
            out.append([b * CANDLE_SECONDS, prev_close, prev_close,
                        prev_close, prev_close, 0.0])
        else:
            out.append([b * CANDLE_SECONDS, c[0], c[1], c[2], c[3], c[4]])
            prev_close = c[3]
    return out


def fetch_ohlcv_candles(pool_address, timeframe, token_address=None, network="solana",
                        quote_address=None, quote_symbol=None):
    """
    Fetches raw OHLCV candles from GeckoTerminal API.
    Supports retries with backoff, and falls back to token address endpoint if pool address fails.
    network: GeckoTerminal network slug ("solana", "robinhood", ...).

    On "robinhood" ONLY, a GeckoTerminal miss falls through to the chain's own
    Swap logs (fetch_onchain_candles) — see the block above for why. Solana has
    no such source and keeps the exact pre-existing behaviour: GT or nothing.
    quote_address/quote_symbol are used solely to orient that on-chain series.
    """
    # Map timeframe to minutes / aggregate candle size
    tf_path = "minute"
    aggregate = 15
    
    clean_tf = str(timeframe).lower().strip()
    if clean_tf in ["5m", "30m"]:
        if clean_tf == "5m":
            aggregate = 5
        else:
            aggregate = 15 # aggregate=15 is supported, aggregate=30 falls back to 15-min aggregate or similar
    else:
        aggregate = 15 # default to 15-min aggregate for 1h/2h/4h/12h/24h
        
    urls = []
    # 1. Primary path: pool address
    urls.append((f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{tf_path}?aggregate={aggregate}", "pool"))
    # 2. Fallback path: token address (if provided; never the quote asset —
    # wrapped SOL on Solana, since its token-level candles are not the pool's)
    if token_address and token_address != "So11111111111111111111111111111111111111112":
        urls.append((f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{token_address}/ohlcv/{tf_path}?aggregate={aggregate}", "token"))
        
    for url, path_type in urls:
        retries = 3
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json;version=20230203"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                    ohlcv_data = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
                    if ohlcv_data:
                        # Success
                        reversed_list = list(ohlcv_data)
                        reversed_list.reverse()
                        return reversed_list
            except Exception as e:
                # Handle rate limit (429) or other temporary issues
                status_code = getattr(e, "code", None)
                print(f"Warning: GeckoTerminal {path_type} OHLCV fetch failed (attempt {attempt+1}/{retries}): {e}")
                if status_code == 429:
                    print("Rate limit hit (429). Waiting 2 seconds before retry...")
                    time.sleep(2)
                elif status_code == 404 and path_type == "pool":
                    print("Pool address not indexed (404). Falling back to token address endpoint.")
                    break
                else:
                    time.sleep(1)

    # Every GeckoTerminal path is exhausted. On Robinhood the chain itself still
    # has the trades — one eth_getLogs against a keyless RPC that nothing else on
    # this box is competing for. Wrapped whole: a fallback that could raise would
    # turn a skipped indicator check into a crashed monitor tick, and this file
    # runs every ~60s against real open positions.
    if network == "robinhood":
        try:
            candles = fetch_onchain_candles(pool_address,
                                            token_address=token_address,
                                            quote_address=quote_address,
                                            quote_symbol=quote_symbol)
            if candles:
                print(f"📈 GeckoTerminal empty — rebuilt {len(candles)} candles "
                      f"from Robinhood Chain Swap logs for {pool_address[:10]}")
                return candles
        except Exception as e:
            print(f"Warning: on-chain candle fallback failed: {e}")

    return []

def calculate_rsi(closes, period=2):
    """
    Calculates Relative Strength Index (RSI) using Wilder's smoothing.
    """
    if len(closes) < period + 1:
        return [50.0] * len(closes)
        
    rsi_list = [50.0] * len(closes)
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))
            
    # Initial average gain and loss
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        rs = 100.0
    else:
        rs = avg_gain / avg_loss
    rsi_list[period] = 100.0 - (100.0 / (1.0 + rs))
    
    for i in range(period + 1, len(closes)):
        gain = gains[i-1]
        loss = losses[i-1]
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rs = 100.0
        else:
            rs = avg_gain / avg_loss
            
        rsi_list[i] = 100.0 - (100.0 / (1.0 + rs))
        
    return rsi_list

def calculate_sma(values, period):
    """
    Calculates Simple Moving Average (SMA).
    """
    if len(values) < period:
        return [sum(values)/len(values) if len(values) > 0 else 0.0] * len(values)
        
    sma = [0.0] * len(values)
    for i in range(len(values)):
        if i < period - 1:
            sma[i] = sum(values[:i+1]) / (i+1)
        else:
            sma[i] = sum(values[i - period + 1 : i + 1]) / period
    return sma

def calculate_standard_deviation(values, sma, period):
    """
    Calculates standard deviation of values over period.
    """
    std = [0.0] * len(values)
    for i in range(len(values)):
        if i < period - 1:
            std[i] = 0.0
        else:
            window = values[i - period + 1 : i + 1]
            mean = sma[i]
            variance = sum((x - mean)**2 for x in window) / period
            std[i] = math.sqrt(variance)
    return std

def calculate_bollinger_bands(closes, period=20, num_std=2):
    """
    Calculates upper, middle (SMA), and lower Bollinger Bands.
    """
    sma = calculate_sma(closes, period)
    std = calculate_standard_deviation(closes, sma, period)
    
    lower = [0.0] * len(closes)
    upper = [0.0] * len(closes)
    
    for i in range(len(closes)):
        lower[i] = sma[i] - (num_std * std[i])
        upper[i] = sma[i] + (num_std * std[i])
        
    return lower, sma, upper

def calculate_atr(highs, lows, closes, period=10):
    """
    Calculates Average True Range (ATR).
    """
    if len(closes) < 2:
        return [0.0] * len(closes)
        
    tr = [0.0] * len(closes)
    tr[0] = highs[0] - lows[0]
    
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        c_prev = closes[i-1]
        tr[i] = max(h - l, abs(h - c_prev), abs(l - c_prev))
        
    # ATR is Wilder's MA of True Range
    atr = [0.0] * len(closes)
    atr[0] = tr[0]
    
    if len(closes) < period:
        return calculate_sma(tr, len(closes))
        
    # Initial SMA of True Range
    atr[period - 1] = sum(tr[:period]) / period
    for i in range(period, len(closes)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
        
    # Fill in index prior to period
    for i in range(period - 1):
        atr[i] = sum(tr[:i+1]) / (i+1)
        
    return atr

def calculate_supertrend(highs, lows, closes, atr_period=10, multiplier=3.0):
    """
    Calculates Supertrend indicator value, direction, and trend changes.
    """
    n = len(closes)
    if n < atr_period:
        return [0.0] * n, ["bullish"] * n, [False] * n, [False] * n
        
    atr = calculate_atr(highs, lows, closes, atr_period)
    
    basic_upper = [0.0] * n
    basic_lower = [0.0] * n
    
    for i in range(n):
        hl2 = (highs[i] + lows[i]) / 2.0
        basic_upper[i] = hl2 + (multiplier * atr[i])
        basic_lower[i] = hl2 - (multiplier * atr[i])
        
    final_upper = [0.0] * n
    final_lower = [0.0] * n
    trend = [1] * n # 1 for bullish, -1 for bearish
    
    final_upper[0] = basic_upper[0]
    final_lower[0] = basic_lower[0]
    
    for i in range(1, n):
        # Final Lower Band
        if basic_lower[i] > final_lower[i-1] or closes[i-1] < final_lower[i-1]:
            final_lower[i] = basic_lower[i]
        else:
            final_lower[i] = final_lower[i-1]
            
        # Final Upper Band
        if basic_upper[i] < final_upper[i-1] or closes[i-1] > final_upper[i-1]:
            final_upper[i] = basic_upper[i]
        else:
            final_upper[i] = final_upper[i-1]
            
        # Direction
        if closes[i] > final_upper[i-1]:
            trend[i] = 1
        elif closes[i] < final_lower[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
            if trend[i] == 1 and final_lower[i] < final_lower[i-1]:
                final_lower[i] = final_lower[i-1]
            if trend[i] == -1 and final_upper[i] > final_upper[i-1]:
                final_upper[i] = final_upper[i-1]
                
    supertrend_vals = [0.0] * n
    supertrend_dirs = ["bullish"] * n
    break_ups = [False] * n
    break_downs = [False] * n
    
    for i in range(n):
        supertrend_vals[i] = final_lower[i] if trend[i] == 1 else final_upper[i]
        supertrend_dirs[i] = "bullish" if trend[i] == 1 else "bearish"
        if i > 0:
            break_ups[i] = (trend[i] == 1 and trend[i-1] == -1)
            break_downs[i] = (trend[i] == -1 and trend[i-1] == 1)
            
    return supertrend_vals, supertrend_dirs, break_ups, break_downs

def calculate_fibonacci(highs, lows):
    """
    Calculates Fibonacci Retracement Levels.
    """
    if not highs or not lows:
        return {"0.500": 0.0, "0.618": 0.0, "0.786": 0.0}
    max_high = max(highs)
    min_low = min(lows)
    diff = max_high - min_low
    return {
        "0.500": max_high - 0.500 * diff,
        "0.618": max_high - 0.618 * diff,
        "0.786": max_high - 0.786 * diff
    }

def check_local_indicators(pool_address, base_mint, side, preset, timeframe, network="solana",
                           quote_address=None, quote_symbol=None):
    """
    Executes timing checks using indicators calculated locally from GeckoTerminal candles.
    Checks Redis cache first. Falls back gracefully on failure.
    network: GeckoTerminal network slug ("solana", "robinhood", ...).

    quote_address/quote_symbol are Robinhood-only and OPTIONAL: they orient the
    on-chain candle fallback (see fetch_onchain_candles) and are ignored on every
    other network. Keyword-only with defaults so the three Solana call sites —
    dlmm_pipeline.py:1332/:1351 and dlmm_monitor.py:1541, all five positional
    args — keep working untouched. Omit them on Robinhood and the fallback simply
    declines rather than guessing a direction.
    """
    label = (base_mint or pool_address)[:8]
    # Exit checks never use cache — trailing TP fires every 20s and needs fresh data.
    # A stale cached REJECTED blocks trailing exits during reversals for up to 4.5min.
    # Entry checks cache for 270s (deploy happens once; spam prevention is worth it).
    if side == "entry":
        cached_val = get_cached_indicator(pool_address, preset, timeframe, side, network=network)
        if cached_val is not None:
            print(f"📊 Indicator timing check for {label} ({preset}) retrieved from Redis cache: {'🟢 CONFIRMED' if cached_val else '🔴 REJECTED'}")
            return cached_val

    print(f"📊 Running local indicators check for pool {pool_address[:8]} ({preset})")

    # 2. Fetch Candles
    candles = fetch_ohlcv_candles(pool_address, timeframe, token_address=base_mint,
                                  network=network, quote_address=quote_address,
                                  quote_symbol=quote_symbol)
    if not candles:
        print("Warning: GeckoTerminal returned empty candles — data unavailable, indicator skipped (fail-open: None).")
        return None

    if len(candles) < 30:
        print(f"Warning: Not enough candle history ({len(candles)} candles < 30) — data unavailable, indicator skipped (fail-open: None).")
        return None
        
    # Extract values
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    closes = [float(c[4]) for c in candles]
    
    # Calculate indicators
    rsi_list = calculate_rsi(closes, period=7)
    bb_lower, bb_middle, bb_upper = calculate_bollinger_bands(closes, period=20, num_std=2)
    st_vals, st_dirs, st_break_ups, st_break_downs = calculate_supertrend(highs, lows, closes, atr_period=10, multiplier=3.0)
    fibonacci = calculate_fibonacci(highs, lows)
    
    # Latest candle index
    i = len(closes) - 1
    
    close = closes[i]
    prev_close = closes[i-1] if i > 0 else close
    rsi = rsi_list[i]
    lower_band = bb_lower[i]
    upper_band = bb_upper[i]
    supertrend_val = st_vals[i]
    supertrend_dir = st_dirs[i]
    supertrend_break_up = st_break_ups[i]
    supertrend_break_down = st_break_downs[i]
    
    fib50 = fibonacci.get("0.500")
    fib618 = fibonacci.get("0.618")
    fib786 = fibonacci.get("0.786")
    
    def crossed_up(level):
        if level is None or close is None or prev_close is None:
            return False
        return prev_close < level and close >= level
        
    def crossed_down(level):
        if level is None or close is None or prev_close is None:
            return False
        return prev_close > level and close <= level

    # Evaluate presets
    oversold = 30
    overbought = 80
    confirmed = False
    
    if preset == "supertrend_break":
        if side == "entry":
            confirmed = supertrend_break_up or (supertrend_dir == "bullish" and close >= supertrend_val)
        else:
            confirmed = supertrend_break_down or (supertrend_dir == "bearish" and close <= supertrend_val)
            
    elif preset == "rsi_reversal":
        if side == "entry":
            confirmed = rsi is not None and rsi <= oversold
        else:
            confirmed = rsi is not None and rsi >= overbought
            
    elif preset == "bollinger_reversion":
        if side == "entry":
            confirmed = close <= lower_band
        else:
            confirmed = close >= upper_band
            
    elif preset == "rsi_plus_supertrend":
        if side == "entry":
            confirmed = (rsi is not None and rsi <= oversold) and (supertrend_break_up or supertrend_dir == "bullish")
        else:
            confirmed = (rsi is not None and rsi >= overbought) and (supertrend_break_down or supertrend_dir == "bearish")
            
    elif preset == "supertrend_or_rsi":
        if side == "entry":
            confirmed = supertrend_break_up or (supertrend_dir == "bullish" and close >= supertrend_val) or (rsi is not None and rsi <= oversold)
        else:
            confirmed = supertrend_break_down or (supertrend_dir == "bearish" and close <= supertrend_val) or (rsi is not None and rsi >= overbought)
            
    elif preset == "bb_plus_rsi":
        if side == "entry":
            confirmed = close <= lower_band and rsi is not None and rsi <= oversold
        else:
            confirmed = close >= upper_band and rsi is not None and rsi >= overbought
            
    elif preset == "fibo_reclaim":
        if side == "entry":
            confirmed = crossed_up(fib618) or crossed_up(fib50) or crossed_up(fib786)
        else:
            confirmed = crossed_up(fib618) or crossed_up(fib50)
            
    elif preset == "fibo_reject":
        if side == "entry":
            confirmed = crossed_down(fib618) or crossed_down(fib50)
        else:
            confirmed = crossed_down(fib618) or crossed_down(fib50) or crossed_down(fib786)
            
    print(f"📊 Local Timing Check for {label} ({preset}): {'🟢 CONFIRMED' if confirmed else '🔴 REJECTED'} (Close: {close:.8f}, RSI: {rsi:.1f}, ST: {supertrend_dir})")

    # 3. Write to Cache (entry only — exit checks must stay uncached)
    if side == "entry":
        set_cached_indicator(pool_address, preset, timeframe, side, confirmed, network=network)
    
    return confirmed

if __name__ == "__main__":
    # Test execution
    test_pool = "AeUfFU6LU159YSBQvhLbXmh5bW2BqCgAFi5zUSQMnUc7" # CHANCE-SOL
    test_mint = "JCKwsT8UAbygnFkZ7u3amDUM7BXRtwUhCsHQv2khpump" # CHANCE
    check_local_indicators(test_pool, test_mint, "entry", "supertrend_or_rsi", "24h")
