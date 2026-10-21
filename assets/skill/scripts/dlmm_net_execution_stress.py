#!/usr/bin/env python3
"""Offline sensitivity of frozen exits to worse token proceeds; never trades."""
import argparse
import json
from pathlib import Path
from dlmm_net_experiment import write

SOL = 'So11111111111111111111111111111111111111112'


def stress(cohort, quotes, bps):
    if type(bps) is not int or not 0 <= bps <= 10000:
        raise ValueError('shock must be integer basis points in [0, 10000]')
    penalties = []
    missing = []
    for row in cohort['positions']:
        decision = row.get('decision')
        if not decision:
            continue
        matches = quotes.get((row['position'], decision['observed_at']), [])
        amounts = set()
        for observation in matches:
            quote = observation.get('quote') or {}
            amount = quote.get('otherAmountThreshold')
            if (observation.get('status') == 'measured'
                    and observation.get('inventory_source') == 'onchain_sol_inventory'
                    and quote.get('outputMint') == SOL
                    and quote.get('swapMode') == 'ExactIn'
                    and isinstance(amount, str) and amount.isascii() and amount.isdigit()):
                amounts.add(int(amount))
        if len(amounts) != 1:
            missing.append(row['position'])
            continue
        minimum = amounts.pop()
        # Conservative integer rounding. Only token proceeds are shocked: native
        # inventory and rent principal do not fall with the token sale price.
        penalty = (minimum * bps + 9999) // 10000
        penalties.append(dict(position=row['position'], token_minimum_lamports=minimum,
                              penalty_lamports=penalty,
                              stressed_modeled_net_lamports=decision['modeled_net_lamports']-penalty))
    complete = not missing and len(penalties) == cohort['modeled_exits']
    return dict(shock_bps=bps, complete=complete, missing_positions=missing,
                net_lower_lamports=cohort['net_lower_lamports']-sum(p['penalty_lamports'] for p in penalties) if complete else None,
                positions=penalties)


def run(source, quote_file, output):
    if output.exists():
        raise ValueError('Output already exists; preserve prior evidence')
    result = json.loads(source.read_text())
    wanted = {(r['position'], r['decision']['observed_at'])
              for c in (result['winner']['training'], result['validation'])
              for r in c['positions'] if r.get('decision')}
    quotes = {}
    with quote_file.open() as handle:
        for line in handle:
            row = json.loads(line)
            key = (row.get('position'), row.get('observed_at'))
            if key in wanted:
                quotes.setdefault(key, []).append(row)
    report = dict(source=str(source), quote_file=str(quote_file), promotion_allowed=False,
                  limitation='Sensitivity only, not executable fills or measured latency costs. Frozen decisions unchanged. Actual-exit fallback retained. Missing sale evidence invalidates aggregate.',
                  training=[stress(result['winner']['training'], quotes, b) for b in (0,100,300,500)],
                  validation=[stress(result['validation'], quotes, b) for b in (0,100,300,500)])
    write(output, report)
    print(json.dumps({k:[{a:b for a,b in r.items() if a!='positions'} for r in report[k]] for k in ('training','validation')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--quotes', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.quotes, args.output)
