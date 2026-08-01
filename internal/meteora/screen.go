package meteora

import (
	"fmt"
	"math"
)

// ModeParams are the per-mode screening thresholds, ported verbatim from
// dlmm_pipeline.py MODE_DEFAULTS / SOUL.md section 9.
type ModeParams struct {
	Mode            string
	Timeframe       string  // discovery timeframe to query
	TfMinutes       float64 // Timeframe in minutes (degen-score window normalization)
	MinTVL          float64 // MIN_TVL_USD
	MinFeeTVL       float64 // MIN_FEE_TVL_24H (percent)
	MinMcap         float64 // MIN_MCAP_USD
	MaxMcap         float64 // mcap ceiling (USD), 0 disables — see gate comment in Screen
	MinHolders      int     // MIN_HOLDERS
	MinDailyFee     float64 // absolute daily-fee floor (USD)
	MinOrganic      float64 // shared MIN_ORGANIC_SCORE
	MinQuoteOrganic float64 // quote-token organic floor (ported from the reference config)
	MinBinStep      int     // DLMM bin-step floor (0 disables the gate)
	MaxBinStep      int     // DLMM bin-step ceiling (0 disables the gate)

	// Turnover-mode gates, all zero-disabled so Casual/Multiday are unaffected.
	MaxTVL           float64 // TVL ceiling (bias small pools where our share matters)
	MinFeePct        float64 // pool base fee % floor (degen fee tiers are 1-5%)
	MinVolTVLRatio   float64 // volume/TVL turnover floor for the timeframe window
	MinSwapCount     float64 // swaps in window (wash-trade guard, with MinUniqueTraders)
	MinUniqueTraders float64 // unique traders in window

	// Pulse-mode gates. Zero-disabled like the block above; the reference
	// bot screens on the ACTIVE-TVL fee ratio and a raw window-volume floor
	// instead of on fee/TVL plus an absolute daily-fee floor.
	MinFeeActiveTVL float64 // fee/active-TVL floor for the window (percent)
	MinVolumeUSD    float64 // raw window volume floor (USD)

	// Ceilings the daemon used to apply unconditionally. Both are zero-disabled
	// so a mode can opt out, which means every mode that wants them must set
	// them explicitly. MaxYieldDecline is a negative percent (e.g. -40).
	MaxVolatility   float64 // IL guard: reject above this window volatility
	MaxYieldDecline float64 // reject when fee/TVL fell by more than this

	// AllowUnverified downgrades the is_verified gate from a hard reject to a
	// score penalty (unverifiedScorePenalty). Off by default — see the gate
	// itself in Screen for why turnover is the one mode that needs it.
	AllowUnverified bool

	// AllowWarningSeverity narrows the token-warning gate to "critical" only.
	// Off by default: casual/multiday/turnover also reject warning severity.
	AllowWarningSeverity bool

	// SkipMomentumGate opts a mode out of the scanner's DexScreener downtrend
	// gate (ENABLE_MOMENTUM_GATE still switches it off globally). Off by
	// default, so a mode keeps the gate unless it says otherwise — see Pulse
	// for the one screen that wants out and why.
	SkipMomentumGate bool

	// Discovery query knobs. Empty = the historical defaults ("trending", API
	// default sort) so Casual/Multiday queries are byte-identical to before.
	Category string
	SortBy   string
}

// Casual and Multiday mirror the two isolated budgets in the pipeline.
// Bin-step band (80–125) ported from the reference config config; tune per strategy.
//
// DIVERGENCE from dlmm_pipeline.py: casual MinFeeTVL is 0.1, not the upstream
// 0.3. The API's fee_tvl_ratio is scoped to the queried timeframe, so for the
// 30m casual window 0.3 demanded a ~14.4%/day fee pace — live probe (2026-07-05)
// showed the 30m median ratio at ~0.01%, so 0 of 50 pools passed most cycles.
// 0.1 (~4.8%/day pace) still sits ~5x above multiday's 1%/day bar.
var (
	// MinHolders recalibrated 2026-07-15 against the 14d close journal (102
	// live closes, net -0.09 SOL): big losers entered at median 7.8k holders,
	// winners at 13.6k. Backtest: casual >=10k flips the mode +0.002 -> +0.126
	// SOL (keeps 20/32 trades); multiday >=5k flips -0.014 -> +0.056 (17/23).
	// Holder count is token-level, so it is the one gate not confounded by the
	// per-mode discovery window.
	// MaxMcap (ported from the reference config, which caps at 10M on a 5m
	// degen window): a tail guard, not a fit gate. Every strategy assumption
	// here (volatility harvest, momentum entries, 30m/24h fee windows) is a
	// memecoin assumption; a $100M+ token passing the fee/TVL bar is almost
	// always a major having a busy day, where those assumptions don't hold.
	// Set well above the mode's real population so it only cuts that tail.
	Casual = ModeParams{
		Mode: "casual", Timeframe: "30m", TfMinutes: 30,
		MinTVL: 5000, MinFeeTVL: 0.1, MinMcap: 250000, MaxMcap: 100_000_000, MinHolders: 10000,
		MinDailyFee: 20, MinOrganic: 60, MinQuoteOrganic: 60,
		MinBinStep: 80, MaxBinStep: 125,
		MaxVolatility: 15, MaxYieldDecline: -40,
	}
	Multiday = ModeParams{
		Mode: "multiday", Timeframe: "24h", TfMinutes: 1440,
		MinTVL: 50000, MinFeeTVL: 1.0, MinMcap: 1000000, MaxMcap: 500_000_000, MinHolders: 5000,
		MinDailyFee: 150, MinOrganic: 60, MinQuoteOrganic: 60,
		MinBinStep: 80, MaxBinStep: 125,
		MaxVolatility: 15, MaxYieldDecline: -40,
	}

	// Turnover is NOT in the Python pipeline — it is this daemon's own mode,
	// targeting the niche the other two never see: small pools (TVL $5k-$300k)
	// with degen base fees (>=1%) turning their TVL over fast. Fee income is
	// fee_pct x turnover and is not capped by the monitor's trailing TP, so
	// this is the profit-maximizing screen. swap_count + unique_traders guard
	// against single-bot wash volume, letting organic relax to 50.
	//
	// Thresholds calibrated live 2026-07-05 against the 30m window: top fee
	// earners showed fee_tvl_ratio 0.1-0.3 (0.16-0.31 among qualifiers),
	// volume/TVL 2-15, swaps 15-80, traders 10-50; this exact filter set
	// matched 6 pools (best paying $382/30m on $128k TVL, ~14%/day pace).
	// MinFeeTVL 0.15/30m ~= 7.2%/day pace. Bin band widened to 250: high-fee
	// launch pools cluster at bin step 100-400.
	// 2026-07-28: TVL band, mcap band and bin-step ceiling realigned to the
	// reference bot's live screen, which is the one currently printing gains.
	// TVL 10k-150k (was 5k-300k): below 10k our ticket moves the price and the
	// exit swap strands; above 150k our share of the fee split is noise. Mcap
	// 150k-10M (was >=1M, no ceiling): the 150k-1M band is where fee-capture
	// pools actually live, and a 10M ceiling replaces "no ceiling" — a token
	// above it clearing the fee bar is usually a major having a busy day, where
	// the volatility-harvest assumption breaks. Bin step 80-125 (was 80-250):
	// wider steps make each bin a bigger price jump, so the ladder sits out of
	// range more and the 2m OOR fuse churns on noise instead of on fills.
	Turnover = ModeParams{
		Mode: "turnover", Timeframe: "30m", TfMinutes: 30,
		MinTVL: 10000, MinFeeTVL: 0.15, MinMcap: 150000, MaxMcap: 10_000_000, MinHolders: 500,
		MinDailyFee: 25, MinOrganic: 50, MinQuoteOrganic: 60,
		MinBinStep: 80, MaxBinStep: 125,
		MaxTVL: 150000, MinFeePct: 1.0, MinVolTVLRatio: 3.0,
		MinSwapCount: 20, MinUniqueTraders: 15,
		MaxVolatility: 15, MaxYieldDecline: -40,
		AllowUnverified: true,
		Category:        "all", SortBy: "fee:desc",
	}

	// Pulse exists because turnover's window was never the whole opportunity.
	// Observed 2026-08-01: across one day, five entries were available in this
	// band and turnover's screen only ever surfaced two of them — the other
	// three lived and died inside a 5m trending window that a 30m fee-sorted
	// query never sampled. The two screens do not overlap by design —
	//
	//   turnover: timeframe 30m, category=all, sort fee:desc
	//   pulse:    timeframe  5m, category=trending, API default sort
	//
	// so they sample different populations of the same universe. Running both
	// makes the daemon's entry set the UNION rather than turnover's slice of it.
	//
	// The band (TVL 10k-150k, mcap 150k-10M, holders 500, bin step 80-125,
	// organic 60/60) is identical to turnover's — 2026-07-28 realigned turnover
	// onto exactly these numbers. What differs is everything turnover added on
	// top and a plain trending screen never had:
	//   - no fee/TVL floor; it gates fee/ACTIVE-TVL >= 0.05 for the 5m window
	//   - no absolute daily-fee floor
	//   - a raw window-volume floor ($500) instead
	//   - no base-fee%, volume/TVL, swap-count or unique-trader gates: it takes
	//     trending pools that are not necessarily high-fee oscillators
	//   - no volatility ceiling and no yield-decline gate
	//   - no is_verified gate and no warning-severity gate (only the API's
	//     critical-warning / ownership / concentration booleans, which Screen
	//     already checks first)
	// Organic stays at 60, ABOVE turnover's relaxed 50: without the swap-count
	// and unique-trader wash-trade guards, organic score is the only
	// inorganic-volume defence left in the screen.
	//
	// The daemon's own Jupiter-audit / GMGN / PVP gates in the scanner still run
	// on this mode. They are fail-open and are the daemon's safety layer, so
	// this screen is looser than turnover's, not unguarded.
	//
	// The momentum gate is the exception (SkipMomentumGate). It is a
	// DIRECTIONAL filter and pulse is not a directional strategy: the position
	// is a SOL-side ladder harvesting fees from oscillation, and the monitor's
	// OOR fuse — not the entry — is what bounds the downside. Measured
	// 2026-08-01: the gate rejected Chiikawa 30+ times across 19:49-20:26 (1h
	// -7% to -23%, 5m -3% to -8.8%); the reference bot, which has no momentum
	// gate at all ("efficiency only, no momentum/change_pct, per design"),
	// entered at 20:25 inside that window and closed +1.39% on the fee take.
	// Turnover KEEPS the gate: its 30m fee-sorted screen is exactly where the
	// APR trap lives (a collapsing price paying huge fees on the way down), and
	// the gate has been catching those. Pulse's 5m trending window selects for
	// pools that are moving, so applying a downtrend gate on top of it rejects
	// most of the population the mode exists to sample.
	Pulse = ModeParams{
		Mode: "pulse", Timeframe: "5m", TfMinutes: 5,
		MinTVL: 10000, MinMcap: 150000, MaxMcap: 10_000_000, MinHolders: 500,
		MinOrganic: 60, MinQuoteOrganic: 60,
		MinBinStep: 80, MaxBinStep: 125,
		MaxTVL: 150000, MinFeeActiveTVL: 0.05, MinVolumeUSD: 500,
		AllowUnverified: true, AllowWarningSeverity: true,
		SkipMomentumGate: true,
		Category:         "trending",
	}
)

// Degen Score targets — each liquidity-relative sub-score saturates here.
// Ported from the reference config; inputs are normalized to a 30m reference window.
const (
	degenRefMinutes      = 30.0
	degenTargetVolRatio  = 20.0    // (30m) volume/active_tvl for a full trading sub-score
	degenTargetLpCount   = 40.0    // (30m) unique_lps + positions_created for a full LP sub-score
	degenTargetFeeRatio  = 0.20    // (30m) fee/active_tvl for a full fee sub-score
	degenTargetLiquidity = 20000.0 // active_tvl ($) for full liquidity sub-score (not TF-scaled)
)

// unverifiedScorePenalty scales the score of a token the API reports as
// is_verified=false, for the modes that let them through (AllowUnverified).
// Sized so an unverified pool always loses a tie-break to an equally strong
// verified one, and a marginal one drops itself through the lone-candidate
// floor (LONE_MIN_SCORE) and the pipeline's per-mode batch-conviction floor.
const unverifiedScorePenalty = 0.85

// SkipReason is returned (non-empty) when a pool fails a gate, for logging.
// A returned Candidate is only valid when reason == "".
func Screen(p Pool, mp ModeParams) (*Candidate, string) {
	// Orientation: exactly one side must be SOL.
	var base, quote Token
	var solIsX bool
	switch {
	case p.TokenY.Address == SolMint:
		base, quote, solIsX = p.TokenX, p.TokenY, false
	case p.TokenX.Address == SolMint:
		base, quote, solIsX = p.TokenY, p.TokenX, true
	default:
		return nil, "non-SOL pool"
	}

	// Authoritative API risk flags (ported from the reference config) — cheaper than parsing
	// the warnings array and caught before any threshold math.
	if p.HasCriticalWarnings {
		return nil, "base token critical warnings"
	}
	if p.QuoteHasCriticalWarnings {
		return nil, "quote token critical warnings"
	}
	if p.HasHighSingleOwnership {
		return nil, "base token high single ownership"
	}
	if p.HasHighSupplyConcentration {
		return nil, "base token high supply concentration"
	}

	if p.TVL < mp.MinTVL {
		return nil, fmt.Sprintf("TVL $%.0f < $%.0f", p.TVL, mp.MinTVL)
	}
	if p.FeeTVLRatio < mp.MinFeeTVL {
		return nil, fmt.Sprintf("fee/TVL %.2f%% < %.2f%%", p.FeeTVLRatio, mp.MinFeeTVL)
	}
	dailyFeeUSD := p.TVL * p.FeeTVLRatio / 100.0
	if dailyFeeUSD < mp.MinDailyFee {
		return nil, fmt.Sprintf("daily fees $%.0f < $%.0f", dailyFeeUSD, mp.MinDailyFee)
	}
	if p.Volatility <= 0 {
		return nil, "volatility <= 0"
	}
	if mp.MaxVolatility > 0 && p.Volatility > mp.MaxVolatility {
		return nil, fmt.Sprintf("volatility %.2f > %.0f (IL risk)", p.Volatility, mp.MaxVolatility)
	}
	if base.OrganicScore < mp.MinOrganic {
		return nil, fmt.Sprintf("organic %.0f < %.0f", base.OrganicScore, mp.MinOrganic)
	}
	if mp.MinQuoteOrganic > 0 && quote.OrganicScore < mp.MinQuoteOrganic {
		return nil, fmt.Sprintf("quote organic %.0f < %.0f", quote.OrganicScore, mp.MinQuoteOrganic)
	}
	if base.MarketCap < mp.MinMcap {
		return nil, fmt.Sprintf("mcap $%.0f < $%.0f", base.MarketCap, mp.MinMcap)
	}
	if mp.MaxMcap > 0 && base.MarketCap > mp.MaxMcap {
		return nil, fmt.Sprintf("mcap $%.0f > $%.0f cap", base.MarketCap, mp.MaxMcap)
	}
	if base.Holders < mp.MinHolders {
		return nil, fmt.Sprintf("holders %d < %d", base.Holders, mp.MinHolders)
	}
	if mp.MaxYieldDecline < 0 && p.FeeTVLRatioChangePct < mp.MaxYieldDecline {
		return nil, fmt.Sprintf("yield declining %.0f%%", p.FeeTVLRatioChangePct)
	}

	// Turnover-mode gates (zero-disabled for the other modes).
	if mp.MaxTVL > 0 && p.TVL > mp.MaxTVL {
		return nil, fmt.Sprintf("TVL $%.0f > $%.0f cap", p.TVL, mp.MaxTVL)
	}
	if mp.MinFeePct > 0 && p.FeePct < mp.MinFeePct {
		return nil, fmt.Sprintf("base fee %.2f%% < %.2f%%", p.FeePct, mp.MinFeePct)
	}
	if mp.MinVolTVLRatio > 0 && p.VolumeTVLRatio < mp.MinVolTVLRatio {
		return nil, fmt.Sprintf("volume/TVL %.2f < %.2f", p.VolumeTVLRatio, mp.MinVolTVLRatio)
	}
	if mp.MinSwapCount > 0 && p.SwapCount < mp.MinSwapCount {
		return nil, fmt.Sprintf("swaps %.0f < %.0f", p.SwapCount, mp.MinSwapCount)
	}
	if mp.MinUniqueTraders > 0 && p.UniqueTraders < mp.MinUniqueTraders {
		return nil, fmt.Sprintf("traders %.0f < %.0f", p.UniqueTraders, mp.MinUniqueTraders)
	}

	// Pulse-mode gates (zero-disabled for the other modes). fee/ACTIVE-TVL
	// is the reference bot's core selectivity gate: it measures the fee pace
	// against the liquidity actually in range, so a pool parking most of its
	// TVL in dead bins can't dilute its way past the bar the way fee/TVL lets it.
	if mp.MinFeeActiveTVL > 0 && p.FeeActiveTVLRatio < mp.MinFeeActiveTVL {
		return nil, fmt.Sprintf("fee/active-TVL %.3f%% < %.3f%%", p.FeeActiveTVLRatio, mp.MinFeeActiveTVL)
	}
	if mp.MinVolumeUSD > 0 && p.VolumeWindow < mp.MinVolumeUSD {
		return nil, fmt.Sprintf("volume $%.0f < $%.0f", p.VolumeWindow, mp.MinVolumeUSD)
	}

	// Supply-concentration safety gates.
	if base.TopHoldersPct > 60.0 {
		return nil, fmt.Sprintf("top10 own %.1f%% (>60%%)", base.TopHoldersPct)
	}
	if base.DevBalancePct > 20.0 {
		return nil, fmt.Sprintf("dev owns %.1f%% (>20%%)", base.DevBalancePct)
	}

	// Authority gates.
	if base.HasFreezeAuth {
		return nil, "freeze authority enabled"
	}
	if base.HasMintAuth {
		return nil, "mint authority enabled"
	}

	// Verified + Jupiter shield, fail-open when absent.
	//
	// The is_verified gate is HARD for casual/multiday but a score penalty for
	// turnover (AllowUnverified). "Fail-open when absent" never actually fired
	// here: the discovery API always emits is_verified, so this was a strict
	// Jupiter-list gate — and turnover deliberately hunts $10k-150k pools on
	// $150k-10M mcap tokens, which are never on that list. Live probe
	// 2026-07-28: 11 of 13 pools inside the turnover band were
	// is_verified=false, including the best-paying pool on the board (BNUT,
	// fee/TVL 1.28%/30m on $22k TVL), so the mode screened out its own thesis
	// and sent 0 batches. Rug risk stays covered by the holders / organic /
	// top10 / dev-balance / freeze-mint-authority gates plus the GMGN and
	// Jupiter-audit gates; upstream marks NOT_VERIFIED severity "info", not
	// "warning", so the warning-severity gate below deliberately ignores it.
	unverified := !boolOr(base.Verified, true)
	if unverified && !mp.AllowUnverified {
		return nil, "not verified"
	}
	jupShield := base.JupShieldVerified
	if jupShield == nil {
		jupShield = base.JupShield
	}
	if !boolOr(jupShield, true) {
		return nil, "failed Jupiter shield"
	}

	// Critical / warning severity gate. AllowWarningSeverity narrows it to
	// critical only, for the mode that ports a screen which never had it.
	for _, w := range base.Warnings {
		if w.Severity == "critical" || (w.Severity == "warning" && !mp.AllowWarningSeverity) {
			return nil, "warning: " + w.Message
		}
	}

	// Bin-step band gate (ported from the reference config). 0 endpoints disable each side.
	binStep := p.DlmmParams.BinStep
	if mp.MinBinStep > 0 && binStep < mp.MinBinStep {
		return nil, fmt.Sprintf("bin_step %d < %d", binStep, mp.MinBinStep)
	}
	if mp.MaxBinStep > 0 && binStep > mp.MaxBinStep {
		return nil, fmt.Sprintf("bin_step %d > %d", binStep, mp.MaxBinStep)
	}

	// Degen Score (0..100) replaces the old additive score: geometric mean of
	// four liquidity-relative sub-scores (trading / LP / fee / liquidity), so a
	// high score requires balance — no single metric can dominate. Falls back to
	// the additive score when the API omits the liquidity-relative inputs.
	score := degenScore(p, mp.TfMinutes)
	if score <= 0 {
		score = base.OrganicScore + (p.FeeActiveTVLRatio * 10) - (p.Volatility * 1.5)
		if p.FeeTVLRatioChangePct > 30 {
			score += 10
		}
	}
	if unverified {
		score *= unverifiedScorePenalty
	}

	return &Candidate{
		Mode:                 mp.Mode,
		Timeframe:            mp.Timeframe,
		Pool:                 p.PoolAddress,
		Name:                 p.Name,
		BaseMint:             base.Address,
		BaseSymbol:           base.Symbol,
		SolIsX:               solIsX,
		TVL:                  p.TVL,
		FeeTVLRatio:          p.FeeTVLRatio,
		FeeActiveTVLRatio:    p.FeeActiveTVLRatio,
		FeeTVLRatioChangePct: p.FeeTVLRatioChangePct,
		DailyFeeUSD:          dailyFeeUSD,
		Volatility:           p.Volatility,
		BinStep:              p.DlmmParams.BinStep,
		FeePct:               p.FeePct,
		VolumeTVLRatio:       p.VolumeTVLRatio,
		SwapCount:            p.SwapCount,
		UniqueTraders:        p.UniqueTraders,
		OrganicScore:         base.OrganicScore,
		Mcap:                 base.MarketCap,
		Holders:              base.Holders,
		TopHoldersPct:        base.TopHoldersPct,
		DevBalancePct:        base.DevBalancePct,
		Score:                score,
		Unverified:           unverified,
		ActiveTVL:            p.ActiveTVL,
		VolumeActiveTVLRatio: p.VolumeActiveTVLRatio,
		UniqueLPs:            p.UniqueLPs,
		PositionsCreated:     p.PositionsCreated,
	}, ""
}

// degenScore returns a pool's 0..100 efficiency score: the geometric mean of
// four liquidity-relative sub-scores (trading, LP activity, fees, liquidity).
// Any zero sub-score => 0, enforcing balance across all four. Window-dependent
// inputs are normalized to a 30m reference so the targets stay valid across
// timeframes. Returns 0 when active_tvl is missing (caller falls back).
func degenScore(p Pool, tfMinutes float64) float64 {
	la := p.ActiveTVL
	if la <= 0 {
		la = p.TVL
	}
	if la <= 0 || tfMinutes <= 0 {
		return 0
	}
	tfScale := degenRefMinutes / tfMinutes

	// When the API omits the precomputed ratios, derive them from the raw
	// window volume/fee (mirrors the reference config). Without this, a missing ratio
	// zeroes the sub-score, zeroes the whole degen score, and the caller
	// falls back to the additive score — which silently bypasses the
	// lone-candidate conviction gate (additive scores sit near 75+).
	tradingRatio := p.VolumeActiveTVLRatio
	if tradingRatio <= 0 {
		tradingRatio = p.VolumeWindow / la
	}
	feeRatio := p.FeeActiveTVLRatio
	if feeRatio <= 0 {
		feeRatio = p.FeeWindow / la
	}
	tradingRatio *= tfScale
	feeRatio *= tfScale
	lpActivity := (p.UniqueLPs + p.PositionsCreated) * tfScale

	sTrading := clamp01(tradingRatio / degenTargetVolRatio)
	sLp := clamp01(lpActivity / degenTargetLpCount)
	sFees := clamp01(feeRatio / degenTargetFeeRatio)
	sLiq := clamp01(math.Log10(la) / math.Log10(degenTargetLiquidity))

	return math.Pow(sTrading*sLp*sFees*sLiq, 0.25) * 100
}

func clamp01(x float64) float64 {
	if math.IsNaN(x) || math.IsInf(x, 0) || x < 0 {
		return 0
	}
	if x > 1 {
		return 1
	}
	return x
}
