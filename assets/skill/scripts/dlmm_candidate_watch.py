"""Record public live-batch identities for later read-only bin observations."""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time

WATCH_FILENAME = 'dlmm_candidate_watch.jsonl'
REJECT_FILENAME = 'dlmm_pipeline_rejects.jsonl'
REJECT_GATE = re.compile(r'[a-z0-9_]{1,40}\Z')
REJECT_NAME_MAX = 64                      # pair labels are short; longer input is truncated
REJECT_MAX_BYTES = 64 * 1024 * 1024       # journal cap: telemetry stops, the entry path never waits
MAX_WATCH_POOLS = 64
MODES = {'casual', 'multiday', 'turnover', 'pulse'}
SOL_MINT = 'So11111111111111111111111111111111111111112'
ADDRESS = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}\Z')


def record_pipeline_candidates(profile, cli):
    """Best-effort identity journal, before capacity/ranking gates; no RPC.

    Receipt time is not the scanner's observation time or an entry decision.
    Missing history remains unknown until a later native read actually occurs.
    Never wait for another writer or let telemetry reject a live entry.
    """
    if os.environ.get('DRY_RUN') == 'true' or cli.mode not in MODES:
        return 0
    try:
        if cli.from_batch:
            records = json.loads(cli.from_batch)
        elif cli.from_signal:
            records = [json.loads(cli.from_signal)]
        else:
            return 0
        if not isinstance(records, list):
            return 0
        stamp = time.time()
        if not math.isfinite(stamp) or stamp <= 0:
            return 0
        selected = {}
        for candidate in records:
            if not isinstance(candidate, dict):
                continue
            pool, mint = candidate.get('pool'), candidate.get('base_mint')
            if (not isinstance(pool, str) or not ADDRESS.fullmatch(pool)
                    or not isinstance(mint, str) or not ADDRESS.fullmatch(mint)
                    or mint == SOL_MINT or candidate.get('sol_is_x') is not False):
                continue
            if pool in selected:
                continue
            row = dict(ts=stamp, pool=pool, mode=cli.mode,
                       candidate=dict(base_mint=mint, sol_is_x=False))
            ident = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
            row.update(id='watch:' + ident, source='pipeline_batch_receipt')
            selected[pool] = row
            if len(selected) >= MAX_WATCH_POOLS:
                break
        if not selected:
            return 0
        memory = Path(profile) / 'memories'
        memory.mkdir(parents=True, exist_ok=True)
        # One bounded append under a nonblocking writer lock. No candidate
        # payload, credential, price, score or fabricated reject is retained.
        with (memory / WATCH_FILENAME).open('a', encoding='utf-8') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            stream.write(''.join(json.dumps(row, allow_nan=False) + '\n'
                                 for row in selected.values()))
        return len(selected)
    except (OSError, ValueError, TypeError, AttributeError):
        return 0


def record_pipeline_reject(profile, mode, gate, pool, mint, sol_is_x, name):
    """Opt-in identity for a pipeline `Skipping` line (DLMM_REJECT_IDENTITY=1).

    The human `Skipping <pair> - <reason>` line is printed unchanged by the caller,
    so every existing parser keeps matching. This adds the pool, mode and a stable
    gate id that the pair name cannot provide: a companion `REJECT_IDENTITY {json}`
    stdout line and one row in memories/dlmm_pipeline_rejects.jsonl. Best effort,
    with no lock wait: regular filesystem I/O can still wait on storage.
    Telemetry must not change an entry decision.
    """
    if os.environ.get('DLMM_REJECT_IDENTITY') != '1':
        return False
    try:
        if (mode not in MODES or not isinstance(gate, str) or not REJECT_GATE.fullmatch(gate)
                or not isinstance(pool, str) or not ADDRESS.fullmatch(pool)):
            return False
        stamp = time.time()
        if not math.isfinite(stamp) or stamp <= 0:
            return False
        row = dict(ts=stamp, pool=pool, mode=mode, gate=gate,
                   name=name[:REJECT_NAME_MAX] if isinstance(name, str) else None,
                   candidate=dict(base_mint=mint if isinstance(mint, str) and ADDRESS.fullmatch(mint) else None,
                                  sol_is_x=sol_is_x if isinstance(sol_is_x, bool) else None))
        row['id'] = 'reject:' + hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        print('REJECT_IDENTITY ' + json.dumps(row, sort_keys=True, allow_nan=False))
        if os.environ.get('DRY_RUN') == 'true':
            return True
        memory = Path(profile) / 'memories'
        memory.mkdir(parents=True, exist_ok=True)
        from dlmm_research_io import research_writer, research_write
        payload = (json.dumps(row, sort_keys=True, allow_nan=False) + '\n').encode()
        with research_writer(memory / REJECT_FILENAME, len(payload), REJECT_MAX_BYTES) as fd:
            research_write(fd, payload)
        return True
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print('REJECT_IDENTITY_ERROR ' + type(error).__name__)
        return False
