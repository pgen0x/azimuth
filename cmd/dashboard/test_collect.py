"""Synthetic regressions for dashboard review F1-F6; never queries live services."""
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import time
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('dashboard_collect',Path(__file__).with_name('collect.py'))
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
T=2000000000
DAY=86400

def rows(path, data):
    path.write_text(''.join(json.dumps(r)+'\n' for r in data))

def snap(ts,slot,native=5,**kw):
    return dict(ts=ts,slot=slot,native_sol=native,spl_mark_sol=0,lp_mark_sol=0,
                refundable_rent_sol=0,known_asset_subtotal_sol=native,tokens=[],issues=[],
                wallet_history_complete=True,**kw)

def bridge_fixture(m):
    rows(m/'dlmm_nav.jsonl',[snap(T-DAY,100),snap(T,200,5.09999)])
    rows(m/'dlmm_wallet_transactions.jsonl',[
        dict(signature='deposit',slot=101,wallet_delta_lamports=-1000005000,fee_lamports=5000,
             token_rent_evidence={'funded':[],'refunded':[]},event_position='position-A',failed=False,nonrefundable_account_cost_lamports=0),
        dict(signature='close',slot=199,wallet_delta_lamports=1099995000,fee_lamports=5000,
             token_rent_evidence={'funded':[],'refunded':[]},event_position='position-A',failed=False,position_account_closed=True,nonrefundable_account_cost_lamports=0)])
    rows(m/'dlmm_transactions.jsonl',[dict(signature='deposit',kind='deploy',position='position-A'),dict(signature='close',kind='close',position='position-A')])
    rows(m/'dlmm_realized.jsonl',[dict(position='position-A',closed_at=T,realized_sol=.1)])
    rows(m/'dlmm_closes.jsonl',[dict(position='position-A',mode='synthetic')])

def receipt(**kw):
    r=dict(success=True,dry_run=False,txHash='receipt-A',fee_lamports=5000,
           accounts=[dict(account='account-A',mint='mint-A',rent_lamports=2000000,burn_raw='10',quote_lamports=1000)])
    r.update(kw);return r

def fact(**kw):
    r=dict(signature='receipt-A',failed=False,landed=True,slot=1,fee_lamports=5000,wallet_delta_lamports=1995000,
           token_rent_evidence=dict(refunded=[dict(account='account-A',mint='mint-A',lamports=2000000)]),token_deltas_raw={'mint-A':'-10'})
    r.update(kw);return r

def journal(data): return '\n'.join('1000.0 fixture node[1]: '+json.dumps(r) for r in data)+'\n'
def runner(data='',code=0): return lambda *a,**k:SimpleNamespace(stdout=data,stderr='',returncode=code)

class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.m=Path(self.tmp.name)
        self.net=patch.object(socket.socket,'connect',side_effect=AssertionError('offline only'));self.net.start()
    def tearDown(self): self.net.stop();self.tmp.cleanup()
    def dust(self,data=None,chain=None):
        rows(self.m/'dlmm_wallet_transactions.jsonl',[fact()] if chain is None else chain)
        return c.dust_ledger(self.m,1000,run=runner(journal([receipt()] if data is None else data)))
    def test_dust_verified_control_and_dedup(self):
        one=self.dust();two=self.dust([receipt(),receipt()])
        self.assertEqual(one['status'],'ok');self.assertEqual(one['closed_accounts'],1)
        self.assertEqual(one['rent_recovered_lamports'],2000000)
        self.assertEqual(one['liquid_native_gain_sol'],.001995)
        self.assertEqual(one['nav_effect_sol'],-.000006)
        for key in ('executed_tx','closed_accounts','rent_recovered_lamports','fee_lamports','forfeited_quote_lamports'):
            self.assertEqual(one[key],two[key],key)
        self.assertEqual(two['duplicates'],1)
    def test_failed_unlanded_unknown_never_credit(self):
        for state,chain in [('failed',[fact(failed=True,wallet_delta_lamports=-5000)]),
                            ('unlanded',[fact(landed=False)]),('unknown',[]),
                            ('missing_outcome',[fact(failed=None)]),('conflicting',[fact()])]:
            with self.subTest(state=state):
                data=[receipt(),receipt(fee_lamports=6000)] if state=='conflicting' else [receipt()]
                r=self.dust(data,chain)
                self.assertEqual(r['closed_accounts'],0);self.assertEqual(r['burned_accounts'],0)
                self.assertIn(r['rent_recovered_lamports'],(0,None));self.assertIn(r['forfeited_quote_lamports'],(0,None))
                if state=='failed':
                    self.assertEqual(r['liquid_native_gain_sol'],-.000005)
                    self.assertEqual(r['verified_subtotal']['failed'],1);self.assertEqual(r['verified_subtotal']['transactions'],0)
                    self.assertTrue(any(v['rule']=='burn transaction failed on-chain' for v in r['violations']))
                if state=='unlanded': self.assertEqual(r['liquid_native_gain_sol'],0)
                if state=='unknown': self.assertIsNone(r['liquid_native_gain_sol'])
                self.assertEqual(r['receipt_claimed']['closed_accounts'],1)
    def test_dust_requires_account_and_burn_evidence(self):
        for change in ({'token_rent_evidence':{}},{'wallet_delta_lamports':10},{'token_deltas_raw':{}},
                       {'token_rent_evidence':dict(refunded=[dict(account='other',mint='mint-A',lamports=2000000)])},
                       {'token_rent_evidence':dict(refunded=[dict(account='account-A',mint='different-mint',lamports=2000000)])}):
            with self.subTest(change=change):
                r=self.dust(chain=[fact(**change)])
                self.assertNotEqual(r['status'],'ok');self.assertIsNone(r['forfeited_quote_lamports'])
    def test_dust_nulls_remain_unknown(self):
        r=receipt(fee_lamports=None);r['accounts'][0]['quote_lamports']=None
        d=self.dust([r],[fact(fee_lamports=None)])
        self.assertIsNone(d['fee_lamports']);self.assertIsNone(d['forfeited_quote_lamports'])
        self.assertIsNone(d['receipt_claimed']['fee_lamports']);self.assertIsNone(d['receipt_claimed']['forfeited_quote_lamports'])
        self.assertIsNone(d['nav_effect_sol']);self.assertFalse(d['rules_complete'])
    def test_dry_run_and_empty_confirmed_window(self):
        r=self.dust([receipt(dry_run=True)])
        self.assertEqual(r['executed_tx'],0);self.assertEqual(r['rent_recovered_lamports'],0)
    def test_journal_errors_unknown_and_bounded(self):
        for run in (runner('',1),lambda *a,**k:(_ for _ in ()).throw(OSError('absent')),
                    runner('x'*(2*1024*1024+1))):
            r=c.dust_ledger(self.m,1000,run=run)
            self.assertEqual(r['status'],'unavailable');self.assertIsNone(r['rent_recovered_lamports'])
            self.assertIsNone(r['liquid_native_gain_sol']);self.assertFalse(r['rules_complete'])
        r=self.dust([dict(success=True,dry_run=True)]*5000)
        self.assertEqual(r['status'],'partial');self.assertTrue(r['source_metadata']['journal']['truncated'])
    def test_error_redaction_preserves_count(self):
        msg='RPC https://rpc.invalid/?api_key=SYNTHETIC_CREDENTIAL'
        r=c.clean(self.dust([dict(success=False,error=msg)]))
        self.assertNotIn('SYNTHETIC_CREDENTIAL',json.dumps(r))
        self.assertEqual(r['errors'][0]['count'],1)
        self.assertNotIn('SYNTHETIC_CREDENTIAL',json.dumps(c.clean({msg:1})))
    def test_journal_fixed_argv(self):
        calls=[]
        def run(argv,**kw): calls.append((argv,kw));return runner()()
        c.dust_ledger(self.m,1234,run=run)
        self.assertEqual(calls[0][0][5],'@1234');self.assertEqual(calls[0][1]['timeout'],5)
        self.assertFalse(calls[0][1].get('shell'))
        with self.assertRaises(ValueError):c.dust_ledger(self.m,'1; touch NEVER',run=run)
        self.assertEqual(len(calls),1)
    def test_real_subprocess_byte_cap_and_timeout(self):
        executable=self.m/'journalctl'
        executable.write_text('#!'+sys.executable+'\nimport os\nfor i in range(1000):\n os.write(1,b"x"*65536)\n os.write(2,b"y"*65536)\n')
        executable.chmod(0o700)
        with patch.dict(os.environ,{'PATH':str(self.m)+os.pathsep+os.environ['PATH']}):
            r=c.bounded_run(['journalctl'],cap=100000)
            self.assertEqual(r.capture_status,'over_cap');self.assertLessEqual(r.capture_bytes,100001)
            self.assertLessEqual(len(r.stdout.encode())+len(r.stderr.encode()),100000)
            d=c.dust_ledger(self.m,1000)
            self.assertEqual(d['status'],'unavailable');self.assertEqual(d['source_metadata']['journal']['status'],'over_cap')
            executable.write_text('#!'+sys.executable+'\nimport time\ntime.sleep(30)\n')
            start=time.monotonic();r=c.bounded_run(['journalctl'],timeout=.1)
            self.assertEqual(r.capture_status,'timeout');self.assertLess(time.monotonic()-start,4)
    def test_bridge_cash_oracle(self):
        bridge_fixture(self.m);b=c.nav_bridge(self.m,T,1);parts={r['component']:r['sol'] for r in b['components']}
        self.assertEqual(b['status'],'ok');self.assertTrue(b['native_identity_exact'])
        self.assertAlmostEqual(parts['lp_realized'],.1);self.assertAlmostEqual(parts['network_fees'],-.00001)
        self.assertAlmostEqual(sum(parts.values()),.09999)
    def test_bridge_every_source_failure_visible(self):
        names=['dlmm_transactions.jsonl','dlmm_wallet_transactions.jsonl','dlmm_realized.jsonl','dlmm_closes.jsonl']
        for name in names:
            for corruption in ('missing','over_cap','corrupt','partial','non_object','bad_key'):
                with self.subTest(name=name,corruption=corruption):
                    bridge_fixture(self.m);f=self.m/name
                    if corruption=='missing': f.unlink()
                    elif corruption=='over_cap':
                        with f.open('wb') as h:h.truncate(64*1024*1024+1)
                    else:
                        with f.open('a') as h:h.write({'corrupt':'broken\n','partial':'{"x":','non_object':'[]\n','bad_key':'{"position":[],"signature":[]}\n'}[corruption])
                    b=c.nav_bridge(self.m,T,1)
                    if name=='dlmm_closes.jsonl' and corruption in ('corrupt','non_object','bad_key'):
                        # closes only label modes: a bad legacy line with every window lifecycle labelled
                        # is reported, not an incomplete bridge (fix2)
                        self.assertEqual(b['status'],'ok');self.assertGreater(b['closes_invalid_lines'],0);self.assertEqual(b['mode_unknown'],0)
                        continue
                    self.assertNotEqual(b['status'],'ok');self.assertTrue(b['incomplete_sources'])
                    self.assertIsNone(next(x['sol'] for x in b['components'] if x['component']=='rent_ledger'))
    def test_bridge_closes_corruption_that_drops_a_mode_is_incomplete(self):
        bridge_fixture(self.m);f=self.m/'dlmm_closes.jsonl'
        f.write_text('broken\n')  # every label gone: the window lifecycle is now mode-unknown
        b=c.nav_bridge(self.m,T,1)
        self.assertEqual(b['mode_unknown'],1);self.assertIn('closes',b['incomplete_sources'])
    def _big_nav(self,rows,pad=40_000):
        with (self.m/'dlmm_nav.jsonl').open('w') as h:
            for r in rows: h.write(json.dumps(dict(r,pad='x'*pad))+'\n')
        self.assertGreater((self.m/'dlmm_nav.jsonl').stat().st_size,c.NAV_FULL_SCAN_BYTES)
    def test_large_monotonic_nav_gives_deltas(self):
        day=86400;base=20000*day+3*3600  # local midnight in America/Sao_Paulo (UTC-3)
        rows=[dict(ts=base+i*day+j*2400,native_sol=1.0+i*.01,lp_mark_sol=0.0,refundable_rent_sol=.01,known_asset_subtotal_sol=1.01+i*.01,
                   external_flow_lamports=0,wallet_history_complete=True) for i in range(4) for j in range(30)]
        self._big_nav(rows)
        ns=c.north_star(self.m,base+3*day+20*3600,days=3,tz='America/Sao_Paulo')
        full=[d for d in ns['days'] if d['status']=='ok']
        self.assertEqual(len(full),3);self.assertEqual(ns['days'][-1]['status'],'partial_day')
        for d in ns['days'][1:]:
            self.assertAlmostEqual(d['d_cash_sol'],.01);self.assertEqual(d['source']['ordering_assumption'],'visited_window_monotonic')
    def test_inversion_next_to_the_pick_is_partial(self):
        rows=[dict(ts=100*i,native_sol=1.0) for i in range(120)]
        rows.insert(21,dict(ts=1,native_sol=9.0))  # out-of-order neighbour right after the pick for t=2000
        self._big_nav(rows)
        meta={};row=c.nav_at(self.m/'dlmm_nav.jsonl',2000,meta=meta)
        self.assertIn(row['ts'],(1,2000));self.assertEqual(meta['status'],'partial');self.assertTrue(meta['out_of_order'])
        meta={};c.nav_at(self.m/'dlmm_nav.jsonl',500,meta=meta)  # inversion far from this pick
        self.assertEqual(meta['status'],'ok')
    def test_neighbour_lines_catch_an_unvisited_inversion(self):
        # Found by search: the binary search never visits the inverted row; only the +1 neighbour read sees it.
        rows=[dict(ts=100*i,native_sol=1.0) for i in range(120)]
        rows.insert(20,dict(ts=1850,native_sol=2.0))
        self._big_nav(rows)
        meta={};c.nav_at(self.m/'dlmm_nav.jsonl',1900,meta=meta)
        self.assertEqual(meta['status'],'partial');self.assertTrue(meta['out_of_order'])
    def _backscan_counterexample(self,base=0):
        """Codex fix3 P1 probe: 300 rows / ~4.8 MB; one row that only previous()'s backward scan
        reads is moved past the cutoff. Returns (rows, changed index, cutoff, reads, spy)."""
        import inspect
        rows=[dict(ts=base+i*100,native_sol=1.0,lp_mark_sol=0.0,refundable_rent_sol=0.0,
                   known_asset_subtotal_sol=1.0,external_flow_lamports=0) for i in range(300)]
        cutoff=base+15090
        def write():
            with (self.m/'dlmm_nav.jsonl').open('w') as h:
                for r in rows: h.write(json.dumps(dict(r,pad='x'*16000))+'\n')
        original=c._nav_line;reads=[]
        def spy(*a,**k):
            item=original(*a,**k)
            if item: reads.append((item[0],item[2],any(fr.function=='previous' for fr in inspect.stack())))
            return item
        write()
        with patch.object(c,'_nav_line',side_effect=spy):c.nav_at(self.m/'dlmm_nav.jsonl',cutoff,meta={})
        other={ts for _,ts,prev in reads if not prev}
        only_prev=sorted({(ts-base)//100 for _,ts,prev in reads if prev and ts not in other and ts<base+14900})
        self.assertTrue(only_prev,'fixture no longer exercises the backward scan')
        changed=only_prev[0];rows[changed].update(ts=base+15050,native_sol=9.0,known_asset_subtotal_sol=9.0)
        write();reads.clear()
        self.assertGreater((self.m/'dlmm_nav.jsonl').stat().st_size,c.NAV_FULL_SCAN_BYTES)
        return rows,changed,cutoff,reads,spy
    def test_inversion_read_by_backward_scan_is_partial(self):
        rows,changed,cutoff,reads,spy=self._backscan_counterexample()
        self.assertEqual(changed,146)  # the exact row of codex's counterexample
        meta={}
        with patch.object(c,'_nav_line',side_effect=spy):c.nav_at(self.m/'dlmm_nav.jsonl',cutoff,meta=meta)
        self.assertIn(15050,[ts for _,ts,prev in reads if prev])  # the inversion was read, by previous()
        self.assertEqual(meta['status'],'partial');self.assertTrue(meta['out_of_order']);self.assertTrue(c.incomplete(meta))
        self.assertEqual(meta['visited_rows'],len({off for off,_,_ in reads}))  # every row read is checked
        self.assertLess(meta['read_calls'],c.NAV_LOOKUP_READS);self.assertLess(meta['read_bytes'],c.NAV_LOOKUP_BYTES)
    def test_backward_scan_inversion_blocks_the_next_days_delta(self):
        day=20000;end=day*86400-7*3600+86400  # end of a local day in Asia/Jakarta (UTC+7)
        rows,changed,cutoff,reads,spy=self._backscan_counterexample(base=end-1-15090)
        ns=c.north_star(self.m,cutoff+14000,days=1,tz='Asia/Jakarta')
        first,last=ns['days']
        self.assertEqual(first['status'],'partial_source');self.assertTrue(first['source']['out_of_order'])
        self.assertNotIn('d_cash_sol',last);self.assertNotIn('d_known_sol',last);self.assertEqual(ns['status'],'partial')
    def test_bridge_unknown_values_and_history(self):
        for field in ('fee_lamports','wallet_delta_lamports','nonrefundable_account_cost_lamports'):
            bridge_fixture(self.m);f=self.m/'dlmm_wallet_transactions.jsonl';data=[json.loads(l) for l in f.read_text().splitlines()];data[0][field]=None;rows(f,data)
            b=c.nav_bridge(self.m,T,1)
            self.assertNotEqual(b['status'],'ok');self.assertIn(field,b['incomplete_values'])
            if field=='wallet_delta_lamports':self.assertIsNone(b['native_identity_exact'])
            else:
                key='network_fees' if field=='fee_lamports' else 'rent_permanent'
                self.assertIsNone(next(x['sol'] for x in b['components'] if x['component']==key))
        bridge_fixture(self.m);f=self.m/'dlmm_nav.jsonl';data=[json.loads(l) for l in f.read_text().splitlines()];data[-1]['wallet_history_complete']=False;rows(f,data)
        b=c.nav_bridge(self.m,T,1);self.assertNotEqual(b['status'],'ok');self.assertIsNone(b['native_identity_exact'])
        self.assertTrue(all(v['sol'] is None for v in b['fees_by_kind'].values()))
        bridge_fixture(self.m);f=self.m/'dlmm_wallet_transactions.jsonl';data=[json.loads(l) for l in f.read_text().splitlines()]
        data[0]['token_rent_evidence']={'funded':[{'lamports':None}],'refunded':[]};rows(f,data)
        b=c.nav_bridge(self.m,T,1);self.assertIn('ata_funding',b['incomplete_values'])
    def test_bridge_component_ids_survive_the_shared_sensor(self):
        # The served payload goes through clean(); component ids must not read as credentials.
        bridge_fixture(self.m);b=c.clean(c.nav_bridge(self.m,T,1))
        ids=[r['component'] for r in b['components']]
        self.assertIn('unexplained',ids);self.assertNotIn('[masked]',json.dumps(b['components']))
    def test_unattributed_cash_not_rent(self):
        bridge_fixture(self.m);rows(self.m/'dlmm_transactions.jsonl',[])
        b=c.nav_bridge(self.m,T,1);p={r['component']:r for r in b['components']}
        self.assertNotEqual(b['status'],'ok');self.assertIsNone(p['rent_ledger']['sol'])
        self.assertEqual(p['rent_ledger']['measured_subtotal_sol'],0)
        self.assertAlmostEqual(p['unattributed_cash']['measured_subtotal_sol'],.1)
    def test_realized_unknown_and_shapes(self):
        rows(self.m/'dlmm_realized.jsonl',[dict(position='p',closed_at=T,realized_sol=None),dict(position=[],closed_at=T,realized_sol=.1)])
        rows(self.m/'dlmm_closes.jsonl',[dict(position='p',mode='synthetic')])
        r=c.realized_by_mode(self.m,T-1);cell=next(iter(r['days'].values()))['synthetic']
        self.assertIsNone(cell['realized_sol']);self.assertEqual(cell['unmeasured'],1);self.assertNotEqual(r['status'],'ok')
    def test_nav_validated_timestamp_and_duplicate_partial(self):
        f=self.m/'dlmm_nav.jsonl'
        f.write_text('{"ts":999999,BROKEN}\n'+json.dumps(dict(ts=10,native_sol=1))+'\n'+json.dumps(dict(ts=20,native_sol=2))+'\n')
        meta={};self.assertEqual(c.nav_at(f,20,meta=meta)['ts'],20);self.assertEqual(meta['invalid_lines'],1)
        rows(f,[{'nested':{'ts':1},'ts':100,'native_sol':9}]);self.assertIsNone(c.nav_at(f,50))
        rows(f,[dict(ts=10,native_sol=1),dict(ts=20,native_sol=2),dict(ts=20,native_sol=3)])
        with f.open('a') as h:h.write('{"ts":21')
        self.assertEqual(c.nav_at(f,20)['native_sol'],3)
    def test_north_star_latest_unknown_and_zone(self):
        for tz,off in (('Asia/Jakarta',7*3600),('America/Sao_Paulo',-3*3600),('UTC',0)):
            with self.subTest(tz=tz):
                base=20000*DAY-off;f=self.m/'dlmm_nav.jsonl'
                bad=snap(base+20,2,None)
                rows(f,[snap(base+10,1,1),bad,snap(base+DAY+10,3,2)])
                ns=c.north_star(self.m,base+DAY+20,1,tz)
                self.assertEqual(ns['tz'],tz);days=ns['days']
                self.assertEqual([d['day'] for d in days],['2024-10-04','2024-10-05'])
                self.assertEqual(days[0]['ts'],base+20);self.assertIsNone(days[1]['d_cash_sol'])
                rows(f,[snap(base-1,1,1),snap(base,2,2),snap(base+DAY-1,3,3),snap(base+DAY,4,4)])
                self.assertEqual([x['native_sol'] for x in c.north_star(self.m,base+DAY,2,tz)['days']],[1,3,4])
    def test_unknown_zone_is_an_unavailable_panel(self):
        self.assertEqual(c.panel(c.north_star,self.m,T,1,'Mars/Olympus')['status'],'unavailable')
    def test_nav_read_work_caps(self):
        f=self.m/'dlmm_nav.jsonl';f.write_bytes(b'x'*(10*1024*1024)+b'\n')
        meta={};self.assertIsNone(c.nav_at(f,20,meta=meta));self.assertEqual(meta['status'],'line_cap')
        self.assertLessEqual(meta['read_bytes'],c.NAV_LOOKUP_BYTES)
        f.write_bytes(b'not a snapshot\n'*10000+json.dumps(dict(ts=20,native_sol=2)).encode()+b'\n')
        meta={};c.nav_at(f,20,meta=meta)
        self.assertLessEqual(meta['read_calls'],c.NAV_LOOKUP_READS);self.assertEqual(meta['status'],'work_cap')
    def test_panel_isolation(self):
        def broken(): raise TypeError('synthetic malformed source')
        self.assertEqual(c.panel(broken)['status'],'unavailable')
        profile=self.m/'profile';memory=profile/'memories';memory.mkdir(parents=True)
        state=self.m/'state';state.mkdir()
        rows(memory/'dlmm_realized.jsonl',[dict(position=[],closed_at=T,realized_sol=.1)])
        with patch.object(c.subprocess,'run',runner()),patch.object(c,'bounded_run',runner()):
            d=c.collect(profile,state,1,('UTC','America/Sao_Paulo'))
        self.assertIn('nav',d);self.assertIn('journal',d);self.assertEqual(set(d['by_tz']),{'UTC','America/Sao_Paulo'})
        self.assertNotEqual(d['by_tz']['America/Sao_Paulo']['realized']['status'],'ok')
        self.assertEqual(d['by_tz']['America/Sao_Paulo']['north_star']['tz'],'America/Sao_Paulo')

class OwnOnlyTests(unittest.TestCase):
    """Owner policy: no comparison with another bot reaches the dashboard."""
    def test_drops_other_bot_keys_recursively_and_keeps_own_cohort(self):
        other='otherbot'  # made-up name, hidden only through the operator deny-list
        report={'lp_comparison':{'azimuth':{'lp_pnl_sol':0.1,'note':'own'},other:{'lp_pnl_sol':0.2}},
                'limits':[{other.upper()+'_cohort':1,'kept':2}],'nested':{'Reference_Bot_wallet':'x','ok':{'Comparison':3,'v':4}},
                'bin_width_holding_replay':[{'limitation':'Gross allocation comparison'}]}
        with patch.dict(os.environ,{'DASHBOARD_HIDE_KEYS':' '+other+' ,,'}):
            out=c.own_only(report)
        self.assertNotIn('lp_comparison',out);self.assertEqual(out['limits'],[{'kept':2}])
        self.assertEqual(out['nested'],{'ok':{'v':4}})
        self.assertEqual(out['bin_width_holding_replay'],report['bin_width_holding_replay'])  # values are untouched
        self.assertNotIn(other,json.dumps(out).lower())
    def test_generic_markers_apply_without_a_deny_list(self):
        with patch.dict(os.environ,{'DASHBOARD_HIDE_KEYS':''}):
            out=c.own_only({'otherbot_pnl':1,'Other_Bot':2,'lp_comparison':3,'reference_bot':4,'own':5})
        self.assertEqual(out,{'otherbot_pnl':1,'own':5})  # names are never built in
    def test_unit_list_is_shipped_units_plus_validated_extras(self):
        self.assertTrue(all(u.startswith(('azimuth','hermes-gateway')) for u in c.unit_list('')))
        self.assertNotIn('daily',' '.join(c.unit_list('')))
        units=c.unit_list('my-job.timer, my-job.service,bad name.service,../x.service,my-job.timer,azimuth.service')
        self.assertEqual(units[len(c.UNITS):],['my-job.timer','my-job.service'])
        self.assertEqual(units.count('azimuth.service'),1)
    def test_collect_has_no_evaluation_and_no_other_bot(self):
        other='otherbot'
        profile=self.m/'profile';(profile/'memories').mkdir(parents=True)
        state=self.m/'state';(state/'reviews'/'r1').mkdir(parents=True)
        (state/'reviews'/'r1'/'evaluation.json').write_text(json.dumps({'generated_at':5,'lp_comparison':{'azimuth':{},other:{}}}))
        rows(profile/'memories'/'dlmm_nav.jsonl',[{'ts':1,'native_sol':1,other+'_wallet':'x'}])
        with patch.object(c.subprocess,'run',runner()),patch.object(c,'bounded_run',runner()),patch.dict(os.environ,{'DASHBOARD_HIDE_KEYS':other}):
            d=c.collect(profile,state,1)
        self.assertNotIn('evaluation',d);self.assertNotIn(other,json.dumps(d).lower())
        self.assertEqual(d['nav']['native_sol'],1)
    setUp=CollectorTests.setUp
    tearDown=CollectorTests.tearDown

KEY='ab'*32  # synthetic 64-hex, shaped like a private key
def rh_run(active='inactive', start='@1000', toggles='robinhood=false, rh-turnover=true', log=None):
    """Fake bounded_run keyed on argv: systemd state, the scanner start line and unit journals."""
    def run(argv, **kw):
        joined=' '.join(argv); out=''
        if argv[:2]==['systemctl','--user'] and 'azimuth-rh-monitor.service' in argv:
            out='Id=azimuth-rh-monitor.service\nActiveState=%s\nUnitFileState=disabled\n' % active
        elif argv[:2]==['systemctl','--user']: out=start+'\n'
        elif 'scanner: started' in joined:
            out=json.dumps({'MESSAGE':'scanner: started (interval=1m0s, pulse=true, %s)' % toggles,'__REALTIME_TIMESTAMP':'1000000000'})+'\n'
        elif 'azimuth-rh-monitor.service' in argv:
            out=''.join(json.dumps({'MESSAGE':m,'__REALTIME_TIMESTAMP':str(t*1000000)})+'\n' for t,m in (log or []))
        return SimpleNamespace(stdout=out,stderr='',returncode=0,capture_status='ok')
    return run

class RobinhoodTests(unittest.TestCase):
    setUp=CollectorTests.setUp
    tearDown=CollectorTests.tearDown
    def closes(self,where=None):
        rows((where or self.m)/'uni_closes.jsonl',[
            {'ts':86400*3,'tokenId':'1','pool':'0xp1','reason':'turnover re-center','success':True,'dry_run':False,'protocol':'v3','quote_symbol':'WETH','realized_quote':0.01,'pnl_basis':'realized','pnl_pct':95.0,'gas_eth':'0.001','gas_txs':3},
            {'ts':86400*3+60,'tokenId':'7','pool':'0xp7','reason':'turnover rung filled','success':True,'dry_run':False,'protocol':'v4','quote_symbol':'ETH','realized_quote':-0.004,'pnl_basis':'realized','pnl_pct':-4,'gas_eth':'0.002','gas_txs':2},
            {'ts':86400*4,'tokenId':'8','pool':'0xp8','reason':'ladder idle','success':True,'dry_run':False,'protocol':'v3','quote_symbol':'WETH','realized_quote':None,'pnl_pct':1},
            {'ts':86400*4+5,'tokenId':'9','pool':'0xp9','reason':'ladder stale','success':True,'dry_run':False,'protocol':'v3','quote_symbol':'USDG','realized_quote':1.5,'pnl_basis':'realized','pnl_pct':2},
            {'ts':86400*4+9,'tokenId':'10','pool':'0xpa','reason':'fill','success':True,'dry_run':False,'protocol':'v3','quote_symbol':'WETH','realized_quote':0.5,'pnl_basis':'mark','stranded':{'symbol':'X'},'pnl_pct':90},
            {'ts':86400*5,'tokenId':'2','pool':'0xp2','reason':'rpc https://rpc.example/KEY failed','success':False,'dry_run':False,'protocol':'v3','realized_quote':9.0,'pnl_basis':'realized','quote_symbol':'WETH'},
            {'ts':86400*5,'tokenId':'11','pool':'0xpb','reason':'dry','success':True,'dry_run':True,'quote_symbol':'WETH','realized_quote':5.0,'pnl_basis':'realized'}])
    def test_closes_success_only_per_asset_null_counted_mark_flagged(self):
        self.closes()
        d=c.rh_closes(self.m,'UTC')
        self.assertEqual(d['skipped'],{'failed':1,'dry_run':1})
        eth,usdg=d['totals']['ETH'],d['totals']['USDG']
        self.assertAlmostEqual(eth['realized_quote'],0.006)  # WETH v3 + native ETH v4, never the failed or dry-run rows
        self.assertEqual((eth['closes'],eth['measured'],eth['unmeasured'],eth['mark_flagged']),(4,2,2,1))
        self.assertEqual((usdg['realized_quote'],usdg['closes']),(1.5,1))  # never summed with ETH
        self.assertAlmostEqual(d['gas']['gas_eth'],0.003);self.assertEqual((d['gas']['gas_txs'],d['gas']['unmetered']),(5,3))
        mark=next(r for r in d['closes'] if r['token_id']=='10')
        self.assertTrue(mark['mark_flagged']);self.assertIsNone(mark['realized_quote'])  # a mark is not money
        self.assertIsNone(next(r for r in d['closes'] if r['token_id']=='8')['realized_quote'])
        self.assertEqual(d['days']['1970-01-05']['ETH']['unmeasured'],2)
    def test_day_buckets_follow_the_viewer_zone(self):
        rows(self.m/'uni_closes.jsonl',[{'ts':86400*3+3600,'tokenId':'1','success':True,'quote_symbol':'WETH','realized_quote':0.1,'pnl_basis':'realized'}])
        self.assertEqual(list(c.rh_closes(self.m,'UTC')['days']),['1970-01-04'])
        self.assertEqual(list(c.rh_closes(self.m,'America/Sao_Paulo')['days']),['1970-01-03'])  # UTC-3
    def test_positions_open_only_without_a_successful_close_and_keyed_by_protocol(self):
        self.closes()
        rows(self.m/'uni_positions.jsonl',[{'tokenId':'1','pool':'0xp1','token0':'0xT','token1':'0xQ','quote':'0xQ','quoteSymbol':'WETH','strategy':'weth_below','tickLower':-600,'tickUpper':0,'ts':86400},
                                           {'tokenId':'2','pool':'0xp2','token0':'0xT','token1':'0xQ','quote':'0xQ','quoteSymbol':'WETH','strategy':'weth_below','ts':86400},
                                           {'tokenId':'11','pool':'0xpb','quoteSymbol':'WETH','strategy':'weth_below','ts':86400}])
        rows(self.m/'uni_v4_positions.jsonl',[{'tokenId':'1','protocol':'v4','pool':'0xv','key':{'currency0':'0x0','currency1':'0xT'},'quote':'0x0','quoteSymbol':'ETH','strategy':'weth_ladder','ts':86400*2}])
        out=c.robinhood(self.m,86400*6,run=rh_run())
        got={(p['protocol'],p['token_id']):p for p in out['positions']}
        self.assertEqual(set(got),{('v3','2'),('v3','11'),('v4','1')})  # dry-run close leaves 11 open; v4 #1 is not v3 #1
        self.assertEqual(got[('v3','2')]['token'],'0xT')
        self.assertNotIn('rpc.example',got[('v3','2')]['last_failed_close']['reason'])
        self.assertEqual(got[('v4','1')]['token'],'0xT');self.assertEqual(got[('v4','1')]['age_s'],86400*4)
    def test_status_inactive_unit_toggles_and_redacted_logs(self):
        log=[(50,'rpc https://rh.example/v2/'+KEY+' timeout'),(60,'PRIVATE_KEY='+KEY+' tokenId=1 gas'),(65,'tokenId=817 gas 0.0001 ETH'),(70,'tx 0x'+KEY+' re-center ok')]
        out=c.robinhood(self.m,100,run=rh_run(log=log))
        self.assertFalse(out['monitor_active']);self.assertEqual(out['unit']['ActiveState'],'inactive')
        self.assertEqual(out['modes']['flags'],{'robinhood':False,'rh-turnover':True});self.assertEqual(out['modes']['started_at'],1000)
        text=json.dumps(out['logs'])
        self.assertNotIn(KEY,text);self.assertNotIn('rh.example',text)
        self.assertIn('PRIVATE_KEY=[masked to end of line]',text);self.assertIn('tokenId=817 gas',text)  # a field name, not a secret
        self.assertEqual([r['time'] for r in out['logs']],[70,65,60,50])
        self.assertEqual(out['positions'],[]);self.assertEqual(out['stranded']['open'],[])  # no journals: empty, not an error
    def test_modes_unknown_when_scanner_not_running(self):
        out=c.robinhood(self.m,100,run=rh_run(start='@0'))
        self.assertEqual(out['modes']['status'],'unknown');self.assertIn('not running',out['modes']['note'])
    def test_stranded_latest_line_per_token_wins(self):
        rows(self.m/'uni_stranded.jsonl',[{'ts':1,'tokenId':'1','token':'0xA','symbol':'A','amount':'5','reason':'no pool','resolved':False},
                                          {'ts':2,'tokenId':'1','token':'0xa','symbol':'A','amount':'5','reason':'sold','resolved':True,'weth_out':'0.1'},
                                          {'ts':3,'tokenId':'2','token':'0xB','symbol':'B','amount':'7','reason':'quote 0','resolved':False,'attempts':4}])
        rows(self.m/'uni_positions.jsonl',[{'tokenId':'2','pool':'0xpool2','ts':1}])
        st=c.robinhood(self.m,100,run=rh_run())['stranded']
        self.assertEqual([(r['symbol'],r['pool'],r['amount_raw']) for r in st['open']],[('B','0xpool2','7')])
        self.assertEqual([r['symbol'] for r in st['resolved']],['A'])
    def test_collect_and_daily_carry_robinhood(self):
        (self.m/'memories').mkdir();self.closes(self.m/'memories')
        with patch.object(c.subprocess,'run',runner()),patch.object(c,'bounded_run',rh_run()):
            d=c.collect(self.m,self.m,1,('UTC',))
        self.assertIn('robinhood',d);self.assertEqual(d['by_tz']['UTC']['robinhood']['totals']['USDG']['closes'],1)

# Synthetic secrets in every form the review reproduced; none may reach any API payload.
SECRETS=['wss://rpc.example/v2/SYNTHETIC_CREDENTIAL_A','HTTPS://rpc.example/v2/SYNTHETIC_CREDENTIAL_B',
         'MNEMONIC="alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima"',
         'PRIVATE_KEY: SYNTHETIC_PRIVATE_VALUE','{"api_key": "SYNTHETIC_JSON_VALUE", "next": "SYNTHETIC_TAIL"}',
         "seed_phrase = 'SYNTHETIC quoted words'",'HELIUS_API_KEY = SYNTHETIC spaced value','Authorization: Bearer SYNTHETIC_BEARER',
         'ws://127.0.0.1:8899/SYNTHETIC_LOCAL_RPC']
SECRETS += [name + '=SYNTHETIC_VALUE public tail' for name in (
    'TOKEN', 'KEY', 'AUTH', 'CUSTOM_TOKEN_SUFFIX', 'SECRET', 'PASSWORD', 'MNEMONIC',
    'SEED', 'PRIVATE', 'API_KEY', 'BEARER', 'PREFIX_KEY_SUFFIX', 'TOKEN_PREFIX',
    'RPC', 'URL')]
SECRETS += ['tokenId=817 pool=0xabc TOKEN=SYNTHETIC_AFTER_PUBLIC',
            'Authorization: Basic SYNTHETIC_BASIC public tail',
            'Bearer SYNTHETIC_INLINE public tail', 'sk-SYNTHETIC_INLINE public tail',
            'VERYLONGCUSTOMENDPOINTSCHEME+TLS://rpc.example/SYNTHETIC_LONG_SCHEME',
            # Prose forms with no single-word name before a separator.
            'Seed phrase: SYNTHETIC_SEED alpha bravo', 'mnemonic SYNTHETIC_PROSE alpha bravo lima',
            'wallet recovery words SYNTHETIC_RECOVERY', 'export backup-phrase=SYNTHETIC_BACKUP',
            # The mask sentinel is untrusted text: it must not shield a later secret on the same line.
            'prior [masked to end of line] mnemonic SYNTHETIC_BYPASS alpha bravo',
            'prior [masked to end of line] TOKEN=SYNTHETIC_BYPASS_ASSIGNMENT',
            '"mnemonic": "SYNTHETIC_QUOTED_PROSE alpha"']
LEAKS=('SYNTHETIC','bravo','lima','rpc.example','127.0.0.1')

class RedactionTests(unittest.TestCase):
    setUp=CollectorTests.setUp
    tearDown=CollectorTests.tearDown
    def assertClean(self,payload):
        text=json.dumps(payload)
        for leak in LEAKS: self.assertNotIn(leak,text)
    def test_shared_helper_masks_every_form_and_keeps_public_fields(self):
        for secret in SECRETS:
            with self.subTest(secret=secret):
                self.assertClean(c.clean(secret));self.assertClean(c.clean(c.rh_redact(secret)))
        kept='tokenId=817 gas 0.0001 ETH re-center; token_id: 5; pool=0xabc'
        self.assertEqual(c.clean(kept),kept);self.assertEqual(c.rh_redact(kept),kept)
        self.assertEqual(c.clean('first line ok\nPRIVATE_KEY=x y\nlast line ok'),'first line ok\nPRIVATE_KEY=[masked to end of line]\nlast line ok')
    def test_nested_secret_keys_and_public_identifiers_in_final_payload(self):
        profile=self.m/'p';memory=profile/'memories';memory.mkdir(parents=True);state=self.m/'s';state.mkdir()
        names=['mnemonic','seed','seed_phrase','private_key','secret','token','password','api_key','auth',
               'TOKEN','KEY','AUTH','CUSTOM_TOKEN_SUFFIX','PRIVATE','BEARER','Authorization']
        secrets={name: {'nested': ['SYNTHETIC_STRUCTURED_SECRET']} for name in names}
        public={'tokenId':'817','token_id':'818','TOKEN_ID':'819','pool':'pool-public',
                'pool_id':'pool-id-public','mint':'mint-public','address':'address-public',
                'public_key':'key-public','SOLANA_PUBLIC_KEY':'wallet-public',
                'token_address':'token-public','base_mint':'base-public'}
        evidence={'outer':[{'fields':secrets,'public':public}]}
        rows(memory/'dlmm_closes.jsonl',[{'position':'p','closed_at':2,'evidence':evidence}])
        with patch.object(c.subprocess,'run',runner()),patch.object(c,'bounded_run',rh_run()):
            d=c.collect(profile,state,1,('UTC',))
        result=next(e['evidence']['evidence']['outer'][0] for e in d['journal'] if e['stage']=='exit')
        self.assertEqual(result['fields'], {name:'[masked]' for name in names})
        self.assertEqual(result['public'],public)
        self.assertClean(d)
        public_line=' '.join(name+'='+value for name,value in public.items())
        self.assertEqual(c.clean(public_line),public_line)
        self.assertEqual(c.rh_redact(public_line),public_line)
        self.assertEqual(c.clean({'outer':[public]}),{'outer':[public]})

    def test_line_masking_keeps_following_public_lines(self):
        for name in ('TOKEN','KEY','AUTH','MNEMONIC','SEED','PRIVATE','BEARER','CUSTOM_TOKEN_SUFFIX'):
            with self.subTest(name=name):
                raw='public first\r\n'+name+'="SYNTHETIC value" public tail\r\ntokenId=817 mint=public\n'
                self.assertEqual(c.clean(raw),'public first\r\n'+name+'=[masked to end of line]\r\ntokenId=817 mint=public\n')

    def test_final_api_composition_for_every_log_panel(self):
        """collect() is exactly what the Go server caches and serves: journal evidence, Robinhood logs,
        close reasons, failed-close reasons on open positions and stranded reasons all pass through it."""
        profile=self.m/'p';memory=profile/'memories';memory.mkdir(parents=True);state=self.m/'s';state.mkdir()
        rows(state/'solana_rejects.jsonl',[{'ts':1,'reason':s,'gate':'g'} for s in SECRETS])
        rows(memory/'dlmm_closes.jsonl',[{'position':'p','closed_at':2,'reason':s,'error':s} for s in SECRETS])
        rows(memory/'uni_closes.jsonl',[{'ts':3,'tokenId':str(i),'success':i>0,'quote_symbol':'WETH','reason':s} for i,s in enumerate(SECRETS)]+
                                       [{'ts':3,'tokenId':'failed'+str(i),'success':False,'reason':secret} for i,secret in enumerate(SECRETS)])
        rows(memory/'uni_positions.jsonl',[{'tokenId':'failed'+str(i),'pool':'0xp','ts':1,'token0':'public-token','token1':'public-quote','quote':'public-quote'} for i in range(len(SECRETS))])
        rows(memory/'uni_stranded.jsonl',[{'ts':4,'tokenId':'99','token':'0x%d' % i,'symbol':'S','amount':'1','reason':s,'resolved':False} for i,s in enumerate(SECRETS)])
        # Hermes session metadata is another panel served from the same final payload.
        import sqlite3
        with sqlite3.connect(profile/'state.db') as db:
            db.execute('CREATE TABLE sessions (id, source, model, started_at, ended_at, end_reason, message_count, tool_call_count, chat_id)')
            db.executemany('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)',
                [(str(i),secret,secret,1,None,secret,0,0,'') for i,secret in enumerate(SECRETS)])
        log=[(10+i,s) for i,s in enumerate(SECRETS)]
        def log_run(argv, **kwargs):
            if argv[0]=='journalctl' and 'azimuth.service' in argv and 'scanner: started' not in argv:
                return SimpleNamespace(stdout=''.join(json.dumps({'MESSAGE':'scanner[rh-turnover]: '+secret,
                    '__REALTIME_TIMESTAMP':str((100+i)*1000000)})+'\n' for i,secret in enumerate(SECRETS)),
                    stderr='',returncode=0,capture_status='ok')
            return rh_run(log=log)(argv, **kwargs)
        with patch.object(c.subprocess,'run',runner()),patch.object(c,'bounded_run',log_run):
            d=c.collect(profile,state,1,('UTC','America/Sao_Paulo'))
        rh=d['robinhood']
        self.assertEqual(len(rh['logs']),2*len(SECRETS));self.assertEqual(len(rh['stranded']['open']),len(SECRETS))
        self.assertEqual({row['unit'] for row in rh['logs']},{'azimuth.service','azimuth-rh-monitor.service'})
        self.assertEqual(len(rh['positions']),len(SECRETS))
        self.assertTrue(all(p['last_failed_close']['reason'] for p in rh['positions']))
        self.assertTrue(d['hermes']['sessions'])
        self.assertTrue(all(p['token_address']=='public-token' and p['token']=='[masked]' for p in rh['positions']))
        self.assertEqual({p['token_address'] for p in rh['stranded']['open']},{'0x%d' % i for i in range(len(SECRETS))})
        self.assertTrue(any(e['stage']=='gate' for e in d['journal']));self.assertTrue(any(e['stage']=='exit' for e in d['journal']))
        self.assertEqual(len(d['by_tz']['UTC']['robinhood']['closes']),len(SECRETS)-1)
        self.assertClean(d)
        with patch.object(c.subprocess,'run',runner()),patch.object(c,'bounded_run',rh_run(log=log)):
            self.assertClean(c.clean(c.daily(profile,1,('Asia/Tokyo',))))  # the per-zone refresh path

class RobinhoodReviewTests(unittest.TestCase):
    setUp=CollectorTests.setUp
    tearDown=CollectorTests.tearDown
    def test_missing_or_unsupported_quote_asset_is_never_summed(self):
        rows(self.m/'uni_closes.jsonl',[
            {'ts':86400,'tokenId':'1','success':True,'realized_quote':1,'pnl_basis':'realized'},
            {'ts':86400,'tokenId':'2','success':True,'quote_symbol':'UNSUPPORTED','realized_quote':100,'pnl_basis':'realized'},
            {'ts':86400,'tokenId':'3','success':True,'quote_symbol':None,'realized_quote':5,'pnl_basis':'realized'},
            {'ts':86400,'tokenId':'4','success':True,'quote_symbol':'weth','realized_quote':0.5,'pnl_basis':'realized'}])
        d=c.rh_closes(self.m)
        unknown=d['totals']['unknown']
        self.assertEqual((unknown['closes'],unknown['measured'],unknown['unmeasured'],unknown['realized_quote']),(3,0,3,None))
        self.assertEqual(d['totals']['ETH']['realized_quote'],0.5)
        self.assertIsNone(d['days']['1970-01-02']['unknown']['realized_quote'])
        row=next(r for r in d['closes'] if r['token_id']=='2')
        self.assertIsNone(row['realized_quote']);self.assertEqual(row['unit_unknown_value'],100)  # evidence, not money
    def test_stranded_pool_join_keeps_the_protocol(self):
        rows(self.m/'uni_positions.jsonl',[{'tokenId':'1','pool':'pool-v3','ts':1}])
        rows(self.m/'uni_v4_positions.jsonl',[{'tokenId':'1','protocol':'v4','pool':'pool-v4','ts':1}])
        rows(self.m/'uni_stranded.jsonl',[{'ts':2,'tokenId':'1','token':'0xA','symbol':'A','amount':'1','resolved':False}])
        rows(self.m/'uni_v4_stranded.jsonl',[{'ts':3,'tokenId':'1','token':'0xB','symbol':'B','amount':'2','resolved':True,'quote_out':'0.2','quote_symbol':'ETH'}])
        st=c.robinhood(self.m,10,run=rh_run())['stranded']
        self.assertEqual([(r['protocol'],r['symbol'],r['pool']) for r in st['open']],[('v3','A','pool-v3')])
        self.assertEqual([(r['protocol'],r['pool'],r['quote_out'],r['quote']) for r in st['resolved']],[('v4','pool-v4','0.2','ETH')])
    def test_fifo_and_symlink_journals_are_refused_without_blocking(self):
        import signal
        def stop(*a): raise AssertionError('collector blocked on a non-regular file')
        old=signal.signal(signal.SIGALRM,stop);signal.alarm(10)
        try:
            os.mkfifo(self.m/'uni_stranded.jsonl')
            real=self.m/'real.jsonl';rows(real,[{'ts':1,'token':'0xA','resolved':False}])
            (self.m/'uni_v4_stranded.jsonl').symlink_to(real)
            os.mkfifo(self.m/'uni_closes.jsonl')
            out=c.robinhood(self.m,10,run=rh_run())
            self.assertEqual([s['status'] for s in out['stranded']['sources']],['unavailable','unavailable'])
            self.assertEqual(out['stranded']['open'],[])
            self.assertEqual(c.rh_closes(self.m)['status'],'unavailable')
            rows_,meta=c.tail(self.m/'uni_stranded.jsonl');self.assertEqual((rows_,meta['status']),([],'unavailable'))
            self.assertEqual(c.tail(self.m/'absent.jsonl')[1]['status'],'missing')
            os.mkfifo(self.m/'report.json')
            with self.assertRaises(OSError): c.read_json(self.m/'report.json')
        finally:
            signal.alarm(0);signal.signal(signal.SIGALRM,old)

if __name__=='__main__': unittest.main()
