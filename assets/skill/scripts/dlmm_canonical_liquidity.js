// Optional background evidence. Never loads a wallet, signs, or gates a trade.
const crypto = require("node:crypto");
const AMM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA";
const PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P";
const SOL = "So11111111111111111111111111111111111111112";
const TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
const TOKEN22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb";
const ATA = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL";
const BASIS = "native_canonical_pump_accounts; circulating_LP_is_potential_withdrawal_upper_bound; not_profit_or_withdrawability_proof";
const POOL_TAG = crypto.createHash("sha256").update("account:Pool").digest().subarray(0, 8);
const U64_MAX = (1n << 64n) - 1n;

function requireFact(condition) {
  if (!condition) throw new Error("invalid_native_accounts");
}

function canonicalKeys(baseMint) {
  const {PublicKey} = require("@solana/web3.js");
  const base = new PublicKey(baseMint), sol = new PublicKey(SOL), amm = new PublicKey(AMM);
  requireFact(base.toString() !== SOL);
  const authority = PublicKey.findProgramAddressSync([Buffer.from("pool-authority"), base.toBuffer()], new PublicKey(PUMP))[0];
  const pool = PublicKey.findProgramAddressSync([Buffer.from("pool"), Buffer.alloc(2), authority.toBuffer(), base.toBuffer(), sol.toBuffer()], amm)[0];
  const lp = PublicKey.findProgramAddressSync([Buffer.from("pool_lp_mint"), pool.toBuffer()], amm)[0];
  const vault = (mint, program) => PublicKey.findProgramAddressSync(
    [pool.toBuffer(), new PublicKey(program).toBuffer(), mint.toBuffer()], new PublicKey(ATA))[0];
  const baseLegacy = vault(base, TOKEN), base22 = vault(base, TOKEN22), quote = vault(sol, TOKEN);
  return {PublicKey, base, authority, pool, lp, baseLegacy, base22, quote,
    addresses: [pool, lp, baseLegacy, base22, quote].map(key => key.toString())};
}

function accountBytes(account, owners, minimum) {
  requireFact(account && owners.includes(account.owner) && account.executable === false
    && Array.isArray(account.data) && account.data.length === 2 && account.data[1] === "base64"
    && typeof account.data[0] === "string" && account.data[0].length <= 5500
    && /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(account.data[0]));
  const bytes = Buffer.from(account.data[0], "base64");
  requireFact(bytes.length >= minimum && bytes.length <= 4096);
  return bytes;
}

function decodeSnapshot(response, keys) {
  requireFact(Number.isSafeInteger(response?.context?.slot) && response.context.slot > 0
    && Array.isArray(response.value) && response.value.length === keys.addresses.length);
  const [poolAccount, mintAccount, baseLegacy, base22, quoteAccount] = response.value;
  if (poolAccount === null) return {status: "unmeasured", reason: "canonical_pool_absent"};
  const pool = accountBytes(poolAccount, [AMM], 243), address = (bytes, offset) =>
    new keys.PublicKey(bytes.subarray(offset, offset + 32)).toString();
  requireFact(pool.subarray(0, 8).equals(POOL_TAG) && pool.readUInt16LE(9) === 0
    && address(pool, 11) === keys.authority.toString() && address(pool, 43) === keys.base.toString()
    && address(pool, 75) === SOL && address(pool, 107) === keys.lp.toString()
    && address(pool, 171) === keys.quote.toString());
  const baseAddress = address(pool, 139);
  requireFact([keys.baseLegacy.toString(), keys.base22.toString()].includes(baseAddress));
  const baseAccount = baseAddress === keys.baseLegacy.toString() ? baseLegacy : base22;
  const baseProgram = baseAddress === keys.baseLegacy.toString() ? TOKEN : TOKEN22;
  const mint = accountBytes(mintAccount, [TOKEN, TOKEN22], 82);
  requireFact(mint[45] === 1 && [0, 1].includes(mint.readUInt32LE(0))
    && [0, 1].includes(mint.readUInt32LE(46)));
  // Token-2022 keeps the SPL base layout; appended mint/account extensions
  // do not turn circulating supply into proof that liquidity is withdrawable.
  requireFact(mintAccount.owner !== TOKEN || mint.length === 82);
  requireFact(mint.length === 82 || mintAccount.owner === TOKEN22 && mint.length >= 166 && mint[165] === 1);
  const token = (account, program, mintAddress) => {
    const bytes = accountBytes(account, [program], 165);
    requireFact(address(bytes, 0) === mintAddress && address(bytes, 32) === keys.pool.toString() && bytes[108] === 1);
    requireFact(program !== TOKEN || bytes.length === 165);
    requireFact(bytes.length === 165 || program === TOKEN22 && bytes.length >= 166 && bytes[165] === 2);
    return bytes.readBigUInt64LE(64);
  };
  const baseReserve = token(baseAccount, baseProgram, keys.base.toString());
  const quoteReserve = token(quoteAccount, TOKEN, SOL);
  const supply = mint.readBigUInt64LE(36), basis = pool.readBigUInt64LE(203);
  // Appended fields are zero only when wholly absent, as the protocol documents.
  const optional = (offset, size, read) => {
    if (pool.length <= offset) return 0n;
    requireFact(pool.length >= offset + size);
    return read();
  };
  for (const offset of [243, 244, 269, 270]) optional(offset, 1, () => {
    requireFact(pool[offset] === 0 || pool[offset] === 1); return BigInt(pool[offset]);
  });
  const virtual = optional(245, 16, () => pool.readBigInt64LE(253) * (1n << 64n) + pool.readBigUInt64LE(245));
  optional(261, 8, () => pool.readBigUInt64LE(261));
  const protocolFees = optional(271, 8, () => pool.readBigUInt64LE(271));
  const creatorFees = optional(279, 8, () => pool.readBigUInt64LE(279));
  const fees = protocolFees + creatorFees, realQuote = quoteReserve - fees;
  const effectiveQuote = quoteReserve + virtual, boost = virtual + fees;
  requireFact(basis > 0n && supply <= basis && realQuote >= 0n && boost >= 0n
    && effectiveQuote >= 0n && effectiveQuote <= U64_MAX);
  return {status: "observed", context_slot: response.context.slot,
    canonical_pool: keys.pool.toString(), lp_mint: keys.lp.toString(),
    lp_token_program: mintAccount.owner, lp_circulating_raw: supply.toString(), protocol_lp_basis_raw: basis.toString(),
    lp_freeze_authority: mint.readUInt32LE(46) === 1 ? address(mint, 50) : null,
    pool_coin_creator: address(pool, 211), base_token_program: baseProgram,
    base_reserve_raw: baseReserve.toString(), quote_vault_raw: quoteReserve.toString(),
    signed_virtual_quote_raw: virtual.toString(), protocol_fees_raw: protocolFees.toString(), creator_fees_raw: creatorFees.toString(),
    real_quote_raw: realQuote.toString(), effective_quote_raw: effectiveQuote.toString(), boost_reserves_raw: boost.toString(),
    basis: BASIS};
}

async function observeCanonicalLiquidity(rpcUrl, baseMint, {timeoutMs = 300, mayRead = () => true, fetchFn = fetch} = {}) {
  const started = Date.now() / 1000;
  const envelope = {version: 1, base_mint: baseMint, quote_mint: SOL, request_started_at: started};
  const unknown = reason => ({status: "unmeasured", reason});
  const controller = new AbortController();
  let timer;
  try {
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) return {...envelope, ...unknown("budget_exhausted"), observed_at: Date.now() / 1000};
    if (!mayRead()) return {...envelope, ...unknown("wallet_trade_active"), observed_at: Date.now() / 1000};
    const keys = canonicalKeys(baseMint);
    const request = (async () => {
      const response = await fetchFn(rpcUrl, {method: "POST", headers: {"content-type": "application/json"},
        body: JSON.stringify({jsonrpc: "2.0", id: 1, method: "getMultipleAccounts",
          params: [keys.addresses, {encoding: "base64", commitment: "confirmed"}]}), signal: controller.signal});
      if (!response.ok) return unknown("rpc_unavailable");
      const data = await response.json();
      if (data.error) return unknown("rpc_unavailable");
      return decodeSnapshot(data.result, keys);
    })().catch(() => unknown("native_evidence_unavailable"));
    const timeout = new Promise(resolve => {
      timer = setTimeout(() => {controller.abort(); resolve(unknown("read_timeout"));}, Math.min(300, timeoutMs));
    });
    return {...envelope, ...await Promise.race([request, timeout]), observed_at: Date.now() / 1000};
  } catch {
    return {...envelope, ...unknown("native_evidence_unavailable"), observed_at: Date.now() / 1000};
  } finally {
    clearTimeout(timer);
    controller.abort();
  }
}

module.exports = {canonicalKeys, decodeSnapshot, observeCanonicalLiquidity, BASIS};
