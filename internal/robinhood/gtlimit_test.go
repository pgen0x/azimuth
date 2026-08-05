package robinhood

import (
	"strings"
	"testing"
	"time"
)

// withFakeClock pins gtNow and restores it, so these tests never sleep and never
// depend on wall time.
func withFakeClock(t *testing.T, start time.Time) *time.Time {
	t.Helper()
	now := start
	gtNow = func() time.Time { return now }
	t.Cleanup(func() { gtNow = time.Now })
	return &now
}

// The gate's whole job is spacing requests: a burst must come out gtMinInterval
// apart rather than all at once, because the burst is what earns the 429.
func TestGateSpacesRequests(t *testing.T) {
	now := withFakeClock(t, time.Unix(1_700_000_000, 0))
	var slept []time.Duration
	g := &gtGate{sleep: func(d time.Duration) { slept = append(slept, d) }}

	for i := 0; i < 3; i++ {
		if err := g.acquire(); err != nil {
			t.Fatalf("acquire %d: %v", i, err)
		}
	}
	// The first call is free (nothing reserved yet); each later one waits another
	// interval, because the fake clock never advances.
	if len(slept) != 2 {
		t.Fatalf("want 2 waits for 3 back-to-back calls, got %d (%v)", len(slept), slept)
	}
	if slept[0] != gtMinInterval || slept[1] != 2*gtMinInterval {
		t.Fatalf("waits should grow one interval per queued call, got %v", slept)
	}

	// Once enough time has passed, the next call is free again.
	*now = now.Add(10 * gtMinInterval)
	slept = nil
	if err := g.acquire(); err != nil {
		t.Fatalf("acquire after idle: %v", err)
	}
	if len(slept) != 0 {
		t.Fatalf("an idle gate must not sleep, slept %v", slept)
	}
}

// A 429 has to stop traffic, not merely slow it: pushing through an active
// refusal is what turns one 429 into a long one.
func TestGateCooldownBlocksUntilItExpires(t *testing.T) {
	now := withFakeClock(t, time.Unix(1_700_000_000, 0))
	g := &gtGate{sleep: func(time.Duration) {}}

	g.penalize()
	err := g.acquire()
	if err == nil {
		t.Fatal("acquire during cooldown must fail fast")
	}
	if !strings.Contains(err.Error(), "cooldown") {
		t.Fatalf("error should name the cooldown, got %q", err)
	}

	// Still cooling one tick before the deadline...
	*now = now.Add(gtCooldown - time.Second)
	if err := g.acquire(); err == nil {
		t.Fatal("cooldown ended early")
	}
	// ...and open again after it.
	*now = now.Add(2 * time.Second)
	if err := g.acquire(); err != nil {
		t.Fatalf("cooldown should have expired: %v", err)
	}
}

// A later penalty must never shorten an active cooldown.
func TestGatePenalizeNeverShortensCooldown(t *testing.T) {
	now := withFakeClock(t, time.Unix(1_700_000_000, 0))
	g := &gtGate{sleep: func(time.Duration) {}}

	g.penalize()
	*now = now.Add(gtCooldown / 2)
	g.penalize() // extends the deadline
	*now = now.Add(gtCooldown / 2)
	// Half of the second cooldown remains, so the gate must still be closed.
	if err := g.acquire(); err == nil {
		t.Fatal("the second penalize should have extended the cooldown past this point")
	}
}

// A queue longer than gtMaxWait is worse than a miss — the scanner loop would
// stall behind it — so the gate refuses instead of sleeping.
func TestGateRefusesRatherThanStall(t *testing.T) {
	withFakeClock(t, time.Unix(1_700_000_000, 0))
	g := &gtGate{sleep: func(time.Duration) {}}

	var lastErr error
	for i := 0; i < 100; i++ {
		if lastErr = g.acquire(); lastErr != nil {
			break
		}
	}
	if lastErr == nil {
		t.Fatal("an unbounded queue should eventually be refused")
	}
	if !strings.Contains(lastErr.Error(), "queue too long") {
		t.Fatalf("want a queue-length refusal, got %q", lastErr)
	}
}

// The cache is what actually cuts request volume, so its TTL boundary matters:
// inside it serves, outside it must miss.
func TestOHLCVCacheServesUntilTTL(t *testing.T) {
	now := withFakeClock(t, time.Unix(1_700_000_000, 0))
	ohlcvCache.m = map[string]ohlcvEntry{}

	storeOHLCV("0xpool", candles{highs: []float64{2}, lows: []float64{1}, closes: []float64{1.5}})

	if got, ok := cachedOHLCV("0xpool"); !ok || got.closes[0] != 1.5 {
		t.Fatalf("fresh entry should hit, got %v ok=%v", got, ok)
	}
	*now = now.Add(gtOHLCVTTL - time.Second)
	if _, ok := cachedOHLCV("0xpool"); !ok {
		t.Fatal("entry expired one second early")
	}
	*now = now.Add(2 * time.Second)
	if _, ok := cachedOHLCV("0xpool"); ok {
		t.Fatal("entry outlived its TTL")
	}
	if _, ok := cachedOHLCV("0xother"); ok {
		t.Fatal("unknown pool must miss")
	}
}
