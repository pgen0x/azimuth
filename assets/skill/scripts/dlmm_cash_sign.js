// Narrow finalized proof: no wallet-funded reserve survives outside this LP.
// Empty tokenRentEvidence.funded alone cannot establish this (e.g. WSOL/PDAs).
const SYSTEM='11111111111111111111111111111111';
const SOL='So11111111111111111111111111111111111111112';
const TOKENS=['TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'];
const PROGRAMS=new Set([SYSTEM,...TOKENS,'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo',
  'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL','ComputeBudget111111111111111111111111111111']);
const BASIS='parsed_system_debits_and_unchanged_retained_token_accounts';

function cashSignEvidence(tx, wallet, position) {
  const m=tx?.meta, message=tx?.transaction?.message;
  if (!position || position===wallet || !m || m.err || !Array.isArray(message?.accountKeys)
      || !Array.isArray(message.instructions) || !Array.isArray(m.innerInstructions)
      || !Array.isArray(m.preTokenBalances) || !Array.isArray(m.postTokenBalances)) return null;
  const keys=message.accountKeys.map(k=>k.pubkey?.toString());
  if (keys[0]!==wallet || message.accountKeys[0].signer!==true || !keys.includes(position)
      || keys.some(k=>typeof k!=='string' || !k) || new Set(keys).size!==keys.length
      || !Array.isArray(m.preBalances) || !Array.isArray(m.postBalances)
      || m.preBalances.length!==keys.length || m.postBalances.length!==keys.length
      || [...m.preBalances,...m.postBalances,m.fee].some(n=>!Number.isSafeInteger(n)||n<0)
      || m.innerInstructions.some(g=>!Array.isArray(g.instructions))) return null;
  const balances=rows=>{
    const result=new Map();
    for (const t of rows) {
      if (!Number.isSafeInteger(t.accountIndex) || !keys[t.accountIndex]
          || typeof t.owner!=='string' || !t.owner || typeof t.mint!=='string' || !t.mint
          || typeof t.uiTokenAmount?.amount!=='string' || !/^[0-9]+$/.test(t.uiTokenAmount.amount)
          || result.has(t.accountIndex)) return null;
      result.set(t.accountIndex,t);
    }
    return result;
  };
  const pre=balances(m.preTokenBalances), post=balances(m.postTokenBalances);
  if (!pre || !post) return null;
  for (const [n,t] of post) if (t.owner===wallet) {
    const before=pre.get(n);
    // No new ATA, WSOL reserve, rent top-up, token proceeds or acquired inventory.
    if (!before || before.owner!==wallet || before.mint!==t.mint
        || before.uiTokenAmount.amount!==t.uiTokenAmount.amount
        || m.preBalances[n]<=0 || m.postBalances[n]>m.preBalances[n]) return null;
  }
  for (const [n,t] of pre) if (t.owner===wallet) {
    const after=post.get(n);
    if (!after || after.owner!==wallet || after.mint!==t.mint
        || after.uiTokenAmount.amount!==t.uiTokenAmount.amount) return null;
  }
  // Also catch retained funding moved directly by a program-owned intermediary,
  // which would not necessarily appear as a system transfer from the wallet.
  for (let n=1;n<keys.length;n++) if (keys[n]!==position && m.postBalances[n]>m.preBalances[n]) {
    const before=pre.get(n), after=post.get(n);
    if (!before || !after || before.owner===wallet || before.owner!==after.owner
        || before.mint!==SOL || after.mint!==SOL || m.preBalances[n]<=0
        || BigInt(after.uiTokenAmount.amount)-BigInt(before.uiTokenAmount.amount)
           !==BigInt(m.postBalances[n]-m.preBalances[n])) return null;
  }
  const instructions=[...message.instructions,...m.innerInstructions.flatMap(g=>g.instructions)];
  const temporaryWSOL=account=>{
    const n=keys.indexOf(account);
    if (n<0 || m.preBalances[n]!==0 || m.postBalances[n]!==0) return false;
    const creates=instructions.filter(i=>i.programId?.toString()===SYSTEM
      && ['createAccount','createAccountWithSeed'].includes(i.parsed?.type)
      && i.parsed.info?.newAccount===account);
    return creates.length===1 && TOKENS.includes(creates[0].parsed.info.owner)
      && instructions.some(i=>i.programId?.toString()===creates[0].parsed.info.owner
        && ['initializeAccount','initializeAccount2','initializeAccount3'].includes(i.parsed?.type)
        && i.parsed.info?.account===account && i.parsed.info.mint===SOL && i.parsed.info.owner===wallet)
      && instructions.some(i=>i.programId?.toString()===creates[0].parsed.info.owner
        && i.parsed?.type==='closeAccount' && i.parsed.info?.account===account
        && i.parsed.info.owner===wallet && i.parsed.info.destination===wallet);
  };
  for (const i of instructions) {
    const id=i.programId?.toString();
    if (!PROGRAMS.has(id)) return null;
    if (id!==SYSTEM && i.program!=='system') continue;
    if (id!==SYSTEM || i.program!=='system') return null;
    const type=i.parsed?.type, info=i.parsed?.info;
    if (!info) return null;
    if (['transfer','transferWithSeed','createAccount','createAccountWithSeed'].includes(type)) {
      if (typeof info.source!=='string' || !Number.isSafeInteger(info.lamports) || info.lamports<0) return null;
      const destination=type.startsWith('create') ? info.newAccount : info.destination;
      const n=keys.indexOf(destination);
      if (n<0 || (destination!==position && !(info.source!==wallet && destination===wallet)
          && !temporaryWSOL(destination))) return null;
    } else if (['allocate','allocateWithSeed','assign','assignWithSeed'].includes(type)) {
      if (typeof info.account!=='string' || info.account===wallet) return null;
    } else return null; // Includes unknown/unparsed system effects and nonce operations.
  }
  return {version:1,position,basis:BASIS,no_retained_wallet_funding_outside_position:true};
}

// Optional metadata follows missing cash facts, never invalidates coverage, and
// gets at most four reads per collection. Persist null attempts too: no hot loop.
function cashSignRefresh(events, cache, closes, wallet, stamp) {
  const closed=new Set(closes.filter(c=>!c.dry_run && typeof c.position==='string'
    && Number.isFinite(c.ts) && c.ts<=stamp && c.ts>=stamp-2*86400).map(c=>c.position));
  const byPosition=new Map();
  for (const e of events.values()) if (closed.has(e.position) && e.wallet===wallet) {
    if (!byPosition.has(e.position)) byPosition.set(e.position,[]);
    byPosition.get(e.position).push(e.signature);
  }
  const pending=[];
  for (const signatures of byPosition.values()) {
    const facts=signatures.map(s=>cache.get(s));
    if (facts.some(f=>!f || f.wallet!==wallet || f.landed===false
        || !Number.isSafeInteger(f.wallet_delta_lamports)
        || !Array.isArray(f.token_rent_evidence?.funded) || f.token_rent_evidence.funded.length)
        || facts.reduce((sum,f)=>sum+f.wallet_delta_lamports,0)>0) continue;
    pending.push(...signatures.filter(s=>!Object.hasOwn(cache.get(s),'cash_sign_evidence')));
  }
  return new Set(pending.slice(0,4));
}
module.exports={cashSignEvidence,cashSignRefresh,BASIS};
