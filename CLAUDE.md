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
    it. Discovery is the **union of two feeds** (`trending.go`): `Mature`'s
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
    rungs vs 1200 — every stock pool traded so far is the 0.3% tier at
    tickSpacing 60, so USDG rung widths quantize to multiples of 60). It spends the wallet's **USDG**, so sizing uses
    `RobinhoodSizeUSDG` (dollar units). §4c.

  Modes are quote-pinned via `ModeParams.QuoteAsset` — a ladder's rungs and its
  sizing must be the same asset, so a mode may not mix WETH- and USDG-quoted
  pools in one batch. **USDG is 6 decimals, WETH is 18**: anything touching
  amounts in `uni_executor.js` must go through `parseQ`/`fmtQ`, never
  `parseEther` (the v4 executor uses `parseUnits`/`formatUnits` at `q.decimals`
  for the same reason).

  Both ladder modes screen v3 **and** v4 pools, and both executors mint the
  shape. Its geometry lives in `assets/skill/scripts/uni_ladder.js`, required by
  both — rung count/width/floor/ramp describe the thesis, not the protocol, and
  `uni_monitor.py`'s `ladder stale` rule reads the same widths. Change it there,
  never in one executor. §4d.

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
