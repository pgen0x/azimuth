// Uniswap v3 position executor for Robinhood Chain (chain ID 4663).
// EVM sibling of dlmm_executor.js: wraps ETH, swaps quote<->token via
// SwapRouter02, and mints/collects/closes NonfungiblePositionManager
// positions. viem only — no @uniswap/* SDKs (tick math needed here is small).
//
// QUOTE ASSETS: WETH (18 decimals) and USDG (6). --quote picks which side of a
// pool the position is funded and settled in; absent, it resolves to WETH, so
// every pre-USDG caller behaves unchanged. --amount is ALWAYS in the resolved
// quote's units — parse and print it with parseQ/fmtQ, never parseEther, or a
// USDG figure lands 10^12 out.
//
// Commands:
//   node uni_executor.js address                       # derived EVM address (fund this)
//   node uni_executor.js balance                       # ETH + WETH + USDG balances
//   node uni_executor.js wrap --amount 0.05            # ETH -> WETH
//   node uni_executor.js unwrap [--amount 0.001]       # WETH -> ETH (bare: refill gas reserve)
//   node uni_executor.js quote --pool 0x..             # pool state (tick, price, fee)
//   node uni_executor.js deploy --pool 0x.. --amount 0.01 [--strategy weth_ladder|usdg_ladder|balanced_tight|weth_below] [--quote 0x..] [--range-pct 10] [--slippage 5]
//   node uni_executor.js positions                     # owned NPM positions
//   node uni_executor.js collect --id 123              # collect fees only
//   node uni_executor.js close --id 123 [--no-swap-out]  # remove + collect + burn (+ token->WETH)
//   node uni_executor.js sweep [--token 0x..]          # retry the token->WETH sell for stranded bags
//
// Env (Hermes profile .env): EVM_PRIVATE_KEY — either a 0x-prefixed 32-byte
// hex key, or a base58 Solana secret key (the 32-byte ed25519 seed is reused
// as the secp256k1 scalar so one funded identity serves both venues until a
// dedicated EVM key exists). ROBINHOOD_RPC_URL optional. DRY_RUN=true skips
// every send and prints the 🧪 DRY RUN DEPLOY marker instead of 🚀 DEPLOYED.
//
// Optional tuning: UNI_GAS_FLOOR_ETH / UNI_GAS_TARGET_ETH (auto-unwrap gas
// reserve), UNI_EXIT_SLIPPAGE_PCT (exit-sell slippage floor),
// UNI_STRANDED_MAX_BACKOFF_S (sweep retry cap), UNI_LADDER_RUNGS,
// UNI_LADDER_RUNG_TICKS / UNI_LADDER_RUNG_TICKS_USDG (rung width per quote),
// UNI_LADDER_MIN_RUNG_WETH / UNI_LADDER_MIN_RUNG_USDG (dust floor per quote).

const bs58 = require("bs58");
const dotenv = require("dotenv");
const fs = require("fs");
const path = require("path");
const {
  createPublicClient, createWalletClient, http, parseEther, formatEther,
  parseUnits, formatUnits,
  getAddress, erc20Abi, parseAbi, parseEventLogs, maxUint128, encodeFunctionData,
  decodeFunctionResult,
} = require("viem");
const { privateKeyToAccount } = require("viem/accounts");
// Ladder geometry, shared verbatim with uni_v4_executor.js — see uni_ladder.js
// for why it is a module and not a copy in each executor. Relative to THIS file,
// so it resolves inside the symlinked scripts/ dir exactly as it does in-repo.
const {
  LADDER_RUNGS, ladderGeom, turnoverGeom, rungWidth, ladderSizes, ladderBands,
  ladderSpan,
} = require("./uni_ladder.js");

// Same profile resolution as dlmm_executor.js: process.argv[1], not __dirname,
// so a symlinked scripts/ dir still resolves to the profile, not this repo.
const SCRIPT_DIR = path.dirname(path.isAbsolute(process.argv[1]) ? process.argv[1] : path.resolve(process.argv[1]));
const PROFILE_DIR = path.dirname(path.dirname(path.dirname(SCRIPT_DIR)));
const profileEnvPath = path.join(PROFILE_DIR, ".env");
if (fs.existsSync(profileEnvPath)) dotenv.config({ path: profileEnvPath });

const RPC_URL = process.env.ROBINHOOD_RPC_URL || "https://rpc.mainnet.chain.robinhood.com";
const DRY_RUN = String(process.env.DRY_RUN || "").toLowerCase() === "true";

// Uniswap v3 deployment on Robinhood Chain. Verified on-chain 2026-07-13:
// NPM.factory() and NPM.WETH9() match, bytecode present at every address
// (docs: developers.uniswap.org v3-robinhood-chain-deployments).
const CHAIN_ID = 4663;
const WETH = getAddress("0x0bd7d308f8e1639fab988df18a8011f41eacad73");
const NPM = getAddress("0x73991a25c818bf1f1128deaab1492d45638de0d3");
const ROUTER = getAddress("0xcaf681a66d020601342297493863e78c959e5cb2");
const FACTORY = getAddress("0x1f7d7550b1b028f7571e69a784071f0205fd2efa");
const ZERO = "0x0000000000000000000000000000000000000000";

// USDG (Paxos' Global Dollar) is the venue's second quote asset and the one
// its tokenized equities trade against — nvda/USDG, gme/USDG, spacex/USDG.
// SIX DECIMALS, not eighteen: every amount that touches it must go through
// parseUnits/formatUnits with the quote's own decimals, never parseEther.
// Sizing an 8 USDG rung with parseEther would offer 8e18 base units — eight
// trillion dollars — and the mint would take the whole wallet balance instead.
const USDG = getAddress("0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168");

// The quote assets this executor can LP against. A pool must have one of them
// on a side; the other side is "the token" — the thing we do not want to hold.
const QUOTES = {
  [WETH]: { address: WETH, symbol: "WETH", decimals: 18 },
  [USDG]: { address: USDG, symbol: "USDG", decimals: 6 },
};

// resolveQuote picks which side of a pool is the quote asset. `want` is the
// --quote flag (the scanner forwards the candidate's quote address); when it is
// absent or not a side of this pool the resolution falls back to WETH, which is
// what every position minted before USDG support used.
//
// Throws when neither side is a known quote: a pool of two unknown tokens has
// no side we are willing to be left holding.
function resolveQuote(st, want) {
  const sides = [st.token0, st.token1];
  const wanted = want ? getAddress(want) : null;
  let addr = wanted && sides.includes(wanted) && QUOTES[wanted] ? wanted : null;
  if (!addr) addr = sides.find((s) => QUOTES[s] && s === WETH) || sides.find((s) => QUOTES[s]);
  if (!addr) throw new Error(`pool has no WETH/USDG side (token0=${st.token0} token1=${st.token1})`);
  if (wanted && wanted !== addr) {
    console.error(`warn: --quote ${wanted} is not a side of this pool — using ${QUOTES[addr].symbol}`);
  }
  const q = QUOTES[addr];
  return { ...q, isToken0: st.token0 === addr, token: st.token0 === addr ? st.token1 : st.token0 };
}

// Amount helpers that take the quote's decimals instead of assuming 18. The
// `q` argument is a resolveQuote() result (or any {decimals}).
function parseQ(v, q) { return parseUnits(String(v), q.decimals); }
function fmtQ(v, q) { return formatUnits(v, q.decimals); }

// Minimum share of each offered side a two-sided mint must actually consume.
// A v3 mint whose range no longer straddles the tick takes ONE token and
// refunds the other without reverting — the failure mode that made every
// balanced_tight entry a dead out-of-range position. Passing this as
// amount0Min/amount1Min turns that silent half-fill into a revert we can
// unwind, while still tolerating the ratio drift a live tick causes.
const MIN_FILL_PCT = parseFloat(process.env.UNI_MIN_FILL_PCT || "25");

// Ladder geometry — rung count, per-quote rung width, per-quote dust floor, the
// size ramp and the band layout — lives in ./uni_ladder.js (required above) and
// is shared verbatim with the v4 executor, because those numbers describe the
// THESIS rather than either protocol. uni_monitor.py's `ladder stale` rule
// compares live drift against the same widths, so a private copy here is exactly
// how a wall ends up re-pinning at a width it was never minted at.

// Every Uniswap v3 fee tier. The exit sell walks all of them, not just the
// tier of the pool we LP'd: a launch pool's liquidity can be pulled out from
// under us while a rival tier still bids on the same token.
const FEE_TIERS = [100, 500, 3000, 10000];

// Slippage floor for the exit sell. Wide on purpose — the alternative to a bad
// fill on a dumping memecoin is no fill, and no fill means the bag rots.
const EXIT_SLIPPAGE_PCT = parseFloat(process.env.UNI_EXIT_SLIPPAGE_PCT || "15");

// Gas floor. Every tx here is paid in native ETH, but every asset the bot holds
// is WETH — so the wallet can be solvent and still unable to close a position,
// which is exactly the moment being stuck costs the most. The executor tops
// itself up from WETH before any state-changing command instead of waiting for
// the operator to unwrap by hand. A full close+sell runs ~0.000035 ETH at the
// chain's ~0.05 gwei, so the default floor is ~8 closes of headroom and the
// target ~23 — small enough that the reserve never meaningfully competes with
// trading capital. Top-ups take only what's needed to reach the target.
const GAS_FLOOR_WEI = parseEther(process.env.UNI_GAS_FLOOR_ETH || "0.0003");
const GAS_TARGET_WEI = parseEther(process.env.UNI_GAS_TARGET_ETH || "0.0008");

// Position entry journal: uni_monitor.py reads cost basis (WETH deployed) +
// entry timestamp from here to compute PnL and age, the EVM analog of the
// Meteora portfolio API the Solana monitor queries. One JSON line per mint.
const POS_JOURNAL = path.join(PROFILE_DIR, "memories", "uni_positions.jsonl");

// Stranded-bag journal. A close is three on-chain steps (decrease, collect,
// burn) plus a sell, and only the first three are guaranteed to work: the pool
// can be rugged to zero liquidity by the time we try to sell back out, and then
// exactInputSingle reverts. The position is gone but the tokens are real and
// still in the wallet, so they get written here and retried by `sweep` — an
// unsellable bag is a fact to schedule around, not an error to throw away.
const STRANDED_JOURNAL = path.join(PROFILE_DIR, "memories", "uni_stranded.jsonl");

const chain = {
  id: CHAIN_ID,
  name: "Robinhood Chain",
  nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
  rpcUrls: { default: { http: [RPC_URL] } },
};

const poolAbi = parseAbi([
  "function slot0() view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)",
  "function liquidity() view returns (uint128)",
  "function tickSpacing() view returns (int24)",
  "function token0() view returns (address)",
  "function token1() view returns (address)",
  "function fee() view returns (uint24)",
]);

const npmAbi = parseAbi([
  "function mint((address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, uint256 amount0Desired, uint256 amount1Desired, uint256 amount0Min, uint256 amount1Min, address recipient, uint256 deadline)) payable returns (uint256 tokenId, uint128 liquidity, uint256 amount0, uint256 amount1)",
  "function positions(uint256 tokenId) view returns (uint96 nonce, address operator, address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, uint128 liquidity, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, uint128 tokensOwed0, uint128 tokensOwed1)",
  "function balanceOf(address owner) view returns (uint256)",
  "function tokenOfOwnerByIndex(address owner, uint256 index) view returns (uint256)",
  "function decreaseLiquidity((uint256 tokenId, uint128 liquidity, uint256 amount0Min, uint256 amount1Min, uint256 deadline)) payable returns (uint256 amount0, uint256 amount1)",
  // Emitted by mint(): the amounts the position ACTUALLY took, which is the only
  // honest cost basis — the rest of what we offered is refunded to the wallet.
  "event IncreaseLiquidity(uint256 indexed tokenId, uint128 liquidity, uint256 amount0, uint256 amount1)",
  "function collect((uint256 tokenId, address recipient, uint128 amount0Max, uint128 amount1Max)) payable returns (uint256 amount0, uint256 amount1)",
  "function burn(uint256 tokenId) payable",
  // weth_ladder mints every rung in ONE tx. Atomicity is the point: a ladder
  // half-minted across N txs is a broken shape (wrong sizes at the wrong
  // ticks) that no exit rule describes, and each extra tx is another chance
  // for the tick to move between rungs.
  "function multicall(bytes[] data) payable returns (bytes[] results)",
]);

const routerAbi = parseAbi([
  "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) payable returns (uint256 amountOut)",
]);

const wethAbi = parseAbi([
  "function deposit() payable",
  "function withdraw(uint256 wad)",
]);

const factoryAbi = parseAbi([
  "function getPool(address tokenA, address tokenB, uint24 fee) view returns (address pool)",
]);

// valueInQuote converts a position's raw (amount0, amount1) into the quote
// asset's own base units using the pool's sqrtPriceX96. Because sqrtPriceX96 is
// defined on RAW token amounts (price = raw_token1 / raw_token0), token
// decimals cancel and no per-token decimal lookup is needed — the result is
// already in the quote's units, whether that is 18-decimal WETH or 6-decimal
// USDG. Format it with fmtQ, never formatEther.
function valueInQuote(amount0, amount1, sqrtPriceX96, quoteIs0) {
  const Q192 = 1n << 192n;
  const p2 = sqrtPriceX96 * sqrtPriceX96; // price * 2^192
  if (quoteIs0) {
    // token1 -> token0(quote): amount1 * 2^192 / sqrtP^2
    return amount0 + (amount1 * Q192) / p2;
  }
  // token0 -> token1(quote): amount0 * sqrtP^2 / 2^192
  return amount1 + (amount0 * p2) / Q192;
}

// journalEntry appends one position's cost basis so uni_monitor.py can price
// PnL later. Best-effort: a journal write failure must never fail a mint.
function journalEntry(rec) {
  try {
    fs.mkdirSync(path.dirname(POS_JOURNAL), { recursive: true });
    fs.appendFileSync(POS_JOURNAL, JSON.stringify(rec) + "\n");
  } catch (e) {
    console.error(`warn: could not journal position entry: ${e.message}`);
  }
}

// journalStranded appends one stranded-bag event. Append-only: the newest line
// for a token wins, so a `resolved: true` line retires an earlier open one.
function journalStranded(rec) {
  try {
    fs.mkdirSync(path.dirname(STRANDED_JOURNAL), { recursive: true });
    // ts/timestamp go LAST: a re-journaled bag is spread from its previous line
    // and would otherwise carry that line's timestamp forward, so every retry
    // and even the final sale would be stamped with the moment the bag was
    // first seen. Each line records when THAT line was written.
    fs.appendFileSync(STRANDED_JOURNAL, JSON.stringify({
      ...rec,
      ts: Math.floor(Date.now() / 1000),
      timestamp: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    }) + "\n");
  } catch (e) {
    console.error(`warn: could not journal stranded bag: ${e.message}`);
  }
}

// retryDelay backs a failing bag off exponentially: 1m, 2m, 4m ... capped at
// STRANDED_MAX_BACKOFF_S. A rugged pool can in principle be re-seeded by
// another LP, so a bag is never permanently written off — but re-offering a
// zero-liquidity token every 60s forever is ~5 RPC reads per bag per tick of
// pure noise, and the noise grows with every future rug. Backoff keeps the
// hopeless ones cheap without ever giving up on them.
const STRANDED_MAX_BACKOFF_S = parseInt(process.env.UNI_STRANDED_MAX_BACKOFF_S || "3600", 10);
function retryDelay(attempts) {
  return Math.min(60 * 2 ** Math.max(0, attempts - 1), STRANDED_MAX_BACKOFF_S);
}

// openStranded returns the still-unsold bags, newest-line-wins per token.
function openStranded() {
  const latest = new Map();
  try {
    for (const line of fs.readFileSync(STRANDED_JOURNAL, "utf8").trim().split("\n")) {
      if (!line) continue;
      const r = JSON.parse(line);
      latest.set(getAddress(r.token), r);
    }
  } catch { /* no journal yet */ }
  return [...latest.values()].filter((r) => !r.resolved);
}

// resolveMintedTokenId pins the tokenId of the position just minted in `rcpt`.
// An orphaned cost basis (tokenId="unknown") is a live-money footgun: the
// monitor keys PnL off uni_positions.jsonl by tokenId, so a wrong/missing id
// means entryWeth=null and SL/TP never fire on that position. Two independent
// sources, most-precise first:
//   1. the ERC721 Transfer(0x0 -> us) log from THIS mint tx (exact),
//   2. the newest NPM token this wallet owns (authoritative post-mint; the
//      just-minted position is the highest owner index).
// Throws if both fail — better to surface a bare tx hash the operator can
// journal by hand than to write an unmanageable position silently.
async function resolveMintedTokenId(rcpt, account) {
  const acct = account.address.toLowerCase();
  const xfer = rcpt.logs.find((l) =>
    l.address.toLowerCase() === NPM.toLowerCase() &&
    l.topics.length === 4 &&                       // ERC721 Transfer (ERC20 has 3)
    BigInt(l.topics[1]) === 0n &&                  // from == 0x0 (mint)
    `0x${l.topics[2].slice(-40)}`.toLowerCase() === acct); // to == us
  if (xfer) return BigInt(xfer.topics[3]).toString();
  console.error("warn: mint Transfer log not found, falling back to NPM owner enumeration");
  const bal = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "balanceOf", args: [account.address] });
  if (bal > 0n) {
    const id = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "tokenOfOwnerByIndex", args: [account.address, bal - 1n] });
    return id.toString();
  }
  throw new Error("could not resolve minted tokenId (no Transfer log, wallet owns 0 positions)");
}

// readEntry returns the newest journal record for a tokenId, or null. The
// monitor passes cost basis on the CLI too (--entry-weth), so a missing
// journal (e.g. hand-created position) is not fatal.
function readEntry(tokenId) {
  try {
    const lines = fs.readFileSync(POS_JOURNAL, "utf8").trim().split("\n");
    for (let i = lines.length - 1; i >= 0; i--) {
      if (!lines[i]) continue;
      const r = JSON.parse(lines[i]);
      if (String(r.tokenId) === String(tokenId)) return r;
    }
  } catch { /* no journal yet */ }
  return null;
}

function getAccount() {
  const raw = (process.env.EVM_PRIVATE_KEY || "").trim();
  if (!raw) throw new Error("EVM_PRIVATE_KEY not set in profile .env");
  if (raw.startsWith("0x") && raw.length === 66) return privateKeyToAccount(raw);
  // Base58 Solana secret key: 64 bytes (seed || ed25519 pubkey) or a bare
  // 32-byte seed. The seed bytes become the secp256k1 private key — a
  // deliberate stopgap so the Solana wallet identity funds this venue too.
  const decoded = Buffer.from(bs58.decode(raw));
  if (decoded.length !== 64 && decoded.length !== 32) {
    throw new Error(`EVM_PRIVATE_KEY: expected 0x-hex(32B) or base58 Solana key, got ${decoded.length} bytes`);
  }
  return privateKeyToAccount(`0x${decoded.subarray(0, 32).toString("hex")}`);
}

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  if (i === -1 || i + 1 >= process.argv.length) return def;
  return process.argv[i + 1];
}
function hasFlag(name) { return process.argv.includes(`--${name}`); }

const pub = createPublicClient({ chain, transport: http(RPC_URL) });

async function send(wallet, req, label) {
  if (DRY_RUN) {
    console.log(`[dry-run] would send: ${label}`);
    return "DRY_RUN_TX_HASH";
  }
  // writeContract takes the node's gas estimate verbatim, but pool state can
  // move between estimate and inclusion (extra tick crossings on a hot pool),
  // so pad 30%. A failed estimate falls through to writeContract, whose own
  // simulation surfaces the actual revert reason.
  const gas = await pub
    .estimateContractGas({ ...req, account: req.account ?? wallet.account })
    .then((g) => (g * 130n) / 100n)
    .catch(() => undefined);
  const hash = await wallet.writeContract(gas ? { ...req, gas } : req);
  const rcpt = await pub.waitForTransactionReceipt({ hash, timeout: 120_000 });
  if (rcpt.status !== "success") throw new Error(`${label} reverted: ${hash}`);
  console.log(`${label}: ${hash}`);
  return hash;
}

// ensureGas unwraps just enough WETH to keep native ETH above GAS_FLOOR_WEI.
// Called before every state-changing command, so the bot can always pay for its
// own exit. Never throws: a failed top-up must not abort the close it was meant
// to enable — the close may still have enough gas to land on its own.
//
// The one unrecoverable case is ETH at literal zero, because the unwrap tx
// itself needs gas. The floor exists to make sure we never get there: it trips
// while several closes' worth of gas is still in the wallet.
async function ensureGas(wallet, account) {
  if (DRY_RUN) return null;
  const eth = await pub.getBalance({ address: account.address });
  if (eth >= GAS_FLOOR_WEI) return null;

  const weth = await pub.readContract({ address: WETH, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
  if (weth === 0n) {
    console.error(`warn: gas low (${formatEther(eth)} ETH) and no WETH to unwrap — fund this wallet`);
    return { low: true, eth: formatEther(eth), unwrapped: "0", reason: "no WETH to unwrap" };
  }
  // A floor set above the target would make `need` negative and hand withdraw()
  // a nonsense amount, so treat the target as at least the floor.
  const target = GAS_TARGET_WEI > GAS_FLOOR_WEI ? GAS_TARGET_WEI : GAS_FLOOR_WEI;
  const need = target - eth;
  if (need <= 0n) return null;
  const amount = need < weth ? need : weth;
  try {
    const tx = await send(wallet, {
      address: WETH, abi: wethAbi, functionName: "withdraw", args: [amount],
      account: wallet.account, chain,
    }, `unwrap ${formatEther(amount)} WETH -> ETH (gas top-up, had ${formatEther(eth)})`);
    return { low: false, eth_before: formatEther(eth), unwrapped: formatEther(amount), tx };
  } catch (e) {
    console.error(`warn: gas top-up failed: ${e.shortMessage || e.message}`);
    return { low: true, eth: formatEther(eth), unwrapped: "0", reason: e.shortMessage || e.message };
  }
}

async function ensureAllowance(wallet, owner, token, spender, amount) {
  const current = await pub.readContract({ address: token, abi: erc20Abi, functionName: "allowance", args: [owner, spender] });
  if (current >= amount) return;
  // Exact-amount approval on purpose — no unlimited allowances on a memecoin venue.
  await send(wallet, { address: token, abi: erc20Abi, functionName: "approve", args: [spender, amount], account: wallet.account, chain }, `approve ${spender.slice(0, 10)}`);
}

// sellTokenForQuote unloads `amount` of `token` into the quote asset `q`
// (a QUOTES entry — WETH unless the position was USDG-quoted), trying
// `preferredFee` first and then every other v3 tier.
//
// It SIMULATES each tier before sending. That simulation is the whole point:
// the sell is the one leg of a close that routinely fails on this venue (dead
// pool after a rug, sell tax, blacklist), and a raw send would revert inside
// send() and throw — aborting a close whose decrease/collect/burn had already
// landed. Since no QuoterV2 is published for Robinhood Chain, a static call to
// SwapRouter02 itself is the quote: it reverts for exactly the reasons a live
// sell would, and its return value is the amountOut we set the slippage floor
// against. Never throws — returns {ok:false, reason} so the caller decides.
async function sellTokenForQuote(wallet, account, token, amount, preferredFee, q = QUOTES[WETH]) {
  if (amount <= 0n) return { ok: false, reason: "zero balance" };
  const tiers = [...new Set([preferredFee, ...FEE_TIERS].filter((f) => f != null).map(Number))];
  const failures = [];

  for (const fee of tiers) {
    const pool = await pub.readContract({
      address: FACTORY, abi: factoryAbi, functionName: "getPool", args: [token, q.address, fee],
    }).catch(() => null);
    if (!pool || getAddress(pool) === ZERO) { failures.push(`${fee}: no pool`); continue; }

    // The router must be able to pull the tokens before the simulation is
    // meaningful — without the allowance every tier "reverts" with STF and we
    // would journal a sellable bag as stranded.
    try {
      await ensureAllowance(wallet, account.address, token, ROUTER, amount);
    } catch (e) {
      return { ok: false, reason: `approve failed: ${e.shortMessage || e.message}` };
    }

    let quoted;
    try {
      const sim = await pub.simulateContract({
        address: ROUTER, abi: routerAbi, functionName: "exactInputSingle",
        args: [{ tokenIn: token, tokenOut: q.address, fee, recipient: account.address, amountIn: amount, amountOutMinimum: 0n, sqrtPriceLimitX96: 0n }],
        account: account.address, chain,
      });
      quoted = sim.result;
    } catch (e) {
      failures.push(`${fee}: ${(e.shortMessage || e.message || "reverted").split("\n")[0].slice(0, 60)}`);
      continue;
    }
    if (quoted === 0n) { failures.push(`${fee}: quote 0`); continue; }

    const minOut = (quoted * BigInt(Math.floor((100 - EXIT_SLIPPAGE_PCT) * 100))) / 10000n;
    try {
      const tx = await send(wallet, {
        address: ROUTER, abi: routerAbi, functionName: "exactInputSingle",
        args: [{ tokenIn: token, tokenOut: q.address, fee, recipient: account.address, amountIn: amount, amountOutMinimum: minOut, sqrtPriceLimitX96: 0n }],
        account: wallet.account, chain,
      }, `sell token -> ${q.symbol} (fee ${fee}, ~${fmtQ(quoted, q)} ${q.symbol})`);
      return { ok: true, amountOut: quoted, fee, tx, quote: q };
    } catch (e) {
      // Simulated clean but reverted on-chain: the pool moved under us between
      // the two calls. Fall through to the next tier rather than throwing.
      failures.push(`${fee}: send reverted (${(e.shortMessage || e.message).slice(0, 40)})`);
    }
  }
  return { ok: false, reason: failures.join("; ") || "no route" };
}

async function poolState(pool) {
  const [slot0, tickSpacing, token0, token1, fee, liquidity] = await Promise.all([
    pub.readContract({ address: pool, abi: poolAbi, functionName: "slot0" }),
    pub.readContract({ address: pool, abi: poolAbi, functionName: "tickSpacing" }),
    pub.readContract({ address: pool, abi: poolAbi, functionName: "token0" }),
    pub.readContract({ address: pool, abi: poolAbi, functionName: "token1" }),
    pub.readContract({ address: pool, abi: poolAbi, functionName: "fee" }),
    pub.readContract({ address: pool, abi: poolAbi, functionName: "liquidity" }),
  ]);
  return { sqrtPriceX96: slot0[0], tick: slot0[1], tickSpacing, token0: getAddress(token0), token1: getAddress(token1), fee, liquidity };
}

// pctToTicks converts a +/- percent band to a tick count (1 tick = 1.0001x).
function pctToTicks(pct) { return Math.round(Math.log(1 + pct / 100) / Math.log(1.0001)); }
function roundToSpacing(tick, spacing, up) {
  const q = tick / spacing;
  return (up ? Math.ceil(q) : Math.floor(q)) * spacing;
}

// spotOutFor computes the spot-price output of `amountIn` of tokenIn using
// sqrtPriceX96 (price of token1 in token0 terms), for the swap minOut guard.
function spotOutFor(amountIn, sqrtPriceX96, zeroForOne) {
  const Q96 = 1n << 96n;
  // price1per0 = (sqrtP/Q96)^2 -> amount1 = amount0 * sqrtP^2 / Q96^2
  if (zeroForOne) return (amountIn * sqrtPriceX96 * sqrtPriceX96) / (Q96 * Q96);
  return (amountIn * Q96 * Q96) / (sqrtPriceX96 * sqrtPriceX96);
}

async function cmdAddress(account) {
  console.log(JSON.stringify({ address: account.address, derivedFrom: process.env.EVM_PRIVATE_KEY?.startsWith("0x") ? "hex" : "solana-seed", chainId: CHAIN_ID }));
}

// cmdBalance reports every asset the scanner sizes against: native ETH (gas
// only), WETH (the memecoin ladders' capital) and USDG (the stock ladders').
// The three are NOT interchangeable — internal/robinhood.Balances keeps them
// apart for exactly that reason, and a USDG deploy sized off the WETH balance
// would be off by five orders of magnitude in dollar terms.
async function cmdBalance(account) {
  const [eth, weth, usdg] = await Promise.all([
    pub.getBalance({ address: account.address }),
    pub.readContract({ address: WETH, abi: erc20Abi, functionName: "balanceOf", args: [account.address] }),
    pub.readContract({ address: USDG, abi: erc20Abi, functionName: "balanceOf", args: [account.address] })
      .catch(() => 0n),
  ]);
  console.log(JSON.stringify({
    address: account.address,
    eth: formatEther(eth),
    weth: formatEther(weth),
    usdg: formatUnits(usdg, QUOTES[USDG].decimals),
  }));
}

async function cmdWrap(wallet) {
  const amount = parseEther(arg("amount", "0"));
  if (amount <= 0n) throw new Error("--amount required (ETH)");
  await send(wallet, { address: WETH, abi: wethAbi, functionName: "deposit", value: amount, account: wallet.account, chain }, `wrap ${formatEther(amount)} ETH`);
  console.log(JSON.stringify({ success: true, wrapped: formatEther(amount) }));
}

async function cmdUnwrap(wallet, account) {
  // --amount unwraps exactly that; bare `unwrap` tops the gas reserve back up
  // to its target, which is what the monitor and the operator usually want.
  const raw = arg("amount", "");
  if (!raw) {
    const eth = await pub.getBalance({ address: account.address });
    const weth = await pub.readContract({ address: WETH, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
    const need = GAS_TARGET_WEI > eth ? GAS_TARGET_WEI - eth : 0n;
    const amount = need < weth ? need : weth;
    if (amount === 0n) {
      console.log(JSON.stringify({ success: true, unwrapped: "0", note: "gas reserve already at target", eth: formatEther(eth) }));
      return;
    }
    await send(wallet, { address: WETH, abi: wethAbi, functionName: "withdraw", args: [amount], account: wallet.account, chain }, `unwrap ${formatEther(amount)} WETH`);
    console.log(JSON.stringify({ success: true, unwrapped: formatEther(amount), eth_before: formatEther(eth) }));
    return;
  }
  const amount = parseEther(raw);
  if (amount <= 0n) throw new Error("--amount must be > 0 (WETH)");
  await send(wallet, { address: WETH, abi: wethAbi, functionName: "withdraw", args: [amount], account: wallet.account, chain }, `unwrap ${formatEther(amount)} WETH`);
  console.log(JSON.stringify({ success: true, unwrapped: formatEther(amount) }));
}

// cmdGasTopup buys gas with strategy capital: sell USDG for WETH, then unwrap
// it to native ETH. A usdg_ladder wallet earns and holds dollars but pays gas
// in ETH, so its gas balance only ever falls — and a wallet that cannot pay gas
// can neither mint NOR close, which turns a resting rung into a position no
// exit rule can release. Its own command rather than folded into deploy:
// how much capital to pull out of the strategy is an operator decision, not
// something a deploy should do silently mid-flight.
async function cmdGasTopup(wallet, account) {
  const q = QUOTES[USDG];
  const amount = parseQ(arg("amount", "0"), q);
  if (amount <= 0n) throw new Error("--amount required (USDG)");
  const held = await pub.readContract({ address: USDG, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
  if (held < amount) throw new Error(`insufficient USDG: have ${fmtQ(held, q)}, want ${fmtQ(amount, q)}`);

  // sellTokenForQuote walks the fee tiers and sets the slippage floor off a
  // router simulation, so a thin tier fails over instead of executing badly.
  const sold = await sellTokenForQuote(wallet, account, USDG, amount, null, QUOTES[WETH]);
  if (!sold.ok) throw new Error(`USDG -> WETH failed: ${sold.reason}`);

  // Unwrap the proceeds only, never the whole WETH balance: on a wallet that
  // also runs weth_ladder the rest of that balance is working capital.
  await send(wallet, { address: WETH, abi: wethAbi, functionName: "withdraw", args: [sold.amountOut], account: wallet.account, chain }, `unwrap ${formatEther(sold.amountOut)} WETH`);
  const eth = await pub.getBalance({ address: account.address });
  console.log(JSON.stringify({
    success: true, sold_usdg: fmtQ(amount, q), weth_out: formatEther(sold.amountOut),
    fee_tier: sold.fee, eth: formatEther(eth), swap_tx: sold.tx,
  }));
}

async function cmdQuote() {
  const pool = getAddress(arg("pool", ""));
  const st = await poolState(pool);
  const [sym0, sym1] = await Promise.all([
    pub.readContract({ address: st.token0, abi: erc20Abi, functionName: "symbol" }).catch(() => "?"),
    pub.readContract({ address: st.token1, abi: erc20Abi, functionName: "symbol" }).catch(() => "?"),
  ]);
  console.log(JSON.stringify({
    pool, token0: `${sym0} ${st.token0}`, token1: `${sym1} ${st.token1}`,
    fee: Number(st.fee), tick: Number(st.tick), tickSpacing: Number(st.tickSpacing),
    sqrtPriceX96: st.sqrtPriceX96.toString(), liquidity: st.liquidity.toString(),
    wethIsToken0: st.token0 === WETH,
    quoteSymbol: QUOTES[st.token0]?.symbol || QUOTES[st.token1]?.symbol || null,
  }));
}

// cmdDeployLadder mints the ladder shape: N one-sided rungs of the pool's
// QUOTE asset, in a single NPM.multicall. It serves both ladder strategies —
// weth_ladder (WETH rungs under a memecoin) and usdg_ladder (USDG rungs under
// a tokenized equity). Only the geometry differs, and that comes from
// ladderGeom(); the shape, the atomic mint and the exit rules are identical.
//
// This is the venue's answer to why balanced_tight lost money. That strategy
// swaps half the commit into the memecoin before minting, so every position is
// LONG a token on a chain where tokens bleed — every exit it took was a price
// exit, never a fee take-profit. A ladder never buys the token. It parks WETH under
// the price and gets paid the fee tier whenever the market trades down into
// it, so the only inventory it ever holds is inventory the market handed it at
// a price we chose. Exits are re-pins, not stop-losses — see uni_monitor.py.
async function cmdDeployLadder(wallet, account, strategy) {
  const pool = getAddress(arg("pool", ""));

  await ensureGas(wallet, account);

  const st = await poolState(pool);
  // Which asset the rungs are made of. --quote comes from the scanner (the
  // screened candidate's quote side); absent, this resolves to WETH, so every
  // pre-USDG call behaves exactly as before.
  const q = resolveQuote(st, arg("quote", ""));
  const quoteIs0 = q.isToken0;
  const geom = ladderGeom(q);
  const rungTicks = parseInt(arg("rung-ticks", String(geom.rungTicks)), 10);
  // Parsed at the QUOTE's decimals — parseEther here would inflate a USDG
  // amount by 10^12 and offer the whole wallet to the first rung.
  const amountQuote = parseQ(arg("amount", "0"), q);
  if (amountQuote <= 0n) throw new Error(`--amount required (${q.symbol})`);
  const spacing = Number(st.tickSpacing);
  const tick = Number(st.tick);

  const { sizes, rungs } = ladderSizes(amountQuote, parseInt(arg("rungs", String(LADDER_RUNGS)), 10), q);
  const bands = ladderBands(tick, spacing, quoteIs0, rungs, rungTicks);
  const deadline = BigInt(Math.floor(Date.now() / 1000) + 120);

  const mints = bands.map((b, k) => ({
    token0: st.token0, token1: st.token1, fee: st.fee,
    tickLower: b.tickLower, tickUpper: b.tickUpper,
    amount0Desired: quoteIs0 ? sizes[k] : 0n,
    amount1Desired: quoteIs0 ? 0n : sizes[k],
    // A one-sided range has a zero side by construction and consumes
    // essentially all of the funded side, so there is no half-fill to guard
    // against — the MIN_FILL_PCT guard exists only for two-sided mints.
    amount0Min: 0n, amount1Min: 0n,
    recipient: account.address, deadline,
  }));

  const { tickLo, tickHi, dropPct } = ladderSpan(bands);
  console.log(`ladder: ${rungs} rungs x ${rungWidth(spacing, rungTicks)} ticks `
    + `on the bid side of tick ${tick} (${q.symbol} is token${quoteIs0 ? 0 : 1}), `
    + `covering a ${dropPct.toFixed(0)}% fall, sizes `
    + `[${sizes.map((s) => fmtQ(s, q)).join(", ")}] ${q.symbol}`);

  if (DRY_RUN) {
    console.log(`🧪 DRY RUN DEPLOY pool=${pool} strategy=${strategy} rungs=${rungs} `
      + `ticks=[${tickLo},${tickHi}] `
      + `amount=${fmtQ(amountQuote, q)} ${q.symbol}`);
    console.log(JSON.stringify({
      success: true, dryRun: true, pool, strategy, rungs,
      quote: q.address, quoteSymbol: q.symbol,
      bands, sizes: sizes.map((s) => fmtQ(s, q)),
    }));
    return;
  }

  await ensureAllowance(wallet, account.address, q.address, NPM, amountQuote);

  const calls = mints.map((m) => encodeFunctionData({ abi: npmAbi, functionName: "mint", args: [m] }));
  let hash, rcpt;
  try {
    hash = await wallet.writeContract({
      address: NPM, abi: npmAbi, functionName: "multicall", args: [calls],
      account: wallet.account, chain,
    });
    rcpt = await pub.waitForTransactionReceipt({ hash, timeout: 120_000 });
    if (rcpt.status !== "success") throw new Error(`ladder mint reverted: ${hash}`);
  } catch (e) {
    // Nothing to unwind: the ladder never swapped, so every unit is still quote
    // asset in the wallet. That is the whole point of the one-sided shape — a
    // failed entry costs gas and nothing else.
    const reason = (e.shortMessage || e.message || "ladder mint failed").split("\n")[0];
    console.log(`❌ DEPLOY FAILED (no position opened): ${reason}`);
    console.log(JSON.stringify({ success: false, error: `ladder mint failed: ${reason}`, pool, strategy, quoteSymbol: q.symbol }));
    return;
  }

  // Every rung is journaled as its own position (the monitor prices and closes
  // per tokenId) but they share a ladderId so the re-pin rule can treat the
  // ladder as one unit and tear it down together.
  const ladderId = `${pool.toLowerCase()}-${Math.floor(Date.now() / 1000)}`;
  const incs = parseEventLogs({ abi: npmAbi, eventName: "IncreaseLiquidity", logs: rcpt.logs });
  if (incs.length !== rungs) {
    console.error(`warn: ${incs.length} IncreaseLiquidity events for ${rungs} rungs — `
      + "journaling only what landed; unjournaled rungs are invisible to the monitor");
  }
  const opened = [];
  for (const inc of incs) {
    const tokenId = inc.args.tokenId.toString();
    const p = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "positions", args: [inc.args.tokenId] });
    const tickLower = Number(p[5]);
    const tickUpper = Number(p[6]);
    const entryQuote = valueInQuote(inc.args.amount0, inc.args.amount1, st.sqrtPriceX96, quoteIs0);
    const rung = bands.findIndex((b) => b.tickLower === tickLower && b.tickUpper === tickUpper);
    journalEntry({
      tokenId, pool, token0: st.token0, token1: st.token1, fee: Number(st.fee),
      tickLower, tickUpper, strategy,
      // quoteIn is the canonical cost basis; wethIn mirrors it for the readers
      // that predate USDG (cmdState's fallback, older journal analysis). The
      // mirror is only honest because quote/quoteSymbol travel with it — a
      // ladder's basis is in its OWN quote asset, never converted to WETH.
      quote: q.address, quoteSymbol: q.symbol, quoteDecimals: q.decimals,
      quoteIn: fmtQ(entryQuote, q), wethIn: fmtQ(entryQuote, q),
      ladderId, rung: rung < 0 ? null : rung, rungs,
      // Spot at the moment the wall was laid — the ONLY honest zero for drift.
      // The band edges are not: ladderBands() pins one spacing off spot and then
      // quantizes, so rung 0's near edge is born spacing..2*spacing away from
      // `tick`, and a drift rule that measures from the edge reads that birth
      // offset as market movement. See uni_monitor.py's rung_drift().
      entryTick: tick,
      committedQuote: fmtQ(rung < 0 ? 0n : sizes[rung], q),
      used0: inc.args.amount0.toString(), used1: inc.args.amount1.toString(),
      ts: Math.floor(Date.now() / 1000),
    });
    opened.push({ tokenId, tickLower, tickUpper, quoteIn: fmtQ(entryQuote, q) });
  }

  const totalIn = incs.reduce((acc, i) => acc + valueInQuote(i.args.amount0, i.args.amount1, st.sqrtPriceX96, quoteIs0), 0n);
  console.log(`🚀 DEPLOYED pool=${pool} strategy=${strategy} rungs=${opened.length} `
    + `ladder=${ladderId} ${q.symbol.toLowerCase()}=${fmtQ(totalIn, q)} tx=${hash}`);
  console.log(JSON.stringify({
    success: true, pool, strategy, ladderId, rungs: opened.length,
    quote: q.address, quoteSymbol: q.symbol,
    positions: opened, tx: hash, quoteIn: fmtQ(totalIn, q),
    committedQuote: fmtQ(amountQuote, q),
  }));
}

async function cmdDeploy(wallet, account) {
  const pool = getAddress(arg("pool", ""));
  const strategy = arg("strategy", "balanced_tight");
  const rangePct = parseFloat(arg("range-pct", "10"));
  const slippagePct = parseFloat(arg("slippage", "5"));
  // Either ladder mints N positions in one multicall, so it cannot share this
  // function's single-tokenId tail (cost basis, journal, in-range report).
  // Routed here rather than given its own subcommand so the Go Runner's
  // `deploy --strategy X` contract keeps working unchanged.
  if (strategy === "weth_ladder" || strategy === "usdg_ladder") {
    return cmdDeployLadder(wallet, account, strategy);
  }

  // Top up gas BEFORE minting: an entry that spends the wallet down to no ETH
  // leaves the position with no way to pay for its own exit.
  await ensureGas(wallet, account);

  const st = await poolState(pool);
  const q = resolveQuote(st, arg("quote", ""));
  const quoteIs0 = q.isToken0;
  const token = q.token;
  const amountQuote = parseQ(arg("amount", "0"), q);
  if (amountQuote <= 0n) throw new Error(`--amount required (${q.symbol})`);
  const spacing = Number(st.tickSpacing);
  const tick = Number(st.tick);
  const bandTicks = Math.max(pctToTicks(rangePct), spacing);

  let tickLower, tickUpper, amount0 = 0n, amount1 = 0n, swapped = 0n;
  // Pool state the band is built from and the cost basis is priced at.
  // balanced_tight replaces it with a post-swap read; weth_below never swaps.
  let mintSt = st;

  if (strategy === "balanced_tight") {
    // Two-sided +/- rangePct band, half the quote asset swapped into the token
    // so both sides carry inventory.
    //
    // The swap goes FIRST and the band is centered on the tick it leaves behind,
    // because by mint time the tick read at the top of this function is stale on
    // two counts: our own buy moves a thin launch pool, and other traders move it
    // while our swap is in flight. #111130 (2026-07-14) centered a +/-953-tick
    // band on tick ~168150 and minted at 166042 — 2108 ticks away, of which our
    // 0.0015 WETH buy was 783 (-7.5%) and 18 seconds of market dump was the rest.
    // A range that no longer straddles the tick makes the mint take one token and
    // refund the other, so the position was born out-of-range earning no fees.
    const half = amountQuote / 2n;
    const spotOut = spotOutFor(half, st.sqrtPriceX96, quoteIs0);
    const minOut = (spotOut * BigInt(Math.floor((100 - slippagePct) * 100))) / 10000n;
    const balBefore = DRY_RUN ? 0n
      : await pub.readContract({ address: token, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
    await ensureAllowance(wallet, account.address, q.address, ROUTER, half);
    await send(wallet, {
      address: ROUTER, abi: routerAbi, functionName: "exactInputSingle",
      args: [{ tokenIn: q.address, tokenOut: token, fee: st.fee, recipient: account.address, amountIn: half, amountOutMinimum: minOut, sqrtPriceLimitX96: 0n }],
      account: wallet.account, chain,
    }, `swap ${fmtQ(half, q)} ${q.symbol} -> token`);
    swapped = half;

    if (!DRY_RUN) mintSt = await poolState(pool);
    const midTick = Number(mintSt.tick);
    const movedPct = (Math.pow(1.0001, midTick - tick) - 1) * 100;
    console.log(`entry impact: tick ${tick} -> ${midTick} (${movedPct >= 0 ? "+" : ""}${movedPct.toFixed(2)}% price) — band +/-${bandTicks} ticks around ${midTick}`);
    tickLower = roundToSpacing(midTick - bandTicks, spacing, false);
    tickUpper = roundToSpacing(midTick + bandTicks, spacing, true);

    // Only the tokens THIS swap bought are inventory. A leftover bag of the same
    // token from an earlier stranded exit is not ours to LP, and counting it
    // would inflate the cost basis with capital already written off.
    const balAfter = DRY_RUN ? spotOut
      : await pub.readContract({ address: token, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
    const tokenBal = balAfter - balBefore;
    if (quoteIs0) { amount0 = amountQuote - half; amount1 = tokenBal; }
    else { amount0 = tokenBal; amount1 = amountQuote - half; }
  } else if (strategy === "weth_below") {
    // One-sided quote-asset band adjacent to the current tick (bid side): no
    // swap, pure fee capture that converts to the token only if price crosses
    // in. This is rh-turnover's entry shape, and it is LITERALLY a ladder of
    // one — same ladderBands() call the wall uses, with rungs=1 — so the
    // direction invariant (quote-as-token0 fills as the tick RISES, so its band
    // sits above spot; quote-as-token1 the reverse) has exactly one
    // implementation on this venue rather than a second copy that can drift
    // out of agreement with uni_monitor.py's fill rule.
    //
    // Width comes from TURNOVER_RUNG_TICKS, not --range-pct. The band is not a
    // tolerance around a price we are betting on, it is the depth we are
    // willing to be traded into before re-pinning, and the monitor judges drift
    // against that same number. --range-pct is still accepted (and ignored)
    // here so the deploy contract stays one shape for every strategy.
    const rungTicks = parseInt(arg("rung-ticks", "") || turnoverGeom(q).rungTicks, 10);
    const [band] = ladderBands(tick, spacing, quoteIs0, 1, rungTicks);
    tickLower = band.tickLower;
    tickUpper = band.tickUpper;
    if (quoteIs0) amount0 = amountQuote; else amount1 = amountQuote;
    const { dropPct } = ladderSpan([band]);
    console.log(`turnover rung: [${tickLower},${tickUpper}] `
      + `${rungWidth(spacing, rungTicks)} ticks wide (spacing ${spacing}, requested ${rungTicks}) `
      + `— covers ${dropPct.toFixed(2)}% from spot tick ${tick}`);
  } else {
    throw new Error(`unknown strategy ${strategy}`);
  }

  await ensureAllowance(wallet, account.address, q.address, NPM, quoteIs0 ? amount0 : amount1);
  if (swapped > 0n) await ensureAllowance(wallet, account.address, token, NPM, quoteIs0 ? amount1 : amount0);

  const deadline = BigInt(Math.floor(Date.now() / 1000) + 120);
  // A two-sided strategy demands a two-sided fill: each side must take at least
  // MIN_FILL_PCT of what we offered, or the mint reverts and the funds stay in
  // the wallet where `sellTokenForQuote` below can put them back into the quote. A
  // one-sided strategy has a zero side by construction, so its mins stay 0.
  const twoSided = strategy === "balanced_tight";
  const minFill = (x) => (x * BigInt(Math.floor(MIN_FILL_PCT * 100))) / 10000n;
  const mintArgs = {
    token0: mintSt.token0, token1: mintSt.token1, fee: mintSt.fee,
    tickLower, tickUpper,
    amount0Desired: amount0, amount1Desired: amount1,
    amount0Min: twoSided ? minFill(amount0) : 0n,
    amount1Min: twoSided ? minFill(amount1) : 0n,
    recipient: account.address, deadline,
  };

  if (DRY_RUN) {
    console.log(`🧪 DRY RUN DEPLOY pool=${pool} strategy=${strategy} ticks=[${tickLower},${tickUpper}] amount=${fmtQ(amountQuote, q)} ${q.symbol}`);
    console.log(JSON.stringify({ success: true, dryRun: true, pool, strategy, tickLower, tickUpper, quoteSymbol: q.symbol }));
    return;
  }
  let hash, rcpt;
  try {
    hash = await wallet.writeContract({ address: NPM, abi: npmAbi, functionName: "mint", args: [mintArgs], account: wallet.account, chain });
    rcpt = await pub.waitForTransactionReceipt({ hash, timeout: 120_000 });
    if (rcpt.status !== "success") throw new Error(`mint reverted: ${hash}`);
  } catch (e) {
    // The mint never landed, so no position exists and the only capital at risk
    // is the token half we swapped into. Put it back into the quote asset rather
    // than leave an unmanaged bag the monitor knows nothing about; if even that
    // fails, hand it to the stranded journal so `sweep` keeps retrying.
    const reason = (e.shortMessage || e.message || "mint failed").split("\n")[0];
    console.error(`mint failed (no position opened): ${reason}`);
    let refund = null;
    if (swapped > 0n) {
      const bal = await pub.readContract({ address: token, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
      const sym = await pub.readContract({ address: token, abi: erc20Abi, functionName: "symbol" }).catch(() => "?");
      const r = await sellTokenForQuote(wallet, account, token, bal, Number(mintSt.fee), q);
      if (r.ok) {
        refund = { symbol: sym, quote_out: fmtQ(r.amountOut, q), quote_symbol: q.symbol };
        console.log(`refunded swap leg: sold ${sym} back for ${fmtQ(r.amountOut, q)} ${q.symbol}`);
      } else {
        refund = { symbol: sym, failed: r.reason };
        journalStranded({
          ts: Math.floor(Date.now() / 1000),
          timestamp: new Date().toISOString(),
          tokenId: null, token, symbol: sym, amount: bal.toString(),
          // The bag must be sold back to the SAME asset the entry was funded
          // in; sweep reads this to route a USDG position's bag to USDG.
          quote: q.address,
          reason: r.reason, resolved: false,
          attempts: 1, next_try: Math.floor(Date.now() / 1000) + retryDelay(1),
        });
        console.error(`warn: could not refund ${sym} swap leg (${r.reason}) — queued for sweep`);
      }
    }
    // Marker line for internal/robinhood.Summarize — a clean "we opened nothing
    // and put the money back" is a real outcome, not a crash, and the operator's
    // report should say so in words instead of leaking the JSON result line.
    const refundNote = refund
      ? (refund.quote_out ? `, refunded ${refund.quote_out} ${refund.quote_symbol}` : `, ${refund.symbol} REFUND FAILED (${refund.failed}) — queued for sweep`)
      : "";
    console.log(`❌ DEPLOY FAILED (no position opened): ${reason}${refundNote}`);
    console.log(JSON.stringify({
      success: false, error: `mint failed: ${reason}`,
      pool, strategy, tickLower, tickUpper, refund,
    }));
    return;
  }
  // Resolve tokenId from two independent sources; never journal "unknown" — an
  // orphaned entry disables the monitor's SL/TP for that position.
  let tokenId;
  try {
    tokenId = await resolveMintedTokenId(rcpt, account);
  } catch (e) {
    // Mint already landed on-chain; funds are committed. Surface the tx so the
    // operator can journal the cost basis by hand rather than lose it silently.
    console.error(`ERROR: mint ${hash} succeeded but tokenId unresolved: ${e.message}`);
    console.log(JSON.stringify({ success: false, error: "tokenId unresolved", pool, strategy, tickLower, tickUpper, tx: hash, quoteIn: fmtQ(amountQuote, q), quoteSymbol: q.symbol }));
    return;
  }
  // Cost basis = what the position ACTUALLY took, read from the mint's own
  // IncreaseLiquidity event, priced in WETH at the tick we minted at.
  //
  // It used to be the full WETH committed. But a mint only pulls the ratio its
  // range needs and refunds the rest to the wallet, so cmdState — which values
  // the position alone — measured a shrunken position against the whole commit
  // and reported a double-digit loss the instant the position opened. That is
  // enough to trip the monitor's emergency stop-loss, which deliberately
  // bypasses the age grace, so every position was closed within a tick or two of
  // being born (#106405/#106446/#111130, all "emergency SL" under 2 minutes old,
  // none ever reaching a positive peak). The refunded leftovers are still ours —
  // they sit in the wallet and cmdClose sells them out — so they belong nowhere
  // in this position's PnL.
  const inc = parseEventLogs({ abi: npmAbi, eventName: "IncreaseLiquidity", logs: rcpt.logs })
    .find((l) => l.args.tokenId.toString() === String(tokenId));
  if (!inc) {
    // Should not happen — NPM.mint always emits it — but falling back to the
    // full commit would resurrect the instant-stop-loss bug, so say so loudly.
    console.error("warn: no IncreaseLiquidity event in mint receipt — cost basis falls back to the full commit, which will overstate the loss");
  }
  const used0 = inc ? inc.args.amount0 : amount0;
  const used1 = inc ? inc.args.amount1 : amount1;
  const entryQuote = valueInQuote(used0, used1, mintSt.sqrtPriceX96, quoteIs0);
  const idleQuote = amountQuote - entryQuote;
  journalEntry({
    tokenId, pool, token0: st.token0, token1: st.token1, fee: Number(st.fee),
    tickLower, tickUpper, strategy,
    quote: q.address, quoteSymbol: q.symbol, quoteDecimals: q.decimals,
    quoteIn: fmtQ(entryQuote, q), wethIn: fmtQ(entryQuote, q),
    committedQuote: fmtQ(amountQuote, q),
    used0: used0.toString(), used1: used1.toString(),
    // Spot the band was built around — `mintSt` is the SAME sample both branches
    // laid their ticks from (post-swap for balanced_tight, the pre-mint read for
    // weth_below), so this is the price the position was centred on, not a
    // second read that has already moved. Drift is measured from here; a band
    // edge cannot serve, see the note in cmdDeployLadder's journal write.
    entryTick: Number(mintSt.tick),
    ts: Math.floor(Date.now() / 1000),
  });
  const inRange = Number(mintSt.tick) >= tickLower && Number(mintSt.tick) < tickUpper;
  console.log(`position value ${fmtQ(entryQuote, q)} ${q.symbol} of ${fmtQ(amountQuote, q)} committed `
    + `(${fmtQ(idleQuote, q)} left in wallet), ${inRange ? "IN range" : "OUT OF range"} at tick ${mintSt.tick}`);
  console.log(`🚀 DEPLOYED pool=${pool} strategy=${strategy} position=${tokenId} tx=${hash}`);
  console.log(JSON.stringify({
    success: true, pool, strategy, tokenId, tickLower, tickUpper, tx: hash,
    quote: q.address, quoteSymbol: q.symbol,
    quoteIn: fmtQ(entryQuote, q), committedQuote: fmtQ(amountQuote, q), inRange,
  }));
}

// cmdState prices one position for the monitor: current value IN THE POOL'S
// OWN QUOTE ASSET, PnL vs entry cost basis, in-range flag, age, and — since
// 2026-08-05 — the position's UNCOLLECTED FEES (`feesQuote`).
//
// `valueWeth` (quote units despite the name) is deliberately still
// PRINCIPAL-ONLY: principal from a simulated full decreaseLiquidity, which
// reuses the pool contract's own tick math, plus any already-poked tokensOwed.
// Its meaning is a contract with uni_monitor.py's SL/TP/trailing rules and with
// the entry cost basis it is compared against, so fees are reported ALONGSIDE
// it, never folded into it. Neither figure is ever cross-converted to WETH,
// because PnL is a ratio and a USDG position's ratio is honest in dollars and
// meaningless in ether.
//
// WHY FEES NEED THEIR OWN MEASUREMENT, and why the obvious ways don't work:
//
//  - NPM.positions().tokensOwed0/1 (p[10], p[11]) reads ZERO on a live
//    position no matter what it earned. tokensOwed is only written when the
//    position is poked (decrease/collect/burn); until then the fees exist as
//    feeGrowthInside deltas inside the POOL, not on the NFT.
//  - A standalone `collect` static-call is no better: with liquidity untouched
//    it also returns only the already-poked tokensOwed, i.e. 0.
//  - decreaseLiquidity alone returns the PRINCIPAL released. The accrued fees
//    are credited to tokensOwed inside that same call but are NOT part of its
//    return value — which is why this function reported "zero fees" for every
//    rung it ever priced, and why `ladder idle: zero fees` in the 2026-08-04/05
//    logs (17 ladder closes over ~40h) was a meter reading, not a measurement.
//  - decreaseLiquidity(0) as a "poke" is not portable — whether NPM reverts on
//    zero liquidity depends on the deployment, and a revert here would take the
//    value read down with it.
//
// So: ONE simulated NPM.multicall batching decreaseLiquidity(full) THEN
// collect(max). Both legs run against the same simulated state inside a single
// eth_call — same request budget as before, no extra RPC per position — and the
// collect leg sees the tokensOwed the decrease leg just credited:
//     result[0] -> (principal0, principal1)
//     result[1] -> (total0, total1) = tokensOwed_prior + principal + fees
//     fees = total - principal          (all uncollected fees, monotonic while
//                                        the position lives — nothing collects
//                                        mid-life except close, which burns)
// The bytes[] legs are decoded with viem's decodeFunctionResult against the
// same npmAbi that encoded them, so there is no second hand-written ABI to
// drift out of sync.
//
// FAILURE IS REPORTED, NEVER GUESSED. If the batched simulate throws (an NPM
// without Multicall, a chain that rejects it, an RPC that won't run it) this
// falls back to the old single decreaseLiquidity simulate so `valueWeth` — and
// with it every hard-risk rule — keeps working, and emits `feesQuote: null`.
// Null means "unmeasured" and makes uni_monitor.py fall through to its next
// meter; emitting 0 would be a lie that closes live, earning rungs.
async function cmdState(account) {
  const id = BigInt(arg("id", "0"));
  if (id <= 0n) throw new Error("--id required");
  const p = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "positions", args: [id] });
  const token0 = getAddress(p[2]), token1 = getAddress(p[3]), fee = p[4];
  const tickLower = Number(p[5]), tickUpper = Number(p[6]), liquidity = p[7];
  let owed0 = p[10], owed1 = p[11];

  const entry = readEntry(id);
  let pool = entry?.pool;
  if (!pool) {
    pool = await pub.readContract({ address: FACTORY, abi: factoryAbi, functionName: "getPool", args: [token0, token1, fee] });
  }
  pool = getAddress(pool);
  const st = await poolState(pool);
  // The journal's `quote` is authoritative — it records what the position was
  // actually funded with. Falls back to pool-side resolution for positions
  // minted before the field existed (all of them WETH).
  const q = resolveQuote(st, entry?.quote || "");
  const quoteIs0 = q.isToken0;
  // Pair label for operator-facing reports — the monitor's card names
  // positions "WETH / SYM", not by NPM tokenId.
  const tokenAddr = quoteIs0 ? token1 : token0;
  const tokenSymbol = await pub.readContract({
    address: tokenAddr, abi: erc20Abi, functionName: "symbol",
  }).catch(() => "?");

  let amount0 = owed0, amount1 = owed1;
  // Uncollected fees in RAW token units. Seeded with tokensOwed: with no
  // liquidity left to decrease nothing is accruing, so what is already poked
  // onto the NFT is the whole of it. null once measurement is attempted and
  // fails — see the header block on why null, not zero.
  let fees0 = owed0, fees1 = owed1;
  if (liquidity > 0n) {
    const deadline = BigInt(Math.floor(Date.now() / 1000) + 120);
    const decArgs = [{ tokenId: id, liquidity, amount0Min: 0n, amount1Min: 0n, deadline }];
    const colArgs = [{
      tokenId: id, recipient: account.address,
      amount0Max: maxUint128, amount1Max: maxUint128,
    }];
    try {
      // decrease THEN collect, one eth_call. Order is load-bearing: collect
      // first would return the (zero) tokensOwed of an un-poked position.
      const { result } = await pub.simulateContract({
        address: NPM, abi: npmAbi, functionName: "multicall",
        args: [[
          encodeFunctionData({ abi: npmAbi, functionName: "decreaseLiquidity", args: decArgs }),
          encodeFunctionData({ abi: npmAbi, functionName: "collect", args: colArgs }),
        ]],
        account: account.address,
      });
      const [principal0, principal1] = decodeFunctionResult({
        abi: npmAbi, functionName: "decreaseLiquidity", data: result[0],
      });
      const [total0, total1] = decodeFunctionResult({
        abi: npmAbi, functionName: "collect", data: result[1],
      });
      amount0 += principal0;
      amount1 += principal1;
      // Clamped rather than trusted: an NPM whose collect somehow returns less
      // than the principal it was just handed is a shape we do not understand,
      // and a negative BigInt would print as a fee CREDIT and hold a dead rung
      // open forever.
      fees0 = total0 > principal0 ? total0 - principal0 : 0n;
      fees1 = total1 > principal1 ? total1 - principal1 : 0n;
    } catch (e) {
      // Fall back to the pre-2026-08-05 read so the value figure (and every
      // hard-risk rule that depends on it) survives a venue that cannot run the
      // batch. The fee meter goes dark, loudly.
      const reason = (e.shortMessage || e.message || "multicall simulate failed").split("\n")[0];
      console.error(`warn: batched fee simulate failed (${reason}) — fees UNMEASURED for #${id}`);
      const { result } = await pub.simulateContract({
        address: NPM, abi: npmAbi, functionName: "decreaseLiquidity",
        args: decArgs, account: account.address,
      });
      amount0 += result[0];
      amount1 += result[1];
      fees0 = null;
      fees1 = null;
    }
  }

  const valueRaw = valueInQuote(amount0, amount1, st.sqrtPriceX96, quoteIs0);
  const valueQuote = Number(fmtQ(valueRaw, q));
  // Fees priced in the quote at spot, exactly like value — so feesQuote and
  // valueWeth are the same unit and their ratio is the fee yield the idle rule
  // wants. fmtQ, never formatEther: a 6-decimal USDG fee through formatEther
  // reads as 0.000000000001 of a dollar and every stock rung looks fee-dead.
  const feesQuote = (fees0 === null || fees1 === null)
    ? null
    : Number(fmtQ(valueInQuote(fees0, fees1, st.sqrtPriceX96, quoteIs0), q));
  const entryQuote = entry ? Number(entry.quoteIn ?? entry.wethIn)
    : (arg("entry-weth", "") ? Number(arg("entry-weth")) : null);
  const pnlPct = entryQuote ? ((valueQuote - entryQuote) / entryQuote) * 100 : null;
  const tick = Number(st.tick);
  const inRange = tick >= tickLower && tick < tickUpper;
  const ageMin = entry ? (Math.floor(Date.now() / 1000) - entry.ts) / 60 : null;

  console.log(JSON.stringify({
    tokenId: id.toString(), pool, pair: `${q.symbol} / ${tokenSymbol}`,
    token: tokenAddr, tokenSymbol,
    tick, tickLower, tickUpper, inRange, liquidity: liquidity.toString(),
    // quoteSymbol tells uni_monitor.py what unit the two value fields are in —
    // it converts ETH-quoted PnL to dollars and leaves USDG-quoted PnL alone.
    // valueWeth/entryWeth keep their names (the monitor's field contract, and
    // the v4 executor's) but hold QUOTE units, never a WETH conversion.
    quote: q.address, quoteSymbol: q.symbol,
    valueWeth: valueQuote, entryWeth: entryQuote, pnlPct, ageMin,
    // Uncollected fees in the SAME quote units as valueWeth, measured on-chain
    // (see the header block). This is the only fee figure this venue can
    // produce without a third party, and it is what uni_monitor.py's `ladder
    // idle` rule falls back to when Krystal is down — which, on 2026-08-05, it
    // was (HTTP 521 + read timeouts) for the whole soak that judged 17 ladders
    // "zero fees". null = unmeasured, NOT zero.
    feesQuote,
    // Ladder metadata, echoed from the entry journal so uni_monitor.py can tell
    // a resting bid rung from a normal position WITHOUT reading the journal
    // itself. It matters because the two need opposite exit rules: a ladder
    // rung is out-of-range BY DESIGN, so the fee-dead OOR timeout that protects
    // a balanced_tight position would close every rung 30 minutes after it was
    // minted. `rung` (0 = nearest spot) and `rungs` let the monitor separate
    // real price drift from the rung's own intended offset.
    strategy: entry?.strategy || null,
    ladderId: entry?.ladderId || null,
    rung: entry?.rung ?? null,
    rungs: entry?.rungs ?? null,
    // The pin this position was centred on, and the pool's tick quantum. Both
    // exist for one rule: drift. `entryTick` gives it an exact zero; where it is
    // missing (every position minted before 2026-08-07) `tickSpacing` lets
    // uni_monitor.py subtract the band's WORST-CASE birth offset instead of
    // reading it as a move the market never made.
    entryTick: entry?.entryTick ?? null,
    tickSpacing: Number(st.tickSpacing),
    // quoteIs0 is what ladder_decide reads to know which tick direction fills
    // a rung; wethIs0 stays as its pre-USDG alias so an older monitor build
    // against a WETH ladder keeps working.
    quoteIs0,
    wethIs0: quoteIs0,
  }));
}

async function cmdPositions(account) {
  const n = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "balanceOf", args: [account.address] });
  const out = [];
  for (let i = 0n; i < n; i++) {
    const id = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "tokenOfOwnerByIndex", args: [account.address, i] });
    const p = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "positions", args: [id] });
    out.push({
      tokenId: id.toString(), token0: p[2], token1: p[3], fee: Number(p[4]),
      tickLower: Number(p[5]), tickUpper: Number(p[6]), liquidity: p[7].toString(),
      owed0: p[10].toString(), owed1: p[11].toString(),
    });
  }
  // `count` is NFTs, `ladders` is distinct funded pools. Under weth_ladder one
  // entry is N NFTs, so a cap expressed in NFTs would let a single ladder
  // exhaust the position budget. The scanner caps on `ladders`; `count` stays
  // for backwards compatibility and for the balanced_tight era where the two
  // are equal. Rungs drained to zero liquidity don't count — they hold nothing.
  const ladders = new Set(
    out.filter((p) => p.liquidity !== "0")
      .map((p) => `${p.token0}-${p.token1}-${p.fee}`.toLowerCase()),
  ).size;
  console.log(JSON.stringify({ address: account.address, count: Number(n), ladders, positions: out }));
}

async function cmdCollect(wallet, account) {
  const id = BigInt(arg("id", "0"));
  if (id <= 0n) throw new Error("--id required");
  await ensureGas(wallet, account);
  await send(wallet, {
    address: NPM, abi: npmAbi, functionName: "collect",
    args: [{ tokenId: id, recipient: account.address, amount0Max: maxUint128, amount1Max: maxUint128 }],
    account: wallet.account, chain,
  }, `collect #${id}`);
  console.log(JSON.stringify({ success: true, tokenId: id.toString() }));
}

async function cmdClose(wallet, account) {
  const id = BigInt(arg("id", "0"));
  if (id <= 0n) throw new Error("--id required");
  // Close authority guard, mirroring the Solana executor's DLMM_CLOSE_AUTH:
  // uni_monitor.py is the only authorized closer (it owns the exit rulebook),
  // so a bare `close` from anywhere else is rejected unless the operator
  // passes --force for an explicit manual close. Prevents the deploy Runner or
  // a stray script from unwinding a live position outside the exit rules.
  if (!DRY_RUN && process.env.UNI_CLOSE_AUTH !== "1" && !hasFlag("force")) {
    throw new Error("close requires UNI_CLOSE_AUTH=1 (monitor) or --force (manual)");
  }
  // A close is the one command that must never fail for want of gas — it is how
  // a losing position stops losing. Top up first, from the WETH the wallet is
  // already holding.
  const gasTopup = await ensureGas(wallet, account);
  const p = await pub.readContract({ address: NPM, abi: npmAbi, functionName: "positions", args: [id] });
  const [token0, token1, liquidity] = [getAddress(p[2]), getAddress(p[3]), p[7]];
  const deadline = BigInt(Math.floor(Date.now() / 1000) + 120);

  // Which asset this position must be unwound INTO, resolved BEFORE the
  // decrease so the quote the position itself pays back can be measured. The
  // token-side sell below reads the same `q`.
  const entry = readEntry(id);
  const q = resolveQuote({ token0, token1 }, entry?.quote || "");

  // Quote held before the unwind, so decrease+collect's payout can be read as a
  // balance delta — the same measurement the token side already uses below.
  //
  // This exists because a ONE-SIDED quote position (weth_below, every ladder
  // rung) closes with nothing to sell, and reporting only the swap proceeds
  // said its entire ticket had evaporated. Live proof, 2026-08-07: turnover
  // position #616818 paid back its full 0.017466515519518273 WETH on-chain
  // (DecreaseLiquidity/Collect amount0, amount1 = 0) and still printed
  // weth_out "0". uni_monitor.py books that number as realized PnL, so the
  // re-center circuit breaker recorded -0.0175 against the pool and declined
  // every future re-center of it — disabling the one loop this thesis runs on.
  const quoteBefore = DRY_RUN ? 0n
    : await pub.readContract({ address: q.address, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });

  if (liquidity > 0n) {
    await send(wallet, {
      address: NPM, abi: npmAbi, functionName: "decreaseLiquidity",
      args: [{ tokenId: id, liquidity, amount0Min: 0n, amount1Min: 0n, deadline }],
      account: wallet.account, chain,
    }, `decrease #${id}`);
  }
  await send(wallet, {
    address: NPM, abi: npmAbi, functionName: "collect",
    args: [{ tokenId: id, recipient: account.address, amount0Max: maxUint128, amount1Max: maxUint128 }],
    account: wallet.account, chain,
  }, `collect #${id}`);
  await send(wallet, { address: NPM, abi: npmAbi, functionName: "burn", args: [id], account: wallet.account, chain }, `burn #${id}`);

  // Measured HERE — after collect, before the token-side sell — so this is the
  // position's own payout (principal + fees) and not the swap's.
  const quoteFromPosition = DRY_RUN ? 0n
    : (await pub.readContract({ address: q.address, abi: erc20Abi, functionName: "balanceOf", args: [account.address] })) - quoteBefore;

  // Sell the freed token side back to the position's quote asset unless told
  // otherwise, mirroring the Solana monitor's auto-swap-to-SOL on close.
  //
  // The position is already burned by this point, so the sell must NOT be able
  // to fail the close. It used to: a revert here (rugged pool, sell tax) threw
  // out of cmdClose before it printed its result, so uni_monitor.py journaled
  // success=false on a position that was in fact gone — and the tokens sat in
  // the wallet forever with nothing to retry them. 4 of the first 9 live closes
  // stranded their bag that way. Now the sell reports itself instead: the close
  // is a success (it is — the liquidity is out), and an unsold bag becomes a
  // stranded-journal entry for `sweep` to keep retrying.
  let sold = null;
  let stranded = null;
  // Which asset to sell back INTO: the entry journal's quote if this position
  // has one (a USDG ladder must not be unwound into WETH — that would leave
  // the strategy's capital in the wrong asset and the next deploy unfunded),
  // else the pool's own quote side.
  if (!hasFlag("no-swap-out") && !DRY_RUN) {
    const token = q.token;
    const bal = await pub.readContract({ address: token, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
    if (bal > 0n) {
      const sym = await pub.readContract({ address: token, abi: erc20Abi, functionName: "symbol" }).catch(() => "?");
      const r = await sellTokenForQuote(wallet, account, token, bal, Number(p[4]), q);
      if (r.ok) {
        sold = { token, symbol: sym, quote_out: fmtQ(r.amountOut, q), fee: r.fee, tx: r.tx };
      } else {
        stranded = {
          tokenId: id.toString(), token, symbol: sym, amount: bal.toString(),
          quote: q.address,
          reason: r.reason, resolved: false,
          attempts: 1, next_try: Math.floor(Date.now() / 1000) + retryDelay(1),
        };
        journalStranded(stranded);
        console.error(`warn: could not sell ${sym} on close #${id} — ${r.reason} (bag journaled for sweep)`);
      }
    }
  }
  // Sum in base units, format once: adding two decimal strings would round the
  // 6-decimal quote's cents away (the parseQ/fmtQ rule this file follows).
  const totalQuoteOut = fmtQ(quoteFromPosition + (sold ? parseQ(sold.quote_out, q) : 0n), q);

  console.log(JSON.stringify({
    success: true, closed: id.toString(),
    swapped_out: !!sold,
    // weth_out keeps its name for uni_monitor.py's close journal (and the v4
    // executor prints the same pair of fields); quote_symbol is what says
    // whether those digits are ether or dollars.
    //
    // Both halves of the unwind, NOT just the sell: the position's own payout
    // plus whatever the token side fetched. The two are broken out beside it
    // because they answer different questions — a close where the position
    // returned everything and sold nothing is a rung that was never traded
    // into, while a close that is all swap proceeds is a rung that filled.
    weth_out: totalQuoteOut,
    quote_out: totalQuoteOut,
    quote_from_position: fmtQ(quoteFromPosition, q),
    quote_from_swap: sold ? sold.quote_out : "0",
    quote_symbol: q.symbol,
    stranded,
    gas_topup: gasTopup,
  }));
}

// cmdSweep retries the exit sell for every bag the close path could not unload.
// Run every monitor tick: a pool that was dead at close time can be revived by
// another LP, and a sell that reverted on a transient can just work next time.
async function cmdSweep(wallet, account) {
  const only = arg("token", "");
  let bags = openStranded();
  // Cheap when there is nothing to sell: skip the gas preflight's two RPC reads
  // on the empty path, which is most ticks.
  if (bags.length || only) await ensureGas(wallet, account);
  if (only) {
    const t = getAddress(only);
    const known = bags.find((b) => getAddress(b.token) === t);
    if (known) {
      bags = [known];
    } else {
      // An operator sweeping a token by hand is asserting it IS stranded, so
      // adopt it into the journal before trying to sell. If this sell fails the
      // monitor's per-tick sweep inherits it and keeps retrying — a manual
      // attempt should never be the only attempt.
      const [sym, bal] = await Promise.all([
        pub.readContract({ address: t, abi: erc20Abi, functionName: "symbol" }).catch(() => "?"),
        pub.readContract({ address: t, abi: erc20Abi, functionName: "balanceOf", args: [account.address] }),
      ]);
      const bag = { tokenId: null, token: t, symbol: sym, amount: bal.toString(), reason: "adopted by manual sweep", resolved: false };
      journalStranded(bag);
      bags = [bag];
    }
  }

  const now = Math.floor(Date.now() / 1000);
  const results = [];
  let waiting = 0;
  for (const bag of bags) {
    // An explicit --token sweep is the operator overriding the schedule, so it
    // ignores the backoff. The per-tick sweep respects it.
    if (!only && bag.next_try && bag.next_try > now) { waiting++; continue; }

    const token = getAddress(bag.token);
    const bal = await pub.readContract({ address: token, abi: erc20Abi, functionName: "balanceOf", args: [account.address] });
    if (bal === 0n) {
      // Sold or moved by hand — retire it so the sweep stops retrying forever.
      journalStranded({ ...bag, amount: "0", resolved: true, note: "balance is zero" });
      results.push({ token, symbol: bag.symbol, resolved: true, weth_out: "0", note: "balance is zero" });
      continue;
    }
    if (DRY_RUN) {
      results.push({ token, symbol: bag.symbol, dry_run: true, amount: bal.toString() });
      continue;
    }
    // Bags journaled by a USDG position carry their quote; older lines and
    // manual adoptions have none and sell back to WETH as they always did.
    const bq = QUOTES[bag.quote ? getAddress(bag.quote) : WETH] || QUOTES[WETH];
    const r = await sellTokenForQuote(wallet, account, token, bal, bag.fee ?? null, bq);
    if (r.ok) {
      const out = fmtQ(r.amountOut, bq);
      journalStranded({ ...bag, amount: bal.toString(), resolved: true, weth_out: out, quote_symbol: bq.symbol, fee: r.fee, tx: r.tx });
      results.push({ token, symbol: bag.symbol, resolved: true, weth_out: out, quote_symbol: bq.symbol, fee: r.fee, tx: r.tx });
    } else {
      const attempts = (bag.attempts || 0) + 1;
      const delay = retryDelay(attempts);
      journalStranded({ ...bag, amount: bal.toString(), reason: r.reason, resolved: false, attempts, next_try: now + delay });
      results.push({ token, symbol: bag.symbol, resolved: false, amount: bal.toString(), reason: r.reason, attempts, retry_in_s: delay });
    }
  }
  const recovered = results.filter((r) => r.resolved && r.weth_out !== "0");
  // Totals are per quote asset — WETH and USDG recoveries in one sweep must
  // never be added together, and 6-decimal dollars would round to nothing at
  // WETH's precision anyway.
  const byQuote = {};
  for (const r of recovered) {
    const sym = r.quote_symbol || "WETH";
    byQuote[sym] = (byQuote[sym] || 0) + parseFloat(r.weth_out);
  }
  console.log(JSON.stringify({
    success: true,
    swept: results.length,
    backing_off: waiting,
    recovered_weth: (byQuote.WETH || 0).toFixed(6),
    recovered: Object.fromEntries(Object.entries(byQuote).map(([s, v]) => [s, v.toFixed(s === "WETH" ? 6 : 2)])),
    still_stranded: results.filter((r) => r.resolved === false).length,
    results,
  }));
}

async function main() {
  const cmd = process.argv[2];
  const account = getAccount();
  const wallet = createWalletClient({ account, chain, transport: http(RPC_URL) });
  switch (cmd) {
    case "address": return cmdAddress(account);
    case "balance": return cmdBalance(account);
    case "wrap": return cmdWrap(wallet);
    case "quote": return cmdQuote();
    case "deploy": return cmdDeploy(wallet, account);
    case "positions": return cmdPositions(account);
    case "state": return cmdState(account);
    case "collect": return cmdCollect(wallet, account);
    case "close": return cmdClose(wallet, account);
    case "sweep": return cmdSweep(wallet, account);
    case "unwrap": return cmdUnwrap(wallet, account);
    case "gas-topup": return cmdGasTopup(wallet, account);
    default:
      console.error("usage: uni_executor.js address|balance|wrap|unwrap|gas-topup|quote|deploy|positions|state|collect|close|sweep [--flags]");
      process.exit(2);
  }
}

main().catch((e) => {
  console.log(JSON.stringify({ success: false, error: e.shortMessage || e.message }));
  process.exit(1);
});
