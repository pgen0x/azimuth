package robinhood

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"
)

// One process-wide throttle in front of every GeckoTerminal call this package
// makes, plus a cache for the one call that repeats.
//
// The problem it solves, measured 2026-08-05: rh-usdg-ladder logged 34
// `geckoterminal status 429` fetch errors in three hours — roughly a quarter of
// its cycles discovered NOTHING, because the enrich call is the first GT request
// of a cycle and the mode fails closed without it. The requests are not one per
// cycle:
//
//   - one /pools/multi/ enrich per mature-family mode per cycle,
//   - one /ohlcv/ per candidate walked by the entry-timing gate, which on a
//     24-candidate batch can be most of the batch, and
//   - the new_pools and trending_pools pages when Fresh is enabled.
//
// The budget is smaller than this file first assumed. GT's public tier documents
// ~10 requests/minute per IP, not ~30, and the IP is shared: uni_monitor.py polls
// the same API for every open position's exit rules from a process this gate
// cannot see. That process was the larger spender until it was batched into one
// /pools/multi/ call per tick, which is why the spacing below can now leave it a
// slice of the budget instead of half. The two changes are one change: raising
// the interval here without batching the monitor would only make this side slower
// at losing the same race.
//
// Three mechanisms, cheapest first:
//
//  1. Spacing. Requests are serialized at least gtMinInterval apart, so a batch
//     of OHLCV reads becomes a paced trickle instead of a burst.
//  2. Cooldown. A 429 means the budget is already spent, and pushing through it
//     extends the refusal. For the next gtCooldown, calls fail FAST with a clear
//     error instead of spending latency to be refused.
//  3. Caching, for OHLCV only. The entry-timing gate re-reads the SAME pools
//     every cycle (the mature feed is stable) and asks for 15-minute candles, so
//     a TTL well under one candle costs no signal and removes most of the request
//     volume outright. Enrich is deliberately NOT cached: it is one call per cycle
//     carrying the flow numbers every gate reads, and a stale reserve or volume
//     figure would quietly change what the screen means.
const (
	// ~8 requests/minute at steady state, which is the documented ~10 minus the
	// slice uni_monitor.py needs: one /pools/multi/ per ~82s tick, plus the rare
	// OHLCV read when an exit rule fires and wants indicator confirmation.
	gtMinInterval = 7 * time.Second
	// Long enough to leave a one-minute window entirely, short enough that a
	// single 429 costs at most a cycle or two.
	gtCooldown = 75 * time.Second
	// Under one 15m candle: an entry-timing decision can be at most this stale,
	// which cannot flip a supertrend band built from 30+ candles. Sized just under
	// the candle rather than at the old 4m because that TTL re-fetched the same
	// pool up to four times per candle for a band that cannot move between them —
	// pure request volume for no signal.
	gtOHLCVTTL = 13 * time.Minute
	// A caller should not block indefinitely behind a long queue. Past this it is
	// better to fail open (indicators) or skip the cycle (enrich) than to stall
	// the scanner loop. Three requests deep at the interval above: enough for an
	// enrich plus a short entry-timing walk in one cycle, and still far inside the
	// one-minute poll so a queue can never overlap the next cycle's.
	gtMaxWait = 21 * time.Second
)

// gtNow is the gate's clock, injectable for tests. The repo convention is to take
// `now` from the caller, but a rate limiter is the one thing that cannot: it is
// consulted from inside leaf HTTP helpers whose signatures are shared with
// unthrottled paths, and threading a clock through all of them would put a time
// argument on functions with no other use for one. Confining the read to this
// variable keeps it in a single overridable place.
var gtNow = time.Now

var gt = &gtGate{}

type gtGate struct {
	mu        sync.Mutex
	next      time.Time // earliest permitted request
	coolUntil time.Time // 429 backoff deadline
	// sleep is the gate's delay, injectable so tests need not actually wait.
	sleep func(time.Duration)
}

// acquire blocks until a request may be sent, or returns an error if the gate is
// in 429 cooldown or the wait would exceed gtMaxWait. Callers treat that error
// like any other GT failure, which in this package means fail-open for
// indicators and skip-the-cycle for discovery.
func (g *gtGate) acquire() error {
	g.mu.Lock()
	now := gtNow()
	if now.Before(g.coolUntil) {
		left := g.coolUntil.Sub(now).Truncate(time.Second)
		g.mu.Unlock()
		return fmt.Errorf("geckoterminal rate-limit cooldown, %v left", left)
	}
	wait := time.Duration(0)
	if g.next.After(now) {
		wait = g.next.Sub(now)
	}
	if wait > gtMaxWait {
		g.mu.Unlock()
		return fmt.Errorf("geckoterminal request queue too long (%v wait)", wait.Truncate(time.Millisecond))
	}
	// Reserve the slot before unlocking, so concurrent callers queue behind it
	// instead of all measuring the same free instant.
	g.next = now.Add(wait + gtMinInterval)
	sleep := g.sleep
	g.mu.Unlock()

	if wait > 0 {
		if sleep == nil {
			sleep = time.Sleep
		}
		sleep(wait)
	}
	return nil
}

// penalize starts the cooldown. Call it on any 429 from any GT endpoint: the
// budget is per-IP, so one endpoint's refusal is every endpoint's problem.
func (g *gtGate) penalize() {
	g.mu.Lock()
	defer g.mu.Unlock()
	until := gtNow().Add(gtCooldown)
	if until.After(g.coolUntil) {
		g.coolUntil = until
		log.Printf("robinhood: geckoterminal 429 — pausing all GT calls for %v", gtCooldown)
	}
}

// ohlcvCache memoizes fetchOHLCV per pool. Stored values are immutable: the
// candles slices are never written after the fetch that built them, and the
// indicator math only reads.
var ohlcvCache = struct {
	mu sync.Mutex
	m  map[string]ohlcvEntry
}{m: map[string]ohlcvEntry{}}

type ohlcvEntry struct {
	c  candles
	at time.Time
}

// CandleStore is the cache's optional persistent half. An in-process map dies
// with the process, and the process dies more often than the cache TTL: the
// daemon restarted twice on 2026-08-05 and each restart re-fetched every walked
// pool's candles from GeckoTerminal at once — the burst that earns the 429 the
// rest of this file exists to avoid. *store.Seen satisfies this interface, and
// the interface is declared HERE rather than importing the store so the
// dependency keeps pointing one way (scanner -> robinhood); the scanner installs
// the backend at startup.
//
// ok=false must mean "not cached" for every failure mode — no backend, no entry,
// unreadable value — because the only alternative reading is a wrong candle set.
type CandleStore interface {
	CachedCandles(ctx context.Context, pool string, out any) bool
	PutCandles(ctx context.Context, pool string, v any, ttl time.Duration)
}

var (
	candleDBMu sync.Mutex
	candleDB   CandleStore
)

// SetCandleStore installs the persistent layer. Called once at startup; nil (the
// default) leaves the cache memory-only, which is what an operator running
// without REDIS_ADDR gets.
func SetCandleStore(cs CandleStore) {
	candleDBMu.Lock()
	candleDB = cs
	candleDBMu.Unlock()
}

func candleStore() CandleStore {
	candleDBMu.Lock()
	defer candleDBMu.Unlock()
	return candleDB
}

// ohlcvBlob is the wire form of a cached candle set. candles' fields are
// unexported — nothing outside this package builds one — so encoding/json cannot
// see them; this mirror exists only to cross a restart. At carries the FETCH
// time, not the write time, so a restart inherits the entry's remaining
// freshness instead of silently restarting the TTL on candles that are already
// most of a candle old.
type ohlcvBlob struct {
	Highs  []float64 `json:"h"`
	Lows   []float64 `json:"l"`
	Closes []float64 `json:"c"`
	At     int64     `json:"at"` // unix seconds
}

// toCandles converts a decoded blob back, rejecting anything the indicator math
// must not see. Mismatched slice lengths are the dangerous case: supertrend and
// ATR index highs/lows/closes in lockstep off len(closes), so a blob truncated
// by a partial write or a schema change would panic or, worse, compute a band
// from misaligned bars. A short/corrupt blob reads as a cache miss — one extra
// GT request, versus a fabricated entry signal.
func (b ohlcvBlob) toCandles() (candles, time.Time, bool) {
	n := len(b.Closes)
	if n == 0 || len(b.Highs) != n || len(b.Lows) != n || b.At <= 0 {
		return candles{}, time.Time{}, false
	}
	return candles{highs: b.Highs, lows: b.Lows, closes: b.Closes}, time.Unix(b.At, 0), true
}

// cachedOHLCV returns a fresh-enough cached candle set, if any: memory first,
// then the persistent layer, whose hits are promoted back into memory so the
// rest of the cycle's candidates cost neither a Redis round-trip nor a request.
//
// context.Background() is deliberate here, for the same reason gtNow exists:
// these helpers are called from inside leaf HTTP paths (fetchOHLCV) whose
// signatures are shared with unthrottled callers, and threading a context
// through them would put one on functions with no other use for it. The read is
// a single local Redis GET on the hot path of a request we are trying NOT to
// make — there is nothing here worth cancelling.
func cachedOHLCV(pool string) (candles, bool) {
	ohlcvCache.mu.Lock()
	e, ok := ohlcvCache.m[pool]
	ohlcvCache.mu.Unlock()
	if ok && gtNow().Sub(e.at) <= gtOHLCVTTL {
		return e.c, true
	}

	db := candleStore()
	if db == nil {
		return candles{}, false
	}
	var b ohlcvBlob
	if !db.CachedCandles(context.Background(), pool, &b) {
		return candles{}, false
	}
	c, at, ok := b.toCandles()
	if !ok {
		return candles{}, false
	}
	// The persistent TTL should already have expired a stale entry, but the check
	// is cheap and this side must not out-live the in-memory rule: a longer TTL
	// configured on the Redis instance would otherwise widen the freshness
	// contract the entry-timing gate is documented against.
	if gtNow().Sub(at) > gtOHLCVTTL {
		return candles{}, false
	}
	ohlcvCache.mu.Lock()
	ohlcvCache.m[pool] = ohlcvEntry{c: c, at: at}
	ohlcvCache.mu.Unlock()
	return c, true
}

func storeOHLCV(pool string, c candles) {
	now := gtNow()
	ohlcvCache.mu.Lock()
	ohlcvCache.m[pool] = ohlcvEntry{c: c, at: now}
	ohlcvCache.mu.Unlock()

	if db := candleStore(); db != nil {
		db.PutCandles(context.Background(), pool, ohlcvBlob{
			Highs: c.highs, Lows: c.lows, Closes: c.closes, At: now.Unix(),
		}, gtOHLCVTTL)
	}
}
