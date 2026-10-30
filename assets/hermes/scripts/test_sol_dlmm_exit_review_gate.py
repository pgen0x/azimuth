"""Exit-review wake gate on monitor report rows with unavailable fee yield (synthetic, offline)."""
import unittest

import sol_dlmm_exit_review_gate as gate

BASE = {'in_range': True, 'mode': 'turnover', 'age_minutes': 600, 'pnl_pct': 0.5, 'peak_pnl': 0.5}


class WantsReviewTests(unittest.TestCase):
    def test_unknown_yield_never_wakes_the_low_yield_band(self):
        for fee in (None, True, 'n/a'):
            with self.subTest(fee=fee):
                self.assertIsNone(gate.wants_review(dict(BASE, fee_per_tvl_24h=fee)))
        self.assertIsNone(gate.wants_review(BASE))  # absent field: unknown, not zero

    def test_measured_low_yield_still_wakes_and_other_bands_are_unchanged(self):
        self.assertEqual(gate.wants_review(dict(BASE, fee_per_tvl_24h=0)), 'low-yield')
        self.assertEqual(gate.wants_review(dict(BASE, fee_per_tvl_24h=1.0)), 'low-yield')
        self.assertIsNone(gate.wants_review(dict(BASE, fee_per_tvl_24h=5.0)))
        self.assertEqual(gate.wants_review(dict(BASE, fee_per_tvl_24h=None, pnl_pct=-6)), 'drawdown')
        self.assertEqual(gate.wants_review(dict(BASE, fee_per_tvl_24h=None, triggered_rules=['x'])), 'rule-firing')


if __name__ == '__main__':
    unittest.main()
