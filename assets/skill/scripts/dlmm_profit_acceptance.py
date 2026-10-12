"""Conservative per-position cash acceptance; read-only, never a trading gate."""
import collections
import math

from dlmm_accounting import refund_cash_bounds
from dlmm_cash_sign import cash_sign_upper_bound


def position_profit_acceptance(accounting, entries, start, end):
    """Require strictly positive proved cash for every entry in the window.

    Root cash can establish a position's result only for a single-position root.
    Shared refund fees retain conservative bounds; bounds must never be summed.
    Open/incomplete positions remain in the denominator, with no assumed result.
    """
    chains = {c['root_chain_id']: c for c in accounting['chains']}
    owners = collections.defaultdict(list)
    for chain in accounting['chains']:
        for position in chain.get('positions', []):
            owners[position].append(chain['root_chain_id'])
    groups = collections.defaultdict(list)
    for group in accounting.get('rent_refund_groups', []):
        for root in group['root_chain_ids']:
            groups[root].append(group)
    selected = collections.defaultdict(list)
    sign_proofs = collections.defaultdict(list)
    for proof in accounting.get('nonpositive_cash_upper_bounds', []):
        sign_proofs[proof['root_chain_id']].append(proof)
    for entry in entries:
        deployed = entry.get('deployed_at')
        if (type(deployed) in (int, float) and math.isfinite(deployed)
                and start <= deployed <= end):
            selected[entry['position']].append(entry)

    positions = []
    for position, records in sorted(selected.items()):
        entry = records[0]
        root = entry.get('root_chain_id') or entry.get('recenter_of') or position
        row = dict(position=position, root=root, mode=entry.get('mode'),
                   deployed_at=entry['deployed_at'], outcome='unmeasured',
                   cash_lower_lamports=None, cash_upper_lamports=None)
        positions.append(row)
        chain = chains.get(root)
        if len(records) != 1 or owners[position] != [root] or chain is None:
            row['reason'] = 'entry_or_root_identity_not_unique'
            continue
        if chain.get('positions') != [position]:
            row['reason'] = 'multiple_position_root_has_no_per_position_cash_attribution'
            continue
        first, last = chain.get('first_activity'), chain.get('last_activity')
        if (type(first) not in (int, float) or type(last) not in (int, float)
                or not start <= first <= last <= end):
            row['reason'] = 'root_activity_not_contained_in_entry_window'
            continue
        if chain.get('accounting_status') != 'settled_cash':
            row['reason'] = 'position_cash_incomplete'
            continue
        if not groups[root] and len(sign_proofs[root]) == 1:
            upper = cash_sign_upper_bound(sign_proofs[root][0], chain, end)
            if upper is not None:
                row.update(cash_upper_lamports=upper, outcome='nonpositive',
                           reason='proved_no_retained_wallet_funding; upper_only; final_cleanup_cost_unknown')
                continue
        if len(groups[root]) != 1:
            row['reason'] = 'owned_rent_proof_missing_or_ambiguous'
            continue
        group = groups[root][0]
        if any(len(groups[member]) != 1 for member in group['root_chain_ids']):
            row['reason'] = 'owned_rent_proof_missing_or_ambiguous'
            continue
        last_refund = group.get('last_activity')
        if (type(last_refund) not in (int, float) or not math.isfinite(last_refund)
                or last_refund > end):
            row['reason'] = 'refund_not_observed_by_cutoff'
            continue
        bounds = refund_cash_bounds(group, chains, {root})
        if bounds is None:
            row['reason'] = 'refund_cash_bounds_not_proved'
            continue
        lower, upper = bounds
        row.update(cash_lower_lamports=lower, cash_upper_lamports=upper,
                   outcome='positive' if lower > 0 else 'nonpositive' if upper <= 0 else 'unresolved',
                   reason='single_position_settled_cash_with_proved_owned_rent')

    counts = collections.Counter(row['outcome'] for row in positions)
    status = ('failed' if counts['nonpositive'] else
              'observed_all_positive' if positions and counts['positive'] == len(positions)
              else 'not_verified')
    return dict(status=status, window_positions=len(positions),
                positive_positions=counts['positive'], nonpositive_positions=counts['nonpositive'],
                unresolved_positions=counts['unresolved'], unmeasured_positions=counts['unmeasured'],
                positive_fraction_of_all_entries=counts['positive']/len(positions) if positions else None,
                positions=positions, future_profit_guaranteed=False,
                basis='entry_window; strictly_positive_per_position_settled_cash_lower_bound_after_costs_and_proved_rent; no_multi_position_root_allocation; do_not_sum_shared_fee_bounds; not_portfolio_NAV')
