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
const {dependencyKeys, captureBank, boundedJson, allowed, archiveTarget} = mod.exports;
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
  const directory = fs.mkdtempSync(path.join(require('os').tmpdir(), 'exit-bank-series-'));
  try {
    const now = Date.now(), position = key(20);
    const first = archiveTarget(directory, position, now);
    assert.equal(path.basename(first.output), position + '.json');
    fs.writeFileSync(first.output, 'original bank');
    fs.utimesSync(first.output, new Date(now), new Date(now));
    assert.equal(archiveTarget(directory, position, now + 599999).status, 'archive_interval');
    const second = archiveTarget(directory, position, now + 600001);
    assert.equal(path.basename(second.output), position + '.2.json');
    fs.writeFileSync(second.output, 'later bank');
    fs.utimesSync(second.output, new Date(now + 600001), new Date(now + 600001));
    assert.equal(archiveTarget(directory, position, now + 600002).status, 'archive_interval');
    const third = archiveTarget(directory, position, now + 1200002);
    assert.equal(path.basename(third.output), position + '.3.json');
    fs.writeFileSync(third.output, 'last bank');
    assert.equal(archiveTarget(directory, position, now + 1800003).status, 'position_archive_capacity');
    assert.equal(fs.readFileSync(first.output, 'utf8'), 'original bank');
    for (let n=21;n<28;n++) fs.writeFileSync(path.join(directory,key(n)+'.json'),'bank');
    assert.equal(archiveTarget(directory,key(28),now).status,'archive_capacity');
    fs.utimesSync(path.join(directory,key(21)+'.json'),new Date(now),new Date(now));
    assert.equal(archiveTarget(directory,key(21),now+600001).sequence,2);
    const large=path.join(directory,key(21)+'.json');
    fs.truncateSync(large,481*1024*1024);
    assert.equal(archiveTarget(directory,key(21),now+600001).status,'archive_byte_capacity');
  } finally { fs.rmSync(directory, {recursive:true, force:true}); }
  const close = [ix(key(1), [key(2), key(3)])];
  const response = {tokenLedgerInstruction: ix(key(4), [key(5)]),
    swapInstruction: ix(key(4), [key(6)]), addressLookupTableAddresses: [key(7)],
    setupInstructions: [ix(key(8), [key(9)])], cleanupInstruction: ix(key(8), [key(10)])};
  const keys = dependencyKeys(close, response, {position: key(2), oracle: key(13)});
  for (let n=1;n<=10;n++) assert(keys.includes(key(n)), `missing dependency ${n}`);
  assert(keys.includes(key(13)), 'direct-pool oracle absent from external route');
  assert.throws(() => dependencyKeys(close, {}, {position: key(2)}), /missing_swap/);
  assert.throws(() => dependencyKeys(close, {...response,
    addressLookupTableAddresses: Array.from({length:101},(_,i)=>key(i))}, {position:key(2)}), /account_limit/);
  const program = key(1), dataAddress = key(11), position = key(2);
  const programBytes = Buffer.alloc(36); programBytes.writeUInt32LE(2);
  new PublicKey(dataAddress).toBuffer().copy(programBytes, 4);
  const elf = Buffer.alloc(50); elf.writeUInt32LE(3);
  const state = {[program]:account(loader,programBytes,true),
    [dataAddress]:account(loader,elf), [position]:account(program,Buffer.from('position')),
    [key(13)]:account(program,Buffer.from('oracle'))};
  const requests = [];
  const bank = await captureBank([program,position,key(12),key(13)], async requested => {
    requests.push(requested); return {context:{slot:10+requests.length},
      value:requested.map(k=>state[k]||null)};
  }, position);
  assert.equal(requests.length,2); assert(requests[1].includes(dataAddress));
  assert.equal(bank.snapshot_slot,12); assert.equal(bank.discovery_slot,11);
  assert.equal(bank.accounts[key(12)],null); // Explicit absence is replay evidence.
  assert.deepEqual(bank.accounts[dataAddress],state[dataAddress]);
  assert(requests.every(requested => requested.includes(key(13))));
  assert.deepEqual(bank.accounts[key(13)],state[key(13)]);
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
