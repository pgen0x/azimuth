"""Local evidence only: no network clients, trading imports or write operations."""
import base64, json, os, re, sqlite3, subprocess, sys, time
from pathlib import Path

SECRET = re.compile(r"(password|secret|credential|authorization|api.?key|private.?key|access.?token|bot.?token|system_prompt|model_config|origin_json)", re.I)
URL = re.compile(r"https?://[^\s\"<>]+")

def clean(value):
    if isinstance(value, dict):
        return {k: '[masked]' if SECRET.search(k) else clean(v) for k,v in value.items()}
    if isinstance(value, list): return [clean(v) for v in value]
    if isinstance(value, str):
        value = URL.sub('[endpoint masked]', value)
        return re.sub(r'(?i)\b(bearer\s+|sk-)[A-Za-z0-9_.-]+', '[masked]', value)
    return value

def tail(path, limit=500, budget=2*1024*1024):
    meta = {'path': str(path), 'status': 'missing', 'truncated': False, 'invalid_lines': 0}
    rows = []
    try:
        with path.open('rb') as f:
            stat=os.fstat(f.fileno()); offset=max(0,stat.st_size-budget); f.seek(offset)
            data=f.read(budget)
        meta.update(status='ok', modified_at=stat.st_mtime, bytes=stat.st_size, truncated=offset>0)
        if offset: data=data.partition(b'\n')[2]
        lines=data.splitlines()
        # Concurrent append can leave a partial final line. Never present it as evidence.
        if data and not data.endswith(b'\n'): lines=lines[:-1];meta['partial_line']=True
        for line in lines:
            try:
                row=json.loads(line)
                if isinstance(row,dict): rows.append(row)
            except (ValueError,UnicodeDecodeError): meta['invalid_lines']+=1
        meta['truncated'] |= len(rows)>limit
        rows=rows[-limit:]
    except OSError: pass
    meta['rows']=len(rows)
    return rows,meta

def event_time(row):
    return next((row[k] for k in ('ts','block_time','observed_at','closed_at','deployed_at','created_at','fetched_at') if isinstance(row.get(k),(int,float))),0)

def select(d, keys): return {k:d.get(k) for k in keys.split()}

def read_json(path):
    if path.stat().st_size>32*1024*1024: raise ValueError('report exceeds 32 MiB')
    return json.loads(path.read_text())

def collect(profile, state):
    now=time.time();memory=profile/'memories';sources=[];events=[]
    nav,meta=tail(memory/'dlmm_nav.jsonl',1);sources.append(meta)
    for filename,stage,root in [
        ('solana_deliveries.jsonl','AI / fallback',state),('solana_rejects.jsonl','gate',state),
        ('dlmm_transactions.jsonl','transaction',memory),('dlmm_transaction_facts.jsonl','transaction',memory),('dlmm_wallet_transactions.jsonl','transaction',memory),('dlmm_closes.jsonl','exit',memory),
        ('dlmm_report_guard.jsonl','AI / fallback',memory),('dlmm_root_decisions.jsonl','gate',memory),('dlmm_recenter_decisions.jsonl','gate',memory),
        ('dlmm_rent_history.jsonl','refund',memory),('dlmm_realized.jsonl','settlement',memory)]:
        rows,meta=tail(root/filename);sources.append(meta)
        for i,row in enumerate(rows):
            kind=row.get('kind','')
            actual={'deploy':'deploy','open':'deploy','close':'exit','swap':'swap','rent_refund':'refund','rent_reclaim':'refund'}.get(kind,stage)
            if row.get('stage')=='prepared': actual='candidate'
            evidence=select(row,'ts observed_at closed_at fetched_at delivery_id id entry_id root_chain_id position pool mode stage kind signature refund_signature account http_status reason gate allow status landed failed slot block_time fee_lamports event_position classification complete dry_run session_id receipt_count route fallback_reason lp_pnl_sol settled_cash_pnl_sol net_pnl_sol accounting_status realized_sol pnl_sol wallet_delta_lamports network_fee_lamports token_deltas_raw error')
            if isinstance(row.get('candidate'),dict): evidence['candidate']=select(row['candidate'],'pool name base_symbol base_mint mode')
            if isinstance(row.get('signal'),dict):
                evidence['candidates']=[select(c,'pool name base_symbol base_mint mode') for c in row['signal'].get('payload',[]) if isinstance(c,dict)]
            # Nested economic evidence is already produced by the accounting pipeline.
            for key in ('chain','evidence'):
                if isinstance(row.get(key),dict): evidence[key]=row[key]
            events.append({'stage':actual,'time':event_time(row), 'source':str(root/filename),'source_tail_index':i,'evidence':evidence,'note':'Submission recorded before broadcast; inspect matching transaction facts for confirmation.' if filename=='dlmm_transactions.jsonl' else ''})
    evaluation={};report_source=None;report_errors=[]
    candidates=sorted((state/'reviews').glob('*/evaluation.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:50]
    for path in candidates:
        try:
            candidate=read_json(path)
            if candidate.get('generated_at',0)>evaluation.get('generated_at',0):evaluation=candidate;report_source=str(path)
        except (OSError,ValueError): report_errors.append(str(path))
    hermes={'profile':profile.name,'config_status':'missing','sessions':[],'session_note':'An open session row is not proof that a process is alive. No messages or prompts are read.'}
    try:
        import yaml
        try: cfg=yaml.safe_load((profile/'config.yaml').read_text()) or {}
        except yaml.YAMLError as err: raise ValueError('invalid config') from err
        if not isinstance(cfg,dict): raise ValueError('invalid config')
        model=cfg.get('model',{})
        if isinstance(model,dict): model={k:v for k,v in model.items() if k in ('default','provider','api_mode') and isinstance(v,(str,int,bool))}
        hermes.update(config_status='read',model=select(model,'default provider api_mode') if isinstance(model,dict) else model,
                      fallback_providers=[select(x,'provider model') for x in cfg.get('fallback_providers',[]) if isinstance(x,dict)],
                      skills=sorted(p.parent.name for p in (profile/'skills').glob('**/SKILL.md'))[:100],
                      bot={'configured':'telegram' in (cfg.get('platforms') or {}), 'live_delivery':'unknown'},
                      provider_state='configuration only; no provider probe',webhook_state='see persisted deliveries; HTTP 202 is acceptance only')
    except (OSError,ValueError,ImportError): hermes['config_status']='unavailable'
    try:
        with sqlite3.connect('file:'+str(profile/'state.db')+'?mode=ro',uri=True,timeout=1) as db:
            db.row_factory=sqlite3.Row
            session_rows=[dict(r) for r in db.execute('SELECT id, source, model, started_at, ended_at, end_reason, message_count, tool_call_count, chat_id FROM sessions ORDER BY started_at DESC LIMIT 40')]
            hermes['sessions']=[{k:v for k,v in row.items() if k!='chat_id'} for row in session_rows]
            prepared={e['evidence'].get('delivery_id'):e for e in events if e['evidence'].get('stage')=='prepared'}
            for ident,event in prepared.items():
                identity=json.dumps([profile.name,'dlmm-signal',ident],ensure_ascii=False,separators=(',',':')).encode()
                names=['webhook:dlmm-signal:'+ident,'webhook:v2:'+base64.urlsafe_b64encode(identity).decode().rstrip('=')]
                matches=[r for r in session_rows if r['source']=='webhook' and r['chat_id'] in names]
                if matches:
                    evidence={'delivery_id':ident,'execution_verified':False,'session_state':'ambiguous' if len(matches)>1 else 'ended_execution_unverified' if matches[0]['ended_at'] else 'no_end_recorded_liveness_unknown'}
                    if len(matches)==1: evidence['session_id']=matches[0]['id']
                    events.append({'stage':'AI / fallback','time':event['time'],'source':str(profile/'state.db'),'evidence':evidence})
    except sqlite3.Error: hermes['sessions_status']='unavailable'
    units=['azimuth.service','hermes-gateway.service','azimuth-sol-monitor.service','azimuth-sol-accounting.service','azimuth-sol-accounting.timer','azimuth-sol-rent.service','azimuth-sol-rent.timer','azimuth-solana-review-daily.service','azimuth-solana-review-daily.timer']
    services=[]
    try:
        result=subprocess.run(['systemctl','--user','show',*units,'--property=Id,LoadState,ActiveState,SubState,Result,ExecMainStatus,ActiveEnterTimestamp,InactiveEnterTimestamp,NextElapseUSecRealtime'],capture_output=True,text=True,timeout=4)
        for block in result.stdout.strip().split('\n\n'):
            services.append(dict(line.split('=',1) for line in block.splitlines() if '=' in line))
    except (OSError,subprocess.TimeoutExpired):services=[{'status':'unavailable'}]
    # Only structured route markers from the scanner unit, never Hermes message contents.
    try:
        route_log=subprocess.run(['journalctl','--user','-u','azimuth.service','--since','48 hours ago','-n','100','--grep=entry_route=','-o','json','--no-pager'],capture_output=True,text=True,timeout=3)
        for line in route_log.stdout.splitlines():
            try: log=json.loads(line)
            except ValueError: continue
            match=re.search(r'scanner\[([a-z]+)\]: entry_route=(hermes_ai|deterministic_fallback)(?: reason=([a-z_]+))?',log.get('MESSAGE',''))
            if match:
                events.append({'stage':'AI / fallback','time':int(log.get('__REALTIME_TIMESTAMP',0))/1e6,'source':'journalctl --user -u azimuth.service; last 100 route markers / 48 hours', 'evidence':{'mode':match[1],'route':match[2],'fallback_reason':match[3], 'execution_verified':False},'note':'Route observation only; no candidate or execution correlation is implied.'})
    except (OSError,subprocess.TimeoutExpired): pass
    # Entry files supply explicit entry -> root -> position links; never infer links by time.
    entries=sorted((memory/'dlmm_entries').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]
    for path in entries:
        try:
            row=read_json(path)
            evidence=select(row,'entry_id root_chain_id position pool signature ts created_at mode status base_mint base_symbol size_sol strategy')
            evidence['deployed_at']=row.get('deployed_at')
            events.append({'stage':'deploy','time':event_time(row), 'source':str(path),'evidence':evidence,'note':'Entry metadata alone does not prove a landed transaction.'})
        except (OSError,ValueError): pass
    hermes['gateway'] = next((s for s in services if s.get('Id')=='hermes-gateway.service'), {'ActiveState':'unknown'})
    for delivery in evaluation.get('delivery_tracking',{}).get('deliveries',[]):
        events.append({'stage':'AI / fallback','time':delivery.get('prepared_at',0),'source':report_source,'evidence':delivery})
    events.sort(key=lambda e:e.get('time') or 0,reverse=True)
    return clean({'collected_at':now,'nav':nav[-1] if nav else {},'evaluation':evaluation,'evaluation_source':report_source,'report_errors':report_errors,'journal':events,'sources':sources,'hermes':hermes,'services':services})

if __name__=='__main__':
    print(json.dumps(collect(Path(sys.argv[1]),Path(sys.argv[2])),allow_nan=False))
