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

WIB=7*3600
NAV_TS=re.compile(rb'"ts":\s*(\d+)')

def _nav_line(f, offset, size):
    """First complete snapshot line starting at or after offset: (start, end, ts, raw)."""
    if offset:
        f.seek(offset-1)
        if f.read(1)!=b'\n': f.readline()  # mid-line offset: skip to the next line start
    else: f.seek(0)
    while f.tell()<size:
        start=f.tell(); raw=f.readline(4*1024*1024)
        if not raw.endswith(b'\n'): return None  # partial append or oversized line
        m=NAV_TS.search(raw[:256])
        if m: return start,f.tell(),int(m[1]),raw
    return None

def nav_at(path, t, need=('native_sol',), tries=50):
    """Last dlmm_nav.jsonl row with ts <= t whose `need` fields are non-null.
    Binary search over byte offsets (rows are appended in time order), so a
    multi-hundred-MB history costs a few dozen small reads, not a full parse."""
    try:
        with path.open('rb') as f:
            size=os.fstat(f.fileno()).st_size; limit=size
            for _ in range(tries):
                # Last line starting before `limit` with ts <= t.
                first=_nav_line(f,0,size)
                if not first or first[0]>=limit or first[2]>t: return None
                best,lo,hi=first,first[1],limit
                while lo<hi:
                    mid=(lo+hi)//2; line=_nav_line(f,mid,size)
                    if line is None or line[0]>=limit or line[2]>t: hi=mid
                    else: best,lo=line,line[1]
                try: row=json.loads(best[3])
                except ValueError: row=None
                if isinstance(row,dict) and all(row.get(k) is not None for k in need): return row
                limit=best[0]  # unusable row: search strictly earlier lines
    except OSError: pass
    return None

def north_star(memory, now, days=14):
    """Per WIB day: the day's last snapshot. cash = native + LP mark + refundable rent;
    known = native + SPL mark + LP mark + rent. Unmeasured parts stay null, never 0."""
    path=memory/'dlmm_nav.jsonl'; out=[]; prev=None
    today=int((now+WIB)//86400)
    for day in range(today-days, today+1):
        end=day*86400-WIB+86400
        row=nav_at(path,min(end-1,now))
        if row is None or int((row['ts']+WIB)//86400)!=day:
            out.append({'day':time.strftime('%Y-%m-%d',time.gmtime(day*86400)),'status':'no_snapshot'}); prev=None; continue
        parts=[row.get(k) for k in ('native_sol','lp_mark_sol','refundable_rent_sol')]
        cash=sum(parts) if all(isinstance(v,(int,float)) for v in parts) else None
        known=row.get('known_asset_subtotal_sol')
        tokens=row.get('tokens') if isinstance(row.get('tokens'),list) else []
        item={'day':time.strftime('%Y-%m-%d',time.gmtime(day*86400)),'status':'partial_day' if day==today else 'ok',
              'ts':row['ts'],'native_sol':row.get('native_sol'),'cash_sol':cash,'known_sol':known,
              'refundable_rent_sol':row.get('refundable_rent_sol'),'wallet_history_complete':row.get('wallet_history_complete'),
              'unpriced_tokens':sum(1 for i in row.get('issues') or [] if isinstance(i,str) and i.startswith('unpriced_token:')),
              'quote_deferred_tokens':sum(1 for x in tokens if isinstance(x,dict) and x.get('mark_error')=='quote_budget_deferred'),
              'external_flow_lamports':row.get('external_flow_lamports')}
        if prev:
            item['d_cash_sol']=None if cash is None or prev['cash_sol'] is None else cash-prev['cash_sol']
            item['d_known_sol']=None if known is None or prev['known_sol'] is None else known-prev['known_sol']
            a,b=prev.get('external_flow_lamports'),item['external_flow_lamports']
            item['d_external_sol']=(b-a)/1e9 if isinstance(a,int) and isinstance(b,int) else None
        out.append(item); prev=item
    return {'days':out,'basis':'Last snapshot per WIB day. known = native + SPL mark + LP mark + refundable rent. cash = native + LP mark + refundable rent (no SPL marks). Deltas are between consecutive observed days; a missing day breaks the chain.',
            'caveats':['SPL marks drop out when a quote is deferred or a token is unpriced: known then falls without a trade (phantom loss). cash excludes SPL marks and is immune to that, but also misses real token value.',
                       'External deposits/withdrawals are not netted out of either delta; check d_external_sol before reading a jump as profit.',
                       'Refundable rent is a recoverable reserve, not income; native growth can be recovered principal or rent.']}

def read_jsonl(path, cap=64*1024*1024):
    """Whole-file JSONL read for exact window sums; over `cap` the bridge is marked incomplete."""
    rows,meta=[],{'path':str(path),'status':'missing','invalid_lines':0}
    try:
        with path.open('rb') as f:
            size=os.fstat(f.fileno()).st_size
            if size>cap: meta.update(status='over_cap',bytes=size); return rows,meta
            data=f.read(cap)
        meta.update(status='ok',bytes=size)
        lines=data.splitlines()
        if data and not data.endswith(b'\n'): lines=lines[:-1];meta['partial_line']=True
        for line in lines:
            try:
                row=json.loads(line)
                if isinstance(row,dict): rows.append(row)
            except (ValueError,UnicodeDecodeError): meta['invalid_lines']+=1
    except OSError: pass
    return rows,meta

def _token_marks(snap):
    return {t['mint']:t['mark_sol'] for t in snap.get('tokens') or [] if isinstance(t,dict) and t.get('mint') and isinstance(t.get('mark_sol'),(int,float))}

def _inline_refund(r):
    ev=r.get('token_rent_evidence') or {}
    items=ev.get('refunded') or []
    if items: return sum(i.get('lamports') or 0 for i in items)
    return sum(i.get('pre_lamports') or 0 for i in ev.get('inline_closed') or [])

def _funded(r):
    return sum(i.get('lamports') or 0 for i in (r.get('token_rent_evidence') or {}).get('funded') or [])

BRIDGE_NEED=('native_sol','spl_mark_sol','lp_mark_sol','refundable_rent_sol','known_asset_subtotal_sol','slot')

def nav_bridge(memory, now, days=14):
    """Decompose the change in known SOL over the last `days` into additive parts.
    Identity: Δknown = Σ wallet tx deltas + ΔSPL mark + ΔLP mark + Δrefundable rent.
    Port of the nav-bridge study; same per-lifecycle split, no new data source."""
    L=1e9; path=memory/'dlmm_nav.jsonl'
    b=nav_at(path,now,need=BRIDGE_NEED)
    a=nav_at(path,b['ts']-days*86400,need=BRIDGE_NEED) if b else None
    out={'basis':'Change in known SOL (native + SPL mark + LP mark + refundable rent) between two NAV snapshots. '
         'This is not NAV/ROI and is never withdrawal + fees - deposit; each component keeps its own basis.','days':days}
    if not a or not b or a['ts']>=b['ts']:
        out['status']='insufficient_snapshots'; return out
    sources={}
    kinds={r.get('signature'):r for r in read_jsonl(memory/'dlmm_transactions.jsonl')[0]}
    txrows,sources['wallet_transactions']=read_jsonl(memory/'dlmm_wallet_transactions.jsonl')
    realrows,sources['realized']=read_jsonl(memory/'dlmm_realized.jsonl')
    closerows,sources['closes']=read_jsonl(memory/'dlmm_closes.jsonl')
    txs={r.get('signature'):r for r in txrows}  # repeated observations: keep the last
    realized={r.get('position'):r for r in realrows}
    mode={r['position']:r['mode'] for r in closerows if r.get('position') and r.get('mode')}
    win=[r for r in txs.values() if isinstance(r.get('slot'),int) and a['slot']<r['slot']<=b['slot']]
    d_known=b['known_asset_subtotal_sol']-a['known_asset_subtotal_sol']
    d_native=b['native_sol']-a['native_sol']; d_rent=b['refundable_rent_sol']-a['refundable_rent_sol']
    d_lp=b['lp_mark_sol']-a['lp_mark_sol']; d_spl=b['spl_mark_sol']-a['spl_mark_sol']
    ma,mb=_token_marks(a),_token_marks(b)
    spl_both=sum(mb[m]-ma[m] for m in set(ma)&set(mb))
    fee={}; per_pos={}; unattr={}; perm=0
    add=lambda d,k,v:d.__setitem__(k,d.get(k,0)+v)
    for r in win:
        k=kinds.get(r.get('signature'),{})
        kind=k.get('kind') or ('external' if r.get('classification')=='external_transfer' else 'unrecorded')
        f=fee.setdefault(kind,{'n':0,'failed':0,'lamports':0})
        f['n']+=1; f['lamports']+=r.get('fee_lamports') or 0; f['failed']+=bool(r.get('failed'))
        perm+=r.get('nonrefundable_account_cost_lamports') or 0
        pos=r.get('event_position') or k.get('position')
        delta,fl=r.get('wallet_delta_lamports') or 0,r.get('fee_lamports') or 0
        nonref=r.get('nonrefundable_account_cost_lamports') or 0
        if pos and kind in ('deploy','close','claim','swap'):
            p=per_pos.setdefault(pos,{}); add(p,'n_'+kind,1); add(p,'fee',fl)
            if kind=='swap':
                locked=r.get('refundable_rent_locked_lamports') or 0
                add(p,'swap_net',delta+fl+nonref+locked-_inline_refund(r)); add(p,'ata_refund',_inline_refund(r)); add(p,'swap_rent_locked',locked)
            else:
                add(p,'lp_cash',delta+fl+nonref); add(p,'ata_funded',_funded(r)); add(p,'closed',bool(r.get('position_account_closed')))
        else:
            add(unattr,kind,delta+fl+nonref); add(unattr,'ext',r.get('external_flow_lamports') or 0)
    R=TV=SW=0.0; complete=0; partial={'n':0,'cash':0.0,'unmeasured_realized':0}; by_mode={}
    for pos,p in per_pos.items():
        rz=(realized.get(pos) or {}).get('realized_sol')
        if not (p.get('n_deploy',0)>=1 and p.get('closed',0)>=1 and isinstance(rz,(int,float))):
            partial['n']+=1; partial['unmeasured_realized']+=bool(pos in realized and not isinstance(rz,(int,float)))
            partial['cash']+=(p.get('lp_cash',0)+p.get('swap_net',0)+p.get('ata_refund',0)-p.get('swap_rent_locked',0))/L
            continue
        complete+=1
        lp_native=(p.get('lp_cash',0)+p.get('ata_funded',0))/L
        tv,sw=rz-lp_native,p.get('swap_net',0)/L
        R+=rz; TV+=tv; SW+=sw
        m=by_mode.setdefault(mode.get(pos,'unknown'),{'n':0,'realized_sol':0.0,'fees_sol':0.0,'swap_residual_sol':0.0,'ata_rent_left_sol':0.0})
        m['n']+=1; m['realized_sol']+=rz; m['fees_sol']-=p.get('fee',0)/L; m['swap_residual_sol']+=sw-tv
        m['ata_rent_left_sol']+=(p.get('ata_funded',0)+p.get('swap_rent_locked',0)-p.get('ata_refund',0))/L
    fees_total=sum(v['lamports'] for v in fee.values())/L
    ata_left=sum(v['ata_rent_left_sol'] for v in by_mode.values())
    rent_ledger=d_rent-ata_left+(unattr.get('rent_reclaim',0)+unattr.get('swap',0)+unattr.get('unrecorded',0))/L
    comps=[('lp_realized','LP realized (Meteora flows, complete lifecycles)',R),
           ('network_fees','Network fees, all transactions incl. failed',-fees_total),
           ('rent_permanent','Rent: permanent account cost',-perm/L),
           ('rent_ledger','Rent: ledger mismatch (Δrent vs locks, refunds, reclaims)',rent_ledger),
           ('swap_residual','Swap residual (settlement proceeds - Meteora token value)',SW-TV),
           ('spl_mark','SPL mark change, tokens priced at both ends',spl_both),
           ('lp_unrealized','Unrealized: Δ LP mark',d_lp),
           ('external','External transfers',unattr.get('external',0)/L),
           ('partial_lifecycles','Partial lifecycles straddling the window',partial['cash']),
           ('spl_coverage','SPL valuation coverage (priced at one end only)',d_spl-spl_both)]
    comps.append(('unexplained','Unexplained residual',d_known-sum(v for _,_,v in comps)))
    incomplete=[k for k,m in sources.items() if m['status']!='ok']
    out.update(status='incomplete_sources' if incomplete else 'ok', incomplete_sources=incomplete,
               start_ts=a['ts'],end_ts=b['ts'],slots=[a['slot'],b['slot']],d_known_sol=d_known,d_native_sol=d_native,
               sum_tx_delta_sol=sum(r.get('wallet_delta_lamports') or 0 for r in win)/L,transactions=len(win),
               native_identity_exact=abs(sum(r.get('wallet_delta_lamports') or 0 for r in win)/L-d_native)<1e-9,
               components=[{'key':k,'label':l,'sol':v} for k,l,v in comps],
               fees_by_kind={k:{'n':v['n'],'failed':v['failed'],'sol':v['lamports']/L} for k,v in sorted(fee.items())},
               positions={'complete':complete,'partial':partial['n'],'realized_unmeasured':partial['unmeasured_realized']},
               by_mode=by_mode,
               unpriced_tokens=[sum(1 for t in s.get('tokens') or [] if isinstance(t,dict) and t.get('mark_sol') is None) for s in (a,b)])
    return out

def dust_ledger(memory, since, run=None):
    """Rent-reclaim results printed by the rent unit since `since`, checked against the
    dust rules: a burn never forfeits more than half the rent it frees, and fee +
    forfeited must stay below the rent recovered. Wallet facts confirm landing."""
    run=run or subprocess.run
    out={'since':since,'runs':0,'executed_tx':0,'failed_without_tx':0,'deferred':0,'closed_accounts':0,'burned_accounts':0,
         'rent_recovered_lamports':0,'fee_lamports':0,'forfeited_quote_lamports':0,'violations':[],'tx_not_ingested':0,'errors':{},
         'source':'journalctl --user -u azimuth-sol-rent.service; last 5000 lines since the cutover'}
    try:
        text=run(['journalctl','--user','-u','azimuth-sol-rent.service','--since','@%d'%int(since),'-n','5000','-o','short-unix','--no-pager'],
                 capture_output=True,text=True,timeout=5).stdout
    except (OSError,subprocess.TimeoutExpired):
        out['status']='unavailable'; return out
    facts={r.get('signature'):r for r in read_jsonl(memory/'dlmm_wallet_transactions.jsonl')[0]}
    for line in text.splitlines():
        head,_,body=line.partition(' ')
        if '{' not in body: continue
        try: r=json.loads(body[body.index('{'):]); ts=float(head)
        except ValueError: continue
        if not isinstance(r,dict) or not ('success' in r or 'txHash' in r): continue
        out['runs']+=1
        if r.get('deferred'): out['deferred']+=1
        if r.get('success') is False and not r.get('txHash'):
            out['failed_without_tx']+=1
            reason=str(r.get('error') or r.get('reason') or 'unknown')[:120]
            out['errors'][reason]=out['errors'].get(reason,0)+1
        if not r.get('txHash') or r.get('dry_run') is not False: continue
        accts=[a for a in r.get('accounts') or [] if isinstance(a,dict)]
        burns=[a for a in accts if a.get('burn_raw')]
        rent=sum(a.get('rent_lamports') or 0 for a in accts); forfeited=sum(a.get('quote_lamports') or 0 for a in burns); fee=r.get('fee_lamports') or 0
        out['executed_tx']+=1; out['closed_accounts']+=len(accts); out['burned_accounts']+=len(burns)
        out['rent_recovered_lamports']+=rent; out['fee_lamports']+=fee; out['forfeited_quote_lamports']+=forfeited
        sig=r['txHash']
        for a in burns:
            if (a.get('quote_lamports') or 0)*2>(a.get('rent_lamports') or 0): out['violations'].append({'rule':'quote above half rent','signature':sig,'time':ts})
        if burns and fee+forfeited>=rent: out['violations'].append({'rule':'fee + forfeited >= rent','signature':sig,'time':ts})
        fact=facts.get(sig)
        if fact is None: out['tx_not_ingested']+=1
        elif fact.get('failed') and burns: out['violations'].append({'rule':'burn transaction failed on-chain','signature':sig,'time':ts})
    out['status']='ok'
    out['liquid_native_gain_sol']=(out['rent_recovered_lamports']-out['fee_lamports'])/1e9
    out['nav_effect_sol']=-(out['forfeited_quote_lamports']+out['fee_lamports'])/1e9
    return out

def realized_by_mode(memory, since):
    """Per WIB day and mode, closes since the cutover from dlmm_realized.jsonl (the arbiter).
    A null realized figure is counted as unmeasured, never added as 0."""
    realrows,meta=read_jsonl(memory/'dlmm_realized.jsonl')
    closerows,_=read_jsonl(memory/'dlmm_closes.jsonl')
    mode={r['position']:r['mode'] for r in closerows if r.get('position') and r.get('mode')}
    days={}
    for r in {r.get('position'):r for r in realrows}.values():
        t=r.get('closed_at')
        if not isinstance(t,(int,float)) or t<since: continue
        day=time.strftime('%Y-%m-%d',time.gmtime(t+WIB)); m=mode.get(r.get('position'),'unknown')
        cell=days.setdefault(day,{}).setdefault(m,{'closes':0,'measured':0,'unmeasured':0,'realized_sol':0.0})
        cell['closes']+=1
        if isinstance(r.get('realized_sol'),(int,float)): cell['measured']+=1; cell['realized_sol']+=r['realized_sol']
        else: cell['unmeasured']+=1
    return {'since':since,'status':meta['status'],'days':days,'basis':'realized_sol from dlmm_realized.jsonl, keyed by close time (WIB day) and the mode on the close journal. Null realized = unmeasured, never 0.'}

def collect(profile, state, since=None):
    now=time.time();memory=profile/'memories';sources=[];events=[]
    since=float(since) if since and float(since)>0 else now-7*86400  # cutover; 0/absent = the last 7 days
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
            evidence=select(row,'ts observed_at closed_at fetched_at delivery_id id entry_id root_chain_id position pool mode stage kind signature refund_signature account http_status reason gate allow status landed failed slot block_time fee_lamports event_position classification complete dry_run session_id receipt_count route fallback_reason lp_pnl_sol settled_cash_pnl_sol net_pnl_sol accounting_status realized_sol pnl_sol pnl_basis pnl_currency wallet_delta_lamports network_fee_lamports token_deltas_raw error')
            # Close-journal figures are marks read one tick before the close; the arbiter is
            # dlmm_realized.jsonl. Older rows carry no basis field, so label them, never imply cash.
            if filename=='dlmm_closes.jsonl' and evidence.get('pnl_sol') is not None and not evidence.get('pnl_basis'):
                evidence['pnl_basis']='mark_unlabeled'
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
    return clean({'collected_at':now,'north_star':north_star(memory,now),'nav_bridge':nav_bridge(memory,now),'live':{'dust':dust_ledger(memory,since),'realized':realized_by_mode(memory,since)},'nav':nav[-1] if nav else {},'evaluation':evaluation,'evaluation_source':report_source,'report_errors':report_errors,'journal':events,'sources':sources,'hermes':hermes,'services':services})

if __name__=='__main__':
    print(json.dumps(collect(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3] if len(sys.argv)>3 else None),allow_nan=False))
