#!/usr/bin/env bash
# Offline: runs install.sh's own merge_subscription on temp files. No Hermes, no network.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
SUB_SRC="$REPO/assets/hermes/webhook_subscriptions.json"
PROFILE="$TMP/.hermes/profiles/example"
mkdir -p "$PROFILE"
# Define merge_subscription exactly as install.sh does.
eval "$(sed -n '/^merge_subscription() {/,/^}/p' "$REPO/install.sh")"

# Root file with a stale prompt and operator-set fields: prompt follows the repo, the rest is kept.
ROOT="$TMP/.hermes/webhook_subscriptions.json"
cat > "$ROOT" <<'JSON'
{"dlmm-signal": {"prompt": "STALE STEP 5 --from-signal '<CHOSEN_RECORD_JSON>'", "secret": "real-secret",
 "deliver": "telegram", "deliver_extra": {"chat_id": "123"}, "model": "m", "enabled": true,
 "toolsets": ["terminal"], "profile": "example"},
 "other-route": {"prompt": "untouched"}}
JSON
chmod 600 "$ROOT"
merge_subscription "$ROOT" 0 >/dev/null
python3 - "$ROOT" "$SUB_SRC" "$PROFILE" <<'PY'
import json, os, stat, sys
d = json.load(open(sys.argv[1])); e = d["dlmm-signal"]
want = json.loads(open(sys.argv[2]).read().replace("__PROFILE__", sys.argv[3]))["dlmm-signal"]["prompt"]
assert e["prompt"] == want, "prompt not merged"
assert (e["secret"], e["deliver"], e["deliver_extra"], e["model"], e["enabled"], e["toolsets"], e["profile"]) == \
    ("real-secret", "telegram", {"chat_id": "123"}, "m", True, ["terminal"], "example"), e
assert d["other-route"] == {"prompt": "untouched"}
assert stat.S_IMODE(os.stat(sys.argv[1]).st_mode) == 0o600
assert "CHOSEN_RECORD_JSON" not in e["prompt"]
PY
[ -z "$(ls -A "$TMP/.hermes" | grep '^\.webhook_subscriptions\.' || true)" ] || { echo "temp file left behind"; exit 1; }

# Root file without the entry, or no root file at all: nothing is created.
echo '{"other-route": {"prompt": "x"}}' > "$ROOT"
merge_subscription "$ROOT" 0 >/dev/null
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert list(d)==["other-route"], d' "$ROOT"
rm "$ROOT"
merge_subscription "$ROOT" 0 >/dev/null
[ ! -e "$ROOT" ] || { echo "root file must not be created"; exit 1; }
echo "install.sh webhook merge checks passed"
