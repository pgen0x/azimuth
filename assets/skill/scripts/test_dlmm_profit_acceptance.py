"""Regression cases for the user's every-position net SOL requirement."""
from copy import deepcopy
import unittest

from dlmm_profit_acceptance import position_profit_acceptance


def entry(position, root=None, deployed=120):
    return dict(position=position, root_chain_id=root or position,
                mode='turnover', deployed_at=deployed)


def chain(root, cash, positions=None, first=120, last=180, status='settled_cash'):
    return dict(root_chain_id=root, positions=positions or [root],
                first_activity=first, last_activity=last,
                wallet_delta_lamports=cash, accounting_status=status)


def group(chains, gross, fee=5, last=190):
    return dict(root_chain_ids=list(gross), refund_signatures=['refund'],
                last_activity=last,
                refund_components=[dict(signature='refund', gross_by_root=gross, fee_lamports=fee)],
                cash_with_matched_refunds_sol=(sum(c['wallet_delta_lamports'] for c in chains)
                                              + sum(gross.values())-fee)/1e9)


def assess(chains, entries, groups=None):
    return position_profit_acceptance(dict(chains=chains, rent_refund_groups=groups or []),
                                      entries, 100, 200)


class PositionProfitAcceptanceTests(unittest.TestCase):
    def test_positive_aggregate_cannot_hide_one_loss(self):
        roots = [chain('winner', -100), chain('loser', -100)]
        refund = group(roots, dict(winner=1100, loser=90))
        self.assertGreater(refund['cash_with_matched_refunds_sol'], 0)
        result = assess(roots, [entry('winner'), entry('loser')], [refund])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual((result['positive_positions'], result['nonpositive_positions']), (1, 1))
        self.assertEqual(result['positive_fraction_of_all_entries'], .5)

    def test_one_lamport_after_all_costs_passes_observed_cohort_only(self):
        roots = [chain('p', -100)]
        result = assess(roots, [entry('p')], [group(roots, dict(p=106))])
        self.assertEqual(result['status'], 'observed_all_positive')
        self.assertEqual(result['positions'][0]['cash_lower_lamports'], 1)
        self.assertFalse(result['future_profit_guaranteed'])

    def test_exact_zero_is_failure(self):
        roots = [chain('p', -100)]
        result = assess(roots, [entry('p')], [group(roots, dict(p=105))])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['positive_positions'], 0)

    def test_shared_fee_uncertainty_cannot_pass(self):
        roots = [chain('p', -100), chain('other', -100, first=20)]
        result = assess(roots, [entry('p')], [group(roots, dict(p=103, other=100))])
        self.assertEqual(result['status'], 'not_verified')
        row = result['positions'][0]
        self.assertEqual((row['cash_lower_lamports'], row['cash_upper_lamports']), (-2, 3))
        self.assertEqual(result['unresolved_positions'], 1)

    def test_upper_bound_zero_cannot_be_strictly_positive(self):
        roots = [chain('p', -100), chain('other', -100, first=20)]
        result = assess(roots, [entry('p')], [group(roots, dict(p=100, other=100))])
        self.assertEqual(result['status'], 'failed')

    def test_positive_root_does_not_prove_each_recenter_leg(self):
        roots = [chain('root', -100, ['first', 'second'])]
        result = assess(roots, [entry('first', 'root'), entry('second', 'root')],
                        [group(roots, dict(root=1000))])
        self.assertEqual(result['status'], 'not_verified')
        self.assertEqual(result['unmeasured_positions'], 2)
        self.assertTrue(all(p['cash_lower_lamports'] is None for p in result['positions']))

    def test_open_position_remains_in_denominator(self):
        roots = [chain('win', -100), chain('open', -100, status='incomplete')]
        result = assess(roots, [entry('win'), entry('open')],
                        [group(roots[:1], dict(win=110))])
        self.assertEqual(result['status'], 'not_verified')
        self.assertEqual((result['window_positions'], result['positive_positions'],
                          result['unmeasured_positions']), (2, 1, 1))
        self.assertEqual(result['positive_fraction_of_all_entries'], .5)

    def test_empty_or_outside_window_cannot_pass(self):
        result = assess([], [entry('old', deployed=99), entry('future', deployed=201)])
        self.assertEqual(result['status'], 'not_verified')
        self.assertIsNone(result['positive_fraction_of_all_entries'])

    def test_carry_in_root_cannot_be_relabelled_as_complete_position(self):
        roots = [chain('p', -100, first=99)]
        result = assess(roots, [entry('p')], [group(roots, dict(p=110))])
        self.assertEqual(result['unmeasured_positions'], 1)

    def test_late_missing_duplicate_or_invalid_refunds_remain_unmeasured(self):
        roots = [chain('p', -100)]
        good = group(roots, dict(p=110))
        invalid = deepcopy(good)
        invalid['cash_with_matched_refunds_sol'] = 999
        for refunds in ([], [dict(good, last_activity=201)], [good, good], [invalid]):
            with self.subTest(refunds=refunds):
                result = assess(roots, [entry('p')], refunds)
                self.assertEqual(result['status'], 'not_verified')
                self.assertEqual(result['unmeasured_positions'], 1)

    def test_duplicate_entries_or_conflicting_root_identity_cannot_pass(self):
        roots = [chain('p', -100)]
        for entries in ([entry('p'), entry('p')], [entry('p', 'wrong')]):
            result = assess(roots, entries, [group(roots, dict(p=110))])
            self.assertEqual(result['status'], 'not_verified')
            self.assertEqual(result['window_positions'], 1)

    def test_conflicting_refund_owner_elsewhere_invalidates_whole_group(self):
        roots = [chain('p', -100), chain('other', -100, first=20)]
        shared = group(roots, dict(p=110, other=110))
        overlapping = group(roots[1:], dict(other=110))
        result = assess(roots, [entry('p')], [shared, overlapping])
        self.assertEqual(result['unmeasured_positions'], 1)

    def test_single_position_owned_inline_rent_uses_cash_once(self):
        roots = [dict(chain('p', 1), recorded_signatures=['fund', 'sale'])]
        inline = dict(root_chain_ids=['p'], refund_signatures=[], refund_components=[],
                      last_activity=190, cash_with_matched_refunds_sol=1e-9,
                      basis='root_cash_with_owned_inline_rent; no_additional_refund_credit; not_NAV',
                      inline_rent_pairs=[dict(account='ata', mint='token', lamports=100,
                                              funding_slot=10, close_slot=20,
                                              funding_signature='fund', close_signature='sale')])
        result = assess(roots, [entry('p')], [inline])
        self.assertEqual(result['status'], 'observed_all_positive')
        self.assertEqual(result['positions'][0]['cash_upper_lamports'], 1)


if __name__ == '__main__':
    unittest.main()
