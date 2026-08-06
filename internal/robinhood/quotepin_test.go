package robinhood

import (
	"strings"
	"testing"
	"time"
)

// The bug this pins down: v4 pools ether natively (zero address) and v3 pools
// use the ERC-20 wrapper, both spelled "WETH" by the feeds. A WETH pin that
// compared addresses exactly saw 2 of the 70 pools the pulse registry carried
// on 2026-08-07.
func TestQuotePinMatchAcceptsBothEtherSpellings(t *testing.T) {
	cases := []struct {
		name      string
		poolQuote string
		pin       string
		want      bool
	}{
		{"wrapped pool, WETH pin", WETH, WETH, true},
		{"native pool, WETH pin", NativeETH, WETH, true},
		{"wrapped pool, native pin", WETH, NativeETH, true},
		{"usdg pool, WETH pin", USDG, WETH, false},
		{"native pool, USDG pin", NativeETH, USDG, false},
		{"usdg pool, USDG pin", USDG, USDG, true},
	}
	for _, c := range cases {
		if got := quotePinMatch(c.poolQuote, c.pin); got != c.want {
			t.Errorf("%s: quotePinMatch(%q, %q) = %v, want %v", c.name, c.poolQuote, c.pin, got, c.want)
		}
	}
}

// A USDG ladder must never see an ether pool: its rungs are dollars and its
// sizing reads the USDG balance.
func TestQuotePinKeepsLaddersApart(t *testing.T) {
	if quotePinMatch(NativeETH, StockLadder.QuoteAsset) {
		t.Error("a native-ETH pool must not satisfy the USDG-pinned stock ladder")
	}
	if !quotePinMatch(NativeETH, PulseLadder.QuoteAsset) {
		t.Error("a native-ETH pool is exactly what the WETH-pinned pulse ladder trades")
	}
}

// End to end through the filter the pulse ladder actually calls.
func TestLadderEligibleAcceptsNativeETHPool(t *testing.T) {
	now := time.Now()
	native := youngPool("0xnative", now.Add(-2*time.Hour))
	native.Protocol = "v4"
	native.Dex = "uniswap-v4-robinhood"
	native.QuoteAddress = NativeETH
	native.QuoteSymbol = "WETH"

	usdgSide := youngPool("0xusdg", now.Add(-2*time.Hour))
	usdgSide.QuoteAddress = USDG
	usdgSide.QuoteSymbol = "USDG"

	got := addrsOf(ladderEligible([]Pool{native, usdgSide}, PulseLadder))
	if len(got) != 1 || got[0] != "0xnative" {
		t.Fatalf("want only the native-ETH pool eligible for a WETH ladder, got %v", got)
	}
}

// Screen is the gate the scanner runs; the pin must agree with ladderEligible
// or a pool clears discovery and dies one layer later.
func TestScreenAcceptsNativeETHQuote(t *testing.T) {
	now := time.Now()
	p := youngPool("0xnative", now.Add(-2*time.Hour))
	p.Protocol = "v4"
	p.Dex = "uniswap-v4-robinhood"
	p.QuoteAddress = NativeETH
	p.QuoteSymbol = "WETH"

	if _, reason := Screen(p, PulseLadder, now); strings.Contains(reason, "quote-asset") {
		t.Fatalf("a native-ETH pool must not be rejected on the quote pin, got %q", reason)
	}
}
