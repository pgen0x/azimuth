---
name: solana-dlmm
description: |
  Autonomous Meteora DLMM pool screening and position management.
  Filters candidates, deploys concentrated liquidity, and tracks ranges.
trigger:
  - "solana dlmm"
  - "meteora dlmm"
  - "solana lp"
  - "dlmm portfolio"
---

# Solana DLMM Liquidity Provision Skill

## Overview
Automated lifecycle of a Solana Meteora DLMM concentrated liquidity position:
Screen Pools (Fee/TVL, TVL, Volatility, Base Token Safety Gates) → Deploy Single-Sided SOL LP Position → Monitor Active Bins / PnL → Exit Out-of-Range or SL/TP positions → Account realized yields.

## Scripts Directory
`<profile>/skills/solana-dlmm/scripts/` (symlinked to this repo's `assets/skill/scripts/` by `install.sh` — edit here, it's live everywhere)

---

## Tools & Commands

2026-07-22 strategy merge: ground truth from the Meteora portfolio API (30d,
119 closes) showed 47.9% winrate / PF 0.84 / net -0.34 SOL — a loss tail (9
closes <= -8%) and zero-fee churn, both structural (position shape + exit
shape), not screening thresholds. Entry now defaults to `sol_bidask`
(single-sided SOL ladder, zero token exposure at entry); exits gained a fast
rug-velocity gate (5m <= -20% = emergency close) and a fee-pace-death exit,
which let the hard SL widen back out to -25% as a deep backstop instead of
the primary tail defense. Robinhood venue and turnover mode stay off
(negative edge in their own ground truth) and momentum entry gates stay
tightened (5m <= -3%, 1h <= -7%, 6h <= -10%, 24h <= -20%).

### 1. `dlmm_pipeline.py` — Ingestion Pipeline
**Purpose**: Screens Meteora's pool discovery API and deploys into the best candidate.
**Command**: `python3 ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_pipeline.py --mode <casual|multiday>`

Two modes with **isolated position budgets** (2 slots each, max 4 total):

**`--mode casual`** (30m timeframe — volume spike plays, hold 2-6h):
*   TVL >= $5k, Fee/TVL >= 0.3%, Mcap >= $250k, Holders >= 500, Max 2 positions

**`--mode multiday`** (24h timeframe — quality holds, target 24h+):
*   TVL >= $50k, Fee/TVL >= 1.0%, Mcap >= $1M, Holders >= 1,000, Max 2 positions

**Shared filters (both modes)**:
*   Organic Score >= 75, Volatility 0–15
*   Momentum: reject if 5m <= -3% or 1h <= -7% (tightened 2026-07-20 after downtrend entries dominated losses)
*   Downtrend gate: reject if 6h <= -10% or 24h <= -20%
*   Verified + Jupiter shield (fail-open if API omits field)
*   Dev balance <= 20%, top-10 holders <= 60%, no freeze/mint authority, no critical warnings

**Flags**: `--analyze-only` (screen only, non-blocking), `--pool <ADDR>`, `--strategy <NAME>`

**Batch mode (`--from-batch '<payload array>' --mode <mode>`)**: consumes the
azimuth daemon's whole signal batch and replaces the LLM agent's pick step —
deterministic conviction re-rank (dev-exit / global-fees / PVP hard rejects,
GMGN boosts+penalties, darwinian signal weights from Redis), strategy chosen
from the same table the agent prompt used, and runner-up fallback when a live
gate (bin-array rent, entry timing) rejects the top pick. Used by the daemon's
`DEPLOY_CMD` direct mode.

**Entry memory gates (all modes, incl. `--from-signal` / `--from-batch`)**:
*   Symbol cooldown (`sol:dlmm:cooldown:<SYMBOL>`) and pool cooldown (`sol:dlmm:cooldown:pool:<POOL>`) — skip while set.
*   Pool memory: skip a pool whose journaled closes (`sol:dlmm:history:pool:<POOL>`) show >= 2 past closes netting negative PnL — this pool already cost us.
*   Repeat-deploy churn guard: the 3rd deploy into the same pool within 24h sets a 12h pool cooldown.
*   Every deploy snapshots the winning candidate's entry signals into the position record (`signal` field) — feeds the darwinian weights (see `dlmm_weights.py`).

### 2. `dlmm_monitor.py` — Position Monitor
**Purpose**: Monitors all open positions in Redis and checks SL/TP or Out-of-Range limits.
**Command**: `python3 ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_monitor.py`
**Exits managed**:
*   Stop-Loss: SOUL `Hard Stop-Loss` (currently -25%, widened 2026-07-22 — a deep backstop now that the fast rails below own the tail; fallback constant also -25%).
*   Rug velocity gate: 5m price change <= -20% (`RUG_M5_PCT`) — emergency close NOW, same class as the emergency SL floor. Fail-open on missing 5m data.
*   Take-Profit: Price rises >= +50% from entry price.
*   Out of Range: asymmetric fuse by pool geometry (sol_bidask is single-sided, so the two OOR directions mean opposite things). SOL-side OOR (fully converted to SOL, PnL frozen) gets the patient SOUL `Max Out of Range Minutes` fuse (currently 45m) plus a profit lock — `pnl_pct >= +1.5%` closes immediately, banking the frozen win. Token-side OOR (full token bag, decaying every tick) gets the fast SOUL `OOR Downside Max Minutes` fuse (currently 5m); one one-shot green-5m-candle grace extension, then closes via the dump path. Orientation must be positively known (`meta.sol_is_x`) — unknown defaults to the patient fuse.
*   Fee-pace-death exit: after 45m age, unclaimed-fee growth < 0.02% of position value across a 30m window (≈ <1%/day pace) — rotate dead capital out. Skips trailing-armed winners, re-baselines on fee claims, fail-open on missing Portfolio-API fee data.
*   Thin Liquidity: Live pool liquidity drains below $7k floor (SOUL.md `Min Exit Liquidity`) — exit before the position strands. Re-checked every cycle; fail-open on fetch error.
*   Fast-out dump exit: trailing TP armed + 5m price change <= -3% + PnL >= +0.3% lock — realize the profit immediately instead of letting the dump gap through the ratchet floor between ticks. Fail-open on missing 5m data.
*   Trailing TP: activates at SOUL `Trailing TP Trigger` (currently 4%); exit floor is a profit ratchet (peak ≥5% locks ≥+3%, ≥10% locks ≥+7%, ≥20% locks 70% of peak, ≥30% locks 75%; below that, flat `Trailing TP Drop` from peak).
*   Emergency SL floor: 3pp below `Hard Stop-Loss` — always closes immediately, bypassing the SL grace, AI holds, and indicator timing. SL grace itself only applies to a young (<15m) in-range position with fee/TVL ≥ 10%.
*   Rug blacklist: a realized close <= -30% PnL, OR any close whose reason contains "rug" (e.g. the velocity gate above, regardless of realized PnL — a fast reaction can book a near-zero loss on a token that just cratered) — blocks the mint for `RUG_BLACKLIST_TTL_DAYS` (default 7d) via one TTL'd key per mint, `sol:dlmm:blocklist:mint:<MINT>`, and the deployer for `DEV_BLOCKLIST_TTL_DAYS` (default 30d) via one TTL'd key per wallet, `sol:dlmm:blocklist:dev:<WALLET>`. Both checked by the pipeline before every deploy. Each side was a permanent set once — the mint until 2026-08-07, the deployer until 2026-08-12 — because discovery recycles a small ticker pool and a small set of launchpad-scale deployers, so a monotonic blocklist eventually starves the mode of candidates, silently (every batch just reports no candidate). The deployer window is the longer of the two: a wallet that rugs once can mint again, which makes the claim stronger — but not permanent. A re-blacklist refreshes the window, so a repeat rug keeps its ban.
*   Note: `--report-only` is read-only — never claims/closes/redeploys (incl. fee_compounding & partial_harvest strategies) — with ONE exception: an emergency close (SL floor breach / rug velocity / thin liquidity) executes even in report-only, because the cron runs report-only and the agent hop adds minutes. Pass `--no-enforce` for pure reporting.
*   Every close is journaled to `<profile>/memories/dlmm_closes.jsonl` (uniform schema, API-verified PnL, carries the entry-signal snapshot) AND to per-pool memory `sol:dlmm:history:pool:<POOL>` (last 10 closes, 30d expiry — the pipeline's "past losses" skip gate reads this and fires when 2+ closes net at or below `POOL_MEMORY_NET_FLOOR_PCT`, default -10%; it fired on ANY negative sum until 2026-08-07, which rejected pools that had merely churned to a fraction of a percent below break-even; the daemon ships a summary as `prior_closes`/`prior_net_pnl_sol` on future signals for that pool). Audit journal vs Meteora portfolio API ground truth with `python3 .../scripts/dlmm_reconcile.py [--days 30]`.
*   A "Low yield" close also sets a 4h pool cooldown (`sol:dlmm:cooldown:pool:<POOL>`) — fee flow that already decayed doesn't recover within the 1h symbol cooldown, so block the pool itself from immediate re-entry.
*   Each run ends by triggering `dlmm_weights.py --quiet` (self-guarded, never fails the monitor).

**Close GUARD (overrides all exits above):** NEVER close when `in_range` AND `fee_per_tvl_24h >= 10%` AND no hard rule triggered. Do not discretionarily close an empty-`triggered_rules` position unless `5m <= -3%` OR `break_even_days >= 5`. Hard floor `pnl < -25%` and thin-liquidity always close. (Full policy: SOUL.md §9 "Close GUARD".) The `--override-close` path enforces this in code and refuses a healthy close unless `--force`.

**AI HOLD blocks `--override-close`:** If `ai_hold_active: true` in the report, do NOT call `--override-close` — the code will exit(2) and refuse. Only exceptions: (1) pass `--force` for genuine manual override, or (2) `pnl_pct <= -25%` (hard SL emergency, hold auto-bypassed by code). If conditions worsened to emergency, use `--force` and explain in `--reason`.

**Who sets an AI hold:** the `sol_dlmm_ai_exit_review` cron (every 5m). It is the LLM's ONLY authority over exits — it may defer a non-emergency close by 10-20 minutes and may do nothing else; it cannot close, claim, or deploy. Its pre-run script (`<profile>/scripts/sol_dlmm_exit_review_gate.py`, installed from `assets/hermes/scripts/`) emits `{"wakeAgent": false}` unless a position sits in a band *approaching* a suppressible rule, so most 5m ticks cost no model call. Those bands must stay ahead of the rules: the 20s loop closes on the same tick a rule fires, so a review that waited for `triggered_rules` would always arrive after the close. Every hold is journaled to `<profile>/memories/ai_holds.jsonl` and increments `sol:dlmm:position:<addr>:ai_hold_count` (7d TTL), which `log_close` stamps onto the close record as `ai_holds` — without that field, held and unheld closes are indistinguishable afterwards and the whole arrangement is unmeasurable.

**Exit chokepoint:** `dlmm_monitor.py` is the ONLY authorized closer — it sets `DLMM_CLOSE_AUTH` after the GUARD/rules pass. A raw `node dlmm_executor.js close <addr>` is REFUSED (exit 3) unless `--force`/`DRY_RUN`. The gateway agent and the spot fast-monitor must never close DLMM positions directly.

### 3. `dlmm_weights.py` — Darwinian Signal Weights
**Purpose**: Learns which entry signals predict winners. Correlates the entry-signal snapshots in `dlmm_closes.jsonl` (last 60d, needs >= 10 closes with both wins and losses) with realized PnL, producing a signed **lift** per signal; each weight then steps 35% of the way toward `1.0 + 3 × lift`, clamped [0.3, 2.5]. Persists weights **and lifts** to `<profile>/memories/signal_weights.json`, mirrored to Redis `sol:dlmm:signal_weights`, which the deploy pick reads when ranking candidates.

Two properties are deliberate, both applied 2026-08-13 after an audit found 10 of 14 weights sitting exactly on a clamp after 108 recalcs:
*   **Mean-reverting, not ratcheting.** A weight is a function of the CURRENT lift, so evidence that fades pulls it back toward neutral. The old ×1.05/×0.95 quartile ratchet compounded over stable quartile membership and could only ever end on the rails, after which no new evidence could move it.
*   **The learned set equals the applied set.** `SIGNAL_NAMES` here must stay identical to `WEIGHTED_SIGNALS_HIGHER_IS_BETTER` in `dlmm_pipeline.py`. Six non-directional signals (`volatility`, `mcap`, `tvl`, `fee_pct`, `swap_count`, `bot_holders_pct`) were learned but never applied, and because their lift went through `abs()` it was never negative — so they monopolised the boost quartile and pushed the signals that *do* score toward the floor. They are retired and pruned from stored state. Adding a signal here means teaching the pipeline to apply it, not just appending a name.

A weight near 1.0 is ambiguous on its own — "no evidence" and "evidence of no effect" both land there — which is why the `lifts` map is published alongside it and `--show` prints both columns.
**Commands**:
*   `python3 ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_weights.py --show` — print current weights
*   `python3 .../dlmm_weights.py --force` — recalc now (normally self-guarded to once per 6h, auto-run by the monitor)

### 4. `dlmm_executor.js` — SDK Transaction Executor
**Purpose**: Interacts directly with Meteora DLMM program on-chain. Invoked by Python runners. Supports RPC failover rotation.
**Commands**:
*   `node ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_executor.js active-bin <pool_address>`
*   `node ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_executor.js deploy <pool_address> <amount_sol> <bins_below> [bins_above]`
*   `node ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_executor.js claim <position_address>`
*   `node ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_executor.js close <position_address>`
*   `node ~/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/dlmm_executor.js positions`

### 5. `uni_executor.js` — Robinhood Chain (Uniswap v3) Executor
**Purpose**: EVM sibling of `dlmm_executor.js` for the Robinhood Chain venue
(chain ID 4663, see `docs/ROBINHOOD_CHAIN_PLAN.md`). Wraps ETH, swaps via
SwapRouter02, mints/collects/closes NonfungiblePositionManager positions.
Reads `EVM_PRIVATE_KEY` from the profile `.env` — either a 0x-hex secp256k1
key or a base58 Solana secret key (the 32-byte seed is reused as the EVM key
so one funded identity serves both venues). `DRY_RUN=true` skips all sends.
**Commands** (same profile path prefix as above):
*   `uni_executor.js address` — derived EVM address (fund this with bridged ETH)
*   `uni_executor.js balance` / `wrap --amount 0.05` — ETH/WETH balances, ETH→WETH
*   `uni_executor.js quote --pool 0x..` — pool tick/fee/price state
*   `uni_executor.js deploy --pool 0x.. --amount 0.01 [--strategy balanced_tight|weth_below|weth_ladder|usdg_ladder] [--range-pct 10] [--slippage 5] [--rung-ticks N]`
    *   `weth_below` = rh-turnover's single one-sided quote rung. Ignores
        `--range-pct`/`--slippage`: its width is `UNI_TURNOVER_RUNG_TICKS`
        (`uni_ladder.js`, overridable with `--rung-ticks`) and it never swaps.
*   `uni_executor.js positions` / `collect --id N` / `close --id N [--no-swap-out]`

---

## Redis State Keys

| Key | TTL | Purpose |
|---|---|---|
| `sol:dlmm:position:<ADDR>` | 7d | LP Position metadata: pool, pair, base_mint, base_symbol, entry_price, entry_bin, bins_below, bins_above, size_sol, deployed_at, tx_hash, strategy, **mode** (casual\|multiday) |
| `sol:dlmm:active_positions` | permanent set | All currently active DLMM position addresses |
| `sol:dlmm:position:<ADDR>:oor_since` | permanent | Timestamp when the position was first detected out of range |
| `sol:dlmm:pnl:daily:YYYY-MM-DD` | 7d | Realized yields tracker: total_sol, count_exits |
| `sol:dlmm:cooldown:<SYMBOL>` | 1-72h | Token re-entry cooldown set on close (dump closes 2h, others 1h; repeat losses escalate 24h/72h) |
| `sol:dlmm:cooldown:pool:<POOL>` | 4-12h | Pool-level cooldown: 12h repeat-deploy churn guard (pipeline), 4h low-yield close (monitor) |
| `sol:dlmm:deploys:<POOL>` | 24h | Rolling deploy counter per pool; 3rd deploy sets the pool cooldown |
| `sol:dlmm:history:pool:<POOL>` | 30d | Last 10 close outcomes per pool (`ts`, `pnl_pct`, `pnl_sol`, `mode`, `reason`) — pipeline's "past losses" skip gate |
| `sol:dlmm:loss_streak:<SYMBOL>` | 7d | Consecutive-loss counter per token, escalates the symbol cooldown |
| `sol:dlmm:signal_weights` | permanent | Learned signal weights (JSON), written by `dlmm_weights.py`, read by the deploy agent |
