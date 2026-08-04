package robinhood

import (
	"strings"
	"testing"
	"time"
)

func TestParseFeePct(t *testing.T) {
	cases := []struct {
		name string
		want float64
	}{
		{"CALLIE / WETH 0.3%", 0.3},
		{"NOXA / WETH 1%", 1},
		{"USDG / XIAO 87%", 87},
		{"NOFEE / WETH", 0},
		{"", 0},
	}
	for _, c := range cases {
		if got := parseFeePct(c.name); got != c.want {
			t.Errorf("parseFeePct(%q) = %v, want %v", c.name, got, c.want)
		}
	}
}

// passingPool returns a pool that clears every Fresh gate; each test case
// breaks exactly one gate from this baseline.
func passingPool(now time.Time) Pool {
	return Pool{
		Address:      "0xc187feb911997c06bc94903def113b677e6577c9",
		Name:         "CALLIE / WETH 1%",
		Dex:          "uniswap-v3-robinhood",
		CreatedAt:    now.Add(-2 * time.Hour),
		BaseAddress:  "0x21028be78e8f521214d24328715c1a8aadbac5a8",
		BaseSymbol:   "CALLIE",
		QuoteAddress: WETH,
		QuoteSymbol:  "WETH",
		FeePct:       1,
		ReserveUSD:   20000,
		FdvUSD:       300000,
		VolumeH1USD:  8000, // fee pace = 8000*24*1% / 20000 = 9.6%/day
		TxH1:         gtTxWindow{Buys: 40, Sells: 25, Buyers: 20, Sellers: 12},
		ChangeM5Pct:  1, ChangeH1Pct: 5, ChangeH6Pct: 10, ChangeH24Pct: 20,
	}
}

func TestScreenPasses(t *testing.T) {
	now := time.Now()
	cand, reason := Screen(passingPool(now), Fresh, now)
	if reason != "" {
		t.Fatalf("expected pass, got reject: %s", reason)
	}
	if cand.Chain != Chain || cand.Dex != "uniswap-v3" {
		t.Errorf("candidate venue fields wrong: chain=%q dex=%q", cand.Chain, cand.Dex)
	}
	if cand.FeeTVLDayPct < 9.5 || cand.FeeTVLDayPct > 9.7 {
		t.Errorf("fee pace = %v, want ~9.6", cand.FeeTVLDayPct)
	}
	if cand.Score <= 0 || cand.Score > 100 {
		t.Errorf("score out of range: %v", cand.Score)
	}
}

func TestScreenRejects(t *testing.T) {
	now := time.Now()
	cases := []struct {
		name   string
		mutate func(*Pool)
		want   string // reason prefix
	}{
		{"non-quote-asset quote", func(p *Pool) { p.QuoteAddress = "0x1111111111111111111111111111111111111111" }, "quote not"},
		{"v4 hooked pool", func(p *Pool) { p.Hook = "0x4e3468951D49f2EEa976eD0D6e75fFCb44a9a544" }, "v4 hooked"},
		{"v4 dynamic fee", func(p *Pool) { p.DynamicFee = true }, "v4 dynamic"},
		{"too young", func(p *Pool) { p.CreatedAt = now.Add(-1 * time.Minute) }, "too-young"},
		{"too old", func(p *Pool) { p.CreatedAt = now.Add(-30 * time.Hour) }, "too-old"},
		{"reserve floor", func(p *Pool) { p.ReserveUSD = 500 }, "reserve"},
		{"reserve cap", func(p *Pool) { p.ReserveUSD = 900000 }, "reserve"},
		{"fee tier floor", func(p *Pool) { p.FeePct = 0.05 }, "fee tier"},
		{"fee pace floor", func(p *Pool) { p.VolumeH1USD = 100 }, "fee/TVL pace"},
		{"txn floor", func(p *Pool) { p.TxH1 = gtTxWindow{Buys: 5, Sells: 5, Buyers: 20} }, "txns"},
		{"buyer floor", func(p *Pool) { p.TxH1 = gtTxWindow{Buys: 30, Sells: 10, Buyers: 3} }, "buyers"},
		{"no sells honeypot shape", func(p *Pool) { p.TxH1 = gtTxWindow{Buys: 40, Sells: 0, Buyers: 20} }, "no sells"},
		{"fdv floor", func(p *Pool) { p.FdvUSD = 1000 }, "fdv"},
		{"fdv cap", func(p *Pool) { p.FdvUSD = 90_000_000 }, "fdv"},
		{"m5 dump", func(p *Pool) { p.ChangeM5Pct = -8 }, "5m"},
		{"h1 dump", func(p *Pool) { p.ChangeH1Pct = -20 }, "1h"},
		{"h6 downtrend", func(p *Pool) { p.ChangeH6Pct = -15 }, "6h"},
		{"h24 downtrend", func(p *Pool) { p.ChangeH24Pct = -30 }, "24h"},
	}
	for _, c := range cases {
		p := passingPool(now)
		c.mutate(&p)
		cand, reason := Screen(p, Fresh, now)
		if reason == "" {
			t.Errorf("%s: expected reject, candidate passed (score %.0f)", c.name, cand.Score)
			continue
		}
		if !strings.HasPrefix(reason, c.want) {
			t.Errorf("%s: reason = %q, want prefix %q", c.name, reason, c.want)
		}
	}
}

// The venue's second and third quote assets: USDG pools and v4 native-ETH
// pools must pass the quote gate, and a quote asset arriving on the BASE side
// (GeckoTerminal lists USDG base-side in USDG/memecoin pools) must be
// re-oriented, not rejected.
func TestScreenQuoteAssets(t *testing.T) {
	now := time.Now()

	usdg := passingPool(now)
	usdg.Protocol = "v4"
	usdg.QuoteAddress, usdg.QuoteSymbol, usdg.QuoteDecimals = USDG, "USDG", 6
	cand, reason := Screen(usdg, Fresh, now)
	if reason != "" {
		t.Fatalf("USDG-quoted pool: expected pass, got reject: %s", reason)
	}
	if cand.Dex != "uniswap-v4" || cand.Protocol != "v4" {
		t.Errorf("v4 candidate fields wrong: dex=%q protocol=%q", cand.Dex, cand.Protocol)
	}

	native := passingPool(now)
	native.Protocol = "v4"
	native.QuoteAddress, native.QuoteSymbol = NativeETH, "ETH"
	if _, reason := Screen(native, Fresh, now); reason != "" {
		t.Errorf("native-ETH-quoted v4 pool: expected pass, got reject: %s", reason)
	}

	flipped := passingPool(now)
	flipped.Protocol = "v4"
	// USDG on the base side, memecoin on the quote side — the GT orientation
	// for USDG/memecoin pairs.
	flipped.BaseAddress, flipped.BaseSymbol, flipped.BaseDecimals = USDG, "USDG", 6
	flipped.QuoteAddress, flipped.QuoteSymbol, flipped.QuoteDecimals = "0x21028be78e8f521214d24328715c1a8aadbac5a8", "CALLIE", 18
	cand, reason = Screen(flipped, Fresh, now)
	if reason != "" {
		t.Fatalf("base-side USDG pool: expected pass, got reject: %s", reason)
	}
	if cand.QuoteSymbol != "USDG" || cand.BaseSymbol != "CALLIE" {
		t.Errorf("orientation not repaired: base=%q quote=%q", cand.BaseSymbol, cand.QuoteSymbol)
	}
}

// A v3 pool never sets Protocol today (only discover/mature constructors do);
// Screen must default it rather than emit an empty dex.
func TestScreenProtocolDefault(t *testing.T) {
	now := time.Now()
	cand, reason := Screen(passingPool(now), Fresh, now)
	if reason != "" {
		t.Fatal(reason)
	}
	if cand.Protocol != "v3" || cand.Dex != "uniswap-v3" {
		t.Errorf("protocol default wrong: dex=%q protocol=%q", cand.Dex, cand.Protocol)
	}
}

func TestSecurityReject(t *testing.T) {
	tax := func(v float64) *float64 { return &v }
	cases := []struct {
		name   string
		sec    *Security
		reject bool
	}{
		{"nil fails open", nil, false},
		{"all unknown fails open", &Security{Honeypot: -1, Blacklist: -1}, false},
		{"clean passes", &Security{Honeypot: 0, Blacklist: 0, SellTaxPct: tax(0)}, false},
		{"honeypot rejects", &Security{Honeypot: 1}, true},
		{"blacklist rejects", &Security{Blacklist: 1}, true},
		{"sell tax over cap rejects", &Security{SellTaxPct: tax(25)}, true},
		{"sell tax under cap passes", &Security{SellTaxPct: tax(5)}, false},
	}
	for _, c := range cases {
		if got := SecurityReject(c.sec) != ""; got != c.reject {
			t.Errorf("%s: reject = %v, want %v", c.name, got, c.reject)
		}
	}
}

// The Ladder mode exists because Mature's yield bar is the wrong instrument
// for a strategy that holds no inventory. This is the concrete case: a pool
// with the median profile of the 23 pools a profitable ladder LP actually
// worked (TVL ~$132k, 1% tier, ~2.6%/day fee pace, 8 days old). Mature must
// reject it on fee pace and Ladder must take it — if this ever inverts, the
// two modes have collapsed into one and rh-ladder is dead weight.
func TestLadderTakesChurnPoolsMatureRejects(t *testing.T) {
	now := time.Now()
	p := Pool{
		Address:      "0xc4a21f9d6485fc5893dd4a491b320a83daf4da1d",
		Name:         "CHURN / WETH 1%",
		Dex:          "uniswap-v3-robinhood",
		CreatedAt:    now.Add(-8 * 24 * time.Hour),
		BaseAddress:  "0x21028be78e8f521214d24328715c1a8aadbac5a8",
		BaseSymbol:   "CHURN",
		QuoteAddress: WETH,
		QuoteSymbol:  "WETH",
		FeePct:       1,
		ReserveUSD:   132000,
		FdvUSD:       1800000,
		// 343200 * 1% / 132000 = 2.6%/day — over Ladder's 1.5 floor, under
		// Mature's 8. Both modes read the realized 24h window (FeePaceH24).
		VolumeH24USD: 343200,
		VolumeH1USD:  14300,
		TxH1:         gtTxWindow{Buys: 25, Sells: 20, Buyers: 15, Sellers: 12},
		ChangeM5Pct:  1, ChangeH1Pct: 2, ChangeH6Pct: 3, ChangeH24Pct: 5,
	}

	if _, reason := Screen(p, Mature, now); reason == "" {
		t.Fatal("Mature accepted a 2.6%/day pool; its 8%/day bar is what makes rh-ladder necessary")
	} else if !strings.Contains(reason, "fee/TVL pace") {
		t.Fatalf("Mature rejected for the wrong reason: %q", reason)
	}

	cand, reason := Screen(p, Ladder, now)
	if reason != "" {
		t.Fatalf("Ladder rejected a pool matching its reference profile: %s", reason)
	}
	if cand.Mode != "rh-ladder" {
		t.Errorf("Mode = %q, want rh-ladder", cand.Mode)
	}
	if cand.FeeTVLDayPct < 2.5 || cand.FeeTVLDayPct > 2.7 {
		t.Errorf("FeeTVLDayPct = %.2f, want ~2.6", cand.FeeTVLDayPct)
	}
}

// A ladder is many NFTs but one entry, and the reference wallet ran 23 pools
// at once — so the mode must not inherit Mature's implicit "one book is
// enough" shape via a reserve ceiling that only fits a handful of pools.
func TestLadderAcceptsTheReserveBandMatureCapsOut(t *testing.T) {
	now := time.Now()
	p := Pool{
		Address:      "0xb7eedf33d02c743507c38e1ee20ef421e60661c6",
		Name:         "BIG / WETH 1%",
		Dex:          "uniswap-v3-robinhood",
		CreatedAt:    now.Add(-13 * 24 * time.Hour),
		BaseAddress:  "0x21028be78e8f521214d24328715c1a8aadbac5a8",
		BaseSymbol:   "BIG",
		QuoteAddress: WETH,
		QuoteSymbol:  "WETH",
		FeePct:       1,
		ReserveUSD:   1043554, // over Mature's 500k cap, inside Ladder's 2M
		FdvUSD:       19800000,
		VolumeH24USD: 1669686, // 1.6%/day — over Ladder's 1.5 floor, under Mature's 8
		VolumeH1USD:  65000,
		TxH1:         gtTxWindow{Buys: 40, Sells: 30, Buyers: 20, Sellers: 15},
		ChangeM5Pct:  0, ChangeH1Pct: 1, ChangeH6Pct: 2, ChangeH24Pct: 3,
	}
	if _, reason := Screen(p, Mature, now); !strings.Contains(reason, "reserve") {
		t.Fatalf("Mature should cap out on reserve, got %q", reason)
	}
	if _, reason := Screen(p, Ladder, now); reason != "" {
		t.Fatalf("Ladder rejected a $1.04M book: %s", reason)
	}
}

// stockPool is the profile of the venue's tokenized equities, read off the
// live USDG book on 2026-08-04: nvda / USDG 0.05%, $714k TVL, $3.42M of 24h
// volume — a 0.24%/day fee pace, an order of magnitude under anything a
// memecoin mode would look at.
func stockPool(now time.Time) Pool {
	return Pool{
		Address:      "0xd4eb21209c4d6093f80b5b84f5c45cc093ea14a3",
		Name:         "nvda / USDG 0.05%",
		Dex:          "uniswap-v3-robinhood",
		CreatedAt:    now.Add(-20 * 24 * time.Hour),
		BaseAddress:  "0x21028be78e8f521214d24328715c1a8aadbac5a8",
		BaseSymbol:   "nvda",
		QuoteAddress: USDG,
		QuoteSymbol:  "USDG",
		FeePct:       0.05,
		ReserveUSD:   714180,
		// 3.42M * 0.05% / 714180 = 0.24%/day.
		VolumeH24USD: 3420000,
		VolumeH1USD:  95000,
		// Thin h1 flow on purpose: equities trade on market hours, and the
		// mode's floors (10/3) exist to allow exactly this.
		TxH1:        gtTxWindow{Buys: 8, Sells: 6, Buyers: 5, Sellers: 4},
		ChangeM5Pct: 0.1, ChangeH1Pct: 0.4, ChangeH6Pct: -1, ChangeH24Pct: 2,
	}
}

// StockLadder exists for the pools every other mode is structurally blind to.
// If Ladder ever accepts this profile the two modes have collapsed and the
// WETH ladder is being sized off the wrong wallet balance.
func TestStockLadderTakesEquityPoolsLadderRejects(t *testing.T) {
	now := time.Now()
	p := stockPool(now)

	cand, reason := Screen(p, StockLadder, now)
	if reason != "" {
		t.Fatalf("StockLadder rejected its own reference profile: %s", reason)
	}
	if cand.Mode != "rh-usdg-ladder" {
		t.Errorf("Mode = %q, want rh-usdg-ladder", cand.Mode)
	}
	if cand.FeeTVLDayPct < 0.23 || cand.FeeTVLDayPct > 0.25 {
		t.Errorf("FeeTVLDayPct = %.3f, want ~0.24", cand.FeeTVLDayPct)
	}

	// Ladder must refuse it on the quote pin BEFORE the yield bar — the pin is
	// the safety property (rungs and sizing must share one asset), the yield
	// bar is only a preference.
	if _, reason := Screen(p, Ladder, now); !strings.Contains(reason, "quote-asset") {
		t.Fatalf("Ladder should reject a USDG pool on the quote pin, got %q", reason)
	}
}

// The mirror: StockLadder must not reach for WETH pools, or a batch of them
// would be sized in dollars off a WETH balance.
func TestStockLadderRejectsWethQuotedPools(t *testing.T) {
	now := time.Now()
	p := passingPool(now)
	p.CreatedAt = now.Add(-30 * 24 * time.Hour)
	p.VolumeH24USD = 300000
	if _, reason := Screen(p, StockLadder, now); !strings.Contains(reason, "quote-asset") {
		t.Fatalf("StockLadder should reject a WETH pool on the quote pin, got %q", reason)
	}
}

// The equity profile is invisible to every mode that came before it — and not
// on one gate but on three: the quote pin, the deep book, the 0.05% tier and
// the 0.24%/day pace each disqualify it independently. Documents WHY a fourth
// mode had to exist rather than a threshold tweak to Ladder.
func TestEquityProfileIsInvisibleToTheMemecoinModes(t *testing.T) {
	now := time.Now()
	p := stockPool(now)
	for _, mp := range []ModeParams{Fresh, Mature, Ladder} {
		if _, reason := Screen(p, mp, now); reason == "" {
			t.Errorf("%s accepted an equity pool — the memecoin modes must not size USDG books off the WETH balance", mp.Mode)
		}
	}
	// With the quote pin lifted, the yield bar alone still separates them: the
	// pace this pool prints is under both memecoin floors and over the equity
	// mode's. If that ordering ever breaks, rh-usdg-ladder has stopped being a
	// distinct thesis.
	pace := (p.VolumeH24USD * p.FeePct / 100) / p.ReserveUSD * 100
	if pace >= Ladder.MinFeeTVLDay || pace >= Mature.MinFeeTVLDay {
		t.Errorf("equity pace %.2f%%/day now clears a memecoin floor (ladder %.1f, mature %.1f)",
			pace, Ladder.MinFeeTVLDay, Mature.MinFeeTVLDay)
	}
	if pace < StockLadder.MinFeeTVLDay {
		t.Errorf("equity pace %.2f%%/day is under rh-usdg-ladder's own %.2f floor — the mode would screen nothing",
			pace, StockLadder.MinFeeTVLDay)
	}
}
