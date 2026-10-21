"""As-of native price-path diagnostics. No strategy decisions or transactions."""
import argparse
import json
import math
from pathlib import Path


def features(rows, pool, mint, cutoff):
    if type(cutoff) not in (int,float) or not math.isfinite(cutoff):
        raise ValueError('Finite cutoff required')
    result=dict(pool=pool,base_mint=mint,cutoff=cutoff,status='unmeasured',
                basis='sampled_native_active_bins_not_continuous_price_path_or_profit')
    eligible=[]
    for r in rows:
        if r.get('pool')!=pool or r.get('base_mint')!=mint or r.get('status')!='observed':continue
        stamps=[r.get(k) for k in ('requested_at','observed_at','collected_at')]
        if any(type(t) not in (int,float) or not math.isfinite(t) for t in stamps):continue
        requested,observed,collected=stamps
        if not cutoff-1800<=requested<=observed<=collected<=cutoff:continue
        if observed-requested>25 or collected-observed>5:continue
        if (r.get('commitment')!='confirmed' or r.get('basis')!='native_lb_pair_active_bin_not_fee_or_profit'
                or type(r.get('slot')) is not int or r['slot']<=0
                or type(r.get('active_bin')) is not int or abs(r['active_bin'])>100000
                or type(r.get('bin_step')) is not int or not 0<r['bin_step']<=10000):continue
        eligible.append(r)
    eligible.sort(key=lambda r:(r['observed_at'],r['slot']))
    slots={};path=[]
    for r in eligible:
        if r['slot'] in slots:
            old=slots[r['slot']]
            if (r['active_bin'],r['bin_step'])!=(old['active_bin'],old['bin_step']):
                return dict(result,reason='conflicting_same_slot')
            continue  # Repeated RPC slot cannot extend observation coverage.
        if path and r['slot']<path[-1]['slot']:
            return dict(result,reason='slot_regression')
        slots[r['slot']]=r;path.append(r)
    if not path:return dict(result,reason='no_eligible_observations',samples=0)
    if len({r['bin_step'] for r in path})!=1:return dict(result,reason='bin_step_changed')
    times=[r['observed_at'] for r in path]
    span=times[-1]-times[0];gap=max([b-a for a,b in zip(times,times[1:])],default=0)
    result.update(samples=len(path),span_seconds=span,max_gap_seconds=gap,last_age_seconds=cutoff-times[-1])
    if len(path)<3 or span<600 or gap>180 or cutoff-times[-1]>120:
        return dict(result,reason='insufficient_path_coverage')
    bins=[r['active_bin'] for r in path];peak=bins[0];drawdown=0
    for b in bins:
        peak=max(peak,b);drawdown=max(drawdown,peak-b)
    return dict(result,status='measured',bin_step=path[0]['bin_step'],first_slot=path[0]['slot'],
                last_slot=path[-1]['slot'],net_bins=bins[-1]-bins[0],observed_span_bins=max(bins)-min(bins),
                observed_drawdown_bins=drawdown)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--cutoff',type=float,required=True)
    a=p.parse_args()
    rows=[json.loads(line) for line in a.input.read_text().splitlines() if line.strip()]
    identities=sorted({(r['pool'],r['base_mint']) for r in rows if r.get('collected_at',float('inf'))<=a.cutoff})
    print(json.dumps([features(rows,pool,mint,a.cutoff) for pool,mint in identities],indent=2))
