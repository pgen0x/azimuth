"""Prospective timing, identity, first-outcome selection and collector isolation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dlmm_shadow as shadow
from dlmm_fee_forecast import FORECAST_FILE, candidate_fee_forecast, sample_hash, score_forecasts

POOL = 'HZs6bUjefdrPqJZP7TU4uUWvXE125zWdyeHp5eY8TTDX'
MINT = '3q2U15sSP4gy6PEYgmcVtEyurEHBhXgLre21NeHNpump'
SOL = 'So11111111111111111111111111111111111111112'
DELTA = 2**48


def sample(ts=10000, counter=DELTA, **changes):
    row = dict(status='observed', pool=POOL, base_mint=MINT, mode='pulse', ts=ts,
               collected_at=ts+.1, active_bin=0, anchor_bin=0, lower_bin=-69, upper_bin=16,
               price=.000001, decimals_x=6, decimals_y=9, sol_is_x=False,
               token_x_mint=MINT, token_y_mint=SOL, bin_step=100,
               bins=[dict(id=i, x='0', y='1000000000', supply=str(2**96),
                          fee_x='0', fee_y=str(counter), price=.000001*1.01**i) for i in range(-69, 17)])
    row.update(changes)
    return row


class CandidateForecastTests(unittest.TestCase):
    def setUp(self):
        self.old = sample(9700, 0)
        self.base = sample()

    def freeze(self, base=None, history=None, frozen_at=10000.2, **kwargs):
        return candidate_fee_forecast(base or self.base, history if history is not None else [self.old],
                                      frozen_at, shadow.validate_candidate_snapshot, **kwargs)

    def score(self, forecast, future=(), cutoff=12401):
        return score_forecasts([forecast], [self.old, self.base, *future], cutoff,
                               shadow.validate_candidate_snapshot)

    def test_lower_bin_fees_are_not_attributed_to_current_active_bin(self):
        self.base['bins'][-17]['fee_y'] = '0'  # Active bin 0; lower bins earned.
        forecast = self.freeze()
        self.assertEqual(forecast['version'], 2)
        attribution = forecast['fee_attribution']
        self.assertEqual(attribution['active_bin'], 0)
        self.assertEqual(attribution['active_bin_fraction'], 0)
        self.assertGreater(forecast['linear_fee_lamports'], 0)
        for token in ('x', 'y'):
            key = 'historical_fee_' + token + '_raw'
            self.assertEqual(sum(int(b[key]) for b in attribution['bins']), int(forecast[key]))
        future = sample(11800, DELTA*2)
        self.assertEqual(self.score(forecast, [future])['scored'], 1)
        forecast['fee_attribution']['bins'][0]['historical_fee_y_raw'] = '123'
        result = self.score(forecast, [future])
        self.assertEqual(result['scored'], 0)
        self.assertEqual(result['results'][0]['reason'], 'forecast_or_input_binding_mismatch')

    def test_legacy_forecasts_still_score_and_new_zero_fee_is_not_a_fraction(self):
        legacy = self.freeze(model_version=1)
        self.assertNotIn('fee_attribution', legacy)
        self.assertEqual(self.score(legacy, [sample(11800, DELTA*2)])['scored'], 1)
        self.assertNotEqual(legacy['id'], self.freeze()['id'])
        flat = self.freeze(history=[sample(9700, DELTA)])
        self.assertIsNone(flat['fee_attribution']['active_bin_fraction'])
        self.assertEqual(flat['linear_fee_lamports'], 0)

    def test_freezes_inputs_geometry_and_never_claims_cash_profit(self):
        before = deepcopy([self.old, self.base])
        self.base['unrelatedSecret'] = 'https://secret.invalid/key'
        prediction = self.freeze()
        self.assertEqual(prediction['status'], 'frozen_prediction')
        self.assertEqual(prediction['bins_below'], 44)
        self.assertEqual(prediction['prior_sha256'], sample_hash(self.old))
        self.assertEqual(prediction['baseline_sha256'], sample_hash(self.base))
        self.assertGreater(prediction['linear_fee_lamports'], 0)
        self.assertLess(prediction['max_added_over_existing_bin_supply'], 1)
        self.assertFalse(prediction['funded_position'])
        self.assertFalse(prediction['net_cash_profit_proved'])
        self.assertNotIn('secret', json.dumps(prediction))
        del self.base['unrelatedSecret']
        self.assertEqual([self.old, self.base], before)
        with patch('dlmm_pipeline.sol_bidask_bins', return_value=35):
            with patch.dict('dlmm_fee_forecast.HORIZONS', pulse=300):
                result = self.score(prediction, [sample(11800, DELTA)])
        self.assertEqual(result['scored'], 1)  # Later production geometry cannot rewrite the forecast.

    def test_earliest_complete_preexisting_history_and_explicit_unknowns(self):
        earlier = sample(9200, 0)
        self.assertEqual(self.freeze(history=[self.old, earlier])['prior_ts'], 9200)
        self.assertEqual(self.freeze(history=[])['reason'], 'missing_complete_prior_history')
        self.assertEqual(self.freeze(history_limited=True)['reason'], 'prior_history_budget_exceeded')
        self.assertEqual(self.freeze(frozen_at=11800)['reason'], 'not_frozen_before_horizon')
        for bad in [sample(9700, 0, collected_at=10001), sample(7000, 0),
                    sample(9700, DELTA*2), sample(9700, 0, token_x_mint=SOL)]:
            self.assertEqual(self.freeze(history=[bad])['status'], 'unmeasured')
        for field in ['supply', 'y']:
            base = deepcopy(self.base)
            base['bins'][30][field] = '0'
            self.assertEqual(self.freeze(base=base)['status'], 'unmeasured')
        base = deepcopy(self.base)
        for b in base['bins']:
            b['y'] = '1'
        self.assertEqual(self.freeze(base=base)['reason'], 'added_liquidity_exceeds_existing_bin_model')

    def test_first_terminal_sample_not_later_favorable_fees(self):
        prediction = self.freeze()
        first, later = sample(11800, DELTA), sample(11900, DELTA*100)
        result = self.score(prediction, [later, first])['results'][0]
        self.assertEqual(result['status'], 'scored')
        self.assertEqual(result['observed_until_ts'], 11800)
        self.assertEqual(result['modeled_fee_at_baseline_price_lamports'], 0)
        self.assertEqual(result['modeled_over_linear'], 0)
        self.assertFalse(result['net_cash_profit_proved'])
        self.assertEqual(self.score(prediction, cutoff=11799)['results'][0]['status'], 'pending')
        self.assertEqual(self.score(prediction)['results'][0]['status'], 'unmeasured')
        malformed = deepcopy(first)
        malformed['bins'][30]['fee_y'] = '0'
        self.assertEqual(self.score(prediction, [malformed, later])['results'][0]['status'], 'unmeasured')

    def test_hash_and_timing_changes_cannot_masquerade_as_valid_forecasts(self):
        prediction = self.freeze()
        altered = deepcopy(prediction)
        altered['linear_fee_lamports'] += 1
        self.assertEqual(self.score(altered, [sample(11800)])['results'][0]['reason'], 'forecast_or_input_binding_mismatch')
        recorded_late = dict(prediction, recorded_at=11800)
        self.assertEqual(self.score(recorded_late, [sample(11800)])['results'][0]['status'], 'unmeasured')
        self.assertEqual(self.score(prediction, cutoff=10000.1)['forecasts'], 0)
        for change in [dict(collected_at=11799), dict(decimals_x=5), dict(token_x_mint=SOL)]:
            self.assertEqual(self.score(prediction, [sample(11800, **change)])['results'][0]['status'], 'unmeasured')
        with self.assertRaises(ValueError):
            score_forecasts([], [], float('nan'), shadow.validate_candidate_snapshot)

    def test_raw_token_fee_growth_is_separate_from_price_revaluation(self):
        for b in self.base['bins']:
            b.update(fee_x=str(DELTA), fee_y='0')
        prediction = self.freeze()
        terminal = sample(11800, 0, active_bin=1, price=.000001*1.01)
        for b in terminal['bins']:
            b['fee_x'] = str(DELTA*7)
        row = self.score(prediction, [terminal])['results'][0]
        self.assertEqual(row['status'], 'scored')
        self.assertGreater(row['modeled_fee_at_baseline_price_lamports'], 0)
        self.assertAlmostEqual(row['modeled_fee_at_terminal_price_lamports'] /
                               row['modeled_fee_at_baseline_price_lamports'], 1.01)

    def test_existing_collector_freezes_without_extra_command_and_preserves_bins_on_failure(self):
        candidates = {POOL: dict(pool=POOL, base_mint=MINT, mode='pulse', source_id='watch', source_ts=10000)}
        for fail in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                profile = Path(directory)
                file = profile/'memories/dlmm_candidate_bin_samples.jsonl'
                shadow.append(file, self.old)
                with patch.object(shadow.time, 'time', return_value=10000.2), \
                     patch.object(shadow.time, 'monotonic', return_value=0), \
                     patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(self.base).encode()) as read:
                    if fail:
                        with patch('dlmm_fee_forecast.candidate_fee_forecast', side_effect=ValueError('secret URL')):
                            result = shadow.collect_candidate_bins(profile, candidates, 40)
                    else:
                        result = shadow.collect_candidate_bins(profile, candidates, 40)
                self.assertEqual(read.call_count, 1)
                self.assertEqual(result['candidate_bin_snapshots_observed'], 1)
                self.assertEqual(len(shadow.rows(file)[-1]['bins']), 86)
                if not fail:
                    self.assertEqual(result['candidate_fee_forecasts_frozen'], 1)
                    forecast = shadow.rows(profile/'memories'/FORECAST_FILE)[0]
                    self.assertEqual(forecast['frozen_at'], 10000.2)
                    self.assertEqual(forecast['status'], 'frozen_prediction')
                else:
                    self.assertEqual(result['candidate_fee_forecasts_unmeasured'], 1)


if __name__ == '__main__':
    unittest.main()
