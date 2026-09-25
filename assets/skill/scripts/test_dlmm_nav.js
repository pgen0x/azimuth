const assert=require('node:assert/strict'), fs=require('node:fs'), os=require('node:os'), path=require('node:path');
const {collect,transactionFact}=require('./dlmm_nav.js');
const wallet='wallet',key=s=>({toString:()=>s});
const tx={slot:100,blockTime:Math.floor(Date.now()/1000),transaction:{message:{accountKeys:[{pubkey:key(wallet)},{pubkey:key('outside')}],instructions:[{program:'system',parsed:{type:'transfer',info:{source:wallet,destination:'outside',lamports:100}}}]}},meta:{err:null,fee:5,preBalances:[1000,0],postBalances:[895,100],preTokenBalances:[],postTokenBalances:[]}};
const fact=transactionFact(tx,wallet,'sig');
assert.equal(fact.wallet_delta_lamports,-105);assert.equal(fact.external_flow_lamports,-100);assert.equal(fact.fee_lamports,5);
assert.equal(transactionFact(tx,wallet,'sig',{position:'position'}).external_flow_lamports,null);
const failed=JSON.parse(JSON.stringify(tx));failed.transaction.message.accountKeys=tx.transaction.message.accountKeys;failed.meta.err={InstructionError:[0,'failed']};failed.meta.postBalances=[995,0];
assert.equal(transactionFact(failed,wallet,'fail').fee_lamports,5);
assert.equal(transactionFact(failed,wallet,'fail').external_flow_lamports,null);
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nav-check-'));
let unknown=false;
const connection={
 getSignaturesForAddress:async(_,options)=>options.before ? [] : [{signature:'sig',slot:100,blockTime:tx.blockTime}],
 getParsedTransaction:async()=>tx,getSlot:async()=>101,getBalance:async()=>1000000000,
 getParsedTokenAccountsByOwner:async(_,options)=>({value:options.programId.toString().startsWith('Tokenkeg') ? [{account:{lamports:1002039280,data:{parsed:{info:{mint:unknown?'unknown':'So11111111111111111111111111111111111111112',tokenAmount:{amount:'1000000000'}}}}}}]:[]}),
};
global.fetch=async url=>{if(url.includes('/quote?'))throw new Error('no route');return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})}};
(async()=>{
 const args={dir,wallet,PublicKey:function(s){return key(s)},rpc:fn=>fn(connection)};
 const r=await collect(args);assert.equal(r.nav_sol,2.00203928);assert.equal(r.wallet_history_complete,true);
 unknown=true;const missing=await collect(args);assert.equal(missing.nav_sol,null);assert.equal(missing.issues[0],'unpriced_token:unknown');
 assert.equal(fs.readFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),'utf8').trim().split('\n').length,1);
 console.log('NAV includes reserves once, classifies external flows, keeps failed fees and rejects unpriced assets');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>fs.rmSync(dir,{recursive:true,force:true}));
