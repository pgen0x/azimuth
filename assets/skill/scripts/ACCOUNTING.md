# Solana accounting evidence

Run from the profile script path (not the repository path):

```sh
python3 ~/.hermes/profiles/solanza/skills/solana-dlmm/scripts/dlmm_accounting.py --refresh --hours 24
```

The optional `azimuth-sol-accounting.timer` runs reconciliation every five minutes
in a separate service with a 45-second timeout, outside the trading loop. Its
unit targets the `solanza` profile; adjust the path for other installations.

`--refresh` only reads RPC and appends finalized facts to the local cache.
The window selects recently active roots; each root includes all recorded legs,
including legs before the window. This is not a period-return calculation.

## Files in the profile memories directory

- `dlmm_transactions.jsonl`: signature, wallet, position, root, operation and expiry;
  written before broadcast, including submissions whose confirmation times out.
- `dlmm_transaction_facts.jsonl`: finalized native balance change, fee paid by
  this wallet, raw SPL balance changes, chain outcome, block time and observation time.
- `dlmm_recenter_decisions.jsonl`: contemporaneous policy inputs and decision;
  existing live policy still uses its pool counters and LP marks.
- `dlmm_entries/*.json`: explicit root and immediate parent for new monitor reentries.

A journal write failure blocks new LP deployment, but does not block an exit or
liquidation; a warning records the coverage gap. Reports remain incomplete.

Duplicate signatures count once. Missing transactions remain unresolved, including
expired submissions whose historical absence has not been proven. Failed on-chain
transactions still contribute their fee. Raw token quantities retain integer precision.

Native wallet change already includes network fees and account rent movements:
subtracting the reported fee again would double charge it. It is **not net PnL**.
LP PnL remains a separate Meteora-valued measure. The report returns null for NAV
and net PnL until wallet-wide transaction coverage and asset marks are verified.

Historical/manual transactions and cleanup swaps without a position cannot be
attributed by guessing. Pre-existing token balances can mix with exit proceeds.
Still required for #93: wallet-wide reconciliation, external-flow classification,
open LP/SPL valuation, separate refundable rent vs permanent costs, inventory/swap
attribution, and root-chain policy replay. Replay must honor `observed_at` as well
as block time; facts fetched later were not available to the original decision.

The executor scripts are shared through profile symlinks. Local changes affect
new invocations immediately; use an isolated checkout for future development.
