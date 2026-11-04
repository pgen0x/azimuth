"""Parse the one pool record the AI passes to ``dlmm_pipeline.py --from-signal``.

The agent copies one element out of the webhook's ``payload`` array by hand.
Two copy slips repeatedly cost entry turns, some of which never reached the
pipeline at all:

* the element plus the array's closing bracket or separator, ``{...}]`` or
  ``{...},`` -> "Extra data"
* the element still wrapped in its array, ``[{...}]``

Both are unambiguous — there is exactly one record — so they are accepted.
Anything that could mean a different or a second record (two objects, a
multi-element array, trailing text) is still refused.
"""
import json
import os
import re
import time
from pathlib import Path

_STRAY_CLOSERS = re.compile(r"[\s\],]*")


class SignalRecordError(ValueError):
    pass


def parse_signal_record(text):
    """Return the single pool record dict in ``text`` or raise SignalRecordError."""
    if not isinstance(text, str):
        raise SignalRecordError("--from-signal is not valid JSON: not a string")
    body = text.strip()
    try:
        value, end = json.JSONDecoder().raw_decode(body)
    except ValueError as exc:
        raise SignalRecordError(f"--from-signal is not valid JSON: {exc}") from None
    rest = body[end:]
    if rest and not (isinstance(value, dict) and _STRAY_CLOSERS.fullmatch(rest)):
        # Report it the way json.loads would, so the message stays familiar.
        try:
            json.loads(body)
        except ValueError as exc:
            raise SignalRecordError(f"--from-signal is not valid JSON: {exc}") from None
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], dict):
            value = value[0]
        else:
            raise SignalRecordError("--from-signal got an array; pass ONE payload element (a single pool record)")
    if not isinstance(value, dict):
        raise SignalRecordError("--from-signal must be one JSON object (a single pool record)")
    return value


# --from-pool: the agent names the pool, the pipeline reads the record.
#
# Hand-copying a ~1.3 KB JSON object into a single-quoted shell argument was
# the dominant way an AI entry turn broke: copy slips (above), bash quoting
# (a symbol with an apostrophe ends the quote), Python-repr rewrites. The
# scanner already persists every Solana webhook signal BEFORE sending it — a
# ``stage: "prepared"`` row in its delivery journal whose ``signal.payload`` is
# the exact array the agent's prompt renders. So the agent only needs to pass
# the pool address, a base58 token that never needs quoting.
_POOL_ADDRESS = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")
# Dedup keeps a pool out of new batches for SEEN_TTL, so within this window
# the newest delivered record for (pool, mode) is the one this turn received.
DELIVERED_MAX_AGE_S = 1800
_TAIL_BYTES = 4 << 20


def delivery_journal_path(env=None):
    """Same resolution as the scanner's ``internal/webhook/delivery.go``."""
    env = os.environ if env is None else env
    return Path(env.get("SOLANA_DELIVERY_PATH")
                or Path.home() / ".local/state/azimuth/solana_deliveries.jsonl")


def _tail_lines(path, tail_bytes):
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        start = max(0, size - tail_bytes)
        f.seek(start)
        data = f.read()
    lines = data.split(b"\n")
    if start:
        lines = lines[1:]  # first line is a partial row
    return lines


def _payload_of(signal):
    if not isinstance(signal, dict):
        return None
    payload = signal.get("payload")
    if payload is None and isinstance(signal.get("payload_json"), str):
        try:
            payload = json.loads(signal["payload_json"])
        except ValueError:
            return None
    return payload if isinstance(payload, list) else None


def load_delivered_record(pool, mode, path=None, now=None,
                          max_age=DELIVERED_MAX_AGE_S, tail_bytes=_TAIL_BYTES):
    """Return the newest delivered signal record for ``pool`` in ``mode``.

    Only ``prepared`` rows younger than ``max_age`` count. Raises
    SignalRecordError with a message naming why nothing was found; the record
    itself is returned unmodified (the same dict --from-signal would parse).
    """
    pool = (pool or "").strip()
    if not _POOL_ADDRESS.fullmatch(pool):
        raise SignalRecordError(f"--from-pool is not a Solana pool address: {pool[:60]!r}")
    path = Path(path) if path else delivery_journal_path()
    now = time.time() if now is None else now
    try:
        lines = _tail_lines(path, tail_bytes)
    except OSError as exc:
        raise SignalRecordError(f"--from-pool: delivery journal unreadable ({path}): {exc.strerror or exc}") from None
    for raw in reversed(lines):
        if b'"prepared"' not in raw or pool.encode() not in raw:
            continue
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(row, dict) or row.get("stage") != "prepared":
            continue
        ts = row.get("observed_at")
        if not isinstance(ts, (int, float)):
            continue
        if ts > now:
            continue  # written after this turn started; not the record it received
        if now - ts > max_age:
            # Rows are appended in time order: everything older is stale too.
            break
        for rec in _payload_of(row.get("signal")) or ():
            if isinstance(rec, dict) and rec.get("pool") == pool and rec.get("mode") == mode:
                return rec
    raise SignalRecordError(
        f"--from-pool: no {mode} signal for {pool} delivered in the last "
        f"{max_age // 60} minutes ({path})")
