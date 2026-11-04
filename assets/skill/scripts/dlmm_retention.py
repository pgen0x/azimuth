#!/usr/bin/env python3
"""Archive old rows of the large append-only research journals.

Moves the leading run of rows older than ``--keep-days`` from
``memories/<name>.jsonl`` into ``memories/archive/<name>.<UTC stamp>.jsonl.gz``.
The split is byte-exact and prefix-only: archives (in name order) followed by
the live file reproduce the original bytes, so line hashes survive.

Dry run by default; ``--apply`` writes. Only files in POLICY can be archived:
each one's live readers look back at most ``floor_days`` (cited below), so the
live loops never miss a row they read. Full-history research readers go
through ``archived_rows`` / ``archived_bytes``.

``dlmm_nav.jsonl`` is deliberately NOT in POLICY: ``dlmm_accounting.report``
anchors on the FIRST NAV snapshot and the scoreboard/dashboard read the whole
series, so dropping its prefix would change live root-budget decisions.
"""
import argparse
import fcntl
import gzip
import json
import math
import os
import time
from pathlib import Path

DAY = 86400
# name -> (timestamp key(s), floor_days). floor = longest live lookback, rounded up:
# dlmm_bin_samples: dlmm_shadow samples a position only through mode horizon
#   (<= 86400s) + 600s grace.
# dlmm_candidate_bin_samples: dlmm_shadow bracket index <= 86400+3600+600s,
#   candidate paper <= 1800s.
# dlmm_candidate_fee_forecasts: shadow due index <= horizon (86400s), paper <= 900s,
#   executor reads only the tail (dlmm_entry_forecast.MAX_BYTES).
# dlmm_geometry_shadow_obs: no live reader (the monitor only appends); the
#   report reads full history through archived_rows.
POLICY = {
    'dlmm_bin_samples.jsonl': (('ts',), 2),
    'dlmm_candidate_bin_samples.jsonl': (('collected_at', 'ts'), 2),
    'dlmm_candidate_fee_forecasts.jsonl': (('recorded_at',), 2),
    'dlmm_geometry_shadow_obs.jsonl': (('ts',), 2),
}
DEFAULT_KEEP_DAYS = 14
GRACE_SECONDS = 1.0


def archives(path):
    """Archive files for ``path``, oldest first (UTC stamps sort lexically)."""
    path = Path(path)
    stem = path.name[:-len('.jsonl')] if path.name.endswith('.jsonl') else path.name
    folder = path.parent / 'archive'
    return sorted(folder.glob(stem + '.*.jsonl.gz')) if folder.is_dir() else []


def archived_bytes(path):
    """Original journal bytes: every archive, then the live file."""
    path = Path(path)
    parts = [gzip.decompress(p.read_bytes()) for p in archives(path)]
    if path.exists():
        parts.append(path.read_bytes())
    return b''.join(parts)


def archived_rows(path):
    """Rows from every archive, then the live file. Corruption stays visible."""
    path = Path(path)
    for source in archives(path) + ([path] if path.exists() else []):
        opener = gzip.open if source.suffix == '.gz' else open
        with opener(source, 'rt') as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)


def _stamp(line, keys):
    try:
        row = json.loads(line)
    except ValueError:
        return None
    if not isinstance(row, dict):
        return None
    for key in keys:
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            return value
    return None


def prefix_end(path, keys, cutoff):
    """Byte offset and row count of the leading complete rows stamped before cutoff.

    Stops at the first newer, unstamped, unparsable or unterminated line: the
    archive is always a prefix, never a filter.
    """
    end = rows = 0
    with open(path, 'rb') as stream:
        for line in stream:
            if not line.endswith(b'\n'):
                break
            if line.strip():
                stamp = _stamp(line, keys)
                if stamp is None or stamp >= cutoff:
                    break
                rows += 1
            end += len(line)
    return end, rows


def _copy(src, dst, start):
    src.seek(start)
    copied = 0
    while True:
        chunk = src.read(1 << 20)
        if not chunk:
            return copied
        dst.write(chunk)
        copied += len(chunk)


def archive_file(path, keys, cutoff, now, apply=False):
    path = Path(path)
    result = dict(file=path.name, cutoff=cutoff, archived_rows=0, archived_bytes=0,
                  size_before=path.stat().st_size if path.exists() else 0, applied=False)
    if not path.exists():
        result['status'] = 'missing'
        return result
    end, rows = prefix_end(path, keys, cutoff)
    result.update(archived_rows=rows, archived_bytes=end)
    if not apply or end == 0:
        result['status'] = 'planned' if end else 'nothing_to_archive'
        return result
    folder = path.parent / 'archive'
    folder.mkdir(mode=0o700, exist_ok=True)
    stem = path.name[:-len('.jsonl')]
    target = folder / f"{stem}.{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(now))}.jsonl.gz"
    if target.exists():
        raise FileExistsError(target)
    mode = path.stat().st_mode & 0o777
    with open(path, 'rb') as old:
        partial = target.with_name(target.name + '.partial')
        with open(partial, 'wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as gz:
            old.seek(0)
            remaining = end
            while remaining:
                chunk = old.read(min(remaining, 1 << 20))
                if not chunk:
                    raise IOError('journal shrank during archive')
                gz.write(chunk)
                remaining -= len(chunk)
        with gzip.open(partial, 'rb') as check:
            restored = 0
            while chunk := check.read(1 << 20):
                restored += len(chunk)
        if restored != end:
            raise IOError('archive verification failed')
        os.chmod(partial, mode)
        os.replace(partial, target)
        # Writers append by path. Copy the tail, swap, then keep draining the old
        # inode until it stops growing, so an append racing the swap is kept.
        fresh = path.with_name(path.name + '.retention')
        with open(fresh, 'wb') as out:
            copied = end + _copy(old, out, end)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(fresh, mode)
        os.replace(fresh, path)
        while True:
            time.sleep(GRACE_SECONDS)
            size = os.fstat(old.fileno()).st_size
            if size <= copied:
                break
            with open(path, 'ab') as out:
                copied += _copy(old, out, copied)
    result.update(status='archived', applied=True, archive=target.name,
                  size_after=path.stat().st_size)
    return result


def run(memory, keep_days, files, apply, now=None):
    now = time.time() if now is None else now
    memory = Path(memory)
    results = []
    # A dry run writes nothing, not even the lock file.
    lock_path = memory / '.retention.lock' if apply else os.devnull
    with open(lock_path, 'w') as lock:
        try:
            if apply:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return [dict(status='locked')]
        for name in files:
            if name not in POLICY:
                results.append(dict(file=name, status='refused_not_in_policy'))
                continue
            keys, floor_days = POLICY[name]
            if keep_days < floor_days:
                results.append(dict(file=name, status='refused_below_floor', floor_days=floor_days))
                continue
            results.append(archive_file(memory / name, keys, now - keep_days * DAY, now, apply))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--keep-days', type=float, default=DEFAULT_KEEP_DAYS)
    parser.add_argument('--file', action='append', dest='files',
                        help='journal name (repeatable); default: every POLICY file')
    parser.add_argument('--apply', action='store_true', help='write; default is a dry run')
    args = parser.parse_args(argv)
    results = run(args.profile / 'memories', args.keep_days, args.files or sorted(POLICY), args.apply)
    print(json.dumps(results, indent=2))
    return 1 if any(r.get('status', '').startswith('refused') or r.get('status') == 'locked'
                    for r in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
