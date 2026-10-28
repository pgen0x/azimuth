# Dashboard deployment and rollback

This is an operator runbook, not part of the collector. Run it only after the user
approves the reviewed candidate. The fix task does not install a binary, alter a
unit, or restart anything. Keep the same shell for the following steps. Use the
full immutable commit from the accepted review; a branch name is not a pin.

Prepare and validate, without touching the installed binary:

```bash
set -euo pipefail
: "${DASHBOARD_REVIEWED_SHA:?Set the full 40-character commit from the accepted review}"
[[ "$DASHBOARD_REVIEWED_SHA" =~ ^[0-9a-f]{40}$ ]]
repo=$(git rev-parse --show-toplevel)
test "$(git -C "$repo" rev-parse "$DASHBOARD_REVIEWED_SHA^{commit}")" = "$DASHBOARD_REVIEWED_SHA"
mkdir -p "$HOME/.local/state/azimuth" "$HOME/.local/bin"
run_dir=$(mktemp -d "$HOME/.local/state/azimuth/dashboard-deploy.XXXXXXXX")
chmod 700 "$run_dir"
git -C "$repo" worktree add --detach "$run_dir/checkout" "$DASHBOARD_REVIEWED_SHA"
test -z "$(git -C "$run_dir/checkout" status --porcelain)"
export GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local GOTELEMETRY=off
(cd "$run_dir/checkout" && go test -count=1 ./... && go vet ./...)
binary="$HOME/.local/bin/azimuth-dashboard"
candidate=$(mktemp "${binary}.candidate.XXXXXXXX")
(cd "$run_dir/checkout" && go build -buildvcs=true -o "$candidate" ./cmd/dashboard)
go version -m "$candidate" > "$run_dir/candidate.build"
grep -Fq "vcs.revision=$DASHBOARD_REVIEWED_SHA" "$run_dir/candidate.build"
grep -Fq 'vcs.modified=false' "$run_dir/candidate.build"
test -z "$(git -C "$run_dir/checkout" status --porcelain)"
chmod 755 "$candidate"
test -f "$binary" && test ! -L "$binary"
sha256sum "$candidate" > "$run_dir/candidate.sha256"
sha256sum "$binary" > "$run_dir/installed-before.sha256"
unit=azimuth-dashboard.service
dropin="$HOME/.config/systemd/user/azimuth-dashboard.service.d/dashboard-since.conf"
printf 'unchanged\n' > "$run_dir/dropin-action"
systemctl --user cat "$unit" > "$run_dir/unit-before.txt"
systemctl --user show "$unit" -p FragmentPath -p DropInPaths -p ExecStart > "$run_dir/unit-properties-before.txt"
```

The offline dependency cache must already contain the build dependencies. A
failure stops preparation. Inspect `unit-before.txt`: this runbook targets the
dashboard unit, never a trading or Hermes unit. Preserve its profile, state,
listen address and Redis settings. Without an optional cutover change, leave
every unit/drop-in byte untouched.

The activation block below is deliberately pure file handling until the later
restart step. It creates a unique backup, verifies both hashes and atomically
renames the candidate on the installed binary's filesystem. Never move the old
binary out of service before the candidate is ready.

```bash
# BEGIN FILE ACTIVATION (also rehearsed with synthetic files in tests)
test ! -e "$run_dir/previous.binary"
test -f "$candidate" && test ! -L "$candidate"
sha256sum -c "$run_dir/installed-before.sha256"
sha256sum -c "$run_dir/candidate.sha256"
(set -o noclobber; cat "$binary" > "$run_dir/previous.binary")
chmod --reference="$binary" "$run_dir/previous.binary"
cmp "$binary" "$run_dir/previous.binary"
sha256sum "$run_dir/previous.binary" > "$run_dir/previous.sha256"
candidate_hash=$(sha256sum "$candidate" | cut -d ' ' -f 1)
printf '%s  %s\n' "$candidate_hash" "$binary" > "$run_dir/activated.sha256"
mv -T "$candidate" "$binary"
test "$(sha256sum "$binary" | cut -d ' ' -f 1)" = "$candidate_hash"
# END FILE ACTIVATION
```

Optional `-since` override, **only for the stock unit** whose ExecStart is
`%h/.local/bin/azimuth-dashboard -env-file REPO/.env`. For a customized ExecStart,
keep it unchanged and prepare a separately reviewed full command; this optional
block must not discard existing flags. Set `DASHBOARD_SINCE` to positive Unix
seconds. This owns only `dashboard-since.conf`; other drop-ins stay in place.

```bash
dropin="$HOME/.config/systemd/user/azimuth-dashboard.service.d/dashboard-since.conf"
printf 'unchanged\n' > "$run_dir/dropin-action"
if [ -n "${DASHBOARD_SINCE:-}" ]; then
  [[ "$DASHBOARD_SINCE" =~ ^[1-9][0-9]*$ ]]
  python3 - "$run_dir/unit-properties-before.txt" "$binary" "$repo/.env" <<'PY'
import pathlib,re,sys
commands=re.findall(r'argv\[\]=(.*?) ;',pathlib.Path(sys.argv[1]).read_text())
assert commands==[sys.argv[2]+' -env-file '+sys.argv[3]], 'Requires the reviewed stock ExecStart; preserve custom arguments'
PY
  test ! -L "$dropin"
  if [ -f "$dropin" ]; then
    (set -o noclobber; cat "$dropin" > "$run_dir/previous.dropin")
    printf 'restore\n' > "$run_dir/dropin-action"
  else
    test ! -e "$dropin"
    printf 'remove\n' > "$run_dir/dropin-action"
  fi
  mkdir -p "$(dirname "$dropin")"
  staged_dropin=$(mktemp "${dropin}.XXXXXXXX")
  # Escape unit command quoting. Reject percent expansion/newlines in repo paths.
  [[ "$repo" != *'%'* && "$repo" != *$'\n'* && "$repo" != *'"'* && "$repo" != *'\'* ]]
  printf '[Service]\nExecStart=\nExecStart=%%h/.local/bin/azimuth-dashboard -env-file "%s/.env" -since %s\n' "$repo" "$DASHBOARD_SINCE" > "$staged_dropin"
  mv -T "$staged_dropin" "$dropin"
  sha256sum "$dropin" > "$run_dir/activated-dropin.sha256"
fi
```

Restart and verification are real gates. Preserve the activation time and verify
the running executable, not just a filename. Keep the URL loopback-only; change
the port only to match the reviewed unit. The probe waits at most 45 seconds for
a fresh snapshot from all three endpoints, rejects hidden collector/panel
errors, and confirms POST is refused. Partial economic evidence is allowed but
must remain visible in the response; it is not proof of profit.

```bash
activation_ts=$(date +%s)
printf '%s\n' "$activation_ts" > "$run_dir/activation-time"
systemctl --user daemon-reload
systemctl --user restart "$unit"
systemctl --user is-active --quiet "$unit"
pid=$(systemctl --user show -p MainPID --value "$unit")
[[ "$pid" =~ ^[1-9][0-9]*$ ]]
test "$(sha256sum "/proc/$pid/exe" | cut -d ' ' -f 1)" = "$candidate_hash"
go version -m "/proc/$pid/exe" | grep -F "vcs.revision=$DASHBOARD_REVIEWED_SHA"
python3 - "$activation_ts" <<'PY'
import json,sys,time,urllib.request,urllib.error
start=float(sys.argv[1]); deadline=time.monotonic()+45
def check_errors(value):
    if isinstance(value,dict):
        assert not value.get('collection_error'), 'collector/panel error'
        for item in value.values(): check_errors(item)
    elif isinstance(value,list):
        for item in value: check_errors(item)
base='http://127.0.0.1:8787'
while True:
    try:
        for route in ('overview','capital','live'):
            with urllib.request.urlopen(base+'/api/'+route,timeout=2) as response:
                body=response.read(8*1024*1024+1)
                assert len(body)<=8*1024*1024
                data=json.loads(body)
            assert data['collected_at']>=start, 'stale snapshot'
            check_errors(data)
        break
    except (OSError,ValueError,KeyError,AssertionError):
        if time.monotonic()>=deadline: raise
        time.sleep(1)
try:
    urllib.request.urlopen(urllib.request.Request(base+'/api/live',data=b'{}',method='POST'),timeout=2)
except urllib.error.HTTPError as error:
    assert error.code==405
else: raise AssertionError('POST was accepted')
print('Fresh overview/capital/live; no collection error; POST refused')
PY
git -C "$repo" worktree remove "$run_dir/checkout"
```

If activation or verification fails, keep the evidence in `run_dir` and use the
following rollback in the same shell (or restore `run_dir`, `binary`, `dropin`
and `unit` from the recorded deployment). Hash guards stop if someone has since
changed the installed binary/drop-in. Review that newer change instead of
overwriting it. The backup file is never consumed or overwritten.

```bash
# BEGIN FILE ROLLBACK (also rehearsed with synthetic files in tests)
sha256sum -c "$run_dir/activated.sha256"
sha256sum -c "$run_dir/previous.sha256"
restore=$(mktemp "${binary}.restore.XXXXXXXX")
cat "$run_dir/previous.binary" > "$restore"
chmod --reference="$run_dir/previous.binary" "$restore"
cmp "$restore" "$run_dir/previous.binary"
mv -T "$restore" "$binary"
cmp "$binary" "$run_dir/previous.binary"
# END FILE ROLLBACK
action=$(cat "$run_dir/dropin-action")
if [ "$action" != unchanged ]; then
  sha256sum -c "$run_dir/activated-dropin.sha256"
  if [ "$action" = restore ]; then
    restored_dropin=$(mktemp "${dropin}.XXXXXXXX")
    cat "$run_dir/previous.dropin" > "$restored_dropin"
    mv -T "$restored_dropin" "$dropin"
  elif [ "$action" = remove ]; then
    rm "$dropin"
  else
    echo 'Unknown saved drop-in action' >&2; exit 1
  fi
fi
systemctl --user daemon-reload
systemctl --user restart "$unit"
systemctl --user is-active --quiet "$unit"
pid=$(systemctl --user show -p MainPID --value "$unit")
cmp "/proc/$pid/exe" "$run_dir/previous.binary"
go version -m "/proc/$pid/exe"
```

Repeat the fresh GET/error and POST checks above after rollback, using its new
restart timestamp (an older binary may lack the two new endpoints; use the saved
API contract for that revision). No Git reset is involved. Keep the backup and
hash files until the user accepts the deployed version.
