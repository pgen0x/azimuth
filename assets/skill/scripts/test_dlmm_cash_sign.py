"""Adversarial offline checks for upper-only negative labels and their consumers."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from dlmm_cash_sign import FACT_BASIS, nonpositive_cash_upper_bounds, cash_sign_upper_bound
from dlmm_profit_acceptance import position_profit_acceptance
import dlmm_weights as weights


def fixture(cash=-15):
    chain = dict(root_chain_id='p', positions=['p'], accounting_status='settled_cash',
                 recorded_signatures=['fund', 'close'], wallet_delta_lamports=cash,
                 network_fee_lamports=10, first_activity=100, last_activity=180,
                 pending_signatures=[], expired_unlanded_signatures=[], token_deltas_raw={})
    def fact(signature, delta, slot):
        return dict(signature=signature, wallet='wallet', event_position='p', failed=False,
                    classification='recorded_bot', schema_version=12, slot=slot, block_time=slot,
                    observed_at=190, wallet_delta_lamports=delta, fee_lamports=5,
                    basis='finalized_transaction_balances', token_deltas_raw={'mint':'0'},
                    cash_sign_evidence=dict(version=1, position='p', basis=FACT_BASIS,
                                            no_retained_wallet_funding_outside_position=True))
    facts = dict(fund=fact('fund', -155, 110), close=fact('close', 155+cash, 170))
    facts['close']['position_account_closed'] = True
    return [chain], facts


def proofs(chains, facts, groups=None, cutoff=200):
    return nonpositive_cash_upper_bounds(chains, facts, groups or [], cutoff)


class CashSignTests(unittest.TestCase):
    def test_retained_rent_caps_loss_without_booking_a_refund(self):
        from dlmm_cash_sign import RENT_FACT_BASIS
        chains, facts = fixture(-25)
        facts['fund']['cash_sign_evidence'] = None
        facts['fund']['retained_rent_evidence'] = dict(version=1, position='p', basis=RENT_FACT_BASIS,
            max_future_rent_credit_lamports=20, funded_accounts=[dict(account='ata',mint='mint',lamports=20)])
        proof, = proofs(chains, facts)
        self.assertEqual(cash_sign_upper_bound(proof, chains[0], 200), -5)
        self.assertEqual(chains[0]['wallet_delta_lamports'], -25)
        self.assertIsNone(proof['cash_lower_lamports'])
        ledger=dict(chains=chains,rent_refund_groups=[],nonpositive_cash_upper_bounds=[proof])
        result=position_profit_acceptance(ledger,[dict(position='p',deployed_at=100)],100,200)
        self.assertEqual(result['positions'][0]['cash_upper_lamports'], -5)
        self.assertEqual(result['nonpositive_positions'], 1)
        for mutate in [lambda p:p.update(max_future_rent_credit_lamports=19),
                       lambda p:p.update(max_future_rent_credit_lamports=True),
                       lambda p:p['funded_accounts'].append(dict(p['funded_accounts'][0])),
                       lambda p:p['funded_accounts'][0].update(account='wallet'),
                       lambda p:p['funded_accounts'][0].update(lamports=-20)]:
            invalid=deepcopy(facts);mutate(invalid['fund']['retained_rent_evidence'])
            self.assertEqual(proofs(chains,invalid),[])
        chains[0]['wallet_delta_lamports']=-15
        facts['close']['wallet_delta_lamports']+=10
        self.assertEqual(proofs(chains,facts),[])  # Possible refund could make it positive.

    def test_pool_history_preserves_upper_only_and_requires_complete_coverage(self):
        from dlmm_accounting import pool_cash_history
        chains, facts = fixture()
        proof, = proofs(chains, facts)
        ledger = dict(chains=chains, rent_refund_groups=[], nonpositive_cash_upper_bounds=[proof])
        closes = [dict(position='p',pool='pool',ts=195,pnl_sol=1)]
        view = pool_cash_history(closes, ledger, 200)['pool']
        self.assertEqual(view['prior_pnl_basis'], 'nonpositive_cash_upper_bound')
        self.assertEqual(view['prior_cash_upper_sol'], -15e-9)
        self.assertIsNone(view['prior_cash_lower_sol'])
        self.assertIsNone(view['prior_net_pnl_sol'])
        for altered in (dict(ledger, nonpositive_cash_upper_bounds=[proof,proof]),
                        dict(ledger, nonpositive_cash_upper_bounds=[])):
            self.assertIsNone(pool_cash_history(closes, altered, 200)['pool']['prior_cash_upper_sol'])
        closes.append(dict(position='unknown',pool='pool',ts=196,pnl_sol=0))
        self.assertIsNone(pool_cash_history(closes,ledger,200)['pool']['prior_cash_upper_sol'])

    def test_only_an_upper_bound_no_exact_cash_or_rent_group(self):
        chains, facts = fixture()
        proof, = proofs(chains, facts)
        self.assertIsNone(proof['cash_lower_lamports'])
        self.assertEqual(cash_sign_upper_bound(proof, chains[0], 200), -15)
        self.assertEqual(proofs(chains, facts, [dict(root_chain_ids=['p'])]), [])

    def test_zero_is_nonpositive_but_positive_cash_is_never_a_label(self):
        for cash in (-1, 0, 1):
            chains, facts = fixture(cash)
            self.assertEqual(len(proofs(chains, facts)), int(cash <= 0))

    def test_missing_old_or_ambiguous_evidence_is_not_inferred(self):
        changes = [lambda c,f:f['fund'].pop('cash_sign_evidence'),
                   lambda c,f:f['fund'].update(cash_sign_evidence=None),
                   lambda c,f:f['fund']['cash_sign_evidence'].update(position='other'),
                   lambda c,f:f['fund']['cash_sign_evidence'].update(no_retained_wallet_funding_outside_position=False),
                   lambda c,f:f['close'].pop('position_account_closed'),
                   lambda c,f:f['fund'].update(schema_version=11),
                   lambda c,f:f['fund'].update(wallet='other'),
                   lambda c,f:f['fund'].update(event_position='other'),
                   lambda c,f:f['fund'].update(wallet_delta_lamports=-154),
                   lambda c,f:f['fund'].update(fee_lamports=6),
                   lambda c,f:f['fund'].update(observed_at=201),
                   lambda c,f:f['fund'].update(block_time=201),
                   lambda c,f:f['fund'].update(observed_at=float('nan')),
                   lambda c,f:f['fund'].update(landed=False),
                   lambda c,f:f['fund'].update(fee_lamports=True),
                   lambda c,f:f['fund']['token_deltas_raw'].update(mint='1'),
                   lambda c,f:f['fund'].update(slot=170),
                   lambda c,f:f['fund'].update(slot=180),
                   lambda c,f:c[0].update(accounting_status='incomplete'),
                   lambda c,f:c[0].update(last_activity=201),
                   lambda c,f:c[0]['positions'].append('recenter'),
                   lambda c,f:c[0]['pending_signatures'].append('pending'),
                   lambda c,f:c[0]['expired_unlanded_signatures'].append('expired'),
                   lambda c,f:c[0]['token_deltas_raw'].update(mint='1'),
                   lambda c,f:c[0]['recorded_signatures'].append('fund'),
                   lambda c,f:c.append(dict(c[0],root_chain_id='other'))]
        for change in changes:
            chains, facts = fixture();change(chains,facts)
            self.assertEqual(proofs(chains,facts), [], change)

    def test_landed_failure_fee_is_included_never_skipped(self):
        chains,facts=fixture()
        chains[0]['recorded_signatures'].append('failed')
        chains[0]['wallet_delta_lamports']-=5;chains[0]['network_fee_lamports']+=5
        facts['failed']={**facts['fund'], 'signature':'failed','failed':True,
                         'wallet_delta_lamports':-5,'cash_sign_evidence':None}
        self.assertEqual(proofs(chains,facts)[0]['cash_upper_lamports'],-20)
        facts['failed']['wallet_delta_lamports']=0
        self.assertEqual(proofs(chains,facts),[])

    def test_acceptance_fails_the_position_without_fabricating_final_pnl(self):
        chains,facts=fixture();proof=proofs(chains,facts)
        ledger=dict(chains=chains,rent_refund_groups=[],nonpositive_cash_upper_bounds=proof)
        entries=[dict(position='p',deployed_at=100)]
        result=position_profit_acceptance(ledger,entries,100,200)
        self.assertEqual((result['nonpositive_positions'],result['unmeasured_positions']),(1,0))
        self.assertIsNone(result['positions'][0]['cash_lower_lamports'])
        self.assertEqual(result['status'],'failed')
        for mutate in [lambda p:p.update(cash_upper_lamports=1),
                       lambda p:p.update(cash_lower_lamports=-15),
                       lambda p:p.update(recorded_signatures=['fund']),
                       lambda p:p.update(observed_at=201)]:
            invalid=deepcopy(proof);mutate(invalid[0])
            result=position_profit_acceptance(dict(ledger,nonpositive_cash_upper_bounds=invalid),entries,100,200)
            self.assertEqual(result['unmeasured_positions'],1)

    def test_learner_uses_sign_only_and_deduplicates_proof(self):
        chains,facts=fixture();proof=proofs(chains,facts)
        ledger=dict(chains=chains,rent_refund_groups=[],nonpositive_cash_upper_bounds=proof)
        with TemporaryDirectory() as directory:
            path=Path(directory)/'closes.jsonl'
            close=dict(position='p',ts=195,signal={'score':70},pnl_sol=99,pnl_basis='realized')
            path.write_text(json.dumps(close)+'\n'+json.dumps(dict(close,signal={'score':20}))+'\n')
            with patch.object(weights,'CLOSES_PATH',str(path)), patch.object(weights,'report',return_value=ledger), patch.object(weights.time,'time',return_value=200):
                rows=weights.load_recent_closes()
                self.assertEqual(len(rows),1)
                self.assertEqual(rows[0]['signal']['score'],20)
                self.assertIsNone(rows[0]['cash_pnl_lower_sol'])
                self.assertEqual(weights.outcome_sol(rows[0]),-15e-9)
                ledger['nonpositive_cash_upper_bounds']*=2
                self.assertEqual(weights.load_recent_closes(),[])
        for upper in (1, True, float('inf'), float('nan'), None):
            self.assertIsNone(weights.outcome_sol(dict(outcome_basis=weights.UPPER_ONLY_BASIS,
                                                       cash_pnl_lower_sol=None,cash_pnl_upper_sol=upper)))


if __name__=='__main__':
    unittest.main()
