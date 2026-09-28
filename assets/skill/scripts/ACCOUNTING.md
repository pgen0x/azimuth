# Solana accounting and review

Unlinked cleanup swaps can be attributed to a root only when finalized transaction
balances show an exact sale of its entire residual inventory, one closed root is
the sole recorded owner, and wallet coverage is complete and fresh. Shared mint
balances, partial sales, unresolved submissions, same-mint external inflows and
missing transaction-time balances remain unresolved. Attribution is recorded in
`cleanup_settlements`; it never edits the original event journal. Cash proceeds
and fees are counted once. Historical replay still uses evidence observation time.

Unsigned, read-only-wallet SPL credits made solely through known transfer/ATA
instructions are classified as `external_token_inflow`. They do not invalidate
unrelated bot root chains. A chain touching the same mint during the inflow stays
incomplete pending attribution, even if its recorded token deltas net to zero.
Wallet wealth change remains unmeasured across such inflows: neither donated
tokens nor externally funded ATA reserves are trading profit. Unknown programs,
authority changes, outflows, wallet signatures or SOL changes remain unclassified.

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

## September 26 evaluation corrections

- Executor authorization replay uses its persisted post-refresh evidence; the earlier
  pre-settlement eligibility replay is reported separately. Historical facts are not backdated.
- Root fee pace starts observing at the first fresh portfolio sample, independently
  of exit triggers, and still requires a full 30-minute window. Missing opportunity
  has its own reason, separate from insufficient measured fees.
- Missing finalized transaction responses remain pending without declaring an RPC
  outage. Expired submissions are excluded from cash flows only with complete
  finalized wallet history, a finalized height beyond signed expiry captured before
  the history scan, and a history-enabled null signature status. RPC errors never
  prove non-landing. Failed landed transactions still count their fees.
- Read-only, unsigned Bubblegum activity with no native/SPL balance involvement is
  classified outside the SOL/SPL/LP asset scope. NFTs are excluded, not valued at zero.
- The ten-quote fallback budget rotates between missing accounts; errors and budget
  deferrals are recorded separately. Unavailable token prices still leave NAV null.

Quote fallbacks are paced at least 1.1 seconds apart and stop for the remainder
of the collection pass after HTTP 429; the next scheduled pass resumes the rotated
budget. Rate-limit deferrals never become zero-valued assets.

## Helius supplementary valuation

The collector reuses `HELIUS_API_KEY` or keys from HTTPS `*.helius-rpc.com`
entries in `SOLANA_RPC_URLS`. Wallet API requests use an authentication header,
follow pagination, and rotate keys after failures within a 12-second budget.
No credentials or provider response bodies are persisted. No extra key is required
when a configured Helius RPC key grants Wallet API access.

Fresh Jupiter marks remain preferred. Missing marks can use positive Helius
`pricePerToken` values with matching token decimals and a Helius SOL conversion
price; quantities always come from finalized RPC, never Wallet API totals/balances.
Helius-valued tokens do not consume Jupiter's quote fallback budget.

Wallet API prices lack a source update timestamp. Such values are labeled
`helius_wallet_estimate` with `provider_timestamp_unavailable`, included in the
known-asset subtotal, and leave strict NAV incomplete (`undated_helius_price`).
Response receipt time is not presented as price freshness. Zero/missing/invalid
prices and incomplete paginated responses are not usable prices. Trading swap
routing and root authorization are unchanged; history-only collection skips prices.

### Empty SPL account rent

`node dlmm_executor.js reclaim-empty-accounts` previews up to eight eligible
classic SPL accounts. Add `--execute` to close that batch back to the same wallet.
This is manual maintenance, not a scheduled trading action. Nonzero balances,
wrapped SOL, Token-2022, delegated/frozen accounts, foreign close authorities and
mints with open Meteora positions are excluded. Entry and swap locks are held;
unexpired trading reservations block maintenance. An uncertain send retains its
signed transaction identity for reconciliation before another batch can run.

Submissions use `rent_reclaim` with no entry/root attribution. Reclaimed lamports
are a move from recoverable account reserves to spendable SOL, **not trading
profit**. Portfolio NAV includes both sides; the network fee is a cost. Historical
root cash accounting is not retroactively credited with these wallet-level funds.

### Externally initiated rent maintenance

The observed CLEANAL wrapper is classified as `rent_maintenance` only when every
inner operation is an empty non-native SPL account close to the signing wallet
followed by its explicit service-fee transfer. All token accounts must disappear,
all pre-balances must be zero tokens and owned by the wallet, and every native
balance change must match those instructions plus the network fee. Unknown
wrappers, extra instructions or unexplained balance changes remain unclassified.

Facts expose recovered rent and the wrapper service fee separately. External flow
is zero: reserves became spendable SOL, while fees reduced wealth. No trading root
gets credited with this maintenance cash. Schema 6 refreshes previously unknown
transactions with a new observation timestamp; historical evaluations retain the
evidence available at their cutoff.
