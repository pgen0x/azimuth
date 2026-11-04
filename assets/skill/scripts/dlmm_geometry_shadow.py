"""Shadow-only geometry study: SOL BidAsk coverage 0.35 (live) vs 0.40 (candidate).

Never used for a trading decision. Two append-only research journals under
``<profile>/memories``:

* ``dlmm_geometry_shadow.jsonl`` — one ``entry`` row per pipeline sol_bidask
  deploy, both arms computed from the SAME anchor (the active bin the executor
  built the live range on), the same bin step and the same ticket.
* ``dlmm_geometry_shadow_obs.jsonl`` — active-bin observations of open pulse
  sol_bidask positions, reusing the monitor's own per-tick read (no extra RPC),
  at most one row per position per ``OBS_MIN_INTERVAL_S``.

``dlmm_geometry_shadow_report.py`` joins the two to closes. Every writer here is
best effort: it swallows its own errors and never raises into the caller.
"""
import json
import math
import os
import re
import stat
import time

SCHEMA = 1
ENTRY_FILE = "dlmm_geometry_shadow.jsonl"
OBS_FILE = "dlmm_geometry_shadow_obs.jsonl"
OBS_MARKER_DIR = "dlmm_geometry_shadow.d"
OBS_MIN_INTERVAL_S = 60
MAX_BYTES = 64 * 1024 * 1024
BASELINE_COVERAGE = 0.35
CANDIDATE_COVERAGE = 0.40
_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def enabled():
    """On by default; DLMM_GEOMETRY_SHADOW=0 turns both writers off."""
    return os.environ.get("DLMM_GEOMETRY_SHADOW", "1") != "0"


def _int(value):
    return value if type(value) is int else None


def arm(active_bin, bins, bin_step, sol_is_x, coverage):
    """Range a SOL-only BidAsk ladder of ``bins`` bins would occupy.

    SOL=Y: ladder sits below the active bin; SOL=X: above it (same orientation
    rule as the live deploy). ``span_pct`` is the downside price coverage in the
    token's SOL price, which is the same formula on either side.
    """
    lower, upper = (active_bin, active_bin + bins) if sol_is_x else (active_bin - bins, active_bin)
    span = (1.0 - (1.0 + bin_step / 10000.0) ** -bins) * 100.0
    return dict(coverage=coverage, lower_bin=lower, upper_bin=upper, bins=bins + 1,
                bins_ladder=bins, span_pct=round(span, 4))


def arms(active_bin, bin_step, sol_is_x, bins_fn):
    """Both arms from one snapshot. ``bins_fn(bin_step, coverage)`` is the live
    ``sol_bidask_bins``, so the MIN/MAX caps and the 20% floor stay identical."""
    return dict(
        baseline=arm(active_bin, bins_fn(bin_step, BASELINE_COVERAGE), bin_step, sol_is_x, BASELINE_COVERAGE),
        candidate=arm(active_bin, bins_fn(bin_step, CANDIDATE_COVERAGE), bin_step, sol_is_x, CANDIDATE_COVERAGE))


def _append(memories, name, rows):
    from dlmm_research_io import research_writer, research_write
    payload = b"".join((json.dumps(r, allow_nan=False, sort_keys=True) + "\n").encode() for r in rows)
    os.makedirs(memories, exist_ok=True)
    with research_writer(os.path.join(memories, name), len(payload), MAX_BYTES) as fd:
        research_write(fd, payload)


def record_entry(profile_dir, *, position, pool, mode, strategy, bin_step, active_bin, anchor,
                 sol_is_x, size_sol, live_bins_below, live_bins_above, dry_run, bins_fn, now=None):
    """One row per deploy decision. Returns the row written, or None."""
    if not enabled():
        return None
    try:
        if strategy != "sol_bidask" or _int(active_bin) is None or type(sol_is_x) is not bool:
            return None
        if not isinstance(position, str) or not _ID.fullmatch(position):
            return None
        if type(bin_step) not in (int, float) or not math.isfinite(bin_step) or bin_step <= 0:
            return None
        both = arms(active_bin, bin_step, sol_is_x, bins_fn)
        live = both["baseline"]
        # The live range is the baseline arm by construction. If it is not, the
        # constants drifted from the study's assumption; journal it, don't hide it.
        live_lower, live_upper = active_bin - live_bins_below, active_bin + live_bins_above
        row = dict(kind="entry", schema=SCHEMA, ts=time.time() if now is None else now,
                   position=position, pool=pool, mode=mode, strategy=strategy, bin_step=bin_step,
                   active_bin=active_bin, anchor=anchor, sol_is_x=sol_is_x, size_sol=size_sol,
                   dry_run=bool(dry_run), arms=both,
                   arms_identical=both["baseline"]["bins"] == both["candidate"]["bins"],
                   live_matches_baseline=(live_lower, live_upper) == (live["lower_bin"], live["upper_bin"]))
        _append(os.path.join(profile_dir, "memories"), ENTRY_FILE, [row])
        return row
    except Exception as error:  # Research output must never change a deploy.
        print("GEOMETRY_SHADOW_ENTRY_ERROR " + type(error).__name__)
        return None


def observe(profile_dir, position, pool, active_bin, observed_at=None):
    """Rate-limited active-bin observation. Returns True when a row was written.

    The marker file's mtime is the per-position clock, so the limit survives the
    monitor being a fresh process every tick. A failed write leaves the marker
    untouched, so the next tick retries; a lost row is unknown, never zero.
    """
    if not enabled():
        return False
    try:
        if _int(active_bin) is None or not isinstance(position, str) or not _ID.fullmatch(position):
            return False
        now = time.time() if observed_at is None else observed_at
        memories = os.path.join(profile_dir, "memories")
        markers = os.path.join(memories, OBS_MARKER_DIR)
        marker = os.path.join(markers, position)
        try:
            st = os.lstat(marker)
            if not stat.S_ISREG(st.st_mode):
                return False
            if now - st.st_mtime < OBS_MIN_INTERVAL_S:
                return False
        except FileNotFoundError:
            pass
        _append(memories, OBS_FILE, [dict(kind="obs", schema=SCHEMA, ts=now, position=position,
                                          pool=pool, active_bin=active_bin)])
        os.makedirs(markers, mode=0o700, exist_ok=True)
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        os.utime(marker, (now, now))
        return True
    except Exception as error:
        print("GEOMETRY_SHADOW_OBS_ERROR " + type(error).__name__)
        return False
