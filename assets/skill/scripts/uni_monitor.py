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
        })
        w["rungs"].append(str(tid))
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


def _idle_window(ps, now, kind, level, basis=None):
    """Snapshot-and-compare a monotonic `level` over LADDER_IDLE_WINDOW_MIN,
    judged against `basis` (defaults to the snapshot itself, i.e. relative
    growth). Returns a close reason, or None to hold — rolling the window
    forward in `ps` as a side effect.

    `ps` is the WALL's state dict for a laddered rung (ladder_wall_key), so one
    window covers the whole wall; only a rung with no ladderId still snapshots
    into its own position state."""
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
    return (f"ladder idle: +{growth_pct:.4f}% {kind} in {window_min:.0f}m "
            f"(< {LADDER_IDLE_MIN_PCT}%) — wall untraded, re-pin")


def ladder_idle_reason(s, age_min, ps, now, kry=None):
    """Close reason when a resting WALL has earned nothing across a full window,
    or None. Rolls the measurement window forward in `ps` as a side effect —
    `now` is a unix time.

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
        return (f"ladder idle: zero fees in {age_min:.0f}m since mint "
                f"(>= {LADDER_IDLE_WINDOW_MIN:.0f}m) — wall untraded, re-pin")

    if kry and kry.get("fees_usd") is not None and kry.get("value_usd"):
        return _idle_window(ps, now, "fee", kry["fees_usd"], kry["value_usd"])

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
            return (f"ladder idle: zero on-chain fees in {age_min:.0f}m since mint "
                    f"(>= {LADDER_IDLE_WINDOW_MIN:.0f}m) — wall untraded, re-pin")
        value_q = s.get("valueWeth")
        if value_q:
            return _idle_window(ps, now, "chain_fee", fees_q, value_q)

    value = s.get("valueWeth")  # quote units despite the name (executor contract)
    if value is None or value <= 0:
        return None
    if bool(s.get("inRange")):
        # Mid-conversion: value tracks price, not fees. Rebaseline and wait.
        ps["idle_value_snap"], ps["idle_value_at"] = value, now
        return None
    return _idle_window(ps, now, "value", value)


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
        out[lid] = {"idle": ladder_idle_reason(w["state"], w["age_min"], ps, now, w["kry"])}
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
    # quoteIs0 is the current field; wethIs0 is its pre-USDG name, still emitted
    # by the executor (and the only one an older v4 build sends).
    quote_is0 = bool(s.get("quoteIs0", s.get("wethIs0")))
    qsym = s.get("quoteSymbol") or "WETH"
    stale_ticks = LADDER_STALE_TICKS.get(qsym, LADDER_STALE_TICKS["WETH"])
    rung = s.get("rung") or 0
    width = hi - lo
    # Which tick direction fills the rung depends on token ordering, the same
    # invariant ladderBands() mints on: the quote as token0 means a RISING tick
    # makes the token cheaper, so the ladder sits above spot and fills upward.
    if quote_is0:
        filled, gap = tick >= hi, lo - tick
    else:
        filled, gap = tick <= lo, tick - hi

    if filled:
        # Fully converted: this rung is now pure token inventory, which is the
        # one thing the strategy exists to avoid holding. Sell it back. This is
        # indicator-confirmable on purpose (see exit_confirmable) — if price
        # recovers the rung un-fills back into WETH on its own, for free, so
        # waiting out a bullish dip strictly beats crossing the spread twice.
        return f"ladder rung filled (tick {tick} past [{lo},{hi}])"

    drift = gap - rung * width
    if drift > stale_ticks:
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

    "ladder rung filled" joins the confirmable set because its close is a SELL
    into weakness that the market may undo for us: an un-filling rung costs
    nothing, a round-trip through the pool costs the fee tier twice. "ladder
    stale" and "ladder idle" do not — dead capital does not get better by
    waiting, and an idle rung has already waited a full window.
    """
    return reason.startswith(("trailing exit", "fast-out", "downtrend", "ladder rung filled"))


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


def fetch_momentum(pool):
    """Best-effort GeckoTerminal price-change windows for a pool. Returns
    (m5, h1) percent, or (None, None) — missing data never fires a rule."""
    url = f"https://api.geckoterminal.com/api/v2/networks/robinhood/pools/{pool}"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            d = json.load(resp)
        pc = d["data"]["attributes"]["price_change_percentage"]
        return float(pc.get("m5") or 0), float(pc.get("h1") or 0)
    except Exception:
        return None, None


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
    the original path unchanged.

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
                confirmed = check_local_indicators(pool, s.get("token"), "exit",
                                                   INDICATORS_PRESET, "24h", network="robinhood")
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
            continue

        if DRY_RUN:
            print(f"monitor: [dry-run] would close {proto} #{tid}: {reason}")
            continue

        out, cerr = run_executor(executor, ["close", "--id", str(tid)], close_auth=True)
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
        })
        if closed:
            state.pop(skey, None)
            live.discard(skey)
            msg = f"🔴 Robinhood LP closed {pair} (#{tid})\n{reason}\npnl {pnl_str} peak {peak:.1f}%"
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
            print(f"monitor: CLOSE FAILED {proto} #{tid}: {cerr}")

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
