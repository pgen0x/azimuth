---
name: ship
description: Build, vet, test, restart the azimuth user unit, and verify it came back clean. Run after changing daemon code.
disable-model-invocation: true
---

# Ship

Restarts the **live** daemon. It trades real funds, so every step below is
ordered: nothing restarts until the binary is proven good, and nothing is
declared done until the log says the new process is polling.

`systemctl --user`, never `sudo systemctl` — these are user units and the
system-level command reports "unit not found".

## Steps

Run from the repo root.

**1. Prove the code first.**

```bash
gofmt -l . | grep -v node_modules   # must print nothing
go vet ./...
go test ./internal/...
go build -o azimuth .
```

Any failure stops here. Do not restart a unit on a red build — the old binary
is still running and still working.

**2. Note what is live before touching it.**

```bash
systemctl --user is-active azimuth; systemctl --user is-enabled azimuth
```

Record both. `active` + `disabled` means it is running now but will not survive
a reboot; that is a pre-existing condition to report, not something to fix
mid-ship unless asked.

**3. Restart.**

```bash
systemctl --user restart azimuth
```

**4. Verify it actually came back.**

```bash
systemctl --user is-active azimuth
journalctl --user -u azimuth -n 40 --no-pager
```

The log must show the startup banner — `scanner started (interval=…, casual=…,
multiday=…, turnover=…, pulse=…)` — with the mode toggles you expect. A restart
that exits immediately leaves `is-active` reporting `failed` or `activating`;
treat either as a failed ship.

**5. Confirm a poll cycle, don't assume one.**

Wait one `POLL_INTERVAL`, then re-tail. A clean start with no subsequent cycle
line means the daemon is up but wedged on a fetch.

## Reporting

Say what actually happened. If tests failed, quote them and stop. If the unit
restarted but the log shows fetch errors, say the daemon is up **and** degraded
— do not round that to "shipped". Never report a deploy or a trade outcome that
you have not read in the journal yourself.

## If the restart fails

`journalctl --user -u azimuth -n 100 --no-pager` for the crash, then
`systemctl --user status azimuth`. Config errors surface at startup because
`internal/config` parses the environment before the scanner loop begins — a
missing or malformed variable kills the process in the first second. The
previous binary is gone at this point; rebuilding from `git stash` or the last
good commit is the rollback.
