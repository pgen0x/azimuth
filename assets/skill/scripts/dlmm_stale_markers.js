// Stale executor markers: an operator command, not a timer.
//
// A pending marker exists so a restarted process can reconcile the exact
// signed bytes it may have broadcast. Writers clear it once they see a
// verdict, but several paths stop looking first: a swap whose 8s confirm
// timed out is reconciled only when the SAME mint pair swaps again (a sold bag
// never does), and a close whose confirm timed out is never retried once the
// monitor sees the position gone. Each one then outlives its blockhash forever.
//
// This archives a marker only when nothing can still happen to it: its
// blockhash has expired at finalized height AND its signature's outcome is
// final (finalized ok, finalized failed, or absent after expiry: the same
// verdicts reconcilePendingSwap acts on). Anything else stays where it is.
// A deferred dust settlement (no route / below the recovery floor) older than
// 24h whose remaining value cannot pay a base fee is retired the same way, so
// the dust rules own the mint instead of a 15-minute retry that can never win.
//
// Archive, never delete: files move to memories/archive/markers/<dir>/ with a
// <file>.resolution.json note beside them. RPC, quotes and locks are injected
// (deps), so every rule is testable offline. A dry run writes nothing.
"use strict";

const SIGNATURE_DIRS = ["dlmm_pending_swaps", "dlmm_pending_deploys", "dlmm_pending_closes", "dlmm_pending_rent"];
const SETTLEMENT_DIR = "dlmm_settlements";
const SETTLEMENT_RETIRE_AGE_S = 24 * 3600;
// Below one base fee no settlement swap can net a positive lamport.
const SETTLEMENT_DUST_MAX_LAMPORTS = 5000n;
// dlmm_monitor.settle_pending retries a deferred marker after 900s; act only
// inside the quiet part of that window so the monitor is not mid-attempt.
const SETTLEMENT_QUIET_S = 800;
const DUST_REASONS = ["swap_no_route", "net_recovery_below_floor"];

const keep = (why, extra = {}) => ({ action: "keep", resolution: why, ...extra });
const archive = (why, extra = {}) => ({ action: "archive", resolution: why, ...extra });

// status: one getSignatureStatuses(..., {searchTransactionHistory: true}) entry.
function classifySignature({ dir, marker, finalizedHeight, status, positionExists }) {
  if (!marker || typeof marker.signature !== "string" || !Number.isSafeInteger(marker.lastValidBlockHeight)) {
    return keep("invalid_marker");
  }
  if (!Number.isSafeInteger(finalizedHeight)) return keep("height_unmeasured");
  if (finalizedHeight <= marker.lastValidBlockHeight) return keep("blockhash_live");
  if (status === undefined) return keep("status_unmeasured");
  let outcome;
  if (status === null) outcome = "never_landed_expired";
  else if (status.confirmationStatus !== "finalized") return keep("not_finalized");
  else if (status.err === null) outcome = "landed_finalized";
  else if (status.err) outcome = "failed_finalized";
  else return keep("status_unmeasured");
  // A landed close is resolved only once the position is gone; a failed or
  // unlanded one leaves an open position the monitor closes again itself.
  if (dir === "dlmm_pending_closes" && outcome === "landed_finalized" && positionExists !== false) {
    return keep(positionExists === true ? "close_landed_position_open" : "position_unmeasured");
  }
  return archive(outcome);
}

// Hadron exclusion sidecar (dlmm_route_retry): a 300s TTL, meaningless once past.
function classifyRoute({ marker, now }) {
  if (!marker || !Number.isFinite(marker.expires_at)) return keep("invalid_marker");
  return now >= marker.expires_at ? archive("route_exclusion_expired") : keep("route_exclusion_live");
}

// The rules that need no RPC. null = passed, so chain reads are worth spending.
function settlementOfflineGate({ marker, now, queuedAt }) {
  if (!marker || typeof marker.position !== "string" || typeof marker.mint !== "string") return keep("invalid_marker");
  if (marker.state !== "deferred" || !DUST_REASONS.includes(marker.reason)) return keep("not_deferred_dust");
  if (!/^\d+$/.test(String(marker.remaining_raw ?? ""))) return keep("remaining_unknown");
  if (!Number.isFinite(queuedAt)) return keep("age_unknown");
  if (now - queuedAt < SETTLEMENT_RETIRE_AGE_S) return keep("younger_than_24h");
  const since = now - Number(marker.last_attempt);
  if (!Number.isFinite(since) || since < 0 || since >= SETTLEMENT_QUIET_S) return keep("retry_due");
  return null;
}

// quote: dustQuoteLamports(mint, balance) result, only asked when needed.
function classifySettlement({ marker, now, queuedAt, positionExists, balanceRaw, quote }) {
  const offline = settlementOfflineGate({ marker, now, queuedAt });
  if (offline) return offline;
  if (positionExists !== false) return keep(positionExists === true ? "position_open" : "position_unmeasured");
  if (typeof balanceRaw !== "string" || !/^\d+$/.test(balanceRaw)) return keep("balance_unmeasured");
  // A later exit topped the balance up; that inventory is a new question.
  if (BigInt(balanceRaw) > BigInt(marker.remaining_raw)) return keep("balance_grew");
  if (balanceRaw === "0") return archive("settled_elsewhere", { balance_raw: balanceRaw });
  if (quote?.lamports !== undefined) {
    return BigInt(quote.lamports) < SETTLEMENT_DUST_MAX_LAMPORTS
      ? archive("dust_below_base_fee", { balance_raw: balanceRaw, quote_lamports: String(quote.lamports) })
      : keep("value_above_base_fee", { quote_lamports: String(quote.lamports) });
  }
  // A day of deferral plus a fresh no-route: retiring only hands the mint to
  // the dust rules, which never burn on no-route either.
  if (quote?.verdict === "no_route") return archive("no_route_dust", { balance_raw: balanceRaw });
  return keep("quote_unavailable", { verdict: quote?.verdict || null });
}

function readMarkers(memoriesDir, fs, path) {
  const out = [];
  const list = dir => fs.existsSync(dir) ? fs.readdirSync(dir).sort() : [];
  for (const dir of [...SIGNATURE_DIRS, SETTLEMENT_DIR]) {
    for (const file of list(path.join(memoriesDir, dir))) {
      const kind = file.endsWith(".json.route") && dir === "dlmm_pending_swaps" ? "route"
        : file.endsWith(".json") ? (dir === SETTLEMENT_DIR ? "settlement" : "signature") : null;
      if (!kind) continue;
      const filePath = path.join(memoriesDir, dir, file);
      let text = null, marker = null;
      try { text = fs.readFileSync(filePath, "utf8"); marker = JSON.parse(text); } catch { /* invalid stays */ }
      out.push({ dir, file, kind, filePath, text, marker });
    }
  }
  return out;
}

// Move one marker under archive/markers/<dir>/ only if it is byte-identical to
// what was classified; a writer that touched it since owns it again.
function archiveMarker(item, note, { memoriesDir, fs, path, now }) {
  let current;
  try { current = fs.readFileSync(item.filePath, "utf8"); } catch { return false; }
  if (current !== item.text) return false;
  const dest = path.join(memoriesDir, "archive", "markers", item.dir);
  fs.mkdirSync(dest, { recursive: true, mode: 0o700 });
  let name = item.file;
  if (fs.existsSync(path.join(dest, name))) name = `${item.file}.${Math.floor(now)}`;
  fs.writeFileSync(path.join(dest, `${name}.resolution.json`), JSON.stringify({ ...note, archived_at: now,
    source: `${item.dir}/${item.file}` }), { mode: 0o600, flag: "wx" });
  fs.renameSync(item.filePath, path.join(dest, name));
  return true;
}

// deps: memoriesDir, fs, path, finalizedHeight(), signatureStatuses(sigs),
// positionExists(address) -> bool|null, walletBalanceRaw(mint) -> string|null,
// quote(mint, raw), closedAt(position) -> unix s|null.
async function reconcileStaleMarkers({ execute = false, now = Date.now() / 1000 } = {}, deps) {
  const { memoriesDir, fs, path } = deps;
  const items = readMarkers(memoriesDir, fs, path);
  const signed = items.filter(i => i.kind === "signature" && typeof i.marker?.signature === "string");
  const finalizedHeight = items.some(i => i.kind === "signature") ? await deps.finalizedHeight() : null;
  let statuses = new Map();
  if (signed.length) {
    const list = await deps.signatureStatuses(signed.map(i => i.marker.signature));
    if (Array.isArray(list) && list.length === signed.length) {
      statuses = new Map(signed.map((i, n) => [i.marker.signature, list[n]]));
    }
  }
  const results = [];
  for (const item of items) {
    let verdict, evidence = {};
    if (item.kind === "route") {
      verdict = classifyRoute({ marker: item.marker, now });
    } else if (item.kind === "signature") {
      const sig = item.marker?.signature;
      const status = statuses.has(sig) ? statuses.get(sig) : undefined;
      let positionExists;
      if (item.dir === "dlmm_pending_closes" && status?.confirmationStatus === "finalized" && status.err === null) {
        positionExists = await deps.positionExists(item.file.replace(/\.json$/, ""));
      }
      verdict = classifySignature({ dir: item.dir, marker: item.marker, finalizedHeight, status, positionExists });
      evidence = { signature: sig || null, last_valid_block_height: item.marker?.lastValidBlockHeight ?? null,
        finalized_height: finalizedHeight, status: status === undefined ? "unmeasured" : status,
        ...(positionExists !== undefined ? { position_exists: positionExists } : {}) };
    } else {
      const m = item.marker || {};
      const queuedAt = Number.isFinite(m.queued_at) ? m.queued_at : deps.closedAt(m.position);
      verdict = settlementOfflineGate({ marker: item.marker, now, queuedAt });
      if (!verdict) {
        // Spend RPC and quote budget only on markers every offline rule passed.
        const positionExists = await deps.positionExists(m.position);
        const balanceRaw = positionExists === false ? await deps.walletBalanceRaw(m.mint) : null;
        let quote;
        if (/^[1-9]\d*$/.test(String(balanceRaw)) && BigInt(balanceRaw) <= BigInt(m.remaining_raw)) {
          quote = await deps.quote(m.mint, balanceRaw);
        }
        verdict = classifySettlement({ marker: m, now, queuedAt, positionExists, balanceRaw, quote });
      }
      evidence = { position: m.position ?? null, mint: m.mint ?? null, queued_at: queuedAt ?? null,
        remaining_raw: m.remaining_raw ?? null };
    }
    const row = { marker: `${item.dir}/${item.file}`, ...verdict, ...evidence };
    if (execute && verdict.action === "archive") {
      row.archived = archiveMarker(item, row, { memoriesDir, fs, path, now });
      if (!row.archived) row.resolution = "changed_since_read";
    }
    results.push(row);
  }
  return { success: true, dry_run: !execute, finalized_height: finalizedHeight,
    archivable: results.filter(r => r.action === "archive").length,
    archived: results.filter(r => r.archived).length, kept: results.filter(r => r.action === "keep").length,
    markers: results };
}

function parseArgs(args) {
  if (args.some(a => a !== "--execute")) throw new Error("Usage: reconcile-stale-markers [--execute]");
  return { execute: args.includes("--execute") };
}

module.exports = { reconcileStaleMarkers, classifySignature, classifySettlement, classifyRoute, readMarkers,
  archiveMarker, parseArgs, SIGNATURE_DIRS, SETTLEMENT_RETIRE_AGE_S, SETTLEMENT_QUIET_S, SETTLEMENT_DUST_MAX_LAMPORTS };
