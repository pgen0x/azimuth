"""Durable event delivery outside the position risk and settlement paths.

Transport: every send names the Hermes profile (`hermes -p <name> send`). Bare
`hermes send` reads the DEFAULT Hermes home, which on a profile-based install has
no messaging target, so every alert failed silently. The name is HERMES_PROFILE
when set, else the profile directory's basename when it sits in a `profiles/`
directory (~/.hermes/profiles/<name>); a profile outside one is the default home
and gets no flag. `hermes_send_argv` is the one place this is decided; the daily
card (dlmm_stats.py) and the Robinhood monitor use it too.

Outbox (memories/dlmm_alert_outbox/, one JSON file per message):
- one successful send per flush, oldest first, but a failing item never blocks
  the queue: it is retried with its own backoff (attempts and next_attempt_at
  are kept in the item) and the flush moves on to the next one;
- every failed send is logged to stderr with the return code;
- an item older than ARCHIVE_AFTER_S is moved to archive/ UNSENT and logged, so a
  backlog left by a broken transport never floods the chat once it is fixed;
- an unreadable or malformed item is archived too, instead of sitting forever.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

ARCHIVE_AFTER_S = 24 * 3600
MAX_SENDS_PER_FLUSH = 3
BACKOFF_BASE_S = 60
BACKOFF_MAX_S = 3600
PROFILE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')


def hermes_profile(profile, env=None):
    """The Hermes profile name for `hermes -p`, or None for the default home."""
    env = os.environ if env is None else env
    name = (env.get('HERMES_PROFILE') or '').strip()
    if name:
        if PROFILE_NAME.match(name):
            return name
        print(f'dlmm_alerts: ignoring invalid HERMES_PROFILE {name[:40]!r}', file=sys.stderr)
    path = Path(os.path.abspath(str(profile)))  # never resolve: the scripts dir is a symlink into the repo
    if path.parent.name == 'profiles' and PROFILE_NAME.match(path.name):
        return path.name
    return None


def hermes_send_argv(profile, env=None):
    """`hermes [-p <name>] send` for this profile; callers append the send arguments."""
    name = hermes_profile(profile, env)
    return ['hermes'] + (['-p', name] if name else []) + ['send']


def enqueue(profile, target, text):
    if not target:
        return
    directory = Path(profile) / 'memories/dlmm_alert_outbox'
    directory.mkdir(parents=True, exist_ok=True)
    name = f'{time.time_ns():020d}-{uuid.uuid4().hex}.json'
    temporary = directory / (name + '.tmp')
    with open(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as out:
        json.dump({'target': target, 'text': text}, out)
        out.flush()
        os.fsync(out.fileno())
    temporary.replace(directory / name)


def _queued_at(path):
    """Seconds since the epoch from the time_ns file-name prefix, else the mtime."""
    head = path.name.split('-', 1)[0]
    if head.isdigit() and len(head) >= 19:
        return int(head) / 1e9
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _rewrite(path, item):
    temporary = path.with_name(path.name + '.tmp')
    with open(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as out:
        json.dump(item, out)
        out.flush()
        os.fsync(out.fileno())
    temporary.replace(path)


def _archive(path, why):
    archive = path.parent / 'archive'
    archive.mkdir(exist_ok=True)
    path.replace(archive / path.name)
    print(f'dlmm_alerts: archived {path.name} unsent ({why})', file=sys.stderr)


def _send(profile, item, run):
    with tempfile.NamedTemporaryFile('w', suffix='.txt') as body:
        body.write(item['text'])
        body.flush()
        return run(hermes_send_argv(profile) + ['-t', item['target'], '-f', body.name, '-q'],
                   timeout=30, capture_output=True)


def flush_one(profile, now=None, run=None):
    """Archive stale items, then deliver at most one message (trying at most
    MAX_SENDS_PER_FLUSH due items). Returns the number delivered (0 or 1)."""
    run = run or subprocess.run
    directory = Path(profile) / 'memories/dlmm_alert_outbox'
    if not directory.is_dir():
        return 0
    with open(directory / '.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        now = time.time() if now is None else now
        due = []
        for path in sorted(directory.glob('*.json')):
            try:
                if now - _queued_at(path) > ARCHIVE_AFTER_S:
                    _archive(path, f'older than {ARCHIVE_AFTER_S // 3600}h')
                    continue
                item = json.loads(path.read_text())
                if (not isinstance(item, dict) or not isinstance(item.get('target'), str) or not item['target']
                        or not isinstance(item.get('text'), str)):
                    _archive(path, 'malformed item')
                    continue
            except ValueError:
                _archive(path, 'unreadable item')
                continue
            except OSError as e:
                print(f'dlmm_alerts: cannot read {path.name}: {e.__class__.__name__}', file=sys.stderr)
                continue
            next_at = item.get('next_attempt_at')
            if type(next_at) in (int, float) and next_at > now:
                continue
            due.append((path, item))
        for path, item in due[:MAX_SENDS_PER_FLUSH]:
            try:
                result = _send(profile, item, run)
                code, err = result.returncode, (result.stderr or b'')
            except subprocess.TimeoutExpired:
                code, err = 'timeout', b''
            except OSError as e:
                code, err = e.__class__.__name__, b''
            if code == 0:
                path.unlink()
                return 1
            attempts = int(item.get('attempts') or 0) + 1
            item.update(attempts=attempts, last_error=str(code),
                        next_attempt_at=now + min(BACKOFF_BASE_S * 2 ** (attempts - 1), BACKOFF_MAX_S))
            if isinstance(err, str):
                err = err.encode()
            detail = err.decode('utf-8', 'replace').strip().splitlines()[-1][:200] if err.strip() else ''
            print(f'dlmm_alerts: SEND FAILED {path.name} (attempt {attempts}, exit {code})'
                  + (f': {detail}' if detail else ''), file=sys.stderr)
            try:
                _rewrite(path, item)
            except OSError:
                pass  # retried on the next flush without backoff; never drop it
        return 0


if __name__ == '__main__':
    if os.environ.get('DLMM_ALERT_TARGET', 'telegram'):
        flush_one(Path(os.path.abspath(__file__)).parents[3])
