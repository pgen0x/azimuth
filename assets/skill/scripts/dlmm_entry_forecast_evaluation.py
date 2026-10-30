"""Read-only verification of pre-submission forecast references and position cash."""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path

from dlmm_fee_forecast import FORECAST_FILE, HORIZONS, candidate_fee_forecast, sample_hash
from dlmm_profit_acceptance import position_profit_acceptance
from dlmm_shadow import validate_candidate_snapshot


def verify_reference(entry, records, samples):
    ref = entry.get('fee_forecast_reference')
    if not isinstance(ref, dict) or ref.get('status') != 'matched_reference':
        return dict(status='unmeasured', reason='no_matched_pre_submission_reference')
    try:
        f = records[ref['forecast_line_sha256']]
        when = ref['recorded_at']
        if (type(when) not in (int, float) or not math.isfinite(when)
                or math.floor(when) != entry['deployed_at']
                or f['id'] != ref['forecast_id'] or f['version'] != 2
                or f['pool'] != entry['pool'] or f['base_mint'] != entry['base_mint']
                or f['mode'] != entry['mode'] or entry['strategy'] != 'sol_bidask'
                or entry['amount_x'] != 0 or entry['amount_y'] != .1 or entry['bins_above'] != 0
                or f['capital_lamports'] != 100000000 or f['bin_step'] != entry['bin_step']
                or f['bins_below'] != entry['bins_below']
                or f['horizon_seconds'] != HORIZONS[entry['mode']]
                or not f['baseline_ts'] <= f['frozen_at'] <= f['recorded_at'] <= when < f['horizon_target_ts']
                or when - f['baseline_ts'] > 600
                or ref['baseline_age_seconds'] != when - f['baseline_ts']
                or ref['forecast_recorded_at'] != f['recorded_at']
                or ref['linear_fee_lamports'] != f['linear_fee_lamports']
                or ref['baseline_sha256'] != f['baseline_sha256'] or ref['prior_sha256'] != f['prior_sha256']
                or [a['id'] for a in f['allocations']] != list(range(entry['entry_bin']-entry['bins_below'], entry['entry_bin']+1))):
            raise ValueError('entry binding mismatch')
        base, prior = samples[f['baseline_sha256']], samples[f['prior_sha256']]
        rebuilt = candidate_fee_forecast(base, [prior], f['frozen_at'], validate_candidate_snapshot,
                                         frozen_geometry=f['bins_below'], frozen_horizon=f['horizon_seconds'],
                                         model_version=f['version'])
        rebuilt['recorded_at'] = f['recorded_at']
        if rebuilt != f:
            raise ValueError('forecast reconstruction mismatch')
        return dict(status='verified_reference', forecast_id=f['id'],
                    forecast_fee_lamports=f['linear_fee_lamports'], horizon_seconds=f['horizon_seconds'],
                    basis='pre_submission_local_provenance; not_onchain_entry_time_or_profit')
    except (KeyError, TypeError, ValueError, OverflowError):
        return dict(status='unmeasured', reason='forecast_entry_or_input_binding_mismatch')


def evaluate(entries, accounting, forecast_bytes, samples, start, end):
    records = {}
    # Only full newline-terminated records, preserving the exact JS line hash.
    for line in forecast_bytes.split(b'\n')[:-1]:
        try:
            records[hashlib.sha256(line).hexdigest()] = json.loads(line)
        except (ValueError, UnicodeError):
            continue
    by_hash = {}
    for sample in samples:
        try:
            by_hash[sample_hash(sample)] = sample
        except (TypeError, ValueError):
            continue
    cash = position_profit_acceptance(accounting, entries, start, end)
    by_position = {}
    for entry in entries:
        by_position.setdefault(entry['position'], []).append(entry)
    rows = []
    for outcome in cash['positions']:
        matches = by_position[outcome['position']]
        reference = (verify_reference(matches[0], records, by_hash) if len(matches) == 1 else
                     dict(status='unmeasured', reason='ambiguous_entry_records'))
        rows.append(dict(position=outcome['position'], reference=reference, cash=outcome))
    return dict(cash_acceptance=cash, entries=len(rows),
                verified_references=sum(r['reference']['status']=='verified_reference' for r in rows),
                rows=rows, future_profit_guaranteed=False,
                limits=['All entries remain in the cash denominator, including missing forecast references.',
                        'Forecast fee and settled net cash are different quantities; their ratio is not prediction accuracy.',
                        'Reference verification proves local provenance and geometry, not executable returns or pure IL.',
                        'Shared refund cash bounds must not be summed.'])


if __name__ == '__main__':
    from dlmm_accounting import report, rows
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--start', type=float, required=True)
    args = parser.parse_args()
    memory = args.profile/'memories'
    entries = [json.loads(p.read_text()) for p in (memory/'dlmm_entries').glob('*.json')]
    journal = memory/FORECAST_FILE
    print(json.dumps(evaluate(entries, report(args.profile), journal.read_bytes() if journal.exists() else b'',
                              list(rows(memory/'dlmm_candidate_bin_samples.jsonl')), args.start, time.time()), indent=2))
