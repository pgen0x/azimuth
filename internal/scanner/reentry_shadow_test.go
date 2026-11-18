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

// reentryHarness runs pulse pollMode cycles against a fake discovery page, with
// the named pools' symbols in re-entry cooldown, and reports what was forwarded.
type reentryHarness struct {
	t         *testing.T
	s         *Scanner
	clock     time.Time
	forwarded []string
	journal   string
}

func newReentryHarness(t *testing.T, journal string, pools []meteora.Pool, cooling map[string]bool) *reentryHarness {
	t.Helper()
	dir := t.TempDir()
	t.Setenv("SOLANA_SHADOW_PATH", filepath.Join(dir, "rejects.jsonl"))
	t.Setenv("SOLANA_DELIVERY_PATH", filepath.Join(dir, "deliveries.jsonl"))
	t.Setenv("SOLANA_CANDIDATE_WATCH_PATH", filepath.Join(dir, "watch.jsonl"))
	h := &reentryHarness{t: t, clock: time.Unix(1_800_000_000, 0), journal: journal}
	page, err := json.Marshal(map[string]any{"data": pools})
	if err != nil {
		t.Fatal(err)
	}
	old := http.DefaultTransport
	t.Cleanup(func() { http.DefaultTransport = old })
	http.DefaultTransport = solanaTransport(func(r *http.Request) (*http.Response, error) {
		body := `{"data":[]}`
		switch r.URL.Host {
		case "discovery.test":
			if r.URL.Query().Get("page_size") != "1" {
				body = string(page)
			}
		case "webhook.test":
			var signal struct{ Payload []meteora.Candidate }
			if err := json.NewDecoder(r.Body).Decode(&signal); err != nil {
				return nil, err
			}
			for _, c := range signal.Payload {
				h.forwarded = append(h.forwarded, c.BaseSymbol)
			}
			body = "{}"
		default:
			return nil, fmt.Errorf("unexpected network request: %s", r.URL)
		}
		return &http.Response{StatusCode: 200, Header: make(http.Header),
			Body: io.NopCloser(strings.NewReader(body))}, nil
	})
	h.s = &Scanner{
		cfg: config.Config{DiscoverURL: "https://discovery.test", WebhookURL: "https://webhook.test",
			SeenTTL: time.Hour, PulseSeenTTL: time.Minute, ReentryShadowPath: journal},
		seen: store.New("", "test", time.Hour), dep: deploy.New("", "", time.Minute),
		fwd: webhook.New("https://webhook.test", "test"),
		now: func() time.Time { return h.clock },
		cooldownLookup: func(_ context.Context, symbol, _, _ string) time.Duration {
			if cooling[symbol] {
				return 45 * time.Minute
			}
			return 0
		},
	}
	return h
}

func (h *reentryHarness) cycle(after time.Duration) {
	h.clock = h.clock.Add(after)
	h.s.pollMode(context.Background(), meteora.Pulse)
}

func (h *reentryHarness) rows() []map[string]any {
	data, err := os.ReadFile(h.journal)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		h.t.Fatal(err)
	}
	var out []map[string]any
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		var row map[string]any
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			h.t.Fatal(err)
		}
		out = append(out, row)
	}
	return out
}

// A pool stopped only by the cooldown writes one row, deduped for 10m; a pool
// that also fails a Screen gate writes nothing; the forwarded set is the same
// as with the journal off.
func TestReentryShadowBlockedByCooldownOnly(t *testing.T) {
	cooled := pulseFixture("COOL", 0.06)  // passes Screen, in cooldown
	failing := pulseFixture("FAIL", 0.01) // fails fee/active-TVL AND in cooldown
	free := pulseFixture("FREE", 0.06)    // passes, no cooldown
	pools := []meteora.Pool{cooled, failing, free}
	cooling := map[string]bool{"COOL": true, "FAIL": true}

	journal := filepath.Join(t.TempDir(), "memories", "dlmm_reentry_shadow.jsonl")
	h := newReentryHarness(t, journal, pools, cooling)
	h.cycle(0)
	rows := h.rows()
	if len(rows) != 1 {
		t.Fatalf("first cycle wrote %d rows, want 1: %v", len(rows), rows)
	}
	r := rows[0]
	if r["kind"] != "blocked" || r["pool"] != cooled.PoolAddress || r["mint"] != cooled.TokenX.Address ||
		r["block_reason"] != "cooldown" || r["fee_active_tvl_5m"] != 0.06 || r["active_tvl"] != cooled.ActiveTVL ||
		r["ts"] != float64(h.clock.Unix()) || r["cooldown_remaining_secs"] != float64(45*60) {
		t.Fatalf("row lost a field: %v", r)
	}
	h.cycle(5 * time.Minute) // inside the dedup window
	if n := len(h.rows()); n != 1 {
		t.Fatalf("dedup window wrote again: %d rows", n)
	}
	h.cycle(6 * time.Minute) // 11m after the first row
	if n := len(h.rows()); n != 2 {
		t.Fatalf("after dedup window got %d rows, want 2", n)
	}

	// Same pools with the journal off: identical forwarded set.
	off := newReentryHarness(t, "", pools, cooling)
	off.cycle(0)
	if got, want := strings.Join(off.forwarded, ","), "FREE"; got != want {
		t.Fatalf("journal off forwarded %q, want %q", got, want)
	}
	if strings.Join(h.forwarded, ",") != "FREE" {
		t.Fatalf("journal on forwarded %v, want only FREE (and only once)", h.forwarded)
	}
}
