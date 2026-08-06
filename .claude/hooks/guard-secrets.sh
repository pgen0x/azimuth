#!/usr/bin/env bash
# PreToolUse guard: refuse to read, edit, or dump this repo's .env.
#
# .env holds live Solana/EVM wallet private keys (see the .gitignore comment and
# CLAUDE.md "Security"). It is gitignored but sits in the worktree, so any Read,
# Edit, or `cat` pulls the keys straight into a model context. .env.example is
# the non-secret template and stays allowed.
#
# Sourcing .env to actually run the daemon (`set -a && . ./.env`) is legitimate
# and is NOT blocked — only commands that print, copy, or ship the file are.
set -uo pipefail

payload=$(cat)
tool=$(printf '%s' "$payload" | jq -r '.tool_name // ""')
path=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // ""')
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')

# Matches .env, .env.bak, .env.local, .env.2026-07-13 — never .env.example.
SECRET_ENV='\.env\b(?!\.example)'
# Commands that would expose the contents rather than load them.
DUMP_VERBS='\b(cat|bat|less|more|head|tail|nl|strings|xxd|od|grep|rg|awk|sed|cp|mv|rsync|scp|base64|tee)\b'

deny() {
	echo "BLOCKED: $1 targets .env, which holds live wallet private keys." >&2
	echo "Read .env.example instead for the config schema; ask the operator for values." >&2
	exit 2
}

if [[ -n "$path" ]] && printf '%s' "$path" | grep -qP "$SECRET_ENV"; then
	deny "$tool"
fi

if [[ "$tool" == "Bash" && -n "$cmd" ]]; then
	if printf '%s' "$cmd" | grep -qP "$DUMP_VERBS" && printf '%s' "$cmd" | grep -qP "$SECRET_ENV"; then
		deny "this command"
	fi
fi

exit 0
