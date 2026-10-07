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
marks per pass fall back to full-balance quotes. Rotation processes the selected
accounts in cursor order and advances only for attempts made, so a rate limit
does not skip unattempted accounts. Quote marks must match the requested input
mint, full raw balance, SOL output mint and ExactIn mode, have a positive integer
output amount, and carry a valid provider context slot within 1,500 slots of the
finalized balance observation. Slots may lead finalized RPC when the provider
quotes at a more recent commitment. Cache schema 2 retains that actual slot;
legacy marks with an assumed wallet slot expire from use and are recollected
within the same budget. Fresh quote and cache evidence retains the provider slot
in each NAV token row. This validates [Jupiter quote response fields](https://developers.jup.ag/docs/api-reference/swap/v1/quote),
without adding signing, RPC calls or quota allowance. Stale, absent or changing snapshots
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

Disabled by default to avoid recurring Wallet API credit charges. Explicit
`DLMM_HELIUS_WALLET_PRICES=true` enables these optional, undated estimates.
With it disabled, existing fresh marks and bounded quotes are used; missing
valuations remain unknown. Native/token balances still come from RPC.

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
classic SPL or Token-2022 accounts with only `immutableOwner`. Add `--execute` to close that batch back to the same wallet.
This is manual maintenance, not a scheduled trading action. Nonzero balances,
wrapped SOL, other/unknown Token-2022 extensions, delegated/frozen accounts, foreign close authorities and
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
followed by one or two explicit service-fee transfers. All token accounts must disappear,
all pre-balances must be zero tokens and owned by the wallet, and every native
balance change must match those instructions plus the network fee. Unknown
wrappers, extra instructions or unexplained balance changes remain unclassified.

Facts expose recovered rent and the wrapper service fee separately. External flow
is zero: reserves became spendable SOL, while fees reduced wealth. No trading root
gets credited with this maintenance cash. Schema 9 refreshes previously unknown
transactions with a new observation timestamp; historical evaluations retain the
evidence available at their cutoff.

### Pump cashback and accumulator maintenance

The observed wrapper is recognized only for the complete finalized sequence of
WSOL account creation, Pump cashback claim, WSOL close, accumulator close and
explicit service fees. Program IDs, instruction discriminators and shared account
bindings must match; all native and token balance changes must reconcile exactly.
The fixture is a finalized transaction; instruction layouts come from the
[official Pump AMM IDL](https://github.com/pump-fun/pump-public-docs/blob/main/idl/pump_amm.json).

`rent_maintenance.cashback_lamports` is wallet-level protocol income, separate from
`released_lamports` (returned reserve) and `service_fee_lamports`. External funding
is zero; no Azimuth root receives this income. Schema 10 refreshes older unknown
facts with the current observation time. Historical cutoff reports stay unchanged.

## Pooled settlement reporting

A full-wallet exit swap can sell residual tokens from several closed roots.
`pooled_settlements` reports their combined cash only when every connected owner
has complete entry/close and wallet coverage, no pending transactions or external
inflow ambiguity, and the group's exact integer token deltas cancel for every mint.
It includes all owners connected by residual mints; incomplete owners block the group.
Members remain incomplete individually and cannot pass the root re-entry gate.
Combined cash already includes fees and rent; it is not per-position PnL, win rate,
IL or wallet NAV. Evaluation shows only groups whose entire lifetime fits its window.

Account funding also recognizes System transfer → allocate → assign sequences.
The account must start unfunded, end with exactly the wallet's known funding,
and have one allocation and assignment. Wallet-owned token/position accounts
remain reserves; other program accounts are conservatively charged to the root
execution-cost budget. This classification does not subtract cash twice or
claim that a program-specific future refund is impossible. Old recorded facts
refresh to schema 7 within the existing 60-transaction collection budget;
coverage stays incomplete until that refresh finishes. Historical evidence is
not backdated.

Reconciliation writes the same enriched finalized transaction facts used by NAV collection, so a newly landed journaled transaction needs one `getTransaction` read across both paths. Existing legacy facts remain readable; missing and unfinalized evidence stays unresolved.

Native System transfers may include the standard Memo program. Classification
requires the transfer sum to match the wallet's finalized native delta plus its
fee, with no token delta. Memo content is ignored. Schema 8 refreshes only older
unclassified facts; already recorded transactions at schema 7 stay cached.

### Token-account rent evidence

New finalized facts include additive `token_rent_evidence` (version 1): exact wallet-funded token-account creations and fully reconciled pure empty-account refunds, keyed by account address and mint. Wrapped SOL, failed transactions, ambiguous funding and combined/custom closes are excluded. Empty lists mean no supported evidence was identified, not proof that no rent moved. Existing schema-11 facts remain cached; a missing field is historical evidence not yet measured, and does not trigger migration. These records do not allocate shared fees, change root cash, or authorize re-entry.

### Closed-position LP value validation

Realized backfill caches only explicitly closed positions with finite PnL and
percentage values, a positive deposit, and nonnegative withdrawal/fee values.
Missing or malformed API economics remain unmeasured and retryable; measured
zero PnL and zero fees remain valid. Existing historical zero records cannot
be distinguished from older defaulted zeros without fetching source evidence.
These LP valuations still exclude wallet transaction costs and later rent refunds.

### Bounded rent account history

When wallet coverage is complete and classified, the collector records at most
one account-history lookup per cycle in `dlmm_rent_history.jsonl`. Candidates
require existing finalized funding and pure-close refund evidence for the same
account, mint and rent amount. The bounded history must reach a funding signature,
and every intervening signature must match a cached wallet fact and failure status.
Completed evidence is cached; incomplete attempts rotate for retry. RPC failover
can retry the single logical lookup. No bulk transaction migration is triggered.

This proves the recorded history interval, not unique root ownership. Future
attribution must check every referenced signature against roots, preserve
observation times, and count shared refund transaction fees only once. Existing
cash reports and root re-entry gates are unchanged.

### Cash groups including matched rent refunds

`rent_refund_groups` combines settled root cash with wallet-level pure-close
refunds only when every refunded account has observed history evidence and all
its referenced signatures belong to one root. Every account in a shared refund
must match; unknown, cross-root or incomplete ownership leaves the refund out.
Roots connected by shared refunds form one group. Root cash and each refund
transaction (including its fee) appear once within that group. Refunds between
root legs are included only after the entire root is settled.

These are alternative, overlapping views of the root cash subtotal: never sum
both. Individual root cash, re-entry decisions and per-root win rates are
unchanged. Groups are not full NAV or proof all historical refunds are measured.
Evaluation includes only groups whose whole activity lies within its window;
history evidence observed later cannot alter earlier reports or decisions.

### Swap quote evidence

New swap submission rows include `swap_quote`: quote receipt time, input/output
mints, raw input/output amounts, minimum output, authorized slippage, provider
context slot and price-impact estimate. Only these selected fields are copied;
quotes are not realized proceeds. The journal is written and flushed before
broadcast, including sends whose outcome is uncertain. Existing exit behavior
on journal write failure remains unchanged and logs incomplete coverage.

Compare quotes with finalized token movements and separately identified native
rent/fee movements. A wallet native delta alone is not gross swap output. Old
transactions lacking a saved quote remain unmeasured for quote-to-fill slippage;
do not reconstruct their historical quotes from current market prices.

Evaluation reports group signed attempts by authorized slippage. SOL output is
measured as finalized native delta plus network fees plus funded token rent minus
refunded token rent. Failed transaction fees, pending facts and unmeasured rows
remain explicit. Negative shortfall means the fill improved on the quote. These
groups are execution evidence, not trading profit or causal savings; failures
before a signed submission are outside their attempt counts.

### Mode-specific bin replay horizons

Bin shadow collection uses the existing mode horizons: pulse 30 minutes,
turnover 1 hour, casual 4 hours, multiday/unknown 24 hours. It permits a terminal
observation up to ten minutes late, then stops requests for that entry. A stored
terminal observation also stops further collection for that entry.

Replay uses the first observation at/after the target within that grace window;
it cannot select a more favorable later outcome. `horizon_complete` distinguishes
full horizons from partial models, and `observed_until_ts` states the actual end.
The evaluation summarizes these counts. Past snapshots remain available, but new
extended holding-period bin studies beyond these horizons would require explicit
collection changes. Trading monitors and actual position exits are independent.


### Pool selection history

The periodic `dlmm_executor.js accounting` command publishes a local-only cash
history cache after collecting finalized facts. It expires after 15 minutes.
The scanner compares the cache's latest close timestamp and close count against
its Redis journal; a newly closed position invalidates older cash evidence.

Signals expose `prior_mark_pnl_sol` separately from `prior_net_pnl_sol`.
Net is present only with `prior_pnl_basis=matched_refund_cash`: every root in the
last ten closes (within 30 days) must be wholly covered by verified refund groups.
Shared cleanup fees count once. A refund group spanning different pools is not
split arbitrarily, so those pools retain unknown cash. Unknown is not zero.

Ranking prefers verified cash, with the existing conservative mark loss penalty
when cash is unavailable. The separate pool percentage-loss safety gate continues
to use the existing marked history and its unchanged threshold. This cache is
advisory selection evidence, not portfolio NAV or a new risk-limit authority.


### Hermes delivery evidence

Solana webhook requests receive a random `X-Request-ID`, supported by Hermes as
its delivery ID. The scanner persists the signal before sending, then records
acceptance/rejection/uncertainty in
`~/.local/state/azimuth/solana_deliveries.jsonl` (override `SOLANA_DELIVERY_PATH`).
No webhook URL, credential, or response body is stored. Receipt IDs must match.

The evaluator joins delivery IDs to the profile's read-only Hermes session DB,
respecting its evaluation cutoff. HTTP acceptance and session end are lifecycle
evidence only; neither proves a completed AI pick or finalized trade. Missing
or ambiguous evidence remains explicit. This journal does not replay requests
or relax the scanner's accepted/ambiguous-delivery deduplication protection.

### Forward liquidation observations

The existing shadow job samples at most one recent, unclosed position per cycle
in `dlmm_liquidation_quotes.jsonl`. It performs one Meteora position HTTP read
and, if token inventory is nonzero, one Jupiter quote read; no Helius calls,
retries or transactions. Attempts are spaced at least 240 seconds per position
and rotate oldest observations first. Existing mode horizons bound collection.

Initial support covers SOL as token Y, recorded mint decimals, and positions
with no previous withdrawals, fee claims or outstanding rewards. Inventory
older than 180 seconds, missing fields, invalid quantities or mismatched quotes
remain unmeasured. Zero token inventory needs no quote. The report preserves
observation times and includes only samples observed within its time window.

`quoted_assets_change_before_network_fees_sol` replaces the token inventory mark
with quoted SOL proceeds, including the provider's route costs. It excludes
network fees and rent and is **not net cash**. Inventory and quote are different
observations; withdrawing liquidity can change the eventual route and price.
These observations do not change exit rules, selection, learning or risk limits.

## LP comparison precision

Full-life LP cohorts include funded positions created and closed inside the report window. Funded positions created earlier are carry-in closes; positions with zero deposit are counted separately. A win requires at least one lamport of positive LP valuation PnL, a loss at least one lamport negative, and smaller marks count as break-even. This affects win labels only; raw LP PnL and deposit totals are retained. LP wins are before wallet fees and settlement costs. Missing or nonfinite required values leave the wallet comparison unmeasured.
