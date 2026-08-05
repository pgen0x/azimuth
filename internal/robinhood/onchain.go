package robinhood

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/big"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Candles built from the chain itself, as the entry-timing gate's fallback when
// GeckoTerminal will not serve them.
//
// Why this exists, measured 2026-08-05: GT's public tier is ~10 requests/minute
// per IP — not the ~30 this package first assumed — and three consumers share
// the box's IP (this daemon's discovery enrich, this gate's OHLCV reads, and
// uni_monitor.py's exit rules). The daemon logged 82 `geckoterminal status 429`
// in six hours and roughly 23% of cycles discovered nothing. Spacing, cooldown
// and caching (gtlimit.go) cut the request count; they cannot manufacture a
// candle when the budget is already spent, and a refused OHLCV read makes the
// gate fail open — which is the safe direction, but it means the downtrend veto
// silently stops existing exactly when the venue is busiest.
//
// Robinhood Chain's public RPC has a far larger budget, and eth_getLogs here
// takes a wide range in one request (measured: 900_000 blocks of one v3 pool's
// Swap topic returned 8316 logs in 3.5s). A pool's whole price history is in
// its Swap logs, so the fallback derives the same 15-minute series locally.
//
// "Larger", not "unlimited" — do not read the paragraph above as a licence.
// Measured while building this: the node 429s on back-to-back heavy log scans,
// and it caps a single query at 10000 results. Both are handled by asking for
// one narrower window (see onchainRetryBlocks) rather than by retrying harder,
// because the failure mode of retrying harder is losing the RPC too and having
// no source at all.
//
// It is a FALLBACK, not a replacement: GT stays the primary because it is one
// request against this venue's ~8000 logs, and its bucket edges are what
// uni_monitor.py's Python side sees. The chain path only runs when GT errors,
// 429s, or the gate refuses the request outright.

// defaultRPCURL is the chain's public keyless endpoint (eth_chainId = 0x1237 =
// 4663, verified live 2026-08-05). Keyless is the point: an indicator fallback
// that needed a provider account would be one more thing to expire.
const defaultRPCURL = "https://rpc.mainnet.chain.robinhood.com"

// rpcUserAgent is not decoration. This endpoint has been observed to refuse
// default agent strings, and Go's http.Client sends "Go-http-client/1.1" unless
// told otherwise — the same trap uni_monitor.py's USER_AGENT constant documents
// for GeckoTerminal, which 403s "Python-urllib/3.x". Every request below sets it.
const rpcUserAgent = "azimuth-robinhood/1.0"

// v4PoolManager is the singleton every v4 pool's events are emitted from. A v4
// "pool address" in this codebase is a 32-byte poolId (66 chars with 0x), not a
// contract — so a v4 log filter addresses the manager and puts the poolId in
// topic1, where v3 addresses the pool contract itself.
const v4PoolManager = "0x8366a39cc670b4001a1121b8f6a443a643e40951"

// Event topic0s, all three computed from their canonical signature with keccak256
// and then verified against live payloads on 2026-08-05 rather than trusted:
//
//   - v3SwapTopic0 is keccak("Swap(address,address,int256,int256,uint160,uint128,int24)").
//     It reproduces the independently known v3 value bit for bit, which is what
//     validates the signature-string convention used for the other two.
//   - v4SwapTopic0 is keccak("Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)").
//     Confirmed by pulling live logs for poolId 0xacea8920…521a (FRONG/WETH) off
//     the PoolManager: 3 topics (topic0, poolId, sender) and exactly 6 data words,
//     which is the non-indexed tail of that signature and nothing else. Word 4
//     decoded to tick 122314 and word 2 to sqrtPriceX96 35873989574806965919922432937786;
//     1.0001^122314 = 205027 and (sqrt/2**96)**2 = 205027 agree, so the field
//     order is the decoder's, not a guess.
//   - v4InitTopic0 is keccak("Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)"),
//     confirmed on the same pool: topic2/topic3 came back as the zero address
//     (native ETH) and 0x6245e6…0c47, and data word 0 was 2500 = the pool's 0.25%
//     fee tier.
const (
	v3SwapTopic0 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
	v4SwapTopic0 = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
	v4InitTopic0 = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
)

// v3 pool getters, used to learn a pool's token ordering once.
const (
	selToken0 = "0x0dfe1681" // token0()
	selToken1 = "0xd21220a7" // token1()
)

const (
	// onchainCandleSec matches the GT request this falls back for
	// (ohlcv/minute?aggregate=15). The two series must bucket the same way or
	// the Go entry gate and uni_monitor.py's exit gate would disagree about what
	// a candle is.
	onchainCandleSec = 900

	// blocksPerSec turns a block height into a time, which on this node is the
	// ONLY way to get one: log entries come back with blockTimestamp "0x0", so
	// there is nothing in the payload to read. Fetching a block per candle is not
	// an option either — that is ~100 round-trips per pool.
	//
	// It is the measured block rate: block 27700417 stamped
	// 1785854137 and block 28600417 stamped 1785944402 — 900_000 blocks in
	// 90_265s, i.e. 0.10029 s/block. Rounding to a flat 10 blocks/second is
	// deliberate. Height→time is used ONLY to decide which 15-minute bucket a
	// swap lands in, and the mapping stays strictly monotonic in block height,
	// so the rounding can shift a bucket EDGE (~4 minutes at the far end of a
	// 25h window, a third of a candle) but can never reorder two trades or move
	// one across another. Reading one eth_getBlockByNumber per candle to remove
	// that shift would cost ~100 round-trips per pool to buy nothing the
	// indicators can see: RSI, ATR and Supertrend read the sequence, not the
	// clock.
	blocksPerSec = 10

	// onchainWindowBlocks is ~25h at the rate above, which is the same span
	// GeckoTerminal's default 100-candle page covers. Same length matters:
	// Supertrend's band depends on how much history it was fed, so a fallback
	// that quietly returned 40 candles would change the verdict rather than
	// preserve it.
	onchainWindowBlocks = 900_000

	// onchainMaxCandles bounds the bucket array against a bad head timestamp or
	// a clock jump; onchainWindowBlocks/(onchainCandleSec*blocksPerSec) = 100,
	// so anything past this is arithmetic gone wrong, not history.
	onchainMaxCandles = 120

	// onchainRetryBlocks is the ONE narrower retry a failed full window gets.
	//
	// The node refuses a too-wide query two different ways, both measured: a busy
	// v3 pool over 900k blocks answers "logs matched by query exceeds limit of
	// 10000" (a RESULT cap, not a range cap), and a busy v4 poolId answers
	// "log query timed out" because the v4 filter addresses the shared
	// PoolManager, where every v4 pool's logs live. Both mean the same thing:
	// narrow the window.
	//
	// 300k blocks is ~8.3h ~ 33 candles, which still clears minCandles (30). That
	// is exactly why there is no third attempt: halving again drops the series
	// below the floor, and a too-short series is not a weaker answer, it is a
	// "data unavailable" that fails open anyway. Better to spend one request
	// learning that than three.
	//
	// This policy is shared with uni_monitor.py's exit-side builder ON PURPOSE.
	// Entry and exit are two halves of one rule; if the two sides built candles
	// over different windows the venue would enter on one shape and exit on
	// another, with real funds in between.
	onchainRetryBlocks = 300_000

	// onchainRetryPause spaces the retry. The RPC is far more generous than
	// GeckoTerminal but it is NOT unmetered — back-to-back heavy log scans earn
	// an HTTP 429 here (observed while developing this file). A retry that fires
	// instantly is how a wide-window failure becomes a rate-limit failure.
	onchainRetryPause = 2 * time.Second
)

// onchainClient gets its own timeout, separate from ohlcvClient's 15s. These
// requests are a different shape: a 900k-block log scan is a server-side index
// walk measured at 1.8-5.0s and occasionally a halving retry on top, where a GT
// page either answers fast or is being refused.
var onchainClient = &http.Client{Timeout: 30 * time.Second}

var (
	onchainMu      sync.RWMutex
	onchainRPCURL  = defaultRPCURL
	onchainFellOn  = true
	onchainSources = map[string]bool{} // pool -> its cached candles came from the chain
)

// SetOnchainFallback installs the RPC endpoint and the enable toggle. Called
// once from config.Load; the defaults above are what a caller that never calls
// it gets, so tests and any future embedder still have a working fallback.
// An empty url keeps the public default rather than disabling the endpoint —
// an unset variable must not silently mean "no RPC".
func SetOnchainFallback(url string, enabled bool) {
	onchainMu.Lock()
	defer onchainMu.Unlock()
	if url != "" {
		onchainRPCURL = url
	}
	onchainFellOn = enabled
}

func onchainEnabled() bool {
	onchainMu.RLock()
	defer onchainMu.RUnlock()
	return onchainFellOn
}

func rpcEndpoint() string {
	onchainMu.RLock()
	defer onchainMu.RUnlock()
	return onchainRPCURL
}

// markSource records which venue the pool's CURRENTLY cached candles came from,
// so a decision taken minutes later off the cache still names its source. The
// journal has to be able to say why a gate said what it said; "the chain, not
// GeckoTerminal" is part of that.
func markSource(pool string, onchain bool) {
	onchainMu.Lock()
	if onchain {
		onchainSources[strings.ToLower(pool)] = true
	} else {
		delete(onchainSources, strings.ToLower(pool))
	}
	onchainMu.Unlock()
}

// candleSource returns a short tag for the pool's cached candle provenance,
// empty when they came from GeckoTerminal (the unremarkable case).
func candleSource(pool string) string {
	onchainMu.RLock()
	defer onchainMu.RUnlock()
	if onchainSources[strings.ToLower(pool)] {
		return "on-chain"
	}
	return ""
}

// --- JSON-RPC ------------------------------------------------------------

type rpcLog struct {
	Address     string   `json:"address"`
	Topics      []string `json:"topics"`
	Data        string   `json:"data"`
	BlockNumber string   `json:"blockNumber"`
}

// rpcCall issues one JSON-RPC request and decodes "result" into out (nil to
// discard). A JSON-RPC error object is returned as a Go error verbatim — the
// halving retry below reads the node's own wording ("log query timed out")
// rather than guessing from a status code, which is always 200 here.
func rpcCall(method string, params []any, out any) error {
	body, err := json.Marshal(map[string]any{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  method,
		"params":  params,
	})
	if err != nil {
		return err
	}
	req, err := http.NewRequest(http.MethodPost, rpcEndpoint(), strings.NewReader(string(body)))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", rpcUserAgent)
	resp, err := onchainClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("rpc %s status %d", method, resp.StatusCode)
	}
	var env struct {
		Result json.RawMessage `json:"result"`
		Error  *struct {
			Code    int    `json:"code"`
			Message string `json:"message"`
		} `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&env); err != nil {
		return fmt.Errorf("rpc %s decode: %w", method, err)
	}
	if env.Error != nil {
		return fmt.Errorf("rpc %s: %s (code %d)", method, env.Error.Message, env.Error.Code)
	}
	if out == nil {
		return nil
	}
	if len(env.Result) == 0 {
		return fmt.Errorf("rpc %s returned no result", method)
	}
	return json.Unmarshal(env.Result, out)
}

func hexUint(n uint64) string { return "0x" + strconv.FormatUint(n, 16) }

func parseHexUint(s string) (uint64, error) {
	return strconv.ParseUint(strings.TrimPrefix(strings.TrimPrefix(s, "0x"), "0X"), 16, 64)
}

// rpcHead reads the head block's height AND timestamp in one call. One call is
// the whole point: every other block's time is derived from these two numbers
// and the measured spacing (see blocksPerSec).
func rpcHead() (block uint64, unix int64, err error) {
	var b struct {
		Number    string `json:"number"`
		Timestamp string `json:"timestamp"`
	}
	if err := rpcCall("eth_getBlockByNumber", []any{"latest", false}, &b); err != nil {
		return 0, 0, err
	}
	n, err := parseHexUint(b.Number)
	if err != nil {
		return 0, 0, fmt.Errorf("head block number %q: %w", b.Number, err)
	}
	ts, err := parseHexUint(b.Timestamp)
	if err != nil {
		return 0, 0, fmt.Errorf("head block timestamp %q: %w", b.Timestamp, err)
	}
	return n, int64(ts), nil
}

// rpcLogs fetches one topic-filtered log range. Single shot: the
// window-narrowing policy lives in onchainCandles, where it is one decision
// about how much history to ask for rather than a recursion that can fan one
// candidate out into a dozen requests against a node that rate-limits.
func rpcLogs(address string, topics []any, from, to uint64) ([]rpcLog, error) {
	var out []rpcLog
	err := rpcCall("eth_getLogs", []any{map[string]any{
		"address":   address,
		"fromBlock": hexUint(from),
		"toBlock":   hexUint(to),
		"topics":    topics,
	}}, &out)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// --- pool identity -------------------------------------------------------

// poolRef is everything the candle builder needs about a pool that the pool
// address alone does not carry.
//
// invert is the field that matters, and it is the one thing a future reader
// will doubt, so: a Uniswap swap log carries sqrtPriceX96, and
// price = (sqrtPriceX96 / 2**96)**2 is the price of token0 denominated in
// token1. TOKEN DECIMALS DO NOT MATTER HERE. Decimals contribute a constant
// multiplicative factor, and RSI, ATR and Supertrend are all scale-invariant:
// RSI is a ratio of averaged differences, ATR scales with the series, and the
// Supertrend band is ATR-scaled around the same series — a constant factor
// cancels out of every verdict. That is why this file never looks up a decimals
// field, and why the 6-vs-18-decimal trap that governs uni_executor.js sizing
// is simply not a trap here.
//
// ORIENTATION, on the other hand, decides the answer. An inverted series turns
// a downtrend into an uptrend, and the entry gate would read a token in free
// fall as a confirmed bullish break. Both v3 and v4 sort currency0 < currency1
// by ADDRESS BYTES, so which side is token0 is not a choice the pool made — it
// is a property of the two addresses. We want the base token priced in the
// quote:
//
//	token0 == base  -> (sqrt/2**96)**2 is already quote-per-base -> no invert
//	token0 == quote -> it is base-per-quote                      -> invert
//
// Hence the builder needs the base and quote ADDRESSES, not just the pool id,
// and resolvePool goes and gets them. Verified on the live FRONG/WETH v4 pool,
// whose currency0 is the zero address (native ETH — the quote), so its raw price
// reads 205027 "FRONG per ETH" and must be inverted to 4.9e-6 ETH per FRONG
// before any indicator touches it.
type poolRef struct {
	pool   string
	v4     bool
	token0 string
	token1 string
	invert bool
}

var (
	refMu    sync.Mutex
	refCache = map[string]poolRef{}
)

// resolvePool learns a pool's token ordering, cached for the life of the
// process. The facts are immutable — a pool's currencies cannot change — so
// there is no TTL and no staleness to reason about.
func resolvePool(pool string) (poolRef, error) {
	key := strings.ToLower(pool)
	refMu.Lock()
	r, ok := refCache[key]
	refMu.Unlock()
	if ok {
		return r, nil
	}

	// 66 chars = 32-byte poolId = v4; 42 = a v3 pool contract. This is the same
	// length test discover.go uses to tell the two apart.
	r = poolRef{pool: key, v4: len(key) == 66}
	var err error
	if r.v4 {
		r.token0, r.token1, err = v4Currencies(key)
	} else {
		r.token0, r.token1, err = v3Tokens(key)
	}
	if err != nil {
		return poolRef{}, err
	}

	q0, q1 := quoteAssets[r.token0], quoteAssets[r.token1]
	switch {
	case q0 && !q1:
		r.invert = true
	case q1 && !q0:
		r.invert = false
	default:
		// Both sides quote assets (a WETH/USDG book) or neither: there is no
		// base to price. Refusing beats picking a side — an unoriented series is
		// exactly the failure this whole comment exists to prevent, and the
		// caller fails open on the error.
		return poolRef{}, fmt.Errorf("cannot orient %s: token0=%s token1=%s", key, r.token0, r.token1)
	}

	refMu.Lock()
	refCache[key] = r
	refMu.Unlock()
	return r, nil
}

// v3Tokens reads token0()/token1() off the pool contract.
func v3Tokens(pool string) (string, string, error) {
	t0, err := ethCallAddress(pool, selToken0)
	if err != nil {
		return "", "", err
	}
	t1, err := ethCallAddress(pool, selToken1)
	if err != nil {
		return "", "", err
	}
	return t0, t1, nil
}

func ethCallAddress(to, selector string) (string, error) {
	var out string
	if err := rpcCall("eth_call", []any{map[string]any{"to": to, "data": selector}, "latest"}, &out); err != nil {
		return "", err
	}
	return addressFromWord(out)
}

// v4Currencies recovers a v4 pool's currencies from its Initialize event, whose
// currency0/currency1 are INDEXED — so they arrive as topics and no ABI decode
// of the data blob is needed. A poolId is a hash of the pool key; there is
// nothing to call, and the PoolManager does not store the key. The scan spans
// the whole chain because a pool is initialized once, at an unknown height, and
// that is affordable precisely because it is topic-filtered down to one log:
// measured 0.3s from block 0 to latest.
func v4Currencies(poolID string) (string, string, error) {
	var logs []rpcLog
	// Spelled with block TAGS rather than rpcLogs' numeric range: this query
	// wants the whole chain and has no reason to halve — it is one indexed log,
	// not a volume scan.
	err := rpcCall("eth_getLogs", []any{map[string]any{
		"address":   v4PoolManager,
		"fromBlock": "0x0",
		"toBlock":   "latest",
		"topics":    []any{v4InitTopic0, poolID},
	}}, &logs)
	if err != nil {
		return "", "", err
	}
	return initCurrencies(logs)
}

func initCurrencies(logs []rpcLog) (string, string, error) {
	if len(logs) == 0 {
		return "", "", fmt.Errorf("no v4 Initialize log found")
	}
	l := logs[0]
	if len(l.Topics) < 4 {
		return "", "", fmt.Errorf("v4 Initialize log has %d topics, want 4", len(l.Topics))
	}
	c0, err := addressFromWord(l.Topics[2])
	if err != nil {
		return "", "", err
	}
	c1, err := addressFromWord(l.Topics[3])
	if err != nil {
		return "", "", err
	}
	return c0, c1, nil
}

// addressFromWord takes the low 20 bytes of a 32-byte ABI word, which is how
// both an indexed address topic and an address return value are encoded.
func addressFromWord(w string) (string, error) {
	h := strings.TrimPrefix(strings.ToLower(w), "0x")
	if len(h) != 64 {
		return "", fmt.Errorf("expected a 32-byte word, got %d hex chars", len(h))
	}
	return "0x" + h[24:], nil
}

// --- decoding ------------------------------------------------------------

// onchainSwap is one decoded Swap: the price the pool was left at, and the
// height it happened at. Price here is still RAW (token1 per token0);
// orientation is applied when bucketing, so that inverting also swaps high and
// low correctly (the max of 1/p is 1/min p, not 1/max p).
type onchainSwap struct {
	block uint64
	price float64
}

// two96 is 2**96, the Q64.96 scale. Only ever read.
var two96 = new(big.Float).SetMantExp(big.NewFloat(1), 96)

// decodeSwap pulls the price out of one Swap log, v3 or v4.
//
// The layouts differ in their non-indexed tail — v3 is
// (int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity,
// int24 tick) = 5 words, v4 is (int128, int128, uint160, uint128, int24, uint24)
// = 6 — but sqrtPriceX96 is the THIRD word in both, which is why one decoder
// serves both protocols. Nothing else in the payload is read: amounts and
// liquidity say nothing an OHLC series needs, and tick is a lossier spelling of
// the same price.
func decodeSwap(l rpcLog) (onchainSwap, error) {
	blk, err := parseHexUint(l.BlockNumber)
	if err != nil {
		return onchainSwap{}, fmt.Errorf("swap log block %q: %w", l.BlockNumber, err)
	}
	data := strings.TrimPrefix(strings.ToLower(l.Data), "0x")
	// Three words is the minimum that CONTAINS sqrtPriceX96. Anything shorter is
	// a truncated or foreign payload and is dropped rather than read past — a
	// short read here would produce a plausible-looking price from the wrong
	// bytes, which is worse than a missing candle.
	if len(data) < 3*64 {
		return onchainSwap{}, fmt.Errorf("swap log data too short: %d hex chars", len(data))
	}
	sq, ok := new(big.Int).SetString(data[2*64:3*64], 16)
	if !ok || sq.Sign() <= 0 {
		return onchainSwap{}, fmt.Errorf("swap log sqrtPriceX96 unreadable")
	}
	p := sqrtX96ToPrice(sq)
	if p <= 0 || math.IsInf(p, 0) || math.IsNaN(p) {
		return onchainSwap{}, fmt.Errorf("swap log price out of range")
	}
	return onchainSwap{block: blk, price: p}, nil
}

// sqrtX96ToPrice is the one line of math the whole file is about:
// price = (sqrtPriceX96 / 2**96)**2. Done in big.Float because sqrtPriceX96 is
// a uint160 — up to 2**160, far past float64's exact-integer range — and then
// squared in float64, where the result (at most ~3e38 for a legal tick range)
// comfortably fits.
func sqrtX96ToPrice(sq *big.Int) float64 {
	f := new(big.Float).SetInt(sq)
	f.Quo(f, two96)
	r, _ := f.Float64()
	return r * r
}

// --- bucketing -----------------------------------------------------------

// bucketCandles turns decoded swaps into a contiguous oldest-first 15-minute
// series, the same shape and ordering fetchOHLCV builds from GeckoTerminal.
//
// Two rules earn their keep:
//
//   - Logs are sorted by height first. eth_getLogs answers in order, but this
//     merges the halves of a split range (see rpcLogs), and a re-ordered series
//     would corrupt every indicator silently rather than loudly.
//   - EMPTY BUCKETS CARRY THE PREVIOUS CLOSE. A 15-minute window with no trades
//     is a flat candle, not a hole. Dropping it would compress the time axis and
//     desync this series from the Python side's, and — worse — ATR would read the
//     resumption of trading as one enormous true range instead of a quiet stretch
//     followed by a normal bar. A fee-dead pool is precisely the case the ladder
//     thesis cares about, so this is the common path, not the corner.
func bucketCandles(sw []onchainSwap, headBlock uint64, headUnix int64, invert bool) candles {
	if len(sw) == 0 {
		return candles{}
	}
	s := make([]onchainSwap, len(sw))
	copy(s, sw)
	sort.SliceStable(s, func(i, j int) bool { return s[i].block < s[j].block })

	bucketOf := func(b uint64) int64 {
		// Signed on purpose: a log can be newer than the head we read a moment
		// earlier, and uint64 subtraction would wrap that into a 58-billion-second
		// past.
		delta := int64(headBlock) - int64(b)
		return floorDiv(headUnix-delta/blocksPerSec, onchainCandleSec)
	}

	first, last := bucketOf(s[0].block), bucketOf(s[len(s)-1].block)
	if last < first {
		last = first
	}
	// Clamp a nonsense span (bad head timestamp, clock jump) to the newest
	// onchainMaxCandles rather than allocating whatever the arithmetic asked for.
	if last-first+1 > onchainMaxCandles {
		first = last - onchainMaxCandles + 1
	}
	n := int(last-first) + 1

	type bucket struct {
		h, l, c float64
		set     bool
	}
	bs := make([]bucket, n)
	for _, x := range s {
		idx := int(bucketOf(x.block) - first)
		if idx < 0 || idx >= n {
			continue // clamped off the front
		}
		p := x.price
		if invert {
			if p == 0 {
				continue
			}
			p = 1 / p
		}
		b := &bs[idx]
		if !b.set {
			b.h, b.l, b.set = p, p, true
		} else {
			if p > b.h {
				b.h = p
			}
			if p < b.l {
				b.l = p
			}
		}
		b.c = p
	}

	c := candles{
		highs:  make([]float64, n),
		lows:   make([]float64, n),
		closes: make([]float64, n),
	}
	var prev float64
	for i := range bs {
		if bs[i].set {
			prev = bs[i].c
			c.highs[i], c.lows[i], c.closes[i] = bs[i].h, bs[i].l, bs[i].c
			continue
		}
		c.highs[i], c.lows[i], c.closes[i] = prev, prev, prev
	}
	return c
}

// floorDiv floors toward negative infinity, so a bucket index stays monotonic
// if a timestamp ever lands before the epoch.
func floorDiv(a, b int64) int64 {
	q := a / b
	if (a%b != 0) && ((a < 0) != (b < 0)) {
		q--
	}
	return q
}

// --- the fallback itself -------------------------------------------------

// onchainCandles builds the pool's 15-minute series from its Swap logs. Returns
// the series and how many swaps it was built from (for the journal line).
func onchainCandles(pool string) (candles, int, error) {
	ref, err := resolvePool(pool)
	if err != nil {
		return candles{}, 0, err
	}
	head, headUnix, err := rpcHead()
	if err != nil {
		return candles{}, 0, err
	}
	address, topics := swapFilter(ref)

	// Two attempts, never three — see onchainRetryBlocks. The node refuses a
	// too-wide query either as a 10000-result cap or as a query timeout, and
	// there is no way to know in advance which side of that line a given pool
	// sits on: it depends on how busy the pool has been, which is exactly what
	// we are asking about.
	logs, from, err := swapLogsWindow(address, topics, head, onchainWindowBlocks)
	if err != nil {
		time.Sleep(onchainRetryPause)
		logs, from, err = swapLogsWindow(address, topics, head, onchainRetryBlocks)
		if err != nil {
			return candles{}, 0, err
		}
	}

	swaps := make([]onchainSwap, 0, len(logs))
	var bad int
	for _, l := range logs {
		s, err := decodeSwap(l)
		if err != nil {
			bad++
			continue
		}
		swaps = append(swaps, s)
	}
	if len(swaps) == 0 {
		return candles{}, 0, fmt.Errorf("no decodable swaps in %d blocks (%d logs, %d undecodable)", head-from, len(logs), bad)
	}
	return bucketCandles(swaps, head, headUnix, ref.invert), len(swaps), nil
}

// swapLogsWindow asks for the last span blocks of Swap logs, returning the logs
// and the height the window started at (the caller needs it for the journal).
func swapLogsWindow(address string, topics []any, head, span uint64) ([]rpcLog, uint64, error) {
	var from uint64
	if head > span {
		from = head - span
	}
	logs, err := rpcLogs(address, topics, from, head)
	if err != nil {
		return nil, from, err
	}
	return logs, from, nil
}

// swapFilter builds the log filter for the pool's protocol. v3 filters the
// pool contract by topic0 alone; v4 filters the shared PoolManager and narrows
// to this pool with the poolId in topic1.
func swapFilter(ref poolRef) (string, []any) {
	if ref.v4 {
		return v4PoolManager, []any{v4SwapTopic0, ref.pool}
	}
	return ref.pool, []any{v3SwapTopic0}
}

// onchainFallback is what fetchOHLCV calls when GeckoTerminal would not answer.
// gtErr is threaded through so a total failure reports BOTH causes: "GT 429 and
// the RPC also refused" is a different operational story from either alone.
func onchainFallback(pool string, gtErr error) (candles, error) {
	if !onchainEnabled() {
		return candles{}, gtErr
	}
	c, n, err := onchainCandles(pool)
	if err != nil {
		return candles{}, fmt.Errorf("geckoterminal: %v; on-chain fallback: %w", gtErr, err)
	}
	// One line per build, and a build happens at most once per gtOHLCVTTL per
	// pool because the result is cached exactly like the GT path — so this
	// cannot spam a cycle even when every candidate falls back.
	log.Printf("robinhood: %s — geckoterminal unavailable (%v); built %d 15m candles from %d on-chain swaps",
		shortPool(pool), gtErr, len(c.closes), n)
	return c, nil
}

func shortPool(p string) string {
	if len(p) > 10 {
		return p[:10]
	}
	return p
}
