const assert=require('node:assert/strict'), fs=require('node:fs'), os=require('node:os'), path=require('node:path');
const {collect,transactionFact,heliusPrices,parsedAccountingTransaction,navQuoteMark}=require('./dlmm_nav.js');
const wallet='wallet',key=s=>({toString:()=>s});
const tx={slot:100,blockTime:Math.floor(Date.now()/1000),transaction:{message:{accountKeys:[{pubkey:key(wallet)},{pubkey:key('outside')}],instructions:[{program:'system',parsed:{type:'transfer',info:{source:wallet,destination:'outside',lamports:100}}}]}},meta:{err:null,fee:5,preBalances:[1000,0],postBalances:[895,100],preTokenBalances:[],postTokenBalances:[]}};
const fact=transactionFact(tx,wallet,'sig');
assert.equal(fact.wallet_delta_lamports,-105);assert.equal(fact.external_flow_lamports,-100);assert.equal(fact.fee_lamports,5);
assert.equal(transactionFact(tx,wallet,'sig',{position:'position'}).external_flow_lamports,null);
// Memo text never changes the economic classification of a proven SOL transfer.
const memoTransfer={...tx,transaction:{message:{...tx.transaction.message,
 instructions:[...tx.transaction.message.instructions,{programId:key('MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'),parsed:'untrusted memo'}]}}};
assert.equal(transactionFact(memoTransfer,wallet,'memo').external_flow_lamports,-100);
assert.equal(transactionFact(memoTransfer,'outside','incoming').external_flow_lamports,100);
const mismatch={...memoTransfer,meta:{...tx.meta,postBalances:[894,100]}};
assert.equal(transactionFact(mismatch,wallet,'mismatch').classification,'unclassified');
const custom={...memoTransfer,transaction:{message:{...memoTransfer.transaction.message,
 instructions:[...memoTransfer.transaction.message.instructions,{programId:key('custom')} ]}}};
assert.equal(transactionFact(custom,wallet,'custom').classification,'unclassified');
assert.equal(transactionFact({...memoTransfer,meta:{...tx.meta,err:'failed'}},wallet,'failed-memo').external_flow_lamports,null);

// Exact token-account funding and pure reclaim proof, without treating rent as income.
const rentToken='TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb';
const fundedToken={slot:100,blockTime:100,transaction:{message:{accountKeys:[{pubkey:wallet,signer:true},{pubkey:'ata'}],
 instructions:[{program:'system',parsed:{type:'createAccount',info:{source:wallet,newAccount:'ata',owner:rentToken,lamports:200}}}]}},
 meta:{err:null,fee:5,preBalances:[1000,0],postBalances:[795,200],preTokenBalances:[],
 postTokenBalances:[{accountIndex:1,owner:wallet,mint:'mint',uiTokenAmount:{amount:'10'}}]}};
assert.deepEqual(transactionFact(fundedToken,wallet,'fund').token_rent_evidence,
 {version:1,funded:[{account:'ata',mint:'mint',lamports:200}],refunded:[]});
for(const alter of [t=>{t.meta.err='failed'},t=>{t.transaction.message.instructions[0].parsed.info.source='other'},
 t=>{t.meta.postBalances[1]=201},t=>{t.meta.postTokenBalances[0].mint='So11111111111111111111111111111111111111112'}]){
 const t=JSON.parse(JSON.stringify(fundedToken));alter(t);assert.deepEqual(transactionFact(t,wallet,'unproved').token_rent_evidence.funded,[]);
}
const reclaimedToken=JSON.parse(JSON.stringify(fundedToken));
reclaimedToken.transaction.message.instructions=[{programId:rentToken,parsed:{type:'closeAccount',info:{account:'ata',owner:wallet,destination:wallet}}}];
Object.assign(reclaimedToken.meta,{preBalances:[1000,200],postBalances:[1195,0],preTokenBalances:[{accountIndex:1,owner:wallet,mint:'mint',uiTokenAmount:{amount:'0'}}],postTokenBalances:[]});
assert.deepEqual(transactionFact(reclaimedToken,wallet,'refund').token_rent_evidence,
 {version:1,funded:[],refunded:[{account:'ata',mint:'mint',lamports:200}]});
for(const alter of [t=>{t.meta.err='failed'},t=>{t.meta.postBalances[0]--},
 t=>{t.meta.preTokenBalances[0].uiTokenAmount.amount='1'},
 t=>{t.transaction.message.instructions[0].parsed.info.destination='other'},
 t=>{t.transaction.message.instructions.push({programId:'unknown'})},
 t=>{t.transaction.message.instructions.push(t.transaction.message.instructions[0])}]){
 const t=JSON.parse(JSON.stringify(reclaimedToken));alter(t);assert.deepEqual(transactionFact(t,wallet,'unproved').token_rent_evidence.refunded,[]);
}

const closed={...tx,meta:{...tx.meta,preBalances:[1000,100],postBalances:[1095,0]}};
assert.equal(transactionFact(closed,wallet,'closed',{position:'outside'}).position_account_closed,true);
assert.equal(transactionFact(tx,wallet,'open',{position:'outside'}).position_account_closed,false);
const failed=JSON.parse(JSON.stringify(tx));failed.transaction.message.accountKeys=tx.transaction.message.accountKeys;failed.meta.err={InstructionError:[0,'failed']};failed.meta.postBalances=[995,0];
assert.equal(transactionFact(failed,wallet,'fail').fee_lamports,5);
assert.equal(transactionFact(failed,wallet,'fail').external_flow_lamports,null);
const passive={...tx,transaction:{message:{accountKeys:[{pubkey:key('payer')},{pubkey:key(wallet),writable:false,signer:false}],instructions:[{programId:key('BGUMAp9Gq7iTEuizy4pqaxsTyUCBK68MDfK752saRPUY')}]}},meta:{...tx.meta,preBalances:[1000,10],postBalances:[995,10]}};
assert.equal(transactionFact(passive,wallet,'nft').classification,'passive_nft_outside_scope');
passive.transaction.message.accountKeys[1].writable=true;
assert.equal(transactionFact(passive,wallet,'nft').classification,'unclassified');
const gift={slot:150,blockTime:150,transaction:{message:{accountKeys:[{pubkey:'payer'}, {pubkey:wallet,writable:false,signer:false},{pubkey:'ata'}],instructions:[{programId:'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',parsed:{type:'transfer'}}]}},meta:{err:null,fee:5,preBalances:[3000000,10,0],postBalances:[960715,10,2039280],preTokenBalances:[],postTokenBalances:[{owner:wallet,mint:'gift',accountIndex:2,uiTokenAmount:{amount:'10000000000'}}]}};
assert.equal(transactionFact(gift,wallet,'gift').classification,'external_token_inflow');
assert.equal(transactionFact(gift,wallet,'gift').external_flow_lamports,null);
assert.deepEqual(transactionFact(gift,wallet,'gift').token_pre_balances_raw,{});
assert.deepEqual(transactionFact(gift,wallet,'gift').token_post_balances_raw,{gift:'10000000000'});
assert.equal(transactionFact(gift,wallet,'gift',{position:'p'}).classification,'recorded_bot');
for(const alter of [
  t=>{t.transaction.message.accountKeys[1].signer=true},
  t=>{t.meta.postBalances[1]=9},
  t=>{t.transaction.message.instructions[0].parsed.type='approve'},
  t=>{t.meta.innerInstructions=[{instructions:[{programId:'unknown-hook'}]}]},
  t=>{t.meta.preTokenBalances=[{owner:wallet,mint:'sold',accountIndex:2,uiTokenAmount:{amount:'1'}}]},
]){const t=JSON.parse(JSON.stringify(gift));alter(t);assert.equal(transactionFact(t,wallet,'unknown').classification,'unclassified');}
// Recorded wrapper transaction shape: return empty account rent, pay its
// explicit service fee and network fee. This is internal capital, not income.
const wrapper='CLEANALo6FtS6quqTTEXDGFFTuSKMkeKGgcweeiPRJzK';
const cleaning={slot:200,blockTime:200,transaction:{message:{accountKeys:[
 {pubkey:wallet,signer:true},{pubkey:'empty-account'},{pubkey:'service'}],
 instructions:[{programId:wrapper}]}},meta:{err:null,fee:5,
 preBalances:[1000,200,0],postBalances:[1193,0,2],
 preTokenBalances:[{accountIndex:1,owner:wallet,mint:'empty-mint',uiTokenAmount:{amount:'0'}}],postTokenBalances:[],
 innerInstructions:[{index:0,instructions:[
 {programId:'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',parsed:{type:'closeAccount',info:{account:'empty-account',owner:wallet,destination:wallet}}},
 {programId:'11111111111111111111111111111111',parsed:{type:'transfer',info:{source:wallet,destination:'service',lamports:2}}}]}]}};
const maintenance=transactionFact(cleaning,wallet,'rent');
assert.equal(maintenance.classification,'rent_maintenance');
assert.equal(maintenance.external_flow_lamports,0);
assert.equal(maintenance.wallet_delta_lamports,193);
assert.deepEqual(maintenance.rent_maintenance,{released_lamports:200,service_fee_lamports:2});
for(const alter of [
 t=>{t.meta.preTokenBalances[0].uiTokenAmount.amount='1'},
 t=>{t.meta.preTokenBalances[0].mint='So11111111111111111111111111111111111111112'},
 t=>{t.meta.preTokenBalances[0].owner='other'},
 t=>{t.transaction.message.accountKeys[0].signer=false},
 t=>{t.transaction.message.instructions[0].programId='unknown-wrapper'},
 t=>{t.meta.innerInstructions[0].instructions[0].parsed.info.destination='service'},
 t=>{t.meta.innerInstructions[0].instructions[0].parsed.info.owner='other'},
 t=>{t.meta.innerInstructions[0].instructions[1].parsed.info.source='other'},
 t=>{t.meta.innerInstructions[0].instructions.push({programId:'unknown-hook'})},
 t=>{t.meta.innerInstructions[0].index=99},
 t=>{t.meta.postBalances[0]--;t.meta.postBalances[2]++},
 t=>{t.meta.postBalances[1]=1},
 t=>{t.meta.postTokenBalances=t.meta.preTokenBalances},
]){const t=JSON.parse(JSON.stringify(cleaning));alter(t);assert.equal(transactionFact(t,wallet,'unknown').classification,'unclassified');}
// The observed wrapper now splits its fee into two native transfers.
const splitFee=JSON.parse(JSON.stringify(cleaning));
splitFee.meta.innerInstructions[0].instructions.push(JSON.parse(JSON.stringify(splitFee.meta.innerInstructions[0].instructions[1])));
splitFee.meta.postBalances[0]-=2;splitFee.meta.postBalances[2]+=2;
assert.deepEqual(transactionFact(splitFee,wallet,'split').rent_maintenance,{released_lamports:200,service_fee_lamports:4});
for(const alter of [
 t=>{t.meta.innerInstructions[0].instructions[2].parsed.info.source='other'},
 t=>{t.meta.innerInstructions[0].instructions[2].parsed.info.lamports=-1},
 t=>{t.meta.innerInstructions[0].instructions[2].programId='unknown'},
 t=>{t.meta.postBalances[0]++},
]){const t=JSON.parse(JSON.stringify(splitFee));alter(t);assert.equal(transactionFact(t,wallet,'bad-split').classification,'unclassified');}
const pumpCleaning=require('./test_pump_maintenance.json');
const pumpWallet=pumpCleaning.transaction.message.accountKeys[0].pubkey;
const pumpFact=transactionFact(pumpCleaning,pumpWallet,'pump-maintenance');
assert.equal(pumpFact.classification,'rent_maintenance');
assert.equal(pumpFact.external_flow_lamports,0);
assert.deepEqual(pumpFact.rent_maintenance,{released_lamports:1346200,service_fee_lamports:27526,cashback_lamports:120535});
assert.equal(pumpFact.wallet_delta_lamports,1428913);
// web3 getParsedTransaction returns PublicKey objects for unparsed accounts.
const sdkPump=JSON.parse(JSON.stringify(pumpCleaning));
for(const group of sdkPump.meta.innerInstructions) for(const i of group.instructions) {
  if(i.accounts)i.accounts=i.accounts.map(value=>({toString:()=>value}));
  const id=i.programId;i.programId={toString:()=>id};
}
for(const i of sdkPump.transaction.message.instructions) {
  const id=i.programId;i.programId={toString:()=>id};
}
for(const k of sdkPump.transaction.message.accountKeys) {const value=k.pubkey;k.pubkey={toString:()=>value};}
assert.deepEqual(transactionFact(sdkPump,pumpWallet,'sdk-pump').rent_maintenance,pumpFact.rent_maintenance);

for(const alter of [
 t=>{t.meta.innerInstructions[0].instructions[5].data='unknown'},
 t=>{t.meta.innerInstructions[0].instructions[9].accounts[0]='other'},
 t=>{t.meta.innerInstructions[0].instructions[6].parsed.info.source=pumpWallet},
 t=>{t.meta.innerInstructions[0].instructions[6].parsed.info.tokenAmount.amount='120536'},
 t=>{t.meta.innerInstructions[0].instructions[12].parsed.info.source='other'},
 t=>{t.meta.innerInstructions[0].instructions[8].parsed.info.destination='other'},
 t=>{t.meta.innerInstructions[0].instructions.push({programId:'unknown'})},
 t=>{t.meta.preTokenBalances=[{accountIndex:0,owner:pumpWallet,mint:'token',uiTokenAmount:{amount:'1'}}]},
 t=>{t.meta.postBalances[0]++},
 t=>{t.meta.err={failed:true}},
]){const t=JSON.parse(JSON.stringify(pumpCleaning));alter(t);assert.equal(transactionFact(t,pumpWallet,'bad-pump').rent_maintenance,null);}
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nav-check-'));
let unknown=false, height=101, signatureStatus=null;
const connection={
 getSignaturesForAddress:async(_,options)=>options.before ? [] : [{signature:'sig',slot:100,blockTime:tx.blockTime}],
 getBlockHeight:async()=>height,getSignatureStatuses:async signatures=>({value:signatures.map(()=>signatureStatus)}),
 getParsedTransaction:async()=>tx,getSlot:async()=>101,getBalance:async()=>1000000000,
 getParsedTokenAccountsByOwner:async(_,options)=>({value:options.programId.toString().startsWith('Tokenkeg') ? [{account:{lamports:1002039280,data:{parsed:{info:{mint:unknown?'unknown':'So11111111111111111111111111111111111111112',tokenAmount:{amount:'1000000000'}}}}}}]:[]}),
};
global.fetch=async url=>{if(url.includes('/quote?'))throw new Error('no route');return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})}};
(async()=>{
 const payer='11111111111111111111111111111111', receiver='So11111111111111111111111111111111111111112';
 const v1={version:1,slot:100,blockTime:100,transaction:{signatures:['v1sig'],message:{
   accountKeys:[{pubkey:payer,signer:true,writable:true},{pubkey:receiver,signer:false,writable:true}],
   instructions:[{program:'system',programId:payer,parsed:{type:'transfer',info:{source:payer,destination:receiver,lamports:1}}}]}},
   meta:{err:null,fee:5,preBalances:[100,0],postBalances:[94,1],preTokenBalances:[],postTokenBalances:[],innerInstructions:[]}};
 let reply={result:v1}, rawCalls=0;
 const v1rpc={getParsedTransaction:async()=>{throw Object.assign(new Error('Transaction version (1) is not supported'),{code:-32015});},
   _rpcRequest:async(method,params)=>{rawCalls++;assert.equal(method,'getTransaction');assert.equal(params[1].maxSupportedTransactionVersion,1);assert.equal(params[1].commitment,'finalized');return reply;}};
 const parsed=await parsedAccountingTransaction(v1rpc,'v1sig');
 assert.equal(transactionFact(parsed,receiver,'v1sig').external_flow_lamports,1);
 assert.equal(transactionFact(parsed,receiver,'v1sig').fee_lamports,0);
 for(const mutate of [t=>t.version=2,t=>t.transaction.signatures[0]='wrong',t=>t.meta.preBalances.pop(),
   t=>t.meta.postBalances[1]=Number.MAX_SAFE_INTEGER+1,t=>delete t.meta.preTokenBalances,
   t=>t.meta.preTokenBalances.push({accountIndex:99}),t=>t.meta.innerInstructions=[{index:4,instructions:[]}],
   t=>delete t.transaction.message.instructions[0].programId]) {
   reply={result:JSON.parse(JSON.stringify(v1))};mutate(reply.result);
   await assert.rejects(parsedAccountingTransaction(v1rpc,'v1sig'),/Invalid version 1/);
 }
 reply={result:null};assert.equal(await parsedAccountingTransaction(v1rpc,'v1sig'),null);
 reply={error:{code:-32000}};await assert.rejects(parsedAccountingTransaction(v1rpc,'v1sig'),/RPC error/);
 const before=rawCalls;
 assert.equal(await parsedAccountingTransaction({...v1rpc,getParsedTransaction:async()=>tx},'sig'),tx);
 await assert.rejects(parsedAccountingTransaction({...v1rpc,getParsedTransaction:async()=>{throw new Error('timeout');}},'sig'),/timeout/);
 assert.equal(rawCalls,before);

 const args={dir,wallet,PublicKey:function(s){return key(s)},rpc:fn=>fn(connection)};
 const r=await collect(args);assert.equal(r.nav_sol,2.00203928);assert.equal(r.wallet_history_complete,true);
 unknown=true;const missing=await collect(args);assert.equal(missing.nav_sol,null);assert.equal(missing.issues[0],'unpriced_token:unknown');
 assert.equal(fs.readFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),'utf8').trim().split('\n').length,1);
 // Expiry is not enough: confirmed or potentially live submissions remain unresolved.
 const event={signature:'absent',wallet,position:'p',ts:tx.blockTime-300,lastValidBlockHeight:150};
 fs.writeFileSync(path.join(dir,'dlmm_transactions.jsonl'),JSON.stringify(event)+'\n');
 // Keep the collection boundary earlier than the submission.
 const snap=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').split('\n')[0]);
 snap.started_at=tx.blockTime-1000;fs.writeFileSync(path.join(dir,'dlmm_nav.jsonl'),JSON.stringify(snap)+'\n');
 await collect({...args,historyOnly:true});
 assert.equal(fs.readFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),'utf8').includes('expired_unlanded'),false);
 height=151;signatureStatus={confirmationStatus:'confirmed'};await collect({...args,historyOnly:true});
 assert.equal(fs.readFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),'utf8').includes('expired_unlanded'),false);
 signatureStatus=null;await collect({...args,historyOnly:true});
 const expired=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),'utf8').trim().split('\n').at(-1));
 assert.equal(expired.classification,'expired_unlanded');assert.equal(expired.landed,false);
 // More than ten unpriced accounts rotate; unavailable assets retain null value.
 const quoted=[];
 connection.getParsedTokenAccountsByOwner=async(_,o)=>({value:o.programId.toString().startsWith('Tokenkeg') ? Array.from({length:12},(_,i)=>({account:{lamports:2039280,data:{parsed:{info:{mint:'unknown'+i,tokenAmount:{amount:'1',decimals:9}}}}}})) : []});
 global.fetch=async url=>{if(url.includes('/quote?')){quoted.push(new URL(url).searchParams.get('inputMint'));throw new Error('no route');}return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})}};
 await collect(args);await collect(args);
 assert.equal(new Set(quoted).size,12);
 fs.writeFileSync(path.join(dir,'dlmm_quote_marks.json'),JSON.stringify({unknown0:{schema_version:2,in_amount:'1',out_lamports:'2000000',observed_at:Math.floor(Date.now()/1000),slot:100}}));
 let rateLimitedRequests=0;
 global.fetch=async url=>{if(url.includes('/quote?')){rateLimitedRequests++;return {ok:false,status:429};}return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})}};
 const limited=await collect(args);
 assert.equal(rateLimitedRequests,1);assert.equal(limited.nav_sol,null);
 const latest=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim().split('\n').at(-1));
 assert.ok(latest.tokens.some(t=>t.mark_error==='quote_rate_limit_deferred'));
 assert.equal(latest.tokens.find(t=>t.mint==='unknown0').basis,'cached_quote');
 assert.equal(latest.tokens.find(t=>t.mint==='unknown0').mark_sol,0.002);
 // Reject different balances, future/expired marks, and the old unit-ambiguous schema.
 for (const invalid of [
   {in_amount:'2',out_lamports:'2000000',observed_at:Math.floor(Date.now()/1000)},
   {in_amount:'1',out_lamports:'2000000',observed_at:Math.floor(Date.now()/1000)+60},
   {in_amount:'1',out_lamports:'2000000',observed_at:Math.floor(Date.now()/1000)-601},
   {sol_per_token:2,observed_at:Math.floor(Date.now()/1000)},
 ]) {
   fs.writeFileSync(path.join(dir,'dlmm_quote_marks.json'),JSON.stringify({unknown0:{schema_version:2,...invalid,slot:100}}));
   await collect(args);
   const rejected=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim().split('\n').at(-1));
   assert.equal(rejected.tokens.find(t=>t.mint==='unknown0').mark_sol,null);
 }
 // A six-decimal token must retain the exact SOL quote on the next collection.
 const previousAccounts=connection.getParsedTokenAccountsByOwner;
 connection.getParsedTokenAccountsByOwner=async(_,o)=>({value:o.programId.toString().startsWith('Tokenkeg') ? [{account:{lamports:2039280,data:{parsed:{info:{mint:'six-decimal',tokenAmount:{amount:'1000000',decimals:6}}}}}}] : []});
 let quoteCalls=0;
 global.fetch=async url=>{if(url.includes('/quote?')){quoteCalls++;return {ok:true,json:async()=>({inputMint:'six-decimal',outputMint:'So11111111111111111111111111111111111111112',swapMode:'ExactIn',inAmount:'1000000',outAmount:'2000000',contextSlot:115})};}return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})}};
 await collect(args);await collect(args);
 const cached=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim().split('\n').at(-1));
 assert.equal(quoteCalls,1);assert.equal(cached.tokens[0].basis,'cached_quote');assert.equal(cached.tokens[0].mark_sol,0.002);assert.equal(cached.tokens[0].price_context_slot,115);
 connection.getParsedTokenAccountsByOwner=previousAccounts;
 // Preserve the provider slot, including a processed slot ahead of finalized RPC.
 assert.equal(JSON.parse(fs.readFileSync(path.join(dir,'dlmm_quote_marks.json')))["six-decimal"].slot,115);
 const goodQuote={inputMint:'mint',outputMint:'So11111111111111111111111111111111111111112',inAmount:'1',outAmount:'2000',swapMode:'ExactIn',contextSlot:2000};
 assert.equal(navQuoteMark(goodQuote,'mint','1',2001).slot,2000);
 for(const slot of [undefined,null,0,NaN,2000.5]) assert.throws(()=>navQuoteMark(goodQuote,'mint','1',slot),/quote evidence/);
 for(const bad of [{inputMint:'wrong'},{outputMint:'wrong'},{inAmount:'2'},{swapMode:'ExactOut'},
   {outAmount:'0'},{outAmount:'-1'},{outAmount:'1e6'},{outAmount:2000},
   {contextSlot:undefined},{contextSlot:1},{contextSlot:4001},{contextSlot:2000.5}]){
   assert.throws(()=>navQuoteMark({...goodQuote,...bad},'mint','1',2001),/quote evidence/);
 }
 // A 429 on the first selected account advances only one place, even at wraparound.
 connection.getParsedTokenAccountsByOwner=previousAccounts;
 fs.writeFileSync(path.join(dir,'dlmm_quote_marks.json'),'{}');
 fs.writeFileSync(path.join(dir,'dlmm_quote_cursor.json'),JSON.stringify({offset:11}));
 const attempted=[];
 global.fetch=async url=>{if(url.includes('/quote?')){attempted.push(new URL(url).searchParams.get('inputMint'));return {ok:false,status:429};}return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})}};
 await collect(args);await collect(args);
 assert.deepEqual(attempted,['unknown11','unknown0']);
 assert.equal(JSON.parse(fs.readFileSync(path.join(dir,'dlmm_quote_cursor.json'))).offset,1);
 // Helius paginates, rotates keys, rejects unusable prices and keeps secrets out of URLs.
 const sol='So11111111111111111111111111111111111111112';
 const calls=[];
 global.fetch=async(url,options)=>{
   assert.ok(!url.includes('test-key'));
   const key=options.headers['X-Api-Key'], page=new URL(url).searchParams.get('page');calls.push([key,page]);
   if(key==='test-key-bad')return {ok:false,status:429};
   return {ok:true,json:async()=>({balances:page==='1' ? [{mint:'So11111111111111111111111111111111111111111',decimals:9,pricePerToken:100}] :
     [{mint:'valid',decimals:9,pricePerToken:2},{mint:'zero',decimals:9,pricePerToken:0},{mint:'invalid',decimals:9,pricePerToken:'3'}],pagination:{hasMore:page==='1'}})};
 };
 const h=await heliusPrices(wallet,{HELIUS_API_KEY:'test-key-bad',SOLANA_RPC_URLS:'https://mainnet.helius-rpc.com/?api-key=test-key-good,https://attacker.invalid/?api-key=wrong'});
 assert.equal(h.status,'ok');assert.equal(h.marks.size,2);assert.equal(h.marks.get(sol).usdPrice,100);assert.equal(calls.length,3);
 // Incomplete pagination cannot silently promote partial provider data.
 global.fetch=async(url)=>new URL(url).searchParams.get('page')==='1' ? {ok:true,json:async()=>({balances:[{mint:sol,decimals:9,pricePerToken:100}],pagination:{hasMore:true}})} : {ok:false,status:503};
 assert.equal((await heliusPrices(wallet,{HELIUS_API_KEY:'test-key-good'})).marks.size,0);
 const savedWalletPrices=process.env.DLMM_HELIUS_WALLET_PRICES;
 delete process.env.DLMM_HELIUS_WALLET_PRICES;
 const savedKey=process.env.HELIUS_API_KEY;process.env.HELIUS_API_KEY='test-key-good';
 let quotesWithHelius=0, walletApiCalls=0;
 global.fetch=async(url)=>{
   if(url.includes('api.helius.xyz')){walletApiCalls++;return {ok:true,json:async()=>({balances:[{mint:sol,decimals:9,pricePerToken:100},...Array.from({length:12},(_,i)=>({mint:'unknown'+i,decimals:9,pricePerToken:2,balance:99999999,usdValue:99999999}))],pagination:{hasMore:false}})};}
   if(url.includes('/quote?')){quotesWithHelius++;throw new Error('unexpected quote');}
   return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})};
 };
 await collect(args);
 assert.equal(walletApiCalls,0); // Routine snapshots must not spend Wallet API credits.
 process.env.DLMM_HELIUS_WALLET_PRICES="true"; quotesWithHelius=0;
 const enriched=await collect(args);
 assert.equal(quotesWithHelius,0);assert.equal(enriched.nav_sol,null);
 const enrichedSnapshot=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim().split('\n').at(-1));
 assert.ok(Math.abs(enrichedSnapshot.tokens[0].mark_sol-0.00000000002)<1e-24); // finalized RPC quantity, not provider wallet total
 assert.equal(enrichedSnapshot.tokens[0].basis,'helius_wallet_estimate');
 assert.ok(enriched.issues.every(i=>i.startsWith('undated_helius_price:')));
 const heliusFetch=global.fetch;
 global.fetch=async(url,options)=>url.includes('/assets/search') ? {ok:true,json:async()=>[sol,'unknown0'].map(id=>({id,usdPrice:id===sol?100:3,updatedAt:new Date().toISOString(),priceBlockId:101}))} : heliusFetch(url,options);
 await collect(args);
 const preferred=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim().split('\n').at(-1));
 assert.equal(preferred.tokens[0].basis,'spot_mark');
 assert.ok(Math.abs(preferred.tokens[0].mark_sol-0.00000000003)<1e-24);
 if(savedWalletPrices===undefined)delete process.env.DLMM_HELIUS_WALLET_PRICES;else process.env.DLMM_HELIUS_WALLET_PRICES=savedWalletPrices;
 if(savedKey===undefined)delete process.env.HELIUS_API_KEY;else process.env.HELIUS_API_KEY=savedKey;
 // Upgrade cached unknown facts once, using fresh on-chain observations.
 fs.writeFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),JSON.stringify({signature:'sig',wallet,schema_version:10,classification:'unclassified'})+'\n');
 let refreshed=0;
 connection.getParsedTransaction=async()=>{refreshed++;return {...cleaning,slot:100,blockTime:tx.blockTime}};
 await collect({...args,historyOnly:true}); await collect({...args,historyOnly:true});
 const upgraded=fs.readFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(f=>f.signature==='sig').at(-1);
 assert.equal(upgraded.schema_version,11);assert.equal(upgraded.classification,'rent_maintenance');assert.equal(refreshed,1);
 const recordedEvent={signature:'sig',wallet,position:'p'};
 fs.writeFileSync(path.join(dir,'dlmm_transactions.jsonl'),JSON.stringify(recordedEvent)+'\n');
 fs.writeFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),JSON.stringify({...transactionFact(tx,wallet,'sig',recordedEvent),schema_version:7})+'\n');
 await collect({...args,historyOnly:true});
 assert.equal(refreshed,1); // No broad schema migration of already-recorded transactions.

 console.log('NAV includes reserves once, classifies external flows, keeps failed fees and rejects unpriced assets');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>fs.rmSync(dir,{recursive:true,force:true}));

const allocated={...tx,transaction:{message:{...tx.transaction.message,instructions:[
  ...tx.transaction.message.instructions,
  {program:'system',parsed:{type:'allocate',info:{account:'outside',space:137}}},
  {program:'system',parsed:{type:'assign',info:{account:'outside',owner:'poolProgram'}}}
]}}};
const allocationFact=transactionFact(allocated,wallet,'allocation',{position:'p'});
assert.equal(allocationFact.nonrefundable_account_cost_lamports,100);
assert.equal(allocationFact.wallet_delta_lamports,-105); // classification must not subtract twice
assert.equal(transactionFact(allocated,wallet,'allocation',{position:'outside'}).refundable_rent_locked_lamports,100);
for (const altered of [
 {...allocated,transaction:{message:{...allocated.transaction.message,instructions:[...allocated.transaction.message.instructions,allocated.transaction.message.instructions[1]]}}},
 {...allocated,meta:{...allocated.meta,err:{failed:true}}},
 {...allocated,meta:{...allocated.meta,preBalances:[1000,1]}},
 {...allocated,meta:{...allocated.meta,postBalances:[895,99]}},
 {...allocated,transaction:{message:{...allocated.transaction.message,instructions:allocated.transaction.message.instructions.slice(0,2)}}},
 {...allocated,transaction:{message:{...allocated.transaction.message,instructions:[{program:'system',parsed:{type:'transfer',info:{source:'other',destination:'outside',lamports:100}}},...allocated.transaction.message.instructions.slice(1)]}}}
]) assert.equal(transactionFact(altered,wallet,'allocation',{position:'p'}).nonrefundable_account_cost_lamports,0);
console.log('Allocated account funding classification passed');

(async()=>{
  const {collectRentHistory}=require('./dlmm_nav');
  const rentDir=fs.mkdtempSync(path.join(require('os').tmpdir(),'rent-history-'));
  try {
    const item={account:'ata',mint:'mint',lamports:1513840};
    const funding={signature:'fund',wallet,slot:10,failed:false,token_rent_evidence:{funded:[item]}};
    const middle={signature:'swap',wallet,slot:20,failed:false};
    const refund={signature:'refund',wallet,slot:30,failed:false,token_rent_evidence:{refunded:[item]}};
    const cache=new Map([funding,middle,refund].map(f=>[f.signature,f]));
    let calls=0, history=[{signature:'swap',slot:20,err:null},{signature:'fund',slot:10,err:null}];
    const args={dir:rentDir,wallet,PublicKey:class {constructor(value){this.value=value}},cache,
      rpc:async fn=>fn({getSignaturesForAddress:async(key,options,commitment)=>{
        calls++;assert.equal(key.value,'ata');assert.deepEqual(options,{before:'refund',limit:100});
        assert.equal(commitment,'finalized');return history;
      }})};
    const latest=()=>JSON.parse(fs.readFileSync(path.join(rentDir,'dlmm_rent_history.jsonl'),'utf8').trim().split('\n').at(-1));
    cache.delete('swap');await collectRentHistory(args);
    assert.equal(latest().complete,false);assert.equal(calls,1);
    cache.set('swap',middle);history=[{signature:'unknown',slot:20,err:null}];
    await collectRentHistory(args);assert.equal(latest().reason,'funding_not_in_bounded_history');
    history=[{signature:'swap',slot:20,err:{error:true}},{signature:'fund',slot:10,err:null}];
    await collectRentHistory(args);assert.equal(latest().complete,false);
    history=[{signature:'swap',slot:20,err:null},{signature:'fund',slot:10,err:null}];
    await collectRentHistory(args);assert.equal(latest().complete,true);
    assert.deepEqual(latest().history_signatures,['swap','fund']);
    assert.equal(latest().funding_signature,'fund');
    const done=calls;await collectRentHistory(args);assert.equal(calls,done);
    assert.equal(cache.get('refund').wallet_delta_lamports,undefined); // evidence cannot allocate cash
    console.log('Bounded rent account history, retry, cache completeness and no cash mutation passed');
  } finally {fs.rmSync(rentDir,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1});
