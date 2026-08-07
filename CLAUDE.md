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
| `hermes-gateway-<profile>` | Hermes gateway that receives the webhook | Hermes, not this repo |

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
    2026-08-07**, and the port of Solana `turnover`: a TIGHT two-sided WETH
    range (`balanced_tight`) in an oscillating pool, **re-centered** on every
    out-of-range break rather than closed. It replaced the ladders on evidence,
    not taste — 104 live ladder rung closes produced **zero** fee-positive
    exits (63 `ladder idle`, 30 `ladder stale`, 11 fills averaging −9.48%),
    because a resting one-sided bid only earns when the market trades *through*
    it. The mode pins its own strategy in `sizeFor` instead of inheriting
    `ROBINHOOD_DEPLOY_STRATEGY`: screening for churn and then minting a shape
    that cannot collect it is the exact pairing that produced those 104 zeros.
    Shares `Mature`'s gateway feed with a turnover-band prefilter, and is polled
    BEFORE the ladders so a spent GeckoTerminal budget starves the comparison
    arm first.

    Its whole viability is the **re-center loop in `uni_monitor.py`**, which
    this venue did not have until now, and whose absence is what killed
    `balanced_tight` at −15.04%/trade — `uni_executor.js:1119` records
    two-sided positions closed by the 30m OOR timeout half an hour after
    minting. A churn strategy with no churn realizes every drift as a loss.
    So: `turnover re-center` is a distinct close reason, deliberately NOT in
    `exit_confirmable` (indicator confirmation would break the cadence) and NOT
    in `cool_off` (cooling the pool would switch the mode off), and it is the
    ONLY reason that re-mints — an SL/downtrend/trailing close is the pool
    telling us it changed, and re-minting into that turns a churn loop into a
    bag-holding loop. Mirrors `dlmm_monitor.py`'s `is_oor_rebalance` exclusions.
    Guarded by a per-pool 24h circuit breaker (`rh:turnover:{recenters,pnl}:<pool>`)
    that fails **CLOSED** — unlike `cool_off`, a re-center is optional work on
    top of an already-completed close, so an unreadable window means take the
    normal exit. Fee compounding is `collect`-to-wallet, not Solana's in-place
    increase: neither executor has an `increaseLiquidity` path, and a loop whose
    holding period is minutes recycles the fees into the next mint anyway.

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
- **Redis TTL is per-key on purpose.** `SetNX` per pool gives each an independent
  rolling `SEEN_TTL`. The old `SAdd`+`Expire` refreshed the whole set's TTL every
  write so pools were deduped forever — see the comment in `store.go`; don't
  reintroduce a single-key set.
- **No hidden clock reads.** `webhook.Send` takes `nowUnix` from the caller.
  Keep time injection at the edges.
- **Webhook payload is a contract** documented in `docs/SIGNAL_SCHEMA.md`.
  Update that doc when changing the emitted shape.

## Security

Wallet keys never live in this repo — the skill reads `SOLANA_PUBLIC_KEY` /
`SOLANA_PRIVATE_KEY` from the Hermes profile `.env` at runtime. Keep
`HERMES_WEBHOOK_SECRET` matched on both daemon and subscription. Trades real funds.
