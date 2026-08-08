package robinhood

import (
	"strings"
	"testing"
	"time"
)

// resetRanked clears the process-wide cache so cases cannot leak into each
// other (the cache is package state by design — see ranked.go).
func resetRanked() {
	ranked.mu.Lock()
	defer ranked.mu.Unlock()
	ranked.pools = nil
	ranked.at = time.Time{}
	ranked.lastTry = time.Time{}
}

func TestRankedRequestURLSortsByVolume(t *testing.T) {
	got := rankedRequestURL(2)
	// The sort key is the whole point of using this endpoint over the gateway:
	// a churn mode is paid fee_tier x volume, so volume order is fee-income
	// order. Losing it silently would leave the feed on GeckoTerminal's default
	// ordering — the liquidity ranking ranked.go exists to escape.
	if !strings.Contains(got, "sort=h24_volume_usd_desc") {
		t.Errorf("ranked URL must sort by 24h volume, got %q", got)
	}
	// Without the include the response carries no token resources, so every
	// pool maps with an empty base/quote address and orientQuote rejects the
	// lot — a silent total blackout rather than a visible error.
	if !strings.Contains(got, "include=base_token%2Cquote_token") {
		t.Errorf("ranked URL must include token resources, got %q", got)
	}
	if !strings.Contains(got, "page=2") {
		t.Errorf("ranked URL must carry the requested page, got %q", got)
	}
}

func TestRankedSnapshotExpires(t *testing.T) {
	resetRanked()
	base := time.Date(2026, 8, 8, 12, 0, 0, 0, time.UTC)
	storeRanked([]Pool{{Address: "0xabc", Protocol: "v3"}}, base)

	if got := rankedSnapshot(base.Add(rankedUsable - time.Minute)); len(got) != 1 {
		t.Fatalf("fresh ranking must serve, got %d pools", len(got))
	}
	// Past rankedUsable the cache blanks rather than serving a stale order. A
	// 429 should cost the mode a gateway-only cycle, never a mint priced off an
	// hour-old ranking.
	if got := rankedSnapshot(base.Add(rankedUsable + time.Minute)); got != nil {
		t.Errorf("stale ranking must blank, got %d pools", len(got))
	}
}

func TestRankedSnapshotIsACopy(t *testing.T) {
	resetRanked()
	now := time.Date(2026, 8, 8, 12, 0, 0, 0, time.UTC)
	storeRanked([]Pool{{Address: "0xabc"}}, now)

	got := rankedSnapshot(now)
	got[0].Address = "0xmutated"
	// The cache is read by every turnover cycle; a caller mutating a screened
	// pool in place would corrupt the ranking for every cycle after it.
	if again := rankedSnapshot(now); again[0].Address != "0xabc" {
		t.Errorf("snapshot must copy, cache now holds %q", again[0].Address)
	}
}

func TestRefreshRankedThrottlesAfterAFailedAttempt(t *testing.T) {
	resetRanked()
	base := time.Date(2026, 8, 8, 12, 0, 0, 0, time.UTC)
	// Simulate an attempt that failed: lastTry advanced, nothing cached. The
	// throttle must key on the ATTEMPT, not on the cache — otherwise a
	// GeckoTerminal 429 costs one request per cycle instead of one per window,
	// which is what starved the mature-family modes (gtlimit.go).
	ranked.mu.Lock()
	ranked.lastTry = base
	ranked.mu.Unlock()

	refreshRanked(base.Add(time.Minute)) // inside rankedRefresh — must not fetch

	ranked.mu.Lock()
	lastTry := ranked.lastTry
	ranked.mu.Unlock()
	if !lastTry.Equal(base) {
		t.Errorf("refresh inside the throttle window must not claim a new attempt, lastTry=%v", lastTry)
	}
}

// TestFeedEligibleDropsUnmintableRankedPools is the guard this feed needs most.
// Unlike trending_pools, the ranked page's HEAD is full of things the venue must
// never mint into: on 2026-08-08 the chain's largest pools by volume were
// WETH/USDG (no token side at all) and pons-v2-dex (no executor speaks it).
func TestFeedEligibleDropsUnmintableRankedPools(t *testing.T) {
	pools := []Pool{
		{ // pons-v2-dex: mapGTPools drops these, feedEligible is the backstop
			Address: "0x1", Protocol: "", Dex: "pons-v2-dex",
			BaseAddress: "0xtoken", QuoteAddress: WETH, QuoteSymbol: "WETH",
		},
		{ // both sides a quote asset — the venue's top pool by volume
			Address: "0x2", Protocol: "v3", Dex: "uniswap-v3-robinhood",
			BaseAddress: WETH, QuoteAddress: USDG, QuoteSymbol: "USDG",
		},
		{ // hooked v4: a hook can block or skim the withdrawal
			Address: "0x3", Protocol: "v4", Dex: "uniswap-v4-robinhood",
			Hook:        "0xdeadbeef",
			BaseAddress: "0xtoken", QuoteAddress: WETH, QuoteSymbol: "WETH",
		},
		{ // USDG-quoted while the mode is pinned to WETH
			Address: "0x4", Protocol: "v3", Dex: "uniswap-v3-robinhood",
			BaseAddress: "0xtoken", QuoteAddress: USDG, QuoteSymbol: "USDG",
		},
		{ // the one keeper: WETH-quoted Uniswap v3 with a real token side
			Address: "0x5", Protocol: "v3", Dex: "uniswap-v3-robinhood",
			BaseAddress: "0xtoken", QuoteAddress: WETH, QuoteSymbol: "WETH",
		},
	}
	got := feedEligible(pools, Turnover)
	if len(got) != 1 || got[0].Address != "0x5" {
		var addrs []string
		for _, p := range got {
			addrs = append(addrs, p.Address)
		}
		t.Fatalf("want only 0x5 eligible, got %v", addrs)
	}
}

// TestRankByFeeDensityPrefersTheThinnerBook pins the ordering change. Two pools
// with identical flow SHAPE differing only in depth: the churn mode must prefer
// the one where the same crossings are split fewer ways.
func TestRankByFeeDensityPrefersTheThinnerBook(t *testing.T) {
	thin := Pool{ReserveUSD: 58000, VolumeH1USD: 58000 * 1.5, TxH1: gtTxWindow{Buyers: 30}}
	deep := Pool{ReserveUSD: 500000, VolumeH1USD: 500000 * 1.5, TxH1: gtTxWindow{Buyers: 30}}
	// Same turnover ratio and buyer count by construction. The paces are the two
	// ends of the band measured on 2026-08-08 (PONS/WETH 0.3% at 7.1%/day,
	// BOYZ/WETH 0.25% at 3.1%/day).
	const thinPace, deepPace = 7.1, 3.1

	density := ModeParams{RankByFeeDensity: true}
	if s1, s2 := score(thin, thinPace, density), score(deep, deepPace, density); s1 <= s2 {
		t.Errorf("fee-density ranking must prefer the thinner book: thin=%.2f deep=%.2f", s1, s2)
	}
	// The default ranking must be untouched: every other mode holds inventory
	// for days and still wants the depth it will need to exit through.
	def := ModeParams{}
	if score(deep, deepPace, def) == score(deep, deepPace, density) {
		t.Errorf("RankByFeeDensity must change the score, both gave %.2f", score(deep, deepPace, def))
	}
}

// TestRankByFeeDensityStillNeedsFlow guards the one way this reweighting could
// go wrong. It drops the depth term, so it must not end up ranking a drained
// husk top — the ranked feed surfaces several (CT/WETH held $172 of TVL against
// $2.6M of volume on 2026-08-08). Score cannot REJECT, that is MinReserveUSD's
// job, but the geometric mean must still zero on missing flow.
func TestRankByFeeDensityStillNeedsFlow(t *testing.T) {
	husk := Pool{ReserveUSD: 172, VolumeH1USD: 2_600_000, TxH1: gtTxWindow{Buyers: 0}}
	if got := score(husk, 15000, ModeParams{RankByFeeDensity: true}); got != 0 {
		t.Errorf("a pool with no buyers must score 0, got %.2f", got)
	}
}

// TestTurnoverPinsFeeDensityRanking is the wiring check: ranked.go's feed and
// this ranking were turned on together and only make sense together.
func TestTurnoverPinsFeeDensityRanking(t *testing.T) {
	if !Turnover.RankByFeeDensity {
		t.Error("rh-turnover must rank on fee density — its income is fee_tier x crossings")
	}
	// The ladders are the comparison arm; changing their ranking too would make
	// the soak unreadable.
	for _, mp := range []ModeParams{Fresh, Mature, Ladder, StockLadder, PulseLadder} {
		if mp.RankByFeeDensity {
			t.Errorf("%s must keep the default depth-aware ranking", mp.Mode)
		}
	}
}
