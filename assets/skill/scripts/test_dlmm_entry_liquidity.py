"""Avoid opening a pool already known to trigger the configured thin-pool exit."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch
import dlmm_pipeline as pipeline


class EntryLiquidityTests(unittest.TestCase):
    def gate(self, value=6107, *, address='Pool', chain='solana', floor=7000):
        pairs = [dict(chainId='solana', pairAddress='Other', liquidity={'usd': 100000},
                      priceChange={'m5': 1}),
                 dict(chainId=chain, pairAddress=address, liquidity={'usd': value},
                      priceChange={'m5': -2})]
        candidate = dict(pool='Pool', base_mint='token', name='TOKEN-SOL', fee_tvl_ratio=1)
        with patch.dict(pipeline.os.environ, {'DRY_RUN': 'false'}), \
             patch.object(pipeline, 'load_exit_params', return_value={'MIN_EXIT_LIQUIDITY_USD': floor}), \
             patch.object(pipeline.urllib.request, 'urlopen', return_value=contextlib.nullcontext(io.StringIO(json.dumps({'pairs': pairs})))) as request, \
             patch.object(pipeline, 'fetch_live_fee_tvl', return_value=1) as fees, \
             patch.object(pipeline, 'get_price_impact_sol_to_token', return_value=0) as impact:
            with contextlib.redirect_stdout(io.StringIO()):
                rejection = pipeline.predeploy_live_gate_reject(candidate, .1, '30m')
            self.assertEqual(request.call_count, 1)
            if rejection:
                fees.assert_not_called()
                impact.assert_not_called()
        return rejection, candidate['entry_live_gates']

    def test_deep_other_venue_cannot_hide_thin_target(self):
        reason, evidence = self.gate()
        self.assertIn('below exit floor', reason)
        self.assertEqual(evidence['pool_liquidity_usd'], 6107)
        self.assertEqual(evidence['m5_pct'], 1)

    def test_same_configured_floor_and_inclusive_boundary(self):
        self.assertIsNone(self.gate(7000)[0])
        self.assertIsNone(self.gate(6107, floor=5000)[0])
        self.assertIsNotNone(self.gate(0)[0])

    def test_unknown_depth_is_not_zero_or_another_pool(self):
        for value in [None, True, -1, 'NaN', 'Infinity', 'invalid']:
            with self.subTest(value=value):
                reason, evidence = self.gate(value)
                self.assertIsNone(reason)
                self.assertIsNone(evidence['pool_liquidity_usd'])
        for options in [{'address': 'pool'}, {'address': 'OtherTarget'}, {'chain': 'ethereum'}]:
            reason, evidence = self.gate(**options)
            self.assertIsNone(reason)
            self.assertIsNone(evidence['pool_liquidity_usd'])


if __name__ == '__main__':
    unittest.main()
