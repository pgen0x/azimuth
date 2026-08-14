package meteora

import (
	"strings"
	"testing"
)

// newPair builds one venue entry for the pair-selection table below.
func newPair(liqUSD, m5, h1, h6, h24 float64) dexPair {
	var p dexPair
	p.Liquidity.USD = liqUSD
	p.PriceChange.M5 = m5
	p.PriceChange.H1 = h1
	p.PriceChange.H6 = h6
	p.PriceChange.H24 = h24
	return p
}

// The regression this covers: on 2026-08-14 the Solana modes opened nothing for
// 12h because rug blacklists had been written off -99.9% five-minute reads that
// belonged to husk pools rather than to ours. Both halves of the fix are pinned
// here — believe the deepest venue, and refuse an impossible short window.
func TestMomentumFromPicksDeepestAndRejectsImpossibleReads(t *testing.T) {
	cases := []struct {
		name  string
		pairs []dexPair
		want  Momentum
	}{
		{
			// The live Plumber shape, 2026-08-15: a $177 corpse listed ahead of
			// the real $45k pool. Reading pairs[0] would have seen -99.96%.
			name: "husk listed first loses to the deepest pool",
			pairs: []dexPair{
				newPair(177, -99.9, -99.96, -99.98, -99.98),
				newPair(45690, -1.17, -16.16, -35.01, -38.21),
				newPair(825, 0.97, -13.47, -30.0, -37.39),
			},
			want: Momentum{M5: -1.17, H1: -16.16, H6: -35.01, H24: -38.21},
		},
		{
			// Nothing but a husk to read: the floor is the second line of
			// defence, so the short legs go neutral and the day legs stay honest.
			name:  "impossible short windows neutralized, long ones survive",
			pairs: []dexPair{newPair(500, -99.9, -100, -99.98, -99.99)},
			want:  Momentum{M5: 0, H1: 0, H6: -99.98, H24: -99.99},
		},
		{
			// A genuine rug prints in the -20s/-30s and must pass through intact.
			name:  "a real rug is left alone",
			pairs: []dexPair{newPair(20000, -21.5, -30.3, -40, -55)},
			want:  Momentum{M5: -21.5, H1: -30.3, H6: -40, H24: -55},
		},
		{
			// Equal depth must not panic or reorder; first wins deterministically.
			name:  "ties keep the first pair",
			pairs: []dexPair{newPair(100, -1, -2, -3, -4), newPair(100, -5, -6, -7, -8)},
			want:  Momentum{M5: -1, H1: -2, H6: -3, H24: -4},
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := momentumFrom(dexResponse{Pairs: tc.pairs})
			if got != tc.want {
				t.Fatalf("momentumFrom() = %+v, want %+v", got, tc.want)
			}
		})
	}
}

// The floor must not disarm the gate it protects: a real rug still rejects, and
// the long horizons still bind after the short legs have been zeroed.
func TestSanitizedMomentumStillGates(t *testing.T) {
	if r := MomentumReject(Momentum{M5: -21.5, H1: -30.3}, Casual); r == "" {
		t.Fatal("a -21.5% 5m rug must still be rejected")
	}
	if r := MomentumReject(Momentum{M5: 0, H1: 0, H6: -35, H24: -38}, Casual); r == "" {
		t.Fatal("long horizons must still gate once the short legs are zeroed")
	}
	if r := MomentumReject(Momentum{M5: -1.17, H1: -6, H6: -5, H24: -10}, Casual); r != "" {
		t.Fatalf("healthy pool must pass, got reject: %s", r)
	}
}

func TestMomentumRejectTightenedDumpGates(t *testing.T) {
	cases := []struct {
		name string
		m    Momentum
		mp   ModeParams
		want string
	}{
		{"m5 dump", Momentum{M5: -3.1}, Casual, "5m -3.1% <= -3%"},
		{"h1 dump", Momentum{M5: 0, H1: -7.1}, Casual, "1h -7.1% <= -7%"},
		{"h6 downtrend", Momentum{M5: 0, H1: 0, H6: -10.1}, Casual, "6h -10.1% <= -10%"},
		{"h24 downtrend", Momentum{M5: 0, H1: 0, H6: 0, H24: -20.1}, Casual, "24h -20.1% <= -20%"},
		{"passes", Momentum{M5: -2.9, H1: -6.9, H6: -9.9, H24: -19.9}, Casual, ""},

		// Turnover holds for minutes, so the long horizons cannot bind on it —
		// but the short ones still must, because that is where a token dying
		// inside the hold shows up. BOIÚNA (6h -24.6%) and MARIO64 (24h -72.9%)
		// are the live 2026-08-13 rejections this opts out of.
		{"turnover ignores h6", Momentum{H6: -24.6}, Turnover, ""},
		{"turnover ignores h24", Momentum{H24: -72.9}, Turnover, ""},
		{"turnover still cuts m5", Momentum{M5: -3.1, H6: -24.6}, Turnover, "5m -3.1% <= -3%"},
		{"turnover still cuts h1", Momentum{H1: -7.1, H24: -72.9}, Turnover, "1h -7.1% <= -7%"},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := MomentumReject(tc.m, tc.mp)
			if tc.want == "" {
				if got != "" {
					t.Fatalf("MomentumReject() = %q, want pass", got)
				}
				return
			}
			if !strings.Contains(got, tc.want) {
				t.Fatalf("MomentumReject() = %q, want contains %q", got, tc.want)
			}
		})
	}
}
