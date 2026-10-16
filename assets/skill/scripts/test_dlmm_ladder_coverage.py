"""A capped ladder must still meet the promised downside coverage."""
import unittest
from dlmm_pipeline import sol_bidask_bins, SOL_BIDASK_MIN_COVERAGE, BINS_BELOW_HARD_MAX


class LadderCoverageTests(unittest.TestCase):
    def test_production_band_keeps_existing_geometry(self):
        for step, expected in [(80, 53), (100, 44), (125, 35)]:
            self.assertEqual(sol_bidask_bins(step), expected)

    def test_every_accepted_step_meets_floor_within_budget(self):
        for step in range(1, 401):
            if 1-(1+step/10000)**-BINS_BELOW_HARD_MAX < SOL_BIDASK_MIN_COVERAGE:
                with self.assertRaises(ValueError):
                    sol_bidask_bins(step)
            else:
                bins = sol_bidask_bins(step)
                self.assertLessEqual(bins, BINS_BELOW_HARD_MAX)
                self.assertGreaterEqual(1-(1+step/10000)**-bins, SOL_BIDASK_MIN_COVERAGE)

    def test_low_step_is_rejected_instead_of_silent_undercoverage(self):
        self.assertLess(1-1.0001**-100, .01)
        with self.assertRaisesRegex(ValueError, '2232 bins'):
            sol_bidask_bins(1)

    def test_invalid_step_does_not_become_one(self):
        for step in [0, -1, True, None, '100', float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                sol_bidask_bins(step)


if __name__ == '__main__':
    unittest.main()
