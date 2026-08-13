#!/usr/bin/env bash
# Installs the DLMM signal system into a Hermes profile:
#   1. copies the solana-dlmm skill + safety scripts, rewriting absolute paths
#   2. installs the dlmm-signal webhook subscription (agent decision logic)
#   3. builds the Go discovery daemon
# It never touches your wallet keys — those live in the profile .env you create.
set -euo pipefail

PROFILE="${1:-$HOME/.hermes/profiles/dlmm}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "→ Target Hermes profile: $PROFILE"
mkdir -p "$PROFILE/skills/solana-dlmm" "$PROFILE/skills/solana-web3/scripts"

echo "→ Symlinking solana-dlmm scripts"
# scripts/ is symlinked (not copied) so edits in the repo take effect immediately in
# every installed profile without re-running install.sh. The scripts resolve their own
# profile dir at runtime (3 levels up from their own file location), so no path rewrite
# is needed here.
if [ -e "$PROFILE/skills/solana-dlmm/scripts" ] && [ ! -L "$PROFILE/skills/solana-dlmm/scripts" ]; then
  echo "   ⚠ $PROFILE/skills/solana-dlmm/scripts exists as a real directory (pre-symlink install)."
  echo "     Back it up / diff it against $REPO/assets/skill/scripts, then remove it before re-running."
  exit 1
fi
ln -sfn "$REPO/assets/skill/scripts" "$PROFILE/skills/solana-dlmm/scripts"
# SKILL.md is symlinked too — it documents the monitor's exit rules, and a stale copy
# in the profile means the agent reasons from outdated policy. package.json stays a
# copy (informational only; node resolves modules against the scripts' real path).
ln -sfn "$REPO/assets/skill/SKILL.md" "$PROFILE/skills/solana-dlmm/SKILL.md"
cp "$REPO/assets/skill/package.json" "$PROFILE/skills/solana-dlmm/"

echo "→ Symlinking DLMM-relevant solana-web3 scripts"
# Individual file symlinks (not a whole-dir symlink): $PROFILE/skills/solana-web3/scripts
# also holds other, non-DLMM scripts that live only in the profile.
for f in "$REPO/assets/skill/solana-web3-scripts/"*.py; do
  ln -sfn "$f" "$PROFILE/skills/solana-web3/scripts/$(basename "$f")"
done

echo "→ Merging DLMM section into SOUL.md"
# Section 9 only — SOUL.md is a large per-profile personality/config document with
# sections unrelated to DLMM; this replaces/inserts just the "## 9. Meteora DLMM ..."
# block instead of touching (or symlinking) the whole file, which self_improvement.py's
# update_soul_section.py also tunes live based on trading performance.
SOUL_DST="$PROFILE/SOUL.md"
touch "$SOUL_DST"
python3 - "$SOUL_DST" "$REPO/assets/hermes/SOUL_dlmm_section.md" <<'PY'
import re, sys
dst_path, section_path = sys.argv[1], sys.argv[2]
section = open(section_path).read().rstrip() + "\n"
content = open(dst_path).read()
pattern = re.compile(r"^## 9\..*?(?=^## \d|\Z)", re.DOTALL | re.MULTILINE)
if pattern.search(content):
    content = pattern.sub(section, content)
    print("   replaced existing ## 9. section in SOUL.md")
else:
    sep = "\n\n" if content.strip() else ""
    content = content.rstrip() + sep + "\n" + section
    print("   appended ## 9. section to SOUL.md")
open(dst_path, "w").write(content)
PY

echo "→ Installing cron pre-run scripts"
# Copied with the __PROFILE__ token rewritten, not symlinked: Hermes validates a
# cron job's script path against HERMES_HOME/scripts/ and rejects anything that
# resolves outside it, so these cannot live in the repo the way skills/scripts do.
mkdir -p "$PROFILE/scripts"
for f in "$REPO/assets/hermes/scripts/"*; do
  sed "s#__PROFILE__#$PROFILE#g" "$f" > "$PROFILE/scripts/$(basename "$f")"
  chmod +x "$PROFILE/scripts/$(basename "$f")"
  echo "   $(basename "$f")"
done

echo "→ Merging DLMM cron jobs (skips any job id or name that already exists)"
JOBS_DST="$PROFILE/cron/jobs.json"
mkdir -p "$(dirname "$JOBS_DST")"
[ -f "$JOBS_DST" ] || echo "[]" > "$JOBS_DST"
python3 - "$JOBS_DST" "$REPO/assets/hermes/cron_jobs_template.json" "$PROFILE" <<'PY'
import json, sys
dst, src, profile = sys.argv[1], sys.argv[2], sys.argv[3]
raw = json.load(open(dst))
# Hermes stores {"jobs": [...], "updated_at": ...}; older files were a bare
# list. Remember which shape we read and write the same one back — dumping a
# bare list over a wrapped file made Hermes log "Auto-repaired jobs.json (bare
# list wrapped as dict)" on its next tick.
wrapped = isinstance(raw, dict)
existing = raw.get("jobs", []) if wrapped else raw
# Match on id AND name. Name alone is not an identity: the operator renames
# jobs per profile ("DLMM ..." -> "Solanza ..."), and a name-only check then
# re-appended the template under an id that was already live — two entries
# sharing one id, one still carrying the REPLACE_ME deliver placeholder, both
# claiming the same schedule.
existing_ids = {j.get("id") for j in existing if j.get("id")}
existing_names = {j.get("name") for j in existing}
template = json.loads(open(src).read().replace("__PROFILE__", profile))
added = 0
for job in template:
    if job.get("id") in existing_ids:
        print(f"   skipped (id already present): {job['id']}")
        continue
    if job["name"] in existing_names:
        print(f"   skipped (already present): {job['name']}")
        continue
    existing.append(job)
    existing_ids.add(job.get("id"))
    existing_names.add(job["name"])
    added += 1
    print(f"   added: {job['name']} (edit \"deliver\" — it's a placeholder)")
if wrapped:
    raw["jobs"] = existing
    json.dump(raw, open(dst, "w"), indent=2)
else:
    json.dump(existing, open(dst, "w"), indent=2)
if added == 0:
    print("   no new jobs added")
PY

echo "→ Installing webhook subscription (merges into existing file if present)"
SUB_SRC="$REPO/assets/hermes/webhook_subscriptions.json"
SUB_DST="$PROFILE/webhook_subscriptions.json"
if [ -f "$SUB_DST" ]; then
  python3 - "$SUB_DST" "$SUB_SRC" "$PROFILE" <<'PY'
import json,sys
dst,src,profile=sys.argv[1],sys.argv[2],sys.argv[3]
d=json.load(open(dst))
s=json.loads(open(src).read().replace("__PROFILE__",profile))
# Preserve per-profile config on re-install: an existing entry's secret,
# delivery target, model and enabled flag are live operator-set values —
# only the prompt (and any brand-new fields) should follow the repo. The
# repo's placeholders must never clobber real values.
PRESERVE=("secret","deliver","deliver_extra","model","enabled")
for name,entry in s.items():
    old=d.get(name)
    if isinstance(old,dict):
        for k in PRESERVE:
            if k in old:
                entry[k]=old[k]
    d[name]=entry
json.dump(d,open(dst,'w'),indent=2)
print("   merged dlmm-signal into existing webhook_subscriptions.json (kept existing secret/delivery/model)")
PY
else
  sed "s#__PROFILE__#$PROFILE#g" "$SUB_SRC" > "$SUB_DST"
  echo "   created $SUB_DST"
fi

echo "→ npm install (Meteora SDK) in repo"
# Installed in the repo, not the profile: dlmm_executor.js is reached through the
# scripts/ symlink, and Node resolves require() against the script's *real* path
# (it always realpaths symlinks for module resolution) — so node_modules has to live
# next to the real file, in $REPO/assets/skill, not under the profile.
( cd "$REPO/assets/skill" && npm install --no-audit --no-fund >/dev/null 2>&1 ) && echo "   ok" || echo "   ⚠ npm install failed — run manually in $REPO/assets/skill"

echo "→ Building Go daemon"
( cd "$REPO" && go build -o azimuth . ) && echo "   built $REPO/azimuth"

echo "→ Installing user systemd services"
# Three user units, all WantedBy=default.target (so `loginctl enable-linger` is
# what actually keeps them alive across logout/reboot):
#   azimuth-sol-monitor         — 20s exit loop, the trader-side safety net:
#                              auto-close, auto-swap-to-SOL, OOR re-centering and
#                              cooldowns fire from here; the Hermes cron is only
#                              the reporting layer. Enabled + started.
#   azimuth — the Go discovery daemon (this repo). Enabled +
#                              started only if $REPO/.env exists; it is the unit's
#                              EnvironmentFile, so starting without it just fails.
#   azimuth-rh-monitor          — Robinhood Chain exit loop. Installed, NOT enabled:
#                              that venue is observe-only until you deploy there.
# Idempotent: re-running rewrites the units and restarts what is enabled.
if command -v systemctl >/dev/null 2>&1 && systemctl --user show-environment >/dev/null 2>&1; then
  UNIT_DIR="$HOME/.config/systemd/user"
  mkdir -p "$UNIT_DIR"
  sed "s#__PROFILE__#$PROFILE#g" "$REPO/assets/systemd/azimuth-sol-monitor.service" > "$UNIT_DIR/azimuth-sol-monitor.service"
  sed "s#__PROFILE__#$PROFILE#g" "$REPO/assets/systemd/azimuth-rh-monitor.service"  > "$UNIT_DIR/azimuth-rh-monitor.service"
  # The daemon posts to this profile's Hermes gateway, so order after it. Weak
  # Wants= — if that unit doesn't exist (direct-deploy-only hosts) systemd just
  # logs a warning instead of refusing to start the daemon.
  GATEWAY_UNIT="hermes-gateway-$(basename "$PROFILE").service"
  sed -e "s#__REPO__#$REPO#g" -e "s#__GATEWAY__#$GATEWAY_UNIT#g" \
    "$REPO/assets/systemd/azimuth.service" > "$UNIT_DIR/azimuth.service"
  systemctl --user daemon-reload
  systemctl --user enable --now azimuth-sol-monitor.service
  echo "   installed + started azimuth-sol-monitor.service"
  if [ -f "$REPO/.env" ]; then
    systemctl --user enable --now azimuth.service
    systemctl --user restart azimuth.service
    echo "   installed + started azimuth.service"
  else
    echo "   installed azimuth.service (not started — create $REPO/.env first,"
    echo "     then: systemctl --user enable --now azimuth.service)"
  fi
  echo "   installed azimuth-rh-monitor.service (not enabled — Robinhood venue is observe-only)"
  echo "   ⚠ run 'loginctl enable-linger $USER' once so the loops survive logout/reboot"
  echo "   logs: journalctl --user -u azimuth -f"
else
  echo "   ⚠ no user systemd available — run the loop + daemon yourself:"
  echo "     nohup bash $PROFILE/skills/solana-dlmm/scripts/dlmm_monitor_loop.sh &"
  echo "     ( cd $REPO && set -a && . ./.env && set +a && nohup ./azimuth & )"
fi

cat <<DONE

✅ Install complete.

Next steps:
  1. Create $PROFILE/.env with:
       SOLANA_PUBLIC_KEY=...
       SOLANA_PRIVATE_KEY=...          # base58, used by dlmm_executor.js
       SOLANA_RPC_URLS=...             # comma-separated, tried in order with failover
                                        # (defaults to public mainnet-beta RPC if unset)
       DLMM_ALERT_TARGET=telegram      # instant trade alerts via \`hermes send\`
                                        # ("platform" or "platform:chat_id"; empty disables)
       DLMM_TZ=Asia/Jakarta            # report-card timezone (IANA name; empty = system zone)
       DLMM_STATS_HOUR=09              # daily scoreboard send hour in DLMM_TZ (00-23)
  2. Edit $SUB_DST:
       - set "secret" (match HERMES_WEBHOOK_SECRET below)
       - set deliver_extra.chat_id to your channel
  3. Enable the webhook platform in $PROFILE/config.yaml (port 8646).
  4. Edit $JOBS_DST — replace the "deliver" placeholder on the three DLMM cron jobs
     (Position Monitor, Self-Improvement Review, Journal Reconciliation) with your channel.
  5. Configure + run the daemon:
       cp $REPO/.env.example $REPO/.env   # edit secret to match step 2
       systemctl --user enable --now azimuth.service
       # or, foreground:  cd $REPO && set -a && . ./.env && set +a && ./azimuth

Services + logs:
  systemctl --user status azimuth azimuth-sol-monitor
  journalctl --user -u azimuth -u azimuth-sol-monitor -f
DONE
