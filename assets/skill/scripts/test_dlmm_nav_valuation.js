// Offline final snapshot regressions: unknown is never zero or invented complete NAV.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {collect,navSpotMark}=require('./dlmm_nav');
const SOL='So11111111111111111111111111111111111111112',mint='test-mint';
const stamp=Math.floor(Date.now()/1000),slot=1000;
const asset=(id= mint,decimals=6)=>({id,decimals,usdPrice:id===SOL?100:2,updatedAt:new Date(stamp*1000).toISOString(),priceBlockId:slot});
const valid=asset();assert.equal(navSpotMark(valid,mint,6,slot,stamp).observed_at,stamp);
for(const change of [{id:'other'},{decimals:9},{usdPrice:NaN},{usdPrice:Infinity},{usdPrice:0},
 {updatedAt:'invalid'},{updatedAt:new Date((stamp+6)*1000).toISOString()},
 {updatedAt:new Date((stamp-601)*1000).toISOString()}, {priceBlockId:slot+1501},
 {priceBlockId:slot-1501},{priceBlockId:1.5}]) assert.equal(navSpotMark({...valid,...change},mint,6,slot,stamp),null);
const root=fs.mkdtempSync(path.join(os.tmpdir(),'nav-valuation-'));
const originalFetch=global.fetch,originalTimer=global.setTimeout,savedHelius=process.env.DLMM_HELIUS_WALLET_PRICES;
global.setTimeout=(fn)=>originalTimer(fn,0);process.env.DLMM_HELIUS_WALLET_PRICES='false';
const connection={getBlockHeight:async()=>1000,getSignaturesForAddress:async()=>[],getSlot:async()=>slot,
 getBalance:async()=>1000000000,getParsedTokenAccountsByOwner:async(_,o)=>({value:o.programId.toString().startsWith('Tokenkeg')?
 [{account:{lamports:2039280,data:{parsed:{info:{mint,tokenAmount:{amount:'1000000',decimals:6}}}}}}]:[]})};
let quotes=0,provided=[asset(),asset(SOL,9)],failure='TOKEN_NOT_TRADABLE';
global.fetch=async(url)=>{
 if(url.includes('/assets/search'))return{ok:true,json:async()=>provided};
 if(url.includes('/portfolio/open'))return{ok:true,json:async()=>({totalPositions:0,pools:[],hasNext:false})};
 if(url.includes('/quote?')){quotes++;return{ok:false,status:400,json:async()=>({errorCode:failure,debug:'PRIVATE_RESPONSE_SHOULD_NEVER_APPEAR'})};}
 throw new Error('Unexpected network path');
};
const snapshot=async(name)=>{
 const dir=path.join(root,name);await collect({dir,wallet:'synthetic-wallet',PublicKey:class{constructor(x){this.x=x}toString(){return this.x}},rpc:fn=>fn(connection),includeRentHistory:false});
 return JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim());
};
(async()=>{
 const good=await snapshot('valid');assert.equal(quotes,0);assert.equal(good.tokens[0].mark_sol,.02);assert.notEqual(good.nav_sol,null);
 assert.equal(good.tokens[0].price_observed_at,stamp);assert.equal(good.tokens[0].price_context_slot,slot);
 assert.equal(good.tokens[0].reference_price_observed_at,stamp);assert.equal(good.tokens[0].reference_price_context_slot,slot);
 assert.deepEqual(good.valuation_coverage.unknown_by_reason,{});
 for(const [label,assets] of [['future-time',[{...asset(),updatedAt:new Date((stamp+60)*1000).toISOString()},asset(SOL,9)]],
  ['near-expiry',[{...asset(),updatedAt:new Date((stamp-520)*1000).toISOString()},asset(SOL,9)]],
  ['future-slot',[{...asset(),priceBlockId:slot+1501},asset(SOL,9)]],['decimal-mismatch',[asset(mint,9),asset(SOL,9)]],
  ['stale-reference',[asset(),{...asset(SOL,9),updatedAt:new Date((stamp-601)*1000).toISOString()}]]]){
  provided=assets;const r=await snapshot(label);assert.equal(r.nav_sol,null);assert.equal(r.tokens[0].mark_sol,null);
  assert.equal(r.tokens[0].mark_error_code,'quote_no_route');assert.equal(r.valuation_coverage.unmeasured,1);
  assert.equal(r.valuation_coverage.unknown_by_reason.quote_no_route,1);assert.equal(r.valuation_coverage.quote_budget_cap,40);
  assert.equal(JSON.stringify(r).includes('PRIVATE_RESPONSE_SHOULD_NEVER_APPEAR'),false);
 }
 provided=[];failure='CANNOT_COMPUTE_OTHER_AMOUNT_THRESHOLD';let r=await snapshot('threshold');assert.equal(r.tokens[0].mark_error_code,'quote_threshold_unavailable');assert.equal(r.nav_sol,null);
 failure='UNTRUSTED_PRIVATE_CODE';r=await snapshot('unknown-error');assert.equal(r.tokens[0].mark_error_code,'price_unavailable');assert.equal(JSON.stringify(r).includes(failure),false);
 assert.equal(quotes,7);console.log('NAV final payload validates both USD legs, preserves unknowns and bounds error diagnostics');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>{global.fetch=originalFetch;global.setTimeout=originalTimer;
 if(savedHelius===undefined)delete process.env.DLMM_HELIUS_WALLET_PRICES;else process.env.DLMM_HELIUS_WALLET_PRICES=savedHelius;fs.rmSync(root,{recursive:true,force:true});});
