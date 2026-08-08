package robinhood

import (
	"fmt"
	"log"
	"sync"
	"time"
)

// This file gives the churn modes a THIRD discovery source: GeckoTerminal's
// plain ranked pool list, sorted by 24h volume.
//
// The venue had three feeds before it and a hole in the middle of them.
// discover.go's new_pools answers "what launched in the last few minutes";
// mature.go's Uniswap gateway answers "what does the TVL leaderboard hold, of
// things at least a day old"; trending.go's page answers "what is hot right
// now". None of them answers the question a churn mode actually asks — WHICH
// POOLS ON THIS CHAIN TRADE THE MOST RELATIVE TO THEIR SIZE — and the gap
// showed. Of the 19 pools rh-turnover minted into between 2026-08-07 and
// 2026-08-08, exactly 2 appear anywhere in the venue's top 60 by 24h volume.
// The mode was screening a fringe of the book and calling it the book.
//
// The ranked endpoint answers it directly and cheaply: one request returns 20
// pools already ordered by the numerator of the fee-density ratio, so two pages
// cover the liquid half of a chain this size. It is NOT a replacement for the
// gateway feed — the gateway carries authoritative v3 fee tiers, v4 hook
// metadata, and pools whose GT volume rank is low but whose TVL is real — so it
// is unioned in, the same shape trending.go established for the ladders.
//
// What this feed is NOT is a fee-density filter. Every threshold stays in
// Screen. Ranking by volume gets the right pools in FRONT of the gates; the
// gates still decide. That distinction matters here because the ranked page's
// head is full of pools this venue must never touch: on 2026-08-08 its top rows
// included WETH/USDG pairs with no token side at all, pons-v2-dex pools no
// executor can mint in, and several sub-$500-reserve husks (CT/WETH at $172 of
// TVL against $2.6M of volume — a 15,000x turnover that is a drained pool, not
// an opportunity). mapGTPools drops the wrong DEXes; Screen's quote-asset and
// MinReserveUSD gates drop the rest.

// rankedURL is the venue's pool list. Unlike new_pools and trending_pools it
// takes a sort key, and h24_volume_usd_desc is the one that matches the churn
// thesis: fee income is fee_tier x volume, so within a tier volume order IS
// fee-income order. TVL order — what the gateway feed gives — ranks hardest the
// pools we least want, because a deep book is where a small position earns
// least.
const rankedURL = "https://api.geckoterminal.com/api/v2/networks/robinhood/pools"

const (
	// rankedPages is how many 20-pool pages to pull per refresh. Two covers the
	// top 40 by volume, which on the 2026-08-08 census reached down to ~$800k of
	// 24h volume — well past the point where a pool still clears the churn
	// gates. A third page would spend a request out of a ~4/min budget (see
	// discover.go) to rank pools Screen rejects on flow anyway.
	rankedPages = 2

	// rankedRefresh is the MINIMUM spacing between refreshes across all
	// consumers — a rate limit, not just a freshness bound, matching
	// trendingRefresh. A ranking over a 24h volume window does not reorder in
	// five minutes.
	rankedRefresh = 5 * time.Minute

	// rankedUsable is how stale a cached ranking may be and still be unioned in.
	// Deliberately several refresh windows wide, for trendingUsable's reason: a
	// GeckoTerminal 429 must degrade this feed to a slightly stale ORDER, never
	// blank it. The numbers the gates read are re-fetched by the gateway path
	// for any pool both feeds carry, and re-read wholesale on the next
	// successful refresh.
	rankedUsable = 20 * time.Minute
)

// ranked is the process-wide cached ranking. Same mutex discipline as
// trending: one scanner goroutine polls today, but a cache read by several
// modes is exactly what a future parallel poll would race on.
var ranked struct {
	mu      sync.Mutex
	pools   []Pool
	at      time.Time // caller's clock when the cached ranking was fetched
	lastTry time.Time // when a fetch was last ATTEMPTED (throttles retry after a 429)
}

func rankedRequestURL(page int) string {
	return fmt.Sprintf("%s?include=base_token%%2Cquote_token&page=%d&sort=h24_volume_usd_desc", rankedURL, page)
}

func storeRanked(pools []Pool, now time.Time) {
	ranked.mu.Lock()
	defer ranked.mu.Unlock()
	ranked.pools = pools
	ranked.at = now
	ranked.lastTry = now
}

// rankedSnapshot returns a copy of the cached ranking, or nil when there is
// none or it has aged past rankedUsable. Read-only: it never fetches.
func rankedSnapshot(now time.Time) []Pool {
	ranked.mu.Lock()
	defer ranked.mu.Unlock()
	if ranked.at.IsZero() || now.Sub(ranked.at) > rankedUsable {
		return nil
	}
	return append([]Pool(nil), ranked.pools...)
}

// refreshRanked fetches the ranking only if no consumer has fetched it within
// rankedRefresh — including a fetch that FAILED, so a GeckoTerminal 429 costs
// one request per window rather than one per cycle.
func refreshRanked(now time.Time) {
	ranked.mu.Lock()
	if !ranked.lastTry.IsZero() && now.Sub(ranked.lastTry) < rankedRefresh {
		ranked.mu.Unlock()
		return
	}
	// Claim the window before releasing the lock, so a second caller in the same
	// cycle cannot issue a duplicate request while this one is in flight.
	ranked.lastTry = now
	ranked.mu.Unlock()

	pools, err := fetchRankedPages(rankedPages)
	if err != nil {
		// Fail-soft, like trending: keep serving the previous ranking. A stale
		// order beats a gateway-only cycle, and it blanks itself once it ages
		// past rankedUsable.
		log.Printf("robinhood: ranked refresh failed, serving the cached ranking: %v", err)
		return
	}
	storeRanked(pools, now)
}

// fetchRankedPages pulls the ranking through the SAME mapping and v4-meta
// resolution every other GeckoTerminal path uses, so a pool discovered here is
// field-identical to one discovered by new_pools or trending_pools.
//
// Page failures after the first are tolerated and logged, matching
// fetchNewPoolsPages: a partial ranking still ranks. A first-page failure is
// fatal because it leaves nothing to serve.
func fetchRankedPages(pages int) ([]Pool, error) {
	if pages < 1 {
		pages = 1
	}
	tokens := map[string]gtToken{}
	var data []gtPool
	for page := 1; page <= pages; page++ {
		gr, err := fetchPage(rankedRequestURL(page))
		if err != nil {
			if page == 1 {
				return nil, err
			}
			log.Printf("robinhood: ranked page %d/%d fetch failed (continuing partial): %v", page, pages, err)
			continue
		}
		data = append(data, gr.Data...)
		indexTokens(gr, tokens)
		// Same burst spacing discover.go pays: the public tier throttles well
		// below its documented average.
		if page < pages {
			time.Sleep(1200 * time.Millisecond)
		}
	}
	if len(data) == 0 {
		return nil, fmt.Errorf("ranked feed returned no pools")
	}
	return fillV4Meta(mapGTPools(data, tokens)), nil
}

// FetchTurnoverPools is rh-turnover's discovery source: the union of Uniswap's
// gateway leaderboard (prefiltered with the turnover params) and the cached
// volume ranking, deduped by pool address.
//
// The ranked refresh runs FIRST so the two gateway POSTs inside
// FetchMaturePools sit between it and that function's GeckoTerminal enrich
// call — natural spacing on the rate-limited host, no sleep needed. Same
// ordering trick FetchLadderPools uses with trending.
//
// now is the cycle's clock, injected by the caller like every other rhFetcher.
func FetchTurnoverPools(mp ModeParams, now time.Time) ([]Pool, error) {
	refreshRanked(now)

	gateway, err := FetchMaturePools(mp, now)
	extra := feedEligible(rankedSnapshot(now), mp)
	if err != nil {
		if len(extra) == 0 {
			return nil, err
		}
		// A partial view still yields a usable cycle — same policy as
		// FetchLadderPools and discover.go's tolerated pages.
		log.Printf("robinhood: turnover gateway feed failed, continuing on %d ranked pool(s): %v", len(extra), err)
	}

	merged := mergeFeeds(gateway, extra)
	log.Printf("robinhood[%s]: feed union gateway=%d ranked=%d merged=%d",
		mp.Mode, len(gateway), len(extra), len(merged))
	return merged, nil
}
