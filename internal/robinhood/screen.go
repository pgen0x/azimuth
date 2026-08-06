package robinhood

import (
	"fmt"
	"math"
	"strings"
	"time"
)

// ModeParams are the per-mode screening thresholds for the Robinhood Chain
// venue. Unlike the Solana modes (verbatim ports of dlmm_pipeline.py), these
// are FIRST-PASS values chosen from the 2026-07-13 spike sample and exist to
// be recalibrated from Phase 1 signal-only journals — expect churn.
type ModeParams struct {
	Mode string

	MinAge time.Duration // dodge the first sniper/MEV minutes of a launch
	MaxAge time.Duration // stay inside the mode's thesis window (0 disables)

	MinReserveUSD float64 // liquidity floor: LP fees on dust reserves round to zero
	MaxReserveUSD float64 // ceiling biases small pools where our share matters (0 disables)
	MinFeePct     float64 // v3 fee tier floor; memecoin launches sit at 1% (Noxa default)
	MinFeeTVLDay  float64 // projected daily fee/TVL % floor (volume pace x fee tier)
	MinTxH1       int     // swaps in the last hour (wash guard with MinBuyersH1)
	MinBuyersH1   int     // unique buyers in the last hour
	MinFdvUSD     float64 // FDV sanity floor
	MaxFdvUSD     float64 // FDV sanity ceiling (0 disables): fake-priced pools show absurd FDV

	// QuoteAsset pins the mode to ONE quote-side asset (lowercase address; ""
	// accepts any whitelisted quote). Ladder modes must set it: a ladder's
	// rungs are denominated in the pool's quote asset, and the deploy sizes
	// against that asset's wallet balance — a mode whose batch mixed WETH- and
	// USDG-quoted pools would size in one unit and mint in another.
	QuoteAsset string

	// FeePaceH24 measures the fee/TVL pace over the realized 24h volume instead
	// of extrapolating the h1 window out to a day. Modes selecting for
	// SUSTAINED fee generation must set it: under h1 extrapolation one busy
	// hour mints a 24x-inflated daily rate, which is precisely the pool a
	// mature mode must not buy. Fresh leaves it false — a pool minutes old has
	// no 24h history to measure, so extrapolating is the only option it has.
	FeePaceH24 bool
}

// Fresh is the starter mode: young Uniswap v3 WETH pools already showing
// two-sided flow. One mode only until the signal-only journals justify more.
var Fresh = ModeParams{
	Mode:   "rh-fresh",
	MinAge: 3 * time.Minute,
	MaxAge: 24 * time.Hour,
	// 8000 (initial guess, set by analogy to Solana casual mode) killed 73% of
	// all pools before any other gate ran — live sample 2026-07-13 showed
	// median reserve ~$3,959, only 6/16 pools clearing $8k. 2500 lets the
	// bulk of real launches through to the gates that actually matter
	// (txn/buyer counts, honeypot shape, GMGN security) — see
	// docs/ROBINHOOD_CHAIN_PLAN.md calibration notes.
	MinReserveUSD: 2500,
	MaxReserveUSD: 500000,
	MinFeePct:     0.25,
	MinFeeTVLDay:  5.0, // ~5%/day pace, between casual (~4.8) and turnover (~7.2) bars
	MinTxH1:       30,
	MinBuyersH1:   12,
	MinFdvUSD:     20000,
	MaxFdvUSD:     50_000_000,
}

// Mature is the second mode: pools PAST the launch window that are still
// printing outsized fees on real liquidity. It exists because Fresh and
// GeckoTerminal's new_pools feed are structurally blind to them — a pool
// scrolls off new_pools within minutes, and Fresh.MaxAge rejects anything over
// 24h. The live 2026-07-14 sample made the gap concrete: 19 of 62 indexed v3
// pools cleared a 5%/day fee pace inside the reserve band, and every one was
// 66-144h old (DATABEAR/WETH: $65k TVL, $1.44M 24h volume, 1% tier = 22%/day,
// roughly 8000% APR). Fed by FetchMaturePools (Uniswap's gateway), not
// FetchNewPools.
//
// FIRST-PASS values like Fresh's — expect churn once the journals land.
var Mature = ModeParams{
	Mode: "rh-mature",

	// Starts exactly where Fresh ends, so the two modes partition the age axis
	// and no pool can signal twice. No ceiling: a pool that has printed fees
	// for a week is MORE proven, not less — the fee-pace gate is what expires a
	// stale pool, and it does so on evidence rather than on a clock.
	MinAge: 24 * time.Hour,
	MaxAge: 0,

	// 12500 tracks the floor of what Uniswap's gateway actually indexes (~$12.6k
	// on the live sample) — below it we would gate on pools the discovery source
	// cannot see anyway. It is also 5x Fresh's floor on purpose: Fresh accepts
	// thin books because it is paid for launch-window volatility, while this
	// mode holds for days and needs an exit.
	MinReserveUSD: 12500,
	MaxReserveUSD: 500000,
	MinFeePct:     0.25,

	// 8%/day (~2900% APR) against Fresh's 5%. A mature pool competes on
	// SUSTAINED yield and has a full 24h of history to prove it, so the bar
	// should be higher than the one a minutes-old pool clears on extrapolation.
	// Sample check: 19/62 pools cleared 5%, only 5 cleared 8% — a shortlist,
	// which is what the single-position cap wants.
	MinFeeTVLDay: 8.0,
	FeePaceH24:   true,

	// Higher flow floors than Fresh (30/12): these pools have hours of history,
	// so a quiet hour here is real evidence of decay rather than a cold start.
	MinTxH1:     60,
	MinBuyersH1: 20,

	MinFdvUSD: 20000,
	MaxFdvUSD: 50_000_000,
}

// Ladder is the weth_ladder mode: pools worth parking a one-sided WETH bid
// wall under. Unlike Fresh and Mature — which buy the token and are therefore
// betting on it — a ladder holds only WETH until the market trades down into
// a rung, so what it needs from a pool is CHURN, not yield.
//
// That inverts the usual threshold logic and is why this mode exists at all
// rather than reusing Mature. Mature demands 8%/day because it holds inventory
// and must out-earn the bleed; the bar has to be high or the position loses.
// A ladder has no bleed to out-earn, so a high bar just starves it: measured
// against a profitable Robinhood Chain ladder LP (23 pools, 2026-08-04),
// Mature's gates matched exactly ONE of the 23 pools it actually worked, and
// Fresh matched none. These values are read off that real pool set — see
// docs/ROBINHOOD_CHAIN_PLAN.md.
var Ladder = ModeParams{
	Mode: "rh-ladder",

	// WETH-quoted pools only. The rungs ARE WETH, so a USDG-quoted pool in this
	// batch would be sized off the WETH balance and minted in USDG — see
	// StockLadder, which is the same shape aimed at that universe.
	QuoteAsset: WETH,

	// The observed wallet entered as early as 9.3h after pool creation, but our
	// mature discovery source (Uniswap's gateway) indexes nothing younger than a
	// day, so anything below 24h is unreachable here no matter what this says.
	// Set to what the source can actually deliver rather than to a number that
	// would silently never bind. 21 of the 23 observed entries were over 24h.
	MinAge: 24 * time.Hour,
	MaxAge: 0, // a ladder does not care how old a pool is, only whether it trades

	// Observed entry reserves ran $11k–$8.25M, median $134k. The floor sits just
	// under the smallest ($11.3k). The ceiling is OURS, not theirs: fee share is
	// proportional to our liquidity's share of the active tick, so on their
	// $8.25M pool a 0.05 WETH ladder earns rounding error. 2M keeps 22 of the 23.
	MinReserveUSD: 10000,
	MaxReserveUSD: 2_000_000,

	// 21 of 23 observed pools were the 1% tier, 2 were 0.3%. Below 0.3% a rung
	// has to be crossed far too often to pay for its own gas.
	MinFeePct: 0.3,

	// 1.5%/day against Mature's 8%. Observed fee pace across the 23 pools ran
	// 0.21%–27.8%/day, median 2.6% — this keeps 17 of 23 and drops only the
	// genuinely dead books. A ladder in a slow pool costs opportunity, not
	// capital, so the floor buys shortlist quality rather than safety.
	MinFeeTVLDay: 1.5,
	FeePaceH24:   true, // established pools have real 24h history; never extrapolate h1

	// Fresh's flow floors (30/12), not Mature's (60/20). A quiet hour is a real
	// risk to a position holding the token and a non-event to one holding WETH,
	// so this mode can afford the thinner books that Mature must refuse.
	MinTxH1:     30,
	MinBuyersH1: 10,

	MinFdvUSD: 20000,
	MaxFdvUSD: 50_000_000,
}

// PulseLadder is the weth_ladder shape aimed one age-band earlier than Ladder:
// WETH memecoin pools in their FIRST DAY, which no feed here could reach until
// the carried registry in pulse.go existed.
//
// Same wall, same executor, same exit rulebook. What differs is only which pools
// it looks at, and that is deliberate — rung width and count describe how far a
// token can fall, not how old it is, so the geometry keys on the quote asset
// (uni_ladder.js) and a pulse-discovered WETH pool gets the same 1200-tick rungs
// rh-ladder mints. If a soak shows a first-day pool wants a different wall, the
// knob to add is per-strategy geometry, NOT a second WETH constant.
//
// The two modes hand off at 24h with no overlap by construction: MaxAge here is
// Ladder's MinAge, which is itself set by the gateway's inability to index
// anything younger. Below that line this mode is the only one that can see the
// pool; above it, rh-ladder's feed is strictly richer.
//
// FIRST-PASS thresholds. Unlike Ladder's — which were read off a profitable
// LP's 23 real entries — nothing here is backed by an outcome yet, only by what
// the venue's young universe looks like (measured 2026-08-06: 33 WETH launches
// in the new_pools window, median reserve $4.8k, a handful at $21k-$27k with
// 79-153 h1 txns). Treat every number below as a starting point for the soak.
var PulseLadder = ModeParams{
	Mode: "rh-pulse-ladder",

	// WETH-quoted only, for the reason every ladder mode pins its quote: the
	// rungs ARE the quote asset and the deploy sizes against that same balance.
	QuoteAsset: WETH,

	// One hour is the cheapest available "this launch survived" filter. The
	// venue mints ~6 WETH pools a minute, nearly all of them $4.8k template dust
	// that stops trading within the hour; waiting one out costs a mode whose
	// thesis is a resting bid wall almost nothing, because a wall parked at
	// minute 3 of a launch sits under a price nobody has discovered yet.
	MinAge: 1 * time.Hour,
	MaxAge: 24 * time.Hour, // == Ladder.MinAge: the handoff, not a thesis edge

	// Ladder's floor. A wall in a $5k pool is not a smaller version of a wall in
	// a $50k pool — our rungs would BE the book, so every fill is adverse and
	// there is no external bid to exit into (measured 2026-08-06: young v4 pools
	// whose active liquidity had drained refused swaps in BOTH directions with
	// NotEnoughLiquidity). The ceiling is ours, not theirs: fee share is our
	// share of the active tick.
	MinReserveUSD: 10000,
	MaxReserveUSD: 2_000_000,

	// 0.25%, not Ladder's 0.3%. The venue's v4 launch template mints at the
	// 0.25% tier — 20 of the 33 pools in the measured window — so a 0.3% floor
	// would silently exclude most of this mode's universe on a rounding edge.
	MinFeePct: 0.25,

	// h1 EXTRAPOLATION here, unlike both established ladder modes, because a
	// six-hour-old pool has no 24h history: GT's h24 volume for it is LIFETIME
	// volume, so a realized pace would understate a pool that only started
	// trading an hour ago. The bar is correspondingly higher than Ladder's
	// realized 1.5% — an extrapolated rate reads high by construction, and 4%
	// keeps the comparison honest rather than pretending the two measure the
	// same thing.
	MinFeeTVLDay: 4.0,
	FeePaceH24:   false,

	// Ladder's flow floors. A quiet hour is a non-event for a wall holding WETH,
	// so these exist to drop dead books, not to rank live ones.
	MinTxH1:     30,
	MinBuyersH1: 10,

	MinFdvUSD: 20000,
	MaxFdvUSD: 50_000_000,
}

// StockLadder is the usdg_ladder mode: the SAME one-sided bid-wall shape as
// Ladder, pointed at the venue's other universe — the tokenized equities
// (nvda, gme, spacex …), which quote in USDG rather than WETH.
//
// It is a separate mode rather than a quote-widened Ladder because the two
// universes are nothing alike on the axis that sets the thresholds. A
// memecoin ladder is paid by violence: 1%-tier pools, wide rungs, a 1.5%/day
// churn floor. A tokenized equity trades a real book — deep, low-volatility —
// so it clears a fraction of that pace and would be rejected wholesale by
// Ladder's bar. Measured 2026-08-04 on the five live USDG equity pools: fee
// pace 0.23%–1.86%/day, TVL $173k–$712k, and only gme/USDG 1% cleared 1.5%/day.
//
// The equity universe spans all three fee tiers, and an underlying often lists
// at two or three of them at once — of the 12 USDG pools this mode has minted
// into, 3 were 0.05%, 6 were 0.3%, 3 were 1%. So MinFeePct below is a floor
// that admits every tier, not a description of the book, and rung geometry
// quantizes per tier (see uni_ladder.js). It also means one underlying can
// occupy several position slots at once; there is no per-token cap yet.
//
// The trade this mode makes is explicit: far less yield per rung, in exchange
// for a bid wall that is far less likely to be run over. A ladder's real risk
// is a collapse that fills every rung and leaves us holding the token — the
// failure mode that killed balanced_tight — and a tokenized equity is the
// least collapse-prone base asset on the chain.
var StockLadder = ModeParams{
	Mode: "rh-usdg-ladder",

	// USDG-quoted only, for the same reason Ladder is WETH-only: the rungs and
	// the sizing must be denominated in one asset. USDG is 6 decimals, so the
	// deploy path sizes it with the dollar-unit SizeParams (config.RobinhoodSizeUSDG)
	// and the executor parses the amount at the quote's own decimals.
	QuoteAsset: USDG,

	// Same discovery source as Ladder (the gateway indexes nothing younger than
	// a day), and the same indifference to age: an equity pool does not decay
	// out of thesis, its book either trades or it doesn't.
	MinAge: 24 * time.Hour,
	MaxAge: 0,

	// The observed pools ran $173k–$712k. The ceiling sits well over the
	// largest and binds harder than Ladder's on purpose: our fee share is our
	// share of the active tick, and these books are 5-50x deeper than a
	// memecoin's, so a rung in a $5M equity pool earns rounding error.
	//
	// The floor was $50k until a census of the venue's whole USDG book
	// (2026-08-05: the gateway returned 90 v3 pools against a page cap of 100,
	// so that census is the complete v3 universe, not one page of it) showed
	// what it cost. Of 26 USDG/token pools, $50k admitted 19 and cut SEVEN that
	// were already past MinAge: USO $47.9k, BNKR $46.3k, CASHCAT $44.8k,
	// DELL $43.8k, GOOGL $42.7k, INTC $41.8k, MSFT $35.1k. Every one sits
	// within 30% of the old floor — the number was not separating deep books
	// from thin ones, it was clipping a cluster. $20k restores all 26 (nothing
	// in the census falls between $20k and $35k, so this is not a slippery
	// slope toward dust) and leaves the pace and flow gates below to drop dead
	// books, which is their job and not the floor's.
	MinReserveUSD: 20_000,
	MaxReserveUSD: 5_000_000,

	// 0.05% — the tier the deepest equity pools actually use (nvda/USDG did
	// $3.42M of 24h volume there). Ladder's 0.3% floor would leave only the
	// thin 1% pools, which is the opposite of this mode's thesis.
	MinFeePct: 0.05,

	// 0.2%/day against Ladder's 1.5%. That is ~73%/yr on idle USDG with no
	// token exposure, and it keeps 4 of the 5 observed pools; the bar exists to
	// drop dead books, not to rank. FeePaceH24 for the same reason Ladder sets
	// it: these pools have real 24h history and h1 extrapolation would let one
	// busy hour fake a 24x rate.
	MinFeeTVLDay: 0.2,
	FeePaceH24:   true,

	// Lower flow floors than any other mode (Ladder is 30/10). Equities trade
	// on market hours: an h1 window sampled at 03:00 UTC is legitimately quiet
	// on a pool that did millions the previous session, and the 24h fee pace
	// above is the honest measure of whether the book is alive. These stay only
	// as a fully-dead-pool guard.
	MinTxH1:     10,
	MinBuyersH1: 3,

	// FDV gates OFF on purpose (both zero-disabled). A tokenized equity's FDV
	// is a function of the wrapper's token supply, not of a float anyone can
	// dump — it is neither a rug signal here nor comparable to a memecoin's, so
	// gating on it would reject or admit pools for reasons unrelated to risk.
	MinFdvUSD: 0,
	MaxFdvUSD: 0,
}

// Score saturation targets, degen-score analogs computed over the h1 window.
const (
	targetTurnoverH1 = 3.0     // h1 volume / reserve for a full trading sub-score
	targetBuyersH1   = 60.0    // h1 unique buyers for a full participation sub-score
	targetFeeDayPct  = 25.0    // projected daily fee/TVL % for a full fee sub-score
	targetReserveUSD = 30000.0 // reserve ($) for a full liquidity sub-score
)

// Screen applies the venue gates to one pool. A non-empty reason means the
// pool failed; the Candidate is only valid when reason == "". now comes from
// the caller — clock reads stay at the edges, matching the repo convention.
func Screen(p Pool, mp ModeParams, now time.Time) (*Candidate, string) {
	// Quote side must be a whitelisted quote asset (WETH, USDG, or v4 native
	// ETH) — the venue analog of the SOL-side requirement. orientQuote also
	// repairs orientation: sources put the quote asset base-side for USDG
	// pools, and rejecting on the raw quote field would drop that universe.
	p, ok := orientQuote(p)
	if !ok {
		return nil, fmt.Sprintf("quote not WETH/USDG/ETH (%s/%s)", p.BaseSymbol, p.QuoteSymbol)
	}
	// A mode pinned to one quote asset takes only that asset's pools — the
	// ladder modes are, because their rungs and their sizing are denominated in
	// it (see ModeParams.QuoteAsset).
	if mp.QuoteAsset != "" && !strings.EqualFold(p.QuoteAddress, mp.QuoteAsset) {
		return nil, fmt.Sprintf("quote-asset %s not this mode's", p.QuoteSymbol)
	}
	// Both sides a quote asset (WETH/USDG, ETH/USDG …) means there is no token
	// here — orientQuote picks a side by address order, so such a pool lands in
	// whichever mode the arbitrary "base" happens to suit and never leaves it.
	// That is how rh-usdg-ladder deployed a USDG wall under WETH on 2026-08-04:
	// WETH sorts below USDG, so the gateway's token0 was WETH, the mode's USDG
	// quote pin matched, and every remaining gate (deep book, 0.3% tier, real
	// 24h volume) passed easily. The shape was sound and the thesis was not —
	// a fill leaves the wallet long ETH, and no security/holder gate here says
	// anything meaningful about a quote asset.
	if quoteAssets[strings.ToLower(p.BaseAddress)] {
		return nil, fmt.Sprintf("quote-asset base %s/%s (no token side)", p.BaseSymbol, p.QuoteSymbol)
	}

	// v4-only hard gates. A hook can block or skim withdrawals (its behavior
	// lives in the 14 permission bits of the hook address — the Cork exploit
	// class), and a dynamic fee invalidates the fee-pace math below — both
	// reject outright. Costs almost nothing: 79/80 top v4 pools were hookless
	// on the 2026-07-14 sample.
	if p.Hook != "" {
		return nil, fmt.Sprintf("v4 hooked pool (%s)", p.Hook)
	}
	if p.DynamicFee {
		return nil, "v4 dynamic fee"
	}

	// Distinct reason prefixes on purpose: the cycle tally collapses reasons
	// to their prefix, and "too fresh to trust" vs "past the thesis window"
	// need separate counts to diagnose coverage (see the 2026-07-13 smoke
	// runs where 57/57 landed in one opaque "age" bucket).
	age := now.Sub(p.CreatedAt)
	if age < mp.MinAge {
		return nil, fmt.Sprintf("too-young %dm < %dm", int(age.Minutes()), int(mp.MinAge.Minutes()))
	}
	if mp.MaxAge > 0 && age > mp.MaxAge {
		return nil, fmt.Sprintf("too-old %.1fh > %.1fh", age.Hours(), mp.MaxAge.Hours())
	}

	if p.ReserveUSD < mp.MinReserveUSD {
		return nil, fmt.Sprintf("reserve $%.0f < $%.0f", p.ReserveUSD, mp.MinReserveUSD)
	}
	if mp.MaxReserveUSD > 0 && p.ReserveUSD > mp.MaxReserveUSD {
		return nil, fmt.Sprintf("reserve $%.0f > $%.0f cap", p.ReserveUSD, mp.MaxReserveUSD)
	}
	if p.FeePct < mp.MinFeePct {
		return nil, fmt.Sprintf("fee tier %.2f%% < %.2f%%", p.FeePct, mp.MinFeePct)
	}

	// Daily fee/TVL. Neither source exposes a fee field, but v3 fees are
	// deterministic (volume x tier), so this is exact for the window it reads.
	// Fresh extrapolates the h1 window (it has no more history); FeePaceH24
	// modes read the realized 24h volume instead — see the field's comment.
	feeTVLDay := 0.0
	if p.ReserveUSD > 0 {
		dayVolume := p.VolumeH1USD * 24
		if mp.FeePaceH24 {
			dayVolume = p.VolumeH24USD
		}
		feeTVLDay = (dayVolume * p.FeePct / 100) / p.ReserveUSD * 100
	}
	if feeTVLDay < mp.MinFeeTVLDay {
		return nil, fmt.Sprintf("fee/TVL pace %.1f%%/d < %.1f%%/d", feeTVLDay, mp.MinFeeTVLDay)
	}

	txH1 := p.TxH1.Buys + p.TxH1.Sells
	if txH1 < mp.MinTxH1 {
		return nil, fmt.Sprintf("txns %d < %d", txH1, mp.MinTxH1)
	}
	if p.TxH1.Buyers < mp.MinBuyersH1 {
		return nil, fmt.Sprintf("buyers %d < %d", p.TxH1.Buyers, mp.MinBuyersH1)
	}

	// Honeypot heuristic, pre-GMGN: real two-sided flow must include sells.
	// Many buys and literally zero sells over an hour is the classic
	// cannot-sell shape; reject before spending safety-gate budget on it.
	if p.TxH1.Buys >= 10 && p.TxH1.Sells == 0 {
		return nil, fmt.Sprintf("no sells (%d buys, 0 sells h1)", p.TxH1.Buys)
	}

	if p.FdvUSD < mp.MinFdvUSD {
		return nil, fmt.Sprintf("fdv $%.0f < $%.0f", p.FdvUSD, mp.MinFdvUSD)
	}
	if mp.MaxFdvUSD > 0 && p.FdvUSD > mp.MaxFdvUSD {
		return nil, fmt.Sprintf("fdv $%.0f > $%.0f cap", p.FdvUSD, mp.MaxFdvUSD)
	}

	// Momentum gates on GeckoTerminal's own windows — same thresholds as the
	// Solana venue's DexScreener gate (meteora.MomentumReject), no extra HTTP.
	if p.ChangeM5Pct <= -5 {
		return nil, fmt.Sprintf("5m %.1f%% <= -5%% (dumping)", p.ChangeM5Pct)
	}
	if p.ChangeH1Pct <= -15 {
		return nil, fmt.Sprintf("1h %.1f%% <= -15%% (dumping)", p.ChangeH1Pct)
	}
	if p.ChangeH6Pct <= -12 {
		return nil, fmt.Sprintf("6h %.1f%% <= -12%% (downtrend)", p.ChangeH6Pct)
	}
	if p.ChangeH24Pct <= -25 {
		return nil, fmt.Sprintf("24h %.1f%% <= -25%% (downtrend)", p.ChangeH24Pct)
	}

	protocol := p.Protocol
	if protocol == "" {
		protocol = "v3" // pre-v4 callers (and tests) never set the field
	}
	return &Candidate{
		Chain:        Chain,
		Mode:         mp.Mode,
		Pool:         p.Address,
		Dex:          "uniswap-" + protocol,
		Protocol:     protocol,
		Name:         p.Name,
		CreatedAt:    p.CreatedAt.UTC().Format(time.RFC3339),
		AgeMin:       age.Minutes(),
		BaseAddress:  p.BaseAddress,
		BaseSymbol:   p.BaseSymbol,
		BaseDecimals: p.BaseDecimals,
		QuoteAddress: p.QuoteAddress,
		QuoteSymbol:  p.QuoteSymbol,
		FeePct:       p.FeePct,
		ReserveUSD:   p.ReserveUSD,
		FdvUSD:       p.FdvUSD,
		McapUSD:      p.McapUSD,
		VolumeH1USD:  p.VolumeH1USD,
		VolumeH24USD: p.VolumeH24USD,
		FeeTVLDayPct: feeTVLDay,
		TxH1:         txH1,
		BuyersH1:     p.TxH1.Buyers,
		SellersH1:    p.TxH1.Sellers,
		ChangeM5Pct:  p.ChangeM5Pct,
		ChangeH1Pct:  p.ChangeH1Pct,
		Score:        score(p, feeTVLDay),
	}, ""
}

// score is the venue's 0..100 efficiency score: geometric mean of four
// sub-scores (turnover, participation, fee pace, liquidity), mirroring the
// Solana degen score's balance-enforcing shape — any zero sub-score zeroes
// the whole score.
func score(p Pool, feeTVLDay float64) float64 {
	if p.ReserveUSD <= 0 {
		return 0
	}
	sTurnover := clamp01((p.VolumeH1USD / p.ReserveUSD) / targetTurnoverH1)
	sBuyers := clamp01(float64(p.TxH1.Buyers) / targetBuyersH1)
	sFees := clamp01(feeTVLDay / targetFeeDayPct)
	sLiq := clamp01(math.Log10(p.ReserveUSD) / math.Log10(targetReserveUSD))
	return math.Pow(sTurnover*sBuyers*sFees*sLiq, 0.25) * 100
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
