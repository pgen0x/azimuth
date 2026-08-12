#!/bin/bash
# uni_monitor_loop.sh — Continuous Robinhood Chain (Uniswap v3) position
# monitor. Runs the one-shot uni_monitor.py scan in a loop so the exit rules
# (SL/TP/trailing/fast-out/OOR) fire reliably, mirroring dlmm_monitor_loop.sh.
#
# Interval matches the Solana loop (20s). It did not always: the tick used to
# cost one GeckoTerminal request per position against the ~10 req/min budget the
# discovery daemon shares, so 60s was the only cadence that stayed clear of it —
# which, with a ~24s scan, made the real reaction time ~84s.
#
# Two changes removed the coupling. /pools/multi/ made momentum ONE request per
# tick regardless of position count, and that request is now served from a cache
# with its own TTL (uni_monitor.py MOMENTUM_TTL, 60s) instead of the loop's
# period. So the GT spend at 20s is what it was at 60s, while the rules that
# actually need speed — PnL, in-range, ladder rung fills — are on-chain reads
# whose budget is far larger. A filled rung is now seen within ~20s of the scan
# rather than up to ~84s.
#
# Do not shorten this further without re-measuring the scan itself: once the
# sleep is shorter than a scan, ticks are paced by the scan and the number here
# stops meaning anything.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_DIR="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

echo "Starting Robinhood Chain (Uniswap v3/v4) Position Monitor Loop (20s interval)..."

cd "$SCRIPT_DIR" || exit 1
while true; do
    # Re-source the profile .env EVERY tick, not once at startup. Sourcing it
    # outside the loop froze the process env at launch time: a later edit to
    # DRY_RUN (true -> false) stayed invisible to the running loop, which kept
    # printing "[dry-run] would close" while a position sat 22 points past its
    # emergency SL — exits live in the file, dead in the process. A trading loop
    # must never hold a stale copy of its own kill switch.
    set -a
    source "$PROFILE_DIR/.env" 2>/dev/null
    set +a

    python3 "$SCRIPT_DIR/uni_monitor.py"
    sleep 20
done
