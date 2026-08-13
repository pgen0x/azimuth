package meteora

import (
	"strings"
	"testing"
)

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
