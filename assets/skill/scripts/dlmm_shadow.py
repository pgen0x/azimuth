#!/usr/bin/env python3
"""Forward shadow outcomes and bin replay. Never submits a trade or changes weights."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import time
import urllib.parse
import urllib.request
from decimal import Decimal, getcontext
from dlmm_accounting import rows

getcontext().prec = 60
HORIZONS = {'turnover': 3600, 'pulse': 1800, 'casual': 14400, 'multiday': 86400}


def append(file, row):
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open('a') as stream:
        stream.write(json.dumps(row, allow_nan=False) + '\n')


def rejected_outcome(row, price, observed_at):
    target = row['ts'] + HORIZONS.get(row['mode'], 86400)
    if observed_at < target:
        return None
    result = dict(id=row['id'], gate=row['gate'], mode=row['mode'], target_ts=target,
                  observed_at=observed_at, basis='pool_price_proxy_not_simulated_LP_return')
    baseline = row['snapshot'].get('pool_price')
    if observed_at > target + 600:
        return dict(result, status='censored', reason='missed_horizon')
    if not baseline or not price or not math.isfinite(price) or price <= 0:
        return dict(result, status='unmeasured', reason='price_unavailable')
    change = price / baseline - 1
    if row.get('candidate', {}).get('sol_is_x'):
        change = baseline / price - 1
    return dict(result, status='measured', return_pct=100*change,
                # Fixed 1% hurdle, not selected after seeing winners.
                estimated_false_reject_proxy=change > 0.01, hurdle_pct=1)


def bin_replay(entry, samples, cost_sol=None):
    """Infinitesimal fixed-share replay using observed per-share fee growth.

    Does not claim to predict the market impact of adding liquidity. No invented
    fees when a supply/fee counter is missing. Schemes are fixed before outcomes.
    """
    initial = entry.get('bin_snapshot')
    if not initial or not samples:
        return {'status': 'unmeasured', 'reason': 'missing_entry_or_followup_bins'}
    target = initial['ts'] + HORIZONS.get(entry.get('mode'), 86400)
    ordered = sorted([s for s in samples if initial['ts'] < s['ts'] <= target+600], key=lambda s: s['ts'])
    if not ordered:
        return {'status': 'unmeasured' if any(s['ts'] > target+600 for s in samples) else 'pending',
                'reason': 'no_followup_within_mode_horizon', 'horizon_target_ts': target}
    terminal = next((i for i,s in enumerate(ordered) if s['ts'] >= target), None)
    if terminal is not None:
        ordered = ordered[:terminal+1]  # First terminal observation, never a later favorable sample.
    start = {b['id']: b for b in initial['bins']}
    if not start or any(int(b['supply']) <= 0 for b in start.values()):
        return {'status': 'unmeasured', 'reason': 'empty_bin_counterfactual_requires_market_impact_model'}
    amount = Decimal(str(entry.get('size_sol') or 0))
    if amount <= 0:
        return {'status': 'unmeasured', 'reason': 'missing_capital'}
    sol_x = initial['sol_is_x']
    dx, dy = Decimal(10)**initial['decimals_x'], Decimal(10)**initial['decimals_y']
    def sol_value(x, y, price):
        return x/dx + y/dy/price if sol_x else x/dx*price + y/dy
    prices = Decimal(str(initial['price']))
    ids = sorted(start)
    results = {}
    for scheme in ('uniform', 'near_active', 'far_active'):
        distances = {i: abs(i-initial['active_bin'])+1 for i in ids}
        raw = {i: Decimal(1) if scheme=='uniform' else Decimal(1)/distances[i] if scheme=='near_active' else Decimal(distances[i]) for i in ids}
        weights = {i: v/sum(raw.values()) for i,v in raw.items()}
        shares = {}
        for i,b in start.items():
            value = sol_value(Decimal(b['x']),Decimal(b['y']),Decimal(str(b['price'])))
            if value <= 0:
                return {'status':'unmeasured','reason':'zero_bin_value'}
            shares[i] = amount*weights[i]*Decimal(b['supply'])/value
        initial_x = sum(shares[i]*Decimal(start[i]['x'])/Decimal(start[i]['supply']) for i in ids)
        initial_y = sum(shares[i]*Decimal(start[i]['y'])/Decimal(start[i]['supply']) for i in ids)
        utilization = Decimal(0); oor = 0; previous_ts = initial['ts']; elapsed=0
        for sample in ordered:
            bins={b['id']:b for b in sample['bins']}
            if not set(ids) <= bins.keys() or any(int(bins[i]['supply'])<=0 or int(bins[i]['fee_x'])<int(start[i]['fee_x']) or int(bins[i]['fee_y'])<int(start[i]['fee_y']) for i in ids):
                return {'status':'unmeasured','reason':'missing_or_reset_bin_state'}
            dt=sample['ts']-previous_ts; previous_ts=sample['ts']; elapsed+=dt
            utilization+=weights.get(sample['active_bin'],Decimal(0))*dt
            oor+=int(sample['active_bin']<min(ids) or sample['active_bin']>max(ids))
        price=Decimal(str(ordered[-1]['price']))
        x=sum(shares[i]*Decimal(bins[i]['x'])/Decimal(bins[i]['supply']) for i in ids)
        y=sum(shares[i]*Decimal(bins[i]['y'])/Decimal(bins[i]['supply']) for i in ids)
        # SDK: (positionShare >> 64) * deltaFeePerToken >> 64.
        fx=sum(Decimal((int(shares[i]) >> 64)*(int(bins[i]['fee_x'])-int(start[i]['fee_x'])) >> 64) for i in ids)
        fy=sum(Decimal((int(shares[i]) >> 64)*(int(bins[i]['fee_y'])-int(start[i]['fee_y'])) >> 64) for i in ids)
        principal=sol_value(x,y,price); fees=sol_value(fx,fy,price)
        hodl=sol_value(initial_x,initial_y,price)
        gross=principal+fees-amount
        results[scheme]=dict(fee_capture_sol=float(fees),principal_change_sol=float(principal-amount),
            inventory_drift_x_raw=str(x-initial_x),inventory_drift_y_raw=str(y-initial_y),
            il_vs_hodl_sol=float(principal-hodl),active_bin_utilization=float(utilization/elapsed),
            oor_samples=oor,observed_samples=len(ordered),gross_pnl_sol=float(gross),
            net_after_observed_cost_sol=float(gross)-cost_sol if cost_sol is not None else None)
    return {'status':'modeled', 'horizon_target_ts':target, 'observed_until_ts':ordered[-1]['ts'],
            'horizon_complete':ordered[-1]['ts'] >= target,
            'basis':'infinitesimal_fixed_shares; fixed_mode_horizon_with_600s_terminal_grace; sampled_OOR; observed_costs_only; no_slippage_or_recenter_counterfactual', 'schemes':results}


def liquidation_observation(entry, wallet, fetch):
    """Indexed inventory plus a sell quote; excludes network fees and rent."""
    sol = 'So11111111111111111111111111111111111111112'
    initial = entry['bin_snapshot']
    decimals = initial['decimals_x']
    if initial['sol_is_x'] is not False or type(decimals) is not int or not 0 <= decimals <= 18:
        raise ValueError('unsupported_token_orientation_or_decimals')

    def number(value):
        n = Decimal(str(value))
        if not n.is_finite() or not math.isfinite(float(n)):
            raise ValueError('invalid_amount')
        return n

    query = urllib.parse.urlencode(dict(user=wallet, status='open', pageSize=100, page=1))
    data = fetch('https://dlmm.datapi.meteora.ag/positions/'
                 + urllib.parse.quote(entry['pool'], safe='') + '/pnl?' + query)
    if data['tokenX'] != entry['base_mint'] or data['tokenY'] != sol:
        raise ValueError('mint_mismatch')
    position = next(p for p in data['positions'] if p['positionAddress'] == entry['position'])
    updated = number(position['updatedAt'])
    if position['isClosed'] is not False or not -5 <= time.time() - float(updated) <= 180:
        raise ValueError('closed_or_stale_position')
    deposit = number(position['allTimeDeposits']['total']['sol'])
    if (deposit <= 0 or number(position['allTimeWithdrawals']['total']['sol']) != 0
            or number(position['allTimeFees']['total']['sol']) != 0):
        raise ValueError('unsupported_prior_position_flows')
    inventory = position['unrealizedPnl']
    for side in ('X', 'Y'):
        if number(inventory['unclaimedRewardToken' + side]['amount']) != 0:
            raise ValueError('unvalued_rewards')
    amounts = [number(inventory[k]['amount']) for k in
               ('balanceTokenX', 'unclaimedFeeTokenX', 'balanceTokenY', 'unclaimedFeeTokenY')]
    if any(n < 0 for n in amounts):
        raise ValueError('negative_inventory')
    raw = int((amounts[0] + amounts[1]) * 10**decimals)
    if not 0 <= raw < 2**64:
        raise ValueError('invalid_token_quantity')
    native = amounts[2] + amounts[3]
    mark = number(position['pnlSol'])
    quote = None
    out = minimum = 0
    if raw:
        query = urllib.parse.urlencode(dict(inputMint=entry['base_mint'], outputMint=sol,
                                           amount=raw, slippageBps=100))
        quote = fetch('https://api.jup.ag/swap/v1/quote?' + query)
        values = [quote[k] for k in ('inAmount', 'outAmount', 'otherAmountThreshold')]
        if (not all(isinstance(v, str) and v.isascii() and v.isdigit() for v in values)
                or quote['inputMint'] != entry['base_mint'] or quote['outputMint'] != sol
                or quote['swapMode'] != 'ExactIn' or type(quote['slippageBps']) is not int
                or quote['slippageBps'] != 100):
            raise ValueError('invalid_quote')
        incoming, out, minimum = map(int, values)
        if incoming != raw or not 0 < minimum <= out < 2**64:
            raise ValueError('quote_amount_mismatch')
    observed = time.time()
    if not -5 <= observed - float(updated) <= 180:
        raise ValueError('inventory_expired_during_quote')
    return dict(status='measured', position_updated_at=float(updated), observed_at=observed,
                deposit_sol=float(deposit), lp_mark_pnl_sol=float(mark),
                native_lp_assets_including_fees_sol=float(native), token_sell_raw=str(raw),
                quote=quote,
                quoted_assets_change_before_network_fees_sol=float(native + Decimal(out)/10**9 - deposit),
                minimum_quoted_assets_change_before_network_fees_sol=float(native + Decimal(minimum)/10**9 - deposit),
                basis='indexed_inventory_plus_sell_quote_before_network_fees_not_net_cash',
                limitation='Inventory and quote differ in time; withdrawal can change liquidity. '
                           'Excludes network fees, rent, prior flows and rewards; quote is not an executed exit.')


def collect_liquidation(profile):
    """At most one position and two public HTTP reads per scheduled cycle."""
    memory = profile / 'memories'
    file = memory / 'dlmm_liquidation_quotes.jsonl'
    latest = {r['position']: r['observed_at'] for r in rows(file)}
    closed = {r['position'] for r in rows(memory / 'dlmm_closes.jsonl')
              if r.get('position') and not r.get('dry_run')}
    wallets = {r['position']: r['wallet'] for r in rows(memory / 'dlmm_transactions.jsonl')
               if r.get('kind') == 'deploy' and r.get('position') and r.get('wallet')}

    def fetch(url):
        request = urllib.request.Request(url, headers={'User-Agent': 'dlmm-lp/1.0'})
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)

    for entry_file in sorted((memory / 'dlmm_entries').glob('*.json'),
                             key=lambda p: latest.get(p.stem, 0)):
        entry = json.loads(entry_file.read_text())
        position = entry['position']
        initial = entry.get('bin_snapshot')
        if not initial or position in closed or position not in wallets:
            continue
        if not initial['ts'] <= time.time() <= initial['ts'] + HORIZONS.get(entry.get('mode'), 86400) + 600:
            continue
        if time.time() - latest.get(position, 0) < 240:
            continue
        sample = dict(position=position, pool=entry['pool'], observed_at=time.time())
        try:
            sample.update(liquidation_observation(entry, wallets[position], fetch))
        except Exception as error:
            # HTTP errors can contain URLs; persist only their type, never credentials.
            sample.update(status='unmeasured', reason=type(error).__name__, observed_at=time.time())
        append(file, sample)
        return 1
    return 0


def collect(profile, reject_file):
    memory=profile/'memories'; executor=profile/'skills/solana-dlmm/scripts/dlmm_executor.js'
    rejected={}
    for row in rows(reject_file):
        rejected.setdefault(row['id'],row)
    done={r['id'] for r in rows(memory/'dlmm_reject_outcomes.jsonl')}
    prices={}; processed=0
    for ident,row in rejected.items():
        if ident in done or time.time()<row['ts']+HORIZONS.get(row['mode'],86400): continue
        if processed>=100: break
        processed+=1
        price=None
        if time.time() <= row['ts']+HORIZONS.get(row['mode'],86400)+600:
            mint=row.get('candidate',{}).get('base_mint')
            try:
                if mint not in prices:
                    query=urllib.parse.urlencode({'query':mint,'page_size':100,'filter_by':'pool_type=dlmm','timeframe':'30m'})
                    request=urllib.request.Request('https://pool-discovery-api.datapi.meteora.ag/pools?'+query,headers={'User-Agent':'curl/8.5.0'})
                    with urllib.request.urlopen(request,timeout=10) as response:
                        prices[mint]={p['pool_address']:p.get('pool_price') for p in json.load(response)['data']}
                price=prices[mint].get(row['pool'])
            except Exception: pass
        append(memory/'dlmm_reject_outcomes.jsonl',rejected_outcome(row,price,int(time.time())))
    existing=rows(memory/'dlmm_bin_samples.jsonl')
    latest={}
    for sample in existing: latest[sample['position']]=sample['ts']
    count=0
    for file in sorted((memory/'dlmm_entries').glob('*.json'),key=lambda p:latest.get(p.stem,0)):
        entry=json.loads(file.read_text()); initial=entry.get('bin_snapshot')
        if not initial: continue
        position=entry['position']
        target=initial['ts']+HORIZONS.get(entry.get('mode'),86400)
        if time.time()>target+600 or latest.get(position,0)>=target: continue
        if time.time()-latest.get(position,0)<240: continue
        if count>=12: break
        count+=1
        try:
            ids=[b['id'] for b in initial['bins']]
            output=subprocess.check_output(['node',str(executor),'bin-snapshot',entry['pool'],str(min(ids)),str(max(ids))],stderr=subprocess.DEVNULL,timeout=25)
            sample=json.loads(output);sample['position']=position
            append(memory/'dlmm_bin_samples.jsonl',sample)
        except Exception: pass
    return {'rejects_total':len(rejected),'outcomes_attempted':processed,'bin_snapshots_attempted':count,
            'liquidation_observations_attempted':collect_liquidation(profile)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,default=Path(os.path.abspath(__file__)).parent.parent.parent.parent)
    parser.add_argument('--rejects',type=Path,default=Path.home()/'.local/state/azimuth/solana_rejects.jsonl')
    args=parser.parse_args();print(json.dumps(collect(args.profile,args.rejects)))

if __name__=='__main__':main()
