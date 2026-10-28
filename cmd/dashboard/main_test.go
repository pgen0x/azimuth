package main

import (
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestReadOnlyCachedAPI(t *testing.T) {
	s := &server{data: object{"north_star": object{"days": []any{}}, "nav": object{"nav_sol": nil, "native_sol": 0.0}, "journal": []any{object{"stage": "swap", "evidence": object{"signature": "proof-1"}}, object{"stage": "gate", "evidence": object{"pool": "pool-2"}}}}}
	for _, tc := range []struct {
		method, path, host string
		status             int
		want               string
	}{
		{"GET", "/api/overview", "localhost", 200, `"nav_sol":null`},
		{"GET", "/api/journal?q=proof-1&stage=swap", "127.0.0.1:8787", 200, `"total_in_retained_tail":1`},
		{"GET", "/api/journal?offset=999", "localhost", 200, `"rows":[]`},
		{"GET", "/api/journal?offset=-1", "localhost", 400, "invalid offset"},
		{"POST", "/api/redis", "localhost", 405, "read only"},
		{"GET", "/api/overview", "attacker.example", 403, "localhost only"},
		{"GET", "/api/capital", "localhost", 200, `"north_star":{"days":[]}`},
		{"GET", "/api/command", "localhost", 404, "404"},
	} {
		r := httptest.NewRequest(tc.method, tc.path, nil)
		r.Host = tc.host
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		if w.Code != tc.status || !strings.Contains(w.Body.String(), tc.want) {
			t.Fatalf("%s: %d %s", tc.path, w.Code, w.Body.String())
		}
	}
}

func TestRedisConfigAllowlist(t *testing.T) {
	path := filepath.Join(t.TempDir(), "env")
	os.WriteFile(path, []byte("REDIS_ADDR=127.0.0.1:6379\nREDISCLI_AUTH='private'\nWALLET_PRIVATE_KEY=never-load\n"), 0600)
	t.Setenv("REDIS_SEEN_KEY", "test-prefix")
	got := redisSettings(path)
	if len(got) != 3 || got["REDIS_SEEN_KEY"] != "test-prefix" {
		t.Fatalf("unexpected settings keys")
	}
}

func TestCollectorEvidenceBoundaries(t *testing.T) {
	// Run the actual collector helpers with local synthetic evidence, without runtime probes.
	code := strings.Split(collector, "if __name__=='__main__':")[0] + `
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'journal.jsonl'
    path.write_bytes(b'{"nav_sol":null}\ninvalid\n{"native_sol":0}\n{"partial":')
    rows,meta=tail(path)
    assert rows == [{'nav_sol':None},{'native_sol':0}]
    assert meta['invalid_lines']==1 and meta['partial_line']
    rows,meta=tail(path,limit=1)
    assert rows==[{'native_sol':0}] and meta['truncated']
    assert clean({'api_key':'private','nested':{'password':'private'},'nav_sol':None})=={'api_key':'[masked]','nested':{'password':'[masked]'},'nav_sol':None}
    assert 'private' not in clean('https://private.example?token=private')
    assert clean('risk-assessment') == 'risk-assessment'
    assert event_time({'closed_at':123,'fetched_at':456}) == 123
    assert event_time({'ts':None,'observed_at':456}) == 456
    rows,meta=tail(Path(tmp)/'absent')
    assert rows==[] and meta['status']=='missing'
    profile=Path(tmp)/'solanza'; state=Path(tmp)/'state'; memory=profile/'memories'
    memory.mkdir(parents=True); state.mkdir()
    (memory/'dlmm_wallet_transactions.jsonl').write_text(json.dumps({'signature':'proof','failed':False,'slot':123,'fee_lamports':5000,'block_time':100,'observed_at':200})+'\n')
    (memory/'dlmm_transactions.jsonl').write_text(json.dumps({'signature':'proof','kind':'deploy','ts':90})+'\n')
    (memory/'dlmm_realized.jsonl').write_text(json.dumps({'position':'p','closed_at':150,'fetched_at':250})+'\n')
    (memory/'dlmm_closes.jsonl').write_text(json.dumps({'position':'old','pnl_sol':0.5,'closed_at':160})+'\n'+json.dumps({'position':'new','pnl_sol':-0.1,'pnl_basis':'pre_swap_mark','closed_at':170})+'\n')
    (state/'solana_deliveries.jsonl').write_text(json.dumps({'delivery_id':'delivery','stage':'prepared','ts':80})+'\n')
    identity=json.dumps(['solanza','dlmm-signal','delivery'],separators=(',',':')).encode()
    with sqlite3.connect(profile/'state.db') as db:
        db.execute('CREATE TABLE sessions (id, source, model, started_at, ended_at, end_reason, message_count, tool_call_count, chat_id)')
        db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)',('session','webhook','markt',81,None,None,1,1,'webhook:v2:'+base64.urlsafe_b64encode(identity).decode().rstrip('=')))
    subprocess.run=lambda *a,**k: type('Result',(),{'stdout':''})()
    data=collect(profile,state)
    fact=next(e for e in data['journal'] if e['evidence'].get('slot')==123)
    assert fact['time']==100 and fact['evidence']['failed'] is False and fact['evidence']['fee_lamports']==5000
    realized=next(e for e in data['journal'] if e['stage']=='settlement')
    assert realized['time']==150
    session=next(e for e in data['journal'] if e['evidence'].get('session_id')=='session')
    assert session['evidence']['execution_verified'] is False
    assert session['evidence']['session_state']=='no_end_recorded_liveness_unknown'
    closes={e['evidence']['position']:e['evidence'] for e in data['journal'] if e['stage']=='exit'}
    assert closes['old']['pnl_basis']=='mark_unlabeled' and closes['new']['pnl_basis']=='pre_swap_mark'
    deploy=next(e for e in data['journal'] if e['stage']=='deploy')
    assert 'before broadcast' in deploy['note']

`
	out, err := exec.Command("python3", "-c", code).CombinedOutput()
	if err != nil {
		t.Fatalf("collector check: %v %s", err, out)
	}
}

func TestNorthStarFromNavHistory(t *testing.T) {
	// Synthetic NAV history: binary search must equal a linear scan, null parts stay null.
	code := strings.Split(collector, "if __name__=='__main__':")[0] + `
import random, tempfile
rnd=random.Random(7)
for trial in range(150):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'nav.jsonl'; rows=[]; ts=1000
        for i in range(rnd.randint(1,40)):
            ts+=rnd.randint(0,3); rows.append({'ts':ts,'native_sol':None if rnd.random()<.15 else 1.0,'pad':'x'*rnd.randint(0,200)})
        body=[json.dumps(r)+'\n' for r in rows]
        if rnd.random()<.3: body.insert(rnd.randint(0,len(body)),'no timestamp\n')
        p.write_text(''.join(body)+('{"ts": 9' if rnd.random()<.3 else ''))
        for t in range(995,ts+2):
            want=[r for r in rows if r['ts']<=t and r['native_sol'] is not None]
            assert nav_at(p,t)==(want[-1] if want else None),(trial,t)
with tempfile.TemporaryDirectory() as tmp:
    memory=Path(tmp); day=86400; base=20000*day-WIB
    snaps=[{'ts':base+3600,'native_sol':1.0,'lp_mark_sol':0.5,'refundable_rent_sol':0.25,'known_asset_subtotal_sol':2.0,'external_flow_lamports':0,'wallet_history_complete':True,
            'issues':['unpriced_token:m1'],'tokens':[{'mint':'m2','mark_error':'quote_budget_deferred'}]},
           {'ts':base+day+3600,'native_sol':1.2,'lp_mark_sol':None,'refundable_rent_sol':0.25,'known_asset_subtotal_sol':None,'external_flow_lamports':0,'wallet_history_complete':False},
           {'ts':base+2*day+60,'native_sol':1.1,'lp_mark_sol':0.5,'refundable_rent_sol':0.25,'known_asset_subtotal_sol':2.1,'external_flow_lamports':100000000,'wallet_history_complete':True},
           {'ts':base+4*day+60,'native_sol':1.2,'lp_mark_sol':0.5,'refundable_rent_sol':0.25,'known_asset_subtotal_sol':2.3,'external_flow_lamports':100000000,'wallet_history_complete':True},
           {'ts':base+5*day+60,'native_sol':1.3,'lp_mark_sol':0.5,'refundable_rent_sol':0.25,'known_asset_subtotal_sol':2.4,'external_flow_lamports':100000000,'wallet_history_complete':True}]
    (memory/'dlmm_nav.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in snaps))
    out={d['day']:d for d in north_star(memory,base+5*day+120,days=6)['days']}
    d=[out[time.strftime('%Y-%m-%d',time.gmtime((20000+i)*day))] for i in range(-1,6)]
    assert d[0]['status']=='no_snapshot'
    assert d[1]['cash_sol']==1.75 and d[1]['unpriced_tokens']==1 and d[1]['quote_deferred_tokens']==1 and 'd_cash_sol' not in d[1]
    assert d[2]['cash_sol'] is None and d[2]['known_sol'] is None and d[2]['d_cash_sol'] is None and d[2]['d_known_sol'] is None
    assert d[3]['d_cash_sol'] is None and abs(d[3]['d_external_sol']-0.1)<1e-12  # previous day unmeasured
    assert d[4]['status']=='no_snapshot' and 'd_cash_sol' not in d[5]  # a missing day breaks the chain
    assert d[6]['status']=='partial_day' and abs(d[6]['d_cash_sol']-0.1)<1e-12 and abs(d[6]['d_known_sol']-0.1)<1e-12 and d[6]['d_external_sol']==0
`
	out, err := exec.Command("python3", "-c", code).CombinedOutput()
	if err != nil {
		t.Fatalf("north star check: %v %s", err, out)
	}
}

func TestNavBridgeSyntheticLedger(t *testing.T) {
	// One complete lifecycle, one with unmeasured realized PnL, an external transfer and an SPL move.
	code := strings.Split(collector, "if __name__=='__main__':")[0] + `
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    m=Path(tmp); T=2000000000
    a={'ts':T-86400,'slot':100,'native_sol':1.0,'spl_mark_sol':0.1,'lp_mark_sol':0.0,'refundable_rent_sol':0.002,'known_asset_subtotal_sol':1.102,'tokens':[{'mint':'m1','mark_sol':0.1}]}
    b={'ts':T,'slot':200,'native_sol':1.029,'spl_mark_sol':0.12,'lp_mark_sol':0.1,'refundable_rent_sol':0.002,'known_asset_subtotal_sol':1.251,'tokens':[{'mint':'m1','mark_sol':0.12},{'mint':'m3','mark_sol':None}]}
    (m/'dlmm_nav.jsonl').write_text(json.dumps(a)+'\n'+json.dumps(b)+'\n')
    tx=lambda sig,slot,delta,fee=5000,**k: dict(signature=sig,slot=slot,wallet_delta_lamports=delta,fee_lamports=fee,**k)
    wallet=[tx('d1',101,-500000000),tx('c1',102,520000000,position_account_closed=True),tx('s1',103,9000000),
            tx('x1',104,100000000,0,classification='external_transfer'),tx('d2',105,-100000000),tx('old',50,7)]
    (m/'dlmm_wallet_transactions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in wallet))
    kinds=[dict(signature='d1',kind='deploy',position='P'),dict(signature='c1',kind='close',position='P'),dict(signature='s1',kind='swap',position='P'),dict(signature='d2',kind='deploy',position='Q')]
    (m/'dlmm_transactions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in kinds))
    (m/'dlmm_realized.jsonl').write_text(json.dumps({'position':'P','realized_sol':0.03})+'\n'+json.dumps({'position':'Q','realized_sol':None})+'\n')
    (m/'dlmm_closes.jsonl').write_text(json.dumps({'position':'P','mode':'pulse'})+'\n')
    r=nav_bridge(m,T,days=1); c={x['key']:x['sol'] for x in r['components']}
    assert r['status']=='ok' and r['native_identity_exact'] and r['transactions']==5
    assert abs(c['lp_realized']-0.03)<1e-12 and abs(c['network_fees']+0.00002)<1e-12
    assert abs(c['swap_residual']-(0.009005-(0.03-0.02001)))<1e-12 and abs(c['spl_mark']-0.02)<1e-12
    assert abs(c['external']-0.1)<1e-12 and abs(c['lp_unrealized']-0.1)<1e-12 and abs(c['partial_lifecycles']+0.099995)<1e-12
    assert abs(c['unexplained'])<1e-9 and abs(sum(c.values())-r['d_known_sol'])<1e-12
    assert r['positions']=={'complete':1,'partial':1,'realized_unmeasured':1} and r['by_mode']['pulse']['n']==1
    assert r['fees_by_kind']['external']['n']==1 and r['unpriced_tokens']==[0,1]
    assert nav_bridge(m,T-86400,days=1)['status']=='insufficient_snapshots'
    (m/'dlmm_realized.jsonl').unlink()
    assert nav_bridge(m,T,days=1)['incomplete_sources']==['realized']
`
	out, err := exec.Command("python3", "-c", code).CombinedOutput()
	if err != nil {
		t.Fatalf("nav bridge check: %v %s", err, out)
	}
}
