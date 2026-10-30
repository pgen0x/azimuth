# Observe bundle: gated activation and rollback

Gated activation and rollback steps for the observe bundle. These are operator steps
for a reviewed integration tip, after user approval for a canary. Nothing in the
offline review executes them. Set `EXPECTED_PRE` to the full SHA of the production
commit you reviewed as the base. Create the integration tip from that exact base in a
separate worktree, merge the reviewed observe branch there, and pass suites with
observe OFF/ON and with every feature flag your production runs at both values.
If production HEAD has moved, stop and review a new integration base.
Do not replace the production binary.

Set `P` to the production checkout, `U` to its user-systemd config directory,
`RUN_PARENT` to a private evidence directory, `TIP` to the full approved integration
SHA, `EXPECTED_PRE` to the reviewed production base SHA, `PROTECTED_DROPINS` to the
existing drop-ins that must survive (below), and `REVIEWED_STATUS` to the
exact `git status --porcelain` output reviewed for this deploy (including existing
user edits). `HERMES=0` by default; `HERMES=1` needs explicit approval to restart
the gateway. `HERMES_UNIT` names that unit: `hermes-gateway` by default, or the
name your install uses (for example `hermes-gateway-<profile>`); it must match
`hermes-gateway` or `hermes-gateway-<name>`, and activation records it for the later
blocks. Both activation and rollback check its cgroup for work in flight,
as they do for azimuth. Run each block in a fresh bash.

The activation block aborts on any failure. It creates a unique evidence directory
and refuses any existing `observe-bundle.conf`, including a symlink; retries must
review the partial deployment first. Save the printed `RUN` path for rollback.
`PROTECTED_DROPINS` is a space-separated list of the drop-ins your production already
relies on, relative to `$U`, for example
`PROTECTED_DROPINS="azimuth.service.d/my-override.conf azimuth-sol-monitor.service.d/my-flag.conf"`.
List every existing drop-in on the affected units (`systemctl --user cat <unit>` shows
them); an empty value is allowed only when there are none, and leaving it unset is
refused. Each listed file is recorded by hash and must remain in place, byte-for-byte:
every block re-checks the hashes and stops on a difference. Do not rename, copy over,
remove or reorder them. All profile files remain untouched. Flags
read from profile `.env` can override unit flags: a fresh child mismatch is a
failed deployment, not a reason to edit the profile automatically.

<!-- activation -->
```bash
set -euo pipefail
: "${P:?}" "${U:?}" "${RUN_PARENT:?}" "${TIP:?}" "${REVIEWED_STATUS?}"
: "${EXPECTED_PRE:?}" "${PROTECTED_DROPINS?}"
read -ra protected <<< "$PROTECTED_DROPINS"
for rel in "${protected[@]}"; do
  [[ "$rel" =~ ^[A-Za-z0-9@_.-]+\.service\.d/[A-Za-z0-9@_.-]+\.conf$ && "$rel" != */observe-bundle.conf ]]
  [[ -f "$U/$rel" && ! -L "$U/$rel" ]]
done
HERMES=${HERMES:-0}
[[ "$HERMES" == 0 || "$HERMES" == 1 ]]
HERMES_UNIT=${HERMES_UNIT:-hermes-gateway}
[[ "$HERMES_UNIT" =~ ^hermes-gateway(-[A-Za-z0-9_.-]+)?$ ]]
[[ "$TIP" =~ ^[0-9a-f]{40}$ && "$EXPECTED_PRE" =~ ^[0-9a-f]{40}$ ]]
[[ "$(git -C "$P" rev-parse HEAD)" == "$EXPECTED_PRE" ]]
[[ "$(git -C "$P" status --porcelain)" == "$REVIEWED_STATUS" ]]
git -C "$P" merge-base --is-ancestor "$EXPECTED_PRE" "$TIP"
units=(azimuth-sol-monitor azimuth azimuth-sol-shadow)
flags=(DLMM_SHADOW_EXITS DLMM_REJECT_IDENTITY DLMM_BRACKET_REJECTS)
if [[ "$HERMES" == 1 ]]; then units+=("$HERMES_UNIT"); flags+=(DLMM_REJECT_IDENTITY); fi
for unit in "${units[@]}"; do
  file="$U/$unit.service.d/observe-bundle.conf"
  [[ ! -e "$file" && ! -L "$file" ]]
done
umask 077
mkdir -p "$RUN_PARENT"
RUN=$(mktemp -d "$RUN_PARENT/observe.XXXXXXXX")
printf '%s\n' "$RUN"
printf '%s\n' "$EXPECTED_PRE" > "$RUN/pre"
printf '%s\n' "$HERMES" > "$RUN/hermes"
printf '%s\n' "$HERMES_UNIT" > "$RUN/hermes-unit"
printf '%s\n' activating > "$RUN/phase"
for rel in "${protected[@]}"; do sha256sum "$U/$rel"; done > "$RUN/protected-dropins.sha256"
git -C "$P" diff --binary > "$RUN/before.patch"
git -C "$P" diff --cached --binary > "$RUN/before-index.patch"
git -C "$P" merge --ff-only "$TIP"
[[ "$(git -C "$P" rev-parse HEAD)" == "$TIP" ]]
git -C "$P" rev-parse HEAD > "$RUN/tip"
git -C "$P" log --format='%H %s' "$EXPECTED_PRE..$TIP" > "$RUN/integrated-commits"
idle="$P/assets/skill/scripts/dlmm_observer_idle.py"
# Catch an occupied unit before changing any drop-in. Recheck just before restart.
python3 "$idle" --unit azimuth --timeout 120 > "$RUN/azimuth-idle-preflight.json"
if [[ "$HERMES" == 1 ]]; then
  python3 "$idle" --unit "$HERMES_UNIT" --timeout 120 > "$RUN/hermes-idle-preflight.json"
fi
for i in "${!units[@]}"; do
  unit=${units[$i]}; file="$U/$unit.service.d/observe-bundle.conf"
  mkdir -p "$(dirname "$file")"
  printf '[Service]\nEnvironment=%s=1\n' "${flags[$i]}" > "$RUN/$unit.conf"
  (set -o noclobber; cat "$RUN/$unit.conf" > "$file")
done
systemctl --user daemon-reload
gate="$P/assets/skill/scripts/dlmm_observer_gate.py"
T0=$(date +%s.%N); printf '%s\n' "$T0" > "$RUN/restart"
systemctl --user restart azimuth-sol-monitor
python3 "$gate" --unit azimuth-sol-monitor --component monitor --expected 1 --since "$T0" --timeout 180 > "$RUN/monitor-proof.json"
T2=$(date +%s.%N)
systemctl --user start azimuth-sol-shadow
python3 "$gate" --unit azimuth-sol-shadow --component shadow --expected 1 --since "$T2" --timeout 900 > "$RUN/shadow-proof.json"
[[ ! -s "$RUN/protected-dropins.sha256" ]] || sha256sum -c "$RUN/protected-dropins.sha256"
python3 "$idle" --unit azimuth --timeout 120 > "$RUN/azimuth-idle-restart.json"
T1=$(date +%s.%N); printf '%s\n' "$T1" > "$RUN/pipeline-since"
systemctl --user restart azimuth
if [[ "$HERMES" == 1 ]]; then
  python3 "$idle" --unit "$HERMES_UNIT" --timeout 120 > "$RUN/hermes-idle-restart.json"
  T3=$(date +%s.%N); printf '%s\n' "$T3" > "$RUN/hermes-since"
  systemctl --user restart "$HERMES_UNIT"
fi
[[ ! -s "$RUN/protected-dropins.sha256" ]] || sha256sum -c "$RUN/protected-dropins.sha256"
printf '%s\n' activated > "$RUN/phase"
printf '%s\n' 'Monitor/shadow verified. Pipeline evidence PENDING; use the verification-only block.'
```

`OBSERVER_TICK` comes on stderr from the actual monitor/shadow Python process
after successful completion (including normal `SystemExit(0)`), with PID,
start/end times and only three whitelisted flags. Nonzero exits and exceptions
produce no success record. Override/report/settlement commands do not qualify
as regular monitor ticks. Journal metadata may identify the parent that opened
the stream; the payload identifies the child. OFF also emits this diagnostic.

The pipeline gate checks `/proc` for a fresh Python `dlmm_pipeline.py` descendant
of the unit's MainPID, verifying its start time, ancestry and own environment.
MainPID is only the ancestry root; its environment is never accepted as proof.
The pipeline's output is unchanged (the daemon uses its final line in reports).
The proof retains only PID, parent, start time and `DLMM_REJECT_IDENTITY`, never
batch arguments, secrets or the full environment. This proves the flag in an
actual running child, not that an entry succeeded or a reject row was persisted.

A failed restart, failed idle check, or missing/mismatched monitor/shadow tick
stops activation. Keep the run directory and report the partial state. `is-active`,
parent environment and first-trigger rows are not substitutes for child evidence.
An old shadow invocation keeps its previous flags until it finishes; its next
invocation must satisfy the gate.

Pipeline activity can be sparse. It is **not** a prerequisite for activating the
remaining units: monitor and shadow are verified first, then azimuth and optional
Hermes restart once. Their pipeline flags remain PENDING until the block below
observes real children. Retry **only that block**, with the saved original
`pipeline-since` / `hermes-since` timestamps. Timeout does not request rollback,
restart, a second activation, or a trade to manufacture evidence. A flag mismatch
or other read error is also unverified: inspect the saved error before retrying.

The idle helper reads each unit's ControlGroup and its `cgroup.procs`, including
nested groups, then checks member command lines for `dlmm_pipeline.py` or
`dlmm_executor.js`. Busy work is polled for at most 120 seconds; an unreadable,
missing or oversized source fails closed. It requires a one-second quiet interval
and is called again immediately before each azimuth/Hermes restart. It does not
signal, kill, freeze or alter the unit. This is an observed idle check, **not an
atomic admission lock**: a new dispatch can race the final check. Keep other
operators from initiating deploys during this short maintenance sequence; this
runbook does not claim to eliminate that residual scheduling race.

<!-- verification -->
```bash
set -euo pipefail
: "${P:?}" "${RUN:?}"
phase=$(cat "$RUN/phase")
case "$phase" in
  activated) expected=1; prefix= ;;
  rolled-back) expected=0; prefix=rollback- ;;
  *) echo 'Activation/rollback did not finish; review the saved partial state first.' >&2; exit 1 ;;
esac
HERMES=$(cat "$RUN/hermes")
[[ "$HERMES" == 0 || "$HERMES" == 1 ]]
HERMES_UNIT=$(cat "$RUN/hermes-unit")
[[ "$HERMES_UNIT" =~ ^hermes-gateway(-[A-Za-z0-9_.-]+)?$ ]]
units=(azimuth); stamps=(pipeline-since)
if [[ "$HERMES" == 1 ]]; then units+=("$HERMES_UNIT"); stamps+=(hermes-since); fi
attempt=$(mktemp -d "$RUN/verify-${prefix}XXXXXXXX")
gate="$P/assets/skill/scripts/dlmm_observer_gate.py"
pending=0
for i in "${!units[@]}"; do
  unit=${units[$i]}; since=$(cat "$RUN/${prefix}${stamps[$i]}")
  if python3 "$gate" --unit "$unit" --component pipeline --expected "$expected" --since "$since" --timeout 900 > "$attempt/$unit.output" 2> "$attempt/$unit.error"; then
    mv "$attempt/$unit.output" "$attempt/$unit-proof.json"
  else
    pending=1
    printf '%s\n' "$unit: PENDING_NOT_VERIFIED; inspect $attempt/$unit.error. Retry this block only."
  fi
done
if [[ "$pending" == 0 ]]; then
  printf '%s\n' "VERIFIED expected=$expected" > "$attempt/status"
else
  printf '%s\n' PENDING_NOT_VERIFIED > "$attempt/status"
fi
cat "$attempt/status"
```

The verification block returns normally even when evidence is pending; its
explicit status is authoritative, not its shell exit code. Each attempt retains
its own proofs/errors. Only VERIFIED confirms the requested child flags; it is
still not proof of complete observation coverage or profitable trades.

Rollback uses the saved run directory. It removes only exact files this run wrote,
after checking all of them first. A changed file or symlink stops for review.
There is no reset, automatic revert list, journal deletion or marker cleanup.
The integration commit list is evidence, not an approved list of commits to revert.

<!-- rollback -->
```bash
set -euo pipefail
: "${P:?}" "${U:?}" "${RUN:?}"
HERMES=$(cat "$RUN/hermes")
[[ "$HERMES" == 0 || "$HERMES" == 1 ]]
HERMES_UNIT=$(cat "$RUN/hermes-unit")
[[ "$HERMES_UNIT" =~ ^hermes-gateway(-[A-Za-z0-9_.-]+)?$ ]]
units=(azimuth-sol-monitor azimuth azimuth-sol-shadow)
if [[ "$HERMES" == 1 ]]; then units+=("$HERMES_UNIT"); fi
for unit in "${units[@]}"; do
  file="$U/$unit.service.d/observe-bundle.conf"
  [[ -f "$file" && ! -L "$file" ]]
  cmp -- "$RUN/$unit.conf" "$file"
done
[[ ! -s "$RUN/protected-dropins.sha256" ]] || sha256sum -c "$RUN/protected-dropins.sha256"
idle="$P/assets/skill/scripts/dlmm_observer_idle.py"
python3 "$idle" --unit azimuth --timeout 120 > "$RUN/rollback-azimuth-idle-preflight.json"
if [[ "$HERMES" == 1 ]]; then
  python3 "$idle" --unit "$HERMES_UNIT" --timeout 120 > "$RUN/rollback-hermes-idle-preflight.json"
fi
printf '%s\n' rolling-back > "$RUN/phase"
for unit in "${units[@]}"; do rm -- "$U/$unit.service.d/observe-bundle.conf"; done
systemctl --user daemon-reload
gate="$P/assets/skill/scripts/dlmm_observer_gate.py"
T0=$(date +%s.%N)
systemctl --user restart azimuth-sol-monitor
python3 "$gate" --unit azimuth-sol-monitor --component monitor --expected 0 --since "$T0" --timeout 180 > "$RUN/rollback-monitor-proof.json"
T2=$(date +%s.%N)
systemctl --user start azimuth-sol-shadow
python3 "$gate" --unit azimuth-sol-shadow --component shadow --expected 0 --since "$T2" --timeout 900 > "$RUN/rollback-shadow-proof.json"
[[ ! -s "$RUN/protected-dropins.sha256" ]] || sha256sum -c "$RUN/protected-dropins.sha256"
python3 "$idle" --unit azimuth --timeout 120 > "$RUN/rollback-azimuth-idle-restart.json"
T1=$(date +%s.%N); printf '%s\n' "$T1" > "$RUN/rollback-pipeline-since"
systemctl --user restart azimuth
if [[ "$HERMES" == 1 ]]; then
  python3 "$idle" --unit "$HERMES_UNIT" --timeout 120 > "$RUN/rollback-hermes-idle-restart.json"
  T3=$(date +%s.%N); printf '%s\n' "$T3" > "$RUN/rollback-hermes-since"
  systemctl --user restart "$HERMES_UNIT"
fi
[[ ! -s "$RUN/protected-dropins.sha256" ]] || sha256sum -c "$RUN/protected-dropins.sha256"
printf '%s\n' rolled-back > "$RUN/phase"
printf '%s\n' 'Monitor/shadow confirm OFF. Pipeline evidence PENDING; use the verification-only block.'
```

If rollback stops, do not claim every observer is OFF. An old oneshot can retain
its original flags until it finishes. If code must be removed, prepare and review
a separate revert from the then-current HEAD, test it and obtain approval.

## Evidence and limits

- Shadow-exit and close-bin observation I/O runs after all monitor positions have
  completed their risk/close handling. A queue holds at most 256 observations;
  reaching this limit emits `TICK_OBSERVATION_LIMIT` and coverage may be missing.
  Timestamps retain the decision/mark time, not the later flush time. Fee pace
  updates remain in risk handling because decisions use them.
- Markers are never pruned in a tick. Dedup is per position/variant across restarts;
  at most two markers per position, with no lifetime storage cap. Do not delete
  markers or rotate journals automatically. A legacy journal without matching
  markers can gain duplicate first-trigger rows; dedup analysis by position and
  variant across the legacy/new records, never count them as independent evidence.
- Marker creation followed by a failed write/crash can leave no row. Markers are
  claims, not successful observations. Missing evidence remains unknown; no proof
  of profit or completed brackets follows from a healthy tick alone.
- Three research writers serialize cooperating appends under nonblocking locks.
  Projected size cannot exceed 64 MiB. Short writes fail explicitly and their
  partial tail is retained; further appends refuse that tail. No existing data is
  truncated. Research readers retain valid prefix rows, count corruption and check
  the deadline even while draining oversized lines. Files already above the cap
  require separate offline reconciliation. Lock, cap and write errors are explicit
  diagnostics, including `append:refused` in sampler results.
- Terminal reuse validates the entire snapshot (identity, native counters,
  contiguous bins, anchor, coverage and time). Read budgets remain unchanged.
  ON can use otherwise idle sampler slots, so observation volume can increase.
- Regular filesystem I/O can wait on storage despite O_NONBLOCK. Moving writes
  after risk handling protects decisions within that tick, not the start time of
  the next tick. No live latency or prospective strategy profit is proved here.
