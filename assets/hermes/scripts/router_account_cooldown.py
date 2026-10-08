#!/usr/bin/env python3
"""Version-pinned hotfix for the installed 9router 0.5.95 CLI build.

No credentials, combo changes, or database writes. Back up JS before applying.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

OLD_LOCK = 'function j(a,b){let c=a[i(b)]||a[h];return!!c&&new Date(c).getTime()>Date.now()}'
NEW_LOCK = 'function j(a,b){return[a[i(b)],a[h]].some(c=>c&&new Date(c).getTime()>Date.now())}'
ANCHOR = 'r=function(a,b,c){if("github"'
INSERT_V1 = 'r=function(a,b,c){if("codebuddy-cn"===(0,h.rs)(c)&&((403===Number(a)&&/"code"\\s*:\\s*11140\\b/.test(String(b||"")))||(429===Number(a)&&/"code"\\s*:\\s*14018\\b/.test(String(b||"")))))return Math.max(Date.now()+18e5,Number(k)||0);if("github"'
INSERT = 'r=function(a,b,c){if(["codebuddy-cn","codebuddy-intl"].includes((0,h.rs)(c))&&((403===Number(a)&&/"code"\\s*:\\s*11140\\b/.test(String(b||"")))||(429===Number(a)&&/"code"\\s*:\\s*14018\\b/.test(String(b||"")))))return Math.max(Date.now()+18e5,Number(k)||0);if("antigravity"===(0,h.rs)(c)&&429===Number(a))try{let d=JSON.parse(String(b||"").slice(String(b||"").indexOf("{"))),e=d.error;if("RESOURCE_EXHAUSTED"===e?.status&&Array.isArray(e.details)&&e.details.some(a=>"QUOTA_EXHAUSTED"===a.reason)){let a=e.details.find(a=>"type.googleapis.com/google.rpc.RetryInfo"===a["@type"])?.retryDelay;if("string"==typeof a&&/^\\d+(?:\\.\\d+)?s$/.test(a)){let b=Date.now()+Math.ceil(parseFloat(a)*1e3);Number.isSafeInteger(b)&&Number.isFinite(new Date(b).getTime())&&b>Date.now()&&(k=Math.max(Number(k)||0,b))}}}catch{};if("github"'

# Gemini daily quota is model-scoped. Honor its structured reset without the
# generic 30-minute cap; per-minute throttling keeps the existing policy.
INSERT_V2 = INSERT
GEMINI_DAILY = r'if("gemini"===(0,h.rs)(c)&&429===Number(a))try{let d=JSON.parse(String(b||"").slice(String(b||"").indexOf("{"))),e=d.error;if("RESOURCE_EXHAUSTED"===e?.status&&Array.isArray(e.details)&&e.details.some(a=>"type.googleapis.com/google.rpc.QuotaFailure"===a["@type"]&&Array.isArray(a.violations)&&a.violations.some(a=>"string"==typeof a.quotaId&&/PerDay(?:-|$|Per)/.test(a.quotaId)))){let a=e.details.find(a=>"type.googleapis.com/google.rpc.RetryInfo"===a["@type"])?.retryDelay;if("string"==typeof a&&/^\d+(?:\.\d+)?s$/.test(a)){let b=Date.now()+Math.ceil(parseFloat(a)*1e3);Number.isSafeInteger(b)&&Number.isFinite(new Date(b).getTime())&&b>Date.now()&&(k=Math.max(Number(k)||0,b),Q=!0)}}}catch{};'
INSERT_V3 = INSERT_V2.replace('if("github"', GEMINI_DAILY + 'if("github"')
# Account-wide budget failures cannot recover on another model. xAI retries
# after the existing 30-minute restriction interval; Cloudflare resets at UTC midnight.
ACCOUNT_BUDGET = r'if(("xai"===(0,h.rs)(c)&&402===Number(a))||("cloudflare-ai"===(0,h.rs)(c)&&429===Number(a)))try{let d=JSON.parse(String(b||"").slice(String(b||"").indexOf("{")));if("xai"===(0,h.rs)(c)&&"personal-team-blocked:spending-limit"===d.code)return Math.max(Date.now()+18e5,Number(k)||0);if("cloudflare-ai"===(0,h.rs)(c)&&!1===d.success&&Array.isArray(d.errors)&&d.errors.some(a=>4006===a.code&&"string"==typeof a.message&&/used up your daily free allocation/i.test(a.message)))return Math.max((Math.floor(Date.now()/864e5)+1)*864e5,Number(k)||0)}catch{};'
INSERT = INSERT_V3.replace('if("github"', ACCOUNT_BUDGET + 'if("github"')
# A definite model retirement cannot recover in the generic two-minute retry.
# Keep this connection/model scoped; other models and combo order still work.
INSERT_V4 = INSERT
GEMINI_RETIRED = r'if("gemini"===(0,h.rs)(c)&&404===Number(a)&&"string"==typeof i&&i)try{let d=JSON.parse(String(b||"").slice(String(b||"").indexOf("{"))),e=d.error;404===e?.code&&"NOT_FOUND"===e.status&&"string"==typeof e.message&&e.message.includes("models/"+i+" is no longer available to new users.")&&(k=Math.max(Date.now()+18e5,Number(k)||0))}catch{};'
INSERT = INSERT_V4.replace('if("github"', GEMINI_RETIRED + 'if("github"')
INSERT_V5 = INSERT
AG_RETIRED = r'if("antigravity"===(0,h.rs)(c)&&404===Number(a)&&"string"==typeof i&&i)try{let d=JSON.parse(String(b||"").slice(String(b||"").indexOf("{"))),e=d.error;404===e?.code&&"NOT_FOUND"===e.status&&"MODEL_RETIRED"===e.reason&&e.model===i&&(k=Math.max(Date.now()+18e5,Number(k)||0))}catch{};'
INSERT = INSERT_V5.replace('if("github"', AG_RETIRED + 'if("github"')
INSERT_V6 = INSERT
OR_UNAVAILABLE = r'if("openrouter"===(0,h.rs)(c)&&404===Number(a)&&"string"==typeof i&&i.endsWith(":free"))try{let d=JSON.parse(String(b||"").slice(String(b||"").indexOf("{"))),e=d.error;404===e?.code&&e.message==="This model is unavailable for free. The paid version is available now - use this slug instead: "+i.slice(0,-5)&&(k=Math.max(Date.now()+18e5,Number(k)||0))}catch{};'
INSERT = INSERT_V6.replace('if("github"', OR_UNAVAILABLE + 'if("github"')

# OpenCode has no connection row: consult the same module's cache before HTTP.
# ponytail: public model locks reset on restart; revisit if 9router adds durable no-auth locks.
OLD_AUTH = 'let k=Promise.resolve();async function l('
NEW_AUTH = 'let k=Promise.resolve(),U=new Map;async function l('
OLD_PUBLIC = 'let g=(0,h.rs)(a);if(h.IS[g]?.noAuth){'
NEW_PUBLIC = '''let g=(0,h.rs)(a);
if(h.IS[g]?.noAuth&&"opencode"===g){
 const lock=U.get(c);
 if(lock&&lock.until>Date.now()){
  const retryAfter=new Date(lock.until).toISOString();
  return{allRateLimited:!0,retryAfter,retryAfterHuman:(0,f.Qo)(retryAfter),lastError:lock.error,lastErrorCode:401};
 }
 U.delete(c);
}
if(h.IS[g]?.noAuth){'''
OLD_PUBLIC_MARK = 'if(!a||"noauth"===a)return{shouldFallback:!1,cooldownMs:0};'
NEW_PUBLIC_MARK = '''if(!a||"noauth"===a){
 if("opencode"===(0,h.rs)(e)&&401===Number(b)&&"string"==typeof i&&i)try{
  const body=JSON.parse(String(c||"").slice(String(c||"").indexOf("{")));
  if(body.type==="error"&&body.error?.type==="ModelError"&&body.error.message==="Model "+i+" is not supported"){
   for(const [model,lock]of U)if(lock.until<=Date.now())U.delete(model);
   if(U.size>=256&&!U.has(i))U.delete(U.keys().next().value);
   U.set(i,{until:Date.now()+18e5,error:body.error.message});
  }
 }catch{}
 return{shouldFallback:!1,cooldownMs:0};
}'''
OLD_SCOPE = 'async function m(a,b,c,e=null,i=null,k=null){let l,n,o;'
NEW_SCOPE = OLD_SCOPE + 'let Q=!1;'
OLD_CAP = 'n="antigravity"===(0,h.rs)(e)?k-Date.now():Math.min(k-Date.now(),g.fh)'
NEW_CAP = OLD_CAP.replace('n=', 'n=Q||')

# A cached Antigravity reset must also reach the existing durable model lock.
OLD_FALLBACK = '"antigravity"===y&&A||(await (0,f.vk)(b.connectionId,x.status,x.error,y,z,G)).shouldFallback'
NEW_FALLBACK = '(await (0,f.vk)(b.connectionId,x.status,x.error,y,z,G)).shouldFallback'

# Exhausted weekly quota cannot recover during the current HTTP retry loop.
OLD_RETRY = 'async computeRetryDelay(a,b){let c="",d=null,e=this.parseRetryHeaders(a.headers);try{d=(c=await a.clone().text())?JSON.parse(c):null}catch{}let f=this.extractErrorMessage(d,c);return(e||(e=this.parseRetryFromErrorMessage(f)),e)?e<=1e4&&e:!!this.isTransientAntigravityError(a.status,f)&&Math.min(1e3*2**b,a.status===i.gx.RATE_LIMITED?1e4:15e3)}'
NEW_RETRY = OLD_RETRY.replace("catch{}let f=", "catch{}" + 'if(429===a.status&&"RESOURCE_EXHAUSTED"===d?.error?.status&&Array.isArray(d.error.details)&&d.error.details.some(a=>"QUOTA_EXHAUSTED"===a.reason))return!1;' + "let f=")

# Normalize the observed HTTP-200 retirement notice before ChatCore can mark
# success. Peek a bounded prefix, preserving every byte on ordinary responses.
AG_CLASS = 'class x extends f.H{constructor(){super("antigravity",g.xq.antigravity)}'
AG_EXECUTE = r'''async execute(args) {
 const result = await super.execute(args), response = result.response;
 const type = response.headers.get("content-type") || "";
 if (!response.ok || !response.body || !/^gemini-[\d.]+-flash(?:-agent)?$/.test(args.model || "") ||
     !/application\/json|text\/event-stream/.test(type)) return result;
 const reader = response.body.getReader(), saved = [], decoder = new TextDecoder();
 const sse = type.includes("text/event-stream");
 let text = "", size = 0, ended = false, notice = false, complete = false;
 const observed = "Gemini 3.5 Flash is no longer available. Please switch to Gemini 3.7 Flash in the latest version of Antigravity.";
 const inspect = data => {
  const body = data?.response, candidates = body?.candidates;
  if (!Array.isArray(candidates) || !candidates.length) return;
  const parts = candidates[0]?.content?.parts;
  if (!Array.isArray(parts) || !parts.length) { complete = !!(body.usageMetadata || candidates[0].finishReason); return; }
  complete = true;
  notice = candidates.length === 1 && !body.usageMetadata && !candidates[0].finishReason &&
   Array.isArray(parts) && parts.length === 1 && Object.keys(parts[0]).length === 1 && parts[0].text === observed;
 };
 try {
  // ponytail: inspect at most 8 KiB; audit a new provider envelope if this notice changes.
  while (!complete && size < 8192 && !ended) {
   const item = await reader.read(); ended = item.done;
   if (item.value) { saved.push(item.value); size += item.value.byteLength; }
   if (size > 8192) break;
   if (item.value) text += decoder.decode(item.value, {stream: true});
   if (ended) text += decoder.decode();
   if (sse) {
    const frames = text.split(/\r?\n\r?\n/); text = frames.pop();
    if (ended && text.trim()) { frames.push(text); text = ""; }
    for (const frame of frames) {
     const data = frame.split(/\r?\n/).filter(line => line.startsWith("data:")).map(line => line.slice(5).trimStart()).join("\n");
     if (!data || data === "[DONE]") continue;
     try { inspect(JSON.parse(data)); } catch { complete = true; }
     if (complete) break;
    }
   } else {
    try { inspect(JSON.parse(text)); complete = true; } catch { if (ended) complete = true; }
   }
  }
 } catch (error) { reader.cancel().catch(() => {}); throw error; }
 if (notice) {
  await reader.cancel().catch(() => {});
  result.response = new Response(JSON.stringify({error: {code: 404, status: "NOT_FOUND", reason: "MODEL_RETIRED",
   model: args.model, message: "Antigravity returned a model retirement notice."}}),
   {status: 404, headers: {"Content-Type": "application/json"}});
 } else {
  let index = 0;
  result.response = new Response(new ReadableStream({
   async pull(controller) {
    if (index < saved.length) { controller.enqueue(saved[index++]); return; }
    if (ended) { controller.close(); return; }
    try { const item = await reader.read(); if (item.done) controller.close(); else controller.enqueue(item.value); }
    catch (error) { controller.error(error); }
   }, cancel(reason) { return reader.cancel(reason); }
  }), {status: response.status, statusText: response.statusText, headers: response.headers});
 }
 return result;
}'''
AG_PATCHED_CLASS = AG_CLASS + AG_EXECUTE

def changes(app):
    if json.loads((app.parent / "package.json").read_text()).get("version") != "0.5.95":
        raise ValueError("Unsupported 9router version; audit upstream before applying")
    root = app / ".next-cli-build/server"
    patches = []
    readers = writers = fallbacks = retries = executors = auth = public = public_mark = 0
    for path in root.rglob("*.js"):
        original = path.read_text()
        readers += original.count(OLD_LOCK) + original.count(NEW_LOCK)
        writers += original.count(ANCHOR) + original.count(INSERT_V1) + original.count(INSERT_V2) + original.count(INSERT_V3) + original.count(INSERT_V4) + original.count(INSERT_V5) + original.count(INSERT_V6) + original.count(INSERT)
        fallbacks += original.count(OLD_FALLBACK) + (0 if OLD_FALLBACK in original else original.count(NEW_FALLBACK))
        retries += original.count(OLD_RETRY) + original.count(NEW_RETRY)
        executors += original.count(AG_CLASS)
        auth += original.count(OLD_AUTH) + original.count(NEW_AUTH)
        public += original.count(OLD_PUBLIC) + original.count(NEW_PUBLIC)
        public_mark += original.count(OLD_PUBLIC_MARK) + original.count(NEW_PUBLIC_MARK)
        updated = original.replace(OLD_LOCK, NEW_LOCK).replace(INSERT_V6, INSERT).replace(INSERT_V5, INSERT).replace(INSERT_V4, INSERT).replace(INSERT_V3, INSERT).replace(INSERT_V2, INSERT).replace(INSERT_V1, INSERT).replace(ANCHOR, INSERT).replace(NEW_SCOPE, OLD_SCOPE).replace(OLD_SCOPE, NEW_SCOPE).replace(OLD_CAP, NEW_CAP).replace(OLD_FALLBACK, NEW_FALLBACK).replace(OLD_RETRY, NEW_RETRY).replace(AG_PATCHED_CLASS, AG_CLASS).replace(AG_CLASS, AG_PATCHED_CLASS).replace(NEW_AUTH, OLD_AUTH).replace(OLD_AUTH, NEW_AUTH).replace(NEW_PUBLIC, OLD_PUBLIC).replace(OLD_PUBLIC, NEW_PUBLIC).replace(NEW_PUBLIC_MARK, OLD_PUBLIC_MARK).replace(OLD_PUBLIC_MARK, NEW_PUBLIC_MARK)
        if original != updated:
            patches.append((path, original, updated))
    if (readers, writers, fallbacks, retries, executors, auth, public, public_mark) != (9, 1, 1, 1, 1, 1, 1, 1):
        raise ValueError(f"Build shape changed: {readers} lock readers, {writers} account writer, {fallbacks} chat fallback, {retries} AG retry, {executors} AG executor, {auth} auth module, {public} public selector, {public_mark} public writer")
    return patches


def check(app, patched=False):
    patches = changes(app)
    if patched and patches:
        raise ValueError("Installed build is not fully patched")
    # Exercise real functions extracted from every installed copy, without requests.
    for path in (app / ".next-cli-build/server").rglob("*.js"):
        source = path.read_text().replace(OLD_LOCK, NEW_LOCK).replace(INSERT_V6, INSERT).replace(INSERT_V5, INSERT).replace(INSERT_V4, INSERT).replace(INSERT_V3, INSERT).replace(INSERT_V2, INSERT).replace(INSERT_V1, INSERT).replace(ANCHOR, INSERT).replace(NEW_SCOPE, OLD_SCOPE).replace(OLD_SCOPE, NEW_SCOPE).replace(OLD_CAP, NEW_CAP).replace(OLD_FALLBACK, NEW_FALLBACK).replace(OLD_RETRY, NEW_RETRY).replace(AG_PATCHED_CLASS, AG_CLASS).replace(AG_CLASS, AG_PATCHED_CLASS).replace(NEW_AUTH, OLD_AUTH).replace(OLD_AUTH, NEW_AUTH).replace(NEW_PUBLIC, OLD_PUBLIC).replace(OLD_PUBLIC, NEW_PUBLIC).replace(NEW_PUBLIC_MARK, OLD_PUBLIC_MARK).replace(OLD_PUBLIC_MARK, NEW_PUBLIC_MARK)
        if NEW_LOCK in source:
            harness = """const assert=require('node:assert/strict'),vm=require('node:vm');
const lock=vm.runInNewContext('('+process.argv[1]+')',{i:m=>'modelLock_'+m,h:'modelLock___all'});
const future=new Date(Date.now()+60000).toISOString(),past=new Date(Date.now()-60000).toISOString();
assert(lock({modelLock_m:past,modelLock___all:future},'m'));
assert(lock({modelLock_m:future,modelLock___all:past},'m'));
assert(lock({modelLock_m:'invalid',modelLock___all:future},'m'));
assert(!lock({modelLock_m:past,modelLock___all:past},'m'));
assert(!lock({},'m'));
"""
            subprocess.run(["node", "-e", harness, NEW_LOCK], check=True)
        if INSERT in source:
            start = source.index("async function m(a,b,c,e=null,i=null,k=null){")
            end = source.index("async function n(a,b,c=null){", start)
            harness = """const assert=require('node:assert/strict'),vm=require('node:vm');
let update,clock=null;
class Clock extends Date{static now(){return clock??Date.now()}}
const mark=vm.runInNewContext('('+process.argv[1]+')',{
d:{getProviderConnections:async()=>[{id:'conn',backoffLevel:0}],updateProviderConnection:async(id,value)=>{update=value}},
Date:Clock,U:new Map,
f:{hk:()=>({shouldFallback:true,cooldownMs:30000}),S5:(model,ms)=>({[model?'modelLock_'+model:'modelLock___all']:new Date(Clock.now()+ms).toISOString()})},
h:{rs:p=>p},g:{fh:1800000},j:{warn:()=>{}},console:{error:()=>{}}});
(async()=>{
 for(const [status,error,provider,global] of [
 [403,'{"code":11140,"msg":"restricted"}','codebuddy-cn',true],
 [429,'{"error":{"data":{"code":14018}}}','codebuddy-cn',true],
 [429,'{"error":{"data":{"code":14018}}}','codebuddy-intl',true],
 [403,'{"code":111400}','codebuddy-cn',false],
 [429,'temporary rate limit','codebuddy-cn',false],
 [403,'{"code":11140}','other-provider',false],
 [400,'{"code":11102}','codebuddy-cn',false]]){
 const before=Date.now();await mark('conn',status,error,provider,'model');
 assert.equal(Object.hasOwn(update,'modelLock___all'),global);
 if(global)assert(Date.parse(update.modelLock___all)>=before+1800000);
 }
 const spending=JSON.stringify({code:'personal-team-blocked:spending-limit',error:'budget depleted'});
 const cf=JSON.stringify({success:false,errors:[{code:4006,message:'AiError: you have used up your daily free allocation of 10,000 neurons'}]});
 for(const stamp of ['2026-10-07T15:00:00Z','2026-10-07T23:59:59.999Z','2026-10-08T00:00:00Z']){
 clock=Date.parse(stamp);
 await mark('conn',402,'[402]: '+spending,'xai','model');
 assert.equal(Date.parse(update.modelLock___all),clock+1800000);
 await mark('conn',402,spending,'xai','model',clock+3600000);
 assert.equal(Date.parse(update.modelLock___all),clock+3600000);
 await mark('conn',429,cf,'cloudflare-ai','model');
 assert.equal(Date.parse(update.modelLock___all),(Math.floor(clock/86400000)+1)*86400000);
 const later=(Math.floor(clock/86400000)+2)*86400000;
 await mark('conn',429,cf,'cloudflare-ai','model',later);
 assert.equal(Date.parse(update.modelLock___all),later);
 }
 clock=null;
 for(const [status,error,provider] of [
 [429,spending,'xai'],[402,spending,'other'],[402,'{"code":"other"}','xai'],
 [402,'broken {','xai'],[402,'{"error":{"code":"personal-team-blocked:spending-limit"}}','xai'],
 [503,cf,'cloudflare-ai'],[429,cf,'other'],
 [429,'{"success":false,"errors":[{"code":4006,"message":"temporary rate limit"}]}','cloudflare-ai'],
 [429,'{"success":false,"errors":[{"code":4007,"message":"used up your daily free allocation"}]}','cloudflare-ai'],
 [429,'{"success":true,"errors":[{"code":4006,"message":"used up your daily free allocation"}]}','cloudflare-ai'],
 [429,'{"success":false,"errors":null}','cloudflare-ai'],[429,'broken {','cloudflare-ai']]){
 await mark('conn',status,error,provider,'model');
 assert(!Object.hasOwn(update,'modelLock___all'));
 assert(Date.parse(update.modelLock_model)<Date.now()+60000);
 }
 const quota=JSON.stringify({error:{status:'RESOURCE_EXHAUSTED',details:[
 {reason:'QUOTA_EXHAUSTED'}, {'@type':'type.googleapis.com/google.rpc.RetryInfo',retryDelay:'580382.606185709s'}]}});
 const quotaStart=Date.now();await mark('conn',429,'[429]: '+quota,'antigravity','model');
 assert(!Object.hasOwn(update,'modelLock___all'));
 assert(Date.parse(update.modelLock_model)>=quotaStart+580382606);
 for(const delay of ['bad','1e100s','0s','999999999999999999999s']){
 const invalid=JSON.stringify({error:{status:'RESOURCE_EXHAUSTED',details:[
 {reason:'QUOTA_EXHAUSTED'}, {'@type':'type.googleapis.com/google.rpc.RetryInfo',retryDelay:delay}]}});
 await mark('conn',429,invalid,'antigravity','model');
 assert(Number.isFinite(Date.parse(update.modelLock_model)));
 }
 const daily=(id,delay)=>JSON.stringify({error:{status:'RESOURCE_EXHAUSTED',details:[
 {'@type':'type.googleapis.com/google.rpc.QuotaFailure',violations:[{quotaId:id}]},
 {'@type':'type.googleapis.com/google.rpc.RetryInfo',retryDelay:delay}]}});
 for(const id of ['GenerateRequestsPerDayPerProjectPerModel-FreeTier','GenerateContentInputTokensPerModelPerDay-FreeTier']){
 const before=Date.now();await mark('conn',429,'[429]: '+daily(id,'30737.25s'),'gemini','model');
 assert(!Object.hasOwn(update,'modelLock___all'));
 assert(Date.parse(update.modelLock_model)>=before+30737250);
 }
 for(const [provider,id,delay] of [
 ['gemini','GenerateRequestsPerMinutePerProjectPerModel-FreeTier','30737s'],
 ['other','GenerateRequestsPerDayPerProjectPerModel-FreeTier','30737s'],
 ['gemini','GenerateRequestsPerDayPerProjectPerModel-FreeTier','0s'],
 ['gemini','GenerateRequestsPerDayPerProjectPerModel-FreeTier','bad'],
 ['gemini','GenerateRequestsPerDayPerProjectPerModel-FreeTier','999999999999999999s']]){
 await mark('conn',429,daily(id,delay),provider,'model');
 assert(Date.parse(update.modelLock_model)<Date.now()+60000);
 }
 const laterReset=Date.now()+86400000;
 await mark('conn',429,daily('GenerateRequestsPerDayPerProjectPerModel-FreeTier','30737s'),'gemini','model',laterReset);
 assert(Date.parse(update.modelLock_model)>=laterReset);
 const retired=(model='gemini-2.5-pro',code=404,status='NOT_FOUND',message=null)=>JSON.stringify({error:{code,status,
 message:message??`This model models/${model} is no longer available to new users. Please update your code.`}});
 const retiredStart=Date.now();
 await mark('conn',404,retired(),'gemini','gemini-2.5-pro');
 assert(!Object.hasOwn(update,'modelLock___all'));
 assert(Date.parse(update['modelLock_gemini-2.5-pro'])>=retiredStart+1800000);
 const retiredLater=Date.now()+3600000;
 await mark('conn',404,'[404]: '+retired(),'gemini','gemini-2.5-pro',retiredLater);
 assert(!Object.hasOwn(update,'modelLock___all'));
 // The existing Gemini cap stays 30 minutes; daily-quota resets above bypass it.
 assert(Date.parse(update['modelLock_gemini-2.5-pro'])>=Date.now()+1799990);
 assert(Date.parse(update['modelLock_gemini-2.5-pro'])<retiredLater);
 for(const [http,error,provider,model] of [
 [404,retired(),'other','gemini-2.5-pro'],[429,retired(),'gemini','gemini-2.5-pro'],
 [404,retired('other-model'),'gemini','gemini-2.5-pro'],
 [404,retired('gemini-2.5-pro',403),'gemini','gemini-2.5-pro'],
 [404,retired('gemini-2.5-pro',404,'OTHER'),'gemini','gemini-2.5-pro'],
 [404,retired('gemini-2.5-pro',404,'NOT_FOUND','Model not found'),'gemini','gemini-2.5-pro'],
 [404,'broken {','gemini','gemini-2.5-pro'],
 [404,retired(),'gemini',null]]){
 await mark('conn',http,error,provider,model);
 if(model)assert(!Object.hasOwn(update,'modelLock___all'));
 const key=model?'modelLock_'+model:'modelLock___all';
 assert(Date.parse(update[key])<Date.now()+60000);
 }
 const retry=Date.now()+3600000;
 const retiredAG=JSON.stringify({error:{code:404,status:'NOT_FOUND',reason:'MODEL_RETIRED',model:'gemini-3-flash-agent'}});
 const agStart=Date.now();await mark('conn',404,'[404]: '+retiredAG,'antigravity','gemini-3-flash-agent');
 assert(!Object.hasOwn(update,'modelLock___all'));
 assert(Date.parse(update['modelLock_gemini-3-flash-agent'])>=agStart+1800000);
 for(const [status,error,provider,model] of [
 [503,retiredAG,'antigravity','gemini-3-flash-agent'],[404,retiredAG,'other','gemini-3-flash-agent'],
 [404,retiredAG,'antigravity','other-model'],[404,retiredAG.replace('MODEL_RETIRED','OTHER'),'antigravity','gemini-3-flash-agent'],
 [404,'broken {','antigravity','gemini-3-flash-agent']]){
 await mark('conn',status,error,provider,model);
 assert(!Object.hasOwn(update,'modelLock___all'));
 assert(Date.parse(update['modelLock_'+model])<Date.now()+60000);
 }
 const freeModel='z-ai/glm-5.2:free';
 const unavailable=(slug='z-ai/glm-5.2',code=404)=>JSON.stringify({error:{code,
  message:'This model is unavailable for free. The paid version is available now - use this slug instead: '+slug}});
 for(const prefix of ['', '[404]: ']){
  const before=Date.now();await mark('conn',404,prefix+unavailable(),'openrouter',freeModel);
  assert(!Object.hasOwn(update,'modelLock___all'));
  assert(Date.parse(update['modelLock_'+freeModel])>=before+1800000);
 }
 for(const [http,error,provider,model] of [
  [401,unavailable(),'openrouter',freeModel],[404,unavailable(),'other',freeModel],
  [404,unavailable('other-model'),'openrouter',freeModel],[404,unavailable('z-ai/glm-5.2',403),'openrouter',freeModel],
  [404,unavailable(),'openrouter','z-ai/glm-5.2'],[404,'broken {','openrouter',freeModel],
  [404,'{"error":{"code":404,"message":"Model not found"}}','openrouter',freeModel]]){
  await mark('conn',http,error,provider,model);
  assert(!Object.hasOwn(update,'modelLock___all'));
  assert(Date.parse(update['modelLock_'+model])<Date.now()+60000);
 }
 await mark('conn',429,'{"code":14018}','codebuddy-cn','model',retry);
 assert(Date.parse(update.modelLock___all)>=retry);
 await mark('conn',402,"you've reached your additional usage limit for your plan",'github','model');
 assert(Object.hasOwn(update,'modelLock___all'));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
            subprocess.run(["node", "-e", harness, source[start:end]], check=True)
        if NEW_AUTH in source:
            start = source.index(NEW_AUTH)
            end = source.index('async function n(a,b,c=null){', start)
            harness = r'''const assert=require('node:assert/strict'),vm=require('node:vm');
let clock=Date.now(),writes=0,settings=0;
class Clock extends Date{static now(){return clock}}
const {select,mark,locks}=vm.runInNewContext(process.argv[1]+';({select:l,mark:m,locks:U})',{
 Date:Clock,
 d:{mt:async()=>{settings++;return{}},getProviderConnections:async()=>[{id:'conn',backoffLevel:0}],
  updateProviderConnection:async()=>{writes++}},
 e:{B:async()=>({}),p:()=>null},h:{rs:p=>p==='oc'?'opencode':p,IS:{opencode:{noAuth:true},publicOther:{noAuth:true}}},
 f:{Qo:()=> '30 minutes',Bl:()=>false,hk:()=>({shouldFallback:true,cooldownMs:30000}),
  S5:(model,ms)=>({['modelLock_'+model]:new Date(clock+ms).toISOString()})},
 g:{fh:1800000},j:{warn:()=>{},debug:()=>{}},console:{error:()=>{}}});
const model='deepseek-v4-flash-free';
const unsupported=(selected=model,type='ModelError')=>JSON.stringify({type:'error',error:{type,message:'Model '+selected+' is not supported'}});
(async()=>{
 assert.equal((await select('oc',null,model)).id,'noauth');
 // The first error exits this account attempt, preventing a no-auth retry loop.
 assert.equal((await mark(null,401,'[401]: '+unsupported(),'oc',model)).shouldFallback,false);
 const calls=settings,blocked=await select('opencode',null,model);
 assert.equal(blocked.allRateLimited,true);assert.equal(blocked.lastErrorCode,401);
 assert.equal(Date.parse(blocked.retryAfter),clock+1800000);assert.equal(settings,calls);assert.equal(writes,0);
 assert.equal((await select('opencode',null,'another-model')).id,'noauth');
 assert.equal((await select('publicOther',null,model)).id,'noauth');
 clock+=1800000;assert.equal((await select('opencode',null,model)).id,'noauth');assert.equal(locks.size,0);
 for(const [id,status,error,provider,selected] of [
  [null,403,unsupported(),'opencode',model],[null,401,unsupported(),'publicOther',model],
  [null,401,unsupported('other-model'),'opencode',model],[null,401,unsupported(model,'AuthError'),'opencode',model],
  [null,401,'broken {','opencode',model],[null,401,'Model '+model+' is not supported','opencode',model],
  [null,401,unsupported(),'opencode',null],['conn',401,unsupported(),'opencode',model]]){
  await mark(id,status,error,provider,selected);
  assert.equal(locks.size,0);assert.equal((await select('opencode',null,model)).id,'noauth');
 }
 await mark('noauth',401,unsupported(),'opencode',model);assert.equal(locks.size,1);
 // Concurrent auth selection shares the cached lock; it does not change credentials.
 const results=await Promise.all(Array.from({length:5},()=>select('opencode',null,model)));
 assert(results.every(a=>a.allRateLimited));
 locks.clear();locks.set('expired',{until:clock-1});
 for(let i=0;i<256;i++)locks.set('other-'+i,{until:clock+1800000});
 await mark(null,401,unsupported(),'opencode',model);
 assert(!locks.has('expired'));assert.equal(locks.size,256);assert(locks.has(model));
 assert.equal(writes,1); // Only the ordinary credentialed error above writes an account.
 console.log('Public model cache, expiry, scoping, bounded storage and fallback checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
            subprocess.run(["node", "-e", harness, source[start:end]], check=True)
        if NEW_FALLBACK in source:
            harness = """const assert=require('node:assert/strict'),vm=require('node:vm');
let calls=[];
const fallback=vm.runInNewContext('(async(x,y,z,G,b,A)=>'+process.argv[1]+')',{
f:{vk:async(...args)=>{calls.push(args);return {shouldFallback:true}}}});
(async()=>{
 const reset=Date.now()+86400000;
 assert(await fallback({status:429,error:'quota'},'antigravity','model',reset,{connectionId:'conn'},reset));
 assert.equal(calls.length,1);assert.equal(calls[0][5],reset);
 assert.equal(calls[0][4],'model');
 assert(await fallback({status:503,error:'upstream'},'other','model',null,{connectionId:'conn'},null));
 assert.equal(calls.length,2);
})().catch(e=>{console.error(e);process.exitCode=1});
"""
            subprocess.run(["node", "-e", harness, NEW_FALLBACK], check=True)
        if NEW_RETRY in source:
            harness = """const assert=require('node:assert/strict'),vm=require('node:vm');
const retry=vm.runInNewContext('({'+process.argv[1]+'}).computeRetryDelay',{i:{gx:{RATE_LIMITED:429}}});
const ctx={parseRetryHeaders:()=>null,parseRetryFromErrorMessage:()=>null,
 extractErrorMessage:(d,c)=>d?.error?.message||c,isTransientAntigravityError:s=>s===429||s===503};
const response=(status,body)=>({status,headers:{},clone:()=>({text:async()=>JSON.stringify(body)})});
(async()=>{
 const exhausted={error:{status:'RESOURCE_EXHAUSTED',details:[{reason:'QUOTA_EXHAUSTED'}]}};
 assert.equal(await retry.call(ctx,response(429,exhausted),1),false);
 assert.equal(await retry.call(ctx,response(429,{error:{status:'RESOURCE_EXHAUSTED',details:[{reason:'RATE_LIMIT_EXCEEDED'}]}}),1),2000);
 assert.equal(await retry.call(ctx,response(503,{error:{message:'capacity'}}),1),2000);
 assert.equal(await retry.call(ctx,response(429,{error:{details:null}}),1),2000);
 ctx.parseRetryHeaders=()=>20000;
 assert.equal(await retry.call(ctx,response(429,{error:{message:'temporary'}}),1),false);
})().catch(e=>{console.error(e);process.exitCode=1});
"""
            subprocess.run(["node", "-e", harness, NEW_RETRY], check=True)
        if AG_PATCHED_CLASS in source:
            harness = r'''const assert=require('node:assert/strict'),vm=require('node:vm');
let supplied,reads=0,cancelled=0;
class Base {async execute(){return {response:supplied,url:'fixture',headers:{},transformedBody:{fixture:true}}}}
const Executor=vm.runInNewContext('(class extends Base{'+process.argv[1]+'})',
 {Base,Response,ReadableStream,TextDecoder});
const executor=new Executor(),encoder=new TextEncoder();
const model='gemini-3-flash-agent',notice='Gemini 3.5 Flash is no longer available. Please switch to Gemini 3.7 Flash in the latest version of Antigravity.';
const payload=text=>({response:{candidates:[{content:{parts:[{text}]}}]}});
const frame=data=>'data: '+JSON.stringify(data)+'\r\n\r\n';
function fixture(text,type='application/json',fragment=1,status=200){
 const bytes=encoder.encode(text);let offset=0;
 return new Response(new ReadableStream({pull(c){reads++;if(offset>=bytes.length){c.close();return}
 c.enqueue(bytes.slice(offset,offset+fragment));offset+=fragment},cancel(){cancelled++}}),
 {status,headers:{'Content-Type':type,'X-Fixture':'preserved'}});
}
async function run(text,type,fragment=1,selected=model,status=200){
 supplied=fixture(text,type,fragment,status);return executor.execute({model:selected,stream:type==='text/event-stream'});
}
(async()=>{
 for(const [text,type] of [
 [JSON.stringify(payload(notice)),'application/json'],[frame(payload(notice)),'text/event-stream'],
 [': heartbeat\r\n\r\n'+frame({response:{candidates:[{content:{parts:[]}}]}})+frame(payload(notice)),'text/event-stream']]){
 const result=await run(text,type);assert.equal(result.response.status,404);
 const error=(await result.response.json()).error;assert.equal(error.reason,'MODEL_RETIRED');assert.equal(error.model,model);
 assert.equal(result.url,'fixture');assert.equal(result.transformedBody.fixture,true);
 }
 const usage=payload(notice);usage.response.usageMetadata={totalTokenCount:10};
 const finish=payload(notice);finish.response.candidates[0].finishReason='STOP';
 const tool=payload(notice);tool.response.candidates[0].content.parts.push({functionCall:{name:'health_check'}});
 const multiple=payload(notice);multiple.response.candidates.push(payload('other').response.candidates[0]);
 for(const body of [payload('normal 🦀 output'),usage,finish,tool,multiple,payload(notice+' quoted')]){
 for(const type of ['application/json','text/event-stream']){
 const text=type==='application/json'?JSON.stringify(body):frame(body)+'data: [DONE]\r\n\r\n';
 const result=await run(text,type);assert.equal(result.response.status,200);
 assert.equal(result.response.headers.get('X-Fixture'),'preserved');assert.equal(await result.response.text(),text);
 }}
 for(const [text,type,fragment,selected,status] of [
 [JSON.stringify(payload(notice)),'application/json',1,'claude-sonnet-4-6',200],
 ['broken {','application/json',1,model,200],['data: broken {\n\n','text/event-stream',1,model,200],
 [JSON.stringify(payload('x'.repeat(10000))),'application/json',257,model,200],
 [frame(payload('normal'))+frame(payload(notice)),'text/event-stream',4096,model,200],
 [JSON.stringify(payload(notice)),'application/json',4096,model,503]]){
 const result=await run(text,type,fragment,selected,status);assert.equal(result.response.status,status);
 assert.equal(await result.response.text(),text);
 }
 supplied=fixture(frame(payload('normal'))+'data: '+ 'x'.repeat(20000),'text/event-stream',5);
 const result=await executor.execute({model});await result.response.body.cancel('stop');assert(cancelled>0);
 supplied=new Response(new ReadableStream({pull(c){c.error(Error('fixture aborted'))}}),{headers:{'Content-Type':'application/json'}});
 await assert.rejects(()=>executor.execute({model}),/fixture aborted/);
 // A healthy response after the retired one is reached by the existing HTTP-error fallback.
 let attempts=0,successes=0;
 for(const text of [JSON.stringify(payload(notice)),JSON.stringify(payload('valid response'))]){
 attempts++;const result=await run(text,'application/json',20);
 if(!result.response.ok){assert.equal(result.response.status,404);continue}
 successes++;assert.equal((await result.response.json()).response.candidates[0].content.parts[0].text,'valid response');break;
 }
 assert.equal(attempts,2);assert.equal(successes,1);
 console.log('Retirement notice JSON/SSE, byte preservation, cancellation and fallback checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
            subprocess.run(["node", "-e", harness, AG_EXECUTE], check=True)
    print("Router lock, durable fallback and exhausted-quota retry checks passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-dir", type=Path)
    args = parser.parse_args()
    patches = changes(args.app)
    check(args.app)
    if not args.apply:
        print(f"Validated; {len(patches)} files would change")
        return
    if patches and not args.backup_dir:
        parser.error("--backup-dir required when changing the installed build")
    if args.backup_dir:
        args.backup_dir.mkdir(parents=True, exist_ok=False)
    manifest = []
    try:
        for index, (path, original, updated) in enumerate(patches):
            backup = args.backup_dir / (str(index) + ".js")
            shutil.copy2(path, backup)
            manifest.append({"path": str(path), "backup": str(backup),
                             "before_sha256": hashlib.sha256(original.encode()).hexdigest(),
                             "after_sha256": hashlib.sha256(updated.encode()).hexdigest()})
            with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as out:
                out.write(updated)
                temporary = Path(out.name)
            temporary.chmod(path.stat().st_mode)
            temporary.replace(path)
        check(args.app, patched=True)
    except Exception:
        for row in manifest:
            shutil.copy2(row["backup"], row["path"])
        raise
    if args.backup_dir:
        (args.backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Applied {len(patches)} files; restart 9router after inspecting active work")


if __name__ == "__main__":
    main()
