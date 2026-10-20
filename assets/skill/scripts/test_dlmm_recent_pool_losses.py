import copy
import json
import unittest

from dlmm_accounting import pool_cash_history, recent_position_cash_losses
from dlmm_pool_cash_gate import negative_pool_cash


class RecentPoolLossTests(unittest.TestCase):
    def setUp(self):
        self.now = 10000
        self.journal = [dict(position=p, root_chain_id=p, pool='P', ts=t)
                        for p, t in [('b', 9990), ('a', 9980), ('unknown', 9970)]]
        self.ledger = dict(chains=[dict(root_chain_id=p, positions=[p],
                            accounting_status='settled_cash', wallet_delta_lamports=-110)
                            for p in ('a', 'b')] + [dict(root_chain_id='unknown', positions=['unknown'],
                            accounting_status='incomplete')],
                           rent_refund_groups=[dict(root_chain_ids=['a', 'b'], last_activity=9995,
                            refund_signatures=['cleanup'], refund_components=[dict(signature='cleanup',
                            gross_by_root=dict(a=100, b=100), fee_lamports=10)],
                            cash_with_matched_refunds_sol=-30/1e9)])

    def gate(self, journal=None, cache=None):
        return negative_pool_cash(cache or self.cache, 'P',
            '\n'.join(json.dumps(r) for r in (self.journal if journal is None else journal)), self.now)

    def test_incomplete_old_root_cannot_hide_two_proved_losses(self):
        self.cache = pool_cash_history(self.journal, self.ledger, self.now)
        self.assertIsNone(self.cache['P']['prior_cash_upper_sol'])
        proofs = self.cache['P']['recent_position_cash_losses']
        self.assertEqual([p['cash_upper_lamports'] for p in proofs], [-10, -10])
        self.assertEqual(self.gate()['scope'], 'each_of_latest_two')
        self.assertEqual(self.gate()['cash_upper_sol'], -10/1e9)  # not a sum of shared bounds

    def test_latest_unknown_positive_zero_or_multileg_never_proves_streak(self):
        for change in ('unknown', 'positive', 'zero', 'multileg', 'refund_missing', 'conflicting_group', 'future_refund'):
            ledger = copy.deepcopy(self.ledger)
            chain = ledger['chains'][1]
            group = ledger['rent_refund_groups'][0]
            if change == 'unknown': chain['accounting_status'] = 'incomplete'
            if change in ('positive', 'zero'):
                chain['wallet_delta_lamports'] = -99 if change == 'positive' else -100
                group['cash_with_matched_refunds_sol'] = (-19 if change == 'positive' else -20)/1e9
            if change == 'multileg': chain['positions'].append('extra')
            if change == 'refund_missing': ledger['rent_refund_groups'] = []
            if change == 'conflicting_group': ledger['rent_refund_groups'].append(copy.deepcopy(group))
            if change == 'future_refund': group['last_activity'] = self.now+1
            with self.subTest(change=change):
                self.assertEqual(recent_position_cash_losses(self.journal, ledger, self.now), [])

    def test_stale_new_close_and_replaced_identity_invalidate_cache(self):
        self.cache = pool_cash_history(self.journal, self.ledger, self.now)
        new = [dict(position='new', root_chain_id='new', pool='P', ts=9999)] + self.journal
        self.assertIsNone(self.gate(journal=new))
        replaced = copy.deepcopy(self.journal); replaced[0]['position'] = 'different'
        self.assertIsNone(self.gate(journal=replaced))
        for field, value in [('observed_at', self.now-901), ('observed_at', self.now+1), ('journal_closes', 2)]:
            cache=copy.deepcopy(self.cache);cache['P'][field]=value
            self.assertIsNone(self.gate(cache=cache))
        for value in (0, 1, True, float('nan')):
            cache=copy.deepcopy(self.cache);cache['P']['recent_position_cash_losses'][0]['cash_upper_lamports']=value
            self.assertIsNone(self.gate(cache=cache))

    def test_newer_recovered_close_cannot_be_skipped(self):
        ledger=copy.deepcopy(self.ledger)
        ledger['recovered_closes']=[dict(position='recovered',pool='P',ts=9999)]
        result=pool_cash_history(self.journal,ledger,self.now)
        self.assertEqual(result['P']['recent_position_cash_losses'],[])

    def test_tied_latest_times_or_same_root_are_ambiguous(self):
        journal=copy.deepcopy(self.journal);journal[1]['ts']=journal[0]['ts']
        self.assertEqual(recent_position_cash_losses(journal,self.ledger,self.now),[])
        journal=copy.deepcopy(self.journal);journal[1]['root_chain_id']='b'
        self.assertEqual(recent_position_cash_losses(journal,self.ledger,self.now),[])

if __name__ == '__main__':
    unittest.main()
