// Offline protocol fixtures; no installed SDK, RPC, wallet or signing.
const assert = require('node:assert/strict');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path'), vm = require('node:vm');
const f = require('./test_dlmm_position_pda.json');
class PublicKey {
  constructor(value) {this.value = value;}
  toString() {return this.value;}
  equals(other) {return this.value === other?.toString();}
  toBuffer() {return Buffer.from(f.key_bytes[this.value], 'hex');}
  static findProgramAddressSync(seeds, program) {
    assert.equal(program.toString(), f.instructions.standard.program);
    if (seeds.length === 1) {
      assert.equal(seeds[0].toString(), '__event_authority');
      return [new PublicKey(f.instructions.standard.keys[6].address)];
    }
    assert.equal(seeds[0].toString(), 'position');
    assert.equal(seeds[1].toString('hex'), f.key_bytes[f.pool]);
    assert.equal(seeds[2].toString('hex'), f.key_bytes[f.wallet]);
    assert.equal(seeds[3].readInt32LE(), f.lower);
    assert.equal(seeds[4].readInt32LE(), f.upper-f.lower+1);
    return [new PublicKey(f.pda)];
  }
}
class TransactionInstruction {constructor(fields) {Object.assign(this, fields);}}
class Transaction {
  constructor(options) {
    this.feePayer = options.feePayer;
    this.recentBlockhash = 'lastValidBlockHeight' in options ? options.blockhash : options.recentBlockhash;
    this.lastValidBlockHeight = options.lastValidBlockHeight;
    this.signatures = []; this.instructions = [];
  }
  add(ix) {this.instructions.push(ix); return this;}
  compileMessage() {
    assert.ok(this.recentBlockhash, 'Transaction recentBlockhash required');
    const signerKeys = [this.feePayer];
    for (const ix of this.instructions) for (const meta of ix.keys) {
      if (meta.isSigner && !signerKeys.some(key=>key.equals(meta.pubkey))) signerKeys.push(meta.pubkey);
    }
    return {header: {numRequiredSignatures: signerKeys.length}, accountKeys: signerKeys};
  }
}
const web3 = {PublicKey, Transaction, TransactionInstruction, SystemProgram: {programId:new PublicKey('11111111111111111111111111111111')},
  SYSVAR_RENT_PUBKEY: new PublicKey('SysvarRent111111111111111111111111111111111')};
const context = {module: {exports: {}}, require: name=>name==='@solana/web3.js'?web3:require(name),
  Buffer, AbortController, setTimeout, clearTimeout, fetch:()=>{throw new Error('Network forbidden');}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'dlmm_position_pda.js'),'utf8'), context);
const {preparePositionPda, beginPositionPdaHistory} = context.module.exports;
const instruction = kind => new TransactionInstruction({programId:new PublicKey(f.instructions[kind].program),
  data:Buffer.from(f.instructions[kind].data,'hex'),
  keys:f.instructions[kind].keys.map(({address,...meta})=>({...meta,pubkey:new PublicKey(address)}))});
const root=fs.mkdtempSync(path.join(os.tmpdir(),'position-pda-'));
let requests=0, signal;
const fetchFn=async(url, options)=>{
  requests++;signal=options.signal;
  const body=JSON.parse(options.body);
  assert.equal(body.method,'getSignaturesForAddress');assert.equal(body.params[0],f.pda);
  assert.equal(body.params[1].limit,1);assert.equal(body.params[1].commitment,'confirmed');
  return {ok:true,json:async()=>({result:[]})};
};
function setup() {
  const wallet=new PublicKey(f.wallet), originalPosition=new PublicKey(f.standard);
  const transaction=new Transaction({feePayer:wallet,blockhash:'retained-blockhash',lastValidBlockHeight:123});
  transaction.add(instruction('standard')).add(new TransactionInstruction({programId:new PublicKey('liquidity-program'),
    data:Buffer.from('aabbcc','hex'),keys:[{pubkey:originalPosition,isSigner:false,isWritable:true},{pubkey:wallet,isSigner:true,isWritable:false}]}));
  const pool={pubkey:new PublicKey(f.pool),program:{programId:new PublicKey(f.instructions.standard.program),methods:{
    initializePositionPda(lower,width) {
      assert.equal(lower,f.lower);assert.equal(width,f.upper-f.lower+1);
      return {accountsStrict(accounts) {
        assert.equal(accounts.base.toString(),f.wallet);assert.equal(accounts.owner.toString(),f.wallet);
        assert.equal(accounts.position.toString(),f.pda);
        return {instruction:async()=>instruction('pda')};
      }};
    }}}};
  return {pool,transaction,wallet,originalPosition,lower:f.lower,upper:f.upper,entryDir:root,rpcUrl:'https://secret.invalid'};
}
function clockedHelper() {
  let now=0, next=0, reply;
  const timers=new Map(), state={requests:0};
  const testContext={...context,module:{exports:{}},
    require:name=>name==='node:perf_hooks'?{performance:{now:()=>now}}:context.require(name),
    setTimeout:(callback,ms)=>{const id=++next;timers.set(id,{at:now+ms,callback});return id;},
    clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'dlmm_position_pda.js'),'utf8'),testContext);
  return {...testContext.module.exports,state,
    fetch:async(url,options)=>{state.requests++;state.signal=options.signal;return new Promise(resolve=>{reply=resolve;});},
    respond:data=>reply({ok:true,json:async()=>data}),
    now:()=>now,timerCount:()=>timers.size,
    advance:ms=>{
      const target=now+ms;
      while(true){
        const due=[...timers].filter(([,t])=>t.at<=target).sort((a,b)=>a[1].at-b[1].at)[0];
        if(!due)break;
        now=due[1].at;timers.delete(due[0]);due[1].callback();
      }
      now=target;
    }};
}
const flush=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
(async()=>{
  const input=setup(), before=JSON.stringify(input.transaction);
  const optimized=await preparePositionPda(input,fetchFn);
  assert.ok(optimized);assert.equal(optimized.position.toString(),f.pda);
  assert.equal(optimized.transaction.compileMessage().header.numRequiredSignatures,1);
  assert.equal(optimized.transaction.recentBlockhash,'retained-blockhash');
  assert.equal(optimized.transaction.lastValidBlockHeight,123);
  assert.equal(JSON.stringify(input.transaction),before);
  assert.equal(optimized.transaction.instructions[1].data.toString('hex'),'aabbcc');
  assert.equal(optimized.transaction.instructions[1].keys[0].pubkey.toString(),f.pda);
  assert.equal(optimized.transaction.instructions[1].keys[0].isWritable,true);
  assert.equal(optimized.creation.kind,'wallet_pda');assert.equal(signal.aborted,true);
  assert.ok(!JSON.stringify(optimized.creation).includes('secret'));
  const concurrent=setup(), previous=requests;
  concurrent.history=beginPositionPdaHistory(concurrent,fetchFn);
  assert.ok(await preparePositionPda(concurrent,()=>{throw new Error('No second lookup');}));
  assert.equal(requests,previous+1);
  assert.equal(concurrent.history.reason,'unused');
  assert.equal(await preparePositionPda({...setup(),history:null},fetchFn),null);assert.equal(requests,previous+1);
  assert.equal(await preparePositionPda({...setup(),history:{address:'other',read:Promise.resolve(true)}},fetchFn),null);
  for(const mutate of [x=>x.lower=-(2**31)-1,x=>x.upper=2**31,x=>x.upper=x.lower+70,
    x=>x.transaction.signatures=[{signature:Buffer.from([1])}],x=>x.transaction.feePayer=new PublicKey('foreign'),
    x=>x.transaction.instructions[0].data[8]^=1,x=>x.transaction.instructions.push(instruction('standard')),
    x=>x.transaction.instructions[0].keys[2].pubkey=new PublicKey('foreign'),
    x=>x.transaction.instructions[1].keys[0].isSigner=true,
    x=>x.pool.program.programId=new PublicKey('foreign')]){
    const candidate=setup();mutate(candidate);const count=requests;
    assert.equal(await preparePositionPda(candidate,fetchFn),null);assert.equal(requests,count);
  }
  const file=path.join(root,f.pda+'.json');fs.writeFileSync(file,'existing provenance');
  const count=requests;assert.equal(await preparePositionPda(setup(),fetchFn),null);assert.equal(requests,count);
  assert.equal(fs.readFileSync(file,'utf8'),'existing provenance');fs.unlinkSync(file);
  for(const [data,reason] of [[{result:[{signature:'previous'}]},'history_exists'],[{result:null},'invalid_history_response'],[{error:{message:'secret'}},'rpc_error']]){
    const candidate=setup();
    candidate.history=beginPositionPdaHistory(candidate,async()=>({ok:true,json:async()=>data}));
    assert.equal(await preparePositionPda(candidate),null);
    assert.equal(candidate.history.reason,reason);
    assert.ok(!JSON.stringify(candidate.history).includes('secret'));
  }
  assert.equal(await preparePositionPda(setup(),async()=>{throw new Error('secret URL');}),null);
  const unavailable=setup();unavailable.pool.program.methods.initializePositionPda=()=>{throw new Error('unsupported');};
  assert.equal(await preparePositionPda(unavailable,fetchFn),null);
  const forged=setup();forged.pool.program.methods.initializePositionPda=()=>({accountsStrict:()=>({instruction:async()=>instruction('standard')})});
  assert.equal(await preparePositionPda(forged,fetchFn),null);
  assert.equal(await preparePositionPda(setup(),async(url,options)=>{signal=options.signal;return new Promise(()=>{});}),null);
  assert.equal(signal.aborted,true);
  // A completed late response can save a signature while the SDK is busy,
  // without adding any wait after its builder returns.
  for(const data of [{result:[]},{result:[{signature:'prior-entry'}]}]){
    const clock=clockedHelper(),candidate=setup();
    candidate.history=clock.beginPositionPdaHistory(candidate,clock.fetch);
    clock.advance(800);assert.equal(clock.state.signal.aborted,false);
    clock.respond(data);await flush();
    const at=clock.now(),result=await clock.preparePositionPda(candidate);
    assert.equal(clock.now(),at);assert.equal(clock.state.requests,1);assert.equal(clock.timerCount(),0);
    if(data.result.length)assert.equal(result,null);
    else assert.equal(result.transaction.compileMessage().header.numRequiredSignatures,1);
  }
  // Fast builders retain only the remainder of the original 300 ms window.
  for(const responds of [true,false]){
    const clock=clockedHelper(),candidate=setup();
    candidate.history=clock.beginPositionPdaHistory(candidate,clock.fetch);
    clock.advance(100);
    let done=false;
    const result=clock.preparePositionPda(candidate).then(value=>{done=true;return value;});
    await flush();clock.advance(responds?150:199);await flush();assert.equal(done,false);
    if(responds)clock.respond({result:[]});else clock.advance(1);
    await flush();
    const value=await result;
    if(responds)assert.equal(value.transaction.compileMessage().header.numRequiredSignatures,1);
    else assert.equal(value,null);
    assert.equal(clock.now(),responds?250:300);assert.equal(clock.state.signal.aborted,true);
    assert.equal(clock.state.requests,1);assert.equal(clock.timerCount(),0);
  }
  // A slow builder with no completed history falls back immediately. A later
  // empty response cannot resurrect the canceled evidence or trigger a retry.
  const pendingClock=clockedHelper(),pending=setup();
  pending.history=pendingClock.beginPositionPdaHistory(pending,pendingClock.fetch);
  pendingClock.advance(500);
  assert.equal(await pendingClock.preparePositionPda(pending),null);
  assert.equal(pendingClock.now(),500);assert.equal(pendingClock.state.signal.aborted,true);
  assert.equal(pendingClock.timerCount(),0);
  pendingClock.advance(300);pendingClock.respond({result:[]});await flush();
  assert.equal(await pending.history.read,false);
  assert.equal(pending.history.reason,'wait_window_elapsed');
  assert.equal(await pendingClock.preparePositionPda(pending),null);
  assert.equal(pendingClock.state.requests,1);
  const abandonedClock=clockedHelper(),abandoned=setup();
  const abandonedHistory=abandonedClock.beginPositionPdaHistory(abandoned,abandonedClock.fetch);
  abandonedClock.advance(2999);assert.equal(abandonedClock.state.signal.aborted,false);
  abandonedClock.advance(1);assert.equal(await abandonedHistory.read,false);
  assert.equal(abandonedHistory.reason,'history_timeout');
  assert.equal(abandonedClock.state.signal.aborted,true);assert.equal(abandonedClock.timerCount(),0);
  console.log('position PDA identity, unsigned rewrite, bounded history and fallback checks passed');
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>fs.rmSync(root,{recursive:true,force:true}));
