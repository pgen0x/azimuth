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

type solanaTransport func(*http.Request) (*http.Response, error)

func (f solanaTransport) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestMomentumRecoveryRetriesAlongsideDeliveredPool(t *testing.T) {
	// The stable pool must retain its delivery TTL while the rejected pool
	// recovers on the next poll, even though the first batch was not empty.
	pools := []meteora.Pool{}
	for _, name := range []string{"stable", "recovering"} {
		pools = append(pools, meteora.Pool{
			PoolAddress: name + "PoolAddress", Name: name + "-SOL", TVL: 20_000, ActiveTVL: 20_000,
			Volatility: 2, TokenX: meteora.Token{Address: name, Symbol: name},
			TokenY: meteora.Token{Address: meteora.SolMint, Symbol: "SOL"},
		})
	}
	discovery, err := json.Marshal(map[string]any{"data": pools})
	if err != nil {
		t.Fatal(err)
	}
	cycle := 0
	var delivered []string
	old := http.DefaultTransport
	t.Cleanup(func() { http.DefaultTransport = old })
	http.DefaultTransport = solanaTransport(func(r *http.Request) (*http.Response, error) {
		body := "{}"
		switch r.URL.Host {
		case "discovery.test":
			body = string(discovery)
		case "api.dexscreener.com":
			m5 := 0
			if strings.HasSuffix(r.URL.Path, "/recovering") && cycle == 0 {
				m5 = -4
			}
			body = fmt.Sprintf(`{"pairs":[{"liquidity":{"usd":20000},"priceChange":{"m5":%d}}]}`, m5)
		case "webhook.test":
			var signal struct{ Payload []meteora.Candidate }
			if err := json.NewDecoder(r.Body).Decode(&signal); err != nil {
				return nil, err
			}
			for _, c := range signal.Payload {
				delivered = append(delivered, c.BaseMint)
			}
		default:
			return nil, fmt.Errorf("unexpected network request: %s", r.URL)
		}
		return &http.Response{StatusCode: 200, Header: make(http.Header),
			Body: io.NopCloser(strings.NewReader(body))}, nil
	})
	s := &Scanner{
		cfg: config.Config{DiscoverURL: "https://discovery.test", WebhookURL: "https://webhook.test",
			EnableMomentumGate: true, TurnoverSeenTTL: 30 * time.Minute},
		seen: store.New("", "test", time.Hour), dep: deploy.New("", "", time.Minute),
		fwd: webhook.New("https://webhook.test", "test"),
	}
	mp := meteora.ModeParams{Mode: "turnover", Timeframe: "30m", TfMinutes: 30}
	s.pollMode(context.Background(), mp)
	if strings.Join(delivered, ",") != "stable" {
		t.Fatalf("first poll delivered %v; dumping pool must be rejected", delivered)
	}
	cycle++
	s.pollMode(context.Background(), mp)
	if strings.Join(delivered, ",") != "stable,recovering" {
		t.Fatalf("recovery poll delivered %v; want stable once, then recovering", delivered)
	}
}

func TestDirectDeployOwnsEntryWhenWebhookIsAlsoConfigured(t *testing.T) {
	pool := meteora.Pool{PoolAddress: "directPoolAddress", Name: "DIRECT-SOL", TVL: 20_000, ActiveTVL: 20_000,
		Volatility: 2, TokenX: meteora.Token{Address: "direct", Symbol: "DIRECT"},
		TokenY: meteora.Token{Address: meteora.SolMint, Symbol: "SOL"}}
	discovery, err := json.Marshal(map[string]any{"data": []meteora.Pool{pool}})
	if err != nil {
		t.Fatal(err)
	}
	old := http.DefaultTransport
	t.Cleanup(func() { http.DefaultTransport = old })
	hitWebhook := false
	http.DefaultTransport = solanaTransport(func(r *http.Request) (*http.Response, error) {
		if r.URL.Host == "webhook.test" {
			hitWebhook = true
		}
		return &http.Response{StatusCode: 200, Header: make(http.Header),
			Body: io.NopCloser(strings.NewReader(string(discovery)))}, nil
	})
	marker := filepath.Join(t.TempDir(), "deploy-ran")
	script := marker + ".sh"
	if err := os.WriteFile(script, []byte("#!/bin/sh\ntouch \""+marker+"\"\necho deterministic reject\n"), 0o700); err != nil {
		t.Fatal(err)
	}
	s := &Scanner{
		cfg: config.Config{DiscoverURL: "https://discovery.test", WebhookURL: "https://webhook.test",
			SeenTTL: time.Hour, DeployTimeout: time.Minute},
		seen: store.New("", "test", time.Hour), dep: deploy.New(script, "", time.Minute),
		fwd: webhook.New("https://webhook.test", "test"),
	}
	s.pollMode(context.Background(), meteora.ModeParams{Mode: "turnover", Timeframe: "30m", TfMinutes: 30})
	if hitWebhook {
		t.Fatal("webhook received live batch even though deterministic deploy was configured")
	}
	if _, err := os.Stat(marker); err != nil {
		t.Fatalf("deterministic deploy did not run: %v", err)
	}
}
