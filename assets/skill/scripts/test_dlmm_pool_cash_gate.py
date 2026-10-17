import json
import unittest
from dlmm_pool_cash_gate import negative_pool_cash

class PoolCashGateTests(unittest.TestCase):
    def setUp(self):
        self.now=10000000
        self.journal='\n'.join(json.dumps(dict(ts=self.now-i, pnl_pct=1)) for i in (10,20))
        self.cash=dict(prior_closes=2,journal_closes=2,journal_last_close_ts=self.now-10,
                      last_close_ts=self.now-10,observed_at=self.now-1,prior_roots=2,prior_cash_roots=2,
                      prior_pnl_basis='matched_refund_cash',prior_net_pnl_sol=-.00005,
                      prior_cash_lower_sol=-.00005,prior_cash_upper_sol=-.00005)
    def check(self, **change):
        return negative_pool_cash({'pool':dict(self.cash,**change)},'pool',self.journal,self.now)
    def test_cash_loss_refuses_despite_positive_marks(self):
        self.assertIsNotNone(self.check())
    def test_stale_incomplete_or_new_close_cannot_refuse(self):
        for change in [dict(observed_at=self.now-901),dict(observed_at=self.now+1),dict(prior_cash_roots=1),
                       dict(journal_closes=1),dict(journal_last_close_ts=self.now-20),dict(prior_closes=1),
                       dict(prior_pnl_basis='pre_swap_mark_only'),dict(prior_cash_upper_sol=float('nan'))]:
            with self.subTest(change=change):self.assertIsNone(self.check(**change))
    def test_positive_and_ambiguous_bounds_do_not_refuse(self):
        for hi in (0,.1):
            self.assertIsNone(self.check(prior_pnl_basis='matched_refund_cash_bounds',prior_net_pnl_sol=None,
                                        prior_cash_lower_sol=-.1,prior_cash_upper_sol=hi))
    def test_negative_bounds_and_upper_only(self):
        for basis,lo in [('matched_refund_cash_bounds',-.1),('nonpositive_cash_upper_bound',None)]:
            self.assertIsNotNone(self.check(prior_pnl_basis=basis,prior_net_pnl_sol=None,prior_cash_lower_sol=lo))
    def test_bad_or_mismatched_journal(self):
        for raw in ('bad','null','{}','',self.journal+'\n'+json.dumps(dict(ts=self.now-1))):
            self.assertIsNone(negative_pool_cash({'pool':self.cash},'pool',raw,self.now))
    def test_recovered_closes_bind_separate_journal(self):
        self.cash.update(prior_closes=3,prior_roots=3,prior_cash_roots=3)
        self.assertIsNotNone(self.check())

if __name__=='__main__':unittest.main()
