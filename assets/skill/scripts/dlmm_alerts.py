"""Durable event delivery outside the position risk and settlement paths."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid


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


def flush_one(profile):
    directory = Path(profile) / 'memories/dlmm_alert_outbox'
    if not directory.is_dir():
        return
    with open(directory / '.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        for path in sorted(directory.glob('*.json')):
            try:
                item = json.loads(path.read_text())
                if not isinstance(item.get('target'), str) or not item['target'] or not isinstance(item.get('text'), str):
                    continue
                with tempfile.NamedTemporaryFile('w', suffix='.txt') as body:
                    body.write(item['text'])
                    body.flush()
                    result = subprocess.run(['hermes', 'send', '-t', item['target'], '-f', body.name, '-q'],
                                            timeout=30, capture_output=True)
                if result.returncode == 0:
                    path.unlink()
                return
            except (OSError, ValueError, subprocess.TimeoutExpired):
                # Retain an unacknowledged delivery across process restarts.
                return


if __name__ == '__main__':
    if os.environ.get('DLMM_ALERT_TARGET', 'telegram'):
        flush_one(Path(os.path.abspath(__file__)).parents[3])
