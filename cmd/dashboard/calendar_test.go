package main

import (
	"context"
	"encoding/json"
	"errors"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// monthServer answers month collections from a stub that records each mode and zone.
func monthServer(t *testing.T, now time.Time, fail bool) (*server, *[]string) {
	calls := []string{}
	s := &server{now: func() time.Time { return now }}
	s.runCollector = func(_ context.Context, mode string, zones []string) ([]byte, error) {
		calls = append(calls, mode+"@"+strings.Join(zones, ","))
		if fail {
			return nil, errors.New("killed")
		}
		month := strings.TrimPrefix(mode, "month ")
		days := `[]`
		if month == "2026-09" {
			days = `[{"day":"2026-09-01","status":"ok","cash_sol":1,"d_cash_sol":null}]`
		}
		return []byte(`{"collected_at":1,"north_star":{"month":"` + month + `","first_month":"2026-09","days":` + days + `}}`), nil
	}
	return s, &calls
}

func get(t *testing.T, s *server, path string) *httptest.ResponseRecorder {
	t.Helper()
	cookie := signIn(t, s)
	r := httptest.NewRequest("GET", path, nil)
	r.Host = "localhost"
	r.AddCookie(cookie)
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	return w
}

func TestParseMonthBounds(t *testing.T) {
	now := time.Date(2026, 11, 30, 20, 0, 0, 0, time.UTC) // already December in Asia/Jakarta
	jkt, _ := time.LoadLocation("Asia/Jakarta")
	for _, tc := range []struct {
		query string
		loc   *time.Location
		want  string
		ok    bool
	}{
		{"", time.UTC, "2026-11", true},
		{"", jkt, "2026-12", true},
		{"2026-12", jkt, "2026-12", true},
		{"2026-12", time.UTC, "", false}, // future in UTC
		{"2026-09", time.UTC, "2026-09", true},
		{"2020-01", time.UTC, "2020-01", true},
		{"2019-12", time.UTC, "", false},
		{"2026-13", time.UTC, "", false},
		{"2026-00", time.UTC, "", false},
		{"2026-9", time.UTC, "", false},
		{"26-09", time.UTC, "", false},
		{"2026-09-01", time.UTC, "", false},
		{"../2026-09", time.UTC, "", false},
	} {
		got, err := parseMonth(tc.query, now, tc.loc)
		if (err == nil) != tc.ok || got != tc.want {
			t.Errorf("parseMonth(%q, %s) = %q, %v", tc.query, tc.loc, got, err)
		}
	}
}

func TestMonthEndpoint(t *testing.T) {
	now := time.Date(2026, 11, 19, 12, 0, 0, 0, time.UTC)
	s, calls := monthServer(t, now, false)
	for _, tc := range []struct {
		path   string
		status int
		want   string
	}{
		{"/api/capital/month", 200, `"month":"2026-11"`},
		{"/api/capital/month?month=2026-09&tz=Asia/Jakarta", 200, `"day":"2026-09-01"`},
		{"/api/capital/month?month=2026-08", 200, `"days":[]`}, // before the data: empty, not an error
		{"/api/capital/month?month=2026-13", 400, "invalid month"},
		{"/api/capital/month?month=2026-9", 400, "invalid month"},
		{"/api/capital/month?month=2026-12", 400, "out of range"},
		{"/api/capital/month?month=1999-01", 400, "out of range"},
		{"/api/capital/month?month=2026-09&tz=Mars/Olympus", 200, `"tz_fallback":true`},
	} {
		w := get(t, s, tc.path)
		if w.Code != tc.status || !strings.Contains(w.Body.String(), tc.want) {
			t.Fatalf("%s: %d %s", tc.path, w.Code, w.Body.String())
		}
	}
	want := []string{"month 2026-11@UTC", "month 2026-09@Asia/Jakarta", "month 2026-08@UTC", "month 2026-09@UTC"}
	if strings.Join(*calls, ";") != strings.Join(want, ";") {
		t.Fatalf("collector calls %v", *calls)
	}
	// Cached: a repeat costs no collector run; the current month expires with the slow period.
	get(t, s, "/api/capital/month?month=2026-09&tz=Asia/Jakarta")
	get(t, s, "/api/capital/month")
	if len(*calls) != 4 {
		t.Fatalf("cache miss: %v", *calls)
	}
	s.now = func() time.Time { return now.Add(monthCurrentTTL) }
	get(t, s, "/api/capital/month")
	get(t, s, "/api/capital/month?month=2026-09&tz=Asia/Jakarta")
	if len(*calls) != 5 {
		t.Fatalf("current month should refresh, past month stay cached: %v", *calls)
	}
}

func TestMonthEndpointFailureAndAccess(t *testing.T) {
	s, _ := monthServer(t, time.Date(2026, 11, 19, 0, 0, 0, 0, time.UTC), true)
	if w := get(t, s, "/api/capital/month?month=2026-09"); w.Code != 503 {
		t.Fatalf("collector failure: %d %s", w.Code, w.Body.String())
	}
	if len(s.months) != 0 {
		t.Fatal("a failed collection must not be cached")
	}
	r := httptest.NewRequest("GET", "/api/capital/month", nil)
	r.Host = "localhost"
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	if w.Code != 401 {
		t.Fatalf("unauthenticated month: %d", w.Code)
	}
}

func TestMonthCacheIsBounded(t *testing.T) {
	s := &server{}
	base := time.Unix(0, 0)
	for i := 0; i < monthCacheMax+5; i++ {
		s.storeMonth(string(rune('a'+i)), monthEntry{at: base.Add(time.Duration(i) * time.Second), ttl: time.Hour})
	}
	if len(s.months) != monthCacheMax {
		t.Fatalf("cache size %d", len(s.months))
	}
	if _, ok := s.months["a"]; ok {
		t.Fatal("oldest entry should be evicted first")
	}
}

func TestPriceFailsSoftAndCaches(t *testing.T) {
	now := time.Date(2026, 11, 19, 0, 0, 0, 0, time.UTC)
	fetches, fail := 0, true
	s := &server{now: func() time.Time { return now }}
	s.fetchPrice = func(context.Context) (float64, error) {
		fetches++
		if fail {
			return 0, errors.New("network down")
		}
		return 150.25, nil
	}
	read := func() object {
		w := get(t, s, "/api/price/sol")
		if w.Code != 200 {
			t.Fatalf("price must answer 200: %d", w.Code)
		}
		var v object
		json.Unmarshal(w.Body.Bytes(), &v)
		return v
	}
	if v := read(); v["status"] != "unavailable" || v["usd"] != nil {
		t.Fatalf("fail-soft: %v", v)
	}
	read()
	if fetches != 1 {
		t.Fatalf("a failure must back off before retrying: %d fetches", fetches)
	}
	fail, now = false, now.Add(priceFailTTL)
	if v := read(); v["status"] != "ok" || v["usd"] != 150.25 {
		t.Fatalf("recovered: %v", v)
	}
	now = now.Add(priceTTL - time.Second)
	read()
	if fetches != 2 {
		t.Fatalf("a good price is cached for priceTTL: %d fetches", fetches)
	}
	now = now.Add(time.Second)
	read()
	if fetches != 3 {
		t.Fatalf("stale price must refetch: %d fetches", fetches)
	}
}

func TestPriceWorksWithoutSnapshot(t *testing.T) {
	// The snapshot gate (503 until the first collection) must not hide the price or month routes.
	s := &server{fetchPrice: func(context.Context) (float64, error) { return 0, errors.New("x") }}
	if w := get(t, s, "/api/price/sol"); w.Code != 200 {
		t.Fatalf("%d", w.Code)
	}
}

func TestParseSOLPrice(t *testing.T) {
	if v, err := parseSOLPrice(strings.NewReader(`{"` + solMint + `":{"usdPrice":73.5,"decimals":9}}`)); err != nil || v != 73.5 {
		t.Fatalf("%v %v", v, err)
	}
	for _, body := range []string{`{}`, `{"` + solMint + `":{"usdPrice":0}}`, `{"` + solMint + `":{"usdPrice":-1}}`, `not json`} {
		if _, err := parseSOLPrice(strings.NewReader(body)); err == nil {
			t.Fatalf("accepted %s", body)
		}
	}
}

// rhMonthServer answers Robinhood month collections; it fails the test if the Solana month mode is asked for.
func rhMonthServer(t *testing.T, now time.Time) (*server, *[]string) {
	calls := []string{}
	s := &server{now: func() time.Time { return now }}
	s.runCollector = func(_ context.Context, mode string, zones []string) ([]byte, error) {
		calls = append(calls, mode+"@"+strings.Join(zones, ","))
		if strings.HasPrefix(mode, "month ") {
			return []byte(`{"collected_at":1,"north_star":{"month":"` + strings.TrimPrefix(mode, "month ") + `","days":[]}}`), nil
		}
		month := strings.TrimPrefix(mode, "rhmonth ")
		days := `{}`
		if month == "2026-08" {
			// One measured ETH day and one wholly unmeasured day: null must reach the client as null, never 0.
			days = `{"2026-08-03":{"ETH":{"closes":1,"measured":1,"unmeasured":0,"realized_quote":0.01},"gas_eth":0.001},` +
				`"2026-08-04":{"ETH":{"closes":1,"measured":0,"unmeasured":1,"realized_quote":null},"gas_eth":null}}`
		}
		return []byte(`{"collected_at":1,"robinhood":{"month":"` + month + `","first_month":"2026-07","days":` + days + `}}`), nil
	}
	return s, &calls
}

func TestRobinhoodMonthEndpoint(t *testing.T) {
	now := time.Date(2026, 11, 19, 12, 0, 0, 0, time.UTC)
	s, calls := rhMonthServer(t, now)
	for _, tc := range []struct {
		path   string
		status int
		want   string
	}{
		{"/api/robinhood/month", 200, `"month":"2026-11"`},
		{"/api/robinhood/month?month=2026-08&tz=Asia/Jakarta", 200, `"realized_quote":null`},
		{"/api/robinhood/month?month=2026-06", 200, `"days":{}`}, // before the first close: empty, not an error
		{"/api/robinhood/month?month=2026-13", 400, "invalid month"},
		{"/api/robinhood/month?month=2026-12", 400, "out of range"},
		{"/api/robinhood/month?month=../2026-08", 400, "invalid month"},
	} {
		w := get(t, s, tc.path)
		if w.Code != tc.status || !strings.Contains(w.Body.String(), tc.want) {
			t.Fatalf("%s: %d %s", tc.path, w.Code, w.Body.String())
		}
		if tc.status == 200 && strings.Contains(w.Body.String(), `"north_star"`) {
			t.Fatalf("%s leaked the Solana section: %s", tc.path, w.Body.String())
		}
	}
	want := []string{"rhmonth 2026-11@UTC", "rhmonth 2026-08@Asia/Jakarta", "rhmonth 2026-06@UTC"}
	if strings.Join(*calls, ";") != strings.Join(want, ";") {
		t.Fatalf("collector calls %v", *calls)
	}
	// The cache is per venue: the same month and zone on the Solana route is its own collection.
	get(t, s, "/api/robinhood/month?month=2026-08&tz=Asia/Jakarta")
	get(t, s, "/api/capital/month?month=2026-08&tz=Asia/Jakarta")
	if len(*calls) != 4 || (*calls)[3] != "month 2026-08@Asia/Jakarta" {
		t.Fatalf("per-kind cache: %v", *calls)
	}
}

func TestRobinhoodMonthEmptyAndFailure(t *testing.T) {
	now := time.Date(2026, 11, 19, 0, 0, 0, 0, time.UTC)
	s := &server{now: func() time.Time { return now }}
	s.runCollector = func(context.Context, string, []string) ([]byte, error) {
		return []byte(`{"collected_at":1,"robinhood":{"month":"2026-11","first_month":null,"days":{}}}`), nil
	}
	if w := get(t, s, "/api/robinhood/month"); w.Code != 200 || !strings.Contains(w.Body.String(), `"first_month":null`) {
		t.Fatalf("empty journal: %d %s", w.Code, w.Body.String())
	}
	f, _ := monthServer(t, now, true)
	if w := get(t, f, "/api/robinhood/month?month=2026-09"); w.Code != 503 {
		t.Fatalf("collector failure: %d %s", w.Code, w.Body.String())
	}
	if len(f.months) != 0 {
		t.Fatal("a failed collection must not be cached")
	}
	r := httptest.NewRequest("GET", "/api/robinhood/month", nil)
	r.Host = "localhost"
	w := httptest.NewRecorder()
	f.ServeHTTP(w, r)
	if w.Code != 401 {
		t.Fatalf("unauthenticated month: %d", w.Code)
	}
}

func TestETHPriceFailsSoftApartFromSOL(t *testing.T) {
	now := time.Date(2026, 11, 19, 0, 0, 0, 0, time.UTC)
	eth, sol := 0, 0
	s := &server{now: func() time.Time { return now }}
	s.fetchPrice = func(context.Context) (float64, error) { sol++; return 150, nil }
	s.fetchETHPrice = func(context.Context) (float64, error) { eth++; return 0, errors.New("network down") }
	read := func(path string) object {
		w := get(t, s, path)
		if w.Code != 200 {
			t.Fatalf("%s must answer 200: %d", path, w.Code)
		}
		var v object
		json.Unmarshal(w.Body.Bytes(), &v)
		return v
	}
	if v := read("/api/price/eth"); v["status"] != "unavailable" || v["usd"] != nil || v["asset"] != "ETH" {
		t.Fatalf("fail-soft: %v", v)
	}
	if v := read("/api/price/sol"); v["status"] != "ok" || v["usd"] != 150.0 || v["asset"] != "SOL" {
		t.Fatalf("an ETH failure must not touch the SOL price: %v", v)
	}
	read("/api/price/eth")
	if eth != 1 || sol != 1 {
		t.Fatalf("each price backs off and caches on its own: eth %d sol %d", eth, sol)
	}
	s.fetchETHPrice = func(context.Context) (float64, error) { eth++; return 3012.5, nil }
	now = now.Add(priceFailTTL)
	if v := read("/api/price/eth"); v["status"] != "ok" || v["usd"] != 3012.5 {
		t.Fatalf("recovered: %v", v)
	}
}

func TestParseJupiterPriceETH(t *testing.T) {
	if v, err := parseJupiterPrice(strings.NewReader(`{"`+ethMint+`":{"usdPrice":3012.5}}`), ethMint); err != nil || v != 3012.5 {
		t.Fatalf("%v %v", v, err)
	}
	// The SOL entry is not an ETH price.
	if _, err := parseJupiterPrice(strings.NewReader(`{"`+solMint+`":{"usdPrice":150}}`), ethMint); err == nil {
		t.Fatal("accepted another mint's price")
	}
}

func TestRobinhoodViewCarriesWalletNAVPerZone(t *testing.T) {
	data := object{"robinhood": map[string]any{"logs": []any{"a", "b"}}}
	panels := object{"robinhood": object{"tz": "Asia/Tokyo"}, "rh_nav": object{"tz": "Asia/Tokyo", "latest": nil}}
	v := robinhoodView(data, panels, 1)
	nav, ok := v["nav"].(object)
	if !ok || nav["tz"] != "Asia/Tokyo" {
		t.Fatalf("nav panel missing from the Robinhood view: %v", v)
	}
	if _, ok := object(robinhoodView(object{}, object{}, 1))["nav"]; !ok {
		t.Fatal("nav key must exist (null) even without a snapshot panel")
	}
}
