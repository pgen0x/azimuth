// Legacy bag liquidation: an operator command, not a timer.
//
// Token balances left behind before the settlement queue existed (2026-10-01)
// sit in ATAs the rent timer will never touch: dust maintenance only burns a
// balance quoted at or below half the account's rent, and these quote above
// it. This sells each one in full through the ordinary swapToken path and
// leaves the now-empty account for the rent timer's next close.
//
// Everything with RPC, signer or lock side effects is injected (deps), so the
// selection and the stop rules are testable offline. A dry run reads only:
// no lock, no file write, no swap.
"use strict";

const SOL_MINT = "So11111111111111111111111111111111111111112";
const QUOTE_GAP_MS = 2100;        // keyless Jupiter pacing, same as the swap and dust paths
const MAX_QUOTES = 16;            // bounds one run's quote time to ~35s
const DEFAULT_MAX_SALES = 4;
const EST_FEE_LAMPORTS = 10000;   // selection-time estimate: base fee plus priority headroom
const MAX_IMPACT_PCT = 15;        // the monitor's settlement-swap cap
const PENDING_DIRS = ["dlmm_pending_swaps", "dlmm_pending_deploys", "dlmm_pending_rent"];

// Any unexpired (or unreadable) pending trade, deploy or rent submission
// blocks the whole run: its signed bytes can still land against the same
// inventory. Settlement markers do not block; they claim their mint.
function readMarkers(memoriesDir, finalizedHeight, fs, path) {
  const blocked = [], settlementMints = new Set();
  const list = dir => fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith(".json")).sort() : [];
  for (const name of PENDING_DIRS) {
    for (const file of list(path.join(memoriesDir, name))) {
      let marker;
      try { marker = JSON.parse(fs.readFileSync(path.join(memoriesDir, name, file), "utf8")); }
      catch { blocked.push(`unreadable ${name}/${file}`); continue; }
      if (!Number.isSafeInteger(marker?.lastValidBlockHeight) || !Number.isSafeInteger(finalizedHeight)
          || finalizedHeight <= marker.lastValidBlockHeight) blocked.push(`pending ${name}/${file}`);
    }
  }
  const settlements = path.join(memoriesDir, "dlmm_settlements");
  for (const file of list(settlements)) {
    let mint;
    try { mint = JSON.parse(fs.readFileSync(path.join(settlements, file), "utf8"))?.mint; }
    catch { blocked.push(`unreadable dlmm_settlements/${file}`); continue; }
    if (typeof mint !== "string" || !mint) blocked.push(`mintless dlmm_settlements/${file}`);
    else settlementMints.add(mint);
  }
  return { blocked, settlementMints };
}

// accounts: [{ pubkey: string, account: parsed token account }]. Zero
// balances are the rent timer's job and are ignored here.
function selectCandidates(accounts, { owner, positionMints, settlementMints, ataOf, canClose }) {
  const held = accounts.filter(a => /^[1-9]\d*$/.test(String(a.account?.data?.parsed?.info?.tokenAmount?.amount)));
  const perMint = new Map();
  for (const a of held) {
    const mint = a.account.data.parsed.info.mint;
    perMint.set(mint, (perMint.get(mint) || 0) + 1);
  }
  const eligible = [], skipped = [];
  for (const a of held) {
    const info = a.account.data.parsed.info, mint = info.mint, raw = info.tokenAmount.amount;
    const decimals = info.tokenAmount.decimals, program = a.account.owner?.toString();
    const skip = reason => skipped.push({ account: a.pubkey, mint, reason });
    if (mint === SOL_MINT) { skip("sol"); continue; }
    if (positionMints.has(mint)) { skip("open_position"); continue; }
    if (settlementMints.has(mint)) { skip("settlement"); continue; }
    // A swap sells from the ATA; a second account would survive the sale.
    if (perMint.get(mint) !== 1) { skip("split_inventory"); continue; }
    let ata = null;
    try { ata = ataOf(mint, program); } catch { /* An unknown program has no ATA. */ }
    if (ata !== a.pubkey) { skip("not_ata"); continue; }
    // Only an account the rent timer can close afterwards is worth emptying.
    if (!Number.isInteger(decimals) || !canClose(a.account, owner, raw)) { skip("unsupported_account"); continue; }
    eligible.push({ account: a.pubkey, mint, raw, decimals, program, rent_lamports: a.account.lamports });
  }
  return { eligible, skipped };
}

// Accounts the dust timer already quoted as worth keeping go first, so a
// small quote budget reaches the known bags before the long tail.
async function quoteCandidates(eligible, { quote, sleep }, hint = new Set(), maxQuotes = MAX_QUOTES) {
  const order = [...eligible].sort((a, b) => Number(hint.has(b.account)) - Number(hint.has(a.account)));
  const sellable = [], skipped = [];
  let quotes = 0, stopped = null;
  for (const c of order) {
    if (quotes >= maxQuotes) { stopped = "quote_budget"; break; }
    if (quotes++) await sleep(QUOTE_GAP_MS);
    const q = await quote(c.mint, c.raw);
    if (q?.lamports === undefined) {
      skipped.push({ account: c.account, mint: c.mint, reason: q?.verdict || "unavailable" });
      if (q?.verdict === "rate_limited") { stopped = "rate_limited"; break; }
      continue;
    }
    const lamports = BigInt(q.lamports);
    if (lamports * 2n <= BigInt(c.rent_lamports)) {
      skipped.push({ account: c.account, mint: c.mint, reason: "dust_for_rent_timer", quote_lamports: Number(lamports) });
    } else if (lamports - BigInt(EST_FEE_LAMPORTS) <= 0n) {
      skipped.push({ account: c.account, mint: c.mint, reason: "below_fee", quote_lamports: Number(lamports) });
    } else {
      sellable.push({ ...c, quote_lamports: Number(lamports) });
    }
  }
  sellable.sort((a, b) => b.quote_lamports - a.quote_lamports);
  return { sellable, skipped, quotes, stopped };
}

// deps: readState() -> { blocked, positionMints, settlementMints, accounts },
// owner, ataOf, canClose, quote, sleep, lock() -> release, swap(item) -> result.
async function liquidateLegacyBags({ execute = false, max = DEFAULT_MAX_SALES, dryRunEnv = false, hint } = {}, deps) {
  if (!Number.isSafeInteger(max) || max < 1) throw new Error("--max must be a positive integer");
  const live = execute && !dryRunEnv;
  const select = state => selectCandidates(state.accounts, { owner: deps.owner, positionMints: state.positionMints,
    settlementMints: state.settlementMints, ataOf: deps.ataOf, canClose: deps.canClose });
  const state = await deps.readState();
  const selected = select(state);
  const quoted = await quoteCandidates(selected.eligible, deps, hint);
  const plan = quoted.sellable.slice(0, max);
  const result = {
    success: true, dry_run: !live, blocked: state.blocked, quotes: quoted.quotes, quote_stopped: quoted.stopped,
    plan: plan.map(({ account, mint, raw, decimals, rent_lamports, quote_lamports }) =>
      ({ account, mint, raw, decimals, rent_lamports, quote_lamports })),
    planned_quote_lamports: plan.reduce((s, p) => s + p.quote_lamports, 0),
    planned_rent_lamports: plan.reduce((s, p) => s + p.rent_lamports, 0),
    sellable_beyond_max: quoted.sellable.length - plan.length,
    skipped: [...selected.skipped, ...quoted.skipped],
    sales: [],
  };
  if (!live) return result;
  if (state.blocked.length) return { ...result, success: false, stopped: "blocked" };
  if (!plan.length) return result;
  const release = await deps.lock();
  try {
    for (const item of plan) {
      // Re-read under the lock: a settlement, deploy or rent burn that started
      // after selection owns this inventory now.
      const now = await deps.readState();
      if (now.blocked.length) { result.success = false; result.stopped = "blocked"; result.blocked = now.blocked; break; }
      const current = select(now).eligible.find(e => e.account === item.account);
      if (!current || current.mint !== item.mint || current.raw !== item.raw) {
        result.success = false; result.stopped = "inventory_changed";
        result.sales.push({ account: item.account, mint: item.mint, success: false, reason: "inventory_changed" });
        break;
      }
      await deps.sleep(QUOTE_GAP_MS);
      let res;
      try { res = await deps.swap(item); }
      catch (err) { res = { success: false, error: err.message }; }
      result.sales.push({ account: item.account, mint: item.mint, raw: item.raw, success: res?.success === true && !res.dryRun,
        ...["txHash", "inputAmount", "outputAmount", "reason", "error", "pending", "aborted"]
          .reduce((o, k) => (res?.[k] === undefined ? o : { ...o, [k]: res[k] }), {}) });
      if (res?.success !== true || res.dryRun) { result.success = false; result.stopped = "sale_failed"; break; }
    }
  } finally {
    await release();
  }
  return result;
}

function parseArgs(args) {
  let execute = false, max = DEFAULT_MAX_SALES;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--execute") execute = true;
    else if (args[i] === "--max" && /^[1-9]\d*$/.test(args[i + 1] || "")) max = Number(args[++i]);
    else throw new Error("Usage: liquidate-legacy-bags [--execute] [--max N]");
  }
  return { execute, max };
}

module.exports = { liquidateLegacyBags, selectCandidates, quoteCandidates, readMarkers, parseArgs,
  SOL_MINT, QUOTE_GAP_MS, MAX_QUOTES, DEFAULT_MAX_SALES, EST_FEE_LAMPORTS, MAX_IMPACT_PCT };
