package scanner

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
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

// pulseFixture is an in-band pulse pool at the given 5m fee/active-TVL ratio.
func pulseFixture(name string, ratio float64) meteora.Pool {
	verified := true
	return meteora.Pool{
		PoolAddress: name + "Pool", Name: name + "-SOL",
		TVL: 28_993, ActiveTVL: 27_400, FeeActiveTVLRatio: ratio, VolumeWindow: 912,
		Volatility: 4.3, UniqueLPs: 3, PositionsCreated: 2,
		TokenX: meteora.Token{Address: name + "Mint", Symbol: name,
			OrganicScore: 65, MarketCap: 412_000, Holders: 1_200, TopHoldersPct: 22.4, Verified: &verified},
		TokenY:     meteora.Token{Address: meteora.SolMint, Symbol: "SOL", OrganicScore: 99},
		DlmmParams: meteora.DlmmParams{BinStep: 100},
	}
}

type shadowRun struct {
	strictCalls, widenedCalls int
	forwarded                 []string
	journal                   []string
}

// runShadowCycle drives one pulse pollMode. The fake discovery API answers the
// widened (0.025) and strict (0.050) queries from separate pages, so the test
// sees which page fed the screen and which fed the journal.
func runShadowCycle(t *testing.T, shadowOn bool, widened, strict []meteora.Pool) shadowRun {
	t.Helper()
	dir := t.TempDir()
	t.Setenv("SOLANA_SHADOW_PATH", filepath.Join(dir, "rejects.jsonl"))
	t.Setenv("SOLANA_DELIVERY_PATH", filepath.Join(dir, "deliveries.jsonl"))
	t.Setenv("SOLANA_CANDIDATE_WATCH_PATH", filepath.Join(dir, "watch.jsonl"))
	journal := filepath.Join(dir, "dlmm_supply_shadow.jsonl")
	var run shadowRun
	page := func(pools []meteora.Pool) string {
		b, err := json.Marshal(map[string]any{"data": pools})
		if err != nil {
			t.Fatal(err)
		}
		return string(b)
	}
	old := http.DefaultTransport
	t.Cleanup(func() { http.DefaultTransport = old })
	http.DefaultTransport = solanaTransport(func(r *http.Request) (*http.Response, error) {
		body := `{"data":[]}`
		switch r.URL.Host {
		case "discovery.test":
			q := r.URL.Query()
			filter, _ := url.QueryUnescape(q.Get("filter_by"))
			switch {
			case q.Get("page_size") == "1": // volatility re-read: keep page values
			case strings.Contains(filter, "fee_active_tvl_ratio>=0.025"):
				run.widenedCalls++
				body = page(widened)
			case strings.Contains(filter, "fee_active_tvl_ratio>=0.050"):
				run.strictCalls++
				body = page(strict)
			default:
				return nil, fmt.Errorf("unexpected discovery filter: %s", filter)
			}
		case "webhook.test":
			var signal struct{ Payload []meteora.Candidate }
			if err := json.NewDecoder(r.Body).Decode(&signal); err != nil {
				return nil, err
			}
			for _, c := range signal.Payload {
				run.forwarded = append(run.forwarded, c.BaseSymbol)
			}
			body = "{}"
		default:
			return nil, fmt.Errorf("unexpected network request: %s", r.URL)
		}
		return &http.Response{StatusCode: 200, Header: make(http.Header),
			Body: io.NopCloser(strings.NewReader(body))}, nil
	})
	cfg := config.Config{DiscoverURL: "https://discovery.test", WebhookURL: "https://webhook.test",
		SeenTTL: time.Hour, PulseSeenTTL: 2 * time.Hour}
	if shadowOn {
		cfg.SupplyShadowPath, cfg.PulseNearMissFeeFloor = journal, 0.025
	}
	s := &Scanner{cfg: cfg, seen: store.New("", "test", time.Hour), dep: deploy.New("", "", time.Minute),
		fwd: webhook.New("https://webhook.test", "test"),
		now: func() time.Time { return time.Unix(1_800_000_000, 0) }}
	s.pollMode(context.Background(), meteora.Pulse)
	if data, err := os.ReadFile(journal); err == nil {
		for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
			var row struct{ Symbol string }
			if err := json.Unmarshal([]byte(line), &row); err != nil {
				t.Fatal(err)
			}
			run.journal = append(run.journal, row.Symbol)
		}
	}
	return run
}

// The widened query reaches the 0.025-0.05 band the strict one cannot: the
// 0.03 pool is fetched and journaled but NOT forwarded, and the strict passer
// is forwarded exactly as before. No extra request on a non-full page.
func TestSupplyShadowWidenedPageJournalsWithoutForwarding(t *testing.T) {
	near, pass := pulseFixture("NEAR", 0.03), pulseFixture("PASS", 0.06)
	run := runShadowCycle(t, true, []meteora.Pool{pass, near}, []meteora.Pool{pass})
	if run.widenedCalls != 1 || run.strictCalls != 0 {
		t.Fatalf("calls widened=%d strict=%d, want 1/0", run.widenedCalls, run.strictCalls)
	}
	if strings.Join(run.journal, ",") != "NEAR" {
		t.Fatalf("journal = %v, want [NEAR]", run.journal)
	}
	if strings.Join(run.forwarded, ",") != "PASS" {
		t.Fatalf("forwarded = %v, want [PASS] — the shadow must not change the sent set", run.forwarded)
	}
}

// A full widened page may have truncated strict passers out of the sort, so the
// strict query runs too and ITS page is screened; the widened page only feeds
// the journal.
func TestSupplyShadowFullPageFallsBackToStrictQuery(t *testing.T) {
	near, pass := pulseFixture("NEAR", 0.03), pulseFixture("PASS", 0.06)
	widened := []meteora.Pool{near}
	for i := 1; i < meteora.DiscoverPageSize; i++ {
		widened = append(widened, pulseFixture(fmt.Sprintf("LOW%d", i), 0.01))
	}
	run := runShadowCycle(t, true, widened, []meteora.Pool{pass})
	if run.widenedCalls != 1 || run.strictCalls != 1 {
		t.Fatalf("calls widened=%d strict=%d, want 1/1", run.widenedCalls, run.strictCalls)
	}
	if strings.Join(run.journal, ",") != "NEAR" {
		t.Fatalf("journal = %v, want [NEAR]", run.journal)
	}
	if strings.Join(run.forwarded, ",") != "PASS" {
		t.Fatalf("forwarded = %v, want [PASS] from the strict page", run.forwarded)
	}
}

// Shadow off: the query and the forwarded set are exactly the pre-shadow ones.
func TestSupplyShadowOffKeepsStrictQuery(t *testing.T) {
	pass := pulseFixture("PASS", 0.06)
	run := runShadowCycle(t, false, nil, []meteora.Pool{pass})
	if run.widenedCalls != 0 || run.strictCalls != 1 {
		t.Fatalf("calls widened=%d strict=%d, want 0/1", run.widenedCalls, run.strictCalls)
	}
	if len(run.journal) != 0 || strings.Join(run.forwarded, ",") != "PASS" {
		t.Fatalf("journal=%v forwarded=%v", run.journal, run.forwarded)
	}
}
