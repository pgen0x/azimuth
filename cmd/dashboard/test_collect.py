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
        bridge_fixture(self.m);b=c.nav_bridge(self.m,T,1);parts={r['key']:r['sol'] for r in b['components']}
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
                    self.assertIsNone(next(x['sol'] for x in b['components'] if x['key']=='rent_ledger'))
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
        day=86400;base=20000*day-c.WIB
        rows=[dict(ts=base+i*day+j*2400,native_sol=1.0+i*.01,lp_mark_sol=0.0,refundable_rent_sol=.01,known_asset_subtotal_sol=1.01+i*.01,
                   external_flow_lamports=0,wallet_history_complete=True) for i in range(4) for j in range(30)]
        self._big_nav(rows)
        ns=c.north_star(self.m,base+3*day+20*3600,days=3)
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
        day=20000;end=day*86400-c.WIB+86400
        rows,changed,cutoff,reads,spy=self._backscan_counterexample(base=end-1-15090)
        ns=c.north_star(self.m,cutoff+14000,days=1)
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
                self.assertIsNone(next(x['sol'] for x in b['components'] if x['key']==key))
        bridge_fixture(self.m);f=self.m/'dlmm_nav.jsonl';data=[json.loads(l) for l in f.read_text().splitlines()];data[-1]['wallet_history_complete']=False;rows(f,data)
        b=c.nav_bridge(self.m,T,1);self.assertNotEqual(b['status'],'ok');self.assertIsNone(b['native_identity_exact'])
        self.assertTrue(all(v['sol'] is None for v in b['fees_by_kind'].values()))
        bridge_fixture(self.m);f=self.m/'dlmm_wallet_transactions.jsonl';data=[json.loads(l) for l in f.read_text().splitlines()]
        data[0]['token_rent_evidence']={'funded':[{'lamports':None}],'refunded':[]};rows(f,data)
        b=c.nav_bridge(self.m,T,1);self.assertIn('ata_funding',b['incomplete_values'])
    def test_unattributed_cash_not_rent(self):
        bridge_fixture(self.m);rows(self.m/'dlmm_transactions.jsonl',[])
        b=c.nav_bridge(self.m,T,1);p={r['key']:r for r in b['components']}
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
    def test_north_star_latest_unknown_and_wib(self):
        base=20000*DAY-c.WIB;f=self.m/'dlmm_nav.jsonl'
        bad=snap(base+20,2,None)
        rows(f,[snap(base+10,1,1),bad,snap(base+DAY+10,3,2)])
        days=c.north_star(self.m,base+DAY+20,1)['days']
        self.assertEqual(days[0]['ts'],base+20);self.assertIsNone(days[1]['d_cash_sol'])
        rows(f,[snap(base-1,1,1),snap(base,2,2),snap(base+DAY-1,3,3),snap(base+DAY,4,4)])
        self.assertEqual([x['native_sol'] for x in c.north_star(self.m,base+DAY,2)['days']],[1,3,4])
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
            d=c.collect(profile,state,1)
        self.assertIn('nav',d);self.assertIn('journal',d)
        self.assertNotEqual(d['live']['realized']['status'],'ok')

if __name__=='__main__': unittest.main()
