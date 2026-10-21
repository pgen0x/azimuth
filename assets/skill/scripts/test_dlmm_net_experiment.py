import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import dlmm_net_experiment as experiment

class NetExperimentTests(unittest.TestCase):
    def setUp(self):
        self.entry=dict(position='p',deployed_at=100,size_sol=.1)
        self.quote=dict(position='p',observed_at=300,position_updated_at=299,status='measured',
                        inventory_source='onchain_sol_inventory',minimum_quoted_assets_change_before_network_fees_sol=.0002)

    def test_net_trigger_subtracts_cost_before_comparison(self):
        self.assertIsNotNone(experiment.trigger(self.quote,self.entry,{'tp':.001},25000,100))
        self.assertIsNone(experiment.trigger(self.quote,self.entry,{'tp':.001},150000,100))
        self.assertIsNone(experiment.trigger(self.quote,self.entry,{},25000,100))

    def test_missing_stale_indexed_wrong_identity_and_early_quotes_fail(self):
        for change in [dict(status='unmeasured'),dict(position_updated_at=280),
                       dict(inventory_source='indexed_position'),dict(position='other'),
                       dict(observed_at=200),dict(minimum_quoted_assets_change_before_network_fees_sol=float('nan'))]:
            self.assertIsNone(experiment.trigger(dict(self.quote,**change),self.entry,{'tp':.001},25000,100))
        self.assertIsNone(experiment.trigger(self.quote,self.entry,{'tp':.001},25000,301))

    def test_shared_refund_counted_once_and_subset_bounds_preserved(self):
        ledger=dict(chains=[dict(root_chain_id=p,accounting_status='settled_cash',wallet_delta_lamports=-110) for p in ('a','b')],
            rent_refund_groups=[dict(root_chain_ids=['a','b'],refund_signatures=['s'],
                refund_components=[dict(signature='s',gross_by_root={'a':100,'b':100},fee_lamports=10)],
                cash_with_matched_refunds_sol=-30/1e9)])
        self.assertEqual(experiment.aggregate(ledger,{'a','b'}),(-30,-30))
        self.assertEqual(experiment.aggregate(ledger,{'a'}),(-20,-10))

    def test_cost_knowledge_requires_refund_observed_not_just_block_time(self):
        c=dict(recorded_signatures=['trade']);g=[dict(refund_signatures=['rent'])]
        self.assertEqual(experiment.known_at(c,g,{'trade':{'observed_at':100},'rent':{'observed_at':200}}),200)
        self.assertEqual(experiment.known_at(c,g,{'trade':{'observed_at':100}}),float('inf'))

    def test_dry_decision_frozen_and_missing_quotes_never_sell(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);memory=root/'memories';(memory/'dlmm_entries').mkdir(parents=True)
            out=root/'experiment';out.mkdir()
            config=dict(frozen_at=100,strategies=experiment.STRATEGIES,cost_budget_lamports=25000)
            experiment.write(out/'config.json',config)
            entry=dict(self.entry,deployed_at=101,pool='pool')
            (memory/'dlmm_entries/p.json').write_text(json.dumps(entry))
            (memory/'dlmm_transactions.jsonl').write_text(json.dumps(dict(kind='deploy',position='p',wallet='w'))+'\n')
            (memory/'dlmm_closes.jsonl').write_text('')
            with patch.object(experiment,'read_native_risk_mark',return_value={}), \
                 patch.object(experiment,'liquidation_observation',return_value={k:v for k,v in self.quote.items() if k!='position'}), \
                 patch.object(experiment,'dry_summary'):
                experiment.dry_tick(root,out)
                state=json.loads((out/'dry-state.json').read_text());decision=state['positions']['p']['decisions']['net_tp_0_1pct']
                with patch.object(experiment,'liquidation_observation',side_effect=ValueError('bad quote')):
                    experiment.dry_tick(root,out)
                self.assertEqual(json.loads((out/'dry-state.json').read_text())['positions']['p']['decisions']['net_tp_0_1pct'],decision)
                self.assertEqual(json.loads((out/'dry-quotes.jsonl').read_text().splitlines()[-1])['status'],'unmeasured')
                config['cost_budget_lamports']=30000;experiment.write(out/'config.json',config)
                with self.assertRaisesRegex(ValueError,'Frozen'):experiment.dry_tick(root,out)

if __name__=='__main__':unittest.main()
