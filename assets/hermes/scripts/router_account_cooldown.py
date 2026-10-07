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

# A cached Antigravity reset must also reach the existing durable model lock.
OLD_FALLBACK = '"antigravity"===y&&A||(await (0,f.vk)(b.connectionId,x.status,x.error,y,z,G)).shouldFallback'
NEW_FALLBACK = '(await (0,f.vk)(b.connectionId,x.status,x.error,y,z,G)).shouldFallback'

# Exhausted weekly quota cannot recover during the current HTTP retry loop.
OLD_RETRY = 'async computeRetryDelay(a,b){let c="",d=null,e=this.parseRetryHeaders(a.headers);try{d=(c=await a.clone().text())?JSON.parse(c):null}catch{}let f=this.extractErrorMessage(d,c);return(e||(e=this.parseRetryFromErrorMessage(f)),e)?e<=1e4&&e:!!this.isTransientAntigravityError(a.status,f)&&Math.min(1e3*2**b,a.status===i.gx.RATE_LIMITED?1e4:15e3)}'
NEW_RETRY = OLD_RETRY.replace("catch{}let f=", "catch{}" + 'if(429===a.status&&"RESOURCE_EXHAUSTED"===d?.error?.status&&Array.isArray(d.error.details)&&d.error.details.some(a=>"QUOTA_EXHAUSTED"===a.reason))return!1;' + "let f=")

def changes(app):
    if json.loads((app.parent / "package.json").read_text()).get("version") != "0.5.95":
        raise ValueError("Unsupported 9router version; audit upstream before applying")
    root = app / ".next-cli-build/server"
    patches = []
    readers = writers = fallbacks = retries = 0
    for path in root.rglob("*.js"):
        original = path.read_text()
        readers += original.count(OLD_LOCK) + original.count(NEW_LOCK)
        writers += original.count(ANCHOR) + original.count(INSERT_V1) + original.count(INSERT)
        fallbacks += original.count(OLD_FALLBACK) + (0 if OLD_FALLBACK in original else original.count(NEW_FALLBACK))
        retries += original.count(OLD_RETRY) + original.count(NEW_RETRY)
        updated = original.replace(OLD_LOCK, NEW_LOCK).replace(INSERT_V1, INSERT).replace(ANCHOR, INSERT).replace(OLD_FALLBACK, NEW_FALLBACK).replace(OLD_RETRY, NEW_RETRY)
        if original != updated:
            patches.append((path, original, updated))
    if readers != 9 or writers != 1 or fallbacks != 1 or retries != 1:
        raise ValueError(f"Build shape changed: {readers} lock readers, {writers} account writer, {fallbacks} chat fallback, {retries} AG retry")
    return patches


def check(app, patched=False):
    patches = changes(app)
    if patched and patches:
        raise ValueError("Installed build is not fully patched")
    # Exercise real functions extracted from every installed copy, without requests.
    for path in (app / ".next-cli-build/server").rglob("*.js"):
        source = path.read_text().replace(OLD_LOCK, NEW_LOCK).replace(INSERT_V1, INSERT).replace(ANCHOR, INSERT).replace(OLD_FALLBACK, NEW_FALLBACK).replace(OLD_RETRY, NEW_RETRY)
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
let update;
const mark=vm.runInNewContext('('+process.argv[1]+')',{
d:{getProviderConnections:async()=>[{id:'conn',backoffLevel:0}],updateProviderConnection:async(id,value)=>{update=value}},
f:{hk:()=>({shouldFallback:true,cooldownMs:30000}),S5:(model,ms)=>({[model?'modelLock_'+model:'modelLock___all']:new Date(Date.now()+ms).toISOString()})},
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
 const retry=Date.now()+3600000;
 await mark('conn',429,'{"code":14018}','codebuddy-cn','model',retry);
 assert(Date.parse(update.modelLock___all)>=retry);
 await mark('conn',402,"you've reached your additional usage limit for your plan",'github','model');
 assert(Object.hasOwn(update,'modelLock___all'));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
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
