const assert=require('node:assert/strict'), fs=require('node:fs'), os=require('node:os'), path=require('node:path');
const {collect,transactionFact}=require('./dlmm_nav.js');
const wallet='wallet',key=s=>({toString:()=>s});
const tx={slot:100,blockTime:Math.floor(Date.now()/1000),transaction:{message:{accountKeys:[{pubkey:key(wallet)},{pubkey:key('outside')}],instructions:[{program:'system',parsed:{type:'transfer',info:{source:wallet,destination:'outside',lamports:100}}}]}},meta:{err:null,fee:5,preBalances:[1000,0],postBalances:[895,100],preTokenBalances:[],postTokenBalances:[]}};
const fact=transactionFact(tx,wallet,'sig');
assert.equal(fact.wallet_delta_lamports,-105);assert.equal(fact.external_flow_lamports,-100);assert.equal(fact.fee_lamports,5);
assert.equal(transactionFact(tx,wallet,'sig',{position:'position'}).external_flow_lamports,null);
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
 let rateLimitedRequests=0;
 global.fetch=async url=>{if(url.includes('/quote?')){rateLimitedRequests++;return {ok:false,status:429};}return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})}};
 const limited=await collect(args);
 assert.equal(rateLimitedRequests,1);assert.equal(limited.nav_sol,null);
 const latest=JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim().split('\n').at(-1));
 assert.ok(latest.tokens.some(t=>t.mark_error==='quote_rate_limit_deferred'));
 console.log('NAV includes reserves once, classifies external flows, keeps failed fees and rejects unpriced assets');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>fs.rmSync(dir,{recursive:true,force:true}));
