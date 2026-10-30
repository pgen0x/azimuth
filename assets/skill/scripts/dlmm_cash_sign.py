"""Upper-only cash sign proof; never an exact outcome, positive label or subtotal."""
import collections
import math

FACT_BASIS = 'parsed_system_debits_and_unchanged_retained_token_accounts'
UPPER_BASIS = 'settled_cash_without_retained_wallet_funding; upper_only; not_NAV'


RENT_FACT_BASIS = 'parsed_empty_token_rent_with_no_other_retained_wallet_funding'
RENT_UPPER_BASIS = 'settled_cash_with_maximum_retained_rent_credit; upper_only; not_NAV'


def retained_credit(fact, position):
    proof = fact.get('cash_sign_evidence')
    if (isinstance(proof, dict) and proof.get('version') == 1
            and proof.get('position') == position and proof.get('basis') == FACT_BASIS
            and proof.get('no_retained_wallet_funding_outside_position') is True):
        return 0
    proof = fact.get('retained_rent_evidence')
    if (not isinstance(proof, dict) or proof.get('version') != 1
            or proof.get('position') != position or proof.get('basis') != RENT_FACT_BASIS):
        return None
    accounts, cap = proof.get('funded_accounts'), proof.get('max_future_rent_credit_lamports')
    if (not isinstance(accounts, list) or not accounts or type(cap) is not int
            or not 0 < cap <= 2**53-1):
        return None
    seen, total = set(), 0
    for row in accounts:
        if (not isinstance(row, dict) or not isinstance(row.get('account'), str)
                or not row['account'] or row['account'] in (position, fact.get('wallet'))
                or row['account'] in seen or not isinstance(row.get('mint'), str)
                or not row['mint'] or type(row.get('lamports')) is not int or row['lamports'] <= 0):
            return None
        seen.add(row['account'])
        total += row['lamports']
    return cap if total == cap else None


def nonpositive_cash_upper_bounds(chains, facts, rent_groups, as_of):
    """Credit only a proved maximum retained reserve; later cleanup costs can only hurt.

    Restrict to single-position roots with unchanged inventory, bounded reserve and
    collector proof for every successful transaction. No legacy cache inference.
    """
    owners = collections.defaultdict(set)
    for chain in chains:
        for signature in chain.get('recorded_signatures', []):
            owners[signature].add(chain['root_chain_id'])
    matched = {root for group in rent_groups for root in group['root_chain_ids']}
    result = []
    for chain in chains:
        root = chain['root_chain_id']
        positions = chain.get('positions', [])
        cash = chain.get('wallet_delta_lamports')
        signatures = chain.get('recorded_signatures', [])
        if (root in matched or chain.get('accounting_status') != 'settled_cash'
                or len(positions) != 1 or chain.get('pending_signatures')
                or chain.get('expired_unlanded_signatures') or chain.get('token_deltas_raw')
                or type(cash) is not int or cash > 0 or not signatures
                or len(set(signatures)) != len(signatures)
                or any(owners[s] != {root} for s in signatures)):
            continue
        records = [facts.get(s, {}) for s in signatures]
        wallet = records[0].get('wallet')
        valid = isinstance(wallet, str) and bool(wallet)
        rent_credit = 0
        for signature, fact in zip(signatures, records):
            if (fact.get('signature') != signature or fact.get('wallet') != wallet
                    or fact.get('event_position') != positions[0]
                    or fact.get('classification') != 'recorded_bot'
                    or fact.get('basis') != 'finalized_transaction_balances'
                    or fact.get('landed') is False or type(fact.get('failed')) is not bool
                    or type(fact.get('schema_version')) is not int or fact['schema_version'] < 12
                    or type(fact.get('slot')) is not int or fact['slot'] <= 0
                    or type(fact.get('wallet_delta_lamports')) is not int
                    or type(fact.get('fee_lamports')) is not int or fact['fee_lamports'] < 0
                    or any(type(fact.get(k)) not in (int, float) or not math.isfinite(fact[k])
                           or fact[k] > as_of for k in ('block_time', 'observed_at'))):
                valid = False
                break
            if fact['failed']:
                if (fact['wallet_delta_lamports'] != -fact['fee_lamports']
                        or not isinstance(fact.get('token_deltas_raw'), dict)
                        or any(v != '0' for v in fact['token_deltas_raw'].values())):
                    valid = False
                    break
                continue  # Finalized failure persists only its network fee.
            credit = retained_credit(fact, positions[0])
            if (credit is None or not isinstance(fact.get('token_deltas_raw'), dict)
                    or any(v != '0' for v in fact['token_deltas_raw'].values())):
                valid = False
                break
            rent_credit += credit  # Repeated funding overcredits conservatively; never undercredits.
        if not valid or cash + rent_credit > 0:
            continue
        successful = [f for f in records if f.get('failed') is False]
        latest = max((f.get('slot', 0) for f in successful), default=0)
        final = [f for f in successful if f.get('slot') == latest]
        if (len(final) != 1 or final[0].get('position_account_closed') is not True
                or sum(f['wallet_delta_lamports'] for f in records) != cash
                or sum(f['fee_lamports'] for f in records) != chain.get('network_fee_lamports')):
            continue
        observed = max([chain.get('last_activity', float('inf'))]
                       + [f['observed_at'] for f in records] + [f['block_time'] for f in records])
        if not math.isfinite(observed) or observed > as_of:
            continue
        result.append(dict(root_chain_id=root, position=positions[0],
                           cash_lower_lamports=None, cash_upper_lamports=cash+rent_credit,
                           recorded_signatures=signatures, observed_at=observed,
                           basis=RENT_UPPER_BASIS if rent_credit else UPPER_BASIS,
                           **({'max_future_rent_credit_lamports': rent_credit} if rent_credit else {})))
    return result


def cash_sign_upper_bound(proof, chain, as_of):
    """Validate an in-process report result against its current whole root."""
    upper = proof.get('cash_upper_lamports')
    observed = proof.get('observed_at')
    credit = proof.get('max_future_rent_credit_lamports', 0)
    if (type(credit) is not int or credit < 0
            or (proof.get('basis') == UPPER_BASIS and credit != 0)
            or (proof.get('basis') == RENT_UPPER_BASIS and credit <= 0)):
        return None
    if (proof.get('basis') not in (UPPER_BASIS, RENT_UPPER_BASIS) or proof.get('root_chain_id') != chain['root_chain_id']
            or chain.get('positions') != [proof.get('position')]
            or chain.get('accounting_status') != 'settled_cash'
            or chain.get('pending_signatures') or chain.get('expired_unlanded_signatures')
            or chain.get('token_deltas_raw')
            or proof.get('recorded_signatures') != chain.get('recorded_signatures')
            or not proof.get('recorded_signatures') or proof.get('cash_lower_lamports') is not None
            or type(upper) is not int or upper > 0
            or type(chain.get('wallet_delta_lamports')) is not int
            or upper != chain['wallet_delta_lamports'] + credit
            or type(observed) not in (int, float) or not math.isfinite(observed) or observed > as_of
            or observed < chain.get('last_activity', float('inf'))):
        return None
    return upper
