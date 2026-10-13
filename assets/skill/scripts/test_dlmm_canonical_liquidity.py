"""Optional native evidence cannot corrupt bins, leak payloads, or become a gate."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dlmm_canonical_liquidity import BASIS, SOL, retain_canonical_snapshot
import dlmm_shadow as shadow

MINT = '3q2U15sSP4gy6PEYgmcVtEyurEHBhXgLre21NeHNpump'
POOL = 'HZs6bUjefdrPqJZP7TU4uUWvXE125zWdyeHp5eY8TTDX'
TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'


def native(**changes):
    return dict(dict(version=1, status='observed', base_mint=MINT, quote_mint=SOL,
                     request_started_at=10000, observed_at=10000.1, context_slot=456200000,
                     canonical_pool='7qZeWsd4UBcRDT6HRhJDvTvwxEp5HcvV2SaZPJRF4Q34',
                     lp_mint='9bwAcKgXVwuMP9uyUJKuK4HiA1gMFStARjUYnKEh7PWj',
                     lp_token_program=TOKEN, base_token_program=TOKEN,
                     lp_freeze_authority=None, pool_coin_creator=MINT,
                     lp_circulating_raw='9007199254740993', protocol_lp_basis_raw='9007199254740994',
                     base_reserve_raw='100000000000000', quote_vault_raw='1000000000000',
                     signed_virtual_quote_raw='-3000000', protocol_fees_raw='1000000', creator_fees_raw='2000000',
                     real_quote_raw='999997000000', effective_quote_raw='999997000000', boost_reserves_raw='0',
                     basis=BASIS, secret='must-not-persist'), **changes)


class CanonicalLiquidityTests(unittest.TestCase):
    def keep(self, value):
        return retain_canonical_snapshot(value, MINT, 10000, 10000.2)

    def test_signed_reserves_exact_large_integers_and_whitelist(self):
        result = self.keep(native())
        self.assertEqual(result['status'], 'observed')
        self.assertEqual(result['lp_circulating_raw'], '9007199254740993')
        self.assertEqual(result['signed_virtual_quote_raw'], '-3000000')
        self.assertNotIn('secret', result)
        value = native(signed_virtual_quote_raw='5000000', effective_quote_raw='1000005000000', boost_reserves_raw='8000000')
        self.assertEqual(self.keep(value)['status'], 'observed')
        self.assertNotIn('withdrawable', self.keep(value))

    def test_invalid_identity_time_integer_and_economic_relationships(self):
        for change in [dict(base_mint=SOL), dict(quote_mint=MINT), dict(version=True),
                       dict(context_slot=True), dict(observed_at=10001), dict(request_started_at=9998),
                       dict(observed_at=float('nan')), dict(lp_circulating_raw=9007199254740993),
                       dict(lp_circulating_raw=str(2**64)), dict(protocol_lp_basis_raw='0'),
                       dict(protocol_lp_basis_raw='1'), dict(real_quote_raw='1000000000000'),
                       dict(effective_quote_raw='1000000000000'), dict(boost_reserves_raw='1'),
                       dict(signed_virtual_quote_raw=str(2**127)), dict(lp_mint='bad'),
                       dict(lp_token_program='bad'), dict(lp_freeze_authority='bad'),
                       dict(protocol_fees_raw='-1'), dict(creator_fees_raw=str(2**64))]:
            with self.subTest(change=change):
                self.assertEqual(self.keep(native(**change))['status'], 'unmeasured')
        for value in [None, {}, [], 'secret', native(reason=[], status='unmeasured')]:
            self.assertEqual(self.keep(value)['status'], 'unmeasured')

    def test_absence_and_failure_do_not_mean_zero_or_retain_error_text(self):
        result = self.keep(native(status='unmeasured', reason='canonical_pool_absent'))
        self.assertEqual(result['reason'], 'canonical_pool_absent')
        self.assertNotIn('lp_circulating_raw', result)
        result = self.keep(native(status='unmeasured', reason='https://secret.invalid'))
        self.assertNotIn('secret', json.dumps(result))
        self.assertNotIn('lp_circulating_raw', result)

    def test_existing_candidate_collector_retains_optional_evidence_without_extra_command(self):
        sample = dict(status='observed', pool=POOL, ts=10000, active_bin=0, anchor_bin=0,
                      lower_bin=-69, upper_bin=16, price=.001, decimals_x=6, decimals_y=9,
                      sol_is_x=False, token_x_mint=MINT, token_y_mint=SOL, bin_step=100,
                      canonical_liquidity=native(),
                      bins=[dict(id=i, x='0', y='1000000', supply=str(2**64),
                                 fee_x='0', fee_y='0', price=.001) for i in range(-69, 17)])
        candidates = {POOL: dict(pool=POOL, base_mint=MINT, mode='pulse', source_id='watch', source_ts=10000)}
        for value in [native(), native(base_mint=SOL), None]:
            sample['canonical_liquidity'] = value
            with tempfile.TemporaryDirectory() as directory:
                profile = Path(directory)
                with patch.object(shadow.time, 'time', return_value=10000.2), \
                     patch.object(shadow.time, 'monotonic', return_value=0), \
                     patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(sample).encode()) as read:
                    result = shadow.collect_candidate_bins(profile, candidates, 40)
                self.assertEqual(read.call_count, 1)
                self.assertEqual(result['candidate_bin_snapshots_observed'], 1)
                stored = shadow.rows(profile / 'memories/dlmm_candidate_bin_samples.jsonl')[0]
                self.assertEqual(len(stored['bins']), 86)
                self.assertEqual(stored['bin_step'], 100)
                self.assertNotIn('secret', json.dumps(stored))
                self.assertEqual(stored['canonical_liquidity']['status'], 'observed' if value and value['base_mint'] == MINT else 'unmeasured')
                # Neither a later native observation nor a later collection can
                # masquerade as pre-entry evidence through the existing join.
                initial = deepcopy(sample)
                initial['ts'] = 10240
                initial['bins'] = [dict(b, fee_y='100') for b in initial['bins'] if -44 <= b['id'] <= 0]
                entry = dict(position='future', pool=POOL, base_mint=MINT, deployed_at=10241, bin_snapshot=initial)
                self.assertEqual(shadow.pre_entry_bin_coverage([entry], profile / 'memories/dlmm_candidate_bin_samples.jsonl', 10300)[0]['status'], 'observed')


if __name__ == '__main__':
    unittest.main()
