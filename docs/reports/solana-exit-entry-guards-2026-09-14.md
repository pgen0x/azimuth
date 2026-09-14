# Solana exit and entry guards — 14 September 2026

Follow-up to the journal/API audit at `/home/ubuntu/azimuth-audits/review-2026-09-14/report.md`. The 24h first post-deployment LP flow was −0.009680 SOL for Azimuth versus +0.098837 SOL for Meridian. Latest rolling 24h was +0.004457 / −0.013005 SOL; cumulative 37h25m was −0.008353 / +0.068762 SOL. These exclude wallet swap/gas/rent settlement and open positions.

## Failure and change

PERPSPAD's monitor re-center and scanner minted positions one second apart on the same pool. A preflight exposure snapshot did not serialize the shared executor. The additional scanner position lost 0.010005 SOL. It also peaked +2.79%, armed trailing, and continued through repeated indicator vetoes until the hard stop: trailing had already occupied `close_reason`, hiding the downtrend guard.

- Tight-mode risk floors now override discretionary profit reasons before the indicator/AI hold stages. Armed trailing, downtrend, fast-out and giveback stops cannot be vetoed in turnover/pulse. Existing emergency reasons and hard stops take priority. Thesis modes and pure report-only semantics are retained.
- Every raw DLMM deployment shares a wallet-level Linux abstract-socket lock, including scanner, LLM and monitor re-center. Under that lock the executor reads on-chain position accounts and refuses existing exposure in the same pool or a sibling pool with the same non-SOL mint. Missing/failed chain reads block new deployment; cached Redis/portfolio emptiness cannot authorize one.
- Before sending, the executor persists the position, signed transaction signature/blockhash and last valid block height. It sends those exact bytes. Errors after submission return UNVERIFIED without RPC failover into another mint or blindly closing potentially funded liquidity. The durable reservation remains through blockhash expiry, including successful sends, before a subsequent entry can recheck exposure. This temporarily serializes wallet entries through the validity window; exits and swaps are not locked. Linux lock scope is this host; multi-host trading would require a distributed reservation.
- Pipeline and re-center pass entry provenance, persisted before broadcast. Timeout adoption recovers the exact mode, strategy, range and root-chain from that record. Re-center uses the existing 120s close-command budget instead of 30s and no longer claims an unconfirmed mint definitely failed.

No changes to ticket sizing, range width, momentum/organic/bundler limits, cooldown duration or Robinhood code. Re-center profitability and wallet settlement accounting remain separate follow-up measurements, not solved by these guards.

## Why Meridian's capital is not the whole explanation

In the first 24h, Meridian deployed 19.499999 SOL cumulatively across 39 closes (about 0.5 SOL per position). Azimuth recycled 8.959959 SOL across 71 closes (about 0.1262 SOL per position). Meridian therefore used about 3.96x the average ticket and 2.18x total recycled deposits. These are not initial wallet equity or NAV.

Even after normalizing by recycled deposit, Meridian returned +0.5069% versus Azimuth −0.1080%. Fees/deposit were 1.0175% versus 0.4812%; principal change/deposit −0.5107% versus −0.5893%. On 11 pools common to both wallets during that window, return/deposit was +0.3446% versus +0.0201%. Entry times, bin placement and fee share still differ. Larger capital explains larger nominal flow, not the entire normalized gap. Identical fixed transaction costs are a smaller fraction of a larger ticket; their actual contribution cannot be measured without wallet cost reconciliation. Scaling a losing process is not evidence of improved returns.

Meridian also suffered an INDEX close of −0.098646 SOL, making its latest 24h negative despite a high win rate. Preserve risk gates; do not infer guaranteed profit from one favorable interval.

## Verification

- `python3 assets/skill/scripts/test_dlmm_guards.py`: executes the production hold section against PERPSPAD-like trailing/downtrend/SL states, preserves thesis-mode veto, verifies provenance.
- `node assets/skill/scripts/test_dlmm_executor.js`: real cross-process socket exclusion, concurrent deploy, on-chain same-token exposure, exact signed blockhash, pending/expired reservation, read/build failure, post-send timeout, partial wide mint and chain confirmation error, malformed marker and invalid amount.
- Existing `test_solana_policy.py`, Python syntax, Node syntax, Go vet/test/build and diff whitespace checks.
- Read-only live SDK query with the Azimuth public wallet succeeded and refused the already-held reference pool. No test submitted a transaction.

Deployment timestamps and hashes are recorded outside the repository under `/home/ubuntu/azimuth-audits` when applied. Profitability after this patch remains to be observed.
