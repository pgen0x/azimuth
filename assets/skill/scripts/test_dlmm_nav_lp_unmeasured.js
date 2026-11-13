// Unmeasured LP valuation is stored as null with a reason, never as a hard 0.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {collect}=require('./dlmm_nav');
const slot=1000,stamp=Math.floor(Date.now()/1000);
const root=fs.mkdtempSync(path.join(os.tmpdir(),'nav-lp-'));
const HELIUS='DLMM_HELIUS_WALLET_PRICES';
const originalFetch=global.fetch,originalTimer=global.setTimeout,savedHelius=process['env'][HELIUS];
global.setTimeout=(fn)=>originalTimer(fn,0);process['env'][HELIUS]='false';
const connection={getBlockHeight:async()=>1000,getSignaturesForAddress:async()=>[],getSlot:async()=>slot,
 getBalance:async()=>1000000000,getParsedTokenAccountsByOwner:async()=>({value:[]}),
 getAccountInfo:async()=>({lamports:57000000})};
let portfolio;
global.fetch=async(url)=>{
 if(url.includes('/portfolio/open'))return{ok:true,json:async()=>portfolio};
 throw new Error('Unexpected network path');
};
const pool=(over={})=>({poolAddress:'pool1',balancesSol:'0.3',unclaimedFeesSol:'0.01',updatedAt:stamp,listPositions:['pos1'],...over});
const snapshot=async(name,body)=>{
 portfolio=body;const dir=path.join(root,name);
 await collect({dir,wallet:'synthetic-wallet',PublicKey:class{constructor(x){this.x=x}toString(){return this.x}},rpc:fn=>fn(connection),includeRentHistory:false});
 return JSON.parse(fs.readFileSync(path.join(dir,'dlmm_nav.jsonl'),'utf8').trim().split('\n').pop());
};
(async()=>{
 // Real zero: API answers coherently with no open positions.
 let r=await snapshot('real-zero',{totalPositions:0,pools:[],hasNext:false});
 assert.equal(r.lp_mark_sol,0);assert.equal(r.known_asset_subtotal_sol,1);assert.equal('lp_mark_unmeasured_reason' in r,false);
 // Measured LP stays a number.
 r=await snapshot('measured',{totalPositions:1,pools:[pool()],hasNext:false});
 assert.ok(Math.abs(r.lp_mark_sol-0.31)<1e-9);assert.notEqual(r.known_asset_subtotal_sol,null);
 // Empty/invalid body (no totalPositions, no pools): unmeasured, not 0.
 r=await snapshot('empty-body',{});
 assert.equal(r.lp_mark_sol,null);assert.equal(r.known_asset_subtotal_sol,null);assert.match(r.lp_mark_unmeasured_reason,/lp_read_invalid/);assert.equal(r.nav_sol,null);
 // API says positions exist but the pools list came back empty.
 r=await snapshot('count-mismatch',{totalPositions:2,pools:[],hasNext:false});
 assert.equal(r.lp_mark_sol,null);assert.equal(r.known_asset_subtotal_sol,null);assert.match(r.lp_mark_unmeasured_reason,/lp_count_mismatch/);
 // Stale pool valuation.
 r=await snapshot('stale',{totalPositions:1,pools:[pool({updatedAt:stamp-1000})],hasNext:false});
 assert.equal(r.lp_mark_sol,null);assert.match(r.lp_mark_unmeasured_reason,/stale_or_invalid_lp/);
 // Position count > 0 with value 0.
 r=await snapshot('zero-value',{totalPositions:1,pools:[pool({balancesSol:'0',unclaimedFeesSol:'0'})],hasNext:false});
 assert.equal(r.lp_mark_sol,null);assert.equal(r.known_asset_subtotal_sol,null);assert.match(r.lp_mark_unmeasured_reason,/lp_positions_zero_value/);

 // Coherent zero now, but the previous row held LP value and no close was journaled: unmeasured.
 const seed=(name,rows)=>{const d=path.join(root,name);fs.mkdirSync(d,{recursive:true});
  if(rows.nav)fs.writeFileSync(path.join(d,'dlmm_nav.jsonl'),rows.nav.map(x=>JSON.stringify(x)).join('\n')+'\n');
  if(rows.closes)fs.writeFileSync(path.join(d,'dlmm_closes.jsonl'),rows.closes.map(x=>JSON.stringify(x)).join('\n')+'\n');};
 const prevTs=stamp-60,zero={totalPositions:0,pools:[],hasNext:false};
 seed('vanished',{nav:[{ts:prevTs,lp_mark_sol:0.35}],closes:[{ts:prevTs-100,position:'old'}]});
 r=await snapshot('vanished',zero);
 assert.equal(r.lp_mark_sol,null);assert.equal(r.known_asset_subtotal_sol,null);assert.equal(r.lp_mark_unmeasured_reason,'lp_vanished_without_close');assert.equal(r.nav_sol,null);
 // A close journaled after the previous row explains the zero: real 0.
 seed('closed',{nav:[{ts:prevTs,lp_mark_sol:0.35}],closes:[{ts:prevTs+10,position:'p1',success:true}]});
 r=await snapshot('closed',zero);
 assert.equal(r.lp_mark_sol,0);assert.equal('lp_mark_unmeasured_reason' in r,false);
 // A failed close is not a close.
 seed('failed-close',{nav:[{ts:prevTs,lp_mark_sol:0.35}],closes:[{ts:prevTs+10,position:'p1',success:false}]});
 r=await snapshot('failed-close',zero);
 assert.equal(r.lp_mark_sol,null);assert.equal(r.lp_mark_unmeasured_reason,'lp_vanished_without_close');
 // Previous row had no LP value: real 0 (same as having no previous row).
 seed('prev-zero',{nav:[{ts:prevTs,lp_mark_sol:0}]});
 r=await snapshot('prev-zero',zero);
 assert.equal(r.lp_mark_sol,0);
 console.log('NAV writes null + reason for an unmeasured LP mark and keeps a real zero');
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>{global.fetch=originalFetch;global.setTimeout=originalTimer;
 if(savedHelius===undefined)delete process['env'][HELIUS];else process['env'][HELIUS]=savedHelius;fs.rmSync(root,{recursive:true,force:true});});
