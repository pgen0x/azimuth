"""Prospective candidate fee diagnostics. Never collect, trade, or prove profit."""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

FORECAST_FILE = 'dlmm_candidate_fee_forecasts.jsonl'
HORIZONS = {'turnover': 3600, 'pulse': 1800, 'casual': 14400, 'multiday': 86400}
SAMPLE_FIELDS = ('pool', 'base_mint', 'mode', 'ts', 'collected_at', 'active_bin', 'anchor_bin',
                 'lower_bin', 'upper_bin', 'price', 'decimals_x', 'decimals_y',
                 'sol_is_x', 'token_x_mint', 'token_y_mint', 'bin_step', 'bins')
BASIS = 'unfunded_fixed_share_fee_pace_diagnostic; no_occupancy_or_market_impact_forecast; not_net_profit'


def sample_hash(sample):
    public = {key: sample.get(key) for key in SAMPLE_FIELDS}
    return hashlib.sha256(json.dumps(public, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def candidate_fee_forecast(sample, history, frozen_at, validate, *, history_limited=False,
                           frozen_geometry=None, frozen_horizon=None, model_version=2):
    """Freeze the first complete prior, using only already collected observations."""
    result = dict(version=model_version, pool=sample['pool'], base_mint=sample['base_mint'],
                  mode=sample['mode'], frozen_at=frozen_at, recorded_at=frozen_at, status='unmeasured', basis=BASIS,
                  funded_position=False, net_cash_profit_proved=False)
    try:
        if type(model_version) is not int or model_version not in (1, 2):
            return dict(result, reason='unsupported_version')
        validate(sample, sample['pool'], sample['base_mint'])
        horizon = HORIZONS[sample['mode']] if frozen_horizon is None else frozen_horizon
        if type(horizon) is not int or horizon <= 0:
            return dict(result, reason='invalid_horizon')
        if not sample['ts'] <= sample['collected_at'] <= frozen_at < sample['ts'] + horizon:
            return dict(result, reason='not_frozen_before_horizon')
        step = sample.get('bin_step')
        if type(step) is not int or not 0 < step <= 10000:
            return dict(result, reason='missing_native_bin_step')
        if history_limited:
            return dict(result, reason='prior_history_budget_exceeded')
        # Reuse the production geometry; this does not call the pipeline CLI.
        if frozen_geometry is None:
            from dlmm_pipeline import sol_bidask_bins
            below = sol_bidask_bins(step)
        else:
            below = frozen_geometry
        if type(below) is not int or not 0 <= below < 70:
            return dict(result, reason='extended_position_model_unsupported')
        anchor = sample['active_bin']
        ids = list(range(anchor-below, anchor+1))
        current = {b['id']: b for b in sample['bins']}
        if not set(ids) <= current.keys():
            return dict(result, reason='current_planned_bins_missing')
        previous = None
        for row in sorted(history, key=lambda r: (r.get('ts', 0), r.get('collected_at', 0))):
            try:
                validate(row, sample['pool'], sample['base_mint'])
                if (row.get('base_mint') != sample['base_mint']
                        or not row['ts'] <= row['collected_at'] <= sample['ts']
                        or not 240 <= sample['ts']-row['ts'] <= 1800
                        or any(row[k] != sample[k] for k in ('decimals_x', 'decimals_y', 'sol_is_x'))):
                    continue
                old = {b['id']: b for b in row['bins']}
                if (not set(ids) <= old.keys()
                        or any(not math.isclose(old[i]['price'], current[i]['price'], rel_tol=1e-9, abs_tol=0)
                               or any(int(current[i][k]) < int(old[i][k]) for k in ('fee_x', 'fee_y')) for i in ids)):
                    continue
                previous = row
                break
            except (KeyError, TypeError, ValueError):
                continue
        if previous is None:
            return dict(result, reason='missing_complete_prior_history')
        old = {b['id']: b for b in previous['bins']}
        budget, weights = 100000000, (below+1)*(below+2)//2
        allocations, fx, fy, ratios = [], 0, 0, []
        fee_bins = []
        decimals = Fraction(10**sample['decimals_y'], 10**sample['decimals_x'])
        for i in ids:
            b = current[i]
            if int(b['supply']) <= 0 or int(old[i]['supply']) <= 0:
                return dict(result, reason='empty_bin_requires_market_impact_model')
            reserve = int(b['y']) + int(b['x'])*Fraction(str(b['price']))*decimals
            if reserve <= 0:
                return dict(result, reason='zero_bin_reserve')
            paid = budget*(anchor-i+1)//weights
            share = int(paid*int(b['supply'])/reserve)
            ratios.append(Fraction(share, int(b['supply'])))
            bin_fx = ((share >> 64)*(int(b['fee_x'])-int(old[i]['fee_x']))) >> 64
            bin_fy = ((share >> 64)*(int(b['fee_y'])-int(old[i]['fee_y']))) >> 64
            fx += bin_fx
            fy += bin_fy
            fee_bins.append(dict(id=i, historical_fee_x_raw=str(bin_fx),
                                 historical_fee_y_raw=str(bin_fy)))
            allocations.append(dict(id=i, paid_lamports=paid, estimated_share_raw=str(share),
                                    initial_fee_x=b['fee_x'], initial_fee_y=b['fee_y']))
        span = sample['ts']-previous['ts']
        if max(ratios) >= 1:
            return dict(result, reason='added_liquidity_exceeds_existing_bin_model')
        price = Fraction(str(sample['price']))*decimals
        rate = (fx*price+fy)/span
        prediction = float(rate*horizon)
        if not math.isfinite(prediction):
            return dict(result, reason='fee_projection_out_of_bounds')
        baseline_hash, prior_hash = sample_hash(sample), sample_hash(previous)
        recipe = json.dumps(dict(mode=sample['mode'], bins_below=below, horizon_seconds=horizon,
                                 capital_lamports=budget, frozen_at=frozen_at), sort_keys=True, separators=(',', ':'))
        ident = hashlib.sha256(('candidate-fee-v'+str(model_version)+':'+baseline_hash+':'+prior_hash+':'+recipe).encode()).hexdigest()
        attribution = {}
        if model_version == 2:
            total = fx*price+fy
            active = fee_bins[-1]
            active_fee = int(active['historical_fee_x_raw'])*price+int(active['historical_fee_y_raw'])
            attribution['fee_attribution'] = dict(
                basis='historical_fee_by_planned_bin; not_future_bin_occupancy',
                active_bin=anchor, bins=fee_bins,
                active_bin_fraction=float(active_fee/total) if total else None)
        return dict(result, status='frozen_prediction', id=ident, **attribution,
                    baseline_sha256=baseline_hash, prior_sha256=prior_hash,
                    baseline_ts=sample['ts'], baseline_collected_at=sample['collected_at'],
                    prior_ts=previous['ts'], prior_collected_at=previous['collected_at'],
                    history_span_seconds=span, capital_lamports=budget, bins_below=below,
                    bin_step=step, raw_token_price_numerator=str(price.numerator),
                    raw_token_price_denominator=str(price.denominator), historical_fee_x_raw=str(fx),
                    historical_fee_y_raw=str(fy), linear_fee_lamports=prediction,
                    horizon_seconds=horizon, horizon_target_ts=sample['ts']+horizon,
                    max_added_over_existing_bin_supply=float(max(ratios)), allocations=allocations)
    except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return dict(result, reason='invalid_forecast_inputs')


def score_forecasts(forecasts, samples, cutoff, validate):
    """Score recorded forecasts only. First terminal sample; no retrospective writes."""
    if type(cutoff) not in (int, float) or not math.isfinite(cutoff):
        raise ValueError('A finite observation cutoff is required')
    forecasts, samples = list(forecasts), list(samples)
    by_hash = {sample_hash(row): row for row in samples}
    by_pool = {}
    for row in samples:
        by_pool.setdefault(row.get('pool'), []).append(row)
    results = []
    for f in forecasts:
        if f.get('status') != 'frozen_prediction' or f.get('recorded_at', float('inf')) > cutoff:
            continue
        row = dict(id=f.get('id'), pool=f.get('pool'), base_mint=f.get('base_mint'),
                   mode=f.get('mode'), frozen_at=f.get('frozen_at'), status='unmeasured', basis=BASIS)
        results.append(row)
        try:
            if type(f.get('version')) is not int or f['version'] not in (1, 2):
                raise ValueError('unsupported version')
            base, prior = by_hash[f['baseline_sha256']], by_hash[f['prior_sha256']]
            rebuilt = candidate_fee_forecast(base, [prior], f['frozen_at'], validate,
                                             frozen_geometry=f['bins_below'], frozen_horizon=f['horizon_seconds'],
                                             model_version=f['version'])
            if not f['frozen_at'] <= f['recorded_at'] <= cutoff or not f['recorded_at'] < f['horizon_target_ts']:
                raise ValueError('forecast recorded after cutoff or horizon')
            rebuilt['recorded_at'] = f['recorded_at']
            if rebuilt != f:
                row['reason'] = 'forecast_or_input_binding_mismatch'
                continue
            target = f['horizon_target_ts']
            if cutoff < target:
                row.update(status='pending', horizon_target_ts=target)
                continue
            future = sorted((s for s in by_pool.get(f['pool'], [])
                             if target <= s.get('ts', 0) <= target+600
                             and s.get('collected_at', float('inf')) <= cutoff), key=lambda s: (s['ts'], s['collected_at']))
            if not future:
                row.update(status='pending' if cutoff <= target+600 else 'unmeasured',
                           reason='terminal_observation_missing', horizon_target_ts=target)
                continue
            terminal = future[0]
            validate(terminal, f['pool'], f['base_mint'])
            if (not terminal['ts'] <= terminal['collected_at'] <= cutoff
                    or any(terminal[k] != base[k] for k in ('decimals_x', 'decimals_y', 'sol_is_x'))):
                raise ValueError('terminal timing or decimals mismatch')
            bins = {b['id']: b for b in terminal['bins']}
            initial_bins = {b['id']: b for b in base['bins']}
            fx, fy = 0, 0
            for b in f['allocations']:
                observed = bins[b['id']]
                if (int(observed['supply']) <= int(b['estimated_share_raw'])
                        or not math.isclose(observed['price'], initial_bins[b['id']]['price'], rel_tol=1e-9, abs_tol=0)):
                    raise ValueError('empty terminal bin')
                dx, dy = int(observed['fee_x'])-int(b['initial_fee_x']), int(observed['fee_y'])-int(b['initial_fee_y'])
                if dx < 0 or dy < 0:
                    raise ValueError('counter reset')
                share = int(b['estimated_share_raw']) >> 64
                fx += share*dx >> 64
                fy += share*dy >> 64
            price = Fraction(int(f['raw_token_price_numerator']), int(f['raw_token_price_denominator']))
            at_baseline = fx*price+fy
            terminal_price = Fraction(str(terminal['price']))*Fraction(10**terminal['decimals_y'], 10**terminal['decimals_x'])
            elapsed = terminal['ts']-f['baseline_ts']
            expected = Fraction(f['historical_fee_x_raw'])*price+int(f['historical_fee_y_raw'])
            expected = expected*elapsed/f['history_span_seconds']
            row.update(status='scored', observed_until_ts=terminal['ts'], elapsed_seconds=elapsed,
                       modeled_fee_at_baseline_price_lamports=float(at_baseline),
                       modeled_fee_at_terminal_price_lamports=float(fx*terminal_price+fy),
                       linear_fee_at_observed_duration_lamports=float(expected),
                       modeled_over_linear=float(at_baseline/expected) if expected else None,
                       terminal_active_bin=terminal['active_bin'], terminal_sha256=sample_hash(terminal),
                       funded_position=False, net_cash_profit_proved=False)
        except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError):
            row.update(reason='invalid_or_missing_scoring_inputs')
    visible = [r for r in forecasts if r.get('recorded_at', float('inf')) <= cutoff]
    return dict(cutoff=cutoff, recorded_forecasts=len(visible),
                unmeasured_forecasts=sum(r.get('status')=='unmeasured' for r in visible),
                forecasts=len(results), scored=sum(r['status']=='scored' for r in results),
                unique_pools=len({r['pool'] for r in results}),
                limitation='Overlapping candidate forecasts are correlated. Unfunded fee diagnostics exclude principal loss, execution costs, occupancy prediction and market impact. They are not position cash outcomes.', results=results)


if __name__ == '__main__':
    import time
    from dlmm_accounting import rows
    from dlmm_shadow import validate_candidate_snapshot
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--as-of', type=float, default=None)
    args = parser.parse_args()
    memory = args.profile/'memories'
    print(json.dumps(score_forecasts(rows(memory/FORECAST_FILE), rows(memory/'dlmm_candidate_bin_samples.jsonl'),
                                    time.time() if args.as_of is None else args.as_of, validate_candidate_snapshot), indent=2))
