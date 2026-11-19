package scanner

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/pgen0x/azimuth/internal/config"
	"github.com/pgen0x/azimuth/internal/deploy"
	"github.com/pgen0x/azimuth/internal/meteora"
	"github.com/pgen0x/azimuth/internal/store"
	"github.com/pgen0x/azimuth/internal/webhook"
)

func intp(n int) *int { return &n }

func readJSONL(t *testing.T, file string) []map[string]any {
	t.Helper()
	data, err := os.ReadFile(file)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		t.Fatal(err)
	}
	var out []map[string]any
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		if line == "" {
			continue
		}
		var row map[string]any
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			t.Fatal(err)
		}
		out = append(out, row)
	}
	return out
}

// inflowRig drives recordSmartInflow directly with an injected clock.
type inflowRig struct {
	t       *testing.T
	s       *Scanner
	clock   time.Time
	journal string
	pool    meteora.Pool
}

func newInflowRig(t *testing.T, journal string) *inflowRig {
	t.Helper()
	t.Setenv("SOLANA_CANDIDATE_WATCH_PATH", filepath.Join(t.TempDir(), "watch.jsonl"))
	r := &inflowRig{t: t, clock: time.Unix(1_800_000_000, 0), journal: journal, pool: pulseFixture("INF", 0.06)}
	r.s = &Scanner{cfg: config.Config{SmartInflowShadowPath: journal}, now: func() time.Time { return r.clock }}
	return r
}

// read feeds one GMGN reading for the rig's pool, after advancing the clock.
func (r *inflowRig) read(after time.Duration, smart, kol *int) int {
	r.t.Helper()
	r.clock = r.clock.Add(after)
	cand := &meteora.Candidate{Pool: r.pool.PoolAddress, BaseMint: r.pool.TokenX.Address, BaseSymbol: "INF",
		GmgnSmartWallets: smart, GmgnKolWallets: kol}
	r.s.recordSmartInflow(meteora.Pulse, r.pool, cand)
	return len(readJSONL(r.t, r.journal))
}

func TestSmartInflowThresholds(t *testing.T) {
	cases := []struct {
		name         string
		smart0, kol0 int
		smart1, kol1 int
		wantRow      bool
	}{
		{"smart +1 is not an inflow", 3, 0, 4, 0, false},
		{"smart +2 is an inflow", 3, 0, 5, 0, true},
		{"kol +1 is an inflow", 3, 0, 3, 1, true},
		{"a fall is not an inflow", 5, 2, 1, 0, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			journal := filepath.Join(t.TempDir(), "memories", "dlmm_smart_inflow_shadow.jsonl")
			r := newInflowRig(t, journal)
			if n := r.read(0, intp(tc.smart0), intp(tc.kol0)); n != 0 {
				t.Fatalf("first reading is a baseline, wrote %d rows", n)
			}
			n := r.read(2*time.Hour, intp(tc.smart1), intp(tc.kol1))
			if tc.wantRow != (n == 1) {
				t.Fatalf("rows = %d, want row %v", n, tc.wantRow)
			}
			if !tc.wantRow {
				return
			}
			row := readJSONL(t, journal)[0]
			want := map[string]any{
				"ts": float64(r.clock.Unix()), "pool": r.pool.PoolAddress, "mint": r.pool.TokenX.Address,
				"symbol": "INF", "smart_before": float64(tc.smart0), "smart_after": float64(tc.smart1),
				"kol_before": float64(tc.kol0), "kol_after": float64(tc.kol1), "mode": "pulse",
				"active_tvl": r.pool.ActiveTVL, "fee_active_tvl_5m": 0.06, "fee_window": "5m",
			}
			for k, v := range want {
				if row[k] != v {
					t.Fatalf("%s = %v, want %v (row %v)", k, row[k], v, row)
				}
			}
		})
	}
}

// Unknown counts are never an event, and a blank reading keeps the baseline.
func TestSmartInflowUnknownCounts(t *testing.T) {
	journal := filepath.Join(t.TempDir(), "inflow.jsonl")
	r := newInflowRig(t, journal)
	r.read(0, nil, nil)
	if n := r.read(time.Minute, intp(9), intp(9)); n != 0 {
		t.Fatalf("nil -> known wrote %d rows", n)
	}
	if n := r.read(time.Minute, nil, nil); n != 0 {
		t.Fatalf("known -> nil wrote %d rows", n)
	}
	if n := r.read(time.Minute, intp(11), nil); n != 1 {
		t.Fatalf("smart 9 -> (blank) -> 11 should compare against 9: %d rows", n)
	}
}

// At most one row per pool per 30 minutes; the baseline still moves meanwhile.
func TestSmartInflowDedup(t *testing.T) {
	journal := filepath.Join(t.TempDir(), "inflow.jsonl")
	r := newInflowRig(t, journal)
	r.read(0, intp(1), intp(0))
	if n := r.read(5*time.Minute, intp(3), intp(0)); n != 1 {
		t.Fatalf("first inflow wrote %d rows", n)
	}
	if n := r.read(10*time.Minute, intp(6), intp(0)); n != 1 {
		t.Fatalf("inflow inside the 30m window wrote again: %d rows", n)
	}
	if n := r.read(21*time.Minute, intp(8), intp(0)); n != 2 {
		t.Fatalf("inflow 31m after the first row: %d rows, want 2", n)
	}
	rows := readJSONL(t, journal)
	if rows[1]["smart_before"] != float64(6) {
		t.Fatalf("baseline did not advance inside the dedup window: %v", rows[1])
	}
}

// A baseline older than smartInflowBaselineMax is dropped, not compared.
func TestSmartInflowStaleBaseline(t *testing.T) {
	journal := filepath.Join(t.TempDir(), "inflow.jsonl")
	r := newInflowRig(t, journal)
	r.read(0, intp(1), intp(0))
	if n := r.read(smartInflowBaselineMax, intp(9), intp(5)); n != 0 {
		t.Fatalf("stale baseline produced %d rows", n)
	}
}

func TestSmartInflowOffWhenPathEmpty(t *testing.T) {
	r := newInflowRig(t, "")
	r.read(0, intp(1), intp(0))
	r.clock = r.clock.Add(time.Hour)
	r.s.recordSmartInflow(meteora.Pulse, r.pool, &meteora.Candidate{Pool: r.pool.PoolAddress,
		GmgnSmartWallets: intp(9), GmgnKolWallets: intp(9)})
	if r.s.smartLast != nil {
		t.Fatalf("journal off still tracked state: %v", r.s.smartLast)
	}
	if rows := readJSONL(t, os.Getenv("SOLANA_CANDIDATE_WATCH_PATH")); len(rows) != 0 {
		t.Fatalf("journal off requested a price path: %v", rows)
	}
}

// inflowCycle runs one pulse pollMode with GMGN faked to answer smart wallet
// counts per mint, and each pool's previous reading pre-seeded, and returns
// the forwarded symbols.
func inflowCycle(t *testing.T, journal string, pools []meteora.Pool, smart map[string]int, seed map[string]int) []string {
	t.Helper()
	dir := t.TempDir()
	t.Setenv("SOLANA_SHADOW_PATH", filepath.Join(dir, "rejects.jsonl"))
	t.Setenv("SOLANA_DELIVERY_PATH", filepath.Join(dir, "deliveries.jsonl"))
	t.Setenv("SOLANA_CANDIDATE_WATCH_PATH", filepath.Join(dir, "watch.jsonl"))
	page, err := json.Marshal(map[string]any{"data": pools})
	if err != nil {
		t.Fatal(err)
	}
	var forwarded []string
	old := http.DefaultTransport
	t.Cleanup(func() { http.DefaultTransport = old })
	http.DefaultTransport = solanaTransport(func(r *http.Request) (*http.Response, error) {
		body := `{"data":[]}`
		switch r.URL.Host {
		case "discovery.test":
			if r.URL.Query().Get("page_size") != "1" {
				body = string(page)
			}
		case "openapi.gmgn.ai":
			body = fmt.Sprintf(`{"code":0,"data":{"wallet_tags_stat":{"smart_wallets":%d,"renowned_wallets":0}}}`,
				smart[r.URL.Query().Get("address")])
		case "webhook.test":
			var signal struct{ Payload []meteora.Candidate }
			if err := json.NewDecoder(r.Body).Decode(&signal); err != nil {
				return nil, err
			}
			for _, c := range signal.Payload {
				forwarded = append(forwarded, c.BaseSymbol)
			}
			body = "{}"
		default:
			return nil, fmt.Errorf("unexpected network request: %s", r.URL)
		}
		return &http.Response{StatusCode: 200, Header: make(http.Header),
			Body: io.NopCloser(strings.NewReader(body))}, nil
	})
	clock := time.Unix(1_800_000_000, 0)
	s := &Scanner{
		cfg: config.Config{DiscoverURL: "https://discovery.test", WebhookURL: "https://webhook.test",
			SeenTTL: time.Hour, PulseSeenTTL: time.Minute, SmartInflowShadowPath: journal,
			EnableGmgnGate: true, GmgnAPIKey: "test"},
		seen: store.New("", "test", time.Hour), dep: deploy.New("", "", time.Minute),
		fwd: webhook.New("https://webhook.test", "test"),
		now: func() time.Time { return clock },
	}
	if journal != "" {
		s.smartLast = map[string]smartReading{}
		s.smartRowAt = map[string]time.Time{}
		for pool, n := range seed {
			s.smartLast[pool] = smartReading{smart: intp(n), kol: intp(0), at: clock.Add(-2 * time.Hour)}
		}
	}
	s.pollMode(context.Background(), meteora.Pulse)
	return forwarded
}

func addressPool(sym, letter string, ratio float64) meteora.Pool {
	p := pulseFixture(sym, ratio)
	p.PoolAddress = strings.Repeat(letter, 43)
	p.TokenX.Address = strings.Repeat(strings.ToLower(letter), 43)
	return p
}

// The journal row lands, the price-path sampler is asked to follow the pool,
// and the forwarded set is identical with the journal on and off.
func TestSmartInflowPollModeIsLoggingOnly(t *testing.T) {
	up := addressPool("UPX", "U", 0.06)   // smart 1 -> 4: inflow
	flat := addressPool("FLT", "F", 0.06) // smart 2 -> 3: below threshold
	pools := []meteora.Pool{up, flat}
	smart := map[string]int{up.TokenX.Address: 4, flat.TokenX.Address: 3}
	seed := map[string]int{up.PoolAddress: 1, flat.PoolAddress: 2}

	journal := filepath.Join(t.TempDir(), "memories", "dlmm_smart_inflow_shadow.jsonl")
	on := inflowCycle(t, journal, pools, smart, seed)
	rows := readJSONL(t, journal)
	if len(rows) != 1 || rows[0]["pool"] != up.PoolAddress || rows[0]["smart_before"] != float64(1) ||
		rows[0]["smart_after"] != float64(4) {
		t.Fatalf("journal rows = %v, want one UPX inflow 1->4", rows)
	}
	watch := readJSONL(t, os.Getenv("SOLANA_CANDIDATE_WATCH_PATH"))
	var requested bool
	for _, w := range watch {
		if w["source"] == "smart_inflow_shadow" && w["pool"] == up.PoolAddress && w["mode"] == "pulse" {
			requested = true
		}
	}
	if !requested {
		t.Fatalf("no price-path request for the inflow pool in watch journal: %v", watch)
	}

	off := inflowCycle(t, "", pools, smart, seed)
	if strings.Join(on, ",") != strings.Join(off, ",") || len(on) != 2 {
		t.Fatalf("forwarded with journal on %v, off %v: want the same two pools", on, off)
	}
}
