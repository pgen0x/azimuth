import unittest
from dlmm_net_execution_stress import stress, SOL


class ExecutionStressTests(unittest.TestCase):
    def setUp(self):
        self.cohort = dict(modeled_exits=1, net_lower_lamports=1000000,
                           positions=[dict(position='p', decision=dict(observed_at=1, modeled_net_lamports=200000))])
        self.quote = dict(status='measured', inventory_source='onchain_sol_inventory',
                          quote=dict(outputMint=SOL, swapMode='ExactIn', otherAmountThreshold='10000001'))

    def test_only_token_leg_is_shocked_and_rounds_conservatively(self):
        result = stress(self.cohort, {('p',1):[self.quote]}, 100)
        self.assertEqual(result['net_lower_lamports'], 899999)
        self.assertEqual(result['positions'][0]['stressed_modeled_net_lamports'], 99999)

    def test_missing_wrong_timestamp_and_conflicting_evidence_are_unknown(self):
        conflict = dict(self.quote, quote=dict(self.quote['quote'], otherAmountThreshold='2'))
        for quotes in ({}, {('p',2):[self.quote]}, {('p',1):[self.quote,conflict]}):
            self.assertIsNone(stress(self.cohort, quotes,100)['net_lower_lamports'])

    def test_indexed_inventory_is_not_native_evidence(self):
        quote = dict(self.quote, inventory_source='indexed')
        self.assertFalse(stress(self.cohort, {('p',1):[quote]},100)['complete'])

    def test_zero_shock_preserves_baseline(self):
        self.assertEqual(stress(self.cohort,{('p',1):[self.quote]},0)['net_lower_lamports'],1000000)


if __name__ == '__main__':
    unittest.main()
