#!/usr/bin/env python3
"""Read-only, bounded pre-restart check for DLMM work in a systemd unit cgroup."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import time


def read_bounded(path, cap=65536):
    with path.open('rb') as stream:
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise RuntimeError('process evidence exceeds read cap')
    return data


def busy_pids(group, proc, deadline):
    """Include nested cgroups; unreadable evidence is not an idle result."""
    pids = set()
    def failed(error):
        raise error
    for count, (directory, children, _) in enumerate(os.walk(group, onerror=failed)):
        if count >= 128 or time.monotonic() >= deadline:
            raise RuntimeError('cgroup scan budget exhausted')
        if any((Path(directory) / name).is_symlink() for name in children):
            raise RuntimeError('symlinked cgroup directory')
        values = read_bounded(Path(directory) / 'cgroup.procs').split()
        if any(not v.isdigit() or int(v) <= 0 for v in values):
            raise RuntimeError('invalid cgroup PID list')
        pids.update(int(v) for v in values)
        if len(pids) > 4096:
            raise RuntimeError('cgroup PID cap')
    busy = []
    for pid in sorted(pids):
        if time.monotonic() >= deadline:
            raise RuntimeError('process scan deadline')
        try:
            # Large --from-batch arguments are common; the script is near the
            # front. A truncated unrelated command cannot prove idle.
            with (proc / str(pid) / 'cmdline').open('rb') as stream:
                command = stream.read(65537)
            if b'dlmm_pipeline.py' in command or b'dlmm_executor.js' in command:
                busy.append(pid)
            elif len(command) > 65536:
                raise RuntimeError('unidentified oversized command')
        except FileNotFoundError:
            if (proc / str(pid)).exists():
                raise RuntimeError('process command unavailable')
            # Process exited after the cgroup snapshot. Recheck the group below.
    return busy, len(pids)


def wait_idle(unit, timeout, proc=Path('/proc'), cgroups=Path('/sys/fs/cgroup'), quiet=1):
    end = time.monotonic() + timeout
    quiet_since, last_group = None, None
    root = cgroups.resolve()
    while time.monotonic() < end:
        result = subprocess.run(
            ['systemctl', '--user', 'show', '--property=ControlGroup', '--value', '--', unit],
            capture_output=True, text=True, check=True, timeout=max(.001, min(5, end-time.monotonic())))
        name = result.stdout.strip()
        if not name.startswith('/') or name == '/' or '..' in Path(name).parts:
            raise RuntimeError('unit cgroup unavailable')
        group = root / name.lstrip('/')
        if group.resolve(strict=True) != group or not group.is_dir():
            raise RuntimeError('unit cgroup is not a real directory')
        busy, count = busy_pids(group, proc, end)
        now = time.monotonic()
        if now >= end:
            break
        if busy or name != last_group:
            quiet_since = None
        if not busy:
            if quiet_since is None:
                quiet_since = now
            elif now - quiet_since >= quiet:
                return dict(unit=unit, control_group=name, checked_at=time.time(),
                            quiet_seconds=now-quiet_since, pids_checked=count, status='idle')
        last_group = name
        time.sleep(max(0, min(.2, end-time.monotonic())))
    raise RuntimeError('unit did not become idle before deadline; do not restart')


# The scanner, or the Hermes gateway under its default or per-profile name (hermes-gateway-<profile>).
UNIT = re.compile(r'^(azimuth|hermes-gateway(-[A-Za-z0-9_.-]+)?)$')


def unit_name(value):
    if not UNIT.match(value):
        raise argparse.ArgumentTypeError('unit must be azimuth, hermes-gateway or hermes-gateway-<name>')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit', type=unit_name, required=True)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    if not 0 < args.timeout <= 900:
        parser.error('timeout must be positive and <= 900 seconds')
    try:
        print(json.dumps(wait_idle(args.unit, args.timeout)))
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, type(error).__name__ + ': ' + str(error) + '\n')


if __name__ == '__main__':
    main()
