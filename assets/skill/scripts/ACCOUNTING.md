# Solana accounting and review

Run commands through the profile scripts path, or pass `--profile` explicitly.

```sh
python3 ~/.hermes/profiles/solanza/skills/solana-dlmm/scripts/dlmm_accounting.py --refresh --hours 24
python3 ~/.hermes/profiles/solanza/skills/solana-dlmm/scripts/dlmm_shadow.py
python3 ~/.hermes/profiles/solanza/skills/solana-dlmm/scripts/dlmm_evaluate.py --start START_EPOCH --end END_EPOCH --output REVIEW_DIRECTORY
```

## Accounting basis

The executor journals signed submissions before broadcast. The read-only collector
reconciles finalized wallet transactions and caches their actual balance changes,
fees (including failed transactions), SPL movements, and account creation costs.
Missing transactions are unresolved; duplicate signatures count once. External
native transfers are classified only when all instructions prove a simple transfer.
Unrecognized/manual operations block flow-adjusted performance and root promotion.

Marked NAV = native SOL + current SPL marks/quotes + Meteora open LP balance and
unclaimed fees + recoverable token/position account reserves. SPL marks use batched
Jupiter prices bounded by observed timestamp and price slot; at most ten missing
marks per pass fall back to full-balance quotes. Stale, absent or changing snapshots
return null NAV plus a known-asset subtotal. Marked NAV is not liquidation proceeds.
Wealth change subtracts external flows between the first and last complete marks;
it is not an annualized return or a closed-position ROI.

Each root report separates LP PnL, swap native cash movement, token inventory movement,
network fees, nonrefundable account costs, and final cash settlement. Cash already
includes fees and net rent movements: never subtract those costs twice. Root cash
PnL conservatively charges rent still held in recoverable accounts; portfolio NAV
includes those reserves separately. The difference from LP PnL combines settlement
valuation and execution effects; it is not described as pure slippage or IL.

Historical transactions/positions without complete provenance remain unmeasured.
The 60-transaction per-pass fetch budget resumes from the durable wallet cache;
coverage is incomplete until the whole interval has been fetched. Trading during a
multi-source snapshot invalidates it. Collector services never send transactions.

## Root policy

All deploy callers with a root/recenter link use the same gate before signing.
The gate refreshes transaction coverage without fetching all wallet price quotes.
It requires reconciled entry/close evidence, no unsettled token inventory, fresh
wallet coverage, the full-root strike/loss budget, and observed 30-minute fee
opportunity greater than cumulative cash loss plus the next cycle's average observed
execution cost. Missing evidence or fee pace stops the reentry. Existing exit paths
remain available. This is a conservative cost guard, not a promise of future fees.

`dlmm_root_decisions.jsonl` persists the evidence, cost, strikes and reason.
`dlmm_recenter_decisions.jsonl` preserves the earlier eligibility decision and market
inputs. Replay filters on observation time, not merely transaction block time;
future-fetched facts cannot justify historical decisions. Unknown historical cases
remain unknown; no counterfactual profit is invented for paths not executed.

## Shadow study

Scanner cooldown, momentum, audit and bundler/insider rejects preserve full candidate,
pool and gate evidence under stable five-minute cohort IDs. Repeated IDs count once.
Forward horizons are pulse 30 minutes, turnover 1 hour, casual 4 hours, multiday 24
hours. Outcomes collected more than ten minutes late are censored. The reported
false-rejection *proxy* is a pool-price gain above a fixed 1% hurdle, with measured,
pending, unmeasured and censored denominators. It is not simulated LP profit.

Entry bin state is captured before broadcast; subsequent bin states retain reserves,
supply and fee-growth counters. Fixed uniform, near-active and far-active allocations
are replayed under an infinitesimal fixed-share assumption. Results show fees,
inventory change, HODL-relative IL, sampled OOR, utilization and observed-cost-adjusted
PnL where costs exist. Empty/reset/missing bins are unmeasured. Price impact and
hypothetical recenter/slippage costs are not inferred. Live weights are unchanged.

## Operations

`azimuth-sol-accounting.timer` and `azimuth-sol-shadow.timer` collect outside the
trading loop. Unit templates target the solanza profile; adapt the path elsewhere.
Evaluation writes `report.md`, `evaluation.json`, and redacted runtime logs. Optional
`--reference-wallet` adds the same full-life LP cohort for Meridian; LP comparison
is explicitly separate from Azimuth wallet NAV. No reports are automatically sent.

Use an isolated checkout for development: the live profile scripts are symlinks.
