// Offline: node assets/skill/scripts/test_dlmm_legacy_bags.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const bags = require("./dlmm_legacy_bags");
const { liquidateLegacyBags, selectCandidates, quoteCandidates, readMarkers, parseArgs, SOL_MINT } = bags;

const OWNER = "owner-wallet", RENT = 2039280;
const acct = (pubkey, mint, raw, { decimals = 6, program = "spl", lamports = RENT, closable = true } = {}) =>
  ({ pubkey, account: { owner: { toString: () => program }, lamports, closable,
    data: { parsed: { info: { mint, tokenAmount: { amount: raw, decimals } } } } } });
const ataOf = (mint, program) => program === "spl" || program === "t22" ? `ata-${mint}` : null;
const canClose = (account, owner, raw) => account.closable && owner === OWNER
  && account.data.parsed.info.tokenAmount.amount === raw;
const noSets = { positionMints: new Set(), settlementMints: new Set() };

(async () => {
  // --- readMarkers: pending submissions block, settlements claim their mint.
  const mem = fs.mkdtempSync(path.join(os.tmpdir(), "legacy-bags-"));
  try {
    assert.deepEqual(readMarkers(mem, 100, fs, path).blocked, []);
    const put = (dir, file, body) => {
      fs.mkdirSync(path.join(mem, dir), { recursive: true });
      fs.writeFileSync(path.join(mem, dir, file), typeof body === "string" ? body : JSON.stringify(body));
    };
    put("dlmm_pending_swaps", "expired.json", { lastValidBlockHeight: 99 });
    put("dlmm_pending_swaps", "note.txt", "not a marker");
    assert.deepEqual(readMarkers(mem, 100, fs, path).blocked, []);
    put("dlmm_pending_swaps", "equal.json", { lastValidBlockHeight: 100 });
    assert.deepEqual(readMarkers(mem, 100, fs, path).blocked, ["pending dlmm_pending_swaps/equal.json"]);
    assert.equal(readMarkers(mem, null, fs, path).blocked.length, 2); // unknown height cannot prove expiry
    fs.rmSync(path.join(mem, "dlmm_pending_swaps", "equal.json"));
    for (const dir of ["dlmm_pending_deploys", "dlmm_pending_rent"]) {
      put(dir, "w.json", { lastValidBlockHeight: 150 });
      assert.deepEqual(readMarkers(mem, 100, fs, path).blocked, [`pending ${dir}/w.json`]);
      put(dir, "w.json", { signature: "s" }); // no expiry height: still pending
      assert.deepEqual(readMarkers(mem, 100, fs, path).blocked, [`pending ${dir}/w.json`]);
      put(dir, "w.json", "{broken");
      assert.deepEqual(readMarkers(mem, 100, fs, path).blocked, [`unreadable ${dir}/w.json`]);
      fs.rmSync(path.join(mem, dir), { recursive: true });
    }
    put("dlmm_settlements", "pos.json", { position: "pos", mint: "settling-mint" });
    let m = readMarkers(mem, 100, fs, path);
    assert.deepEqual(m.blocked, []); assert.deepEqual([...m.settlementMints], ["settling-mint"]);
    put("dlmm_settlements", "bad.json", "{");
    put("dlmm_settlements", "blank.json", { position: "x" });
    m = readMarkers(mem, 100, fs, path);
    assert.deepEqual(m.blocked, ["unreadable dlmm_settlements/bad.json", "mintless dlmm_settlements/blank.json"]);
  } finally {
    fs.rmSync(mem, { recursive: true, force: true });
  }

  // --- selectCandidates: every exclusion, and zero balances are ignored.
  const accounts = [
    acct("ata-good", "good", "500"), acct("ata-zero", "zero", "0"),
    acct(`ata-${SOL_MINT}`, SOL_MINT, "7"), acct("ata-live", "live", "5"), acct("ata-settling", "settling", "5"),
    acct("ata-split", "split", "5"), acct("other-split", "split", "1"), acct("ata-split0", "split0", "5"),
    acct("other-split0", "split0", "0"), acct("loose", "loose", "5"), acct("ata-weird", "weird", "5", { program: "foreign" }),
    acct("ata-frozen", "frozen", "5", { closable: false }), acct("ata-nodec", "nodec", "5", { decimals: null }),
    acct("ata-t22", "t22", "9", { program: "t22" }),
  ];
  const sel = selectCandidates(accounts, { owner: OWNER, positionMints: new Set(["live"]),
    settlementMints: new Set(["settling"]), ataOf, canClose });
  assert.deepEqual(sel.eligible.map(e => e.account), ["ata-good", "ata-split0", "ata-t22"]);
  assert.deepEqual(sel.eligible[0], { account: "ata-good", mint: "good", raw: "500", decimals: 6, program: "spl", rent_lamports: RENT });
  assert.deepEqual(Object.fromEntries(sel.skipped.map(s => [s.account, s.reason])), {
    [`ata-${SOL_MINT}`]: "sol", "ata-live": "open_position", "ata-settling": "settlement",
    "ata-split": "split_inventory", "other-split": "split_inventory", loose: "not_ata", "ata-weird": "not_ata",
    "ata-frozen": "unsupported_account", "ata-nodec": "unsupported_account",
  });
  assert.equal(selectCandidates(accounts, { owner: OWNER, ...noSets, canClose,
    ataOf: () => { throw new Error("bad mint"); } }).eligible.length, 0);

  // --- quoteCandidates: half-rent and fee boundaries, pacing, hint order, stops.
  const cand = (account, rent = RENT) => ({ account, mint: `m-${account}`, raw: "1", decimals: 6, program: "spl", rent_lamports: rent });
  const sleeps = [], asked = [];
  const deps = (table) => ({ sleep: async ms => { sleeps.push(ms); }, quote: async mint => { asked.push(mint); return table[mint]; } });
  const half = RENT / 2;
  let q = await quoteCandidates([cand("at-half"), cand("over-half"), cand("big"), cand("nr"), cand("tiny", 10000), cand("tiny-ok", 10000)],
    deps({ "m-at-half": { lamports: BigInt(half) }, "m-over-half": { lamports: BigInt(half + 1) }, "m-big": { lamports: 5000000n },
      "m-nr": { verdict: "no_route" }, "m-tiny": { lamports: 10000n }, "m-tiny-ok": { lamports: 10001n } }));
  assert.deepEqual(q.sellable.map(s => [s.account, s.quote_lamports]), [["big", 5000000], ["over-half", half + 1], ["tiny-ok", 10001]]);
  assert.deepEqual(Object.fromEntries(q.skipped.map(s => [s.account, s.reason])),
    { "at-half": "dust_for_rent_timer", nr: "no_route", tiny: "below_fee" });
  assert.equal(q.quotes, 6); assert.deepEqual(sleeps, Array(5).fill(2100)); assert.equal(q.stopped, null);
  sleeps.length = asked.length = 0;
  q = await quoteCandidates([cand("a"), cand("b"), cand("c")], deps({ "m-c": { verdict: "rate_limited" }, "m-a": { lamports: 5000000n } }),
    new Set(["c"]));
  assert.deepEqual(asked, ["m-c"]); assert.equal(q.stopped, "rate_limited"); assert.equal(q.sellable.length, 0);
  sleeps.length = asked.length = 0;
  q = await quoteCandidates(Array.from({ length: 20 }, (_, i) => cand(`x${i}`)), deps({}));
  assert.equal(q.quotes, bags.MAX_QUOTES); assert.equal(q.stopped, "quote_budget");
  assert.equal(q.skipped.every(s => s.reason === "unavailable"), true);

  // --- liquidateLegacyBags orchestration.
  const world = (over = {}) => {
    const w = { reads: 0, locks: 0, releases: 0, swaps: [], sleeps: [], blockedAfter: Infinity, mutate: null,
      accounts: [acct("ata-a", "a", "10"), acct("ata-b", "b", "20"), acct("ata-c", "c", "30"), acct("ata-d", "d", "1")],
      quotes: { a: 3000000n, b: 9000000n, c: 6000000n, d: 100n }, swapResult: () => ({ success: true, txHash: "sig", outputAmount: "1" }),
      ...over };
    w.deps = {
      owner: OWNER, ataOf, canClose,
      readState: async () => {
        w.reads++;
        if (w.mutate) w.mutate(w);
        return { blocked: w.reads > w.blockedAfter ? ["pending dlmm_pending_rent/x.json"] : (w.blocked || []),
          positionMints: w.positionMints || new Set(), settlementMints: new Set(), accounts: w.accounts };
      },
      quote: async mint => ({ lamports: w.quotes[mint] }),
      sleep: async ms => { w.sleeps.push(ms); },
      lock: async () => { w.locks++; return async () => { w.releases++; }; },
      swap: async item => { w.swaps.push(item); return w.swapResult(item); },
    };
    return w;
  };

  // Dry run: plan only. No lock, no swap, one state read.
  let w = world(), r = await liquidateLegacyBags({}, w.deps);
  assert.equal(r.dry_run, true); assert.equal(r.success, true);
  assert.deepEqual(r.plan.map(p => p.mint), ["b", "c", "a"]);
  assert.equal(r.planned_quote_lamports, 18000000); assert.equal(r.planned_rent_lamports, 3 * RENT);
  assert.equal(r.sellable_beyond_max, 0); assert.deepEqual(r.skipped.map(s => s.reason), ["dust_for_rent_timer"]);
  assert.deepEqual([w.locks, w.swaps.length, w.reads], [0, 0, 1]);
  // DRY_RUN=true wins over --execute; a blocked dry run still prints the plan.
  w = world({ blocked: ["pending dlmm_pending_swaps/x.json"] });
  r = await liquidateLegacyBags({ execute: true, dryRunEnv: true }, w.deps);
  assert.equal(r.dry_run, true); assert.equal(r.success, true); assert.equal(r.plan.length, 3);
  assert.deepEqual(r.blocked, ["pending dlmm_pending_swaps/x.json"]); assert.deepEqual([w.locks, w.swaps.length], [0, 0]);
  // Execute refuses a blocked state before locking.
  r = await liquidateLegacyBags({ execute: true }, w.deps);
  assert.equal(r.success, false); assert.equal(r.stopped, "blocked"); assert.deepEqual([w.locks, w.swaps.length], [0, 0]);

  // Execute: highest quote first, full raw balance, paced, --max honored, lock released once.
  w = world(); r = await liquidateLegacyBags({ execute: true, max: 2 }, w.deps);
  assert.equal(r.success, true); assert.equal(r.dry_run, false); assert.equal(r.sellable_beyond_max, 1);
  assert.deepEqual(w.swaps.map(s => [s.mint, s.raw, s.decimals]), [["b", "20", 6], ["c", "30", 6]]);
  assert.deepEqual(r.sales.map(s => [s.mint, s.success, s.txHash]), [["b", true, "sig"], ["c", true, "sig"]]);
  assert.deepEqual([w.locks, w.releases, w.reads], [1, 1, 3]); // one selection read + one re-read per sale
  assert.deepEqual(w.sleeps, Array(3 + 2).fill(2100)); // 3 between 4 quotes, then one before each sale's own quote

  // Stop on the first failure of any kind; the lock is always released.
  for (const swapResult of [() => ({ success: false, aborted: true, reason: "price_impact_exceeded" }),
    () => ({ success: false, pending: true, txHash: "unsure" }), () => ({ success: true, dryRun: true }),
    () => { throw new Error("SWAP BUSY: another matching swap is active for this wallet"); }, () => undefined]) {
    w = world({ swapResult }); r = await liquidateLegacyBags({ execute: true }, w.deps);
    assert.equal(r.success, false); assert.equal(r.stopped, "sale_failed");
    assert.equal(w.swaps.length, 1); assert.equal(r.sales.length, 1); assert.equal(r.sales[0].success, false);
    assert.deepEqual([w.locks, w.releases], [1, 1]);
  }
  w = world({ swapResult: () => { throw new Error("SWAP BUSY"); } });
  r = await liquidateLegacyBags({ execute: true }, w.deps);
  assert.equal(r.sales[0].error, "SWAP BUSY");
  w = world({ swapResult: () => ({ success: false, pending: true, txHash: "unsure" }) });
  r = await liquidateLegacyBags({ execute: true }, w.deps);
  assert.equal(r.sales[0].pending, true); assert.equal(r.sales[0].txHash, "unsure");

  // State changes under the lock stop the run before that sale.
  const changes = [
    ["blocked", w2 => { w2.blockedAfter = 1; }],
    ["inventory_changed", w2 => { w2.mutate = x => { if (x.reads === 2) x.accounts[1] = acct("ata-b", "b", "21"); }; }],
    ["inventory_changed", w2 => { w2.mutate = x => { if (x.reads === 2) x.positionMints = new Set(["b"]); }; }],
    ["inventory_changed", w2 => { w2.mutate = x => { if (x.reads === 2) x.accounts.push(acct("other-b", "b", "1")); }; }],
  ];
  for (const [stopped, arrange] of changes) {
    w = world(); arrange(w); r = await liquidateLegacyBags({ execute: true }, w.deps);
    assert.equal(r.success, false); assert.equal(r.stopped, stopped); assert.equal(w.swaps.length, 0);
    assert.deepEqual([w.locks, w.releases], [1, 1]);
  }
  // A change after the first sale stops before the second.
  w = world(); w.mutate = x => { if (x.reads === 3) x.accounts[2] = acct("ata-c", "c", "0"); };
  r = await liquidateLegacyBags({ execute: true }, w.deps);
  assert.deepEqual(w.swaps.map(s => s.mint), ["b"]); assert.equal(r.stopped, "inventory_changed");
  // Nothing sellable: execute takes no lock.
  w = world({ quotes: {} }); r = await liquidateLegacyBags({ execute: true }, w.deps);
  assert.equal(r.success, true); assert.deepEqual([w.locks, w.swaps.length], [0, 0]);

  await assert.rejects(liquidateLegacyBags({ max: 0 }, world().deps), /--max/);
  await assert.rejects(liquidateLegacyBags({ max: 1.5 }, world().deps), /--max/);

  // --- CLI parsing.
  assert.deepEqual(parseArgs([]), { execute: false, max: bags.DEFAULT_MAX_SALES });
  assert.deepEqual(parseArgs(["--max", "3", "--execute"]), { execute: true, max: 3 });
  for (const bad of [["--max"], ["--max", "0"], ["--max", "-1"], ["--max", "2x"], ["--force"], ["3"]]) {
    assert.throws(() => parseArgs(bad), /Usage: liquidate-legacy-bags/);
  }
  console.log("legacy bag selection, exclusions, dry-run, pacing and stop rules passed");
})().catch(err => { console.error(err); process.exitCode = 1; });
