package robinhood

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sort"
	"strings"
	"sync"
	"time"
)

// Discovery for the pulse ladder — the WETH memecoin band BETWEEN the venue's
// two existing feeds.
//
// rh-fresh reads GeckoTerminal's new_pools (launches) and rh-ladder reads
// Uniswap's gateway, which indexes nothing younger than 24h. Neither covers the
// hours in between, and on this venue that is not a gap anyone can close by
// paging harder: measured 2026-08-06, new_pools returned 33 WETH pools and ALL
// of them were 1-5 minutes old. Launches are dense enough that a pool scrolls
// off the feed within minutes, so the API is physically unable to answer "which
// WETH pools are three hours old".
//
// So this mode REMEMBERS. Every young pool either feed publishes is recorded
// with its creation time and carried until it ages past the mode's window; each
// cycle the entries that have aged INTO the window are re-enriched (one
// /pools/multi/ call, the same budget every mature-family mode spends) and
// handed to Screen with fresh flow numbers.
//
// Why a mode wants that band at all: the ladder shape parks one-sided WETH on
// the bid side and never owns the token, so its edge is churn, and churn on this
// venue is highest in a memecoin's first day — exactly where rh-ladder's
// gateway-imposed 24h floor forbids it from looking. The two modes hand off at
// 24h with no overlap by construction (PulseLadder.MaxAge == Ladder.MinAge).

const (
	// pulseRefresh is the minimum spacing between SELF-SERVED new_pools sweeps.
	// When rh-fresh is enabled its own sweep fills the registry and this mode
	// makes no launch request at all — same sharing rule trending.go uses, and
	// the reason both publish through a cache instead of owning a fetch.
	pulseRefresh = 55 * time.Second

	// pulseMaxWatch bounds the registry. At the observed launch rate (~6 WETH
	// pools/minute) a 24h window is ~8600 entries, nearly all of them $4.8k dust
	// that will never clear a gate. Keeping the newest N is not a real loss:
	// eviction is by AGE, and the entries it drops are the ones the window was
	// about to drop anyway.
	pulseMaxWatch = 3000

	// pulseSweepPages is how deep a SELF-SERVED sweep pages. One, because the
	// sweep only RECORDS launches: page 1 holds 20 pools and the venue mints ~6
	// WETH pools a minute, so a page covers more than a pulseRefresh interval.
	// The full newPoolPages depth belongs to rh-fresh, which screens those pages
	// rather than filing them — and paging deep here is what starved the GT
	// budget into a rate-limit cooldown the first time pulse ran without
	// rh-fresh to share the feed.
	pulseSweepPages = 1

	// watchKeep is the widest age any pulse mode can ask for, and therefore how
	// long an entry is worth carrying. Tied to Ladder.MinAge by intent: past 24h
	// the gateway feed indexes the pool and rh-ladder owns it.
	watchKeep = 24 * time.Hour
)

// watch is the process-wide young-pool registry. Same locking rationale as
// trending: one scanner goroutine today, but a structure several modes can reach
// is what a future parallel poll would race on.
var watch struct {
	mu      sync.Mutex
	pools   map[string]Pool // lowercased address -> the pool as first seen
	lastTry time.Time       // when a launch sweep was last ATTEMPTED
}

// WatchStore is the registry's optional persistent half. Declared here rather
// than importing the store, for the reason CandleStore gives: the dependency
// points one way (scanner -> robinhood), and the scanner installs the backend.
// *store.Seen satisfies it.
//
// The registry is the one piece of this mode's state a restart cannot rebuild
// quickly. Entries only become useful once they are MinAge old, so a cold
// registry means an hour of `eligible=0` and a full day before the carry is
// back to depth — measured 2026-08-07, when a deploy dropped it from 2405
// pools to 80 and the next cycles found nothing to screen. Persisting identity
// (which never changes) costs one SET per newly-seen launch.
type WatchStore interface {
	LoadYoungPools(ctx context.Context) [][]byte
	SaveYoungPool(ctx context.Context, addr string, v any, ttl time.Duration)
}

var (
	watchDBMu sync.Mutex
	watchDB   WatchStore
	watchLoad sync.Once
)

// SetWatchStore installs the persistent layer. Called once at startup; nil (the
// default) leaves the registry memory-only, which is what an operator running
// without REDIS_ADDR gets — and what every test gets unless it installs a fake.
func SetWatchStore(ws WatchStore) {
	watchDBMu.Lock()
	watchDB = ws
	watchLoad = sync.Once{}
	watchDBMu.Unlock()
}

func watchStore() WatchStore {
	watchDBMu.Lock()
	defer watchDBMu.Unlock()
	return watchDB
}

// youngEntry is the wire form of a carried registry entry. It holds IDENTITY
// only — the same subset publishYoung documents as safe to carry — so a
// restored entry can no more reach a gate with stale numbers than a carried one
// can. ReserveUSD rides along because it is the discovery-snapshot value the
// enrich ranking sorts on, and it is overwritten by the enrich before any gate
// reads it.
type youngEntry struct {
	Address       string    `json:"address"`
	Name          string    `json:"name"`
	Dex           string    `json:"dex"`
	Protocol      string    `json:"protocol"`
	CreatedAt     time.Time `json:"created_at"`
	Hook          string    `json:"hook,omitempty"`
	DynamicFee    bool      `json:"dynamic_fee,omitempty"`
	BaseAddress   string    `json:"base_address"`
	BaseSymbol    string    `json:"base_symbol"`
	BaseDecimals  int       `json:"base_decimals"`
	QuoteAddress  string    `json:"quote_address"`
	QuoteSymbol   string    `json:"quote_symbol"`
	QuoteDecimals int       `json:"quote_decimals"`
	FeePct        float64   `json:"fee_pct"`
	ReserveUSD    float64   `json:"reserve_usd"`
}

func toYoungEntry(p Pool) youngEntry {
	return youngEntry{
		Address: p.Address, Name: p.Name, Dex: p.Dex, Protocol: p.Protocol,
		CreatedAt: p.CreatedAt, Hook: p.Hook, DynamicFee: p.DynamicFee,
		BaseAddress: p.BaseAddress, BaseSymbol: p.BaseSymbol, BaseDecimals: p.BaseDecimals,
		QuoteAddress: p.QuoteAddress, QuoteSymbol: p.QuoteSymbol, QuoteDecimals: p.QuoteDecimals,
		FeePct: p.FeePct, ReserveUSD: p.ReserveUSD,
	}
}

func (e youngEntry) pool() Pool {
	return Pool{
		Address: e.Address, Name: e.Name, Dex: e.Dex, Protocol: e.Protocol,
		CreatedAt: e.CreatedAt, Hook: e.Hook, DynamicFee: e.DynamicFee,
		BaseAddress: e.BaseAddress, BaseSymbol: e.BaseSymbol, BaseDecimals: e.BaseDecimals,
		QuoteAddress: e.QuoteAddress, QuoteSymbol: e.QuoteSymbol, QuoteDecimals: e.QuoteDecimals,
		FeePct: e.FeePct, ReserveUSD: e.ReserveUSD,
	}
}

// restoreWatch seeds the registry from the persistent half, once per process.
// It never overwrites an entry the running process already recorded: a live
// sighting is at least as good as a stored one, and first-sighting order is
// what publishYoung preserves.
func restoreWatch(now time.Time) {
	db := watchStore()
	if db == nil {
		return
	}
	watchLoad.Do(func() {
		blobs := db.LoadYoungPools(context.Background())
		if len(blobs) == 0 {
			return
		}
		restored := 0
		watch.mu.Lock()
		if watch.pools == nil {
			watch.pools = make(map[string]Pool, len(blobs))
		}
		for _, b := range blobs {
			var e youngEntry
			if json.Unmarshal(b, &e) != nil || e.Address == "" || e.CreatedAt.IsZero() {
				continue
			}
			// Re-apply the age rule on read. Redis expiry and this prune agree, but
			// only one of them is this package's contract.
			if now.Sub(e.CreatedAt) > watchKeep {
				continue
			}
			k := strings.ToLower(e.Address)
			if _, ok := watch.pools[k]; !ok {
				watch.pools[k] = e.pool()
				restored++
			}
		}
		pruneWatch(now)
		watch.mu.Unlock()
		if restored > 0 {
			log.Printf("robinhood: restored %d carried young pool(s) from the store", restored)
		}
	})
}

// publishYoung records a discovery cycle's pools in the registry. Called by
// FetchNewPools with the cycle's whole mapped result, so the registry fills
// whether the sweep was rh-fresh's or this mode's own.
//
// Only IDENTITY survives the carry: address, protocol, currencies, fee tier and
// creation time never change, and every NUMBER is re-read at enrich time. An
// entry is therefore never stale in a way a gate can see — which is what makes
// carrying one safe at all.
func publishYoung(pools []Pool, now time.Time) {
	var fresh []Pool
	func() {
		watch.mu.Lock()
		defer watch.mu.Unlock()
		if watch.pools == nil {
			watch.pools = make(map[string]Pool, len(pools))
		}
		watch.lastTry = now
		for _, p := range pools {
			if p.CreatedAt.IsZero() {
				// No creation time means no age, and age is the only axis this
				// registry is organized on. Dropping beats stamping it with `now`: a
				// pool aged from the moment we happened to see it would leave the
				// window on our clock rather than on its own.
				continue
			}
			k := strings.ToLower(p.Address)
			if _, ok := watch.pools[k]; !ok {
				watch.pools[k] = p
				fresh = append(fresh, p)
			}
		}
		pruneWatch(now)
	}()

	// Outside the lock on purpose: these are network writes, and the registry is
	// read by every pulse cycle. The in-process map is already correct, so a slow
	// or failing store delays nothing a cycle depends on.
	persistYoung(fresh, now)
}

// persistYoung mirrors newly-recorded entries into the persistent half so the
// next process starts with the carry instead of rebuilding it. Only FIRST
// sightings are written — a re-seen pool's stored record is already correct and
// re-writing it would restart a TTL that must age on the pool's clock.
//
// Each key gets the pool's REMAINING watch window, so Redis expires an entry at
// the same moment pruneWatch would drop it. Called WITHOUT the registry lock;
// the writes are best-effort and the store's own methods swallow their errors.
func persistYoung(pools []Pool, now time.Time) {
	db := watchStore()
	if db == nil || len(pools) == 0 {
		return
	}
	ctx := context.Background()
	for _, p := range pools {
		ttl := watchKeep - now.Sub(p.CreatedAt)
		if ttl <= 0 {
			continue
		}
		db.SaveYoungPool(ctx, p.Address, toYoungEntry(p), ttl)
	}
}

// pruneWatch drops entries past watchKeep, then enforces pulseMaxWatch by
// evicting the OLDEST first. Caller holds the lock.
func pruneWatch(now time.Time) {
	for k, p := range watch.pools {
		if now.Sub(p.CreatedAt) > watchKeep {
			delete(watch.pools, k)
		}
	}
	if len(watch.pools) <= pulseMaxWatch {
		return
	}
	keys := make([]string, 0, len(watch.pools))
	for k := range watch.pools {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		return watch.pools[keys[i]].CreatedAt.After(watch.pools[keys[j]].CreatedAt)
	})
	for _, k := range keys[pulseMaxWatch:] {
		delete(watch.pools, k)
	}
}

// inWindow reports whether a pool's age sits inside the mode's [MinAge, MaxAge)
// band. A zero MaxAge disables the ceiling, matching every other mode's reading
// of the field.
func inWindow(p Pool, mp ModeParams, now time.Time) bool {
	if p.CreatedAt.IsZero() {
		return false
	}
	age := now.Sub(p.CreatedAt)
	return age >= mp.MinAge && (mp.MaxAge == 0 || age < mp.MaxAge)
}

// watchWindow returns the registry's in-window entries, newest first.
func watchWindow(mp ModeParams, now time.Time) []Pool {
	watch.mu.Lock()
	defer watch.mu.Unlock()
	out := make([]Pool, 0, len(watch.pools))
	for _, p := range watch.pools {
		if inWindow(p, mp, now) {
			out = append(out, p)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].CreatedAt.After(out[j].CreatedAt) })
	return out
}

// watchNeedsSweep reports whether this mode must fetch new_pools itself.
func watchNeedsSweep(now time.Time) bool {
	watch.mu.Lock()
	defer watch.mu.Unlock()
	return watch.lastTry.IsZero() || now.Sub(watch.lastTry) >= pulseRefresh
}

// FetchPulsePools is the pulse ladder's discovery source: the registry's
// in-window entries unioned with any in-window pool on the cached trending page,
// re-enriched in ONE GeckoTerminal call.
//
// now is the cycle's clock, injected by the caller like every other rhFetcher.
func FetchPulsePools(mp ModeParams, now time.Time) ([]Pool, error) {
	// Seed from the persistent half before anything reads the registry. No-op
	// after the first cycle, and a no-op forever without a store installed.
	restoreWatch(now)

	if watchNeedsSweep(now) {
		// FetchNewPools publishes into the registry itself, so its result is
		// deliberately discarded — this call exists to KEEP THE REGISTRY FED when
		// rh-fresh is disabled, not to screen launches. A failure is survivable:
		// the registry still holds everything earlier sweeps recorded, which is
		// the entire point of carrying it.
		if _, err := fetchNewPoolsPages(DefaultDiscoverURL, now, pulseSweepPages); err != nil {
			log.Printf("robinhood[%s]: launch sweep failed, continuing on %d carried pool(s): %v",
				mp.Mode, len(watchWindow(mp, now)), err)
		}
	}
	refreshTrending(now)

	// Trending is unioned in for the reason rh-ladder unions it: it carries pools
	// no other feed here indexes. Age-filtered against the same window so a
	// three-day-old trending pool cannot enter through this mode's back door.
	extra := make([]Pool, 0)
	for _, p := range ladderEligible(trendingSnapshot(now), mp) {
		if inWindow(p, mp, now) {
			extra = append(extra, p)
		}
	}

	carried := watchWindow(mp, now)
	eligible := ladderEligible(carried, mp)
	candidates := mergeFeeds(eligible, extra)
	if len(candidates) == 0 {
		// Logged, not silent. A cycle that returns nothing has three very
		// different causes — an empty registry, a registry whose entries are all
		// too young, and a window full of pools this mode may not touch (a
		// USDG-quoted trending pool against a WETH-pinned mode) — and without
		// these counts they are indistinguishable from the outside, which is
		// exactly the question the first live cycles asked.
		watch.mu.Lock()
		total := len(watch.pools)
		watch.mu.Unlock()
		log.Printf("robinhood[%s]: no candidates — registry=%d in_window=%d eligible=%d trending=%d",
			mp.Mode, total, len(carried), len(eligible), len(extra))
		return nil, nil
	}

	// The registry can hold hundreds of in-window pools; the enrich takes 30.
	// Rank by the reserve recorded at DISCOVERY — the one number a launch
	// snapshot carries that says whether a pool was funded seriously rather than
	// minted from a template. It ranks only; every gate re-reads it below.
	sort.SliceStable(candidates, func(i, j int) bool {
		return candidates[i].ReserveUSD > candidates[j].ReserveUSD
	})
	if len(candidates) > maxEnrich {
		candidates = candidates[:maxEnrich]
	}

	if err := enrichFromGT(candidates); err != nil {
		// Fail CLOSED, exactly as FetchMaturePools does and for a sharper reason:
		// every remaining gate (flow, fee pace, FDV, momentum) reads a field only
		// the enrich supplies, and here the un-enriched values are additionally
		// STALE — a launch-minute snapshot of a pool that may be hours old.
		return nil, fmt.Errorf("pulse enrich: %w", err)
	}

	// Drop anything the enrich did not refresh. A pool GeckoTerminal no longer
	// returns keeps its launch-minute numbers, and a carried registry must never
	// let those reach a gate. A genuinely dead pool reads zero flow too and would
	// fail MinTxH1 anyway, so this is one rule and not two.
	live := make([]Pool, 0, len(candidates))
	for _, p := range candidates {
		if p.TxH1.Buys+p.TxH1.Sells > 0 {
			live = append(live, p)
		}
	}

	log.Printf("robinhood[%s]: carried=%d trending=%d enriched=%d live=%d",
		mp.Mode, len(carried), len(extra), len(candidates), len(live))
	return live, nil
}
