package robinhood

import (
	"fmt"
	"testing"
	"time"
)

func resetWatch() {
	watch.mu.Lock()
	watch.pools = nil
	watch.lastTry = time.Time{}
	watch.mu.Unlock()
}

func youngPool(addr string, created time.Time) Pool {
	return Pool{
		Address:      addr,
		Name:         addr + " / WETH 1%",
		Dex:          "uniswap-v3-robinhood",
		Protocol:     "v3",
		CreatedAt:    created,
		BaseAddress:  "0xbase" + addr,
		QuoteAddress: WETH,
		QuoteSymbol:  "WETH",
		FeePct:       1,
		ReserveUSD:   50000,
	}
}

// The registry exists because new_pools scrolls a pool off within minutes, so
// the one thing it must never do is forget a pool that has not aged out yet.
func TestPublishYoungCarriesAcrossSweeps(t *testing.T) {
	resetWatch()
	now := time.Now()

	publishYoung([]Pool{youngPool("0xaaa", now.Add(-2*time.Minute))}, now)
	// A later sweep no longer lists the pool at all — the launch feed moved on.
	later := now.Add(3 * time.Hour)
	publishYoung([]Pool{youngPool("0xbbb", later.Add(-time.Minute))}, later)

	got := watchWindow(PulseLadder, later)
	if len(got) != 1 || got[0].Address != "0xaaa" {
		t.Fatalf("want the carried 3h-old pool in window, got %v", addrsOf(got))
	}
}

func TestPublishYoungKeepsFirstSighting(t *testing.T) {
	resetWatch()
	now := time.Now()
	first := youngPool("0xaaa", now.Add(-90*time.Minute))
	publishYoung([]Pool{first}, now)

	// A second sighting with a different creation time must not overwrite the
	// original: age is the axis the whole registry is organized on.
	publishYoung([]Pool{youngPool("0xaaa", now)}, now)

	watch.mu.Lock()
	got := watch.pools["0xaaa"]
	watch.mu.Unlock()
	if !got.CreatedAt.Equal(first.CreatedAt) {
		t.Fatalf("createdAt overwritten: want %v, got %v", first.CreatedAt, got.CreatedAt)
	}
}

func TestPublishYoungSkipsUnknownCreation(t *testing.T) {
	resetWatch()
	now := time.Now()
	publishYoung([]Pool{youngPool("0xaaa", time.Time{})}, now)

	watch.mu.Lock()
	n := len(watch.pools)
	watch.mu.Unlock()
	if n != 0 {
		t.Fatalf("a pool with no creation time has no age and must not be carried, got %d entries", n)
	}
}

func TestPruneWatchDropsAgedOut(t *testing.T) {
	resetWatch()
	now := time.Now()
	publishYoung([]Pool{
		youngPool("0xold", now.Add(-25*time.Hour)),
		youngPool("0xnew", now.Add(-2*time.Hour)),
	}, now)

	watch.mu.Lock()
	_, oldKept := watch.pools["0xold"]
	_, newKept := watch.pools["0xnew"]
	watch.mu.Unlock()
	if oldKept {
		t.Error("a pool past watchKeep belongs to rh-ladder's feed and must be dropped")
	}
	if !newKept {
		t.Error("a 2h-old pool is exactly this mode's band and must be kept")
	}
}

func TestPruneWatchCapEvictsOldestFirst(t *testing.T) {
	resetWatch()
	now := time.Now()
	pools := make([]Pool, 0, pulseMaxWatch+10)
	for i := 0; i < pulseMaxWatch+10; i++ {
		// i == 0 is the oldest, still inside watchKeep.
		age := time.Duration(pulseMaxWatch+10-i) * time.Second
		pools = append(pools, youngPool(fmt.Sprintf("0x%05d", i), now.Add(-age)))
	}
	publishYoung(pools, now)

	watch.mu.Lock()
	defer watch.mu.Unlock()
	if len(watch.pools) != pulseMaxWatch {
		t.Fatalf("want the registry capped at %d, got %d", pulseMaxWatch, len(watch.pools))
	}
	if _, ok := watch.pools["0x00000"]; ok {
		t.Error("the oldest entry must be the one evicted")
	}
	if _, ok := watch.pools[fmt.Sprintf("0x%05d", pulseMaxWatch+9)]; !ok {
		t.Error("the newest entry must survive the cap")
	}
}

// The handoff with rh-ladder is the mode's whole boundary: below MinAge nobody
// should trade the pool, at or past MaxAge the gateway feed owns it.
func TestWatchWindowBounds(t *testing.T) {
	resetWatch()
	now := time.Now()
	publishYoung([]Pool{
		youngPool("0xtooyoung", now.Add(-30*time.Minute)),
		youngPool("0xinband", now.Add(-6*time.Hour)),
		youngPool("0xhandoff", now.Add(-24*time.Hour)),
	}, now)

	got := addrsOf(watchWindow(PulseLadder, now))
	if len(got) != 1 || got[0] != "0xinband" {
		t.Fatalf("want only the in-band pool, got %v", got)
	}
}

func TestInWindowZeroMaxAgeHasNoCeiling(t *testing.T) {
	now := time.Now()
	mp := ModeParams{MinAge: time.Hour, MaxAge: 0}
	if !inWindow(youngPool("0xaaa", now.Add(-40*24*time.Hour)), mp, now) {
		t.Error("MaxAge 0 disables the ceiling, same as every other mode reads it")
	}
	if inWindow(youngPool("0xaaa", now.Add(-time.Minute)), mp, now) {
		t.Error("MinAge still binds when MaxAge is disabled")
	}
}

func TestWatchNeedsSweepSharesTheLaunchFetch(t *testing.T) {
	resetWatch()
	now := time.Now()
	if !watchNeedsSweep(now) {
		t.Fatal("an empty registry must sweep")
	}
	// rh-fresh's own sweep publishes, which is what a shared feed means.
	publishYoung([]Pool{youngPool("0xaaa", now)}, now)
	if watchNeedsSweep(now.Add(10 * time.Second)) {
		t.Error("a sweep within pulseRefresh must not be repeated by this mode")
	}
	if !watchNeedsSweep(now.Add(pulseRefresh + time.Second)) {
		t.Error("past pulseRefresh the registry must be refreshed")
	}
}

// PulseLadder and Ladder must not both claim a pool: one wallet funding two
// walls on the same book is one wall of the wrong shape.
func TestPulseAndLadderHandOffCleanly(t *testing.T) {
	if PulseLadder.MaxAge != Ladder.MinAge {
		t.Fatalf("age bands must abut: pulse MaxAge %v vs ladder MinAge %v", PulseLadder.MaxAge, Ladder.MinAge)
	}
	if PulseLadder.QuoteAsset != Ladder.QuoteAsset {
		t.Fatalf("both walls are WETH-denominated: %q vs %q", PulseLadder.QuoteAsset, Ladder.QuoteAsset)
	}
	if PulseLadder.FeePaceH24 {
		t.Error("a sub-24h pool has no 24h history; the pace must be extrapolated")
	}
}

func addrsOf(pools []Pool) []string {
	out := make([]string, len(pools))
	for i, p := range pools {
		out[i] = p.Address
	}
	return out
}
