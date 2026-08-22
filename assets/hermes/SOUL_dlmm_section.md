## 9. Meteora DLMM LP Ingestion & Management Parameters

Before any DLMM pool is ingested or monitored, these rules and parameters are applied.

Pipeline supports three modes with **isolated position budgets** — each mode's positions do NOT block the other modes' slots.

### Casual Mode Parameters (30m timeframe — volume spike plays, hold 2-6h)
*   Casual Min TVL: $5,000
*   Casual Min Fee/TVL: 0.3%
*   Casual Min Mcap: $250,000
*   Casual Min Holders: 500
*   Casual Max Positions: 3

### Multiday Mode Parameters (24h timeframe — quality holds, target 24h+; screens every 4h)
*   Multiday Min TVL: $50,000
*   Multiday Min Fee/TVL: 1.0%
*   Multiday Min Mcap: $1,000,000
*   Multiday Min Holders: 1,000
*   Multiday Max Positions: 3

### Turnover Mode Parameters (30m timeframe — fee-capture on small high-fee pools, hold hours)
*   Turnover Min TVL: $5,000 / Max TVL: $300,000
*   Turnover Min Fee/TVL (30m window): 0.15% (~7%/day pace)
*   Turnover Min Base Fee: 1.0% (degen fee tier; fee income is the thesis, not price)
*   Turnover Min Mcap: $150,000 (the daemon's own screen passes 150k-10M; a higher floor here is a second, silent screen over what discovery already found. It ran at $1,000,000 until 2026-08-10 and cost the mode its entry rate — 18 opens in 24h against a reference bot's 50 on the same band, off 2-9 pools per cycle)
*   Turnover Min Holders: 500
*   Turnover Max Positions: 2
*   Prefer tight ranges around active bin (balanced_tight two-sided) — profit is fee_pct × turnover, so stay in range; exit on turnover decay, not price targets

### Shared Ingestion Gates
*   Minimum Base Organic Score: 60 (GLOBAL, not per-mode — it re-screens every pool the daemon already cleared at organic >= 50/60, so a higher value here starves entries across all modes at once. Was 75 until 2026-08-10; the escalation rule below still raises it during a losing streak)
*   Slippage: 1000 (bps, e.g. 10% slippage tolerance)

### Entry Conviction & Learning
*   Lone-Candidate Conviction Floor: 50 (degen score 0–100; a signal cycle producing exactly ONE fresh pool only emits it above this — "only option" is not "good option")
*   Audit Gate: reject > 30% bot holders (daemon-side); reject global fees < 30 SOL when the value is present (agent-side — bundled/scam line; absent = unknown, never reject on absence)
*   Pool Memory: never re-enter a pool whose last closes (>= 2) net out negative PnL
*   Repeat-Deploy Cooldown: 3rd deploy into the same pool within 24h → 12h pool cooldown
*   Signal Weights: darwinian — entry signals of every close are correlated with realized PnL (60d window, recalc <= 1×/6h); the deploy pick prioritizes candidates strong on high-weight signals (`sol:dlmm:signal_weights`)

### Active Strategy Configuration
*   Strategy: sol_bidask (options: sol_bidask, spot, custom_ratio_spot, balanced_tight, single_sided_reseed, fee_compounding, partial_harvest, stage_aware) — sol_bidask is the single-sided SOL bid-ask ladder (~35% downside coverage, zero token exposure at entry); the batch pick table also defaults every thesis mode to it (turnover keeps balanced_tight). Narrowed from ~70% on 2026-08-14: every one of the 23 deploys in the preceding 48h printed "Bins Below | 100", the clamp, and bid-ask weights liquidity toward the FAR end — so most of each ticket sat 30-60% below spot where the market never came, earning nothing ($6.25 fees/24h against the reference bot's $19.32 on comparable capital) and, worse, keeping the position INSIDE its range through 18-24%/h dumps so the 5m OOR fuse could never fire. A hard 20% coverage floor still applies at small bin steps, where a fixed bin count buys too little price
*   Indicators Enabled: true (enable indicator timing checks before entry/exit)
*   Indicators Preset: supertrend_break (timing presets)

### Exit Parameters
*   Hard Stop-Loss: -8.0% (unconditional floor — no trend confirmation, no second leg. Tightened from -25.0 on 2026-08-12: the wide floor assumed the fast rails owned the tail, but the sustained-downtrend rail needs a 1h trend to confirm and so fired at -15.64% and -8.34% on a rule written for -5%, leaving nothing unconditional between -5% and -25%. Six closes produced a full day's loss while 33 others returned ~0. Grace applies only to a young in-range position with fee/TVL ≥ 10%; an EMERGENCY floor 3pp below this always closes immediately — bypasses grace, AI holds, indicator timing, and report-only mode)
*   Downtrend PnL-Only Floor: -6.0% (the sustained-downtrend exit on PnL alone, no 1h confirmation — sits between the confirmed -5% rule and the hard SL. Fixed in monitor, not read from here; listed so the exit ordering is legible: confirmed downtrend -5%, unconfirmed -6%, hard floor -8%, emergency -11%)
*   Downtrend Tight Floors: -2.5% confirmed / -3.0% PnL-only (turnover + pulse, the same set that gets its own trailing pair. For these modes the PnL-only leg is the PRIMARY rail, not the fallback: measured over the 24h to 2026-08-14, all four downtrend closes left through the CONFIRMED leg and every one fired with h1 already at -12.8 / -18.1 / -22.2 / -23.9%, so the -2.5% tolerance never got to speak. A one-sided SOL position moves ~1/5 of the token, so PnL crosses -2.5% long before DexScreener's h1 window has aggregated the decline that authorises the close. Booked PnL was -2.80 / -4.48 / -4.57 / -5.21% against a win band of 1.2-2.5% — -0.0821 SOL from those 4 closes against +0.0374 SOL from the other 23, i.e. the whole day's loss. Fixed in monitor, not read from here. Tight ordering: unconfirmed -3% usually first, confirmed -2.5% only when h1 arrives early enough to matter, hard floor -8% unchanged)
*   Trailing TP Trigger: 3.0% (activate trailing exits once profit exceeds this; tune against your own close history — set too high, trailing never activates before another rule cuts the position)
*   Trailing TP Drop: 1.5% (floor below peak before the first ratchet tier; above +5% peak the monitor's profit ratchet takes over: peak ≥5% locks +2%, ≥10% locks +6%, ≥20% locks 70% of peak)
*   Peak-Giveback Stop: peak >= +0.5%, give back >= 1.5% (turnover + pulse only, fixed in monitor, added 2026-08-19. The rail under the arming threshold: a tight-mode position only arms the ratchet at +1.2%, so everything peaking between +0.5% and there had no downside rule at all until the downtrend leg at -2.5%/-3%. That gap is where the losers live — of the four worst closes in the 24h to 2026-08-19, three peaked at +0.51/+0.75/+0.76% and booked -4.12/-3.32/-3.27%. Over the preceding 7d the rule fires on 8 of the 12 closes worse than -1% (-0.133 SOL between them) against 2 eventual winners worth +0.011 SOL that dipped that far and recovered. Never a take-profit: the giveback lands near flat, under the 0.3% minimum lock, so it does not route the TP path. Bypasses AI holds — a 10-20m defer turns it back into the -3% close it exists to pre-empt)
*   Underwater Fast-Out: 5m <= -3.0% with PnL <= -1.5% (turnover + pulse only, fixed in monitor, added 2026-08-19. The armed fast-out's mirror image. `downtrend` is the biggest real loss bucket in the 7d to 2026-08-19 — 9 closes, 0% win rate, -0.257 SOL — and it books -4.82% on average against triggers of -2.5%/-3.0%, because a one-sided SOL position that is underwater IS a token bag and the close swaps it out at the bottom of the move that tripped the level. This leg reads the same velocity the armed rule does and fires while the move is still happening, instead of waiting for the level to arrive. Stays well above the rug-velocity rail at -20%, which remains the emergency class. Fail-open: missing m5 never fires. Bypasses AI holds for the same reason as the giveback stop)
*   Max Bins Pumped Above: 10 (exit if active bin exceeds upper bin by this count)
*   Max Out of Range Minutes: 30 (UPSIDE fuse only — above range the position is 100% SOL with PnL frozen, so patience is free; a banked gain ≥ +1.5% closes immediately via the OOR-upside profit lock)
*   OOR Downside Max Minutes: 5 (asymmetric fast fuse — below range every bin has filled into a token bag losing value each tick; sell everything before the decay compounds. The one-shot green-5m-candle recovery grace still applies; close routes through the dump path: 2h cooldown, no re-center)
*   Turnover Max OOR Minutes: 5 (turnover-mode fast fuse, TOKEN side — below range every bin has filled into a decaying bag, so it closes into a re-center rather than riding the long fuse above. Raised 2 -> 5 on 2026-08-12, matching the SOL-side value below: the measurement that set that one was never direction-specific, and all 21 token-side OOR closes in the preceding 24h fired at 2.1-2.2m for an average of +0.0006 SOL — the fuse was round-tripping capital for zero before a fee could accrue, paying gas and slippage each trip)
*   Turnover SOL-Side OOR Minutes: 5 (the same fuse on the SOL side, where nothing decays. Running the 2m fuse in both directions cost the mode its upside: over the 24h to 2026-08-10 its six SOL-side OOR closes averaged +0.01% — out before a fee accrued — while the same event waited out to 5m elsewhere averaged +0.04%, and the pumps held rather than cut averaged +0.38%. The +1.5% OOR-upside profit lock now applies to turnover too, and a profitable close still routes back into the re-center)
*   Turnover CB Loss SOL: -0.015 (turnover rebalance circuit breaker — once a pool's cumulative realized PnL across rebalance closes in the last 24h drops below this many SOL, re-centering stops and normal exit + pool cooldown applies. Was -0.05 against a 20/24h count backstop and neither ever fired: over the 24h to 2026-08-14 the worst single pool lost -0.0288 SOL across its ENTIRE re-center run, so the floor could not be reached before the run ended on its own)
*   Turnover Re-center Strikes: 3 (per pool per 24h — the count is now a real guard, not a backstop. A turnover pool's run reads as a ladder of crumbs ending in one full-size loss: over the 24h to 2026-08-14 five of the six pools entered more than once had their LARGEST loss as the LAST entry — OnlyMarms -0.43 +3.23 -0.07 +0.10 -2.80; Niles -0.77 +2.90 -4.48; cc +0.14 -4.57; MARIO64 -0.03 -5.21. A re-pinned rung is a bid resting under a market: while the pool oscillates it earns ~0.1%, and when the pool finally trends it hands back 4-5% at once, so bounding the run bounds how many times we offer that trade. Matches the reference bot's oorCooldownTriggerCount, which works the same book and took no downtrend close at all in the same window)
*   Turnover Strike Cooldown Hours: 12 (exhausting the strikes — or tripping the breaker above — cools the POOL, not just the symbol. The symbol cooldown can be as short as 15m after a profitable exit, and the daemon would re-signal the same pool straight into a fresh run. Matches the reference bot's oorCooldownHours and the pipeline's own repeat-deploy churn guard, which never saw these runs because a monitor re-center never passes through the deploy path)
*   Turnover Max Hold Minutes: 60 (turnover-only stale-ticket re-pin, added 2026-08-17. Closes a ticket that is still in range, has never armed the ratchet, and is past this age — the one state no other rule can speak into, because the OOR fuse needs OOR, the tight yield bar is 5% against pools reading 20-35%, fee-pace-death cannot fire before 75m, and the ratchet needs a 1.2% peak. Left alone such a ticket sits until the -2.5% downtrend rail, which is a loss rule doing a staleness rule's job: WOFL-SOL sat 94.0m and MEOW-SOL 73.8m in exactly that state and left at -2.65% / -2.82% with fee/TVL still above 19%. 60m is where the mode's own outcomes stop improving — median PnL by hold bucket over 457 closes runs +0.13% / +0.24% / +0.10% / -0.19% for <30m / <60m / <120m / >=120m, win rate 68.4 / 69.7 / 51.3 / 42.9 — so the bar cannot touch the two best buckets, which closed before it, and its blast radius is the 67 closes past 60m whose combined realized PnL is -0.0064 SOL. Not an exit: the reason carries no loss keyword, so a profitable close re-pins through the existing churn leg while a losing one exits with a cooldown. It spends the shared re-center budget, and a refused ask cools the pool for the strike window. Turnover-only on purpose — pulse's equivalent holds already leave through Low yield at its 30m grace)
*   Min Age for Yield Check: 60 minutes
*   Pulse Min Age for Yield Check: 30 minutes (pulse-only override — pulse enters off a 5-MINUTE trending window, so an hour of grace is more than an order of magnitude longer than the signal it acted on. A pulse pool not paying by 30m was never screened as a slow starter. Added 2026-08-13 after Solana turnover was switched off on 08-12 and the pulse-only book's median hold ran 4.7m -> 60.9m -> 136.8m: those holds were in range with PnL inside the trailing trigger, so no OOR fuse and no ratchet could fire and this grace was the only clock running. ASTEROID-SOL read fee/TVL 0.63% at 54m with no exit rule available until minute 60. No hard max-hold accompanies it — both closes past 300m in the journal are winners)
*   Min 24h Fee/TVL for Yield Check: 1.0% (exit if age exceeds minimum and fee/TVL drops below this)
*   Tight Min 24h Fee/TVL for Yield Check: 5.0% (turnover + pulse override — the same set that gets its own trailing pair. 1.0% is a solvency bar, not an earning bar: at that pace a pool pays back 1% of TVL a day, of which our share is our liquidity over the pool's. A fee-capture ticket earns by turning over, so a pool that has decayed to that pace is not a slow window to sit through, it is a slot another candidate should have. Measured over the 24h to 2026-08-14: 11 of 27 closes sat past 54m and the book logged ZERO "Max positions reached" aborts against 196 cycles of "already exposed to all winners" — throughput was bounded by how long each ticket sat, not by slot count, so this bar is the throughput lever. The reference bot holds the same book to 7% and turns capital over twice as fast for it: median hold 20.6m against 33m, 47 closes/24h against 27, on FEWER slots. Set below its 7% because our exit also has the fee-pace-death rail underneath, which reads realized SOL rather than the pool's advertised ratio)
*   Income-death exits skip indicator confirmation (fixed in monitor): `Low yield` and `Fee pace death` close immediately instead of waiting on a supertrend/RSI exit read. A price indicator has nothing to say about a stopped fee stream, and postponing turns a position earning nothing into a position earning nothing that also carries token risk for up to another hour. Same verdict Robinhood reached on fills 2026-08-08. Measured 2026-08-12/13: 282 then 164 postponement ticks, 67-SOL blocked ~52m, ASTEROID-SOL ~20m, STONKS-SOL ~19m — and the episodes stack, because the block key clears on each confirm and the next block restarts the 60m timeout from zero. An AI hold can still defer these; that suppression is bounded to 20 minutes and journaled
*   Min Exit Liquidity: $7,000 (exit if live pool liquidity drains below this after entry — can't exit cleanly; set below the $10k entry TVL gate so fresh positions never trip it)
*   Rug Velocity Gate (fixed in monitor): 5m candle ≤ -20% → EMERGENCY close, same class as the emergency SL floor. It used to be the argument for a wide hard SL; since 2026-08-12 it is a complement to a tight one — it catches the token dying faster than any PnL threshold can, while the SL catches the ordinary bleed it was never built to see
*   Fee-Pace-Death Exit (fixed in monitor): after 45m age, unclaimed-fee growth < 0.02% of position value across a 30m window (≈ <1%/day pace) → rotate the capital out; skips trailing-armed winners, re-baselines on fee claims
*   Permanent Rug Blacklist (fixed in monitor, 2026-07-22): fires on a realized close ≤ -30% PnL, OR on any close whose reason names a rug pattern (e.g. the velocity gate above) regardless of realized PnL — a fast reaction can book a near-zero loss on a token that just cratered, and that crater alone is rug evidence

### Close GUARD — hold the healthy winner (applies to EVERY actor)

This GUARD overrides every exit parameter above and binds all of me — the cron monitor, the
interactive/gateway agent, and any manual action:

*   **NEVER close a position when ALL of these hold:** `in_range == true` AND `fee_per_tvl_24h >= 10%`
    AND no hard exit rule has triggered (`triggered_rules` empty). A young, in-range position earning
    high fees is healthy — HOLD it regardless of a small unrealized drawdown. Closing a fresh,
    in-range, high-fee winner is the single worst error I can make (it is the Joby-class bug).
*   **Do not discretionarily close** an empty-`triggered_rules` position unless `5m price <= -3%`
    (real dump) OR `break_even_days >= 5`. A mild pullback (e.g. -2.9% 5m) is NOT a close trigger.
*   **Hard floor:** `pnl_pct < -8%` (the Hard Stop-Loss above) always closes; a 5m candle
    ≤ -20% (rug velocity gate) always closes; thin-liquidity (< Min Exit Liquidity) always
    closes (can't exit later is worse than forgone fees).

### Exit ownership — single chokepoint

*   **Only `dlmm_monitor.py` may close a DLMM position.** It applies this GUARD, then sets the
    `DLMM_CLOSE_AUTH` token the executor requires. A raw `dlmm_executor.js close` is REFUSED.
*   The interactive/gateway agent must **NOT** close DLMM positions on request or its own judgment —
    the monitor owns all exits. If asked to close one, defer to the monitor / explain the GUARD,
    and only `--force` on explicit, deliberate human override.
*   The spot fast-monitor (`monitor_positions.py`) operates a **separate** keyspace and must never
    touch a DLMM base-token bag (it excludes active DLMM base mints).
