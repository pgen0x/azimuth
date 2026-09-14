// Offline: node assets/skill/scripts/test_dlmm_executor.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const vm = require("node:vm");
const { execFileSync } = require("node:child_process");
const source = fs.readFileSync(path.join(__dirname, "dlmm_executor.js"), "utf8");
const root = fs.mkdtempSync(path.join(os.tmpdir(), "dlmm-guards-"));
let reads = 0, sends = 0, builds = 0, minted = 0, height = 100, sendError = false, buildError = false;
let positions = [], confirmationError = false;
const key = (value) => ({ toString: () => value });
const wallet = { publicKey: key(`test-wallet-${process.pid}`) };
const transaction = () => ({ signature: Buffer.from([1]), sign() {}, serialize() { return Buffer.from(this.recentBlockhash); } });
const pool = {
  pubkey: key("pool"), lbPair: { tokenXMint: key("TOKEN"), tokenYMint: key("So11111111111111111111111111111111111111112") },
  program: { account: {
    positionV2: { all: async () => { reads++; return positions; } },
    lbPair: { fetch: async () => ({ tokenXMint: key("TOKEN"), tokenYMint: key("SOL") }) },
  } },
  getActiveBin: async () => ({ binId: 0, price: "1" }), fromPricePerLamport: (x) => x,
  initializePositionAndAddLiquidityByStrategy: async () => { builds++; if (buildError) throw new Error("build failed"); return transaction(); },
  createExtendedEmptyPosition: async () => [transaction()],
  addLiquidityByStrategyChunkable: async () => { throw new Error("wide add failed"); },
};
class Connection {
  async getBlockHeight() { return height; }
  async getLatestBlockhash() { return { blockhash: "exact-blockhash", lastValidBlockHeight: 150 }; }
  async sendRawTransaction(raw) { sends++; assert.equal(raw.toString(), "exact-blockhash"); if (sendError) throw new Error("timeout after send"); return "sig"; }
  async confirmTransaction(strategy) { assert.equal(strategy.blockhash, "exact-blockhash"); return { value: { err: confirmationError ? "chain error" : null } }; }
}
const deps = {
  "@solana/web3.js": { Connection, Keypair: { generate: () => ({ publicKey: key(`position-${++minted}`) }) }, PublicKey: function (v) { return key(v); } },
  "@meteora-ag/dlmm": { create: async () => pool, StrategyType: { Spot: 0, Curve: 1, BidAsk: 2 }, positionOwnerFilter: () => ({}) },
  "bn.js": function (value) { this.value = value; }, "bs58": { encode: () => "signature" },
  "dotenv": { config() {}, parse: () => ({}) },
};
const env = { SOLANA_RPC_URLS: "fake-rpc-1,fake-rpc-2", DLMM_ENTRY_CONTEXT: JSON.stringify({ mode: "turnover", recenter_of: "root", pair: "TEST-SOL" }) };
const sandbox = { require: (name) => deps[name] || require(name), module: { exports: {} },
  process: { argv: ["node", path.join(root, "skills/solana-dlmm/scripts/dlmm_executor.js")], env },
  console: { log() {}, warn() {}, error() {} }, Buffer, setTimeout, clearTimeout };
vm.runInNewContext(source + "\ngetWallet = () => testWallet; getTokenDecimals = async () => 9; assertRangeDoesNotRequireBinArrayInitialization = async () => {};", Object.assign(sandbox, { testWallet: wallet }));
const { deployPosition, acquireDeployLock, assertNoTokenExposure } = sandbox.module.exports;
const marker = path.join(root, "memories/dlmm_pending_deploys", `${wallet.publicKey}.json`);
const deploy = () => deployPosition("pool", 0, 0.1, 20, 0, "bid_ask", 1000);
const clearMarker = () => fs.rmSync(marker, { force: true });

(async () => {
  // The OS lock excludes another process, not only another Promise.
  const release = await acquireDeployLock(wallet.publicKey.toString());
  await assert.rejects(acquireDeployLock(wallet.publicKey.toString()), /ENTRY BUSY/);
  const code = `const net=require('net');const s=net.createServer();s.on('error',e=>process.exit(e.code==='EADDRINUSE'?0:2));s.listen(${JSON.stringify("\0azimuth-dlmm-entry-" + wallet.publicKey)},()=>s.close(()=>process.exit(3)));`;
  execFileSync(process.execPath, ["-e", code]);
  await release();
  await (await acquireDeployLock(wallet.publicKey.toString()))();
  const parallel = await Promise.allSettled([deploy(), deploy()]);
  assert.equal(parallel.filter((r) => r.status === "fulfilled" && r.value.success).length, 1);
  assert.equal(sends, 1);
  assert.equal((await deploy()).pending, true); // prior blockhash still valid
  assert.equal(sends, 1);
  const provenance = JSON.parse(fs.readFileSync(path.join(root, "memories/dlmm_entries/position-1.json")));
  assert.equal(provenance.mode, "turnover"); assert.equal(provenance.recenter_of, "root");
  assert.equal(provenance.pool, "pool");
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
  console.log("Cross-process lock, concurrent mint, chain exposure, signed expiry and uncertain-send checks passed");
})().catch((err) => { console.error(err); process.exitCode = 1; }).finally(() => fs.rmSync(root, { recursive: true, force: true }));
