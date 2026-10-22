from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from dlmm_candidate_replay import replay, select_cohorts, run
from dlmm_fee_forecast import candidate_fee_forecast
from dlmm_shadow import validate_candidate_snapshot
from test_dlmm_fee_forecast import sample


class CandidateReplayTests(unittest.TestCase):
    def setUp(self):
        self.base = sample(10000, 0)
        self.end = sample(11800, 0)
        self.args = dict(below=2, capital=1000000, network_cost=100,
                         entry_bps=200, exit_bps=300, max_share_bps=100)

    def test_idle_SOL_still_pays_cost_and_rounding_dust_is_retained(self):
        r = replay(self.base, self.end, offset=1, **self.args)
        # Flooring inferred shares can lose less than one additional lamport.
        self.assertIn(r['modeled_net_lamports'], (-101, -100))
        self.assertIn(r['principal_change_lamports'], (-1, 0))
        self.assertEqual(r['entry_friction_lamports'], 0)
        self.assertEqual(r['exit_friction_lamports'], 0)
        self.assertEqual(r['unspent_lamports'], 1)

    def test_passive_range_does_not_collect_active_bin_fees(self):
        next(b for b in self.end['bins'] if b['id']==0)['fee_y'] = str(2**64)
        baseline = replay(self.base, self.end, offset=0, **self.args)
        passive = replay(self.base, self.end, offset=1, **self.args)
        self.assertGreater(baseline['fee_lamports'], 0)
        self.assertEqual(passive['fee_lamports'], 0)

    def test_liquidation_friction_is_on_token_inventory_only(self):
        for b in self.end['bins']:
            b['x'], b['y'] = '1000000000000', '0'
        zero = replay(self.base, self.end, offset=1, **dict(self.args, exit_bps=0))
        stressed = replay(self.base, self.end, offset=1, **self.args)
        self.assertLessEqual(abs(zero['modeled_net_lamports']-stressed['modeled_net_lamports']-
                                 stressed['exit_friction_lamports']), 1)
        self.assertGreater(stressed['exit_friction_lamports'], 0)

    def test_missing_reset_or_large_share_never_becomes_profit(self):
        for change, reason in [('missing', 'missing_candidate_bins'),
                               ('reset', 'fee_counter_reset'),
                               ('large', 'liquidity_share_exceeds_model_limit')]:
            base, end = deepcopy(self.base), deepcopy(self.end)
            if change=='missing': end['bins'].pop()
            if change=='reset':
                for b in base['bins']: b['fee_y']='1'
            if change=='large':
                for b in end['bins']: b['supply']='1'
            with self.assertRaisesRegex(ValueError, reason):
                replay(base, end, offset=1, **self.args)
        for b in self.base['bins']: b['x']='1'
        with self.assertRaisesRegex(ValueError, 'passive_entry_not_SOL_only'):
            replay(self.base, self.end, offset=1, **self.args)

    def test_cohort_overlap_is_reserved_even_when_outcome_missing(self):
        def f(t, pool='pool'):
            return dict(status='frozen_prediction', recorded_at=t, baseline_ts=t,
                        id=str(t), baseline_sha256=str(t), pool=pool, horizon_target_ts=t+1800)
        first, overlap, next_one = f(100), f(1000), f(2500)
        self.assertEqual(select_cohorts([overlap,next_one,first], 3000), [first,next_one])
        # Another pool does not consume the first pool's interval; this is not
        # a claim that a finite wallet can fund both simultaneously.
        other=f(1000,'other')
        self.assertEqual(select_cohorts([first,other,overlap,next_one], 2000), [first,other])

    def test_end_to_end_uses_first_terminal_and_keeps_missing_outcomes(self):
        old = sample(9700, 0)
        forecast = candidate_fee_forecast(self.base, [old], 10000.2, validate_candidate_snapshot)
        for terminals in ([self.end, sample(11900, 2**64)], []):
            with self.subTest(terminal_available=bool(terminals)), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);memory=root/'profile/memories';memory.mkdir(parents=True)
                samples=[old,self.base,*terminals]
                (memory/'dlmm_candidate_bin_samples.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples))
                (memory/'dlmm_candidate_fee_forecasts.jsonl').write_text(json.dumps(forecast)+'\n')
                before={p.name:p.read_bytes() for p in memory.iterdir()}
                with contextlib.redirect_stdout(io.StringIO()):
                    run(root/'profile',root/'out',12500)
                result=json.loads((root/'out/result.json').read_text())
                self.assertEqual(result['selected_cohorts'],1)
                row=result['results'][0]
                if terminals:
                    self.assertEqual(row['terminal_ts'],11800)
                    self.assertEqual(row['status'],'paired')
                    self.assertLess(row['strategies']['passive_one_bin_below']['modeled_net_lamports'],0)
                else:
                    self.assertEqual(row['reason'],'terminal_missing')
                    self.assertEqual(row['status'],'unmeasured')
                self.assertFalse(result['promotion_allowed'])
                self.assertEqual(before,{p.name:p.read_bytes() for p in memory.iterdir()})
                with self.assertRaisesRegex(ValueError,'New output directory'):
                    run(root/'profile',root/'out',12500)


if __name__ == '__main__':
    unittest.main()
