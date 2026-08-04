#!/usr/bin/env bash
# Bucket the azimuth journal into per-mode batch/deploy/reject counts.
#
# Deterministic on purpose: the numbers a soak decision rests on should come out
# of the same greps every time, not out of whatever the model felt like counting
# on this run. Line formats come from internal/scanner/scanner.go and the gate
# prefixes in internal/deploy/deploy.go (GateNarrative).
#
# Usage: soak_report.sh ["<journalctl --since arg>"]   (default: 24 hours ago)
set -uo pipefail

SINCE="${1:-24 hours ago}"

log=$(journalctl --user -u azimuth --since "$SINCE" --no-pager 2>/dev/null)
if [[ -z "$log" ]]; then
	echo "No azimuth journal entries since '$SINCE'."
	echo "Check: systemctl --user is-active azimuth"
	exit 0
fi

count() { printf '%s\n' "$log" | grep -cF "$1"; }

echo "# azimuth soak report — since $SINCE"
echo
printf 'journal lines: %s\n' "$(printf '%s\n' "$log" | wc -l)"
echo

echo "## Batches per mode"
printf '%-12s %8s %8s %8s\n' mode signals deploys skipped
for mode in casual multiday turnover pulse fresh mature; do
	tag="scanner[$mode]:"
	sig=$(printf '%s\n' "$log" | grep -F "$tag" | grep -cE 'SIGNAL batch sent|OBSERVE batch of|direct deploy done')
	dep=$(printf '%s\n' "$log" | grep -F "$tag" | grep -cF 'deployed=true')
	skip=$(printf '%s\n' "$log" | grep -F "$tag" | grep -cF 'DEPLOY SKIPPED')
	[[ "$sig" == 0 && "$dep" == 0 && "$skip" == 0 ]] && continue
	printf '%-12s %8s %8s %8s\n' "$mode" "$sig" "$dep" "$skip"
done
echo

echo "## Deploy outcomes"
printf 'deployed=true   %s\n' "$(count 'deployed=true')"
printf 'deployed=false  %s\n' "$(count 'deployed=false')"
printf 'deploy failed   %s\n' "$(count 'direct deploy failed')"
printf 'DRY RUN         %s\n' "$(count 'DRY RUN DEPLOY')"
echo

echo "## Decisive gates (top 15)"
# GateNarrative lines: "Batch reject <sym>: <reason>", "Skipping <sym>: <reason>",
# "Aborting: <reason>". Strip the symbol and digits so reasons aggregate.
printf '%s\n' "$log" |
	grep -oE '(Batch reject|Skipping|Aborting:|DEPLOY SKIPPED).*' |
	sed -E 's/(Batch reject|Skipping) [A-Za-z0-9_.$-]+/\1/; s/[0-9]+(\.[0-9]+)?/N/g' |
	sort | uniq -c | sort -rn | head -15
echo

echo "## Pre-screen rejects"
printf 'holders       %s\n' "$(printf '%s\n' "$log" | grep -cE 'rejected: holders')"
printf 'security      %s\n' "$(printf '%s\n' "$log" | grep -cE 'rejected on security')"
printf 'gmgn          %s\n' "$(printf '%s\n' "$log" | grep -cE 'rejected on gmgn')"
printf 'entry timing  %s\n' "$(printf '%s\n' "$log" | grep -cE 'rejected on entry timing')"
printf 'copycat       %s\n' "$(count 'is a copycat')"
echo

echo "## Errors"
printf '%s\n' "$log" |
	grep -oE '(fetch error|seen store error|webhook error|batch marshal error|report delivery failed)' |
	sort | uniq -c | sort -rn
