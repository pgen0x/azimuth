from copy import deepcopy
import hashlib
import json
import unittest

from dlmm_entry_forecast_evaluation import evaluate
from dlmm_fee_forecast import candidate_fee_forecast
from dlmm_shadow import validate_candidate_snapshot
from test_dlmm_fee_forecast import sample, POOL, MINT


class EntryReferenceTests(unittest.TestCase):
    def setUp(self):
        self.samples = [sample(9700, 0), sample()]
        self.forecast = candidate_fee_forecast(self.samples[1], self.samples[:1], 10000.2,
                                              validate_candidate_snapshot)
        self.line = json.dumps(self.forecast).encode()
        f = self.forecast
        self.entry = dict(position='pos', root_chain_id='pos', deployed_at=10001,
                          pool=POOL, base_mint=MINT, mode='pulse', strategy='sol_bidask',
                          amount_x=0, amount_y=.1, bins_above=0, bins_below=f['bins_below'],
                          entry_bin=0, bin_step=100,
                          fee_forecast_reference=dict(status='matched_reference', recorded_at=10001.1,
                              forecast_id=f['id'], forecast_line_sha256=hashlib.sha256(self.line).hexdigest(),
                              baseline_sha256=f['baseline_sha256'], prior_sha256=f['prior_sha256'],
                              baseline_age_seconds=10001.1-f['baseline_ts'],
                              forecast_recorded_at=f['recorded_at'], linear_fee_lamports=f['linear_fee_lamports']))
        self.accounting = dict(chains=[dict(root_chain_id='pos',positions=['pos'],first_activity=10001,
            last_activity=10010,wallet_delta_lamports=-20,accounting_status='settled_cash')])

    def run_report(self, entries=None, journal=None):
        return evaluate(entries or [self.entry], self.accounting,
                        self.line+b'\n' if journal is None else journal, self.samples, 10000, 11000)

    def test_valid_prediction_is_not_profit(self):
        result = self.run_report()
        self.assertEqual(result['verified_references'], 1)
        self.assertEqual(result['cash_acceptance']['positive_positions'], 0)
        self.assertFalse(result['future_profit_guaranteed'])

    def test_missing_reference_stays_in_denominator(self):
        self.entry.pop('fee_forecast_reference')
        result = self.run_report()
        self.assertEqual(result['entries'], 1)
        self.assertEqual(result['verified_references'], 0)
        self.assertEqual(result['cash_acceptance']['window_positions'], 1)

    def test_tampering_timing_geometry_and_partial_records(self):
        original = deepcopy(self.entry)
        for key, value in [('entry_bin',1),('amount_y',.2),('deployed_at',9999),('mode','turnover')]:
            self.entry = dict(original, **{key:value})
            self.assertEqual(self.run_report()['verified_references'],0)
        self.entry = original
        self.assertEqual(self.run_report(journal=self.line)['verified_references'],0)
        self.samples[0]['bins'][0]['fee_y']='123'
        self.assertEqual(self.run_report()['verified_references'],0)

    def test_forged_forecast_with_updated_hash_still_fails_rebuild(self):
        self.forecast['linear_fee_lamports'] += 100
        self.line = json.dumps(self.forecast).encode()
        ref = self.entry['fee_forecast_reference']
        ref['forecast_line_sha256']=hashlib.sha256(self.line).hexdigest()
        ref['linear_fee_lamports']=self.forecast['linear_fee_lamports']
        self.assertEqual(self.run_report()['verified_references'],0)

    def test_duplicate_entry_does_not_double_verified_count(self):
        result=self.run_report(entries=[self.entry,deepcopy(self.entry)])
        self.assertEqual(result['verified_references'],0)


if __name__ == '__main__':
    unittest.main()
