// Offline: node assets/skill/scripts/test_dlmm_stale_markers.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const m = require("./dlmm_stale_markers");
const { classifySignature, classifySettlement, classifyRoute, reconcileStaleMarkers, parseArgs } = m;

const OK = { confirmationStatus: "finalized", err: null };
const FAIL = { confirmationStatus: "finalized", err: { InstructionError: [2, { Custom: 6001 }] } };
const sig = (lvb = 100) => ({ signature: "sig", lastValidBlockHeight: lvb });

// --- classifySignature: only expired + final outcome archives.
{
  const c = (o) => classifySignature({ dir: "dlmm_pending_swaps", marker: sig(), finalizedHeight: 200, status: OK, ...o });
  assert.deepEqual(c({}), { action: "archive", resolution: "landed_finalized" });
  assert.equal(c({ status: FAIL }).resolution, "failed_finalized");
  assert.equal(c({ status: null }).resolution, "never_landed_expired");
  assert.equal(c({ finalizedHeight: 100 }).resolution, "blockhash_live"); // equal height is still valid
  assert.equal(c({ finalizedHeight: null }).resolution, "height_unmeasured");
  assert.equal(c({ status: undefined }).resolution, "status_unmeasured");
  assert.equal(c({ status: { confirmationStatus: "confirmed", err: null } }).resolution, "not_finalized");
  assert.equal(c({ status: { confirmationStatus: "finalized" } }).resolution, "status_unmeasured");
  assert.equal(c({ marker: { signature: "sig" } }).resolution, "invalid_marker");
  assert.equal(c({ marker: null }).action, "keep");
  // A landed close needs the position gone; failed/unlanded does not.
  const close = (o) => c({ dir: "dlmm_pending_closes", ...o });
  assert.equal(close({ positionExists: false }).action, "archive");
  assert.equal(close({ positionExists: true }).resolution, "close_landed_position_open");
  assert.equal(close({ positionExists: null }).resolution, "position_unmeasured");
  assert.equal(close({ status: FAIL }).action, "archive");
  // Deploy markers: landed is resolved whatever the position did since.
  assert.equal(c({ dir: "dlmm_pending_deploys" }).action, "archive");
}

// --- classifyRoute: TTL sidecar.
assert.equal(classifyRoute({ marker: { expires_at: 10 }, now: 10 }).action, "archive");
assert.equal(classifyRoute({ marker: { expires_at: 10 }, now: 9 }).resolution, "route_exclusion_live");
assert.equal(classifyRoute({ marker: {}, now: 9 }).resolution, "invalid_marker");

// --- classifySettlement.
{
  const NOW = 10 * 86400;
  const marker = { position: "P", mint: "M", state: "deferred", reason: "swap_no_route",
    remaining_raw: "36", last_attempt: NOW - 100 };
  const s = (o = {}, mo = {}) => classifySettlement({ marker: { ...marker, ...mo }, now: NOW, queuedAt: NOW - 20 * 86400,
    positionExists: false, balanceRaw: "36", quote: { verdict: "no_route" }, ...o });
  assert.deepEqual(s(), { action: "archive", resolution: "no_route_dust", balance_raw: "36" });
  assert.equal(s({ quote: { lamports: 4999n } }).resolution, "dust_below_base_fee");
  assert.equal(s({ quote: { lamports: 5000n } }).resolution, "value_above_base_fee");
  assert.equal(s({ quote: { verdict: "rate_limited" } }).resolution, "quote_unavailable");
  assert.equal(s({ quote: undefined }).resolution, "quote_unavailable");
  assert.equal(s({ balanceRaw: "0", quote: undefined }).resolution, "settled_elsewhere");
  assert.equal(s({ balanceRaw: "37" }).resolution, "balance_grew");
  assert.equal(s({ balanceRaw: null }).resolution, "balance_unmeasured");
  assert.equal(s({ positionExists: true }).resolution, "position_open");
  assert.equal(s({ positionExists: null }).resolution, "position_unmeasured");
  assert.equal(s({ queuedAt: NOW - 23 * 3600 }).resolution, "younger_than_24h");
  assert.equal(s({ queuedAt: null }).resolution, "age_unknown");
  assert.equal(s({}, { last_attempt: NOW - m.SETTLEMENT_QUIET_S }).resolution, "retry_due");
  assert.equal(s({}, { last_attempt: NOW + 5 }).resolution, "retry_due");
  assert.equal(s({}, { state: "pending" }).resolution, "not_deferred_dust");
  assert.equal(s({}, { reason: "swap_quote_threshold_unavailable" }).resolution, "not_deferred_dust");
  assert.equal(s({}, { reason: "net_recovery_below_floor" }).action, "archive");
  assert.equal(s({}, { remaining_raw: undefined }).resolution, "remaining_unknown");
}

assert.deepEqual(parseArgs([]), { execute: false });
assert.deepEqual(parseArgs(["--execute"]), { execute: true });
assert.throws(() => parseArgs(["--force"]), /Usage/);

(async () => {
  // --- End to end over a temp memories dir shaped like the 2026-11-04 profile.
  const mem = fs.mkdtempSync(path.join(os.tmpdir(), "stale-markers-"));
  const NOW = 1793794629;
  const put = (dir, file, obj) => {
    fs.mkdirSync(path.join(mem, dir), { recursive: true });
    fs.writeFileSync(path.join(mem, dir, file), typeof obj === "string" ? obj : JSON.stringify(obj));
  };
  put("dlmm_pending_swaps", "W-A-SOL.json", { signature: "swapOk", lastValidBlockHeight: 100 });
  put("dlmm_pending_swaps", "W-B-SOL.json", { signature: "swapLive", lastValidBlockHeight: 1000 });
  put("dlmm_pending_swaps", "W-C-SOL.json", { signature: "swapConfirmed", lastValidBlockHeight: 100 });
  put("dlmm_pending_swaps", "W-D-SOL.json.route", { position: "X", dex: "Hadron", failed_at: 1, expires_at: 301 });
  put("dlmm_pending_swaps", "W-E-SOL.json.123.tmp", "partial"); // never touched
  put("dlmm_pending_swaps", "W-F-SOL.json", "{torn");
  put("dlmm_pending_deploys", "W.json", { position: "D", signature: "deployOk", lastValidBlockHeight: 100 });
  put("dlmm_pending_closes", "CLOSED.json", { signature: "closeOk", lastValidBlockHeight: 100, raw: "AA==" });
  put("dlmm_pending_closes", "OPEN.json", { signature: "closeOpen", lastValidBlockHeight: 100, raw: "AA==" });
  put("dlmm_settlements", "S.json", { position: "S", mint: "DUST", state: "deferred", reason: "swap_no_route",
    remaining_raw: "36", last_attempt: NOW - 60 });
  put("dlmm_settlements", "Q.json", { position: "Q", mint: "LIVE", state: "pending", last_attempt: NOW - 60 });
  const statuses = { swapOk: OK, swapLive: null, swapConfirmed: { confirmationStatus: "confirmed", err: null },
    deployOk: OK, closeOk: OK, closeOpen: OK };
  const calls = [];
  const deps = { memoriesDir: mem, fs, path,
    finalizedHeight: async () => 500,
    signatureStatuses: async sigs => { calls.push(["status", sigs.length]); return sigs.map(s => statuses[s]); },
    positionExists: async a => { calls.push(["exists", a]); return a === "OPEN"; },
    walletBalanceRaw: async mint => { calls.push(["balance", mint]); return "36"; },
    quote: async (mint, raw) => { calls.push(["quote", mint, raw]); return { verdict: "no_route" }; },
    closedAt: p => (p === "S" ? NOW - 20 * 86400 : null) };

  const before = fs.readdirSync(mem).sort();
  const dry = await reconcileStaleMarkers({ now: NOW }, deps);
  const by = Object.fromEntries(dry.markers.map(r => [r.marker, r]));
  assert.equal(dry.dry_run, true);
  assert.equal(by["dlmm_pending_swaps/W-A-SOL.json"].resolution, "landed_finalized");
  assert.equal(by["dlmm_pending_swaps/W-B-SOL.json"].resolution, "blockhash_live");
  assert.equal(by["dlmm_pending_swaps/W-C-SOL.json"].resolution, "not_finalized");
  assert.equal(by["dlmm_pending_swaps/W-D-SOL.json.route"].resolution, "route_exclusion_expired");
  assert.equal(by["dlmm_pending_swaps/W-F-SOL.json"].resolution, "invalid_marker");
  assert.equal(by["dlmm_pending_swaps/W-E-SOL.json.123.tmp"], undefined);
  assert.equal(by["dlmm_pending_deploys/W.json"].action, "archive");
  assert.equal(by["dlmm_pending_closes/CLOSED.json"].action, "archive");
  assert.equal(by["dlmm_pending_closes/OPEN.json"].resolution, "close_landed_position_open");
  assert.equal(by["dlmm_settlements/S.json"].resolution, "no_route_dust");
  assert.equal(by["dlmm_settlements/Q.json"].resolution, "not_deferred_dust");
  assert.equal(dry.archivable, 5);
  assert.equal(dry.archived, 0);
  // One batched status call; chain reads only where an offline rule passed.
  assert.deepEqual(calls.filter(c => c[0] === "status"), [["status", 6]]);
  assert.ok(!calls.some(c => c[1] === "LIVE" || c[1] === "Q"));
  // A dry run writes nothing.
  assert.deepEqual(fs.readdirSync(mem).sort(), before);
  assert.ok(fs.existsSync(path.join(mem, "dlmm_settlements", "S.json")));

  // A marker rewritten between read and move stays (its writer owns it again).
  const realRead = fs.readFileSync;
  let touched = false;
  const racyFs = { ...fs, readFileSync: (p, enc) => {
    const out = realRead(p, enc);
    if (!touched && String(p).endsWith(path.join("dlmm_pending_deploys", "W.json"))) {
      touched = true; // first read = classification; rewrite before the archive's re-read
      fs.writeFileSync(p, JSON.stringify({ position: "D2", signature: "deployOk", lastValidBlockHeight: 100 }));
    }
    return out;
  } };
  const run = await reconcileStaleMarkers({ execute: true, now: NOW }, { ...deps, fs: racyFs });
  const ran = Object.fromEntries(run.markers.map(r => [r.marker, r]));
  assert.equal(ran["dlmm_pending_deploys/W.json"].resolution, "changed_since_read");
  assert.equal(ran["dlmm_pending_deploys/W.json"].archived, false);
  assert.ok(fs.existsSync(path.join(mem, "dlmm_pending_deploys", "W.json")));
  assert.equal(run.archived, 4);
  const arch = path.join(mem, "archive", "markers");
  for (const [dir, file] of [["dlmm_pending_swaps", "W-A-SOL.json"], ["dlmm_pending_swaps", "W-D-SOL.json.route"],
                             ["dlmm_pending_closes", "CLOSED.json"], ["dlmm_settlements", "S.json"]]) {
    assert.ok(!fs.existsSync(path.join(mem, dir, file)), `${file} moved`);
    assert.ok(fs.existsSync(path.join(arch, dir, file)), `${file} archived`);
    const note = JSON.parse(fs.readFileSync(path.join(arch, dir, `${file}.resolution.json`), "utf8"));
    assert.equal(note.source, `${dir}/${file}`);
    assert.equal(note.archived_at, NOW);
  }
  const closeNote = JSON.parse(fs.readFileSync(path.join(arch, "dlmm_pending_closes", "CLOSED.json.resolution.json"), "utf8"));
  assert.equal(closeNote.position_exists, false);
  assert.equal(closeNote.signature, "closeOk");
  // Kept markers are untouched.
  for (const f of ["W-B-SOL.json", "W-C-SOL.json", "W-F-SOL.json", "W-E-SOL.json.123.tmp"]) {
    assert.ok(fs.existsSync(path.join(mem, "dlmm_pending_swaps", f)), `${f} kept`);
  }
  assert.ok(fs.existsSync(path.join(mem, "dlmm_pending_closes", "OPEN.json")));
  assert.ok(fs.existsSync(path.join(mem, "dlmm_settlements", "Q.json")));

  // Re-archiving a same-named marker never overwrites the earlier archive.
  put("dlmm_pending_swaps", "W-A-SOL.json", { signature: "swapOk", lastValidBlockHeight: 100 });
  const again = await reconcileStaleMarkers({ execute: true, now: NOW + 1 }, deps);
  assert.ok(again.markers.find(r => r.marker === "dlmm_pending_swaps/W-A-SOL.json").archived);
  assert.ok(fs.existsSync(path.join(arch, "dlmm_pending_swaps", `W-A-SOL.json.${NOW + 1}`)));

  // A status list of the wrong length measures nothing.
  put("dlmm_pending_swaps", "W-G-SOL.json", { signature: "swapOk", lastValidBlockHeight: 100 });
  const short = await reconcileStaleMarkers({ now: NOW }, { ...deps, signatureStatuses: async () => [] });
  assert.equal(short.markers.find(r => r.marker === "dlmm_pending_swaps/W-G-SOL.json").resolution, "status_unmeasured");

  // queued_at on the marker wins over the close journal.
  put("dlmm_settlements", "Y.json", { position: "Y", mint: "M2", state: "deferred", reason: "swap_no_route",
    remaining_raw: "5", last_attempt: NOW - 60, queued_at: NOW - 3600 });
  const young = await reconcileStaleMarkers({ now: NOW }, { ...deps, closedAt: () => NOW - 30 * 86400 });
  assert.equal(young.markers.find(r => r.marker === "dlmm_settlements/Y.json").resolution, "younger_than_24h");

  fs.rmSync(mem, { recursive: true, force: true });
  console.log("test_dlmm_stale_markers: ok");
})().catch(err => { console.error(err); process.exit(1); });
