# Operational dashboard

Run from the repository root (Go 1.22+, Python 3; existing PyYAML enables Hermes config metadata):

```sh
rtk go run ./cmd/dashboard
```

Open http://127.0.0.1:8787. From your laptop, run `ssh -N -L 8787:127.0.0.1:8787 oc` (replace `oc` with your SSH host alias), then open that same address locally. The listener accepts loopback IPs only, rejects non-local Host headers, and exposes only GET/HEAD. For remote use, forward the localhost port over the existing SSH connection. No public listener, trading service restart, Telegram test, transaction, inference or RPC is needed.

Build a standalone binary (HTML and collector are embedded):

```sh
rtk go build -o /tmp/azimuth-dashboard ./cmd/dashboard
rtk proxy /tmp/azimuth-dashboard
rtk go test ./cmd/dashboard
```

Flags: `-listen`, `-profile`, `-state`, `-env-file`, `-redis`, `-dedup-prefix`. Defaults use `~/.hermes/profiles/solanza`, `~/.local/state/azimuth`, and repository `.env`. Only `REDIS_ADDR`, `REDISCLI_AUTH`, and `REDIS_SEEN_KEY` are read from that file; matching environment variables override file settings. `-redis disabled` skips Redis. Missing Redis configuration disables its panel. No credential is returned or logged. Config metadata is field-allowlisted; prompts, session messages, private keys and bot credentials are excluded.

For a persistent user service, build the binary and install the included unit:

```sh
rtk go build -o "$HOME/.local/bin/azimuth-dashboard" ./cmd/dashboard
rtk proxy sed "s|__REPO__|$PWD|g" assets/systemd/azimuth-dashboard.service > "$HOME/.config/systemd/user/azimuth-dashboard.service"
rtk proxy systemctl --user daemon-reload
rtk proxy systemctl --user enable --now azimuth-dashboard.service
```

The unit reads only the three Redis settings through the command, rather than importing the full trading environment. After dashboard code updates, rebuild the binary and restart `azimuth-dashboard.service`.

## JSON API

| Endpoint | Evidence |
| --- | --- |
| `/api/overview` | Latest persisted NAV, source freshness, unit states, collector timestamp/error |
| `/api/journal?q=IDENTIFIER&stage=swap&offset=0` | 50 rows/page, case-insensitive filter, exact stage filter, retained-tail match count |
| `/api/evaluation` | Existing evaluation JSON, source file, generation and window timestamps |
| `/api/hermes` | Profile/model/fallback configuration, skills, gateway state, recent session metadata |
| `/api/redis` | Timestamped fixed capacity keys, position tracking sample, cooldown and dedup TTLs |

Refreshes serve an immutable in-memory snapshot. A background collector updates every 30 seconds with a 20-second deadline. Collection failure retains the previous snapshot and exposes an error. Browser activity never invokes NAV collection, accounting evaluation, blockchain RPC, model/provider probes or Helius Wallet API.

## Source traceability and scope

- NAV: `memories/dlmm_nav.jsonl`; native SOL, SPL marks, LP marks and recoverable account reserves remain separate. Unknown NAV stays JSON null and displays Unknown.
- Journal: delivery/rejection files under state, and transaction/fact/wallet-fact, close, decision, rent and realized journals under profile memories. Each row carries a source path, observed time and explicit evidence identifiers. Each journal reads at most 2 MiB / 500 complete recent rows; NAV retains one row. Partial final lines are omitted; invalid lines and truncated coverage are reported. These are source tails, not exhaustive historical counts.
- Entry metadata: latest 100 `memories/dlmm_entries/*.json`; metadata is not proof of a landed deployment.
- Routing: last 100 `entry_route=` markers from the actual `azimuth.service` journal within 48 hours. Only mode, route, reason and timestamp are extracted. No free-form service logs or Hermes tool messages are exposed.
- Session correlations: exact legacy or v2 webhook identity for deliveries, against the latest 40 session metadata rows in read-only SQLite. Existing evaluation delivery correlations are also retained with their report source. No time/pool heuristic invents a trade link; incomplete coverage remains uncorrelated. An HTTP 202, route/probe result or open session is not execution proof.
- Evaluations: newest generated valid report among the latest 50 modified `reviews/*/evaluation.json` files, each capped at 32 MiB. Existing calculations are displayed without recomputing finance. LP wins use full-life LP positions; cash-positive roots use settled roots. Incomplete roots, carry-in closes, Meridian cohorts, pooled cash and matched refund evidence retain their source bases. Shared refunds are never independently summed or allocated. Root cash, pooled cash and refund groups overlap. Root cash excludes refunds that require grouping multiple roots; the matched-refund table shows the corresponding group cash including those refunds. Compare their root sets before drawing conclusions.
- Hermes: selected `config.yaml` fields, installed profile skill names and read-only `state.db` metadata. Provider and bot delivery availability remain Unknown without a probe. Gateway state comes from systemd.
- Services: fixed scanner, gateway, SOL monitor, accounting, rent and daily-review services/timers using selected systemd properties. Inactive oneshots can be healthy; a failed run can be a busy-wallet deferral rather than an infrastructure failure.
- Redis: `SCARD`, one bounded `SSCAN` of `sol:dlmm:active_positions`, and pipelined `TTL`/bounded `GETRANGE` for at most 400 derived keys. At most 100 recent candidate records and 100 active members inform the sample. Position fields are allowlisted; arbitrary stored error strings are not exposed. No KEYS, writes, arbitrary-key or command endpoint. TTL -2 means missing, -1 means no expiry, null means read failure. All TTLs are observations at the displayed timestamp.

Native SOL increases include recovered principal/rent and transfers; they do not establish profit. The existing 0.20 SOL reserve + 0.05 allowance + 0.10 minimum position rule is displayed as a 0.35 SOL floor; this dashboard never authorizes or changes entry behavior.

Configuration editing, restarts, historical indexing and active provider/bot probes are outside this read-only MVP.

## Verified deployment reports

The Solanza `dlmm-report-guard` Hermes plugin uses official pre/post tool hooks and
`transform_llm_output`. For the `dlmm-signal` webhook it injects a fresh nonce into
a direct terminal pipeline call, accepts a receipt only from that call's successful
completed result, and replaces AI deployment text with the pipeline's exact values.
Dry runs and submissions awaiting position verification have separate statuses.
Without a matching receipt, deployment claims are withheld; inspect transaction
facts before retrying. Receipts prove tool execution and its verification result,
not profit. Rejections without deployment claims keep their AI narrative.

Install into the target profile's `plugins/dlmm-report-guard/` by copying
`assets/hermes/plugins/dlmm-report-guard/{plugin.yaml,__init__.py}`; then run
`hermes -p solanza plugins enable dlmm-report-guard --no-allow-tool-override` and
`hermes -p solanza plugins doctor dlmm-report-guard --ci`. Set
`display.platforms.webhook.streaming: false` so provisional model text cannot
precede the final guard. Restart the gateway after checking no deployment is in
flight. The plugin needs no dependencies and does not change model order or risk.

The dashboard journal reads only `dlmm_report_guard.jsonl` metadata (session ID,
status, receipt count, timestamp), never raw messages, tool output or receipt nonce.
Evaluation also correlates allowlisted public position/signature IDs and dry-run/
verification flags from guarded outputs. Legacy receipt counts alone never prove
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
