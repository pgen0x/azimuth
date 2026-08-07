package robinhood

import (
	"encoding/json"
	"strings"
	"testing"
	"time"
)

// resetTrending clears the process-wide cache so cases cannot leak into each
// other (the cache is package state by design — see trending.go).
func resetTrending() {
	trending.mu.Lock()
	defer trending.mu.Unlock()
	trending.pools = nil
	trending.at = time.Time{}
	trending.lastTry = time.Time{}
}

// gtTrendingPage is a trending_pools response shaped exactly like the live one,
// carrying the four DEX identities the venue actually returns. LEMON.FUN is the
// real gap this feed exists to close: a Uniswap v3 WETH pool, 10.8 days old,
// $49.6k TVL, absent from the gateway's 90-pool v3 leaderboard (2026-08-05).
const gtTrendingPage = `{
  "data": [
    {
      "id": "robinhood_0x1111111111111111111111111111111111111111",
      "attributes": {
        "address": "0x1111111111111111111111111111111111111111",
        "name": "LEMON.FUN / WETH 1%",
        "pool_created_at": "2026-07-25T09:00:00Z",
        "reserve_in_usd": "49600.0",
        "fdv_usd": "512000.0",
        "market_cap_usd": "430000.0",
        "price_change_percentage": {"m5": "0.4", "h1": "1.9", "h6": "-3.2", "h24": "7.5"},
        "transactions": {
          "m15": {"buys": 11, "sells": 7, "buyers": 6, "sellers": 5},
          "h1":  {"buys": 40, "sells": 25, "buyers": 18, "sellers": 12},
          "h24": {"buys": 620, "sells": 480, "buyers": 210, "sellers": 160}
        },
        "volume_usd": {"m15": "1500.0", "h1": "6000.0", "h24": "120000.0"}
      },
      "relationships": {
        "base_token":  {"data": {"id": "robinhood_lemon", "type": "token"}},
        "quote_token": {"data": {"id": "robinhood_weth",  "type": "token"}},
        "dex":         {"data": {"id": "uniswap-v3-robinhood", "type": "dex"}}
      }
    },
    {
      "id": "robinhood_0x2222222222222222222222222222222222222222",
      "attributes": {
        "address": "0x2222222222222222222222222222222222222222",
        "name": "TURBO / WETH",
        "pool_created_at": "2026-07-20T09:00:00Z",
        "reserve_in_usd": "180000.0",
        "fdv_usd": "900000.0",
        "market_cap_usd": "800000.0",
        "price_change_percentage": {"m5": "0.1", "h1": "1.0", "h6": "2.0", "h24": "3.0"},
        "transactions": {
          "h1":  {"buys": 90, "sells": 70, "buyers": 44, "sellers": 30},
          "h24": {"buys": 900, "sells": 800, "buyers": 400, "sellers": 300}
        },
        "volume_usd": {"h1": "40000.0", "h24": "900000.0"}
      },
      "relationships": {
        "base_token":  {"data": {"id": "robinhood_turbo", "type": "token"}},
        "quote_token": {"data": {"id": "robinhood_weth",  "type": "token"}},
        "dex":         {"data": {"id": "pons-dot-family", "type": "dex"}}
      }
    },
    {
      "id": "robinhood_0x3333333333333333333333333333333333333333",
      "attributes": {
        "address": "0x3333333333333333333333333333333333333333",
        "name": "HOODRAT / WETH 0.3%",
        "pool_created_at": "2026-07-22T09:00:00Z",
        "reserve_in_usd": "60000.0",
        "fdv_usd": "700000.0",
        "market_cap_usd": "600000.0",
        "price_change_percentage": {"m5": "0.2", "h1": "1.1", "h6": "2.2", "h24": "3.3"},
        "transactions": {
          "h1":  {"buys": 55, "sells": 40, "buyers": 25, "sellers": 20},
          "h24": {"buys": 700, "sells": 600, "buyers": 300, "sellers": 250}
        },
        "volume_usd": {"h1": "20000.0", "h24": "400000.0"}
      },
      "relationships": {
        "base_token":  {"data": {"id": "robinhood_hoodrat", "type": "token"}},
        "quote_token": {"data": {"id": "robinhood_weth",    "type": "token"}},
        "dex":         {"data": {"id": "uniswap-v2-robinhood", "type": "dex"}}
      }
    },
    {
      "id": "robinhood_0x4444444444444444444444444444444444444444",
      "attributes": {
        "address": "0x4444444444444444444444444444444444444444",
        "name": "USDG / NVDA 0.3%",
        "pool_created_at": "2026-07-01T09:00:00Z",
        "reserve_in_usd": "300000.0",
        "fdv_usd": "9000000.0",
        "market_cap_usd": "8000000.0",
        "price_change_percentage": {"m5": "0.0", "h1": "0.3", "h6": "0.5", "h24": "1.2"},
        "transactions": {
          "h1":  {"buys": 30, "sells": 20, "buyers": 14, "sellers": 10},
          "h24": {"buys": 400, "sells": 350, "buyers": 180, "sellers": 150}
        },
        "volume_usd": {"h1": "15000.0", "h24": "600000.0"}
      },
      "relationships": {
        "base_token":  {"data": {"id": "robinhood_usdg", "type": "token"}},
        "quote_token": {"data": {"id": "robinhood_nvda", "type": "token"}},
        "dex":         {"data": {"id": "uniswap-v3-robinhood", "type": "dex"}}
      }
    }
  ],
  "included": [
    {"id": "robinhood_lemon", "type": "token", "attributes": {"address": "0xaaa0000000000000000000000000000000000001", "name": "Lemon Fun", "symbol": "LEMON.FUN", "decimals": 18}},
    {"id": "robinhood_turbo", "type": "token", "attributes": {"address": "0xaaa0000000000000000000000000000000000002", "name": "Turbo", "symbol": "TURBO", "decimals": 18}},
    {"id": "robinhood_hoodrat", "type": "token", "attributes": {"address": "0xaaa0000000000000000000000000000000000003", "name": "Hoodrat", "symbol": "HOODRAT", "decimals": 18}},
    {"id": "robinhood_nvda", "type": "token", "attributes": {"address": "0xaaa0000000000000000000000000000000000004", "name": "Nvidia", "symbol": "nvda", "decimals": 18}},
    {"id": "robinhood_weth", "type": "token", "attributes": {"address": "0x0bd7d308f8e1639fab988df18a8011f41eacad73", "name": "Wrapped Ether", "symbol": "WETH", "decimals": 18}},
    {"id": "robinhood_usdg", "type": "token", "attributes": {"address": "0x5fc5360d0400a0fd4f2af552add042d716f1d168", "name": "Global Dollar", "symbol": "USDG", "decimals": 6}},
    {"id": "robinhood_dex_noise", "type": "dex", "attributes": {"name": "Uniswap V3"}}
  ]
}`

// parseTrendingFixture decodes the fixture through the SAME mapping the live
// trending fetch uses (fetchTrendingPage minus the HTTP call).
func parseTrendingFixture(t *testing.T) []Pool {
	t.Helper()
	var gr gtResponse
	if err := json.Unmarshal([]byte(gtTrendingPage), &gr); err != nil {
		t.Fatalf("fixture decode: %v", err)
	}
	tokens := map[string]gtToken{}
	indexTokens(&gr, tokens)
	return mapGTPools(gr.Data, tokens)
}

func findPool(pools []Pool, addr string) (Pool, bool) {
	for _, p := range pools {
		if strings.EqualFold(p.Address, addr) {
			return p, true
		}
	}
	return Pool{}, false
}

// TestMapGTPoolsFiltersByDexIdentity is the requirement that a pool our
// executors cannot mint in never becomes a candidate: the filter is on DEX
// identity, so pons-dot-family and Uniswap v2 are dropped at the mapping,
// before Screen ever sees them, rather than passed on with an empty Protocol.
func TestMapGTPoolsFiltersByDexIdentity(t *testing.T) {
	pools := parseTrendingFixture(t)

	cases := []struct {
		name     string
		addr     string
		wantKept bool
		wantProt string
	}{
		{"uniswap v3 kept", "0x1111111111111111111111111111111111111111", true, "v3"},
		{"pons-dot-family dropped", "0x2222222222222222222222222222222222222222", false, ""},
		{"uniswap v2 dropped", "0x3333333333333333333333333333333333333333", false, ""},
		{"usdg v3 kept by mapping", "0x4444444444444444444444444444444444444444", true, "v3"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			p, ok := findPool(pools, tc.addr)
			if ok != tc.wantKept {
				t.Fatalf("kept=%v, want %v", ok, tc.wantKept)
			}
			if ok && p.Protocol != tc.wantProt {
				t.Fatalf("protocol=%q, want %q", p.Protocol, tc.wantProt)
			}
		})
	}
	for _, p := range pools {
		if p.Protocol == "" {
			t.Fatalf("pool %s reached the feed with an empty Protocol", p.Address)
		}
	}
}

// TestLadderEligible covers the mode's identity gates on the cached page: the
// quote pin (a USDG pool may never enter the WETH ladder's batch), the
// no-token-side case, the v4 hard rejects, and the empty-Protocol backstop.
func TestLadderEligible(t *testing.T) {
	base := Pool{
		Address:      "0x1111111111111111111111111111111111111111",
		Protocol:     "v3",
		BaseAddress:  "0xaaa0000000000000000000000000000000000001",
		BaseSymbol:   "LEMON.FUN",
		QuoteAddress: WETH,
		QuoteSymbol:  "WETH",
	}
	mutate := func(f func(*Pool)) Pool {
		p := base
		f(&p)
		return p
	}

	cases := []struct {
		name string
		pool Pool
		mode ModeParams
		want bool
	}{
		{"weth v3 pool passes the weth ladder", base, Ladder, true},
		{"v4 hookless passes", mutate(func(p *Pool) { p.Protocol = "v4" }), Ladder, true},
		{
			name: "usdg-quoted pool rejected from the weth ladder",
			pool: mutate(func(p *Pool) { p.QuoteAddress, p.QuoteSymbol = USDG, "USDG" }),
			mode: Ladder, want: false,
		},
		{
			name: "usdg base-side pool (gt orientation) still rejected from the weth ladder",
			pool: mutate(func(p *Pool) {
				p.BaseAddress, p.BaseSymbol = USDG, "USDG"
				p.QuoteAddress, p.QuoteSymbol = "0xaaa0000000000000000000000000000000000004", "nvda"
			}),
			mode: Ladder, want: false,
		},
		{
			name: "weth/usdg has no token side",
			pool: mutate(func(p *Pool) { p.BaseAddress, p.BaseSymbol = USDG, "USDG" }),
			mode: Ladder, want: false,
		},
		{
			name: "neither side a quote asset",
			pool: mutate(func(p *Pool) { p.QuoteAddress, p.QuoteSymbol = "0xdead00000000000000000000000000000000beef", "SHIB" }),
			mode: Ladder, want: false,
		},
		{
			name: "empty protocol backstop",
			pool: mutate(func(p *Pool) { p.Protocol = "" }),
			mode: Ladder, want: false,
		},
		{
			name: "v2 protocol never becomes eligible",
			pool: mutate(func(p *Pool) { p.Protocol = "v2" }),
			mode: Ladder, want: false,
		},
		{
			name: "hooked v4 rejected",
			pool: mutate(func(p *Pool) { p.Protocol, p.Hook = "v4", "0xf00d000000000000000000000000000000000001" }),
			mode: Ladder, want: false,
		},
		{
			name: "dynamic-fee v4 rejected",
			pool: mutate(func(p *Pool) { p.Protocol, p.DynamicFee = "v4", true }),
			mode: Ladder, want: false,
		},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := ladderEligible([]Pool{tc.pool}, tc.mode)
			if (len(got) == 1) != tc.want {
				t.Fatalf("eligible=%v (n=%d), want %v", len(got) == 1, len(got), tc.want)
			}
		})
	}
}

// TestLadderEligibleRejectsUsdgFromTrendingPage runs the same pin over the real
// fixture: the USDG/nvda pool survives the DEX filter and must still never
// reach the WETH ladder's batch.
func TestLadderEligibleRejectsUsdgFromTrendingPage(t *testing.T) {
	eligible := ladderEligible(parseTrendingFixture(t), Ladder)
	if len(eligible) != 1 {
		t.Fatalf("eligible=%d, want 1 (only the WETH v3 pool)", len(eligible))
	}
	if !strings.EqualFold(eligible[0].Address, "0x1111111111111111111111111111111111111111") {
		t.Fatalf("eligible pool = %s, want the LEMON.FUN/WETH pool", eligible[0].Address)
	}
}

// TestTrendingPoolFieldParity is the field-parity guard: a pool that arrives
// only through the trending feed must have every field Screen reads for the
// ladder mode populated. A silently-zero field would mis-fire a gate — a zero
// VolumeH24USD fails the fee pace, a zero CreatedAt makes the age enormous and
// passes MinAge for the wrong reason.
func TestTrendingPoolFieldParity(t *testing.T) {
	p, ok := findPool(parseTrendingFixture(t), "0x1111111111111111111111111111111111111111")
	if !ok {
		t.Fatal("LEMON.FUN pool missing from the mapped page")
	}

	cases := []struct {
		field string
		zero  bool
	}{
		{"Address", p.Address == ""},
		{"Name", p.Name == ""},
		{"Dex", p.Dex == ""},
		{"Protocol", p.Protocol == ""},
		{"CreatedAt", p.CreatedAt.IsZero()},
		{"BaseAddress", p.BaseAddress == ""},
		{"BaseSymbol", p.BaseSymbol == ""},
		{"BaseDecimals", p.BaseDecimals == 0},
		{"QuoteAddress", p.QuoteAddress == ""},
		{"QuoteSymbol", p.QuoteSymbol == ""},
		{"QuoteDecimals", p.QuoteDecimals == 0},
		{"FeePct", p.FeePct == 0},
		{"ReserveUSD", p.ReserveUSD == 0},
		{"FdvUSD", p.FdvUSD == 0},
		{"McapUSD", p.McapUSD == 0},
		{"VolumeM15USD", p.VolumeM15USD == 0},
		{"TxM15.Buys", p.TxM15.Buys == 0},
		{"TxM15.Sells", p.TxM15.Sells == 0},
		{"VolumeH1USD", p.VolumeH1USD == 0},
		{"VolumeH24USD", p.VolumeH24USD == 0},
		{"TxH1.Buys", p.TxH1.Buys == 0},
		{"TxH1.Sells", p.TxH1.Sells == 0},
		{"TxH1.Buyers", p.TxH1.Buyers == 0},
		{"TxH1.Sellers", p.TxH1.Sellers == 0},
		{"TxH24.Buys", p.TxH24.Buys == 0},
		{"ChangeM5Pct", p.ChangeM5Pct == 0},
		{"ChangeH1Pct", p.ChangeH1Pct == 0},
		{"ChangeH6Pct", p.ChangeH6Pct == 0},
		{"ChangeH24Pct", p.ChangeH24Pct == 0},
	}
	for _, tc := range cases {
		if tc.zero {
			t.Errorf("%s is zero on a trending-sourced pool", tc.field)
		}
	}

	// And it must actually pass the ladder screen on those values: 1% tier x
	// $120k of 24h volume on $49.6k of reserve = 2.42%/day against a 1.5% floor.
	now := p.CreatedAt.Add(11 * 24 * time.Hour)
	cand, reason := Screen(p, Ladder, now)
	if reason != "" {
		t.Fatalf("trending-sourced ladder pool rejected: %s", reason)
	}
	if cand.FeeTVLDayPct < Ladder.MinFeeTVLDay {
		t.Fatalf("fee pace %.2f%%/d below the mode floor — pace read a zero volume", cand.FeeTVLDayPct)
	}
	if cand.QuoteSymbol != "WETH" || cand.BaseSymbol != "LEMON.FUN" {
		t.Fatalf("orientation wrong: base=%s quote=%s", cand.BaseSymbol, cand.QuoteSymbol)
	}
}

// TestMergeFeeds covers the union dedup: a pool both feeds carry appears ONCE,
// address case does not create a duplicate, the gateway copy wins a collision,
// and its zero fields are backfilled from the trending copy (the case where the
// /pools/multi enrich never matched the pool).
func TestMergeFeeds(t *testing.T) {
	gwAddr := "0xAbCdEf0000000000000000000000000000000001"
	gateway := []Pool{{
		Address:      gwAddr,
		Name:         "MEOW / WETH 1%",
		Protocol:     "v3",
		FeePct:       1.0,
		ReserveUSD:   65000,
		VolumeH24USD: 1440000,
		QuoteAddress: WETH,
	}}
	trend := []Pool{
		{ // same pool, lowercase (GeckoTerminal spelling), richer flow fields
			Address:      strings.ToLower(gwAddr),
			Name:         "MEOW / WETH 1%",
			Protocol:     "v3",
			FeePct:       0, // name-parsed tier missing: must not overwrite the gateway's
			ReserveUSD:   64000,
			VolumeH1USD:  90000,
			VolumeH24USD: 1400000,
			TxH1:         gtTxWindow{Buys: 50, Sells: 30, Buyers: 22, Sellers: 15},
			FdvUSD:       750000,
			ChangeH1Pct:  2.5,
			QuoteAddress: WETH,
		},
		{ // gateway-invisible pool: the whole point of the second feed
			Address:      "0x1111111111111111111111111111111111111111",
			Name:         "LEMON.FUN / WETH 1%",
			Protocol:     "v3",
			FeePct:       1.0,
			ReserveUSD:   49600,
			VolumeH24USD: 120000,
			QuoteAddress: WETH,
		},
	}

	merged := mergeFeeds(gateway, trend)
	if len(merged) != 2 {
		t.Fatalf("merged=%d pools, want 2 (one shared pool must appear once)", len(merged))
	}

	shared, ok := findPool(merged, gwAddr)
	if !ok {
		t.Fatal("shared pool missing from the union")
	}
	if shared.Address != gwAddr {
		t.Fatalf("collision kept %s, want the gateway spelling %s", shared.Address, gwAddr)
	}
	cases := []struct {
		field string
		got   float64
		want  float64
	}{
		{"FeePct (gateway wins)", shared.FeePct, 1.0},
		{"ReserveUSD (gateway wins)", shared.ReserveUSD, 65000},
		{"VolumeH24USD (gateway wins)", shared.VolumeH24USD, 1440000},
		{"VolumeH1USD (backfilled)", shared.VolumeH1USD, 90000},
		{"FdvUSD (backfilled)", shared.FdvUSD, 750000},
		{"ChangeH1Pct (backfilled)", shared.ChangeH1Pct, 2.5},
	}
	for _, tc := range cases {
		if tc.got != tc.want {
			t.Errorf("%s = %v, want %v", tc.field, tc.got, tc.want)
		}
	}
	if shared.TxH1.Buyers != 22 {
		t.Errorf("TxH1 not backfilled: buyers=%d, want 22", shared.TxH1.Buyers)
	}
	if _, ok := findPool(merged, "0x1111111111111111111111111111111111111111"); !ok {
		t.Error("gateway-invisible trending pool lost in the merge")
	}
}

// TestPublishTrendingStoresOnlyTheTrendingSlice guards the cache contract:
// FetchNewPools hands it the whole cycle, and only the pools that came from the
// trending page may be published — a new_pools pool leaking in would put
// minutes-old launches into a mode whose MinAge is 24h.
func TestPublishTrendingStoresOnlyTheTrendingSlice(t *testing.T) {
	resetTrending()
	defer resetTrending()

	now := time.Date(2026, 8, 5, 12, 0, 0, 0, time.UTC)
	cycle := []Pool{
		{Address: "0xNEW0000000000000000000000000000000000001", Protocol: "v3"},
		{Address: "0xTREND000000000000000000000000000000000001", Protocol: "v3"},
	}
	publishTrending(cycle, map[string]bool{
		strings.ToLower("0xTREND000000000000000000000000000000000001"): true,
	}, now)

	got := trendingSnapshot(now)
	if len(got) != 1 || !strings.EqualFold(got[0].Address, "0xTREND000000000000000000000000000000000001") {
		t.Fatalf("snapshot=%+v, want only the trending pool", got)
	}
}

// TestTrendingSnapshotStaleness covers the usable window: a page inside
// trendingUsable is served (even if a refresh is due), and one past it is
// dropped rather than unioned in.
func TestTrendingSnapshotStaleness(t *testing.T) {
	resetTrending()
	defer resetTrending()

	at := time.Date(2026, 8, 5, 12, 0, 0, 0, time.UTC)
	storeTrending([]Pool{{Address: "0x1", Protocol: "v3"}}, at)

	cases := []struct {
		name string
		now  time.Time
		want int
	}{
		{"same instant", at, 1},
		{"one refresh window old", at.Add(trendingRefresh), 1},
		{"just inside the usable window", at.Add(trendingUsable - time.Second), 1},
		{"past the usable window", at.Add(trendingUsable + time.Second), 0},
		{"hours old", at.Add(4 * time.Hour), 0},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := len(trendingSnapshot(tc.now)); got != tc.want {
				t.Fatalf("snapshot len=%d, want %d", got, tc.want)
			}
		})
	}
}

// TestTrendingSnapshotEmptyCache: with no page ever published (rh-fresh
// disabled and no refresh yet) the union must degrade to the gateway feed
// alone, not to a nil-deref or a phantom pool.
func TestTrendingSnapshotEmptyCache(t *testing.T) {
	resetTrending()
	defer resetTrending()
	if got := trendingSnapshot(time.Date(2026, 8, 5, 12, 0, 0, 0, time.UTC)); got != nil {
		t.Fatalf("snapshot=%+v, want nil on a cold cache", got)
	}
}

// TestRefreshTrendingThrottled asserts the rate limit that makes this feed
// free: inside trendingRefresh of the last ATTEMPT, refreshTrending must return
// without issuing a request. The test would hit the network if it did not.
func TestRefreshTrendingThrottled(t *testing.T) {
	resetTrending()
	defer resetTrending()

	at := time.Date(2026, 8, 5, 12, 0, 0, 0, time.UTC)
	storeTrending([]Pool{{Address: "0x1", Protocol: "v3"}}, at)

	refreshTrending(at.Add(trendingRefresh - time.Second))

	trending.mu.Lock()
	defer trending.mu.Unlock()
	if !trending.at.Equal(at) {
		t.Fatalf("cache timestamp moved to %v — a throttled refresh fetched", trending.at)
	}
	// lastTry moves on any ATTEMPT, successful or not — this is what proves no
	// request was issued rather than that one was issued and failed.
	if !trending.lastTry.Equal(at) {
		t.Fatalf("lastTry moved to %v — a throttled refresh attempted a request", trending.lastTry)
	}
	if len(trending.pools) != 1 {
		t.Fatalf("cached pools=%d, want the untouched 1", len(trending.pools))
	}
}
