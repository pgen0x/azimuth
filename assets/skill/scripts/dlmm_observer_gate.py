#!/usr/bin/env python3
"""Read-only gate: fresh monitor tick / shadow run, or actual fresh pipeline child.

This never invokes the pipeline, monitor or wallet. No matching completed child
within the operator's deadline is failure, even when systemd says 'active'.
"""
import argparse
import json
import math
import os
import re
from pathlib import Path
import subprocess
import time

FLAGS = {'monitor': 'DLMM_SHADOW_EXITS', 'pipeline': 'DLMM_REJECT_IDENTITY',
         'shadow': 'DLMM_BRACKET_REJECTS'}


def pipeline_child(proc, parent, expected, since, now):
    """Read only whitelisted flag values from an actual fresh descendant.

    MainPID is an ancestry root, never the environment being verified. Bound the
    process census, each file read and ancestry walk. Vanished/unreadable children
    are no evidence. Never return argv, other environment keys or their values.
    """
    def read(path, limit):
        with path.open('rb') as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError('proc read cap')
        return data
    boot = next(int(line.split()[1]) for line in read(proc / 'stat', 65536).splitlines()
                if line.startswith(b'btime '))
    processes = {}
    for count, directory in enumerate(proc.iterdir()):
        if count >= 10000:
            raise RuntimeError('process census cap')
        if not directory.name.isdigit():
            continue
        try:
            fields = read(directory / 'stat', 4096).rsplit(b')', 1)[1].split()
            processes[int(directory.name)] = (int(fields[1]), boot + int(fields[19]) / os.sysconf('SC_CLK_TCK'))
        except (OSError, ValueError, IndexError):
            continue
    for pid, (ppid, started) in processes.items():
        if pid == parent or not since <= started <= now + 2:
            continue
        ancestor = ppid
        for _ in range(128):
            if ancestor in (0, 1, parent):
                break
            ancestor = processes.get(ancestor, (0, 0))[0]
        if ancestor != parent:
            continue
        directory = proc / str(pid)
        try:
            # --from-batch can be large. Only the leading interpreter/script argv
            # is needed, and none of it is retained in the proof.
            with (directory / 'cmdline').open('rb') as stream:
                argv = stream.read(4096).split(b'\0')
            if (not re.fullmatch(r'python(?:[23](?:\.\d+)?)?', Path(os.fsdecode(argv[0])).name)
                    or not any(Path(os.fsdecode(arg)).name == 'dlmm_pipeline.py' for arg in argv[1:5])):
                continue
            env = read(directory / 'environ', 65536).split(b'\0')
            values = [item.split(b'=', 1)[1] for item in env if item.startswith(b'DLMM_REJECT_IDENTITY=')]
            value = values == [b'1']
            # Reject PID reuse/races between identity and environment reads.
            fields = read(directory / 'stat', 4096).rsplit(b')', 1)[1].split()
            if (int(fields[1]), boot + int(fields[19]) / os.sysconf('SC_CLK_TCK')) != (ppid, started):
                continue
            if len(values) > 1 or value != expected:
                raise RuntimeError('fresh child flag mismatch: DLMM_REJECT_IDENTITY')
            return dict(component='pipeline', pid=pid, parent=parent, started_at=started,
                        source='proc_child', flags={'DLMM_REJECT_IDENTITY': value})
        except (OSError, ValueError, IndexError):
            continue
    return None


def match_tick(line, component, expected, since, now):
    try:
        entry = json.loads(line)
        message = entry['MESSAGE']
        if not message.startswith('OBSERVER_TICK '):
            return None
        row = json.loads(message[len('OBSERVER_TICK '):])
        times = [row['started_at'], row['completed_at']]
        if not all(type(t) in (float, int) and math.isfinite(t) for t in times):
            return None
        if (row['component'] != component or row['regular_tick'] is not True
                or type(row['pid']) is not int or row['pid'] <= 0
                or not since <= times[0] <= times[1] <= now + 2
                or not since <= int(entry['__REALTIME_TIMESTAMP']) / 1e6 <= now + 2):
            return None
        value = row['flags'].get(FLAGS[component])
        if type(value) is not bool or value != expected:
            raise RuntimeError('fresh child flag mismatch: ' + FLAGS[component])
        return row
    except (ValueError, TypeError, KeyError, AttributeError):
        return None


def wait_for_tick(unit, component, expected, since, timeout, proc=Path('/proc')):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if component == 'pipeline':
            result = subprocess.run(['systemctl', '--user', 'show', '-p', 'MainPID', '--value', unit],
                                    capture_output=True, text=True, check=True, timeout=min(5, end - time.monotonic()))
            parent = int(result.stdout.strip())
            row = pipeline_child(proc, parent, expected, since, time.time()) if parent > 1 else None
            if row is not None:
                return row
        else:
            result = subprocess.run(
                ['journalctl', '--user', '-u', unit, '--since', '@' + str(since),
                 '-n', '256', '--no-pager', '-o', 'json'],
                capture_output=True, text=True, check=True, timeout=min(5, end - time.monotonic()))
            for line in reversed(result.stdout.splitlines()):
                row = match_tick(line, component, expected, since, time.time())
                if row is not None:
                    return row
        time.sleep(max(0, min(1, end - time.monotonic())))
    raise RuntimeError('no fresh completed ' + component + ' child before deadline')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit', required=True)
    parser.add_argument('--component', choices=FLAGS, required=True)
    parser.add_argument('--expected', choices=['0', '1'], required=True)
    parser.add_argument('--since', type=float, required=True)
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('--proc-root', type=Path, default=Path('/proc'), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not math.isfinite(args.since) or args.since <= 0 or not 0 < args.timeout <= 900:
        parser.error('positive timestamp and timeout <= 900 required')
    print(json.dumps(wait_for_tick(args.unit, args.component, args.expected == '1', args.since, args.timeout, args.proc_root)))


if __name__ == '__main__':
    main()
