package robinhood

import (
	"context"
	"encoding/json"
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

// fakeCandleStore is the persistent half, kept in a map. It round-trips through
// JSON like the Redis backend does, so anything the wire form cannot carry fails
// here too.
type fakeCandleStore struct {
	m       map[string][]byte
	reads   int
	writes  int
	lastTTL time.Duration
}

func newFakeCandleStore(t *testing.T) *fakeCandleStore {
	t.Helper()
	f := &fakeCandleStore{m: map[string][]byte{}}
	SetCandleStore(f)
	t.Cleanup(func() { SetCandleStore(nil) })
	return f
}

func (f *fakeCandleStore) CachedCandles(_ context.Context, pool string, out any) bool {
	f.reads++
	b, ok := f.m[pool]
	if !ok {
		return false
	}
	return json.Unmarshal(b, out) == nil
}

func (f *fakeCandleStore) PutCandles(_ context.Context, pool string, v any, ttl time.Duration) {
	f.writes++
	f.lastTTL = ttl
	b, err := json.Marshal(v)
	if err != nil {
		return
	}
	f.m[pool] = b
}

// Why the persistent half exists: the process dies more often than the TTL. A
// restart empties the map, and every pool the entry-timing gate walks would
// otherwise be re-fetched from GeckoTerminal at once — the burst that earns the
// 429 this whole file exists to avoid.
func TestPersistedCandlesSurviveARestart(t *testing.T) {
	withFakeClock(t, time.Unix(1_700_000_000, 0))
	db := newFakeCandleStore(t)
	ohlcvCache.m = map[string]ohlcvEntry{}

	storeOHLCV("0xpool", candles{highs: []float64{2}, lows: []float64{1}, closes: []float64{1.5}})
	if db.writes != 1 {
		t.Fatalf("storing candles should write through, got %d writes", db.writes)
	}
	if db.lastTTL != gtOHLCVTTL {
		t.Fatalf("persistent TTL must match the in-memory one, got %v", db.lastTTL)
	}

	ohlcvCache.m = map[string]ohlcvEntry{} // the restart

	got, ok := cachedOHLCV("0xpool")
	if !ok || len(got.closes) != 1 || got.closes[0] != 1.5 {
		t.Fatalf("entry did not survive the restart: %v ok=%v", got, ok)
	}
	// Promoted back into memory, so the rest of the cycle costs no round-trip.
	before := db.reads
	if _, ok := cachedOHLCV("0xpool"); !ok {
		t.Fatal("second read missed")
	}
	if db.reads != before {
		t.Fatalf("a memory hit must not touch the store, reads went %d -> %d", before, db.reads)
	}
}

// A persisted entry carries its FETCH time, so a restart inherits the remaining
// freshness instead of silently restarting the window on candles that are already
// most of a candle old.
func TestPersistedCandlesExpireOnFetchTime(t *testing.T) {
	now := withFakeClock(t, time.Unix(1_700_000_000, 0))
	newFakeCandleStore(t)
	ohlcvCache.m = map[string]ohlcvEntry{}

	storeOHLCV("0xpool", candles{highs: []float64{2}, lows: []float64{1}, closes: []float64{1.5}})
	*now = now.Add(gtOHLCVTTL + time.Second)
	ohlcvCache.m = map[string]ohlcvEntry{} // the restart

	if _, ok := cachedOHLCV("0xpool"); ok {
		t.Fatal("a restart must not resurrect candles that already aged out")
	}
}

// A truncated or mismatched blob must read as a miss. Supertrend and ATR index
// highs/lows/closes in lockstep off len(closes), so misaligned bars would either
// panic or, worse, compute a band from bars that never traded together. One extra
// GT request is the cheaper failure.
func TestCorruptPersistedBlobReadsAsMiss(t *testing.T) {
	withFakeClock(t, time.Unix(1_700_000_000, 0))
	db := newFakeCandleStore(t)
	ohlcvCache.m = map[string]ohlcvEntry{}

	for name, blob := range map[string]ohlcvBlob{
		"short highs":   {Highs: []float64{2}, Lows: []float64{1, 1}, Closes: []float64{1.5, 1.6}, At: 1_700_000_000},
		"no closes":     {Highs: []float64{2}, Lows: []float64{1}, At: 1_700_000_000},
		"no fetch time": {Highs: []float64{2}, Lows: []float64{1}, Closes: []float64{1.5}},
	} {
		b, err := json.Marshal(blob)
		if err != nil {
			t.Fatalf("%s: marshal: %v", name, err)
		}
		db.m["0xpool"] = b
		if _, ok := cachedOHLCV("0xpool"); ok {
			t.Fatalf("%s: corrupt blob was served as a cache hit", name)
		}
	}
}

// With no backend installed — an operator running without REDIS_ADDR — the cache
// is memory-only, and nothing on this path may panic on the nil store.
func TestCacheWorksWithoutAPersistentBackend(t *testing.T) {
	withFakeClock(t, time.Unix(1_700_000_000, 0))
	SetCandleStore(nil)
	ohlcvCache.m = map[string]ohlcvEntry{}

	storeOHLCV("0xpool", candles{highs: []float64{2}, lows: []float64{1}, closes: []float64{1.5}})
	if _, ok := cachedOHLCV("0xpool"); !ok {
		t.Fatal("memory-only cache should still serve")
	}
	ohlcvCache.m = map[string]ohlcvEntry{}
	if _, ok := cachedOHLCV("0xpool"); ok {
		t.Fatal("without a backend there is nothing to survive a restart")
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
