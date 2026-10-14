const assert=require('node:assert/strict');
const {retainedRentEvidence,BASIS}=require('./dlmm_retained_rent.js');
const {cashSignEvidence}=require('./dlmm_cash_sign.js');
const {transactionFact}=require('./dlmm_nav.js');
const S='11111111111111111111111111111111',T='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA';
const D='LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo',SOL='So11111111111111111111111111111111111111112';
const ix=(programId,type,info)=>({programId,...(programId===S?{program:'system'}:{}),parsed:{type,info}});
const token=(accountIndex,owner,mint,amount)=>({accountIndex,owner,mint,uiTokenAmount:{amount}});
function funding(){return {slot:100,blockTime:120,transaction:{message:{
 accountKeys:['wallet','position','ata','temporary','vault'].map(pubkey=>({pubkey,signer:pubkey==='wallet'})),
 instructions:[{programId:D},ix(S,'transfer',{source:'wallet',destination:'temporary',lamports:100}),
 ix(S,'createAccount',{source:'wallet',newAccount:'position',owner:D,lamports:50}),
 ix(S,'createAccount',{source:'wallet',newAccount:'temporary',owner:T,lamports:20}),
 ix(T,'initializeAccount3',{account:'temporary',mint:SOL,owner:'wallet'}),
 ix(T,'closeAccount',{account:'temporary',destination:'wallet',owner:'wallet'}),
 ix(S,'createAccount',{source:'wallet',newAccount:'ata',owner:T,lamports:20}),
 ix(T,'initializeAccount3',{account:'ata',mint:'mint',owner:'wallet'})]}},
 meta:{err:null,fee:5,innerInstructions:[],preBalances:[1000,0,0,0,500],postBalances:[825,50,20,0,600],
 preTokenBalances:[token(4,'pool',SOL,'480')],postTokenBalances:[token(2,'wallet','mint','0'),token(4,'pool',SOL,'580')]}};}
const tx=funding(),before=JSON.stringify(tx);
const expected={version:1,position:'position',basis:BASIS,max_future_rent_credit_lamports:20,
 funded_accounts:[{account:'ata',mint:'mint',lamports:20}]};
assert.equal(cashSignEvidence(tx,'wallet','position'),null);
assert.deepEqual(retainedRentEvidence(tx,'wallet','position'),expected);
assert.equal(JSON.stringify(tx),before);
assert.deepEqual(transactionFact(tx,'wallet','sig',{position:'position'}).retained_rent_evidence,expected);
const inner=funding();inner.meta.innerInstructions=[{index:0,instructions:inner.transaction.message.instructions.splice(1)}];
assert.deepEqual(retainedRentEvidence(inner,'wallet','position'),expected);
for(const [name,change] of Object.entries({
 inventory:t=>t.meta.postTokenBalances[0].uiTokenAmount.amount='1',
 wrongFunding:t=>t.transaction.message.instructions[6].parsed.info.source='other',
 amountMismatch:t=>t.transaction.message.instructions[6].parsed.info.lamports=19,
 wrongOwner:t=>t.transaction.message.instructions[7].parsed.info.owner='other',
 wrongMint:t=>t.transaction.message.instructions[7].parsed.info.mint='other',
 missingInit:t=>t.transaction.message.instructions.pop(),
 extraDebit:t=>t.transaction.message.instructions.push(ix(S,'transfer',{source:'wallet',destination:'ata',lamports:1})),
 unknownProgram:t=>t.transaction.message.instructions.push({programId:'unknown'}),
 unparsed:t=>t.transaction.message.instructions.push({programId:S,data:'unknown'}),
 duplicateToken:t=>t.meta.postTokenBalances.push({...t.meta.postTokenBalances[0]}),
 existingTopup:t=>{t.meta.preBalances[2]=10;t.meta.preTokenBalances.push(token(2,'wallet','mint','0'));},
 unknownReserve:t=>{t.meta.postBalances[4]++;},
 unsafeRent:t=>t.meta.postBalances[2]=Number.MAX_SAFE_INTEGER+1,
 failed:t=>t.meta.err={InstructionError:[0,'failed']},
 missingBalances:t=>delete t.meta.preTokenBalances,
 missingSystemLabel:t=>delete t.transaction.message.instructions[6].program,
})) {const t=funding();change(t);assert.equal(retainedRentEvidence(t,'wallet','position'),null,name);}
assert.equal(retainedRentEvidence(tx,'wallet',undefined),null);
console.log('Retained rent proof: exact empty funding, integration, immutability and adversarial rejection passed');
// Existing finalized facts with retained rent receive one bounded optional upgrade.
const {cashSignRefresh}=require('./dlmm_cash_sign.js');
const events=new Map([['fund',{position:'position',signature:'fund',wallet:'wallet'}]]);
const cache=new Map([['fund',{wallet:'wallet',wallet_delta_lamports:-25,cash_sign_evidence:null,
 token_rent_evidence:{funded:[{account:'ata',mint:'mint',lamports:20}]}}]]);
const closes=[{position:'position',ts:200}];
assert.deepEqual([...cashSignRefresh(events,cache,closes,'wallet',300)],['fund']);
cache.get('fund').retained_rent_evidence=null;
assert.deepEqual([...cashSignRefresh(events,cache,closes,'wallet',300)],[]);
