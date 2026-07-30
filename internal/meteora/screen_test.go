package meteora

import "testing"

// turnoverPool builds a synthetic pool that clears every turnover gate, so a
// test can flip exactly one field and attribute the outcome to that field.
// Numbers mirror a real qualifying pool's shape (small TVL, 2% fee tier, fast
// turnover) without being tied to any live pool.
func turnoverPool(verified *bool) Pool {
	base := Token{
		Address:       "Base1111111111111111111111111111111111111111",
		Symbol:        "TEST",
		OrganicScore:  75,
		MarketCap:     226_275,
		Holders:       3275,
		TopHoldersPct: 15.2,
		Verified:      verified,
		// Upstream tags an unverified token with severity "info", which the
		// warning-severity gate must keep ignoring — otherwise admitting
		// unverified tokens would be undone by the warnings loop.
		Warnings: []Warning{{Severity: "info", Message: "This token is not verified"}},
	}
	return Pool{
		PoolAddress:          "Pool1111111111111111111111111111111111111111",
		Name:                 "TEST-SOL",
		TVL:                  22_648,
		ActiveTVL:            21_521,
		FeeTVLRatio:          1.26,
		FeeActiveTVLRatio:    1.32,
		VolumeActiveTVLRatio: 39.9,
		VolumeTVLRatio:       37.9,
		FeePct:               2.0,
		SwapCount:            30,
		UniqueTraders:        20,
		UniqueLPs:            20,
		PositionsCreated:     20,
		Volatility:           4.3,
		TokenX:               base,
		TokenY:               Token{Address: SolMint, Symbol: "SOL", OrganicScore: 99},
		DlmmParams:           DlmmParams{BinStep: 100},
	}
}

func boolPtr(b bool) *bool { return &b }

// Turnover admits an unverified token (its thesis pools are never on the
// Jupiter strict list); casual/multiday still hard-reject it.
func TestScreenUnverified(t *testing.T) {
	tests := []struct {
		name       string
		mp         ModeParams
		verified   *bool
		wantReason string
		wantFlag   bool
	}{
		{"turnover admits unverified", Turnover, boolPtr(false), "", true},
		{"turnover admits verified", Turnover, boolPtr(true), "", false},
		{"turnover admits absent (fail-open)", Turnover, nil, "", false},
		{"casual rejects unverified", Casual, boolPtr(false), "not verified", false},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			p := turnoverPool(tc.verified)
			// Casual screens the same fixture only to prove the verified gate
			// still bites there; give it the mcap/holders it demands so the
			// reject can't come from an unrelated gate.
			if tc.mp.Mode == Casual.Mode {
				p.TokenX.MarketCap = 5_000_000
				p.TokenX.Holders = 12_000
			}
			cand, reason := Screen(p, tc.mp)
			if reason != tc.wantReason {
				t.Fatalf("reason = %q, want %q", reason, tc.wantReason)
			}
			if tc.wantReason != "" {
				return
			}
			if cand.Unverified != tc.wantFlag {
				t.Errorf("Unverified = %v, want %v", cand.Unverified, tc.wantFlag)
			}
		})
	}
}

// The haircut must actually land on the emitted score: it is what makes an
// unverified pool lose every tie-break and fall through LONE_MIN_SCORE and the
// pipeline's batch-conviction floor on its own.
func TestScreenUnverifiedScorePenalty(t *testing.T) {
	ok, reason := Screen(turnoverPool(boolPtr(true)), Turnover)
	if reason != "" {
		t.Fatalf("verified pool rejected: %s", reason)
	}
	bad, reason := Screen(turnoverPool(boolPtr(false)), Turnover)
	if reason != "" {
		t.Fatalf("unverified pool rejected: %s", reason)
	}
	if ok.Score <= 0 {
		t.Fatalf("verified score = %v, want > 0", ok.Score)
	}
	want := ok.Score * unverifiedScorePenalty
	if diff := bad.Score - want; diff > 1e-9 || diff < -1e-9 {
		t.Errorf("unverified score = %v, want %v (%.2f x %v)", bad.Score, want, unverifiedScorePenalty, ok.Score)
	}
}
