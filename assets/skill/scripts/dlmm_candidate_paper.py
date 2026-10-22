"""Observe paired paper LPs and fresh exit quotes without live entries or trades."""
import argparse
import collections
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.parse
import urllib.request

from dlmm_candidate_replay import replay
from dlmm_fee_forecast import candidate_fee_forecast, sample_hash
from dlmm_net_experiment import write
from dlmm_shadow import iter_rows, validate_candidate_snapshot, SOL_MINT

MODEL = dict(capital=100000000, network_cost=26151, entry_bps=200, exit_bps=300, max_share_bps=100)
STRATEGIES = {'current_geometry': 0, 'passive_one_bin_below': 1}


def error_reason(error):
    # Exception text from subprocess/HTTP libraries may contain URLs or secrets.
    message=str(error)
    return message if type(error) is ValueError and re.fullmatch(r'[a-z_]{1,100}',message) else type(error).__name__


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def trading():
    try:
        for line in Path('/proc/net/unix').read_text().splitlines():
            fields = line.split()
            if (len(fields)==8 and fields[4:6]==['0001','01'] and int(fields[3],16)&0x10000
                    and fields[7].startswith(('@azimuth-dlmm-entry-', '@azimuth-dlmm-swap-'))):
                return True
        return False
    except OSError:
        return True


def snapshot(profile, pool, mint, mode, anchor=None):
    if trading():
        raise ValueError('wallet_trade_active')
    command=['node', str(profile/'skills/solana-dlmm/scripts/dlmm_executor.js'),
             'candidate-bin-snapshot', pool, '69', '16']
    if anchor is not None:
        command.append(str(anchor))
    started=time.time()
    raw=subprocess.check_output(command, stderr=subprocess.DEVNULL, timeout=12)
    row=json.loads(raw)
    if row.get('status')=='deferred':
        raise ValueError('wallet_trade_active')
    if row.get('status')!='observed' or row.get('pool')!=pool:
        raise ValueError('snapshot_identity_mismatch')
    row.update(pool=pool, base_mint=mint, mode=mode, collected_at=time.time(), status='observed')
    validate_candidate_snapshot(row,pool,mint)
    if not started-1 <= row['ts'] <= row['collected_at'] or row['collected_at']-row['ts']>10:
        raise ValueError('stale_snapshot')
    if anchor is not None and row['anchor_bin']!=anchor:
        raise ValueError('terminal_anchor_mismatch')
    return row


def quoted_exit(inventory, mint, terminal_ts, config, fetch, clock=time.time):
    """Quote inferred raw inventory, retaining cost assumptions separately."""
    if not 0 <= clock()-terminal_ts <= 30:
        raise ValueError('stale_inventory')
    amount=int(inventory['terminal_token_raw'])
    if not 0 <= amount < 2**64:
        raise ValueError('invalid_inventory')
    quote=None;minimum=0
    if amount:
        query=urllib.parse.urlencode(dict(inputMint=mint,outputMint=SOL_MINT,amount=amount,slippageBps=100))
        quote=fetch('https://api.jup.ag/swap/v1/quote?'+query)
        values=[quote.get(k) for k in ('inAmount','outAmount','otherAmountThreshold')]
        if (not all(isinstance(v,str) and v.isascii() and v.isdigit() for v in values)
                or quote.get('inputMint')!=mint or quote.get('outputMint')!=SOL_MINT
                or quote.get('swapMode')!='ExactIn' or type(quote.get('slippageBps')) is not int
                or quote['slippageBps']!=100):
            raise ValueError('invalid_quote')
        incoming,out,minimum=map(int,values)
        if incoming!=amount or not 0<minimum<=out<2**64:
            raise ValueError('quote_amount_mismatch')
    if not 0 <= clock()-terminal_ts <= 30:
        raise ValueError('inventory_expired_during_quote')
    net=(inventory['terminal_sol_lamports']+inventory['unspent_lamports']+minimum-config['capital']
         -config['network_cost']-inventory['entry_friction_lamports'])
    return dict(status='quoted_model', observed_at=clock(), quote=quote,
                quoted_minimum_net_lamports=net, extra_execution_stress_lamports=net-100000,
                unrecovered_ata_stress_lamports=net-1513840,
                basis='inferred_inventory_plus_fresh_sell_quote_minus_estimated_costs; not_executed_profit')


def fetch_quote(url):
    if trading():
        raise ValueError('wallet_trade_active')
    time.sleep(2.1)
    if trading():
        raise ValueError('wallet_trade_active')
    request=urllib.request.Request(url,headers={'User-Agent':'dlmm-paper/1.0'})
    with urllib.request.urlopen(request,timeout=8) as response:
        return json.load(response)


def tick(profile, output):
    now=time.time();config_file=output/'config.json'
    if not config_file.exists():
        write(config_file,dict(version=1,frozen_at=now,model=MODEL,strategies=STRATEGIES,
            horizon_seconds=3600,terminal_grace_seconds=600,max_open=2,retry_seconds=300,
            selection='Recent forecast pool identities, least attempted pool first. Fresh native baseline and complete prior required. No live position dependency.',
            purpose='Observational paired paper cohort, not a validated winner or finite-capital portfolio.',
            evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            replay_sha256=hashlib.sha256(Path(__file__).with_name('dlmm_candidate_replay.py').read_bytes()).hexdigest(),
            limitations=['Inferred fixed shares omit added-liquidity effects. 1% share cap is a modeling restriction.',
                'Quotes are not fills. Network and entry composition costs are estimated; full principal rent recovery assumed.',
                'Two open observations is a collection budget, not wallet capital accounting.'],promotion_allowed=False))
    config=json.loads(config_file.read_text());state_file=output/'state.json'
    state=json.loads(state_file.read_text()) if state_file.exists() else dict(config_hash=digest(config),active=[],attempted={})
    if state['config_hash']!=digest(config):
        raise ValueError('frozen_config_changed')
    if (config['evaluator_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            or config['replay_sha256']!=hashlib.sha256(Path(__file__).with_name('dlmm_candidate_replay.py').read_bytes()).hexdigest()):
        raise ValueError('frozen_evaluator_changed')
    result=dict(checked_at=now,status='idle',active=len(state['active']),promotion_allowed=False)
    due=sorted((r for r in state['active'] if r['target']<=now),key=lambda r:r['target'])
    if due:
        item=due[0];record=json.loads((output/'entries'/f"{item['id']}.json").read_text())
        outcome=dict(id=item['id'],target=item['target'],status='unmeasured',strategies={},config_hash=state['config_hash'])
        if now>item['target']+config['terminal_grace_seconds']:
            outcome['reason']='terminal_deadline_missed'
        else:
            try:
                terminal=snapshot(profile,record['pool'],record['mint'],record['mode'],record['base']['active_bin'])
                outcome.update(terminal=terminal,terminal_sha256=sample_hash(terminal))
                for name,offset in config['strategies'].items():
                    inventory=None
                    try:
                        inventory=replay(record['base'],terminal,record['below'],offset,**config['model'])
                        quote=quoted_exit(inventory,record['mint'],terminal['ts'],config['model'],fetch_quote)
                        outcome['strategies'][name]=dict(quote,inventory=inventory)
                    except (ValueError,KeyError,TypeError,OSError) as error:
                        outcome['strategies'][name]=dict(status='unmeasured',reason=error_reason(error),inventory=inventory)
                outcome['status']='paired' if all(x['status']=='quoted_model' for x in outcome['strategies'].values()) else 'unmeasured'
            except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as error:
                # Preserve the first scheduled observation attempt as missing;
                # never retry until a later, more profitable market snapshot.
                outcome['reason']=error_reason(error)
        outcome['observed_at']=time.time()
        write(output/'outcomes'/f"{item['id']}.json",outcome)
        state['active']=[r for r in state['active'] if r['id']!=item['id']]
        result.update(status='terminal_observed',outcome=outcome['status'])
    elif len(state['active'])<config['max_open']:
        recent={}
        for f in iter_rows(profile/'memories/dlmm_candidate_fee_forecasts.jsonl'):
            if (f.get('status')=='frozen_prediction' and 0<=now-f['recorded_at']<=900
                    and f['pool'] not in {a['pool'] for a in state['active']}):
                recent[f['pool']]=f
        ready=[f for f in recent.values() if now-state['attempted'].get(f['pool'],0)>=config['retry_seconds']]
        if ready:
            source=min(ready,key=lambda f:(state['attempted'].get(f['pool'],0),-f['recorded_at'],f['pool']))
            pool,mint,mode=source['pool'],source['base_mint'],source['mode']
            state['attempted'][pool]=now
            history=[s for s in iter_rows(profile/'memories/dlmm_candidate_bin_samples.jsonl')
                     if s.get('pool')==pool and s.get('status')=='observed' and 0<=now-s.get('collected_at',0)<=1800]
            try:
                base=snapshot(profile,pool,mint,mode)
                frozen=time.time()
                forecast=candidate_fee_forecast(base,history,frozen,validate_candidate_snapshot,
                    frozen_geometry=source['bins_below'],frozen_horizon=config['horizon_seconds'])
                if forecast['status']!='frozen_prediction':
                    raise ValueError('complete_prior_required')
                # Check both allocation models before reserving an observation.
                same=dict(base,ts=base['ts']+0.001)
                for offset in config['strategies'].values():
                    replay(base,same,source['bins_below'],offset,**config['model'])
                record=dict(pool=pool,mint=mint,mode=mode,below=source['bins_below'],base=base,
                            frozen_at=frozen,forecast=forecast,config_hash=state['config_hash'])
                ident=digest(record);record['id']=ident
                write(output/'entries'/f'{ident}.json',record)
                state['active'].append(dict(id=ident,pool=pool,target=base['ts']+config['horizon_seconds']))
                result.update(status='paper_entry_frozen',id=ident)
            except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as error:
                result.update(status='entry_unmeasured',reason=error_reason(error))
        state['attempted']={p:t for p,t in state['attempted'].items() if now-t<=86400}
    write(state_file,state)
    outcomes=[json.loads(p.read_text()) for p in (output/'outcomes').glob('*.json')]
    summary=dict(result,active=len(state['active']),completed=len(outcomes),
                 statuses=dict(collections.Counter(r['status'] for r in outcomes)),net_cash_profit_proved=False)
    write(output/'summary.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    with (a.output/'runner.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print(json.dumps(tick(a.profile,a.output)))
