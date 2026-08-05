package robinhood

import (
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
// of a cycle and the mode fails closed without it. GT's public tier allows ~30
// requests/minute per IP, and the requests are not one per cycle:
//
//   - one /pools/multi/ enrich per mature-family mode per cycle,
//   - one /ohlcv/ per candidate walked by the entry-timing gate, which on a
//     24-candidate batch can be most of the batch, and
//   - the new_pools and trending_pools pages when Fresh is enabled.
//
// The IP is also shared with anything else on the box hitting GT, so the real
// budget is smaller than it looks and bursts are what trip it.
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
	// ~24 requests/minute at steady state, leaving headroom under GT's ~30 for
	// whatever else shares the IP.
	gtMinInterval = 2500 * time.Millisecond
	// Long enough to leave a one-minute window entirely, short enough that a
	// single 429 costs at most a cycle or two.
	gtCooldown = 75 * time.Second
	// Under one 15m candle: an entry-timing decision can be at most this stale,
	// which cannot flip a supertrend band built from 30+ candles.
	gtOHLCVTTL = 4 * time.Minute
	// A caller should not block indefinitely behind a long queue. Past this it is
	// better to fail open (indicators) or skip the cycle (enrich) than to stall
	// the scanner loop.
	gtMaxWait = 8 * time.Second
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

// cachedOHLCV returns a fresh-enough cached candle set, if any.
func cachedOHLCV(pool string) (candles, bool) {
	ohlcvCache.mu.Lock()
	defer ohlcvCache.mu.Unlock()
	e, ok := ohlcvCache.m[pool]
	if !ok || gtNow().Sub(e.at) > gtOHLCVTTL {
		return candles{}, false
	}
	return e.c, true
}

func storeOHLCV(pool string, c candles) {
	ohlcvCache.mu.Lock()
	defer ohlcvCache.mu.Unlock()
	ohlcvCache.m[pool] = ohlcvEntry{c: c, at: gtNow()}
}
