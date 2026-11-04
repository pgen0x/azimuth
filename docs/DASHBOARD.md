# Operational dashboard

Run from the repository root (Go 1.22+, Python 3; existing PyYAML enables Hermes config metadata):

```sh
rtk go run ./cmd/dashboard
```

A password hash is required (see [Sign-in](#sign-in)); without it the dashboard serves no data. Open http://127.0.0.1:8787. From your laptop, run `ssh -N -L 8787:127.0.0.1:8787 <ssh-host>` (replace `<ssh-host>` with your SSH host or alias), then open that same address locally. The listener accepts loopback IPs only, rejects non-local Host headers, and exposes only GET/HEAD, apart from the `/login` and `/logout` form posts. For remote use, forward the localhost port over the existing SSH connection. No public listener, trading service restart, Telegram test, transaction, inference or RPC is needed.

Build a standalone binary (HTML and collector are embedded):

```sh
rtk go build -o /tmp/azimuth-dashboard ./cmd/dashboard
rtk proxy /tmp/azimuth-dashboard
rtk go test ./cmd/dashboard
```

Flags: `-listen`, `-profile`, `-state`, `-env-file`, `-redis`, `-dedup-prefix`, `-since` (live-change cutover, unix seconds; 0 = the last 7 days). Defaults use `~/.hermes/profiles/dlmm`, `~/.local/state/azimuth`, and repository `.env`; pass `-profile` when your Hermes profile has another name. The dashboard exits at startup if the profile directory does not exist, rather than serve empty panels. Only `REDIS_ADDR`, `REDISCLI_AUTH`, and `REDIS_SEEN_KEY` are read from that file; matching environment variables override file settings. `-redis disabled` skips Redis. Missing Redis configuration disables its panel. No credential is returned or logged. Config metadata is field-allowlisted; prompts, session messages, private keys and bot credentials are excluded.

For a persistent user service, build the binary and install the included unit:

```sh
rtk go build -o "$HOME/.local/bin/azimuth-dashboard" ./cmd/dashboard
rtk proxy sed "s|__REPO__|$PWD|g" assets/systemd/azimuth-dashboard.service > "$HOME/.config/systemd/user/azimuth-dashboard.service"
rtk proxy systemctl --user daemon-reload
rtk proxy systemctl --user enable --now azimuth-dashboard.service
```

The unit reads only the three Redis settings through the command, rather than importing the full trading environment. The unit passes no `-profile`, so it uses `~/.hermes/profiles/dlmm`; for another profile, add a drop-in such as `~/.config/systemd/user/azimuth-dashboard.service.d/profile.conf` that clears and restates the command (`ExecStart=` on one line, then `ExecStart=%h/.local/bin/azimuth-dashboard -env-file <repo>/.env -profile %h/.hermes/profiles/<name>`), then `systemctl --user daemon-reload`. The installation example is for a first install. For updates, use the [SHA-pinned deployment and rollback runbook](DASHBOARD_DEPLOY.md); do not build over the running binary or reuse a fixed backup name.

## Sign-in

Every page and every `/api/*` route needs a session. Only `/login`, `/favicon.svg` and `/ui.css` answer
without one: HTML routes redirect to `/login`, API routes return `401`.

- The password is checked against `DASHBOARD_PASSWORD_HASH`, a PBKDF2-HMAC-SHA256 hash (600,000 iterations,
  16-byte random salt, 32-byte key, constant-time compare) in the form
  `pbkdf2-sha256:<iterations>:<salt>:<key>`. PBKDF2 is built from the standard library because the module
  targets Go 1.22 and pulling in `x/crypto` for scrypt/argon2id would raise its Go version and dependencies.
- Generate a hash: the command reads one line from stdin without a prompt or echo control, so pipe the
  password from a password manager (or type it and press Enter in a private terminal). Nothing is stored or
  logged:

  ```sh
  rtk proxy "$HOME/.local/bin/azimuth-dashboard" -hash-password
  ```

- If the variable is missing or malformed the server refuses to serve data (fail closed) and the login page
  says why.
- Sessions are random 256-bit tokens in an `HttpOnly`, `SameSite=Strict` cookie, held in memory only (a
  restart signs everyone out), valid 12 hours, at most 32 at once. The cookie is not `Secure` because the
  listener is plain HTTP on loopback; reach it over an SSH tunnel.
- Five failed attempts within 10 minutes pause sign-in until the oldest failure ages out. One password check
  runs at a time. Cross-site posts to `/login` and `/logout` are refused.

The unit drop-in that supplies the hash is in [DASHBOARD_DEPLOY.md](DASHBOARD_DEPLOY.md#password-hash).

## Time zones

The API carries UTC epochs only. Daily series (`/api/capital` north star and calendar, `/api/robinhood` closes, `/api/live` realized per
mode) are split into days in the viewer's IANA time zone: the page sends
`Intl.DateTimeFormat().resolvedOptions().timeZone` as `?tz=`. The server validates the name with Go's embedded
zone database; a missing value means UTC, an invalid one falls back to UTC with `tz_fallback: true`. Each
response states the zone it used in `tz`. A zone is computed on first request (about a second) and kept in the
10-minute slow-panel refresh for the six most recently used zones, UTC always included. Every time the page displays names
its zone.

## JSON API

| Endpoint | Evidence |
| --- | --- |
| `/api/overview` | Latest persisted NAV, source freshness, unit states, collector timestamp/error |
| `/api/journal?q=IDENTIFIER&stage=swap&offset=0` | 50 rows/page, case-insensitive filter, exact stage filter, retained-tail match count |
| `/api/capital?tz=ZONE` | North star per local day over six weeks (cash, known, deltas, unpriced/deferred SPL counts, external-flow delta) and the 14-day NAV bridge |
| `/api/live?tz=ZONE` | Dust rent ledger and realized PnL by mode and local day since the `-since` cutover |
| `/api/robinhood?tz=ZONE&n=200` | Robinhood Chain: monitor unit state, scanner toggles, last `n` (1 to 1000) log lines, open positions per the journals, successful closes per quote asset and local day, stranded tokens |
| `/api/hermes` | Profile/model/fallback configuration, skills, gateway state, recent session metadata |
| `/api/redis` | Timestamped fixed capacity keys, position tracking sample, cooldown and dedup TTLs |
| `/api/agent/brief?hours=12&n=10&tz=ZONE&format=text` | Agent brief (see below): wallet, open positions, recent closes, entry funnel, health, alerts. JSON by default, the CLI's text with `format=text` |

Refreshes serve an immutable in-memory snapshot, built from two collector halves with a 60-second deadline
per run (a slow run delays the next one; runs never overlap):

- **Fast panels, every 60 seconds:** the event journal, latest NAV row, source freshness, unit states, Hermes
  and Redis. `collected_at` is this half's time.
- **Slow panels, every 10 minutes:** day calendars per zone, the 14-day NAV bridge, the dust rent ledger and
  Robinhood (unit journals, positions, closes). `slow_collected_at` is this half's time. They are day-scale or
  48h-scale evidence, and were about 80% of a refresh's CPU (NAV lookups in a ~200MB `dlmm_nav.jsonl` per zone,
  `journalctl --grep` over 48 hours).

Fast plus slow panels carry the same content as a single full collection at the same instant (tested), plus `slow_collected_at`. Collection
failure retains the previous snapshot or slow panels and exposes an error; a failed slow half is retried on the
next 60-second tick. Browser activity never invokes NAV collection, accounting runs, blockchain RPC, model/provider probes or Helius Wallet API.

## Agent brief

One compact read for an orchestrating agent, from the same collector (its `brief` mode), read only:

```bash
azimuth-dashboard brief --profile ~/.hermes/profiles/<profile>            # text, about 40-60 lines
azimuth-dashboard brief --json --hours 24 --n 20 --tz Asia/Jakarta --profile ...
```

The subcommand needs no HTTP server, login or Redis. `/api/agent/brief` serves the same result behind the
normal sign-in, cached for 20 seconds per parameter set, with one collector run at a time.

| Section | Source and basis |
| --- | --- |
| wallet | `dlmm_nav.jsonl`, last snapshot per day in `tz` over 14 days: native, cash, known, rent, daily deltas (the rows the capital north star reads; days split in `tz`). External flows are not netted out. |
| positions | Latest `MONITOR_REPORT:` line of `azimuth-sol-monitor.service` (15 min); a newer `0 position(s) found on-chain` line empties it. pnl is a portfolio MARK, never money. |
| closes | Last close row per position in `dlmm_closes.jsonl`, joined to `dlmm_realized.jsonl`. Money is `realized_sol` only; `pnl_basis` is `realized`, `unmeasured` (row with a null figure) or `not_reconciled` (no row yet). |
| funnel | `azimuth.service` journal markers (`SIGNAL batch sent`, `entry_route=... reason=...`, audit/cooldown/lone rejects, direct deploy runs), `dlmm_pipeline_rejects.jsonl` gates and submitted deploy transactions in `dlmm_transactions.jsonl` (recorded before broadcast, not chain-confirmed). |
| health | `azimuth`, `azimuth-sol-monitor`, `hermes-gateway`, `azimuth-dashboard` active + enabled; failed user units; disk free % of the profile volume; MemAvailable; age of the monitor's last `OBSERVER_TICK`. |
| alerts | disk free < 15%, MemAvailable < 1200 MB, core unit not active / not enabled / failed, any failed user unit, `azimuth-sol-rent` failed (when installed), an executor marker (`dlmm_pending_{swaps,deploys,rent,closes}`, `dlmm_settlements`) older than 2 h, no deploy submitted in 12 h, monitor tick older than 2 min, a section that could not be read. Each alert has an `id` (its code, plus the unit for per-unit rules). |
| today | Today's native SOL (latest `dlmm_nav.jsonl` snapshot, day in `tz`) minus yesterday's last; the rent reclaimed since local midnight from the `azimuth-sol-rent` unit journal, verified against wallet transaction facts (the same rules as the live dust ledger), and the delta net of that rent. Any unverified rent receipt makes the rent total null; a labeled verified subtotal is shown beside it. |
| realized_7d | `dlmm_realized.jsonl` rows closed in the last 7 days: n, measured, sum and mean `realized_sol` by mode (from the close journal) and by entry route (the entry file's `risk_sizing.source`: `from_batch` = `deterministic`, `from_signal` = `ai`; older entries `unknown`, missing file `no_entry_file`). Unmeasured rows count in n, never as 0. |

The dashboard's **ops** section shows the funnel, health and alerts of this brief.

## Operator alerts

The brief's alert rules, run unattended so a red flag reaches the operator without an agent watching:

```bash
azimuth-dashboard alerts -profile ~/.hermes/profiles/<profile>                     # print new/cleared alerts
azimuth-dashboard alerts -profile ... -send-cmd "hermes send -t telegram"           # pipe them to a sender
```

It runs only the panels its rules read (health, last deploy, markers; under a second). Differences from the
brief: MemAvailable alerts below **800 MB** (the OOM line, not the brief's 1200 MB heavy-step line), and
`no_deploy_12h` is marked `i` (info) rather than `!`.

- **Dedup.** `-state-file` (default `~/.local/state/azimuth/alerts.json`) remembers, per alert id, whether the
  operator was last told it is firing. A message goes out only when an alert starts or clears, at most one per
  alert id per 6 h; a raise or clear held back by that cap goes out on the first run after the window opens. A
  standing alert is only listed under `still firing` when something else is sent.
- **Blind runs never clear.** If the collector fails, or any section is unavailable, alerts missing from that
  run keep their state; `collector_failed` is raised instead.
- **Sending.** The plain-text message (at most 1000 characters) is piped on stdin to `-send-cmd`, split on
  whitespace like `REPORT_CMD`. Empty prints it. A send failure is logged to stderr, leaves the state unsaved so
  the next run retries, and exits 0 so the timer stays green; only bad flags exit non-zero.
- **Timer.** `assets/systemd/azimuth-alerts.{service,timer}` (every 10 min) are rendered into
  `<profile>/systemd/` by `install.sh` and never enabled by it. Copy both to `~/.config/systemd/user/`, add the
  `-send-cmd` drop-in shown in the service file, then `systemctl --user enable --now azimuth-alerts.timer`.

## Trace

One position's lifecycle, or every position and pipeline reject of a pool or symbol, for debugging without
grepping journals. Same collector (its `trace` mode), read only, CLI only (not served over HTTP):

```bash
azimuth-dashboard trace <position> --profile ~/.hermes/profiles/<profile>   # chronological timeline
azimuth-dashboard trace <pool|SYMBOL> --days 7 --profile ... --json          # positions + rejects in the window
```

A position timeline joins on exact identifiers: the newest webhook delivery before the deploy whose payload
carries the pool (`solana_deliveries.jsonl`, with its HTTP acceptance), the scanner's batch / `entry_route=` /
`direct deploy done` lines naming the symbol, the Hermes decision (first 300 characters of the last assistant
message in that delivery's webhook session, `state.db` opened read-only, redacted), pipeline rejects of the pool in
the 2 h before deploy, the entry file (including `active_bin_reanchor`), the monitor's `MONITOR_REPORT` lines for the
position (count, MARK pnl min/max, out-of-range ticks), every close-journal row (marks labeled), the settlement
file, the `dlmm_realized.jsonl` row (the arbiter) and the cooldowns the monitor printed at close plus the daemon's
later `in re-entry cooldown` skips for the pool. Redis is not read; cooldowns come from the unit journals.
A pair name (`NIO-SOL` or `SOL-NIO`, any case) is looked up as its symbol.
Exit status 3 means nothing was found.

## Source traceability and scope

- NAV: `memories/dlmm_nav.jsonl`; native SOL, SPL marks, LP marks and recoverable account reserves remain separate. Unknown NAV stays JSON null and displays Unknown.
- Journal: delivery/rejection files under state, and transaction/fact/wallet-fact, close, decision, rent and realized journals under profile memories. Each row carries a source path, observed time and explicit evidence identifiers. Each journal reads at most 2 MiB / 500 complete recent rows; NAV retains one row. Partial final lines are omitted; invalid lines and truncated coverage are reported. These are source tails, not exhaustive historical counts.
- North star (Capital tab): latest snapshot per local day in the requested zone, including null values, with selection coverage. Cash is native + LP mark + refundable rent; known also includes SPL marks. Missing/unknown days break deltas. See the bounds and large-file ordering limitation below.
- NAV bridge (Capital tab, issue #93): known-SOL deltas and a source-qualified decomposition using transaction-kind, wallet, realized and close journals. Complete measured components reconcile; incomplete components stay null. Unattributed cash stays separate from rent. Snapshot history coverage and every journal status are exposed. It is not NAV/ROI or withdrawal + fees - deposit.
- Live changes: deduplicated rent-unit receipt claims, separately verified transaction/account results, measured costs and explicit unknown totals. Realized PnL by mode uses close time and the close journal; wholly unmeasured cohorts remain null. The rules and coverage limits below apply to both views.
- NAV ordering (fix2): over 4 MiB the NAV journal is binary-searched within 8 MiB / 256 reads / 2 s per lookup. Whole-file ordering is not provable there, so each lookup checks the timestamps of every row it visited including every row of the backward scan, plus one neighbour line on each side of the selected row (`ordering_assumption: visited_window_monotonic`); only an observed inversion marks that day partial. `dlmm_closes.jsonl` only labels bridge modes: legacy corrupt lines are reported as `closes_invalid_lines`, and make the bridge incomplete only when a lifecycle in the window has no mode (`mode_unknown`).
- Close marks: `pnl_sol` in `dlmm_closes.jsonl` is the mark read one tick before the close, not realized cash. The journal passes the row's `pnl_basis` through and labels older rows without one `mark_unlabeled`; realized figures come only from `dlmm_realized.jsonl` (`realized_sol`, null = unmeasured).
- Entry metadata: latest 100 `memories/dlmm_entries/*.json`; metadata is not proof of a landed deployment.
- Routing: last 100 `entry_route=` markers from the actual `azimuth.service` journal within 48 hours. Only mode, route, reason and timestamp are extracted. No free-form service logs or Hermes tool messages are exposed.
- Session correlations: exact legacy or v2 webhook identity for deliveries, against the latest 40 session metadata rows in read-only SQLite. No time/pool heuristic invents a trade link; incomplete coverage remains uncorrelated. An HTTP 202, route/probe result or open session is not execution proof.
- This bot only: the dashboard has no evaluation or comparison view. As a guard, the collector also drops, recursively, any snapshot key containing `comparison`, `reference_bot`, `other_bot` or `lp_comparison` (case-insensitive), so such data reaches neither a page nor the JSON API. To hide more key names, set `DASHBOARD_HIDE_KEYS` in the dashboard's environment to a comma-separated list of case-insensitive substrings, for example `DASHBOARD_HIDE_KEYS=somebot,peer_wallet`. The pages render what the collector returns and apply no filter of their own.
- Hermes: selected `config.yaml` fields, installed profile skill names and read-only `state.db` metadata. Provider and bot delivery availability remain Unknown without a probe. Gateway state comes from systemd.
- Services: the scanner, gateway, SOL monitor, accounting and rent services/timers this repository ships, using selected systemd properties. `DASHBOARD_EXTRA_UNITS` adds your own user units (comma-separated `name.service` / `name.timer`, at most 16; other names are ignored). Inactive oneshots can be healthy; a failed run can be a busy-wallet deferral rather than an infrastructure failure.
- Robinhood: `azimuth-rh-monitor.service` state from systemd; the Robinhood toggles from the `scanner: started` line of the current `azimuth.service` run (read in a five-minute window after its start; Unknown when absent); the last 1000 monitor journal lines plus `[rh-` / `robinhood` lines of `azimuth.service` from 48 hours. Log text gets the redaction every panel uses (any URL, any scheme or case; the rest of any line where a secret-like name is followed by `=` or `:`, bare, quoted or JSON; the rest of any line after a wallet phrase word such as `mnemonic` or `seed phrase`, even in prose; text that already contains a mask marker is not trusted) plus masking of every 64-hex string (keys and transaction hashes alike). Bare uppercase credential names and keywords anywhere in uppercase names are covered; nested credential fields are masked before serialization. Public identity fields such as `tokenId`, `token_id`, pool IDs, mints and addresses stay. Positions are "open" when `uni_positions.jsonl` / `uni_v4_positions.jsonl` hold a mint with no successful close for the same protocol and token ID: a journal view, not a chain read. Closes count only `success == true`, non-dry-run rows of `uni_closes.jsonl`; money is `realized_quote` summed over `pnl_basis == "realized"` rows per quote asset (v3 WETH and v4 native ETH are both ETH, USDG separate; a missing or unsupported quote asset has no known unit and is never summed), a null is unmeasured and counted, and `pnl_pct` is a mark shown only to rank. Rows that left stranded or unclaimed value are flagged. Gas is the metered `gas_eth` / `gas_txs` sum. Stranded tokens come from the latest line per token of `uni_stranded.jsonl` / `uni_v4_stranded.jsonl`, amounts in raw token units.
- Redis: `SCARD`, one bounded `SSCAN` of `sol:dlmm:active_positions`, and pipelined `TTL`/bounded `GETRANGE` for at most 400 derived keys. At most 100 recent candidate records and 100 active members inform the sample. Position fields are allowlisted; arbitrary stored error strings are not exposed. No KEYS, writes, arbitrary-key or command endpoint. TTL -2 means missing, -1 means no expiry, null means read failure. All TTLs are observations at the displayed timestamp.

Native SOL increases include recovered principal/rent and transfers; they do not establish profit. The overview does not show an entry floor: entry is decided by the configured cash policy (`dlmm_cash_policy.json`: reserve, rent allowance, minimum ticket) and the other entry guards, which this dashboard never authorizes or changes.

Configuration editing, restarts, historical indexing and active provider/bot probes are outside this read-only MVP.

### Evidence coverage in Capital and Live changes

Receipt signatures are deduplicated. `receipt_claimed` is separate from
`verified_subtotal`: failed, unlanded, missing or conflicting outcomes never
credit verified closes, rent or forfeiture. Successful landing alone is not
account-close proof: account rent evidence and wallet delta must match, and
mint deltas must match a claimed burn. Quotes remain receipt valuations. Fees
and native deltas include measured landed failures. Window totals are null
when evidence is missing; a verified subtotal is not a complete window total.

Every bridge journal retains source metadata, including transaction kinds.
Missing/oversized/corrupt/partial sources, incomplete wallet history and null
money fields prevent an `ok` decomposition. Native identity is unknown when
wallet deltas or coverage are unknown. Unattributed flows are never classified
as rent. Realized cells with no measured closes stay null; mixed cohorts show
only their labeled measured subtotal and unmeasured count.

NAV searches parse top-level timestamps before using them, and preserve the
latest day's null fields. A lookup reads at most 8 MiB / 256 operations, with a
1 MiB line limit and a two-second work deadline. Files up to 4 MiB are scanned
and ordering checked within that budget. Larger files use bounded seeks; every
row a lookup reads is ordering-checked, and an observed inversion marks that
day partial (its deltas and bridge attribution stay unknown). Ordering of rows
the lookup did not read is assumed, not proved (`visited_window_monotonic`); a
verified historical index would be needed to prove large-file coverage.
No new index is written by the read-only dashboard.

Whole accounting journals are capped at 64 MiB, 100,000 lines and 1 MiB per
line. Rent-unit capture has a five-second deadline and a combined 2 MiB
stdout/stderr cap; nonzero exit, timeout or capture cap is unavailable, while
the 5,000-line tail limit is partial coverage. Errors are grouped only after
sanitizing their messages. Every API/tab carries collector freshness/errors;
Capital and Live refresh automatically. A malformed new panel is isolated from
unrelated panels. These are resource and evidence limits, not profit claims.

## Verified deployment reports

The `dlmm-report-guard` Hermes plugin uses official pre/post tool hooks and
`transform_llm_output`. For the `dlmm-signal` webhook it injects a fresh nonce into
a direct terminal pipeline call, accepts a receipt only from that call's successful
completed result, and replaces AI deployment text with the pipeline's exact values.
Dry runs and submissions awaiting position verification have separate statuses.
Without a matching receipt, deployment claims are withheld; inspect transaction
facts before retrying. Receipts prove tool execution and its verification result,
not profit. Rejections without deployment claims keep their AI narrative.

Install into the target profile's `plugins/dlmm-report-guard/` by copying
`assets/hermes/plugins/dlmm-report-guard/{plugin.yaml,__init__.py}`; then run
`hermes -p <profile> plugins enable dlmm-report-guard --no-allow-tool-override` and
`hermes -p <profile> plugins doctor dlmm-report-guard --ci`. Set
`display.platforms.webhook.streaming: false` so provisional model text cannot
precede the final guard. Restart the gateway after checking no deployment is in
flight. The plugin needs no dependencies and does not change model order or risk.

The dashboard journal reads only `dlmm_report_guard.jsonl` metadata (session ID,
status, receipt count, timestamp), never raw messages, tool output or receipt nonce.
Legacy receipt counts alone never prove
execution. Output preparation is separate from session closure and Telegram delivery;
no lifecycle state proves a worker is live or permits retrying a batch.
The guard is scoped to this profile and route, bounds in-memory state to 256 turns,
and deliberately fails closed for execution claims after process restart or when
an execution result was not completed. It is protection against model mistakes,
not a sandbox against an agent with arbitrary shell access. Direct agent messaging
outside the webhook final response is outside this hook.

Offline check: `python3 assets/hermes/plugins/dlmm-report-guard/test_guard.py`.

## Shared router account cooldown

The installed 9router 0.5.95 CLI build has a version-pinned operational fix in
`assets/hermes/scripts/router_account_cooldown.py`. Exact CodeBuddy CN/Intl account
restriction (`403 / 11140`) and exhausted credit (`429 / 14018`) responses use
the existing connection-wide lock for 30 minutes, extended by a later provider
retry deadline. Antigravity `RESOURCE_EXHAUSTED / QUOTA_EXHAUSTED` responses
with a valid Google `RetryInfo.retryDelay` preserve the specified reset deadline
in the existing model-specific lock; malformed/absent delays keep normal fallback.
The chat fallback also persists reset deadlines learned by the Antigravity quota
cache before selecting another account, so restarting the router preserves them.
Explicit Antigravity quota exhaustion stops retries within that HTTP call;
temporary rate limits and capacity errors retain the existing retry behavior.
Temporary rate limits and unrelated provider/model errors retain
the router's existing behavior. A future global lock remains effective when a
model-specific lock has expired. Model order, credentials, quotas and trading risk
settings are preserved. This respects provider limits and does not replenish quota.

Run the script with `--app /path/to/9router/app` to validate the exact build and
exercise every patched lock reader and the account error writer without network
calls. Add `--apply --backup-dir /new/backup/directory` to install, then restart
9router. The backup manifest lists original JS files and before/after hashes.
Restore those backups and restart to roll back. A router package update can
replace the compiled fix; version/build mismatches stop before edits. Re-audit
upstream before applying to another version. Do not clear live provider locks
to test or speed up fallback.
