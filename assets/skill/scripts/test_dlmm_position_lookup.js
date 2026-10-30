// Offline test of production lookup; no wallet decoding, signing or RPC.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname,'dlmm_executor.js'),'utf8');
const code = source.slice(source.indexOf('async function findPoolForPosition('),source.indexOf('\nfunction positionIsEmpty('));
class Key { constructor(value) { if (!value || value==='bad') throw Error('bad address'); this.value=value; } toString(){return this.value;} }
const key = value=>new Key(value);
async function run(change={}) {
  let wide=0, targeted=0, poolReads=0;
  const native={owner:key('wallet'),lbPair:key('pool'),...change.native};
  const pool={program:{coder:{accounts:{decode:()=>native}}},getPosition:async()=>{
    targeted++;
    return {publicKey:key('position'),positionData:{owner:key('wallet')},...change.position};
  }};
  const account={owner:key('program'),data:Buffer.from([1,2,3,4,5,6,7,8]),...change.account};
  const connection={getAccountInfo:async()=>{if(change.rpcError)throw Error('RPC unavailable');return change.accountNull?null:account;}};
  const context={Buffer,path,PROFILE_DIR:'/profile',PublicKey:Key,AbortSignal,
    fs:{readFileSync:()=>{if(change.missing)throw Error('missing');return JSON.stringify(change.entry||{position:'position',pool:'pool'});}},
    DLMM:{IDL:{address:'program',accounts:[{name:'PositionV2',discriminator:[1,2,3,4,5,6,7,8]}]},
      create:async()=>{poolReads++;return pool;},getAllLbPairPositionsByUser:async()=>{wide++;return new Map();}},
    fetch:async()=>({ok:true,json:async()=>({pools:[]})}),console};
  vm.createContext(context);vm.runInContext(code+'\nthis.lookup=findPoolForPosition;',context);
  const result=await context.lookup(connection,{publicKey:key('wallet')},'position');
  return {result,wide,targeted,poolReads};
}
(async()=>{
  let r=await run();assert.equal(r.result.poolAddressStr,'pool');assert.equal(r.wide,0);assert.equal(r.targeted,1);
  for(const change of [{missing:true},{entry:{position:'other',pool:'pool'}},{entry:{position:'position',pool:'bad'}},
    {account:{owner:key('other')}},{account:{data:Buffer.alloc(8)}},
    {native:{owner:key('other')}},{native:{lbPair:key('other')}}]){
    r=await run(change);assert.equal(r.result,null);assert.equal(r.wide,1);assert.equal(r.targeted,0);
  }
  r=await run({position:{positionData:{owner:key('other')}}});assert.equal(r.result,null);assert.equal(r.wide,1);
  // The SDK position must be the requested one, not just any position owned by the wallet.
  r=await run({position:{publicKey:key('other')}});assert.equal(r.result,null);assert.equal(r.wide,1);
  // A missing account is not verification: fall back without reading the hinted pool.
  r=await run({accountNull:true});assert.equal(r.result,null);assert.equal(r.wide,1);assert.equal(r.poolReads,0);
  await assert.rejects(run({rpcError:true}),/RPC unavailable/);
  console.log('Targeted position lookup verifies native ownership and pool; legacy discovery retained');
})().catch(error=>{console.error(error);process.exitCode=1;});
