const assert=require('node:assert/strict');
const {cashSignEvidence,cashSignRefresh}=require('./dlmm_cash_sign.js');
const {transactionFact}=require('./dlmm_nav.js');
const S='11111111111111111111111111111111', T='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA';
const D='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo', SOL='So11111111111111111111111111111111111111112';
const instruction=(programId,type,info)=>({programId,...(programId===S?{program:'system'}:{}),parsed:{type,info}});
const token=(accountIndex,owner,mint,amount)=>({accountIndex,owner,mint,uiTokenAmount:{amount}});
function funding() {
  return {slot:100,blockTime:120,transaction:{message:{
    accountKeys:['wallet','position','legacy','temporary','vault'].map(pubkey=>({pubkey,signer:pubkey==='wallet'})),
    instructions:[{programId:D},instruction(S,'transfer',{source:'wallet',destination:'temporary',lamports:100}),
      instruction(S,'createAccount',{source:'wallet',newAccount:'position',owner:D,lamports:50}),
      instruction(S,'createAccount',{source:'wallet',newAccount:'temporary',owner:T,lamports:20}),
      instruction(T,'initializeAccount3',{account:'temporary',mint:SOL,owner:'wallet'}),
      instruction(T,'closeAccount',{account:'temporary',destination:'wallet',owner:'wallet'})]}},
    meta:{err:null,fee:5,innerInstructions:[],preBalances:[1000,0,20,0,500],postBalances:[845,50,20,0,600],
      preTokenBalances:[token(2,'wallet','mint','123'),token(4,'pool',SOL,'480')],
      postTokenBalances:[token(2,'wallet','mint','123'),token(4,'pool',SOL,'580')]}};
}
const expected={version:1,position:'position',basis:'parsed_system_debits_and_unchanged_retained_token_accounts',no_retained_wallet_funding_outside_position:true};
assert.deepEqual(cashSignEvidence(funding(),'wallet','position'),expected);
assert.deepEqual(transactionFact(funding(),'wallet','fund',{position:'position'}).cash_sign_evidence,expected);
const inner=funding();inner.meta.innerInstructions=[{index:0,instructions:inner.transaction.message.instructions.splice(1)}];
assert.deepEqual(cashSignEvidence(inner,'wallet','position'),expected);
for (const [name,change] of Object.entries({
  missingInner:t=>{delete t.meta.innerInstructions}, missingTokens:t=>{delete t.meta.postTokenBalances},
  failed:t=>{t.meta.err={InstructionError:[0,'failed']}}, noSigner:t=>{t.transaction.message.accountKeys[0].signer=false},
  missingOwner:t=>{delete t.meta.postTokenBalances[0].owner}, tokenInventory:t=>{t.meta.postTokenBalances[0].uiTokenAmount.amount='124'},
  rentTopup:t=>{t.meta.postBalances[2]++}, retainedWSOL:t=>{t.meta.postBalances[3]=20;t.meta.postTokenBalances.push(token(3,'wallet',SOL,'0'))},
  newATA:t=>{t.meta.preBalances[2]=0;t.meta.preTokenBalances.shift()},
  unknownProgram:t=>{t.transaction.message.instructions.push({programId:'unknown'})},
  unparsedSystem:t=>{t.meta.innerInstructions=[{instructions:[{programId:S,data:'unparsed'}]}]},
  nonce:t=>{t.transaction.message.instructions.push(instruction(S,'withdrawNonce',{nonceAccount:'legacy',lamports:1}))},
  assignWallet:t=>{t.transaction.message.instructions.push(instruction(S,'assign',{account:'wallet',owner:D}))},
  closedProxy:t=>{t.transaction.message.instructions[3].parsed.info.owner=D},
  closeToOther:t=>{t.transaction.message.instructions.at(-1).parsed.info.destination='other'},
  noWSOLinit:t=>{t.transaction.message.instructions[4].parsed.info.mint='mint'},
  indirectReserve:t=>{t.meta.preTokenBalances.pop();t.meta.postTokenBalances.pop()},
  reserveRent:t=>{t.meta.postBalances[4]++},
  newVault:t=>{t.meta.preBalances[4]=0},
  unsafeBalance:t=>{t.meta.postBalances[1]=Number.MAX_SAFE_INTEGER+1},
})) {
  const t=funding();change(t);assert.equal(cashSignEvidence(t,'wallet','position'),null,name);
}
// A PDA transfer+allocate, a tip, or funding an uninitialized retained account
// cannot disappear just because the token-rent decoder doesn't recognize it.
for(const destination of ['legacy','vault']) {
  const t=funding();t.transaction.message.instructions.push(instruction(S,'transfer',{source:'wallet',destination,lamports:1}));
  assert.equal(cashSignEvidence(t,'wallet','position'),null);
}
assert.equal(cashSignEvidence(funding(),'wallet','missing'),null);
// Optional upgrades are bounded, do not retry null proofs, and skip new rent,
// positive cash, unknown transactions, unlanded attempts, old/future closes.
const events=new Map(),cache=new Map(),closes=[];
for(let n=0;n<8;n++) {
  const position='p'+n,signature='s'+n;
  events.set(signature,{position,signature,wallet:'wallet'});
  cache.set(signature,{wallet:'wallet',wallet_delta_lamports:-1,token_rent_evidence:{funded:[]}});
  closes.push({position,ts:200});
}
assert.deepEqual([...cashSignRefresh(events,cache,closes,'wallet',300)],['s0','s1','s2','s3']);
cache.get('s0').cash_sign_evidence=null;cache.get('s1').token_rent_evidence.funded=[{}];cache.get('s2').wallet_delta_lamports=1;
cache.delete('s3');cache.get('s4').landed=false;closes[5].ts=301;closes[6].ts=300-2*86400-1;
assert.deepEqual([...cashSignRefresh(events,cache,closes,'wallet',300)],['s7']);
console.log('cash sign finalized metadata and bounded refresh checks passed');

(async()=>{
  const fs=require('fs'),os=require('os'),path=require('path');
  const {collect}=require('./dlmm_nav.js');
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'cash-sign-'));
  try {
    const stamp=Math.floor(Date.now()/1000), missing=Array.from({length:60},(_,i)=>'missing-'+i);
    const optional=Array.from({length:4},(_,i)=>'optional-'+i), signatures=[...optional,...missing];
    const event=signature=>({signature,wallet:'wallet',position:optional.includes(signature)?'position':'open'});
    const write=(name,rows)=>fs.writeFileSync(path.join(dir,name),rows.map(JSON.stringify).join('\n')+'\n');
    write('dlmm_transactions.jsonl',signatures.map(event));
    write('dlmm_closes.jsonl',[{position:'position',ts:stamp-1}]);
    write('dlmm_nav.jsonl',[{started_at:100}]);
    write('dlmm_wallet_transactions.jsonl',optional.map(signature=>{
      const f=transactionFact(funding(),'wallet',signature,event(signature));delete f.cash_sign_evidence;return f;
    }));
    const reads=[],connection={getBlockHeight:async()=>200,getSlot:async()=>200,
      getSignaturesForAddress:async(_,options)=>options.before?[]:signatures.slice(0,options.limit).map(signature=>({signature,slot:100,blockTime:120})),
      getParsedTransaction:async signature=>{reads.push(signature);return funding();}};
    const args={dir,wallet:'wallet',PublicKey:class {constructor(s){this.s=s;}toString(){return this.s;}},
                rpc:fn=>fn(connection),historyOnly:true};
    const first=await collect(args);
    assert.equal(first.wallet_history_complete,true);assert.deepEqual(reads,missing);
    await collect({...args,includeRentHistory:false});assert.equal(reads.length,60);
    const second=await collect(args);
    assert.equal(second.wallet_history_complete,true);assert.deepEqual(reads.slice(60),optional);
    await collect(args);assert.equal(reads.length,64);
    const facts=fs.readFileSync(path.join(dir,'dlmm_wallet_transactions.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
    assert.ok(facts.slice(-4).every(f=>f.cash_sign_evidence?.no_retained_wallet_funding_outside_position===true));
    console.log('cash sign optional refresh preserves coverage and the shared 60-fetch cap');
  } finally { fs.rmSync(dir,{recursive:true,force:true}); }
})().catch(e=>{console.error(e);process.exitCode=1;});
