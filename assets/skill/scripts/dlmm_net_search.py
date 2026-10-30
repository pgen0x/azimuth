#!/usr/bin/env python3
"""Bounded training-only exit search; validate only the frozen winner. No trades."""
import argparse
import itertools
import json
from pathlib import Path
import time
from dlmm_net_experiment import load, aggregate, trigger, write, entry_eligible
from dlmm_profit_acceptance import position_profit_acceptance


def policies():
    # Fixed before scoring. Do not expand the grid in response to holdout results.
    for tp,sl in itertools.product((None,.0005,.001,.002,.003,.005),(None,-.0025,-.005,-.01,-.02)):
        if tp is None and sl is None:continue
        yield f'tp_{tp}_sl_{sl}',dict(**({'tp':tp} if tp is not None else {}),**({'sl':sl} if sl is not None else {}))


def evaluate(data,start,end,policy,cost,entry_filter=None):
    ledger,entries,quotes,closes,facts=data
    rows=position_profit_acceptance(ledger,entries,start,end)['positions']
    entries={e['position']:e for e in entries};chains={c['root_chain_id']:c for c in ledger['chains']}
    held=set();modeled=[];details=[];missing=0;covered=0;skipped=0
    for row in rows:
        if not entry_eligible(entries[row['position']],entry_filter):
            skipped+=1
            continue
        if row['cash_lower_lamports'] is None:
            missing+=1;continue
        entry=entries[row['position']]
        deadline=closes.get(row['position'],{}).get('ts',0)
        deletions=[facts.get(s,{}) for s in chains[row['root']]['recorded_signatures']]
        deleted=[f['block_time'] for f in deletions if f.get('position_account_closed') is True and isinstance(f.get('block_time'),(int,float))]
        if deleted:deadline=min(deadline,min(deleted))
        decision=None
        ordered=sorted([q for q in quotes.get(row['position'],[]) if q.get('observed_at',0)<deadline],key=lambda q:q['observed_at'])
        covered+=any(q.get('status')=='measured' and q.get('inventory_source')=='onchain_sol_inventory' for q in ordered)
        for q in ordered:
            decision=trigger(q,entry,policy,cost,entry['deployed_at'])
            if decision:break
        if decision:
            modeled.append(decision['modeled_net_lamports']);lo=hi=decision['modeled_net_lamports']
        else:held.add(row['root']);lo,hi=row['cash_lower_lamports'],row['cash_upper_lamports']
        details.append(dict(position=row['position'],pair=entry.get('pair'),decision=decision,
                            net_lower_lamports=lo,net_upper_lamports=hi))
    lo,hi=aggregate(ledger,held)
    return dict(entries=len(rows),evaluated=len(details),skipped_entries=skipped,unknown=missing,quote_covered=covered,
                modeled_exits=len(modeled),net_lower_lamports=lo+sum(modeled),net_upper_lamports=hi+sum(modeled),
                extra_cost_stress_lamports=lo+sum(modeled)-100000*len(modeled),
                unrecovered_ata_stress_lamports=lo+sum(modeled)-1513840*len(modeled),
                positive=sum(r['net_lower_lamports']>0 for r in details),
                nonpositive=sum(r['net_upper_lamports']<=0 for r in details),positions=details)


def choose(scored):
    # A late-settling loser can reverse a positive partial sum. Require the
    # entire selected cohort to be measured before ranking its net return.
    eligible=[r for r in scored if r['training']['modeled_exits']>=3
              and r['training']['evaluated']>=10
              and r['training'].get('unknown')==0
              and r['training']['extra_cost_stress_lamports']>0]
    if not eligible:return None
    return max(eligible,key=lambda r:(r['training']['extra_cost_stress_lamports'],r['training']['net_lower_lamports'],r['name']))


def run(profile,output,source):
    if (output/'protocol.json').exists():raise ValueError('New experiment directory required')
    config=json.loads((source/'config.json').read_text())
    start=1792281600  # 2026-10-18 00:00 UTC
    split=1792454400  # 2026-10-20 00:00 UTC
    end=config['frozen_at']  # Existing prospective dry run is kept separate.
    grid=list(policies())
    protocol=dict(created_at=time.time(),start=start,split=split,end=end,policies=dict(grid),
                  cost_budget_lamports=config['cost_budget_lamports'],cost_source=str(source/'config.json'),
                  selection='Max strictly positive training lower net under +100000 lamports per modeled exit; no unknown selected outcomes, >=3 modeled exits and >=10 evaluated entries.',
                  holdout='Score only the frozen training winner on subsequent period; no retuning after inspecting validation.',
                  limitation='Historical periods were previously inspected. This is a retrospective chronological challenge, not pristine holdout. Prospective dry run is independent.')
    write(output/'protocol.json',protocol)
    training=load(profile,split-0.001)
    baseline_train=evaluate(training,start,split-0.001,{},config['cost_budget_lamports'])
    scored=[dict(name=name,policy=policy,training=evaluate(training,start,split-0.001,policy,config['cost_budget_lamports'])) for name,policy in grid]
    write(output/'training-grid.json',scored)
    winner=choose(scored)
    write(output/'selection.json',winner or {'status':'no_eligible_candidate'})
    if winner:
        validation=load(profile,end)
        baseline=evaluate(validation,split,end,{},config['cost_budget_lamports'])
        outcome=evaluate(validation,split,end,winner['policy'],config['cost_budget_lamports'])
        result=dict(protocol=protocol,winner=winner,training_baseline=baseline_train,validation_baseline=baseline,validation=outcome,
                    positive_both_periods=winner['training']['net_lower_lamports']>0 and outcome['net_lower_lamports']>0,
                    stress_positive_both=winner['training']['extra_cost_stress_lamports']>0 and outcome['extra_cost_stress_lamports']>0,
                    every_validation_position_positive=outcome['unknown']==0 and outcome['positive']==outcome['entries'],
                    promotion_allowed=False,
                    limitations=['Partial quote replay with actual-exit fallback on missing/no-trigger samples.',
                                 'Net modeled exits include frozen lifecycle costs, quote fees/impact/slippage; refundable principal assumed returned.',
                                 'No reuse of early-exit capital, no unobserved fills, no guaranteed executable quotes.',
                                 'Grid search creates selection bias. Positive historical totals alone never authorize live promotion.'])
        write(output/'result.json',result)
        # Keep the same dry runner: original strategy plus exactly the selected alternative.
        forward=dict(config,frozen_at=time.time(),strategies={'current':{},'training_selected':winner['policy']},
                     selected_from=str(output/'selection.json'))
        write(output/'config.json',forward)
        compact=lambda r:{k:v for k,v in r.items() if k!='positions'}
        print(json.dumps(dict(selected=winner['policy'],training=compact(winner['training']),validation=compact(outcome),
                              validation_baseline=compact(baseline),positive_both=result['positive_both_periods'],stress_positive_both=result['stress_positive_both'])))
    else:print(json.dumps({'status':'no_eligible_candidate'}))

def run_entry(profile,output,parent):
    if (output/'protocol.json').exists():raise ValueError('New experiment directory required')
    selection=json.loads((parent/'selection.json').read_text())
    protocol=json.loads((parent/'protocol.json').read_text())
    config=json.loads((parent/'config.json').read_text())
    rules=[dict(fee_tvl_pct_per_hour=f,min_traders=t)
           for f,t in itertools.product((0,.2,.5,1),(0,20,50))]
    write(output/'protocol.json',dict(created_at=time.time(),rules=rules,exit_policy=selection['policy'],parent=str(parent),
        selection='Max strictly positive training lower net under +100000 lamports per modeled exit; no unknown selected outcomes, >=3 modeled exits and >=10 evaluated entries.',
        limitation='Second-stage research reuses inspected validation. Not independent validation; prospective dry run required.'))
    train=load(profile,protocol['split']-.001)
    scored=[dict(name=str(i),policy=selection['policy'],entry_filter=rule,
                 training=evaluate(train,protocol['start'],protocol['split']-.001,selection['policy'],config['cost_budget_lamports'],rule))
            for i,rule in enumerate(rules)]
    write(output/'training-grid.json',scored)
    winner=choose(scored);write(output/'selection.json',winner or {'status':'no_eligible_candidate'})
    if not winner:return
    val=load(profile,protocol['end'])
    outcome=evaluate(val,protocol['split'],protocol['end'],winner['policy'],config['cost_budget_lamports'],winner['entry_filter'])
    baseline=evaluate(val,protocol['split'],protocol['end'],{},config['cost_budget_lamports'])
    result=dict(winner=winner,validation=outcome,baseline=baseline,
                positive_both=winner['training']['net_lower_lamports']>0 and outcome['net_lower_lamports']>0,promotion_allowed=False)
    write(output/'result.json',result)
    write(output/'config.json',dict(config,frozen_at=time.time(),entry_filter=winner['entry_filter'],
        strategies={'current':{},'training_selected':winner['policy']},selected_from=str(output/'selection.json')))
    print(json.dumps({k:v for k,v in result.items() if k not in ('winner','validation','baseline')}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--entry-stage',action='store_true')
    a=p.parse_args()
    (run_entry if a.entry_stage else run)(a.profile,a.output,a.source)
