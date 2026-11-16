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

// A pulse pool that fails only the fee/active-TVL gate writes exactly one
// supply-shadow row, is deduped on the next cycle, and is never sent.
func TestPulseNearMissJournaledOncePerTTL(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("SOLANA_SHADOW_PATH", filepath.Join(dir, "rejects.jsonl"))
	journal := filepath.Join(dir, "memories", "dlmm_supply_shadow.jsonl")
	verified := false
	pool := meteora.Pool{
		PoolAddress: "NearMissPool1111111111111111111111111111111", Name: "NEAR-SOL",
		TVL: 28_993, ActiveTVL: 27_400, FeeActiveTVLRatio: 0.03, VolumeWindow: 912,
		Volatility: 4.3, UniqueLPs: 3, PositionsCreated: 2,
		TokenX: meteora.Token{Address: "NearMissMint11111111111111111111111111111111", Symbol: "NEAR",
			OrganicScore: 65, MarketCap: 412_000, Holders: 1_200, TopHoldersPct: 22.4, Verified: &verified},
		TokenY:     meteora.Token{Address: meteora.SolMint, Symbol: "SOL", OrganicScore: 99},
		DlmmParams: meteora.DlmmParams{BinStep: 100},
	}
	if _, reason := meteora.Screen(pool, meteora.Pulse); !strings.HasPrefix(reason, "fee/active-TVL") {
		t.Fatalf("fixture must fail only on fee/active-TVL, got %q", reason)
	}
	discovery, err := json.Marshal(map[string]any{"data": []meteora.Pool{pool}})
	if err != nil {
		t.Fatal(err)
	}
	sent := false
	old := http.DefaultTransport
	t.Cleanup(func() { http.DefaultTransport = old })
	http.DefaultTransport = solanaTransport(func(r *http.Request) (*http.Response, error) {
		switch r.URL.Host {
		case "discovery.test":
			return &http.Response{StatusCode: 200, Header: make(http.Header),
				Body: io.NopCloser(strings.NewReader(string(discovery)))}, nil
		case "webhook.test":
			sent = true
		}
		return nil, fmt.Errorf("unexpected network request: %s", r.URL)
	})
	clock := time.Unix(1_800_000_000, 0)
	s := &Scanner{
		cfg: config.Config{DiscoverURL: "https://discovery.test", WebhookURL: "https://webhook.test",
			PulseSeenTTL: 2 * time.Hour, SupplyShadowPath: journal, PulseNearMissFeeFloor: 0.025},
		seen: store.New("", "test", time.Hour), dep: deploy.New("", "", time.Minute),
		fwd: webhook.New("https://webhook.test", "test"),
		now: func() time.Time { return clock },
	}
	rows := func() []map[string]any {
		data, err := os.ReadFile(journal)
		if err != nil {
			t.Fatal(err)
		}
		var out []map[string]any
		for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
			var row map[string]any
			if err := json.Unmarshal([]byte(line), &row); err != nil {
				t.Fatal(err)
			}
			out = append(out, row)
		}
		return out
	}

	s.pollMode(context.Background(), meteora.Pulse)
	got := rows()
	if len(got) != 1 {
		t.Fatalf("first cycle wrote %d rows, want 1", len(got))
	}
	r := got[0]
	if r["ts"] != float64(clock.Unix()) || r["pool"] != pool.PoolAddress || r["symbol"] != "NEAR" ||
		r["mint"] != pool.TokenX.Address || r["fee_active_tvl_5m"] != 0.03 || r["active_tvl"] != 27_400.0 ||
		r["tvl"] != 28_993.0 || r["volume_5m"] != 912.0 || r["mode"] != "pulse" {
		t.Fatalf("row lost a field: %v", r)
	}

	clock = clock.Add(time.Minute) // next cycle, inside PULSE_SEEN_TTL
	s.pollMode(context.Background(), meteora.Pulse)
	if n := len(rows()); n != 1 {
		t.Fatalf("second cycle wrote again: %d rows, want 1", n)
	}

	clock = clock.Add(2 * time.Hour) // past the TTL: the pool may be journaled again
	s.pollMode(context.Background(), meteora.Pulse)
	if n := len(rows()); n != 2 {
		t.Fatalf("after TTL got %d rows, want 2", n)
	}
	if sent {
		t.Fatal("a near miss must never be dispatched")
	}
}

// An unwritable journal path is logged and ignored, never a panic.
func TestSupplyShadowWriteErrorIgnored(t *testing.T) {
	dir := t.TempDir()
	blocker := filepath.Join(dir, "file")
	if err := os.WriteFile(blocker, nil, 0o600); err != nil {
		t.Fatal(err)
	}
	verified := false
	s := &Scanner{cfg: config.Config{PulseSeenTTL: time.Hour, PulseNearMissFeeFloor: 0.025,
		SupplyShadowPath: filepath.Join(blocker, "sub", "x.jsonl")}}
	s.recordSupplyShadow(meteora.Pool{PoolAddress: "p", TVL: 28_993, ActiveTVL: 27_400,
		FeeActiveTVLRatio: 0.03, VolumeWindow: 912, Volatility: 4.3,
		TokenX: meteora.Token{Address: "m", OrganicScore: 65, MarketCap: 412_000, Holders: 1_200, Verified: &verified},
		TokenY: meteora.Token{Address: meteora.SolMint, OrganicScore: 99}, DlmmParams: meteora.DlmmParams{BinStep: 100},
	}, meteora.Pulse)
}
