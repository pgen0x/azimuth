package robinhood

import (
	"log"
	"strings"
	"sync"
	"time"
)

// This file gives the ladder mode a SECOND discovery source. Uniswap's gateway
// (mature.go) is not the venue's complete universe: diffing GeckoTerminal's
// trending_pools against the gateway's 90-pool v3 leaderboard on 2026-08-05
// found 11 pools the gateway lacked, and one of them — LEMON.FUN/WETH 1%,
// $49.6k TVL, 10.8 days old — was a plain Uniswap v3 pool the gateway simply
// does not index. Seven of the other ten were v4 (already covered by
// topV4PoolsQuery) and three were Uniswap-v2/pons-dot-family, which no executor
// here can mint in at all.
//
// GeckoTerminal 429s are this venue's binding constraint (three mature-family
// modes already spend one enrich call each per cycle), so the second source
// costs no new request in the common case: discover.go ALREADY fetches
// trending_pools on its own cadence for rh-fresh, and now publishes that page
// into the cache below instead of consuming it privately. The ladder path reads
// the cache.
//
// A CACHE rather than a restructure of FetchNewPools, because the two consumers
// are independently toggled: rh-fresh and rh-ladder are separate env switches
// and either can run without the other (live on 2026-08-05: robinhood=false,
// rh-usdg-ladder=true). Sharing one fetch through a rate-limited cache keeps
// the feed available whichever combination is enabled, and caps the venue's
// trending request rate at one page per trendingRefresh no matter how many
// modes read it — which is exactly the rate discover.go's trendingEvery cadence
// spends today at the default 60s POLL_INTERVAL.

const (
	// trendingRefresh is the MINIMUM spacing between trending fetches across
	// every consumer — the cache's rate limit, not just its freshness bound.
	// trendingEvery(5) x the default POLL_INTERVAL(60s) is the same 5 minutes
	// discover.go already spends, so a ladder cycle running alongside rh-fresh
	// never triggers a fetch of its own.
	trendingRefresh = 5 * time.Minute

	// trendingUsable is how old a cached page may be and still be unioned in.
	// Deliberately several refresh windows wide: a 429 must degrade the union to
	// a slightly stale ranking, not blank it. Safe because of what the ladder
	// mode gates on — a churn ranking over pools whose MinAge is 24h does not
	// turn over in fifteen minutes. The h1 flow counts it carries do age, but
	// they only ever gate a pool OUT (MinTxH1/MinBuyersH1), and the gateway feed
	// re-reads the same numbers fresh every cycle for any pool both feeds carry.
	trendingUsable = 15 * time.Minute
)

// trending is the process-wide cached trending_pools page. Guarded by a mutex
// rather than left unsynchronized like discover.go's cycleCount: the modes are
// polled from one scanner goroutine today, but a cache shared by four modes is
// exactly the thing a future parallel poll would race on.
var trending struct {
	mu      sync.Mutex
	pools   []Pool
	at      time.Time // caller's clock when the cached page was fetched
	lastTry time.Time // when a fetch was last ATTEMPTED (throttles retry after a 429)
}

// trendingRequestURL is the one trending request both consumers issue.
func trendingRequestURL() string {
	return trendingURL + "?include=base_token%2Cquote_token&page=1"
}

// publishTrending stores the trending slice of a FetchNewPools cycle: pools is
// that cycle's whole mapped result, addrs the lowercase addresses that came
// from the trending page. Called with the pools already through fillV4Meta.
func publishTrending(pools []Pool, addrs map[string]bool, now time.Time) {
	subset := make([]Pool, 0, len(addrs))
	for _, p := range pools {
		if addrs[strings.ToLower(p.Address)] {
			subset = append(subset, p)
		}
	}
	storeTrending(subset, now)
}

func storeTrending(pools []Pool, now time.Time) {
	trending.mu.Lock()
	defer trending.mu.Unlock()
	trending.pools = pools
	trending.at = now
	trending.lastTry = now
}

// trendingSnapshot returns a copy of the cached page, or nil when there is none
// or it is older than trendingUsable. Read-only: it never fetches.
func trendingSnapshot(now time.Time) []Pool {
	trending.mu.Lock()
	defer trending.mu.Unlock()
	if trending.at.IsZero() || now.Sub(trending.at) > trendingUsable {
		return nil
	}
	return append([]Pool(nil), trending.pools...)
}

// refreshTrending fetches the trending page only if no consumer has fetched it
// within trendingRefresh — including a fetch that FAILED, so a GeckoTerminal
// 429 costs one request per window rather than one per cycle. When rh-fresh is
// enabled it is that mode's page that keeps this cache warm and this function
// makes no request at all.
func refreshTrending(now time.Time) {
	trending.mu.Lock()
	if !trending.lastTry.IsZero() && now.Sub(trending.lastTry) < trendingRefresh {
		trending.mu.Unlock()
		return
	}
	// Claim the window before releasing the lock: a second caller in the same
	// cycle must not issue a duplicate request while this one is in flight.
	trending.lastTry = now
	trending.mu.Unlock()

	pools, err := fetchTrendingPage()
	if err != nil {
		// Keep serving the previous page (fail-soft): the alternative is a
		// gateway-only cycle, and one stale churn ranking is worth more than
		// none. Blank only once it ages past trendingUsable.
		log.Printf("robinhood: trending refresh failed, serving the cached page: %v", err)
		return
	}
	storeTrending(pools, now)
}

// fetchTrendingPage fetches and maps one trending_pools page through the SAME
// mapping and v4-meta resolution FetchNewPools uses, so a pool discovered here
// is field-identical to one discovered there.
func fetchTrendingPage() ([]Pool, error) {
	gr, err := fetchPage(trendingRequestURL())
	if err != nil {
		return nil, err
	}
	tokens := map[string]gtToken{}
	indexTokens(gr, tokens)
	return fillV4Meta(mapGTPools(gr.Data, tokens)), nil
}

// FetchLadderPools is the ladder mode's discovery source: the union of
// Uniswap's gateway leaderboard (FetchMaturePools, prefiltered with this mode's
// params) and the cached GeckoTerminal trending page, deduped by pool address.
//
// Only the ladder mode uses it. rh-mature and rh-usdg-ladder keep the gateway
// alone — the measured gap was entirely WETH-quoted, so there is no evidence a
// trending union helps the USDG universe.
//
// now is the cycle's clock, injected by the caller like every other rhFetcher.
func FetchLadderPools(mp ModeParams, now time.Time) ([]Pool, error) {
	// Trending first, so the two gateway POSTs inside FetchMaturePools sit
	// between this GeckoTerminal request and that function's GT enrich call —
	// natural spacing on the rate-limited host, no sleep needed.
	refreshTrending(now)

	gateway, err := FetchMaturePools(mp, now)
	extra := ladderEligible(trendingSnapshot(now), mp)
	if err != nil {
		if len(extra) == 0 {
			return nil, err
		}
		// A partial view still yields a usable cycle — same policy as
		// discover.go's tolerated page failures.
		log.Printf("robinhood: ladder gateway feed failed, continuing on %d trending pool(s): %v", len(extra), err)
	}

	merged := mergeFeeds(gateway, extra)
	log.Printf("robinhood[%s]: feed union gateway=%d trending=%d merged=%d",
		mp.Mode, len(gateway), len(extra), len(merged))
	return merged, nil
}

// ladderEligible keeps only the cached trending pools this mode could ever
// deploy into. It gates on IDENTITY, not on numbers: every threshold stays in
// Screen so the cycle's reject tally still accounts for it. Dropping a pool
// here makes it invisible, which is right for "no executor speaks this DEX" and
// wrong for "this pool's fee pace is too low".
func ladderEligible(pools []Pool, mp ModeParams) []Pool {
	out := make([]Pool, 0, len(pools))
	for _, p := range pools {
		// Empty Protocol means the pool is on neither Uniswap v3 nor v4 —
		// mapGTPools already drops those, and this is the backstop that keeps a
		// pons-dot-family or Uniswap-v2 pool out of Screen if it ever stops.
		if p.Protocol != "v3" && p.Protocol != "v4" {
			continue
		}
		// v4 hard rejects, mirroring prefilter: a hook can block or skim a
		// withdrawal and a dynamic fee invalidates the fee-pace math.
		if p.Hook != "" || p.DynamicFee {
			continue
		}
		// Quote pin. orientQuote first because GeckoTerminal lists the quote
		// asset base-side for some pools, and a ladder may not mix quote assets:
		// its rungs and its sizing are denominated in one (CLAUDE.md).
		oriented, ok := orientQuote(p)
		if !ok {
			continue
		}
		if quoteAssets[strings.ToLower(oriented.BaseAddress)] {
			continue // WETH/USDG and friends: no token side at all
		}
		if mp.QuoteAsset != "" && !quotePinMatch(oriented.QuoteAddress, mp.QuoteAsset) {
			continue
		}
		out = append(out, p)
	}
	return out
}

// mergeFeeds unions two feeds, deduping case-insensitively by pool address
// (GeckoTerminal lowercases addresses, the gateway checksums them, and a v4
// poolId can be spelled either way).
//
// primary wins a collision because the gateway path is strictly richer: its fee
// tier is the authoritative feeTier rather than a suffix parsed off a display
// name, and it carries v4 hook/dynamic-fee metadata. Fields it left ZERO are
// backfilled from the trending copy — a gateway pool whose /pools/multi enrich
// missed has no flow data at all, and the trending page has it.
func mergeFeeds(primary, extra []Pool) []Pool {
	out := make([]Pool, 0, len(primary)+len(extra))
	idx := make(map[string]int, len(primary)+len(extra))
	add := func(p Pool) {
		k := strings.ToLower(p.Address)
		if i, ok := idx[k]; ok {
			out[i] = backfillZeros(out[i], p)
			return
		}
		idx[k] = len(out)
		out = append(out, p)
	}
	for _, p := range primary {
		add(p)
	}
	for _, p := range extra {
		add(p)
	}
	return out
}

// backfillZeros fills dst's zero-valued screening fields from src. Only zeros
// are touched: a present value from the preferred source always stands, and a
// field neither source knows stays zero so its gate rejects (which is the
// correct outcome — no data, no trade).
func backfillZeros(dst, src Pool) Pool {
	if dst.Name == "" {
		dst.Name = src.Name
	}
	if dst.CreatedAt.IsZero() {
		dst.CreatedAt = src.CreatedAt
	}
	if dst.FeePct == 0 {
		dst.FeePct = src.FeePct
	}
	if dst.ReserveUSD == 0 {
		dst.ReserveUSD = src.ReserveUSD
	}
	if dst.FdvUSD == 0 {
		dst.FdvUSD = src.FdvUSD
	}
	if dst.McapUSD == 0 {
		dst.McapUSD = src.McapUSD
	}
	if dst.VolumeM15USD == 0 {
		dst.VolumeM15USD = src.VolumeM15USD
	}
	if dst.TxM15 == (gtTxWindow{}) {
		dst.TxM15 = src.TxM15
	}
	if dst.VolumeH1USD == 0 {
		dst.VolumeH1USD = src.VolumeH1USD
	}
	if dst.VolumeH24USD == 0 {
		dst.VolumeH24USD = src.VolumeH24USD
	}
	if dst.TxH1 == (gtTxWindow{}) {
		dst.TxH1 = src.TxH1
	}
	if dst.TxH24 == (gtTxWindow{}) {
		dst.TxH24 = src.TxH24
	}
	// Price changes: a legitimate 0 means flat, and both feeds read the same
	// GeckoTerminal windows, so copying across on zero cannot disagree with the
	// preferred source — it only fills a gateway pool the enrich never matched.
	if dst.ChangeM5Pct == 0 {
		dst.ChangeM5Pct = src.ChangeM5Pct
	}
	if dst.ChangeH1Pct == 0 {
		dst.ChangeH1Pct = src.ChangeH1Pct
	}
	if dst.ChangeH6Pct == 0 {
		dst.ChangeH6Pct = src.ChangeH6Pct
	}
	if dst.ChangeH24Pct == 0 {
		dst.ChangeH24Pct = src.ChangeH24Pct
	}
	if dst.BaseDecimals == 0 {
		dst.BaseDecimals = src.BaseDecimals
	}
	if dst.QuoteDecimals == 0 {
		dst.QuoteDecimals = src.QuoteDecimals
	}
	return dst
}
