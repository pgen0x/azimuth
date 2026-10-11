// Offline native-risk proofs, including the executor wiring. No SDK/RPC required.
const assert = require("node:assert/strict");
const fs = require("node:fs"), os = require("node:os"), path = require("node:path"), vm = require("node:vm");
const {SOL, SOURCE, loadInitialContext, initialDeposit, onlyInitialSignature, markInventory} = require("./dlmm_risk_mark");
const root = fs.mkdtempSync(path.join(os.tmpdir(), "dlmm-native-risk-"));
const key = value => ({toString: () => value});
const copy = value => structuredClone(value);
const programId = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo";
const tokenProgram = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
const definition = {name: "add_liquidity_by_strategy2", discriminator: [3,221,149,218,111,141,118,213],
  accounts: ["position","lb_pair","bin_array_bitmap_extension","user_token_x","user_token_y",
    "reserve_x","reserve_y","token_x_mint","token_y_mint","sender","token_x_program","token_y_program"]
    .map(name => ({name}))};
const initializeDefinition = {name: "initialize_position", discriminator: [219,192,234,71,190,191,102,80],
  accounts: ["payer","position","lb_pair","owner"].map(name => ({name}))};
const entry = {position: "2".repeat(32), pool: "3".repeat(32), base_mint: "4".repeat(32),
  entry_id: "entry", root_chain_id: "2".repeat(32), strategy: "sol_bidask", sol_is_x: false,
  size_sol: .1, amount_x: 0, amount_y: .1, entry_bin: 0, bins_below: 1, bins_above: 0};
const submission = {position: entry.position, root_chain_id: entry.root_chain_id,
  entry_id: entry.entry_id, wallet: "5".repeat(32), kind: "deploy", signature: "signed-deposit"};
const context = {entry, submission};
const binding = {definition, initializeDefinitions: [initializeDefinition], decode: text => Buffer.from(text, "hex"), programId,
  tokenX: entry.base_mint, tokenY: SOL, reserveX: "vault-x", reserveY: "vault-y"};
const payload = Buffer.alloc(24); Buffer.from(definition.discriminator).copy(payload);
payload.writeBigUInt64LE(100000000n, 16);
const transfer = (mint, side, amount) => ({programId: tokenProgram, stackHeight: 2,
  parsed: {type: "transferChecked", info: {mint, source: `user-${side}`, destination: `vault-${side}`,
    authority: submission.wallet, tokenAmount: {amount, decimals: mint === SOL ? 9 : 6}}}});
const tx = {transaction: {signatures: [submission.signature], message: {
  accountKeys: [{pubkey: submission.wallet, signer: true}, {pubkey: "user-x"}, {pubkey: "user-y"}],
  instructions: [{programId, data: payload.toString("hex"), accounts: [entry.position, entry.pool, programId,
    "user-x", "user-y", "vault-x", "vault-y", entry.base_mint, SOL, submission.wallet, tokenProgram, tokenProgram]}]}},
  meta: {err: null, preTokenBalances: [{accountIndex: 1, owner: submission.wallet, mint: entry.base_mint}],
    postTokenBalances: [], innerInstructions: [{index: 0, instructions: [transfer(entry.base_mint, "x", "0"),
      transfer(SOL, "y", "99999982")]}, {index: 1, instructions: [{programId: tokenProgram,
      parsed: {type: "initializeAccount3", info: {account: "user-y", mint: SOL, owner: submission.wallet}}}]}]}};
tx.transaction.message.instructions.unshift({programId, data: Buffer.from(initializeDefinition.discriminator).toString("hex"),
  accounts: [submission.wallet, entry.position, entry.pool, submission.wallet]}, {programId: "create-token-account"});
tx.meta.innerInstructions[0].index = 2;
tx.meta.innerInstructions[1].index = 1;
const native = {lbPair: entry.pool, owner: submission.wallet, feeOwner: "11111111111111111111111111111111",
  lowerBinId: -1, upperBinId: 0, liquidityShares: ["100", "200"],
  totalClaimedFeeXAmount: "0", totalClaimedFeeYAmount: "0"};
const data = {...native, totalXAmount: "10000000", totalYAmount: "80000000", feeX: "1000000", feeY: "1000000",
  totalXAmountExcludeTransferFee: "10000000", totalYAmountExcludeTransferFee: "80000000",
  feeXExcludeTransferFee: "1000000", feeYExcludeTransferFee: "1000000", rewardOne: "0", rewardTwo: "0",
  positionBinData: [{binId: -1, positionLiquidity: "100", binLiquidity: "1000", positionXAmount: "10000000",
    positionYAmount: "0", positionFeeXAmount: "1000000", positionFeeYAmount: "0"},
  {binId: 0, positionLiquidity: "200", binLiquidity: "1000", positionXAmount: "0",
    positionYAmount: "80000000", positionFeeXAmount: "0", positionFeeYAmount: "1000000"}]};
const pair = {activeId: 0, binStep: 100};
const writeProfile = (value = entry, events = [submission]) => {
  fs.mkdirSync(path.join(root, "memories/dlmm_entries"), {recursive: true});
  fs.writeFileSync(path.join(root, "memories/dlmm_entries", entry.position+".json"), JSON.stringify(value));
  fs.writeFileSync(path.join(root, "memories/dlmm_transactions.jsonl"), events.map(x => JSON.stringify(x)).join("\n")+"\n");
};
const rejects = callback => assert.throws(callback, /Native risk mark unavailable/);

(async () => {
  writeProfile(); assert.deepEqual(loadInitialContext(root, entry.pool, entry.position), context);
  writeProfile(entry, [submission, submission]); assert.deepEqual(loadInitialContext(root, entry.pool, entry.position), context);
  for (const change of [{kind: "claim"}, {kind: "close"}, {signature: "second-deploy"}, {wallet: "6".repeat(32)}]) {
    writeProfile(entry, [submission, {...submission, ...change}]);
    rejects(() => loadInitialContext(root, entry.pool, entry.position));
  }
  for (const change of [{pool: "other"}, {sol_is_x: null}, {amount_x: 1}, {amount_y: null}, {size_sol: "0.1"},
    {strategy: "token_bidask"}, {bins_below: 70}]) {
    writeProfile({...entry, ...change}); rejects(() => loadInitialContext(root, entry.pool, entry.position));
  }
  rejects(() => loadInitialContext(root, entry.pool, "../entry"));
  writeProfile();
  assert.equal(initialDeposit(tx, context, binding), 99999982n); // actual transfer, not intended 0.1 SOL
  const brokenTransactions = [
    t => {t.meta.err = "failed";}, t => {t.transaction.signatures[0] = "other";},
    t => {t.transaction.message.accountKeys[0].signer = false;},
    t => {t.transaction.message.instructions[2].accounts[0] = "other-position";},
    t => {t.transaction.message.instructions[2].accounts[5] = "other-vault";},
    t => {t.transaction.message.instructions[0].accounts[3] = "other-owner";},
    t => {t.meta.innerInstructions[0].instructions[1].parsed.info.authority = "other-wallet";},
    t => {t.meta.innerInstructions[0].instructions[1].parsed.info.source = "other-source";},
    t => {t.meta.innerInstructions[0].instructions[1].parsed.info.destination = "other-vault";},
    t => {t.meta.innerInstructions[0].instructions[1].parsed.info.tokenAmount.amount = "100000001";},
    t => {t.meta.innerInstructions[0].instructions[0].parsed.info.tokenAmount.amount = "1";},
    t => {t.meta.innerInstructions[0].instructions[1].stackHeight = 3;},
    t => {t.meta.innerInstructions[0].instructions.pop();},
    t => {t.meta.innerInstructions.pop();},
    t => {t.transaction.message.instructions.push(t.transaction.message.instructions[2]);},
    t => {const p = Buffer.from(t.transaction.message.instructions[2].data, "hex"); p.writeBigUInt64LE(1n, 8); t.transaction.message.instructions[2].data = p.toString("hex");},
  ];
  for (const breakTx of brokenTransactions) { const bad = copy(tx); breakTx(bad); rejects(() => initialDeposit(bad, context, binding)); }
  const history = [{signature: submission.signature, err: null, confirmationStatus: "confirmed"}];
  onlyInitialSignature(history, context);
  for (const bad of [[], [...history, {...history[0], signature: "manual-add"}], [{...history[0], err: "failed"}],
    [{...history[0], signature: "other"}], [{...history[0], confirmationStatus: "processed"}]]) rejects(() => onlyInitialSignature(bad, context));
  let mark = markInventory(context, native, data, pair, 100000000n);
  assert.equal(mark.source, SOURCE); assert.equal(mark.pnl_sol, -.008); assert.equal(mark.pnl_pct, -8);
  assert.equal(mark.current_value_sol, .09); assert.equal(mark.unclaimed_fees_sol, .002);
  assert.equal(mark.value_lamports_upper, "92000000");
  assert.deepEqual(mark.bin_observation, {version: 1, bin_step: 100, sol_is_x: false, bins: [
    {id: -1, liquidity_raw: "100", x_raw: "10000000", y_raw: "0", fee_x_raw: "1000000", fee_y_raw: "0"},
    {id: 0, liquidity_raw: "200", x_raw: "0", y_raw: "80000000", fee_x_raw: "0", fee_y_raw: "1000000"}]});
  mark = markInventory(context, native, data, {activeId: -2, binStep: 125}, 100000000n);
  assert.equal(mark.value_lamports_upper, ((81000000n*6561n + 11000000n*6400n + 6560n)/6561n).toString());
  assert.equal(mark.in_range, false);
  const solXContext = {entry: {...entry, sol_is_x: true, amount_x: .1, amount_y: 0}, submission};
  const xPayload = Buffer.from(payload); xPayload.writeBigUInt64LE(100000000n, 8); xPayload.writeBigUInt64LE(0n, 16);
  const xTx = copy(tx); xTx.transaction.message.instructions[2].data = xPayload.toString("hex");
  xTx.transaction.message.instructions[2].accounts[7] = SOL; xTx.transaction.message.instructions[2].accounts[8] = entry.base_mint;
  xTx.meta.preTokenBalances = [{accountIndex: 1, owner: submission.wallet, mint: SOL}, {accountIndex: 2, owner: submission.wallet, mint: entry.base_mint}];
  xTx.meta.innerInstructions = [{index: 2, instructions: [transfer(SOL, "x", "99999982"), transfer(entry.base_mint, "y", "0")]}];
  assert.equal(initialDeposit(xTx, solXContext, {...binding, tokenX: SOL, tokenY: entry.base_mint}), 99999982n);
  mark = markInventory(solXContext, native, data, {activeId: 2, binStep: 125}, 100000000n);
  assert.equal(mark.value_lamports_upper, ((11000000n*6561n + 81000000n*6400n + 6560n)/6561n).toString());
  for (const change of [d => {d.positionBinData.pop();}, d => {d.positionBinData[0].binLiquidity = "0";},
    d => {d.positionBinData[0].positionLiquidity = "99";}, d => {d.positionBinData[0].binId = 1;},
    d => {d.totalXAmount = "0";}, d => {d.feeY = undefined;}, d => {d.feeYExcludeTransferFee = "1000001";},
    d => {d.totalYAmountExcludeTransferFee = undefined;}, d => {d.totalClaimedFeeXAmount = "1";},
    d => {d.rewardOne = "1";}, d => {d.owner = "other-wallet";}, d => {d.feeOwner = "other-wallet";}]) {
    const bad = copy(data); change(bad); rejects(() => markInventory(context, native, bad, pair, 100000000n));
  }
  rejects(() => markInventory(context, {...native, lbPair: "other-pool"}, data, pair, 100000000n));
  rejects(() => markInventory(context, native, data, {...pair, activeId: NaN}, 100000000n));
  rejects(() => markInventory(context, native, data, pair, 0n));

  // Exercise production executor: no indexed HTTP call, signer or transaction send.
  let sdkData = data, nativeAccount = native, signatures = history, signerCalls = 0, rpcCalls = 0;
  class Connection {
    async getAccountInfo() {rpcCalls++; return {owner: key(programId), data: Buffer.from([1,2,3,4,5,6,7,8])};}
    async getParsedTransaction() {rpcCalls++; return tx;}
    async getSignaturesForAddress(_key, options, commitment) {assert.equal(options.limit, 2); assert.equal(commitment, "confirmed"); return signatures;}
    async sendRawTransaction() {throw Error("must never send");}
  }
  const pool = {lbPair: {...pair, tokenXMint: key(entry.base_mint), tokenYMint: key(SOL), reserveX: key("vault-x"), reserveY: key("vault-y")},
    program: {coder: {accounts: {decode: () => nativeAccount}}}, getPosition: async () => ({positionData: sdkData}),
    fromPricePerLamport: value => String(value/1000)};
  const deps = {"@solana/web3.js": {Connection, PublicKey: function(v) {return key(v);}, Keypair: {fromSecretKey() {signerCalls++; throw Error("must never sign");}}},
    "@meteora-ag/dlmm": {create: async () => pool, getPriceOfBinByBinId: () => "1.25", IDL: {address: programId, accounts: [{name: "PositionV2", discriminator: [1,2,3,4,5,6,7,8]}], instructions: [definition, initializeDefinition]}},
    "bn.js": {}, "bs58": {decode: binding.decode}, "dotenv": {config() {}, parse: () => ({})}};
  const sandbox = {require: name => deps[name] || require(name), module: {exports: {}}, Buffer,
    process: {argv: ["node", path.join(root, "skills/solana-dlmm/scripts/dlmm_executor.js")],
      env: {SOLANA_RPC_URLS: "fake", SOLANA_PUBLIC_KEY: submission.wallet}},
    console: {warn() {}, log() {}, error() {}}, fetch: () => {throw Error("indexed HTTP forbidden");}, AbortSignal, setTimeout};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "dlmm_executor.js"), "utf8"), sandbox);
  const run = sandbox.module.exports.getPositionRiskMark;
  mark = await run(entry.pool, entry.position); assert.equal(mark.success, true); assert.equal(mark.pnl_pct, -7.999983439997019);
  assert.equal(mark.pool_price, .00125);
  assert.equal(mark.bin_observation.bins.length, 2);
  assert.equal(signerCalls, 0); assert.equal(rpcCalls, 2);
  sandbox.process.env.SOLANA_PUBLIC_KEY = "foreign-profile-wallet";
  assert.equal((await run(entry.pool, entry.position)).success, false); assert.equal(rpcCalls, 2);
  sandbox.process.env.SOLANA_PUBLIC_KEY = submission.wallet;
  sdkData = {...data, owner: "foreign-owner"}; assert.equal((await run(entry.pool, entry.position)).success, false);
  sdkData = data; signatures = [...history, {...history[0], signature: "manual-claim"}];
  assert.equal((await run(entry.pool, entry.position)).success, false);
  signatures = history; nativeAccount = {...native, owner: "foreign-owner"};
  assert.equal((await run(entry.pool, entry.position)).success, false);
  nativeAccount = native; writeProfile(entry, [submission, {...submission, kind: "close", signature: "closing"}]);
  const before = rpcCalls; assert.equal((await run(entry.pool, entry.position)).success, false); assert.equal(rpcCalls, before);
  assert.equal(signerCalls, 0);
  console.log("Native risk funding, bin coverage, SOL orientation, arithmetic and executor checks passed");
})().catch(error => {console.error(error); process.exitCode = 1;}).finally(() => fs.rmSync(root, {recursive: true, force: true}));
