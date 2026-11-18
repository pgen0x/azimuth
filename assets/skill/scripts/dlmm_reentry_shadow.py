"""Re-entry shadow, pipeline half: LOGGING ONLY.

dlmm_monitor.py appends kind:"close" rows to memories/dlmm_reentry_shadow.jsonl
for pulse closes that were NOT losses (pump above range, upside OOR, trailing,
fast-out in profit). The daemon appends kind:"blocked" rows when such a pool is
stopped by the re-entry cooldown. This module adds the third source: a pulse
candidate refused by the pipeline's m5-dump momentum gate within 60m of one of
those closes. Nothing here changes a decision; an evaluator joins the rows to
the price-path observers to ask whether a fast re-entry would have paid.
"""
import json
import os
import time

CLOSE_WINDOW_S = 3600   # a blocked m5 dump counts within 60m of a close row
DEDUP_S = 600           # one blocked row per pool per 10m
TAIL_BYTES = 262144     # read only the journal's tail


def record_reentry_blocked(profile_dir, mode, c, h1=None, now=None):
    """Append a kind:"blocked" row for a pulse m5-dump reject that follows a
    qualifying close on the same pool+mint. The m5 gate is the first failing
    gate at its call site and h1 must not fail too, so the dump is the only
    reason the candidate was refused. Local file I/O only, never raises, and
    the reject path ignores the return value; REENTRY_SHADOW=0 disables it.
    Dedup is read back from the journal because the pipeline is a fresh
    process per batch."""
    try:
        if mode != "pulse" or os.environ.get("REENTRY_SHADOW", "1").strip() == "0":
            return False
        if h1 is not None and h1 < -15.0:
            return False
        pool, mint = c.get("pool"), c.get("base_mint")
        if not pool or not mint:
            return False
        now = int(time.time() if now is None else now)
        path = os.path.join(profile_dir, "memories", "dlmm_reentry_shadow.jsonl")
        try:
            with open(path, "rb") as f:
                f.seek(0, os.SEEK_END)
                f.seek(max(0, f.tell() - TAIL_BYTES))
                tail = f.read().decode("utf-8", "replace").splitlines()
        except FileNotFoundError:
            return False  # no close rows yet, so nothing to be blocked from
        recent_close = False
        for line in tail:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict) or row.get("pool") != pool:
                continue
            if row.get("kind") == "blocked" and 0 <= now - int(row.get("ts") or 0) < DEDUP_S:
                return False
            if (row.get("kind") == "close" and row.get("mint") == mint
                    and 0 <= now - int(row.get("closed_at") or 0) <= CLOSE_WINDOW_S):
                recent_close = True
        if not recent_close:
            return False
        out = dict(kind="blocked", ts=now, pool=pool, mint=mint, block_reason="momentum_m5_dump",
                   fee_active_tvl_5m=c.get("fee_active_tvl_ratio"), active_tvl=c.get("active_tvl"))
        with open(path, "a") as f:
            f.write(json.dumps(out) + "\n")
        return True
    except Exception as exc:  # a shadow journal must never break a batch
        print(f"⚠️ Re-entry shadow journal failed: {exc}")
        return False
