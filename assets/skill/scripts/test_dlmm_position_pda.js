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
  for(const data of [{result:[{signature:'previous'}]},{result:null},{error:{message:'secret'}}]){
    assert.equal(await preparePositionPda(setup(),async()=>({ok:true,json:async()=>data})),null);
  }
  assert.equal(await preparePositionPda(setup(),async()=>{throw new Error('secret URL');}),null);
  const unavailable=setup();unavailable.pool.program.methods.initializePositionPda=()=>{throw new Error('unsupported');};
  assert.equal(await preparePositionPda(unavailable,fetchFn),null);
  const forged=setup();forged.pool.program.methods.initializePositionPda=()=>({accountsStrict:()=>({instruction:async()=>instruction('standard')})});
  assert.equal(await preparePositionPda(forged,fetchFn),null);
  assert.equal(await preparePositionPda(setup(),async(url,options)=>{signal=options.signal;return new Promise(()=>{});}),null);
  assert.equal(signal.aborted,true);
  console.log('position PDA identity, unsigned rewrite, bounded history and fallback checks passed');
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>fs.rmSync(root,{recursive:true,force:true}));
