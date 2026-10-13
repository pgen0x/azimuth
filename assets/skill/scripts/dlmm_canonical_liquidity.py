"""Validate and retain bounded public native liquidity evidence, never gate trading."""
import re

SOL = 'So11111111111111111111111111111111111111112'
TOKEN_PROGRAMS = {'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
                  'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'}
ADDRESS = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}\Z')
BASIS = ('native_canonical_pump_accounts; circulating_LP_is_potential_withdrawal_upper_bound; '
         'not_profit_or_withdrawability_proof')
REASONS = {'budget_exhausted', 'wallet_trade_active', 'canonical_pool_absent',
           'rpc_unavailable', 'native_evidence_unavailable', 'read_timeout'}
UINT_FIELDS = ('lp_circulating_raw', 'protocol_lp_basis_raw', 'base_reserve_raw',
               'quote_vault_raw', 'protocol_fees_raw', 'creator_fees_raw',
               'real_quote_raw', 'effective_quote_raw', 'boost_reserves_raw')


def retain_canonical_snapshot(value, mint, started, collected):
    """Malformed/absent optional evidence leaves the original bin sample usable."""
    unavailable = dict(version=1, status='unmeasured', reason='invalid_canonical_snapshot')
    if value is None:
        return dict(unavailable, reason='missing_canonical_snapshot')
    try:
        if (not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != 1
                or value.get('base_mint') != mint or value.get('quote_mint') != SOL):
            return unavailable
        request, observed = value.get('request_started_at'), value.get('observed_at')
        if (type(request) not in (int, float) or type(observed) not in (int, float)
                or not started - 1 <= request <= observed <= collected):
            return unavailable
        result = dict(version=1, base_mint=mint, quote_mint=SOL,
                      request_started_at=request, observed_at=observed)
        if value.get('status') == 'unmeasured' and value.get('reason') in REASONS:
            return dict(result, status='unmeasured', reason=value['reason'])
        if (value.get('status') != 'observed' or value.get('basis') != BASIS
                or type(value.get('context_slot')) is not int or value['context_slot'] <= 0
                or value.get('lp_token_program') not in TOKEN_PROGRAMS
                or value.get('base_token_program') not in TOKEN_PROGRAMS):
            return unavailable
        for key in ('canonical_pool', 'lp_mint', 'pool_coin_creator'):
            if not isinstance(value.get(key), str) or not ADDRESS.fullmatch(value[key]):
                return unavailable
            result[key] = value[key]
        freeze = value.get('lp_freeze_authority')
        if freeze is not None and (not isinstance(freeze, str) or not ADDRESS.fullmatch(freeze)):
            return unavailable
        numbers = {}
        for key in UINT_FIELDS + ('signed_virtual_quote_raw',):
            number = value.get(key)
            pattern = r'-?(?:0|[1-9][0-9]{0,38})' if key == 'signed_virtual_quote_raw' else r'0|[1-9][0-9]{0,19}'
            if not isinstance(number, str) or not re.fullmatch(pattern, number):
                return unavailable
            numbers[key] = int(number)
            if key == 'signed_virtual_quote_raw':
                if not -(2**127) <= numbers[key] < 2**127:
                    return unavailable
            elif not 0 <= numbers[key] < 2**64:
                return unavailable
            result[key] = number
        fees = numbers['protocol_fees_raw'] + numbers['creator_fees_raw']
        if (not 0 <= numbers['lp_circulating_raw'] <= numbers['protocol_lp_basis_raw']
                or numbers['protocol_lp_basis_raw'] == 0
                or numbers['real_quote_raw'] != numbers['quote_vault_raw'] - fees
                or numbers['effective_quote_raw'] != numbers['quote_vault_raw'] + numbers['signed_virtual_quote_raw']
                or numbers['boost_reserves_raw'] != numbers['signed_virtual_quote_raw'] + fees):
            return unavailable
        return dict(result, status='observed', context_slot=value['context_slot'],
                    lp_token_program=value['lp_token_program'], base_token_program=value['base_token_program'],
                    lp_freeze_authority=freeze, basis=BASIS)
    except (ValueError, TypeError, OverflowError):
        return unavailable
