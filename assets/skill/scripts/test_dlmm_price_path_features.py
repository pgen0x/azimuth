import unittest
from dlmm_price_path_features import features


class PricePathFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(pool='p',base_mint='m',status='observed',requested_at=t-.1,
            observed_at=t,collected_at=t+.1,slot=100+i,active_bin=b,bin_step=100,
            commitment='confirmed',basis='native_lb_pair_active_bin_not_fee_or_profit')
            for i,(t,b) in enumerate(zip(range(1000,1601,100),[0,2,1,-3,-1,0,1]))]

    def check(self,rows,cutoff=1601):return features(rows,'p','m',cutoff)

    def test_measured_path_and_future_rows_cannot_change_past(self):
        result=self.check(self.rows)
        self.assertEqual(result['status'],'measured')
        self.assertEqual((result['net_bins'],result['observed_drawdown_bins']),(1,5))
        future=dict(self.rows[-1],slot=999,active_bin=-100,requested_at=1700,observed_at=1701,collected_at=1702)
        self.assertEqual(self.check(self.rows+[future]),result)

    def test_repeated_slot_does_not_create_duration(self):
        rows=[dict(r,slot=100,active_bin=0) for r in self.rows]
        result=self.check(rows)
        self.assertEqual(result['samples'],1);self.assertEqual(result['status'],'unmeasured')

    def test_conflicting_slot_regression_and_gaps_fail(self):
        self.assertEqual(self.check(self.rows+[dict(self.rows[-1],active_bin=9)])['reason'],'conflicting_same_slot')
        reg=self.rows[:-1]+[dict(self.rows[-1],slot=99)]
        self.assertEqual(self.check(reg)['reason'],'slot_regression')
        self.assertEqual(self.check(self.rows[:2]+self.rows[5:])['status'],'unmeasured')
        self.assertEqual(self.check(self.rows,1800)['status'],'unmeasured')

    def test_late_collection_and_wrong_identity_are_not_predecision_data(self):
        self.assertEqual(self.check([dict(r,collected_at=2000) for r in self.rows])['samples'],0)
        self.assertEqual(self.check([dict(r,base_mint='other') for r in self.rows])['samples'],0)


if __name__=='__main__':unittest.main()
