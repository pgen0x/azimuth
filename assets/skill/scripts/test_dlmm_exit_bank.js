const assert = require('assert/strict');
const fs = require('fs'), path = require('path'), vm = require('vm');
// Unit fixtures exercise account graph/state checks without installing an SDK.
// Base58/address validation remains the SDK's responsibility in production.
class PublicKey {
  constructor(value) { this.value = Buffer.isBuffer(value) ? value.toString('hex') : String(value); }
  toString() { return this.value; }
  toBuffer() { return Buffer.from(this.value, 'hex'); }
}
const mod = {exports: {}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'dlmm_exit_bank.js'),'utf8'), {
  module: mod, Buffer, Response, console, setTimeout,
  require: name => name === '@solana/web3.js' ? {PublicKey} : require(name),
  fetch: () => { throw new Error('network forbidden in offline test'); },
});
const {dependencyKeys, captureBank, boundedJson, allowed} = mod.exports;
const key = n => new PublicKey(Buffer.alloc(32, n)).toString();
const loader = 'BPFLoaderUpgradeab1e11111111111111111111111';
const account = (owner, data, executable=false) => ({owner, executable,
  lamports: 1, data: [data.toString('base64'), 'base64']});
const ix = (program, accounts=[]) => ({programId: program,
  accounts: accounts.map(pubkey => ({pubkey, isSigner: false, isWritable: true})), data: ''});
(async () => {
  assert.equal((await boundedJson(new Response('{"ok":true}'),100)).ok,true);
  await assert.rejects(boundedJson(new Response('x'.repeat(101)),100), /response_size_limit/);
  for (const method of ['sendTransaction','sendRawTransaction','requestAirdrop','simulateTransaction'])
    assert.equal(allowed.has(method), false);
  const close = [ix(key(1), [key(2), key(3)])];
  const response = {tokenLedgerInstruction: ix(key(4), [key(5)]),
    swapInstruction: ix(key(4), [key(6)]), addressLookupTableAddresses: [key(7)],
    setupInstructions: [ix(key(8), [key(9)])], cleanupInstruction: ix(key(8), [key(10)])};
  const keys = dependencyKeys(close, response, {position: key(2)});
  for (let n=1;n<=10;n++) assert(keys.includes(key(n)), `missing dependency ${n}`);
  assert.throws(() => dependencyKeys(close, {}, {position: key(2)}), /missing_swap/);
  assert.throws(() => dependencyKeys(close, {...response,
    addressLookupTableAddresses: Array.from({length:101},(_,i)=>key(i))}, {position:key(2)}), /account_limit/);
  const program = key(1), dataAddress = key(11), position = key(2);
  const programBytes = Buffer.alloc(36); programBytes.writeUInt32LE(2);
  new PublicKey(dataAddress).toBuffer().copy(programBytes, 4);
  const elf = Buffer.alloc(50); elf.writeUInt32LE(3);
  const state = {[program]:account(loader,programBytes,true),
    [dataAddress]:account(loader,elf), [position]:account(program,Buffer.from('position'))};
  const requests = [];
  const bank = await captureBank([program,position,key(12)], async requested => {
    requests.push(requested); return {context:{slot:10+requests.length},
      value:requested.map(k=>state[k]||null)};
  }, position);
  assert.equal(requests.length,2); assert(requests[1].includes(dataAddress));
  assert.equal(bank.snapshot_slot,12); assert.equal(bank.discovery_slot,11);
  assert.equal(bank.accounts[key(12)],null); // Explicit absence is replay evidence.
  assert.deepEqual(bank.accounts[dataAddress],state[dataAddress]);
  for (const failure of ['closed','program_changed','missing_code','backwards_slot']) {
    let count=0;
    await assert.rejects(captureBank([program,position], async requested => {
      count++; const values=requested.map(k=>state[k]||null);
      if(count===2) {
        if(failure==='closed')values[requested.indexOf(position)]=null;
        if(failure==='program_changed')values[requested.indexOf(program)]=null;
        if(failure==='missing_code')values[requested.indexOf(dataAddress)]=null;
      }
      return {context:{slot:failure==='backwards_slot'&&count===2?9:10},value:values};
    },position));
  }
  console.log('Exit bank: route dependencies, one final bank, program consistency, absence and read-only RPC allowlist');
})().catch(e=>{console.error(e);process.exitCode=1;});
