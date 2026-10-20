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

class PipelineCashGateIntegrationTests(unittest.TestCase):
    def test_both_entry_paths_refuse_before_market_reads(self):
        import contextlib
        import io
        import sys
        from unittest.mock import patch
        import dlmm_pipeline as pipeline
        now=10000000
        cash=dict(prior_closes=2,journal_closes=2,journal_last_close_ts=now-10,
                  last_close_ts=now-10,observed_at=now-1,prior_roots=2,prior_cash_roots=2,
                  prior_pnl_basis='matched_refund_cash',prior_net_pnl_sol=-.00005,
                  prior_cash_lower_sol=-.00005,prior_cash_upper_sol=-.00005)
        journal='\n'.join(json.dumps(dict(ts=now-i,pnl_pct=1,position=str(i),root_chain_id=str(i))) for i in (10,20))
        candidate=dict(pool='pool',name='TOKEN-SOL',base_mint='mint',base_symbol='TOKEN',
                       tvl=50000,volatility=2,score=80,sol_is_x=False,bin_step=100)
        for flag, individual in [(f, i) for f in ('--from-batch','--from-signal') for i in (False, True)]:
            for stale in (False,True):
                with self.subTest(flag=flag,stale=stale), contextlib.ExitStack() as stack:
                    record=dict(cash,observed_at=now-901 if stale else now-1)
                    if individual:
                        record.update(prior_pnl_basis='pre_swap_mark_only', prior_cash_roots=0,
                                      prior_net_pnl_sol=None, prior_cash_lower_sol=None, prior_cash_upper_sol=None,
                                      recent_position_cash_losses=[dict(position=str(i),root=str(i),ts=now-i,
                                                                        cash_upper_lamports=-10) for i in (10,20)])
                    def command(cmd, **kwargs):
                        if 'sol:dlmm:cash_history' in cmd:
                            self.assertEqual(kwargs.get('timeout'),2)
                            return json.dumps({'pool':record}),'',0
                        if 'sol:dlmm:history:pool:' in cmd:return journal,'',0
                        if cmd.startswith('redis-cli '):return '', '', 0
                        raise AssertionError('Unexpected external command: '+cmd)
                    output=io.StringIO();stack.enter_context(contextlib.redirect_stdout(output))
                    payload=[candidate] if flag=='--from-batch' else candidate
                    stack.enter_context(patch.object(sys,'argv',['dlmm_pipeline.py','--mode','turnover',flag,json.dumps(payload)]))
                    for name,value in [('record_pipeline_candidates',None),('reconcile_redis_vs_meteora',None),
                                       ('get_active_positions_count_for_mode',0),('get_wallet_sol_balance',.5),
                                       ('load_signal_weights',{}),('prune_blocklists',None),
                                       ('get_open_positions',[]),('check_pvp_conflict',False)]:
                        stack.enter_context(patch.object(pipeline,name,return_value=value))
                    stack.enter_context(patch.object(pipeline,'load_soul_dlmm_params',return_value={**pipeline.MODE_DEFAULTS['turnover'],'MIN_ORGANIC_SCORE':60}))
                    stack.enter_context(patch.object(pipeline,'run_command',side_effect=command))
                    stack.enter_context(patch.object(pipeline.time,'time',return_value=now))
                    market=stack.enter_context(patch.object(pipeline,'get_momentum',side_effect=RuntimeError('market boundary reached')))
                    if stale:
                        with self.assertRaisesRegex(RuntimeError,'market boundary reached'):pipeline.main()
                        market.assert_called_once()
                    else:
                        with self.assertRaises(SystemExit) as stop:pipeline.main()
                        self.assertEqual(stop.exception.code,0)
                        self.assertIn('pool cash memory',output.getvalue())
                        market.assert_not_called()


if __name__=='__main__':unittest.main()
