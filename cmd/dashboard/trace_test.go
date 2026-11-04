package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"strings"
	"testing"
)

func fixtureTrace() object {
	raw := `{"collected_at":2000000000,"query":"Pos1","kind":"position","status":"ok","days":7,
	"sources":{"closes":"ok","deliveries":"missing"},
	"summary":{"position":"Pos1","pool":"Pool1","pair":"NIO-SOL","mode":"pulse","route":"ai","state":"closed",
	  "deployed_at":1999996400,"closed_at":1999998200,"realized_sol":0.0012,"pnl_basis":"realized"},
	"events":[
	  {"time":1999996380,"stage":"batch_sent","delivery_id":"d1d1d1d1d1d1d1d1","candidates":2,"pools":[{"symbol":"X","score":80,"this":false},{"symbol":"NIO","score":81,"this":true}]},
	  {"time":1999996381,"stage":"route","route":"hermes_ai","fallback_reason":null},
	  {"time":1999996395,"stage":"hermes_decision","status":"ok","text":"Pick NIO because fees"},
	  {"time":1999996400,"stage":"entry","mode":"pulse","strategy":"sol_bidask","size_sol":0.1,"route":"ai","entry_bin":-428,"bins_below":44,"bins_above":0,"score":90.5,"entry_id":"e1"},
	  {"time":1999996400,"stage":"active_bin_reanchor","cached":-430,"fresh":-428,"drift":2},
	  {"time":1999996420,"stage":"monitor_ticks","status":"ok","ticks":3,"last":1999996460,"pnl_pct_min":-2,"pnl_pct_max":3.5,"pnl_sol_min":-0.002,"pnl_sol_max":0.0035,"oor_ticks":1},
	  {"time":1999998200,"stage":"close","reason":"Low yield","age_min":30,"mark_pnl_pct":1,"mark_basis":"pre_swap_mark","ai_holds":1,"txs":1},
	  {"time":1999998201,"stage":"cooldown_set","line":"Re-entry cooldown set for NIO: 1h"},
	  {"time":1999998800,"stage":"realized","realized_sol":0.0012,"realized_pct":1.2,"deposit_sol":0.1,"withdrawal_sol":0.1,"fee_sol":0.0012}]}`
	var d object
	if err := json.Unmarshal([]byte(raw), &d); err != nil {
		panic(err)
	}
	return d
}

func TestTraceTextPosition(t *testing.T) {
	text := traceText(fixtureTrace())
	want := []string{
		"azimuth trace Pos1 · position · ok", "route ai · closed", "realized +0.001200 SOL (realized)",
		"*NIO(81)", "hermes_ai", "Pick NIO because fees", "bin -428 (-44/+0)", "drift=2",
		"MARK pnl -2.00%..+3.50%", "Low yield · held 30m · MARK +1.00% (pre_swap_mark)",
		"Re-entry cooldown set for NIO", "+0.001200 SOL (+1.20%)", "SOURCES not ok: deliveries=missing", "is the arbiter",
	}
	last := -1
	for _, w := range want[3:12] { // timeline rows keep the collector's chronological order
		i := strings.Index(text, w)
		if i < last {
			t.Fatalf("%q out of order:\n%s", w, text)
		}
		last = i
	}
	for _, w := range want {
		if !strings.Contains(text, w) {
			t.Fatalf("missing %q in:\n%s", w, text)
		}
	}
}

func TestTraceTextListingAndNotFound(t *testing.T) {
	raw := `{"query":"NIO","kind":"symbol","status":"ok","days":7,"sources":{},"realized_sum_sol":0.0012,"realized_measured":1,
	"positions":[{"position":"Pos1","mode":"pulse","route":"deterministic","deployed_at":1999996400,"hold_min":30,"realized_sol":null,"pnl_basis":"not_reconciled","close_reason":"SL"}],
	"rejects_total":12,"reject_gates":{"downtrend_h6":11,"entry_timing":1},"rejects":[` +
		strings.Repeat(`{"ts":1999990000,"gate":"downtrend_h6","mode":"pulse","pool":"Pool111111111111"},`, 11) +
		`{"ts":1999990001,"gate":"entry_timing","mode":"pulse","pool":"Pool1"}]}`
	var d object
	if err := json.Unmarshal([]byte(raw), &d); err != nil {
		t.Fatal(err)
	}
	text := traceText(d)
	for _, want := range []string{"POSITIONS 1 · realized +0.001200 SOL over 1 measured", "deterministic", "n/a not_reconciled",
		"PIPELINE REJECTS 12 · downtrend_h6 11, entry_timing 1", "last 10 of 12", "Pool…1111"} {
		if !strings.Contains(text, want) {
			t.Fatalf("missing %q in:\n%s", want, text)
		}
	}
	if n := strings.Count(text, "Pool…1111"); n != 9 {
		t.Fatalf("listing shows %d downtrend rows, want 9 (last 10 incl. entry_timing):\n%s", n, text)
	}
	nf := traceText(object{"query": "X", "kind": "symbol", "status": "not_found", "days": 7.0})
	if !strings.Contains(nf, "nothing found") {
		t.Fatal(nf)
	}
}

func TestTraceMainArgs(t *testing.T) {
	dir := t.TempDir()
	var gotProfile, gotQuery string
	var gotDays int
	run := func(_ context.Context, profile, _ string, query string, days int) (object, error) {
		gotProfile, gotQuery, gotDays = profile, query, days
		switch query {
		case "missing":
			return object{"query": query, "kind": "symbol", "status": "not_found"}, nil
		case "boom":
			return nil, errors.New("collector failed")
		}
		return fixtureTrace(), nil
	}
	cases := []struct {
		args  []string
		code  int
		query string
		days  int
	}{
		{[]string{"Pos1", "-profile", dir}, 0, "Pos1", 7},
		{[]string{"-profile", dir, "NIO", "--days", "3"}, 0, "NIO", 3},
		{[]string{"-profile", dir, "--json", "NIO"}, 0, "NIO", 7},
		{[]string{"-profile", dir}, 2, "", 0},
		{[]string{"a", "b", "-profile", dir}, 2, "", 0},
		{[]string{"NIO", "-profile", dir, "--days", "31"}, 2, "", 0},
		{[]string{"has space", "-profile", dir}, 2, "", 0},
		{[]string{"NIO", "-profile", dir + "/nope"}, 2, "", 0},
		{[]string{"missing", "-profile", dir}, 3, "missing", 7},
		{[]string{"boom", "-profile", dir}, 1, "boom", 7},
	}
	for _, c := range cases {
		gotQuery, gotDays = "", 0
		var out, errb bytes.Buffer
		code := traceMainWith(c.args, &out, &errb, run)
		if code != c.code || gotQuery != c.query || gotDays != c.days {
			t.Fatalf("%v: code %d query %q days %d (stderr %s)", c.args, code, gotQuery, gotDays, errb.String())
		}
		if c.code == 0 && gotProfile != dir {
			t.Fatalf("%v: profile %q", c.args, gotProfile)
		}
	}
	var out bytes.Buffer
	traceMainWith([]string{"--json", "Pos1", "-profile", dir}, &out, &bytes.Buffer{}, run)
	var back object
	if err := json.Unmarshal(out.Bytes(), &back); err != nil || back["kind"] != "position" {
		t.Fatalf("--json output: %v %s", err, out.String())
	}
}

func TestValidQuery(t *testing.T) {
	for q, ok := range map[string]bool{"NIO": true, "███": true, "Pos1111111111111111111111111111111111111": true,
		"": false, "-x": false, "a b": false, "a\nb": false, strings.Repeat("x", 65): false} {
		if validQuery(q) != ok {
			t.Fatalf("validQuery(%q) != %v", q, ok)
		}
	}
}

func TestBriefTextTodayAndRealized(t *testing.T) {
	d := fixtureBrief()
	d["today"] = object{"day": "2033-05-18", "tz": "UTC", "native_delta_sol": 0.0500, "rent_reclaimed_sol": nil, "rent_tx": 3.0,
		"rent_native_gain_sol": nil, "native_delta_ex_rent_sol": nil, "rent_status": "partial", "rent_verified_subtotal_sol": 0.0600, "rent_verified_tx": 2.0}
	d["realized_7d"] = object{"days": 7.0, "status": "ok",
		"by_mode": object{"pulse": object{"n": 4.0, "measured": 4.0, "sum_sol": 0.004, "mean_sol": 0.001}},
		"by_route": object{"ai": object{"n": 3.0, "measured": 3.0, "sum_sol": 0.003, "mean_sol": 0.001},
			"unknown": object{"n": 2.0, "measured": 0.0, "sum_sol": nil, "mean_sol": nil}}}
	text := briefText(d)
	for _, want := range []string{
		"TODAY 2033-05-18 UTC · native Δ +0.0500 SOL", "rent reclaimed n/a SOL (3 tx", "verified subtotal +0.0600 SOL over 2 of 3 tx (not a total)",
		"REALIZED 7d (arbiter)", "pulse n=4 sum +0.004000 mean +0.001000", "ai n=3 sum +0.003000", "unknown n=2 sum n/a mean n/a (0 measured)",
	} {
		if !strings.Contains(text, want) {
			t.Fatalf("missing %q in:\n%s", want, text)
		}
	}
	// A section that failed in the collector is reported, not rendered as zeros.
	d["realized_7d"] = object{"collection_error": "Panel evidence could not be read: KeyError"}
	if text := briefText(d); !strings.Contains(text, "unavailable: Panel evidence") {
		t.Fatal(text)
	}
}
