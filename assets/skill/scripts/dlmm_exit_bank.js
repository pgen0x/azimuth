// Research-only account archive. No keypairs, signing, simulation or submission.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {PublicKey, Connection} = require('@solana/web3.js');
const {walletTradeActive} = require('./dlmm_nav');
const SOL = 'So11111111111111111111111111111111111111112';
const LOADER = 'BPFLoaderUpgradeab1e11111111111111111111111';
const CLOCK = 'SysvarC1ock11111111111111111111111111111111';
const RENT = 'SysvarRent111111111111111111111111111111111';
const allowed = new Set(['getAccountInfo', 'getMultipleAccounts', 'getEpochInfo',
  'getMinimumBalanceForRentExemption', 'getLatestBlockhash']);
function requireThat(ok, reason) { if (!ok) throw new Error(reason); }
function address(value) { return new PublicKey(value).toString(); }
async function boundedJson(response, maximum) {
  const reader = response.body.getReader(), chunks = [];
  let size = 0;
  try {
    for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.length; requireThat(size <= maximum, 'response_size_limit');
      chunks.push(Buffer.from(value));
    }
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } finally { await reader.cancel(); }
}
function encode(ix) {
  return {programId: address(ix.programId), accounts: ix.keys.map(k => ({
    pubkey: address(k.pubkey), isSigner: k.isSigner, isWritable: k.isWritable})),
    data: ix.data.toString('base64')};
}
function dependencyKeys(close, response, identity) {
  requireThat(response.swapInstruction && response.tokenLedgerInstruction,
    'missing_swap_or_ledger');
  const instructions = [...close, ...(response.computeBudgetInstructions || []),
    ...(response.setupInstructions || []), ...(response.otherInstructions || []),
    response.tokenLedgerInstruction, response.swapInstruction,
    ...(response.cleanupInstruction ? [response.cleanupInstruction] : [])];
  const keys = new Set([...Object.values(identity), CLOCK, RENT,
    ...(response.addressLookupTableAddresses || [])].map(address));
  for (const ix of instructions) {
    keys.add(address(ix.programId));
    for (const key of ix.accounts) keys.add(address(key.pubkey));
  }
  requireThat(keys.size <= 100, 'account_limit');
  return [...keys];
}
function programData(account) {
  if (!account?.executable || account.owner !== LOADER) return null;
  const data = Buffer.from(account.data[0], 'base64');
  requireThat(data.length === 36 && data.readUInt32LE(0) === 2, 'invalid_program_account');
  return new PublicKey(data.subarray(4)).toString();
}
async function captureBank(keys, readAccounts, position) {
  const first = await readAccounts(keys);
  requireThat(first.value.length === keys.length, 'account_count');
  const programs = new Map();
  first.value.forEach((a, i) => { const d = programData(a); if (d) programs.set(keys[i], d); });
  const full = [...new Set([...keys, ...programs.values()])];
  requireThat(full.length <= 100, 'account_limit');
  // One final response contains all account bytes, including executable code.
  const final = await readAccounts(full);
  requireThat(final.value.length === full.length && final.context.slot >= first.context.slot,
    'invalid_snapshot_context');
  const accounts = Object.fromEntries(full.map((k, i) => [k, final.value[i]]));
  requireThat(accounts[position], 'position_closed');
  for (const [program, data] of programs) {
    requireThat(programData(accounts[program]) === data && accounts[data]?.owner === LOADER,
      'program_changed_during_capture');
    const raw = Buffer.from(accounts[data].data[0], 'base64');
    requireThat(raw.length > 45 && raw.readUInt32LE(0) === 3, 'program_data_missing');
  }
  // If a previously non-executable account changed into a program, its code
  // was not discovered; do not silently advertise a complete archive.
  for (const k of keys) requireThat(!programData(accounts[k]) || programs.has(k),
    'program_changed_during_capture');
  return {snapshot_slot: final.context.slot, discovery_slot: first.context.slot, accounts};
}
function tradingActive(wallet, position) {
  if (walletTradeActive(wallet)) return true;
  try {
    return fs.readFileSync('/proc/net/unix', 'utf8').split('\n').some(line => {
      const f = line.trim().split(/\s+/);
      return f.length === 8 && f[4] === '0001' && f[5] === '01'
        && (parseInt(f[3], 16) & 0x10000) !== 0 && f[7] === `@azimuth-dlmm-close-${position}`;
    });
  } catch { return true; }
}
async function capture(profile, sample, budgetMs) {
  requireThat(sample.status === 'measured' && sample.inventory_source === 'onchain_sol_inventory'
    && sample.quote && sample.quote.inAmount === sample.token_sell_raw
    && BigInt(sample.token_sell_raw) > 0n && sample.quote.outputMint === SOL,
    'unsupported_inventory');
  const wallet = address(sample.native_inventory.wallet), position = address(sample.position);
  const poolAddress = address(sample.pool), mint = address(sample.quote.inputMint);
  requireThat(mint === sample.native_inventory.token_x_mint
    && sample.native_inventory.token_y_mint === SOL
    && BigInt(sample.native_inventory.net_x_raw) + BigInt(sample.native_inventory.net_fee_x_raw)
       === BigInt(sample.token_sell_raw), 'inventory_mismatch');
  const dir = path.join(profile, 'memories', 'dlmm_exit_banks');
  const output = path.join(dir, position + '.json');
  if (fs.existsSync(output)) return {status: 'already_archived'};
  if (fs.existsSync(dir) && fs.readdirSync(dir).filter(n => n.endsWith('.json')).length >= 8)
    return {status: 'archive_capacity'};
  requireThat(Number.isFinite(sample.observed_at) && Date.now()/1000 - sample.observed_at >= -5
    && Date.now()/1000 - sample.observed_at <= 30, 'stale_quote_observation');
  const deadline = Date.now() + Math.min(15000, budgetMs);
  let calls = 0;
  function check() {
    requireThat(Date.now() < deadline && calls < 24, 'capture_budget');
    requireThat(!tradingActive(wallet, position), 'trading_active');
  }
  const env = require('dotenv').parse(fs.readFileSync(path.join(profile, '.env')));
  const endpoint = (env.SOLANA_RPC_URLS || 'https://api.mainnet-beta.solana.com').split(',')[0].trim();
  async function rpc(method, params) {
    check(); requireThat(allowed.has(method), 'rpc_method_denied'); calls++;
    const response = await fetch(endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({jsonrpc: '2.0', id: 1, method, params}),
      signal: AbortSignal.timeout(Math.max(1, deadline - Date.now()))});
    requireThat(response.ok, 'rpc_http_error');
    const body = await boundedJson(response, 32*1024*1024);
    requireThat(!body.error && body.result, 'rpc_result_unavailable');
    return body.result;
  }
  const connection = new Connection(endpoint, {commitment: 'confirmed', disableRetryOnRateLimit: true,
    fetch: async (_, options) => {
      const request = JSON.parse(options.body);
      const result = await rpc(request.method, request.params);
      return new Response(JSON.stringify({jsonrpc: '2.0', id: request.id, result}),
        {status: 200, headers: {'Content-Type': 'application/json'}});
    }});
  const DLMM = require('@meteora-ag/dlmm'), BN = require('bn.js');
  const pool = await DLMM.create(connection, new PublicKey(poolAddress));
  const pos = await pool.getPosition(new PublicKey(position));
  requireThat(address(pos.positionData.owner) === wallet && address(pool.lbPair.tokenXMint) === mint
    && address(pool.lbPair.tokenYMint) === SOL, 'position_identity');
  const removed = await pool.removeLiquidity({user: new PublicKey(wallet), position: new PublicKey(position),
    fromBinId: pos.positionData.lowerBinId, toBinId: pos.positionData.upperBinId,
    bps: new BN(10000), shouldClaimAndClose: true});
  const txs = Array.isArray(removed) ? removed : [removed];
  requireThat(txs.length === 1, 'multiple_close_transactions');
  const close = txs[0].instructions.map(encode);
  // Respect keyless quote pacing; this remains within the enclosing collector deadline.
  requireThat(deadline - Date.now() > 3100, 'capture_budget');
  await new Promise(resolve => setTimeout(resolve, 2100)); check();
  const built = await fetch('https://api.jup.ag/swap/v1/swap-instructions', {method: 'POST',
    headers: {'Content-Type': 'application/json'}, signal: AbortSignal.timeout(deadline - Date.now()),
    body: JSON.stringify({quoteResponse: sample.quote, userPublicKey: wallet, useTokenLedger: true,
      wrapAndUnwrapSol: true, dynamicComputeUnitLimit: false})});
  requireThat(built.ok, 'swap_instructions_unavailable');
  const response = await boundedJson(built, 1024*1024);
  const keys = dependencyKeys(close, response, {wallet, position, pool: poolAddress, mint});
  const bank = await captureBank(keys, keys => rpc('getMultipleAccounts', [keys,
    {encoding: 'base64', commitment: 'confirmed'}]), position);
  check();
  const fixture = {version: 1, observed_at: Date.now()/1000, wallet, position, pool: poolAddress,
    mint, quote_observation: sample, close_instructions: close, swap_response: response, ...bank,
    rpc_calls: calls, signing_operations: 0, transaction_submissions: 0,
    basis: 'single_response_account_bank; earlier_quote_and_instruction_reads; unsigned_research_only',
    limitations: ['Quote and native inventory predate the bank. Recompute inventory before replay.',
      'Archive is not proof of executable profit, complete CPI coverage or unchanged instruction geometry.',
      'SDK builds unsigned instructions only; no signing or submission. Preserve emergency exit priority.']};
  fs.mkdirSync(dir, {recursive: true, mode: 0o700});
  // Publish only a complete JSON file; interrupted children leave no target.
  const temporary = output + '.' + process.pid + '.tmp';
  fs.writeFileSync(temporary, JSON.stringify(fixture) + '\n', {flag: 'wx', mode: 0o600});
  try { fs.linkSync(temporary, output); } finally { fs.unlinkSync(temporary); }
  return {status: 'archived', snapshot_slot: bank.snapshot_slot, accounts: Object.keys(bank.accounts).length,
    sha256: crypto.createHash('sha256').update(fs.readFileSync(output)).digest('hex')};
}
if (require.main === module) {
  let input = ''; process.stdin.setEncoding('utf8');
  process.stdin.on('data', data => { input += data; if (input.length > 1000000) process.exit(2); });
  process.stdin.on('end', async () => {
    try {
      const {profile, sample, budget_ms} = JSON.parse(input);
      requireThat(Number.isFinite(budget_ms) && budget_ms > 0, 'invalid_budget');
      console.log(JSON.stringify(await capture(profile, sample, budget_ms)));
    } catch { console.log(JSON.stringify({status: 'unmeasured', reason: 'exit_bank_unavailable'})); }
  });
}
module.exports = {dependencyKeys, captureBank, boundedJson, allowed};
