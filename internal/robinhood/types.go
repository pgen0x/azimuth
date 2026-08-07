// Package robinhood discovers and screens Uniswap v3 and v4 pools on Robinhood
// Chain (chain ID 4663), mirroring the internal/meteora poll ▸ screen ▸ dedup ▸
// forward flow for the EVM venue. v4 pools are discovery/observe-only: the
// executor speaks v3, and the scanner excludes v4 candidates from deploy.
//
// Two modes with two discovery sources, because no single feed spans both
// theses (see docs/ROBINHOOD_CHAIN_PLAN.md):
//
//   - rh-fresh (discover.go) — newly-created pools, from GeckoTerminal's
//     new_pools launch feed. A pool scrolls off it within minutes.
//   - rh-mature (mature.go) — established pools still printing outsized
//     fee/TVL, from Uniswap's own interface GraphQL gateway, which indexes
//     nothing younger than about a day.
//   - rh-ladder (trending.go) — the UNION of that gateway feed and a cached
//     GeckoTerminal trending_pools page, because the gateway's leaderboard is
//     not the venue's whole universe (measured 2026-08-05).
//
// Both share every downstream gate: Screen, the safety fetches (safety.go) and
// the copycat guard (copycat.go).
package robinhood

import (
	"encoding/json"
	"strings"
	"time"
)

// Chain is the canonical venue slug used in dedup keys, signal payloads and
// GMGN OpenAPI calls (verified live 2026-07-13: chain=robinhood is the only
// accepted spelling; "rh" and "4663" return code 40000300).
const Chain = "robinhood"

// WETH is the canonical wrapped-ether address on Robinhood Chain — the quote
// side we require, playing the role SolMint plays on the Solana venue.
// Observed as the quote of 16/20 pools on a live new_pools page (2026-07-13).
const WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"

// USDG is Paxos' Global Dollar on Robinhood Chain (6 decimals — not 18;
// anything sizing capital in quote units must care). It is the venue's second
// quote asset and the dominant one on Uniswap v4: 47 of the top 80 v4 pools
// were USDG-sided on the 2026-07-14 gateway sample, versus 5 of 69 on v3.
// Address confirmed against Paxos' mainnet address table.
const USDG = "0x5fc5360d0400a0fd4f2af552add042d716f1d168"

// NativeETH is the zero address, which is how both data sources spell a v4
// native-ETH pool side (v4 pools ether directly, no WETH wrap). GeckoTerminal
// reports the zero address with symbol "WETH"; the Uniswap gateway reports a
// null address with symbol "ETH" (normalized to this constant in toPool).
const NativeETH = "0x0000000000000000000000000000000000000000"

// quoteAssets is the whitelist of accepted quote-side assets — the venue
// analog of the Solana SOL-side requirement, widened from WETH-only when v4
// discovery landed. Keys are lowercase addresses.
var quoteAssets = map[string]bool{
	WETH:      true,
	USDG:      true,
	NativeETH: true,
}

// isEtherQuote reports whether an address is one of the two spellings of ether
// on this venue: the ERC-20 wrapper (v3) and the zero address (v4 pools ether
// natively). They are one asset, and both data sources call it "WETH".
func isEtherQuote(addr string) bool {
	return strings.EqualFold(addr, WETH) || strings.EqualFold(addr, NativeETH)
}

// quotePinMatch reports whether a pool's quote side satisfies a mode's
// QuoteAsset pin. Exact match, EXCEPT that the two ether spellings satisfy each
// other — a pin on WETH means "this mode LPs against ether", not "against the
// ERC-20 wrapper specifically".
//
// This is not a widening of thesis; it is what the rest of the stack already
// assumed. sizeFor sizes native-ETH pools off the WETH balance because the v4
// executor unwraps on demand (ensureNativeFunds) and rewraps after a close, and
// the v4 ladder was DRY_RUN-verified against a native-ETH pool. Only the pin
// disagreed — and it decided everything, because the launch feed is almost
// entirely v4: of 70 pools carried by the pulse registry on 2026-08-07, 68 were
// native-ETH and 2 were wrapped. The mode could see 3% of its own universe.
func quotePinMatch(poolQuote, pin string) bool {
	if strings.EqualFold(poolQuote, pin) {
		return true
	}
	return isEtherQuote(poolQuote) && isEtherQuote(pin)
}

// orientQuote returns p with its quote side guaranteed to be a whitelisted
// quote asset, swapping base/quote when a source put the quote asset on the
// base side (GeckoTerminal lists USDG base-side in USDG/memecoin pools; the
// gateway orders token0/token1 by address). ok is false when neither side is
// a quote asset — such pools are out of thesis entirely.
func orientQuote(p Pool) (Pool, bool) {
	if quoteAssets[strings.ToLower(p.QuoteAddress)] {
		return p, true
	}
	if quoteAssets[strings.ToLower(p.BaseAddress)] {
		p.BaseAddress, p.QuoteAddress = p.QuoteAddress, p.BaseAddress
		p.BaseSymbol, p.QuoteSymbol = p.QuoteSymbol, p.BaseSymbol
		p.BaseDecimals, p.QuoteDecimals = p.QuoteDecimals, p.BaseDecimals
		return p, true
	}
	return p, false
}

// gtTxWindow is the buys/sells breakdown for one time window.
type gtTxWindow struct {
	Buys    int `json:"buys"`
	Sells   int `json:"sells"`
	Buyers  int `json:"buyers"`
	Sellers int `json:"sellers"`
}

// gtPoolAttrs mirrors the attribute block of one GeckoTerminal pool entry.
// Numeric fields arrive as JSON strings ("9016.95") and are parsed by the
// screen; missing/unparseable values become 0 (each gate documents whether
// zero passes or rejects).
type gtPoolAttrs struct {
	Address       string `json:"address"`
	Name          string `json:"name"`
	PoolCreatedAt string `json:"pool_created_at"` // RFC3339
	ReserveUSD    string `json:"reserve_in_usd"`
	FdvUSD        string `json:"fdv_usd"`
	MarketCapUSD  string `json:"market_cap_usd"`

	PriceChangePct struct {
		M5  string `json:"m5"`
		H1  string `json:"h1"`
		H6  string `json:"h6"`
		H24 string `json:"h24"`
	} `json:"price_change_percentage"`

	Transactions struct {
		M15 gtTxWindow `json:"m15"`
		H1  gtTxWindow `json:"h1"`
		H24 gtTxWindow `json:"h24"`
	} `json:"transactions"`

	VolumeUSD struct {
		M15 string `json:"m15"`
		H1  string `json:"h1"`
		H24 string `json:"h24"`
	} `json:"volume_usd"`
}

// gtRel is one JSON:API relationship stub ({"data":{"id":..,"type":..}}).
type gtRel struct {
	Data struct {
		ID   string `json:"id"`
		Type string `json:"type"`
	} `json:"data"`
}

// gtPool is one entry of the new_pools data array.
type gtPool struct {
	ID            string      `json:"id"`
	Attrs         gtPoolAttrs `json:"attributes"`
	Relationships struct {
		BaseToken  gtRel `json:"base_token"`
		QuoteToken gtRel `json:"quote_token"`
		Dex        gtRel `json:"dex"`
	} `json:"relationships"`
}

// gtToken is one included token resource (from ?include=base_token,quote_token).
type gtToken struct {
	ID    string `json:"id"`
	Type  string `json:"type"`
	Attrs struct {
		Address  string `json:"address"`
		Name     string `json:"name"`
		Symbol   string `json:"symbol"`
		Decimals int    `json:"decimals"`
	} `json:"attributes"`
}

// gtResponse is the top-level new_pools envelope. Included resources are kept
// raw and decoded per-type: the array mixes tokens and dexes.
type gtResponse struct {
	Data     []gtPool          `json:"data"`
	Included []json.RawMessage `json:"included"`
}

// Pool is a decoded, unit-normalized GeckoTerminal pool ready for screening.
type Pool struct {
	Address   string // v3 pool contract address, or the bytes32 poolId for v4
	Name      string // "CALLIE / WETH 0.3%"
	Dex       string // "uniswap-v3-robinhood"
	Protocol  string // "v3" or "v4", derived from the dex id
	CreatedAt time.Time

	// v4-only, from the Uniswap gateway (GeckoTerminal exposes neither).
	// Zero values on v3 pools, where no hook or dynamic fee can exist.
	Hook       string // hook contract address; "" = hookless
	DynamicFee bool

	BaseAddress   string
	BaseSymbol    string
	BaseDecimals  int
	QuoteAddress  string
	QuoteSymbol   string
	QuoteDecimals int

	FeePct     float64 // parsed from the trailing "0.3%" in Name; 0 = unknown
	ReserveUSD float64
	FdvUSD     float64
	McapUSD    float64

	// The m15 window is the venue's answer to Solana pulse's 5m window: proof
	// the book is trading NOW, not that it traded sometime in the last hour. A
	// ladder is the mode that needs it — a wall parked on a book whose flow
	// stopped 50 minutes ago earns nothing and re-pins on a timer. 15m rather
	// than pulse's 5m because this chain mints ~6 pools a minute and a 5m window
	// is mostly sampling noise; m15 is the tightest window that still resolves.
	VolumeM15USD float64
	TxM15        gtTxWindow

	VolumeH1USD  float64
	VolumeH24USD float64
	TxH1         gtTxWindow
	TxH24        gtTxWindow

	ChangeM5Pct  float64
	ChangeH1Pct  float64
	ChangeH6Pct  float64
	ChangeH24Pct float64
}

// Candidate is a screened, qualifying Robinhood Chain pool ready to emit.
// The payload shape is documented in docs/SIGNAL_SCHEMA.md under
// "robinhood_pool_discovery" — keep the two in sync.
type Candidate struct {
	Chain     string  `json:"chain"` // always "robinhood"
	Mode      string  `json:"mode"`
	Pool      string  `json:"pool"`     // v3 pool contract address, or bytes32 poolId for v4
	Dex       string  `json:"dex"`      // "uniswap-v3" or "uniswap-v4"
	Protocol  string  `json:"protocol"` // "v3" or "v4"
	Name      string  `json:"name"`
	CreatedAt string  `json:"created_at"` // RFC3339
	AgeMin    float64 `json:"age_minutes"`

	// Hook is the v4 hook address. Always empty today: hooked pools are
	// hard-rejected at screen time (a hook can block or skim withdrawals),
	// so the field only becomes non-empty if that gate is ever relaxed.
	Hook string `json:"hook,omitempty"`

	BaseAddress  string `json:"base_address"`
	BaseSymbol   string `json:"base_symbol"`
	BaseDecimals int    `json:"base_decimals"`
	QuoteAddress string `json:"quote_address"`
	QuoteSymbol  string `json:"quote_symbol"`

	FeePct       float64 `json:"fee_pct"`
	ReserveUSD   float64 `json:"reserve_usd"`
	FdvUSD       float64 `json:"fdv_usd"`
	McapUSD      float64 `json:"mcap_usd"`
	VolumeM15USD float64 `json:"volume_m15_usd"`
	TxM15        int     `json:"tx_m15"`
	FeeTVLM15Pct float64 `json:"fee_tvl_m15_pct"` // fee/TVL % over the LIVE 15m window (ladder flow proof)
	VolumeH1USD  float64 `json:"volume_h1_usd"`
	VolumeH24USD float64 `json:"volume_h24_usd"`
	FeeTVLDayPct float64 `json:"fee_tvl_day_pct"` // daily fee/TVL %: h1 pace extrapolated (rh-fresh) or realized 24h volume (rh-mature)
	TxH1         int     `json:"tx_h1"`
	BuyersH1     int     `json:"buyers_h1"`
	SellersH1    int     `json:"sellers_h1"`
	ChangeM5Pct  float64 `json:"change_m5_pct"`
	ChangeH1Pct  float64 `json:"change_h1_pct"`
	Score        float64 `json:"score"`

	// Blockscout enrichment (safety.go). Pointer + omitempty: absent means the
	// fetch failed (fail-open) — consumers treat missing as unknown, not zero.
	Holders *int `json:"holders,omitempty"`

	// GMGN security enrichment (safety.go). Absent = fetch failed or field
	// null/-1 (unknown) — fail-open. A POSITIVE honeypot/blacklist detection
	// rejects at screen time and never reaches the payload.
	GmgnSellTaxPct *float64 `json:"gmgn_sell_tax_pct,omitempty"`
	GmgnBuyTaxPct  *float64 `json:"gmgn_buy_tax_pct,omitempty"`
	GmgnOpenSource *bool    `json:"gmgn_open_source,omitempty"`
	GmgnLaunchpad  string   `json:"gmgn_launchpad,omitempty"`

	// GMGN holder-quality enrichment — same semantics as the Solana venue's
	// gmgn_* fields (see internal/meteora/gmgn.go).
	GmgnSmartWallets     *int     `json:"gmgn_smart_wallets,omitempty"`
	GmgnBundlerWallets   *int     `json:"gmgn_bundler_wallets,omitempty"`
	GmgnRatVolumePct     *float64 `json:"gmgn_rat_volume_pct,omitempty"`
	GmgnBundlerVolumePct *float64 `json:"gmgn_bundler_volume_pct,omitempty"`
	GmgnTop10Pct         *float64 `json:"gmgn_top10_pct,omitempty"`
	GmgnDevStatus        string   `json:"gmgn_dev_status,omitempty"`

	// Copycat (same-symbol collision) flag — set by EnrichCopycat when more than
	// one candidate in the SAME batch shares this ticker (the observed "2× CALLIE
	// in one cycle" quirk: meme launches spawn imposters under a hot ticker,
	// splitting liquidity/attention). Advisory like the Solana venue's is_pvp —
	// never rejects — but the autonomous picker demotes copycats below any clean
	// candidate. CopycatCount is the size of the colliding group (>= 2).
	IsCopycat    bool `json:"is_copycat,omitempty"`
	CopycatCount int  `json:"copycat_count,omitempty"`
}
