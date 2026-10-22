import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dlmm_candidate_paper as paper
from dlmm_fee_forecast import candidate_fee_forecast
from dlmm_shadow import validate_candidate_snapshot, SOL_MINT
from test_dlmm_fee_forecast import sample, MINT


class CandidatePaperTests(unittest.TestCase):
    def inventory(self):
        return dict(terminal_token_raw='1000',terminal_sol_lamports=50000000,
                    unspent_lamports=10,entry_friction_lamports=5)

    def quote(self,**changes):
        return dict(inputMint=MINT,outputMint=SOL_MINT,inAmount='1000',outAmount='51000000',
                    otherAmountThreshold='50000000',swapMode='ExactIn',slippageBps=100,**changes)

    def test_quote_uses_minimum_actual_route_instead_of_mark_haircut(self):
        r=paper.quoted_exit(self.inventory(),MINT,100,paper.MODEL,lambda url:self.quote(),clock=lambda:101)
        self.assertEqual(r['quoted_minimum_net_lamports'],10-5-26151)
        self.assertEqual(r['extra_execution_stress_lamports'],r['quoted_minimum_net_lamports']-100000)

    def test_zero_token_costs_and_quote_binding(self):
        inv=dict(self.inventory(),terminal_token_raw='0',terminal_sol_lamports=99999990,entry_friction_lamports=0)
        def forbidden(url):raise AssertionError('No quote should be requested')
        r=paper.quoted_exit(inv,MINT,100,paper.MODEL,forbidden,clock=lambda:101)
        self.assertEqual(r['quoted_minimum_net_lamports'],-26151)
        for field,value in [('inputMint','wrong'),('inAmount','999'),('slippageBps',False),('otherAmountThreshold','0')]:
            q=self.quote();q[field]=value
            with self.assertRaises(ValueError):
                paper.quoted_exit(self.inventory(),MINT,100,paper.MODEL,lambda url:q,clock=lambda:101)
        with self.assertRaisesRegex(ValueError,'stale_inventory'):
            paper.quoted_exit(self.inventory(),MINT,100,paper.MODEL,forbidden,clock=lambda:131)
        times=iter([101,131])
        with self.assertRaisesRegex(ValueError,'inventory_expired'):
            paper.quoted_exit(self.inventory(),MINT,100,paper.MODEL,lambda url:self.quote(),clock=lambda:next(times))

    def prepare(self,root):
        profile=root/'profile';memory=profile/'memories';memory.mkdir(parents=True)
        old,base=sample(9700,0),sample(10000,0)
        f=candidate_fee_forecast(base,[old],10000.2,validate_candidate_snapshot)
        (memory/'dlmm_candidate_fee_forecasts.jsonl').write_text(json.dumps(f)+'\n')
        (memory/'dlmm_candidate_bin_samples.jsonl').write_text(json.dumps(old)+'\n'+json.dumps(base)+'\n')
        return profile,root/'paper'

    def test_fresh_paper_entry_and_terminal_need_no_live_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile,out=self.prepare(Path(tmp));before={p.name:p.read_bytes() for p in (profile/'memories').iterdir()}
            with patch.object(paper.time,'time',return_value=10002), patch.object(paper,'snapshot',return_value=sample(10001,0)):
                first=paper.tick(profile,out)
            self.assertEqual(first['status'],'paper_entry_frozen')
            self.assertEqual(first['active'],1)
            quote=paper.quoted_exit
            with patch.object(paper.time,'time',return_value=13602), patch.object(paper,'snapshot',return_value=sample(13601,0)), \
                 patch.object(paper,'quoted_exit',side_effect=lambda *args:quote(*args,clock=lambda:13602)):
                end=paper.tick(profile,out)
            self.assertEqual(end['completed'],1)
            self.assertEqual(end['statuses'],{'paired':1})
            self.assertEqual(end['active'],0)
            outcome=json.loads(next((out/'outcomes').glob('*.json')).read_text())
            for s in outcome['strategies'].values():
                self.assertLess(s['quoted_minimum_net_lamports'],0)
            self.assertEqual(before,{p.name:p.read_bytes() for p in (profile/'memories').iterdir()})

    def test_missed_terminal_is_unknown_and_config_cannot_be_rewritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile,out=self.prepare(Path(tmp))
            with patch.object(paper.time,'time',return_value=10002), patch.object(paper,'snapshot',return_value=sample(10001,0)):
                paper.tick(profile,out)
            with patch.object(paper.time,'time',return_value=15000), patch.object(paper,'snapshot',side_effect=AssertionError('No late sampling')):
                r=paper.tick(profile,out)
            self.assertEqual(r['statuses'],{'unmeasured':1})
            record=json.loads(next((out/'outcomes').glob('*.json')).read_text())
            self.assertEqual(record['reason'],'terminal_deadline_missed')
            config=json.loads((out/'config.json').read_text());config['model']['network_cost']=0
            (out/'config.json').write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'frozen_config_changed'):
                paper.tick(profile,out)

    def test_snapshot_cli_is_read_only_and_wallet_activity_defers(self):
        raw=sample(10000,0)
        with patch.object(paper,'trading',return_value=False),patch.object(paper.time,'time',return_value=10000.5), \
             patch.object(paper.subprocess,'check_output',return_value=json.dumps(raw).encode()) as call:
            paper.snapshot(Path('/profile'),raw['pool'],MINT,'pulse',0)
        self.assertEqual(call.call_args.args[0][2],'candidate-bin-snapshot')
        self.assertEqual(call.call_args.args[0][-1],'0')
        wrong=dict(raw,pool='another')
        with patch.object(paper,'trading',return_value=False),patch.object(paper.subprocess,'check_output',return_value=json.dumps(wrong).encode()):
            with self.assertRaisesRegex(ValueError,'snapshot_identity_mismatch'):
                paper.snapshot(Path('/profile'),raw['pool'],MINT,'pulse')
        with patch.object(paper,'trading',return_value=True),patch.object(paper.subprocess,'check_output') as call:
            with self.assertRaisesRegex(ValueError,'wallet_trade_active'):
                paper.snapshot(Path('/profile'),raw['pool'],MINT,'pulse')
            call.assert_not_called()

    def test_exception_summaries_do_not_leak_provider_details(self):
        self.assertEqual(paper.error_reason(ValueError('https://private/key')), 'ValueError')
        self.assertEqual(paper.error_reason(ValueError('wallet_trade_active')), 'wallet_trade_active')


if __name__=='__main__':unittest.main()
