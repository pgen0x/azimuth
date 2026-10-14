// Independent risk verification, never a realized return or an executable quote.
// Keep the proof/arithmetic dependency-free so regression checks need no RPC/SDK.
const fs = require("node:fs");
const path = require("node:path");

const SOL = "So11111111111111111111111111111111111111112";
const TOKEN_PROGRAMS = new Set(["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
  "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"]);
const SOURCE = "onchain_sol_inventory";
const address = value => value?.toString();
function check(condition, reason) {
  if (!condition) {
    const error = new Error(`Native risk mark unavailable: ${reason}`);
    error.riskMarkUnavailable = true;
    throw error;
  }
}
function raw(value, bits = 64) {
  const text = value?.toString();
  check(typeof text === "string" && /^(0|[1-9][0-9]*)$/.test(text), "missing or invalid raw amount");
  const result = BigInt(text);
  check(result < (1n << BigInt(bits)), "raw amount overflow");
  return result;
}

function loadInitialContext(profile, pool, position) {
  check([pool, position].every(v => typeof v === "string" && /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(v)),
    "invalid position or pool identity");
  const entry = JSON.parse(fs.readFileSync(path.join(profile, "memories", "dlmm_entries", `${position}.json`), "utf8"));
  check(entry.position === position && entry.pool === pool && entry.strategy === "sol_bidask"
    && typeof entry.sol_is_x === "boolean" && entry.base_mint !== SOL
    && /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(entry.base_mint), "unsupported entry provenance");
  check(typeof entry.size_sol === "number" && Number.isFinite(entry.size_sol) && entry.size_sol > 0
    && Number.isSafeInteger(Math.floor(entry.size_sol * 1e9))
    && entry[entry.sol_is_x ? "amount_x" : "amount_y"] === entry.size_sol
    && entry[entry.sol_is_x ? "amount_y" : "amount_x"] === 0, "entry was not funded only with SOL");
  check([entry.entry_bin, entry.bins_below, entry.bins_above].every(Number.isSafeInteger)
    && entry.bins_below >= 0 && entry.bins_above >= 0
    && entry.bins_below + entry.bins_above < 70, "unsupported position bounds");
  const events = fs.readFileSync(path.join(profile, "memories", "dlmm_transactions.jsonl"), "utf8")
    .split("\n").filter(line => line.trim()).map(JSON.parse).filter(row => row.position === position);
  const unique = new Map();
  for (const event of events) {
    check(event.kind === "deploy" && typeof event.signature === "string" && event.signature.length > 0
      && event.entry_id === entry.entry_id && typeof entry.entry_id === "string"
      && event.root_chain_id === entry.root_chain_id
      && /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(event.wallet), "modified or ambiguous funding history");
    const previous = unique.get(event.signature);
    check(!previous || JSON.stringify(previous) === JSON.stringify(event), "conflicting submission evidence");
    unique.set(event.signature, event);
  }
  check(unique.size === 1, "initial deposit is not unique");
  return {entry, submission: [...unique.values()][0]};
}

function initialDeposit(tx, context, binding) {
  const {entry, submission} = context;
  const {definition, initializeDefinitions, decode, programId} = binding;
  check(tx?.meta?.err === null && tx.transaction?.signatures?.[0] === submission.signature,
    "successful deposit transaction missing");
  const message = tx.transaction.message;
  check(address(message?.accountKeys?.[0]?.pubkey) === submission.wallet
    && message.accountKeys[0].signer === true, "deposit wallet mismatch");
  const tokenX = entry.sol_is_x ? SOL : entry.base_mint, tokenY = entry.sol_is_x ? entry.base_mint : SOL;
  check(binding.tokenX === tokenX && binding.tokenY === tokenY, "pool mint mismatch");
  const owned = new Map();
  for (const b of [...(tx.meta.preTokenBalances || []), ...(tx.meta.postTokenBalances || [])]) {
    if (b.owner === submission.wallet) owned.set(address(message.accountKeys[b.accountIndex]?.pubkey), b.mint);
  }
  const inners = tx.meta.innerInstructions;
  check(Array.isArray(inners), "deposit inner instructions missing");
  for (const ix of [...message.instructions, ...inners.flatMap(g => g.instructions)]) {
    const info = ix.parsed?.info;
    if (TOKEN_PROGRAMS.has(address(ix.programId)) && ix.parsed?.type === "initializeAccount3"
      && info.owner === submission.wallet) owned.set(info.account, info.mint);
  }
  let deposited = null, initialized = false;
  for (const [index, ix] of message.instructions.entries()) {
    if (address(ix.programId) !== programId) continue;
    const bytes = Buffer.from(decode(ix.data));
    const discriminator = bytes.subarray(0, 8);
    const init = initializeDefinitions.find(d => discriminator.equals(Buffer.from(d.discriminator)));
    if (init) {
      const accounts = Object.fromEntries(init.accounts.map((a, n) => [a.name, address(ix.accounts[n])]));
      check(!initialized && deposited === null && accounts.position === entry.position
        && accounts.lb_pair === entry.pool && accounts.owner === submission.wallet
        && accounts.payer === submission.wallet, "position initialization mismatch");
      if (init.name === "initialize_position_pda") {
        const lower = entry.entry_bin - entry.bins_below;
        const width = entry.bins_below + entry.bins_above + 1;
        check(accounts.base === submission.wallet && bytes.length === 16
          && bytes.readInt32LE(8) === lower && bytes.readInt32LE(12) === width,
          "PDA initialization base or bounds mismatch");
      }
      initialized = true;
      continue;
    }
    check(initialized && discriminator.equals(Buffer.from(definition.discriminator)) && deposited === null,
      "unsupported or repeated liquidity instruction");
    const accounts = Object.fromEntries(definition.accounts.map((a, n) => [a.name, address(ix.accounts[n])]));
    check(accounts.position === entry.position && accounts.lb_pair === entry.pool
      && accounts.sender === submission.wallet && accounts.token_x_mint === tokenX
      && accounts.token_y_mint === tokenY && accounts.reserve_x === binding.reserveX
      && accounts.reserve_y === binding.reserveY, "deposit accounts mismatch");
    check(bytes.length >= 24 && bytes.readBigUInt64LE(entry.sol_is_x ? 16 : 8) === 0n
      && bytes.readBigUInt64LE(entry.sol_is_x ? 8 : 16) === BigInt(Math.floor(entry.size_sol * 1e9)),
      "deposit instruction was not SOL-only");
    const groups = inners.filter(g => g.index === index);
    check(groups.length === 1, "deposit transfer group missing or duplicated");
    const amounts = {x: 0n, y: 0n}, seen = {x: false, y: false};
    for (const inner of groups[0].instructions) {
      if (!TOKEN_PROGRAMS.has(address(inner.programId))) continue;
      check(inner.parsed?.type === "transferChecked" && inner.stackHeight === 2,
        "unsupported deposit token instruction");
      const info = inner.parsed.info;
      const side = info.mint === tokenX ? "x" : info.mint === tokenY ? "y" : null;
      check(side && !seen[side] && info.authority === submission.wallet
        && info.source === accounts[`user_token_${side}`]
        && info.destination === accounts[`reserve_${side}`]
        && owned.get(info.source) === info.mint
        && address(inner.programId) === accounts[`token_${side}_program`], "deposit transfer ownership mismatch");
      check(info.mint !== SOL || info.tokenAmount?.decimals === 9, "SOL decimals mismatch");
      amounts[side] += raw(info.tokenAmount?.amount);
      seen[side] = true;
    }
    check(seen.x && seen.y && amounts[entry.sol_is_x ? "y" : "x"] === 0n,
      "deposit transfer evidence incomplete or not SOL-only");
    deposited = amounts[entry.sol_is_x ? "x" : "y"];
    check(deposited > 0n && deposited <= BigInt(Math.floor(entry.size_sol * 1e9)), "invalid SOL deposit");
  }
  check(deposited !== null, "liquidity deposit missing");
  return deposited;
}

function onlyInitialSignature(history, context) {
  check(Array.isArray(history) && history.length === 1 && history[0].err === null
    && history[0].signature === context.submission.signature
    && ["confirmed", "finalized"].includes(history[0].confirmationStatus), "position has additional or unknown transactions");
}

// Optional allocation evidence, using the funding transaction already verified
// above. A decode failure must not disable the independent native risk mark.
function initialFundingAllocation(tx, context, binding, deposit) {
  try {
    const {entry, submission} = context;
    check(entry.sol_is_x === false && entry.bins_above === 0, "unsupported allocation orientation");
    check(Number.isSafeInteger(entry.entry_bin) && Number.isSafeInteger(entry.bins_below)
      && entry.bins_below >= 0 && entry.bins_below < 70, "unsupported allocation bounds");
    check(tx.meta.err === null && tx.transaction.signatures[0] === submission.signature
      && Number.isSafeInteger(tx.blockTime) && tx.blockTime > 0, "allocation funding unavailable");
    const instructions = tx.transaction.message.instructions;
    const adds = instructions.map((ix, index) => ({ix, index})).filter(({ix}) =>
      address(ix.programId) === binding.programId
      && Buffer.from(binding.decode(ix.data)).subarray(0, 8).equals(Buffer.from(binding.definition.discriminator)));
    check(adds.length === 1, "ambiguous allocation instruction");
    const {ix, index} = adds[0], decoded = binding.decodeInstruction(ix.data);
    const p = decoded?.data?.liquidityParameter, s = p?.strategyParameters;
    const lower = entry.entry_bin-entry.bins_below, upper = entry.entry_bin;
    check(decoded?.name === "addLiquidityByStrategy2" && raw(p.amountX) === 0n
      && raw(p.amountY) === BigInt(Math.floor(entry.size_sol*1e9))
      && p.activeId === entry.entry_bin && Number.isSafeInteger(p.maxActiveBinSlippage)
      && p.maxActiveBinSlippage >= 0 && p.maxActiveBinSlippage <= 10000
      && s.minBinId === lower && s.maxBinId === upper
      && Object.keys(s.strategyType).join() === "bidAskImBalanced"
      && Array.isArray(s.parameteres) && s.parameteres.length === 64
      && s.parameteres.every(v => v === 0), "unsupported allocation strategy");
    const groups = tx.meta.innerInstructions.filter(g => g.index === index);
    check(groups.length === 1, "allocation event group unavailable");
    const events = [];
    for (const inner of groups[0].instructions) {
      if (address(inner.programId) !== binding.programId || typeof inner.data !== "string") continue;
      const bytes = Buffer.from(binding.decode(inner.data));
      // Anchor's EVENT_IX_TAG, encoded as a little-endian u64 for emit_cpi!.
      check(inner.stackHeight === 2 && bytes.subarray(0, 8).equals(Buffer.from("e445a52e51cb9a1d", "hex")),
        "unsupported allocation self-CPI");
      const event = binding.decodeEvent(bytes.subarray(8).toString("base64"));
      check(event && ["addLiquidity", "compositionFee"].includes(event.name), "unknown allocation event");
      events.push(event);
    }
    const additions = events.filter(e => e.name === "addLiquidity");
    check(additions.length === 1, "allocation event missing or repeated");
    const add = additions[0].data, active = add.activeBinId;
    check(address(add.position) === entry.position && address(add.lbPair) === entry.pool
      && address(add.from) === submission.wallet && Number.isSafeInteger(active)
      && Math.abs(active-entry.entry_bin) <= p.maxActiveBinSlippage
      && active >= lower
      && Array.isArray(add.amounts) && add.amounts.length === 2
      && raw(add.amounts[0]) === 0n && raw(add.amounts[1]) === deposit, "allocation event mismatch");
    const anchor = Math.min(active, upper);
    const budget = raw(p.amountY), count = BigInt(anchor-lower+1), totalWeight = count*(count+1n)/2n;
    const bins = [];
    let total = 0n, feeTotal = 0n, protocolTotal = 0n;
    for (let id = lower; id <= upper; id++) {
      const amount = id <= anchor ? budget*BigInt(anchor-id+1)/totalWeight : 0n;
      bins.push({id, sol_deposit_lamports: amount.toString(), composition_fee_lamports: "0", protocol_fee_lamports: "0"});
      total += amount;
    }
    check(total === deposit && bins.length <= 70, "allocation total disagrees with transfer");
    const charged = new Set();
    for (const {data: fee} of events.filter(e => e.name === "compositionFee")) {
      check(address(fee.from) === submission.wallet && fee.binId === active && !charged.has(fee.binId)
        && raw(fee.tokenXFeeAmount) === 0n && raw(fee.protocolTokenXFeeAmount) === 0n,
        "composition event mismatch");
      const amount = raw(fee.tokenYFeeAmount), protocol = raw(fee.protocolTokenYFeeAmount), bin = bins[fee.binId-lower];
      check(protocol <= amount && amount <= BigInt(bin.sol_deposit_lamports), "invalid composition cost");
      bin.composition_fee_lamports = amount.toString(); bin.protocol_fee_lamports = protocol.toString();
      feeTotal += amount; protocolTotal += protocol; charged.add(fee.binId);
    }
    return {version: 1, wallet: submission.wallet, signature: submission.signature, block_time: tx.blockTime,
      requested_lamports: budget.toString(), deposit_lamports: deposit.toString(), executed_active_bin: active,
      max_active_bin_slippage: p.maxActiveBinSlippage,
      composition_fee_lamports: feeTotal.toString(), protocol_fee_lamports: protocolTotal.toString(), bins,
      basis: "decoded_SOL_only_BidAsk_funding; inferred_integer_bin_allocations; protocol_fee_is_subset"};
  } catch { return null; }
}

function markInventory(context, native, data, lbPair, deposit) {
  const {entry, submission} = context;
  check(address(native.lbPair) === entry.pool && address(native.owner) === submission.wallet
    && address(data?.owner) === submission.wallet, "position owner or pool mismatch");
  const lower = entry.entry_bin - entry.bins_below, upper = entry.entry_bin + entry.bins_above;
  check(native.lowerBinId === lower && native.upperBinId === upper
    && data.lowerBinId === lower && data.upperBinId === upper, "position bounds changed");
  check([native.feeOwner, data.feeOwner].every(v => [submission.wallet, "11111111111111111111111111111111"].includes(address(v))),
    "fees belong to another owner");
  check([native.totalClaimedFeeXAmount, native.totalClaimedFeeYAmount,
    data.totalClaimedFeeXAmount, data.totalClaimedFeeYAmount,
    data.rewardOne, data.rewardTwo].every(v => raw(v) === 0n), "claimed fees or non-SOL rewards require another basis");
  check(Array.isArray(native.liquidityShares) && native.liquidityShares.length >= upper-lower+1
    && Array.isArray(data.positionBinData) && data.positionBinData.length === upper-lower+1,
    "incomplete position bin coverage");
  let x = 0n, y = 0n, fx = 0n, fy = 0n, fundedBins = 0;
  const observedBins = [];
  for (const [index, bin] of data.positionBinData.entries()) {
    const share = raw(native.liquidityShares[index], 128);
    check(bin.binId === lower + index && raw(bin.positionLiquidity, 128) === share,
      "position share coverage mismatch");
    // The SDK substitutes empty bins when an RPC bin-array account is missing.
    // A funded share with zero supply must never become a fabricated -100% mark.
    check(share === 0n || raw(bin.binLiquidity, 128) > 0n, "funded bin array unavailable");
    if (share > 0n) fundedBins++;
    x += raw(bin.positionXAmount); y += raw(bin.positionYAmount);
    fx += raw(bin.positionFeeXAmount); fy += raw(bin.positionFeeYAmount);
    observedBins.push({id: bin.binId, liquidity_raw: share.toString(),
      x_raw: raw(bin.positionXAmount).toString(), y_raw: raw(bin.positionYAmount).toString(),
      fee_x_raw: raw(bin.positionFeeXAmount).toString(), fee_y_raw: raw(bin.positionFeeYAmount).toString()});
  }
  check(fundedBins > 0 && raw(data.totalXAmount) === x && raw(data.totalYAmount) === y
    && raw(data.feeX) === fx && raw(data.feeY) === fy, "inventory totals disagree");
  const netX = raw(data.totalXAmountExcludeTransferFee), netY = raw(data.totalYAmountExcludeTransferFee);
  const feeX = raw(data.feeXExcludeTransferFee), feeY = raw(data.feeYExcludeTransferFee);
  check(netX <= x && netY <= y && feeX <= fx && feeY <= fy, "invalid transfer-fee adjustment");
  const active = lbPair.activeId, step = lbPair.binStep;
  check(Number.isSafeInteger(active) && Math.abs(active) <= 100000
    && Number.isSafeInteger(step) && step > 0 && step <= 10000, "unsupported active-bin price");
  let a = BigInt(10000 + step), b = 10000n;
  let g = a, h = b;
  while (h) [g, h] = [h, g % h];
  a /= g; b /= g;
  let numerator = a ** BigInt(Math.abs(active)), denominator = b ** BigInt(Math.abs(active));
  if (active < 0) [numerator, denominator] = [denominator, numerator];
  if (entry.sol_is_x) [numerator, denominator] = [denominator, numerator];
  const value = (vx, vy) => entry.sol_is_x ? vx * denominator + vy * numerator : vy * denominator + vx * numerator;
  const principal = value(netX, netY), fees = value(feeX, feeY);
  const ceil = n => (n + denominator - 1n) / denominator;
  const totalUpper = ceil(principal + fees);
  check(deposit > 0n && deposit <= BigInt(Number.MAX_SAFE_INTEGER)
    && totalUpper <= BigInt(Number.MAX_SAFE_INTEGER), "mark exceeds safe SOL range");
  const pnl = Number(totalUpper - deposit) / 1e9;
  return {success: true, source: SOURCE, position: entry.position, pool: entry.pool,
    observed_at: Date.now() / 1000, pnl_currency: "SOL", pnl_sol: pnl,
    pnl_pct: Number(totalUpper - deposit) / Number(deposit) * 100,
    current_value_sol: Number(ceil(principal)) / 1e9, unclaimed_fees_sol: Number(ceil(fees)) / 1e9,
    deposit_lamports: deposit.toString(), value_lamports_upper: totalUpper.toString(),
    active_bin: active, lower_bin: lower, upper_bin: upper, in_range: active >= lower && active <= upper,
    funding_signature: submission.signature, funded_bins: fundedBins,
    inventory: {version: 1, wallet: submission.wallet,
      token_x_mint: entry.sol_is_x ? SOL : entry.base_mint,
      token_y_mint: entry.sol_is_x ? entry.base_mint : SOL,
      net_x_raw: netX.toString(), net_y_raw: netY.toString(),
      net_fee_x_raw: feeX.toString(), net_fee_y_raw: feeY.toString()},
    bin_observation: {version: 1, bin_step: step, sol_is_x: entry.sol_is_x, bins: observedBins},
    basis: "native inventory and unclaimed fees at active-bin spot, rounded up; actual initial SOL transfer; excludes rent, network and exit costs"};
}

module.exports = {SOL, SOURCE, check, loadInitialContext, initialDeposit, initialFundingAllocation, onlyInitialSignature, markInventory};
