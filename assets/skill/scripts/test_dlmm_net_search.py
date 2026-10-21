import copy
import unittest
from dlmm_net_search import choose,policies
from dlmm_net_experiment import entry_eligible

class SearchTests(unittest.TestCase):
    def test_fixed_grid_and_training_only_selection(self):
        self.assertEqual(len(list(policies())),29)
        rows=[dict(name='a',training=dict(modeled_exits=3,evaluated=10,extra_cost_stress_lamports=5,net_lower_lamports=8),validation=1000000),
              dict(name='b',training=dict(modeled_exits=3,evaluated=10,extra_cost_stress_lamports=6,net_lower_lamports=7),validation=-1000000)]
        self.assertEqual(choose(rows)['name'],'b')
        rows[0]['validation']=-999999999;rows[1]['validation']=999999999
        self.assertEqual(choose(rows)['name'],'b')
        rows[1]['training']['modeled_exits']=2
        self.assertEqual(choose(rows)['name'],'a')

    def test_entry_features_must_be_observed_before_entry(self):
        e=dict(deployed_at=1000,signal=dict(unique_traders=20,entry_live_gates=dict(
            observed_at=990,fee_timeframe='30m',live_fee_tvl_ratio=.5)))
        rule=dict(fee_tvl_pct_per_hour=1,min_traders=20)
        self.assertTrue(entry_eligible(e,rule))
        for key,value in [('observed_at',1001),('observed_at',800),('live_fee_tvl_ratio',float('nan')),('fee_timeframe','unknown')]:
            bad=copy.deepcopy(e);bad['signal']['entry_live_gates'][key]=value
            self.assertFalse(entry_eligible(bad,rule))
        self.assertFalse(entry_eligible({},rule))
        self.assertTrue(entry_eligible({},None))

    def test_pool_fee_filter_requires_recorded_finite_pre_entry_features(self):
        rule={'min_pool_fee_pct':2}
        e=dict(deployed_at=1000,signal=dict(fee_pct=2,entry_live_gates={'observed_at':990}))
        self.assertTrue(entry_eligible(e,rule))
        for fee in (None,1,float('nan'),float('inf')):
            bad=copy.deepcopy(e);bad['signal']['fee_pct']=fee
            self.assertFalse(entry_eligible(bad,rule))
        e['signal']['entry_live_gates']['observed_at']=1001
        self.assertFalse(entry_eligible(e,rule))

if __name__=='__main__':unittest.main()
