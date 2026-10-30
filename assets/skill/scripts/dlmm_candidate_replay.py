"""Offline candidate LP sensitivity, independent of live position entries.

Uses recorded, bound fee forecasts as decision-time anchors. Fixed-share inventory
and explicit execution-cost assumptions are estimates, never executed net profit.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import time
from fractions import Fraction

from dlmm_fee_forecast import candidate_fee_forecast, sample_hash
from dlmm_net_experiment import write
from dlmm_shadow import iter_rows, validate_candidate_snapshot


def select_cohorts(forecasts, cutoff):
    """Select before reading outcomes; reserve each pool through terminal grace."""
    busy, seen, selected = {}, set(), []
    for f in sorted(forecasts, key=lambda x: (x.get('recorded_at', math.inf), x.get('id', ''))):
        if f.get('status') != 'frozen_prediction' or f.get('recorded_at', math.inf) > cutoff:
            continue
        key = (f['pool'], f['baseline_sha256'])
        if key in seen or f['baseline_ts'] < busy.get(f['pool'], 0):
            continue
        seen.add(key)
        selected.append(f)
        busy[f['pool']] = f['horizon_target_ts'] + 600
    return selected


def replay(base, terminal, below, offset, capital, network_cost, entry_bps, exit_bps, max_share_bps):
    """Hold inferred shares; apply friction to token legs, not the entire capital."""
    for s in (base, terminal):
        validate_candidate_snapshot(s, base['pool'], base['base_mint'])
    if (not base['ts'] < terminal['ts'] or base['bin_step'] != terminal['bin_step']
            or base['decimals_x'] != terminal['decimals_x']):
        raise ValueError('inconsistent_terminal')
    anchor = base['active_bin'] - offset
    ids = range(anchor - below, anchor + 1)
    old, new = ({b['id']: b for b in s['bins']} for s in (base, terminal))
    denominator = (below + 1) * (below + 2) // 2
    scale = Fraction(10**base['decimals_y'], 10**base['decimals_x'])
    terminal_price = Fraction(str(terminal['price'])) * scale
    start_price = Fraction(str(base['price'])) * scale
    x = y = initial_x = Fraction(0)
    fx = fy = spent = 0
    largest_share = Fraction(0)
    for i in ids:
        if i not in old or i not in new:
            raise ValueError('planned_bins_missing')
        b, end = old[i], new[i]
        supply, terminal_supply = int(b['supply']), int(end['supply'])
        if supply <= 0 or terminal_supply <= 0:
            raise ValueError('empty_bin')
        if not math.isclose(b['price'], end['price'], rel_tol=1e-9):
            raise ValueError('bin_price_changed')
        if offset and int(b['x']) != 0:
            raise ValueError('passive_entry_not_SOL_only')
        reserve = int(b['y']) + int(b['x']) * Fraction(str(b['price'])) * scale
        if reserve <= 0:
            raise ValueError('zero_reserve')
        paid = capital * (anchor - i + 1) // denominator
        share = int(paid * supply / reserve)
        largest_share = max(largest_share, Fraction(share, supply), Fraction(share, terminal_supply))
        if largest_share * 10000 > max_share_bps:
            raise ValueError('liquidity_share_exceeds_model_limit')
        dx, dy = int(end['fee_x']) - int(b['fee_x']), int(end['fee_y']) - int(b['fee_y'])
        if min(dx, dy) < 0:
            raise ValueError('fee_counter_reset')
        x += Fraction(share * int(end['x']), terminal_supply)
        y += Fraction(share * int(end['y']), terminal_supply)
        initial_x += Fraction(share * int(b['x']), supply)
        fx += (share >> 64) * dx >> 64
        fy += (share >> 64) * dy >> 64
        spent += paid
    token_value = (x + fx) * terminal_price
    entry_cost = initial_x * start_price * entry_bps / 10000
    exit_cost = token_value * exit_bps / 10000
    gross = token_value + y + fy - spent
    net = gross - network_cost - entry_cost - exit_cost
    floor = lambda n: n.numerator // n.denominator
    return dict(modeled_net_lamports=floor(net), gross_lamports=floor(gross),
                principal_change_lamports=floor(x * terminal_price + y - spent),
                fee_lamports=floor(fx * terminal_price + fy),
                entry_friction_lamports=-floor(-entry_cost), exit_friction_lamports=-floor(-exit_cost),
                network_cost_lamports=network_cost, terminal_token_value_lamports=floor(token_value),
                terminal_token_raw=str(floor(x+fx)), terminal_sol_lamports=floor(y+fy),
                initial_token_value_lamports=floor(initial_x * start_price),
                max_share_fraction=float(largest_share), unspent_lamports=capital-spent,
                extra_execution_stress_lamports=floor(net)-100000,
                unrecovered_ata_stress_lamports=floor(net)-1513840)


def run(profile, output, cutoff):
    if output.exists():
        raise ValueError('New output directory required')
    memory = profile / 'memories'
    config = dict(capital=100000000, network_cost=26151, entry_bps=200, exit_bps=300, max_share_bps=100)
    write(output/'protocol.json', dict(created_at=time.time(), cutoff=cutoff, config=config,
        evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        strategies={'current_geometry': 0, 'passive_one_bin_below': 1},
        selection='Earliest frozen forecast per pool; no overlap through horizon+600s. Selection ignores outcomes.',
        limitations=['Fixed shares exclude market response to added liquidity; each bin share capped at 1%.',
            '2% initial token-leg friction and 3% exit token-leg friction are assumptions, not historical quotes.',
            'Network/cleanup budget 26151 lamports; full principal rent return assumed; separate ATA and extra-cost stress.',
            'Pool cohorts can overlap across pools; sums are diagnostic, not a funded portfolio or wallet backtest.',
            'Historical periods have been inspected. Future paper execution validation required.'], promotion_allowed=False))
    samples = [s for s in iter_rows(memory/'dlmm_candidate_bin_samples.jsonl')
               if s.get('status') == 'observed' and s.get('collected_at', math.inf) <= cutoff]
    hashes = {sample_hash(s): s for s in samples}
    by_pool = collections.defaultdict(list)
    for s in samples:
        by_pool[s['pool']].append(s)
    for pool in by_pool:
        by_pool[pool].sort(key=lambda s: (s['ts'], s['collected_at']))
    forecasts = list(iter_rows(memory/'dlmm_candidate_fee_forecasts.jsonl'))
    selected = select_cohorts(forecasts, cutoff)
    results = []
    for f in selected:
        row = dict(id=f['id'], pool=f['pool'], mode=f['mode'], baseline_ts=f['baseline_ts'],
                   target=f['horizon_target_ts'], status='unmeasured', strategies={})
        results.append(row)
        try:
            base, prior = hashes[f['baseline_sha256']], hashes[f['prior_sha256']]
            rebuilt = candidate_fee_forecast(base, [prior], f['frozen_at'], validate_candidate_snapshot,
                frozen_geometry=f['bins_below'], frozen_horizon=f['horizon_seconds'], model_version=f['version'])
            rebuilt['recorded_at'] = f['recorded_at']
            if rebuilt != f or not f['frozen_at'] <= f['recorded_at'] < f['horizon_target_ts']:
                raise ValueError('forecast_binding_mismatch')
            terminal = next((s for s in by_pool[f['pool']] if f['horizon_target_ts'] <= s['ts'] <= f['horizon_target_ts']+600), None)
            if terminal is None:
                row['status'] = 'pending' if cutoff <= f['horizon_target_ts']+600 else 'unmeasured'
                row['reason'] = 'terminal_missing'
                continue
            if not terminal['ts'] <= terminal['collected_at'] <= cutoff:
                raise ValueError('terminal_timing_invalid')
            row.update(terminal_sha256=sample_hash(terminal), terminal_ts=terminal['ts'])
            for name, offset in (('current_geometry', 0), ('passive_one_bin_below', 1)):
                try:
                    row['strategies'][name] = dict(status='modeled', **replay(base, terminal, f['bins_below'], offset, **config))
                except ValueError as error:
                    row['strategies'][name] = dict(status='unmeasured', reason=str(error))
            row['status'] = 'paired' if all(s['status']=='modeled' for s in row['strategies'].values()) else 'unmeasured'
        except (KeyError, ValueError, TypeError, ZeroDivisionError) as error:
            row['reason'] = str(error)
    result = dict(cutoff=cutoff, frozen_forecasts=sum(f.get('status')=='frozen_prediction' for f in forecasts),
        selected_cohorts=len(selected), pools=len({f['pool'] for f in selected}),
        statuses=dict(collections.Counter(r['status'] for r in results)), results=results,
        promotion_allowed=False, net_cash_profit_proved=False)
    write(output/'result.json', result)
    print(json.dumps({k:v for k,v in result.items() if k!='results'}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--as-of', type=float, default=None)
    a = p.parse_args()
    run(a.profile, a.output, time.time() if a.as_of is None else a.as_of)
