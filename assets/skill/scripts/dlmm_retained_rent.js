// Upper-bound evidence only: a possible rent refund is not received cash.
const {cashSignEvidence}=require('./dlmm_cash_sign.js');
const SYSTEM='11111111111111111111111111111111';
const SOL='So11111111111111111111111111111111111111112';
const TOKENS=new Set(['TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA','TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb']);
const BASIS='parsed_empty_token_rent_with_no_other_retained_wallet_funding';
function retainedRentEvidence(tx,wallet,position) {
  try {
    const m=tx.meta,message=tx.transaction.message;
    if (m.err || !Array.isArray(m.innerInstructions) || !Array.isArray(m.preTokenBalances)
        || !Array.isArray(m.postTokenBalances)) return null;
    const keys=message.accountKeys.map(k=>k.pubkey?.toString());
    const instructions=[...message.instructions,...m.innerInstructions.flatMap(g=>g.instructions)];
    const retained=[],creates=new Set(),seen=new Set();
    for(const t of m.postTokenBalances) {
      if(t.owner!==wallet || m.preTokenBalances.some(p=>p.accountIndex===t.accountIndex)) continue;
      const n=t.accountIndex,account=keys[n];
      if(!Number.isSafeInteger(n) || !account || account===position || account===wallet
          || seen.has(n) || t.mint===SOL || typeof t.mint!=='string' || !t.mint
          || t.uiTokenAmount?.amount!=='0' || m.preBalances[n]!==0
          || !Number.isSafeInteger(m.postBalances[n]) || m.postBalances[n]<=0) return null;
      const funding=instructions.filter(i=>i.programId?.toString()===SYSTEM
        && ['createAccount','createAccountWithSeed'].includes(i.parsed?.type)
        && i.parsed.info?.newAccount===account);
      if(funding.length!==1) return null;
      const info=funding[0].parsed.info;
      if(funding[0].program!=='system' || info.source!==wallet || !TOKENS.has(info.owner)
          || info.lamports!==m.postBalances[n]) return null;
      const init=instructions.filter(i=>i.programId?.toString()===info.owner
        && ['initializeAccount','initializeAccount2','initializeAccount3'].includes(i.parsed?.type)
        && i.parsed.info?.account===account);
      if(init.length!==1 || init[0].parsed.info.owner!==wallet || init[0].parsed.info.mint!==t.mint) return null;
      seen.add(n);creates.add(funding[0]);
      retained.push({account,mint:t.mint,lamports:m.postBalances[n],account_index:n});
    }
    if(!retained.length) return null;
    const cap=retained.reduce((sum,r)=>sum+r.lamports,0);
    if(!Number.isSafeInteger(cap)) return null;
    // Account for exactly the proved creation debits as a maximally refundable
    // reserve, then require the existing strict proof for every remaining effect.
    // No original transaction or metadata is mutated.
    const normalized={...tx,transaction:{...tx.transaction,message:{...message,
      instructions:message.instructions.filter(i=>!creates.has(i))}},meta:{...m,
      preBalances:[...m.preBalances],preTokenBalances:[...m.preTokenBalances],
      innerInstructions:m.innerInstructions.map(g=>({...g,instructions:g.instructions.filter(i=>!creates.has(i))}))}};
    for(const r of retained) {
      normalized.meta.preBalances[r.account_index]=r.lamports;
      normalized.meta.preTokenBalances.push(m.postTokenBalances.find(t=>t.accountIndex===r.account_index));
    }
    if(!cashSignEvidence(normalized,wallet,position)) return null;
    return {version:1,position,basis:BASIS,max_future_rent_credit_lamports:cap,
      funded_accounts:retained.map(({account_index,...r})=>r)};
  } catch {return null;}
}
module.exports={retainedRentEvidence,BASIS};
