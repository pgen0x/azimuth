#!/bin/bash
# Tests for dlmm_realized_cadence.sh: when the monitor loop starts a realized reconciliation.
# Synthetic clock and a temp closes file; nothing is spawned. Run: bash test_dlmm_realized_cadence.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
CLOSES="$TMP/dlmm_closes.jsonl"
fails=0
check() { # check NAME EXPECTED(0=run,1=no run) NOW
    local got=1
    realized_schedule "$3" "$CLOSES"
    realized_take "$3" && got=0
    if [ "$got" != "$2" ]; then echo "FAIL $1: at t=$3 expected $([ "$2" = 0 ] && echo run || echo wait)"; fails=$((fails+1)); fi
}
reset() { unset REALIZED_SIG REALIZED_DUE REALIZED_NEXT_POLL; source "$HERE/dlmm_realized_cadence.sh"; }
close_at() { echo "{\"event\":\"exit\",\"n\":$RANDOM}" >> "$CLOSES"; touch -d "@$1" "$CLOSES"; }

T=1800000000

# No closes file: periodic poll still runs (it is a cheap --if-pending), then every 15 min.
reset
check "no file, first poll" 0 $T
check "no file, inside poll gap" 1 $((T+20))
check "no file, next poll" 0 $((T+900))

# Startup with an existing journal waits the indexer delay, not an immediate fetch.
reset; close_at $((T-3600))
check "startup delay" 1 $T
check "startup delay, 4m" 1 $((T+240))
check "startup run at 5m" 0 $((T+300))
check "after run, quiet" 1 $((T+320))

# A close mid-run schedules 5 min later; a due poll must not pull it earlier.
close_at $((T+1300))
check "close seen, delayed" 1 $((T+1300))
check "poll due but close pending" 1 $((T+1300+120))
check "close run at 5m" 0 $((T+1300+300))
# No further change: polls resume every 15 min (retries an unindexed close).
check "poll gap" 1 $((T+1600+600))
check "poll at 15m" 0 $((T+1600+900))

# A second close before the first fires pushes the due time to the newest close.
reset; close_at $T
check "first close" 1 $T
close_at $((T+120))
check "second close" 1 $((T+120))
check "not at first close + 5m" 1 $((T+300))
check "at second close + 5m" 0 $((T+420))

# A busy worker (caller skips realized_take) leaves the run due for the next tick.
reset; close_at $T
check "close seen" 1 $T
realized_schedule $((T+300)) "$CLOSES"   # due tick, but the worker was busy: no take
check "deferred run fires next tick" 0 $((T+320))

# Same mtime but different size still counts as a change.
reset; close_at $T
check "baseline" 1 $T
realized_take $((T+300)) || { echo "FAIL baseline run"; fails=$((fails+1)); }
echo x >> "$CLOSES"; touch -d "@$T" "$CLOSES"
check "size change" 1 $((T+400))
check "size change run" 0 $((T+700))

if [ "$fails" -eq 0 ]; then echo "ok: realized cadence"; else echo "$fails failure(s)"; exit 1; fi
