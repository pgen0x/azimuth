# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A standalone Go daemon (`azimuth`) that polls Meteora's public DLMM pool-discovery
API, screens pools through quality gates, dedups, and hands each poll cycle's
*batch* of newly-qualifying pools to one of two sinks:

- **Webhook mode** (default): one HMAC-signed webhook per batch to a Hermes
  agent (logic in `assets/hermes/`), which ranks the batch, picks one pool +
  strategy, and deploys via the skill in `assets/skill/`.
- **Direct-deploy mode** (`DEPLOY_CMD` set): the daemon runs
  `dlmm_pipeline.py --from-batch` itself — the pipeline re-ranks the batch
  deterministically (same heuristics the agent prompt encoded) and deploys the
  strongest survivor in seconds instead of an LLM agent turn.

This daemon owns **entry signals only** — exits are the `dlmm_monitor.py`
cron's job.

**Where the LLM sits.** Nowhere in entry: the pick is deterministic
(`dlmm_pipeline.py` via `DEPLOY_CMD`). In exit it has exactly one power, and
only ever a subtractive one — the `sol_dlmm_ai_exit_review` cron (5m) may
DEFER a non-emergency close by 10-20 minutes via
`dlmm_monitor.py --override-hold`, and may do nothing else. The rules stay
authoritative: the emergency SL floor, rug velocity, thin liquidity and a
trailing drop >= 3% all bypass a hold in code. Every hold is journaled
(`<profile>/memories/ai_holds.jsonl`) and counted onto the eventual close
record as `ai_holds`, so held and unheld closes stay comparable.

Its second role writes no state at all: the `sol_dlmm_daily_proposal` cron
(21:00 WIB) reads a precomputed evidence brief
(`assets/hermes/scripts/sol_dlmm_proposal_brief.py`) and **proposes** threshold
changes to the operator over Telegram. It is declared with **no toolsets** —
withholding `terminal` is what makes "propose, never apply" structural instead
of a sentence in a prompt, and it also stops the agent re-reading the journal,
which is what keeps it citing the brief rather than inventing figures. The
brief does every calculation itself and marks thin samples, unmeasurable
sections and a below-noise-floor lift as explicitly *not* evidence; proposing
nothing is the expected output most days. Restoring the LLM's entry role is
deliberately NOT next — that path was removed for cause (fabricated deploy
reports) and needs an on-chain existence check first.

## Build / run

```bash
go build -o azimuth .              # build the daemon
go vet ./...                   # vet
set -a && . ./.env && set +a   # load env (fish: use bass or `env` prefix)
./azimuth                          # run (reads config from environment)
./install.sh ~/.hermes/profiles/dlmm   # wire assets into a Hermes profile + build
```

Go tests exist for `internal/deploy` and `internal/robinhood`
(`go test ./internal/...`); there is no Makefile. All config is environment-driven (`internal/config`,
defaults in `.env.example`); nothing is hardcoded except the screening
thresholds.

## Runtime services + logs

In production nothing runs in a terminal — everything is a **user** systemd unit
(`systemctl --user`, *not* system-level; `sudo systemctl` will report "unit not
found"). `loginctl enable-linger $USER` is what keeps them alive across logout.

| unit | what it is | installed by |
|---|---|---|
| `azimuth` | the `azimuth` daemon in this repo (entry signals) | `install.sh` ← `assets/systemd/azimuth.service` |
| `azimuth-sol-monitor` | 20s Solana exit loop (`dlmm_monitor_loop.sh`) — the real safety net | `install.sh` ← `assets/systemd/azimuth-sol-monitor.service` |
| `azimuth-rh-monitor` | Robinhood Chain exit loop (`uni_monitor_loop.sh`); installed disabled | `install.sh` ← `assets/systemd/azimuth-rh-monitor.service` |
| `hermes-gateway-<profile>` | Hermes gateway that receives the webhook, and ticks the profile's cron jobs | Hermes, not this repo |

Units named after other agents (e.g. a separate LLM LP agent) may also be
running on the same box; they are **not** this repo's and `install.sh` must
never write them.

```bash
journalctl --user -u azimuth -f          # live tail
journalctl --user -u azimuth -n 200 --no-pager
journalctl --user -u azimuth -u azimuth-sol-monitor -f   # both
journalctl --user -u azimuth --no-pager | grep -E 'DEPLOYED|DRY RUN|REJECT'
systemctl --user status  azimuth
systemctl --user restart azimuth          # after `go build`
```

A unit can be `active` while `is-enabled` says `disabled` — it is running now
but will not come back after a reboot. Check both before assuming a box is
self-healing; `systemctl --user enable <unit>` fixes it.

## Architecture

Pipeline is a single loop in `internal/scanner`: `poll ▸ screen ▸ dedup ▸ forward`,
one pass per enabled mode per `POLL_INTERVAL`.

- `internal/config` — env → `Config`. Only enable-toggles live here; screening
  thresholds live in `internal/meteora`.
- `internal/meteora`
  - `discover.go` — builds the discovery API query. `buildFilters` pushes mode
    thresholds into the API's `filter_by` param (API-side prefilter), but
    `Screen` re-checks **every** gate locally — the API filter is best-effort.
  - `screen.go` — the gate logic and `ModeParams` (`Casual`, `Multiday`). This
    is a **verbatim port** of the Python `dlmm_pipeline.py` config.
    When changing gates or thresholds, keep them in sync with that upstream, or
    note the divergence — the comments cite where each value came from.
    Two modes are this daemon's own: `Turnover` (30m, `category=all`,
    `sort=fee:desc`) and `Pulse` (5m, `category=trending`) — a port of the
    reference bot's screen. Same TVL/mcap/holder band, different discovery
    window, so they surface largely disjoint pools; running both makes entries
    the **union** of the two screens. Gates only some modes want (volatility
    ceiling, yield-decline, warning severity, verified) are zero-disabled
    `ModeParams` fields, so a new mode that omits one silently opts out — set
    them explicitly.
  - `momentum.go` — best-effort DexScreener downtrend gate (fail-open).
  - `audit.go` — best-effort Jupiter token-audit gate (fail-open): hard-rejects
    >30% bot holders, enriches signals with bot % + global fees paid.
  - `pvp.go` — best-effort same-symbol rival detection (fail-open, advisory):
    flags candidates whose ticker is contested by an established token with
    its own live DLMM pool (`is_pvp` + rival stats); never rejects.
  - `types.go` — JSON structs mirroring the discovery API response exactly.
- `internal/robinhood` — second venue: Uniswap v3 WETH pools on Robinhood Chain
  (chain ID 4663). **Two modes, two discovery sources** — no single feed spans
  both theses, which is why `pollRobinhood` takes an `rhFetcher`:
  - `Fresh` (`discover.go`) — newly-created pools via GeckoTerminal
    `new_pools`. A launch feed: a pool scrolls off it within minutes.
  - `Mature` (`mature.go`, `ROBINHOOD_MATURE`) — established pools (24h+) still
    printing outsized fee/TVL, via Uniswap's keyless interface GraphQL gateway,
    which indexes **nothing younger than a day**. One gateway call + one
    GeckoTerminal `/pools/multi/` enrich call per cycle; the local prefilter is
    what keeps the enrich to a single request. Sets `FeePaceH24` — the fee pace
    comes from realized 24h volume, because extrapolating an h1 window would let
    one busy hour fake a 24× daily rate.

  - `Ladder` (`ROBINHOOD_LADDER`) — the `weth_ladder` thesis: N contiguous
    **one-sided WETH** rungs parked on the bid side, sized on a linear ramp,
    minted atomically — one `NPM.multicall` on v3; on v4 one `modifyLiquidities`
    unlock carrying N `MINT_POSITION` actions and a single `SETTLE_PAIR`, so the
    quote is pulled once instead of N times. It never buys the token, so its exits are
    re-pins (`ladder stale` / `ladder rung filled` / `ladder idle` — the last
    one because the first two are price rules that a frozen market disarms;
    an equity ladder held 5.6h fee-dead overnight before it existed), not
    SL/TP, and a rung is
    out-of-range **by design** — the fee-dead OOR timeout must never apply to
    it. A **fill is a wall event, not a rung event** (2026-08-07): the first
    rung to convert closes every rung of that `ladderId` (`ladder wall
    breached`), because the rest are resting bids under a market that just came
    down through one — six of eleven observed fills were a repeat in a pool
    that had already filled, averaging -11.8% against -6.7% for the first. A
    fill past `UNI_LADDER_FILL_HARD_PCT` skips indicator confirmation, and a
    fill-class close (never `idle`/`stale`, which ARE the re-pin loop) writes a
    Redis re-entry cooldown the daemon reads at deploy time. Discovery is the **union of two feeds** (`trending.go`): `Mature`'s
    gateway feed plus the cached GeckoTerminal `trending_pools` page, which
    carries v3 pools the gateway does not index at all. The page costs no extra
    GT request while `Fresh` runs — `discover.go` already fetches it and now
    publishes it to a shared, rate-limited cache. Screens on churn, not yield: the
    8%/day bar matched 1 of the 23 pools a profitable ladder LP actually
    worked. This replaced `balanced_tight` as the deploy default, which was long
    a bleeding token by construction. See `docs/ROBINHOOD_CHAIN_PLAN.md` §4b.
  - `StockLadder` (`ROBINHOOD_STOCK_LADDER`) — the same wall, `usdg_ladder`,
    under the chain's **USDG-quoted tokenized equities** (nvda, gme, spacex).
    Same gateway feed; a separate mode because every `Ladder` threshold is
    wrong for a deep, low-vol book (0.2%/day vs 1.5%, $20k floor, 240-tick
    rungs vs 1200). The stock universe spans **all three fee tiers** — of the 12
    pools this mode has minted into, 3 were 0.05% (spacing 10), 6 were 0.3% (60),
    3 were 1% (200) — and one underlying often lists at two or three at once, so
    it can hold several position slots (no per-token cap yet). `rungWidth`
    quantizes to whole spacings, so a 240-tick request collapses to 200 on the 1%
    tier: covered drop per rung is per-tier, and the executor's ladder log line
    is the only honest source for a wall's real width. It spends the wallet's
    **USDG**, so sizing uses `RobinhoodSizeUSDG` (dollar units). §4c.

  - `PulseLadder` (`ROBINHOOD_PULSE_LADDER`) — the same WETH wall as `Ladder`,
    one age band earlier: memecoin pools **1h-24h old**, handing off at exactly
    24h (`PulseLadder.MaxAge == Ladder.MinAge`, asserted by a test). It needs a
    discovery source no other mode does, because **neither feed can answer
    "which WETH pools are three hours old"** — measured 2026-08-06, `new_pools`
    returned 33 WETH pools and every one was 1-5 minutes old, while the gateway
    indexes nothing under a day. So `pulse.go` keeps a **carried registry**:
    every launch sweep records pools by identity + creation time, and each cycle
    the entries that have aged INTO the band are re-enriched in one
    `/pools/multi/` call. Only identity survives the carry — every number a gate
    reads is re-fetched, and an entry the enrich did not refresh is dropped
    rather than screened on launch-minute data. The registry is **mirrored to
    Redis** (`rh:young:<pool>`, one key per pool, TTL = the pool's *remaining*
    24h window, so Redis expires an entry when `pruneWatch` would): entries are
    only useful once they are `MinAge` old, so a process-memory-only registry
    left the mode blind for an hour and thin for a day after every restart.
    In-memory stays authoritative; the store only seeds it at startup. Geometry is unchanged
    (`uni_ladder.js` keys on the quote asset, not the mode): if a soak shows a
    first-day pool wants a different wall, add per-strategy geometry, not a
    second WETH constant.

  - `Turnover` (`ROBINHOOD_TURNOVER`) — **the venue's earning thesis as of
    2026-08-07**, and the port of Solana `turnover`: **ONE one-sided WETH rung**
    (`weth_below`) resting adjacent to spot in an oscillating pool, **re-pinned**
    when price drifts off it or it stops earning, rather than closed. It
    replaced the ladders on evidence, not taste — 104 live ladder rung closes
    produced **zero** fee-positive exits (63 `ladder idle`, 30 `ladder stale`,
    11 fills averaging −9.48%). The diagnosis is *not* "one-sided doesn't work":
    the on-chain fee meter shows the rung NEAREST spot earning (GME rung 0:
    0.002039 USDG/214m) while outer rungs read exactly 0. Two thirds of a wall's
    capital sat where the market never came. One rung concentrates it there, and
    the re-pin loop is what keeps it there. The mode pins its own strategy in
    `sizeFor` instead of inheriting `ROBINHOOD_DEPLOY_STRATEGY`; that pin is also
    what keeps `balanced_tight` — which pre-swaps half the commit into the
    memecoin and lost −15.04%/trade holding it — out of a mode screened for
    churn. Solana settled the same question: `select_batch_strategy()` ends in an
    unconditional `return "sol_bidask"`, every mode single-sided.
    Discovery is the **union of two feeds** (`ranked.go`): `Mature`'s gateway
    feed with a turnover-band prefilter, plus GeckoTerminal's plain pool list
    sorted by 24h volume (`/pools?sort=h24_volume_usd_desc`, 4 pages on a 10m
    refresh, cached and rate-limited exactly like `trending.go`). Two pages until
    2026-08-13, when screening the full ranking showed the FEED DEPTH was the
    binding constraint rather than the gates: pages 1-2 carry 21 WETH-quoted
    candidates of which 4 clear every gate, pages 1-4 carry 39 of which 10 do.
    Volume rank is not thesis rank — the head of this book is its DEEPEST pools,
    which is exactly where a re-pinned rung earns least, so the mode's real
    candidates live in the tail. Five pages was tried live and reverted: the
    keyless tier's budget is a ~4-request burst, `refreshRanked` runs BEFORE the
    gateway arm's enrich, and a 429 trips a GLOBAL GT pause — page 5 spent the
    enrich's request and the cycle logged `gateway=0 ranked=36`. The 10m refresh
    is what bounds the surviving collision to one cycle in ten. The gateway ranks by TVL, which
    sorts hardest for the deep books where a small position earns least; a churn
    mode is paid `fee_tier x volume`, so it needs a volume ranking. Measured
    2026-08-08: of the 19 pools this mode minted into over the preceding two
    days, only **2** appeared anywhere in the venue's top 60 by volume — it was
    screening a fringe of the book and calling it the book. The ranked page's
    head is full of things that must never be minted (WETH/USDG with no token
    side, `pons-v2-dex`, sub-$500-TVL husks posting four-digit turnover), so
    `mapGTPools` drops the wrong DEXes and `Screen` drops the rest: this is a
    ranking, never a gate. Polled BEFORE the ladders so a spent GeckoTerminal
    budget starves the comparison arm first.

    Ranking is also this mode's own: `RankByFeeDensity` replaces the score's
    liquidity term with a second, squared fee-density term. Depth is a virtue
    for a mode holding inventory for days (it is the exit liquidity it will
    need) and a cost for a re-pinned rung (our fee share is our liquidity over
    the pool's), so the default ranking was preferring the pool that pays us
    less. `MinReserveUSD` is what keeps the husks out once depth stops scoring.

    **Geometry is `uni_ladder.js`'s `TURNOVER_RUNG_TICKS`** (600 WETH ticks,
    ~5.8% of covered drop — half a ladder rung, because a re-pinned rung buys
    density where a wall buys depth), laid by the same `ladderBands()` with
    `rungs=1` so the bid-side direction invariant has one implementation. It is
    **out of range by design and there is no OOR fuse**: v3/v4 cannot mint
    one-sided liquidity across spot (a straddling range computes
    `liquidity = min(L(amount), L(0)) = 0`), unlike DLMM's `sol_bidask` which
    includes the active bin — so a 2-minute fuse would close and re-mint forever.
    `turnover_decide` therefore reuses the LADDER rulebook — `rung_fill_state`,
    `ladder_idle_reason` — and only the *response* differs:

    | test | ladder | turnover |
    |---|---|---|
    | filled | close + cooldown | close + cooldown (never re-pin under a market that just came down through the bid) |
    | drift > stale ticks | tear down | **re-center** |
    | earned nothing in a window | tear down | **re-center** |

    Its whole viability is the **re-center loop in `uni_monitor.py`**, which
    this venue did not have until now. Both re-center reasons share the
    `turnover re-center` prefix, which is what the close path routes on: they
    are deliberately NOT in `exit_confirmable` (confirmation would stall the
    cadence, and the rung is pure quote so there is no sell to time) and NOT in
    `cool_off` (cooling the pool would switch the mode off), and they are the
    ONLY reasons that re-mint. Mirrors `dlmm_monitor.py`'s `is_oor_rebalance`
    exclusions. Guarded by a per-pool 24h circuit breaker
    (`rh:turnover:{recenters,pnl}:<pool>`) that fails **CLOSED** — unlike
    `cool_off`, a re-center is optional work on top of an already-completed
    close, so an unreadable window means take the normal exit. Fee compounding
    is `collect`-to-wallet, not Solana's in-place increase: neither executor has
    an `increaseLiquidity` path, and a loop whose holding period is minutes
    recycles the fees into the next mint anyway.

    **No fill reason is confirmable** — `exit_confirmable` now holds only the
    two-sided momentum exits (`trailing exit` / `fast-out` / `downtrend`).
    Fills were confirmable until 2026-08-08 on the sound argument that an
    un-filling rung costs nothing while a round trip costs the fee tier twice;
    218 closes refute it. A fill that closed on its own rule averaged
    **-3.81%** (n=5); one postponed here first averaged **-9.77%** (n=9), and
    six of those nine are in the postponement log, held by a bullish
    supertrend/RSI read until they crossed the -8% hard floor. 422 postponements
    in three days bought back nothing. A fill IS token inventory, which is the
    one thing a one-sided strategy exists never to hold, so it is hard risk like
    SL/TP and the fee-dead OOR timeout.

    **Sizing is per-POOL, not just per-wallet** (`ROBINHOOD_TENURE_*`,
    `robinhood.TenureParams`). `ComputeDeployAmount` says what the wallet can
    afford; the tenure ramp says which pools have earned it. Bucketing the
    venue's own 24 WETH pools by cycles survived, full-cycle (bid spend against
    every WETH the pool paid back, so the ask recovery counts) — `>=20 cycles:
    13.0% fill, +6.50%` / `8-19: 22.9%, -0.35%` / `3-7: 39.4%, -5.04%` / `1-2:
    42.9%, -21.90%`. Monotonic, and it is one fact stated twice: a pool that
    survives many re-centers is genuinely oscillating (the thesis), one that
    fills on cycle 1-2 was trending and we were its exit liquidity. **The
    selection was never wrong** — all 24 passed the same screen — the
    allocation was: the 18 pools under 8 cycles took 54% of the spend at full
    size. So under `PROBE_CYCLES` a pool mints a floor-sized probe, between the
    bars half, at `FULL_CYCLES` the full percentage; and `MAX_FILL_PCT` vetoes a
    pool outright, which is the long horizon the 4h `cool_off` cooldown cannot
    see (a 40%-filler keeps clearing it and coming back). Counters are written
    by `uni_monitor.py`'s `note_tenure` (`rh:tenure:{cycles,fills}:<pool>`,
    rolling 7d) and read in `scanner.sizeFor`. Ask-side closes are NOT cycles —
    they work a bag an earlier fill handed over, and counting them would credit
    a pool with tenure it earned by losing. Unknown tenure (no Redis) keeps FLAT
    sizing and never vetoes: probing everything at the floor forever is a
    different strategy, not a safe default, and blocking on missing data is what
    starved Solana on 2026-08-07.

    **Gas is metered** (`noteGas` / `gasReport` in both executors, journaled by
    `uni_monitor.py` as `gas_eth` / `gas_txs`). It was measured nowhere before
    2026-08-08 while the loop churned ~200 tx/day, so the venue's net was
    always fee income minus fill losses minus a guess. Metered BEFORE the revert
    check — a reverted tx still burns gas — and gas is always ETH even for a
    USDG-quoted position, so it deliberately does not follow `quote_symbol`.
    The two executors keep separate copies; what must stay identical is the
    payload FIELD NAMES, not the code (`uni_ladder.js` is geometry and stays
    free of receipt concerns).

  Modes are quote-pinned via `ModeParams.QuoteAsset` — a ladder's rungs and its
  sizing must be the same asset, so a mode may not mix WETH- and USDG-quoted
  pools in one batch. The pin goes through `quotePinMatch`, not an address
  compare: **ether has two spellings** on this venue (the v3 ERC-20 wrapper and
  the v4 zero address, both reported as "WETH"), and a WETH pin means "LPs
  against ether". An exact compare made the WETH ladders blind to v4 — 68 of
  the 70 pools the pulse registry carried on 2026-08-07 were native-ETH — even
  though `sizeFor` and the v4 executor (`ensureNativeFunds` / `rewrapExcess`)
  were already built to fund a native-quote mint from the WETH balance. **USDG is 6 decimals, WETH is 18**: anything touching
  amounts in `uni_executor.js` must go through `parseQ`/`fmtQ`, never
  `parseEther` (the v4 executor uses `parseUnits`/`formatUnits` at `q.decimals`
  for the same reason).

  Both ladder modes screen v3 **and** v4 pools, and both executors mint the
  shape. Its geometry lives in `assets/skill/scripts/uni_ladder.js`, required by
  both — rung count/width/floor/ramp describe the thesis, not the protocol, and
  `uni_monitor.py`'s `ladder stale` rule reads the same widths. Change it there,
  never in one executor. §4d.

  All three ladder modes also gate on the **live 15-minute window**
  (`MinTxM15` / `MinVolumeM15USD` / `MinFeeTVLM15Pct`) — the port of Solana
  `Pulse`'s `(MinFeeActiveTVL, MinVolumeUSD)` pair, and the fix for the mode's
  dominant failure: 91 of 102 ladder closes earned exactly zero, and every one
  of those pools passed the h1 and 24h gates at mint. `MinFeeTVLM15Pct` is
  window-scoped, NOT annualized — comparing it to `MinFeeTVLDay` is a units
  error. Costs no extra request (GT already returns `volume_usd.m15`).

  All four modes share `Screen` and every safety gate (GMGN OpenAPI
  `chain=robinhood` security + holder quality, Blockscout holders). The deploy
  pick also passes a supertrend/RSI entry-timing gate (`indicators.go`, the Go
  port of the skill's `local_indicators.py` — keep them in sync; fail-open,
  `ROBINHOOD_INDICATOR_GATE`), and `uni_monitor.py` confirms non-emergency
  exits through the same indicators before closing. Phase 1 is
  **observe-only** (`ROBINHOOD_ENABLED`, batches journal to the log;
  `ROBINHOOD_WEBHOOK` forwards them) and NEVER routes to `DEPLOY_CMD` — the
  pipeline is Solana-only. One deliberate divergence from the fail-open rule:
  a POSITIVE honeypot/blacklist/sell-tax detection hard-rejects; unknown still
  passes. Plan + phase status: `docs/ROBINHOOD_CHAIN_PLAN.md`.
- `internal/store` — `Seen` dedup set: Redis (`SetNX`, one key + TTL per pool)
  or in-memory map. Empty `REDIS_ADDR` selects in-memory.
- `internal/webhook` — HMAC-SHA256 forwarder. Signature scheme
  (`hex(HMAC-SHA256(secret, body))` in `X-Webhook-Signature`) must match the
  Hermes/gobot side; the shared secret is `HERMES_WEBHOOK_SECRET`.
- `internal/deploy` — direct-deploy runner: execs `DEPLOY_CMD` with
  `--from-batch <payload> --mode <mode>` per batch, parses the pipeline's
  `🚀 DEPLOYED` / `🧪 DRY RUN DEPLOY` stdout markers, and pipes a condensed
  outcome to `REPORT_CMD` (e.g. `hermes send -t telegram`). Execution failure
  unmarks the batch for retry; a deterministic REJECT does not.
- `assets/` — copied into a Hermes profile by `install.sh`, which rewrites the
  literal `__PROFILE__` token to the target path. `assets/skill` = solana-dlmm
  skill (Python pipeline/monitor + JS executor); `assets/hermes` = the webhook
  subscription (agent decision prompt).

## Conventions that matter

- **Batch, not per-pool.** One cycle emits all fresh candidates as a single
  signal array so the agent compares the set. Don't revert to first-come
  per-pool sends.
- **Dedup before momentum fetch** — avoids hitting DexScreener for already-seen
  pools. On webhook failure, the whole batch is `Unmark`ed to retry next cycle.
- **Fail-open gates.** `verified` / Jupiter shield / momentum treat missing data
  as passing (`boolOr(..., true)`). Preserve this — the API omits these fields
  for some tokens and failing closed would over-reject.
- **A price feed names a POOL, not a token.** DexScreener's token endpoint
  returns every venue a mint trades on, dead ones included, and the order is
  not a contract. Never read `pairs[0]`: match our exact `pairAddress` when we
  hold the position (`dlmm_monitor.get_pool_liquidity_usd` — no match means
  *unknown*, never a substitute pool), and take the DEEPEST pair when all we
  have is a mint (`dlmm_pipeline.get_momentum`, `meteora.momentumFrom`). Paired
  with that, a short-window change at or below `IMPLAUSIBLE_CHANGE_PCT` (-95%,
  mirrored in all three) is a bad read rather than a move and is nulled to
  unknown; h6/h24 are exempt, because a token really can be down 99% in a day
  and nulling that would walk a corpse past the downtrend gate. Not a nicety —
  a husk pool's honest -99.96% read as ours fired the rug-velocity rule on
  healthy positions, and since that rule blacklists via `rug_event`
  (PnL-independent, by design) each false read cost a 7d mint ban plus a 30d
  deployer ban. Eleven such bans starved Solana of every entry for 12h on
  2026-08-14 while the comparison bot entered the same pools green. Pinned by
  `internal/meteora/momentum_test.go`.
- **Redis TTL is per-key on purpose.** `SetNX` per pool gives each an independent
  rolling `SEEN_TTL`. The old `SAdd`+`Expire` refreshed the whole set's TTL every
  write so pools were deduped forever — see the comment in `store.go`; don't
  reintroduce a single-key set.
- **No hidden clock reads.** `webhook.Send` takes `nowUnix` from the caller.
  Keep time injection at the edges.
- **Webhook payload is a contract** documented in `docs/SIGNAL_SCHEMA.md`.
  Update that doc when changing the emitted shape.
- **`pnl_pct` is not money.** In `uni_closes.jsonl` it is a percentage against the
  position's *marked* value, so a close that ended holding an unsellable token can
  read +90% while returning almost no quote, leaving behind a token side no venue
  will buy. Four closes did exactly that. The arbiter is the pair added
  2026-08-13: `realized_quote` (quote out minus quote in, so no price opinion can
  enter it) and `pnl_basis` (`"mark"` when the close left `stranded`/`unclaimed`
  value behind). Sum `realized_quote` over `pnl_basis == "realized"` rows; treat
  `null` as unmeasurable and count it, never as 0.0. Use `pnl_pct` for ranking
  only. The same trap sits in third-party position trackers, whose net worth
  counts zero-market dust rows — including impostor tokens that spell their symbol
  like a real quote asset — at a stale print.
- **A one-sided rung settles in quote.** `--no-swap-out` exists in both executors
  but the monitor never passes it: the re-list that kept filled bags was retired
  2026-08-13 (see the note by `ASK_BAG_STOP_PCT`). Closes that ended in quote
  returned +7.8% of the quote they spent; closes that kept the bag returned half
  of it. A fill is settled at the one moment the pool is provably tradable — it
  has just traded through our rung.

## Security

Wallet keys never live in this repo — the skill reads `SOLANA_PUBLIC_KEY` /
`SOLANA_PRIVATE_KEY` from the Hermes profile `.env` at runtime. Keep
`HERMES_WEBHOOK_SECRET` matched on both daemon and subscription. Trades real funds.
