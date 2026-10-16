"""Closure evidence must bind a successful wallet transaction to the position."""
import unittest
from copy import deepcopy
from dlmm_accounting import proved_recorded_close


class RecoveredCloseTests(unittest.TestCase):
    def setUp(self):
        self.events = [dict(signature=s, position='position', wallet='wallet', kind=s)
                       for s in ('deploy', 'close')]
        self.facts = {s: dict(wallet='wallet', failed=False, slot=slot,
                             event_position='position', position_account_closed=s=='close')
                      for s, slot in [('deploy', 10), ('close', 20)]}

    def test_finalized_bound_close_and_same_slot_deploy(self):
        self.assertEqual(proved_recorded_close('position', self.events, self.facts), 'close')
        self.facts['deploy']['slot'] = 20
        self.assertEqual(proved_recorded_close('position', self.events, self.facts), 'close')

    def test_old_close_cannot_prove_later_deployment_closed(self):
        self.facts['deploy']['slot'] = 21
        self.assertIsNone(proved_recorded_close('position', self.events, self.facts))

    def test_invalid_close_and_wrong_identity_are_not_proof(self):
        for fields in [{'failed': True}, {'landed': False}, {'slot': True},
                       {'slot': 0}, {'slot': None}, {'event_position': 'other'},
                       {'wallet': 'other'}, {'position_account_closed': False}]:
            with self.subTest(fields=fields):
                facts = deepcopy(self.facts)
                facts['close'].update(fields)
                self.assertIsNone(proved_recorded_close('position', self.events, facts))
        self.assertIsNone(proved_recorded_close('position', self.events, {'close': self.facts['close']}))
        self.events[1]['wallet'] = 'other'
        self.assertIsNone(proved_recorded_close('position', self.events, self.facts))


if __name__ == '__main__':
    unittest.main()
