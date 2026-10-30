// Read-only native active-bin history. No wallet, transactions, or bin arrays.
const SOL = 'So11111111111111111111111111111111111111112';
async function observe(connection, program, candidates, PublicKey, mayRead) {
  if (!Array.isArray(candidates) || !candidates.length || candidates.length > 30)
    throw new Error('Expected 1..30 candidate identities');
  const seen = new Set();
  const keys = candidates.map(c => {
    if (!c || typeof c.pool !== 'string' || typeof c.base_mint !== 'string'
        || c.base_mint === SOL || seen.has(c.pool)) throw new Error('Invalid candidate identity');
    seen.add(c.pool); new PublicKey(c.base_mint); return new PublicKey(c.pool);
  });
  if (!mayRead()) return {status:'deferred', reason:'wallet_trade_active', observations:[]};
  const requestedAt = Date.now()/1000;
  const response = await connection.getMultipleAccountsInfoAndContext(keys, {commitment:'confirmed'});
  const observedAt = Date.now()/1000;
  if (!Number.isSafeInteger(response.context?.slot) || response.context.slot <= 0
      || !Array.isArray(response.value) || response.value.length !== candidates.length)
    throw new Error('Invalid native account response');
  return {status:'observed', observations:candidates.map((c,i) => {
    const result = {pool:c.pool, base_mint:c.base_mint, requested_at:requestedAt,
      observed_at:observedAt, slot:response.context.slot, commitment:'confirmed',
      basis:'native_lb_pair_active_bin_not_fee_or_profit', status:'unmeasured'};
    try {
      const a = response.value[i];
      if (!a || !a.owner.equals(program.programId)) throw new Error('owner');
      const pair = program.coder.accounts.decode('lbPair', a.data);
      if (pair.tokenXMint.toString() !== c.base_mint || pair.tokenYMint.toString() !== SOL
          || !Number.isSafeInteger(pair.activeId) || Math.abs(pair.activeId)>100000
          || !Number.isSafeInteger(pair.binStep) || pair.binStep <= 0 || pair.binStep > 10000)
        throw new Error('identity');
      return {...result, status:'observed', active_bin:pair.activeId, bin_step:pair.binStep};
    } catch { return {...result, reason:'account_identity_or_decode_unavailable'}; }
  })};
}
module.exports = {observe};
