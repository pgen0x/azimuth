// Read-only wallet coverage and marked NAV. No signing or transaction submission.
const fs = require('fs');
const path = require('path');
const SOL = 'So11111111111111111111111111111111111111112';
const TOKEN_PROGRAMS = ['TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'];
const read = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : [];
const append = (file, row) => fs.appendFileSync(file, JSON.stringify(row) + '\n', {mode: 0o600});
const now = () => Math.floor(Date.now()/1000);
let quoteReadyAt = 0;
async function json(url, attempts=3, timeout=12000, deadline=Infinity) {
  for (let attempt=0; attempt<attempts; attempt++) {
    const quote = url.includes("/quote?");
    if (quote) {
      // Keyless Jupiter is 0.5 RPS; reserve time for the response before waiting.
      const wait = Math.max(2100, quoteReadyAt-Date.now());
      if (Date.now()+wait+timeout > deadline) throw new Error('quote_budget_deferred');
      await new Promise(resolve=>setTimeout(resolve,wait));
    }
    const response = await fetch(url, {headers: {'User-Agent': 'curl/8.5.0'}, signal: AbortSignal.timeout(timeout)});
    if (quote) {
      const remaining = response.headers?.get('x-ratelimit-remaining');
      const reset = response.headers?.get('x-ratelimit-reset');
      const stamp = Number(reset)*1000;
      if ((response.status===429 || (typeof remaining==='string' && remaining.trim() && Number.isSafeInteger(Number(remaining)) && Number(remaining)<=0))
          && typeof reset==='string' && /^[0-9]+$/.test(reset) && Number.isSafeInteger(stamp)
          && stamp>Date.now() && stamp-Date.now()<=60000) quoteReadyAt=stamp+100;
    }
    if (response.status===429 && attempt<attempts-1) { await new Promise(resolve=>setTimeout(resolve,1000*(attempt+1))); continue; }
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
}

// Validate the response identity and provider slot before promoting a quote to NAV.
function navQuoteMark(q, mint, raw, slot) {
  if (!Number.isSafeInteger(slot) || slot<=0 || !q || q.inputMint!==mint || q.outputMint!==SOL || q.inAmount!==raw || q.swapMode!=='ExactIn'
      || typeof q.outAmount!=='string' || !/^[0-9]+$/.test(q.outAmount) || BigInt(q.outAmount)<=0n
      || !Number.isFinite(Number(q.outAmount)) || !Number.isSafeInteger(q.contextSlot) || q.contextSlot<=0
      || Math.abs(q.contextSlot-slot)>1500) throw new Error('Invalid or stale quote evidence');
  // Quote slots can lead finalized balance slots; retain the provider's slot.
  return {schema_version:2,in_amount:raw,out_lamports:q.outAmount,observed_at:now(),slot:q.contextSlot};
}

// Additional provider marks only; finalized RPC remains the balance source.
async function heliusPrices(wallet, env=process.env) {
  const keys=new Set([env.HELIUS_API_KEY].filter(Boolean));
  for (const endpoint of (env.SOLANA_RPC_URLS || '').split(',')) {
    try {
      const u=new URL(endpoint.trim());
      if (u.protocol==='https:' && (u.hostname==='helius-rpc.com' || u.hostname.endsWith('.helius-rpc.com'))) {
        const key=u.searchParams.get('api-key'); if(key) keys.add(key);
      }
    } catch { /* Non-Helius endpoints provide no Wallet API credentials. */ }
  }
  let status=keys.size ? 'unavailable' : 'not_configured';
  const deadline=Date.now()+12000;
  for (const key of keys) {
    const marks=new Map();
    try {
      for (let page=1;page<=20;page++) {
        if (Date.now()>=deadline) throw new Error('budget_exhausted');
        const response=await fetch(`https://api.helius.xyz/v1/wallet/${encodeURIComponent(wallet)}/balances?page=${page}&limit=100&showNative=true`,
          {headers:{'X-Api-Key':key},redirect:'error',signal:AbortSignal.timeout(Math.max(1,Math.min(4000,deadline-Date.now())))});
        if (!response.ok) { status=`http_${response.status}`; break; }
        const data=await response.json();
        if (!Array.isArray(data.balances) || typeof data.pagination?.hasMore!=='boolean') throw new Error('invalid_response');
        for (const b of data.balances) {
          if (typeof b.mint!=='string' || !Number.isFinite(b.pricePerToken) || b.pricePerToken<=0
              || !Number.isInteger(b.decimals) || b.decimals<0 || b.decimals>255) continue;
          const mint=b.mint==='So11111111111111111111111111111111111111111' ? SOL : b.mint;
          marks.set(mint,{usdPrice:b.pricePerToken,decimals:b.decimals,observed_at:now()});
        }
        if (!data.pagination.hasMore) return {marks,status:'ok'};
        if (page===20) status='pagination_incomplete';
      }
    } catch { status='unavailable'; } // Never persist credentials or response bodies.
    if (Date.now()>=deadline) break;
  }
  return {marks:new Map(),status}; // Discard partial pages before trying another key.
}

// Recognize only the observed empty-account cleaning wrapper with fully
// explained token closures and native balance changes. Extra effects fail closed.
function rentMaintenance(tx, wallet) {
  const wrapper='CLEANALo6FtS6quqTTEXDGFFTuSKMkeKGgcweeiPRJzK';
  const compute='ComputeBudget111111111111111111111111111111';
  const message=tx.transaction.message, meta=tx.meta;
  const keys=message.accountKeys.map(k=>k.pubkey.toString());
  if (meta.err || keys[0]!==wallet || message.accountKeys[0].signer!==true
      || !Number.isSafeInteger(meta.fee) || meta.fee<0
      || meta.preBalances.length!==keys.length || meta.postBalances.length!==keys.length
      || [...meta.preBalances,...meta.postBalances].some(v=>!Number.isSafeInteger(v) || v<0)
      || (meta.postTokenBalances || []).length) return null;
  const outer=message.instructions;
  if (!outer.length || !outer.every(i=>[wrapper,compute].includes(i.programId?.toString()))) return null;
  const groups=meta.innerInstructions || [], wrappers=outer.filter(i=>i.programId?.toString()===wrapper);
  if (!wrappers.length || groups.length!==wrappers.length || new Set(groups.map(g=>g.index)).size!==groups.length) return null;
  const changes=keys.map(()=>0); changes[0]=-meta.fee;
  const closed=new Set(); let released=0, serviceFee=0;
  for (const group of groups) {
    if (outer[group.index]?.programId?.toString()!==wrapper || ![2,3].includes(group.instructions.length)) return null;
    const [close,...transfers]=group.instructions, a=close.parsed?.info;
    if (!TOKEN_PROGRAMS.includes(close.programId?.toString()) || close.parsed?.type!=='closeAccount'
        || a?.owner!==wallet || a.destination!==wallet) return null;
    const account=keys.indexOf(a.account);
    const token=(meta.preTokenBalances || []).find(t=>t.accountIndex===account);
    if (account<=0 || closed.has(account) || !token || token.owner!==wallet
        || token.mint===SOL || token.uiTokenAmount?.amount!=='0'
        || meta.preBalances[account]<=0 || meta.postBalances[account]!==0) return null;
    closed.add(account);
    const rent=meta.preBalances[account]; released+=rent;
    changes[account]-=rent; changes[0]+=rent;
    for (const transfer of transfers) {
      const b=transfer.parsed?.info, recipient=keys.indexOf(b?.destination);
      if (transfer.programId?.toString()!=='11111111111111111111111111111111'
          || transfer.parsed?.type!=='transfer' || b?.source!==wallet || recipient<=0
          || !Number.isSafeInteger(b.lamports) || b.lamports<0) return null;
      serviceFee+=b.lamports; changes[0]-=b.lamports; changes[recipient]+=b.lamports;
    }
  }
  if (closed.size!==(meta.preTokenBalances || []).length
      || !Number.isSafeInteger(released) || !Number.isSafeInteger(serviceFee)
      || changes[0]<0 || changes.some((v,i)=>!Number.isSafeInteger(v) || meta.postBalances[i]-meta.preBalances[i]!==v)) return null;
  return {released_lamports:released,service_fee_lamports:serviceFee};
}

// Observed Pump cashback + accumulator close. Exact instruction shape and all
// balance deltas must agree; rewards stay wallet-level, never LP-root profit.
// Discriminators/accounts: pump-fun/pump-public-docs idl/pump_amm.json.
function pumpMaintenance(tx, wallet) {
  const wrapper='68kTkdQsd9WhXgsg5X9untjvpSinwAMrJgYHXG9NRQmD';
  const pump='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA';
  const system='11111111111111111111111111111111', token=TOKEN_PROGRAMS[0];
  const ata='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL';
  const m=tx.meta, msg=tx.transaction.message, outer=msg.instructions;
  if (!outer.some(i=>i.programId?.toString()===wrapper)) return null;
  const keys=msg.accountKeys.map(k=>k.pubkey.toString()), groups=m.innerInstructions || [];
  if (m.err || keys[0]!==wallet || msg.accountKeys[0].signer!==true
      || !Number.isSafeInteger(m.fee) || m.fee<0
      || m.preBalances.length!==keys.length || m.postBalances.length!==keys.length
      || [...m.preBalances,...m.postBalances].some(v=>!Number.isSafeInteger(v) || v<0)
      || (m.preTokenBalances || []).length!==1 || (m.postTokenBalances || []).length!==1
      || groups.length!==1 || outer.filter(i=>i.programId?.toString()===wrapper).length!==1
      || !outer.every(i=>[wrapper,'ComputeBudget111111111111111111111111111111'].includes(i.programId?.toString()))
      || outer[groups[0].index]?.programId?.toString()!==wrapper) return null;
  const ins=groups[0].instructions;
  const shape=[[ata,'create',2],[token,'getAccountDataSize',3],[system,'createAccount',3],
    [token,'initializeImmutableOwner',3],[token,'initializeAccount3',3],
    [pump,null,2],[token,'transferChecked',3],[pump,null,3],[token,'closeAccount',2],
    [pump,null,2],[pump,null,3],[system,'transfer',2],[system,'transfer',2]];
  if (ins.length!==shape.length || ins.some((i,n)=>i.programId?.toString()!==shape[n][0]
      || (i.parsed?.type || null)!==shape[n][1] || i.stackHeight!==shape[n][2])) return null;
  // The finalized Pump instructions enforce their PDA constraints; bind the
  // same accumulator/vault/user account across every decoded instruction here.
  const [,accumulator,,,vault,account,,authority]=ins[5].accounts?.map(String) || [];
  if ([accumulator,vault,account,authority].some(a=>typeof a!=='string')
      || new Set([wallet,accumulator,vault,account,authority]).size!==5) return null;
  const accounts=(i,want)=>JSON.stringify(i.accounts?.map(String))===JSON.stringify(want);
  if (ins[5].data!=='7E9g4XZrCjE' || !accounts(ins[5],[wallet,accumulator,SOL,token,vault,account,system,authority,pump])
      || ins[9].data!=='ihFZiQrP7CM' || !accounts(ins[9],[wallet,accumulator,authority,pump])
      || !accounts(ins[7],[authority]) || !accounts(ins[10],[authority])) return null;
  const info=n=>ins[n].parsed.info, create=info(2), credit=info(6), close=info(8);
  if (info(0).account!==account || info(0).wallet!==wallet || info(0).source!==wallet
      || info(0).mint!==SOL || info(0).tokenProgram!==token || info(0).systemProgram!==system
      || info(1).mint!==SOL || create.newAccount!==account || create.source!==wallet
      || create.owner!==token || create.space!==165 || !Number.isSafeInteger(create.lamports) || create.lamports<=0
      || info(3).account!==account || info(4).account!==account || info(4).owner!==wallet || info(4).mint!==SOL
      || credit.authority!==accumulator || credit.source!==vault || credit.destination!==account || credit.mint!==SOL
      || credit.tokenAmount?.decimals!==9 || !/^\d+$/.test(credit.tokenAmount?.amount || '')
      || close.account!==account || close.owner!==wallet || close.destination!==wallet) return null;
  const ai=keys.indexOf(accumulator), vi=keys.indexOf(vault), ti=keys.indexOf(account);
  const cashback=Number(credit.tokenAmount.amount);
  if (ai<=0 || vi<=0 || ti<=0 || m.preBalances[ai]<=0 || m.postBalances[ai]!==0
      || m.preBalances[ti]!==0 || m.postBalances[ti]!==0 || !Number.isSafeInteger(cashback) || cashback<=0) return null;
  const pre=m.preTokenBalances[0], post=m.postTokenBalances[0];
  if ([pre,post].some(t=>t.accountIndex!==vi || t.owner!==accumulator || t.mint!==SOL
      || t.programId!==token || t.uiTokenAmount?.decimals!==9
      || !/^\d+$/.test(t.uiTokenAmount?.amount || ''))
      || BigInt(pre.uiTokenAmount.amount)-BigInt(post.uiTokenAmount.amount)!==BigInt(cashback)) return null;
  const rent=m.preBalances[ai], changes=keys.map(()=>0);
  changes[0]=rent+cashback-m.fee; changes[ai]=-rent; changes[vi]=-cashback;
  let fees=0;
  for (const n of [11,12]) {
    const b=info(n), recipient=keys.indexOf(b.destination);
    if (b.source!==wallet || recipient<=0 || !Number.isSafeInteger(b.lamports) || b.lamports<0) return null;
    fees+=b.lamports;changes[0]-=b.lamports;changes[recipient]+=b.lamports;
  }
  if (!Number.isSafeInteger(fees) || changes.some((v,i)=>!Number.isSafeInteger(v) || m.postBalances[i]-m.preBalances[i]!==v)) return null;
  return {released_lamports:rent,service_fee_lamports:fees,cashback_lamports:cashback};
}

// Account-level evidence for later rent attribution. Missing historical fields
// mean unmeasured; this additive field must not trigger a bulk cache migration.
function tokenRentEvidence(tx, wallet) {
  const meta=tx.meta, message=tx.transaction.message;
  const keys=message.accountKeys.map(k=>k.pubkey.toString());
  const evidence={version:1,funded:[],refunded:[]};
  if (meta.err) return evidence;
  const instructions=[...message.instructions,...(meta.innerInstructions || []).flatMap(g=>g.instructions)];
  for (const token of meta.postTokenBalances || []) {
    const n=token.accountIndex, account=keys[n];
    if (!account || token.owner!==wallet || token.mint===SOL || meta.preBalances[n]!==0
        || !Number.isSafeInteger(meta.postBalances[n]) || meta.postBalances[n]<=0) continue;
    const creates=instructions.filter(i=>i.program==='system'
      && ['createAccount','createAccountWithSeed'].includes(i.parsed?.type)
      && i.parsed.info?.newAccount===account);
    if (creates.length!==1 || creates[0].parsed.info.source!==wallet
        || !TOKEN_PROGRAMS.includes(creates[0].parsed.info.owner)
        || creates[0].parsed.info.lamports!==meta.postBalances[n]) continue;
    evidence.funded.push({account,mint:token.mint,lamports:meta.postBalances[n]});
  }
  // Mixed closes can contain rent in the wallet delta without proving its amount.
  const closes=instructions.filter(i=>TOKEN_PROGRAMS.includes(i.programId?.toString())
    && i.parsed?.type==='closeAccount' && i.parsed.info?.destination===wallet);
  if (closes.some(i=>{
    const account=i.parsed.info.account, n=keys.indexOf(account);
    const token=(meta.preTokenBalances || []).find(t=>t.accountIndex===n);
    return token ? token.mint!==SOL : !(meta.preBalances[n]===0 && instructions.some(x=>
      x.programId?.toString()===i.programId?.toString()
      && ['initializeAccount','initializeAccount2','initializeAccount3'].includes(x.parsed?.type)
      && x.parsed.info?.account===account && x.parsed.info.mint===SOL));
  })) evidence.refunds_unmeasured=true;
  // Accept refunds only for pure empty-token-account closes with every native
  // balance change explained. Combined swaps/LP closes stay unmeasured here.
  if (keys[0]!==wallet || message.accountKeys[0].signer!==true
      || !Number.isSafeInteger(meta.fee) || meta.fee<0
      || meta.preBalances.length!==keys.length || meta.postBalances.length!==keys.length
      || [...meta.preBalances,...meta.postBalances].some(n=>!Number.isSafeInteger(n)||n<0)
      || (meta.postTokenBalances || []).length) return evidence;
  const changes=keys.map(()=>0), refunds=[], closed=new Set(); changes[0]=-meta.fee;
  for (const i of instructions) {
    if (i.programId?.toString()==='ComputeBudget111111111111111111111111111111') continue;
    const info=i.parsed?.info, n=keys.indexOf(info?.account);
    const token=(meta.preTokenBalances || []).find(t=>t.accountIndex===n);
    if (!TOKEN_PROGRAMS.includes(i.programId?.toString()) || i.parsed?.type!=='closeAccount'
        || info?.destination!==wallet || info.owner!==wallet || n<=0 || closed.has(n)
        || !token || token.owner!==wallet || token.mint===SOL || token.uiTokenAmount?.amount!=='0'
        || meta.preBalances[n]<=0 || meta.postBalances[n]!==0) return evidence;
    closed.add(n);
    const lamports=meta.preBalances[n]; changes[n]-=lamports; changes[0]+=lamports;
    refunds.push({account:keys[n],mint:token.mint,lamports});
  }
  if (refunds.length && closed.size===(meta.preTokenBalances || []).length
      && changes.every((n,i)=>Number.isSafeInteger(n)&&meta.postBalances[i]-meta.preBalances[i]===n)) {
    evidence.refunded=refunds;
    delete evidence.refunds_unmeasured;
  }
  return evidence;
}

// web3.js 1.x rejects version 1 in its response schema. Keep its normal reader
// for legacy/v0; use the same RPC transport only for an explicit v1 refusal.
async function parsedAccountingTransaction(connection, signature) {
  try {
    return await connection.getParsedTransaction(signature,{commitment:'finalized',maxSupportedTransactionVersion:0});
  } catch (err) {
    if (err.code !== -32015 || !/Transaction version \(1\)/.test(err.message)) throw err;
  }
  const response = await connection._rpcRequest('getTransaction', [signature,
    {encoding:'jsonParsed',commitment:'finalized',maxSupportedTransactionVersion:1}]);
  if (response.error) throw new Error('Version 1 accounting RPC error');
  const tx = response.result;
  if (tx === null) return null;
  const message=tx?.transaction?.message, meta=tx?.meta, keys=message?.accountKeys;
  const address=s=>typeof s==='string' && /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(s);
  const instruction=i=>i && address(i.programId) &&
    (i.parsed && typeof i.parsed==='object' || Array.isArray(i.accounts) && i.accounts.every(address) && typeof i.data==='string');
  if (tx?.version!==1 || tx.transaction?.signatures?.[0]!==signature ||
      !Number.isSafeInteger(tx.slot) || tx.slot<0 || !(tx.blockTime===null || Number.isSafeInteger(tx.blockTime)) ||
      !Array.isArray(keys) || !keys.length || keys.some(k=>!address(k.pubkey)||typeof k.signer!=='boolean'||typeof k.writable!=='boolean') ||
      new Set(keys.map(k=>k.pubkey)).size!==keys.length || !meta || !Object.hasOwn(meta,'err') ||
      !Number.isSafeInteger(meta.fee) || meta.fee<0 ||
      ![meta.preBalances,meta.postBalances].every(a=>Array.isArray(a)&&a.length===keys.length&&a.every(n=>Number.isSafeInteger(n)&&n>=0)) ||
      !Array.isArray(message.instructions) || !message.instructions.every(instruction) ||
      !(meta.innerInstructions===null || Array.isArray(meta.innerInstructions)&&meta.innerInstructions.every(g=>Number.isSafeInteger(g.index)&&g.index>=0&&g.index<message.instructions.length&&Array.isArray(g.instructions)&&g.instructions.every(instruction))) ||
      ![meta.preTokenBalances,meta.postTokenBalances].every(a=>Array.isArray(a)&&a.every(t=>
        Number.isSafeInteger(t.accountIndex)&&t.accountIndex>=0&&t.accountIndex<keys.length&&address(t.mint)&&address(t.owner)&&
        typeof t.uiTokenAmount?.amount==='string'&&/^\d+$/.test(t.uiTokenAmount.amount)))) {
    throw new Error('Invalid version 1 accounting transaction');
  }
  return tx;
}

function transactionFact(tx, wallet, signature, event) {
  const keys = tx.transaction.message.accountKeys.map(k => k.pubkey.toString());
  const index = keys.indexOf(wallet), meta = tx.meta;
  if (index < 0 || !meta || ![meta.preBalances[index], meta.postBalances[index], meta.fee].every(Number.isSafeInteger)) throw new Error('Invalid wallet balances');
  const tokenDeltas = {}, tokenPre = {}, tokenPost = {}, tokenAccounts = new Set();
  for (const [rows, sign] of [[meta.preTokenBalances, -1n], [meta.postTokenBalances, 1n]]) {
    for (const r of rows || []) if (r.owner === wallet) {
      tokenDeltas[r.mint] = (tokenDeltas[r.mint] || 0n) + sign*BigInt(r.uiTokenAmount.amount);
      const balances=sign<0n ? tokenPre : tokenPost;
      balances[r.mint]=(balances[r.mint] || 0n)+BigInt(r.uiTokenAmount.amount);
      tokenAccounts.add(keys[r.accountIndex]);
    }
  }
  const instructions = [...tx.transaction.message.instructions, ...(meta.innerInstructions || []).flatMap(i => i.instructions)];
  let external = 0, rentLocked = 0, permanentRent = 0;
  let simpleTransfer = !event && !meta.err && instructions.every(i => i.program === 'system' && i.parsed?.type === 'transfer' || ['ComputeBudget111111111111111111111111111111','MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'].includes(i.programId?.toString()));
  for (const i of instructions) {
    const info = i.parsed?.info || {};
    if (simpleTransfer && i.program === 'system') {
      if (info.destination === wallet) external += info.lamports;
      if (info.source === wallet) external -= info.lamports;
    }
    if (!meta.err && i.program === 'system' && ['createAccount', 'createAccountWithSeed'].includes(i.parsed?.type) && info.source === wallet) {
      const n = keys.indexOf(info.newAccount);
      if (n >= 0 && meta.postBalances[n] > 0) {
        const amount = meta.postBalances[n] - meta.preBalances[n];
        if (tokenAccounts.has(info.newAccount) || info.newAccount === event?.position) rentLocked += amount;
        else permanentRent += amount;
      }
    }
  }
  simpleTransfer = simpleTransfer && Number.isSafeInteger(external)
    && external === meta.postBalances[index]-meta.preBalances[index]+(index===0 ? meta.fee : 0)
    && Object.values(tokenDeltas).every(amount=>amount===0n);
  // Some programs initialize PDAs with transfer + allocate + assign instead
  // of createAccount. Count only newly funded accounts with exact provenance.
  if (!meta.err) for (const i of instructions) {
    if (i.program !== 'system' || i.parsed?.type !== 'allocate') continue;
    const account=i.parsed.info?.account, n=keys.indexOf(account);
    if (instructions.filter(x=>x.program==='system' && x.parsed?.type==='allocate' && x.parsed.info?.account===account).length!==1) continue;
    if (n<0 || meta.preBalances[n]!==0 || !Number.isSafeInteger(meta.postBalances[n]) || meta.postBalances[n]<=0) continue;
    if (instructions.some(x=>x.program==='system' && ['createAccount','createAccountWithSeed'].includes(x.parsed?.type) && x.parsed.info?.newAccount===account)) continue;
    const assignments=instructions.filter(x=>x.program==='system' && x.parsed?.type==='assign' && x.parsed.info?.account===account);
    const transfers=instructions.filter(x=>x.program==='system' && x.parsed?.type==='transfer' && x.parsed.info?.destination===account);
    if (assignments.length!==1 || !assignments[0].parsed.info.owner || transfers.length===0
        || transfers.some(x=>x.parsed.info.source!==wallet || !Number.isSafeInteger(x.parsed.info.lamports) || x.parsed.info.lamports<=0)) continue;
    const amount=transfers.reduce((sum,x)=>sum+x.parsed.info.lamports,0);
    if (!Number.isSafeInteger(amount) || amount!==meta.postBalances[n]) continue;
    if (tokenAccounts.has(account) || account===event?.position) rentLocked+=amount;
    else permanentRent+=amount;
  }
  // Passive NFT activity is outside the SOL/SPL/LP accounting scope.
  const passiveNFT = !event && !meta.err && tx.transaction.message.accountKeys[index].writable === false
    && tx.transaction.message.accountKeys[index].signer === false
    && meta.preBalances[index] === meta.postBalances[index] && tokenAccounts.size === 0
    && tx.transaction.message.instructions.length > 0
    && tx.transaction.message.instructions.every(i => i.programId?.toString() === 'BGUMAp9Gq7iTEuizy4pqaxsTyUCBK68MDfK752saRPUY');
  // A plain unsolicited SPL credit is an external asset inflow, not bot PnL.
  // Require all outer/inner instructions to be known transfer/ATA operations;
  // custom programs, delegate/authority changes and token-hook calls stay unknown.
  const passiveToken = !event && !meta.err && index !== 0
    && tx.transaction.message.accountKeys[index].writable === false
    && tx.transaction.message.accountKeys[index].signer === false
    && meta.preBalances[index] === meta.postBalances[index]
    && Object.values(tokenDeltas).some(v=>v>0n) && Object.values(tokenDeltas).every(v=>v>=0n)
    && instructions.length>0 && instructions.every(i=>{
      const id=i.programId?.toString(), type=i.parsed?.type;
      return id==='ComputeBudget111111111111111111111111111111'
        || id==='11111111111111111111111111111111' && type==='createAccount'
        || id==='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL' && ['create','createIdempotent'].includes(type)
        || TOKEN_PROGRAMS.includes(id) && ['transfer','transferChecked','getAccountDataSize','initializeImmutableOwner','initializeAccount','initializeAccount2','initializeAccount3'].includes(type);
    });
  const maintenance=!event ? (rentMaintenance(tx,wallet) || pumpMaintenance(tx,wallet)) : null;
  return {schema_version:11,event_position:event?.position,signature, wallet, slot: tx.slot, block_time: tx.blockTime, observed_at: now(), failed: !!meta.err,
    wallet_delta_lamports: meta.postBalances[index]-meta.preBalances[index], fee_lamports: index === 0 ? meta.fee : 0,
    token_deltas_raw: Object.fromEntries(Object.entries(tokenDeltas).map(([m,a]) => [m,a.toString()])),
    token_pre_balances_raw: Object.fromEntries(Object.entries(tokenPre).map(([m,a]) => [m,a.toString()])),
    token_post_balances_raw: Object.fromEntries(Object.entries(tokenPost).map(([m,a]) => [m,a.toString()])),
    external_flow_lamports: simpleTransfer ? external : maintenance ? 0 : null,
    rent_maintenance: maintenance,
    token_rent_evidence: tokenRentEvidence(tx,wallet),
    position_account_closed: !meta.err && !!event?.position && keys.includes(event.position) && meta.preBalances[keys.indexOf(event.position)]>0 && meta.postBalances[keys.indexOf(event.position)]===0,
    classification: event ? 'recorded_bot' : simpleTransfer ? 'external_transfer' : passiveNFT ? 'passive_nft_outside_scope' : passiveToken ? 'external_token_inflow' : maintenance ? 'rent_maintenance' : meta.err ? 'failed' : 'unclassified',
    refundable_rent_locked_lamports: rentLocked, nonrefundable_account_cost_lamports: permanentRent,
    basis: 'finalized_transaction_balances'};
}
async function collectRentHistory({dir, wallet, PublicKey, rpc, cache}) {
  const file=path.join(dir,'dlmm_rent_history.jsonl');
  const previous=new Map(read(file).map(r=>[`${r.refund_signature}:${r.account}`,r]));
  const candidates=[];
  for (const refund of cache.values()) {
    if (refund.wallet!==wallet || refund.failed || refund.landed===false) continue;
    for (const item of refund.token_rent_evidence?.refunded || []) {
      const prior=previous.get(`${refund.signature}:${item.account}`);
      if (prior?.complete) continue;
      const funded=[...cache.values()].filter(f=>f.wallet===wallet && !f.failed && f.landed!==false
        && Number.isSafeInteger(f.slot) && f.slot<refund.slot
        && f.token_rent_evidence?.funded?.some(a=>a.account===item.account
          && a.mint===item.mint && a.lamports===item.lamports));
      if (!funded.length) continue; // No historical refetch or invented origin.
      candidates.push({refund,item,funded,attempted_at:prior?.observed_at || 0});
    }
  }
  // One account-history request per collector cycle; oldest attempt first so
  // one unresolved account cannot starve newer refunds. No transaction fetches.
  candidates.sort((a,b)=>a.attempted_at-b.attempted_at);
  if (!candidates.length) return;
  const {refund,item,funded}=candidates[0];
  const result={version:1,wallet,account:item.account,mint:item.mint,lamports:item.lamports,
    refund_signature:refund.signature,complete:false,history_signatures:[],
    basis:'finalized_account_signature_history; root_ownership_not_yet_attributed'};
  try {
    const history=await rpc(c=>c.getSignaturesForAddress(new PublicKey(item.account),
      {before:refund.signature,limit:100},'finalized'));
    const index=history.findIndex(h=>funded.some(f=>f.signature===h.signature));
    if (index<0) result.reason='funding_not_in_bounded_history';
    else {
      const interval=history.slice(0,index+1);
      const origin=funded.find(f=>f.signature===interval[index].signature);
      if (interval.some(h=>!Number.isSafeInteger(h.slot) || h.slot<origin.slot || h.slot>refund.slot
          || !cache.has(h.signature) || cache.get(h.signature).wallet!==wallet
          || cache.get(h.signature).slot!==h.slot || cache.get(h.signature).landed===false
          || !!cache.get(h.signature).failed!==!!h.err)
          || new Set(interval.map(h=>h.signature)).size!==interval.length) {
        result.reason='account_history_facts_incomplete';
      } else {
        result.complete=true;
        result.funding_signature=origin.signature;
        result.history_signatures=interval.map(h=>h.signature);
      }
    }
  } catch { result.reason='account_history_unavailable'; }
  result.observed_at=now();
  append(file,result);
}
async function collect({dir, wallet, PublicKey, rpc, historyOnly=false}) {
  fs.mkdirSync(dir, {recursive:true, mode:0o700});
  const publicKey = new PublicKey(wallet);
  const events = new Map(read(path.join(dir,'dlmm_transactions.jsonl')).map(r => [r.signature,r]));
  const cachePath = path.join(dir,'dlmm_wallet_transactions.jsonl');
  const cache = new Map(read(cachePath).map(r => [r.signature,r]));
  const snapshots = read(path.join(dir,'dlmm_nav.jsonl'));
  const since = snapshots.length ? snapshots[0].started_at : now()-86400;
  const finalizedHeight=await rpc(c=>c.getBlockHeight('finalized'));
  let before, boundary = false, signatures = [];
  // Bounded pagination; coverage is explicitly incomplete if the bound is hit.
  for (let page=0; page<20; page++) {
    const batch = await rpc(c => c.getSignaturesForAddress(publicKey, {before,limit:1000}, 'finalized'));
    signatures.push(...batch.filter(r => r.blockTime == null || r.blockTime >= since));
    if (!batch.length || batch.some(r => r.blockTime != null && r.blockTime < since)) { boundary=true; break; }
    before = batch[batch.length-1].signature;
  }
  const currentFact=r=>{const f=cache.get(r.signature); return f?.wallet===wallet && f?.schema_version>=2
    && (f.schema_version>=11 || f.classification!=='unclassified')
    && (f.schema_version>=7 || f.classification!=='recorded_bot')
    && (!(events.get(r.signature)?.kind==='swap' && !events.get(r.signature)?.position) || f.token_pre_balances_raw!=null)
    && f.event_position===events.get(r.signature)?.position;};
  let fetched = 0;
  for (const r of signatures) {
    if (currentFact(r)) continue;
    if (fetched++ >= 60) break; // Each invocation resumes from the durable cache.
    try {
      const tx = await rpc(c => parsedAccountingTransaction(c,r.signature));
      if (!tx?.meta) continue; // Successful null response: await indexing, not RPC failover.
      const fact = transactionFact(tx,wallet,r.signature,events.get(r.signature));
      append(cachePath,fact); cache.set(r.signature,fact);
    } catch { /* Missing evidence remains missing; retry on the next run. */ }
  }
  const coverageSlot=await rpc(c=>c.getSlot('finalized'));
  const historyHead=await rpc(c=>c.getSignaturesForAddress(publicKey,{limit:1},'finalized'));
  const missing=signatures.filter(r=>!currentFact(r)).length;
  const coverage={ts:now(),coverage_since:since,end_slot:coverageSlot,
    wallet_history_complete:boundary && missing===0 && historyHead[0]?.signature===signatures[0]?.signature,
    missing_transactions:missing,
    unclassified_transactions:[...cache.values()].filter(r=>r.block_time>=since && !events.has(r.signature) && r.classification==='unclassified').map(r=>r.signature)};
  // A signed submission is not a landed transaction. Require complete finalized
  // wallet history, expired blockhash, and a history-enabled null status together.
  if (coverage.wallet_history_complete) {
    const height=finalizedHeight;
    const present=new Set(signatures.map(r=>r.signature));
    const absent=[...events.values()].filter(e=>e.wallet===wallet && !present.has(e.signature) && !cache.has(e.signature)
      && e.ts>=since && now()-e.ts>120 && Number.isSafeInteger(e.lastValidBlockHeight) && height>e.lastValidBlockHeight).slice(0,60);
    if (absent.length) {
      const statuses=await rpc(c=>c.getSignatureStatuses(absent.map(e=>e.signature),{searchTransactionHistory:true}));
      if (statuses.value.length===absent.length) absent.forEach((e,i)=>{
        if (statuses.value[i]!==null) return;
        const fact={schema_version:3,signature:e.signature,wallet,event_position:e.position,
          observed_at:now(),landed:false,classification:'expired_unlanded',
          last_valid_block_height:e.lastValidBlockHeight,finalized_block_height:height,
          coverage_since:since,end_slot:coverageSlot,basis:'finalized_wallet_history_and_expiry'};
        append(cachePath,fact);cache.set(e.signature,fact);
      });
    }
  }
  append(path.join(dir,'dlmm_wallet_coverage.jsonl'),coverage);
  if (coverage.wallet_history_complete && !coverage.unclassified_transactions.length) {
    await collectRentHistory({dir,wallet,PublicKey,rpc,cache});
  }
  if (historyOnly) return coverage;
  const started = now(), issues = [], tokens = [], positions = [];
  const slot = await rpc(c => c.getSlot('finalized'));
  const balance = await rpc(c => c.getBalance(publicKey,'finalized'));
  let rent = 0, tokenValue = 0, lpValue = 0;
  const allAccounts = [];
  for (const program of TOKEN_PROGRAMS) {
    const accounts = await rpc(c => c.getParsedTokenAccountsByOwner(publicKey,{programId:new PublicKey(program)},'finalized'));
    allAccounts.push(...accounts.value);
  }
  const mints = [...new Set([SOL,...allAccounts.map(a=>a.account.data.parsed.info.mint)])];
  const marks = new Map();
  for (let i=0;i<mints.length;i+=50) {
    try {
      const assets = await json('https://datapi.jup.ag/v1/assets/search?query='+encodeURIComponent(mints.slice(i,i+50).join(',')));
      for (const a of assets) {
        if (a.usdPrice>0 && Number.isFinite(a.usdPrice) && now()-Date.parse(a.updatedAt)/1000<=600 && a.priceBlockId>=slot-1500) marks.set(a.id,a);
      }
    } catch { /* Fall back to bounded executable quotes; never invent missing prices. */ }
  }
  const helius=process.env.DLMM_HELIUS_WALLET_PRICES === "true"
    ? await heliusPrices(wallet) : {marks:new Map(),status:"disabled"};
  const heliusMark=info=>helius.marks.get(SOL)?.decimals===9 && helius.marks.has(info.mint) && helius.marks.get(info.mint).decimals===info.tokenAmount.decimals;
  // Rotate the bounded quote budget: illiquid early accounts must not starve later ones.
  const cursorPath=path.join(dir,'dlmm_quote_cursor.json');
  let cursor=0;
  try {
    const stored=JSON.parse(fs.readFileSync(cursorPath,'utf8')).offset;
    if(Number.isSafeInteger(stored) && stored>=0) cursor=stored;
  } catch { /* First run or damaged cursor: restart the bounded rotation. */ }
  const quoteMarksPath=path.join(dir,'dlmm_quote_marks.json');
  let quoteMarks={};
  try { quoteMarks=JSON.parse(fs.readFileSync(quoteMarksPath,'utf8')); } catch { /* first run */ }
  const freshQuote=info=>{
    const q=quoteMarks[info.mint];
    return q && q.schema_version===2 && q.in_amount===info.tokenAmount.amount
      && typeof q.out_lamports==='string' && /^[0-9]+$/.test(q.out_lamports)
      && Number.isFinite(Number(q.out_lamports)) && Number(q.out_lamports)>0
      && Number.isSafeInteger(q.observed_at) && q.observed_at<=now() && now()-q.observed_at<=600
      && Number.isSafeInteger(q.slot) && q.slot>0 && Math.abs(slot-q.slot)<=1500;
  };
  const missingAccounts=allAccounts.filter(a=>{
    const i=a.account.data.parsed.info;
    return BigInt(i.tokenAmount.amount)>0n && i.mint!==SOL && !(marks.has(i.mint)&&marks.has(SOL)) && !heliusMark(i) && !freshQuote(i);
  });
  const selected=new Set();
  for(let i=0;i<Math.min(10,missingAccounts.length);i++) selected.add(missingAccounts[(cursor+i)%missingAccounts.length]);
  let quoteDeferredReason=null, quoteAttempts=0;
  // Process the selected rotation in order, including across the list boundary.
  for (const account of [...selected,...allAccounts.filter(a=>!selected.has(a))]) {
      const info=account.account.data.parsed.info, raw=info.tokenAmount.amount, mint=info.mint;
      // Include recoverable ATA reserves, but never count wrapped principal twice.
      rent += account.account.lamports-(mint===SOL ? Number(raw) : 0);
      if (BigInt(raw)===0n) continue;
      let value = null, basis="spot_mark", markError=null, priceObservedAt=null, priceContextSlot=null, freshness="timestamp_and_slot_checked";
      try {
        if (mint===SOL) { value=Number(raw)/1e9; freshness="finalized_balance"; }
        else if (marks.has(mint) && marks.has(SOL)) {
          value=Number(raw)/10**info.tokenAmount.decimals*marks.get(mint).usdPrice/marks.get(SOL).usdPrice;
        } else if (heliusMark(info)) {
          const mark=helius.marks.get(mint);
          value=Number(raw)/10**info.tokenAmount.decimals*mark.usdPrice/helius.marks.get(SOL).usdPrice;
          basis='helius_wallet_estimate'; freshness='provider_timestamp_unavailable'; priceObservedAt=mark.observed_at;
          issues.push(`undated_helius_price:${mint}`);
        } else if (freshQuote(info)) {
          const mark=quoteMarks[mint];
          value=Number(mark.out_lamports)/1e9;
          basis='cached_quote'; freshness='quote_cached'; priceObservedAt=mark.observed_at; priceContextSlot=mark.slot;
        } else {
          if (quoteDeferredReason) throw new Error(quoteDeferredReason);
          if (!selected.has(account)) throw new Error('quote_budget_deferred');
          quoteAttempts++;
          const q=await json(`https://api.jup.ag/swap/v1/quote?inputMint=${mint}&outputMint=${SOL}&amount=${raw}&slippageBps=100`,1,2500,(started+90)*1000);
          const mark=navQuoteMark(q,mint,raw,slot);
          value=Number(mark.out_lamports)/1e9; basis="full_balance_quote"; freshness="quote_context_slot_checked";
          priceObservedAt=mark.observed_at; priceContextSlot=mark.slot;
          // Full-balance quotes only apply to the same amount; liquidity impact is nonlinear.
          quoteMarks[mint]=mark;
        }
        if (!Number.isFinite(value) || value<0) throw new Error('Invalid mark');
      } catch (err) {
        value=null; freshness="unavailable"; markError=err.message;
        if (err.message==='HTTP 429') quoteDeferredReason='quote_rate_limit_deferred';
        if (err.message==='quote_budget_deferred') quoteDeferredReason=err.message;
        issues.push(`unpriced_token:${mint}`);
      }
      tokens.push({mint,raw,mark_sol:value,basis,mark_error:markError,price_freshness:freshness,price_observed_at:priceObservedAt,price_context_slot:priceContextSlot,observed_at:now()});
      if (value!==null) tokenValue+=value;
  }
  fs.writeFileSync(cursorPath,JSON.stringify({offset:missingAccounts.length ? (cursor+quoteAttempts)%missingAccounts.length : 0}),{mode:0o600});
  fs.writeFileSync(quoteMarksPath,JSON.stringify(quoteMarks),{mode:0o600});
  let apiPositions=0;
  for (let page=1; page<=100; page++) {
    const data=await json(`https://dlmm.datapi.meteora.ag/portfolio/open?user=${wallet}&page=${page}&pageSize=50`);
    apiPositions=Number(data.totalPositions);
    for (const pool of data.pools || []) {
      const value=Number(pool.balancesSol), fees=Number(pool.unclaimedFeesSol);
      if (pool.balancesSol==null || pool.unclaimedFeesSol==null || !Number.isFinite(value+fees) || value<0 || fees<0 || pool.updatedAt==null || !Number.isFinite(Number(pool.updatedAt)) || Number(pool.updatedAt)>now()+5 || now()-Number(pool.updatedAt)>180) issues.push(`stale_or_invalid_lp:${pool.poolAddress}`);
      else lpValue+=value+fees;
      for (const position of pool.listPositions || []) {
        const account=await rpc(c => c.getAccountInfo(new PublicKey(position),'finalized'));
        if (!account) issues.push(`position_index_mismatch:${position}`);
        else rent+=account.lamports;
        positions.push({position,pool:pool.poolAddress,mark_sol:(pool.listPositions.length===1 ? value+fees : null)});
      }
    }
    if (!data.hasNext) break;
    if (page===100) issues.push('lp_pagination_incomplete');
  }
  if (apiPositions!==positions.length) issues.push('lp_count_mismatch');
  const endSlot=await rpc(c=>c.getSlot('finalized'));
  // A trade during the multi-source snapshot invalidates its combined mark.
  const head=await rpc(c=>c.getSignaturesForAddress(publicKey,{limit:1},'finalized'));
  if (head[0]?.slot>slot || now()-started>120) issues.push('snapshot_changed_or_slow');
  const snapshot={ts:now(),started_at:started,wallet,slot,end_slot:endSlot,coverage_since:since,
    wallet_history_complete:coverage.wallet_history_complete,missing_transactions:missing,
    asset_scope:'native_SOL_SPL_Meteora_LP_and_reserves; NFTs_excluded',
    native_sol:balance/1e9,spl_mark_sol:tokenValue,lp_mark_sol:lpValue,refundable_rent_sol:rent/1e9,
    known_asset_subtotal_sol:balance/1e9+tokenValue+lpValue+rent/1e9,
    nav_sol:issues.length ? null : balance/1e9+tokenValue+lpValue+rent/1e9,
    tokens,positions,issues,price_sources:{helius_wallet:helius.status},
    basis:'native_plus_Jupiter_SPL_marks_or_quotes_and_Helius_estimates_plus_Meteora_LP_marks_plus_refundable_rent',
    external_flow_lamports: [...cache.values()].filter(r=>r.block_time>=since).reduce((sum,r)=>sum+(r.external_flow_lamports || 0),0),
    unclassified_transactions:[...cache.values()].filter(r=>r.block_time>=since && !events.has(r.signature) && r.classification==='unclassified').map(r=>r.signature)};
  append(path.join(dir,'dlmm_nav.jsonl'),snapshot);
  return {nav_sol:snapshot.nav_sol,issues,missing_transactions:missing,wallet_history_complete:snapshot.wallet_history_complete};
}
module.exports={collect,transactionFact,heliusPrices,collectRentHistory,parsedAccountingTransaction,navQuoteMark};
