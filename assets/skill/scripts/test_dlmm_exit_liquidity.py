"""Malformed market data must not manufacture a zero-liquidity exit."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch
import dlmm_monitor as monitor


class ExitLiquidityTests(unittest.TestCase):
    def read(self, **fields):
        pair = dict(pairAddress='Pool', chainId='solana', priceChange={'h1': 1, 'm5': 2})
        pair.update(fields)
        with patch.object(monitor.urllib.request, 'urlopen', side_effect=lambda *a, **k: contextlib.nullcontext(io.StringIO(json.dumps({'pairs': [pair]})))):
            return monitor.get_pool_liquidity_usd('Pool', 'token')

    def test_missing_invalid_and_negative_liquidity_remain_unknown(self):
        self.assertEqual(self.read(), (None, 1, 2))
        for value in [None, True, False, -1, 'NaN', 'Infinity', '-Infinity', 'invalid', {}, []]:
            with self.subTest(value=value):
                self.assertEqual(self.read(liquidity={'usd': value}), (None, 1, 2))

    def test_real_zero_and_thin_values_still_reach_exit_check(self):
        for value in [0, 6107, 7000, '8000']:
            self.assertEqual(self.read(liquidity={'usd': value})[0], float(value))

    def test_bad_momentum_does_not_discard_known_liquidity(self):
        for value in [True, 'NaN', 'Infinity', 'bad', {}]:
            self.assertEqual(self.read(liquidity={'usd': 6107}, priceChange={'h1': value, 'm5': 2}), (6107, None, 2))

    def test_address_case_and_wrong_chain_never_match(self):
        for fields in [{'pairAddress': 'pool'}, {'pairAddress': 'Other'}, {'chainId': 'ethereum'}]:
            self.assertEqual(self.read(liquidity={'usd': 0}, **fields), (None, None, None))


if __name__ == '__main__':
    unittest.main()
