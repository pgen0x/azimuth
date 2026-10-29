"""Local evidence only: no network clients, trading imports or write operations."""
import base64, json, math, os, re, selectors, signal, sqlite3, stat, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timedelta, time as clock
from zoneinfo import ZoneInfo

SECRET = re.compile(r"(password|secret|credential|authorization|api.?key|private.?key|access.?token|bot.?token|system_prompt|model_config|origin_json)", re.I)
# Owner policy: the dashboard reports this bot only, never a comparison with another bot.
# The other bot's name is written as a character class so this directory stays free of it
# (the policy check is a plain `git grep -i` over cmd/dashboard).
OTHER_BOT = re.compile(r"m[e]ridian|comparison|reference_bot", re.I)
def own_only(value):
    """Drop, recursively, every key that names another bot or a comparison with one."""
    if isinstance(value, dict): return {k: own_only(v) for k, v in value.items() if not OTHER_BOT.search(str(k))}
    if isinstance(value, list): return [own_only(v) for v in value]
    return value
URL = re.compile(r"https?://[^\s\"<>]+")

def clean(value):
    if isinstance(value, dict):
        return {clean(str(k)): '[masked]' if SECRET.search(str(k)) else clean(v) for k,v in value.items()}
    if isinstance(value, list): return [clean(v) for v in value]
    if isinstance(value, str):
        value = URL.sub('[endpoint masked]', value)
        return re.sub(r'(?i)\b(bearer\s+|sk-)[A-Za-z0-9_.-]+', '[masked]', value)
    if isinstance(value,float) and not math.isfinite(value): return None
    return value

def number(v):
    return type(v) in (int, float) and math.isfinite(v)

def lamports(v, signed=False):
    return type(v) is int and abs(v) <= 2**53-1 and (signed or v >= 0)

def identifier(v):
    return isinstance(v, str) and 0 < len(v) <= 200

def optional_sum(values):
    values=list(values)
    return sum(values) if all(number(v) for v in values) else None

def open_regular(path):
    fd=os.open(path,os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd); raise OSError('not a regular evidence file')
    return os.fdopen(fd,'rb')

def incomplete(meta):
    return (meta.get('status') != 'ok' or bool(meta.get('invalid_lines'))
            or bool(meta.get('partial_line')) or bool(meta.get('truncated')))

def bounded_run(argv, *, capture_output=True, text=True, timeout=5, cap=2*1024*1024):
    """Fixed argv, bounded combined stdout/stderr, kill/reap our own process group."""
    chunks=[bytearray(),bytearray()]; total=0; status='ok'; deadline=time.monotonic()+timeout
    with subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True) as proc:
        try:
            with selectors.DefaultSelector() as poll:
                for i,stream in enumerate((proc.stdout,proc.stderr)):
                    os.set_blocking(stream.fileno(),False); poll.register(stream,selectors.EVENT_READ,i)
                while poll.get_map():
                    remaining=deadline-time.monotonic()
                    if remaining<=0: status='timeout'; break
                    for key,_ in poll.select(min(remaining,.1)):
                        data=os.read(key.fd,min(65536,cap-total+1))
                        if not data: poll.unregister(key.fileobj); continue
                        total+=len(data)
                        if total>cap: status='over_cap'; break
                        chunks[key.data].extend(data)
                    if status!='ok': break
                if status=='ok':
                    try: proc.wait(timeout=max(.001,deadline-time.monotonic()))
                    except subprocess.TimeoutExpired: status='timeout'
        finally:
            if proc.poll() is None or status!='ok':
                try: os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError: pass
            proc.wait()
    return SimpleNamespace(stdout=bytes(chunks[0]).decode('utf-8','replace'),
                           stderr=bytes(chunks[1]).decode('utf-8','replace'),returncode=proc.returncode,
                           capture_status=status,capture_bytes=total,byte_cap=cap)

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
                else: meta['invalid_lines']+=1
            except (ValueError,UnicodeDecodeError): meta['invalid_lines']+=1
        meta['truncated'] |= len(rows)>limit
        rows=rows[-limit:]
    except OSError: pass
    meta['rows']=len(rows)
    return rows,meta

def event_time(row):
    return next((row[k] for k in ('ts','block_time','observed_at','closed_at','deployed_at','created_at','fetched_at') if number(row.get(k))),0)

def select(d, keys): return {k:d.get(k) for k in keys.split()}

def read_json(path):
    if path.stat().st_size>32*1024*1024: raise ValueError('report exceeds 32 MiB')
    return json.loads(path.read_text())

# Day buckets follow the viewer's IANA zone (validated by the Go server); timestamps stay UTC epochs.
def zone(tz): return ZoneInfo(tz or 'UTC')
def local_day(ts, z): return datetime.fromtimestamp(ts, z).date()
def day_start(d, z): return datetime.combine(d, clock(0), z).timestamp()
NAV_LINE_BYTES=1024*1024
NAV_LOOKUP_BYTES=8*1024*1024
NAV_LOOKUP_READS=256
NAV_FULL_SCAN_BYTES=4*1024*1024

class NavBudget(Exception):
    pass

def _nav_line(f, offset, size, meta, deadline):
    """Validated complete JSON row; every alignment/drain read shares one budget."""
    def line():
        if time.monotonic() >= deadline or meta['read_calls'] >= NAV_LOOKUP_READS:
            raise NavBudget('work_cap')
        remaining=NAV_LOOKUP_BYTES-meta['read_bytes']
        if remaining <= 0: raise NavBudget('byte_cap')
        raw=f.readline(min(NAV_LINE_BYTES+1,remaining))
        meta['read_calls']+=1; meta['read_bytes']+=len(raw)
        if len(raw)>NAV_LINE_BYTES: raise NavBudget('line_cap')
        return raw
    if offset:
        f.seek(offset-1)
        if meta['read_calls']>=NAV_LOOKUP_READS or meta['read_bytes']>=NAV_LOOKUP_BYTES: raise NavBudget('work_cap')
        meta['read_calls']+=1; meta['read_bytes']+=1
        if f.read(1)!=b'\n':
            raw=line()
            if raw and not raw.endswith(b'\n'): raise NavBudget('partial_or_oversized_line')
    else: f.seek(0)
    while f.tell()<size:
        start=f.tell(); raw=line()
        if not raw.endswith(b'\n'):
            meta['partial_line']=True; return None
        try:
            row=json.loads(raw)
            if not isinstance(row,dict) or not number(row.get('ts')): raise ValueError('timestamp')
        except (ValueError,UnicodeDecodeError):
            meta['invalid_lines']+=1; continue
        return start,f.tell(),row['ts'],row
    return None

def nav_at(path, t, need=(), tries=50, meta=None):
    """Latest row, including unknown monetary fields. Optional need is explicit.

    Small files are fully validated. Large-file seeks are bounded; every row the
    lookup reads (binary search, backward scan, neighbour) is ordering-checked and
    any observed inversion marks the lookup partial. Ordering of unread rows is
    assumed (`visited_window_monotonic`), never proved.
    Never use an unparsed or nested timestamp to steer the search.
    """
    meta={} if meta is None else meta
    meta.update(status='missing',invalid_lines=0,read_calls=0,read_bytes=0,ordering_verified=False)
    if not number(t): meta['status']='invalid_cutoff'; return None
    deadline=time.monotonic()+2
    try:
        with open_regular(path) as f:
            info=os.fstat(f.fileno()); size=info.st_size
            if not stat.S_ISREG(info.st_mode): meta['status']='not_regular'; return None
            meta.update(status='ok',bytes=size)
            if size<=NAV_FULL_SCAN_BYTES:
                latest=None; previous=None
                while f.tell()<size:
                    found=_nav_line(f,f.tell(),size,meta,deadline)
                    if found is None: break
                    _,_,stamp,row=found
                    if previous is not None and stamp<previous: meta['out_of_order']=True
                    previous=stamp
                    if stamp<=t and all(number(row.get(k)) for k in need):
                        if latest is None or stamp>=latest['ts']: latest=row
                meta['ordering_verified']=not meta.get('out_of_order',False)
                if incomplete(meta) or meta.get('out_of_order'): meta['status']='partial'
                return latest
            # Whole-file ordering cannot be proved within the bounds; check it where we looked.
            # Every row read (offset, ts), including each row of the backward scan and one
            # neighbour line on each side of the pick, must be non-decreasing; any observed
            # inversion marks the lookup partial.
            meta.update(ordering_assumption='visited_window_monotonic')
            visited={}
            def seen(item):
                if item is not None: visited[item[0]]=item[2]
                return item
            def previous(start):
                back=65536
                while back<=4*NAV_LINE_BYTES:
                    cursor=max(0,start-back); last=None
                    while True:
                        # Every row read here is part of the ordering check, including the one
                        # that stops the scan: an inversion we read must not pass as ok.
                        item=seen(_nav_line(f,cursor,size,meta,deadline))
                        if item is None or item[0]>=start: break
                        last=item; cursor=item[1]
                    if last is not None or cursor==0: return last
                    back*=4
                return None
            def ordered():
                stamps=[visited[k] for k in sorted(visited)]
                return all(a<=b for a,b in zip(stamps,stamps[1:]))
            limit=size
            for _ in range(tries):
                first=seen(_nav_line(f,0,size,meta,deadline))
                if not first or first[0]>=limit or first[2]>t: return None
                best,lo,hi=first,first[1],limit
                while lo<hi:
                    mid=(lo+hi)//2; item=seen(_nav_line(f,mid,size,meta,deadline))
                    if item is None or item[0]>=limit or item[2]>t: hi=mid
                    else: best,lo=item,item[1]
                row=best[3]
                if number(row.get('ts')) and row['ts']<=t and all(number(row.get(k)) for k in need):
                    previous(best[0]); seen(_nav_line(f,best[1],size,meta,deadline))
                    meta['visited_rows']=len(visited)
                    if not ordered(): meta.update(status='partial',out_of_order=True)
                    return row
                limit=best[0]
            meta['status']='work_cap'
    except NavBudget as e: meta['status']=str(e)
    except FileNotFoundError: meta['status']='missing'
    except OSError: meta['status']='unavailable'
    return None

# Six weeks of local days for the dashboard's calendar; the NAV bridge keeps its 14-day window.
CALENDAR_DAYS=41

def north_star(memory, now, days=14, tz='UTC'):
    """Per local day in `tz`: the day's last snapshot. cash = native + LP mark + refundable rent;
    known = native + SPL mark + LP mark + rent. Unmeasured parts stay null, never 0."""
    path=memory/'dlmm_nav.jsonl'; out=[]; prev=None; z=zone(tz)
    today=local_day(now,z)
    for back in range(days,-1,-1):
        day=today-timedelta(days=back); end=day_start(day+timedelta(days=1),z)
        source={}; row=nav_at(path,min(end-1,now),meta=source)
        if row is None or local_day(row['ts'],z)!=day:
            out.append({'day':day.isoformat(),'status':'no_snapshot' if not incomplete(source) else 'unknown','source':source}); prev=None; continue
        parts=[row.get(k) for k in ('native_sol','lp_mark_sol','refundable_rent_sol')]
        cash=optional_sum(parts)
        known=row.get('known_asset_subtotal_sol') if number(row.get('known_asset_subtotal_sol')) else None
        tokens=row.get('tokens') if isinstance(row.get('tokens'),list) else []
        item={'day':day.isoformat(),'status':'partial_day' if day==today else 'ok',
              'ts':row['ts'],'source':source,'native_sol':row.get('native_sol'),'cash_sol':cash,'known_sol':known,
              'refundable_rent_sol':row.get('refundable_rent_sol'),'wallet_history_complete':row.get('wallet_history_complete'),
              'unpriced_tokens':sum(1 for i in row.get('issues') or [] if isinstance(i,str) and i.startswith('unpriced_token:')),
              'quote_deferred_tokens':sum(1 for x in tokens if isinstance(x,dict) and x.get('mark_error')=='quote_budget_deferred'),
              'external_flow_lamports':row.get('external_flow_lamports')}
        if incomplete(source): item['status']='partial_source'
        if prev and not incomplete(source) and not incomplete(prev['source']):
            item['d_cash_sol']=None if cash is None or prev['cash_sol'] is None else cash-prev['cash_sol']
            item['d_known_sol']=None if known is None or prev['known_sol'] is None else known-prev['known_sol']
            a,b=prev.get('external_flow_lamports'),item['external_flow_lamports']
            item['d_external_sol']=(b-a)/1e9 if lamports(a,True) and lamports(b,True) else None
        out.append(item); prev=item
    return {'tz':tz,'days':out,'status':'partial' if any(incomplete(r['source']) for r in out) else 'ok','basis':'Last snapshot per local day in the viewer time zone, including unknown values. known = native + SPL mark + LP mark + refundable rent. cash = native + LP mark + refundable rent (no SPL marks). Deltas require consecutive days and complete source selection. Large files are searched within fixed read bounds; ordering is checked on every row a lookup reads (binary search, backward scan and one neighbour line on each side of the pick), and only an observed inversion marks a day partial.',
            'caveats':['SPL marks drop out when a quote is deferred or a token is unpriced: known then falls without a trade (phantom loss). cash excludes SPL marks and is immune to that, but also misses real token value.',
                       'External deposits/withdrawals are not netted out of either delta; check d_external_sol before reading a jump as profit.',
                       'Refundable rent is a recoverable reserve, not income; native growth can be recovered principal or rent.']}

def read_jsonl(path, cap=64*1024*1024):
    """Whole-file JSONL read for exact window sums; over `cap` the bridge is marked incomplete."""
    rows,meta=[],{'path':str(path),'status':'missing','invalid_lines':0}
    try:
        with open_regular(path) as f:
            size=os.fstat(f.fileno()).st_size
            if size>cap: meta.update(status='over_cap',bytes=size); return rows,meta
            data=f.read(cap+1)
            if len(data)>cap: meta.update(status='over_cap',bytes=len(data)); return rows,meta
        meta.update(status='ok',bytes=size)
        lines=data.splitlines()
        if data and not data.endswith(b'\n'): lines=lines[:-1];meta['partial_line']=True
        for index,line in enumerate(lines):
            if index>=100000: meta.update(status='over_row_cap',truncated=True); break
            if len(line)>1024*1024: meta['invalid_lines']+=1; continue
            try:
                row=json.loads(line)
                if isinstance(row,dict): rows.append(row)
                else: meta['invalid_lines']+=1
            except (ValueError,UnicodeDecodeError): meta['invalid_lines']+=1
    except FileNotFoundError: pass
    except OSError: meta['status']='unavailable'
    if meta['status']=='ok' and incomplete(meta): meta['status']='partial'
    return rows,meta

def keyed(rows, key, meta):
    result={}
    for row in rows:
        if not identifier(row.get(key)):
            meta['invalid_lines']+=1; meta['status']='partial'; continue
        result[row[key]]=row
    return result

def _token_marks(snap):
    return {t['mint']:t['mark_sol'] for t in snap.get('tokens') or [] if isinstance(t,dict) and identifier(t.get('mint')) and number(t.get('mark_sol'))}

def _inline_refund(r):
    ev=r.get('token_rent_evidence')
    if not isinstance(ev,dict): return None
    items=ev.get('refunded')
    if not isinstance(items,list): return None
    if items: return optional_sum(i.get('lamports') if isinstance(i,dict) and lamports(i.get('lamports')) else None for i in items)
    inline=ev.get('inline_closed',[])
    if not isinstance(inline,list) or (ev.get('refunds_unmeasured') and not inline): return None
    return optional_sum(i.get('pre_lamports') if isinstance(i,dict) and lamports(i.get('pre_lamports')) else None for i in inline)

def _funded(r):
    ev=r.get('token_rent_evidence')
    if not isinstance(ev,dict) or not isinstance(ev.get('funded'),list): return None
    return optional_sum(i.get('lamports') if isinstance(i,dict) and lamports(i.get('lamports')) else None for i in ev['funded'])

BRIDGE_NEED=('native_sol','spl_mark_sol','lp_mark_sol','refundable_rent_sol','known_asset_subtotal_sol','slot')

def nav_bridge(memory, now, days=14):
    """Decompose the change in known SOL over the last `days` into additive parts.
    Identity: Δknown = Σ wallet tx deltas + ΔSPL mark + ΔLP mark + Δrefundable rent.
    Port of the nav-bridge study; same per-lifecycle split, no new data source."""
    L=1e9; path=memory/'dlmm_nav.jsonl'
    sources={'nav_start':{},'nav_end':{}}
    b=nav_at(path,now,meta=sources['nav_end'])
    a=nav_at(path,b['ts']-days*86400,meta=sources['nav_start']) if b else None
    out={'basis':'Change in known SOL (native + SPL mark + LP mark + refundable rent) between two NAV snapshots. '
         'This is not NAV/ROI and is never withdrawal + fees - deposit; each component keeps its own basis.','days':days,'sources':sources}
    if not a or not b or a['ts']>=b['ts']:
        out['status']='insufficient_snapshots'; return out
    if not all(number(s.get(k)) for s in (a,b) for k in BRIDGE_NEED):
        out.update(status='unmeasured_snapshots',incomplete_sources=['nav_values']); return out
    kindrows,sources['transaction_kinds']=read_jsonl(memory/'dlmm_transactions.jsonl')
    kinds=keyed(kindrows,'signature',sources['transaction_kinds'])
    txrows,sources['wallet_transactions']=read_jsonl(memory/'dlmm_wallet_transactions.jsonl')
    realrows,sources['realized']=read_jsonl(memory/'dlmm_realized.jsonl')
    closerows,sources['closes']=read_jsonl(memory/'dlmm_closes.jsonl')
    txs=keyed(txrows,'signature',sources['wallet_transactions'])
    realized=keyed(realrows,'position',sources['realized'])
    mode={p:r['mode'] for p,r in keyed(closerows,'position',sources['closes']).items() if identifier(r.get('mode'))}
    values_unknown=[]
    if a.get('wallet_history_complete') is not True or b.get('wallet_history_complete') is not True:
        values_unknown.append('wallet_history_incomplete')
    win=[]
    for r in txs.values():
        if r.get('landed') is False: continue
        if not lamports(r.get('slot')):
            values_unknown.append('transaction_slot'); continue
        if a['slot']<r['slot']<=b['slot']: win.append(r)
    d_known=b['known_asset_subtotal_sol']-a['known_asset_subtotal_sol']
    d_native=b['native_sol']-a['native_sol']; d_rent=b['refundable_rent_sol']-a['refundable_rent_sol']
    d_lp=b['lp_mark_sol']-a['lp_mark_sol']; d_spl=b['spl_mark_sol']-a['spl_mark_sol']
    ma,mb=_token_marks(a),_token_marks(b)
    spl_both=sum(mb[m]-ma[m] for m in set(ma)&set(mb))
    fee={}; per_pos={}; unattr={}; perm=0
    add=lambda d,k,v:d.__setitem__(k,d.get(k,0)+v)
    for r in win:
        k=kinds.get(r.get('signature'),{})
        kind=k.get('kind') if identifier(k.get('kind')) else ('external' if r.get('classification')=='external_transfer' else 'unrecorded')
        if kind=='unrecorded': values_unknown.append('unattributed_transaction')
        for field in ('wallet_delta_lamports','fee_lamports','nonrefundable_account_cost_lamports'):
            if not lamports(r.get(field),field=='wallet_delta_lamports'): values_unknown.append(field)
        # Zero is used only for explicitly labeled measured subtotals below; totals
        # with missing evidence are nulled before returning, never called complete.
        r={**r,**{field:r[field] if lamports(r.get(field),field=='wallet_delta_lamports') else 0
                 for field in ('wallet_delta_lamports','fee_lamports','nonrefundable_account_cost_lamports')}}
        f=fee.setdefault(kind,{'n':0,'failed':0,'lamports':0})
        f['n']+=1; f['lamports']+=r.get('fee_lamports') or 0; f['failed']+=bool(r.get('failed'))
        perm+=r.get('nonrefundable_account_cost_lamports') or 0
        pos=r.get('event_position') or k.get('position')
        if not identifier(pos): pos=None
        delta,fl=r.get('wallet_delta_lamports') or 0,r.get('fee_lamports') or 0
        nonref=r.get('nonrefundable_account_cost_lamports') or 0
        if pos and kind in ('deploy','close','claim','swap'):
            p=per_pos.setdefault(pos,{}); add(p,'n_'+kind,1); add(p,'fee',fl)
            if kind=='swap':
                if not lamports(r.get('refundable_rent_locked_lamports')): values_unknown.append('refundable_rent_locked_lamports')
                locked=r.get('refundable_rent_locked_lamports') if lamports(r.get('refundable_rent_locked_lamports')) else 0
                refunded=_inline_refund(r)
                if refunded is None: values_unknown.append('ata_refunds')
                add(p,'swap_net',delta+fl+nonref+locked-(refunded or 0)); add(p,'ata_refund',refunded or 0); add(p,'swap_rent_locked',locked)
            else:
                funded=_funded(r)
                if funded is None: values_unknown.append('ata_funding')
                add(p,'lp_cash',delta+fl+nonref); add(p,'ata_funded',funded or 0); add(p,'closed',r.get('position_account_closed') is True)
        else:
            add(unattr,kind,delta+fl+nonref); add(unattr,'ext',r.get('external_flow_lamports') or 0)
    R=TV=SW=0.0; complete=0; partial={'n':0,'cash':0.0,'unmeasured_realized':0}; by_mode={}
    for pos,p in per_pos.items():
        rz=(realized.get(pos) or {}).get('realized_sol')
        if not (p.get('n_deploy',0)>=1 and p.get('closed',0)>=1 and number(rz)):
            partial['n']+=1; partial['unmeasured_realized']+=bool(pos in realized and not number(rz))
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
    rent_ledger=d_rent-ata_left+(unattr.get('rent_reclaim',0)+unattr.get('swap',0))/L
    unattributed=sum(v for k,v in unattr.items() if k not in ('rent_reclaim','swap','external','ext'))/L
    comps=[('lp_realized','LP realized (Meteora flows, complete lifecycles)',R),
           ('network_fees','Network fees, all transactions incl. failed',-fees_total),
           ('rent_permanent','Rent: permanent account cost',-perm/L),
           ('rent_ledger','Rent: ledger mismatch (Δrent vs locks, refunds, reclaims)',rent_ledger),
           ('swap_residual','Swap residual (settlement proceeds - Meteora token value)',SW-TV),
           ('spl_mark','SPL mark change, tokens priced at both ends',spl_both),
           ('lp_unrealized','Unrealized: Δ LP mark',d_lp),
           ('external','External transfers',unattr.get('external',0)/L),
           ('unattributed_cash','Unattributed cash (never assumed to be rent)',unattributed),
           ('partial_lifecycles','Partial lifecycles straddling the window',partial['cash']),
           ('spl_coverage','SPL valuation coverage (priced at one end only)',d_spl-spl_both)]
    comps.append(('unexplained','Unexplained residual',d_known-sum(v for _,_,v in comps)))
    # dlmm_closes.jsonl only labels modes here. Legacy corrupt lines are reported; they make the
    # bridge incomplete only when a complete lifecycle in this window has no mode label.
    closes_meta=sources['closes']
    mode_unknown=sum(v['n'] for k,v in by_mode.items() if k=='unknown')
    out['closes_invalid_lines']=closes_meta.get('invalid_lines',0); out['mode_unknown']=mode_unknown
    closes_ok=(closes_meta.get('status') in ('ok','partial') and not closes_meta.get('truncated')
               and not closes_meta.get('partial_line') and (closes_meta.get('status')=='ok' or closes_meta.get('invalid_lines'))
               and mode_unknown==0)
    incomplete_sources=[k for k,m in sources.items() if incomplete(m) and not (k=='closes' and closes_ok)]
    tx_delta=optional_sum(r.get('wallet_delta_lamports') if lamports(r.get('wallet_delta_lamports'),True) else None for r in win)
    if incomplete(sources['wallet_transactions']) or 'transaction_slot' in values_unknown or 'wallet_history_incomplete' in values_unknown: tx_delta=None
    unknown=set(values_unknown)
    component_rows=[]
    for key,label,value in comps:
        # Component attribution needs all journals and value fields; raw NAV
        # deltas can remain measured independently of that decomposition.
        known=not incomplete_sources and not unknown
        if key in ('spl_mark','spl_coverage','lp_unrealized'): known=not any(incomplete(sources[x]) for x in ('nav_start','nav_end'))
        if key=='network_fees': known=not incomplete(sources['wallet_transactions']) and not unknown.intersection(('fee_lamports','transaction_slot','wallet_history_incomplete'))
        if key=='rent_permanent': known=not incomplete(sources['wallet_transactions']) and not unknown.intersection(('nonrefundable_account_cost_lamports','transaction_slot','wallet_history_incomplete'))
        component_rows.append(dict(key=key,label=label,sol=value if known else None,measured_subtotal_sol=value if key!='unexplained' else None))
    if any(c['sol'] is None for c in component_rows[:-1]): component_rows[-1]['sol']=None
    out.update(status='incomplete_sources' if incomplete_sources else 'unmeasured_values' if unknown else 'ok', incomplete_sources=incomplete_sources,
               incomplete_values=sorted(unknown),
               start_ts=a['ts'],end_ts=b['ts'],slots=[a['slot'],b['slot']],d_known_sol=d_known,d_native_sol=d_native,
               sum_tx_delta_sol=None if tx_delta is None else tx_delta/L,transactions=len(win),
               native_identity_exact=None if tx_delta is None else abs(tx_delta/L-d_native)<1e-9,
               components=component_rows,
               fees_by_kind={k:{'n':v['n'],'failed':v['failed'],'sol':v['lamports']/L if not incomplete(sources['wallet_transactions']) and not unknown.intersection(('fee_lamports','transaction_slot','wallet_history_incomplete')) else None} for k,v in sorted(fee.items())},
               positions={'complete':complete,'partial':partial['n'],'realized_unmeasured':partial['unmeasured_realized']},
               by_mode=by_mode if not incomplete_sources and not unknown else {},
               unpriced_tokens=[sum(1 for t in s.get('tokens') or [] if isinstance(t,dict) and t.get('mark_sol') is None) for s in (a,b)])
    return out

def dust_ledger(memory, since, run=None):
    """Deduped receipts are claims. Only finalized balance/account facts verify them.
    The quote is always an off-chain receipt valuation, never on-chain income.
    Missing evidence makes window totals unknown; measured subtotals stay labeled.
    """
    argv=['journalctl','--user','-u','azimuth-sol-rent.service','--since','@%d'%int(since),
          '-n','5000','-o','short-unix','--no-pager']
    out=dict(since=since,status='unavailable',runs=None,executed_tx=0,failed_without_tx=0,deferred=0,
             closed_accounts=0,burned_accounts=0,rent_recovered_lamports=None,fee_lamports=None,
             forfeited_quote_lamports=None,liquid_native_gain_sol=None,nav_effect_sol=None,
             violations=[],rules_complete=False,tx_not_ingested=0,errors=[],duplicates=0,
             source='Rent unit journal; at most 5000 lines / 2 MiB combined output since cutover',
             source_metadata={},transactions=[])
    try: result=(run or bounded_run)(argv,capture_output=True,text=True,timeout=5)
    except (OSError,subprocess.TimeoutExpired): return out
    capture=getattr(result,'capture_status','ok'); text=result.stdout
    size=len(text.encode())+len(getattr(result,'stderr','').encode())
    source=dict(status=capture,returncode=getattr(result,'returncode',None),bytes=size,byte_cap=2*1024*1024)
    out['source_metadata']['journal']=source
    if source['returncode']!=0 or capture!='ok' or size>source['byte_cap']:
        source['status']=capture if capture!='ok' else 'over_cap' if size>source['byte_cap'] else 'command_failed'
        return out
    lines=text.splitlines(); source['lines']=len(lines)
    source['truncated']=len(lines)>=5000
    if source['truncated']: source['status']='partial'
    facts_rows,facts_meta=read_jsonl(memory/'dlmm_wallet_transactions.jsonl')
    facts=keyed(facts_rows,'signature',facts_meta); out['source_metadata']['wallet_transactions']=facts_meta
    receipts={}; reasons={}; invalid=0; out['runs']=0
    for line in lines:
        head,_,body=line.partition(' ')
        if '{' not in body: continue
        try: row=json.loads(body[body.index('{'):]); stamp=float(head)
        except ValueError: invalid+=1; continue
        if not number(stamp) or stamp<since: continue
        if not isinstance(row,dict): invalid+=1; continue
        if 'success' not in row and 'txHash' not in row: continue
        out['runs']+=1
        if row.get('deferred'): out['deferred']+=1
        if row.get('success') is False and not row.get('txHash'):
            out['failed_without_tx']+=1
            reason=clean(str(row.get('error') or row.get('reason') or 'unknown'))[:120]
            reasons[reason]=reasons.get(reason,0)+1
        if row.get('dry_run') is not False: continue
        sig=row.get('txHash')
        if not identifier(sig):
            if sig is not None: invalid+=1
            continue
        if sig in receipts:
            out['duplicates']+=1
            if row!=receipts[sig][1]: receipts[sig]=(stamp,receipts[sig][1],True)
            continue
        receipts[sig]=(stamp,row,False)
    source['invalid_lines']=invalid
    if invalid: source['status']='partial'
    out['errors']=[dict(reason=k,count=v) for k,v in sorted(reasons.items())]
    out['executed_tx']=len(receipts)  # submitted receipt signatures, not confirmed closes
    claimed=dict(transactions=len(receipts),closed_accounts=0,burned_accounts=0)
    claim_rent=[]; claim_fee=[]; claim_quote=[]
    verified=dict(transactions=0,failed=0,unlanded=0,unknown=0,closed_accounts=0,burned_accounts=0,
                  rent_recovered_lamports=0,fee_lamports=0,wallet_delta_lamports=0,forfeited_quote_lamports=0)
    complete=not incomplete(source) and not incomplete(facts_meta); rules_complete=complete
    all_fees=True; all_cash=True; all_rent=True; all_quotes=True
    for sig,(stamp,row,conflict) in receipts.items():
        accounts=row.get('accounts')
        if not isinstance(accounts,list) or any(not isinstance(a,dict) for a in accounts): accounts=[]; conflict=True
        burns=[a for a in accounts if a.get('burn_raw') not in (None,'0',0)]
        rent=optional_sum(a.get('rent_lamports') if lamports(a.get('rent_lamports')) else None for a in accounts)
        quote=optional_sum(a.get('quote_lamports') if lamports(a.get('quote_lamports')) else None for a in burns)
        claimed['closed_accounts']+=len(accounts); claimed['burned_accounts']+=len(burns)
        claim_rent.append(rent); claim_quote.append(quote)
        claim_fee.append(row.get('fee_lamports') if lamports(row.get('fee_lamports')) else None)
        fact=facts.get(sig); detail=dict(signature=sig,time=stamp,status='unknown')
        out['transactions'].append(detail)
        if fact is None: out['tx_not_ingested']+=1
        landed=bool(fact and fact.get('landed') is not False and
                    (fact.get('landed') is True or (lamports(fact.get('slot')) and fact['slot']>0
                     and fact.get('basis')=='finalized_transaction_balances') or
                     (fact.get('failed') is True and lamports(fact.get('fee_lamports')) and lamports(fact.get('wallet_delta_lamports'),True))))
        if fact and fact.get('landed') is False:
            detail['status']='unlanded'; verified['unlanded']+=1
            # No transaction fee is attributed to a transaction proved never landed.
            continue
        if not landed or type(fact.get('failed')) is not bool or conflict:
            verified['unknown']+=1; complete=False; rules_complete=False
            all_fees=all_cash=all_rent=all_quotes=False; continue
        fee=fact.get('fee_lamports'); delta=fact.get('wallet_delta_lamports')
        if lamports(fee): verified['fee_lamports']+=fee
        else: all_fees=False
        if lamports(delta,True): verified['wallet_delta_lamports']+=delta
        else: all_cash=False
        if fact['failed'] is True:
            detail['status']='failed'; verified['failed']+=1
            if burns: out['violations'].append(dict(rule='burn transaction failed on-chain',signature=sig,time=stamp))
            continue  # Atomic failure: no close, rent credit or burned quote.
        verified['transactions']+=1; detail['status']='landed'
        ev=fact.get('token_rent_evidence')
        evidence=ev if isinstance(ev,dict) else {}
        closed={}
        for key,amount in (('refunded','lamports'),('inline_closed','pre_lamports')):
            for a in evidence.get(key) or []:
                if isinstance(a,dict) and identifier(a.get('account')) and lamports(a.get(amount)):
                    closed[a['account']]=(a[amount],a.get('mint'))
        matched=(bool(accounts) and len({a.get('account') for a in accounts if identifier(a.get('account'))})==len(accounts)
                 and all(identifier(a.get('account')) and identifier(a.get('mint'))
                         and closed.get(a['account'])==(a.get('rent_lamports'),a['mint']) for a in accounts)
                 and rent is not None and lamports(fee) and lamports(delta,True) and delta+fee==rent)
        if not matched:
            detail['account_evidence']='unmeasured'; all_rent=all_quotes=False; rules_complete=False; complete=False
            continue
        verified['closed_accounts']+=len(accounts); verified['rent_recovered_lamports']+=rent
        # Mint delta evidence binds the claimed burn quantity to this transaction.
        deltas=fact.get('token_deltas_raw') or {}; expected={}; burn_ok=isinstance(deltas,dict)
        for a in burns:
            raw=a.get('burn_raw'); mint=a.get('mint')
            if not identifier(mint) or not isinstance(raw,str) or not re.fullmatch(r'[0-9]{1,39}',raw): burn_ok=False; continue
            expected[mint]=expected.get(mint,0)+int(raw)
        burn_ok=burn_ok and all(deltas.get(m)==str(-v) for m,v in expected.items())
        if burn_ok:
            verified['burned_accounts']+=len(burns)
            if quote is not None: verified['forfeited_quote_lamports']+=quote
            else: all_quotes=False; rules_complete=False
        else: all_quotes=False; rules_complete=False; complete=False
        for a in burns:
            q=a.get('quote_lamports'); rent_a=a.get('rent_lamports')
            if lamports(q) and lamports(rent_a) and q*2>rent_a:
                out['violations'].append(dict(rule='quote above half rent',signature=sig,time=stamp))
        if burns and number(quote) and lamports(fee) and fee+quote>=rent:
            out['violations'].append(dict(rule='fee + forfeited >= rent',signature=sig,time=stamp))
    claimed.update(rent_recovered_lamports=optional_sum(claim_rent),fee_lamports=optional_sum(claim_fee),
                   forfeited_quote_lamports=optional_sum(claim_quote))
    coverage=not incomplete(source) and not incomplete(facts_meta)
    out.update(receipt_claimed=claimed,verified_subtotal=verified,closed_accounts=verified['closed_accounts'],burned_accounts=verified['burned_accounts'])
    for key,measured in (('rent_recovered_lamports',all_rent),('fee_lamports',all_fees),('forfeited_quote_lamports',all_quotes)):
        out[key]=verified[key] if coverage and measured else None
    if coverage and all_cash: out['liquid_native_gain_sol']=verified['wallet_delta_lamports']/1e9
    if out['fee_lamports'] is not None and out['forfeited_quote_lamports'] is not None:
        out['nav_effect_sol']=-(out['fee_lamports']+out['forfeited_quote_lamports'])/1e9
    out['rules_complete']=rules_complete and all_fees and all_quotes and all_rent
    out['status']='ok' if complete and all_fees and all_cash and all_quotes and all_rent else 'partial'
    return out

def realized_by_mode(memory, since, tz='UTC'):
    """Per local day in `tz` and mode, closes since the cutover from dlmm_realized.jsonl (the arbiter).
    A null realized figure is counted as unmeasured, never added as 0."""
    realrows,meta=read_jsonl(memory/'dlmm_realized.jsonl')
    closerows,closemeta=read_jsonl(memory/'dlmm_closes.jsonl')
    mode={p:r['mode'] for p,r in keyed(closerows,'position',closemeta).items() if identifier(r.get('mode'))}
    days={}; z=zone(tz)
    for r in keyed(realrows,'position',meta).values():
        t=r.get('closed_at')
        if not number(t): meta['status']='partial'; meta['invalid_lines']+=1; continue
        if t<since: continue
        day=local_day(t,z).isoformat(); m=mode.get(r.get('position'),'unknown')
        cell=days.setdefault(day,{}).setdefault(m,{'closes':0,'measured':0,'unmeasured':0,'realized_sol':None})
        cell['closes']+=1
        if number(r.get('realized_sol')): cell['measured']+=1; cell['realized_sol']=(cell['realized_sol'] or 0)+r['realized_sol']
        else: cell['unmeasured']+=1
    return {'tz':tz,'since':since,'status':'partial' if incomplete(meta) or incomplete(closemeta) else 'ok','sources':{'realized':meta,'closes':closemeta},'days':days,'basis':'Measured subtotal of realized_sol by close time (local day in the viewer time zone) and mode. Null realized = unmeasured; a wholly unmeasured cohort is Unknown, not 0.'}

def panel(call, *args):
    """Malformed evidence in one new panel cannot freeze unrelated collections."""
    try: return call(*args)
    except Exception as error: return {'status':'unavailable','collection_error':'Panel evidence could not be read: '+type(error).__name__}

def cutover(since, now): return float(since) if since and float(since)>0 else now-7*86400  # 0/absent = the last 7 days

def daily(profile, since, zones, now=None):
    """Day-bucketed panels, once per requested IANA zone."""
    now=now or time.time(); memory=profile/'memories'; since=cutover(since,now)
    return {'collected_at':now,'by_tz':{tz:{'north_star':panel(north_star,memory,now,CALENDAR_DAYS,tz),'realized':panel(realized_by_mode,memory,since,tz)} for tz in zones}}

def collect(profile, state, since=None, zones=('UTC',)):
    now=time.time();memory=profile/'memories';sources=[];events=[]
    since=cutover(since,now)
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
    events.sort(key=lambda e:e.get('time') or 0,reverse=True)
    return clean(own_only({'collected_at':now,**daily(profile,since,zones,now),'nav_bridge':panel(nav_bridge,memory,now),'live':{'dust':panel(dust_ledger,memory,since)},'nav':nav[-1] if nav else {},'journal':events,'sources':sources,'hermes':hermes,'services':services}))

if __name__=='__main__':
    # argv: profile state since [zones,comma,separated] [daily]; `daily` refreshes only the day-bucketed panels.
    zones=tuple(sys.argv[4].split(',')) if len(sys.argv)>4 and sys.argv[4] else ('UTC',)
    if len(sys.argv)>5 and sys.argv[5]=='daily': out=clean(daily(Path(sys.argv[1]),sys.argv[3],zones))
    else: out=collect(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3] if len(sys.argv)>3 else None,zones)
    print(json.dumps(out,allow_nan=False))
