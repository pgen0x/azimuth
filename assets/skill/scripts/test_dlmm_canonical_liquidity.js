// Offline; uses recorded PDA inputs and pool bytes, no SDK installation or RPC.
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, "test_dlmm_canonical_liquidity.json")));
const alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function decode58(text) {
  let value = 0n;
  for (const char of text) {assert.ok(alphabet.includes(char)); value = value*58n + BigInt(alphabet.indexOf(char));}
  const bytes = [];
  while (value) {bytes.unshift(Number(value & 255n)); value >>= 8n;}
  for (const char of text) {if (char !== "1") break; bytes.unshift(0);}
  return Buffer.from(bytes);
}
function encode58(bytes) {
  let value = BigInt("0x" + Buffer.from(bytes).toString("hex")), text = "";
  while (value) {text = alphabet[Number(value % 58n)] + text; value /= 58n;}
  for (const byte of bytes) {if (byte !== 0) break; text = "1" + text;}
  return text;
}
class PublicKey {
  constructor(value) {this.bytes = typeof value === "string" ? decode58(value) : Buffer.from(value); assert.equal(this.bytes.length, 32);}
  toBuffer() {return this.bytes;}
  toString() {return encode58(this.bytes);}
  static findProgramAddressSync(seeds, program) {
    const inputs = seeds.map(s => Buffer.from(s).toString("hex"));
    const known = fixture.pda_cases.find(p => p.program === program.toString() && JSON.stringify(p.seeds) === JSON.stringify(inputs));
    assert.ok(known, "Canonical PDA seeds or program changed");
    return [new PublicKey(known.address), 255];
  }
}
const sandbox = {module:{exports:{}}, Buffer, AbortController, setTimeout, clearTimeout,
  fetch: () => {throw new Error("No network in tests");},
  require(name) {if (name === "@solana/web3.js") return {PublicKey}; assert.equal(name, "node:crypto"); return require(name);}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "dlmm_canonical_liquidity.js"), "utf8"), sandbox);
const {canonicalKeys, decodeSnapshot, observeCanonicalLiquidity, BASIS} = sandbox.module.exports;
const keys = canonicalKeys(fixture.base_mint), clone = () => structuredClone(fixture.snapshot);
const bytes = (snapshot, index) => Buffer.from(snapshot.value[index].data[0], "base64");
const replace = (snapshot, index, value) => {snapshot.value[index].data[0] = value.toString("base64");};
const signed128 = (buffer, offset, value) => {
  const raw = value < 0n ? value + (1n << 128n) : value;
  buffer.writeBigUInt64LE(raw & ((1n << 64n)-1n), offset); buffer.writeBigUInt64LE(raw >> 64n, offset+8);
};
const observed = decodeSnapshot(clone(), keys), expected = fixture.expected_pool_decoded_by_official_idl;
assert.equal(observed.status, "observed");
assert.equal(observed.protocol_lp_basis_raw, expected.lp_supply);
assert.equal(observed.signed_virtual_quote_raw, expected.virtual_quote_reserves);
assert.equal(observed.protocol_fees_raw, expected.protocol_fees);
assert.equal(observed.creator_fees_raw, expected.creator_fees);
assert.equal(observed.pool_coin_creator, expected.coin_creator);
assert.equal(observed.basis, BASIS);
assert.ok(BigInt(observed.lp_circulating_raw) > 0n);

for (const mutate of [
  s => {s.context.slot = null;}, s => {s.value.pop();},
  s => {s.value[0].owner = keys.pool.toString();},
  s => {s.value[0].executable = true;}, s => {s.value[0].data[1] = "base64+zstd";},
  s => {const b=bytes(s,0); b[0]^=1; replace(s,0,b);},
  s => {const b=bytes(s,0); b.writeUInt16LE(1,9); replace(s,0,b);},
  s => {const b=bytes(s,0); keys.pool.toBuffer().copy(b,107); replace(s,0,b);},
  s => {const b=bytes(s,0); keys.lp.toBuffer().copy(b,139); replace(s,0,b);},
  s => {replace(s,0,bytes(s,0).subarray(0,246));},
  s => {const b=bytes(s,1); b[45]=0; replace(s,1,b);},
  s => {const b=bytes(s,1); b.writeBigUInt64LE(BigInt(expected.lp_supply)+1n,36); replace(s,1,b);},
  s => {const i=s.value[2]?2:3,b=bytes(s,i);keys.base.toBuffer().copy(b,32);replace(s,i,b);},
  s => {const b=bytes(s,4);b[108]=2;replace(s,4,b);},
  s => {const b=bytes(s,0);signed128(b,245,-(1n<<127n));replace(s,0,b);},
  s => {const b=bytes(s,0);signed128(b,245,1n<<100n);replace(s,0,b);},
  s => {const b=bytes(s,0);b.writeBigUInt64LE((1n<<64n)-1n,271);replace(s,0,b);},
]) {const sample=clone();mutate(sample);assert.throws(() => decodeSnapshot(sample,keys), /invalid_native_accounts/);}

let sample=clone();sample.value[0]=null;
assert.equal(decodeSnapshot(sample,keys).reason,"canonical_pool_absent");
sample=clone();replace(sample,0,bytes(sample,0).subarray(0,243));
assert.equal(decodeSnapshot(sample,keys).signed_virtual_quote_raw,"0");
assert.equal(decodeSnapshot(sample,keys).protocol_fees_raw,"0");
sample=clone();let pool=bytes(sample,0);
pool.writeBigUInt64LE(1000000n,271);pool.writeBigUInt64LE(2000000n,279);signed128(pool,245,-3000000n);replace(sample,0,pool);
let decoded=decodeSnapshot(sample,keys);
assert.equal(decoded.signed_virtual_quote_raw,"-3000000");assert.equal(decoded.boost_reserves_raw,"0");
assert.equal(decoded.real_quote_raw,decoded.effective_quote_raw);
signed128(pool,245,5000000n);replace(sample,0,pool);decoded=decodeSnapshot(sample,keys);
assert.equal(decoded.boost_reserves_raw,"8000000");assert.equal(decoded.status,"observed"); // Boost is never an exemption.
sample=clone();const mint=bytes(sample,1);mint.writeBigUInt64LE(0n,36);replace(sample,1,mint);
assert.equal(decodeSnapshot(sample,keys).lp_circulating_raw,"0");
sample=clone();const extended=Buffer.alloc(170);bytes(sample,1).copy(extended);extended[165]=1;replace(sample,1,extended);
assert.equal(decodeSnapshot(sample,keys).status,"observed");
extended[165]=2;replace(sample,1,extended);assert.throws(() => decodeSnapshot(sample,keys));
sample=clone();const huge=bytes(sample,4);huge.writeBigUInt64LE(9007199254740993n,64);replace(sample,4,huge);
assert.equal(decodeSnapshot(sample,keys).quote_vault_raw,"9007199254740993");

(async () => {
  let requests=0, signal;
  const fetchFn=async (url, options) => {
    requests++;signal=options.signal;assert.equal(options.method,"POST");
    const body=JSON.parse(options.body);assert.equal(body.method,"getMultipleAccounts");
    assert.deepEqual(body.params[0],Array.from(keys.addresses));assert.equal(body.params[1].commitment,"confirmed");
    return {ok:true,json:async()=>({result:clone()})};
  };
  const result=await observeCanonicalLiquidity("https://secret.invalid/key",fixture.base_mint,{fetchFn});
  assert.equal(result.status,"observed");assert.equal(requests,1);assert.equal(signal.aborted,true);
  assert.ok(result.request_started_at<=result.observed_at);assert.equal(result.base_mint,fixture.base_mint);
  assert.ok(!JSON.stringify(result).includes("secret"));
  assert.equal((await observeCanonicalLiquidity("unused",fixture.base_mint,{timeoutMs:0,fetchFn})).reason,"budget_exhausted");
  assert.equal((await observeCanonicalLiquidity("unused",fixture.base_mint,{mayRead:()=>false,fetchFn})).reason,"wallet_trade_active");
  assert.equal(requests,1);
  const failure=await observeCanonicalLiquidity("unused",fixture.base_mint,{fetchFn:async()=>{throw new Error("secret URL");}});
  assert.equal(failure.status,"unmeasured");assert.ok(!JSON.stringify(failure).includes("secret"));
  const timeout=await observeCanonicalLiquidity("unused",fixture.base_mint,{timeoutMs:10,
    fetchFn:async(url,options)=>{signal=options.signal;return new Promise(()=>{});}});
  assert.equal(timeout.reason,"read_timeout");assert.equal(signal.aborted,true);
  const bad=await observeCanonicalLiquidity("unused",fixture.base_mint,{fetchFn:async()=>({ok:true,json:async()=>({result:null})})});
  assert.equal(bad.status,"unmeasured");
  console.log("canonical liquidity native account and bounded read checks passed");
})().catch(error=>{console.error(error);process.exitCode=1;});
