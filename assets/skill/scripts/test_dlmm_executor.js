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
let confirmTimeout = false, accountExists = true, failNextSend = false;
const closeBytes = [];
const key = (value) => ({ toString: () => value });
const wallet = { publicKey: key(`test-wallet-${worker ? "swap" : process.pid}`) };
const transaction = () => ({ signature: Buffer.from([1]), sign() {}, compileMessage() { return {}; }, serialize() { return Buffer.from(this.recentBlockhash); } });
const pool = {
  pubkey: key("pool"), lbPair: { tokenXMint: key("TOKEN"), tokenYMint: key("So11111111111111111111111111111111111111112"), binStep: 100 },
  program: { account: {
    positionV2: { all: async () => { reads++; return positions; } },
    lbPair: { fetch: async () => ({ tokenXMint: key("TOKEN"), tokenYMint: key("SOL") }) },
  } },
  claimSwapFee: async () => [],
  removeLiquidity: async () => transaction(),
  getActiveBin: async () => ({ binId: 0, price: "1" }), fromPricePerLamport: (x) => x,
  initializePositionAndAddLiquidityByStrategy: async (args) => { lastSlippage = args.slippage; builds++; if (buildError) throw new Error("build failed"); return transaction(); },
  createExtendedEmptyPosition: async () => [transaction()],
  addLiquidityByStrategyChunkable: async () => { throw new Error("wide add failed"); },
};
let reservePost = 300000000, reserveError = null, reserveChanged = false, reserveReads = 0;
class Connection {
  async getBalanceAndContext() { return {context:{slot:10},value:300000000+(++reserveReads%2===0 && reserveChanged ? 1 : 0)}; }
  async simulateTransaction() { return {context:{slot:10},value:{err:reserveError,accounts:[{lamports:reservePost}]}}; }
  async getAccountInfo() { return accountExists ? {} : null; }
  async getBlockHeight() { return height; }
  async getSignatureStatuses(signatures, options) {
    assert.equal(options.searchTransactionHistory, true);
    return { value: [signatureStatus] };
  }
  async getLatestBlockhash() { return { blockhash: "exact-blockhash", lastValidBlockHeight: 150 }; }
  async sendRawTransaction(raw, options) {
    const event=JSON.parse(fs.readFileSync(path.join(root,"memories/dlmm_transactions.jsonl"),"utf8").trim().split("\n").at(-1));
    if (event.kind === "swap") {
      assert.equal(event.swap_quote.in_amount,"100000000");
      assert.equal(typeof event.swap_quote.out_amount,"string");
      assert.equal(typeof event.swap_quote.observed_at,"number");
      assert.equal(event.swap_quote.unrelatedDebug,undefined);
    }
    sends++; closeBytes.push(raw.toString("hex")); if (failNextSend) { failNextSend = false; throw new Error("429 max usage reached"); } lastMaxRetries = options.maxRetries; assert.equal(raw.toString(), "exact-blockhash"); if (sendError) throw new Error("timeout after send"); return "sig";
  }
  async confirmTransaction(strategy) { if (confirmTimeout) throw new Error("confirmation timeout"); assert.equal(strategy.blockhash, "exact-blockhash"); return { value: { err: confirmationError ? "chain error" : null } }; }
}
const rentInstructions = [];
class RentTransaction {
  constructor() { Object.assign(this, transaction()); }
  add(instruction) { rentInstructions.push(instruction); return this; }
  compileMessage() { return {}; }
}
const deps = {
  "@solana/web3.js": { Transaction: RentTransaction, Connection, Keypair: { generate: () => ({ publicKey: key(`position-${++minted}`) }) }, PublicKey: function (v) { return key(v); }, VersionedTransaction: class { constructor(message) { this.message=message; } static deserialize = () => ({ message: {}, signatures: [Buffer.from([1])], sign() {}, serialize() { return Buffer.from(this.message.recentBlockhash); } }) } },
  "@meteora-ag/dlmm": { create: async () => pool, StrategyType: { Spot: 0, Curve: 1, BidAsk: 2 }, positionOwnerFilter: () => ({}) },
  "bn.js": function (value) { this.value = value; }, "bs58": { encode: () => "signature" },
  "dotenv": { config() {}, parse: () => ({}) },
};
const env = { SOLANA_RPC_URLS: "fake-rpc-1,fake-rpc-2", DLMM_ENTRY_CONTEXT: JSON.stringify({ mode: "turnover", recenter_of: "root", pair: "TEST-SOL" }) };
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
  console: { log() {}, warn() {}, error() {} }, Buffer, AbortSignal, setTimeout, clearTimeout };
vm.runInNewContext(source + "\nmodule.exports.sdkFindPool = findPoolForPosition; module.exports.sdkPositions = getPositions; assertRootBudget = async () => {}; getWallet = () => testWallet; getTokenDecimals = async () => 9; assertRangeDoesNotRequireBinArrayInitialization = async () => {};", Object.assign(sandbox, { testWallet: wallet }));
const { swapAmountRaw, closePosition, swapToken, confirmSignedTransaction, deployPosition, acquireDeployLock, reconcilePendingSwap, assertNoTokenExposure,
  positionIsEmpty, slippageBpsToPercent } = sandbox.module.exports;
const marker = path.join(root, "memories/dlmm_pending_deploys", `${wallet.publicKey}.json`);
const deploy = () => deployPosition("pool", 0, 0.1, 20, 0, "bid_ask", 1000);
const clearMarker = () => fs.rmSync(marker, { force: true });

(async () => {
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
  assert.equal(closeRestart.sends, 1);
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
  const recover = (floor=4000) => swapToken("TOKEN", "So11111111111111111111111111111111111111112", 0.1, 5, 100, floor);
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
  const originalConfirm = Connection.prototype.confirmTransaction;
  const originalAbort = sandbox.AbortSignal;
  let confirmationAttempts = 0;
  sandbox.AbortSignal = { timeout: () => AbortSignal.timeout(5) };
  Connection.prototype.confirmTransaction = async strategy => {
    if (++confirmationAttempts === 1) return new Promise((_, reject) => strategy.abortSignal.addEventListener("abort", () => reject(new Error("timeout"))));
    return { value: { err: null } };
  };
  const keepAlive = setTimeout(() => {}, 200);
  assert.equal((await closePosition("deadline-position")).success, true);
  clearTimeout(keepAlive);
  assert.equal(confirmationAttempts, 2);
  Connection.prototype.confirmTransaction = originalConfirm;
  sandbox.AbortSignal = originalAbort;
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
  fs.rmSync(settlementDir, { recursive: true });
  assert.equal(sends, 0);
  assert.equal(slippageBpsToPercent(1000), 10);
  assert.equal(positionIsEmpty({ positionData: { liquidityShares: [{ isZero: () => true }] } }), true);
  assert.equal(positionIsEmpty({ positionData: { liquidityShares: [{ isZero: () => false }] } }), false);
  assert.equal(positionIsEmpty({ positionData: {} }), null);
  assert.throws(() => slippageBpsToPercent(0), /positive integer/);
  assert.doesNotMatch(source, /const latestBlockHash = await connection\.getLatestBlockhash/);
  assert.match(source, /blockhash, lastValidBlockHeight, signature: txid/);
  assert.match(source, /success: false, pending: true, txHash: signedTxid/);
  assert.ok(source.indexOf("fs.renameSync(markerTmp, pendingPath)") < source.indexOf("txid = await connection.sendRawTransaction(rawTransaction"));
  const swapMarker = path.join(root, "pending-swap.json");
  fs.writeFileSync(swapMarker, JSON.stringify({ signature: "swap-sig", lastValidBlockHeight: 150,
    inputAmount: "10", outputAmount: "20" }));
  signatureStatus = null; height = 100;
  assert.equal((await reconcilePendingSwap(new Connection(), swapMarker)).pending, true);
  signatureStatus = { confirmationStatus: "confirmed", err: null };
  const reconciled = await reconcilePendingSwap(new Connection(), swapMarker);
  assert.equal(reconciled.success, true); assert.equal(reconciled.txHash, "swap-sig");
  assert.ok(!fs.existsSync(swapMarker));
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
  failNextSend = true;
  const recoveredDeploy = await deploy();
  assert.equal(recoveredDeploy.success, true);
  assert.equal(sends-beforeRetry.sends, 2);
  assert.equal(builds-beforeRetry.builds, 1);
  assert.equal(new Set(closeBytes.slice(beforeRetry.bytes)).size, 1);
  const deployMarker = JSON.parse(fs.readFileSync(marker));
  assert.equal(deployMarker.position, recoveredDeploy.position);
  assert.equal(deployMarker.signature, recoveredDeploy.txHashes[0]);
  clearMarker();
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
  assert.equal(JSON.parse(facts[0]).schema_version, 11);
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
      assert.equal(program.toString(), account.toString() === "safe-2022" ? "token2022" : "classic-token");
      return account.toString();
    } };
  // Transaction was destructured when the executor loaded; use its injected class.
  let tokenAccounts = [];
  Connection.prototype.getParsedTokenAccountsByOwner = async (_, {programId}) => ({ value: tokenAccounts.filter(a=>a.account.owner.toString()===programId.toString()) });
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
  const reclaimed = await reclaimEmptyAccounts(true);
  assert.equal(reclaimed.recovered_lamports_before_fee, 2976880); assert.equal(sends, beforeRent + 1);
  assert.deepEqual(rentInstructions, ["eligible", "safe-2022", "eligible", "safe-2022"]); // fee rejection builds but never sends
  const rentEvent = JSON.parse(fs.readFileSync(journal, "utf8").trim().split("\n").at(-1));
  assert.equal(rentEvent.kind, "rent_reclaim"); assert.equal(rentEvent.entry_id, null); assert.equal(rentEvent.root_chain_id, null);
  signatureStatus = null; sendError = true; confirmTimeout = true; height = 100;
  await assert.rejects(reclaimEmptyAccounts(true), /confirmation timeout/);
  assert.equal(sends, beforeRent + 2);
  assert.equal((await reclaimEmptyAccounts(true)).pending, true); assert.equal(sends, beforeRent + 2);
  signatureStatus = { confirmationStatus: "finalized", err: null };
  assert.equal((await reclaimEmptyAccounts(true)).reconciled, true); assert.equal(sends, beforeRent + 2);
  sendError = false; confirmTimeout = false; signatureStatus = null;
  fs.appendFileSync = () => { throw new Error("disk full"); };
  try { await assert.rejects(reclaimEmptyAccounts(true), /disk full/); assert.equal(sends, beforeRent + 2); }
  finally { fs.appendFileSync = append; }
  console.log("Cross-process lock, concurrent mint, chain exposure, signed expiry and uncertain-send checks passed");
})().catch((err) => { console.error(err); process.exitCode = 1; }).finally(() => { if (!worker) fs.rmSync(root, { recursive: true, force: true }); });
