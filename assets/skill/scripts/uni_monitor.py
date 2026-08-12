#!/usr/bin/env python3
"""uni_monitor.py — Robinhood Chain (Uniswap v3 + v4) position monitor.

EVM sibling of dlmm_monitor.py. One-shot scan (run on a loop by
uni_monitor_loop.sh): reads open positions from BOTH executors — v3 via
uni_executor.js (NonfungiblePositionManager) and v4 via uni_v4_executor.js
(the v4 PositionManager; skipped when the script is absent) — and applies the
SAME exit rulebook the Solana monitor uses — hard SL/TP, trailing
profit-ratchet, fast-out velocity exit, sustained-downtrend exit, and
out-of-range timeout — closing through `UNI_CLOSE_AUTH=1 <executor> close`
when a rule trips.

This is the ONLY authorized closer for the venue (both executors' close
commands refuse to run without UNI_CLOSE_AUTH=1 or --force), mirroring the
Solana monitor's DLMM_CLOSE_AUTH contract. PnL is quote-denominated: WETH on
v3, the pool's own quote asset on v4 (WETH, native ETH, or USDG — the state
output's `quoteSymbol` says which). The rulebook is percentages, so the
thresholds are unit-agnostic and shared across protocols.

DRY_RUN=true still tracks peaks and prints decisions, but simulates closes.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

from local_indicators import check_local_indicators

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
# (protocol, executor path) pairs, monitored in order. v4 rides the same tick
# only when its script is deployed — an absent file is pre-Phase-7, not an
# error. v3 state keys stay bare tokenIds (the live state file predates v4);
# v4 keys are namespaced "v4:<tokenId>" because the two PositionManagers mint
# independent, colliding tokenId sequences.
EXECUTORS = [("v3", os.path.join(SCRIPT_DIR, "uni_executor.js"))]
_V4_EXECUTOR = os.path.join(SCRIPT_DIR, "uni_v4_executor.js")
if os.path.exists(_V4_EXECUTOR):
    EXECUTORS.append(("v4", _V4_EXECUTOR))
STATE_PATH = os.path.join(PROFILE_DIR, "memories", "uni_monitor_state.json")
CLOSES_PATH = os.path.join(PROFILE_DIR, "memories", "uni_closes.jsonl")
# Momentum cache, shared ACROSS ticks. The loop runs this script one-shot, so a
# process-local dict dies every tick and the GT request repeats at whatever the
# loop's cadence is. Persisting it decouples the two: the on-chain reads (PnL,
# range, rung fills) tick as fast as the loop wants, while the GT request stays
# on MOMENTUM_TTL. That is what lets a 20s loop cost the GT budget a 60s loop
# did — see uni_monitor_loop.sh.
MOMENTUM_CACHE_PATH = os.path.join(PROFILE_DIR, "memories", "uni_momentum_cache.json")

DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"
# Report-only: read positions + state + momentum, compute the decision label for
# each, print a status card + MONITOR_REPORT JSON, and NEVER close or mutate the
# persisted state file. This is the mode the Hermes reporting cron runs — the
# systemd loop (azimuth-rh-monitor.service) owns the actual exits, so the cron is a
# read-only mirror ("rules not cadence are the lever"). A report tick must never
# race the loop's on-chain writes.
REPORT_ONLY = "--report-only" in sys.argv

# Exit thresholds — percentages, so identical to the Solana monitor's
# (dlmm_monitor.py). "Same like solana" per the operator; recalibrate from the
# venue's own close journal once it has live outcomes.
STOP_LOSS_PCT = float(os.environ.get("UNI_STOP_LOSS_PCT", "-25.0"))
TAKE_PROFIT_PCT = float(os.environ.get("UNI_TAKE_PROFIT_PCT", "50.0"))
TRAILING_TRIGGER_PCT = float(os.environ.get("UNI_TRAILING_TRIGGER_PCT", "5.0"))
TRAILING_DROP_PCT = float(os.environ.get("UNI_TRAILING_DROP_PCT", "1.5"))
TRAILING_MIN_LOCK_PCT = 0.3        # round-trip swap cost floor for a "profit" exit
EMERGENCY_SL_BUFFER_PCT = 3.0      # below SL-buffer, close bypasses the age grace
FAST_EXIT_M5_PCT = -3.0            # armed trailing + this 5m dump -> close now
DOWNTREND_1H_PCT = -5.0            # sustained-downtrend exit (both must trip)
DOWNTREND_PNL_PCT = -5.0
MAX_OOR_MINUTES = 30.0             # out-of-range this long -> close (fee-dead)
MIN_AGE_MIN_BEFORE_SL = 5.0        # grace so a fresh mint's settling isn't an SL

# Consecutive failed close attempts after which a position is declared
# UNCLOSABLE and skipped for the rest of this process's life.
#
# Some closes can never succeed. On 2026-08-09 position #634693 (BLINK, a pool
# the security gate convicted as a honeypot 20 minutes after the mint) failed
# `collect` with `TF` — the token blocks transfers, so the withdraw can never
# settle — and the loop retried it every 40s for 75 minutes: 78 attempts, 78
# journal rows, and a share of every tick. Retrying is right for the transient
# case (a reverted tx, a stale nonce, a busy RPC) and useless for the permanent
# one, and nothing in the error text separates them — so the cap is the
# separator: a few retries cover the transient, the cap covers the rest.
#
# The position stays open on-chain; this only stops the monitor from spending
# every tick on it. Recovery is manual, which is why tripping the cap alerts
# once instead of failing silently.
MAX_CLOSE_FAILURES = int(os.environ.get("UNI_MAX_CLOSE_FAILURES", "5"))

# --- ask side: the second leg of a round trip -------------------------------
# A turnover bid that fills is holding the token. Until 2026-08-09 that bag was
# market-sold on the spot, which cost -4.9% per fill and WAS this venue's entire
# deficit: the 13 untouched rungs earned +0.00039 ETH between them while 5 fills
# lost -0.00231. Breakeven needed a fill rate under 6.1%; the measured rate was
# 27.8%. Tuning the bid cannot close a 4.6x gap, because moving the rung away
# from spot to fill less also earns less — the two move together.
#
# So the fill stops being an exit and becomes the halfway point: re-list the bag
# as a resting ASK above spot (`token_above`) and sell it into the bounce,
# earning the fee tier a second time on the way out. A wallet running this shape
# on the same chain fills MORE often than we do (34%) and still reports a high
# winrate, because a fill there is inventory to be cycled rather than a loss to
# be booked.
ASK_STRATEGY = "token_above"

# The bag stop. An ask rung has no natural floor — if the token keeps falling it
# just sits there holding it, which is exactly how `balanced_tight` lost
# -15.04%/trade. The instant sell we are replacing WAS a stop-loss, so the ask
# must carry an explicit one or the change trades a small certain loss for an
# unbounded one.
#
# Measured from the ask position's OWN entry, which both executors mark at the
# mint tick — i.e. the price the bid was filled at, not the price the bid was
# placed at. -8% matches UNI_LADDER_FILL_HARD_PCT, the floor the postponement
# log showed fills crossing anyway.
ASK_BAG_STOP_PCT = float(os.environ.get("UNI_ASK_BAG_STOP_PCT", "-8.0"))

# Re-list is off by default. It is a live-funds behaviour change on a venue with
# a losing record, so it ships dark and the operator turns it on.
ASK_RELIST_ENABLED = os.environ.get("UNI_ASK_RELIST", "").lower() == "true"

# --- turnover (churn) mode -------------------------------------------------
# Port of Solana turnover's exit half (dlmm_monitor.py). The mode is paid per
# crossing, so its rulebook differs from every other strategy here in ONE
# structural way: leaving the band is not an exit, it is a RE-CENTER. Close,
# re-mint at the new price, keep earning. That loop is the leg this venue never
# had, and its absence is what killed the old two-sided balanced_tight at
# -15.04%/trade — uni_executor.js records positions closed by the 30m OOR
# timeout half an hour after minting. A churn strategy with no churn realizes
# every drift as a loss instead of collecting the fee on the way back.
#
# The SHAPE is one-sided (2026-08-07, operator correction). Solana's
# select_batch_strategy() ends in an unconditional `return "sol_bidask"`: every
# mode there, turnover included, holds zero token at entry. balanced_tight
# pre-swapped half the commit into the memecoin, which is the exposure this
# venue has been losing money on, and it is not what the churn loop needed.
#
# One v3/v4 constraint the Solana port cannot carry over, and it is why this
# mode does NOT get a 2-minute OOR fuse: DLMM lets a one-sided position include
# the active bin (sol_bidask sets upper_bin = active_bin), so it is single-sided
# AND earning at mint. Uniswap cannot — one-sided quote needs the band entirely
# on one side of spot, and a straddling range computes
# liquidity = min(L(amount), L(0)) = 0. So a weth_below rung ALWAYS rests out of
# range, and an OOR fuse would close and re-mint it every two minutes forever.
# Drift and fee-death replace it; see turnover_decide.
TURNOVER_STRATEGY = "weth_below"

# Drift, in ticks, before the rung is re-pinned — the turnover twin of
# LADDER_STALE_TICKS below, and half the rung width for the same reason a
# ladder's is one full rung width: a wall is judged stale when spot has cleared
# the depth it was willing to buy, and a single rung has half a wall's patience
# because re-pinning it costs one mint, not five. Keep each entry at half its
# UNI_TURNOVER_RUNG_TICKS* twin in uni_ladder.js — the executor mints the width,
# this judges drift against it, and the pair only means something together.
TURNOVER_STALE_TICKS = {
    "WETH": float(os.environ.get("UNI_TURNOVER_STALE_TICKS", "300")),
    "USDG": float(os.environ.get("UNI_TURNOVER_STALE_TICKS_USDG", "60")),
}

# A fill past this closes without waiting for indicator confirmation, exactly as
# LADDER_FILL_HARD_PCT does for a rung — same rule, same number by default,
# separate knob because a re-pinning single rung and a five-rung wall can want
# different patience once there is live data to separate them.
TURNOVER_FILL_HARD_PCT = float(os.environ.get("UNI_TURNOVER_FILL_HARD_PCT",
                                              os.environ.get("UNI_LADDER_FILL_HARD_PCT", "-8.0")))

# Re-center circuit breaker, both halves ported from dlmm_monitor.py. The
# cumulative one is primary: re-centering only pays if the crossings cover the
# gas and the spread, and a pool that keeps drifting one way bleeds a little on
# every cycle. Once 24h of realized re-center PnL in a pool drops below the
# floor, that pool stops re-centering and takes a normal exit. The count cap is
# the backstop against a pathological oscillation burning gas.
#
# The floor is in the position's QUOTE asset, so it is 0.004 WETH for a
# WETH-quoted pool — this mode is WETH-pinned (robinhood.Turnover), so there is
# no unit ambiguity to resolve here the way there is in sizing.
TURNOVER_CB_LOSS_QUOTE = float(os.environ.get("UNI_TURNOVER_CB_LOSS_QUOTE", "-0.004"))
TURNOVER_MAX_RECENTERS_24H = int(os.environ.get("UNI_TURNOVER_MAX_RECENTERS", "20"))

# Fee compounding: claim while in range and let the proceeds fund the next
# mint. Divergence from Solana worth naming — dlmm_monitor.py compounds fees
# back INTO the live position, which on v3/v4 would need an increaseLiquidity
# path neither executor has. Here `collect` moves fees to the wallet and the
# re-center loop redeploys them within minutes, which for a strategy whose
# holding period IS minutes is the same capital recycling by another route.
# Threshold is a share of position value so it scales with size; below it the
# gas costs more than the claim recovers.
TURNOVER_COMPOUND_MIN_PCT = float(os.environ.get("UNI_TURNOVER_COMPOUND_MIN_PCT", "0.5"))

# Pre-exit indicator confirmation — the Solana monitor's supertrend timing
# check (dlmm_monitor.py step 7), applied to this venue's non-emergency exits:
# a trailing/fast-out/downtrend close is postponed while the indicators still
# read bullish (a dip, not a dump), then forced once the block ages past the
# cap. Emergency SL / hard SL / TP / OOR-timeout closes are never postponed.
INDICATORS_ENABLED = os.environ.get("UNI_INDICATORS_ENABLED", "true").lower() != "false"
INDICATORS_PRESET = os.environ.get("UNI_INDICATORS_PRESET", "supertrend_or_rsi")
MAX_INDICATOR_BLOCK_MINUTES = 60.0


# --- ladder exit rule ------------------------------------------------------
# A ladder rung is a resting one-sided QUOTE-ASSET bid parked below spot —
# WETH under a memecoin (weth_ladder) or USDG under a tokenized equity
# (usdg_ladder). Both shapes obey the same rulebook; only the tick scale
# differs, because an equity's day is a memecoin's minute. It is
# OUT OF RANGE BY DESIGN and holds no token, so almost none of the rulebook
# above applies to it: there is no entry price to stop out of, no peak to
# trail, and the fee-dead OOR timeout would close every rung 30 minutes after
# it was minted. Its exits are re-pins, not stop-losses — the reference LP's
# ladders closed with a median of ZERO fully-converted rungs, most of the wall
# coming back unfilled each time.
#
# Drift is measured against the rung's INTENDED offset, not against spot
# directly: rung k is built k widths away from the pin, so a flat tick
# threshold would call the outer rungs stale the moment they were created.
# Per quote asset, mirroring uni_executor.js's UNI_LADDER_RUNG_TICKS map — a
# stale threshold is only meaningful relative to the rung width it is judging,
# and USDG rungs are a fraction of a WETH rung's width. One absolute 1200 would
# mean a stock ladder waits for a 12% move before re-pinning, i.e. never.
# Each entry tracks its quote's UNI_LADDER_RUNG_TICKS* one-for-one — keep them
# equal when either moves (USDG went 120 -> 240 on 2026-08-05).
LADDER_STALE_TICKS = {
    "WETH": float(os.environ.get("UNI_LADDER_STALE_TICKS", "1200")),
    "USDG": float(os.environ.get("UNI_LADDER_STALE_TICKS_USDG", "240")),
}

# --- ladder fill is a WALL event ------------------------------------------
# A filled rung used to close alone, leaving the rest of the wall resting under
# a market that had just proved it can come down. That is a limit-buy order
# left under a falling knife, and the journal shows it being taken: of 11 fills
# to 2026-08-07, SIX were a repeat fill in a pool that had already filled once,
# and the repeats averaged -11.8% against -6.7% for the first fill of a wall.
# One WETH pool filled three rungs in thirty minutes — -7.6%, then -12.0%, then
# -40.6%. So the FIRST fill tears the whole wall down: the unfilled rungs are
# still pure quote asset, and closing them costs no swap and no spread.
#
# This is the venue's version of the Solana monitor's pool-scope reaction to a
# loss — there, a dump close cools the pool off; here it also has to retract the
# resting orders, because unlike a DLMM position a ladder keeps buying after the
# thesis has failed.
#
# The second half of the same lesson: a fill deep enough to be a collapse must
# not wait for indicator confirmation. Confirmation is right for a shallow fill
# (an un-filling rung reverts to WETH for free, which strictly beats crossing
# the spread twice) and wrong for a -40% one, which is what the confirm-and-wait
# path produced. Mirrors dlmm_monitor.py's emergency-SL carve-out.
LADDER_FILL_HARD_PCT = float(os.environ.get("UNI_LADDER_FILL_HARD_PCT", "-8.0"))

# --- ladder idle exit ------------------------------------------------------
# Drift and fill are both PRICE rules, so a market that stops moving disarms
# the whole ladder rulebook: a usdg_ladder minted on SPY at 16:56 ET — four
# minutes after the US cash close — sat 5.6h with drift stuck at 56 of the 120
# ticks it needed, zero rungs filled, and zero fees on all three rungs. Nothing
# was broken; no rule *could* fire, because an equity does not move 1.2%
# overnight. Dead capital that no price rule will ever release is what this
# rule releases.
#
# The test is fee productivity, not a bare timer: a rung parked out of range is
# 100% quote asset, so its quote-denominated value moves ONLY when the pool
# trades through the band. Growth below IDLE_MIN_PCT over the window means the
# wall is not being traded into — tear it down and let the scanner re-pin. Port
# of dlmm_monitor.py's fee-pace-death rule, which the ladder never inherited.
#
# Skipped while the rung is IN range: a partially-filled rung holds token, so
# its quote value also moves with price, and a dip would read as "no fees".
#
# LADDER-SCOPED, NOT RUNG-SCOPED (2026-08-05, operator-approved). A ladder's
# OUTER rungs are fee-dead BY DESIGN — rung 2 earns nothing until spot reaches
# rung 2 — so a per-rung verdict closes the far side of a wall while the near
# side is still earning, ratcheting the wall thinner every window until only
# rung 0 is left. The first working on-chain fee meter (feesQuote, landed the
# same day) made that visible on eight live usdg_ladder rungs: GME rung 0 had
# 0.002039 USDG in 214m and NVDA rung 0 0.000297 in 136m, while NVDA rungs 1-2
# and all three TSLA rungs read exactly 0 — judged per rung, five of the eight
# would have been torn out of three walls that were working as designed. That
# is the shape this file's own header block describes: the reference LP's
# ladders "closed with a median of ZERO fully-converted rungs".
#
# Rungs already share a `ladderId` so the re-pin rules can treat them as one
# wall; the idle rule now does too:
#
#   * the three meters are SUMMED over the wall (feesQuote, valueWeth, and
#     Krystal's USD fee/value pair), and the wall's age is its OLDEST rung's,
#   * ANY rung earning holds the WHOLE wall — release needs the AGGREGATE to be
#     fee-dead across the window,
#   * the window snapshot lives under `ladder:<ladderId>` in the monitor state,
#     not under each rung's tokenId: three rungs each rolling their own 90m
#     baseline makes the aggregate meaningless,
#   * and the verdict is computed ONCE per wall per tick and handed to every
#     rung, so the wall comes down whole in a single tick. Without that, the
#     first rung judged would roll the shared window and hand the rest a fresh
#     baseline, tearing the wall down one rung per window anyway.
#
# Unmeasured is never zero: a rung whose `feesQuote` is None voids the whole
# wall's chain-fee meter, and a Krystal reply missing any rung voids the wall's
# Krystal meter, because an understated sum is indistinguishable from "earned
# nothing" — the one reading that closes. Both fall through to the next meter.
#
# The `ladder:<ladderId>` key is restart-safe: the executor mints ladderId as
# `<pool>-<mintUnixTs>` and persists it in the entry journal, so it is byte-
# identical after a deploy. This is the hazard from the note below — three
# restarts on 2026-08-05 each minting a NEW state key and restarting the 90m
# window from zero — not reintroduced. Cutover cost is one window: live rungs'
# pre-existing per-tokenId idle_* snapshots cannot be merged into a wall total
# (different units), so each wall starts one fresh window. The absolute-zero
# branch is judged on AGE, not the window, so a fee-dead wall stays releasable
# across that cutover.
LADDER_IDLE_MIN_AGE_MIN = float(os.environ.get("UNI_LADDER_IDLE_MIN_AGE", "45"))
LADDER_IDLE_WINDOW_MIN = float(os.environ.get("UNI_LADDER_IDLE_WINDOW", "90"))
LADDER_IDLE_MIN_PCT = float(os.environ.get("UNI_LADDER_IDLE_MIN_PCT", "0.02"))

# --- Krystal Cloud position API (optional fee oracle) ----------------------
# Reads REAL accrued fees, which the chain does not hand over cheaply:
# NPM.positions().tokensOwed only updates on poke/burn (it reads 0 on a live
# rung no matter what it earned), and the honest alternative — static-calling
# NPM.collect — costs one call per position per tick. Krystal returns
# pending+claimed fees for the whole wallet in ONE request, which is what makes
# a fee meter affordable at a 60s cadence.
#
# STRICTLY an enrichment. Every hard-risk rule (SL/TP/trailing/OOR, and the
# ladder's fill and stale rules) stays on-chain, and a failure here falls back
# to the meters below. A third party must never sit in the kill path: an outage
# or a 429 cannot be allowed to block a stop-loss.
#
# 2026-08-05: it IS no longer the only fee meter. Krystal spent the entire
# 40h/17-close ladder soak failing — `HTTP Error 521` (Cloudflare: origin down)
# then repeated `read operation timed out` — which silently demoted every ladder
# judgement to the value-drift meter, and that meter cannot see fees at all on
# an out-of-range rung. uni_executor.js cmdState now measures uncollected fees
# on-chain (`feesQuote`) inside the state read the monitor already performs, at
# zero extra requests. Krystal is kept FIRST only because it is one request for
# the whole wallet rather than one per position; it is no longer load-bearing,
# and if the 521s persist it can be dropped outright without losing the rule.
#
# Requires KRYSTAL_API_KEY and KRYSTAL_WALLET (the public EVM address — this
# script must never see a private key). Unset either and the feature is off.
# Costs 10 API units per request; at a 60s tick that is ~14.4k units/day.
KRYSTAL_API_URL = os.environ.get("KRYSTAL_API_URL", "https://cloud-api.krystal.app/v1/positions")
KRYSTAL_API_KEY = os.environ.get("KRYSTAL_API_KEY", "")
KRYSTAL_WALLET = os.environ.get("KRYSTAL_WALLET", "")
KRYSTAL_TIMEOUT = float(os.environ.get("KRYSTAL_TIMEOUT", "10"))
ROBINHOOD_CHAIN_ID = 4663


def _krystal_usd(entries):
    """Sum a Krystal token-amount array to USD, or None if any row is
    unreadable. `balance` is a RAW integer string at the token's own
    `decimals` — USDG is 6 and WETH is 18, so dividing by a hardcoded 1e18
    would silently report a stock rung's fees as zero forever."""
    total = 0.0
    for e in entries or []:
        dec = (e.get("token") or {}).get("decimals")
        if dec is None:
            return None
        try:
            total += int(e.get("balance")) / (10 ** int(dec)) * float(e.get("price") or 0.0)
        except (TypeError, ValueError):
            return None
    return total


def fetch_krystal_positions():
    """{tokenId: {"fees_usd", "value_usd", "earning24h"}} for this wallet's
    open Robinhood positions. Returns {} on ANY failure — a missing oracle
    means the idle rule falls back to value drift, never that a rung is
    closed or held on data we do not have."""
    if not (KRYSTAL_API_KEY and KRYSTAL_WALLET):
        return {}
    url = f"{KRYSTAL_API_URL}?wallet={KRYSTAL_WALLET}&positionStatus=OPEN"
    try:
        req = urllib.request.Request(url, headers={
            "accept": "application/json",
            "KC-APIKey": KRYSTAL_API_KEY,
            "User-Agent": USER_AGENT,
        })
        with urllib.request.urlopen(req, timeout=KRYSTAL_TIMEOUT) as resp:
            rows = json.loads(resp.read())
    except Exception as e:
        print(f"monitor: krystal fetch failed ({e}) — idle rule falls back to value drift")
        return {}
    out = {}
    for r in rows if isinstance(rows, list) else []:
        # chainId is a documented filter but takes a "<name>@<id>" form this
        # chain's spelling is unconfirmed for, so filter locally instead.
        if (r.get("chain") or {}).get("id") != ROBINHOOD_CHAIN_ID:
            continue
        tid = str(r.get("tokenId") or "")
        fee = r.get("tradingFee") or {}
        pending, claimed = _krystal_usd(fee.get("pending")), _krystal_usd(fee.get("claimed"))
        if not tid or pending is None or claimed is None:
            continue
        out[tid] = {
            # pending+claimed, so a collect that moves one to the other keeps
            # the total monotonic and does not read as a fee reversal.
            "fees_usd": pending + claimed,
            "value_usd": float(r.get("currentPositionValue") or 0.0),
            "earning24h": r.get("earning24h"),
        }
    return out


# Prefix that marks a WALL's shared idle-window state, keyed by ladderId rather
# than by tokenId. Distinguishable from a position key on sight, because the
# prune at the end of main() has to treat the two differently: a position key is
# retired when its position closes, a wall key when its LAST rung does.
LADDER_WALL_PREFIX = "ladder:"


def is_ladder(s):
    """True for a ladder rung of either quote asset. Suffix match on the
    strategy name, not a fixed list — same reason `decide` matches that way: a
    new quote asset adds a strategy, and a ladder that fell through to the
    position rulebook would be closed by the fee-dead OOR timeout."""
    return str((s or {}).get("strategy") or "").endswith("_ladder")


def rung_fill_state(s, side="bid"):
    """(filled, gap) for one rung, or (None, None) when the state read has no
    ticks. `gap` is how far spot sits OUTSIDE the rung on the resting side, in
    ticks; the stale rule measures drift from it.

    Which tick direction fills the rung depends on token ordering, the same
    invariant ladderBands() mints on: the quote as token0 means a RISING tick
    makes the token cheaper, so the ladder sits above spot and fills upward.

    `side` mirrors ladderBands()'s argument, and the direction is the same
    equality-of-two-booleans: an ASK rung rests on the opposite side of spot and
    therefore fills on the opposite move. Reading an ask rung with the bid rule
    would report it filled the moment it was minted.

    Shared by ladder_decide (per rung) and ladder_walls (which needs to know
    whether ANY rung of the wall has filled) — one definition, because a wall
    breach that disagreed with the rung's own verdict would close the wall on a
    tick the filled rung then declined to close on.
    """
    tick, lo, hi = (s or {}).get("tick"), (s or {}).get("tickLower"), (s or {}).get("tickUpper")
    if tick is None or lo is None or hi is None:
        return None, None
    # quoteIs0 is the current field; wethIs0 is its pre-USDG name, still emitted
    # by the executor (and the only one an older v4 build sends).
    if (side == "bid") == bool(s.get("quoteIs0", s.get("wethIs0"))):
        return tick >= hi, lo - tick
    return tick <= lo, tick - hi


def rung_drift(s, rung_offset=0.0, side="bid"):
    """How far spot has moved AWAY from the pin this rung was laid around, in
    ticks. Negative means it moved toward the rung (or into it). None when the
    state read can answer neither way.

    Measuring from the pin rather than from the band edge is the fix for the
    2026-08-07 re-center loop. ladderBands() places the near edge one spacing off
    spot and then quantizes to the spacing, so the edge is born
    `spacing..2*spacing` away — 200-400 ticks on the 1% tier, where the pool's
    spacing is 200. TURNOVER_STALE_TICKS is 300, i.e. INSIDE that range, so any
    mint whose rounding landed above it was stale the instant it existed: same
    tick, same band, same gap, re-center, repeat. One rung did that eight times in
    ten minutes on an unchanged commit, each cycle paying gas and reporting a
    376-tick "drift" the market never made.

    `entryTick` (both executors journal it since this fix) is the exact zero.
    Where it is missing — every position minted before it — the fallback
    subtracts the WORST-CASE birth offset, 2*spacing, from the edge distance.
    Conservative on purpose: it re-centers slightly late rather than looping.

    Direction follows rung_fill_state's invariant: quote-as-token0 rests ABOVE
    spot, so it is a FALLING tick that abandons it. Signing this matters — an
    unsigned |drift| would re-center a rung that price had walked into, which is
    the one state where it is earning.
    """
    tick = (s or {}).get("tick")
    if tick is None:
        return None
    entry_tick = s.get("entryTick")
    if entry_tick is not None:
        if (side == "bid") == bool(s.get("quoteIs0", s.get("wethIs0"))):
            return float(entry_tick - tick)
        return float(tick - entry_tick)
    _, gap = rung_fill_state(s, side)
    if gap is None:
        return None
    try:
        spacing = float(s.get("tickSpacing") or 0)
    except (TypeError, ValueError):
        spacing = 0.0
    return float(gap) - rung_offset - 2.0 * spacing


def ladder_wall_key(ladder_id):
    """Monitor-state key for a wall's shared idle window. Keyed by `ladderId`
    alone: the executor mints it as `<pool>-<mintUnixTs>` and persists it in the
    entry journal, so it is globally unique AND identical after a restart, which
    is what keeps the 90m window from re-baselining on every deploy. Not
    proto-namespaced the way state_key() is, and it does not need to be now that
    BOTH executors mint ladders: the pool component is either a 20-byte v3 pool
    address or a 32-byte v4 poolId, which cannot collide, so `<pool>-<ts>` is
    unique across protocols on its own. state_key() still needs its prefix
    because NPM and posm tokenIds both start at 1."""
    return LADDER_WALL_PREFIX + str(ladder_id)


def ladder_walls(reads, krystal):
    """Group this tick's ladder rungs into WALLS by `ladderId`, summing each
    wall's idle meters. `reads` is [(tokenId, state)] over the state reads that
    SUCCEEDED this tick; `krystal` the wallet-wide fee oracle map.

    Every rung of a wall shares one pool and therefore one quote asset, so
    feesQuote and valueWeth sum in a single unit and their ratio is still a real
    fee yield (WETH or USDG). A rung missing from either fee meter voids that
    meter for the entire wall — a partial sum reads as "earned nothing", which
    is the reading that closes.
    """
    walls = {}
    for tid, s in reads:
        if not is_ladder(s):
            continue
        lid = s.get("ladderId")
        if not lid:
            # No wall to join (a pre-ladderId mint, or a build that does not
            # echo it): this rung keeps judging itself, unchanged.
            continue
        w = walls.setdefault(str(lid), {
            "rungs": [], "ages": [], "in_range": False,
            "fees": 0.0, "fees_ok": True,
            "value": 0.0, "value_ok": True,
            "kry_fees": 0.0, "kry_value": 0.0, "kry_ok": True,
            "breached": None,
        })
        w["rungs"].append(str(tid))
        # A filled rung breaches the WHOLE wall — see the LADDER_FILL_HARD_PCT
        # note. Records the lowest-indexed filled rung because that is the one
        # nearest spot, i.e. the one the reason line should name. A rung whose
        # state read carried no ticks contributes nothing either way: unknown is
        # not a breach, and the rung's own ladder_decide holds it for the same
        # reason.
        filled, _ = rung_fill_state(s)
        if filled:
            r = s.get("rung") or 0
            if w["breached"] is None or r < w["breached"]:
                w["breached"] = r
        if s.get("ageMin") is not None:
            w["ages"].append(float(s["ageMin"]))
        if s.get("inRange"):
            # ANY rung in range makes the wall's summed value price-sensitive,
            # so the value meter's mid-conversion carve-out applies to the whole
            # wall — see the `value` meter note in ladder_idle_reason.
            w["in_range"] = True
        fq = s.get("feesQuote")
        if fq is None:
            w["fees_ok"] = False        # unmeasured — never read as zero
        else:
            w["fees"] += float(fq)
        vq = s.get("valueWeth")         # quote units despite the name
        if vq is None:
            w["value_ok"] = False
        else:
            w["value"] += float(vq)
        k = krystal.get(str(tid))
        if not k or k.get("fees_usd") is None:
            w["kry_ok"] = False
        else:
            w["kry_fees"] += float(k["fees_usd"])
            w["kry_value"] += float(k.get("value_usd") or 0.0)
    for w in walls.values():
        # Shaped like one synthetic rung on purpose: ladder_idle_reason reads
        # the wall through the exact same three meters, so the rule's logic and
        # its meter preference order did not have to be duplicated or reordered.
        w["state"] = {
            "feesQuote": w["fees"] if w["fees_ok"] else None,
            "valueWeth": w["value"] if w["value_ok"] else None,
            "inRange": w["in_range"],
        }
        w["kry"] = ({"fees_usd": w["kry_fees"], "value_usd": w["kry_value"]}
                    if w["kry_ok"] else None)
        # OLDEST rung. The rungs are minted in one NPM.multicall so their ages
        # should be equal to the second, but don't assume it — a wall must not
        # read young (and so escape the age gate) because of one rung.
        w["age_min"] = max(w["ages"]) if w["ages"] else None
    return walls


def wall_of(s, verdicts):
    """This rung's precomputed wall verdict, or None when it belongs to no wall
    (non-ladder position, or a rung with no `ladderId`) — None routes back to
    the original per-position judgement."""
    lid = (s or {}).get("ladderId")
    return verdicts.get(str(lid)) if lid else None


def _idle_window(ps, now, kind, level, basis=None, label="ladder idle"):
    """Snapshot-and-compare a monotonic `level` over LADDER_IDLE_WINDOW_MIN,
    judged against `basis` (defaults to the snapshot itself, i.e. relative
    growth). Returns a close reason, or None to hold — rolling the window
    forward in `ps` as a side effect.

    `ps` is the WALL's state dict for a laddered rung (ladder_wall_key), so one
    window covers the whole wall; only a rung with no ladderId still snapshots
    into its own position state.

    `label` prefixes the reason. Turnover passes its own so its verdict reads as
    a re-center rather than a teardown: the reason string is what the close path
    routes on, and the two modes react to fee-death differently — a ladder is
    torn down, a turnover rung is re-pinned."""
    skey, tkey = f"idle_{kind}_snap", f"idle_{kind}_at"
    snap, snap_at = ps.get(skey), ps.get(tkey)
    if snap is None or snap_at is None or level < float(snap):
        # First sighting, or the level fell — either way the baseline is void.
        ps[skey], ps[tkey] = level, now
        return None
    window_min = (now - float(snap_at)) / 60.0
    if window_min < LADDER_IDLE_WINDOW_MIN:
        return None
    denom = float(basis) if basis is not None else float(snap)
    if denom <= 0:
        return None
    growth_pct = (level - float(snap)) / denom * 100.0
    if growth_pct >= LADDER_IDLE_MIN_PCT:
        ps[skey], ps[tkey] = level, now
        return None
    return (f"{label}: +{growth_pct:.4f}% {kind} in {window_min:.0f}m "
            f"(< {LADDER_IDLE_MIN_PCT}%) — untraded, re-pin")


def ladder_idle_reason(s, age_min, ps, now, kry=None, label="ladder idle"):
    """Close reason when a resting WALL has earned nothing across a full window,
    or None. Rolls the measurement window forward in `ps` as a side effect —
    `now` is a unix time.

    `label` is the reason prefix, so rh-turnover's single rung can reuse this
    whole meter stack and still emit a reason the close path routes to a
    re-center (see turnover_decide). Everything else about the rule is
    shape-independent: a resting one-sided bid that has earned nothing is dead
    capital whether it is one of five rungs or the only one.

    Callers pass the WALL AGGREGATE, not one rung (ladder_walls / see the
    LADDER-SCOPED block above): `s` is the wall's summed meters, `age_min` its
    oldest rung's age, `kry` its summed Krystal pair, and `ps` the wall's own
    `ladder:<ladderId>` state dict. Summed fees non-zero means SOME rung earned,
    which holds every rung — an outer rung is fee-dead by design. The one caller
    that still passes a single position is a rung with no `ladderId`, which
    belongs to no wall.

    THREE meters, preferred first — cheapest real measurement wins, and the
    last one is not a measurement at all:

      fee       — real pending+claimed fees from Krystal (`kry`). Preferred
                  because it costs ONE request for the whole wallet regardless
                  of position count. Valid IN range too: a fee is a fee
                  wherever spot sits.
      chain_fee — `feesQuote` from the executor's `state` read: uncollected
                  fees measured on-chain via a batched
                  decreaseLiquidity+collect simulate (uni_executor.js
                  cmdState). Also valid in range, and it needs no third party
                  — but it is already paid for by the state read the monitor
                  does anyway, so it is second only on cost grounds. Added
                  2026-08-05 because Krystal spent that whole soak returning
                  HTTP 521 / read timeouts, which silently demoted every
                  ladder judgement to the meter below.
      value     — quote-denominated position value. LAST RESORT, and it CANNOT
                  SEE FEES: `valueWeth` is principal-only by contract, and an
                  out-of-range rung's principal is 100% quote asset and
                  constant by construction, so growth reads ~0 whatever the
                  rung earned. It detects a rung being TRADED INTO (principal
                  converting), not a rung earning. Only honest while the rung
                  is OUT of range; in range it tracks price and a dip reads as
                  "no fees". Kept only so a total oracle failure still has
                  *some* release valve for dead capital.
    """
    if ps is None or now is None or age_min is None or age_min < LADDER_IDLE_MIN_AGE_MIN:
        return None

    # Absolute zero fees needs no snapshot window. The window exists to tell
    # "earned a little" from "earned nothing", but pending+claimed == 0 across a
    # full window's worth of lifetime is unambiguous: nothing has ever traded
    # through this band. Judging that on age instead of a rolling baseline is
    # also what makes the rule survive a deploy — three restarts on 2026-08-05
    # each added a new idle_* state key, restarting the 90m window from zero and
    # leaving a fee-dead SPY wall parked 6.7h that no rule could release.
    if kry and kry.get("fees_usd") == 0 and age_min >= LADDER_IDLE_WINDOW_MIN:
        return (f"{label}: zero fees in {age_min:.0f}m since mint "
                f"(>= {LADDER_IDLE_WINDOW_MIN:.0f}m) — untraded, re-pin")

    if kry and kry.get("fees_usd") is not None and kry.get("value_usd"):
        return _idle_window(ps, now, "fee", kry["fees_usd"], kry["value_usd"], label=label)

    # Meter 2: on-chain uncollected fees. Same two-stage shape as Krystal
    # (absolute zero judged on age, then a growth window), and the same units
    # discipline — feesQuote and valueWeth are both in the position's own quote
    # asset, so their ratio is a real fee yield in either WETH or USDG.
    #
    # A SEPARATE window key from Krystal's ("chain_fee", not "fee") on purpose:
    # the two levels are different units (USD vs quote), so sharing a snapshot
    # across an oracle recovery would either void the baseline or fake a jump.
    # `feesQuote is None` means the batched simulate failed — unmeasured, so
    # fall through rather than read it as zero.
    fees_q = s.get("feesQuote")
    if fees_q is not None:
        if fees_q == 0 and age_min >= LADDER_IDLE_WINDOW_MIN:
            return (f"{label}: zero on-chain fees in {age_min:.0f}m since mint "
                    f"(>= {LADDER_IDLE_WINDOW_MIN:.0f}m) — untraded, re-pin")
        value_q = s.get("valueWeth")
        if value_q:
            return _idle_window(ps, now, "chain_fee", fees_q, value_q, label=label)

    value = s.get("valueWeth")  # quote units despite the name (executor contract)
    if value is None or value <= 0:
        return None
    if bool(s.get("inRange")):
        # Mid-conversion: value tracks price, not fees. Rebaseline and wait.
        ps["idle_value_snap"], ps["idle_value_at"] = value, now
        return None
    return _idle_window(ps, now, "value", value, label=label)


def judge_ladder_walls(walls, state, now, persist=True):
    """{ladderId: {"idle": reason-or-None}} — ONE idle verdict per wall per
    tick, then applied to every rung of that wall so the wall is held or torn
    down whole. Judging each rung separately would let the first rung roll the
    shared window and hand the others a fresh baseline, which is the rung-at-a-
    time teardown this rule was rescoped to prevent.

    Rolls each wall's window forward in `state` under ladder_wall_key().
    persist=False judges on throwaway copies, which is what the report-only tick
    needs: the systemd loop owns the windows, and a report must never consume
    one.
    """
    out = {}
    for lid, w in walls.items():
        key = ladder_wall_key(lid)
        ps = state.setdefault(key, {}) if persist else dict(state.get(key) or {})
        out[lid] = {
            "idle": ladder_idle_reason(w["state"], w["age_min"], ps, now, w["kry"]),
            "breached": w.get("breached"),
        }
    return out


def ladder_decide(s, pnl, age_min, ps=None, now=None, kry=None, wall=None):
    """Close reason for one ladder rung (either quote asset), or None to hold.

    `wall` is this rung's precomputed WALL verdict (judge_ladder_walls). The
    idle rule is ladder-scoped, so it is decided once for the whole wall and
    handed to each rung; every OTHER rule here — fill, stale, the backstop SL —
    stays per-rung and on-chain. `wall=None` means this rung belongs to no wall
    (no `ladderId`) and judges its own idleness, byte-for-byte the pre-
    2026-08-05 behaviour."""
    tick, lo, hi = s.get("tick"), s.get("tickLower"), s.get("tickUpper")
    if tick is None or lo is None or hi is None:
        return None
    qsym = s.get("quoteSymbol") or "WETH"
    stale_ticks = LADDER_STALE_TICKS.get(qsym, LADDER_STALE_TICKS["WETH"])
    rung = s.get("rung") or 0
    width = hi - lo
    filled, _ = rung_fill_state(s)

    if filled:
        # Fully converted: this rung is now pure token inventory, which is the
        # one thing the strategy exists to avoid holding. Sell it back.
        #
        # NEITHER depth waits for indicator confirmation any more — both reason
        # strings below are outside the confirmable set (see exit_confirmable
        # for the 218-close measurement that removed the shallow one). The
        # split survives only to mark how bad the fill was in the journal, and
        # to keep the deep case unmistakable: the rung that printed -40.6% on
        # 2026-08-07 was a confirm-and-wait on a token that never came back.
        if pnl is not None and pnl <= LADDER_FILL_HARD_PCT:
            return (f"emergency ladder fill {pnl:.1f}% <= {LADDER_FILL_HARD_PCT:.1f}% "
                    f"(tick {tick} past [{lo},{hi}])")
        return f"ladder rung filled (tick {tick} past [{lo},{hi}])"

    # An unfilled rung of a wall whose OTHER rung filled. The wall's thesis was
    # that spot would oscillate above it, and a fill is that thesis failing —
    # what remains is a resting bid under a market that just came down through
    # one. Tear it down with the rest; it is still pure quote asset, so this
    # close costs no swap and no spread (which is also why it never waits for
    # indicator confirmation).
    if wall is not None and wall.get("breached") is not None:
        return (f"ladder wall breached (rung {wall['breached']} filled) — "
                f"retracting the unfilled rungs")

    # Drift from the wall's PIN, not from this rung's edge. rung_drift() prefers
    # the journaled entryTick, which already accounts for the rung's own offset
    # (every rung of a wall shares one pin); the `rung * width` argument is only
    # consumed by its pre-entryTick fallback, where the edge is all there is.
    drift = rung_drift(s, rung * width)
    if drift is not None and drift > stale_ticks:
        # Spot ran away: the wall is too far under the market to be traded into,
        # so it is dead capital. Tear it down and let the scanner re-pin at the
        # new price.
        return (f"ladder stale: spot drifted {drift:.0f} ticks past rung {rung} "
                f"(> {stale_ticks:.0f})")

    # Still within re-pin distance, but is anyone trading into it? A price rule
    # cannot answer that — see ladder_idle_reason. The answer is the WALL's, not
    # this rung's: an outer rung is fee-dead by design, so judging it alone
    # strips the wall's depth while the near rungs are still earning. Every rung
    # of an idle wall gets this same reason on this same tick.
    idle = wall["idle"] if wall is not None else ladder_idle_reason(s, age_min, ps, now, kry)
    if idle:
        return idle

    # Backstop only. A rung mid-conversion does carry some token, so the hard SL
    # still applies — but it should essentially never fire before the filled
    # rule above does.
    if pnl is not None and pnl <= STOP_LOSS_PCT and (age_min is None or age_min >= MIN_AGE_MIN_BEFORE_SL):
        return f"stop loss {pnl:.1f}% <= {STOP_LOSS_PCT:.1f}%"
    return None


def exit_confirmable(reason):
    """Only momentum-shaped exits wait for indicator confirmation; hard-risk
    rules (SL, TP, fee-dead OOR) close unconditionally, mirroring the Solana
    monitor's is_emergency carve-out.

    NO fill reason is confirmable, on either strategy. Both "ladder rung filled"
    and "turnover rung filled" used to be, on the argument that the close is a
    SELL into weakness the market may undo for us: an un-filling rung costs
    nothing, a round-trip through the pool costs the fee tier twice. The
    argument is sound and this venue refutes it anyway. Measured over the 218
    closes to 2026-08-08:

      * a fill that closed on its own rule    -3.81%/trade  (n=5)
      * a fill that was POSTPONED here first  -9.77%/trade  (n=9)

    and six of those nine appear in the postponement log first, held by a
    bullish supertrend/RSI read until they crossed the -8% hard floor and closed
    as "emergency turnover fill" instead. (Position ids deliberately omitted —
    they are traceable to the wallet on-chain; grep the monitor journal for
    "exit postponed" to re-derive the set.)
    The un-fill this gate waits for is real but rare;
    what it reliably buys is the difference between a shallow fill and a hard
    one, ~6 points, on two thirds of every fill the venue produces. There were
    422 postponement events in the three days to 2026-08-08 and they bought
    back nothing.

    A fill means the rung is now token inventory, which is the ONE thing a
    one-sided strategy exists never to hold. Treat it as hard risk, like SL/TP
    and the fee-dead OOR timeout: close on the tick that observes it.

    Two ladder reasons were already outside the set for related reasons, and
    both are named so they cannot match the "ladder rung filled" prefix by
    accident:
      * "emergency ladder fill" — a fill past LADDER_FILL_HARD_PCT. Deep enough
        that waiting for a bullish confirmation is how -7.6% became -40.6%.
        Now merely the deep END of a rule that no longer waits at any depth.
      * "ladder wall breached" — retracting rungs that are still pure quote
        asset. There is no sell to time: nothing is being dumped into weakness,
        so confirmation could only delay a free withdrawal.

    "ladder stale" and "ladder idle" stay out too — dead capital does not get
    better by waiting, and an idle rung has already waited a full window.
    "turnover re-center" is outside the set and must stay outside it: that close
    is half of a close-and-re-mint, the rung is still pure quote asset, and
    postponing it on a bullish read would stall the loop the mode's whole edge
    depends on — the same carve-out dlmm_monitor.py makes for its OOR rebalance.

    What remains confirmable is only the momentum-shaped exits of a TWO-SIDED
    position, where the monitor really is choosing when to dump a bag it already
    holds and a dip is not yet a dump.
    """
    return reason.startswith(("trailing exit", "fast-out", "downtrend"))


def run_executor(executor, args, close_auth=False):
    """Run an executor script and return (parsed_json, err). Reads the last
    stdout line as the JSON payload.

    An executor crash is NOT a parse failure: its top-level handler prints
    {"success": false, "error": ...} to stdout and exits 1, which is valid
    JSON. Parsing that as a payload is how a transient RPC error closed a live
    ladder rung on 2026-08-04 — the caller saw a "state" dict with no
    `strategy` and no `pnlPct`, fell through to the position rulebook, and hit
    the out-of-range timeout that ladders are exempt from. A failure payload is
    an error, so return it as one.
    """
    env = dict(os.environ)
    if close_auth:
        env["UNI_CLOSE_AUTH"] = "1"
    try:
        r = subprocess.run(["node", executor] + args, capture_output=True,
                           text=True, timeout=150, env=env)
        out = (r.stdout or "").strip()
        line = out.splitlines()[-1] if out else ""
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None, (r.stderr or out or "no output").strip()
        if isinstance(payload, dict) and payload.get("success") is False:
            return None, str(payload.get("error") or "executor reported failure")
        return payload, None
    except Exception as e:
        return None, str(e)


def looks_like_state(s):
    """True when `s` is an executor `state` payload and not some other JSON.

    Positive shape check, not a `strategy` check: the v4 executor's state
    payload has no `strategy` key at all, so its absence cannot distinguish a
    real position from a stray payload. `tokenId` + `tickLower` are emitted by
    both executors and by nothing else. Anything failing this is treated as a
    read failure — deciding an exit from a payload we cannot identify is how a
    ladder rung gets closed by a rule that does not apply to it.
    """
    return isinstance(s, dict) and "tokenId" in s and "tickLower" in s


def load_state():
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w") as f:
            json.dump(state, f)
    except OSError as e:
        print(f"warn: could not save monitor state: {e}")


# GeckoTerminal 403s the default urllib User-Agent ("Python-urllib/3.x") — the
# request never reaches the API, fetch_momentum returns (None, None), and the two
# momentum-driven exits (fast-out, sustained-downtrend) silently never fire,
# because missing data is treated as passing. Any non-default UA is accepted
# (Go's default gets 200, which is why the discovery daemon was never affected).
# Same trap the Jupiter audit gate hit. Do not drop this header.
USER_AGENT = "azimuth-uni-monitor/1.0"


# GeckoTerminal's public tier allows ~10 requests/minute per IP, and this process
# shares that IP with the discovery daemon — whose own limiter cannot see these
# requests. One /pools/ call per position per tick was ~5 req/min on its own (7
# rungs every ~82s): half the budget spent on a rule that reads two numbers.
# /pools/multi/ returns the same attributes for up to GT_MULTI_MAX pools in ONE
# request, and a ladder's rungs share a pool, so dedup shrinks it further — a
# tick costs one request, not one per rung. Filled once per tick by
# prefetch_momentum; fetch_momentum only reads it.
GT_MULTI_MAX = 30
_momentum_cache = {}

# How long a fetched (m5, h1) pair stays usable. 60s is not arbitrary: these are
# GeckoTerminal's 5-minute and 1-hour price-change windows, so re-reading them
# every 20s returns the same numbers three times and spends two extra requests
# out of a ~10/min budget this process shares with the discovery daemon. The
# rules that DO need every tick — PnL, in-range, rung fills — are on-chain reads
# and are unaffected by this TTL.
MOMENTUM_TTL = float(os.environ.get("UNI_MOMENTUM_TTL", "60"))


def _load_momentum_cache():
    """Return (age_seconds, {pool: [m5, h1]}) from the persisted cache, or
    (inf, {}) when it is missing/corrupt — an unreadable cache must look stale,
    never fresh-and-empty, or the refetch it should trigger would be skipped."""
    try:
        with open(MOMENTUM_CACHE_PATH) as f:
            d = json.load(f)
        return max(0.0, time.time() - float(d.get("ts") or 0)), dict(d.get("pools") or {})
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return float("inf"), {}


def _save_momentum_cache(pools):
    # The report cron reads the cache but never writes it, same rule that keeps
    # it off STATE_PATH: the loop owns every file the exits depend on, and a
    # report tick landing between two loop ticks must not move the window the
    # loop is pacing its GT requests by.
    if REPORT_ONLY:
        return
    try:
        os.makedirs(os.path.dirname(MOMENTUM_CACHE_PATH), exist_ok=True)
        with open(MOMENTUM_CACHE_PATH, "w") as f:
            json.dump({"ts": time.time(), "pools": pools}, f)
    except OSError as e:
        print(f"warn: could not save momentum cache: {e}")


def prefetch_momentum(pools):
    """Fill this tick's momentum cache for every distinct pool in one (or, past
    GT_MULTI_MAX pools, a few) /pools/multi/ call. Best-effort: a failed chunk
    leaves its pools uncached, so fetch_momentum returns (None, None) for them —
    which every momentum rule treats as passing, same as before.

    Serves the persisted cache instead when it is younger than MOMENTUM_TTL and
    already covers every pool asked for. A pool that is NOT covered (a mint since
    the last fetch) forces the request even on a young cache — a brand-new
    position is exactly the one whose momentum rules must not be blind."""
    want = sorted({p.lower() for p in pools if p})
    if not want:
        return
    age, cached = _load_momentum_cache()
    if age < MOMENTUM_TTL and all(p in cached for p in want):
        _momentum_cache.update({k: tuple(v) for k, v in cached.items()})
        return
    for i in range(0, len(want), GT_MULTI_MAX):
        chunk = want[i:i + GT_MULTI_MAX]
        url = ("https://api.geckoterminal.com/api/v2/networks/robinhood/pools/multi/"
               + ",".join(chunk))
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                d = json.load(resp)
            for entry in d.get("data") or []:
                attrs = entry.get("attributes") or {}
                addr = (attrs.get("address") or "").lower()
                pc = attrs.get("price_change_percentage") or {}
                if addr:
                    _momentum_cache[addr] = (float(pc.get("m5") or 0),
                                             float(pc.get("h1") or 0))
        except Exception:
            continue
    # Persist whatever landed. A partial (or empty, all-chunks-refused) result is
    # written with a fresh timestamp anyway: the NEXT tick's coverage check sees
    # the missing pools and refetches, so a refused call costs one stale tick,
    # not a poisoned window.
    _save_momentum_cache({k: list(v) for k, v in _momentum_cache.items()})


def fetch_momentum(pool):
    """Best-effort GeckoTerminal price-change windows for a pool. Returns
    (m5, h1) percent, or (None, None) — missing data never fires a rule.

    Reads the cache prefetch_momentum filled for this tick. A miss does NOT fall
    back to a single-pool request: the prefetch already asked GT about this pool,
    so a miss means GT does not know it or the call was refused, and re-asking
    one pool at a time is the request storm the batch exists to remove."""
    return _momentum_cache.get((pool or "").lower(), (None, None))


def fetch_eth_usd():
    """Best-effort ETH/USD from Blockscout's stats endpoint — one request per
    tick, shared by every position row. None just drops the $ figures from the
    card; no exit rule reads it."""
    url = "https://robinhoodchain.blockscout.com/api/v2/stats"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.load(resp)
        return float(d["coin_price"])
    except Exception:
        return None


def trailing_floor_pct(peak):
    """Profit-ratchet floor — identical shape to dlmm_monitor.py: tight near
    activation, locks progressively more as the peak grows, gives big winners
    room instead of a flat drop that caps every win."""
    if peak >= 20.0:
        return max(14.0, peak * 0.70)
    if peak >= 10.0:
        return max(6.0, peak - 4.0)
    if peak >= 5.0:
        return max(2.0, peak - 2.5)
    return peak - TRAILING_DROP_PCT


def is_turnover(s):
    """True when this position is an rh-turnover mint.

    Keyed on the strategy string the executors stamp into their entry journal,
    the same way is_ladder keys on the `_ladder` suffix.

    Deliberately does NOT match `balanced_tight`. A position minted before the
    2026-08-07 correction is two-sided and holds token, so every rule
    turnover_decide skips (trailing, the OOR fuse) is a rule that shape still
    needs; routing it here would judge a token-bearing position by a rulebook
    that assumes pure quote. Those keep the default path unchanged.
    """
    return (s or {}).get("strategy") == TURNOVER_STRATEGY


def is_ask(s):
    """True when this position is the ask half of a turnover round trip."""
    return (s or {}).get("strategy") == ASK_STRATEGY


def ask_decide(s, pnl, age_min, ps=None, now=None, kry=None):
    """Close reason for a resting ask rung (token_above), or None to hold.

    The turnover rulebook with the roles reversed. This rung holds TOKEN and is
    waiting to be paid in quote, so:

      filled  -> DONE, and the good outcome. Price came up through the ask, the
                 bag sold into it at our price, and the round trip closed having
                 earned the fee tier on both legs. Plain close, no re-list: we
                 are back to pure quote, which is where a turnover entry starts.
      bag stop-> the token kept falling instead. This is the ONLY hard risk rule
                 an ask has, and it is why ASK_BAG_STOP_PCT exists — without it
                 the position is an unbounded hold. Never confirmable, never
                 re-listed: same class as SL.
      drift   -> RE-CENTER. Spot walked away from the ask, so the offer is too
                 far above the market to ever be hit. Re-list nearer.
      idle    -> RE-CENTER, same reasoning as the bid's.

    Note the asymmetry with turnover_decide: there a fill is the bad case and
    drift is routine; here a fill is the WHOLE POINT. Same two tests, opposite
    verdicts, which is exactly why this is a separate function rather than a
    flag on that one.
    """
    tick, lo, hi = s.get("tick"), s.get("tickLower"), s.get("tickUpper")
    if tick is None or lo is None or hi is None:
        return None
    qsym = s.get("quoteSymbol") or "WETH"
    stale_ticks = TURNOVER_STALE_TICKS.get(qsym, TURNOVER_STALE_TICKS["WETH"])

    filled, _ = rung_fill_state(s, side="ask")
    if filled:
        return f"ask rung sold (tick {tick} past [{lo},{hi}])"

    # Hard bag stop, before the re-center rules: a token in free fall must be
    # dumped, not re-listed lower, or each re-list just chases it down.
    if pnl is not None and pnl <= ASK_BAG_STOP_PCT:
        return f"ask bag stop {pnl:.1f}% <= {ASK_BAG_STOP_PCT:.1f}%"

    drift = rung_drift(s, side="ask")
    if drift is not None and drift > stale_ticks:
        return (f"ask re-center: spot drifted {drift:.0f} ticks past the rung "
                f"(> {stale_ticks:.0f})")

    idle = ladder_idle_reason(s, age_min, ps, now, kry, label="ask re-center — idle")
    if idle:
        return idle
    return None


def turnover_decide(s, pnl, age_min, ps=None, now=None, kry=None):
    """Close reason for an rh-turnover rung (weth_below), or None to hold.

    Deliberately the LADDER rulebook, not the position one, because the shape is
    a ladder rung: one resting one-sided quote-asset bid, out of range by
    design, holding no token. Every rule in `decide` below assumes inventory
    that can be stopped out of or trailed, and none of them can fire correctly
    on pure quote — which is why the rung reuses rung_fill_state() and
    ladder_idle_reason() rather than getting a second implementation of both.

    Where it diverges from ladder_decide is the RESPONSE, not the test:

      filled   -> exit. The rung converted to token, which is the one thing this
                  strategy exists not to hold. Cooled off, not re-pinned: the
                  market came down through our bid, and re-pinning under it is
                  the repeat-fill pattern that averaged -11.8% on the ladder.
      stale    -> RE-CENTER. Spot ran up away from the band. On a ladder that is
                  a teardown; here it is the loop's normal operating cycle and
                  the close path re-mints at the new price.
      idle     -> RE-CENTER. Nobody traded the band for a full window. Same
                  verb as stale on purpose: the mode's premise is that this pool
                  churns, and a pin that collected nothing was in the wrong
                  place. The circuit breaker (recenter_ok) is what stops this
                  from looping forever in a pool that has stopped moving.

    There is no wall: a turnover mint is a single position with no `ladderId`,
    so `ps` is its own state dict and the idle window is its own.
    """
    tick, lo, hi = s.get("tick"), s.get("tickLower"), s.get("tickUpper")
    if tick is None or lo is None or hi is None:
        return None
    qsym = s.get("quoteSymbol") or "WETH"
    stale_ticks = TURNOVER_STALE_TICKS.get(qsym, TURNOVER_STALE_TICKS["WETH"])
    filled, _ = rung_fill_state(s)

    if filled:
        # Same two tiers as a ladder fill and for the same reason: a shallow
        # fill can un-fill back into quote for free, so it waits for indicator
        # confirmation, and a deep one cannot afford to.
        if pnl is not None and pnl <= TURNOVER_FILL_HARD_PCT:
            return (f"emergency turnover fill {pnl:.1f}% <= {TURNOVER_FILL_HARD_PCT:.1f}% "
                    f"(tick {tick} past [{lo},{hi}])")
        return f"turnover rung filled (tick {tick} past [{lo},{hi}])"

    # Drift, measured from the tick the rung was pinned to — NOT from its band
    # edge, which is born one to two tick-spacings away and would read that
    # birth offset as a move. See rung_drift(); this is what the 2026-08-07
    # re-center loop was.
    drift = rung_drift(s)
    if drift is not None and drift > stale_ticks:
        return (f"turnover re-center: spot drifted {drift:.0f} ticks past the rung "
                f"(> {stale_ticks:.0f})")

    idle = ladder_idle_reason(s, age_min, ps, now, kry, label="turnover re-center — idle")
    if idle:
        return idle

    # Backstop. A rung mid-conversion carries some token, so the hard SL still
    # applies — but the fill rule above should always get there first.
    if pnl is not None and pnl <= STOP_LOSS_PCT and (age_min is None or age_min >= MIN_AGE_MIN_BEFORE_SL):
        return f"stop loss {pnl:.1f}% <= {STOP_LOSS_PCT:.1f}%"
    return None


def decide(pnl, peak, in_range, age_min, oor_min, m5, h1, s=None, ps=None, now=None,
           kry=None, wall=None):
    """Return a close reason string, or None to hold. Mirrors the Solana
    monitor's rule precedence: emergency SL first, then hard SL/TP, then
    trailing/fast-out/downtrend, then OOR timeout.

    `s` is the executor's state payload. Ladder rungs (weth_ladder,
    usdg_ladder) are routed to ladder_decide instead — they are one-sided
    resting bids whose entire rulebook differs (see above). Matching on the
    "_ladder" suffix rather than a fixed list is deliberate: a new quote asset
    adds a strategy name, and a ladder that silently fell through to the
    position rulebook would be closed by the fee-dead OOR timeout 30 minutes
    after minting, which is the one failure this branch exists to prevent.
    Positions minted before the ladder existed carry no strategy field and keep
    the original path unchanged. `weth_below` (rh-turnover) is routed to
    turnover_decide for the same structural reason: it is a one-sided rung too.

    `wall` is only read on that ladder branch (see ladder_decide). A position
    with no `ladderId` — every non-ladder strategy, and any pre-ladderId mint —
    never sees it.

    A payload that is not recognizably a state read holds unconditionally: an
    unidentifiable `s` means we do not know which rulebook applies, and the
    default rulebook is the one that closes ladders.
    """
    if s is not None and not looks_like_state(s):
        return None
    if s is not None and is_ladder(s):
        return ladder_decide(s, pnl, age_min, ps, now, kry, wall)
    # The ask half of a turnover round trip: holds token, rests above spot, and
    # its fill is the SUCCESS case. Routed before turnover_decide because it is
    # not a bid and every rule there would read it backwards.
    if s is not None and is_ask(s):
        return ask_decide(s, pnl, age_min, ps, now, kry)
    # Turnover (weth_below) is a one-sided resting bid, so it leaves by the
    # ladder's rules with the ladder's fee-death meters — see turnover_decide.
    # It must never reach the rulebook below: an out-of-range weth_below rung is
    # normal (v3/v4 cannot mint one-sided across spot), so the OOR timeout would
    # close every one of them on the fuse, which is the exact failure the ladder
    # branch above exists to prevent.
    if s is not None and is_turnover(s):
        return turnover_decide(s, pnl, age_min, ps, now, kry)
    if pnl is not None:
        # Emergency SL — bypasses the age grace.
        if pnl <= STOP_LOSS_PCT - EMERGENCY_SL_BUFFER_PCT:
            return f"emergency SL {pnl:.1f}% <= {STOP_LOSS_PCT - EMERGENCY_SL_BUFFER_PCT:.1f}%"
        # Hard SL (after a short settle grace).
        if pnl <= STOP_LOSS_PCT and (age_min is None or age_min >= MIN_AGE_MIN_BEFORE_SL):
            return f"stop loss {pnl:.1f}% <= {STOP_LOSS_PCT:.1f}%"
        # Hard TP.
        if pnl >= TAKE_PROFIT_PCT:
            return f"take profit {pnl:.1f}% >= {TAKE_PROFIT_PCT:.1f}%"
        # Trailing profit ratchet (armed once peak clears the trigger).
        if peak >= TRAILING_TRIGGER_PCT:
            floor = trailing_floor_pct(peak)
            if pnl < floor and pnl >= TRAILING_MIN_LOCK_PCT:
                return f"trailing exit {pnl:.1f}% < floor {floor:.1f}% (peak {peak:.1f}%)"
            # Fast-out velocity: armed + still locked + a steep 5m dump that
            # would gap through the floor between ticks.
            if m5 is not None and m5 <= FAST_EXIT_M5_PCT and pnl >= TRAILING_MIN_LOCK_PCT:
                return f"fast-out {m5:.1f}% 5m dump (pnl {pnl:.1f}%, peak {peak:.1f}%)"
        # Sustained downtrend: underwater AND token in steady 1h decline.
        if h1 is not None and h1 <= DOWNTREND_1H_PCT and pnl <= DOWNTREND_PNL_PCT:
            return f"downtrend 1h {h1:.1f}% + pnl {pnl:.1f}%"
    # Out-of-range timeout — fee-dead capital past the patience window.
    if not in_range and oor_min >= MAX_OOR_MINUTES:
        return f"out of range {oor_min:.0f}m >= {MAX_OOR_MINUTES:.0f}m"
    return None


def journal_close(rec):
    try:
        os.makedirs(os.path.dirname(CLOSES_PATH), exist_ok=True)
        with open(CLOSES_PATH, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except OSError as e:
        print(f"warn: could not journal close: {e}")


# --- re-entry cooldown -----------------------------------------------------
# Ported from dlmm_monitor.py's cooldown block, which the Robinhood venue never
# had. Without it the scanner re-ladders a pool the moment its dedup TTL lapses,
# and the journal shows what that costs: of 11 rung fills to 2026-08-07, six
# were a REPEAT fill in a pool that had already run our wall over once, and the
# repeats averaged -11.8% against -6.7% for the first.
#
# The Solana rule cools every close. This one cools only the FILL class, and the
# difference is the strategy, not an oversight: `ladder idle` and `ladder stale`
# are re-pins by design — the mode's normal operating loop is close-and-re-pin,
# so cooling a pool off for those would switch the mode off. What earns a
# cooldown is the pool proving it trends down THROUGH a resting wall.
#
# Written to the same Redis the daemon dedups in, because the daemon is what
# enforces it (internal/store.Seen.RobinhoodCooldown); a monitor-local file
# could not be read from the Go process. Best-effort throughout: Redis being
# down must never block a close.
COOLDOWN_POOL_SECS = int(os.environ.get("UNI_COOLDOWN_POOL_SECS", "14400"))    # 4h
COOLDOWN_TOKEN_SECS = int(os.environ.get("UNI_COOLDOWN_TOKEN_SECS", "14400"))  # 4h
COOLDOWN_STREAK_SECS = (86400, 259200)  # 2 losses in 7d -> 24h, 3+ -> 72h


def redis_cmd(*args):
    """Run one redis-cli command against the daemon's instance. Returns stdout
    stripped, or None if Redis is unreachable/absent — every caller treats that
    as "no cooldown recorded", which fails OPEN by design: a cooldown is a
    risk brake, and a broken brake must not also break the close path."""
    addr = os.environ.get("REDIS_ADDR", "127.0.0.1:6379")
    host, _, port = addr.partition(":")
    try:
        r = subprocess.run(["redis-cli", "-h", host or "127.0.0.1", "-p", port or "6379"] + [str(a) for a in args],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError) as e:
        print(f"warn: redis {args[0] if args else '?'} failed: {e}")
        return None


def cool_off(pool, token, reason, pnl):
    """Cool a pool (and its token) off after a resting bid was run over.

    `token` may be None on an older state read — the pool key still lands, which
    is the one that matters: a bid is re-pinned per POOL, and the token key only
    widens the block to that token's other pools.

    FILL reasons only, never a re-center. A fill is the market coming down
    THROUGH our bid, and the ladder journal is unambiguous about re-pinning
    under one: six of eleven fills were a repeat in a pool that had already
    filled, averaging -11.8% against -6.7% for the first. A re-center is the
    opposite event — the pin was in the wrong place and nothing was bought —
    and cooling the pool off there would switch the mode off after one cycle.
    """
    if not any(reason.startswith(p) for p in ("ladder rung filled", "emergency ladder fill",
                                              "ladder wall breached", "turnover rung filled",
                                              "emergency turnover fill")):
        return
    secs = COOLDOWN_POOL_SECS
    tkey = f"rh:loss_streak:{str(token).lower()}" if token else None
    if tkey and (pnl is None or pnl < 0):
        redis_cmd("incr", tkey)
        redis_cmd("expire", tkey, 604800)  # the streak's own 7d window
        try:
            streak = int(redis_cmd("get", tkey) or 1)
        except ValueError:
            streak = 1
        if streak >= 2:
            secs = COOLDOWN_STREAK_SECS[1] if streak >= 3 else COOLDOWN_STREAK_SECS[0]
            print(f"monitor: repeat loss #{streak} in 7d on {token} — cooldown escalated to {secs // 3600}h")
    redis_cmd("set", f"rh:cooldown:pool:{str(pool).lower()}", reason[:120], "ex", secs)
    if token:
        redis_cmd("set", f"rh:cooldown:token:{str(token).lower()}", reason[:120], "ex",
                  max(secs, COOLDOWN_TOKEN_SECS))
    print(f"monitor: re-entry cooldown {secs // 3600}h on pool {pool}")


# --- turnover re-center loop ----------------------------------------------
# The mode's profit engine, and the one leg this venue never had. A turnover
# position that leaves its range is closed and IMMEDIATELY re-minted around the
# new price, so the capital goes back to earning instead of sitting in the
# wallet until the scanner happens to signal the pool again.
#
# The re-mint carries no geometry arguments on purpose. A weth_below rung's
# width comes from UNI_TURNOVER_RUNG_TICKS inside the executor (uni_ladder.js),
# which is the same number the scanner's mint used and the same one
# TURNOVER_STALE_TICKS above judges drift against — passing a --range-pct here
# would be a third copy that only this path could get wrong. There is no swap,
# so there is no slippage to set either.
CB_RECENTER_KEY = "rh:turnover:recenters:{}"
CB_PNL_KEY = "rh:turnover:pnl:{}"
CB_WINDOW_SECS = 86400


def _f(v):
    """float(v) or None — executor amounts arrive as strings, and a missing one
    must not raise inside the close path."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cb_record(pool, realized_quote):
    """Book one re-center and its realized PnL into the pool's 24h window.

    Both keys carry their own rolling TTL, so the window is per-pool and
    independent — the same per-key discipline internal/store/store.go documents
    for the dedup set, and for the same reason: one shared key would let a busy
    pool refresh a quiet pool's window forever.
    """
    rk, pk = CB_RECENTER_KEY.format(pool), CB_PNL_KEY.format(pool)
    redis_cmd("incr", rk)
    redis_cmd("expire", rk, CB_WINDOW_SECS)
    if realized_quote is not None:
        redis_cmd("incrbyfloat", pk, f"{realized_quote:.9f}")
        redis_cmd("expire", pk, CB_WINDOW_SECS)


def recenter_ok(pool):
    """(allowed, why) for re-centering this pool — the ported circuit breaker.

    Fails CLOSED, which is the opposite of cool_off's rule above and is
    deliberate. A cooldown is a brake on the close path, so a broken brake must
    not also break closing. A re-center is OPTIONAL EXTRA WORK on top of a close
    that has already happened: if we cannot read the window, we cannot know
    whether this pool has been bleeding on every cycle, and the safe answer to
    that is to take the normal exit and let the scanner re-signal the pool
    through the full screen.
    """
    raw_n = redis_cmd("get", CB_RECENTER_KEY.format(pool))
    if raw_n is None:
        return False, "circuit breaker unreadable (redis down) — normal exit"
    try:
        n = int(raw_n) if raw_n else 0
    except ValueError:
        n = 0
    if n >= TURNOVER_MAX_RECENTERS_24H:
        return False, f"re-center cap {n}/{TURNOVER_MAX_RECENTERS_24H} in 24h"
    raw_p = redis_cmd("get", CB_PNL_KEY.format(pool))
    try:
        realized = float(raw_p) if raw_p else 0.0
    except ValueError:
        realized = 0.0
    if realized <= TURNOVER_CB_LOSS_QUOTE:
        return False, (f"circuit breaker: 24h re-center PnL {realized:+.5f} "
                       f"<= {TURNOVER_CB_LOSS_QUOTE:+.5f} floor")
    return True, f"{n}/{TURNOVER_MAX_RECENTERS_24H} re-centers, 24h PnL {realized:+.5f}"


def recenter(executor, pool, amount, quote, pair):
    """Re-mint a turnover position around the current price. Returns True on a
    confirmed mint.

    `amount` is the quote-asset proceeds of the close we just did, so the
    position compounds by construction: fees collected on the way out are part
    of what gets re-deployed. That is also why compounding needs no
    increaseLiquidity path here — see TURNOVER_COMPOUND_MIN_PCT.
    """
    if amount is None or amount <= 0:
        print(f"monitor: re-center skipped for {pair} — close returned no quote proceeds")
        return False
    args = ["deploy", "--pool", pool, "--amount", f"{amount:.9f}".rstrip("0"),
            "--strategy", TURNOVER_STRATEGY]
    if quote:
        args += ["--quote", quote]
    out, err = run_executor(executor, args)
    if err or not out or not out.get("success"):
        print(f"monitor: RE-CENTER FAILED {pair}: {err or (out or {}).get('error') or 'no payload'}")
        return False
    print(f"monitor: RE-CENTERED {pair} -> #{out.get('tokenId')} "
          f"({amount:.6f} redeployed, ticks [{out.get('tickLower')},{out.get('tickUpper')}])")
    return True


def is_fill_close(reason):
    """True for the reasons that mean the bid converted to token.

    Both tiers, because both leave the same thing in the wallet: a bag. The
    emergency tier only skips indicator confirmation, it does not change what
    the position turned into.
    """
    r = reason or ""
    return r.startswith("turnover rung filled") or r.startswith("emergency turnover fill")


def wants_relist(reason, s):
    """True when this close should keep the token and re-list it as an ask.

    Two cases, both of which end holding token:
      - a turnover BID that filled (the round trip's halfway point), and
      - an ASK that is being re-centered (still unsold, just mispriced).

    Explicitly NOT `ask bag stop` — that reason exists to get rid of the bag, so
    re-listing on it would defeat the only hard risk rule the ask half has. And
    not `ask rung sold`: that one already ended in quote.
    """
    if not ASK_RELIST_ENABLED:
        return False
    if is_turnover(s) and is_fill_close(reason):
        return True
    return is_ask(s) and (reason or "").startswith("ask re-center")


def relist_ask(executor, pool, quote, pair):
    """Mint a resting ask over the token bag the close just left in the wallet.

    Takes no amount: `token_above` lists the whole balance by construction,
    because the position exists to unload exactly that inventory. That also
    sidesteps the decimals trap — the bag is token units, and every amount the
    monitor otherwise handles is quote units.

    A failure here is not fatal and must not be retried into: the close already
    succeeded, so the bag is simply sitting in the wallet where the executor's
    own `sweep` path can still sell it. Reported loudly because a silent failure
    would look exactly like a successful re-list until the next tick.
    """
    args = ["deploy", "--pool", pool, "--strategy", ASK_STRATEGY]
    if quote:
        args += ["--quote", quote]
    out, err = run_executor(executor, args)
    if err or not out or not out.get("success"):
        print(f"monitor: RE-LIST FAILED {pair}: {err or (out or {}).get('error') or 'no payload'} "
              f"— bag left in wallet for sweep")
        return False
    print(f"monitor: RE-LISTED {pair} -> ask #{out.get('tokenId')} "
          f"ticks [{out.get('tickLower')},{out.get('tickUpper')}]")
    return True


def compound_fees(executor, tid, s, proto):
    """Claim fees on an in-range turnover position so they fund the next mint.

    Only worth a transaction when the pending fee is a real share of the
    position — below TURNOVER_COMPOUND_MIN_PCT the gas costs more than the
    claim recovers. Best-effort: a failed collect is not an error, the fees
    stay pending and the next re-center's close collects them anyway.
    """
    fees, val = s.get("feesQuote"), s.get("valueWeth")
    if fees is None or not val or val <= 0:
        return
    pct = float(fees) / float(val) * 100.0
    if pct < TURNOVER_COMPOUND_MIN_PCT:
        return
    out, err = run_executor(executor, ["collect", "--id", str(tid)])
    if err or not out or not out.get("success"):
        print(f"monitor: compound collect failed {proto} #{tid}: {err or 'no payload'}")
        return
    # Gas beside the claim, not in a separate line: a compound is only worth
    # doing while the fee exceeds what collecting it costs, and that comparison
    # is unreadable if the two numbers land in different log entries.
    # TURNOVER_COMPOUND_MIN_PCT is a percentage guess at this; the pair below is
    # the measurement that can eventually replace it.
    gas = (out or {}).get("gasEth")
    print(f"monitor: COMPOUNDED {proto} #{tid} — claimed {fees} "
          f"({pct:.2f}% of position), gas {gas or 'unmetered'}, funds the next re-center")


def sweep_stranded(proto, executor):
    """Retry the exit sell for bags a close could not unload.

    Runs every tick, before the position pass, once per executor (the two keep
    separate stranded journals). A pool that was dead when we closed can be
    re-seeded by another LP, and a sell that reverted on a transient just works
    next time — so the bag is worth re-offering cheaply and often. No-op (one
    RPC read) when nothing is stranded.
    """
    out, err = run_executor(executor, ["sweep"], close_auth=True)
    if err or not out:
        if err:
            print(f"monitor: {proto} sweep failed: {err}")
        return
    if not out.get("swept"):
        return
    for r in out.get("results", []):
        # v3 reports weth_out; v4 reports quote_out + quote_symbol (the quote
        # varies per pool there).
        recovered = r.get("quote_out", r.get("weth_out", "0"))
        unit = r.get("quote_symbol", "WETH")
        if r.get("resolved") and recovered != "0":
            print(f"monitor: SWEPT {r.get('symbol')} -> {recovered} {unit} (fee {r.get('fee')})")
            alert(f"🧹 Robinhood sweep recovered {recovered} {unit}\n"
                  f"sold stranded {r.get('symbol')} ({r.get('token')})")
        elif r.get("resolved") is False:
            print(f"monitor: still stranded {r.get('symbol')} "
                  f"(attempt {r.get('attempts')}, retry in {r.get('retry_in_s')}s): {r.get('reason')}")


def alert(text):
    """Best-effort operator alert via hermes; never fails the tick."""
    target = os.environ.get("DLMM_ALERT_TARGET", "telegram")
    if not target:
        return
    try:
        subprocess.run(["hermes", "send", "-t", target, "-m", text, "-q"],
                       timeout=30, capture_output=True)
    except Exception:
        pass


def render_card(rows):
    """Telegram status card for the reporting cron. Deterministic — the cron
    prompt copies it verbatim, so the format lives here, not in the agent turn.
    First line prefix is load-bearing (the cron's OUTPUT RULE keys off it)."""
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    lines = [f"Robinhood LP Status — {ts}", f"📊 Active Positions: {len(rows)}"]
    if not rows:
        lines.append("\nNo active positions. Bot is idle.")
    for r in rows:
        pnl = f"{r['pnl_pct']:+.1f}%" if r["pnl_pct"] is not None else "n/a"
        if r.get("pnl_usd") is not None:
            pnl += f" (${r['pnl_usd']:+.2f})"
        val = r["value_weth"]
        ent = r["entry_weth"]
        qsym = r.get("quote_symbol") or "WETH"
        # USDG values ARE dollars — two decimals, no ETH/USD conversion.
        if qsym == "USDG":
            val_s = f"{val:.2f}" if val is not None else "?"
            ent_s = f"{ent:.2f}" if ent is not None else "?"
            usd_s = ""
        else:
            val_s = f"{val:.5f}" if val is not None else "?"
            ent_s = f"{ent:.5f}" if ent is not None else "?"
            usd = r.get("eth_usd")
            usd_s = (f" (${val * usd:.2f} / ${ent * usd:.2f})"
                     if usd and val is not None and ent is not None else "")
        age_min = r["age_min"]
        if age_min is None:
            age = "n/a"
        elif age_min >= 60:
            age = f"{int(age_min // 60)}h{int(age_min % 60):02d}m"
        else:
            age = f"{age_min:.0f}m"
        rng = "🟢 In Range" if r["in_range"] else f"🔴 OOR {r['oor_min']:.0f}m"
        m5 = f"{r['m5']:+.1f}%" if r["m5"] is not None else "n/a"
        h1 = f"{r['h1']:+.1f}%" if r["h1"] is not None else "n/a"
        # Only ⚠️ bullets are printed — a healthy position shows just the table
        # and the summary line, matching the Solana card's compact layout.
        warnings = []
        if not r["in_range"]:
            warnings.append(f"⚠️ Out of range {r['oor_min']:.0f}m (limit {MAX_OOR_MINUTES:.0f}m)")
        if r["peak_pct"] >= TRAILING_TRIGGER_PCT:
            warnings.append(f"⚠️ Trailing stop ACTIVE (peak {r['peak_pct']:+.1f}%, floor {trailing_floor_pct(r['peak_pct']):+.1f}%)")
        if r["m5"] is None or r["h1"] is None:
            warnings.append("⚠️ No momentum data — fast-out and downtrend exits cannot fire")
        lines += [
            "",
            "---",
            "",
            f"### {r.get('pair') or 'Position #' + r['tokenId']}",
            (f"`{r['pool']}`" if r.get("pool") else "`?`") + f" · #{r['tokenId']}",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| PnL | {pnl} · peak {r['peak_pct']:+.1f}% |",
            f"| Value | {val_s} / {ent_s} {qsym}{usd_s} |",
            f"| Range | {rng} · age {age} |",
            f"| Price 5m/1h | {m5} / {h1} |",
        ] + [f"- {w}" for w in warnings] + [
            "",
            f"→ {r['decision']}: {r['reason']}",
        ]
    return "\n".join(lines)


def state_key(proto, tid):
    """Peak/oor state key. v3 keys are bare tokenIds (the live state file
    predates v4 and must keep matching); v4 is namespaced because the two
    PositionManagers mint colliding tokenId sequences."""
    return str(tid) if proto == "v3" else f"{proto}:{tid}"


def read_states(work):
    """Read every position's state up front. Returns [(proto, executor, tokenId,
    state)] for the reads that SUCCEEDED; a failure is printed and dropped.

    One pass before any decision is what lets the ladder rules aggregate a whole
    wall from a single consistent snapshot, and it is why the decision loop no
    longer interleaves state reads with closes. The cost is that a later
    position's numbers are a few seconds staler than they used to be, bounded by
    this loop; every rule already acts on up-to-a-tick-old data, and a wall
    judged half from this tick and half from the last is the worse failure.

    A dropped read gets NO peak/oor bookkeeping either — a read we cannot trust
    must not start an oor_since clock a later, healthy tick would act on — but
    the position still counts as live (see main), so its state is not pruned.
    """
    reads = []
    for proto, executor, tid in work:
        s, err = run_executor(executor, ["state", "--id", str(tid)])
        if err or not looks_like_state(s):
            print(f"monitor: {proto} state #{tid} failed: {err or 'unrecognized payload'}")
            continue
        reads.append((proto, executor, tid, s))
    return reads


def main():
    # Gather (proto, executor, tokenId) across executors. One executor's read
    # failure must not blind the monitor to the other's positions — note it,
    # keep scanning, and only fail the tick when EVERY read failed.
    work = []
    errors = []
    for proto, executor in EXECUTORS:
        pos, err = run_executor(executor, ["positions"])
        if err:
            errors.append(f"{proto}: {err}")
            print(f"monitor: {proto} positions read failed: {err}")
            continue
        # Stranded bags outlive the positions that created them, so sweep
        # BEFORE the no-open-positions early return below — the venue sits
        # flat most of the time, and a sweep that only ran when something was
        # open would never run. Each executor keeps its own stranded journal.
        if not REPORT_ONLY and not DRY_RUN:
            sweep_stranded(proto, executor)
        for p in pos.get("positions", []):
            work.append((proto, executor, p["tokenId"]))
    if errors and len(errors) == len(EXECUTORS):
        # Report-only must still hand the cron a parseable line so it can decide
        # SILENT vs surface-the-error, instead of leaving the agent to guess.
        if REPORT_ONLY:
            print("MONITOR_REPORT:" + json.dumps({"positions": [], "error": "; ".join(errors)}))
        sys.exit(1)

    if not work:
        if REPORT_ONLY:
            report = {"positions": []}
            if errors:
                report["error"] = "; ".join(errors)
            print("MONITOR_REPORT:" + json.dumps(report))
            return
        print("monitor: no open positions")
        return

    if REPORT_ONLY:
        state = load_state()
        now = time.time()
        eth_usd = fetch_eth_usd()
        krystal = fetch_krystal_positions()
        reads = read_states(work)
        # One GT request for every row's momentum, before the row loop — same
        # reason the ETH price and the Krystal oracle are fetched here: a tick's
        # API cost must not scale with position count.
        prefetch_momentum([s.get("pool") for _, _, _, s in reads])
        # A wall's verdict needs every rung's state before any row is decided.
        # persist=False — the report must not roll a window the loop owns, the
        # same reason the per-position ps is copied below.
        wall_verdicts = judge_ladder_walls(
            ladder_walls([(tid, s) for _, _, tid, s in reads], krystal),
            state, now, persist=False)
        rows = []
        for proto, _executor, tid, s in reads:
            pnl = s.get("pnlPct")
            in_range = bool(s.get("inRange"))
            age_min = s.get("ageMin")
            pool = s.get("pool")
            qsym = s.get("quoteSymbol") or "WETH"
            # Read persisted peak/oor without mutating — the systemd loop owns
            # writes to STATE_PATH; the report reflects its last tick.
            ps = state.get(state_key(proto, tid), {"peak_pnl": 0.0, "oor_since": None})
            peak = ps.get("peak_pnl", 0.0)
            if pnl is not None and pnl > peak:
                peak = pnl
            if in_range or not ps.get("oor_since"):
                oor_min = 0.0
            else:
                oor_min = (now - ps["oor_since"]) / 60.0
            m5, h1 = fetch_momentum(pool) if pool else (None, None)
            # dict(ps): the idle window is rolled forward as a side effect, and
            # the report must not consume a window the loop owns.
            reason = decide(pnl, peak, in_range, age_min, oor_min, m5, h1, s, dict(ps), now,
                            krystal.get(str(tid)), wall_of(s, wall_verdicts))
            val_w, ent_w = s.get("valueWeth"), s.get("entryWeth")
            # USDG positions are dollar-quoted already; everything else is
            # ETH-quoted and needs the ETH/USD conversion.
            if val_w is None or ent_w is None:
                pnl_usd = None
            elif qsym == "USDG":
                pnl_usd = round(val_w - ent_w, 2)
            else:
                pnl_usd = round((val_w - ent_w) * eth_usd, 2) if eth_usd else None
            rows.append({
                "tokenId": str(tid), "protocol": proto, "pool": pool, "pair": s.get("pair"),
                "quote_symbol": qsym,
                "pnl_pct": round(pnl, 2) if pnl is not None else None,
                "pnl_usd": pnl_usd, "eth_usd": eth_usd,
                "peak_pct": round(peak, 2), "in_range": in_range,
                "oor_min": round(oor_min, 1), "age_min": round(age_min, 1) if age_min is not None else None,
                "m5": m5, "h1": h1,
                "value_weth": val_w, "entry_weth": ent_w,
                "decision": "CLOSE" if reason else "HOLD",
                "reason": reason or "healthy — held by monitor loop",
            })
        report = {"positions": rows}
        if errors:
            report["error"] = "; ".join(errors)
        print(render_card(rows))
        print("MONITOR_REPORT:" + json.dumps(report))
        return

    state = load_state()
    now = time.time()
    # One request for the whole wallet, before the per-position loop — the
    # point of the oracle is that it does not scale with position count.
    krystal = fetch_krystal_positions()
    # Every position we were handed is live, whether or not its state read lands
    # below — a read failure means we could not SEE the position, not that it
    # closed, and pruning on that would reset its peak (see the prune at the
    # bottom).
    live = {state_key(proto, tid) for proto, _executor, tid in work}

    reads = read_states(work)
    # One GT request for every rung's momentum, before the decision loop (see
    # prefetch_momentum): the exit rules read the same two numbers they always
    # did, they just no longer cost a request each.
    prefetch_momentum([s.get("pool") for _, _, _, s in reads])
    # Ladder idle is judged per WALL, once per tick, before any rung is decided:
    # every rung of the wall then gets the same verdict on this same tick, so the
    # wall is never left half torn down. Rolls the walls' windows in `state`.
    wall_verdicts = judge_ladder_walls(
        ladder_walls([(tid, s) for _, _, tid, s in reads], krystal), state, now)

    for proto, executor, tid, s in reads:
        skey = state_key(proto, tid)
        pnl = s.get("pnlPct")
        in_range = bool(s.get("inRange"))
        age_min = s.get("ageMin")
        pool = s.get("pool")
        pair = s.get("pair") or f"#{tid}"
        qsym = s.get("quoteSymbol") or "WETH"

        ps = state.setdefault(skey, {"peak_pnl": 0.0, "oor_since": None})

        # Give up on a position whose close can never land, BEFORE any of the
        # per-tick work (momentum fetch, indicator read, decide) it would only
        # feed into another doomed attempt. See MAX_CLOSE_FAILURES.
        if ps.get("close_fails", 0) >= MAX_CLOSE_FAILURES:
            print(f"monitor: {proto} #{tid} UNCLOSABLE — skipped "
                  f"({ps['close_fails']} failed closes)")
            continue

        lid = s.get("ladderId")
        if lid:
            # Persist which wall this rung belongs to so the prune below can keep
            # the wall's window alive even on a tick whose state read failed.
            # Without it a transient RPC error orphans the wall key, silently
            # re-baselining the 90m window — the exact failure that parked a
            # fee-dead SPY wall for 6.7h on 2026-08-05.
            ps["ladder_id"] = str(lid)
            # The rung's own pre-rescoping idle_* snapshots are dead now that the
            # window is the wall's; drop them rather than leave a second, stale
            # baseline in the state file.
            for k in [k for k in ps if k.startswith("idle_")]:
                ps.pop(k, None)
        if pnl is not None and pnl > ps["peak_pnl"]:
            ps["peak_pnl"] = pnl
        peak = ps["peak_pnl"]

        if in_range:
            ps["oor_since"] = None
            oor_min = 0.0
        else:
            if ps["oor_since"] is None:
                ps["oor_since"] = now
            oor_min = (now - ps["oor_since"]) / 60.0

        m5, h1 = fetch_momentum(pool) if pool else (None, None)
        reason = decide(pnl, peak, in_range, age_min, oor_min, m5, h1, s, ps, now,
                        krystal.get(str(tid)), wall_of(s, wall_verdicts))

        # Pre-exit indicator confirmation (non-emergency exits only): postpone
        # the close while supertrend/RSI still read bullish — a dip inside an
        # uptrend, not a dump — but force it once the block outlives the cap.
        if reason and INDICATORS_ENABLED and exit_confirmable(reason) and pool:
            blocked_since = ps.get("ind_block_since")
            blocked_min = (now - blocked_since) / 60.0 if blocked_since else 0.0
            if blocked_min >= MAX_INDICATOR_BLOCK_MINUTES:
                print(f"monitor: {proto} #{tid} indicator exit block timed out after {blocked_min:.0f}m — forcing close")
                ps.pop("ind_block_since", None)
            else:
                # quote/quoteSymbol are passed so the indicator check can fall
                # back to the chain's own Swap logs when GeckoTerminal is rate-
                # limited (see local_indicators.fetch_onchain_candles). Without
                # them that fallback declines rather than guess: the raw pool
                # price is token1-per-token0, so it takes BOTH addresses to know
                # whether the series needs inverting, and an inverted series
                # reads a dump as a rally — it would postpone exactly the exits
                # this block exists to confirm. `quote` is the executor's
                # authoritative funded-side address (both v3 and v4 emit it);
                # quoteSymbol is the symbol fallback for older payloads.
                confirmed = check_local_indicators(pool, s.get("token"), "exit",
                                                   INDICATORS_PRESET, "24h", network="robinhood",
                                                   quote_address=s.get("quote"),
                                                   quote_symbol=s.get("quoteSymbol"))
                if confirmed is False:
                    print(f"monitor: {proto} #{tid} exit postponed ({INDICATORS_PRESET} rejected): {reason}")
                    if not blocked_since:
                        ps["ind_block_since"] = now
                    reason = None
                else:
                    if confirmed is None:
                        print(f"monitor: {proto} #{tid} indicator data unavailable — proceeding with exit (fail-open)")
                    ps.pop("ind_block_since", None)
        elif not reason:
            # Rule no longer fires — the dip resolved; a stale block must not
            # shortcut a future, unrelated exit straight to "timed out".
            ps.pop("ind_block_since", None)

        pnl_str = f"{pnl:.1f}%" if pnl is not None else "n/a"
        print(f"monitor: {proto} #{tid} pnl={pnl_str} peak={peak:.1f}% "
              f"{'in' if in_range else 'OUT'}range oor={oor_min:.0f}m "
              f"m5={m5} h1={h1} -> {reason or 'HOLD'}")

        if not reason:
            # Claim a turnover rung's fees once they are worth their own gas, so
            # they fund the next mint. Only on a HOLD: a position with a close
            # reason is about to have its fees collected by the close anyway.
            #
            # `in_range` is rare for this shape and that is correct, not a
            # missed case — a weth_below rung is out of range by construction
            # and earns nothing while it sits there, so there is nothing to
            # compound. It reads in-range only while being traded THROUGH, which
            # is exactly the moment fees are accruing. The bulk of the
            # compounding is elsewhere: a re-center redeploys the close's own
            # proceeds, fees included (see recenter()).
            if is_turnover(s) and in_range and not DRY_RUN:
                compound_fees(executor, tid, s, proto)
            continue

        if DRY_RUN:
            print(f"monitor: [dry-run] would close {proto} #{tid}: {reason}")
            continue

        # Keeping the token is what makes the re-list possible at all: the
        # executor's close sells the freed token side by default, and that sale
        # IS the -4.9% we are trying to stop paying.
        relist = wants_relist(reason, s)
        close_args = ["close", "--id", str(tid)]
        if relist:
            close_args.append("--no-swap-out")
        out, cerr = run_executor(executor, close_args, close_auth=True)
        closed = out and out.get("success")
        # A close can succeed while its token->WETH sell fails (rugged pool,
        # sell tax): the liquidity is out and the NFT burned, but the token side
        # is still a bag in the wallet. The executor journals it for `sweep`;
        # record it here too so the close journal never claims a clean exit that
        # actually left value behind.
        stranded = (out or {}).get("stranded")
        journal_close({
            "ts": int(now),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tokenId": str(tid), "protocol": proto, "pool": pool,
            "pnl_pct": round(pnl, 4) if pnl is not None else None,
            "peak_pct": round(peak, 4), "age_min": round(age_min, 1) if age_min else None,
            "reason": reason, "success": bool(closed), "dry_run": False,
            "swapped_out": bool((out or {}).get("swapped_out")),
            # weth_out is the v4 executor's alias for quote_out, so this stays
            # populated on both protocols; quote_symbol says what unit it is.
            "weth_out": (out or {}).get("weth_out"),
            "quote_symbol": (out or {}).get("quote_symbol", qsym),
            "stranded": stranded,
            # Set when the token side could not be transferred out of the pool
            # at all (a honeypot reverting `collect` with `TF`) and was left as
            # tokensOwed on a husk NFT. Unlike `stranded` there is nothing to
            # retry — the value never reached the wallet — so this is a write-off
            # the ledger has to see rather than a job for `sweep`.
            "unclaimed": (out or {}).get("unclaimed"),
            # Realized gas for the close transaction(s), in ETH, straight from
            # the executor's receipt meter. None on any build predating it.
            #
            # Journaled because the venue's ledger cannot be closed without it:
            # fee income and fill losses were both measurable from this file,
            # gas never was, so every net figure to 2026-08-08 carried an
            # estimate in place of its third term. Gas is always ETH even when
            # the position is USDG-quoted — it is the chain's fee token, not the
            # pool's quote — so it deliberately does NOT follow quote_symbol.
            "gas_eth": (out or {}).get("gasEth"),
            "gas_txs": (out or {}).get("gasTxs"),
        })
        if closed:
            ps.pop("close_fails", None)
            state.pop(skey, None)
            live.discard(skey)
            # Only a real, executed close cools a pool off — a failed close
            # leaves the wall standing, and blocking re-entry to a pool we are
            # still in would be the wrong brake on the wrong thing.
            cool_off(pool, s.get("token"), reason, pnl)
            # Turnover's re-center: the close was half of one operation, so
            # finish it before reporting. ONLY the two re-center reasons
            # (drift and fee-death) re-mint — a fill or the backstop SL is the
            # position telling us the pool changed, and re-pinning a bid under a
            # market that just came down through one is how a churn loop turns
            # into a bag-holding loop. (Mirrors dlmm_monitor.py's
            # is_oor_rebalance, which excludes exactly the same classes; the
            # `cool_off` above has already blocked re-entry on those.)
            # The ask leg. Runs before the re-center branch and returns through
            # the same `recentered` flag purely for the report verb; the two are
            # mutually exclusive by construction (wants_relist never matches a
            # `turnover re-center` reason).
            recentered = False
            if relist:
                recentered = relist_ask(executor, pool, s.get("quote"), pair)
            elif reason.startswith("turnover re-center"):
                realized = None
                ent, got = s.get("entryWeth"), (out or {}).get("weth_out")
                try:
                    if ent is not None and got is not None:
                        realized = float(got) - float(ent)
                except (TypeError, ValueError):
                    realized = None
                # Ask the breaker about the window BEFORE writing this close
                # into it. Recording first made the very first re-center of a
                # pool read its own number back and veto itself: on 2026-08-07
                # position #616818 booked -0.01747 (the executor's weth_out bug,
                # fixed in the same change) and recenter_ok declined on the
                # -0.004 floor with `recenters` at 1 and no prior history. The
                # breaker exists to stop a pool that has been bleeding ACROSS a
                # 24h window, not to judge the close it is attached to.
                allowed, why = recenter_ok(pool)
                cb_record(pool, realized)
                if allowed:
                    recentered = recenter(executor, pool, _f(got), s.get("quote"), pair)
                else:
                    print(f"monitor: re-center declined for {pair}: {why}")
            verb = ("📤 re-listed as ask" if (relist and recentered)
                    else "♻️ re-centered" if recentered else "🔴 closed")
            msg = f"{verb} Robinhood LP {pair} (#{tid})\n{reason}\npnl {pnl_str} peak {peak:.1f}%"
            if stranded:
                msg += (f"\n⚠️ {stranded.get('symbol', '?')} NOT sold — {stranded.get('reason', '?')}"
                        f"\ntoken {stranded.get('token')}\nqueued for sweep")
            else:
                msg += (f"\nsold for {(out or {}).get('weth_out', '?')} "
                        f"{(out or {}).get('quote_symbol', qsym)}")
            alert(msg)
            print(f"monitor: CLOSED {proto} #{tid}: {reason}"
                  + (f" [STRANDED {stranded.get('symbol')}]" if stranded else ""))
        else:
            # Count consecutive failures on this position. Reset on any success
            # above, so a pool that closes fine after a transient revert never
            # accumulates toward the cap.
            fails = ps.get("close_fails", 0) + 1
            ps["close_fails"] = fails
            print(f"monitor: CLOSE FAILED {proto} #{tid} ({fails}/{MAX_CLOSE_FAILURES}): {cerr}")
            if fails >= MAX_CLOSE_FAILURES:
                # Alert exactly once — the skip at the top of the loop means
                # this branch cannot be reached again for this position.
                alert(f"⛔ Robinhood LP {pair} (#{tid}) UNCLOSABLE\n"
                      f"{fails} failed closes, last: {cerr}\n"
                      f"position left open on-chain — needs manual recovery")
                print(f"monitor: {proto} #{tid} marked UNCLOSABLE after {fails} failed closes")

    # Drop peak/oor state for positions no longer open (closed elsewhere) —
    # but never for an executor whose positions read failed this tick: its
    # positions are missing from `live` because we couldn't see them, not
    # because they closed, and pruning would reset their peaks to zero.
    failed = {e.split(":", 1)[0] for e in errors}
    keep = set()
    for key in state:
        if key.startswith(LADDER_WALL_PREFIX):
            continue
        proto = key.split(":", 1)[0] if ":" in key else "v3"
        if key in live or proto in failed:
            keep.add(key)
    # A wall's idle window is keyed by ladderId, so it is never in `live` (which
    # holds position keys). Keep the walls still referenced by a surviving rung,
    # read off that rung's persisted ladder_id — dropping a wall key silently
    # restarts its 90m window, which is how a fee-dead wall sat 6.7h on
    # 2026-08-05 with no rule able to release it. When a wall's last rung closes
    # its position key goes, so the wall key goes with it on the same tick.
    keep |= {ladder_wall_key(lid) for lid in
             ((state.get(k) or {}).get("ladder_id") for k in keep) if lid}
    for key in list(state.keys()):
        if key not in keep:
            state.pop(key, None)
    save_state(state)


if __name__ == "__main__":
    main()
