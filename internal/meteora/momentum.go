package meteora

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

var momentumClient = &http.Client{Timeout: 10 * time.Second}

// dexPair is one venue the token trades on. The token endpoint returns every
// one of them, which is why picking the right entry matters — see momentumFrom.
type dexPair struct {
	Liquidity struct {
		USD float64 `json:"usd"`
	} `json:"liquidity"`
	PriceChange struct {
		M5  float64 `json:"m5"`
		H1  float64 `json:"h1"`
		H6  float64 `json:"h6"`
		H24 float64 `json:"h24"`
	} `json:"priceChange"`
}

// dexResponse partially models the DexScreener token endpoint.
type dexResponse struct {
	Pairs []dexPair `json:"pairs"`
}

// implausibleChangePct is the floor below which a short-window price change is
// a bad read rather than a move — the Go twin of IMPLAUSIBLE_CHANGE_PCT in
// dlmm_monitor.py and dlmm_pipeline.py; keep the three in sync.
//
// No pool sheds 95% inside a 5-minute candle and still quotes: the liquidity
// is gone well before the last percent, which is why every real rug this bot
// has closed printed -20% to -35%. A -99.9% therefore means we read the wrong
// pair, and the token endpoint makes that easy — it lists every venue the mint
// trades on, husks included. Measured on Plumber 2026-08-15: 17 pairs, the
// live $46k pool quoting m5 -1.17% next to a $177 corpse quoting h1 -99.96%.
const implausibleChangePct = -95.0

// Momentum holds recent price-change percentages for a base mint.
type Momentum struct {
	M5, H1, H6, H24 float64
}

// GetMomentum fetches DexScreener price momentum for a base mint, reading the
// DEEPEST pair rather than pairs[0] — the endpoint's order is not a contract,
// and the deepest pool is where the token's price is actually discovered.
// Best-effort: on any error it returns ok=false and the caller fails open.
func GetMomentum(baseMint string) (Momentum, bool) {
	url := fmt.Sprintf("https://api.dexscreener.com/latest/dex/tokens/%s", baseMint)
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return Momentum{}, false
	}
	req.Header.Set("User-Agent", "Mozilla/5.0")
	resp, err := momentumClient.Do(req)
	if err != nil {
		return Momentum{}, false
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		io.Copy(io.Discard, io.LimitReader(resp.Body, 512))
		return Momentum{}, false
	}
	var dr dexResponse
	if err := json.NewDecoder(resp.Body).Decode(&dr); err != nil || len(dr.Pairs) == 0 {
		return Momentum{}, false
	}
	return momentumFrom(dr), true
}

// momentumFrom picks the pair to believe out of a token's venues and sanitizes
// it. Split out of GetMomentum so the choice is testable without the network —
// it is the half that had the bug.
func momentumFrom(dr dexResponse) Momentum {
	deepest := 0
	for i := range dr.Pairs {
		if dr.Pairs[i].Liquidity.USD > dr.Pairs[deepest].Liquidity.USD {
			deepest = i
		}
	}
	pc := dr.Pairs[deepest].PriceChange
	m := Momentum{M5: pc.M5, H1: pc.H1, H6: pc.H6, H24: pc.H24}
	// Neutralize an impossible short-window reading instead of rejecting on it.
	// 0 is this struct's "no move" — the gates are all `<= -N`, so a zeroed leg
	// passes, which is the same fail-open the caller applies when the whole
	// fetch fails. H6/H24 are left alone: a token really can be down 99% over a
	// day, and zeroing that would walk a corpse past the downtrend gate.
	if m.M5 <= implausibleChangePct {
		m.M5 = 0
	}
	if m.H1 <= implausibleChangePct {
		m.H1 = 0
	}
	return m
}

// MomentumReject applies the pipeline's momentum + downtrend gates for one
// mode. Returns a non-empty reason when the pool should be rejected.
//
// The mode decides the HORIZON, not the thresholds: a mode whose positions live
// minutes is not exposed to a six-hour trend, so it takes the short legs only
// (mp.SkipLongHorizonMomentum). Whether the gate runs at all is the caller's
// call — see ModeParams.SkipMomentumGate and ENABLE_MOMENTUM_GATE.
func MomentumReject(m Momentum, mp ModeParams) string {
	// Strategy overhaul 2026-07-20: entry failures were mostly downtrend catches.
	// Tighten short-horizon gates so we stop entering tokens already bleeding.
	if m.M5 <= -3 {
		return fmt.Sprintf("5m %.1f%% <= -3%% (dumping)", m.M5)
	}
	if m.H1 <= -7 {
		return fmt.Sprintf("1h %.1f%% <= -7%% (dumping)", m.H1)
	}
	if mp.SkipLongHorizonMomentum {
		return ""
	}
	// Sustained downtrend gate.
	if m.H6 <= -10 {
		return fmt.Sprintf("6h %.1f%% <= -10%% (downtrend)", m.H6)
	}
	if m.H24 <= -20 {
		return fmt.Sprintf("24h %.1f%% <= -20%% (downtrend)", m.H24)
	}
	return ""
}
