package meteora

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// discoverClient timeout mirrors the Python urllib timeout=15.
var discoverClient = &http.Client{Timeout: 15 * time.Second}

// minVolatilityTimeframe is the shortest window whose `volatility` field is
// worth screening on. Ported from the reference bot (MIN_VOLATILITY_TIMEFRAME):
// on a 5m window the API reports volatility 0 for any pool that simply did not
// move in the last five minutes, and Screen hard-rejects `volatility <= 0`.
// Measured 2026-08-01: that one condition was 346 of pulse's 476 rejects in a
// single day, including pools the reference bot entered and closed green. So
// for any mode querying a shorter window we re-read volatility (and the window
// volume, which the same detail call returns) at 30m and screen on THAT.
const minVolatilityTimeframe = "30m"

// timeframeMinutes covers the discovery API's accepted timeframe strings.
var timeframeMinutes = map[string]float64{
	"5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 120,
	"4h": 240, "6h": 360, "12h": 720, "24h": 1440,
}

// volatilityTimeframe returns the window to read volatility from: the mode's
// own timeframe when it already meets minVolatilityTimeframe, else that floor.
func volatilityTimeframe(src string) string {
	if m, ok := timeframeMinutes[src]; ok && m >= timeframeMinutes[minVolatilityTimeframe] {
		return src
	}
	return minVolatilityTimeframe
}

// volatilityRefetchWorkers bounds the extra detail calls in flight. Each is a
// page_size=1 lookup and the API-side filter already trims the page to a
// handful of pools (1-5 observed for pulse), so this only caps the tail.
const volatilityRefetchWorkers = 8

// buildFilters pushes the mode thresholds into the discovery API's filter_by
// query (ported from the reference discovery query) so the API returns pre-filtered
// pools instead of us discarding junk client-side. Screen still re-checks every
// gate locally (belt-and-suspenders) since the API filter is best-effort.
func buildFilters(mp ModeParams) string {
	f := []string{
		"pool_type=dlmm",
		"base_token_has_critical_warnings=false",
		"quote_token_has_critical_warnings=false",
		"base_token_has_high_single_ownership=false",
		"base_token_has_high_supply_concentration=false",
		fmt.Sprintf("base_token_market_cap>=%.0f", mp.MinMcap),
		fmt.Sprintf("base_token_holders>=%d", mp.MinHolders),
		fmt.Sprintf("tvl>=%.0f", mp.MinTVL),
		fmt.Sprintf("base_token_organic_score>=%.0f", mp.MinOrganic),
	}
	if mp.MinQuoteOrganic > 0 {
		f = append(f, fmt.Sprintf("quote_token_organic_score>=%.0f", mp.MinQuoteOrganic))
	}
	// base_token_market_cap<= is verified live — the reference config's own
	// discovery query pushes its maxMcap through this exact field.
	if mp.MaxMcap > 0 {
		f = append(f, fmt.Sprintf("base_token_market_cap<=%.0f", mp.MaxMcap))
	}
	if mp.MinBinStep > 0 {
		f = append(f, fmt.Sprintf("dlmm_bin_step>=%d", mp.MinBinStep))
	}
	if mp.MaxBinStep > 0 {
		f = append(f, fmt.Sprintf("dlmm_bin_step<=%d", mp.MaxBinStep))
	}
	// Turnover-mode thresholds. CAUTION: the API silently returns zero rows for
	// unknown filter fields (no error), so only fields verified live belong here.
	if mp.MaxTVL > 0 {
		f = append(f, fmt.Sprintf("tvl<=%.0f", mp.MaxTVL))
	}
	if mp.MinFeePct > 0 {
		f = append(f, fmt.Sprintf("fee_pct>=%.2f", mp.MinFeePct))
	}
	if mp.MinVolTVLRatio > 0 {
		f = append(f, fmt.Sprintf("volume_tvl_ratio>=%.2f", mp.MinVolTVLRatio))
	}
	if mp.MinSwapCount > 0 {
		f = append(f, fmt.Sprintf("swap_count>=%.0f", mp.MinSwapCount))
	}
	if mp.MinUniqueTraders > 0 {
		f = append(f, fmt.Sprintf("unique_traders>=%.0f", mp.MinUniqueTraders))
	}
	// Pulse-mode thresholds. Both fields are verified live — the reference
	// bot's own discovery query pushes exactly these two through filter_by.
	if mp.MinFeeActiveTVL > 0 {
		f = append(f, fmt.Sprintf("fee_active_tvl_ratio>=%.3f", mp.MinFeeActiveTVL))
	}
	if mp.MinVolumeUSD > 0 {
		f = append(f, fmt.Sprintf("volume>=%.0f", mp.MinVolumeUSD))
	}
	// fee_tvl_ratio is pushed API-side only for full-universe modes: with
	// category=all it is the core selectivity gate, while the trending modes
	// keep their historical query shape (Screen still gates it locally).
	if mp.MinFeeTVL > 0 && mp.Category == "all" {
		f = append(f, fmt.Sprintf("fee_tvl_ratio>=%.2f", mp.MinFeeTVL))
	}
	return strings.Join(f, "&&")
}

// FetchTopPools pulls the trending pools for a mode, applying the mode's
// thresholds API-side. Mirrors dlmm_pipeline.fetch_top_pools.
func FetchTopPools(baseURL string, mp ModeParams) ([]Pool, error) {
	category := mp.Category
	if category == "" {
		category = "trending"
	}
	reqURL := fmt.Sprintf("%s?page_size=50&timeframe=%s&category=%s&filter_by=%s",
		baseURL, mp.Timeframe, category, url.QueryEscape(buildFilters(mp)))
	if mp.SortBy != "" {
		reqURL += "&sort_by=" + url.QueryEscape(mp.SortBy)
	}
	req, err := http.NewRequest(http.MethodGet, reqURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0")

	resp, err := discoverClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 200))
		return nil, fmt.Errorf("discover HTTP %d: %s", resp.StatusCode, string(b))
	}

	var out discoverResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode discover: %w", err)
	}
	applyVolatilityTimeframe(baseURL, out.Data, mp)
	return out.Data, nil
}

// applyVolatilityTimeframe rewrites each pool's Volatility + VolumeWindow with
// the values read at minVolatilityTimeframe, in place. No-op for modes already
// querying a long-enough window (casual/multiday/turnover are all >= 30m), so
// only pulse pays for it. Best-effort and fail-open in both directions: a pool
// whose detail call fails keeps the values the page returned, exactly as if
// this step never ran.
//
// NOTE the API-side `volume>=` prefilter in buildFilters still applies at the
// mode's own timeframe — this only relaxes the LOCAL re-check in Screen, which
// is the same asymmetry the reference bot has.
func applyVolatilityTimeframe(baseURL string, pools []Pool, mp ModeParams) {
	tf := volatilityTimeframe(mp.Timeframe)
	if len(pools) == 0 || tf == mp.Timeframe {
		return
	}

	type detail struct {
		volatility float64
		volume     float64
		ok         bool
	}
	details := make([]detail, len(pools))

	var wg sync.WaitGroup
	sem := make(chan struct{}, volatilityRefetchWorkers)
	for i := range pools {
		if pools[i].PoolAddress == "" {
			continue
		}
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			p, err := fetchPoolDetail(baseURL, pools[i].PoolAddress, tf)
			if err != nil || p == nil {
				return
			}
			details[i] = detail{volatility: p.Volatility, volume: p.VolumeWindow, ok: true}
		}(i)
	}
	wg.Wait()

	for i := range pools {
		d := details[i]
		if !d.ok {
			continue
		}
		// Zero means the longer window says the pool really is flat — take it,
		// so Screen's `volatility <= 0` gate still catches genuinely dead pools.
		pools[i].Volatility = d.volatility
		if d.volume > 0 {
			pools[i].VolumeWindow = d.volume
		}
	}
}

// fetchPoolDetail re-reads one pool at a different timeframe. Mirrors the
// reference bot's fetchPoolDiscoveryDetail: same endpoint, pool_address as the
// only filter, page_size=1.
func fetchPoolDetail(baseURL, poolAddress, timeframe string) (*Pool, error) {
	reqURL := fmt.Sprintf("%s?page_size=1&timeframe=%s&filter_by=%s",
		baseURL, timeframe, url.QueryEscape("pool_address="+poolAddress))
	req, err := http.NewRequest(http.MethodGet, reqURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "Mozilla/5.0")

	resp, err := discoverClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(io.LimitReader(resp.Body, 200))
		return nil, fmt.Errorf("pool detail HTTP %d: %s", resp.StatusCode, string(b))
	}

	var out discoverResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode pool detail: %w", err)
	}
	if len(out.Data) == 0 {
		return nil, nil
	}
	return &out.Data[0], nil
}
