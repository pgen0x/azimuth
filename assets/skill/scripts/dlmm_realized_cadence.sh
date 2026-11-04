# dlmm_realized_cadence.sh: when to run the realized-PnL reconciler between the daily runs.
# Sourced by dlmm_monitor_loop.sh; pure bash state, no I/O beyond one stat, so the 20s risk
# loop pays nothing for it. The loop owns the spawn (one background worker, never waited on).
#
# Two triggers, both feeding REALIZED_DUE (unix seconds; empty = nothing scheduled):
#   - dlmm_closes.jsonl changed (mtime:size): due REALIZED_DELAY_S later, because Meteora's
#     datapi indexes a close minutes after it lands and an early fetch just finds nothing.
#   - otherwise every REALIZED_POLL_S: due now. The worker runs with --if-pending, so a poll
#     with every recent close reconciled reads local files and exits without a fetch.
# A poll never pulls a change-triggered run earlier than its delay.

REALIZED_DELAY_S="${REALIZED_DELAY_S:-300}"
REALIZED_POLL_S="${REALIZED_POLL_S:-900}"
REALIZED_SIG="${REALIZED_SIG:-}"
REALIZED_DUE="${REALIZED_DUE:-}"
REALIZED_NEXT_POLL="${REALIZED_NEXT_POLL:-0}"

# realized_schedule NOW CLOSES_PATH: fold this tick's evidence into REALIZED_DUE.
realized_schedule() {
    local now="$1" sig
    sig=$(stat -c '%Y:%s' "$2" 2>/dev/null) || sig=""
    if [ -n "$sig" ] && [ "$sig" != "$REALIZED_SIG" ]; then
        REALIZED_DUE=$((now + REALIZED_DELAY_S))
    fi
    REALIZED_SIG="$sig"
    if [ -z "$REALIZED_DUE" ] && [ "$now" -ge "$REALIZED_NEXT_POLL" ]; then
        REALIZED_DUE="$now"
    fi
}

# realized_take NOW: succeeds when a run is due, and records it as started. The caller
# checks its worker is free first; a busy worker leaves the run due for the next tick.
realized_take() {
    local now="$1"
    [ -n "$REALIZED_DUE" ] && [ "$now" -ge "$REALIZED_DUE" ] || return 1
    REALIZED_DUE=""
    REALIZED_NEXT_POLL=$((now + REALIZED_POLL_S))
}
