"""Paired forward width study: gross IL/fees, never an executed-profit claim."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dlmm_shadow as shadow
from dlmm_evaluate import evaluate


class WidthStudyTests(unittest.TestCase):
    def setUp(self):
        self.bins = [dict(id=i, x='0', y='1000000000', supply=str(2**128),
                         fee_x='0', fee_y='0', price=1.01**i) for i in range(-69, 1)]
        wide = dict(ts=100, active_bin=0, price=1, decimals_x=9, decimals_y=9,
                    sol_is_x=False, bins=self.bins)
        self.entry = dict(position='position', pool='pool', mode='turnover', deployed_at=100,
                          entry_bin=0, bins_below=44, bins_above=0, size_sol=0.1,
                          amount_x=0, amount_y=0.1, strategy='sol_bidask',
                          bin_snapshot=dict(wide, bins=self.bins[25:]),
                          width_study=dict(target_bins=70, lower_bin=-69, upper_bin=0, snapshot=wide))
        terminal_bins = [dict(b, x=str(int(1e9/b['price'])), y='0') if b['id'] > -10 else b
                         for b in self.bins]
        self.sample = dict(wide, ts=3700, price=1.01**-10, active_bin=-10, bins=terminal_bins)

    def test_same_capital_wider_range_dilutes_the_observed_loss(self):
        result = shadow.bin_width_replay(self.entry, [self.sample])
        self.assertEqual(result['status'], 'modeled')
        self.assertTrue(result['horizon_complete'])
        self.assertLess(result['baseline']['gross_pnl_sol'], 0)
        # Same observed upper bins: their capital share shrinks from 1/1035 to
        # 1/2485; the extra lower bins retain SOL. No invented fees outside them.
        self.assertAlmostEqual(result['wider']['gross_pnl_sol']/result['baseline']['gross_pnl_sol'],
                               1035/2485)
        self.assertEqual(result['wider']['fee_capture_sol'], 0)
        self.assertIsNone(result['wider']['net_after_observed_cost_sol'])

    def test_missing_or_empty_wider_bins_stay_unknown(self):
        old = dict(self.entry, width_study=None)
        self.assertEqual(shadow.bin_width_replay(old, [self.sample])['status'], 'unmeasured')
        broken = copy.deepcopy(self.entry)
        broken['width_study']['snapshot']['bins'][0]['supply'] = '0'
        result = shadow.bin_width_replay(broken, [self.sample])
        self.assertEqual(result['status'], 'unmeasured')
        self.assertEqual(result['wider']['reason'], 'empty_bin_counterfactual_requires_market_impact_model')
        sample = dict(self.sample, bins=self.sample['bins'][25:])
        self.assertEqual(shadow.bin_width_replay(self.entry, [sample])['status'], 'unmeasured')

    def test_snapshot_identity_and_time_must_match(self):
        for field, value in [('ts', 101), ('sol_is_x', True), ('price', 2)]:
            entry = copy.deepcopy(self.entry)
            entry['width_study']['snapshot'][field] = value
            self.assertEqual(shadow.bin_width_replay(entry, [self.sample])['reason'],
                             'inconsistent_width_snapshot')
        self.assertEqual(shadow.bin_width_replay(self.entry, [])['status'], 'unmeasured')
        result = shadow.bin_width_replay(self.entry, [dict(self.sample, ts=200)])
        self.assertFalse(result['horizon_complete'])

    def test_existing_collector_and_evaluator_use_the_wider_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory)
            memory = profile/'memories'
            (memory/'dlmm_entries').mkdir(parents=True)
            (memory/'dlmm_entries'/'position.json').write_text(json.dumps(self.entry))
            with patch.object(shadow.time, 'time', return_value=3700), \
                 patch.object(shadow, 'collect_liquidation', return_value=0), \
                 patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(self.sample)) as read:
                shadow.collect(profile, profile/'rejects.jsonl')
            self.assertEqual(read.call_args.args[0][-2:], ['-69', '0'])
            self.assertEqual(read.call_count, 1)
            result = evaluate(profile, 50, 3800, profile/'rejects.jsonl')
            self.assertEqual(result['bin_width_replay'][0]['status'], 'modeled')
            self.assertTrue(result['bin_width_replay'][0]['horizon_complete'])
            self.assertEqual(result['bin_replay'][0]['status'], 'modeled')

    def test_sol_x_mirrors_the_range_without_changing_the_SOL_benchmark(self):
        bins = [dict(b, id=-b['id'], x=b['y'], y=b['x'], price=1/b['price'])
                for b in reversed(self.bins)]
        wide = dict(self.entry['width_study']['snapshot'], sol_is_x=True, bins=bins)
        entry = dict(self.entry, amount_x=0.1, amount_y=0, bins_below=0, bins_above=44,
                     bin_snapshot=dict(wide, bins=bins[:45]),
                     width_study=dict(target_bins=70, lower_bin=0, upper_bin=69, snapshot=wide))
        terminal = [dict(b, x='0', y=str(int(1e9*b['price']))) if b['id'] < 10 else b for b in bins]
        result = shadow.bin_width_replay(entry, [dict(wide, ts=3700, price=1.01**10,
                                                      active_bin=10, bins=terminal)])
        self.assertEqual(result['status'], 'modeled')
        self.assertLess(result['baseline']['gross_pnl_sol'], 0)
        self.assertAlmostEqual(result['wider']['gross_pnl_sol']/result['baseline']['gross_pnl_sol'],
                               1035/2485)

    def test_summary_keeps_modes_and_incomplete_horizons_separate(self):
        complete = dict(shadow.bin_width_replay(self.entry, [self.sample]), mode='turnover')
        partial = dict(complete, horizon_complete=False)
        summary = shadow.width_study_summary([complete, partial, dict(mode='pulse', status='unmeasured')])
        self.assertEqual(summary['turnover']['total'], 2)
        self.assertEqual(summary['turnover']['complete_pairs'], 1)
        self.assertEqual(summary['turnover']['capital_sol'], 0.1)
        self.assertEqual(summary['turnover']['gross_delta_sol'], complete['deltas']['gross_pnl_sol'])
        self.assertIsNone(summary['pulse']['gross_delta_sol'])

    def test_holding_period_excludes_postclose_loss_and_terminal_grace(self):
        before = dict(self.sample, ts=200, price=1, active_bin=0, bins=self.bins)
        later = dict(self.sample, ts=251)
        original = copy.deepcopy([self.entry, before, later])
        result = shadow.bin_width_holding_replay(self.entry, [later, before], 250)
        self.assertEqual(result['status'], 'modeled')
        self.assertEqual(result['observed_until_ts'], 200)
        self.assertEqual(result['seconds_before_close'], 50)
        self.assertEqual(result['deltas']['gross_pnl_sol'], 0)
        self.assertGreater(shadow.bin_width_replay(self.entry, [later])['deltas']['gross_pnl_sol'], 0)
        self.assertEqual(shadow.bin_width_replay(self.entry, [later], end_ts=250)['status'], 'unmeasured')
        self.assertEqual([self.entry, before, later], original)
        self.assertEqual(shadow.HORIZONS['turnover'], 3600)
        at_close = shadow.bin_width_holding_replay(self.entry, [dict(before, ts=250), later], 250)
        self.assertEqual(at_close['seconds_before_close'], 0)

    def test_holding_period_requires_known_close_and_fresh_preclose_sample(self):
        for closed_at in (None, True, float('nan'), float('inf'), 100):
            self.assertEqual(shadow.bin_width_holding_replay(self.entry, [self.sample], closed_at)['status'], 'unmeasured')
        self.assertEqual(shadow.bin_width_holding_replay(self.entry, [self.sample], 200)['reason'],
                         'no_followup_before_actual_close')
        stale = shadow.bin_width_holding_replay(self.entry, [dict(self.sample, ts=200)], 801)
        self.assertEqual(stale['reason'], 'last_preclose_observation_too_old')
        self.assertEqual(shadow.bin_width_holding_replay(self.entry, [dict(self.sample, ts=200)], 800)['status'], 'modeled')

    def test_evaluator_requires_close_proof_observed_by_its_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory); memory = profile/'memories'
            (memory/'dlmm_entries').mkdir(parents=True)
            (memory/'dlmm_entries/position.json').write_text(json.dumps(self.entry))
            (memory/'dlmm_closes.jsonl').write_text(json.dumps(dict(position='position', ts=250))+'\n')
            (memory/'dlmm_bin_samples.jsonl').write_text(json.dumps(dict(self.sample, position='position', ts=200))+'\n'+json.dumps(dict(self.sample, position='position'))+'\n')
            (memory/'dlmm_transactions.jsonl').write_text(json.dumps(dict(position='position',kind='close',signature='close',wallet='wallet',ts=250))+'\n')
            fact=dict(signature='close',wallet='wallet',observed_at=270,block_time=250,position_account_closed=True,
                      failed=False,wallet_delta_lamports=0,fee_lamports=0,token_deltas_raw={})
            (memory/'dlmm_wallet_transactions.jsonl').write_text(json.dumps(fact)+'\n')
            self.assertEqual(evaluate(profile,50,260,profile/'rejects.jsonl')['bin_width_holding_replay'][0]['status'], 'unmeasured')
            result=evaluate(profile,50,3800,profile/'rejects.jsonl')['bin_width_holding_replay'][0]
            self.assertEqual(result['status'], 'modeled'); self.assertEqual(result['observed_until_ts'], 200)
            self.assertEqual(result['actual_close_ts'], 250)
            for change in [dict(failed=True),dict(landed=False),dict(wallet='other'),dict(block_time=251),
                           dict(block_time=0),dict(block_time=-1),dict(block_time=None),
                           dict(position_account_closed=False)]:
                (memory/'dlmm_wallet_transactions.jsonl').write_text(json.dumps(dict(fact,**change))+'\n')
                self.assertEqual(evaluate(profile,50,3800,profile/'rejects.jsonl')['bin_width_holding_replay'][0]['status'], 'unmeasured')

    def test_delayed_close_journal_cannot_admit_post_chain_close_samples(self):
        with tempfile.TemporaryDirectory() as directory:
            profile=Path(directory);memory=profile/'memories'
            (memory/'dlmm_entries').mkdir(parents=True)
            (memory/'dlmm_entries/position.json').write_text(json.dumps(self.entry))
            (memory/'dlmm_closes.jsonl').write_text(json.dumps(dict(position='position',ts=350))+'\n')
            (memory/'dlmm_transactions.jsonl').write_text(json.dumps(dict(position='position',kind='close',signature='close',wallet='wallet',ts=350))+'\n')
            fact=dict(signature='close',wallet='wallet',observed_at=360,block_time=250,position_account_closed=True,
                      failed=False,wallet_delta_lamports=0,fee_lamports=0,token_deltas_raw={})
            (memory/'dlmm_wallet_transactions.jsonl').write_text(json.dumps(fact)+'\n')
            before=dict(self.sample,position='position',ts=200,price=1,active_bin=0,bins=self.bins)
            after=dict(self.sample,position='position',ts=300)
            (memory/'dlmm_bin_samples.jsonl').write_text('\n'.join(map(json.dumps,[before,after]))+'\n')
            result=evaluate(profile,50,3800,profile/'rejects.jsonl')['bin_width_holding_replay'][0]
            self.assertEqual(result['status'],'modeled')
            self.assertEqual(result['actual_close_ts'],250)
            self.assertEqual(result['observed_until_ts'],200)
            self.assertEqual(result['seconds_before_close'],50)
            self.assertEqual(result['deltas']['gross_pnl_sol'],0)


if __name__ == '__main__':
    unittest.main()
