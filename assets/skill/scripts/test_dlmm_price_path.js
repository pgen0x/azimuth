const assert = require('node:assert/strict');
const {observe} = require('./dlmm_price_path');
const SOL = 'So11111111111111111111111111111111111111112';
class Key {constructor(x){if(!x)throw Error();this.x=x;} toString(){return this.x;}}
(async () => {
  let reads=0;
  const account={owner:{equals:()=>true},data:{tokenXMint:new Key('mint'),tokenYMint:new Key(SOL),activeId:-500,binStep:100}};
  const connection={getMultipleAccountsInfoAndContext:async()=>{reads++;return {context:{slot:123},value:[account]};}};
  const program={programId:'program',coder:{accounts:{decode:(_,data)=>data}}};
  const candidates=[{pool:'pool',base_mint:'mint'}];
  assert.equal((await observe(connection,program,candidates,Key,()=>false)).status,'deferred');
  assert.equal(reads,0);
  let result=await observe(connection,program,candidates,Key,()=>true);
  assert.equal(reads,1);assert.equal(result.observations[0].active_bin,-500);
  assert.equal(result.observations[0].slot,123);
  account.owner.equals=()=>false;
  assert.equal((await observe(connection,program,candidates,Key,()=>true)).observations[0].status,'unmeasured');
  account.owner.equals=()=>true;account.data.tokenXMint=new Key('wrong');
  assert.equal((await observe(connection,program,candidates,Key,()=>true)).observations[0].status,'unmeasured');
  await assert.rejects(()=>observe(connection,program,[...candidates,...candidates],Key,()=>true));
  await assert.rejects(()=>observe({...connection,getMultipleAccountsInfoAndContext:async()=>({context:{slot:123},value:[]})},program,candidates,Key,()=>true));
  console.log('price path tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
