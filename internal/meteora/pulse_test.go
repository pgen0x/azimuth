package meteora

import (
	"strings"
	"testing"
)

// pulsePool builds a synthetic pool shaped like what the 5m trending window
// actually surfaces: inside the shared TVL/mcap/holder band, but WITHOUT the
// high base fee and fast turnover the turnover screen demands. Numbers mirror
// the live shape probed on 2026-08-01 (in-band 5m pools ran fee/active-TVL
// 0.01-0.05 on a few hundred dollars of window volume), so the fixture is a
// pool the two screens genuinely disagree about.
func pulsePool() Pool {
	base := Token{
		Address:       "Base2222222222222222222222222222222222222222",
		Symbol:        "MRDN",
		OrganicScore:  65,
		MarketCap:     412_000,
		Holders:       1_200,
		TopHoldersPct: 22.4,
		Verified:      boolPtr(false),
		Warnings:      []Warning{{Severity: "info", Message: "This token is not verified"}},
	}
	return Pool{
		PoolAddress:          "Pool2222222222222222222222222222222222222222",
		Name:                 "MRDN-SOL",
		TVL:                  28_993,
		ActiveTVL:            27_400,
		FeeTVLRatio:          0.058,
		FeeActiveTVLRatio:    0.061,
		VolumeWindow:         912,
		VolumeActiveTVLRatio: 0.033,
		VolumeTVLRatio:       0.031,
		FeePct:               0.25,
		SwapCount:            6,
		UniqueTraders:        5,
		UniqueLPs:            3,
		PositionsCreated:     2,
		Volatility:           4.3,
		TokenX:               base,
		TokenY:               Token{Address: SolMint, Symbol: "SOL", OrganicScore: 99},
		DlmmParams:           DlmmParams{BinStep: 100},
	}
}

// The whole point of the mode: a pool the reference bot would open and the
// turnover screen throws away. If this ever passes both, the two screens have
// converged and the second mode is only costing API calls.
func TestPulseAdmitsWhatTurnoverRejects(t *testing.T) {
	p := pulsePool()

	cand, reason := Screen(p, Pulse)
	if reason != "" {
		t.Fatalf("pulse rejected its own thesis pool: %s", reason)
	}
	if cand.Mode != "pulse" || cand.Timeframe != "5m" {
		t.Errorf("candidate = mode %q tf %q, want pulse/5m", cand.Mode, cand.Timeframe)
	}

	if _, reason := Screen(p, Turnover); reason == "" {
		t.Error("turnover admitted the pool too — the modes no longer sample different populations")
	}
}

// Each gate pulse does keep must still bite; a mode that rejects nothing is
// not a screen. Every case flips exactly one field off the passing fixture.
func TestPulseGates(t *testing.T) {
	tests := []struct {
		name    string
		mutate  func(*Pool)
		wantSub string
	}{
		{"fee/active-TVL below bar", func(p *Pool) { p.FeeActiveTVLRatio = 0.04 }, "fee/active-TVL"},
		{"window volume below bar", func(p *Pool) { p.VolumeWindow = 480 }, "volume $480"},
		{"TVL above ceiling", func(p *Pool) { p.TVL = 160_000 }, "cap"},
		{"mcap below floor", func(p *Pool) { p.TokenX.MarketCap = 140_000 }, "mcap"},
		{"holders below floor", func(p *Pool) { p.TokenX.Holders = 499 }, "holders"},
		{"organic below 60", func(p *Pool) { p.TokenX.OrganicScore = 59 }, "organic"},
		{"bin step outside band", func(p *Pool) { p.DlmmParams.BinStep = 200 }, "bin_step"},
		{"critical warning", func(p *Pool) {
			p.TokenX.Warnings = []Warning{{Severity: "critical", Message: "honeypot"}}
		}, "warning"},
		{"zero volatility", func(p *Pool) { p.Volatility = 0 }, "volatility"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			p := pulsePool()
			tc.mutate(&p)
			_, reason := Screen(p, Pulse)
			if !strings.Contains(reason, tc.wantSub) {
				t.Errorf("reason = %q, want it to mention %q", reason, tc.wantSub)
			}
		})
	}
}

// The gates pulse deliberately DROPS. These are the ones that let the
// reference bot into trending pools that are not high-fee oscillators; if a
// future edit re-tightens them, this mode stops reproducing its picks.
func TestPulseDropsTurnoverOnlyGates(t *testing.T) {
	tests := []struct {
		name   string
		mutate func(*Pool)
	}{
		// No volatility ceiling: casual/multiday/turnover cap at 15.
		{"volatility above the other modes' ceiling", func(p *Pool) { p.Volatility = 22 }},
		// No yield-decline gate: the other modes reject below -40%.
		{"yield collapsing", func(p *Pool) { p.FeeTVLRatioChangePct = -70 }},
		// Warning severity is narrowed to critical only.
		{"warning-severity token", func(p *Pool) {
			p.TokenX.Warnings = []Warning{{Severity: "warning", Message: "low liquidity"}}
		}},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			p := pulsePool()
			tc.mutate(&p)
			if _, reason := Screen(p, Pulse); reason != "" {
				t.Errorf("pulse rejected on a gate it does not have: %s", reason)
			}
		})
	}
}

// Moving the volatility ceiling and yield-decline gate onto ModeParams must not
// have quietly disarmed them for the modes that always had them.
func TestCeilingsStillArmedForOtherModes(t *testing.T) {
	for _, mp := range []ModeParams{Casual, Multiday, Turnover} {
		p := turnoverPool(boolPtr(true))
		// Widen the fixture until it clears all three modes' floors, so the
		// only thing left to reject it is the ceiling under test.
		p.TokenX.MarketCap, p.TokenX.Holders = 5_000_000, 12_000
		p.TVL, p.ActiveTVL = 60_000, 57_000

		p.Volatility = 22
		if _, reason := Screen(p, mp); !strings.Contains(reason, "volatility") {
			t.Errorf("%s: volatility ceiling disarmed (reason %q)", mp.Mode, reason)
		}

		p.Volatility = 4.3
		p.FeeTVLRatioChangePct = -70
		if _, reason := Screen(p, mp); !strings.Contains(reason, "yield declining") {
			t.Errorf("%s: yield-decline gate disarmed (reason %q)", mp.Mode, reason)
		}
	}
}

// The discovery query is where a typo costs the most: the API answers an
// unknown filter field with zero rows and no error, so a broken clause looks
// exactly like a quiet market. Both fields were probed live 2026-08-01.
func TestPulseDiscoveryFilters(t *testing.T) {
	got := buildFilters(Pulse)
	for _, want := range []string{
		"fee_active_tvl_ratio>=0.050",
		"volume>=500",
		"tvl>=10000",
		"tvl<=150000",
		"base_token_market_cap<=10000000",
		"dlmm_bin_step<=125",
	} {
		if !strings.Contains(got, want) {
			t.Errorf("filters missing %q\ngot: %s", want, got)
		}
	}
	// Turnover's gates must not leak in — they are what it screens on and
	// pulse does not have them.
	for _, unwanted := range []string{"fee_pct", "swap_count", "unique_traders", "volume_tvl_ratio"} {
		if strings.Contains(got, unwanted) {
			t.Errorf("filters contain turnover-only field %q\ngot: %s", unwanted, got)
		}
	}

	// And the reverse: turnover must not have picked up pulse's clauses.
	turnover := buildFilters(Turnover)
	for _, unwanted := range []string{"fee_active_tvl_ratio", "volume>="} {
		if strings.Contains(turnover, unwanted) {
			t.Errorf("turnover filters contain pulse-only field %q\ngot: %s", unwanted, turnover)
		}
	}
}
