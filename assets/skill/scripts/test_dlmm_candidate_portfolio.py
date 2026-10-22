import unittest

from dlmm_candidate_portfolio import simulate


class PortfolioTests(unittest.TestCase):
    def ticket(self,ident,start=0,end=100,net=5,composition=0):
        return dict(id=ident,entry_at=start,exit_at=end,entry_eligible=True,
                    modeled_net_lamports=net,entry_cost_lamports=composition)

    def run_model(self,rows,initial=347,**kw):
        return simulate(rows,initial,ticket=100,rent=45,retained_rent=15,reserve=20,
                        network_cost=1,cleanup_delay=30,**kw)

    def test_two_tickets_fit_but_third_waits_for_cash(self):
        r=self.run_model([self.ticket('a'),self.ticket('b'),self.ticket('c')])
        self.assertEqual(r['selected_positions'],2)
        self.assertEqual(r['capacity_skips'],1)
        self.assertEqual(r['final_equity_lamports'],357)

    def test_network_composition_and_stress_charged_once(self):
        r=self.run_model([self.ticket('a',net=-8,composition=7)],extra_cost=3)
        self.assertEqual(r['final_net_lamports'],-11)
        self.assertEqual(r['final_equity_lamports'],336)
        self.assertEqual(r['decisions'][0]['escrow_lamports'],156)

    def test_no_lookahead_borrowing_and_delayed_rent(self):
        rows=[self.ticket('a',end=100,net=0),self.ticket('b',start=99),
              self.ticket('c',start=110,end=200),self.ticket('d',start=131,end=200)]
        r=self.run_model(rows,initial=166)
        self.assertEqual(r['capacity_skips'],2)
        self.assertEqual([p['id'] for p in r['positions']],['a','d'])
        self.assertEqual(r['final_equity_lamports'],171)

    def test_missing_outcome_keeps_capital_locked_and_equity_unknown(self):
        r=self.run_model([self.ticket('a',end=None,net=None),self.ticket('b',end=None,net=None),
                          self.ticket('c',start=10000)])
        self.assertEqual(r['unknown_positions'],2)
        self.assertIsNone(r['final_equity_lamports'])
        self.assertIsNone(r['final_net_lamports'])
        self.assertEqual(r['available_cash_lamports'],55)
        self.assertEqual(r['unresolved_escrow_lamports'],292)

    def test_preentry_rejection_does_not_consume_cash(self):
        r=self.run_model([dict(self.ticket('a'),entry_eligible=False),self.ticket('b')])
        self.assertEqual(r['eligibility_skips'],1)
        self.assertEqual(r['selected_positions'],1)
        self.assertEqual(r['final_equity_lamports'],352)


if __name__=='__main__':unittest.main()
