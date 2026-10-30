// Offline: node assets/skill/scripts/test_dlmm_executor.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
const { execFileSync } = require("node:child_process");
const source = fs.readFileSync(path.join(__dirname, "dlmm_executor.js"), "utf8");
const worker = process.argv[2];
const root = worker ? process.argv[3] : fs.mkdtempSync(path.join(os.tmpdir(), "dlmm-guards-"));
let reads = 0, sends = 0, builds = 0, minted = 0, height = 100, sendError = false, buildError = false;
let lastSlippage = null, lastMaxRetries = null;
let positions = [], confirmationError = false, signatureStatus = null;
let confirmTimeout = false, accountExists = true, failNextSend = false, sendFailed = false;
let candidateCreates = 0, candidateTradeChecks = 0, candidateTradeAfter = Infinity;
let candidateCanonicalReads = 0, candidateCanonicalError = false;
let pdaMode = null, pdaCalls = 0, pdaHistoryCancels = 0, lastSignedKeys = [], signCalls = 0;
const closeBytes = [];
const key = (value) => ({ toString: () => value });
const wallet = { publicKey: key(`test-wallet-${worker ? "swap" : process.pid}`) };
const transaction = () => ({ signature: Buffer.from([1]), sign(...signers) {signCalls++;lastSignedKeys=signers.map(s=>s.publicKey.toString());}, compileMessage() { return {}; }, serialize() { return Buffer.from(this.recentBlockhash); } });
const pool = {
  pubkey: key("pool"), lbPair: { tokenXMint: key("TOKEN"), tokenYMint: key("So11111111111111111111111111111111111111112"), binStep: 100 },
  program: { account: {
    positionV2: { all: async () => { reads++; return positions; } },
    lbPair: { fetch: async () => ({ tokenXMint: key("TOKEN"), tokenYMint: key("SOL") }) },
  } },
  claimSwapFee: async () => [],
  removeLiquidity: async () => transaction(),
  getActiveBin: async () => ({ binId: 0, price: "1" }), fromPricePerLamport: (x) => x,
  initializePositionAndAddLiquidityByStrategy: async (args) => {
    assert.equal(args.strategy.minBinId, -20); assert.equal(args.strategy.maxBinId, 0);
    lastSlippage = args.slippage; builds++; if (buildError) throw new Error("build failed"); return transaction();
  },
  createExtendedEmptyPosition: async () => [transaction()],
  addLiquidityByStrategyChunkable: async () => { throw new Error("wide add failed"); },
};
let reservePost = 300000000, reserveError = null, reserveChanged = false, reserveReads = 0;
class Connection {
  async getMultipleAccountsInfoAndContext() { throw new Error("unexpected account batch read"); }
  constructor(endpoint = "fake-rpc-1", options = {}) { this.rpcEndpoint = endpoint; this.rpcOptions = options; }
  async getBalanceAndContext() { return {context:{slot:10},value:300000000+(++reserveReads%2===0 && reserveChanged ? 1 : 0)}; }
  async simulateTransaction() { return {context:{slot:10},value:{err:reserveError,accounts:[{lamports:reservePost}]}}; }
  async getAccountInfo() { return accountExists ? {} : null; }
  async getBlockHeight() { return height; }
  async getSignatureStatuses(signatures, options) {
    assert.equal(options.searchTransactionHistory, true);
    // Confirmation reads can observe a successful mock broadcast immediately;
    // durable-marker reads use the explicitly configured historical status.
    const status = this.testConfirming && signatureStatus === null && !confirmTimeout && !sendFailed
      ? {confirmationStatus:"confirmed",err:confirmationError ? "chain error" : null} : signatureStatus;
    return { value: [status] };
  }
  async getLatestBlockhash() { return { blockhash: "exact-blockhash", lastValidBlockHeight: 150 }; }
  async sendRawTransaction(raw, options) {
    const event=JSON.parse(fs.readFileSync(path.join(root,"memories/dlmm_transactions.jsonl"),"utf8").trim().split("\n").at(-1));
    if (event.kind === "swap") {
      const pending=JSON.parse(fs.readFileSync(path.join(root,'memories/dlmm_pending_swaps',
        `${event.wallet}-${event.swap_quote.input_mint}-${event.swap_quote.output_mint}.json`)));
      assert.equal(pending.signature,event.signature);assert.equal(pending.blockhash,raw.toString());
      assert.equal(pending.lastValidBlockHeight,event.lastValidBlockHeight);
      assert.equal(event.swap_quote.in_amount,"100000000");
      assert.equal(typeof event.swap_quote.out_amount,"string");
      assert.equal(typeof event.swap_quote.observed_at,"number");
      assert.equal(event.swap_quote.unrelatedDebug,undefined);
    }
    sends++; closeBytes.push(raw.toString("hex")); sendFailed = failNextSend || sendError; if (failNextSend) { failNextSend = false; throw new Error("429 max usage reached"); } lastMaxRetries = options.maxRetries; assert.equal(raw.toString(), "exact-blockhash"); if (sendError) throw new Error("timeout after send"); return "sig";
  }
  async confirmTransaction() { throw new Error("WebSocket confirmation must not be called"); }
}
const signatureStatusQuery = Connection.prototype.getSignatureStatuses;
const rentInstructions = [];
class RentTransaction {
  constructor() { Object.assign(this, transaction()); }
  add(instruction) { rentInstructions.push(instruction); return this; }
  compileMessage() { return {}; }
}
let swapSigns = 0; // swap transactions signed, so refused paths can prove 'not signed'
let lastSignedMessageHash = null; // sha256 of the message actually signed
class SwapTransaction {
  constructor(message) { this.message = message; this.signatures = [Buffer.from([1])]; }
  static deserialize() { return new SwapTransaction({ header: { numRequiredSignatures: 1 }, staticAccountKeys: [wallet.publicKey], addressTableLookups: [], instructions: [],
    serialize() { return Buffer.from(JSON.stringify({blockhash:this.recentBlockhash,instructions:this.instructions})); } }); }
  sign() { swapSigns++; lastSignedMessageHash = this.message?.serialize
    ? require('crypto').createHash('sha256').update(this.message.serialize()).digest('hex') : null; }
  serialize() { return Buffer.from(this.message.recentBlockhash || "unsigned"); }
}
const deps = {
  "@solana/web3.js": { Transaction: RentTransaction, Connection, Keypair: { generate: () => ({ publicKey: key(`position-${++minted}`) }) }, PublicKey: function (v) { return key(v); }, VersionedTransaction: SwapTransaction,
    TransactionMessage: { decompile(message) { const instructions = [...message.instructions]; return {instructions, compileToV0Message() { return {...message, instructions}; }}; } } },
  "@meteora-ag/dlmm": { create: async () => {candidateCreates++; return pool;}, StrategyType: { Spot: 0, Curve: 1, BidAsk: 2 }, positionOwnerFilter: () => ({}) },
  "./dlmm_nav": { walletTradeActive: () => ++candidateTradeChecks >= candidateTradeAfter },
  "./dlmm_position_pda": {preparePositionPda: async args => {
    pdaCalls++;
    if (!pdaMode) return null;
    if (pdaMode === "throw") throw new Error("Optional optimization unavailable");
    assert.equal(args.lower,-20);assert.equal(args.upper,0);
    assert.equal(args.history.address,"pda-"+pdaMode);
    const tx=transaction();tx.compileMessage=()=>({pda:true});
    return {transaction:tx,position:key("pda-"+pdaMode),creation:{kind:"wallet_pda",base:wallet.publicKey.toString(),lower_bin_id:-20,width:21}};
  },beginPositionPdaHistory: () => ({address:"pda-"+pdaMode,read:Promise.resolve(true),cancel:()=>{pdaHistoryCancels++;}})},
  "./dlmm_canonical_liquidity": {observeCanonicalLiquidity: async (url, mint, options) => {
    if (!options.mayRead()) return {version: 1, status: "unmeasured", reason: "wallet_trade_active"};
    candidateCanonicalReads++;
    assert.ok(options.timeoutMs > 0 && options.timeoutMs <= 2000);
    if (candidateCanonicalError) throw new Error("Optional read failed");
    return {version: 1, status: "unmeasured", reason: "canonical_pool_absent"};
  }},
  "bn.js": function (value) { this.value = value; }, "bs58": { encode: () => "signature" },
  "dotenv": { config() {}, parse: () => ({}) },
};
const entryGates = { observed_at: 1, checked_deploy_sol: .1, fee_timeframe: "30m", m5_pct: 0, h1_pct: null, live_fee_tvl_ratio: 1.4, price_impact_pct: .1 };
const env = { SOLANA_RPC_URLS: "fake-rpc-1,fake-rpc-2", DLMM_ENTRY_CONTEXT: JSON.stringify({ mode: "turnover", recenter_of: "root", pair: "TEST-SOL", dev: "developer", signal: { holders: 0, unique_traders: 100, entry_live_gates: entryGates } }) };
const sandbox = { require: (name) => deps[name] || require(name), module: { exports: {} },
  process: { argv: ["node", path.join(root, "skills/solana-dlmm/scripts/dlmm_executor.js")], env },
  fetch: async (url, options) => {
    if (url.endsWith("/swap")) {
      const request = JSON.parse(options.body);
      assert.equal(request.dynamicComputeUnitLimit, true);
      assert.equal(request.wrapAndUnwrapSol, true);
      assert.equal(request.quoteResponse.inAmount, "100000000");
      assert.equal(request.dynamicSlippage, undefined); // retain the quoted slippage limit
    }
    return { ok: true, json: async () => url.includes("/quote?")
      ? { inAmount: "100000000", outAmount: "20", otherAmountThreshold: "19", contextSlot: 10,
          priceImpactPct: "0", unrelatedDebug: "must-not-persist" }
      : { swapTransaction: "AA==" } };
  },
  console: { log() {}, warn() {}, error() {} }, Buffer, AbortSignal, AbortController, setTimeout, clearTimeout };
// Advance the clock for confirmation polling without sleeping eight real seconds
// per pending fixture. Expiry must still depend on finalized block height.
const fixtureEpoch = Date.now();
let fixtureClock = 0;
sandbox.Date = class extends Date { static now() { return fixtureEpoch + fixtureClock; } };
sandbox.setTimeout = (callback, delay) => setTimeout(() => {fixtureClock += delay;callback();}, 0);
vm.runInNewContext(source + "\nmodule.exports.sdkFindPool = findPoolForPosition; module.exports.sdkPositions = getPositions; assertRootBudget = async () => {}; getWallet = () => testWallet; getTokenDecimals = async () => 9; assertRangeDoesNotRequireBinArrayInitialization = async () => {}; const productionConfirmSignedTransaction = confirmSignedTransaction; confirmSignedTransaction = async (connection, ...args) => { connection.testConfirming = true; try { return await productionConfirmSignedTransaction(connection, ...args); } finally { connection.testConfirming = false; } }; module.exports.confirmSignedTransaction = confirmSignedTransaction;", Object.assign(sandbox, { testWallet: wallet }));
const { swapAmountRaw, closePosition, swapToken, confirmSignedTransaction, deployPosition, acquireDeployLock, reconcilePendingSwap, assertNoTokenExposure,
  positionIsEmpty, slippageBpsToPercent } = sandbox.module.exports;
const marker = path.join(root, "memories/dlmm_pending_deploys", `${wallet.publicKey}.json`);
const deploy = () => deployPosition("pool", 0, 0.1, 20, 0, "bid_ask", 1000);
const clearMarker = () => fs.rmSync(marker, { force: true });
// The transport's concurrency/deadline is exercised separately. Here keep one
// fake send and verify routing/persistence at the executor boundary.
let settlementFanoutCalls=0, settlementFanoutMode='single';
sandbox.settlementFanoutProbe=async(strategy,raw,kind,options)=>{
  settlementFanoutCalls++;assert.equal(kind,'settlement_swap');
  assert.equal(options.skipPreflight,true);assert.equal(options.maxRetries,20);
  const pending=path.join(root,'memories/dlmm_pending_swaps',`${wallet.publicKey}-TOKEN-So11111111111111111111111111111111111111112.json`);
  const marker=JSON.parse(fs.readFileSync(pending));
  assert.equal(marker.signature,strategy.signature);assert.equal(marker.blockhash,strategy.blockhash);
  assert.equal(marker.lastValidBlockHeight,strategy.lastValidBlockHeight);assert.equal(raw.toString(),strategy.blockhash);
  if(settlementFanoutMode==='pending')throw new Error('bounded transport deadline');
  if(settlementFanoutMode==='failed'){const error=new Error('confirmed chain failure');error.transactionFailed=true;throw error;}
  return sandbox.module.exports.confirmSignedTransaction(new Connection(),strategy,raw,options);
};
vm.runInNewContext("const productionExitTransport=confirmExitTransaction;confirmExitTransaction=(...args)=>args[2]==='settlement_swap'?settlementFanoutProbe(...args):productionExitTransport(...args);",sandbox);

(async () => {
  // Wider observation shares one snapshot with the baseline; it never changes
  // the mint bounds. Keep the original baseline when the wider read fails.
  const snapshotReads = [];
  sandbox.snapshotStub = async (_pool, lower, upper) => {
    snapshotReads.push([lower, upper]);
    return { ts: 100, bins: Array.from({length: upper-lower+1}, (_, i) => ({id: lower+i})) };
  };
  vm.runInNewContext("const originalSnapshot = binSnapshot; binSnapshot = snapshotStub; module.exports.entryBinSnapshots = entryBinSnapshots;", sandbox);
  const capture = sandbox.module.exports.entryBinSnapshots;
  let captured = await capture(pool, -44, 0, "below");
  assert.deepEqual(snapshotReads, [[-69, 0]]);
  assert.equal(captured.bin_snapshot.bins.length, 45);
  assert.equal(captured.width_study.snapshot.bins.length, 70);
  assert.equal(captured.bin_snapshot.bins[0].id, -44);
  captured = await capture(pool, 0, 44, "above");
  assert.equal(captured.bin_snapshot.bins.at(-1).id, 44);
  assert.equal(captured.width_study.upper_bin, 69);
  assert.equal((await capture(pool, -80, 0, "below")).width_study, null);
  assert.equal((await capture(pool, -20, 20, null)).width_study, null);
  sandbox.snapshotStub = async (_pool, lower, upper) => {
    if (lower === -69) throw new Error("unavailable wider bins");
    return {ts: 100, bins: [{id: lower}, {id: upper}]};
  };
  vm.runInNewContext("binSnapshot = snapshotStub;", sandbox);
  captured = await capture(pool, -44, 0, "below");
  assert.equal(captured.width_study, null);
  assert.equal(captured.bin_snapshot.bins[0].id, -44);
  vm.runInNewContext("binSnapshot = originalSnapshot;", sandbox);

  if (!worker) {
    const snapshot = sandbox.module.exports.candidateBinSnapshot;
    env.SOLANA_PUBLIC_KEY = wallet.publicKey.toString();
    pool.lbPair.activeId = 0;
    pool.tokenX = {mint: {decimals: 9}}; pool.tokenY = {mint: {decimals: 9}};
    let binReads = 0, activeReads = 0;
    const previousActive = pool.getActiveBin;
    pool.getActiveBin = async () => {activeReads++; return previousActive();};
    pool.getBinsBetweenLowerAndUpperBound = async (lower, upper) => {
      binReads++;
      return {bins: Array.from({length: upper-lower+1}, (_, i) => ({binId: lower+i,
        xAmount: 0, yAmount: 100, supply: 100, feeAmountXPerTokenStored: 0,
        feeAmountYPerTokenStored: 0, pricePerToken: 1}))};
    };
    vm.runInNewContext("const candidateOriginalWallet = getWallet; getWallet = () => {throw new Error('Read-only candidate must not decode wallet');};", sandbox);
    candidateCreates = candidateTradeChecks = 0;
    const observed = await snapshot("pool");
    assert.equal(observed.status, "observed");
    assert.equal(observed.pool, "pool");
    assert.equal(observed.token_x_mint, "TOKEN");
    assert.equal(observed.lower_bin, -69); assert.equal(observed.upper_bin, 16);
    assert.equal(observed.bins.length, 86); assert.equal(binReads, 1); assert.equal(activeReads, 1);
    assert.equal(observed.bin_step, 100); assert.equal(candidateCanonicalReads, 1);
    assert.equal(observed.canonical_liquidity.reason, "canonical_pool_absent");
    candidateCanonicalError = true;
    assert.equal((await snapshot("pool")).status, "observed");
    candidateCanonicalError = false;
    assert.equal(sends, 0); assert.equal(builds, 0);
    for (const [below, above] of [[70, 0], [-1, 0], [1.5, 0], [0, 17], [0, NaN]]) {
      await assert.rejects(snapshot("pool", below, above), /bounds/);
    }
    assert.equal(candidateCreates, 2);
    delete env.SOLANA_PUBLIC_KEY;
    await assert.rejects(snapshot("pool"), /SOLANA_PUBLIC_KEY/);
    env.SOLANA_PUBLIC_KEY = wallet.publicKey.toString();
    for (const at of [1, 2, 3, 4]) {
      candidateTradeChecks = 0; candidateTradeAfter = at; candidateCreates = binReads = activeReads = 0;
      assert.equal((await snapshot("pool")).status, "deferred");
      assert.equal(candidateCreates, at >= 3 ? 1 : 0);
      assert.equal(binReads, at === 4 ? 1 : 0);
      assert.equal(activeReads, 0);
    }
    candidateTradeAfter = Infinity;
    pool.lbPair.tokenYMint = key("NOT-SOL");
    await assert.rejects(snapshot("pool"), /RPC endpoints failed/);
    pool.lbPair.tokenYMint = key("So11111111111111111111111111111111111111112");
    pool.getActiveBin = previousActive;
    delete pool.getBinsBetweenLowerAndUpperBound; delete pool.lbPair.activeId;
    delete pool.tokenX; delete pool.tokenY;
    vm.runInNewContext("getWallet = candidateOriginalWallet;", sandbox);
  }

  if (worker && worker.startsWith("reclaim-")) {
    const shares = worker === "reclaim-unknown" ? undefined : [{binId:0,positionLiquidity:worker === "reclaim-funded" ? "100000000000000000000000000" : "0"}];
    vm.runInNewContext("findPoolForPosition = async () => ({pool: testPool, positionData: {publicKey: testWallet.publicKey, positionData: {lowerBinId:0,upperBinId:0,positionBinData: testShares}}});", Object.assign(sandbox, {testPool:pool,testShares:shares}));
    pool.removeLiquidity = async () => { throw new Error("Empty reclaim must never withdraw"); };
    pool.closePositionIfEmpty = async () => { builds++; return transaction(); };
    Connection.prototype.sendRawTransaction = async () => { sends++; accountExists = worker === "reclaim-race"; return "signature"; };
    const result = await closePosition("reclaim-position", true);
    console.log(JSON.stringify({result,sends,builds,accountExists}));
    return;
  }
  if (worker && worker.startsWith("close-")) {
    vm.runInNewContext("findPoolForPosition = async () => ({pool: testPool, positionData: {publicKey: testWallet.publicKey, positionData: {lowerBinId: 0, upperBinId: 1}}});", Object.assign(sandbox, {testPool: pool}));
    let claimBuilds = 0;
    pool.claimSwapFee = async () => { claimBuilds++; return []; };
    pool.removeLiquidity = async (args) => {
      assert.equal(args.shouldClaimAndClose, true);
      builds++;
      if (worker === "close-empty") throw new Error("no liquidity");
      return transaction();
    };
    if (worker === "close-empty") {
      vm.runInNewContext("findPoolForPosition = async () => ({pool: testPool, positionData: {publicKey: testWallet.publicKey, positionData: {lowerBinId: 0, upperBinId: 1, liquidityShares: [{isZero: () => true}]}}});", sandbox);
      pool.closePositionIfEmpty = async () => transaction();
    }
    sendError = worker === "close-submit";
    if (!sendError) Connection.prototype.sendRawTransaction = async () => { sends++; accountExists = false; return "signature"; };
    const result = await closePosition("restart-position");
    console.log(JSON.stringify({result,sends,builds,claimBuilds}));
    return;
  }
  if (worker) {
    sendError = true;
    signatureStatus = worker === "confirmed" ? { confirmationStatus: "confirmed", err: null } : null;
    if (worker === "unavailable") Connection.prototype.getSignatureStatuses = async () => { throw new Error("offline"); };
    const result = await swapToken("So11111111111111111111111111111111111111112", "TOKEN", 0.1);
    console.log(JSON.stringify({ result, sends }));
    return;
  }
  for (const state of ["funded", "unknown", "empty", "race"]) {
    const out = JSON.parse(execFileSync(process.execPath,[__filename,"reclaim-"+state,root],{encoding:"utf8"}));
    if (["funded","unknown"].includes(state)) {
      assert.equal(out.result.success,false); assert.equal(out.sends,0); assert.equal(out.builds,0);
      assert.equal(out.result.funded,state === "funded");
    } else {
      assert.equal(out.sends,1); assert.equal(out.builds,1);
      assert.equal(out.accountExists,state === "race"); // monitor must verify disappearance
    }
  }
  reservePost=199999999;
  await assert.rejects(swapToken("So11111111111111111111111111111111111111112","TOKEN",0.1),/native reserve/);
  assert.equal(sends,0);
  reservePost=300000000;
  for (const [mode, count] of [["submit", 1], ["pending", 0], ["unavailable", 0], ["confirmed", 0]]) {
    const out = JSON.parse(execFileSync(process.execPath, [__filename, mode, root], { encoding: "utf8" }));
    assert.equal(out.sends, count);
    assert.equal(mode === "confirmed" ? out.result.success : out.result.pending, true);
  }
  const closeFirst = JSON.parse(execFileSync(process.execPath, [__filename, "close-submit", root], {encoding:"utf8"}));
  assert.equal(closeFirst.result.pending, true);
  assert.equal(closeFirst.builds, 1);
  assert.equal(closeFirst.claimBuilds, 0); // combined SDK close already claims fees
  const closeRestart = JSON.parse(execFileSync(process.execPath, [__filename, "close-resume", root], {encoding:"utf8"}));
  assert.equal(closeRestart.result.success, true);
  assert.equal(closeRestart.builds, 0); // resumed the persisted bytes in a new process
  assert.equal(closeRestart.sends, 2); // Same persisted bytes fan out to both configured RPCs.
  const emptyClose = JSON.parse(execFileSync(process.execPath, [__filename, "close-empty", root], {encoding:"utf8"}));
  assert.equal(emptyClose.result.success, true);
  assert.equal(emptyClose.claimBuilds, 1); // preserve fees when combined close cannot be built

  // A local cleanup failure after confirmation must not send a second swap.
  const originalRm = fs.rmSync;
  fs.rmSync = (target, options) => {
    if (String(target).includes("dlmm_pending_swaps")) throw new Error("cleanup denied");
    return originalRm(target, options);
  };
  try {
    assert.equal((await swapToken("So11111111111111111111111111111111111111112", "TOKEN", 0.1)).pending, true);
    assert.equal(sends, 1);
  } finally {
    fs.rmSync = originalRm;
  }
  const quoteEvent=JSON.parse(fs.readFileSync(path.join(root,"memories/dlmm_transactions.jsonl"),"utf8").trim().split("\n").at(-1));
  assert.equal(quoteEvent.kind,"swap");
  assert.equal(quoteEvent.swap_quote.out_amount,"20");
  assert.equal(quoteEvent.swap_quote.minimum_out_amount,"19");
  assert.equal(quoteEvent.swap_quote.context_slot,10);
  assert.equal(quoteEvent.swap_quote.input_mint,"So11111111111111111111111111111111111111112");
  assert.equal(quoteEvent.swap_quote.output_mint,"TOKEN");
  assert.equal(quoteEvent.swap_quote.unrelatedDebug,undefined);
  assert.equal(quoteEvent.swap_quote.net_recovery,undefined);
  // Residual recovery must cover costs and the full slippage allowance before
  // sending. Existing pending-send tests above still exercise the normal path.
  const defaultBalance = Connection.prototype.getBalanceAndContext;
  const defaultSimulation = Connection.prototype.simulateTransaction;
  const oldFetch = sandbox.fetch;
  let simulatedPost = 14600, simulationError = null, changedBalance = false, balanceReads = 0;
  let minimumOutput = "4500";
  sandbox.fetch = async (url) => ({ ok: true, json: async () => url.includes("/quote?")
    ? { inAmount: "100000000", outAmount: "5000", otherAmountThreshold: minimumOutput, priceImpactPct: "0" }
    : { swapTransaction: "AA==" } });
  Connection.prototype.getParsedAccountInfo = async () => ({ value: { data: { parsed: { info: { decimals: 9 } } } } });
  Connection.prototype.getBalanceAndContext = async () => ({ context: { slot: 10 }, value: (++balanceReads % 2 === 0 && changedBalance) ? 10001 : 10000 });
  Connection.prototype.simulateTransaction = async (_, options) => {
    assert.equal(options.sigVerify, false);
    assert.equal(options.minContextSlot, 10);
    return { context: { slot: 10 }, value: { err: simulationError, accounts: [{ lamports: simulatedPost }] } };
  };
  const recover = (floor=4000) => swapToken("TOKEN", "So11111111111111111111111111111111111111112", env.DLMM_SETTLEMENT_POSITION ? "raw:100000000" : 0.1, 5, 100, floor);
  assert.equal(swapAmountRaw(66.324429, 6), "66324429");
  assert.equal(swapAmountRaw("9007199254.740993", 6), "9007199254740993");
  assert.equal(swapAmountRaw("1e-9", 9), "1");
  assert.equal(swapAmountRaw("1.23456789", 6), "1234567"); // excess precision truncates, never overspends
  assert.equal(swapAmountRaw("18446744073709551615", 0), "18446744073709551615");
  for (const bad of [NaN, Infinity, -1, 0, "1bad", "1e999", "18446744073709551616", "0.0000000001"]) {
    assert.throws(() => swapAmountRaw(bad, 9));
  }
  assert.throws(() => swapAmountRaw(1, undefined));
  const previousSends = sends;
  assert.equal((await recover(4101)).reason, "net_recovery_below_floor");
  simulatedPost = 9900;
  assert.equal((await recover(1)).reason, "net_recovery_below_floor");
  simulatedPost = 14600; simulationError = "failed";
  assert.equal((await recover()).reason, "net_recovery_unmeasured");
  simulationError = null; changedBalance = true;
  assert.equal((await recover()).reason, "net_recovery_unmeasured");
  changedBalance = false; minimumOutput = undefined;
  assert.equal((await recover()).reason, "net_recovery_invalid_quote");
  minimumOutput = "4500";
  await assert.rejects(recover(NaN), /positive integer/);
  assert.equal(sends, previousSends);
  assert.equal((await recover(4100)).success, true);
  assert.equal(sends, previousSends + 1);
  // Actual negative recovery example: rent is counted only by simulating a
  // combined full-balance swap + close, never by adding an estimated refund.
  const settlementPosition = "11111111111111111111111111111111";
  const settlementMarker = path.join(root, "memories/dlmm_settlements", settlementPosition + ".json");
  assert.equal(settlementFanoutCalls,0); // Other swaps retain their existing single-RPC transport.
  fs.mkdirSync(path.dirname(settlementMarker), {recursive: true});
  fs.writeFileSync(settlementMarker, JSON.stringify({position:settlementPosition,mint:"TOKEN"}));
  env.DLMM_SETTLEMENT_POSITION = settlementPosition;
  let inventoryProof = {success:true,amount_raw:"100000000",wallet_balance_raw:"100000000",slot:10};
  deps["child_process"] = {execFileSync: (_, args) => {
    assert.equal(args.includes("--settlement-inventory"),true);
    return JSON.stringify(inventoryProof);
  }};
  // Only the root's missing signature is fetched, never unrelated history.
  const journalPath=path.join(root,"memories/dlmm_transactions.jsonl");
  const factPath=path.join(root,"memories/dlmm_wallet_transactions.jsonl");
  const originalJournal=fs.readFileSync(journalPath,"utf8");
  const originalFacts=fs.existsSync(factPath)?fs.readFileSync(factPath,"utf8"):null;
  fs.appendFileSync(journalPath,JSON.stringify({signature:"proof-close",wallet:wallet.publicKey.toString(),position:settlementPosition,kind:"close"})+"\n");
  let proofCalls=0; const requestedFacts=[];
  deps["child_process"].execFileSync=()=>JSON.stringify(++proofCalls===1
    ? {success:false,pending_signatures:["proof-close"]} : inventoryProof);
  deps["./dlmm_nav.js"]={parsedAccountingTransaction:async(_,sig)=>{requestedFacts.push(sig);return {meta:{}};},
    transactionFact:(_,owner,sig)=>({signature:sig,wallet:owner,landed:true})};
  assert.equal((await sandbox.module.exports.settlementInventory(settlementPosition,"TOKEN",wallet.publicKey.toString())).success,true);
  assert.deepEqual(requestedFacts,["proof-close"]);assert.equal(proofCalls,2);
  // DOPE's first swap never landed; the balance gate must be able to obtain
  // the existing expiry proof without waiting for a periodic accounting job.
  const priorHeight = Connection.prototype.getBlockHeight, expirySends = sends;
  let historyRefreshes=0, expiryHeightReads=0, refreshed=false, historyCompletes=true, historyError=false;
  const agedSwap={signature:"expiry-swap",wallet:wallet.publicKey.toString(),position:settlementPosition,
    kind:"swap",ts:Math.floor(sandbox.Date.now()/1000)-300,lastValidBlockHeight:150};
  deps["./dlmm_nav.js"].parsedAccountingTransaction=async()=>null;
  deps["./dlmm_nav.js"].collect=async options=>{
    historyRefreshes++;
    assert.equal(options.wallet,wallet.publicKey.toString());
    assert.equal(options.historyOnly,true);assert.equal(options.includeRentHistory,false);
    if(historyError) throw new Error("history unavailable");
    refreshed=historyCompletes;
  };
  deps["child_process"].execFileSync=()=>JSON.stringify(refreshed ? inventoryProof
    : {success:false,reason:"settlement_inventory_unproven",pending_signatures:[agedSwap.signature]});
  Connection.prototype.getBlockHeight=async commitment=>{
    assert.equal(commitment,"finalized");expiryHeightReads++;return height;
  };
  const expiryCase=async (change=()=>{})=>{
    const event={...agedSwap};change(event);refreshed=false;historyRefreshes=0;expiryHeightReads=0;
    fs.writeFileSync(journalPath,originalJournal+JSON.stringify(event)+"\n");
    return sandbox.module.exports.settlementInventory(settlementPosition,"TOKEN",wallet.publicKey.toString());
  };
  height=151;
  assert.equal((await expiryCase()).success,true);assert.equal(historyRefreshes,1);assert.equal(expiryHeightReads,1);
  for(const change of [e=>e.kind="close",e=>e.wallet="other",e=>e.position="other",
    e=>e.ts=Math.floor(sandbox.Date.now()/1000)-120,e=>e.ts=Math.floor(sandbox.Date.now()/1000)+1,
    e=>e.ts=0,e=>delete e.ts,e=>e.lastValidBlockHeight=null,e=>e.lastValidBlockHeight=0,
    e=>e.lastValidBlockHeight=Number.MAX_SAFE_INTEGER+1]) {
    assert.equal((await expiryCase(change)).success,false);assert.equal(historyRefreshes,0);assert.equal(expiryHeightReads,0);
  }
  height=150;assert.equal((await expiryCase()).success,false);assert.equal(historyRefreshes,0);
  height=151;historyCompletes=false;
  assert.equal((await expiryCase()).success,false);assert.equal(historyRefreshes,1); // Missing history/status proof stays blocked.
  historyError=true;assert.equal((await expiryCase()).success,false);assert.equal(historyRefreshes,1);
  historyError=false;historyCompletes=true;
  Connection.prototype.getBlockHeight=async()=>{throw new Error("RPC unavailable")};
  assert.equal((await expiryCase()).success,false);assert.equal(historyRefreshes,0);
  Connection.prototype.getBlockHeight=priorHeight;height=100;
  deps["child_process"].execFileSync=()=>JSON.stringify(inventoryProof);
  historyRefreshes=0;
  assert.equal((await sandbox.module.exports.settlementInventory(settlementPosition,"TOKEN",wallet.publicKey.toString())).success,true);
  assert.equal(historyRefreshes,0);assert.equal(sends,expirySends); // Already proved inventory adds no refresh or trade.
  fs.writeFileSync(journalPath,originalJournal);
  if(originalFacts===null) fs.rmSync(factPath);else fs.writeFileSync(factPath,originalFacts);
  delete deps["./dlmm_nav.js"];
  deps["child_process"].execFileSync=()=>JSON.stringify(inventoryProof);
  const token = key("settlement-token"), owner = wallet.publicKey.toString();
  deps["@solana/spl-token"] = {TOKEN_PROGRAM_ID:token,TOKEN_2022_PROGRAM_ID:key("2022"),
    createCloseAccountInstruction(account,destination,authority,_,program) {
      assert.equal(destination, wallet.publicKey); assert.equal(authority, wallet.publicKey);
      assert.equal(program, token); return {closeAccount:account.toString()};
    }};
  const eligible = () => ({pubkey:key("settlement-ata"),account:{owner:token,lamports:1488440,
    data:{parsed:{info:{owner,mint:"TOKEN",tokenAmount:{amount:"100000000"},state:"initialized",isNative:false}}}}});
  let accounts = [eligible()], combinedError = false, combinedChanged = false, accountReads = 0;
  Connection.prototype.getParsedTokenAccountsByOwner = async () => {accountReads++;return {value:accounts};};
  Connection.prototype.getBalanceAndContext = async () => ({context:{slot:10},value:++balanceReads%2===0 && combinedChanged ? 10001 : 10000});
  Connection.prototype.simulateTransaction = async tx => {
    const combined = tx.message.instructions.some(i=>i.closeAccount);
    return {context:{slot:10},value:{err:combined && combinedError ? "close refused" : null,
      accounts:[{lamports:8449+(combined?1488440:0)}]}};
  };
  sandbox.fetch = async url => ({ok:true,json:async()=>url.includes("/quote?")
    ? {inputMint:"TOKEN",outputMint:"So11111111111111111111111111111111111111112",inAmount:"100000000",outAmount:"5000",otherAmountThreshold:"4500",priceImpactPct:"0"}
    : {swapTransaction:"AA=="}});
  accountExists = false;
  const beforeAtomic = sends;
  assert.equal((await recover(1)).success, true); assert.equal(sends,beforeAtomic+1);
  const recordedAtomic=fs.readFileSync(path.join(root,'memories/dlmm_transactions.jsonl'),'utf8').trim().split('\n').map(JSON.parse).at(-1);
  assert.equal(recordedAtomic.swap_quote.token_rent_close_included,true);
  assert.ok(settlementFanoutCalls>0);
  // Unknown fanout outcomes keep the signed marker and return directly. A
  // subsequent call reconciles it before requesting another quote or signature.
  const pendingSwap=path.join(root,'memories/dlmm_pending_swaps',`${wallet.publicKey}-TOKEN-So11111111111111111111111111111111111111112.json`);
  const statusBeforeOwned=Connection.prototype.getSignatureStatuses,fetchBeforeOwned=sandbox.fetch;
  let ownedStatusReads=0,ownedQuoteReads=0;
  Connection.prototype.getSignatureStatuses=async function(...args){ownedStatusReads++;return statusBeforeOwned.apply(this,args);};
  sandbox.fetch=async(...args)=>{if(args[0].includes('/quote?'))ownedQuoteReads++;return fetchBeforeOwned(...args);};
  const sendsBeforeOwnedPending=sends,callsBeforeOwnedPending=settlementFanoutCalls;
  settlementFanoutMode='pending';
  const ownedPending=await recover(1);
  assert.equal(ownedPending.pending,true);assert.equal(ownedStatusReads,0);assert.equal(ownedQuoteReads,1);
  assert.equal(fs.existsSync(pendingSwap),true);assert.equal(sends,sendsBeforeOwnedPending);
  settlementFanoutMode='single';
  assert.equal((await recover(1)).pending,true);
  assert.equal(ownedQuoteReads,1);assert.equal(settlementFanoutCalls,callsBeforeOwnedPending+1);
  assert.equal(sends,sendsBeforeOwnedPending);fs.rmSync(pendingSwap);
  settlementFanoutMode='failed';
  assert.equal((await recover(1)).success,false);assert.equal(fs.existsSync(pendingSwap),false);
  settlementFanoutMode='single';Connection.prototype.getSignatureStatuses=statusBeforeOwned;sandbox.fetch=fetchBeforeOwned;
  // Route exclusion end to end. A single-Hadron quote whose confirmed Jupiter
  // instruction fails with 6001 records a five-minute exclusion and the next owned
  // quote requests excludeDexes=Hadron. Other errors and timeouts record nothing,
  // and a failed sidecar write keeps the signed marker so nothing is re-signed.
  {
    const JUP='JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4';
    const routeFile=pendingSwap+'.route';
    const deserializeBefore=SwapTransaction.deserialize, probeBefore=sandbox.settlementFanoutProbe;
    const fetchBefore=sandbox.fetch, writeBefore=fs.writeFileSync;
    SwapTransaction.deserialize=()=>{const t=deserializeBefore();
      t.message.staticAccountKeys=[wallet.publicKey,JUP];t.message.compiledInstructions=[{programIdIndex:1}];return t;};
    const quoteUrls=[];
    sandbox.fetch=async url=>{
      if(url.includes('/quote?')){quoteUrls.push(new URL(url));return{ok:true,json:async()=>({inputMint:'TOKEN',
        outputMint:'So11111111111111111111111111111111111111112',inAmount:'100000000',outAmount:'5000',
        otherAmountThreshold:'4500',priceImpactPct:'0',routePlan:[{swapInfo:{label:'Hadron'}}]})};}
      return{ok:true,json:async()=>({swapTransaction:'AA=='})};
    };
    let failWith=null,seenContext=null,probes=0;
    sandbox.settlementFanoutProbe=async()=>{
      probes++;seenContext=JSON.parse(fs.readFileSync(pendingSwap)).routeContext;
      if(failWith==='timeout')throw new Error('bounded transport deadline');
      const e=new Error('confirmed chain failure');e.transactionFailed=true;e.chainError=failWith;throw e;
    };
    fs.rmSync(routeFile,{force:true});
    // Confirmed 6001 at the bound Jupiter instruction: exclusion recorded.
    failWith={InstructionError:[0,{Custom:6001}]};
    assert.equal((await recover(1)).success,false);
    assert.deepEqual(seenContext,{position:settlementPosition,jupiter_instruction:0,dex:'Hadron'});
    assert.equal(fs.existsSync(routeFile),true);assert.equal(fs.existsSync(pendingSwap),false);
    assert.equal(quoteUrls.at(-1).searchParams.get('excludeDexes'),null);
    // The next quote excludes Hadron; a provider that still routes via Hadron aborts unsigned.
    const probesBeforeExcluded=probes, signsBeforeExcluded=swapSigns;
    assert.equal((await recover(1)).reason,'swap_route_exclusion_unverified');
    assert.equal(quoteUrls.at(-1).searchParams.get('excludeDexes'),'Hadron');
    assert.equal(quoteUrls.at(-1).searchParams.get('slippageBps'),'100');
    assert.equal(probes,probesBeforeExcluded);assert.equal(swapSigns,signsBeforeExcluded);
    fs.rmSync(routeFile,{force:true});
    // A different confirmed program error and a timeout record no exclusion.
    failWith={InstructionError:[0,{Custom:6008}]};
    assert.equal((await recover(1)).success,false);assert.equal(fs.existsSync(routeFile),false);
    failWith='timeout';
    assert.equal((await recover(1)).pending,true);assert.equal(fs.existsSync(routeFile),false);
    assert.equal(fs.existsSync(pendingSwap),true);fs.rmSync(pendingSwap);
    // A sidecar write failure must not clear the signed marker or allow another signature.
    failWith={InstructionError:[0,{Custom:6001}]};
    fs.writeFileSync=(file,...rest)=>{if(String(file).includes('.route.'))throw new Error('disk full');return writeBefore(file,...rest);};
    const probesBeforeStorage=probes;
    let storageResult;
    try{storageResult=await recover(1);}catch(error){storageResult={success:false,error:error.message};}
    fs.writeFileSync=writeBefore;
    assert.notEqual(storageResult.success,true);assert.equal(probes,probesBeforeStorage+1);
    assert.equal(fs.existsSync(pendingSwap),true);assert.equal(fs.existsSync(routeFile),false);
    const quotesBeforeRetry=quoteUrls.length, signsBeforeRetry=swapSigns;
    signatureStatus={confirmationStatus:'processed',err:null};
    assert.equal((await recover(1)).pending,true);
    assert.equal(quoteUrls.length,quotesBeforeRetry);assert.equal(probes,probesBeforeStorage+1);
    assert.equal(swapSigns,signsBeforeRetry);
    signatureStatus=null;fs.rmSync(pendingSwap,{force:true});fs.rmSync(routeFile,{force:true});
    SwapTransaction.deserialize=deserializeBefore;sandbox.settlementFanoutProbe=probeBefore;sandbox.fetch=fetchBefore;
  }
  // Ordinary full-owned settlements may close an ATA too, within a separate
  // abortable budget. Cash from rent cannot hide a worse simulated sale.
  const savedOrdinaryFetch=sandbox.fetch, savedOrdinarySim=Connection.prototype.simulateTransaction;
  const markerBeforeOrdinary=fs.readFileSync(settlementMarker);
  fs.writeFileSync(settlementMarker,JSON.stringify({position:settlementPosition,mint:"TOKEN",emergency_exit:false}));
  let ordinaryCombinedError=false, ordinaryWorseSale=false, ordinarySimulations=[];
  sandbox.fetch=async url=>({ok:true,json:async()=>url.includes('/quote?')
    ? {inputMint:"TOKEN",outputMint:"So11111111111111111111111111111111111111112",inAmount:"100000000",outAmount:"1000000",otherAmountThreshold:"990000",swapMode:"ExactIn",slippageBps:100,priceImpactPct:"0"}
    : {swapTransaction:"AA=="}});
  Connection.prototype.simulateTransaction=async tx=>{
    const combined=tx.message.instructions.some(i=>i.closeAccount);ordinarySimulations.push(combined);
    return {context:{slot:10},value:{err:combined&&ordinaryCombinedError ? 'close refused' : null,
      accounts:[{lamports:1010000+(combined?1488440-(ordinaryWorseSale?1:0):0)}]}};
  };
  const ordinary=()=>swapToken("TOKEN","SOL","raw:100000000",15,100,1,true);
  const lastOrdinary=()=>JSON.parse(fs.readFileSync(journalPath,'utf8').trim().split('\n').at(-1)).swap_quote;
  const beforeOrdinaryReads=accountReads;
  assert.equal((await ordinary()).success,true);
  assert.deepEqual(ordinarySimulations,[false,true]);
  assert.equal(accountReads-beforeOrdinaryReads,1); // Reuse the already checked balance/closed-position evidence.
  assert.equal(lastOrdinary().ordinary_token_rent_close,true);
  assert.equal(lastOrdinary().net_recovery.conservative_wallet_delta_lamports,2478440);
  assert.equal(lastOrdinary().net_recovery.required_minimum_lamports,1);
  assert.equal(lastOrdinary().net_recovery.reserved_quote_slippage_lamports,10000);
  assert.equal(lastOrdinary().net_recovery.token_rent_close_included,true);
  assert.equal(lastOrdinary().net_recovery.simulated_wallet_delta_lamports,2488440);
  assert.equal(lastOrdinary().net_recovery.simulation_slot,10);
  assert.equal(lastOrdinary().net_recovery.wallet_read_before_slot,10);
  assert.equal(lastOrdinary().net_recovery.wallet_read_after_slot,10);
  assert.match(lastOrdinary().net_recovery.message_sha256,/^[a-f0-9]{64}$/);
  // The journaled measurement belongs to the exact message that was signed and sent.
  assert.equal(lastOrdinary().net_recovery.message_sha256,lastSignedMessageHash);
  const selectedRecoveryHash=lastOrdinary().net_recovery.message_sha256;
  const ordinarySimulation=Connection.prototype.simulateTransaction;
  const sendsBeforeMutation=sends;
  Connection.prototype.simulateTransaction=async function(candidate,options) {
    const result=await ordinarySimulation.call(this,candidate,options);
    candidate.message.recentBlockhash="mutated-after-simulation";
    return result;
  };
  assert.equal((await ordinary()).reason,"net_recovery_unmeasured");
  assert.equal(sends,sendsBeforeMutation);
  Connection.prototype.simulateTransaction=ordinarySimulation;
  assert.equal(lastOrdinary().minimum_out_amount,"990000");assert.equal(lastOrdinary().authorized_slippage_bps,100);
  for(const failure of ['simulation','worse-sale','emergency','unknown-emergency','legacy','extension']){
    ordinarySimulations=[];ordinaryCombinedError=failure==='simulation';ordinaryWorseSale=failure==='worse-sale';
    accounts=[eligible()];inventoryProof={success:true,amount_raw:"100000000",wallet_balance_raw:"100000000",slot:10};
    const marker={position:settlementPosition,mint:"TOKEN",emergency_exit:false};
    if(failure==='emergency')marker.emergency_exit=true;
    if(failure==='unknown-emergency')delete marker.emergency_exit;
    if(failure==='legacy'){
      accounts[0].account.data.parsed.info.tokenAmount.amount="100000017";
      inventoryProof.wallet_balance_raw="100000017";
    }
    if(failure==='extension'){
      accounts[0].account.owner=key('2022');accounts[0].account.data.parsed.info.extensions=[{extension:'pausableAccount'}];
    }
    fs.writeFileSync(settlementMarker,JSON.stringify(marker));
    const before=sends;assert.equal((await ordinary()).success,true);assert.equal(sends,before+1);
    assert.equal(lastOrdinary().ordinary_token_rent_close,false);
    assert.equal(lastOrdinary().token_rent_close_included,false);
    assert.equal(lastOrdinary().net_recovery.conservative_wallet_delta_lamports,990000);
    assert.equal(lastOrdinary().net_recovery.token_rent_close_included,false);
    assert.notEqual(lastOrdinary().net_recovery.message_sha256,selectedRecoveryHash);
    assert.equal(lastOrdinary().net_recovery.simulated_wallet_delta_lamports,1000000);
    assert.deepEqual(ordinarySimulations,failure==='simulation'||failure==='worse-sale'?[false,true]:[false]);
  }
  accounts=[eligible()];inventoryProof={success:true,amount_raw:"100000000",wallet_balance_raw:"100000000",slot:10};
  fs.writeFileSync(settlementMarker,JSON.stringify({position:settlementPosition,mint:"TOKEN",emergency_exit:false}));
  let optionalAborts=0;
  sandbox.fetch=async (_url,options)=>new Promise((_resolve,reject)=>{
    options.signal.addEventListener('abort',()=>{optionalAborts++;reject(new Error('read cancelled'));},{once:true});
  });
  const optionalEvidence={position:settlementPosition,positionClosed:true,accounts:{value:accounts}};
  const optionalResult=await sandbox.module.exports.ordinarySettlementRentClose(new Connection(),wallet,
    new SwapTransaction({header:{numRequiredSignatures:1},staticAccountKeys:[wallet.publicKey],addressTableLookups:[],instructions:[]}),
    'TOKEN','100000000',optionalEvidence,async (_tx,read)=>{await read.rpcOptions.fetch('https://optional.invalid',{});return 1;});
  assert.equal(optionalResult,null);assert.equal(optionalAborts,1);
  fs.writeFileSync(settlementMarker,markerBeforeOrdinary);
  sandbox.fetch=savedOrdinaryFetch;Connection.prototype.simulateTransaction=savedOrdinarySim;
  // First ordinary recoveries may spend another 200 bps only when the fresh
  // owned-inventory quote is <=250,000 lamports. Exercise the actual swap path,
  // including the selected quote sent to /swap and journaled before broadcast.
  const atomicFetch = sandbox.fetch, atomicSimulation = Connection.prototype.simulateTransaction;
  const originalTimer = sandbox.setTimeout;
  const quoteCalls = [], quoteDelays = [], swapRequests = [];
  let quotedOutputs = ["250000", "250000"], quoteAlter = null, quoteFailure = null, quoteErrorCode = "NO_ROUTES_FOUND", quoteFailureIndex = 1;
  sandbox.setTimeout = (callback, delay) => { quoteDelays.push(delay); return setTimeout(callback, 0); };
  sandbox.fetch = async (url, options) => {
    if (url.includes("/quote?")) {
      const bps = Number(new URL(url).searchParams.get("slippageBps"));
      const i = quoteCalls.length; quoteCalls.push(bps);
      if (quoteFailure && (quoteFailureIndex instanceof Set ? quoteFailureIndex.has(i) : i === quoteFailureIndex)) return {ok:false,status:quoteFailure,text:async()=>JSON.stringify({errorCode:quoteErrorCode})};
      const out = quotedOutputs[Math.min(i, quotedOutputs.length-1)];
      const q = {inputMint:"TOKEN",outputMint:"So11111111111111111111111111111111111111112",
        inAmount:"100000000",outAmount:out,swapMode:"ExactIn",slippageBps:bps,
        otherAmountThreshold:/^[0-9]+$/.test(out) ? (BigInt(out)*BigInt(10000-bps)/10000n).toString() : "0",priceImpactPct:"0"};
      if (quoteAlter) quoteAlter(q, i);
      return {ok:true,json:async()=>q};
    }
    swapRequests.push(JSON.parse(options.body));
    return {ok:true,json:async()=>({swapTransaction:"AA=="})};
  };
  Connection.prototype.simulateTransaction = async () => ({context:{slot:10},value:{err:null,accounts:[{lamports:300000}]}});
  const settlementSol = "So11111111111111111111111111111111111111112";
  const smallRecovery = () => swapToken("TOKEN",settlementSol,"raw:100000000",15,100,1,true);
  const resetSmall = (outputs=["250000","250000"]) => {
    quotedOutputs=outputs;quoteCalls.length=0;quoteDelays.length=0;swapRequests.length=0;quoteAlter=null;quoteFailure=null;quoteErrorCode="NO_ROUTES_FOUND";quoteFailureIndex=1;
  };
  let smallResult = await smallRecovery();
  assert.equal(smallResult.success,true);assert.deepEqual(quoteCalls,[100,300]);assert.deepEqual(quoteDelays,[2100]);
  assert.equal(swapRequests[0].quoteResponse.slippageBps,300);
  assert.equal(swapRequests[0].quoteResponse.otherAmountThreshold,"242500");
  const smallEvent = JSON.parse(fs.readFileSync(journalPath,"utf8").trim().split("\n").at(-1));
  assert.equal(smallEvent.swap_quote.authorized_slippage_bps,300);
  assert.equal(smallEvent.swap_quote.small_settlement_requote,true);
  resetSmall(["250001"]);
  assert.equal((await smallRecovery()).success,true);assert.deepEqual(quoteCalls,[100]);assert.deepEqual(quoteDelays,[]);
  assert.equal(swapRequests[0].quoteResponse.slippageBps,100);
  resetSmall(["249999","249000"]);
  assert.equal((await smallRecovery()).success,true);assert.equal(swapRequests[0].quoteResponse.outAmount,"249000");
  resetSmall();quoteAlter=q=>q.priceImpactPct="0.15";
  assert.equal((await smallRecovery()).success,true); // Exact 15% ceiling.
  resetSmall();quoteAlter=q=>q.priceImpactPct="1.5e-1";
  assert.equal((await smallRecovery()).success,true); // Same fraction in exponent notation.
  resetSmall(["250000","250000","1"]);quoteFailure=400;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
  assert.equal((await smallRecovery()).success,true);
  assert.deepEqual(quoteCalls,[100,300,0]);
  assert.equal(swapRequests[0].quoteResponse.otherAmountThreshold,"1");
  assert.equal(swapRequests[0].quoteResponse.slippageBps,0);
  resetSmall(["1"]);quoteFailure=400;quoteFailureIndex=0;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
  assert.equal((await swapToken("TOKEN",settlementSol,"raw:100000000",15,300,1)).success,true);
  assert.deepEqual(quoteCalls,[300,0]);
  assert.equal(swapRequests[0].quoteResponse.slippageBps,0);
  resetSmall(["1"]);quoteFailure=400;quoteFailureIndex=0;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
  quoteAlter=q=>q.priceImpactPct="0.262";
  assert.equal((await swapToken("TOKEN",settlementSol,"raw:100000000",15,300,1)).success,true);
  for (const impact of ["0.5","0.9",null,"invalid"]) {
    resetSmall(["1"]);quoteFailure=400;quoteFailureIndex=0;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
    quoteAlter=q=>q.priceImpactPct=impact;
    const previous=sends;
    assert.equal((await swapToken("TOKEN",settlementSol,"raw:100000000",15,300,1)).success,false);
    assert.equal(sends,previous);assert.equal(swapRequests.length,0);
  }
  const smallSends = sends;
  resetSmall(["250000","250001"]);
  assert.equal((await smallRecovery()).reason,"small_settlement_value_changed");assert.equal(swapRequests.length,0);
  for (const alter of [q=>q.otherAmountThreshold="242499",q=>q.otherAmountThreshold="250001",
      q=>q.otherAmountThreshold="0",q=>delete q.otherAmountThreshold,q=>q.slippageBps=500,
      q=>q.swapMode="ExactOut",q=>q.inAmount="100000001",q=>q.inputMint="OTHER",q=>q.outputMint="OTHER"]) {
    resetSmall();quoteAlter=(q,i)=>{if(i===1)alter(q);};
    assert.equal((await smallRecovery()).success,false);assert.equal(swapRequests.length,0);
  }
  for (const value of ["invalid", "-1", "1.5", "0"]) {
    resetSmall([value]);
    if(value==="0") await assert.rejects(smallRecovery(),/empty quote/);
    else assert.equal((await smallRecovery()).reason,"net_recovery_invalid_quote");
    assert.deepEqual(quoteCalls,[100]);assert.equal(swapRequests.length,0);
  }
  resetSmall();quoteFailure=400;
  assert.equal((await smallRecovery()).reason,"swap_no_route");assert.equal(swapRequests.length,0);
  resetSmall();quoteFailure=429;
  await assert.rejects(smallRecovery(),/429/);assert.equal(swapRequests.length,0);
  resetSmall();quoteFailure=400;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
  assert.equal((await smallRecovery()).reason,"swap_quote_threshold_unavailable");
  assert.equal(swapRequests.length,0);
  assert.deepEqual(quoteCalls,[100,300,0]);
  resetSmall(["250000","250000","1"]);quoteFailure=400;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
  const beforeDustSend=sends;
  assert.equal((await swapToken("TOKEN",settlementSol,"raw:100000000",15,100,1000000000,true)).reason,"net_recovery_below_floor");
  assert.equal(sends,beforeDustSend);
  resetSmall(["250000","250000","1"]);quoteFailure=400;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
  quoteAlter=(q,i)=>{if(i===2)q.otherAmountThreshold="0";};
  assert.equal((await smallRecovery()).reason,"swap_quote_threshold_unavailable");assert.equal(swapRequests.length,0);
  resetSmall();quoteFailure=429;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";
  await assert.rejects(smallRecovery(),/429/);assert.equal(swapRequests.length,0);
  for (const impact of [undefined,null,false,""," ","NaN","Infinity","0.01junk","-0.1","1.01",{},[]]) {
    resetSmall();quoteAlter=q=>q.priceImpactPct=impact;
    const beforeImpactSends=sends, beforeImpactSigns=swapSigns;
    assert.equal((await smallRecovery()).reason,"price_impact_unmeasured");
    assert.equal(swapRequests.length,0);
    assert.equal(sends,beforeImpactSends);assert.equal(swapSigns,beforeImpactSigns);
  }
  resetSmall();quoteAlter=q=>q.priceImpactPct="0.16";
  assert.equal((await smallRecovery()).reason,"price_impact_exceeded");assert.equal(swapRequests.length,0);
  resetSmall();accountExists=true;
  assert.equal((await smallRecovery()).reason,"settlement_position_still_open");assert.equal(swapRequests.length,0);accountExists=false;
  resetSmall();inventoryProof={success:false,reason:"settlement_inventory_unproven"};
  assert.equal((await smallRecovery()).reason,"settlement_inventory_unproven");assert.deepEqual(quoteCalls,[]);
  inventoryProof={success:true,amount_raw:"100000000",wallet_balance_raw:"100000000",slot:10};
  resetSmall();Connection.prototype.simulateTransaction=async()=>({context:{slot:10},value:{err:null,accounts:[{lamports:10000}]}});
  assert.equal((await smallRecovery()).reason,"net_recovery_below_floor");
  assert.equal(sends,smallSends); // Every invalid/under-floor case stayed unsigned.
  Connection.prototype.simulateTransaction=async()=>({context:{slot:10},value:{err:null,accounts:[{lamports:300000}]}});
  resetSmall();
  const pendingSmall = path.join(root,"memories/dlmm_pending_swaps",`${wallet.publicKey}-TOKEN-${settlementSol}.json`);
  fs.writeFileSync(pendingSmall,JSON.stringify({signature:"pending-small",lastValidBlockHeight:150}));
  signatureStatus={confirmationStatus:"processed",err:null};
  assert.equal((await smallRecovery()).pending,true);assert.deepEqual(quoteCalls,[]);assert.equal(sends,smallSends);
  fs.rmSync(pendingSmall);signatureStatus=null;
  // Strict one-lamport fallback: eligibility predicates and exact zero-step binding.
  // Every refusal here must build no /swap request, sign nothing and send nothing.
  const thresholdAt=indexes=>{quoteFailure=400;quoteFailureIndex=indexes;quoteErrorCode="CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD";};
  const refusedUnsigned=async(call,reason,calls)=>{
    const s=sends,g=swapSigns;const r=await call();
    assert.equal(r.success,false);if(reason)assert.equal(r.reason,reason);if(calls)assert.deepEqual(quoteCalls,calls);
    assert.equal(swapRequests.length,0);assert.equal(sends,s);assert.equal(swapSigns,g);
  };
  // (a) Without a net-recovery floor there is no zero-slippage requote.
  resetSmall(["1"]);thresholdAt(0);
  await refusedUnsigned(()=>swapToken("TOKEN",settlementSol,"raw:100000000",15,300,null),"swap_quote_threshold_unavailable",[300]);
  // (b) Without owned settlement inventory there is no zero-slippage requote.
  delete env.DLMM_SETTLEMENT_POSITION;
  resetSmall(["1"]);thresholdAt(0);
  await refusedUnsigned(()=>swapToken("TOKEN",settlementSol,0.1,15,300,1),"swap_quote_threshold_unavailable",[300]);
  env.DLMM_SETTLEMENT_POSITION=settlementPosition;
  // (c) A one-lamport quote at ordinary slippage keeps the ordinary impact ceiling.
  resetSmall(["1"]);quoteAlter=q=>q.priceImpactPct="0.262";
  await refusedUnsigned(()=>swapToken("TOKEN",settlementSol,"raw:100000000",15,100,1),"price_impact_exceeded",[100]);
  // (d) The zero-slippage quote must stay exact: mode, echo, amounts and mints.
  for (const alter of [q=>q.swapMode="ExactOut",q=>q.slippageBps=50,q=>q.inAmount="100000001",
      q=>q.inputMint="OTHER",q=>q.outputMint="OTHER",q=>q.outAmount="2",q=>q.otherAmountThreshold="2"]) {
    resetSmall(["250000","250000","1"]);thresholdAt(1);quoteAlter=(q,i)=>{if(i===2)alter(q);};
    await refusedUnsigned(smallRecovery,null,[100,300,0]);
  }
  // (e) A second threshold failure at zero slippage ends the ladder: no fourth quote.
  resetSmall(["250000","250000","1"]);thresholdAt(new Set([1,2]));
  await refusedUnsigned(smallRecovery,"swap_quote_threshold_unavailable",[100,300,0]);
  assert.deepEqual(quoteDelays,[2100,2100]);
  resetSmall();
  await assert.rejects(swapToken("TOKEN","SOL","raw:100000000",15,300,1,true),/Small-settlement allowance/);
  await assert.rejects(swapToken("TOKEN","SOL","raw:100000000",15,100,null,true),/Small-settlement allowance/);
  delete env.DLMM_SETTLEMENT_POSITION;
  await assert.rejects(smallRecovery(),/Small-settlement allowance/);
  env.DLMM_SETTLEMENT_POSITION=settlementPosition;
  resetSmall();
  assert.equal((await swapToken("TOKEN","SOL","raw:100000000",15,100,1)).success,true);
  assert.deepEqual(quoteCalls,[100]); // No caller opt-in means no widening.
  resetSmall();
  assert.equal((await swapToken("TOKEN","SOL","raw:100000000",15,300,1)).success,true);
  assert.deepEqual(quoteCalls,[300]);assert.deepEqual(quoteDelays,[]); // Emergency/retry ceiling is unchanged.
  sandbox.fetch=atomicFetch;Connection.prototype.simulateTransaction=atomicSimulation;sandbox.setTimeout=originalTimer;
  const afterSmallSends = sends;
  for(const alter of [a=>a.account.data.parsed.info.owner="other",a=>a.account.data.parsed.info.closeAuthority="other",
    a=>a.account.data.parsed.info.tokenAmount.amount="100000001",a=>a.account.data.parsed.info.state="frozen",
    a=>a.account.data.parsed.info.delegate="other",a=>a.account.data.parsed.info.isNative=true]){
    accounts=[eligible()];alter(accounts[0]);
    if(accounts[0].account.data.parsed.info.owner!==owner) await assert.rejects(recover(1),/All 2 RPC endpoints failed/);
    else assert.equal((await recover(1)).reason,accounts[0].account.data.parsed.info.tokenAmount.amount!=="100000000" ? "settlement_inventory_changed" : "net_recovery_below_floor");
  }
  accounts=[eligible(),eligible()];assert.equal((await recover(1)).reason,"settlement_inventory_changed");
  accounts=[eligible()];accountExists=true;assert.equal((await recover(1)).reason,"settlement_position_still_open");accountExists=false;
  combinedError=true;assert.equal((await recover(1)).reason,"net_recovery_below_floor");combinedError=false;
  combinedChanged=true;assert.equal((await recover(1)).reason,"net_recovery_unmeasured");combinedChanged=false;
  fs.writeFileSync(settlementMarker,JSON.stringify({position:settlementPosition,mint:"OTHER"}));
  await assert.rejects(recover(1),/Settlement marker mismatch/);
  fs.writeFileSync(settlementMarker,JSON.stringify({position:settlementPosition,mint:"TOKEN"}));
  inventoryProof={success:false,reason:"settlement_inventory_unproven"};
  assert.equal((await recover(1)).reason,"settlement_inventory_unproven");
  inventoryProof={success:true,amount_raw:"0"};
  const legacyFetch=sandbox.fetch;
  sandbox.fetch=async()=>{throw new Error("Legacy dust must not be quoted or sold");};
  assert.equal((await recover(1)).settled,true);
  inventoryProof={success:true,amount_raw:"50000000",wallet_balance_raw:"100000000",slot:10};
  assert.equal((await recover(1)).reason,"settlement_amount_mismatch");
  sandbox.fetch=async url=>({ok:true,json:async()=>url.includes("/quote?")
    ? {inputMint:"TOKEN",outputMint:"So11111111111111111111111111111111111111112",inAmount:"50000000",outAmount:"5000",otherAmountThreshold:"4500",priceImpactPct:"0"}
    : {swapTransaction:"AA=="}});
  // Selling the owned half cannot close the ATA containing the legacy half.
  assert.equal((await swapToken("TOKEN","So11111111111111111111111111111111111111112","raw:50000000",5,100,1)).reason,"net_recovery_below_floor");
  sandbox.fetch=async()=>({ok:true,json:async()=>({inputMint:"TOKEN",outputMint:"So11111111111111111111111111111111111111112",inAmount:"100000000",outAmount:"5000"})});
  assert.equal((await swapToken("TOKEN","So11111111111111111111111111111111111111112","raw:50000000",5,100,1)).reason,"settlement_quote_mismatch");
  sandbox.fetch=legacyFetch;
  assert.equal(sends,afterSmallSends);
  delete deps["child_process"];
  fs.rmSync(settlementMarker);delete env.DLMM_SETTLEMENT_POSITION;accountExists=true;
  // Healthy swap-only recovery never spends account/lookup RPCs for optional rent.
  const readBefore=accountReads;Connection.prototype.simulateTransaction=async()=>({context:{slot:10},value:{err:null,accounts:[{lamports:14600}]}});
  assert.equal((await recover(4100)).success,true);assert.equal(accountReads,readBefore);
  delete deps["@solana/spl-token"];
  sandbox.fetch = async () => ({ok:false,status:400,text:async()=>JSON.stringify({errorCode:"COULD_NOT_FIND_ANY_ROUTE"})});
  assert.equal((await recover()).reason, "swap_no_route");
  sandbox.fetch = async () => ({ok:false,status:429,text:async()=>JSON.stringify({errorCode:"COULD_NOT_FIND_ANY_ROUTE"})});
  await assert.rejects(recover(), /quote/);
  sandbox.fetch = oldFetch;
  Connection.prototype.getBalanceAndContext = defaultBalance;
  Connection.prototype.simulateTransaction = defaultSimulation;
  sends = 0;
  confirmTimeout = true;
  signatureStatus = { confirmationStatus: "confirmed", err: null };
  await confirmSignedTransaction(new Connection(), { signature: "signature", blockhash: "exact-blockhash", lastValidBlockHeight: 150 });
  signatureStatus = null;
  await assert.rejects(confirmSignedTransaction(new Connection(), { signature: "signature" }), /timeout/);
  confirmTimeout = false;
  vm.runInNewContext("findPoolForPosition = async () => ({pool: testPool, positionData: {publicKey: testWallet.publicKey, positionData: {lowerBinId: 0, upperBinId: 1}}});", Object.assign(sandbox, {testPool: pool}));
  // A failed HTTP status query rotates RPCs with the SAME signed bytes. No
  // WebSocket method is available on this connection fixture.
  let confirmationAttempts = 0;
  Connection.prototype.getSignatureStatuses = async () => {
    if (++confirmationAttempts === 1) throw new Error("HTTP timeout");
    return { value: [{confirmationStatus:"confirmed",err:null}] };
  };
  assert.equal((await closePosition("deadline-position")).success, true);
  assert.equal(confirmationAttempts, 2);
  const preparationPath = path.join(root, "memories/dlmm_close_preparations.jsonl");
  const preparation = fs.readFileSync(preparationPath, "utf8").trim().split("\n").map(JSON.parse)
    .filter(row => row.position === "deadline-position");
  assert.deepEqual(preparation.map(row => row.stage), ["started", "lock_acquired", "lookup_started",
    "lookup_completed", "withdrawal_build_started", "withdrawal_build_completed", "blockhash_started",
    "blockhash_completed", "signed_and_persisted", "confirmation_completed", "completed"]);
  assert.equal(new Set(preparation.map(row => row.attempt)).size, 1);
  assert.ok(preparation.every((row, i) => row.since_previous_ms >= 0 &&
    (!i || row.elapsed_ms >= preparation[i-1].elapsed_ms)));
  assert.equal(preparation.find(row => row.stage === "signed_and_persisted").signature, "signature");
  assert.ok(!JSON.stringify(preparation).includes("fake-rpc"));
  // Optional telemetry failure cannot interrupt withdrawal or confirmation.
  fs.renameSync(preparationPath, preparationPath + ".saved");
  fs.mkdirSync(preparationPath);
  try {
    assert.equal((await closePosition("unwritable-journal-position")).success, true);
  } finally {
    fs.rmdirSync(preparationPath);
    fs.renameSync(preparationPath + ".saved", preparationPath);
  }
  // Null/processed responses are pending, even when they have err:null. Poll
  // the original signature until confirmed, without another broadcast.
  const observedStatuses = [null,{confirmationStatus:"processed",err:null},{confirmationStatus:"confirmed",err:null}];
  let statusReads=0;
  Connection.prototype.getSignatureStatuses=async(signatures,options)=>{
    assert.deepEqual(Array.from(signatures),["read-only-signature"]);
    assert.equal(options.searchTransactionHistory,true);
    return {value:[observedStatuses[statusReads++]]};
  };
  const confirmationSends=sends;
  await confirmSignedTransaction(new Connection(),{signature:"read-only-signature"},null);
  assert.equal(statusReads,3);assert.equal(sends,confirmationSends);
  // A bounded observation window cannot prove expiry or success. Existing
  // pending-marker tests below still require finalized height for expiry.
  statusReads=0;const pendingClock=fixtureClock;
  Connection.prototype.getSignatureStatuses=async()=>{statusReads++;return {value:[null]};};
  await assert.rejects(confirmSignedTransaction(new Connection(),{signature:"unknown"},null),/confirmation timeout/);
  assert.ok(fixtureClock-pendingClock>=7900);assert.ok(statusReads<=10);assert.equal(sends,confirmationSends);
  Connection.prototype.getSignatureStatuses = signatureStatusQuery;
  sendError = true;
  const beforeClose = sends;
  assert.equal((await closePosition("position")).pending, true);
  const closeMarker = path.join(root, "memories/dlmm_pending_closes/position.json");
  assert.ok(fs.existsSync(closeMarker)); // persisted before broadcast, survives process restart
  assert.equal(sends, beforeClose + 2); // same signed close retried on both RPCs
  assert.equal(closeBytes.at(-1), closeBytes.at(-2));
  accountExists = false;
  assert.equal((await closePosition("position")).reconciled, true);
  assert.equal(sends, beforeClose + 2); // restart reconciles disappearance without resending
  accountExists = true; sendError = false; sends = 0;
  failNextSend = true;
  assert.equal((await closePosition("position")).success, true);
  assert.equal(sends, 2);
  assert.equal(closeBytes.at(-1), closeBytes.at(-2));
  sends = 0;
  const settlementDir = path.join(root, "memories/dlmm_settlements");
  fs.mkdirSync(settlementDir, { recursive: true });
  fs.writeFileSync(path.join(settlementDir, "position.json"), "{}");
  await assert.rejects(deploy(), /awaiting verified SOL settlement/);
  for (const reason of ["swap_no_route", "net_recovery_below_floor"]) {
    fs.writeFileSync(path.join(settlementDir, "position.json"), JSON.stringify({state:"deferred",reason}));
    const unlock = await acquireDeployLock(wallet.publicKey.toString());
    try { await assert.rejects(deploy(), /BUSY/); } finally { await unlock(); }
  }
  fs.writeFileSync(path.join(settlementDir, "position.json"), JSON.stringify({state:"deferred",reason:"unknown"}));
  await assert.rejects(deploy(), /awaiting verified SOL settlement/);
  fs.writeFileSync(path.join(settlementDir, "position.json"), JSON.stringify({state:"deferred",reason:"swap_quote_threshold_unavailable"}));
  await assert.rejects(deploy(), /awaiting verified SOL settlement/);
  fs.rmSync(settlementDir, { recursive: true });
  assert.equal(sends, 0);
  assert.equal(slippageBpsToPercent(1000), 10);
  assert.equal(positionIsEmpty({ positionData: { liquidityShares: [{ isZero: () => true }] } }), true);
  assert.equal(positionIsEmpty({ positionData: { liquidityShares: [{ isZero: () => false }] } }), false);
  assert.equal(positionIsEmpty({ positionData: {} }), null);
  assert.throws(() => slippageBpsToPercent(0), /positive integer/);
  assert.doesNotMatch(source, /const latestBlockHash = await connection\.getLatestBlockhash/);
  assert.match(source, /blockhash, lastValidBlockHeight, signature: txid/);
  const swapMarker = path.join(root, "pending-swap.json");
  fs.writeFileSync(swapMarker, JSON.stringify({ signature: "swap-sig", lastValidBlockHeight: 150,
    inputAmount: "10", outputAmount: "20" }));
  signatureStatus = null; height = 100;
  assert.equal((await reconcilePendingSwap(new Connection(), swapMarker)).pending, true);
  signatureStatus = { confirmationStatus: "confirmed", err: null };
  const reconciled = await reconcilePendingSwap(new Connection(), swapMarker);
  assert.equal(reconciled.success, true); assert.equal(reconciled.txHash, "swap-sig");
  assert.ok(!fs.existsSync(swapMarker));
  fs.writeFileSync(swapMarker, JSON.stringify({signature:'route-failure', lastValidBlockHeight:150,
    routeContext:{position:'test-route',dex:'Hadron',jupiter_instruction:2}}));
  signatureStatus = {confirmationStatus:'confirmed',err:{InstructionError:[2,{Custom:6001}]}};
  assert.equal(await reconcilePendingSwap(new Connection(), swapMarker), null);
  assert.equal(require('./dlmm_route_retry').excluded(swapMarker, 'test-route'), 'Hadron');
  fs.rmSync(swapMarker+'.route');
  // A failure seen only at "processed" is not a verdict: the block can be dropped
  // and the same signed bytes still land before expiry. Keep the marker and report
  // pending so no new swap is signed, and record no route exclusion from it.
  fs.writeFileSync(swapMarker, JSON.stringify({signature:'processed-failure', lastValidBlockHeight:150,
    routeContext:{position:'test-route',dex:'Hadron',jupiter_instruction:2}}));
  signatureStatus = {confirmationStatus:'processed',err:{InstructionError:[2,{Custom:6001}]}};
  const processedFailure = await reconcilePendingSwap(new Connection(), swapMarker);
  assert.equal(processedFailure?.pending, true); assert.equal(processedFailure.txHash, 'processed-failure');
  assert.ok(fs.existsSync(swapMarker));
  assert.ok(!fs.existsSync(swapMarker+'.route'));
  // Once the failure is confirmed, the marker clears and the retry may proceed.
  signatureStatus = {confirmationStatus:'confirmed',err:{InstructionError:[2,{Custom:6001}]}};
  assert.equal(await reconcilePendingSwap(new Connection(), swapMarker), null);
  assert.ok(!fs.existsSync(swapMarker));
  fs.rmSync(swapMarker+'.route', {force:true});
  fs.writeFileSync(swapMarker, JSON.stringify({ signature: "expired", lastValidBlockHeight: 150 }));
  signatureStatus = null; height = 151;
  assert.equal(await reconcilePendingSwap(new Connection(), swapMarker), null);
  assert.ok(!fs.existsSync(swapMarker));
  height = 100;
  // The OS lock excludes another process, not only another Promise.
  const release = await acquireDeployLock(wallet.publicKey.toString());
  await assert.rejects(acquireDeployLock(wallet.publicKey.toString()), /ENTRY BUSY/);
  const code = `const net=require('net');const s=net.createServer();s.on('error',e=>process.exit(e.code==='EADDRINUSE'?0:2));s.listen(${JSON.stringify("\0azimuth-dlmm-entry-" + wallet.publicKey)},()=>s.close(()=>process.exit(3)));`;
  execFileSync(process.execPath, ["-e", code]);
  await release();
  await (await acquireDeployLock(wallet.publicKey.toString()))();
  const parallel = await Promise.allSettled([deploy(), deploy()]);
  assert.equal(parallel.filter((r) => r.status === "fulfilled" && r.value.success).length, 1);
  assert.equal(lastSlippage, 10);
  assert.equal(sends, 1);
  assert.equal(lastMaxRetries, 20);
  assert.equal((await deploy()).pending, true); // prior blockhash still valid
  assert.equal(sends, 1);
  const provenance = JSON.parse(fs.readFileSync(path.join(root, "memories/dlmm_entries/position-1.json")));
  assert.deepEqual(provenance.signal.entry_live_gates, entryGates);
  assert.equal(provenance.dev, "developer");
  assert.equal(provenance.signal.holders, 0); assert.equal(provenance.signal.unique_traders, 100);
  assert.equal(provenance.mode, "turnover"); assert.equal(provenance.recenter_of, "root");
  assert.equal(provenance.pool, "pool");
  assert.equal(provenance.bin_step, 100);
  height = 151;
  positions = [{ publicKey: key("existing"), account: { lbPair: key("pool") } }];
  assert.match((await deploy()).error, /pool already has position/); assert.equal(sends, 1);
  positions[0].account.lbPair = key("sibling-pool");
  await assert.rejects(assertNoTokenExposure(pool, wallet), /token already exposed/);
  positions = []; clearMarker();
  sendError = true;
  const uncertain = await deploy();
  assert.equal(uncertain.pending, true); assert.equal(sends, 3); // same bytes via both RPCs, no second mint
  const pendingEntry = JSON.parse(fs.readFileSync(path.join(root, `memories/dlmm_entries/${uncertain.position}.json`)));
  assert.equal(pendingEntry.dev, "developer");
  assert.equal(pendingEntry.signal.unique_traders, 100);
  height = 100;
  assert.equal((await deploy()).pending, true); assert.equal(sends, 3);
  clearMarker(); sendError = false;
  const beforeReserve = sends;
  const entriesBeforeReserve=fs.readdirSync(path.join(root,"memories/dlmm_entries")).length;
  for (const post of [163759911,199999999,undefined]) {
    reservePost=post;
    assert.match((await deploy()).error,/native reserve/);
    assert.equal(sends,beforeReserve);
    assert.equal(fs.readdirSync(path.join(root,"memories/dlmm_entries")).length,entriesBeforeReserve);
  }
  reservePost=200000000; reserveError="failed";
  assert.match((await deploy()).error,/unmeasured/);
  reserveError=null;reserveChanged=true;
  assert.match((await deploy()).error,/unmeasured/);
  reserveChanged=false;reservePost=300000000;
  clearMarker(); sendError = false; buildError = true;
  await assert.rejects(deploy(), /RPC endpoints failed/);
  assert.equal(sends, 3); assert.ok(!fs.existsSync(marker));
  buildError = false;
  const wide = await deployPosition("pool", 0, 0.1, 80, 0, "bid_ask", 1000);
  assert.equal(wide.pending, true); assert.equal(sends, 4); // partial mint never re-minted/closed blindly
  clearMarker(); confirmationError = true;
  assert.equal((await deploy()).success, false); assert.equal(sends, 6);
  clearMarker();
  fs.writeFileSync(marker, "broken");
  await assert.rejects(deploy(), /RPC endpoints failed/); assert.equal(sends, 6);
  await assert.rejects(deployPosition("pool", 0, -1, 20, 0), /Invalid deploy/);
  clearMarker(); height = 151; confirmationError = false;
  reservePost=200000000; // exact reserve boundary remains permitted
  assert.equal((await deploy()).success, true); assert.equal(sends, 7); // expired reservation recovers
  clearMarker();reservePost=300000000;
  const oldCreates=pool.createExtendedEmptyPosition;
  pool.createExtendedEmptyPosition=async()=>[transaction(),transaction()];
  let reserveSteps=0;
  Connection.prototype.simulateTransaction=async()=>({context:{slot:10},value:{err:null,accounts:[{lamports:++reserveSteps===1?300000000:199999999}]}});
  const partialReserve=await deployPosition("pool",0,0.1,80,0,"bid_ask",1000);
  assert.equal(partialReserve.pending,true);assert.equal(sends,8);
  assert.match(partialReserve.error,/native reserve/);
  pool.createExtendedEmptyPosition=oldCreates;
  Connection.prototype.simulateTransaction=defaultSimulation;
  clearMarker();
  const beforeRetry = { sends, builds, bytes: closeBytes.length };
  sandbox.snapshotStub = async (_pool, lower, upper) => ({ts: 100,
    bins: Array.from({length: upper-lower+1}, (_, i) => ({id: lower+i}))});
  vm.runInNewContext("binSnapshot = snapshotStub;", sandbox);
  failNextSend = true;
  const recoveredDeploy = await deploy();
  assert.equal(recoveredDeploy.success, true);
  assert.equal(sends-beforeRetry.sends, 2);
  assert.equal(builds-beforeRetry.builds, 1);
  assert.equal(new Set(closeBytes.slice(beforeRetry.bytes)).size, 1);
  const deployMarker = JSON.parse(fs.readFileSync(marker));
  assert.equal(deployMarker.position, recoveredDeploy.position);
  assert.equal(deployMarker.signature, recoveredDeploy.txHashes[0]);
  const recordedEntry = JSON.parse(fs.readFileSync(path.join(root, "memories/dlmm_entries", recoveredDeploy.position + ".json")));
  assert.equal(recordedEntry.bins_below, 20);
  assert.equal(recordedEntry.bin_snapshot.bins.length, 21);
  assert.equal(recordedEntry.width_study.snapshot.bins.length, 70);
  assert.equal(recordedEntry.width_study.lower_bin, -69);
  vm.runInNewContext("binSnapshot = originalSnapshot;", sandbox);
  clearMarker();
  // A broadcast error can follow a landed transaction. Reconcile its signed
  // signature before trying another RPC, keeping exactly one build and send.
  sendError = true;
  const beforeLanded = { sends, builds };
  signatureStatus = { confirmationStatus: "finalized", err: null };
  const landed = await deploy();
  assert.equal(landed.success, true);
  assert.equal(landed.txHash, "signature");
  assert.equal(sends-beforeLanded.sends, 1);
  assert.equal(builds-beforeLanded.builds, 1);
  clearMarker();
  sendError=false;signatureStatus=null;
  const canceledBeforeBuild=pdaHistoryCancels, signedBeforeBuild=signCalls, sentBeforeBuild=sends;
  buildError=true;
  await assert.rejects(deploy(),/RPC endpoints failed/);
  buildError=false;
  assert.equal(pdaHistoryCancels,canceledBeforeBuild+1);
  assert.equal(signCalls,signedBeforeBuild);assert.equal(sends,sentBeforeBuild);
  pdaMode="success";
  const pdaBefore=sends;
  const canceledBeforePda=pdaHistoryCancels;
  const pdaEntry=await deploy();
  assert.equal(pdaEntry.success,true);assert.equal(pdaEntry.position,"pda-success");
  assert.equal(pdaHistoryCancels,canceledBeforePda+1);
  assert.equal(sends,pdaBefore+1);assert.deepEqual(lastSignedKeys,[wallet.publicKey.toString()]);
  const pdaFile=path.join(root,"memories/dlmm_entries/pda-success.json");
  const pdaProvenance=fs.readFileSync(pdaFile,"utf8");
  assert.equal(JSON.parse(pdaProvenance).position_creation.kind,"wallet_pda");
  assert.equal(JSON.parse(fs.readFileSync(marker)).position,pdaEntry.position);
  clearMarker();
  await assert.rejects(deploy(),/RPC endpoints failed/); // exclusive create protects a racing journal
  assert.equal(fs.readFileSync(pdaFile,"utf8"),pdaProvenance);assert.equal(sends,pdaBefore+1);
  pdaMode="simulation-fallback";
  let pdaSimulations=0;
  Connection.prototype.simulateTransaction=async (tx,options)=>{
    pdaSimulations++;
    return tx.message.pda ? {context:{slot:10},value:{err:"AlreadyInUse",accounts:[{lamports:300000000}]}}
      : defaultSimulation.call(new Connection(),tx,options);
  };
  const fallbackEntry=await deploy();
  assert.equal(fallbackEntry.success,true);assert.match(fallbackEntry.position,/^position-/);
  assert.equal(pdaSimulations,2);assert.equal(lastSignedKeys.length,2);
  assert.equal(JSON.parse(fs.readFileSync(path.join(root,"memories/dlmm_entries",fallbackEntry.position+".json"))).position_creation.kind,"keypair");
  assert.equal(fs.existsSync(path.join(root,"memories/dlmm_entries/pda-simulation-fallback.json")),false);
  Connection.prototype.simulateTransaction=defaultSimulation;clearMarker();
  pdaMode="reserve-floor";reservePost=199999999;
  const beforePdaFloor=sends;
  assert.match((await deploy()).error,/native reserve/);assert.equal(sends,beforePdaFloor);
  assert.equal(fs.existsSync(path.join(root,"memories/dlmm_entries/pda-reserve-floor.json")),false);
  reservePost=300000000;
  pdaMode="throw";assert.equal((await deploy()).success,true);assert.equal(lastSignedKeys.length,2);clearMarker();
  pdaMode="uncertain";sendError=true;
  const uncertainPdaBefore={builds,sends,bytes:closeBytes.length};
  const uncertainPda=await deploy();
  assert.equal(uncertainPda.pending,true);assert.equal(uncertainPda.position,"pda-uncertain");
  assert.equal(builds-uncertainPdaBefore.builds,1);assert.equal(sends-uncertainPdaBefore.sends,2);
  assert.equal(new Set(closeBytes.slice(uncertainPdaBefore.bytes)).size,1);
  assert.deepEqual(lastSignedKeys,[wallet.publicKey.toString()]);
  const callsBeforePending=pdaCalls;
  height=100;
  assert.equal((await deploy()).pending,true);assert.equal(pdaCalls,callsBeforePending);
  pdaMode=null;sendError=true;signatureStatus={confirmationStatus:"finalized",err:null};height=151;clearMarker();
  const closeSends = sends;
  assert.equal((await closePosition("landed-close")).success, true);
  assert.equal(sends-closeSends, 2);
  const signed = { signature: "signature", blockhash: "exact-blockhash", lastValidBlockHeight: 150 };
  for (const status of [null, {confirmationStatus:"processed",err:null},
      {confirmationStatus:"confirmed"}, {confirmationStatus:"confirmed",err:false},
      {confirmationStatus:"finalized",err:"chain failure"}]) {
    signatureStatus = status;
    await assert.rejects(confirmSignedTransaction(new Connection(), signed, Buffer.from("exact-blockhash")));
  }
  Connection.prototype.getSignatureStatuses = async () => { throw new Error("status offline"); };
  await assert.rejects(confirmSignedTransaction(new Connection(), signed, Buffer.from("exact-blockhash")), /status offline/);
  Connection.prototype.getSignatureStatuses = signatureStatusQuery;
  signatureStatus = null; sendError = false;
  confirmationError = true;
  const failedSwap = await swapToken("So11111111111111111111111111111111111111112", "TOKEN", 0.1);
  assert.equal(failedSwap.success, false);
  assert.equal(failedSwap.pending, undefined); // explicit chain failure is definitive
  assert.match(failedSwap.error, /Transaction failed/);
  confirmationError = false;
  deps["./dlmm_nav.js"] = {...require("./dlmm_nav.js"), collect: async () => ({})};
  deps.child_process = {execFileSync: () => JSON.stringify({allow:false,reason:"incomplete_chain"})};
  await assert.rejects(sandbox.module.exports.assertRootBudget(), /ENTRY REFUSED: incomplete_chain/);
  deps.child_process.execFileSync = () => JSON.stringify({allow:true});
  await sandbox.module.exports.assertRootBudget();
  const journal = path.join(root, "memories/dlmm_transactions.jsonl");
  const written = fs.readFileSync(journal, "utf8").trim().split("\n").map(JSON.parse);
  assert.ok(written.some(e => e.kind === "deploy" && e.root_chain_id === "root"));
  assert.ok(written.some(e => e.kind === "close"));
  fs.writeFileSync(journal, "");
  const { recordSubmission, reconcileAccounting } = sandbox.module.exports;
  const append = fs.appendFileSync;
  fs.appendFileSync = () => { throw new Error("disk full"); };
  try {
    assert.throws(() => recordSubmission(wallet, "position-1", "deploy", "blocked", 150), /disk full/);
    assert.doesNotThrow(() => recordSubmission(wallet, "position-1", "close", "exit", 150));
  } finally { fs.appendFileSync = append; }
  recordSubmission(wallet, "position-1", "deploy", "measured", 150);
  recordSubmission(wallet, "position-1", "deploy", "missing", 150);
  let measuredReads = 0;
  Connection.prototype.getParsedTransaction = async signature => signature === "missing" ? null : (measuredReads++, {
    slot: 100, blockTime: 200,
    transaction: {message: {accountKeys: [{pubkey: wallet.publicKey}], instructions: []}},
    meta: {err: null, fee: 5000, preBalances: [100000], postBalances: [70000],
      preTokenBalances: [], postTokenBalances: [{owner: wallet.publicKey.toString(), mint: "TOKEN",
        uiTokenAmount: {amount: "9007199254740993"}}]},
  });
  const warnings=[];
  sandbox.console.warn=message=>warnings.push(message);
  assert.equal((await reconcileAccounting()).pending, 1);
  assert.equal((await reconcileAccounting()).pending, 1);
  assert.equal(warnings.some(message=>message.includes('[RPC WARN]')),false);
  fs.appendFileSync(path.join(root,'memories/dlmm_wallet_transactions.jsonl'),JSON.stringify({signature:'missing',wallet:wallet.publicKey.toString(),landed:false,classification:'expired_unlanded'})+'\n');
  const resolved=await reconcileAccounting();
  assert.equal(resolved.pending,0);assert.equal(resolved.expired_unlanded,1);assert.equal(resolved.reconciled,1);
  const facts = fs.readFileSync(path.join(root, "memories/dlmm_wallet_transactions.jsonl"), "utf8").trim().split("\n").filter(line => JSON.parse(line).signature === "measured");
  assert.equal(facts.length, 1); // refresh never counts the same signature twice
  assert.equal(JSON.parse(facts[0]).wallet_delta_lamports, -30000);
  assert.equal(JSON.parse(facts[0]).fee_lamports, 5000);
  assert.equal(JSON.parse(facts[0]).token_deltas_raw.TOKEN, "9007199254740993");
  assert.equal(JSON.parse(facts[0]).schema_version, 12);
  fs.writeFileSync(path.join(root, "memories/dlmm_nav.jsonl"), JSON.stringify({started_at: 100}) + "\n");
  await require("./dlmm_nav.js").collect({dir: path.join(root, "memories"), wallet: wallet.publicKey.toString(),
    PublicKey: function(v) { return key(v); }, historyOnly: true, rpc: fn => fn({
      getBlockHeight: async () => 100, getSlot: async () => 100,
      getSignaturesForAddress: async (_, opts) => opts.limit === 1 ? [{signature: "measured"}] :
        [{signature: "measured", blockTime: 200}, {signature: "old", blockTime: 50}],
      getParsedTransaction: Connection.prototype.getParsedTransaction,
    })});
  assert.equal(measuredReads, 1); // Reconciliation and NAV share one finalized RPC read.
  // Rent maintenance never burns/sells tokens, pays only this wallet, and does
  // not re-broadcast after an uncertain send (including across invocations).
  const { reclaimEmptyAccounts } = sandbox.module.exports;
  const tokenProgram = key("classic-token"), token2022 = key("token2022");
  let fee = 5000;
  deps["@solana/spl-token"] = { TOKEN_PROGRAM_ID: tokenProgram, TOKEN_2022_PROGRAM_ID: token2022,
    createCloseAccountInstruction: (account, destination, authority, signers, program) => {
      assert.equal(destination, wallet.publicKey); assert.equal(authority, wallet.publicKey);
      assert.equal(program.toString(), ["safe-2022","route-2022"].includes(account.toString()) ? "token2022" : "classic-token");
      return account.toString();
    } };
  // Transaction was destructured when the executor loaded; use its injected class.
  let tokenAccounts = [];
  Connection.prototype.getParsedTokenAccountsByOwner = async (_, {programId}) => ({ value: tokenAccounts.filter(a=>a.account.owner.toString()===programId.toString()) });
  Connection.prototype.getLatestBlockhash = async commitment => {
    assert.equal(commitment, "finalized");
    return { blockhash: "exact-blockhash", lastValidBlockHeight: 150 };
  };
  Connection.prototype.getFeeForMessage = async () => ({ value: fee });
  // Match the installed SDK contract: Map<string, PositionInfo>, nested fees.
  const sdkPosition = { publicKey: key("live-position"), positionData: {
    lowerBinId: -1, upperBinId: 1, feeX: key("11"), feeY: key("22") } };
  deps["@meteora-ag/dlmm"].getAllLbPairPositionsByUser = async () => new Map([["pool", { lbPairPositionsData: [sdkPosition] }]]);
  pool.tokenX = {}; pool.tokenY = {};
  const listed = await sandbox.module.exports.sdkPositions();
  assert.equal(listed.length, 1); assert.equal(listed[0].position, "live-position");
  assert.equal(listed[0].feeX, "11"); assert.equal(listed[0].feeY, "22");
  assert.equal(listed[0].tokenX, "TOKEN"); assert.equal(listed[0].in_range, true);
  sandbox.fetch = async () => { throw new Error("Unexpected portfolio API fallback"); };
  assert.equal((await sandbox.module.exports.sdkFindPool(new Connection(), wallet, "live-position")).positionData, sdkPosition);
  const account = (name, overrides = {}, accountOverrides = {}) => ({ pubkey: key(name), account: {
    owner: tokenProgram, lamports: 1488440, data: { parsed: { info: {
      owner: wallet.publicKey.toString(), tokenAmount: { amount: "0" }, state: "initialized",
      isNative: false, mint: "unused-token", ...overrides } } }, ...accountOverrides } });
  tokenAccounts = [account("eligible"), account("nonzero", {tokenAmount: {amount: "1"}}),
    account("active", {mint: "TOKEN"}), account("wrapped", {mint: "So11111111111111111111111111111111111111112"}),
    account("foreign", {owner: "other"}), account("authority", {closeAuthority: "other"}),
    account("frozen", {state: "frozen"}), account("native", {isNative: true}),
    account("delegate", {delegate: "someone"}), account("2022", {}, {owner: token2022}),
    account("safe-2022", {extensions:[{extension:"immutableOwner"}]}, {owner:token2022}),
    account("withheld-2022", {extensions:[{extension:"immutableOwner"},{extension:"transferFeeAmount",state:{withheldAmount:"1"}}]}, {owner:token2022}),
    account("active-2022", {mint:"TOKEN",extensions:[{extension:"immutableOwner"}]}, {owner:token2022}),
    account("unknown-2022", {extensions:[{extension:"unknown"}]}, {owner:token2022})];
  // Observed empty route account: immutableOwner + pausableAccount + idle hook.
  const { tokenAccountCanClose } = sandbox.module.exports;
  const routeExtensions=[{extension:"immutableOwner"},{extension:"pausableAccount"},
    {extension:"transferHookAccount",state:{transferring:false}}];
  const routeAccount=()=>account("route-2022",{extensions:routeExtensions},{owner:token2022});
  assert.equal(tokenAccountCanClose(routeAccount().account,wallet.publicKey.toString()),true);
  for (const extensions of [routeExtensions.concat({extension:"unknown"}),routeExtensions.concat(null),
      routeExtensions.concat({extension:"transferFeeAmount",state:{withheldAmount:"1"}}),
      [{extension:"transferHookAccount",state:{transferring:true}}],
      [{extension:"transferHookAccount",state:{transferring:"false"}}],
      [{extension:"transferHookAccount"}],[]]) {
    assert.equal(tokenAccountCanClose(account("bad-route",{extensions},{owner:token2022}).account,wallet.publicKey.toString()),false);
  }
  for (const info of [{tokenAmount:{amount:"1"}},{owner:"other"},{closeAuthority:"other"},
      {delegate:"other"},{isNative:true},{state:"frozen"}]) {
    assert.equal(tokenAccountCanClose(account("bad-route",{extensions:routeExtensions,...info},{owner:token2022}).account,wallet.publicKey.toString()),false);
  }
  assert.equal(tokenAccountCanClose(account("nonempty-route",{extensions:routeExtensions,tokenAmount:{amount:"1"}},{owner:token2022}).account,wallet.publicKey.toString(),"1"),false);
  // Exercise the actual maintenance path and unchanged active-mint exclusion.
  const previousAccounts=tokenAccounts;
  tokenAccounts=[routeAccount(),account("active-route",{mint:"TOKEN",extensions:routeExtensions},{owner:token2022})];
  assert.deepEqual(Array.from((await reclaimEmptyAccounts()).accounts,a=>a.account),["route-2022"]);
  tokenAccounts=previousAccounts;
  fs.rmSync(path.dirname(marker), {recursive: true, force: true});
  fs.rmSync(path.join(root, "memories/dlmm_pending_swaps"), {recursive: true, force: true});
  const beforeRent = sends;
  const originalHeight = Connection.prototype.getBlockHeight;
  let rentHeightReads = 0;
  Connection.prototype.getBlockHeight = async () => { rentHeightReads++; return height; };
  for (const pendingDir of ["dlmm_pending_deploys", "dlmm_pending_swaps"]) {
    const pendingFile = path.join(root, "memories", pendingDir, "guard-test.json");
    fs.mkdirSync(path.dirname(pendingFile), {recursive: true});
    for (const lastValidBlockHeight of [height, null]) {
      fs.writeFileSync(pendingFile, JSON.stringify({lastValidBlockHeight}));
      rentHeightReads = 0;
      await assert.rejects(reclaimEmptyAccounts(true), /Rent reclaim refused: wait for pending trading blockhash expiry/);
      assert.equal(rentHeightReads, 1); // Policy refusal must not query every RPC.
      assert.equal(sends, beforeRent);
    }
    fs.rmSync(pendingFile);
  }
  rentHeightReads = 0;
  Connection.prototype.getBlockHeight = async () => {
    if (++rentHeightReads === 1) throw new Error("RPC timeout");
    return height;
  };
  assert.equal((await reclaimEmptyAccounts()).eligible, 2);
  assert.equal(rentHeightReads, 2); // Actual provider failures still fail over.
  Connection.prototype.getBlockHeight = originalHeight;
  assert.equal((await reclaimEmptyAccounts()).eligible, 2); assert.equal(sends, beforeRent);
  fee = null;
  await assert.rejects(reclaimEmptyAccounts(true), /unknown or uneconomic/); assert.equal(sends, beforeRent);
  fee = 5000;
  const eligibleSet = tokenAccounts;
  tokenAccounts = Array.from({length: 12}, (_, i) => account(`empty-${i}`));
  const bounded = await reclaimEmptyAccounts();
  assert.equal(bounded.eligible, 12); assert.equal(bounded.accounts.length, 8);
  tokenAccounts = eligibleSet; env.DRY_RUN = "true";
  assert.equal((await reclaimEmptyAccounts(true)).dry_run, true); assert.equal(sends, beforeRent);
  delete env.DRY_RUN;
  const releaseRentLock = await acquireDeployLock(wallet.publicKey.toString());
  try { await assert.rejects(reclaimEmptyAccounts(true), /ENTRY BUSY/); }
  finally { await releaseRentLock(); }
  env.DLMM_ENTRY_ID = "must-not-attribute-rent-to-entry";
  tokenAccounts.push(routeAccount());
  const reclaimed = await reclaimEmptyAccounts(true);
  assert.equal(reclaimed.recovered_lamports_before_fee, 4465320); assert.equal(sends, beforeRent + 1);
  assert.deepEqual(rentInstructions, ["eligible", "safe-2022", "eligible", "safe-2022", "route-2022"]); // fee rejection builds but never sends
  const rentEvent = JSON.parse(fs.readFileSync(journal, "utf8").trim().split("\n").at(-1));
  assert.equal(rentEvent.kind, "rent_reclaim"); assert.equal(rentEvent.entry_id, null); assert.equal(rentEvent.root_chain_id, null);
  signatureStatus = null; sendError = true; confirmTimeout = true; height = 100;
  await assert.rejects(reclaimEmptyAccounts(true), /confirmation timeout/);
  assert.equal(sends, beforeRent + 2);
  assert.equal((await reclaimEmptyAccounts(true)).pending, true); assert.equal(sends, beforeRent + 2);
  assert.equal((await reclaimEmptyAccounts(true, true)).pending, true); assert.equal(sends, beforeRent + 2);
  signatureStatus = { confirmationStatus: "finalized", err: null };
  assert.equal((await reclaimEmptyAccounts(true)).reconciled, true); assert.equal(sends, beforeRent + 2);
  sendError = false; confirmTimeout = false; signatureStatus = null;
  fs.appendFileSync = () => { throw new Error("disk full"); };
  try { await assert.rejects(reclaimEmptyAccounts(true), /disk full/); assert.equal(sends, beforeRent + 2); }
  finally { fs.appendFileSync = append; }
  signatureStatus = { confirmationStatus: "finalized", err: null };
  assert.equal((await reclaimEmptyAccounts(true, true)).reconciled,true);
  assert.equal(sends,beforeRent+2);signatureStatus=null;
  // Automatic batching reduces fee frequency; a singleton stays recoverable
  // only while native cash above the existing reserve can cover its rent.
  const beforeBatch = sends, balanceReader = Connection.prototype.getBalanceAndContext;
  let batchBalance = 300000000, balanceError = false, batchBalanceReads = 0, feeReads = 0;
  Connection.prototype.getBalanceAndContext = async (_, commitment) => {
    assert.equal(commitment, "finalized");batchBalanceReads++;
    if (balanceError) throw new Error("balance unavailable");
    return { context: {slot: 100}, value: batchBalance };
  };
  Connection.prototype.getFeeForMessage = async () => {feeReads++;return {value:fee};};
  tokenAccounts = [account("eligible")];
  const deferred = await reclaimEmptyAccounts(true, true);
  assert.equal(deferred.deferred, true);assert.equal(deferred.reason, "waiting_for_second_empty_account");
  assert.equal(deferred.batch_minimum_accounts, 2);assert.equal(sends, beforeBatch);assert.equal(feeReads, 0);
  assert.equal(fs.existsSync(path.join(root,"memories/dlmm_pending_rent",wallet.publicKey.toString()+".json")),false);
  batchBalance = 200000000 + 1488440;
  assert.equal((await reclaimEmptyAccounts(true,true)).deferred,true);assert.equal(sends,beforeBatch);
  for (const invalid of [null, true, -1, NaN, Infinity, Number.MAX_SAFE_INTEGER+1]) {
    batchBalance=invalid;
    assert.equal((await reclaimEmptyAccounts(true,true)).reason,"native_balance_unmeasured");
    assert.equal(sends,beforeBatch);assert.equal(feeReads,0);
  }
  balanceError=true;
  assert.equal((await reclaimEmptyAccounts(true,true)).reason,"native_balance_unmeasured");
  balanceError=false;batchBalance=200000000+1488440-1;
  assert.equal((await reclaimEmptyAccounts(true,true)).fee_lamports,5000);assert.equal(sends,beforeBatch+1);
  batchBalance=300000000;tokenAccounts=[account("eligible"),account("safe-2022",{extensions:[{extension:"immutableOwner"}]},{owner:token2022})];
  const readsBeforeBatch=batchBalanceReads;
  assert.equal((await reclaimEmptyAccounts(true,true)).accounts.length,2);assert.equal(sends,beforeBatch+2);
  assert.equal(batchBalanceReads,readsBeforeBatch); // A full batch needs no extra balance RPC.
  tokenAccounts=[account("eligible")];
  assert.equal((await reclaimEmptyAccounts(true)).fee_lamports,5000);assert.equal(sends,beforeBatch+3);
  assert.equal(batchBalanceReads,readsBeforeBatch); // Explicit manual cleanup keeps its old behavior.
  tokenAccounts=[account("eligible",{},{lamports:400000000})];
  assert.equal((await reclaimEmptyAccounts(true,true)).fee_lamports,5000);assert.equal(sends,beforeBatch+4);
  env.DRY_RUN="true";batchBalance=0;
  assert.equal((await reclaimEmptyAccounts(true,true)).dry_run,true);assert.equal(sends,beforeBatch+4);
  delete env.DRY_RUN;
  tokenAccounts=[account("eligible")];batchBalance=343630923;
  const beforeEntryRent=sends;
  const entryReady=await reclaimEmptyAccounts(true,true);
  assert.equal(entryReady.entry_liquidity_floor_lamports,345000000);
  assert.equal(entryReady.entry_liquidity_shortfall_lamports,1369077);
  assert.equal(entryReady.fee_lamports,5000);assert.equal(sends,beforeEntryRent+1);
  assert.equal(batchBalance+entryReady.recovered_lamports_before_fee-entryReady.fee_lamports,345114363);
  batchBalance=345000000-1488440+5000;
  assert.equal((await reclaimEmptyAccounts(true,true)).fee_lamports,5000);assert.equal(sends,beforeEntryRent+2);
  batchBalance--;
  const feeCount=feeReads,signCount=signCalls;
  const stillShort=await reclaimEmptyAccounts(true,true);
  assert.equal(stillShort.reason,"singleton_net_below_entry_floor");
  assert.equal(feeReads,feeCount+1);assert.equal(signCalls,signCount);assert.equal(sends,beforeEntryRent+2);
  assert.equal(fs.existsSync(path.join(root,"memories/dlmm_pending_rent",wallet.publicKey.toString()+".json")),false);
  for(const balance of [345000000,345000000-1488440-1]){
    batchBalance=balance;const beforeFee=feeReads;
    assert.equal((await reclaimEmptyAccounts(true,true)).reason,"waiting_for_second_empty_account");
    assert.equal(feeReads,beforeFee);assert.equal(sends,beforeEntryRent+2);
  }
  batchBalance=343630923;fee=null;
  await assert.rejects(reclaimEmptyAccounts(true,true),/unknown or uneconomic/);
  assert.equal(signCalls,signCount);assert.equal(sends,beforeEntryRent+2);fee=5000;
  Connection.prototype.getBalanceAndContext=balanceReader;
  // Dust mode (opt-in): burn + close only when the full-balance quote is at
  // most half the locked rent; unknown quotes, settlements in flight, active
  // mints and a failing simulation never burn. Default mode never burns.
  {
    deps["@solana/spl-token"].createBurnCheckedInstruction=(acct,mint,authority,amount,decimals,signers,program)=>{
      assert.equal(authority,wallet.publicKey);assert.equal(typeof amount,"bigint");assert.equal(decimals,6);
      assert.equal(program.toString(),"classic-token");return `burn:${acct}:${amount}`;};
    const dustAccount=(name,raw,mint,info={},acct={})=>account(name,{mint,tokenAmount:{amount:raw,decimals:6},...info},acct);
    const SOL_MINT="So11111111111111111111111111111111111111112";
    // A string is the quoted outAmount; {status} is a non-OK response; {out,echo} overrides echoed fields.
    const quotes={"dust-mint":"700000","norout-mint":{status:400,code:"COULD_NOT_FIND_ANY_ROUTE"},"rich-mint":"800000",
      "down-mint":"err","TOKEN":"1","pending-mint":"1"};
    const quoted=[];const originalFetch=sandbox.fetch;
    sandbox.fetch=async url=>{const u=new URL(url),mint=u.searchParams.get("inputMint"),amount=u.searchParams.get("amount");quoted.push(mint);
      assert.equal(u.searchParams.get("outputMint"),SOL_MINT);
      const q=quotes[mint];if(q==="err")throw new Error("quote timeout");
      if(q?.status)return{ok:false,status:q.status,text:async()=>JSON.stringify({errorCode:q.code})};
      return{ok:true,json:async()=>({inputMint:mint,outputMint:SOL_MINT,inAmount:amount,outAmount:q?.out ?? q,...(q?.echo||{})})};};
    let simErr=null,sims=0;const originalSim=Connection.prototype.simulateTransaction;
    Connection.prototype.simulateTransaction=async()=>{sims++;return{context:{slot:10},value:{err:simErr}};};
    const settleDir=path.join(root,"memories/dlmm_settlements");fs.mkdirSync(settleDir,{recursive:true});
    fs.writeFileSync(path.join(settleDir,"pos.json"),JSON.stringify({position:"pos",mint:"pending-mint"}));
    tokenAccounts=[dustAccount("dust","5","dust-mint"),dustAccount("norout","9","norout-mint"),dustAccount("rich","7","rich-mint"),
      dustAccount("down","3","down-mint"),dustAccount("active-dust","4","TOKEN"),dustAccount("pending","2","pending-mint"),account("eligible")];
    const plain=await reclaimEmptyAccounts();
    assert.deepEqual(Array.from(plain.accounts,a=>a.account),["eligible"]);assert.equal(quoted.length,0);
    const dry=await reclaimEmptyAccounts(false,false,true);
    assert.deepEqual(Array.from(dry.accounts,a=>a.account),["eligible","dust"]); // no-route is unknown, never zero
    assert.deepEqual(quoted,["dust-mint","norout-mint","rich-mint","down-mint"]); // active + pending mints are never quoted
    assert.equal(dry.forfeited_quote_lamports,700000);assert.equal(dry.accounts[1].burn_raw,"5");assert.equal(sends,beforeEntryRent+2);
    rentInstructions.length=0;simErr={InstructionError:[0,"Custom"]};
    await assert.rejects(reclaimEmptyAccounts(true,false,true),/simulation failed/);assert.equal(sends,beforeEntryRent+2);
    simErr=null;rentInstructions.length=0;
    const burned=await reclaimEmptyAccounts(true,false,true);
    assert.equal(burned.fee_lamports,5000);assert.equal(sends,beforeEntryRent+3);assert.equal(sims,2);
    assert.deepEqual(rentInstructions,["eligible","burn:dust:5","dust"]);
    quotes["dust-mint"]="2000000";tokenAccounts=[dustAccount("dust","5","dust-mint")]; // quote*2 > rent: keep the tokens
    assert.equal((await reclaimEmptyAccounts(false,false,true)).accounts.length,0);
    // Every answer that is not a matching quote is unknown and keeps even a large
    // balance: no-route codes, rate limits, auth/server errors, mismatched echoes.
    const unknowns={"nr-any":{status:400,code:"COULD_NOT_FIND_ANY_ROUTE"},"nr-none":{status:400,code:"NO_ROUTES_FOUND"},
      "nr-tradable":{status:400,code:"TOKEN_NOT_TRADABLE"},"s400":{status:400,code:"BAD_REQUEST"},"s401":{status:401},
      "s429":{status:429},"s500":{status:500},"echo-amount":{out:"1",echo:{inAmount:"999"}},
      "echo-mint":{out:"1",echo:{inputMint:"other-mint"}},"echo-out":{out:"1",echo:{outputMint:"other-mint"}}};
    Object.assign(quotes,unknowns);quoted.length=0;
    tokenAccounts=Object.keys(unknowns).map(m=>dustAccount(`big-${m}`,"1000000000000",m));
    assert.equal((await reclaimEmptyAccounts(false,false,true)).accounts.length,0);
    assert.deepEqual(quoted,Object.keys(unknowns));
    // Nonzero accounts must pass the closeability rule BEFORE any quote: a second
    // Token-2022 extension or a delegate keeps them; immutableOwner alone is fine.
    Object.assign(quotes,{"t22-fee-mint":"1","t22-ok-mint":"1","delegated-mint":"1"});quoted.length=0;
    tokenAccounts=[dustAccount("t22-fee","5","t22-fee-mint",{extensions:[{extension:"immutableOwner"},{extension:"transferFeeAmount"}]},{owner:token2022}),
      dustAccount("t22-ok","5","t22-ok-mint",{extensions:[{extension:"immutableOwner"}]},{owner:token2022}),
      dustAccount("delegated","5","delegated-mint",{delegate:"someone"})];
    assert.deepEqual(Array.from((await reclaimEmptyAccounts(false,false,true)).accounts,a=>a.account),["t22-ok"]);
    assert.deepEqual(quoted,["t22-ok-mint"]);
    // Quoting stops once eight accounts are admitted, and never exceeds 16 per run.
    quotes["dust-mint"]="700000";quoted.length=0;
    tokenAccounts=Array.from({length:10},(_,i)=>dustAccount(`cheap-${i}`,"5","dust-mint"));
    assert.equal((await reclaimEmptyAccounts(false,false,true)).accounts.length,8);assert.equal(quoted.length,8);
    quoted.length=0;tokenAccounts=Array.from({length:20},(_,i)=>dustAccount(`kept-${i}`,"7","rich-mint"));
    assert.equal((await reclaimEmptyAccounts(false,false,true)).accounts.length,0);assert.equal(quoted.length,16);
    // Fee plus forfeited quotes must stay below the rent: here the fee alone would
    // pass (744220 < 1488440) but fee + forfeited equals the rent, so nothing sends.
    quotes["dust-mint"]="744220";tokenAccounts=[dustAccount("dust","5","dust-mint")];
    const sendsBeforeBoundary=sends;fee=744220;
    await assert.rejects(reclaimEmptyAccounts(true,false,true),/uneconomic/);assert.equal(sends,sendsBeforeBoundary);
    fee=5000;
    fs.writeFileSync(path.join(settleDir,"bad.json"),"{");
    await assert.rejects(reclaimEmptyAccounts(false,false,true),/unreadable settlement marker/);
    fs.rmSync(settleDir,{recursive:true,force:true});
    sandbox.fetch=originalFetch;Connection.prototype.simulateTransaction=originalSim;
  }
  // A route-specific confirmed failure changes only the next owned quote.
  const routeRetry = require('./dlmm_route_retry');
  const routePending = path.join(root, 'memories/dlmm_pending_swaps', `${wallet.publicKey}-TOKEN-So11111111111111111111111111111111111111112.json`);
  fs.rmSync(routePending, {force: true});
  fs.mkdirSync(path.dirname(routePending), {recursive: true});
  env.DLMM_SETTLEMENT_POSITION = 'route-position';
  sandbox.routeInventory = async () => ({success:true, amount_raw:'100000000', wallet_balance_raw:'100000000'});
  vm.runInNewContext('const inventoryBeforeRouteTest = settlementInventory; settlementInventory = routeInventory;', sandbox);
  routeRetry.recordFailure(routePending, {position:'route-position', dex:'Hadron', jupiter_instruction:2}, {InstructionError:[2,{Custom:6001}]});
  const fetchBeforeRoute = sandbox.fetch;
  const sendsBeforeRoute = sends;
  sandbox.fetch = async url => {
    const u = new URL(url);
    assert.equal(u.searchParams.get('excludeDexes'), 'Hadron');
    assert.equal(u.searchParams.get('slippageBps'), '100');
    return {ok:false, status:400, text:async()=>JSON.stringify({errorCode:'NO_ROUTES_FOUND'})};
  };
  assert.equal((await recover(1)).reason, 'swap_route_cooldown_no_route');
  sandbox.fetch = async () => ({ok:true,json:async()=>({routePlan:[{swapInfo:{label:'Hadron'}}]})});
  assert.equal((await recover(1)).reason, 'swap_route_exclusion_unverified');
  sandbox.fetch = async url => {
    assert.equal(new URL(url).searchParams.get('excludeDexes'), 'Hadron');
    return {ok:true,json:async()=>({inputMint:'TOKEN',
      outputMint:'So11111111111111111111111111111111111111112', inAmount:'100000000',
      outAmount:'5000',otherAmountThreshold:'4950',priceImpactPct:'0.06',
      routePlan:[{swapInfo:{label:'Pump.fun Amm'}}]})};
  };
  const unsafeAlternative = await recover(1);
  assert.equal(unsafeAlternative.reason, 'price_impact_exceeded');
  assert.equal(unsafeAlternative.priceImpactPct, 6);
  assert.equal(unsafeAlternative.maxPriceImpactPct, 5);
  assert.equal(sends, sendsBeforeRoute);
  fs.rmSync(routePending+'.route', {force:true});
  delete env.DLMM_SETTLEMENT_POSITION;
  sandbox.fetch = fetchBeforeRoute;
  vm.runInNewContext('settlementInventory = inventoryBeforeRouteTest;', sandbox);
  // Exercise the real CLI parser, not a copy of its option handling.
  let cliSwapArgs;
  sandbox.captureCLISwap = async (...args) => {cliSwapArgs=args;return {success:true};};
  vm.runInNewContext("swapToken = captureCLISwap; module.exports.runCLI = main;",sandbox);
  const originalArgv=sandbox.process.argv;
  sandbox.process.argv=originalArgv.concat(["swap","TOKEN","SOL","raw:100000000","15","100","1","--small-settlement"]);
  await sandbox.module.exports.runCLI();assert.equal(cliSwapArgs[6],true);assert.equal(cliSwapArgs[4],100);
  sandbox.process.exit=code=>{throw new Error(`exit ${code}`);};
  for(const option of ["--unknown","--small-settlement --extra"]){
    cliSwapArgs=null;sandbox.process.argv=originalArgv.concat(["swap","TOKEN","SOL","raw:1","15","100","1",...option.split(" ")]);
    await assert.rejects(sandbox.module.exports.runCLI(),/exit 1/);assert.equal(cliSwapArgs,null);
  }
  sandbox.process.argv=originalArgv;
  let cliRentArgs;
  sandbox.captureCLIRent=async(...args)=>{cliRentArgs=args;return {success:true};};
  vm.runInNewContext("reclaimEmptyAccounts = captureCLIRent;",sandbox);
  for (const options of [[],["--batch"],["--execute"],["--execute","--batch"],["--dust"],["--execute","--batch","--dust"]]) {
    sandbox.process.argv=originalArgv.concat(["reclaim-empty-accounts",...options]);
    await sandbox.module.exports.runCLI();
    assert.deepEqual(Array.from(cliRentArgs),[options.includes("--execute"),options.includes("--batch"),options.includes("--dust")]);
  }
  cliRentArgs=null;sandbox.process.argv=originalArgv.concat(["reclaim-empty-accounts","--unknown"]);
  await assert.rejects(sandbox.module.exports.runCLI(),/exit 1/);assert.equal(cliRentArgs,null);
  sandbox.process.argv=originalArgv;
  console.log("Cross-process lock, concurrent mint, chain exposure, signed expiry and uncertain-send checks passed");
})().catch((err) => { console.error(err); process.exitCode = 1; }).finally(() => { if (!worker) fs.rmSync(root, { recursive: true, force: true }); });
