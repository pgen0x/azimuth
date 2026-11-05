package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http/httptest"
	"strings"
	"testing"
)

func fixtureBrief() object {
	raw := `{"collected_at":2000000000,"hours":12,"n":10,
	"alerts":[{"code":"disk_low","message":"disk free 9.0% < 15%"}],
	"wallet":{"tz":"UTC","status":"ok","as_of":1999999940,"native_sol":0.5,"cash_sol":0.6,"known_sol":0.7,"refundable_rent_sol":0.1,"d_known_measured_sum_sol":-0.03,"d_known_measured_days":13,
	  "days":[{"day":"2033-05-17","status":"no_snapshot"},{"day":"2033-05-18","status":"partial_day","native_sol":0.5,"cash_sol":0.6,"known_sol":0.7,"d_cash_sol":null,"d_known_sol":0.001}]},
	"positions":{"status":"ok","report_at":1999999990,"positions":[{"pair":"AAA-SOL","mode":"pulse","age_minutes":5,"pnl_pct":-1.5,"pnl_sol":-0.0015,"in_range":false,"oor_minutes":3,"size_sol":0.1}]},
	"closes":{"status":"ok","window_closes":1,"window_measured":0,"window_realized_sol":null,
	  "recent":[{"ts":1999999000,"pair":"B-SOL","mode":"pulse","reason":"Low yield","hold_min":30,"realized_sol":null,"pnl_basis":"not_reconciled"},
	            {"ts":1999990000,"pair":"C-SOL","mode":"pulse","reason":"SL","hold_min":3,"realized_sol":0.000012,"pnl_basis":"realized"}]},
	"funnel":{"hours":12,"status":"ok","batches":3,"batch_pools":4,"deploys":1,"last_deploy_ts":1999999000,"direct_deploy":{"deployed":0,"not_deployed":1},
	  "routes":{"hermes_ai":2,"deterministic_fallback:timeout":1},"daemon_rejects":{},"pipeline_rejects":{"downtrend_h6":2}},
	"growth":{"day":"2033-05-18","tz":"UTC","status":"partial","d_native_sol":0.0695,"components":[
	  {"component":"realized_lp","sol":null,"pending":1,"closes":1,"measured_subtotal_sol":0},{"component":"rent_reclaimed","sol":0.068436},
	  {"component":"network_fees","sol":-0.000055},{"component":"external","sol":0},{"component":"other","sol":null}]},
	"experiments":{"status":"ok","geometry_shadow":{"entries":0,"report":{"status":"ok","verdict":"NEED-DATA","closed":0,"treated":0}},
	  "hold_canary":{"arms":{"A":14,"B":12}},"active_bin_reanchor":{"entries":27,"reanchored":0}},
	"entry_funnel":{"status":"ok","windows":[
	  {"hours":24,"batches":65,"batch_pools":66,"routes":{"hermes_ai":65,"deterministic_fallback":3},"fallback_reasons":{"timeout":3},
	   "deploys":{"total":3,"verified":2,"unverified":0,"unknown":1},"rejects":{"conviction_floor":2,"downtrend_h6":6}},
	  {"hours":1,"batches":5,"batch_pools":5,"routes":{"hermes_ai":5,"deterministic_fallback":0},"fallback_reasons":{},
	   "deploys":{"total":1,"verified":1,"unverified":0,"unknown":0},"rejects":{}}],
	  "ticket":{"status":"ok","base_ticket_sol":0.1,"minimum_entry_sol":0.1,"min_score":{"pulse":{"floor":30,"min_score":66},"multiday":{"floor":12,"min_score":null}}},
	  "score_bands":{"since":1999990000,"bands":{"<50":{"n":1,"measured":1,"pending":0,"sum_sol":-0.002},"50-70":{"n":0,"measured":0,"pending":0,"sum_sol":null},
	    ">=70":{"n":2,"measured":1,"pending":1,"sum_sol":0.003},"unscored":{"n":0,"measured":0,"pending":0,"sum_sol":null}}}},
	"health":{"units":[{"unit":"azimuth.service","active":"active","enabled":"enabled"}],"failed_units":[],"disk_free_pct":9,"mem_available_mb":2000,"monitor_tick_age_s":15}}`
	var d object
	if err := json.Unmarshal([]byte(raw), &d); err != nil {
		panic(err)
	}
	return d
}

func TestBriefTextCompactAndHonest(t *testing.T) {
	text := briefText(fixtureBrief())
	for _, want := range []string{
		"ALERTS 1", "! disk_low", "WALLET native 0.5000", "2033-05-17  no_snapshot", "(so far)",
		"OPEN 1 · pnl is a MARK", "AAA-SOL", "OOR 3m", "mark -1.50%",
		"n/a not_reconciled", "+0.000012 realized", "realized n/a SOL",
		"batches 3 (4 pools)", "hermes_ai 2, deterministic_fallback:timeout 1", "daemon rejects: none",
		"HEALTH disk free 9%", "azimuth=active/enabled",
		"ENTRY FUNNEL · ok",
		"24h batches 65 (66 pools) · route ai 65 / fallback 3 (timeout 3) · deploys 3: verified 2, unverified 0, unknown 1",
		"rejects: downtrend_h6 6, conviction_floor 2", "1h batches 5 (5 pools)", "rejects: none",
		"ticket base 0.1000 SOL · minimum 0.1000 · clearing score multiday none (floor 12), pulse >=66.0 (floor 30)",
		"score bands since 05-18 00:46Z: <50 n=1 realized -0.002000 (1 measured, 0 pending) · 50-70 n=0 realized n/a",
		"GROWTH Δnative +0.0695 SOL · realized LP unmeasured (1/1 closes not reconciled, so far +0.000000) · rent +0.068436 · fees -0.000055 · external +0.000000 · other unmeasured · partial",
		"EXPERIMENTS geometry shadow 0 entries/0 paired/0 treated NEED-DATA · hold canary A 14 B 12 · re-anchor 0/27 entries",
	} {
		if !strings.Contains(text, want) {
			t.Fatalf("missing %q in:\n%s", want, text)
		}
	}

	// Worst case: 15 wallet days, 10 closes, more alerts and positions than are printed.
	d := fixtureBrief()
	days := []any{}
	for i := 0; i < 15; i++ {
		days = append(days, object{"day": fmt.Sprintf("2033-05-%02d", i+1), "status": "ok", "native_sol": 0.5})
	}
	obj(d["wallet"])["days"] = days
	many := []any{}
	for i := 0; i < 20; i++ {
		many = append(many, object{"code": "x", "message": "y", "pair": "P-SOL"})
	}
	d["alerts"] = many
	obj(d["positions"])["positions"] = many
	obj(d["closes"])["recent"] = many[:10]
	// 60 lines + one GROWTH and one EXPERIMENTS line + seven ENTRY FUNNEL lines.
	if lines := strings.Count(briefText(d), "\n"); lines > 69 {
		t.Fatalf("text brief is %d lines, want <= 69", lines)
	}
	// A failed section names itself instead of rendering empty numbers.
	d["funnel"] = object{"status": "unavailable", "collection_error": "Panel evidence could not be read: OSError"}
	if !strings.Contains(briefText(d), "unavailable: Panel evidence could not be read") {
		t.Fatal("section error not shown")
	}
}

func TestBriefParams(t *testing.T) {
	for _, tc := range []struct {
		h, n, tz string
		ok       bool
	}{{"", "", "", true}, {"168", "50", "Asia/Jakarta", true}, {"0", "", "", false}, {"169", "", "", false}, {"x", "", "", false}, {"", "51", "", false}, {"", "", "Mars/Olympus", false}} {
		_, _, _, err := briefParams(tc.h, tc.n, tc.tz)
		if (err == nil) != tc.ok {
			t.Fatalf("%+v: %v", tc, err)
		}
	}
}

func TestAgentBriefEndpoint(t *testing.T) {
	calls := 0
	var got []string
	var sinces []int64
	s := &server{profile: "p", state: "s"}
	s.runBrief = func(ctx context.Context, profile, state string, hours, n int, tz string, since int64) (object, error) {
		calls++
		got = append(got, fmt.Sprintf("%s %s %d %d %s", profile, state, hours, n, tz))
		sinces = append(sinces, since)
		if tz == "Europe/Paris" {
			return nil, errors.New("synthetic failure")
		}
		return fixtureBrief(), nil
	}
	cookie := signIn(t, s)
	// Login is required like every other /api route; no collector run happens before it.
	if w := do(s, "GET", "/api/agent/brief", nil, nil, nil); w.Code != 401 || calls != 0 {
		t.Fatalf("unauthenticated: %d calls=%d", w.Code, calls)
	}
	get := func(path string) *httptest.ResponseRecorder {
		r := httptest.NewRequest("GET", path, nil)
		r.Host = "localhost"
		r.AddCookie(cookie)
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		return w
	}
	if w := get("/api/agent/brief?hours=999"); w.Code != 400 || calls != 0 {
		t.Fatalf("bad hours: %d", w.Code)
	}
	w := get("/api/agent/brief")
	if w.Code != 200 || !strings.Contains(w.Header().Get("Content-Type"), "json") || !strings.Contains(w.Body.String(), `"code":"disk_low"`) {
		t.Fatalf("json: %d %s", w.Code, w.Body.String())
	}
	w = get("/api/agent/brief?format=text")
	if w.Code != 200 || !strings.HasPrefix(w.Body.String(), "azimuth brief") {
		t.Fatalf("text: %d %s", w.Code, w.Body.String())
	}
	if calls != 1 || got[0] != "p s 12 10 UTC" {
		t.Fatalf("cache/defaults: calls=%d %v", calls, got)
	}
	if w = get("/api/agent/brief?hours=24&n=3&tz=Asia/Jakarta"); w.Code != 200 || calls != 2 || got[1] != "p s 24 3 Asia/Jakarta" {
		t.Fatalf("params: %d %v", w.Code, got)
	}
	if w = get("/api/agent/brief?funnel_since=bogus"); w.Code != 400 || calls != 2 {
		t.Fatalf("bad funnel_since: %d", w.Code)
	}
	if w = get("/api/agent/brief?funnel_since=2026-11-05T15:00:00Z"); w.Code != 200 || calls != 3 || sinces[2] != 1793890800 || sinces[0] != 0 {
		t.Fatalf("funnel_since: %d %v", w.Code, sinces)
	}
	if w = get("/api/agent/brief?tz=Europe/Paris"); w.Code != 503 || strings.Contains(w.Body.String(), "synthetic") {
		t.Fatalf("failure must be 503 without detail: %d %s", w.Code, w.Body.String())
	}
}

func TestBriefMainFlags(t *testing.T) {
	var out, errb bytes.Buffer
	if code := briefMain([]string{"--hours", "0"}, &out, &errb); code != 2 || !strings.Contains(errb.String(), "invalid hours") {
		t.Fatalf("hours: %d %s", code, errb.String())
	}
	errb.Reset()
	if code := briefMain([]string{"--profile", t.TempDir() + "/absent"}, &out, &errb); code != 2 || !strings.Contains(errb.String(), "not found") {
		t.Fatalf("profile: %d %s", code, errb.String())
	}
	if code := briefMain([]string{"--bogus"}, &out, &errb); code != 2 {
		t.Fatalf("unknown flag: %d", code)
	}
}

func TestFunnelSince(t *testing.T) {
	for _, tc := range []struct {
		in   string
		want int64
		ok   bool
	}{{"", 0, true}, {"2026-11-05T15:00:00Z", 1793890800, true}, {"2026-11-05T22:00:00+07:00", 1793890800, true},
		{"1793890800", 1793890800, true}, {"-1", 0, false}, {"yesterday", 0, false}} {
		got, err := funnelSince(tc.in)
		if (err == nil) != tc.ok || got != tc.want {
			t.Fatalf("%q: %d %v", tc.in, got, err)
		}
	}
	var out, errb bytes.Buffer
	if code := briefMain([]string{"--funnel-since", "nope"}, &out, &errb); code != 2 || !strings.Contains(errb.String(), "invalid funnel_since") {
		t.Fatalf("bad flag: %d %q", code, errb.String())
	}
}
