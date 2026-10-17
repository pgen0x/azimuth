#!/usr/bin/env python3
"""Forward shadow outcomes and bin replay. Never submits a trade or changes weights."""
import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
import subprocess
import time
import urllib.parse
import urllib.request
from decimal import Decimal, getcontext
from fractions import Fraction
from dlmm_accounting import rows
from dlmm_monitor import verified_risk_mark
from dlmm_candidate_watch import WATCH_FILENAME
from dlmm_canonical_liquidity import retain_canonical_snapshot
from dlmm_fee_forecast import HORIZONS, FORECAST_FILE

getcontext().prec = 60
COLLECTION_BUDGET_SECONDS = 240
REJECT_BUDGET_SECONDS = 45
BIN_BUDGET_SECONDS = 150
LIQUIDATION_BUDGET_SECONDS = 20
CANDIDATE_BUDGET_SECONDS = 10
CANDIDATE_MAX_POOLS = 64
CANDIDATE_MAX_AGE_SECONDS = 1800
SOL_MINT = 'So11111111111111111111111111111111111111112'
ADDRESS = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}\Z')


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def index_candidate(candidates, row, now):
    """Keep only small, recent pool identities while streaming the reject journal."""
    candidate = row.get('candidate') or {}
    pool, mint, stamp = row.get('pool'), candidate.get('base_mint'), row.get('ts')
    if (not isinstance(pool, str) or not ADDRESS.fullmatch(pool)
            or not isinstance(mint, str) or not ADDRESS.fullmatch(mint) or mint == SOL_MINT
            or candidate.get('sol_is_x') is not False or row.get('mode') not in HORIZONS
            or not finite_number(stamp) or not 0 <= now - stamp <= CANDIDATE_MAX_AGE_SECONDS):
        return
    previous = candidates.get(pool)
    if previous and previous['source_ts'] >= stamp:
        return
    candidates[pool] = dict(pool=pool, base_mint=mint, mode=row['mode'],
                            source_id=row['id'], source_ts=stamp)
    if len(candidates) > CANDIDATE_MAX_POOLS:
        del candidates[min(candidates, key=lambda key: (candidates[key]['source_ts'], key))]


def index_due_forecast(candidates, row, now):
    """Retain terminal observations independently of renewed market selection."""
    target, recorded = row.get('horizon_target_ts'), row.get('recorded_at')
    pool, mint = row.get('pool'), row.get('base_mint')
    if (row.get('status') != 'frozen_prediction'
            or type(row.get('version')) is not int or row['version'] not in (1, 2)
            or row.get('mode') not in HORIZONS
            or not isinstance(pool, str) or not ADDRESS.fullmatch(pool)
            or not isinstance(mint, str) or not ADDRESS.fullmatch(mint) or mint == SOL_MINT
            or not isinstance(row.get('id'), str)
            or not all(finite_number(row.get(k)) for k in
                       ('baseline_ts', 'frozen_at', 'recorded_at', 'horizon_target_ts'))
            or row.get('horizon_seconds') != HORIZONS[row['mode']]
            or target != row['baseline_ts'] + row['horizon_seconds']
            or not row['baseline_ts'] <= row['frozen_at'] <= recorded < target
            or not target <= now <= target + 600):
        return
    existing = candidates.get(pool)
    if existing and existing['base_mint'] != mint:
        return
    allocations = row.get('allocations')
    below = row.get('bins_below')
    if (type(below) is not int or not 0 <= below <= 69
            or not isinstance(allocations, list) or len(allocations) != below+1
            or any(not isinstance(b, dict) or type(b.get('id')) is not int for b in allocations)):
        return
    anchor = allocations[-1]['id']
    if abs(anchor) > 100000 or [b['id'] for b in allocations] != list(range(anchor-below, anchor+1)):
        return
    candidate = dict(existing) if existing else dict(
        pool=pool, base_mint=mint, mode=row['mode'], source_id=row['id'],
        source_ts=recorded, terminal_only=True)
    if target < candidate.get('terminal_target_ts', float('inf')):
        candidate.update(terminal_target_ts=target, terminal_anchor_bin=anchor)
    candidates[pool] = candidate
    if len(candidates) > CANDIDATE_MAX_POOLS:
        # Earliest terminal deadlines precede ordinary rolling watch inputs.
        keep = sorted(candidates, key=lambda p: (
            candidates[p].get('terminal_target_ts', float('inf')), -candidates[p]['source_ts'], p))
        del candidates[keep[-1]]


def validate_candidate_snapshot(sample, pool, mint):
    """Validate native counters, identity and bounded contiguous read coverage."""
    if (sample.get('status') != 'observed' or sample.get('pool') != pool
            or sample.get('token_x_mint') != mint or sample.get('token_y_mint') != SOL_MINT
            or sample.get('sol_is_x') is not False or not finite_number(sample.get('ts'))
            or not finite_number(sample.get('price')) or sample['price'] <= 0
            or type(sample.get('decimals_x')) is not int or not 0 <= sample['decimals_x'] <= 18
            or type(sample.get('decimals_y')) is not int or sample['decimals_y'] != 9):
        raise ValueError('invalid_candidate_identity_or_mark')
    lower, upper, anchor = (sample.get(k) for k in ('lower_bin', 'upper_bin', 'anchor_bin'))
    if (any(type(v) is not int or not -(2**31) <= v < 2**31 for v in (lower, upper, anchor, sample.get('active_bin')))
            or not 0 <= anchor - lower <= 69 or not 0 <= upper - anchor <= 16):
        raise ValueError('invalid_candidate_range')
    bins = sample.get('bins')
    if not isinstance(bins, list) or len(bins) != upper - lower + 1:
        raise ValueError('missing_candidate_bins')
    for ident, b in zip(range(lower, upper + 1), bins):
        if (not isinstance(b, dict) or type(b.get('id')) is not int or b['id'] != ident
                or not finite_number(b.get('price')) or b['price'] <= 0):
            raise ValueError('invalid_candidate_bin')
        for field in ('x', 'y', 'supply', 'fee_x', 'fee_y'):
            value = b.get(field)
            bits = 64 if field in ('x', 'y') else 128
            if (not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,39}', value)
                    or int(value) >= 2**bits):
                raise ValueError('invalid_candidate_counter')


def collect_candidate_bins(profile, candidates, deadline):
    """Use existing timer slack; leave liquidation time and never acquire a lock."""
    result = dict(candidate_bin_snapshots_attempted=0, candidate_bin_snapshots_observed=0,
                  candidate_bin_trading_deferred=False, candidate_bin_budget_exhausted=False,
                  candidate_fee_forecasts_frozen=0, candidate_fee_forecasts_unmeasured=0)
    phase_end = min(deadline - LIQUIDATION_BUDGET_SECONDS,
                    time.monotonic() + CANDIDATE_BUDGET_SECONDS)
    if time.monotonic() >= phase_end:
        result['candidate_bin_budget_exhausted'] = True
        return result
    candidates = {pool: dict(value) for pool, value in candidates.items()}
    for forecast in iter_rows(profile/'memories'/FORECAST_FILE):
        if time.monotonic() >= phase_end:
            result['candidate_bin_budget_exhausted'] = True
            return result
        index_due_forecast(candidates, forecast, time.time())
    if not candidates:
        return result
    if time.monotonic() >= phase_end:
        result['candidate_bin_budget_exhausted'] = True
        return result
    file = profile/'memories/dlmm_candidate_bin_samples.jsonl'
    latest, recent, history_limited, terminal_done = {}, {}, set(), set()
    history_now = time.time()
    for row in iter_rows(file):
        if time.monotonic() >= phase_end:
            result['candidate_bin_budget_exhausted'] = True
            return result
        stamp = row.get('collected_at')
        if row.get('pool') in candidates and finite_number(stamp):
            latest[row['pool']] = max(latest.get(row['pool'], 0), stamp)
            target = candidates[row['pool']].get('terminal_target_ts')
            if (target is not None and row.get('status') == 'observed'
                    and finite_number(row.get('ts')) and target <= row['ts'] <= target+600
                    and row['ts'] <= stamp <= history_now):
                terminal_done.add(row['pool'])
            if (row.get('status') == 'observed' and finite_number(row.get('ts'))
                    and 0 <= history_now-row['ts'] <= 1800):
                history = recent.setdefault(row['pool'], [])
                if len(history) >= 16:
                    history_limited.add(row['pool'])
                else:
                    history.append(row)
    executor = profile/'skills/solana-dlmm/scripts/dlmm_executor.js'
    for pool in sorted(candidates, key=lambda p: (
            candidates[p].get('terminal_target_ts', float('inf')) if p not in terminal_done else float('inf'),
            latest.get(p, 0), -candidates[p]['source_ts'], p)):
        if time.monotonic() >= phase_end:
            result['candidate_bin_budget_exhausted'] = True
            break
        if result['candidate_bin_snapshots_attempted'] >= 3:
            break
        candidate = candidates[pool]
        terminal_due = (pool not in terminal_done and 'terminal_target_ts' in candidate
                        and candidate['terminal_target_ts'] <= time.time() <= candidate['terminal_target_ts']+600)
        if (time.time() - latest.get(pool, 0) < 240
                or (candidate.get('terminal_only') and not terminal_due)
                or (not terminal_due and time.time() - candidate['source_ts'] > CANDIDATE_MAX_AGE_SECONDS)):
            continue
        result['candidate_bin_snapshots_attempted'] += 1
        started = time.time()
        record = dict(candidate, request_started_at=started)
        try:
            command = ['node', str(executor), 'candidate-bin-snapshot', pool, '69', '16']
            if terminal_due:
                command.append(str(candidate['terminal_anchor_bin']))
            output = subprocess.check_output(command,
                stderr=subprocess.DEVNULL, timeout=request_timeout(phase_end, 3))
            sample = json.loads(output)
            if sample.get('status') == 'deferred' and sample.get('reason') == 'wallet_trade_active':
                result['candidate_bin_trading_deferred'] = True
                break
            validate_candidate_snapshot(sample, pool, candidate['base_mint'])
            if terminal_due and sample['anchor_bin'] != candidate['terminal_anchor_bin']:
                raise ValueError('terminal_anchor_mismatch')
            if not started - 1 <= sample['ts'] <= time.time():
                raise ValueError('invalid_candidate_timestamp')
            fields = ('ts', 'active_bin', 'anchor_bin', 'lower_bin', 'upper_bin', 'price',
                      'decimals_x', 'decimals_y', 'sol_is_x', 'token_x_mint', 'token_y_mint', 'bins')
            record.update({k: sample[k] for k in fields})
            if type(sample.get('bin_step')) is int and 0 < sample['bin_step'] <= 10000:
                record['bin_step'] = sample['bin_step']
            record['canonical_liquidity'] = retain_canonical_snapshot(
                sample.get('canonical_liquidity'), candidate['base_mint'], started, time.time())
            record.update(status='observed', basis='native_candidate_pool_bin_state_not_position_return')
            result['candidate_bin_snapshots_observed'] += 1
        except Exception as error:
            record.update(status='unmeasured', reason=type(error).__name__)
        record['collected_at'] = time.time()
        append(file, record)
        # A due terminal read can also supply a new baseline for a still-live
        # discovery candidate. Old terminal-only watches must never self-renew.
        if (record['status'] == 'observed' and not candidate.get('terminal_only')
                and 0 <= record['collected_at'] - candidate['source_ts'] <= CANDIDATE_MAX_AGE_SECONDS):
            try:
                from dlmm_fee_forecast import candidate_fee_forecast, BASIS
                if time.monotonic() >= phase_end:
                    forecast = dict(version=1, pool=pool, base_mint=candidate['base_mint'], mode=candidate['mode'],
                                    frozen_at=time.time(), status='unmeasured', reason='forecast_budget_exhausted',
                                    basis=BASIS, funded_position=False, net_cash_profit_proved=False)
                else:
                    forecast = candidate_fee_forecast(record, recent.get(pool, []), time.time(),
                        validate_candidate_snapshot, history_limited=pool in history_limited)
                forecast['recorded_at'] = time.time()
                append(profile/'memories'/FORECAST_FILE, forecast)
                result['candidate_fee_forecasts_frozen' if forecast['status']=='frozen_prediction'
                       else 'candidate_fee_forecasts_unmeasured'] += 1
            except Exception:
                # Optional diagnostic failures must not discard native bins.
                result['candidate_fee_forecasts_unmeasured'] += 1
    return result


def pre_entry_bin_coverage(entries, file, end_ts):
    """Select complete native history observed 4–30m before the entry snapshot.

    Earliest eligible snapshot is fixed by time, never by subsequent returns.
    This is coverage evidence, not a yield forecast or a trading gate.
    """
    results, targets, selected = {}, {}, {}
    for entry in entries:
        position = entry['position']
        results[position] = dict(position=position, mode=entry.get('mode'), status='unmeasured',
                                 reason='missing_pre_entry_bins')
        initial = entry.get('bin_snapshot') or {}
        if (not finite_number(initial.get('ts')) or not finite_number(entry.get('deployed_at'))
                or not 0 < initial['ts'] <= entry['deployed_at'] <= end_ts
                or not initial.get('bins') or initial.get('sol_is_x') is not False
                or not isinstance(entry.get('pool'), str) or not isinstance(entry.get('base_mint'), str)):
            results[position]['reason'] = 'missing_or_unsupported_entry_snapshot'
            continue
        targets.setdefault(entry['pool'], []).append(entry)
    for sample in iter_rows(file):
        for entry in targets.get(sample.get('pool'), ()):
            position, initial = entry['position'], entry['bin_snapshot']
            stamp, collected = sample.get('ts'), sample.get('collected_at')
            if (not finite_number(stamp) or not finite_number(collected)
                    or not stamp <= collected <= initial['ts']
                    or not 240 <= initial['ts'] - stamp <= 1800):
                continue
            try:
                validate_candidate_snapshot(sample, entry['pool'], entry['base_mint'])
            except ValueError:
                continue
            old = {b['id']: b for b in sample['bins']}
            ids = [b['id'] for b in initial['bins']]
            if (len(set(ids)) != len(ids) or not set(ids) <= old.keys()
                    or any(sample[k] != initial.get(k) for k in ('decimals_x', 'decimals_y'))):
                continue
            if any(int(b['fee_x']) < int(old[b['id']]['fee_x'])
                   or int(b['fee_y']) < int(old[b['id']]['fee_y']) for b in initial['bins']):
                continue
            key = (stamp, collected)
            if position in selected and selected[position] <= key:
                continue
            selected[position] = key
            results[position] = dict(position=position, mode=entry.get('mode'), status='observed',
                span_seconds=initial['ts'] - stamp, covered_entry_bins=len(ids),
                entry_snapshot_ts=initial['ts'], prior_snapshot=sample,
                prior_sha256=hashlib.sha256(json.dumps(sample, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
                basis='observed_pre_entry_pool_bin_counters_not_fee_forecast_or_profit')
    return list(results.values())


def request_timeout(deadline, maximum):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('shadow_collection_budget_exhausted')
    return min(maximum, remaining)


def iter_rows(file):
    """Scan evidence without materializing growing journals; corruption stays visible."""
    if file.exists():
        with file.open() as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)


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


def bin_replay(entry, samples, cost_sol=None, *, end_ts=None):
    """Infinitesimal fixed-share replay using observed per-share fee growth.

    Does not claim to predict the market impact of adding liquidity. No invented
    fees when a supply/fee counter is missing. Schemes are fixed before outcomes.
    """
    initial = entry.get('bin_snapshot')
    if not initial or not samples:
        return {'status': 'unmeasured', 'reason': 'missing_entry_or_followup_bins'}
    target = initial['ts'] + HORIZONS.get(entry.get('mode'), 86400)
    if end_ts is not None:
        if type(end_ts) not in (int, float) or not math.isfinite(end_ts) or end_ts <= initial['ts']:
            return {'status':'unmeasured','reason':'invalid_observation_cutoff'}
        target = end_ts
    limit = target+600 if end_ts is None else target
    ordered = sorted([s for s in samples if initial['ts'] < s['ts'] <= limit], key=lambda s: s['ts'])
    if not ordered:
        return {'status': 'unmeasured' if end_ts is not None or any(s['ts'] > target+600 for s in samples) else 'pending',
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
    deposited_sol, deposited_token = ((entry.get('amount_x'), entry.get('amount_y')) if sol_x
                                      else (entry.get('amount_y'), entry.get('amount_x')))
    sol_only = (type(sol_x) is bool and type(deposited_sol) in (int, float)
                and math.isfinite(deposited_sol) and deposited_sol > 0
                and type(deposited_token) in (int, float) and deposited_token == 0
                and Decimal(str(deposited_sol)) == amount)
    def sol_value(x, y, price):
        return x/dx + y/dy/price if sol_x else x/dx*price + y/dy
    ids = sorted(start)
    reference = ('far_active' if sol_only and sol_x is False
                 and entry.get('strategy') == 'sol_bidask'
                 and entry.get('entry_bin') == initial['active_bin'] and entry.get('bins_above') == 0
                 and type(entry.get('bins_below')) is int and entry['bins_below'] >= 0
                 and ids == list(range(initial['active_bin']-entry['bins_below'], initial['active_bin']+1))
                 else None)
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
        # HODL starts before deposit, not after acquiring the active bin's mixed reserves.
        hodl=amount if sol_only else sol_value(initial_x,initial_y,price)
        gross=principal+fees-amount
        results[scheme]=dict(fee_capture_sol=float(fees),principal_change_sol=float(principal-amount),
            inventory_drift_x_raw=str(x-initial_x),inventory_drift_y_raw=str(y-initial_y),
            il_vs_hodl_sol=float(principal-hodl),active_bin_utilization=float(utilization/elapsed),
            oor_samples=oor,observed_samples=len(ordered),gross_pnl_sol=float(gross),
            net_after_observed_cost_sol=float(gross)-cost_sol if cost_sol is not None else None)
    return {'status':'modeled', 'horizon_target_ts':target, 'observed_until_ts':ordered[-1]['ts'],
            'horizon_complete':ordered[-1]['ts'] >= target,
            'hodl_basis':'recorded_SOL_only_input' if sol_only else 'modeled_initial_bin_inventory',
            'expected_bidask_reference_scheme':reference,
            'basis':'infinitesimal_fixed_shares; '+('fixed_mode_horizon_with_600s_terminal_grace' if end_ts is None else 'explicit_observation_cutoff_without_terminal_grace')+'; sampled_OOR; observed_costs_only; no_slippage_or_recenter_counterfactual', 'schemes':results}


def native_allocation_replay(entry, observation, funding, close, *, end_ts):
    """Reweight realized bin returns, preserving composition costs in principal.

    This is an execution-conditioned sensitivity, never an executable return.
    Both funding and deletion must have finalized facts observed by the cutoff.
    """
    def require(condition):
        if not condition:
            raise ValueError('invalid_native_allocation_evidence')

    def uint(value, bits=64):
        require(isinstance(value, str) and re.fullmatch(r'0|[1-9][0-9]{0,38}', value))
        result = int(value)
        require(result < 2**bits)
        return result

    def timestamp(value):
        require(type(value) in (int, float) and math.isfinite(value) and value > 0)
        return value

    def integer(value):
        require(type(value) is int)
        return value

    try:
        if not observation:
            return dict(status='unmeasured', reason='missing_native_close_observation')
        bins_observation = observation.get('bin_observation') or {}
        initial = bins_observation.get('initial_funding')
        if not initial:
            return dict(status='unmeasured', reason='missing_decoded_initial_bin_allocation')
        cutoff = timestamp(end_ts)
        position, pool = entry['position'], entry['pool']
        require(all(type(entry[k]) in (int,float) and math.isfinite(entry[k])
                    for k in ('size_sol','amount_x','amount_y')) and entry['size_sol'] > 0)
        require(observation['position'] == position and observation['pool'] == pool
                and observation['source'] == 'onchain_sol_inventory'
                and integer(observation['version']) == integer(bins_observation['version']) == integer(initial['version']) == 1
                and entry['strategy'] == 'sol_bidask' and entry['sol_is_x'] is False
                and bins_observation['sol_is_x'] is False
                and entry['amount_x'] == 0 and entry['amount_y'] == entry['size_sol'])
        lower, upper, active = (integer(observation[k]) for k in ('lower_bin', 'upper_bin', 'active_bin'))
        require(integer(entry['entry_bin']) == upper and integer(entry['bins_above']) == 0
                and lower == upper-integer(entry['bins_below']) and 0 < upper-lower+1 <= 70 and abs(active) <= 100000)
        step = integer(bins_observation['bin_step'])
        require(0 < step <= 10000 and step == integer(entry['bin_step']))
        observed = timestamp(observation['observed_at'])
        require(observed <= timestamp(observation['decision_at']) <= timestamp(observation['recorded_at']) <= cutoff)
        require(isinstance(initial['signature'], str) and bool(initial['signature'])
                and initial['signature'] == observation['funding_signature'] == funding['signature']
                and isinstance(initial['wallet'], str) and bool(initial['wallet'])
                and initial['wallet'] == funding['wallet'] == close['wallet'])
        for fact in (funding, close):
            require(fact['failed'] is False and fact.get('landed') is not False
                    and integer(fact['slot']) > 0
                    and timestamp(fact['block_time']) <= timestamp(fact['observed_at']) <= cutoff)
        require(integer(initial['block_time']) == funding['block_time']
                and timestamp(funding['block_time']) <= observed
                and close['position_account_closed'] is True
                and 0 <= timestamp(close['block_time'])-observed <= 30)
        capital, budget = uint(initial['deposit_lamports']), uint(initial['requested_lamports'])
        require(capital == uint(observation['deposit_lamports']) and 0 < capital <= budget
                and budget == int(entry['size_sol']*10**9))
        execution_active = integer(initial['executed_active_bin'])
        slippage = integer(initial['max_active_bin_slippage'])
        require(execution_active >= lower and 0 <= slippage <= 10000 and abs(execution_active-upper) <= slippage)
        anchor = min(execution_active, upper)
        all_ids = list(range(lower, upper+1))
        funded_ids = list(range(lower, anchor+1))
        paid_bins, actual_bins = initial['bins'], bins_observation['bins']
        require(isinstance(paid_bins, list) and isinstance(actual_bins, list)
                and len(paid_bins) == len(actual_bins) == len(all_ids)
                and [integer(b['id']) for b in paid_bins] == [integer(b['id']) for b in actual_bins] == all_ids)
        paid, actual, composition = {}, {}, {}
        weight_sum = len(funded_ids)*(len(funded_ids)+1)//2
        protocol_total = 0
        for i, pay, own in zip(all_ids, paid_bins, actual_bins):
            paid[i] = uint(pay['sol_deposit_lamports'])
            require(paid[i] == (budget*(anchor-i+1)//weight_sum if i <= anchor else 0))
            share = uint(own['liquidity_raw'], 128)
            composition[i] = uint(pay['composition_fee_lamports'])
            protocol = uint(pay['protocol_fee_lamports'])
            require(protocol <= composition[i] <= paid[i]
                    and (composition[i] == 0 or i == execution_active))
            protocol_total += protocol
            actual[i] = {k: uint(own[k]) for k in ('x_raw','y_raw','fee_x_raw','fee_y_raw')}
            require((share > 0) == (paid[i] > 0))
            require(paid[i] > 0 or not any(actual[i].values()))
        require(sum(paid.values()) == capital
                and sum(composition.values()) == uint(initial['composition_fee_lamports'])
                and protocol_total == uint(initial['protocol_fee_lamports']))
        price = Fraction(10000+step, 10000)**active
        principal = sum(b['x_raw']*price+b['y_raw'] for b in actual.values())
        fees = sum(b['fee_x_raw']*price+b['fee_y_raw'] for b in actual.values())
        total = principal+fees
        upper_value = -(-total.numerator//total.denominator)
        require(upper_value == uint(observation['value_lamports_upper'])
                and type(observation['pnl_sol']) in (int,float)
                and math.isfinite(observation['pnl_sol'])
                and abs((upper_value-capital)/10**9-observation['pnl_sol']) <= 1e-12)
        schemes = {}
        for scheme in ('far_active','uniform','near_active'):
            weights = {i: Fraction(anchor-i+1) if scheme == 'far_active' else
                       Fraction(1) if scheme == 'uniform' else Fraction(1,anchor-i+1) for i in funded_ids}
            denominator = sum(weights.values())
            allocated = {i: int(budget*weights[i]/denominator) for i in funded_ids}
            p = f = charged = Fraction(0)
            for i in funded_ids:
                ratio = Fraction(allocated[i],paid[i])
                b = actual[i]
                p += (b['x_raw']*price+b['y_raw'])*ratio
                f += (b['fee_x_raw']*price+b['fee_y_raw'])*ratio
                charged += composition[i]*ratio  # Already inside principal; never subtract twice.
            amount = sum(allocated.values())
            schemes[scheme] = dict(gross_pnl_sol=float((p+f-amount)/10**9),
                                  principal_change_vs_SOL_hodl_sol=float((p-amount)/10**9),
                                  fee_capture_sol=float(f/10**9), unspent_budget_lamports=budget-amount,
                                  scaled_observed_composition_fee_sol=float(charged/10**9))
        for values in schemes.values():
            values['paired_gross_delta_sol'] = values['gross_pnl_sol']-schemes['far_active']['gross_pnl_sol']
        return dict(status='modeled', funded_bins=len(funded_ids), position_bins=len(all_ids),
                    executed_entry_active_bin=execution_active,
                    actual_entry_composition_fee_sol=sum(composition.values())/10**9,
                    native_baseline_reconciliation_lamports=0, schemes=schemes,
                    basis='inferred_integer_funding_payments; fixed_realized_per_bin_return_rates; observed_composition_cost_in_principal; '
                          'integer_funding_allocations; SOL_only_HODL; not_executed_counterfactual_profit_or_IL')
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError):
        return dict(status='unmeasured', reason='invalid_native_allocation_evidence')


def bin_width_replay(entry, samples, *, end_ts=None):
    """Paired fixed-capital gross comparison; wider rent/execution costs unknown."""
    study = entry.get('width_study')
    if not isinstance(study, dict) or not study.get('snapshot'):
        return dict(status='unmeasured', reason='missing_pre_entry_width_snapshot')
    initial = entry.get('bin_snapshot') or {}
    snapshot = study['snapshot']
    lower, upper = study.get('lower_bin'), study.get('upper_bin')
    ids = [b['id'] for b in snapshot.get('bins', [])]
    base_ids = [b['id'] for b in initial.get('bins', [])]
    if (type(entry.get('entry_bin')) is not int
            or type(lower) is not int or type(upper) is not int or upper-lower != 69
            or not lower <= entry['entry_bin'] <= upper
            or sorted(ids) != list(range(lower, upper+1)) or not base_ids
            or not set(base_ids) < set(ids) or initial.get('ts') != snapshot.get('ts')
            or any(initial.get(k) != snapshot.get(k) for k in
                   ('active_bin', 'price', 'decimals_x', 'decimals_y', 'sol_is_x'))
            or [b for b in snapshot['bins'] if b['id'] in base_ids] != initial.get('bins')):
        return dict(status='unmeasured', reason='inconsistent_width_snapshot')
    baseline = bin_replay(entry, samples, end_ts=end_ts)
    wider_entry = dict(entry, bin_snapshot=snapshot,
                       bins_below=entry['entry_bin']-lower, bins_above=upper-entry['entry_bin'])
    wider = bin_replay(wider_entry, samples, end_ts=end_ts)
    if baseline.get('status') != 'modeled' or wider.get('status') != 'modeled':
        return dict(status='pending' if 'pending' in (baseline['status'], wider['status']) else 'unmeasured',
                    reason='paired_bin_replay_unavailable', baseline=baseline, wider=wider)
    old, new = baseline['schemes']['far_active'], wider['schemes']['far_active']
    return dict(status='modeled', baseline_bins=len(base_ids), wider_bins=len(ids),
                capital_sol=entry['size_sol'],
                horizon_complete=baseline['horizon_complete'] and wider['horizon_complete'],
                observed_until_ts=wider['observed_until_ts'], baseline=old, wider=new,
                deltas={k:new[k]-old[k] for k in ('gross_pnl_sol', 'il_vs_hodl_sol', 'fee_capture_sol')},
                basis='paired_infinitesimal_far_active; same_capital_and_observations; gross_before_costs',
                limitation='Not executed returns; wider range rent, market impact, slippage and actual exit policy are unmodeled.')


def bin_width_holding_replay(entry, samples, closed_at):
    """Compare allocations at the last observation before a proved actual close.

    This isolates allocation over the observed holding period. It does not
    simulate the alternative strategy's exit policy or value the sample gap.
    """
    started = (entry.get('bin_snapshot') or {}).get('ts')
    if (type(started) not in (int, float) or not math.isfinite(started)
            or type(closed_at) not in (int, float) or not math.isfinite(closed_at)
            or closed_at <= started):
        return dict(status='unmeasured',reason='actual_close_time_unavailable')
    observations = [s for s in samples if started < s['ts'] <= closed_at]
    if not observations:
        return dict(status='unmeasured',reason='no_followup_before_actual_close')
    terminal = max(s['ts'] for s in observations)
    gap = closed_at-terminal
    if gap > 600:
        return dict(status='unmeasured',reason='last_preclose_observation_too_old',
                    actual_close_ts=closed_at,seconds_before_close=gap)
    result = bin_width_replay(entry, observations, end_ts=terminal)
    return dict(result,actual_close_ts=closed_at,seconds_before_close=gap,
                cutoff_basis='last_observed_bin_state_before_actual_close; no_postclose_samples',
                limitation='Gross allocation comparison at an outcome-defined holding-period cutoff; '
                           'not net cash, executed IL, the unobserved close gap or an alternative exit policy.')


def width_study_summary(results):
    """Aggregate only paired, completed horizons and keep the entry modes apart."""
    groups = {}
    for row in results:
        mode = row.get('mode') or 'unknown'
        group = groups.setdefault(mode, dict(total=0, complete_pairs=0, capital_sol=0.0,
                                            gross_delta_sol=0.0, il_delta_sol=0.0, fee_delta_sol=0.0))
        group['total'] += 1
        if row.get('status') != 'modeled' or row.get('horizon_complete') is not True:
            continue
        group['complete_pairs'] += 1
        group['capital_sol'] += row['capital_sol']
        for dest, source in (('gross_delta_sol', 'gross_pnl_sol'),
                             ('il_delta_sol', 'il_vs_hodl_sol'), ('fee_delta_sol', 'fee_capture_sol')):
            group[dest] += row['deltas'][source]
    for group in groups.values():
        if not group['complete_pairs']:
            for key in ('capital_sol', 'gross_delta_sol', 'il_delta_sol', 'fee_delta_sol'):
                group[key] = None
    return groups


def native_liquidation_inventory(entry, wallet, mark):
    """Validate the exact withdrawal inventory already proved by the executor."""
    if not verified_risk_mark(mark, entry['pool'], entry['position'], time.time()):
        raise ValueError('native_inventory_proof_unavailable')
    inventory = mark.get('inventory')
    sol = 'So11111111111111111111111111111111111111112'
    if (not isinstance(inventory, dict) or type(inventory.get('version')) is not int
            or inventory['version'] != 1 or inventory.get('wallet') != wallet
            or inventory.get('token_x_mint') != entry['base_mint']
            or inventory.get('token_y_mint') != sol
            or not isinstance(mark.get('funding_signature'), str) or not mark['funding_signature']):
        raise ValueError('native_inventory_identity_mismatch')
    amounts = []
    for key in ('net_x_raw', 'net_y_raw', 'net_fee_x_raw', 'net_fee_y_raw'):
        value = inventory.get(key)
        if not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,20}', value) or int(value) >= 2**64:
            raise ValueError('invalid_native_inventory_amount')
        amounts.append(int(value))
    token, native = amounts[0]+amounts[2], amounts[1]+amounts[3]
    if token >= 2**64 or native >= 2**64:
        raise ValueError('native_inventory_sum_overflow')
    return dict(raw=token, native=Decimal(native)/10**9,
                deposit=Decimal(mark['deposit_lamports'])/10**9,
                mark=Decimal(str(mark['pnl_sol'])), updated=Decimal(str(mark['observed_at'])))


def read_native_risk_mark(profile, entry, wallet, deadline):
    """One bounded read-only executor probe; unsupported positions keep indexed fallback."""
    try:
        output = subprocess.check_output(
            ['node', str(profile/'skills/solana-dlmm/scripts/dlmm_executor.js'),
             'pnl-onchain', entry['pool'], entry['position']],
            stderr=subprocess.DEVNULL, timeout=request_timeout(deadline, 3))
        mark = json.loads(output)
        native_liquidation_inventory(entry, wallet, mark)
        return mark
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, KeyError):
        return None


def liquidation_observation(entry, wallet, fetch, native_mark=None):
    """Fresh position inventory plus a sell quote; excludes network fees and rent."""
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

    metadata = {}
    if native_mark is not None:
        proved = native_liquidation_inventory(entry, wallet, native_mark)
        raw, native, deposit, mark, updated = (proved[k] for k in ('raw','native','deposit','mark','updated'))
        maximum_age = 30
        metadata = dict(inventory_source='onchain_sol_inventory',
                        lp_mark_basis='native_active_bin_spot',
                        funding_signature=native_mark['funding_signature'],
                        native_inventory=native_mark['inventory'])
    else:
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
        maximum_age = 180
        metadata = dict(inventory_source='indexed_position', lp_mark_basis='meteora_indexed_lp')
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
    if not -5 <= observed - float(updated) <= maximum_age:
        raise ValueError('inventory_expired_during_quote')
    return dict(status='measured', position_updated_at=float(updated), observed_at=observed,
                deposit_sol=float(deposit), lp_mark_pnl_sol=float(mark),
                native_lp_assets_including_fees_sol=float(native), token_sell_raw=str(raw),
                quote=quote,
                quoted_assets_change_before_network_fees_sol=float(native + Decimal(out)/10**9 - deposit),
                minimum_quoted_assets_change_before_network_fees_sol=float(native + Decimal(minimum)/10**9 - deposit),
                **metadata,
                basis=('native' if native_mark is not None else 'indexed')
                      + '_inventory_plus_sell_quote_before_network_fees_not_net_cash',
                limitation='Inventory and quote differ in time; withdrawal can change liquidity. '
                           'Excludes network fees, rent, prior flows and rewards; quote is not an executed exit.')


def archive_exit_bank(profile, sample, deadline):
    """Optional unsigned research archive; never extend the collection deadline."""
    if (sample.get('status') != 'measured' or sample.get('inventory_source') != 'onchain_sol_inventory'
            or not sample.get('quote') or sample.get('token_sell_raw') == '0'):
        return None
    remaining = deadline - time.monotonic()
    if remaining < 4:
        return dict(status='unmeasured', reason='exit_bank_budget')
    try:
        budget = min(15, remaining)
        result = subprocess.run(
            ['node', str(profile/'skills/solana-dlmm/scripts/dlmm_exit_bank.js')],
            input=json.dumps(dict(profile=str(profile), sample=sample, budget_ms=int(budget*1000))),
            text=True, capture_output=True, timeout=budget, check=True)
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return dict(status='unmeasured', reason='exit_bank_unavailable')


def collect_liquidation(profile, deadline=None):
    """One position, one bounded native probe, then a quote or indexed fallback."""
    deadline = min(deadline if deadline is not None else float('inf'),
                   time.monotonic() + LIQUIDATION_BUDGET_SECONDS)
    memory = profile / 'memories'
    file = memory / 'dlmm_liquidation_quotes.jsonl'
    latest = {r['position']: r['observed_at'] for r in iter_rows(file)}
    closed = {r['position'] for r in iter_rows(memory / 'dlmm_closes.jsonl')
              if r.get('position') and not r.get('dry_run')}
    wallets = {r['position']: r['wallet'] for r in iter_rows(memory / 'dlmm_transactions.jsonl')
               if r.get('kind') == 'deploy' and r.get('position') and r.get('wallet')}

    def fetch(url):
        request = urllib.request.Request(url, headers={'User-Agent': 'dlmm-lp/1.0'})
        with urllib.request.urlopen(request, timeout=request_timeout(deadline, 10)) as response:
            return json.load(response)

    for entry_file in sorted((memory / 'dlmm_entries').glob('*.json'),
                             key=lambda p: latest.get(p.stem, 0)):
        if time.monotonic() >= deadline:
            return 0
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
            native_mark = read_native_risk_mark(profile, entry, wallets[position], deadline)
            sample.update(liquidation_observation(entry, wallets[position], fetch, native_mark=native_mark))
        except Exception as error:
            # HTTP errors can contain URLs; persist only their type, never credentials.
            sample.update(status='unmeasured', reason=type(error).__name__, observed_at=time.time())
        append(file, sample)
        # Save the ordinary quote first: optional research must not erase it.
        archive = archive_exit_bank(profile, sample, deadline)
        if archive is not None:
            append(memory/'dlmm_exit_bank_observations.jsonl',
                   dict(position=position, observed_at=time.time(), **archive))
        return 1
    return 0


def collect(profile, reject_file):
    deadline = time.monotonic() + COLLECTION_BUDGET_SECONDS
    memory=profile/'memories'; executor=profile/'skills/solana-dlmm/scripts/dlmm_executor.js'
    seen=set(); candidates={}; source_now=time.time()
    for row in iter_rows(reject_file):
        seen.add(row['id'])
        index_candidate(candidates,row,source_now)
    # Batch receipts are watch inputs, never rejected-candidate outcome IDs.
    # The same 30m/64-pool index and later three-read budget cover both sources.
    watch_files = [memory/WATCH_FILENAME,
                   Path(os.environ.get('SOLANA_CANDIDATE_WATCH_PATH') or
                        str(Path(reject_file).with_name('solana_candidate_watch.jsonl'))) ]
    for watch_file in watch_files:
        for row in iter_rows(watch_file):
            index_candidate(candidates,row,source_now)
    # Read completions after indexing the reject journal, as before. A second
    # streaming pass processes only the unfinished first-seen IDs.
    done={r['id'] for r in iter_rows(memory/'dlmm_reject_outcomes.jsonl')}
    pending=seen-done; visited=set()
    prices={}; processed=0
    reject_deadline = min(deadline, time.monotonic() + REJECT_BUDGET_SECONDS)
    reject_budget_exhausted = False
    for row in (iter_rows(reject_file) if pending else ()):
        ident=row['id']
        if ident not in pending or ident in visited:
            continue
        visited.add(ident)
        if time.time()<row['ts']+HORIZONS.get(row['mode'],86400): continue
        if time.monotonic() >= reject_deadline:
            reject_budget_exhausted = True
            break
        if processed>=100: break
        processed+=1
        price=None
        if time.time() <= row['ts']+HORIZONS.get(row['mode'],86400)+600:
            mint=row.get('candidate',{}).get('base_mint')
            try:
                if mint not in prices:
                    query=urllib.parse.urlencode({'query':mint,'page_size':100,'filter_by':'pool_type=dlmm','timeframe':'30m'})
                    request=urllib.request.Request('https://pool-discovery-api.datapi.meteora.ag/pools?'+query,headers={'User-Agent':'curl/8.5.0'})
                    with urllib.request.urlopen(request,timeout=request_timeout(reject_deadline,10)) as response:
                        prices[mint]={p['pool_address']:p.get('pool_price') for p in json.load(response)['data']}
                price=prices[mint].get(row['pool'])
            except Exception: pass
        append(memory/'dlmm_reject_outcomes.jsonl',rejected_outcome(row,price,int(time.time())))
    latest={}
    for sample in iter_rows(memory/'dlmm_bin_samples.jsonl'): latest[sample['position']]=sample['ts']
    count=0
    bin_deadline = min(deadline - LIQUIDATION_BUDGET_SECONDS,
                       time.monotonic() + BIN_BUDGET_SECONDS)
    bin_budget_exhausted = False
    for file in sorted((memory/'dlmm_entries').glob('*.json'),key=lambda p:latest.get(p.stem,0)):
        entry=json.loads(file.read_text()); initial=entry.get('bin_snapshot')
        if not initial: continue
        position=entry['position']
        target=initial['ts']+HORIZONS.get(entry.get('mode'),86400)
        if time.time()>target+600 or latest.get(position,0)>=target: continue
        if time.time()-latest.get(position,0)<240: continue
        if time.monotonic() >= bin_deadline:
            bin_budget_exhausted = True
            break
        if count>=12: break
        count+=1
        try:
            study = entry.get('width_study') or {}
            ids=[b['id'] for b in (study.get('snapshot') or initial)['bins']]
            output=subprocess.check_output(['node',str(executor),'bin-snapshot',entry['pool'],str(min(ids)),str(max(ids))],stderr=subprocess.DEVNULL,timeout=request_timeout(bin_deadline,25))
            sample=json.loads(output);sample['position']=position
            append(memory/'dlmm_bin_samples.jsonl',sample)
        except Exception: pass
    candidate_results=collect_candidate_bins(profile,candidates,deadline)
    return {'rejects_total':len(seen),'outcomes_attempted':processed,'bin_snapshots_attempted':count,
            'reject_budget_exhausted':reject_budget_exhausted,
            'bin_budget_exhausted':bin_budget_exhausted,
            **candidate_results,
            'liquidation_observations_attempted':collect_liquidation(profile,deadline)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',type=Path,default=Path(os.path.abspath(__file__)).parent.parent.parent.parent)
    parser.add_argument('--rejects',type=Path,default=Path.home()/'.local/state/azimuth/solana_rejects.jsonl')
    args=parser.parse_args();print(json.dumps(collect(args.profile,args.rejects)))

if __name__=='__main__':main()
