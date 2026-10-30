"""Bounded, best-effort research output. Never used for trading decisions."""
import contextlib
import fcntl
import json
import os
import stat
import sys
import time


@contextlib.contextmanager
def research_writer(path, payload_bytes, max_bytes):
    """Serialize cooperating appenders without waiting for a lock.

    A partial tail is preserved and refused on subsequent appends. No repair,
    truncation, rotation or deletion of existing evidence happens here. Regular
    filesystem I/O can still wait for storage; O_NONBLOCK is not a disk deadline.
    """
    fd = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NONBLOCK | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError('research_not_regular')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        size = os.fstat(fd).st_size
        if size + payload_bytes > max_bytes:
            raise OSError('research_byte_cap')
        if size and os.pread(fd, 1, size - 1) != b'\n':
            raise OSError('research_partial_tail')
        yield fd
    finally:
        os.close(fd)


def research_write(fd, payload):
    if os.write(fd, payload) != len(payload):
        raise OSError('research_short_write')


def observer_tick_status(component, started_at, regular_tick=True):
    """Evidence from the actual completed Python child, including when flags are off."""
    print('OBSERVER_TICK ' + json.dumps(dict(
        component=component, pid=os.getpid(), started_at=started_at,
        completed_at=time.time(), regular_tick=regular_tick,
        flags={key: os.environ.get(key) == '1' for key in (
            'DLMM_SHADOW_EXITS', 'DLMM_REJECT_IDENTITY', 'DLMM_BRACKET_REJECTS')})), file=sys.stderr, flush=True)


def run_observed_main(component, main, regular_tick=True):
    started_at = time.time()
    try:
        result = main()
    except SystemExit as error:
        if error.code in (None, 0):
            observer_tick_status(component, started_at, regular_tick)
        raise
    observer_tick_status(component, started_at, regular_tick)
    return result
