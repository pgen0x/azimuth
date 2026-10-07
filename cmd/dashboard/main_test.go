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
	s := &server{data: object{"nav": object{"nav_sol": nil, "native_sol": 0.0}, "journal": []any{object{"stage": "swap", "evidence": object{"signature": "proof-1"}}, object{"stage": "gate", "evidence": object{"pool": "pool-2"}}}}}
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
    deploy=next(e for e in data['journal'] if e['stage']=='deploy')
    assert 'before broadcast' in deploy['note']

`
	out, err := exec.Command("python3", "-c", code).CombinedOutput()
	if err != nil {
		t.Fatalf("collector check: %v %s", err, out)
	}
}
