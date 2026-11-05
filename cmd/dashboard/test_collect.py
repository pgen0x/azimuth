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

def frozen_clock():
    """nav_at stops after 2 s of wall-clock time. That budget is real time, so on a slow or loaded host a
    large-file fixture could stop early and prove nothing (this flaked in CI). Fixtures that test ordering
    logic freeze the clock; the read-call and byte caps still apply unchanged."""
    return patch.object(c.time,'monotonic',return_value=0.0)

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
        with frozen_clock():ns=c.north_star(self.m,base+3*day+20*3600,days=3,tz='America/Sao_Paulo')
        full=[d for d in ns['days'] if d['status']=='ok']
        self.assertEqual(len(full),3);self.assertEqual(ns['days'][-1]['status'],'partial_day')
        for d in ns['days'][1:]:
            self.assertAlmostEqual(d['d_cash_sol'],.01);self.assertEqual(d['source']['ordering_assumption'],'visited_window_monotonic')
    def test_inversion_next_to_the_pick_is_partial(self):
        rows=[dict(ts=100*i,native_sol=1.0) for i in range(120)]
        rows.insert(21,dict(ts=1,native_sol=9.0))  # out-of-order neighbour right after the pick for t=2000
        self._big_nav(rows)
        with frozen_clock():meta={};row=c.nav_at(self.m/'dlmm_nav.jsonl',2000,meta=meta)
        self.assertIn(row['ts'],(1,2000));self.assertEqual(meta['status'],'partial');self.assertTrue(meta['out_of_order'])
        with frozen_clock():meta={};c.nav_at(self.m/'dlmm_nav.jsonl',500,meta=meta)  # inversion far from this pick
        self.assertEqual(meta['status'],'ok')
    def test_neighbour_lines_catch_an_unvisited_inversion(self):
        # Found by search: the binary search never visits the inverted row; only the +1 neighbour read sees it.
        rows=[dict(ts=100*i,native_sol=1.0) for i in range(120)]
        rows.insert(20,dict(ts=1850,native_sol=2.0))
        self._big_nav(rows)
        with frozen_clock():meta={};c.nav_at(self.m/'dlmm_nav.jsonl',1900,meta=meta)
        self.assertEqual(meta['status'],'partial');self.assertTrue(meta['out_of_order'])
    def _backscan_counterexample(self,base=0):
        """Codex fix3 P1 probe: 300 rows / ~4.8 MB; one row that only previous()'s backward scan
        reads is moved past the cutoff. Returns (rows, changed index, cutoff, reads, spy)."""
        rows=[dict(ts=base+i*100,native_sol=1.0,lp_mark_sol=0.0,refundable_rent_sol=0.0,
                   known_asset_subtotal_sol=1.0,external_flow_lamports=0) for i in range(300)]
        cutoff=base+15090
        def write():
            with (self.m/'dlmm_nav.jsonl').open('w') as h:
                for r in rows: h.write(json.dumps(dict(r,pad='x'*16000))+'\n')
        original=c._nav_line;reads=[]
        def in_previous():
            frame=sys._getframe(1)
            while frame is not None:
                if frame.f_code.co_name=='previous': return True
                frame=frame.f_back
            return False
        def spy(*a,**k):
            item=original(*a,**k)
            if item: reads.append((item[0],item[2],in_previous()))
            return item
        write()
        probe={}
        with patch.object(c,'_nav_line',side_effect=spy),frozen_clock():c.nav_at(self.m/'dlmm_nav.jsonl',cutoff,meta=probe)
        self.assertEqual(probe['status'],'ok',probe)  # a lookup cut short by a budget proves nothing
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
        with patch.object(c,'_nav_line',side_effect=spy),frozen_clock():c.nav_at(self.m/'dlmm_nav.jsonl',cutoff,meta=meta)
        self.assertIn(15050,[ts for _,ts,prev in reads if prev])  # the inversion was read, by previous()
        self.assertEqual(meta['status'],'partial');self.assertTrue(meta['out_of_order']);self.assertTrue(c.incomplete(meta))
        self.assertEqual(meta['visited_rows'],len({off for off,_,_ in reads}))  # every row read is checked
        self.assertLess(meta['read_calls'],c.NAV_LOOKUP_READS);self.assertLess(meta['read_bytes'],c.NAV_LOOKUP_BYTES)
    def test_backward_scan_inversion_blocks_the_next_days_delta(self):
        day=20000;end=day*86400-7*3600+86400  # end of a local day in Asia/Jakarta (UTC+7)
        rows,changed,cutoff,reads,spy=self._backscan_counterexample(base=end-1-15090)
        with frozen_clock():ns=c.north_star(self.m,cutoff+14000,days=1,tz='Asia/Jakarta')
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
    def test_nav_wall_clock_budget_still_stops_a_slow_lookup(self):
        rows=[dict(ts=100*i,native_sol=1.0) for i in range(120)]
        self._big_nav(rows)
        import itertools
        clock=itertools.count(0,0.5)  # every clock read is half a second later
        with patch.object(c.time,'monotonic',side_effect=lambda:next(clock)):
            meta={};self.assertIsNone(c.nav_at(self.m/'dlmm_nav.jsonl',2000,meta=meta))
        self.assertEqual(meta['status'],'work_cap')
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

def jlines(msgs): return '\n'.join(json.dumps({'MESSAGE':m,'__REALTIME_TIMESTAMP':str(int(t*1e6))}) for t,m in msgs)+'\n'

def brief_run(monitor=(), scanner=(), ticks=(), units=None, failed=''):
    """Fake bounded_run: answers each fixed argv from synthetic journals; no live service is read."""
    units=units if units is not None else '\n\n'.join(f'Id={u}\nActiveState=active\nSubState=running\nUnitFileState=enabled' for u in c.CORE_UNITS)
    calls=[]
    def run(argv,**kw):
        calls.append(argv); out=''
        if argv[:3]==['systemctl','--user','show']: out=units
        elif 'list-units' in argv: out=failed
        elif 'azimuth.service' in argv: out=jlines(scanner)
        elif '^OBSERVER_TICK' in argv: out=jlines(ticks)
        elif 'azimuth-sol-monitor.service' in argv and '--grep' in argv: out=jlines(monitor)
        elif 'azimuth-sol-monitor.service' in argv: out=jlines(ticks)
        return SimpleNamespace(stdout=out,stderr='',returncode=0,capture_status='ok')
    run.calls=calls
    return run

REPORT='MONITOR_REPORT:'+json.dumps({'positions':[{'position':'pos-1','pair':'AAA-SOL','mode':'pulse','age_minutes':5,'pnl_pct':-1.5,'pnl_sol':-.0015,'in_range':False,'oor_minutes':3,'size_sol':.1}]})

class BriefTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);self.m=self.p/'memories';self.m.mkdir()
        self.net=patch.object(socket.socket,'connect',side_effect=AssertionError('offline only'));self.net.start()
    def tearDown(self): self.net.stop();self.tmp.cleanup()

    def test_positions_from_latest_report(self):
        out=c.brief_positions(brief_run(monitor=[(T-30,'Meteora Portfolio API: 1 position(s) found on-chain'),(T-29,REPORT)]),T)
        self.assertEqual(out['status'],'ok');self.assertEqual(len(out['positions']),1)
        p=out['positions'][0];self.assertEqual((p['pair'],p['in_range'],p['pnl_sol']),('AAA-SOL',False,-.0015))
        self.assertIn('MARK',out['basis'])
    def test_positions_newer_zero_count_wins_and_order_is_not_trusted(self):
        # Delivered newest-first, as journalctl --grep was observed to do.
        msgs=[(T-10,'Meteora Portfolio API: 0 position(s) found on-chain'),(T-60,REPORT)]
        out=c.brief_positions(brief_run(monitor=msgs),T)
        self.assertEqual((out['positions'],out['onchain_count']),([],0))
    def test_positions_without_report(self):
        self.assertEqual(c.brief_positions(brief_run(),T)['status'],'no_report')
        bad=c.brief_positions(brief_run(monitor=[(T-5,'MONITOR_REPORT:{broken')]),T)
        self.assertEqual((bad['status'],bad['positions']),('invalid_report',[]))

    def test_closes_join_realized_never_mark(self):
        rows(self.m/'dlmm_closes.jsonl',[
            dict(ts=T-100,position='a',pair='A-SOL',mode='pulse',reason='first try',pnl_sol=9.0,event='exit'),
            dict(ts=T-50,position='a',pair='A-SOL',mode='pulse',reason='Low yield',age_min=30,pnl_sol=9.0,event='exit'),
            dict(ts=T-40,position='b',pair='B-SOL',mode='turnover',reason='SL',pnl_sol=-9.0),
            dict(ts=T-30,position='c',pair='C-SOL',mode='pulse',reason='OOR',pnl_sol=1.0),
            dict(ts=T-20,position='a',event='compound',pnl_sol=5.0),
            dict(ts=T-5*DAY,position='old',pair='O-SOL',mode='pulse',reason='x')])
        rows(self.m/'dlmm_realized.jsonl',[dict(position='a',realized_sol=.002),dict(position='b',realized_sol=None)])
        out=c.brief_closes(self.m,T,12,10)
        got={r['position']:(r['realized_sol'],r['pnl_basis'],r['reason']) for r in out['recent']}
        self.assertEqual(got['a'],(.002,'realized','Low yield'))
        self.assertEqual(got['b'],(None,'unmeasured','SL'))
        self.assertEqual(got['c'],(None,'not_reconciled','OOR'))
        self.assertEqual([r['position'] for r in out['recent']],['c','b','a','old'])
        self.assertEqual((out['window_closes'],out['window_measured'],out['window_realized_sol']),(3,1,.002))
        self.assertNotIn('pnl_sol',json.dumps(out['recent']))
        self.assertEqual(len(c.brief_closes(self.m,T,12,2)['recent']),2)

    def test_funnel_counts(self):
        scanner=[(T-60,'scanner[pulse]: SIGNAL batch sent 2 pools: A(80), B(70)'),(T-50,'scanner[pulse]: SIGNAL batch sent 1 pools: C(60)'),
                 (T-49,'scanner[pulse]: entry_route=hermes_ai probe_cached=false; AI probe passed'),
                 (T-48,'scanner[pulse]: entry_route=deterministic_fallback reason=timeout probe_cached=false; batch not sent'),
                 (T-47,'scanner[pulse]: X (abc) rejected on audit: bot holders 40.1% > 25%'),
                 (T-46,'scanner[pulse]: Y (abd) rejected on audit: bot holders 31% > 25%'),
                 (T-45,'scanner[pulse]: CHOO (9JZ) in re-entry cooldown (3m2s left)'),
                 (T-44,'scanner[pulse]: direct deploy done (deployed=false) for A(80)')]
        rows(self.m/'dlmm_pipeline_rejects.jsonl',[dict(ts=T-30,gate='downtrend_h6'),dict(ts=T-20,gate='downtrend_h6'),dict(ts=T-13*3600,gate='old')])
        rows(self.m/'dlmm_transactions.jsonl',[dict(ts=T-40,kind='deploy'),dict(ts=T-35,kind='swap'),dict(ts=T-20*3600,kind='deploy')])
        run=brief_run(scanner=scanner)
        f=c.brief_funnel(self.m,run,T,12)
        self.assertEqual((f['batches'],f['batch_pools'],f['deploys'],f['last_deploy_ts']),(2,3,1,T-40))
        self.assertEqual(f['routes'],{'hermes_ai':1,'deterministic_fallback:timeout':1})
        self.assertEqual(f['daemon_rejects'],{'audit: bot holders N% > N%':2,'re-entry cooldown':1})
        self.assertEqual(f['pipeline_rejects'],{'downtrend_h6':2})
        self.assertEqual(f['direct_deploy'],{'deployed':0,'not_deployed':1})
        argv=next(a for a in run.calls if 'azimuth.service' in a)
        self.assertEqual(argv[argv.index('--since')+1],'@%d'%(T-12*3600))

    def test_alerts(self):
        healthy={'units':[{'unit':u,'active':'active','enabled':'enabled'} for u in c.CORE_UNITS],'failed_units':[],'disk_free_pct':50,'mem_available_mb':4000,'monitor_tick_age_s':10}
        self.assertEqual(c.brief_alerts(healthy,{'last_deploy_ts':T-3600},T),[])
        bad=dict(healthy,disk_free_pct=9.5,mem_available_mb=800,monitor_tick_age_s=500,failed_units=['azimuth-sol-monitor.service','x.timer'],
                 units=[dict(healthy['units'][0],active='failed'),dict(healthy['units'][1],enabled='disabled')]+healthy['units'][2:])
        codes={a['code'] for a in c.brief_alerts(bad,{'last_deploy_ts':T-13*3600},T)}
        self.assertEqual(codes,{'disk_low','mem_low','core_unit_down','core_unit_not_enabled','failed_core_unit','failed_units','no_deploy_12h','monitor_tick_stale'})
        codes={a['code'] for a in c.brief_alerts(dict(healthy,monitor_tick_age_s=None,units=[]),{},T)}
        self.assertEqual(codes,{'monitor_tick_unknown','no_deploy_12h','core_unit_missing'})

    def test_alerts_carry_ids_and_rent_rule(self):
        healthy={'units':[{'unit':u,'active':'active','enabled':'enabled'} for u in c.CORE_UNITS],'failed_units':[],'disk_free_pct':50,'mem_available_mb':4000,'monitor_tick_age_s':10}
        down=dict(healthy,units=[dict(healthy['units'][0],active='failed'),dict(healthy['units'][1],active='failed')]+healthy['units'][2:])
        ids={a['id'] for a in c.brief_alerts(down,{'last_deploy_ts':T},T)}
        self.assertEqual(ids,{'core_unit_down:'+c.CORE_UNITS[0],'core_unit_down:'+c.CORE_UNITS[1]})
        rent=dict(healthy,rent_unit={'load':'loaded','active':'failed','result':'exit-code'},failed_units=[c.RENT_UNIT])
        self.assertEqual({a['code'] for a in c.brief_alerts(rent,{'last_deploy_ts':T},T)},{'rent_failing'})
        for ok in ({'load':'loaded','active':'inactive','result':'success'},{'load':'not-found','active':'inactive','result':'success'},None):
            self.assertEqual(c.brief_alerts(dict(healthy,rent_unit=ok),{'last_deploy_ts':T},T),[])
        # The unattended floor is the OOM line, not the brief's heavy-step line.
        self.assertEqual(c.brief_alerts(dict(healthy,mem_available_mb=1000),{'last_deploy_ts':T},T,mem_min=c.ALERT_MEM_MIN_MB),[])
        self.assertEqual([a['code'] for a in c.brief_alerts(dict(healthy,mem_available_mb=700),{'last_deploy_ts':T},T,mem_min=c.ALERT_MEM_MIN_MB)],['mem_low'])

    def test_rent_unit_read_from_its_own_show(self):
        base=brief_run()
        def run(argv,**kw):
            if argv[:4]==['systemctl','--user','show',c.RENT_UNIT]:
                return SimpleNamespace(stdout='Id=%s\nLoadState=loaded\nActiveState=failed\nResult=exit-code\n'%c.RENT_UNIT,stderr='',returncode=0)
            return base(argv,**kw)
        h=c.brief_health(self.p,run,T,statvfs=lambda _:SimpleNamespace(f_bavail=50,f_blocks=100),meminfo='/nonexistent')
        self.assertEqual(h['rent_unit'],{'load':'loaded','active':'failed','result':'exit-code'})
        self.assertNotIn('rent_unit',c.brief_health(self.p,base,T,statvfs=lambda _:SimpleNamespace(f_bavail=50,f_blocks=100),meminfo='/nonexistent'))

    def test_markers_stale_by_mtime_and_settlement_by_close(self):
        P='P'*40
        for d in c.MARKER_DIRS: (self.m/d).mkdir()
        def put(d,name,age):
            f=self.m/d/(name+'.json'); f.write_text('{}'); os.utime(f,(T-age,T-age))
        put('dlmm_pending_swaps','old',3*DAY); put('dlmm_pending_swaps','new',60); put('dlmm_pending_deploys','fresh',600)
        put('dlmm_settlements',P,30)  # rewritten on every retry, but its close is 5 days old
        rows(self.m/'dlmm_closes.jsonl',[dict(ts=T-5*DAY,position=P,reason='x'),dict(ts=T-60,position=P,reason='retry row')])
        out=c.brief_markers(self.m,T)
        self.assertEqual(out['total'],4)
        self.assertEqual(out['stale'],{'dlmm_pending_swaps':{'count':1,'oldest_s':3*DAY},'dlmm_settlements':{'count':1,'oldest_s':5*DAY}})
        msg=[a for a in c.brief_alerts({'units':[{'unit':u,'active':'active','enabled':'enabled'} for u in c.CORE_UNITS],'monitor_tick_age_s':1},{'last_deploy_ts':T},T,out)]
        self.assertEqual([a['code'] for a in msg],['marker_stale'])
        self.assertIn('dlmm_pending_swaps 1 (oldest 3.0d)',msg[0]['message'])
        self.assertEqual(c.brief_markers(self.m/'absent',T)['stale'],{})
        # A settlement that records queued_at needs no close journal row.
        Q='Q'*40; f=self.m/'dlmm_settlements'/(Q+'.json')
        f.write_text(json.dumps({'queued_at':T-2*DAY})); os.utime(f,(T-30,T-30))
        self.assertEqual(c.brief_markers(self.m,T)['stale']['dlmm_settlements'],{'count':2,'oldest_s':5*DAY})

    def test_alerts_mode_offline(self):
        rows(self.m/'dlmm_transactions.jsonl',[dict(ts=T-60,kind='deploy'),dict(ts=T-30,kind='swap')])
        mem=self.p/'meminfo';mem.write_text('MemAvailable:    1024000 kB\n')
        vfs=SimpleNamespace(f_bavail=50,f_blocks=100)
        out=c.alerts(self.p,now=T,run=brief_run(ticks=[(T-15,'OBSERVER_TICK {}')]),statvfs=lambda _:vfs,meminfo=str(mem))
        self.assertEqual(out['alerts'],[]);self.assertEqual(out['funnel']['last_deploy_ts'],T-60)
        broken=c.alerts(self.p,now=T,run=lambda *a,**k:1/0,statvfs=lambda _:vfs,meminfo=str(mem))
        self.assertIn('section_unavailable:health',{a['id'] for a in broken['alerts']})
        json.dumps(c.scrub(out),allow_nan=False)
        self.assertIn('id',json.dumps(c.scrub(broken)))

    def test_brief_end_to_end_offline(self):
        rows(self.m/'dlmm_nav.jsonl',[snap(T-DAY-60,1,native=1.0),snap(T-60,2,native=1.5)])
        rows(self.m/'dlmm_transactions.jsonl',[dict(ts=T-60,kind='deploy')])
        vfs=SimpleNamespace(f_bavail=10,f_blocks=100)
        mem=self.p/'meminfo';mem.write_text('MemTotal: 8000000 kB\nMemAvailable:    2048000 kB\n')
        out=c.brief(self.p,now=T,hours=12,n=5,run=brief_run(ticks=[(T-15,'OBSERVER_TICK {}')],failed='a.service loaded failed failed A\n'),statvfs=lambda _:vfs,meminfo=str(mem))
        self.assertEqual(out['wallet']['native_sol'],1.5)
        self.assertEqual((out['health']['disk_free_pct'],out['health']['mem_available_mb'],out['health']['monitor_tick_age_s']),(10.0,2000,15))
        self.assertEqual(out['health']['failed_units'],['a.service'])
        self.assertEqual({a['code'] for a in out['alerts']},{'disk_low','failed_units'})
        json.dumps(c.clean(out),allow_nan=False)
        broken=c.brief(self.p,now=T,run=lambda *a,**k:1/0,statvfs=lambda _:vfs,meminfo=str(mem))
        self.assertIn('section_unavailable',{a['code'] for a in broken['alerts']})
        self.assertIn('today',out);self.assertIn('realized_7d',out)
        self.assertIn('entry_funnel',out);self.assertEqual(len(out['entry_funnel']['windows']),2)

    def test_entry_funnel_windows(self):
        A,B,C='A'*40,'B'*40,'C'*40
        scanner=[(T-7200,'scanner[pulse]: SIGNAL batch sent 2 pools: A(80), B(70)'),(T-7199,'scanner[pulse]: entry_route=hermes_ai probe_cached=false; AI probe passed'),
                 (T-600,'scanner[pulse]: entry_route=deterministic_fallback reason=timeout probe_cached=false; batch not sent'),
                 (T-590,'Batch reject X-SOL - conviction score 25.0 < 30 pulse floor'),(T-580,'Batch reject Y-SOL - conviction score 20.0 < 30 pulse floor'),
                 (T-90000,'scanner[pulse]: SIGNAL batch sent 9 pools: old')]
        rows(self.m/'dlmm_pipeline_rejects.jsonl',[dict(ts=T-500,gate='conviction_floor'),dict(ts=T-5000,gate='downtrend_h6'),dict(ts=T-90000,gate='old')])
        rows(self.m/'dlmm_transactions.jsonl',[dict(ts=T-100,kind='deploy',position=A),dict(ts=T-99,kind='deploy',position=A),
                                               dict(ts=T-5000,kind='deploy',position=B),dict(ts=T-6000,kind='deploy',position=C),dict(ts=T-50,kind='close',position=A)])
        rows(self.m/'dlmm_deploy_verifications.jsonl',[dict(ts=T-95,position=A,verified=True),dict(ts=T-4990,position=B,verified=False)])
        rows(self.m/'dlmm_report_guard.jsonl',[dict(ts=T-4980,executions=[dict(position=B,dry_run=False,execution_verified=True)])])
        out=c.entry_funnel(self.p,brief_run(scanner=scanner),T)
        day,hour=out['windows']
        self.assertEqual((day['batches'],day['batch_pools'],day['routes']),(1,2,{'hermes_ai':1,'deterministic_fallback':1}))
        self.assertEqual(day['fallback_reasons'],{'timeout':1})
        # Journal saw 2 conviction rejects, the jsonl 1: the larger wins, never the sum.
        self.assertEqual(day['rejects'],{'conviction_floor':2,'downtrend_h6':1})
        self.assertEqual(day['deploys'],{'total':3,'verified':2,'unverified':0,'unknown':1})
        self.assertEqual((hour['batches'],hour['rejects'],hour['deploys']['total'],hour['deploys']['verified']),(0,{'conviction_floor':2},1,1))
        self.assertEqual(out['ticket']['status'],'no_cash_policy')

    def test_entry_funnel_ticket_and_score_bands(self):
        pol=self.p/c.CASH_POLICY_PATH;pol.parent.mkdir(parents=True)
        pol.write_text(json.dumps(dict(version=1,native_reserve_lamports=50_000_000,entry_rent_allowance_lamports=15_000_000,minimum_entry_lamports=100_000_000)))
        entries=self.m/'dlmm_entries';entries.mkdir()
        since=T-3600
        def entry(pos,score,at):
            (entries/(pos+'.json')).write_text(json.dumps({'position':pos,'deployed_at':at,'risk_sizing':{'adjusted_score':score} if score is not None else None}))
            os.utime(entries/(pos+'.json'),(at,at))  # the collector prefilters entry files by mtime
        for pos,score,at in (('A'*40,45.0,T-100),('B'*40,69.9,T-90),('C'*40,70.0,T-80),('D'*40,None,T-70),('E'*40,90.0,T-7200)):
            entry(pos,score,at)
        rows(self.m/'dlmm_realized.jsonl',[dict(position='A'*40,realized_sol=-.002),dict(position='C'*40,realized_sol=.003),dict(position='E'*40,realized_sol=9.0)])
        out=c.entry_funnel(self.p,brief_run(),T,since,0.6,T-60)
        b=out['score_bands']['bands']
        self.assertEqual(b['<50'],{'n':1,'measured':1,'pending':0,'sum_sol':-.002,'mean_sol':-.002})
        self.assertEqual((b['50-70']['n'],b['50-70']['pending'],b['50-70']['sum_sol']),(1,1,None))
        self.assertEqual((b['>=70']['n'],b['>=70']['sum_sol']),(1,.003))  # E deployed before `since`
        self.assertEqual(b['unscored']['n'],1)
        t=out['ticket']
        self.assertEqual((t['base_ticket_sol'],t['minimum_entry_sol']),(0.1,0.1))  # 0.55*0.45 < 0.3 floor -> minimum ticket
        # A minimum-sized base ticket clears only once round(0.1*mult,2) reaches 0.10: mult 0.95, 36 points over the floor.
        self.assertEqual(t['min_score']['pulse'],{'floor':30.0,'min_score':66.0})
        self.assertEqual(c.entry_funnel(self.p,brief_run(),T,since,0.1)['ticket']['min_score']['pulse']['min_score'],None)

    def test_ticket_math_matches_pipeline(self):
        scripts=Path(__file__).resolve().parents[2]/'assets/skill/scripts'
        sys.path.insert(0,str(scripts))
        try: import dlmm_pipeline as pipeline
        except Exception as e: self.skipTest('pipeline import unavailable: %r'%e)
        finally: sys.path.remove(str(scripts))
        self.assertEqual(c.CONVICTION_FLOOR,pipeline.BATCH_CONVICTION_FLOOR)
        pol=pipeline.CASH_POLICY;minimum=pol['minimum_entry_lamports']/1e9
        for i in range(0,1200,7):
            w=i/100
            self.assertEqual(c.deploy_ticket(w,pol),pipeline.compute_deploy_amount(w),w)
            base=c.deploy_ticket(w,pol)
            for mode,floor in c.CONVICTION_FLOOR.items():
                for s in (floor-1,floor,floor+7.3,floor+20,floor+39.9,floor+50):
                    self.assertEqual(c.risk_ticket(base,s,floor,minimum) if s>=floor else 0.0,
                                     pipeline.risk_scaled_ticket(base,s,mode)[0] if s>=floor else 0.0,(w,mode,s))
                m=c.min_clearing_score(base,floor,minimum)
                if m is not None:
                    self.assertGreater(pipeline.risk_scaled_ticket(base,m,mode)[0],0)
                    if m>floor: self.assertEqual(pipeline.risk_scaled_ticket(base,round(m-0.1,1),mode)[0],0.0)

    def test_realized_by_mode_and_route(self):
        A,B,C,D,E='A'*40,'B'*40,'C'*40,'D'*40,'E'*40
        entries=self.m/'dlmm_entries';entries.mkdir()
        (entries/(A+'.json')).write_text(json.dumps({'risk_sizing':{'source':'from_batch'}}))
        (entries/(B+'.json')).write_text(json.dumps({'risk_sizing':{'source':'from_signal'}}))
        (entries/(C+'.json')).write_text(json.dumps({'mode':'pulse'}))  # pre-provenance entry
        rows(self.m/'dlmm_closes.jsonl',[dict(ts=T-100,position=A,mode='pulse'),dict(ts=T-90,position=B,mode='turnover'),
                                         dict(ts=T-80,position=C,mode='pulse'),dict(ts=T-70,position=D,mode='pulse')])
        rows(self.m/'dlmm_realized.jsonl',[dict(position=A,closed_at=T-100,realized_sol=.002),dict(position=B,closed_at=T-90,realized_sol=-.001),
                                           dict(position=C,closed_at=T-80,realized_sol=None),dict(position=D,closed_at=T-70,realized_sol=.004),
                                           dict(position=E,closed_at=T-8*DAY,realized_sol=9.0)])
        out=c.brief_realized(self.m,T)
        self.assertEqual(out['by_mode']['pulse'],{'n':3,'measured':2,'sum_sol':.006,'mean_sol':.003})
        self.assertEqual(out['by_mode']['turnover']['sum_sol'],-.001)
        r=out['by_route']
        self.assertEqual((r['deterministic']['sum_sol'],r['ai']['sum_sol'],r['no_entry_file']['sum_sol']),(.002,-.001,.004))
        self.assertEqual(r['unknown'],{'n':1,'measured':0,'sum_sol':None,'mean_sol':None})  # unmeasured is never 0
        self.assertNotIn(9.0,[x['sum_sol'] for x in out['by_mode'].values()])

    def test_today_native_delta_and_rent(self):
        wallet={'as_of':T-60,'days':[{'day':'d1','status':'ok','native_sol':1.0},{'day':'d2','status':'partial_day','native_sol':1.25,'d_external_sol':0.0}]}
        rent=dict(status='ok',executed_tx=2,rent_recovered_lamports=200_000_000,liquid_native_gain_sol=.199,
                  verified_subtotal={'rent_recovered_lamports':200_000_000,'transactions':2},source_metadata={'journal':{'status':'ok'}})
        with patch.object(c,'dust_ledger',return_value=rent) as ledger:
            out=c.brief_today(wallet,self.m,T,'UTC',None)
        self.assertEqual(ledger.call_args[0][1],c.day_start(c.local_day(T,c.zone('UTC')),c.zone('UTC')))
        self.assertAlmostEqual(out['native_delta_sol'],.25);self.assertAlmostEqual(out['rent_reclaimed_sol'],.2)
        self.assertAlmostEqual(out['native_delta_ex_rent_sol'],.051);self.assertEqual(out['native_as_of'],T-60)
        with patch.object(c,'dust_ledger',return_value=dict(rent,rent_recovered_lamports=None,liquid_native_gain_sol=None,status='partial',
                                                           verified_subtotal={'rent_recovered_lamports':100_000_000,'transactions':1})):
            out=c.brief_today({'days':[{'native_sol':1.0}]},self.m,T,'UTC',None)
        self.assertEqual((out['native_delta_sol'],out['rent_reclaimed_sol'],out['native_delta_ex_rent_sol']),(None,None,None))
        self.assertEqual((out['rent_verified_subtotal_sol'],out['rent_verified_tx']),(.1,1))

POS='Pos1111111111111111111111111111111111111'
POOL='PooL111111111111111111111111111111111111'
POOL2='PooL222222222222222222222222222222222222'

def trace_run(scanner=(), monitor_reports=(), cooldown_set=(), cooldown_hits=()):
    """Fake bounded_run for trace: answers by unit and --grep pattern, honours --since/--until like journalctl."""
    calls=[]
    def run(argv,**kw):
        calls.append(argv); g=argv[argv.index('--grep')+1] if '--grep' in argv else ''
        lo=float(argv[argv.index('--since')+1][1:]) if '--since' in argv else 0
        hi=float(argv[argv.index('--until')+1][1:]) if '--until' in argv else 9e18
        if 'azimuth.service' in argv: msgs=cooldown_hits if g=='re-entry cooldown' else scanner
        elif g.startswith('^MONITOR_REPORT'): msgs=monitor_reports
        else: msgs=cooldown_set
        return SimpleNamespace(stdout=jlines([(t,m) for t,m in msgs if lo<=t<=hi]) if msgs else '',stderr='',returncode=0,capture_status='ok')
    run.calls=calls
    return run

def report(pnl,in_range=True,pos=POS):
    return 'MONITOR_REPORT:'+json.dumps({'positions':[{'position':'other','pnl_pct':-50},{'position':pos,'pnl_pct':pnl,'pnl_sol':pnl/1000,'in_range':in_range}]})

class TraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'prof';self.m=self.p/'memories';self.m.mkdir(parents=True)
        self.s=Path(self.tmp.name)/'state';self.s.mkdir()
        (self.m/'dlmm_entries').mkdir();(self.m/'dlmm_settlements').mkdir()
        self.net=patch.object(socket.socket,'connect',side_effect=AssertionError('offline only'));self.net.start()
        self.t0=T-3600;self.t1=T-1800
    def tearDown(self): self.net.stop();self.tmp.cleanup()

    def seed(self, source='from_signal'):
        t0,t1=self.t0,self.t1
        (self.m/'dlmm_entries'/(POS+'.json')).write_text(json.dumps({'pool':POOL,'pair':'NIO-SOL','base_symbol':'NIO','mode':'pulse','strategy':'sol_bidask',
            'size_sol':.1,'entry_id':'e1','deployed_at':t0,'entry_bin':-428,'bins_below':44,'bins_above':0,'bin_snapshot':{'bins':[1]*1000},
            'risk_sizing':{'source':source,'adjusted_score':90.5,'accepted_ticket_sol':.1},'active_bin_reanchor':{'cached':-430,'fresh':-428,'drift':2}}))
        rows(self.m/'dlmm_closes.jsonl',[dict(ts=t1,position=POS,pool=POOL,pair='NIO-SOL',mode='pulse',reason='Low yield',pnl_pct=1.0,pnl_sol=.001,
                                              age_min=30,ai_holds=1,txs=['x'],event='exit',pnl_basis='pre_swap_mark'),
                                         dict(ts=t1-100,position='other',pool=POOL2,pair='NIO-SOL',mode='pulse',reason='SL')])
        rows(self.m/'dlmm_realized.jsonl',[dict(position=POS,pool=POOL,pair='NIO-SOL',closed_at=t1,created_at=t0,realized_sol=.0012,fetched_at=t1+600)])
        rows(self.m/'dlmm_pipeline_rejects.jsonl',[dict(ts=t0-600,pool=POOL,gate='downtrend_h6',mode='pulse',name='NIO-SOL'),
                                                   dict(ts=t0-9*3600,pool=POOL,gate='old',mode='pulse',name='NIO-SOL'),
                                                   dict(ts=t0-600,pool=POOL2,gate='other_pool',mode='pulse',name='NIO-SOL')])
        (self.m/'dlmm_settlements'/(POS+'.json')).write_text(json.dumps({'state':'deferred','reason':'swap_no_route','last_attempt':t1+60}))
        sig=lambda pools:{'payload':[{'pool':p,'base_symbol':s,'score':80,'mode':'pulse'} for p,s in pools]}
        rows(self.s/'solana_deliveries.jsonl',[dict(delivery_id='old',observed_at=t0-3*3600,stage='prepared',signal=sig([(POOL,'NIO')])),
                                               dict(delivery_id='d1',observed_at=t0-20,stage='prepared',signal=sig([(POOL2,'X'),(POOL,'NIO')])),
                                               dict(delivery_id='d1',observed_at=t0-19,stage='accepted',http_status=202),
                                               dict(delivery_id='d2',observed_at=t0-10,stage='prepared',signal=sig([(POOL2,'X')]))])
        import base64,sqlite3
        ident=base64.urlsafe_b64encode(json.dumps(['prof','dlmm-signal','d1'],separators=(',',':')).encode()).decode().rstrip('=')
        with sqlite3.connect(self.p/'state.db') as db:
            db.execute('CREATE TABLE sessions (id TEXT, source TEXT, chat_id TEXT, started_at REAL, ended_at REAL, end_reason TEXT)')
            db.execute('CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, timestamp REAL)')
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?)',('s1','webhook','webhook:v2:'+ident,t0-18,None,None))
            db.executemany('INSERT INTO messages (session_id,role,content,timestamp) VALUES (?,?,?,?)',
                           [('s1','assistant','thinking',t0-15),('s1','assistant','Pick NIO\n'+'x'*500,t0-5),('s1','assistant','',t0-4),('s1','user','hi',t0-3)])

    def test_position_timeline_ai_route(self):
        self.seed(); t0,t1=self.t0,self.t1
        run=trace_run(
            scanner=[(t0-20,'scanner[pulse]: SIGNAL batch sent 2 pools: X(80), NIO(80)'),(t0-20,'scanner[pulse]: entry_route=hermes_ai probe_cached=false'),
                     (t0-20,'scanner[pulse]: SIGNAL batch sent 1 pools: ANIO(70)')],
            monitor_reports=[(t0+20,report(-2.0)),(t0+40,report(3.5,False)),(t0+60,report(1.0))],
            cooldown_set=[(t1+1,'🚫 Re-entry cooldown set for NIO: 1h (reason: normal exit)'),(t1+1,'🚫 Re-entry cooldown set for NIOX: 1h'),
                          (t1+1,'🚫 Pool cooldown set 4h (low yield): '+POOL),(t1+2,'🔴 REPEAT LOSS #2 in 7d — escalating NIO cooldown to 24h')],
            cooldown_hits=[(t1+60,'scanner[pulse]: NIO (PooL1111) in re-entry cooldown (59m left)'),(t1+120,'scanner[pulse]: NIO (PooL1111) in re-entry cooldown (58m left)'),
                           (t1+90,'scanner[pulse]: NIO (PooL2222) in re-entry cooldown (5m left)')])
        out=c.trace(self.p,self.s,POS,now=T,run=run)
        self.assertEqual((out['kind'],out['status']),('position','ok'))
        s=out['summary']
        self.assertEqual((s['route'],s['pool'],s['symbol'],s['realized_sol'],s['pnl_basis'],s['state']),('ai',POOL,'NIO',.0012,'realized','closed'))
        stages=[e['stage'] for e in out['events']]
        self.assertEqual(stages,['pipeline_reject','batch_sent','batch_logged','route','webhook_accepted','hermes_decision','entry','active_bin_reanchor',
                                 'monitor_ticks','close','cooldown_set','cooldown_set','cooldown_set','settlement','cooldown_blocked','realized'])
        ev={e['stage']:e for e in out['events']}
        self.assertEqual(ev['batch_sent']['delivery_id'],'d1');self.assertEqual(ev['batch_sent']['candidates'],2)
        self.assertEqual(ev['webhook_accepted']['http_status'],202)
        self.assertEqual(ev['route']['route'],'hermes_ai')
        self.assertTrue(ev['hermes_decision']['text'].startswith('Pick NIO x'));self.assertEqual(len(ev['hermes_decision']['text']),300)
        self.assertEqual(ev['pipeline_reject']['gate'],'downtrend_h6')
        self.assertEqual(ev['active_bin_reanchor']['drift'],2)
        self.assertNotIn('bin_snapshot',json.dumps(out))
        m=ev['monitor_ticks']
        self.assertEqual((m['ticks'],m['pnl_pct_min'],m['pnl_pct_max'],m['pnl_pct_max_at'],m['oor_ticks']),(3,-2.0,3.5,t0+40,1))
        self.assertEqual((ev['close']['mark_pnl_pct'],ev['close']['mark_basis'],ev['close']['ai_holds']),(1.0,'pre_swap_mark',1))
        self.assertNotIn('NIOX',json.dumps([e for e in out['events'] if e['stage']=='cooldown_set']))
        self.assertEqual(ev['cooldown_blocked']['count'],2)
        self.assertEqual(ev['settlement']['state'],'deferred')
        argv=next(a for a in run.calls if any(x.startswith('^MONITOR_REPORT') for x in a))
        self.assertIn('^MONITOR_REPORT:.*'+POS,argv)
        json.dumps(c.scrub(out),allow_nan=False)

    def test_position_deterministic_route_anchors_on_direct_deploy(self):
        self.seed('from_batch'); t0=self.t0
        (self.s/'solana_deliveries.jsonl').unlink()
        run=trace_run(scanner=[(t0-700,'scanner[pulse]: entry_route=hermes_ai probe_cached=false'),
                               (t0-15,'scanner[pulse]: entry_route=deterministic_fallback reason=command_timeout probe_cached=false; batch not sent to Hermes'),
                               (t0+10,'scanner[pulse]: direct deploy done (deployed=true) for NIO(69)')])
        out=c.trace(self.p,self.s,POS,now=T,run=run)
        ev={e['stage']:e for e in out['events']}
        self.assertEqual(out['summary']['route'],'deterministic')
        self.assertEqual((ev['route']['route'],ev['route']['fallback_reason'],ev['direct_deploy']['deployed']),('deterministic_fallback','command_timeout',True))
        self.assertNotIn('batch_sent',ev);self.assertNotIn('hermes_decision',ev)
        self.assertEqual(out['sources']['deliveries'],'missing')

    def test_symbol_and_pool_listing(self):
        self.seed()
        out=c.trace(self.p,self.s,'nio',now=T,run=trace_run())
        self.assertEqual((out['kind'],out['status']),('symbol','ok'))
        self.assertEqual({p['position'] for p in out['positions']},{POS,'other'})
        self.assertEqual(out['reject_gates'],{'downtrend_h6':1,'old':1,'other_pool':1})
        self.assertEqual((out['realized_sum_sol'],out['realized_measured']),(.0012,1))
        pool=c.trace(self.p,self.s,POOL,now=T,run=trace_run())
        self.assertEqual((pool['kind'],[p['position'] for p in pool['positions']],pool['reject_gates']),('pool',[POS],{'downtrend_h6':1,'old':1}))
        self.assertEqual(c.trace(self.p,self.s,'NOPE',now=T,run=trace_run())['status'],'not_found')
        for q in ('NIO-SOL','nio-sol','SOL-NIO','sol-Nio'):
            pair=c.trace(self.p,self.s,q,now=T,run=trace_run())
            self.assertEqual((pair['kind'],pair['status'],pair['query']),('symbol','ok',q))
            self.assertEqual({p['position'] for p in pair['positions']},{POS,'other'})
        for q in ('NIO-USDC','SOL-SOL','-SOL'):
            self.assertEqual(c.trace(self.p,self.s,q,now=T,run=trace_run())['status'],'not_found')

    def test_query_never_becomes_a_path_or_pattern(self):
        self.seed()
        (self.m/'evil.json').write_text(json.dumps({'pool':POOL}))
        run=trace_run()
        for q in ('../evil','../memories/evil','.*'):
            out=c.trace(self.p,self.s,q,now=T,run=run)
            self.assertEqual((out['kind'],out['status']),('symbol','not_found'))
        self.assertEqual(run.calls,[])
        self.assertIsNone(c.read_entry(self.m,'../evil'))

MIDNIGHT=T-T%DAY  # UTC local midnight of T's day

def nsnap(ts,slot,native,**kw): r=snap(ts,slot,native);r.update(kw);return r
def stamped(rows_): return ''.join('%.1f fixture node[1]: %s\n'%(t,json.dumps(r)) for t,r in rows_)

class GrowthTests(unittest.TestCase):
    """Today's native split: parts reconcile exactly to Δ native, and missing evidence is None."""
    setUp=CollectorTests.setUp
    tearDown=CollectorTests.tearDown
    def fixture(self,closes=None,realized=None,receipts=None,m=None):
        m=m or self.m
        rows(m/'dlmm_nav.jsonl',[nsnap(MIDNIGHT-DAY,50,0.9),nsnap(MIDNIGHT-100,100,1.0,refundable_rent_sol=.01),
                                 nsnap(MIDNIGHT+60,120,1.0),nsnap(T-60,200,1.103,refundable_rent_sol=.008,lp_mark_sol=.2)])
        rows(m/'dlmm_wallet_transactions.jsonl',[
            dict(signature='close-P',slot=150,wallet_delta_lamports=99995000,fee_lamports=5000,failed=False),
            fact(slot=160),
            dict(signature='ext',slot=170,wallet_delta_lamports=1000000,fee_lamports=0,classification='external_transfer',failed=False),
            dict(signature='before',slot=90,wallet_delta_lamports=-7,fee_lamports=5000,failed=False),
            dict(signature='unlanded',slot=180,landed=False,wallet_delta_lamports=0,fee_lamports=5000)])
        rows(m/'dlmm_closes.jsonl',closes if closes is not None else [dict(position='P',ts=T-1000,event='exit'),dict(position='old',ts=MIDNIGHT-500,event='exit')])
        rows(m/'dlmm_realized.jsonl',realized if realized is not None else [dict(position='P',closed_at=T-1000,realized_sol=.05),dict(position='old',closed_at=MIDNIGHT-500,realized_sol=9)])
        run=runner(stamped(receipts if receipts is not None else [(T-500,receipt())]))
        return c.growth_today(m,T,'UTC',run)
    def comp(self,g): return {x['component']:x for x in g['components']}
    def test_parts_reconcile_to_native_delta(self):
        g=self.fixture();k=self.comp(g)
        self.assertEqual(g['status'],'ok');self.assertEqual(g['day'],'2033-05-18')
        self.assertEqual((g['start_ts'],g['end_ts']),(MIDNIGHT-100,T-60))
        self.assertAlmostEqual(g['d_native_sol'],.103,12)
        self.assertEqual(k['realized_lp']['sol'],.05)          # 'old' closed before midnight: excluded
        self.assertAlmostEqual(k['rent_reclaimed']['sol'],(2000000-1000)/1e9,12)
        self.assertAlmostEqual(k['network_fees']['sol'],-10000/1e9,12)  # before-window and unlanded excluded
        self.assertAlmostEqual(k['external']['sol'],.001,12)
        self.assertAlmostEqual(sum(x['sol'] for x in g['components']),g['d_native_sol'],12)
        self.assertAlmostEqual(g['d_refundable_rent_sol'],-.002,12);self.assertAlmostEqual(g['d_lp_mark_sol'],.2,12)
    def test_unreconciled_close_is_unmeasured_not_zero(self):
        g=self.fixture(closes=[dict(position='P',ts=T-1000,event='exit'),dict(position='Q',ts=T-900)])
        k=self.comp(g)
        self.assertIsNone(k['realized_lp']['sol']);self.assertEqual((k['realized_lp']['pending'],k['realized_lp']['closes']),(1,2))
        self.assertEqual(k['realized_lp']['measured_subtotal_sol'],.05)
        self.assertIsNone(k['other']['sol']);self.assertEqual(g['status'],'partial')
    def test_unverified_rent_receipt_is_unmeasured(self):
        rows(self.m/'x',[]);g=self.fixture(receipts=[(T-500,receipt(txHash='not-ingested'))])
        self.assertIsNone(self.comp(g)['rent_reclaimed']['sol']);self.assertIsNone(self.comp(g)['other']['sol'])
        self.assertEqual((self.comp(g)['rent_reclaimed']['pending'],self.comp(g)['rent_reclaimed']['measured_subtotal_sol']),(1,0))
    def test_rent_receipt_after_the_window_end_is_not_counted(self):
        g=self.fixture(receipts=[(T-500,receipt()),(T-10,receipt(txHash='late-not-ingested'))])
        self.assertAlmostEqual(self.comp(g)['rent_reclaimed']['sol'],(2000000-1000)/1e9,12)
    def test_no_snapshot_before_midnight(self):
        rows(self.m/'dlmm_nav.jsonl',[snap(MIDNIGHT+60,120),snap(T-60,200)])
        self.assertEqual(c.growth_today(self.m,T,'UTC',runner('')).get('status'),'insufficient_snapshots')
    def test_viewer_zone_moves_the_window(self):
        self.fixture()
        g=c.growth_today(self.m,T,'Asia/Tokyo',runner(''))  # Tokyo midnight is 15:00 UTC the day before
        self.assertEqual(g['day'],'2033-05-18');self.assertEqual(g['start_ts'],MIDNIGHT-DAY)
    def test_north_star_carries_lp_mark(self):
        self.fixture();ns=c.north_star(self.m,T,2,'UTC')
        self.assertEqual(ns['days'][-1]['lp_mark_sol'],.2)
    def test_daily_and_brief_carry_growth(self):
        p=self.m/'profile';(p/'memories').mkdir(parents=True);want=self.fixture(m=p/'memories')
        with patch.object(c,'bounded_run',runner('')):
            d=c.daily(p,0,('UTC',),now=T);self.assertIn('growth',d['by_tz']['UTC'])
            self.assertIn('experiments',c.slow_panels(p,0,('UTC',),now=T))
        b=c.brief(p,now=T,run=runner(''),statvfs=lambda _:SimpleNamespace(f_bavail=1,f_blocks=1),meminfo=str(self.m/'none'))
        self.assertEqual(b['growth']['d_native_sol'],want['d_native_sol']);self.assertIn('hold_canary',b['experiments'])

class ExperimentsTests(unittest.TestCase):
    setUp=CollectorTests.setUp
    tearDown=CollectorTests.tearDown
    def test_counts_only_and_report_verdict(self):
        p=self.m;mem=p/'memories';(mem/'dlmm_entries').mkdir(parents=True)
        rows(mem/'dlmm_geometry_shadow.jsonl',[dict(kind='entry',ts=T-5),dict(kind='entry',ts=T-4,dry_run=True),dict(kind='other')])
        rows(mem/'dlmm_closes.jsonl',[dict(position='p1',ts=T-3,hold_canary_arm='A'),dict(position='p1',ts=T-2,event='exit',hold_canary_arm='A'),
                                      dict(position='p2',ts=T-1,hold_canary_arm='B'),dict(position='p3',ts=T-1),dict(position='p4',ts=T,event='compound',hold_canary_arm='B')])
        (mem/'dlmm_entries'/'a.json').write_text(json.dumps({'active_bin_reanchor':{'cached_bin':5,'active_bin':3,'drift':-2}}))
        (mem/'dlmm_entries'/'b.json').write_text(json.dumps({'mode':'pulse'}))
        for f in ('a.json','b.json'): os.utime(mem/'dlmm_entries'/f,(T-60,T-60))
        old=mem/'dlmm_entries'/'old.json';old.write_text(json.dumps({'active_bin_reanchor':{'drift':3}}));os.utime(old,(T-10*DAY,T-10*DAY))
        script=p/c.GEOMETRY_REPORT;script.parent.mkdir(parents=True);script.write_text('')
        calls=[]
        def run(argv,**k):
            calls.append(argv)
            return SimpleNamespace(stdout=json.dumps({'verdict':'NEED-DATA','entries':1,'closed':0,'treated':0,'gate':{'min_n':30},'positions':['x']},indent=2)+'\nNEED-DATA: n=0/30\n',stderr='',returncode=0,capture_status='ok')
        with patch.object(c.os.path,'getmtime',side_effect=AssertionError):
            e=c.experiments(p,T-7*DAY,T,run)
        self.assertEqual(calls,[['python3',str(script),'--profile',str(p)]])
        self.assertEqual((e['geometry_shadow']['entries'],e['geometry_shadow']['live_entries']),(2,1))
        self.assertEqual(e['geometry_shadow']['report']['verdict'],'NEED-DATA');self.assertNotIn('positions',e['geometry_shadow']['report'])
        self.assertEqual(e['hold_canary']['arms'],{'A':1,'B':1});self.assertEqual(e['hold_canary']['closes'],2)
        self.assertEqual((e['active_bin_reanchor']['entries'],e['active_bin_reanchor']['reanchored'],e['active_bin_reanchor']['max_drift_bins']),(2,1,2))
        self.assertNotIn('realized_sol',json.dumps(e))  # counts only: no outcome to peek at
    def test_empty_profile_is_ok_and_missing_report_is_named(self):
        e=c.experiments(self.m,T-DAY,T,lambda *a,**k:1/0)
        self.assertEqual(e['status'],'ok');self.assertEqual(e['geometry_shadow']['entries'],0)
        self.assertEqual(e['geometry_shadow']['report'],{'status':'missing'})
        self.assertEqual(e['active_bin_reanchor']['entries'],0)
    def test_failed_report_is_failed(self):
        script=self.m/c.GEOMETRY_REPORT;script.parent.mkdir(parents=True);script.write_text('')
        e=c.experiments(self.m,T-DAY,T,lambda *a,**k:SimpleNamespace(stdout='',stderr='boom',returncode=1,capture_status='ok'))
        self.assertEqual(e['geometry_shadow']['report'],{'status':'failed'})

class PerformanceParityTests(unittest.TestCase):
    """The cheap paths must produce exactly what the reference paths produce."""
    setUp=CollectorTests.setUp
    tearDown=CollectorTests.tearDown

    def test_redaction_fast_path_equals_full_rules(self):
        import random
        rng=random.Random(7)
        alphabet='abkKsS-_:= \t\n"\'/.0123456789' + 'Bearer sk-mnemonic phrase words seed' + 'Kſİé'
        corpus=list(SECRETS)+['pool-A','9gAKLMXq27oLVwnkW1tJxCuGEcbS4GZ1w3Ar2DnsLz6W','23h37m20s','', '\n',
                               'plain text', 'SK-X', 'bEaReR x', 'Seed Words y', 'K', 'SK-x', 'ſk-x']
        corpus+=[''.join(rng.choice(alphabet) for _ in range(rng.randint(0,24))) for _ in range(20000)]
        for text in corpus:
            self.assertEqual(c.redact_text(text),c._redact_text(text),repr(text))

    def test_scrub_equals_clean_of_own_only(self):
        value={'pool':'p','api_key':'x','nested':[{'TOKEN':'y','ok':float('inf'),'n':1,'b':True,'z':None,
               'lp_comparison':{'a':1},'t':('tuple','kept')}],'msg':'TOKEN=abc tail','otherbot_x':1,7:'int key',
               'mixed':[{1:'one'},{True:'true'},{'1':'str one'},{'pool':'p','api_key':'again'}]}
        for extra in ('', 'otherbot'):
            pattern=c.hide_pattern(extra)
            self.assertEqual(json.dumps(c.scrub(value,pattern),sort_keys=True,default=str),
                             json.dumps(c.clean(c.own_only(value,pattern)),sort_keys=True,default=str))

    def test_fast_plus_slow_equals_full_collect(self):
        profile=self.m/'profile';m=profile/'memories';m.mkdir(parents=True)
        bridge_fixture(m); RobinhoodTests.closes(self,m)
        with patch.object(c.subprocess,'run',runner()),patch.object(c,'bounded_run',rh_run()),\
             patch.object(c.time,'time',return_value=T),frozen_clock():
            full=c.collect(profile,profile,1,('UTC','Asia/Jakarta'))
            slow=c.slow_panels(profile,1,('UTC','Asia/Jakarta'),T)
            fast=c.fast_panels(profile,profile,1,T)
        self.assertEqual(set(slow)-{'collected_at'},set(c.SLOW_KEYS))
        merged=c.scrub({'collected_at':T,**{k:slow[k] for k in c.SLOW_KEYS},**fast})
        self.assertEqual(json.dumps(merged,sort_keys=True),json.dumps(full,sort_keys=True))
        # Non-trivial on both sides: a measured calendar day and Robinhood closes reach the snapshot.
        self.assertTrue(any(d.get('known_sol') for d in full['by_tz']['Asia/Jakarta']['north_star']['days']))
        self.assertEqual(full['by_tz']['UTC']['robinhood']['totals']['USDG']['closes'],1)
        self.assertEqual(full['nav']['ts'],T)

    def test_jsonl_memo_rereads_a_changed_file_and_isolates_meta(self):
        path=self.m/'j.jsonl'; rows(path,[{'a':1}])
        first,meta=c.read_jsonl(path); meta['invalid_lines']+=5; first.append({'mutated':True})
        again,meta2=c.read_jsonl(path)
        self.assertEqual((again,meta2['invalid_lines']),([{'a':1}],0))
        with path.open('a') as f: f.write(json.dumps({'a':2})+'\n')
        self.assertEqual(c.read_jsonl(path)[0],[{'a':1},{'a':2}])
        path.unlink(); self.assertEqual(c.read_jsonl(path)[1]['status'],'missing')

    def test_recent_entries_match_glob_order(self):
        d=self.m/'dlmm_entries';d.mkdir()
        for i in range(5):
            p=d/('e%d.json'%i);p.write_text('{}');os.utime(p,(1000+i%3,1000+i%3))
        (d/'.hidden.json').write_text('{}');(d/'note.txt').write_text('');(d/'dangling.json').symlink_to(d/'missing')
        want=sorted((p for p in d.glob('*.json') if p.exists()),key=lambda p:p.stat().st_mtime,reverse=True)[:3]
        self.assertEqual(c.recent_entries(d,3),want)

SKILL_SCRIPTS=Path(__file__).resolve().parents[2]/'assets'/'skill'/'scripts'
PA,PB,PC,PD='A'*40,'B'*40,'C'*40,'D'*40

def close(pos,ts,pnl_sol=-1.0,reason='take profit',**kw):
    # pnl_sol here is the journal MARK; the loss rules must never read it.
    return dict(position=pos,pair=pos[:4]+'-SOL',ts=ts,pnl_sol=pnl_sol,pnl_pct=-50.0,reason=reason,dry_run=False,**kw)

class LossAlertTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'prof';self.m=self.p/'memories';self.m.mkdir(parents=True)
        # The profile's scripts dir is a symlink into the repo, as installed.
        (self.p/'skills'/'solana-dlmm').mkdir(parents=True);(self.p/'skills'/'solana-dlmm'/'scripts').symlink_to(SKILL_SCRIPTS)
    def tearDown(self): self.tmp.cleanup()
    def run_rules(self,closes,realized,env=None):
        rows(self.m/'dlmm_closes.jsonl',closes);rows(self.m/'dlmm_realized.jsonl',realized)
        loss=c.loss_evidence(self.p,T,env or {})
        return loss,{a['id']:a for a in c.loss_alerts(loss)}

    def test_single_close_reads_realized_never_the_mark(self):
        loss,got=self.run_rules([close(PA,T-3600),close(PB,T-3600),close(PC,T-3600)],
            [dict(position=PA,realized_sol=-0.06,realized_pct=-20.0),dict(position=PB,realized_sol=-0.049,realized_pct=-15.0)],{'ALERT_DAY_LOSS_SOL':'1'})
        self.assertEqual(set(got),{'loss_single:'+PA})
        self.assertIn('-0.0600 SOL <= -0.05',got['loss_single:'+PA]['message'])
        # PC has no realized row: unmeasured, never its -1.0 mark and never 0.
        pc=[x for x in loss['closes'] if x['position']==PC][0]
        self.assertIsNone(pc['realized_sol']);self.assertEqual(loss['day']['unmeasured'],1)
        self.assertAlmostEqual(loss['day']['realized_sol'],-0.109)
        # Older than 24h: the per-close rule no longer reports it.
        _,got=self.run_rules([close(PA,T-DAY-60)],[dict(position=PA,realized_sol=-0.2,realized_pct=-40.0)])
        self.assertNotIn('loss_single:'+PA,got)

    def test_day_window(self):
        closes=[close(PA,T-3600),close(PB,T-7200),close(PC,T-9000)]
        realized=[dict(position=PA,realized_sol=-0.04),dict(position=PB,realized_sol=-0.045)]
        _,got=self.run_rules(closes,realized)
        self.assertIn('loss_day',got);self.assertNotIn('loss_single:'+PA,got)
        self.assertIn('2 measured close(s), 1 unmeasured (not counted)',got['loss_day']['message'])
        _,got=self.run_rules(closes,[dict(position=PA,realized_sol=-0.04),dict(position=PB,realized_sol=0.01)])
        self.assertNotIn('loss_day',got)
        # Every close unmeasured: no sum, no alert, never a 0.0 total.
        loss,got=self.run_rules(closes,[])
        self.assertIsNone(loss['day']['realized_sol']);self.assertEqual(got,{})

    def test_week_window(self):
        closes=[close(p,T-d*DAY) for p,d in ((PA,2),(PB,4),(PC,6.5),(PD,8))]
        realized=[dict(position=p,realized_sol=-0.055) for p in (PA,PB,PC,PD)]
        loss,got=self.run_rules(closes,realized)
        self.assertEqual(set(got),{'loss_week'});self.assertEqual(loss['week']['measured'],3)  # PD is outside 7d
        self.assertIn('7d realized -0.1650',got['loss_week']['message'])
        _,got=self.run_rules(closes,realized,{'ALERT_WEEK_LOSS_SOL':'0.2'})
        self.assertEqual(got,{})

    def test_emergency_gap(self):
        sl='EMERGENCY Stop-Loss (-14.20% <= -11.0% floor) — bypasses grace/holds'
        closes=[close(PA,T-600,reason=sl),close(PB,T-600,reason=sl),close(PC,T-600,reason=sl),close(PD,T-600,reason='Stop-Loss')]
        realized=[dict(position=PA,realized_sol=-0.03,realized_pct=-23.0),dict(position=PB,realized_sol=-0.02,realized_pct=-21.0),
                  dict(position=PD,realized_sol=-0.01,realized_pct=-60.0)]
        _,got=self.run_rules(closes,realized,{'ALERT_DAY_LOSS_SOL':'1'})
        # PA past 2x the floor; PB inside it; PC unmeasured; PD was not an emergency close.
        self.assertEqual(set(got),{'loss_emergency_gap:'+PA})
        self.assertIn('-23.00%',got['loss_emergency_gap:'+PA]['message'])

    def test_thresholds_from_env(self):
        th,bad=c.loss_thresholds({})
        self.assertEqual(th,{'ALERT_SINGLE_LOSS_SOL':0.05,'ALERT_DAY_LOSS_SOL':0.08,'ALERT_WEEK_LOSS_SOL':0.15});self.assertEqual(bad,[])
        th,bad=c.loss_thresholds({'ALERT_SINGLE_LOSS_SOL':'0.1','ALERT_DAY_LOSS_SOL':'-1','ALERT_WEEK_LOSS_SOL':'nan'})
        self.assertEqual(th['ALERT_SINGLE_LOSS_SOL'],0.1);self.assertEqual(bad,['ALERT_DAY_LOSS_SOL','ALERT_WEEK_LOSS_SOL'])
        _,got=self.run_rules([],[],{'ALERT_DAY_LOSS_SOL':'x'})
        self.assertEqual(set(got),{'loss_threshold_invalid'})

    def test_dedup_ids_and_duplicate_journal_rows(self):
        # A re-journaled close (timeout/re-adoption) is one close: one id, counted once.
        closes=[close(PA,T-3600),close(PA,T-3000)]
        loss,got=self.run_rules(closes,[dict(position=PA,realized_sol=-0.09)])
        self.assertEqual(loss['day']['closes'],1);self.assertAlmostEqual(loss['day']['realized_sol'],-0.09)
        self.assertEqual(sorted(got),['loss_day','loss_single:'+PA])
        _,again=self.run_rules(closes,[dict(position=PA,realized_sol=-0.09)])
        self.assertEqual(sorted(again),sorted(got))  # stable ids are what the Go state file dedups on

    def test_wired_into_alerts_and_missing_skill_is_loud(self):
        rows(self.m/'dlmm_closes.jsonl',[close(PA,T-60)]);rows(self.m/'dlmm_realized.jsonl',[dict(position=PA,realized_sol=-0.07)])
        vfs=SimpleNamespace(f_bavail=50,f_blocks=100);mem=self.p/'meminfo';mem.write_text('MemAvailable:    1024000 kB\n')
        with patch.dict(os.environ,{},clear=False):
            for k in ('ALERT_SINGLE_LOSS_SOL','ALERT_DAY_LOSS_SOL','ALERT_WEEK_LOSS_SOL'): os.environ.pop(k,None)
            out=c.alerts(self.p,now=T,run=lambda *a,**k:1/0,statvfs=lambda _:vfs,meminfo=str(mem))
            self.assertIn('loss_single:'+PA,{a['id'] for a in out['alerts']})
            json.dumps(c.scrub(out),allow_nan=False)
            (self.p/'skills'/'solana-dlmm'/'scripts').unlink()
            out=c.alerts(self.p,now=T,run=lambda *a,**k:1/0,statvfs=lambda _:vfs,meminfo=str(mem))
            self.assertIn('section_unavailable:loss',{a['id'] for a in out['alerts']})

if __name__=='__main__': unittest.main()
