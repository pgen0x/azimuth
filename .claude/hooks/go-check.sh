#!/usr/bin/env bash
# PostToolUse: gofmt + vet + unit tests after every Go edit.
#
# .github/workflows/ci.yml runs `go vet` and `go build` only — the tests under
# internal/ (screen, pulse, momentum, indicators, deploy, mature, copycat) have
# no other gate, and they are the ones guarding the screening thresholds that
# decide what this daemon buys. Whole suite is ~4s.
set -uo pipefail

payload=$(cat)
path=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // ""')

[[ "$path" == *.go ]] || exit 0
[[ "$path" == *node_modules* ]] && exit 0

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0

fail=""

# Scoped to the edited file on purpose: a repo-wide `gofmt -l` would fail this
# hook on pre-existing drift in files the edit never touched, and a hook that
# always fires gets ignored.
if [[ -n "$(gofmt -l "$path" 2>/dev/null)" ]]; then
	fail+="gofmt: $path needs formatting (run: gofmt -w $path)\n"
fi

if ! vet=$(timeout 120 go vet ./... 2>&1); then
	fail+="go vet failed:\n$vet\n"
fi

if ! test_out=$(timeout 180 go test ./internal/... 2>&1); then
	fail+="go test failed:\n$test_out\n"
fi

if [[ -n "$fail" ]]; then
	printf 'Go checks failed after editing %s:\n\n' "$path" >&2
	printf '%b' "$fail" >&2
	exit 2
fi

exit 0
