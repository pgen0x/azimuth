// Ladder geometry shared by BOTH Robinhood Chain executors — uni_executor.js
// (Uniswap v3, NonfungiblePositionManager) and uni_v4_executor.js (Uniswap v4,
// PositionManager). The two executors otherwise duplicate their primitives on
// purpose (tick math, journals, quote resolution) because every protocol
// assumption differs; this file is the exception, and the reason is that the
// numbers here are not protocol-specific at all.
//
// A rung's width, count and size ramp are properties of the THESIS — how far a
// token can fall before the wall is worth re-pinning, and how much inventory we
// are willing to have converted on the way down. They are also read a second
// time by uni_monitor.py's `ladder stale` rule (LADDER_STALE_TICKS), which
// compares live spot drift against the rung width the mint actually used. Three
// copies of one number, two of them in files edited for unrelated reasons, is
// how a wall silently ends up re-pinning at a width it was never minted at. So:
// one definition, required by both executors.
//
// The same argument covers `weth_below`, the ONE-rung turnover shape at the
// bottom of this file: it is a ladder of one, laid by the same ladderBands(),
// and uni_monitor.py judges its drift against the width defined here.
//
// Everything here is pure — no chain access, no protocol types. The `q` argument
// is any quote descriptor carrying `{symbol, decimals}`, which both executors'
// quote objects satisfy (v3's resolveQuote() result and v4's QUOTES entry).

"use strict";

const { parseUnits, formatUnits } = require("viem");

// Rung count. Reverse-engineered 2026-08-04 from a profitable Robinhood Chain
// LP: N contiguous one-sided rungs stacked on the BID side, sized on a linear
// ramp so the rung nearest spot is smallest. See docs/ROBINHOOD_CHAIN_PLAN.md
// "weth_ladder" for the shape.
//
// Defaults are scaled DOWN from that reference, which ran both more rungs and
// wider ones: rung count is the knob that trades fee-capture resolution against
// per-rung dust, and our ticket is an order of magnitude smaller. The executors
// lower this further at runtime when the amount can't fund it — see
// ladderSizes().
const LADDER_RUNGS = parseInt(process.env.UNI_LADDER_RUNGS || "5", 10);

// Rung width, PER QUOTE ASSET. The WETH figure is the reference wallet's, read
// off a memecoin venue where a 12% move is a Tuesday. USDG pools are tokenized
// equities: they move 1-3% in a day, so a 1200-tick wall would sit entirely out
// of reach — five rungs covering a 45% crash is not a bid wall, it is a bet the
// stock halts.
//
// 2026-08-05: USDG widened 120 -> 240, because 120 was near the narrowest rung
// these pools can express. The stock universe is NOT one fee tier — a census of
// the 12 USDG pools this mode has actually minted into (position journal) spans
// all three, with several underlyings present at two or even three of them:
//
//   0.05% / spacing 10    3 pools   240 exact (24 spacings)
//   0.3%  / spacing 60    6 pools   240 exact (4 spacings)
//   1%    / spacing 200   3 pools   200  <-- quantized DOWN, see rungWidth
//
// So the widening bought depth in 9 of 12 pools and nothing in the other 3: at
// spacing 200 a 240-tick request rounds to a single spacing, and the minted
// rungs confirm it (every 1%-tier rung came out 200 ticks both before and after
// this change). Sizing the constant for the 60-spacing majority is deliberate —
// that is where most of the traded book is — but covered drop is therefore
// PER TIER, not per mode: ~2.4% a rung at spacing 10 and 60, ~2.0% at 200.
//
// What 120 cost at that majority tier: two spacings, and the deposit floor
// (UNI_LADDER_MIN_RUNG_USDG against a ~$7 commit) drops the wall to 3 rungs, so
// 3 x 120 covered 3.6% of downside — a wall that a market moving 1-3% a day
// steps over and never returns to. 240 covers 7.2% at 3 rungs, 12% at five.
//
// Widening is a trade, not a free win: rung 0's top edge is pinned adjacent to
// spot either way (see ladderBands), so a wider rung buys depth by HALVING
// liquidity density, and density is what pays on the small oscillations around
// spot that make up most of an equity session. The stronger lever is rung
// COUNT — sol_bidask, the Solana sibling this shape is ported from, reaches
// -70% with ~70 NARROW bins, not with wide ones. Count here is capped by
// deposit size, not by this constant.
const LADDER_RUNG_TICKS = {
  WETH: parseInt(process.env.UNI_LADDER_RUNG_TICKS || "1200", 10),
  USDG: parseInt(process.env.UNI_LADDER_RUNG_TICKS_USDG || "240", 10),
};

// Floor on the SMALLEST rung, per quote asset. A rung below this is dust: it
// earns fees that never repay the gas of minting and later burning it, and on
// exit it is the rung most likely to strand an unsellable bag. The observed
// wallet's smallest WETH rung was ~0.0115; ours is the old single-position
// floor. The USDG figure is lower in dollar terms because the risk it guards
// against is different — an equity rung will not strand (the book is real and
// deep), so $2 only has to beat the gas of its own mint-and-burn, which at this
// chain's ~0.05 gwei is cents.
//
// Consequence worth knowing: ladderSizes() drops rungs until the smallest
// clears this, so a ladder funded near ROBINHOOD_DEPLOY_FLOOR_USDG mints two or
// three real rungs instead of five dust ones. Five-rung stock ladders want
// roughly $30 of commit.
const LADDER_MIN_RUNG = {
  WETH: process.env.UNI_LADDER_MIN_RUNG_WETH || "0.003",
  USDG: process.env.UNI_LADDER_MIN_RUNG_USDG || "2",
};

// Native ETH is WETH for every purpose this file has: a v4 pool can quote in
// currency0 == address(0), and its rungs want the same width and floor as a
// wrapped-WETH pool's. Without these two lines a native-quoted ladder would
// still get the WETH numbers via the ?? fallbacks below — the right answer, but
// by accident, and an accident that stops being right the day a third quote
// asset is added.
LADDER_RUNG_TICKS.ETH = LADDER_RUNG_TICKS.WETH;
LADDER_MIN_RUNG.ETH = LADDER_MIN_RUNG.WETH;

// --- turnover: the SINGLE rung ---------------------------------------------
// `weth_below` is the same one-sided resting bid as a ladder rung, minted ONE
// at a time and re-pinned instead of stacked. It lives here rather than in the
// executors for the same reason the ladder numbers do: uni_monitor.py's
// `turnover re-center` drift rule (TURNOVER_STALE_TICKS) is judged against this
// width, so a copy per executor plus a copy in the monitor is three chances to
// re-pin at a width nothing was ever minted at.
//
// Why one rung and not five (2026-08-07): 104 live ladder closes produced zero
// fee-positive exits, and the on-chain fee meter says why — the NEAR rung is
// the only one that ever earned (GME rung 0: 0.002039 USDG/214m, while NVDA
// rungs 1-2 and all three TSLA rungs read exactly 0). The ladder did not fail
// for being one-sided; it failed because two thirds of the capital sat in rungs
// the market never traded into. One rung puts all of it where the fees were.
//
// Narrower than a ladder rung on purpose (600 vs 1200 WETH ticks, ~5.8% of
// covered drop vs ~11%). A ladder buys DEPTH — it wants to still be there after
// a fall — while turnover buys DENSITY: range it cannot reach before the next
// re-center is liquidity spread thin for nothing.
//
// The USDG figure is LATENT — robinhood.Turnover is WETH-pinned, and the
// equities that make up the USDG universe are the wrong book for this thesis
// (a deep, low-vol stock pool crosses a tight range rarely, which is the one
// thing the mode is paid for). It is here so the shape has an answer if that is
// ever revisited, and it carries the ladder's quantization trap: at the 1% tier
// (spacing 200) a 120-tick request rounds UP to 200, so the rung covers ~2.0%
// while UNI_TURNOVER_STALE_TICKS_USDG still judges drift at 60. Calibrate that
// pair against the executor's log line, not the env var, before enabling it.
const TURNOVER_RUNG_TICKS = {
  WETH: parseInt(process.env.UNI_TURNOVER_RUNG_TICKS || "600", 10),
  USDG: parseInt(process.env.UNI_TURNOVER_RUNG_TICKS_USDG || "120", 10),
};
TURNOVER_RUNG_TICKS.ETH = TURNOVER_RUNG_TICKS.WETH;

// turnoverGeom is ladderGeom's one-rung sibling: same unknown-quote fallback,
// no minRung (a single rung IS the whole commit, so there is nothing to drop to
// keep it above dust — the deploy floor in the Go daemon is what guards that).
function turnoverGeom(q) {
  return { rungTicks: TURNOVER_RUNG_TICKS[q.symbol] ?? TURNOVER_RUNG_TICKS.WETH };
}

// ladderGeom resolves the per-quote geometry. Unknown quotes fall back to the
// WETH numbers — silently minting a zero-width rung would be worse than an
// approximation.
function ladderGeom(q) {
  return {
    rungTicks: LADDER_RUNG_TICKS[q.symbol] ?? LADDER_RUNG_TICKS.WETH,
    minRung: parseUnits(String(LADDER_MIN_RUNG[q.symbol] ?? LADDER_MIN_RUNG.WETH), q.decimals),
  };
}

// rungWidth quantizes a requested rung width to the pool's tick spacing. A rung
// must be a whole number of spacings or the pool cannot express it; the floor of
// one spacing keeps a too-narrow request from rounding to a zero-width range.
// Both executors report this in their ladder log line, so it lives here rather
// than being recomputed inline at each call site.
//
// The rounding is silent and it BINDS in production, so read the log line, not
// the env var, when you want to know how wide a wall actually is. On the 1% tier
// (spacing 200) the USDG request of 240 rounds to 1 spacing, i.e. 200 — 17%
// narrower than asked, and unchanged by the 120 -> 240 widening because 120
// rounds there too. Any request under 1.5 spacings collapses to exactly one.
// See LADDER_RUNG_TICKS above for the per-tier census.
function rungWidth(spacing, rungTicks) {
  return Math.max(spacing, Math.round(rungTicks / spacing) * spacing);
}

// ladderSizes splits `amountRaw` across `rungs` on a linear 1:2:...:N ramp,
// smallest rung FIRST (nearest spot). The ramp is not decoration: the near
// rungs are the ones price actually reaches, so they are the ones that get
// converted into the token when it dips. Keeping them small means a wick costs
// little inventory, while the far rungs — which only fill in a real collapse,
// and which we intend to tear down before that happens — hold the bulk of the
// idle quote where it earns the widest fee coverage.
//
// Returns { sizes, rungs }: rungs is lowered until the smallest rung clears the
// quote's minimum (ladderGeom), because a ladder of dust is strictly worse than
// a shorter ladder of real rungs. Throws if even one rung can't clear it.
// `amountRaw` and the returned sizes are in the QUOTE's base units, so callers
// must format them at the quote's decimals — a 6-decimal USDG amount printed
// through formatEther reads as zero.
function ladderSizes(amountRaw, rungs, q) {
  const { minRung } = ladderGeom(q);
  let n = Math.max(1, rungs);
  while (n > 1) {
    const total = BigInt((n * (n + 1)) / 2);
    if (amountRaw / total >= minRung) break;
    n--;
  }
  const total = BigInt((n * (n + 1)) / 2);
  if (amountRaw / total < minRung) {
    throw new Error(`amount ${formatUnits(amountRaw, q.decimals)} ${q.symbol} cannot fund even one rung `
      + `of ${formatUnits(minRung, q.decimals)} ${q.symbol} (UNI_LADDER_MIN_RUNG_${q.symbol})`);
  }
  const sizes = [];
  let assigned = 0n;
  for (let k = 1; k <= n; k++) {
    const s = (amountRaw * BigInt(k)) / total;
    sizes.push(s);
    assigned += s;
  }
  // Integer division leaves a few base units; give them to the outermost rung so
  // the ladder commits exactly `amountRaw` and no dust is left dangling.
  sizes[sizes.length - 1] += amountRaw - assigned;
  return { sizes, rungs: n };
}

// ladderBands lays `rungs` contiguous, non-overlapping ranges on ONE side of
// `tick`, holding a single asset:
//
//   side="bid" (default) — the side where the token is CHEAPER than spot, so
//     each rung is a resting QUOTE bid that converts to token only if price
//     comes down to it. Every ladder and the turnover rung use this.
//   side="ask" — the mirror: the side where the token is DEARER than spot, so
//     each rung is a resting TOKEN offer that converts back to quote only if
//     price comes up to it. This is what a filled bid is re-listed as, so the
//     round trip is buy-low/sell-high instead of buy-low/market-dump.
//
// Which tick direction either side is depends on token ordering: the pool price
// is token1/token0, so with the QUOTE as token0 a RISING tick means more token
// per unit of quote (token cheaper) and the BID side goes up; with the quote as
// token1 it goes down. The ask side is the opposite in both cases, which is why
// `up` below is the equality of two booleans rather than two copies of the loop.
//
// Getting this backwards mints a band against an asset we do not hold — on v3
// the mint takes nothing and refunds, on v4 it reverts against that side's zero
// amountMax — so this is a correctness invariant, not a preference. It is also
// why the side is an explicit argument: a caller that means "sell this bag"
// must say so, never infer it from whichever balance happens to be non-zero.
//
// Rungs are returned inner-first (index 0 nearest spot) to line up with
// ladderSizes()'s smallest-first ramp.
function ladderBands(tick, spacing, quoteIs0, rungs, rungTicks, side = "bid") {
  if (side !== "bid" && side !== "ask") throw new Error(`ladderBands: bad side ${side}`);
  const w = rungWidth(spacing, rungTicks);
  const round = (t, up) => (up ? Math.ceil(t / spacing) : Math.floor(t / spacing)) * spacing;
  const bands = [];
  // Bid with quote-as-token0 ascends; flipping either the side or the ordering
  // flips the direction, so "both true or both false" is what ascending means.
  const up = (side === "bid") === Boolean(quoteIs0);
  if (up) {
    // Start one spacing AWAY from spot so rung 0 is adjacent but never
    // straddles: a straddling rung would demand both tokens and take only part
    // of the single asset offered.
    const base = round(tick + spacing, true);
    for (let k = 0; k < rungs; k++) {
      bands.push({ tickLower: base + k * w, tickUpper: base + (k + 1) * w });
    }
  } else {
    const base = round(tick - spacing, false);
    for (let k = 0; k < rungs; k++) {
      bands.push({ tickLower: base - (k + 1) * w, tickUpper: base - k * w });
    }
  }
  return bands;
}

// ladderSpan is a whole wall's tick extent and the price DROP that extent
// covers. Bands are ordered inner-first, which is DESCENDING in tick terms when
// the quote is token1, so the extent has to come from min/max rather than from
// the first and last entries. The drop is what the wall actually buys: a x1.82
// tick span is a -45% fall in the token, not a +82% rise.
function ladderSpan(bands) {
  const tickLo = Math.min(...bands.map((b) => b.tickLower));
  const tickHi = Math.max(...bands.map((b) => b.tickUpper));
  return { tickLo, tickHi, dropPct: (1 - 1 / Math.pow(1.0001, tickHi - tickLo)) * 100 };
}

module.exports = {
  LADDER_RUNGS,
  LADDER_RUNG_TICKS,
  LADDER_MIN_RUNG,
  TURNOVER_RUNG_TICKS,
  turnoverGeom,
  ladderGeom,
  rungWidth,
  ladderSizes,
  ladderBands,
  ladderSpan,
};
