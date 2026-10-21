# Solana accounting and review

### Native allocation execution evidence

Native risk marking can attach `bin_observation.initial_funding` using the
funding transaction it already reads. This optional evidence supports SOL-only
BidAsk deposits with supported strategy parameters. It decodes the executed
active bin and composition fees from program-scoped Anchor self-CPI events,
checks inferred integer bin allocations against the actual SOL transfer, and keeps
protocol fees as a subset of composition fees. Unsupported or incomplete
execution evidence leaves this field absent and does not disable native risk
marking. No additional RPC or signer is used.

The existing pre-close journal carries this evidence into `native_bin_replay`
in scheduled evaluation. Funding and account-deletion facts must be finalized
and observed by the report cutoff. The native observation must precede the
earliest proved close block by no more than 30 seconds; its recording time must
also be within the report. Historical rows without execution evidence remain
unmeasured.

This comparison scales actual bin principal and earned fees under three fixed
allocation schemes. Composition costs stay inside principal; the displayed
scaled cost is explanatory and is never subtracted again. The native baseline
must reproduce its recorded lamport mark. This is a fixed realized return-rate
sensitivity, not an executed trade or demonstrated improvement in IL. Different
allocations can change fee dilution, composition rates, transfer fees, price
impact, exit decisions and settlement costs. Pre-broadcast reserve models do
not account for those execution composition costs or a changed active bin.

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

Signed transaction confirmation polls HTTP `getSignatureStatuses` with history
search enabled, at one-second intervals over an eight-second polling window.
The existing per-request HTTP timeout still applies, so an in-flight request may
finish after that window. Only `confirmed`/`finalized` with explicit `err: null`
proves success. A confirmed chain error is definitive; null/processed status,
missing error evidence, an unavailable RPC or an elapsed polling window cannot
authorize a replacement transaction. Durable markers and finalized block-height
expiry remain authoritative, and RPC failover resends the same signed bytes.
No WebSocket subscription is created: a denied handshake can otherwise leave
the installed SDK reconnecting after HTTP confirmation, keeping the one-shot
executor alive until the monitor timeout and delaying SOL settlement.

Marked NAV = native SOL + current SPL marks/quotes + Meteora open LP balance and
unclaimed fees + recoverable token/position account reserves. SPL marks use batched
Jupiter prices bounded by observed timestamp and price slot; at most forty missing
marks per pass fall back to full-balance quotes. Rotation processes the selected
accounts in cursor order and advances only for attempts made, so a rate limit
does not skip unattempted accounts. Cached quotes must remain within the existing
600-second freshness limit through the remaining 90-second collection window;
near-expiry quotes enter the same bounded refresh rotation. Failed refreshes do
not fall back to the expiring price. This does not increase the request budget
or guarantee every asset can be valued in one pass. Quote marks must match the requested input
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

## Post-close cooldowns

The monitor's ordinary and forced-close paths retain their normal cooldown when
only a nonnegative pre-close LP mark is available. That mark cannot shorten the
cooldown to 15 minutes or clear the token's existing loss streak: a positive LP
valuation can settle to negative native cash after a swap and account funding.
Negative marks retain the existing escalation; loss history expires through its
existing seven-day TTL. This does not add a cash-win reset or retrospectively
rewrite Redis history. Recenter eligibility still passes the executor's separate
root-accounting gate, and close/settlement execution is unchanged.

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

Collection uses a monotonic 240-second budget inside the five-minute service
timeout. Rejected-candidate HTTP reads have a 45-second phase budget; bin
subprocesses have 150 seconds, leaving time for one 20-second liquidation probe.
Each request uses the remaining phase time. Exhausted phases are reported and
unattempted records remain pending for the next run; missing bin observations
are never filled from later prices. This prevents slow discovery requests from
consuming the entire run before the IL snapshots can be collected.

The collector streams growing journals instead of retaining full historical bin
samples or completed reject payloads in memory. It keeps completed IDs, first-seen
reject IDs, unfinished IDs and the last recorded timestamp per position. Pending
candidate payloads are processed one at a time, even with a large backlog.
Duplicate cohort IDs retain their first record, and corrupt JSON remains an error;
no evidence is deleted or silently skipped. This bounds memory by the indexes and
pending work rather than every historical snapshot's reserves and fee counters.

Entry bin state is captured before broadcast; subsequent bin states retain reserves,
supply and fee-growth counters. Fixed uniform, near-active and far-active allocations
are replayed under an infinitesimal fixed-share assumption. Results show fees,
inventory change, HODL-relative IL, sampled OOR, utilization and observed-cost-adjusted
PnL where costs exist. Empty/reset/missing bins are unmeasured. Price impact and
hypothetical recenter/slippage costs are not inferred. Live weights are unchanged.

For recorded SOL-only inputs whose amount matches replay capital, HODL retains
that SOL, including when the active bin contains both tokens. Other entries retain
the explicitly labeled modeled-inventory benchmark. `far_active` is labeled as the
expected SDK BidAsk reference only for a SOL=Y, contiguous below-to-active range
matching the recorded entry. This is a pre-broadcast allocation reference, not
proof of executed shares, fills or live IL; other geometries remain unlabeled.

New SOL-only BidAsk entries narrower than 70 bins also observe a fixed 70-bin
alternative on the SOL side. One wider snapshot is cropped for the original
`bin_snapshot` and retained as `width_study`; mint geometry is unchanged. If that
read fails, the original snapshot is attempted without a width study. The existing
shadow timer follows the union of the two ranges in its normal bounded collection.

`bin_width_replay` compares far-active allocations at the same capital and sampled
mode horizon. The daily report separates modes and totals only complete pairs.
Extra empty, missing or reset bins make the comparison unmeasured; historical
entries without a pre-entry wider snapshot are not backfilled with today's bins.
The comparison is gross: additional rent, market impact, slippage and the live
exit policy are unknown, so a modeled fee or IL advantage is not deployable profit.

The evaluator also reports `bin_width_holding_replay`. It requires a recorded
close plus account-deletion evidence observed by the evaluation cutoff, then
compares both allocations at the last bin observation at or before the finalized
transaction's block time. A delayed close journal cannot extend the holding
period; repeated proof uses the earliest valid finalized close time.
The observation must be no more than 600 seconds old; post-close samples and the
normal fixed-horizon terminal grace cannot enter this view. Missing close proof
or a missing/stale pre-close observation remains unmeasured. Both diagnostics use
the same pre-entry capital and bin snapshots. The holding-period comparison is
gross and has an outcome-defined duration; it does not simulate the alternative
exit policy, fill the unobserved gap, or establish executed IL or net profit.

A tracked position omitted by the indexer receives one bounded three-second
native risk read before the missing-position branch can skip it. A verified mark
continues through the existing risk rules and is reused without another native
read. The two-hour cleanup grace and RPC absence requirement remain in force
when native evidence is unavailable; an indexer omission alone cannot remove
tracking or manufacture a close. Missing or invalid indexed fee yield stays
unknown: it cannot trigger the low-yield exit, and status reports show null yield
and breakeven estimates instead of zero. A measured zero remains eligible for
the existing age-qualified low-yield rule; native risk and fee-stall rules remain
independent of this indexed metric.

Native risk marks also expose the already-read per-bin position shares, raw
inventory and unclaimed fees. After a normal rule-driven close attempt, the
monitor appends that decision-time observation to
`memories/dlmm_close_bin_observations.jsonl`. It adds no RPC or inference request;
file writes happen after close execution and failures cannot change its verdict.
Unavailable native marks and dry runs produce no observation. This journal covers
the ordinary close branch, not override, compounding or reseed branches.
An observation is not a landed close or a full pool-bin snapshot. Consumers must
respect both `observed_at` and `recorded_at`, join finalized account-deletion proof,
and measure the remaining gap. Alternative allocation costs and exits remain
unmodeled; the existing bin replay does not automatically consume this journal.

## Operations

`azimuth-sol-accounting.timer` and `azimuth-sol-shadow.timer` collect outside the
trading loop. Unit templates target the solanza profile; adapt the path elsewhere.
Evaluation writes `report.md`, `evaluation.json`, and redacted runtime logs. Optional
`--reference-wallet` adds the same full-life LP cohort for Meridian; LP comparison
is explicitly separate from Azimuth wallet NAV. No reports are automatically sent.

Use an isolated checkout for development: the live profile scripts are symlinks.

The monitor resolves position bin limits from a per-position PnL response or the
executor's matching `dlmm_entries/<position>.json` record. Portfolio pool aggregates
omit these limits; Redis entry estimates and parent positions are not substitutes.
The executor records the bin limits used by the mint, and re-centering creates a
new position. With valid limits and the already-fetched current active bin, range
checks use that geometry, including ranges above spot for SOL=X. Missing geometry
or an unavailable current bin retains the indexed range flag and leaves directional
checks unmeasured. This restores existing range guards; it does not turn indexed
PnL into executable cash value or prove that historical losses were preventable.

Signed deploy, close, claim, swap and rent transactions reconcile their own signature
after broadcast errors as well as confirmation timeouts. RPC acknowledgement is not
proof of execution. Confirmation is bounded to eight seconds; its fallback uses
[`getSignatureStatuses` with `searchTransactionHistory`](https://solana.com/docs/rpc/http/getsignaturestatuses).
Only confirmed/finalized status with an explicit null error proves success. Missing,
processed or unavailable status keeps the submission uncertain; on-chain failures
remain failures. Durable pending markers and retries of the same signed bytes remain
in place.

Monitor risk valuation first attempts the three-second native inventory read before
starting any per-position indexed PnL fallback. A valid native result skips that
fallback's potential 30-second wait; unavailable native data retains indexed
fallback. Already fetched portfolio data still supplies fee-rate context. A verified native loss can
therefore reach emergency stop rules during an indexer outage. If neither source
provides usable valuation, the tick skips risk evaluation instead of treating the
initialized zero PnL or token price return as a measured LP result.

Funded-position closes broadcast their persisted signed bytes concurrently to
the distinct configured RPC endpoints. Each signed transaction has one eight-second
group deadline covering broadcast and confirmation; the first confirmed/finalized verdict ends
the group and cancels the other HTTP requests and polling timers. A confirmed
chain error remains a failure. RPC acknowledgement, processed status and a group
timeout cannot authorize another transaction or a new blockhash. Restart retries
reuse the same pending close bytes. Empty-only cleanup retains its existing path.

This changes transport only: the transaction, preflight options, fees and close
instructions are unchanged. Close preparation first uses the saved entry's pool
as a hint, verifying the native position program, discriminator, pool and wallet
owner before a targeted SDK position read. The returned owner and position must
also match. Missing or mismatched hints retain wallet-wide discovery; RPC errors
retain ordinary failover. Local metadata alone never authorizes withdrawal.
This avoids enumerating unrelated positions for a verified known position;
it is not proof of improved live latency or exit price.
Optional `dlmm_close_preparations.jsonl` records each invocation's ID and position,
lock acquisition, lookup, transaction construction, blockhash acquisition, persisted
signature and confirmation boundaries. Monotonic elapsed times separate preparation
from broadcast latency; wall-clock timestamps link to monitor decisions. A final
failed/pending/refused/completed stage describes the executor result, not finalized
cash settlement. Reconciliation and RPC retries remain inside the same invocation.
No endpoint URLs, error bodies, private keys or signed bytes are recorded, and a
journal failure cannot prevent withdrawal. A killed process may leave an incomplete
sequence; this alone does not prove the process remains live or identify a root cause.
Optional `dlmm_close_transports.jsonl` records the
signature, bytes hash, configured endpoint count, client elapsed time and outcome.
It stores no RPC URLs or raw transaction. Journal failure cannot block a close.
These timings are client observations, not finalized block times, saved SOL or
proof that an earlier close would have prevented a historical loss.

After finalized accounting proves a closed position's owned token inventory,
its settlement swap uses the same concurrent RPC transport and one shared
eight-second broadcast/confirmation deadline. The signature is persisted before
broadcast; every endpoint receives the same signed bytes and the existing
skip-preflight options. Amount, route, slippage ceiling, simulation and net
recovery checks stay the same. An unknown group outcome returns pending without
another unbounded status read, retaining the marker for normal reconciliation
before any later quote or signing. A confirmed chain failure remains a failure.
Other swaps retain their existing transport. Optional
`dlmm_swap_transports.jsonl` records the same public timing/hash fields as the
close journal. This does not shorten the finalized inventory proof or establish
that a historical swap would have filled earlier or profitably.

The settlement balance reader also refreshes finalized wallet history when a
still-unresolved swap belongs to that exact position and wallet, is over 120 seconds
old, and its last valid block height has passed at finalized commitment. This uses
the existing accounting collector's complete-history, stable-head and null historical
status requirements; a null transaction alone never authorizes another swap.
The refresh skips NAV, price quotes and optional rent-account history. Young or
still-valid submissions add no history scan, and an unavailable or incomplete proof
keeps inventory unproven. This avoids leaving withdrawn tokens exposed solely while
waiting for the periodic accounting timer. Slippage, fees, inventory ownership,
pending-transaction reconciliation and the separate risk-monitor loop are unchanged.

## September 26 evaluation corrections

- Executor authorization replay uses its persisted post-refresh evidence; the earlier
  pre-settlement eligibility replay is reported separately. Historical facts are not backdated.
- Root fee pace starts observing at the first fresh position sample, independently
  of exit triggers, and still requires a full 30-minute window. When this tick's
  native risk mark is verified, fee growth and fee-stall checks use its fees,
  principal value and observation time together; a stale indexer timestamp cannot
  hide an observed fee stall. Otherwise the indexed sample retains its own
  freshness requirement. This reuses the existing native read. Missing opportunity
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
classic SPL or supported Token-2022 accounts. Add `--execute` to close that batch back to the same wallet.
Nonzero balances,
wrapped SOL, other/unknown Token-2022 extensions, delegated/frozen accounts, foreign close authorities and
mints with open Meteora positions are excluded. Entry and swap locks are held;
unexpired trading reservations block maintenance. An uncertain send retains its
signed transaction identity for reconciliation before another batch can run.
Rent batches use a finalized blockhash and require a measured network fee below
the reclaimed rent before signing; a missing fee still prevents submission.

The scheduled unit passes `--batch`, which waits for at least two eligible
accounts to share one network fee. A singleton is reclaimed immediately when
its rent exceeds free native cash above the executor's existing 0.02 SOL reserve;
this also avoids retaining a large account balance. It can also run when the
measured net refund restores the pipeline's minimum entry liquidity:
0.02 SOL reserve + 0.045 SOL rent allowance + 0.1 SOL minimum ticket = 0.165 SOL.
The 0.045 SOL allowance covers the observed 0.043414 SOL position/ATA rent;
the executor still simulates the exact transaction and enforces the 0.02 SOL
post-entry reserve before signing. Larger actual costs can still refuse entry.
These amounts share `dlmm_cash_policy.json` between the pipeline and
executor. The policy is loaded on entry/maintenance paths; exit reconciliation
does not depend on it. When the gross refund could restore entry liquidity, the
executor reads the actual network fee and defers without signing if the net
refund is still insufficient. A wallet already above the entry floor, or one
whose singleton cannot cover the gap, continues waiting for a second account
unless the original reserve-pressure exception applies. Unknown native cash defers
the singleton without signing. Batch deferral leaves one eligible account
funded, so spendable SOL can temporarily be lower while its rent remains
recoverable. The eight-account cap, exclusions, trading locks and pending-send
reconciliation still apply. Explicit manual cleanup retains its previous
behavior unless `--batch` is supplied. Batched refund fees retain the accounting
report's conservative shared-fee bounds; a rent release is never new profit.

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
require existing finalized funding and pure-close refund or final outer token-account
closure evidence for the same
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
refunds only when every refunded account has observed history evidence and each
referenced signature belongs to exactly one known, settled root. An account may
be reused by several settled roots: all users join the group, while its exact
rent principal returns to the root that paid the proved funding transaction.
Other users receive zero rent principal and participate in shared fee bounds.
Every account in a shared refund must match; unknown, ambiguous or incomplete
ownership leaves the refund out.
Roots connected by shared refunds form one group. Root cash and each refund
transaction (including its fee) appear once within that group. Refunds between
root legs are included only after the entire root is settled.

These are alternative, overlapping views of the root cash subtotal: never sum
both. Individual root cash, re-entry decisions and per-root win rates are
unchanged. Groups are not full NAV or proof all historical refunds are measured.
Evaluation includes only groups whose whole activity lies within its window;
history evidence observed later cannot alter earlier reports or decisions.

A root can also close its own funded token account in the final instruction of
a swap. Schema 12 records this as `inline_closed` lifecycle evidence while
retaining `refunds_unmeasured`: the aggregate swap credit is not a measured rent
refund or pure swap proceeds. The same bounded finalized account history must
reach the proved funding transaction, with every intervening signature owned
uniquely by that root. Every funded non-native account must match a closure with
the same mint and lamports; shared users, missing histories and unmatched accounts
leave this path unmeasured. WSOL closures are excluded.

Such a settled root produces a group with `inline_rent_pairs` and empty external
refund components. Its cash equals the recorded wallet delta exactly, including
failed transaction fees. No rent credit or additional fee subtraction is applied.
Proved expired, unlanded submissions have no slot or fee and are excluded from
the landed lifecycle records only when the settled chain and collector expiry
proof agree. Their wallet, observation time and expired finalized height must
match the proof contract. Unknown submissions and landed failures are not excluded.
Evaluation, advisory pool history and the signal learner can consume this exact
cash outcome, including negative outcomes with positive LP PnL. New evidence keeps
its observation time and does not retroactively change earlier decisions.
Schema 11 mixed-close facts are optionally refreshed within the existing
60-transaction budget, after missing cash facts; unavailable optional metadata
does not invalidate already-proved wallet coverage.

### Signal learner outcomes

Settled single-position roots can also prove a **nonpositive cash upper bound**
without an owned token-rent refund. This covers native-only LP activity that
reuses an unchanged legacy token account. A new additive finalized transaction
proof requires complete native/token balances and inner instructions, only
known DLMM/System/ATA/token/compute programs, unchanged retained wallet token
accounts, and no retained funding outside the recorded LP position. Temporary
WSOL must be created, initialized and closed to the wallet in that transaction.
Other native balance increases must exactly match principal entering an existing
non-wallet WSOL vault; new reserves, rent top-ups, unknown programs and indirect
funding to other accounts fail this proof.

Every successful transaction must carry this proof; the last successful slot
must contain one transaction that deletes the LP position. Finalized failures
retain their fee, and unlanded/unknown submissions are excluded from this narrow
path. The whole root must already be settled with unique signature attribution,
no token inventory and nonpositive recorded cash. Legacy facts and an empty
`token_rent_evidence.funded` list alone never establish a cash sign. Optional
refresh considers closed positions from the last two days, at most four facts
per collection, after missing cash facts and within the existing 60-fetch cap.
Null proof attempts are cached; missing optional evidence does not affect coverage.

`nonpositive_cash_upper_bounds` has a null lower bound. It can establish a
non-win for the learner and the every-position acceptance report, but cannot
establish positive profit, enter cash subtotals or create a rent-refund group.
Future shared-account cleanup costs may make the result worse. Existing matched
refund groups take precedence. Each proof retains its real observation cutoff;
it cannot change earlier reports.

The pre-broadcast entry record retains the same entry signal fields as normal
Redis registration, including measured zeros, and the known developer address.
Timeout adoption copies these fields from the exact position record. Without
the developer address, the existing repeated-rug developer ban cannot count an
adopted position's offense; losing holder/fee/trader fields also drops learner
inputs. Monitor redeploy contexts retain developer identity too, while re-center
signals continue to describe only their newly measured conditions. Unknown
developer addresses remain unknown; older records are not reconstructed.

`dlmm_weights.py` learns win/non-win labels from `refund_cash_bounds` and the
proved nonpositive upper bounds above, using
cached finalized cash and complete account histories. Only roots containing
one position can label that position's entry signals. Recenter chains, missing
refund proofs without a separate upper-bound proof, and intervals crossing
from nonpositive to positive are excluded;
LP marks and realized LP values cannot substitute for cash. Close rows are
deduplicated by position without rewriting the source journal.

The bounds establish a label, not an exact per-root profit or summable portfolio
PnL. The existing sample floor, smoothing, weight limits and scoring signals
remain; the first cash recalc updates existing weights once, then retains the
six-hour guard. File, Redis and proposal output identify `outcome_basis` as
`proved_cash_sign_bounds`; upper-only samples carry `nonpositive_cash_upper_bound`.
Only the observed, fully reconciled subset can train, so these lifts may have
coverage and selection bias and do not prove improved prospective returns.

### Swap quote evidence

The executor interprets Jupiter Metis `priceImpactPct` as a decimal fraction
and multiplies it by 100 for the configured percentage ceiling. It requires a
complete finite numeric string in [0, 1]; absent, malformed, negative and
out-of-range values return `price_impact_unmeasured` before swap construction.
Scientific notation remains accepted. The DLMM SDK's quote impact is already
in percentage units and must not reuse this conversion when routes are compared.
See [Jupiter's Metis guide](https://developers.jup.ag/docs/guides/how-to-build-a-custom-swap-with-metis).

For swaps using the minimum-recovery gate, `swap_quote.net_recovery` records
the selected unsigned transaction's simulated wallet delta after reserving the
quoted slippage allowance, the required minimum, and whether an inline token
rent close was included. Accepted rent-close variants retain their own measured
value; rejected variants do not replace the original simulation's value.
This includes simulated account funding and refunds, but is neither executed
proceeds nor whole-position profit. Swaps without that gate omit this evidence.
Recording it introduces no additional simulation or RPC request.
New evidence also includes the SHA-256 of the selected serialized message,
simulation slot, before/after wallet-read slots, and simulated wallet delta
before reserving quote slippage. A message change during the measurement
invalidates that result before signing. Accepted rent-close variants retain their
own hash and readings; rejected optional variants cannot replace the selected
message evidence. Slot numbers and equal wallet balances do not prove an atomic
cross-route bank snapshot or unchanged market liquidity.
Evaluation compares this evidence with the finalized wallet delta only after
binding wallet, signature, position, input token amount and observation cutoff.
`net_recovery_summary` counts measured comparisons and outcomes below the
simulated recovery or required minimum. It includes account funding/refunds and
fees without reconstructing gross swap output, and remains independent of
whether rent attribution is complete. It does not alter position profit labels.

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

Automatic settlement quotes ordinary exits at 100 bps and retries at 300 bps.
On a first ordinary attempt, the monitor also passes `--small-settlement`:
only an owned, closed-position token-to-SOL recovery with a positive net floor
may requote at 300 bps when output is at most 250,000 lamports (0.00025 SOL).
The additional 200 bps allowance is at most 5,000 lamports, one base transaction
fee. The executor waits 2.1 seconds before the fresh quote, validates its exact
input, ExactIn mode and 300 bps minimum, and refuses to send if the fresh output
crosses that size ceiling. A quote/API failure sends nothing. Larger first
ordinary settlements keep the original 100 bps quote; other callers must
explicitly opt in, and both quotes still precede any build/sign/send.

The October 5–11 signed-attempt audit contained 37 first ordinary 100 bps
settlements at or below this size, with five failures costing 88,611 lamports.
The cohort's total additional 200 bps allowance would have been about 31,837
lamports. These are observed failure costs and an allowance comparison, not
proof that 300 bps would have landed or saved money. Pre-broadcast failures are
excluded. The extra quote adds latency and may be unavailable. Journaled
`authorized_slippage_bps` records the selected fresh quote's limit, and
`small_settlement_requote` distinguishes this policy from emergency/retry swaps.

The monitor's existing emergency flag (rug velocity, emergency stop-loss or
thin liquidity) is persisted in the settlement marker and starts at 300 bps.
It can promote a queued ordinary close that later becomes an emergency;
existing retry fields and legacy markers remain valid. This avoids requiring
a tight first attempt during an emergency: STRKT's 2026-10-11 rug exit failed
at 100 bps, and its successful 300 bps retry 42 seconds later had a quote
2,400,680 lamports lower. This does not establish what an earlier fill would
have received. The 300 bps ceiling, pending-signature reconciliation, owned
inventory proof, impact guard and positive-net recovery floor still apply.

Atomic settlement sales record `token_rent_close_included` before broadcast.
Finalized mixed token-account closes set `token_rent_evidence.refunds_unmeasured`
when the pure refund proof cannot separate rent from sale proceeds. These rows
retain native cash and known fees but remain unmeasured for quote-to-fill
comparisons. This additive evidence does not refetch historical caches.

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

New pipeline entries retain `signal.entry_live_gates` in executor provenance and
Redis tracking, which the close journal also preserves. These are the already
fetched pre-deploy momentum windows, screened/live fee ratio and timeframe,
depth impact, checked amount and local observation time. Missing/nonfinite
momentum remains null; a measured zero stays zero. This adds no market request
and does not reconstruct older entry conditions or prove a hypothetical filter
would have prevented a loss. Risk thresholds and exit rules are unchanged.

The periodic `dlmm_executor.js accounting` command publishes a local-only cash
history cache after collecting finalized facts. It expires after 15 minutes.
The scanner compares the cache's latest close timestamp and close count against
its Redis journal; a newly closed position invalidates older cash evidence.

Signals expose `prior_mark_pnl_sol` separately from `prior_net_pnl_sol`.
Net is present only with `prior_pnl_basis=matched_refund_cash`: every root in the
last ten closes (within 30 days) must be wholly covered by verified refund groups.
Shared cleanup fees count once. For a group spanning pools, individually proved
refund amounts produce `prior_cash_lower_sol` / `prior_cash_upper_sol` with
`matched_refund_cash_bounds`. Lower charges every shared refund fee in full;
upper assigns none. These ranges cannot be added across pools, and exact net
remains absent. The whole group's cash reconciles before projecting a range.
Missing components, partial roots and uncovered closes retain unknown cash.
Unknown is not zero.

Ranking prefers exact cash or a proved interval sign (upper < 0 means loss;
lower >= 0 means nonnegative). A range crossing zero retains the existing
conservative mark loss penalty. No penalty size or risk limit changes. The separate pool percentage-loss safety gate continues
to use the existing marked history and its unchanged threshold. This cache is
advisory selection evidence, not portfolio NAV or a new risk-limit authority.


### Hermes delivery evidence

The pre-dispatch inference probe checks the primary model, then explicitly
configured custom-provider fallbacks using the same endpoint and credentials.
All attempts share the existing 60-second deadline. Different endpoints,
providers, or explicit fallback credentials are not probed with the primary
credentials. A healthy fallback permits the existing Hermes route to own the
batch; it does not change the configured model chain, submit a trade, or prove
a completed pick. Exhausted/unavailable probes retain deterministic fallback.

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

After saving a measured native inventory/quote observation, the existing shadow
collector can archive an unsigned exit bank using its remaining deadline (at
most 15 seconds, within the existing 20-second liquidation phase). It yields
to entry, settlement and the position's close worker. There is no new timer,
signing key, transaction submission or RPC simulation. The SDK's optional
compute estimate is refused by a read-only method allowlist; replay must
measure compute use itself.

`dlmm_exit_banks/<position>.json` contains SDK close instructions, Jupiter's
ledger swap instructions, lookup tables and one final account-response bank
including discovered upgradeable program data and the position pool's oracle
for direct-pool swap replay even when Jupiter routes through another pool.
Missing accounts remain explicit
nulls. A changed program, closed position, budget overrun or more than 100
accounts leaves the observation unmeasured. Capture is limited to eight distinct positions, three banks per position,
and 512 MiB total JSON storage. Later banks are at least ten minutes apart,
regardless of quote profitability. A 32 MiB per-bank ceiling is reserved before
network reads. The first bank retains `<position>.json`; later banks use
`<position>.2.json` and `<position>.3.json`. Existing banks are never replaced.
These sparse observations do not constitute complete exit-path coverage. Summary outcomes go to
`dlmm_exit_bank_observations.jsonl`; collection failure preserves the ordinary
quote. Replay still must recompute inventory/geometry at the bank slot, check
remaining CPI dependencies and account for all costs. This is research input,
not evidence of executable profit or permission to delay an emergency exit.

The existing shadow job samples at most one recent, unclosed position per cycle
in `dlmm_liquidation_quotes.jsonl`. It first makes one read-only native risk probe
with a three-second timeout. A verified mark supplies transfer-adjusted token
principal plus fees directly to the Jupiter quote, with a 30-second freshness
limit checked again after the quote. `inventory_source`, `lp_mark_basis`, funding
signature and raw inventory identify this basis separately from older observations.
Unsupported or unavailable native proof retains the indexed position HTTP fallback
and its 180-second freshness limit. The existing 20-second overall budget applies;
there are no Helius calls, retries or transactions. Attempts are spaced at least
240 seconds per position
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

## Automatic settlement inventory

The durable settlement worker sells only the positive raw token delta proved by
finalized transactions of the closed root. It never uses the full wallet token
balance as the sale amount. Pending root signatures are reconciled individually;
missing entry/close evidence, foreign wallet attribution, external inflows,
negative current-root inventory or another same-mint movement since entry refuse a sale.
Before building the swap, the executor verifies the position is absent and the
live token balance still matches the cached transaction balance. Quotes must
match the authorized mint pair and exact raw amount. Partial sales cannot close
an ATA containing legacy tokens. Zero owned inventory completes settlement
without selling wallet dust; a nonzero wallet balance alone is not a blocker.
This proof authorizes inventory disposal, not NAV or profit. Older legacy sales
remain incomplete in accounting. Ambiguous inventory requires investigation.

### Evaluation of root cash after refunds

`matched_refund_cash_cohort` selects roots whose entire recorded activity lies
inside the evaluation window, then projects complete proved refund groups onto
those roots using the same cash bounds as the learner. Older carry-in roots can
share the refund batch but their cash and funding returns are excluded. Shared
fees are charged once per group in the cohort bounds. Individual root bounds
must not be added; their fee assumptions overlap.

The report gives positive, negative, exact-zero, ambiguous and unmeasured root
counts. Its positive rate uses only roots with a proved sign; ambiguous and
missing evidence are explicit, not zero losses or wins. This measured subset
is root cash after fees and matched refunds, not position win rate or full NAV.
No trading rule, risk limit or historical decision is changed.

### Every-position profit acceptance

`position_profit_acceptance` includes every recorded entry deployed in the
evaluation window, including positions with incomplete cash evidence. A position
passes only when its settled cash lower bound is strictly positive after costs
and proved owned rent. Zero and negative upper bounds fail. An interval spanning
zero, missing evidence or a multiple-position root remains unresolved/unmeasured;
aggregate root gains cannot establish the result of each constituent position.
Shared refund fees use the existing conservative cash bounds, which must not be
summed across positions. The full root activity must fit within the window and
the refund proof must exist by its cutoff.

One proved nonpositive position makes the criterion `failed`. Any unresolved or
unmeasured position makes it `not_verified` when there is no proved failure.
An empty cohort cannot pass. `observed_all_positive` describes that entry cohort
only, never a guarantee of future profit or complete portfolio NAV. This report
does not change ranking, execution, risk exits or learning.

### Signal learning by entry mode

Cash-proved single-position roots train each entry mode independently. Pulse's
five-minute fee signals no longer train turnover's thirty-minute preferences or
vice versa. Each mode retains the existing ten-sample minimum, both outcome
classes, six-hour recalc guard, smoothing and weight limits. New mode weights
start at neutral; insufficient mode evidence produces neutral ranking rather
than borrowing another mode's weights. Unknown modes are excluded from mode fits.
The top-level pooled weights remain for legacy readers; current AI context,
deterministic ranking and proposal reports select the matching `by_mode` bucket.
Historical correlations and the resulting rankings do not prove prospective profit.

### Quote collection pacing

NAV quote collection uses keyless Jupiter pacing (at least 2.1 seconds between
requests) and honors a valid provider reset timestamp when the response reports
no remaining quota. Reset headers must fall inside the documented 60-second
window. The quote phase reserves response time inside 90 seconds and retains
its 40-attempt rotation; cached quotes must match the exact balance, be no more
than 600 seconds old, and remain within 2,500 slots. Fresh provider quotes
retain the stricter 1,500-slot check. A 429 stops the remaining quotes for that run.
No quote retry, Helius Wallet API call, stale mark or zero price is introduced.
Other clients sharing the same public rate bucket can still cause deferrals.

Before each NAV quote and again after its pacing wait, the collector checks the
executor's existing wallet entry/swap lock in Linux `/proc/net/unix`. An active
worker defers the remaining background quotes with `quote_trading_deferred`.
Finalized wallet history, balances, cached/spot marks and portfolio reads still
run; missing marks stay unpriced. The collector never acquires a trading lock.
Released workers leave no stale priority marker, and other wallets do not block
this collection. Without procfs the existing pacing behavior applies. This
reduces local quote competition; it cannot cancel an in-flight request, reserve
provider quota, or prove that an exit will avoid 429 responses or be profitable.

The observed wallet has 105 nonzero token balances, with 65–74 requiring
quotes instead of fresh spot marks. Two capped rotations can now cover up to
80 balances before the 600-second cache limit at the current roughly 500-second
collection interval. The 90-second deadline, 2.1-second pacing, provider reset
headers and 429 stop remain authoritative: 40 is a ceiling, not a guarantee of
complete NAV. Failed quotes stay unpriced. This changes read-only valuation
capacity, not trading, RPC collection frequency or risk thresholds.

Provider limits: https://developers.jup.ag/docs/portal/rate-limits

### Evaluation journal memory

The rolling evaluator streams reject and NAV history, keeping only records
needed by the requested window. Accounting retains the first complete NAV and
last eligible NAV in file order. The public `rows()` helper still returns a
list, and malformed JSON remains an error even outside the selected window.
Bin samples are indexed once by byte offset for eligible entries, then loaded
one position at a time with a SHA-256 check against the indexed bytes. Appends
after indexing cannot add samples to that run; changed indexed records fail
visibly. Duplicate/order semantics, financial formulas and cutoff rules remain
unchanged. No journal is truncated, deleted or backfilled by this read path.

### Pre-entry candidate bin evidence

The existing shadow timer also observes up to three recent candidate pools per
cycle with `candidate-bin-snapshot`. Sources are SOL-as-Y pools in reject records
pipeline batch receipts and scanner observations before routing from the past
30 minutes, indexed by pool using only the latest 64 identities across all sources.
The phase has a ten-second ceiling, a three-second process timeout per pool and
a four-minute retry interval. It preserves the existing 20-second liquidation
reserve, streams its history and rotates pools by oldest attempt first.

The read-only command observes at most 86 bins, from 69 below to 16 above the
pool's cached active bin. This can cover a later 54-bin entry after a 15-bin
move in either direction; larger moves can leave incomplete coverage. Identity,
SOL orientation, decimals, contiguous bounds and native counters are checked
before writing `memories/dlmm_candidate_bin_samples.jsonl`. Failures remain
unmeasured without invented counters. `request_started_at` and `collected_at`
surround the read, and the source watch/reject ID and timestamp remain attached.

Before AI health probing or dispatch, the scanner writes at most 64 unique
public SOL-as-Y pool/mint identities to `solana_candidate_watch.jsonl` beside
its reject journal (`SOLANA_CANDIDATE_WATCH_PATH` overrides this in both
scanner and collector). These `scanner_before_routing` observations survive
model failures before the pipeline is invoked. They do not establish admission,
execution or profitability. Writes use a nonblocking lock and do not add RPCs.

Before capacity/ranking checks, live `--from-batch` and `--from-signal`
invocations append at most 64 unique public SOL-as-Y pool/mint identities to
`memories/dlmm_candidate_watch.jsonl`. Receipt time describes this local watch
input, not scanner freshness, eligibility or an executed entry. Dry runs and
pick-context reads do not append. The optional journal uses a nonblocking
writer lock; its failure cannot reject a trade. `watch:` source IDs distinguish
these receipts from reject IDs. They never enter reject-outcome counts.
Collection still shares the existing three-pool/ten-second phase and trading
priority checks; this adds no RPC calls to the entry path or new timer.

Before SDK creation and each explicit bin/active read, the command checks the
wallet's existing entry/swap sockets and defers while a trading worker is active.
It requires only `SOLANA_PUBLIC_KEY`, never decodes a signing key, acquires a
trading lock or submits a transaction. In-flight reads cannot be cancelled by a
later lock acquisition. No new service or timer is installed.

The evaluator embeds the earliest complete matching prior sample observed
4–30 minutes before each entry snapshot, with its canonical JSON SHA-256. Both
native observation time and collection time must precede entry; samples fetched
after entry cannot backfill the estimate. Mints, decimals, all funded bin IDs
and monotonic fee counters must match. Missing history stays unmeasured.

These are separately fetched pool/bin reads, not an atomic bank snapshot.
These bounded sources are not representative of all pools, and pool-level fee/TVL is
not the fee yield of a funded BidAsk ladder. This adds coverage evidence for
later prospective fee calibration; it does not estimate profit, change gates,
claim consistent returns or prove an IL improvement.

#### Prospective candidate fee calibration

After a successful natural candidate observation, the same shadow cycle can
append a versioned record to `dlmm_candidate_fee_forecasts.jsonl`. It uses
already collected counters from the earliest complete matching sample 4–30
minutes earlier, the production SOL BidAsk geometry and a fixed hypothetical
0.1 SOL budget. The first prediction is frozen immediately after collection,
before its future mode horizon. Published native bin prices, exact integer
share/counter arithmetic, input hashes, geometry, horizon, input freeze time and
journal record time remain
bound to the record. It adds no subprocess or RPC calls. The existing candidate
phase and liquidation reserve still bound collection; missing, empty, oversized
or unsupported inputs stay unmeasured. At most 16 recent samples per indexed
pool are retained for this optional calculation; overflow remains unmeasured.

During a frozen forecast's terminal window, its pool remains eligible for a
read even if the ordinary 30-minute candidate watch has expired. Due terminal
observations receive priority within the same 64-pool, three-request and
10-second phase limits; the 240-second per-pool pacing and trading deferral
remain in force. A terminal-only observation does not create another forecast.
When the pool also has a fresh discovery/watch input, the same terminal read may
supply a new baseline without another RPC. The forecast validator still requires
complete current planned bins and prior history; a changed anchor may leave it
unmeasured. This prevents terminal scoring from silently suppressing fresh
candidate forecasts while preventing expired watches from renewing themselves.
Already observed terminal windows are skipped. This reduces dependence on
continued candidate selection, but does not guarantee coverage under the
shared request budget or recover missing historical observations.
Terminal reads use the earliest due forecast's original allocation anchor,
keeping the same bounded 69-below/16-above snapshot while separately observing
the current active bin and price. They do not freeze new forecasts from this
historical geometry. Different overlapping forecasts can still require bins
outside that single snapshot; missing coverage remains unmeasured.

`python3 scripts/dlmm_fee_forecast.py --profile <profile> [--as-of <timestamp>]`
reads and scores these recorded forecasts locally. It uses the first native
terminal observation within the mode horizon's 600-second grace and never
replaces an invalid first outcome with a later favorable one. It reports fees
at both the original and terminal price and compares fee pace at the actual
observed duration. Recorded geometry and horizons survive later production
parameter changes. The reader never creates retrospective forecasts.
An observation's allocation can differ from a later funded entry; using a
forecast for that entry requires separate support, identity and timing checks.

These are correlated observations of unfunded candidates, not realized position
returns. They cannot predict bin occupancy, the actual exit time, added-liquidity
impact or net cash profit. The scorer also reports a separate `principal_sensitivity`:
fixed inferred shares valued against terminal reserves, principal change against
allocated capital, and principal plus fees before costs. Unallocated rounding dust
stays in cash. A separate initial-inventory holding comparison distinguishes token
price revaluation from relative LP inventory change. Neither comparison is executed
profit or pure IL, especially when the inferred starting inventory contains tokens.
Entry composition charges, added-liquidity effects, rent and execution costs remain
excluded. They do not enter position profit acceptance or change entry
and exit rules. This replaces the fragile manual forecast capture used in the
earlier calibration study, whose overnight window produced no saved predictions.

#### Optional canonical market liquidity

After the bin reads, the same background command can append
`canonical_liquidity` and the DLMM `bin_step` to its existing sample. It derives
the SOL PumpSwap canonical pool and LP mint from the base mint, then reads the
pool, LP mint and possible base/quote vaults in one `getMultipleAccounts` call.
Only these canonical accounts share an atomic RPC slot; the earlier DLMM bin
reads are separate observations. The read has no retry, aborts after at most
300 milliseconds, and is skipped when the command has used its two-second
read allowance or a trading worker is active. The existing three-second process
timeout, pool rotation and liquidation reserve still apply. No RPC is added to
the entry or exit path.

Version 1 evidence binds the owner programs, pool discriminator, canonical PDA,
mint/vault identities and token authorities before retaining exact raw amounts.
`lp_circulating_raw` is the SPL mint supply; `protocol_lp_basis_raw` is the
pool's LP supply, which does not shrink when holders burn LP outside a withdrawal.
Their ratio is a potential withdrawal upper bound. Escrow, frozen accounts,
holder control and protocol settings can limit actual withdrawal; neither zero
circulating supply nor a nonzero boost establishes token safety or future profit.
`pool_coin_creator` is the currently observed fee recipient identity, not a
replacement for a developer missing from a historical entry record.

Retained protocol/creator fees are excluded from `real_quote_raw`.
`signed_virtual_quote_raw` is a signed i128, and `effective_quote_raw` adds it
to the quote vault amount. `boost_reserves_raw` adds the retained fees back to
the virtual field. The native decoder and journal validator preserve these
relationships, including negative virtual reserves. See the official
[PumpSwap LP supply description](https://github.com/pump-fun/pump-public-docs/blob/main/docs/PUMP_SWAP_README.md)
and [reserve/fee accounting](https://github.com/pump-fun/pump-public-docs/blob/main/docs/VIRTUAL_QUOTE_RESERVES_FEE_ADJUSTMENT.md).

Missing canonical pools, timeouts and invalid/unsupported accounts remain
`unmeasured` without invented zero balances. Optional failure cannot discard an
otherwise valid bin observation. The Python writer keeps only validated public
fields and bounded reason codes, never RPC URLs, response payloads or error text.
Both native request/observation timestamps and the existing collection timestamp
remain attached. These candidate observations cannot establish unchanged supply
or reserve state at a later entry without additional historical/freshness proof.
They do not activate a trading gate or predict a cash return.

### Position creation fees

For a new position spanning at most 70 bins, the executor may replace the SDK's
unsigned `initialize_position` instruction with `initialize_position_pda`, using
the wallet as payer, base and owner. The liquidity amounts, bin range, slippage,
remaining instructions, custody and close path are preserved. One signature
replaces two; in the frozen native-bank comparison, initialization and a funded
entry/close both saved 5,000 lamports, with identical position bytes, rent and
other account balances. This is a local cost comparison, not a live profit or
IL result. See the official
[Meteora position instructions](https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/program/instructions.mdx).

The PDA depends on wallet, pool, lower bin and width, so it must never replace an
old entry's identity. An existing entry file or any returned address history
keeps the ordinary builder. The optional history read has no retry and overlaps
the existing snapshot/build reads. Its background lifetime is at most three
seconds, so a reply taking over 300 ms can still be used when the builder takes
longer. Entry can wait only within the original 300 ms window measured from the
lookup's start; when that window has elapsed, a still-pending read is canceled
and the ordinary builder proceeds immediately. Any returned prior signature
or unavailable evidence keeps the ordinary builder. Build failures and
other early returns also cancel pending reads. PDA provenance
uses an exclusive file create before signing, protecting a race with another
writer. `position_creation` records the selected kind and public derivation
fields. Extended positions retain the ordinary initialization.

The exact final unsigned transaction still passes the native reserve simulation.
Only failure of that simulation before persistence/signing can select and
simulate the original SDK transaction instead. A successful simulation below
the native reserve floor is still rejected. After signing or uncertain
submission, the existing persisted signature and blockhash reconciliation apply;
there is no identity change, replacement signing or second position mint.

### Rent return during ordinary settlement

An owned ordinary settlement at 100 bps can append the existing empty-account
close instruction even when the swap alone already passes its net recovery
floor. The caller must explicitly opt into the ordinary settlement path; its
durable marker must say `emergency_exit: false`. Emergency/retry swaps and
unknown markers retain their existing path. The optional operation shares a
250 ms read/simulation timeout on an abortable connection and reuses the closed
position and exact wallet balance already checked before the swap was built.

Only a single supported token account holding exactly the owned input qualifies.
Legacy tokens, split accounts, unsupported extensions, missing lookup tables,
oversized transactions or a failed/timed-out simulation leave the original
swap in place. The combined simulation must preserve its conservative proceeds
after subtracting the existing rent reserve. A refund cannot disguise a worse
sale. Input, quote, slippage threshold and compute-budget instructions are
unchanged; signing, pending markers and confirmation still run once.

SPL enforces emptiness atomically after the swap. An external token transfer
after simulation can still make the combined transaction fail and require the
existing next-tick retry; simulation cannot reserve the bank state. Successful
inline closure avoids a later standalone cleanup transaction. The rent itself
is an existing asset, not profit; actual avoided fees depend on the cleanup
batch. `ordinary_token_rent_close` distinguishes this path in quote evidence,
and finalized account balance facts remain authoritative for accounting.

Historical ledger residues alone do not prove ownership of a new position's
withdrawal. Positive sale authorization now verifies each root fact's raw token
balance conservation and preserves the exact wallet token balance seen before
its first transaction. Same-mint activity by other owners/transfers since that
entry refuses a sale; the live balance must still match before signing. This
permits independently proved new lots even when earlier ledger residues remain
unresolved, without selling old inventory or rewriting historical accounting.

Batch and AI-selected signal risk sizing apply the existing conviction multiplier before selecting
an executable candidate. If the rounded ticket falls below the configured
minimum, that candidate is skipped instead of increasing its size back to the
minimum. A valid runner-up can still be selected; an explicit pool choice in a
signal is checked again before deployment. AI-selected records receive the same
per-candidate conviction adjustments once from the original signal score;
within-batch ranking adjustments require multiple candidates and therefore do
not apply to a singleton. Manual discovery retains its existing sizing.
This enforces the existing risk
budget and does not establish profitability or protect against a high-score
pool collapsing. It does not modify exits or existing positions.

Accepted automatic entries carry `risk_sizing` in the executor context persisted
before transaction submission: original and adjusted scores, adjustment notes,
requested ticket, multiplier, accepted ticket and configured minimum. This is
decision provenance, not a profit prediction. Manual discovery has no such
proof, and historical entries without it remain unknown rather than being
backfilled with today's policy or weights.

Native inventory verification recognizes both ordinary position initialization
and wallet-PDA initialization. PDA funding must bind the same payer, base wallet,
owner, pool and planned bin range before its SOL transfer can establish the
principal denominator. Unsupported or mismatched initialization remains
unmeasured; PDA fee savings must not disable independent native valuation.


### SOL BidAsk coverage under the bin limit

The Python entry path rejects SOL BidAsk candidates when the 20% minimum
price-range coverage requires more than the existing 100-bin technical limit.
It does not silently clamp an unsupported range into a narrower position.
Candidates are checked before winner selection, and the geometry helper also
rejects invalid or unsupported bin steps for other callers. The production Go
screen's 80–125 bin-step band retains its existing 53/44/35-bin geometry at
steps 80/100/125. Coverage describes a price range, not a loss cap or a profit
guarantee. Supporting correlated assets at smaller steps requires an explicit
strategy-specific range policy, not bypassing this check.

### Consistent entry bin anchor

The installed DLMM SDK's `getActiveBin()` fetches pool state independently,
while `initializePositionAndAddLiquidityByStrategy()` uses cached
`lbPair.activeId` for the instruction's active-bin anchor. Entry refuses a
noninteger or changed fresh bin before building or signing, so range selection
and the SDK builder use the same anchor. A later normal scanner pass may
reconsider the pool; this refusal does not submit a transaction or immediately
retry a moving price. This check adds no RPC reads and does not eliminate price
movement after the reads, replace on-chain slippage checks, or prove that
historical out-of-range exits were caused by this mismatch.

### Entry liquidity versus the exit floor

The predeploy gate reuses its existing DexScreener token response to inspect
the exact Solana pool's liquidity, while momentum retains its deepest-venue
selection. Known liquidity below the monitor's configured
`MIN_EXIT_LIQUIDITY_USD` rejects that candidate before further entry checks.
Pool addresses are case-sensitive. A different venue, missing liquidity,
negative value, boolean or nonfinite value cannot establish pool depth;
unknown data keeps the existing entry behavior. Evidence and the configured
floor are retained in `entry_live_gates`. This adds no HTTP calls and cannot
prevent liquidity disappearing after the observation. Historical thin-pool
exits alone do not prove the same liquidity was available to read before entry.

The exit-side reader also preserves unknown liquidity instead of coercing a
missing field to zero. Missing, boolean, negative and nonfinite depth cannot
trigger a thin-pool exit; an explicit zero still can. Invalid momentum fields
do not erase independently valid liquidity. Solana pool identity uses exact,
case-sensitive addresses, and an explicitly different chain is rejected.
These checks preserve existing risk thresholds and add no network requests.

### Position PDA history diagnostics

Entry provenance retains `position_pda_history_outcome`, a fixed reason code
from the optional lookup (`unused`, `history_exists`, `http_error`, `rpc_error`,
`invalid_history_response`, `history_read_failed`, `history_timeout`,
`wait_window_elapsed`, `cancelled`, or `not_started_or_unavailable`). No endpoint
or raw error is retained. This describes the history lookup, not every possible
rewrite or simulation fallback: `unused` with keypair creation still requires
examining later checks. The existing 300 ms wait window, background lifetime,
single lookup and unsigned fallback remain; no retry or additional RPC is added.

### Zero inventory after an unjournaled close

Settlement may complete zero root-owned token inventory when a local close
report is missing, only with reconciled close facts explicitly bound to every
root position and the wallet, a positive integer slot, successful landed status,
and proof that the position account closed. Other accounting refusal reasons
remain enforced. This exception never authorizes selling nonzero inventory,
touches legacy wallet tokens, creates a close report or marks cash accounting
complete by itself. It lets the normal settlement worker clear a stale pending marker
after an independently proved close without inventing profit or a refund.

Accounting separately records `unjournaled_close_evidence` when a successful
recorded close has wallet/position-bound finalized deletion evidence and its
slot is at least the latest successful deployment slot. This can establish
closure without a monitor report; pending transactions, residual inventory,
coverage gaps and all other accounting checks still prevent settled cash.
It does not backfill a journal, guess an exit reason or invent an LP mark.
Nonzero settlement inventory with a missing close journal remains refused.

The report also exposes derived `recovered_closes` with the recorded pool,
position, root, finalized block time and signature. Pool cash history includes
these identities within its existing 30-day/last-ten-close window, preferring
actual journal rows if present. Recovered rows carry no LP PnL mark. Root
completeness, refund ownership and cash-sign proof requirements remain in force;
recovering an identity cannot turn unvalued inventory into a profit or loss.

Jupiter HTTP 400 `CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD` triggers one paced
zero-slippage requote only for proved owned settlement inventory with an explicit
net recovery floor. The fallback must quote exactly one lamport in ExactIn mode,
with a one-lamport minimum and zero slippage. For this fallback alone, a known
price impact below 50% may exceed the ordinary percentage ceiling: the inferred
absolute impact on a one-lamport output is less than one lamport. Unknown impact
and impact at or above 50% still refuse; ordinary swaps retain their limits. The executor still checks inventory,
price impact and exact unsigned simulation, including an eligible atomic token
account close, before any send. Rent recovery is not trading profit. A changed or
invalid fallback remains `swap_quote_threshold_unavailable`: inventory stays
explicit, retries back off 900 seconds, and entry remains blocked. Only verified
zero owned inventory completes settlement.

### Entry-bound forecast references

Immediately before signing the first deployment transaction, the executor saves
`fee_forecast_reference` with entry provenance. This reads at most the final
256 KiB of the local candidate forecast journal, with no RPC or model call.
Only committed v2 records already recorded at that time qualify. Pool, token,
mode, bin step, exact contiguous bin range, 0.1 SOL capital and mode horizon must
match; the baseline may be at most 600 seconds old. Unsupported entries, missing
journals, partial records and missing matches remain explicitly unmeasured.

A `matched_reference` stores the forecast ID and SHA-256 of the exact journal
line. It is not a validated forecast or an entry approval: downstream evaluation
must independently rebuild the bound forecast and compare against settled cash.
The observation does not change entry eligibility, sizing, stops or reserve
policy. A bounded-tail miss is not evidence that no older matching record exists.

Run `python3 dlmm_entry_forecast_evaluation.py --profile PROFILE --start UNIX_TS`
for a read-only join of these references with per-position cash acceptance. The
evaluator checks the exact journal-line hash, independently rebuilds the forecast
from its hashed input snapshots, and checks entry time, capital and exact range.
Missing or invalid references do not remove positions from cash acceptance. The
report keeps modeled fee and settled cash separate: their ratio is not forecast
accuracy, and a verified reference is not evidence of profit. Existing entries
without a saved reference remain unmeasured; this command never backfills them.

### Repeat-entry cash loss refusal

The pipeline now rejects a pool with at least two closes in its last-ten,
30-day history when the proved aggregate cash upper bound is strictly negative.
It reads the local cash-history cache once per batch and binds each pool to the
current Redis close count and latest timestamp, including the separate original
journal binding for recovered closes. Evidence must be at most 900 seconds old,
cover every selected root, and use an exact, bounded or upper-only cash basis.
Unknown, stale, ambiguous or changed history does not trigger this cash refusal;
existing mark-loss and other entry gates still apply. This is a risk control,
not a claim that historical rejected trades would have lost or future entries
will profit. The same rule applies to direct and agent-selected pipeline calls.

### Event alerts outside settlement

The monitor persists event alerts in `memories/dlmm_alert_outbox` before
continuing. A separate loop worker delivers one message per tick with a 30-second
timeout and an exclusive delivery lock. Alert delivery cannot delay completion of
the risk scan or startup of the settlement worker. Failed or timed-out deliveries
remain queued across restarts; a timeout after remote acceptance can cause a
duplicate on retry. An empty `DLMM_ALERT_TARGET` disables delivery. Queue files
contain the original configured destination and message, with mode 0600.

This removes a potential scheduling delay, not the requirement to prove a close,
reconcile owned inventory, or simulate settlement recovery. It does not prove
that an earlier swap would have obtained a better price.

#### Confirmed Hadron slippage retry

For an owned token-to-SOL settlement whose quote uses only Hadron, the signed
transaction marker records the Jupiter instruction index and position. A
confirmed or finalized Jupiter `6001` failure at that index temporarily excludes
Hadron from quotes for the same wallet, token pair and position for five minutes.
Timeouts, other program errors, mixed routes and other positions do not activate
this exclusion. The quote journal records route labels and requested exclusions.

Alternative quotes retain the caller's slippage, price-impact, ownership and
net-recovery checks. An absent alternative or an ignored exclusion returns a
retryable result without signing. The exclusion expires automatically; it does
not permanently blacklist a venue or prove that another route would have been
profitable. This addresses repeated paid retries observed on TSI, whose four
Hadron failures produced instruction outputs about 4.928% below their quotes.
Failed instruction transfers reverted; their network fees remained paid.

### Settlement retry ordering

Pending exits take the worker's single settlement attempt before inventory
previously deferred for missing routes or uneconomic recovery. Within each
class, the oldest attempt still runs first. Deferred inventory retains its
15-minute retry backoff and is retried when no pending exit consumes the slot;
continuous pending exits can postpone it further. Ownership, pending-signature,
slippage, and positive-recovery checks are unchanged.

This addresses the October 20 COMPUTE exit, where an OMNI no-route retry ran
between pending COMPUTE attempts. It removes that queue interference; it does
not prove a particular saving or eliminate simulation, RPC, or market delays.

### Two recent individually proved pool losses

Pool memory also refuses a repeat entry when each of the two newest closed
positions on that pool has a strictly negative cash upper bound after matched
rent refunds. Older incomplete inventory stays unknown; this rule makes no
claim about the pool's lifetime or thirty-day aggregate profit.

The two proofs bind position, root, and close timestamp to the latest live
journal records. Both must be single-position, settled roots with unambiguous
refund ownership. Shared cleanup fees retain individual conservative bounds;
those bounds are never summed. A newer recovered close absent from the live
journal, zero/positive/unknown outcome, tied close timestamps, or a stale cache
prevents this new refusal. The existing aggregate-loss rule remains available.

This covers PAID's repeated small net losses despite older attribution gaps.
It is an entry risk constraint, not proof of improved trading returns: it can
also skip a future winner. Forward evaluation must retain rejected candidates
and all executed losses rather than claiming saved money from rejection alone.

### Paired net exit experiment

`dlmm_net_experiment.py backtest --profile <profile> --output <new-directory>`
compares recorded live entries/exits against fixed quote-based exit rules:
0.1% net take-profit, 1% net stop, and both. Entry timing, capital, and LP
allocation are held fixed. This is an exit-policy experiment, not a historical
re-execution of every version of the scanner or a new entry strategy.

Training precedes the chronological validation split. Only finalized lifecycle
costs whose trade and rent facts were already observed before that split train
the frozen p90 cost budget. Quotes include pool fees, price impact, and the
minimum output under quoted slippage; the budget covers observed network costs,
failed submissions, nonrefundable costs and cleanup. Full refundable rent return
is an explicit assumption. Extra-cost and unrecovered-ATA-rent stress cases are
reported. Hypothetical transactions can cost differently or fail, so modeled
net returns are not proved realized profit after all costs.

Missing quote opportunities cannot be recreated: the partial replay retains the
actual baseline exit when no observed quote triggers. Quote coverage, unknown
outcomes, and modeled-exit counts remain visible. Shared refund fees for actual
fallback exits are grouped once. Historical policies changed over the sample;
the recorded baseline must not be labeled a full backtest of today's code.

`dry-tick` records new actual entry identities after config freeze, reads one
position's native inventory and a sell quote, and freezes the first decision
per alternative. It only invokes `pnl-onchain`, never deploy/close/swap. It does
not alter the live trader. The timer samples one least-recently-observed open
position per minute, with a 20-second quote budget. Missing native reads or quotes
stay unmeasured. Closed pairs are reconciled in `dry-summary.json`; the current
strategy uses actual cash, and alternate earlier exits stay explicitly modeled.
A config hash prevents silent parameter changes mid-experiment. Use a new output
directory for a new protocol. The daily report is not a performance guarantee.
