"""Reject repeat entries only from fresh, journal-bound proved pool cash losses."""
import json
import math


def negative_pool_cash(cache, pool, journal_text, now):
    """Return a strictly negative cash upper bound, otherwise no new refusal."""
    finite = lambda v: type(v) in (int, float) and math.isfinite(v)
    if not finite(now) or not isinstance(cache, dict) or not isinstance(journal_text, str):
        return None
    cash = cache.get(pool)
    if not isinstance(cash, dict):
        return None
    try:
        journal = []
        for line in journal_text.splitlines():
            if not line or line == '(nil)':
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not finite(row.get('ts')):
                return None
            if now - 30*86400 <= row['ts'] <= now:
                journal.append(row)
        latest = max((r['ts'] for r in journal), default=0)
        # This independent proof requires both newest journal positions to be
        # individually negative. It never substitutes zero for older unknowns.
        recent = cash.get('recent_position_cash_losses')
        ordered = sorted(journal, key=lambda row: row['ts'], reverse=True)
        if (isinstance(recent, list) and len(recent) == 2 and len(ordered) >= 2
                and finite(cash.get('observed_at')) and 0 <= now-cash['observed_at'] <= 900
                and type(cash.get('journal_closes')) is int and cash['journal_closes'] == len(journal)
                and cash.get('journal_last_close_ts') == latest
                and ordered[0]['ts'] != ordered[1]['ts']
                and all(isinstance(proof, dict) and isinstance(proof.get('position'), str)
                        and proof['position'] and proof['position'] == row.get('position')
                        and proof.get('root') == (row.get('root_chain_id') or row.get('recenter_of') or row.get('position'))
                        and proof.get('ts') == row['ts']
                        and type(proof.get('cash_upper_lamports')) is int
                        and -2**53 < proof['cash_upper_lamports'] < 0
                        for proof, row in zip(recent, ordered[:2]))
                and len({proof['root'] for proof in recent}) == 2):
            return dict(closes=2, basis='latest_two_individual_cash_losses',
                        cash_upper_sol=max(p['cash_upper_lamports'] for p in recent)/1e9,
                        scope='each_of_latest_two')
        count = cash['prior_closes']
        if (type(count) is not int or not 2 <= count <= 10
                or type(cash['journal_closes']) is not int
                or cash['journal_closes'] != len(journal)
                or cash['journal_last_close_ts'] != latest
                or count < len(journal)
                or not finite(cash['observed_at']) or not 0 <= now-cash['observed_at'] <= 900
                or not finite(cash['last_close_ts'])
                or not max(latest, now-30*86400) <= cash['last_close_ts'] <= now
                or type(cash['prior_roots']) is not int or not 1 <= cash['prior_roots'] <= count
                or type(cash['prior_cash_roots']) is not int
                or cash['prior_cash_roots'] != cash['prior_roots']):
            return None
        basis = cash['prior_pnl_basis']
        net, lo, hi = (cash.get(k) for k in ('prior_net_pnl_sol','prior_cash_lower_sol','prior_cash_upper_sol'))
        if basis == 'matched_refund_cash':
            if not finite(net) or lo != net or hi != net:
                return None
        elif basis == 'matched_refund_cash_bounds':
            if net is not None or not finite(lo) or not finite(hi) or lo > hi:
                return None
        elif basis == 'nonpositive_cash_upper_bound':
            if net is not None or lo is not None:
                return None
        else:
            return None
        if finite(hi) and hi < 0:
            return dict(closes=count, cash_upper_sol=hi, basis=basis)
    except (KeyError, TypeError, ValueError):
        pass
    return None
