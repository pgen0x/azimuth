#!/usr/bin/env python3
"""Paired exit-policy replay and prospective quote-only dry run. Never signs trades."""
import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
import time
import urllib.request

from dlmm_accounting import report, refund_cash_bounds, rows
from dlmm_profit_acceptance import position_profit_acceptance
from dlmm_shadow import read_native_risk_mark, liquidation_observation

STRATEGIES = {'current': {}, 'net_tp_0_1pct': {'tp': .001},
              'net_stop_1pct': {'sl': -.01}, 'net_tp_and_stop': {'tp': .001, 'sl': -.01}}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    os.chmod(temp, 0o600)
    temp.replace(path)


def finite(x):
    return type(x) in (float, int) and math.isfinite(x)


def trigger(quote, entry, policy, cost, start):
    ts = quote.get('observed_at')
    value = quote.get('minimum_quoted_assets_change_before_network_fees_sol')
    if (quote.get('status') != 'measured' or quote.get('inventory_source') != 'onchain_sol_inventory'
            or not finite(ts) or ts < max(start, entry['deployed_at']+120)
            or not finite(value) or not finite(quote.get('position_updated_at'))
            or not 0 <= ts-quote['position_updated_at'] <= 10
            or quote.get('position') != entry['position']):
        return None
    size = entry.get('size_sol')
    if not finite(size) or size <= 0:
        return None
    net = round(value*1e9)-cost
    ratio = net/(size*1e9)
    if ('tp' in policy and ratio >= policy['tp']) or ('sl' in policy and ratio <= policy['sl']):
        return {'observed_at': ts, 'modeled_net_lamports': net,
                'quoted_minimum_before_cost_lamports': round(value*1e9),
                'cost_budget_lamports': cost, 'reason': 'net_take_profit' if ratio >= 0 else 'net_stop'}
    return None


def entry_eligible(entry, rule):
    """Only recorded pre-entry features; unknown measurements do not qualify."""
    if not rule:return True
    signal=entry.get('signal') or {}
    gates=signal.get('entry_live_gates') or {}
    stamp=gates.get('observed_at');deployed=entry.get('deployed_at')
    if not finite(stamp) or not finite(deployed) or not 0 <= deployed-stamp <= 120:return False
    if 'min_pool_fee_pct' in rule:
        pool_fee=signal.get('fee_pct')
        if not finite(pool_fee) or pool_fee < rule['min_pool_fee_pct']:return False
        if set(rule)=={'min_pool_fee_pct'}:return True
    fee=gates.get('live_fee_tvl_ratio');traders=signal.get('unique_traders')
    minutes={'5m':5,'30m':30}.get(gates.get('fee_timeframe'))
    if not minutes or not finite(fee) or not finite(traders):return False
    return fee*60/minutes >= rule['fee_tvl_pct_per_hour'] and traders >= rule['min_traders']


def known_at(chain, groups, facts):
    signatures = set(chain['recorded_signatures'])
    for group in groups:
        signatures.update(group.get('refund_signatures', []))
    timestamps = [facts.get(s, {}).get('observed_at') for s in signatures]
    if not timestamps or any(not finite(t) for t in timestamps):
        return float('inf')
    return max(timestamps)


def load(profile, end):
    memory = profile/'memories'
    ledger = report(profile, as_of=end)
    entries = sorted([json.loads(p.read_text()) for p in (memory/'dlmm_entries').glob('*.json')],
                     key=lambda e: e.get('deployed_at', 0))
    quotes = {}
    for q in rows(memory/'dlmm_liquidation_quotes.jsonl'):
        if q.get('observed_at', 0) <= end:
            quotes.setdefault(q['position'], []).append(q)
    closes = {r['position']: r for r in rows(memory/'dlmm_closes.jsonl') if r.get('position') and not r.get('dry_run')}
    facts = {r['signature']: r for name in ('dlmm_transaction_facts.jsonl', 'dlmm_wallet_transactions.jsonl')
             for r in rows(memory/name) if r.get('observed_at', 0) <= end}
    return ledger, entries, quotes, closes, facts


def aggregate(ledger, positions):
    chains = {c['root_chain_id']: c for c in ledger['chains']}
    remaining = set(positions)
    lower = upper = 0
    for group in ledger['rent_refund_groups']:
        selected = remaining & set(group['root_chain_ids'])
        if not selected:
            continue
        bounds = refund_cash_bounds(group, chains, selected)
        if bounds is None:
            raise ValueError('Unproved refund group')
        lower += bounds[0]; upper += bounds[1]; remaining -= selected
    if remaining:
        raise ValueError('Missing cash group')
    return lower, upper


def backtest(profile, output, start, split):
    end = time.time()
    ledger, entries, quotes, closes, facts = load(profile, end)
    acceptance = position_profit_acceptance(ledger, entries, start, end)
    chains = {c['root_chain_id']: c for c in ledger['chains']}
    byid = {e['position']: e for e in entries}
    costs = []
    for row in acceptance['positions']:
        chain = chains.get(row['root'])
        groups = [g for g in ledger['rent_refund_groups'] if row['root'] in g['root_chain_ids']]
        if (row['deployed_at'] < split and row['cash_lower_lamports'] is not None
                and known_at(chain, groups, facts) < split):
            # Count shared cleanup fee fully: conservative training cost, not allocated PnL.
            cleanup = sum(p['fee_lamports'] for g in groups for p in g.get('refund_components', []))
            costs.append(chain['network_fee_lamports']+chain.get('nonrefundable_account_cost_lamports', 0)+cleanup)
    if len(costs) < 5:
        raise ValueError('Insufficient pre-split finalized cost examples')
    costs.sort()
    budget = max(25000, costs[math.ceil(.9*len(costs))-1])
    config = dict(version=1, frozen_at=end, historical_start=start, validation_start=split,
                  strategies=STRATEGIES, cost_budget_lamports=budget,
                  training_cost_observations=len(costs), minimum_hold_seconds=120,
                  size_basis='same actual entries and size as running strategy',
                  rent_assumption='return all refundable principal; cleanup fee included in cost budget',
                  stress_extra_lamports=[0, 100000, 1513840],
                  baseline_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write(output/'config.json', config)
    results = []
    details = []
    for period in ('training', 'validation'):
        cohort = [r for r in acceptance['positions'] if (r['deployed_at'] < split) == (period == 'training')]
        for strategy, policy in STRATEGIES.items():
            held = set(); modeled = []; unknown = []; wins = losses = covered_quotes = 0
            for row in cohort:
                entry = byid[row['position']]
                if row['cash_lower_lamports'] is None:
                    unknown.append(row['position']); continue
                close = closes.get(row['position'], {})
                close_ts = close.get('ts', 0)
                # Do not extend hypothetical holding past finalized deletion.
                close_facts = [facts.get(s, {}) for s in chains[row['root']]['recorded_signatures']]
                deleted = [f['block_time'] for f in close_facts if f.get('position_account_closed') is True and finite(f.get('block_time'))]
                if deleted: close_ts = min(close_ts, min(deleted))
                eligible_quotes = [q for q in quotes.get(row['position'], []) if q.get('status') == 'measured'
                    and q.get('inventory_source') == 'onchain_sol_inventory'
                    and entry['deployed_at']+120 <= q.get('observed_at', 0) < close_ts]
                covered_quotes += bool(eligible_quotes)
                decision = None
                for quote in sorted(quotes.get(row['position'], []), key=lambda q:q['observed_at']):
                    if quote['observed_at'] >= close_ts: break
                    decision = trigger(quote, entry, policy, budget, entry['deployed_at'])
                    if decision: break
                if decision:
                    modeled.append(decision['modeled_net_lamports'])
                    lo = hi = decision['modeled_net_lamports']
                else:
                    held.add(row['root']);lo,hi=row['cash_lower_lamports'],row['cash_upper_lamports']
                wins += lo > 0;losses += hi <= 0
                details.append(dict(period=period,strategy=strategy,position=row['position'],pair=entry.get('pair'),
                                    actual_cash_lower_lamports=row['cash_lower_lamports'],
                                    actual_cash_upper_lamports=row['cash_upper_lamports'],decision=decision,
                                    measured_quote_count=sum(q.get('status')=='measured' for q in quotes.get(row['position'],[]))))
            lo,hi=aggregate(ledger,held)
            results.append(dict(period=period,strategy=strategy,entries=len(cohort),unknown=len(unknown),
                                evaluated=len(cohort)-len(unknown),positive=wins,nonpositive=losses,
                                modeled_exits=len(modeled),actual_exit_fallback=len(held),
                                positions_with_preclose_native_quotes=covered_quotes,
                                net_lower_lamports=lo+sum(modeled),net_upper_lamports=hi+sum(modeled),
                                stress_lower_lamports={str(extra):lo+sum(modeled)-extra*len(modeled)
                                                       for extra in config['stress_extra_lamports']}))
    result=dict(checked_at=end,config=config,results=results,positions=details,limits=[
        'Current baseline is recorded deployed policy across historical revisions, not a full replay of today code.',
        'Same entries and sizes; counterfactual earlier exits do not recycle freed capital into extra trades.',
        'Alternative exits use first available timestamped native quote, not guaranteed fills; missing quotes cannot establish no opportunity. No-trigger and missing-quote paths retain actual baseline outcomes as a partial-replay assumption, not a validated counterfactual.',
        'Modeled net subtracts pre-split p90 observed lifecycle network/failed transaction/nonrefundable/cleanup costs from minimum quote proceeds.',
        'Pool fees/impact and quoted slippage are embedded in quote; full refundable rent return assumed. Stress adds 100k lamports or one unrecovered token-account rent.',
        'Alternative costs and post-withdrawal liquidity can differ. Modeled results are not proved all-cost realized profit.',
        'Validation is chronological retrospective, not untouched research data; these histories have been inspected before. Forward dry run is the untouched check.',
        'Unknown baseline positions remain excluded from paired sums and included in denominator. Shared refunds counted once per actual-exit subset.'])
    write(output/'backtest.json',result)
    lines=['# Net exit-policy experiment','',f'Frozen lifecycle cost budget: {budget} lamports; training observations: {len(costs)}.',
           '', '| Period | Strategy | Evaluated / total | Modeled exits | Wins / losses | Net SOL lower–upper |',
           '|---|---|---:|---:|---:|---:|']
    for r in results:
        lines.append(f"| {r['period']} | {r['strategy']} | {r['evaluated']}/{r['entries']} | {r['modeled_exits']} | {r['positive']}/{r['nonpositive']} | {r['net_lower_lamports']/1e9:+.9f} … {r['net_upper_lamports']/1e9:+.9f} |")
    lines+=['','## Limits','']+['- '+x for x in result['limits']]
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return dict(cost_budget_lamports=budget,results=results)


def dry_tick(profile, output):
    config=json.loads((output/'config.json').read_text())
    config_hash=hashlib.sha256((output/'config.json').read_bytes()).hexdigest()
    state_path=output/'dry-state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else dict(config_hash=config_hash,positions={})
    if state['config_hash'] != config_hash: raise ValueError('Frozen experiment config changed')
    memory=profile/'memories';now=time.time()
    closed={r['position'] for r in rows(memory/'dlmm_closes.jsonl') if r.get('position') and not r.get('dry_run')}
    wallets={r['position']:r['wallet'] for r in rows(memory/'dlmm_transactions.jsonl') if r.get('kind')=='deploy'}
    active=[]
    path_rows=None
    for f in (memory/'dlmm_entries').glob('*.json'):
        e=json.loads(f.read_text())
        if e.get('deployed_at',0) < config['frozen_at'] or e['position'] not in wallets:continue
        pos=e['position'];row=state['positions'].setdefault(pos,dict(entry=e,last_observed=0,decisions={}))
        if config.get('price_path_filter') and 'entry_path_evidence' not in row:
            from dlmm_price_path_features import assess_entry
            if path_rows is None:path_rows=list(rows(memory/'dlmm_candidate_price_paths.jsonl'))
            row['entry_path_evidence']=dict(assess_entry(row['entry'],path_rows,config['price_path_filter']),
                                            evaluated_at=now)
        eligible=entry_eligible(row['entry'],config.get('entry_filter'))
        if config.get('price_path_filter'):eligible=eligible and row['entry_path_evidence']['qualifies']
        if not eligible:
            for name in config['strategies']:
                if name != 'current':
                    row['decisions'].setdefault(name,dict(observed_at=now,reason='entry_filter_skip',modeled_net_lamports=0))
        if pos in closed:row['closed_observed_at']=row.get('closed_observed_at',now)
        else:active.append(row)
    attempted=0
    if active and any(config['strategies'].values()):
        row=min(active,key=lambda r:r['last_observed']);e=row['entry'];deadline=time.monotonic()+20
        def fetch(url):
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'azimuth-dry-net/1'}),
                                        timeout=max(.1,min(8,deadline-time.monotonic()))) as response:return json.load(response)
        mark=read_native_risk_mark(profile,e,wallets[e['position']],deadline)
        try:
            # No indexed fallback: missing native inventory stays unmeasured.
            if mark is None:raise ValueError('native mark unavailable')
            q=dict(position=e['position'],pool=e['pool'],**liquidation_observation(e,wallets[e['position']],fetch,native_mark=mark))
        except Exception as error:q=dict(position=e['position'],observed_at=time.time(),status='unmeasured',reason=type(error).__name__)
        with (output/'dry-quotes.jsonl').open('a') as stream:stream.write(json.dumps(q,allow_nan=False)+'\n')
        for name,policy in config['strategies'].items():
            if name in row['decisions']:continue
            decision=trigger(q,e,policy,config['cost_budget_lamports'],config['frozen_at'])
            if decision:row['decisions'][name]=decision
        row['last_observed']=time.time();attempted=1
    state.update(checked_at=time.time(),active_positions=len(active),last_tick_quote_attempts=attempted)
    write(state_path,state)
    dry_summary(profile, output, config, state)
    return dict(checked_at=state['checked_at'],active_positions=len(active),tracked_positions=len(state['positions']),quote_attempts=attempted)


def dry_summary(profile, output, config, state):
    result=dict(checked_at=time.time(),started_at=config['frozen_at'],
                tracked_entries=len(state['positions']),strategies=[],
                basis='prospective decisions; modeled exits are estimates, current strategy uses finalized cash when complete')
    if state['positions']:
        ledger=report(profile,as_of=result['checked_at'])
        entries=[r['entry'] for r in state['positions'].values()]
        accepted=position_profit_acceptance(ledger,entries,config['frozen_at'],result['checked_at'])
        actual={r['position']:r for r in accepted['positions']}
        for name in config['strategies']:
            held=set();modeled=[];pending=0;skipped=0
            for pos,row in state['positions'].items():
                proof=actual.get(pos,{})
                if proof.get('cash_lower_lamports') is None:
                    pending+=1;continue
                decision=row['decisions'].get(name)
                if decision and decision['reason']=='entry_filter_skip':skipped+=1
                elif decision:modeled.append(decision['modeled_net_lamports'])
                else:held.add(proof['root'])
            lo,hi=aggregate(ledger,held)
            result['strategies'].append(dict(strategy=name,paired_completed=len(held)+len(modeled)+skipped,skipped_entries=skipped,
                pending_or_unmeasured=pending,modeled_exits=len(modeled),
                paired_net_lower_lamports=lo+sum(modeled),paired_net_upper_lamports=hi+sum(modeled)))
    write(output/'dry-summary.json',result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['backtest','dry-tick'])
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--start',type=float,default=1791974850)
    parser.add_argument('--split',type=float,default=1792252800)  # Oct 18 00:00 UTC
    args=parser.parse_args()
    if args.command=='backtest' and (args.output/'config.json').exists():raise ValueError('Use a new output directory; config is immutable')
    result=backtest(args.profile,args.output,args.start,args.split) if args.command=='backtest' else dry_tick(args.profile,args.output)
    print(json.dumps(result,allow_nan=False))

if __name__=='__main__':main()
