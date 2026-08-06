package robinhood

import (
	"context"
	"math"
	"strconv"
	"strings"
	"testing"
	"time"
)

// defaults mirrors config.go's ROBINHOOD_DEPLOY_* defaults.
func defaults() SizeParams {
	return SizeParams{Reserve: 0.002, Pct: 0.45, Floor: 0.003, Ceil: 0.05}
}

func TestComputeDeployAmount(t *testing.T) {
	tests := []struct {
		name    string
		balance float64
		params  SizeParams
		want    float64
	}{
		{
			// The live wallet that motivated this: the old fixed 0.003 WETH size
			// was deploying ~17% of it. (0.017410 - 0.002) * 0.45 = 0.0069345.
			name:    "live wallet sizes up from the old fixed 0.003",
			balance: 0.017410,
			params:  defaults(),
			want:    0.0069345,
		},
		{
			// Percentage of the REMAINING balance, so exposure tapers as
			// positions stack instead of marching to a zero balance. The reserve
			// is subtracted every time, not just on the first deploy:
			// (0.0104755 - 0.002) * 0.45 = 0.003813975.
			name:    "second position is smaller than the first",
			balance: 0.017410 - 0.0069345,
			params:  defaults(),
			want:    0.003813975,
		},
		{
			// Above the floor in total, but the 45% haircut lands under it —
			// deploy exactly the floor rather than dust.
			name:    "haircut below floor clamps up to floor",
			balance: 0.008,
			params:  defaults(),
			want:    0.003,
		},
		{
			// Deployable = 0.003, exactly the floor -> fundable, deploys floor.
			name:    "exactly floor-fundable deploys the floor",
			balance: 0.005,
			params:  defaults(),
			want:    0.003,
		},
		{
			// 0.004 - 0.002 = 0.002 deployable < 0.003 floor -> skip entirely.
			// 0 means SKIP, never "deploy nothing".
			name:    "below floor after reserve returns 0 (skip)",
			balance: 0.004,
			params:  defaults(),
			want:    0,
		},
		{
			name:    "empty wallet skips",
			balance: 0,
			params:  defaults(),
			want:    0,
		},
		{
			name:    "balance under reserve skips (no negative size)",
			balance: 0.001,
			params:  defaults(),
			want:    0,
		},
		{
			// Scales with the wallet without a config edit — until the ceil.
			// (1.0 - 0.002) * 0.45 = 0.4491, capped to 0.05.
			name:    "whale wallet clamps to ceil",
			balance: 1.0,
			params:  defaults(),
			want:    0.05,
		},
		{
			name:    "zero ceil means uncapped",
			balance: 1.0,
			params:  SizeParams{Reserve: 0.002, Pct: 0.45, Floor: 0.003, Ceil: 0},
			want:    0.4491,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ComputeDeployAmount(tt.balance, tt.params)
			if math.Abs(got-tt.want) > 1e-9 {
				t.Errorf("ComputeDeployAmount(%v) = %v, want %v", tt.balance, got, tt.want)
			}
		})
	}
}

// A deploy must never spend more than the wallet holds, nor dip into the
// reserve — the two properties that turn a sizing bug into a drained wallet.
func TestComputeDeployAmountNeverOverspends(t *testing.T) {
	p := defaults()
	for _, bal := range []float64{0, 0.001, 0.002, 0.003, 0.005, 0.0174, 0.1, 1, 100} {
		got := ComputeDeployAmount(bal, p)
		if got < 0 {
			t.Fatalf("balance %v: negative size %v", bal, got)
		}
		if got > bal {
			t.Fatalf("balance %v: size %v exceeds balance", bal, got)
		}
		if got > 0 && got > bal-p.Reserve {
			t.Fatalf("balance %v: size %v eats into the %v reserve", bal, got, p.Reserve)
		}
	}
}

// The executor prints ether amounts as decimal STRINGS (viem formatEther), and
// its JSON payload is the LAST stdout line, after any tx-log noise.
func TestLastLineStripsLogNoise(t *testing.T) {
	out := "some tx log noise\n" +
		`{"address":"0xABCDEF0000000000000000000000000000000000","eth":"0.00084617594819808","weth":"0.017409921705255751"}`
	line := lastLine(out)
	if line == "" || line[0] != '{' {
		t.Fatalf("lastLine did not strip log noise: %q", line)
	}
	if got := lastLine("  single line  "); got != "single line" {
		t.Fatalf("lastLine single-line = %q", got)
	}
}

// A mint that reverts without opening a position exits 0 (the executor sells the
// swap leg back to WETH and reports it), so Summarize must recognise its marker
// line instead of falling through and reporting the raw JSON result line.
func TestSummarizeReportsFailedDeployInWords(t *testing.T) {
	out := "swap 0.0015 WETH -> token: 0xabc\n" +
		"mint failed (no position opened): Price slippage check\n" +
		"❌ DEPLOY FAILED (no position opened): Price slippage check, refunded 0.00148 WETH\n" +
		`{"success":false,"error":"mint failed: Price slippage check","pool":"0xdead"}`

	got := Summarize(out)
	if strings.Contains(got, "{") {
		t.Fatalf("Summarize leaked the JSON result line: %q", got)
	}
	if !strings.Contains(got, "DEPLOY FAILED") || !strings.Contains(got, "refunded 0.00148 WETH") {
		t.Fatalf("Summarize dropped the failure detail: %q", got)
	}
	if Deployed(out) {
		t.Fatal("Deployed() must be false when no position was opened")
	}
}

// fakeRunner builds a Runner whose "executor" is a shell snippet printing a
// canned stdout. run() appends the subcommand as an extra argv, which `sh -c`
// binds to $0 and ignores, so the snippet runs unchanged.
func fakeRunner(stdout string) *Runner {
	return &Runner{execCmd: []string{"sh", "-c", "printf '%s\\n' " + strconv.Quote(stdout)}, timeout: 5 * time.Second}
}

// Under weth_ladder one entry mints N rungs, so counting NPM NFTs would report
// a single ladder as N positions and a cap of 3 would reject every deploy
// after the first. The cap is denominated in entries; the executor reports
// both numbers and OpenPositions must prefer `ladders`.
func TestOpenPositionsCountsLaddersNotNFTs(t *testing.T) {
	got, err := fakeRunner(`{"address":"0xabc","count":5,"ladders":1}`).OpenPositions(context.Background())
	if err != nil {
		t.Fatalf("OpenPositions: %v", err)
	}
	if got != 1 {
		t.Fatalf("OpenPositions = %d, want 1 (5 NFTs are one ladder)", got)
	}
}

// The v4 executor and any build predating the field report only `count`, where
// one position really is one entry. Zero ladders and a missing field must not
// be confused: only the missing field may fall back.
func TestOpenPositionsFallsBackToCountWhenLaddersAbsent(t *testing.T) {
	got, err := fakeRunner(`{"address":"0xabc","count":2}`).OpenPositions(context.Background())
	if err != nil {
		t.Fatalf("OpenPositions: %v", err)
	}
	if got != 2 {
		t.Fatalf("OpenPositions = %d, want 2 (no ladders field -> count)", got)
	}
	got, err = fakeRunner(`{"address":"0xabc","count":4,"ladders":0}`).OpenPositions(context.Background())
	if err != nil {
		t.Fatalf("OpenPositions: %v", err)
	}
	if got != 0 {
		t.Fatalf("OpenPositions = %d, want 0 — an explicit ladders:0 must not fall back to count", got)
	}
}

// Why the per-token cap exists: one underlying listing at several fee tiers is
// normal here, and a wallet-wide slot count cannot see that three walls are one
// price bet. Inventory attributes each POOL — not each rung — to its base token.
func TestInventoryCountsPoolsPerBaseToken(t *testing.T) {
	// GME at two tiers (3 rungs + 2 rungs) and NVDA at one, all USDG-quoted.
	const gme, nvda = "0x1b0e319c6a659f002271b69db8a7df2f911c153e", "0xd0601ce157db5bdc3162bbac2a2c8af5320d9eec"
	out := `{"address":"0xabc","count":6,"ladders":3,"positions":[{"tokenId":"1","token0":"` + gme + `","token1":"` + USDG + `","fee":3000,"liquidity":"100"},{"tokenId":"2","token0":"` + gme + `","token1":"` + USDG + `","fee":3000,"liquidity":"200"},{"tokenId":"3","token0":"` + gme + `","token1":"` + USDG + `","fee":3000,"liquidity":"300"},{"tokenId":"4","token0":"` + gme + `","token1":"` + USDG + `","fee":10000,"liquidity":"100"},{"tokenId":"5","token0":"` + gme + `","token1":"` + USDG + `","fee":10000,"liquidity":"200"},{"tokenId":"6","token0":"` + nvda + `","token1":"` + USDG + `","fee":500,"liquidity":"100"}]}`

	inv, err := fakeRunner(out).Inventory(context.Background())
	if err != nil {
		t.Fatalf("Inventory: %v", err)
	}
	if inv.Ladders != 3 {
		t.Fatalf("Ladders = %d, want 3 (the executor's own count)", inv.Ladders)
	}
	// Two POOLS of GME, not five rungs of it.
	if got := inv.ByToken[gme]; got != 2 {
		t.Fatalf("GME = %d, want 2 pools (5 rungs across 2 fee tiers)", got)
	}
	if got := inv.ByToken[nvda]; got != 1 {
		t.Fatalf("NVDA = %d, want 1", got)
	}
	if got := inv.ByToken[strings.ToLower(USDG)]; got != 0 {
		t.Fatalf("the quote asset must never count as an underlying, got %d", got)
	}
}

// v4 reports pool sides as currency0/currency1, and one pair+fee can exist at
// several tick spacings — those are different pools. Both facts must survive the
// decode or the cap silently under-counts.
func TestInventoryHandlesV4FieldsAndTickSpacing(t *testing.T) {
	const tsla = "0x322f0929c4625ed5bad873c95208d54e1c003b2d"
	out := `{"address":"0xabc","count":2,"ladders":2,"positions":[{"tokenId":"1","protocol":"v4","currency0":"` + tsla + `","currency1":"` + USDG + `","fee":3000,"tickSpacing":60,"liquidity":"100"},{"tokenId":"2","protocol":"v4","currency0":"` + tsla + `","currency1":"` + USDG + `","fee":3000,"tickSpacing":10,"liquidity":"100"}]}`

	inv, err := fakeRunner(out).Inventory(context.Background())
	if err != nil {
		t.Fatalf("Inventory: %v", err)
	}
	if got := inv.ByToken[tsla]; got != 2 {
		t.Fatalf("TSLA = %d, want 2 — one pair and fee at two tick spacings is two pools", got)
	}
}

// A rung drained to zero liquidity holds nothing, exactly as the executors' own
// `ladders` count treats it. Counting one would keep a token blocked forever
// after its wall was closed.
func TestInventoryIgnoresDrainedRungs(t *testing.T) {
	const uso = "0xa30fa36db767ad9ed3f7a60fc79526fb4d56d344"
	out := `{"address":"0xabc","count":2,"ladders":0,"positions":[{"tokenId":"1","token0":"` + uso + `","token1":"` + USDG + `","fee":3000,"liquidity":"0"},{"tokenId":"2","token0":"` + uso + `","token1":"` + USDG + `","fee":3000,"liquidity":"0"}]}`

	inv, err := fakeRunner(out).Inventory(context.Background())
	if err != nil {
		t.Fatalf("Inventory: %v", err)
	}
	if len(inv.ByToken) != 0 {
		t.Fatalf("drained rungs hold no token, got %v", inv.ByToken)
	}
}

// A quote/quote pool (the WETH/USDG wall minted before that gate closed) has no
// underlying to cap, so it attributes to neither side — while still spending a
// wallet-wide slot, which `ladders` already accounts for.
func TestInventorySkipsQuoteOnlyPools(t *testing.T) {
	out := `{"address":"0xabc","count":3,"ladders":1,"positions":[{"tokenId":"1","token0":"` + WETH + `","token1":"` + USDG + `","fee":3000,"liquidity":"100"}]}`

	inv, err := fakeRunner(out).Inventory(context.Background())
	if err != nil {
		t.Fatalf("Inventory: %v", err)
	}
	if len(inv.ByToken) != 0 {
		t.Fatalf("a quote/quote pool has no underlying, got %v", inv.ByToken)
	}
	if inv.Ladders != 1 {
		t.Fatalf("it still occupies a slot: Ladders = %d, want 1", inv.Ladders)
	}
}

// Callers fail closed on error, so an unreadable payload must BE an error and
// never an empty-but-successful census — that would read as "holds nothing" and
// unblock every candidate.
func TestInventoryErrorsOnUnparseableOutput(t *testing.T) {
	if _, err := fakeRunner("not json").Inventory(context.Background()); err == nil {
		t.Fatal("unparseable positions output must error, not return an empty inventory")
	}
}
