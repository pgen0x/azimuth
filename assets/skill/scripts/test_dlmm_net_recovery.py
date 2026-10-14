"""Net recovery uses actual wallet cash, including costs and returned reserves."""
from copy import deepcopy
import unittest
from dlmm_evaluate import swap_execution


class NetRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.event = dict(kind='swap', signature='sig', position='pos', wallet='wallet', ts=101,
            swap_quote=dict(input_mint='TOKEN', output_mint='So11111111111111111111111111111111111111112',
                in_amount='10', out_amount='1000', minimum_out_amount='990', observed_at=100,
                authorized_slippage_bps=100, token_rent_close_included=True,
                net_recovery=dict(version=1, recorded_at=101.5, conservative_wallet_delta_lamports=790,
                    required_minimum_lamports=1, reserved_quote_slippage_lamports=10,
                    token_rent_close_included=True)))
        self.fact = dict(signature='sig', event_position='pos', wallet='wallet', failed=False,
            block_time=102, observed_at=110, basis='finalized_transaction_balances',
            wallet_delta_lamports=795, fee_lamports=5, token_deltas_raw={'TOKEN':'-10'},
            token_rent_evidence=dict(version=1, funded=[], refunded=[], refunds_unmeasured=True))

    def result(self, event=None, fact=None, end=200):
        return swap_execution([event or self.event], {'sig':fact or self.fact},100,end)

    def test_cash_comparison_independent_of_gross_output_rent_decomposition(self):
        result = self.result()
        item = result['attempts'][0]
        self.assertEqual(item['status'],'unmeasured')  # Gross output needs rent proof.
        self.assertEqual(item['net_recovery']['status'],'measured')
        self.assertEqual(item['net_recovery']['actual_minus_simulated_lamports'],5)
        self.assertEqual(result['net_recovery_summary']['measured'],1)
        bad = self.result(fact=dict(self.fact,wallet_delta_lamports=-20))
        self.assertEqual(bad['net_recovery_summary']['below_required_minimum'],1)

    def test_missing_old_evidence_is_not_reconstructed(self):
        event = deepcopy(self.event)
        del event['swap_quote']['net_recovery']
        self.assertEqual(self.result(event=event)['net_recovery_summary']['recorded'],0)

    def test_identity_timing_amount_and_failed_transaction_do_not_pass(self):
        for change in (dict(wallet='other'), dict(signature='other'), dict(event_position='other'),
                       dict(failed=True), dict(landed=False), dict(observed_at=201),
                       dict(block_time=100), dict(token_deltas_raw={'TOKEN':'-9'})):
            result = self.result(fact=dict(self.fact,**change))
            self.assertEqual(result['net_recovery_summary']['measured'],0,change)
        for change in (dict(recorded_at=float('nan')),dict(recorded_at=102),
                       dict(reserved_quote_slippage_lamports=9),dict(version=True),
                       dict(conservative_wallet_delta_lamports=True),dict(token_rent_close_included=False)):
            event = deepcopy(self.event)
            event['swap_quote']['net_recovery'].update(change)
            self.assertEqual(self.result(event=event)['net_recovery_summary']['measured'],0,change)


if __name__ == '__main__':
    unittest.main()
