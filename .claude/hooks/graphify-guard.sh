#!/usr/bin/env bash
# PreToolUse hook: forward the tool payload to `graphify hook-guard <mode>`.
#
# graphify is an optional, per-machine tool, so the hook resolves it from PATH
# (then ~/.local/bin) instead of a hard-coded absolute path. Without graphify the
# hook is a no-op: contributors who never installed it are not blocked.
set -uo pipefail

mode=${1:?usage: graphify-guard.sh search|read}
bin=$(command -v graphify 2>/dev/null || true)
[[ -z "$bin" && -x "$HOME/.local/bin/graphify" ]] && bin="$HOME/.local/bin/graphify"
if [[ -z "$bin" ]]; then
  cat >/dev/null
  exit 0
fi
exec "$bin" hook-guard "$mode"
