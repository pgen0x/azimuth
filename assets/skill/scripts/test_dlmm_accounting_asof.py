"""Adversarial synthetic controls for canonical cash evidence; no RPC/profile data."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from dlmm_accounting import report, root_decision, pooled_settlements


class AccountingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.profile = Path(self.temp.name)
        self.mem = self.profile / 'memories'
        (self.mem / 'dlmm_entries').mkdir(parents=True)
        self.entry = dict(position='position', root_chain_id='root', deployed_at=100)
        self.events = [dict(signature=sig, wallet='wallet', position='position', root_chain_id='root', kind=kind, ts=stamp)
                       for sig, kind, stamp in [('deploy', 'deploy', 110), ('close', 'close', 180)]]
        self.facts = [dict(signature=sig, wallet='wallet', slot=slot, block_time=stamp, observed_at=stamp + 1,
                           wallet_delta_lamports=delta, fee_lamports=5000, failed=False,
                           token_deltas_raw={}, position_account_closed=sig == 'close')
                      for sig, slot, stamp, delta in [('deploy', 10, 110, -100000000), ('close', 20, 180, 101000000)]]
        self.coverage = dict(ts=200, coverage_since=90, end_slot=30, wallet_history_complete=True, unclassified_transactions=[])
        (self.mem / 'dlmm_entries/p.json').write_text(json.dumps(self.entry))
        self.write('dlmm_closes.jsonl', [dict(position='position', root_chain_id='root', ts=180)])
        self.write('dlmm_transactions.jsonl', self.events)
        self.write('dlmm_wallet_transactions.jsonl', self.facts)
        self.write('dlmm_wallet_coverage.jsonl', [self.coverage])
    def write(self, name, rows):
        (self.mem / name).write_text(''.join(json.dumps(row) + '\n' for row in rows))
    def chain(self, at=200):
        return next(row for row in report(self.profile, at)['chains'] if row['root_chain_id'] == 'root')
    def decision(self):
        result = root_decision(self.chain(), .01)
        return result['allow'], result['reason']
    def test_future_facts_and_coverage_do_not_change_decision(self):
        self.write('dlmm_nav.jsonl', [dict(ts=190, nav_sol=1, end_slot=25)])
        before = self.chain()
        decision = self.decision()
        self.write('dlmm_nav.jsonl', [dict(ts=190, nav_sol=1, end_slot=25), dict(ts=201, nav_sol=999, end_slot=31)])
        future = dict(self.facts[1], observed_at=201, wallet_delta_lamports=999999999)
        self.write('dlmm_wallet_transactions.jsonl', self.facts + [future])
        self.write('dlmm_wallet_coverage.jsonl', [self.coverage, dict(self.coverage, ts=201, wallet_history_complete=False)])
        self.assertEqual(self.chain(), before)
        self.assertEqual(self.decision(), decision)
    def test_missing_and_foreign_fact_remain_unknown(self):
        for facts in [self.facts[:1], [self.facts[0], dict(self.facts[1], wallet='foreign')]]:
            self.write('dlmm_wallet_transactions.jsonl', facts)
            self.assertIsNone(self.chain()['settled_cash_pnl_sol'])
            self.assertFalse(self.decision()[0])
    def test_duplicate_failed_fee_counted_once(self):
        failed = dict(self.facts[1], signature='failed', block_time=185, observed_at=186, slot=21,
                      failed=True, wallet_delta_lamports=-7000, fee_lamports=7000, position_account_closed=False)
        event = dict(self.events[1], signature='failed', kind='swap', ts=185)
        self.write('dlmm_transactions.jsonl', self.events + [event, copy.deepcopy(event)])
        self.write('dlmm_wallet_transactions.jsonl', self.facts + [failed, copy.deepcopy(failed)])
        self.write('dlmm_transaction_facts.jsonl', [failed])
        chain = self.chain()
        self.assertEqual(chain['wallet_delta_lamports'], 993000)
        self.assertEqual(chain['network_fee_lamports'], 17000)
        self.assertEqual(chain['failed_transactions'], 1)
    def test_mixed_wallet_events_do_not_form_one_known_cash_root(self):
        self.events[1]['wallet'] = 'foreign'
        self.facts[1]['wallet'] = 'foreign'
        self.write('dlmm_transactions.jsonl', self.events)
        self.write('dlmm_wallet_transactions.jsonl', self.facts)
        self.assertIsNone(self.chain()['settled_cash_pnl_sol'])
        self.assertFalse(self.decision()[0])
    def test_nonfinite_cash_never_passes_root_gate(self):
        self.facts[1]['wallet_delta_lamports'] = float('nan')
        self.write('dlmm_wallet_transactions.jsonl', self.facts)
        self.assertIsNone(self.chain()['settled_cash_pnl_sol'])
        self.assertFalse(self.decision()[0])
    def test_pooled_cash_requires_one_common_wallet(self):
        base = dict(first_activity=100, last_activity=180, network_fee_lamports=5000,
                    reasons=['token_inventory_requires_valuation'], wallets=['wallet'])
        a = dict(base, root_chain_id='a', token_deltas_raw={'TOKEN': '100'}, wallet_delta_lamports=10000000)
        b = dict(base, root_chain_id='b', token_deltas_raw={'TOKEN': '-100'}, wallet_delta_lamports=10000000)
        self.assertEqual(len(pooled_settlements([a, b])), 1)
        for wallets in [['foreign'], [], ['wallet', 'foreign']]:
            self.assertEqual(pooled_settlements([a, dict(b, wallets=wallets)]), [])
        self.assertEqual(a['reasons'], ['token_inventory_requires_valuation'])

    def test_unproved_expiry_cannot_erase_a_fee(self):
        expired = dict(signature='expired', wallet='wallet', landed=False,
                       classification='expired_unlanded', observed_at=190,
                       basis='finalized_wallet_history_and_expiry',
                       last_valid_block_height=10, finalized_block_height=11,
                       wallet_delta_lamports=0, fee_lamports=0)
        event = dict(self.events[1], signature='expired', ts=185, kind='swap')
        self.write('dlmm_transactions.jsonl', self.events + [event])
        self.write('dlmm_wallet_transactions.jsonl', self.facts + [expired])
        self.assertEqual(self.chain()['expired_unlanded_signatures'], ['expired'])
        self.assertTrue(self.decision()[0])
        for change in [dict(fee_lamports=5000), dict(wallet_delta_lamports=-5000),
                       dict(basis=None), dict(finalized_block_height=10),
                       dict(last_valid_block_height=True), dict(observed_at=201)]:
            with self.subTest(change=change):
                self.write('dlmm_wallet_transactions.jsonl', self.facts + [dict(expired, **change)])
                self.assertIsNone(self.chain()['settled_cash_pnl_sol'])
                self.assertFalse(self.decision()[0])

    def test_invalid_native_and_token_cash_stays_unknown(self):
        for change in [dict(wallet_delta_lamports=True), dict(fee_lamports=float('nan')),
                       dict(fee_lamports=-1), dict(nonrefundable_account_cost_lamports=float('inf')),
                       dict(token_deltas_raw={'TOKEN': '1_000'}), dict(token_deltas_raw={'TOKEN': '--1'})]:
            with self.subTest(change=change):
                self.write('dlmm_wallet_transactions.jsonl', [self.facts[0], dict(self.facts[1], **change)])
                self.assertIsNone(self.chain()['settled_cash_pnl_sol'])
                self.assertFalse(self.decision()[0])

    def test_direct_root_gate_rejects_nonfinite_evidence(self):
        good = self.chain()
        self.assertTrue(root_decision(good, .01)['allow'])
        for key, values in [('settled_cash_pnl_sol', [float('nan'), float('inf'), -float('inf'), None]),
                            ('network_fee_lamports', [float('nan'), float('inf'), -1, True]),
                            ('nonrefundable_account_cost_lamports', [float('nan'), -1])]:
            for value in values:
                with self.subTest(key=key, value=value):
                    self.assertFalse(root_decision(dict(good, **{key: value}), .01)['allow'])

    def test_future_lp_row_does_not_erase_known_past_diagnostic(self):
        old = dict(position='position', realized_sol=.001, fetched_at=190)
        self.write('dlmm_realized.jsonl', [old])
        before = self.chain()['lp_pnl_sol']
        self.write('dlmm_realized.jsonl', [old, dict(old, fetched_at=201, realized_sol=-1)])
        self.assertEqual(self.chain()['lp_pnl_sol'], before)


if __name__ == '__main__':
    unittest.main()
