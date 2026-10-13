// Offline transport/confirmation tests; no signing and no external RPC requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, 'dlmm_executor.js'), 'utf8');
const raw = Buffer.from('one-persisted-signed-close');
const strategy = {signature:'same-signature',blockhash:'same-blockhash',lastValidBlockHeight:150};

function fixture(plans, urls = ['rpc-1','rpc-2']) {
  let now=0, sequence=0;
  const timers=new Map(), sends=[], reads=[], signals=[], logs=[], journal=[];
  let journalError=false;
  const clock={now:()=>now, setTimeout(fn,ms){const id=++sequence;timers.set(id,{at:now+ms,fn});return id;},clearTimeout(id){timers.delete(id);}};
  const flush=async()=>{for(let i=0;i<25;i++)await Promise.resolve();};
  const tick=async(ms)=>{
    const end=now+ms;await flush();
    while(true){
      const next=[...timers].filter(([,t])=>t.at<=end).sort((a,b)=>a[1].at-b[1].at||a[0]-b[0])[0];
      if(!next)break;
      now=next[1].at;timers.delete(next[0]);next[1].fn();await flush();
    }
    now=end;await flush();
  };
  class Connection {
    constructor(url,options){this.url=url;this.options=options;}
    async sendRawTransaction(bytes,options){
      sends.push({url:this.url,at:now,bytes:bytes.toString('hex'),options:{...options}});
      assert.equal(bytes,raw);assert.equal(options.preflightCommitment,'confirmed');
      assert.equal(options.maxRetries,20);assert.equal(options.skipPreflight,undefined);
      const plan=plans[this.url];
      if(plan.sendError)throw new Error('transport rejected');
      if(plan.stallSend)return this.options.fetch(this.url,{method:'POST'});
      if(plan.sendDelay)await new Promise(resolve=>clock.setTimeout(resolve,plan.sendDelay));
      return strategy.signature;
    }
    async getSignatureStatuses(signatures,options){
      assert.deepEqual(Array.from(signatures),[strategy.signature]);assert.equal(options.searchTransactionHistory,true);
      reads.push({url:this.url,at:now});
      const plan=plans[this.url];
      if(plan.readError)throw new Error('status unavailable');
      if(plan.stallStatus)return this.options.fetch(this.url,{method:'POST'});
      if(plan.statuses?.length>1)return {value:[plan.statuses.shift()]};
      return {value:[plan.statuses?.[0]??null]};
    }
    async confirmTransaction(){throw new Error('No WebSocket confirmation');}
  }
  const fakeRequire=name=>{
    if(name==='@solana/web3.js')return {Connection};
    if(name==='@meteora-ag/dlmm')return {};
    if(name==='dotenv')return {config(){},parse(){return {};}};
    if(name==='bn.js'||name==='bs58'||name==='./dlmm_risk_mark')return {};
    if(name==='fs')return {...fs,existsSync:()=>false,mkdirSync(){},appendFileSync(_file,line){
      if(journalError)throw new Error('optional journal unavailable');
      journal.push(JSON.parse(line));
    }};
    return require(name);
  };
  const context={require:fakeRequire,module:{exports:{}},process:{argv:['node','/offline/skills/solana-dlmm/scripts/dlmm_executor.js'],env:{SOLANA_RPC_URLS:urls.join(',')}},
    Buffer,AbortController,AbortSignal,Date:class extends Date{static now(){return now;}},
    setTimeout:clock.setTimeout,clearTimeout:clock.clearTimeout,console:{warn:l=>logs.push(l),log(){},error(){}},
    fetch:async(_url,options)=>new Promise((_resolve,reject)=>{
      signals.push(options.signal);
      const abort=()=>reject(new Error('fetch aborted'));
      if(options.signal.aborted)abort();else options.signal.addEventListener('abort',abort,{once:true});
    })};
  vm.runInNewContext(source+'\nmodule.exports.confirmCloseTransaction=confirmCloseTransaction;',context);
  return {confirm:()=>context.module.exports.confirmCloseTransaction(strategy,raw),single:()=>context.module.exports.confirmSignedTransaction(new Connection('rpc-1',{}),strategy,raw),tick,flush,sends,reads,signals,timers,logs,journal,failJournal(){journalError=true;},now:()=>now};
}
const confirmed={confirmationStatus:'confirmed',err:null};
const finalized={confirmationStatus:'finalized',err:null};
(async()=>{
  // The healthy second provider submits and confirms before the first send
  // resolves. Cancellation aborts the slow HTTP request rather than waiting for it.
  let f=fixture({'rpc-1':{stallSend:true},'rpc-2':{statuses:[confirmed]}});
  await f.confirm();
  assert.deepEqual(f.sends.map(s=>[s.url,s.at]),[['rpc-1',0],['rpc-2',0]]);
  assert.equal(new Set(f.sends.map(s=>s.bytes)).size,1);assert.equal(f.signals.length,1);assert.ok(f.signals[0].aborted);
  await f.flush();assert.equal(f.timers.size,0);
  assert.ok(f.logs.some(l=>l.includes('close-fanout-confirmed')&&l.includes('"rpc_index":1')));
  assert.deepEqual(f.journal.map(r=>r.stage),['started','finished']);
  assert.equal(f.journal[1].outcome,'confirmed');assert.equal(f.journal[1].confirmed_rpc_index,1);
  assert.equal(f.journal[0].raw_sha256,require('node:crypto').createHash('sha256').update(raw).digest('hex'));
  assert.ok(f.journal.every(r=>r.signature===strategy.signature&&r.raw===undefined));

  // A transport error after submission cannot conceal a confirmed signature.
  f=fixture({'rpc-1':{sendError:true,statuses:[finalized]},'rpc-2':{stallSend:true}});
  await f.confirm();assert.equal(f.sends.length,2);assert.equal(f.reads.length,1);assert.ok(f.signals[0].aborted);

  // Processed status, including a processed error, is insufficient. The shared
  // deadline leaves the signature pending and cancels every HTTP request/poll.
  for(const status of [null,{confirmationStatus:'processed',err:null},{confirmationStatus:'processed',err:'temporary fork'}]){
    f=fixture({'rpc-1':{statuses:[status]},'rpc-2':{stallSend:true}});
    const result=f.confirm().then(()=>({ok:true}),error=>({error}));
    await f.tick(7999);assert.ok(f.timers.size>0);
    await f.tick(1);const r=await result;
    assert.match(r.error.message,/timeout.*pending/);assert.equal(f.now(),8000);
    assert.equal(f.sends.length,2);assert.ok(f.signals.every(s=>s.aborted));assert.equal(f.timers.size,0);
    assert.equal(f.journal[1].outcome,'pending');assert.equal(f.journal[1].elapsed_ms,8000);
  }

  // A confirmed chain error ends the observation as a failure, even if another
  // provider is unresponsive. It cannot be treated as successful submission.
  f=fixture({'rpc-1':{statuses:[{confirmationStatus:'confirmed',err:{InstructionError:[0,'failure']}}]},'rpc-2':{stallStatus:true}});
  await assert.rejects(f.confirm(),e=>e.transactionFailed===true&&/Transaction failed/.test(e.message));
  await f.flush();assert.ok(f.signals.every(s=>s.aborted));assert.equal(f.timers.size,0);
  assert.equal(f.journal[1].outcome,'chain_failure');

  // Unknown/malformed confirmed status remains unmeasured; another provider may
  // supply a real verdict, but all unavailable providers do not prove expiry.
  f=fixture({'rpc-1':{statuses:[{confirmationStatus:'confirmed'}]},'rpc-2':{statuses:[finalized]}});
  await f.confirm();assert.equal(f.sends.length,2);
  f=fixture({'rpc-1':{sendError:true,readError:true},'rpc-2':{sendError:true,readError:true}});
  await assert.rejects(f.confirm(),/unavailable.*pending/);assert.equal(f.timers.size,0);
  f=fixture({'rpc-1':{stallSend:true},'rpc-2':{statuses:[confirmed]}});
  f.failJournal();await f.confirm();assert.equal(f.sends.length,2);assert.equal(f.journal.length,0);

  // A changing observed status still requires confirmed/finalized. Endpoint
  // duplication in configuration must not create redundant workers.
  f=fixture({'rpc-1':{statuses:[null,{confirmationStatus:'processed',err:null},confirmed]}},['rpc-1','rpc-1']);
  const result=f.confirm();await f.tick(2000);await result;
  assert.equal(f.sends.length,1);assert.equal(f.reads.length,3);assert.equal(f.timers.size,0);

  // Controlled transport comparison: five seconds spent in the first provider's
  // send is removed by the parallel second provider. This is not a mainnet fill.
  const baseline=fixture({'rpc-1':{sendDelay:5000,statuses:[confirmed]}});
  const old=baseline.single();await baseline.tick(5000);await old;
  const parallel=fixture({'rpc-1':{stallSend:true},'rpc-2':{statuses:[confirmed]}});
  await parallel.confirm();assert.equal(baseline.now(),5000);assert.equal(parallel.now(),0);
  console.log('close RPC fanout: identical bytes, confirmed verdicts, cancellation, pending deadline and controlled transport delay passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
