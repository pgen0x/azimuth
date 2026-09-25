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
let confirmTimeout = false, accountExists = true;
const key = (value) => ({ toString: () => value });
const wallet = { publicKey: key(`test-wallet-${worker ? "swap" : process.pid}`) };
const transaction = () => ({ signature: Buffer.from([1]), sign() {}, serialize() { return Buffer.from(this.recentBlockhash); } });
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
class Connection {
  async getAccountInfo() { return accountExists ? {} : null; }
  async getBlockHeight() { return height; }
  async getSignatureStatuses(signatures, options) {
    assert.equal(options.searchTransactionHistory, true);
    return { value: [signatureStatus] };
  }
  async getLatestBlockhash() { return { blockhash: "exact-blockhash", lastValidBlockHeight: 150 }; }
  async sendRawTransaction(raw, options) { sends++; lastMaxRetries = options.maxRetries; assert.equal(raw.toString(), "exact-blockhash"); if (sendError) throw new Error("timeout after send"); return "sig"; }
  async confirmTransaction(strategy) { if (confirmTimeout) throw new Error("confirmation timeout"); assert.equal(strategy.blockhash, "exact-blockhash"); return { value: { err: confirmationError ? "chain error" : null } }; }
}
const deps = {
  "@solana/web3.js": { Connection, Keypair: { generate: () => ({ publicKey: key(`position-${++minted}`) }) }, PublicKey: function (v) { return key(v); }, VersionedTransaction: { deserialize: () => ({ message: {}, signatures: [Buffer.from([1])], sign() {}, serialize() { return Buffer.from(this.message.recentBlockhash); } }) } },
  "@meteora-ag/dlmm": { create: async () => pool, StrategyType: { Spot: 0, Curve: 1, BidAsk: 2 }, positionOwnerFilter: () => ({}) },
  "bn.js": function (value) { this.value = value; }, "bs58": { encode: () => "signature" },
  "dotenv": { config() {}, parse: () => ({}) },
};
const env = { SOLANA_RPC_URLS: "fake-rpc-1,fake-rpc-2", DLMM_ENTRY_CONTEXT: JSON.stringify({ mode: "turnover", recenter_of: "root", pair: "TEST-SOL" }) };
const sandbox = { require: (name) => deps[name] || require(name), module: { exports: {} },
  process: { argv: ["node", path.join(root, "skills/solana-dlmm/scripts/dlmm_executor.js")], env },
  fetch: async (url) => ({ ok: true, json: async () => url.includes("/quote?")
    ? { inAmount: "100000000", outAmount: "20", priceImpactPct: "0" }
    : { swapTransaction: "AA==" } }),
  console: { log() {}, warn() {}, error() {} }, Buffer, setTimeout, clearTimeout };
vm.runInNewContext(source + "\nassertRootBudget = async () => {}; getWallet = () => testWallet; getTokenDecimals = async () => 9; assertRangeDoesNotRequireBinArrayInitialization = async () => {};", Object.assign(sandbox, { testWallet: wallet }));
const { closePosition, swapToken, confirmSignedTransaction, deployPosition, acquireDeployLock, reconcilePendingSwap, assertNoTokenExposure,
  positionIsEmpty, slippageBpsToPercent } = sandbox.module.exports;
const marker = path.join(root, "memories/dlmm_pending_deploys", `${wallet.publicKey}.json`);
const deploy = () => deployPosition("pool", 0, 0.1, 20, 0, "bid_ask", 1000);
const clearMarker = () => fs.rmSync(marker, { force: true });

(async () => {
  if (worker) {
    sendError = true;
    signatureStatus = worker === "confirmed" ? { confirmationStatus: "confirmed", err: null } : null;
    if (worker === "unavailable") Connection.prototype.getSignatureStatuses = async () => { throw new Error("offline"); };
    const result = await swapToken("So11111111111111111111111111111111111111112", "TOKEN", 0.1);
    console.log(JSON.stringify({ result, sends }));
    return;
  }
  for (const [mode, count] of [["submit", 1], ["pending", 0], ["unavailable", 0], ["confirmed", 0]]) {
    const out = JSON.parse(execFileSync(process.execPath, [__filename, mode, root], { encoding: "utf8" }));
    assert.equal(out.sends, count);
    assert.equal(mode === "confirmed" ? out.result.success : out.result.pending, true);
  }
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
  sends = 0;
  confirmTimeout = true;
  signatureStatus = { confirmationStatus: "confirmed", err: null };
  await confirmSignedTransaction(new Connection(), { signature: "signature", blockhash: "exact-blockhash", lastValidBlockHeight: 150 });
  signatureStatus = null;
  await assert.rejects(confirmSignedTransaction(new Connection(), { signature: "signature" }), /timeout/);
  confirmTimeout = false;
  vm.runInNewContext("findPoolForPosition = async () => ({pool: testPool, positionData: {publicKey: testWallet.publicKey, positionData: {lowerBinId: 0, upperBinId: 1}}});", Object.assign(sandbox, {testPool: pool}));
  sendError = true;
  const beforeClose = sends;
  assert.equal((await closePosition("position")).pending, true);
  assert.equal(sends, beforeClose + 1); // no second signed close on another RPC
  accountExists = false;
  assert.equal((await closePosition("position")).reconciled, true);
  assert.equal(sends, beforeClose + 2);
  accountExists = true; sendError = false; sends = 0;
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
  assert.equal(uncertain.pending, true); assert.equal(sends, 2); // no second RPC mint
  height = 100;
  assert.equal((await deploy()).pending, true); assert.equal(sends, 2);
  clearMarker(); sendError = false; buildError = true;
  await assert.rejects(deploy(), /RPC endpoints failed/);
  assert.equal(sends, 2); assert.ok(!fs.existsSync(marker));
  buildError = false;
  const wide = await deployPosition("pool", 0, 0.1, 80, 0, "bid_ask", 1000);
  assert.equal(wide.pending, true); assert.equal(sends, 3); // partial mint never re-minted/closed blindly
  clearMarker(); confirmationError = true;
  assert.equal((await deploy()).success, false); assert.equal(sends, 4);
  clearMarker();
  fs.writeFileSync(marker, "broken");
  await assert.rejects(deploy(), /RPC endpoints failed/); assert.equal(sends, 4);
  await assert.rejects(deployPosition("pool", 0, -1, 20, 0), /Invalid deploy/);
  clearMarker(); height = 151; confirmationError = false;
  assert.equal((await deploy()).success, true); assert.equal(sends, 5); // expired reservation recovers
  deps["./dlmm_nav.js"] = {collect: async () => ({})};
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
  Connection.prototype.getParsedTransaction = async signature => signature === "missing" ? null : ({
    slot: 100, blockTime: 200,
    transaction: {message: {accountKeys: [{pubkey: wallet.publicKey}]}},
    meta: {err: null, fee: 5000, preBalances: [100000], postBalances: [70000],
      preTokenBalances: [], postTokenBalances: [{owner: wallet.publicKey.toString(), mint: "TOKEN",
        uiTokenAmount: {amount: "9007199254740993"}}]},
  });
  assert.equal((await reconcileAccounting()).pending, 1);
  assert.equal((await reconcileAccounting()).pending, 1);
  const facts = fs.readFileSync(path.join(root, "memories/dlmm_transaction_facts.jsonl"), "utf8").trim().split("\n");
  assert.equal(facts.length, 1); // refresh never counts the same signature twice
  assert.equal(JSON.parse(facts[0]).wallet_delta_lamports, -30000);
  assert.equal(JSON.parse(facts[0]).fee_lamports, 5000);
  assert.equal(JSON.parse(facts[0]).token_deltas_raw.TOKEN, "9007199254740993");
  console.log("Cross-process lock, concurrent mint, chain exposure, signed expiry and uncertain-send checks passed");
})().catch((err) => { console.error(err); process.exitCode = 1; }).finally(() => { if (!worker) fs.rmSync(root, { recursive: true, force: true }); });
