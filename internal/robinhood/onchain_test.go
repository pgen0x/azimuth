package robinhood

import (
	"math"
	"math/big"
	"strings"
	"testing"
)

// Every test here is offline by construction: decodeSwap and bucketCandles are
// pure, and the log payloads below are the real wire shapes (the v4 one is a
// verbatim live log from poolId 0xacea8920…521a, pulled 2026-08-05). Nothing in
// this file may touch the RPC — a unit test that needs a chain is a test that
// stops running the first time the chain is slow.

// word left-pads a hex string to one 32-byte ABI word.
func word(h string) string {
	h = strings.TrimPrefix(h, "0x")
	return strings.Repeat("0", 64-len(h)) + h
}

// sqrtWord is a sqrtPriceX96 whose price is exactly want: sqrt(want) * 2**96,
// built from the float so the test states the price it means rather than a
// magic constant.
func sqrtWord(want float64) string {
	// 2**96 as a float is exact; the product is rounded, which is fine — the
	// assertions below use a relative tolerance.
	v := math.Sqrt(want) * math.Pow(2, 96)
	return word(bigHex(v))
}

func bigHex(v float64) string {
	i, _ := big.NewFloat(v).Int(nil)
	return i.Text(16)
}

// v3Log builds a 5-word v3 Swap payload: amount0, amount1, sqrtPriceX96,
// liquidity, tick.
func v3Log(block string, price float64) rpcLog {
	data := word("1") + word("2") + sqrtWord(price) + word("3") + word("4")
	return rpcLog{
		Address:     "0x2e3d2bdc4a6e048baef175c04deb6e18d33662e5",
		Topics:      []string{v3SwapTopic0, word("aa"), word("bb")},
		Data:        "0x" + data,
		BlockNumber: block,
	}
}

// v4Log builds a 6-word v4 Swap payload: amount0, amount1, sqrtPriceX96,
// liquidity, tick, fee — one word longer than v3, same sqrtPriceX96 slot.
func v4Log(block string, price float64) rpcLog {
	data := word("1") + word("2") + sqrtWord(price) + word("3") + word("4") + word("5")
	return rpcLog{
		Address:     v4PoolManager,
		Topics:      []string{v4SwapTopic0, word("acea"), word("cc")},
		Data:        "0x" + data,
		BlockNumber: block,
	}
}

func TestDecodeSwapV3Layout(t *testing.T) {
	s, err := decodeSwap(v3Log("0x64", 1234.5))
	if err != nil {
		t.Fatalf("decodeSwap(v3): %v", err)
	}
	if s.block != 100 {
		t.Errorf("block = %d, want 100", s.block)
	}
	if math.Abs(s.price-1234.5)/1234.5 > 1e-9 {
		t.Errorf("price = %.9f, want 1234.5", s.price)
	}
}

func TestDecodeSwapV4Layout(t *testing.T) {
	// The 6-word v4 tail must decode to the SAME price as the 5-word v3 tail:
	// sqrtPriceX96 is the third word in both, which is the whole reason one
	// decoder serves both protocols.
	s3, err := decodeSwap(v3Log("0x64", 0.004))
	if err != nil {
		t.Fatalf("decodeSwap(v3): %v", err)
	}
	s4, err := decodeSwap(v4Log("0x64", 0.004))
	if err != nil {
		t.Fatalf("decodeSwap(v4): %v", err)
	}
	if s3.price != s4.price {
		t.Errorf("v3 price %.12g != v4 price %.12g — word offset differs between layouts", s3.price, s4.price)
	}
	if math.Abs(s4.price-0.004)/0.004 > 1e-9 {
		t.Errorf("v4 price = %.12g, want 0.004", s4.price)
	}
}

// TestDecodeSwapLiveV4Payload pins the decoder to a real log captured from the
// chain on 2026-08-05 (poolId 0xacea8920…521a, block 28500432). Its tick word is
// 122314, and 1.0001**122314 = 205027 — so if the decoder ever reads the wrong
// word, the price stops agreeing with the tick and this fails.
func TestDecodeSwapLiveV4Payload(t *testing.T) {
	l := rpcLog{
		Address: v4PoolManager,
		Topics: []string{
			v4SwapTopic0,
			"0xacea8920877840033f0275c37f9b61550b5326917e948bcf8339714d96f9521a",
			"0x0000000000000000000000008876789976decbfcbbbe364623c63652db8c0904",
		},
		Data: "0x" +
			"000000000000000000000000000000000000000000000000002951acf6872e6c" + // amount0
			"ffffffffffffffffffffffffffffffffffffffffffffff7e5e52d58b5fe80000" + // amount1 (negative int128)
			"00000000000000000000000000000000000001c4cb1cabd4670a071856ae8f3a" + // sqrtPriceX96
			"00000000000000000000000000000000000000000000176c2ab4475089cc2ed4" + // liquidity
			"000000000000000000000000000000000000000000000000000000000001ddca" + // tick = 122314
			"0000000000000000000000000000000000000000000000000000000000000b53", // fee
		BlockNumber: "0x1b2e1d0",
	}
	s, err := decodeSwap(l)
	if err != nil {
		t.Fatalf("decodeSwap(live v4): %v", err)
	}
	if s.block != 28500432 {
		t.Errorf("block = %d, want 28500432", s.block)
	}
	// Tolerance is 1e-3 relative, not 1e-6: a tick is the FLOOR of the log price,
	// so the two agree only to within one tick (~1e-4 here). That is still four
	// orders of magnitude tighter than reading any other word would land.
	fromTick := math.Pow(1.0001, 122314)
	if math.Abs(s.price-fromTick)/fromTick > 1e-3 {
		t.Errorf("price %.6f disagrees with the log's own tick (%.6f) — wrong data word", s.price, fromTick)
	}
}

func TestDecodeSwapMalformed(t *testing.T) {
	cases := []struct {
		name string
		l    rpcLog
	}{
		// Two words: sqrtPriceX96's slot does not exist. Reading past it would
		// invent a plausible price out of the wrong bytes.
		{"short data", rpcLog{Data: "0x" + word("1") + word("2"), BlockNumber: "0x1"}},
		{"empty data", rpcLog{Data: "0x", BlockNumber: "0x1"}},
		{"no data field", rpcLog{BlockNumber: "0x1"}},
		{"zero sqrtPrice", rpcLog{Data: "0x" + word("1") + word("2") + word("0") + word("3") + word("4"), BlockNumber: "0x1"}},
		{"bad block number", rpcLog{Data: "0x" + word("1") + word("2") + sqrtWord(5) + word("3") + word("4"), BlockNumber: "not-hex"}},
	}
	for _, tc := range cases {
		if _, err := decodeSwap(tc.l); err == nil {
			t.Errorf("%s: decodeSwap returned nil error, want a rejection", tc.name)
		}
	}
}

// head fixes a head block/timestamp so bucket boundaries are exact: at 10
// blocks/second a 15-minute candle is 9000 blocks.
const (
	testHeadBlock = 1_000_000
	testHeadUnix  = 1_785_943_800 // exactly divisible by 900, so the head sits on a bucket edge
)

// blockAt returns the block height that lands secondsAgo before the head.
func blockAt(secondsAgo int64) uint64 {
	return uint64(testHeadBlock - secondsAgo*blocksPerSec)
}

func TestBucketCandlesSingleSwap(t *testing.T) {
	c := bucketCandles([]onchainSwap{{block: blockAt(10), price: 42}}, testHeadBlock, testHeadUnix, false)
	if len(c.closes) != 1 {
		t.Fatalf("len = %d, want 1 candle", len(c.closes))
	}
	if c.highs[0] != 42 || c.lows[0] != 42 || c.closes[0] != 42 {
		t.Errorf("single swap candle = h%.0f l%.0f c%.0f, want 42/42/42", c.highs[0], c.lows[0], c.closes[0])
	}
}

func TestBucketCandlesOHLCWithinBucket(t *testing.T) {
	// Four swaps in one 15m window, deliberately not in price order.
	sw := []onchainSwap{
		{block: blockAt(800), price: 10},
		{block: blockAt(700), price: 15},
		{block: blockAt(600), price: 8},
		{block: blockAt(500), price: 12},
	}
	c := bucketCandles(sw, testHeadBlock, testHeadUnix, false)
	if len(c.closes) != 1 {
		t.Fatalf("len = %d, want 1 candle (all four swaps share a bucket)", len(c.closes))
	}
	if c.highs[0] != 15 || c.lows[0] != 8 || c.closes[0] != 12 {
		t.Errorf("h/l/c = %.0f/%.0f/%.0f, want 15/8/12", c.highs[0], c.lows[0], c.closes[0])
	}
}

func TestBucketCandlesEmptyBucketCarriesClose(t *testing.T) {
	// Two swaps ~45 minutes apart: three buckets, the middle one traded nothing.
	sw := []onchainSwap{
		{block: blockAt(2000), price: 100},
		{block: blockAt(200), price: 130},
	}
	c := bucketCandles(sw, testHeadBlock, testHeadUnix, false)
	if len(c.closes) != 3 {
		t.Fatalf("len = %d, want 3 contiguous candles", len(c.closes))
	}
	// The gap must be FLAT AT THE PREVIOUS CLOSE, not dropped and not zero: a
	// dropped bucket compresses the time axis, and a zero would hand ATR an
	// enormous fake true range.
	if c.highs[1] != 100 || c.lows[1] != 100 || c.closes[1] != 100 {
		t.Errorf("empty bucket = h%.0f l%.0f c%.0f, want a flat 100 carried from the previous close",
			c.highs[1], c.lows[1], c.closes[1])
	}
	if c.closes[0] != 100 || c.closes[2] != 130 {
		t.Errorf("closes = %v, want first 100 and last 130", c.closes)
	}
}

func TestBucketCandlesOutOfOrderBlocks(t *testing.T) {
	// eth_getLogs answers in order, but merging the halves of a split range can
	// interleave them. A re-ordered series corrupts every indicator silently.
	ordered := []onchainSwap{
		{block: blockAt(3000), price: 5},
		{block: blockAt(2000), price: 7},
		{block: blockAt(1000), price: 9},
		{block: blockAt(100), price: 11},
	}
	shuffled := []onchainSwap{ordered[2], ordered[0], ordered[3], ordered[1]}
	a := bucketCandles(ordered, testHeadBlock, testHeadUnix, false)
	b := bucketCandles(shuffled, testHeadBlock, testHeadUnix, false)
	if len(a.closes) != len(b.closes) {
		t.Fatalf("shuffled input produced %d candles, ordered produced %d", len(b.closes), len(a.closes))
	}
	for i := range a.closes {
		if a.closes[i] != b.closes[i] || a.highs[i] != b.highs[i] || a.lows[i] != b.lows[i] {
			t.Fatalf("candle %d differs between ordered and shuffled input: %v vs %v", i, a, b)
		}
	}
	if a.closes[len(a.closes)-1] != 11 {
		t.Errorf("last close = %.0f, want 11 (the newest swap)", a.closes[len(a.closes)-1])
	}
}

func TestBucketCandlesInvertedOrientation(t *testing.T) {
	// The case that matters: an inverted series turns a downtrend into an
	// uptrend. Raw prices RISE here, so the inverted series must FALL.
	sw := []onchainSwap{
		{block: blockAt(3000), price: 100},
		{block: blockAt(2000), price: 200},
		{block: blockAt(1000), price: 400},
	}
	up := bucketCandles(sw, testHeadBlock, testHeadUnix, false)
	down := bucketCandles(sw, testHeadBlock, testHeadUnix, true)
	if up.closes[0] >= up.closes[len(up.closes)-1] {
		t.Fatalf("uninverted series should rise, got %v", up.closes)
	}
	if down.closes[0] <= down.closes[len(down.closes)-1] {
		t.Errorf("inverted series should FALL (an inverted downtrend reads as a buy signal), got %v", down.closes)
	}
	for i := range up.closes {
		if math.Abs(down.closes[i]-1/up.closes[i]) > 1e-12 {
			t.Errorf("close[%d]: inverted %.12g != 1/%.12g", i, down.closes[i], up.closes[i])
		}
	}
}

func TestBucketCandlesInvertSwapsHighAndLow(t *testing.T) {
	// Inversion has to happen BEFORE min/max, because the max of 1/p is 1/min p.
	// Inverting the finished candle would put the high below the low.
	sw := []onchainSwap{
		{block: blockAt(800), price: 10},
		{block: blockAt(700), price: 20},
	}
	c := bucketCandles(sw, testHeadBlock, testHeadUnix, true)
	if len(c.closes) != 1 {
		t.Fatalf("len = %d, want 1", len(c.closes))
	}
	if c.highs[0] < c.lows[0] {
		t.Fatalf("inverted candle has high %.4f below low %.4f", c.highs[0], c.lows[0])
	}
	if math.Abs(c.highs[0]-0.1) > 1e-12 || math.Abs(c.lows[0]-0.05) > 1e-12 {
		t.Errorf("h/l = %.4f/%.4f, want 0.1/0.05 (1/10 and 1/20)", c.highs[0], c.lows[0])
	}
}

func TestBucketCandlesEmptyInput(t *testing.T) {
	if c := bucketCandles(nil, testHeadBlock, testHeadUnix, false); len(c.closes) != 0 {
		t.Errorf("no swaps should yield no candles, got %d", len(c.closes))
	}
}

func TestBucketCandlesSpanClamped(t *testing.T) {
	// A swap far older than the window (or a bad head timestamp) must not
	// allocate an unbounded array; the newest onchainMaxCandles survive.
	sw := []onchainSwap{
		{block: 1, price: 5},
		{block: blockAt(100), price: 9},
	}
	c := bucketCandles(sw, testHeadBlock, testHeadUnix, false)
	if len(c.closes) > onchainMaxCandles {
		t.Errorf("len = %d, want <= %d", len(c.closes), onchainMaxCandles)
	}
	if c.closes[len(c.closes)-1] != 9 {
		t.Errorf("last close = %.0f, want 9 (the newest swap must survive clamping)", c.closes[len(c.closes)-1])
	}
}

func TestBucketCandlesLogNewerThanHead(t *testing.T) {
	// A block can arrive between the head read and the log read. Unsigned
	// subtraction would wrap that into a 58-billion-second past.
	c := bucketCandles([]onchainSwap{
		{block: testHeadBlock + 50, price: 3},
		{block: blockAt(100), price: 4},
	}, testHeadBlock, testHeadUnix, false)
	if len(c.closes) == 0 || len(c.closes) > onchainMaxCandles {
		t.Fatalf("len = %d, want a small positive candle count", len(c.closes))
	}
}

func TestSwapFilter(t *testing.T) {
	v3 := poolRef{pool: "0x2e3d2bdc4a6e048baef175c04deb6e18d33662e5"}
	addr, topics := swapFilter(v3)
	if addr != v3.pool || len(topics) != 1 || topics[0] != v3SwapTopic0 {
		t.Errorf("v3 filter = %s %v, want the pool contract filtered by topic0 alone", addr, topics)
	}

	v4 := poolRef{pool: "0xacea8920877840033f0275c37f9b61550b5326917e948bcf8339714d96f9521a", v4: true}
	addr, topics = swapFilter(v4)
	// A v4 "pool address" is a poolId, not a contract — the filter must address
	// the shared PoolManager and narrow with topic1, or it would query nothing.
	if addr != v4PoolManager || len(topics) != 2 || topics[1] != v4.pool {
		t.Errorf("v4 filter = %s %v, want PoolManager + poolId in topic1", addr, topics)
	}
}

func TestAddressFromWord(t *testing.T) {
	got, err := addressFromWord("0x0000000000000000000000006245e67affa44a23077f0ea7f981a8dc743a0c47")
	if err != nil {
		t.Fatalf("addressFromWord: %v", err)
	}
	if got != "0x6245e67affa44a23077f0ea7f981a8dc743a0c47" {
		t.Errorf("got %s", got)
	}
	if _, err := addressFromWord("0xdeadbeef"); err == nil {
		t.Error("a short word should be rejected, not padded into a wrong address")
	}
}

// TestInitCurrenciesNativeETH covers the live shape that made orientation worth
// testing: v4's currency0 for an ETH-quoted pool is the ZERO address, which
// quoteAssets recognizes as NativeETH — so the pool inverts.
func TestInitCurrenciesNativeETH(t *testing.T) {
	c0, c1, err := initCurrencies([]rpcLog{{
		Topics: []string{
			v4InitTopic0,
			"0xacea8920877840033f0275c37f9b61550b5326917e948bcf8339714d96f9521a",
			word("0"),
			"0x0000000000000000000000006245e67affa44a23077f0ea7f981a8dc743a0c47",
		},
	}})
	if err != nil {
		t.Fatalf("initCurrencies: %v", err)
	}
	if c0 != NativeETH {
		t.Errorf("currency0 = %s, want the zero address (native ETH)", c0)
	}
	if !quoteAssets[c0] || quoteAssets[c1] {
		t.Errorf("expected currency0 to be the quote asset and currency1 not: %v/%v", quoteAssets[c0], quoteAssets[c1])
	}
	if _, _, err := initCurrencies(nil); err == nil {
		t.Error("no Initialize log should be an error, not a silent zero-address pair")
	}
	if _, _, err := initCurrencies([]rpcLog{{Topics: []string{v4InitTopic0}}}); err == nil {
		t.Error("a log with too few topics should be rejected")
	}
}

func TestFloorDiv(t *testing.T) {
	cases := [][3]int64{
		{1800, 900, 2},
		{1799, 900, 1},
		{0, 900, 0},
		{-1, 900, -1},
		{-900, 900, -1},
		{-901, 900, -2},
	}
	for _, c := range cases {
		if got := floorDiv(c[0], c[1]); got != c[2] {
			t.Errorf("floorDiv(%d, %d) = %d, want %d", c[0], c[1], got, c[2])
		}
	}
}
