// Read-only wallet coverage and marked NAV. No signing or transaction submission.
const fs = require('fs');
const path = require('path');
const SOL = 'So11111111111111111111111111111111111111112';
const TOKEN_PROGRAMS = ['TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA', 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'];
const read = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : [];
const append = (file, row) => fs.appendFileSync(file, JSON.stringify(row) + '\n', {mode: 0o600});
const now = () => Math.floor(Date.now()/1000);
async function json(url, attempts=3, timeout=12000) {
  for (let attempt=0; attempt<attempts; attempt++) {
    if (url.includes("/quote?")) await new Promise(resolve=>setTimeout(resolve,1100));
    const response = await fetch(url, {headers: {'User-Agent': 'curl/8.5.0'}, signal: AbortSignal.timeout(timeout)});
    if (response.status===429 && attempt<attempts-1) { await new Promise(resolve=>setTimeout(resolve,1000*(attempt+1))); continue; }
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
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

function transactionFact(tx, wallet, signature, event) {
  const keys = tx.transaction.message.accountKeys.map(k => k.pubkey.toString());
  const index = keys.indexOf(wallet), meta = tx.meta;
  if (index < 0 || !meta || ![meta.preBalances[index], meta.postBalances[index], meta.fee].every(Number.isSafeInteger)) throw new Error('Invalid wallet balances');
  const tokenDeltas = {}, tokenAccounts = new Set();
  for (const [rows, sign] of [[meta.preTokenBalances, -1n], [meta.postTokenBalances, 1n]]) {
    for (const r of rows || []) if (r.owner === wallet) {
      tokenDeltas[r.mint] = (tokenDeltas[r.mint] || 0n) + sign*BigInt(r.uiTokenAmount.amount);
      tokenAccounts.add(keys[r.accountIndex]);
    }
  }
  const instructions = [...tx.transaction.message.instructions, ...(meta.innerInstructions || []).flatMap(i => i.instructions)];
  let external = 0, rentLocked = 0, permanentRent = 0;
  const simpleTransfer = !event && !meta.err && instructions.every(i => i.program === 'system' && i.parsed?.type === 'transfer' || i.programId?.toString() === 'ComputeBudget111111111111111111111111111111');
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
  // Passive NFT activity is outside the SOL/SPL/LP accounting scope.
  const passiveNFT = !event && !meta.err && tx.transaction.message.accountKeys[index].writable === false
    && tx.transaction.message.accountKeys[index].signer === false
    && meta.preBalances[index] === meta.postBalances[index] && tokenAccounts.size === 0
    && tx.transaction.message.instructions.length > 0
    && tx.transaction.message.instructions.every(i => i.programId?.toString() === 'BGUMAp9Gq7iTEuizy4pqaxsTyUCBK68MDfK752saRPUY');
  return {schema_version:3,event_position:event?.position,signature, wallet, slot: tx.slot, block_time: tx.blockTime, observed_at: now(), failed: !!meta.err,
    wallet_delta_lamports: meta.postBalances[index]-meta.preBalances[index], fee_lamports: index === 0 ? meta.fee : 0,
    token_deltas_raw: Object.fromEntries(Object.entries(tokenDeltas).map(([m,a]) => [m,a.toString()])),
    external_flow_lamports: simpleTransfer ? external : null,
    position_account_closed: !meta.err && !!event?.position && keys.includes(event.position) && meta.preBalances[keys.indexOf(event.position)]>0 && meta.postBalances[keys.indexOf(event.position)]===0,
    classification: event ? 'recorded_bot' : simpleTransfer ? 'external_transfer' : passiveNFT ? 'passive_nft_outside_scope' : meta.err ? 'failed' : 'unclassified',
    refundable_rent_locked_lamports: rentLocked, nonrefundable_account_cost_lamports: permanentRent,
    basis: 'finalized_transaction_balances'};
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
    && (f.schema_version>=3 || f.classification!=='unclassified')
    && f.event_position===events.get(r.signature)?.position;};
  let fetched = 0;
  for (const r of signatures) {
    if (currentFact(r)) continue;
    if (fetched++ >= 60) break; // Each invocation resumes from the durable cache.
    try {
      const tx = await rpc(c => c.getParsedTransaction(r.signature,{commitment:'finalized',maxSupportedTransactionVersion:0}));
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
  const helius=await heliusPrices(wallet);
  const heliusMark=info=>helius.marks.get(SOL)?.decimals===9 && helius.marks.has(info.mint) && helius.marks.get(info.mint).decimals===info.tokenAmount.decimals;
  // Rotate the bounded quote budget: illiquid early accounts must not starve later ones.
  const cursorPath=path.join(dir,'dlmm_quote_cursor.json');
  const cursor=fs.existsSync(cursorPath) ? JSON.parse(fs.readFileSync(cursorPath,'utf8')).offset : 0;
  const missingAccounts=allAccounts.filter(a=>{
    const i=a.account.data.parsed.info;
    return BigInt(i.tokenAmount.amount)>0n && i.mint!==SOL && !(marks.has(i.mint)&&marks.has(SOL)) && !heliusMark(i);
  });
  const selected=new Set();
  for(let i=0;i<Math.min(10,missingAccounts.length);i++) selected.add(missingAccounts[(cursor+i)%missingAccounts.length]);
  fs.writeFileSync(cursorPath,JSON.stringify({offset:missingAccounts.length ? (cursor+selected.size)%missingAccounts.length : 0}),{mode:0o600});
  let quoteRateLimited=false;
  for (const account of allAccounts) {
      const info=account.account.data.parsed.info, raw=info.tokenAmount.amount, mint=info.mint;
      // Include recoverable ATA reserves, but never count wrapped principal twice.
      rent += account.account.lamports-(mint===SOL ? Number(raw) : 0);
      if (BigInt(raw)===0n) continue;
      let value = null, basis="spot_mark", markError=null, priceObservedAt=null, freshness="timestamp_and_slot_checked";
      try {
        if (mint===SOL) { value=Number(raw)/1e9; freshness="finalized_balance"; }
        else if (marks.has(mint) && marks.has(SOL)) {
          value=Number(raw)/10**info.tokenAmount.decimals*marks.get(mint).usdPrice/marks.get(SOL).usdPrice;
        } else if (heliusMark(info)) {
          const mark=helius.marks.get(mint);
          value=Number(raw)/10**info.tokenAmount.decimals*mark.usdPrice/helius.marks.get(SOL).usdPrice;
          basis='helius_wallet_estimate'; freshness='provider_timestamp_unavailable'; priceObservedAt=mark.observed_at;
          issues.push(`undated_helius_price:${mint}`);
        } else {
          if (quoteRateLimited) throw new Error('quote_rate_limit_deferred');
          if (!selected.has(account)) throw new Error('quote_budget_deferred');
          const q=await json(`https://api.jup.ag/swap/v1/quote?inputMint=${mint}&outputMint=${SOL}&amount=${raw}&slippageBps=100`,1,2500);
          if (q.inAmount!==raw || !q.outAmount) throw new Error('Quote mismatch');
          value=Number(q.outAmount)/1e9; basis="full_balance_quote"; freshness="quote_received_now";
        }
        if (!Number.isFinite(value) || value<0) throw new Error('Invalid mark');
      } catch (err) { value=null; freshness="unavailable"; markError=err.message; if (err.message==='HTTP 429') quoteRateLimited=true; issues.push(`unpriced_token:${mint}`); }
      tokens.push({mint,raw,mark_sol:value,basis,mark_error:markError,price_freshness:freshness,price_observed_at:priceObservedAt,observed_at:now()});
      if (value!==null) tokenValue+=value;
  }
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
module.exports={collect,transactionFact,heliusPrices};
