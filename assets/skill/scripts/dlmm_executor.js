const { Connection, Keypair, PublicKey, VersionedTransaction, Transaction } = require("@solana/web3.js");
const DLMM = require("@meteora-ag/dlmm");
const { StrategyType } = require("@meteora-ag/dlmm");
const BN = require("bn.js");
const bs58 = require("bs58");
const dotenv = require("dotenv");
const fs = require("fs");
const path = require("path");
const net = require("net");

// Resolved from the invoked path (process.argv[1]), NOT __dirname — Node always
// realpaths __dirname/__filename through symlinks, which would resolve to this repo
// instead of the profile when scripts/ is symlinked into a Hermes profile.
// process.argv[1] is the literal path the process was launched with, untouched.
const SCRIPT_DIR = path.dirname(path.isAbsolute(process.argv[1]) ? process.argv[1] : path.resolve(process.argv[1]));
const PROFILE_DIR = path.dirname(path.dirname(path.dirname(SCRIPT_DIR)));

// Load environment variables
const profileEnvPath = path.join(PROFILE_DIR, ".env");
const legacyEnvPath = path.join(PROFILE_DIR, ".env");

if (fs.existsSync(profileEnvPath)) {
  dotenv.config({ path: profileEnvPath });
}
if (fs.existsSync(legacyEnvPath)) {
  const legacyEnv = dotenv.parse(fs.readFileSync(legacyEnvPath));
  for (const k in legacyEnv) {
    if (!process.env[k]) process.env[k] = legacyEnv[k];
  }
}

// Comma-separated list of RPC endpoints, tried in order with failover on error.
// Set SOLANA_RPC_URLS in <profile>/.env — put your own Helius/QuickNode/etc. keys
// there, never hardcode them here (this repo is public).
const RPC_URLS = (process.env.SOLANA_RPC_URLS || "https://api.mainnet-beta.solana.com")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const RPC_SEND_MAX_RETRIES = Math.max(2, Number.parseInt(process.env.SOLANA_RPC_MAX_RETRIES || "20", 10) || 20);
const CONFIRM_OPTIONS = { commitment: "confirmed", preflightCommitment: "confirmed", maxRetries: RPC_SEND_MAX_RETRIES };

let currentRpcIndex = 0;

function getWallet() {
  const pk = process.env.SOLANA_PRIVATE_KEY || process.env.WALLET_PRIVATE_KEY;
  if (!pk) {
    throw new Error("Solana private key not found in environment (checked SOLANA_PRIVATE_KEY and WALLET_PRIVATE_KEY)");
  }
  try {
    return Keypair.fromSecretKey(bs58.decode(pk.trim()));
  } catch (err) {
    // Try raw bytes parse if base58 fails
    try {
      return Keypair.fromSecretKey(Uint8Array.from(JSON.parse(pk)));
    } catch {
      throw new Error(`Failed to decode private key: ${err.message}`);
    }
  }
}

async function runWithFailover(fn) {
  let attempts = 0;
  while (attempts < RPC_URLS.length) {
    const rpcUrl = RPC_URLS[currentRpcIndex];
    try {
      const connection = new Connection(rpcUrl, { commitment: "confirmed", disableRetryOnRateLimit: true,
        fetch: (url, options) => fetch(url, { ...options, signal: AbortSignal.timeout(8000) }) });
      return await fn(connection);
    } catch (err) {
      if (err.message?.startsWith("ENTRY REFUSED:") || err.message?.startsWith("Rent reclaim refused:")) throw err;
      console.warn(`[RPC WARN] Failed execution on RPC #${currentRpcIndex}: ${err.message}`);
      currentRpcIndex = (currentRpcIndex + 1) % RPC_URLS.length;
      attempts++;
    }
  }
  throw new Error(`All ${RPC_URLS.length} RPC endpoints failed to execute the command.`);
}

// Durable accounting evidence is written before broadcast, including uncertain sends.
function recordSubmission(wallet, position, kind, signature, lastValidBlockHeight, swapQuote = null) {
  try {
    let context = {};
    if (position) {
      if (path.basename(position) !== position) throw new Error("Invalid position address");
      const file = path.join(PROFILE_DIR, "memories", "dlmm_entries", `${position}.json`);
      if (fs.existsSync(file)) context = JSON.parse(fs.readFileSync(file, "utf8"));
    }
    const dir = path.join(PROFILE_DIR, "memories");
    fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
    fs.appendFileSync(path.join(dir, "dlmm_transactions.jsonl"), JSON.stringify({
      ts: Math.floor(Date.now() / 1000), wallet: wallet.publicKey.toString(),
      position: position || null, root_chain_id: context.root_chain_id || context.recenter_of || position || null,
      entry_id: kind === "rent_reclaim" ? null : context.entry_id || process.env.DLMM_ENTRY_ID || null, kind, signature, lastValidBlockHeight,
      ...(kind === "swap" && swapQuote ? { swap_quote: swapQuote } : {}),
    }) + "\n", { mode: 0o600, flush: kind === "rent_reclaim" || kind === "swap" });
  } catch (err) {
    if (kind === "deploy" || kind === "rent_reclaim") throw err;
    // Accounting storage must not prevent an exit or liquidation.
    console.warn(`[ACCOUNTING] Recording failed for ${kind} ${signature}; coverage incomplete`);
  }
}

async function recordedClaim(connection, tx, wallet, position) {
  const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
  tx.recentBlockhash = blockhash;
  tx.feePayer = wallet.publicKey;
  tx.sign(wallet);
  const raw = tx.serialize();
  recordSubmission(wallet, position, "claim", bs58.encode(tx.signature), lastValidBlockHeight);
  const signature = await connection.sendRawTransaction(raw, CONFIRM_OPTIONS);
  await confirmSignedTransaction(connection, { signature, blockhash, lastValidBlockHeight });
  return signature;
}

// Confirm the signed transaction before treating a timeout as a failed send.
async function confirmSignedTransaction(connection, strategy) {
  console.warn(`[TX] ${JSON.stringify({stage: "confirm", ...strategy})}`);
  let confirmation;
  try {
    confirmation = await connection.confirmTransaction({ ...strategy, abortSignal: AbortSignal.timeout(8000) }, "confirmed");
  } catch (err) {
    const status = (await connection.getSignatureStatuses(
      [strategy.signature], { searchTransactionHistory: true }
    )).value[0];
    console.warn(`[TX] ${JSON.stringify({stage: "reconcile", signature: strategy.signature,
      status: status?.confirmationStatus || "unknown", chainError: status?.err || null})}`);
    if (!status || !["confirmed", "finalized"].includes(status.confirmationStatus)) throw err;
    confirmation = { value: { err: status.err } };
  }
  if (confirmation.value.err) throw new Error(`Transaction failed: ${JSON.stringify(confirmation.value.err)}`);
}

async function getActiveBin(poolAddressStr) {
  return await runWithFailover(async (connection) => {
    const pool = await DLMM.create(connection, new PublicKey(poolAddressStr));
    const activeBin = await pool.getActiveBin();
    const price = pool.fromPricePerLamport(Number(activeBin.price));
    return {
      binId: activeBin.binId,
      price: price,
      pricePerLamport: activeBin.price.toString()
    };
  });
}

async function getTokenDecimals(connection, mintPubKey) {
  if (mintPubKey.toString() === "So11111111111111111111111111111111111111112") {
    return 9;
  }
  try {
    const info = await connection.getParsedAccountInfo(mintPubKey);
    return info.value?.data?.parsed?.info?.decimals ?? 9;
  } catch (err) {
    console.warn(`Failed to get decimals for ${mintPubKey.toString()}, defaulting to 9: ${err.message}`);
    return 9;
  }
}

function getDlmmProgramId() {
  return new PublicKey("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo");
}

function formatSolFee(value) {
  const number = Number(value ?? 0);
  return Number.isFinite(number) ? number.toFixed(8).replace(/0+$/, "").replace(/\.$/, "") : "unknown";
}

// Read-only inspection of whether a price range can be deployed into without
// paying to initialize new Meteora bin arrays / bitmap extension. Spends nothing.
// Returns { deployable, missing, totalFee, needsBitmap, bitmapFee, missingSample }.
// Throws only if the SDK helpers are unavailable (cannot verify -> caller decides).
async function inspectBinArrayCoverage(connection, pool, minBinId, maxBinId) {
  const getBinArrayKeysCoverage = DLMM.getBinArrayKeysCoverage;
  const getBinArrayIndexesCoverage = DLMM.getBinArrayIndexesCoverage;
  const deriveBinArrayBitmapExtension = DLMM.deriveBinArrayBitmapExtension;
  const isOverflowDefaultBinArrayBitmap = DLMM.isOverflowDefaultBinArrayBitmap;
  const BIN_ARRAY_FEE = Number(DLMM.BIN_ARRAY_FEE ?? 0.07143744);
  const BIN_ARRAY_BITMAP_FEE = Number(DLMM.BIN_ARRAY_BITMAP_FEE ?? 0.01180416);

  if (!getBinArrayKeysCoverage || !getBinArrayIndexesCoverage) {
    throw new Error("Cannot verify Meteora bin-array initialization risk; SDK helpers unavailable.");
  }

  const programId = getDlmmProgramId();
  const poolPubkey = pool.pubkey;
  const lower = new BN(Math.min(minBinId, maxBinId));
  const upper = new BN(Math.max(minBinId, maxBinId));
  const indexes = getBinArrayIndexesCoverage(lower, upper);
  const keys = getBinArrayKeysCoverage(lower, upper, poolPubkey, programId);
  const accounts = await connection.getMultipleAccountsInfo(keys, "confirmed");
  const missing = accounts
    .map((account, index) => account ? null : {
      index: indexes[index]?.toString?.() ?? String(index),
      address: keys[index].toString(),
    })
    .filter(Boolean);

  let needsBitmap = false;
  if (deriveBinArrayBitmapExtension && isOverflowDefaultBinArrayBitmap) {
    const overflow = indexes.some((index) => isOverflowDefaultBinArrayBitmap(index));
    if (overflow) {
      const [bitmapExtension] = deriveBinArrayBitmapExtension(poolPubkey, programId);
      const account = await connection.getAccountInfo(bitmapExtension, "confirmed");
      needsBitmap = !account;
    }
  }

  const totalFee = missing.length * BIN_ARRAY_FEE + (needsBitmap ? BIN_ARRAY_BITMAP_FEE : 0);
  return {
    deployable: missing.length === 0 && !needsBitmap,
    missing: missing.length,
    totalFee,
    binArrayFee: BIN_ARRAY_FEE,
    needsBitmap,
    bitmapFee: BIN_ARRAY_BITMAP_FEE,
    missingSample: missing.slice(0, 3).map((e) => `${e.index}:${e.address.slice(0, 8)}`),
  };
}

async function assertRangeDoesNotRequireBinArrayInitialization(connection, pool, minBinId, maxBinId) {
  const cov = await inspectBinArrayCoverage(connection, pool, minBinId, maxBinId);
  if (cov.missing > 0) {
    const sample = cov.missingSample.join(", ");
    throw new Error(
      `Deploy skipped: selected range requires ${cov.missing} missing Meteora bin-array initialization(s) ` +
      `(~${formatSolFee(cov.missing * cov.binArrayFee)} SOL non-refundable pool rent; ${formatSolFee(cov.binArrayFee)} SOL each). ` +
      `Missing indexes: ${sample}${cov.missing > 3 ? ", ..." : ""}. Pick an already-initialized range/pool.`
    );
  }
  if (cov.needsBitmap) {
    throw new Error(
      `Deploy skipped: selected range requires Meteora bin-array bitmap extension initialization ` +
      `(~${formatSolFee(cov.bitmapFee)} SOL non-refundable pool rent). Pick a closer initialized range/pool.`
    );
  }
}

// Read-only: resolve a pool's active bin, then report bin-array coverage for the
// range [activeBin - binsBelow, activeBin + binsAbove]. No spend.
async function checkBinCoverage(poolAddressStr, binsBelow, binsAbove) {
  return await runWithFailover(async (connection) => {
    const pool = await DLMM.create(connection, new PublicKey(poolAddressStr));
    const activeBin = await pool.getActiveBin();
    const minBinId = activeBin.binId - binsBelow;
    const maxBinId = activeBin.binId + binsAbove;
    const cov = await inspectBinArrayCoverage(connection, pool, minBinId, maxBinId);
    return { success: true, pool: poolAddressStr, activeBin: activeBin.binId, minBinId, maxBinId, ...cov };
  });
}

// ponytail: one deployment per wallet on this host; use a distributed lock
// if a wallet is ever traded from multiple hosts. Same kernel-lock pattern as
// uni_ladder: no stale PID files or lease expiry while a send is still running.
async function acquireDeployLock(walletAddress) {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(`\0azimuth-dlmm-entry-${walletAddress}`, resolve);
  }).catch((err) => {
    if (err.code === "EADDRINUSE") throw new Error("ENTRY BUSY: another deploy is active for this wallet");
    throw err;
  });
  return () => new Promise((resolve) => server.close(resolve));
}

async function acquireSwapLock(walletAddress) {
  const server = net.createServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(`\0azimuth-dlmm-swap-${walletAddress}`, resolve);
  }).catch((err) => {
    if (err.code === "EADDRINUSE") throw new Error("SWAP BUSY: another matching swap is active for this wallet");
    throw err;
  });
  return () => new Promise((resolve) => server.close(resolve));
}

async function reconcilePendingSwap(connection, pendingPath, label = "Swap") {
  if (!fs.existsSync(pendingPath)) return null;
  let pending;
  try {
    pending = JSON.parse(fs.readFileSync(pendingPath, "utf8"));
  } catch (err) {
    return { success: false, pending: true, error: `${label} reconciliation blocked by invalid marker: ${err.message}` };
  }
  const finalizedHeight = await connection.getBlockHeight("finalized");
  const status = (await connection.getSignatureStatuses(
    [pending.signature], { searchTransactionHistory: true }
  )).value[0];
  if (status?.err) {
    fs.rmSync(pendingPath, { force: true });
    return null;
  }
  if (status && ["confirmed", "finalized"].includes(status.confirmationStatus)) {
    fs.rmSync(pendingPath, { force: true });
    return { success: true, reconciled: true, txHash: pending.signature,
      inputAmount: pending.inputAmount, outputAmount: pending.outputAmount };
  }
  if (status || !Number.isSafeInteger(pending.lastValidBlockHeight)
      || finalizedHeight <= pending.lastValidBlockHeight) {
    return { success: false, pending: true, txHash: pending.signature,
      error: `${label} confirmation pending from a previous submission` };
  }
  fs.rmSync(pendingPath, { force: true });
  return null;
}

// Manual maintenance only. Token-2022/extensions and wrapped SOL are deliberately
// excluded. The SPL program also rejects closure if tokens arrive after this read.
async function reclaimEmptyAccounts(execute = false) {
  const { TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID, createCloseAccountInstruction } = require("@solana/spl-token");
  const wallet = getWallet(), owner = wallet.publicKey.toString();
  const releaseEntry = await acquireDeployLock(owner);
  let releaseSwap;
  try {
    releaseSwap = await acquireSwapLock(owner);
    const pendingPath = path.join(PROFILE_DIR, "memories", "dlmm_pending_rent", `${owner}.json`);
    // Read failover is safe. Broadcast below runs once, on this connection only.
    const state = await runWithFailover(async connection => {
      const pending = await reconcilePendingSwap(connection, pendingPath, "Rent reclaim");
      if (pending) return { pending };
      const finalizedHeight = await connection.getBlockHeight("finalized");
      for (const name of ["dlmm_pending_swaps", "dlmm_pending_deploys"]) {
        const dir = path.join(PROFILE_DIR, "memories", name);
        for (const file of fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith(".json")) : []) {
          const marker = JSON.parse(fs.readFileSync(path.join(dir, file), "utf8"));
          if (!Number.isSafeInteger(marker.lastValidBlockHeight) || finalizedHeight <= marker.lastValidBlockHeight) {
            throw new Error("Rent reclaim refused: wait for pending trading blockhash expiry");
          }
        }
      }
      const excluded = new Set(["So11111111111111111111111111111111111111112"]);
      const positions = await DLMM.getAllLbPairPositionsByUser(connection, wallet.publicKey);
      for (const [address, data] of positions) {
        if (!data.lbPairPositionsData.length) continue;
        const pool = await DLMM.create(connection, new PublicKey(address));
        excluded.add(pool.lbPair.tokenXMint.toString());
        excluded.add(pool.lbPair.tokenYMint.toString());
      }
      const candidates = [];
      for (const programId of [TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID]) {
        const response = await connection.getParsedTokenAccountsByOwner(wallet.publicKey, { programId }, "finalized");
        candidates.push(...response.value.filter(a => a.account.owner.toString() === programId.toString()));
      }
      const accounts = candidates.filter(({ account }) => {
        const info = account.data?.parsed?.info;
        const extensions = info?.extensions;
        const supported = account.owner.toString() === TOKEN_PROGRAM_ID.toString()
          || Array.isArray(extensions) && extensions.length === 1 && extensions[0].extension === "immutableOwner";
        return supported && info?.owner === owner && (info.closeAuthority || owner) === owner
          && info.tokenAmount?.amount === "0" && info.state === "initialized"
          && info.isNative === false && !info.delegate && !excluded.has(info.mint)
          && Number.isSafeInteger(account.lamports) && account.lamports > 0;
      });
      return { connection, accounts };
    });
    if (state.pending) return state.pending;
    // ponytail: eight accounts per manual call keeps legacy transactions small;
    // rerun after confirmation for more, rather than introducing a background job.
    const accounts = state.accounts.slice(0, 8);
    const result = { success: true, dry_run: !execute || process.env.DRY_RUN === "true",
      eligible: state.accounts.length, accounts: accounts.map(a => ({ account: a.pubkey.toString(),
        mint: a.account.data.parsed.info.mint, program: a.account.owner.toString(), rent_lamports: a.account.lamports })),
      recovered_lamports_before_fee: accounts.reduce((sum, a) => sum + a.account.lamports, 0) };
    if (result.dry_run || !accounts.length) return result;
    const connection = state.connection;
    const tx = new Transaction();
    for (const a of accounts) tx.add(createCloseAccountInstruction(a.pubkey, wallet.publicKey, wallet.publicKey, [], a.account.owner));
    const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
    tx.recentBlockhash = blockhash;
    tx.feePayer = wallet.publicKey;
    const fee = (await connection.getFeeForMessage(tx.compileMessage(), "confirmed")).value;
    if (!Number.isSafeInteger(fee) || fee < 0 || fee >= result.recovered_lamports_before_fee) {
      throw new Error("Rent reclaim refused: unknown or uneconomic network fee");
    }
    tx.sign(wallet);
    const raw = tx.serialize(), signature = bs58.encode(tx.signature);
    fs.mkdirSync(path.dirname(pendingPath), { recursive: true, mode: 0o700 });
    fs.writeFileSync(pendingPath, JSON.stringify({ signature, blockhash, lastValidBlockHeight }), { mode: 0o600, flag: "wx", flush: true });
    recordSubmission(wallet, null, "rent_reclaim", signature, lastValidBlockHeight);
    try {
      await connection.sendRawTransaction(raw, CONFIRM_OPTIONS);
    } catch (_) {
      // Sending may have succeeded despite the RPC error. Never rebuild/retry.
    }
    await confirmSignedTransaction(connection, { signature, blockhash, lastValidBlockHeight });
    fs.rmSync(pendingPath);
    return { ...result, txHash: signature, fee_lamports: fee };
  } finally {
    if (releaseSwap) await releaseSwap();
    await releaseEntry();
  }
}

async function assertNoTokenExposure(pool, wallet) {
  // Read position accounts, not cached portfolio values or bin arrays. Empty
  // NFTs also block until the monitor reconciles them. Includes sibling pools
  // of the same base mint, even before Python has written their Redis metadata.
  const positions = await pool.program.account.positionV2.all([
    DLMM.positionOwnerFilter(wallet.publicKey),
  ]);
  const sol = "So11111111111111111111111111111111111111112";
  const mints = [pool.lbPair.tokenXMint, pool.lbPair.tokenYMint]
    .map(String).filter((mint) => mint !== sol);
  for (const position of positions) {
    if (position.account.lbPair.toString() === pool.pubkey.toString()) {
      throw new Error(`ENTRY REFUSED: pool already has position ${position.publicKey}`);
    }
    const pair = await pool.program.account.lbPair.fetch(position.account.lbPair);
    if ([pair.tokenXMint, pair.tokenYMint].some((mint) => mints.includes(mint.toString()))) {
      throw new Error(`ENTRY REFUSED: token already exposed through position ${position.publicKey}`);
    }
  }
}

async function assertRootBudget() {
  const context = JSON.parse(process.env.DLMM_ENTRY_CONTEXT || "{}");
  const root = context.root_chain_id || context.recenter_of;
  if (!root || process.env.DRY_RUN === "true") return;
  await reconcileAccounting();
  const {collect} = require("./dlmm_nav.js");
  await collect({dir:path.join(PROFILE_DIR,"memories"),wallet:getWallet().publicKey.toString(),PublicKey,rpc:runWithFailover,historyOnly:true});
  const args = [path.join(SCRIPT_DIR,"dlmm_accounting.py"), "--profile", PROFILE_DIR, "--check-root", root];
  if (Number.isFinite(context.fee_opportunity_sol) && Number.isFinite(context.fee_opportunity_observed_at)
      && Date.now()/1000-context.fee_opportunity_observed_at >= 0
      && Date.now()/1000-context.fee_opportunity_observed_at <= 1800) args.push("--opportunity", String(context.fee_opportunity_sol));
  if (Number.isFinite(context.root_floor_sol)) args.push("--floor", String(context.root_floor_sol));
  if (Number.isInteger(context.root_strike_cap)) args.push("--strike-cap", String(context.root_strike_cap));
  const decision = JSON.parse(require("child_process").execFileSync("python3", args, {encoding:"utf8",timeout:20000}));
  console.warn(`[ROOT] ${JSON.stringify(decision)}`);
  if (!decision.allow) throw new Error(`ENTRY REFUSED: ${decision.reason}`);
}

// Guard native cash after the exact transaction, including rent and network fees.
async function assertNativeReserve(connection, wallet, transaction) {
  const before = await connection.getBalanceAndContext(wallet.publicKey, "confirmed");
  const simulated = await connection.simulateTransaction(transaction, {
    commitment: "confirmed", sigVerify: false, minContextSlot: before.context.slot,
    accounts: { encoding: "base64", addresses: [wallet.publicKey.toString()] }
  });
  const after = await connection.getBalanceAndContext(wallet.publicKey,
    { commitment: "confirmed", minContextSlot: simulated.context.slot });
  const post = simulated.value.accounts?.[0]?.lamports;
  if (simulated.value.err || !Number.isSafeInteger(post) || !Number.isSafeInteger(before.value)
      || before.value !== after.value) throw new Error("ENTRY REFUSED: native reserve simulation unmeasured");
  if (post < 200000000) throw new Error("ENTRY REFUSED: rent/fees would breach 0.2 SOL native reserve");
}

async function deployPosition(poolAddressStr, amountX, amountY, binsBelow, binsAbove, strategyTypeStr = "spot", slippageBps = 1000) {
  if (![amountX, amountY].every((n) => Number.isFinite(n) && n >= 0)
      || amountX + amountY <= 0
      || ![binsBelow, binsAbove].every((n) => Number.isSafeInteger(n) && n >= 0)
      || !Number.isSafeInteger(slippageBps) || slippageBps <= 0 || slippageBps > 10000
      || !["spot", "curve", "bid_ask"].includes(strategyTypeStr)) {
    throw new Error("Invalid deploy amounts, range, strategy or slippage");
  }
  const wallet = getWallet();
  const dry = process.env.DRY_RUN === "true";
  await assertRootBudget();
  const settlements = path.join(PROFILE_DIR, "memories", "dlmm_settlements");
  if (!dry && fs.existsSync(settlements) && fs.readdirSync(settlements).some(f => {
    if (!f.endsWith(".json")) return false;
    try {
      const item = JSON.parse(fs.readFileSync(path.join(settlements, f), "utf8"));
      return item.state !== "deferred" || !["swap_no_route", "net_recovery_below_floor"].includes(item.reason);
    } catch { return true; }
  })) {
    throw new Error("ENTRY REFUSED: a previous exit is awaiting verified SOL settlement");
  }
  const release = dry ? async () => {} : await acquireDeployLock(wallet.publicKey.toString());
  const pendingDir = path.join(PROFILE_DIR, "memories", "dlmm_pending_deploys");
  const pendingPath = path.join(pendingDir, `${wallet.publicKey}.json`);
  const entryDir = path.join(PROFILE_DIR, "memories", "dlmm_entries");
  try {
    return await runWithFailover(async (connection) => {
      let submitted = false;
      const txHashes = [];
      const newPosition = Keypair.generate();
      try {
        if (!dry && fs.existsSync(pendingPath)) {
          const pending = JSON.parse(fs.readFileSync(pendingPath, "utf8"));
          // A timed-out or killed sender may still land. Never release its
          // reservation by wall-clock timeout; wait for the actual blockhash
          // validity to end, then re-read all on-chain exposure below.
          if (!Number.isSafeInteger(pending.lastValidBlockHeight)
              || await connection.getBlockHeight("finalized") <= pending.lastValidBlockHeight) {
            return { success: false, pending: true, position: pending.position,
              error: "ENTRY PENDING: previous submission requires on-chain reconciliation" };
          }
        }
        const pool = await DLMM.create(connection, new PublicKey(poolAddressStr));
        if (!dry) await assertNoTokenExposure(pool, wallet);
        const activeBin = await pool.getActiveBin();
        const minBinId = activeBin.binId - binsBelow;
        const maxBinId = activeBin.binId + binsAbove;
        const tokenXDecimals = await getTokenDecimals(connection, pool.lbPair.tokenXMint);
        const tokenYDecimals = await getTokenDecimals(connection, pool.lbPair.tokenYMint);
        const totalXLamports = new BN(Math.floor(amountX * Math.pow(10, tokenXDecimals)));
        const totalYLamports = new BN(Math.floor(amountY * Math.pow(10, tokenYDecimals)));
        const strategyType = { spot: StrategyType.Spot, curve: StrategyType.Curve,
          bid_ask: StrategyType.BidAsk }[strategyTypeStr];
        if (dry) return { success: true, dryRun: true, position: "DRY_RUN_POSITION_ADDR" };
        await assertRangeDoesNotRequireBinArrayInitialization(connection, pool, minBinId, maxBinId);
        fs.mkdirSync(pendingDir, { recursive: true, mode: 0o700 });
        fs.mkdirSync(entryDir, { recursive: true, mode: 0o700 });
        // Persist provenance BEFORE submission, so timeout adoption keeps the
        // caller's mode and re-center root. No wallet secret is recorded.
        const context = JSON.parse(process.env.DLMM_ENTRY_CONTEXT || "{}");
        let bin_snapshot = null;
        try { bin_snapshot = await binSnapshot(pool, minBinId, maxBinId); }
        catch { console.warn("[SHADOW] Entry bin snapshot unavailable"); }

        const persistEntry = () => fs.writeFileSync(path.join(entryDir, `${newPosition.publicKey}.json`), JSON.stringify({
          ...context, bin_snapshot, root_chain_id: context.root_chain_id || context.recenter_of || newPosition.publicKey.toString(),
          pool: poolAddressStr, position: newPosition.publicKey.toString(),
          entry_bin: activeBin.binId, entry_price: pool.fromPricePerLamport(Number(activeBin.price)),
          bins_below: binsBelow, bins_above: binsAbove, bin_step: Number(pool.lbPair.binStep),
          amount_x: amountX, amount_y: amountY,
          deployed_at: Math.floor(Date.now() / 1000),
        }), { mode: 0o600 });
        const send = async (tx, signers) => {
          const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
          tx.recentBlockhash = blockhash;
          tx.lastValidBlockHeight = lastValidBlockHeight;
          tx.feePayer = wallet.publicKey;
          await assertNativeReserve(connection, wallet, new VersionedTransaction(tx.compileMessage()));
          if (!submitted) persistEntry();
          tx.sign(...signers);
          const raw = tx.serialize();
          const signature = bs58.encode(tx.signature);
          // Send the EXACT signed bytes whose expiry we persist. web3.js's
          // sendTransaction helper can replace the blockhash behind our back.
          fs.writeFileSync(pendingPath, JSON.stringify({ position: newPosition.publicKey.toString(),
            pool: poolAddressStr, signature, lastValidBlockHeight, blockhash }), { mode: 0o600 });
          recordSubmission(wallet, newPosition.publicKey.toString(), "deploy", signature, lastValidBlockHeight);
          submitted = true;
          txHashes.push(signature);
          console.warn(`[TX] ${JSON.stringify({stage: "send", signature, blockhash, lastValidBlockHeight})}`);
          // Retry the same signed transaction, never the position builder.
          return await runWithFailover(async (rpc) => {
            const hash = await rpc.sendRawTransaction(raw, CONFIRM_OPTIONS);
            await confirmSignedTransaction(rpc, { signature: hash, blockhash, lastValidBlockHeight });
            return hash;
          });
        };
        if (binsBelow + binsAbove > 69) {
          const creates = await pool.createExtendedEmptyPosition(minBinId, maxBinId,
            newPosition.publicKey, wallet.publicKey);
          const createTxs = Array.isArray(creates) ? creates : [creates];
          for (let i = 0; i < createTxs.length; i++) {
            await send(createTxs[i], i === 0 ? [wallet, newPosition] : [wallet]);
          }
          const adds = await pool.addLiquidityByStrategyChunkable({
            positionPubKey: newPosition.publicKey, user: wallet.publicKey,
            totalXAmount: totalXLamports, totalYAmount: totalYLamports,
            strategy: { minBinId, maxBinId, strategyType }, slippage: slippageBpsToPercent(slippageBps),
          });
          for (const tx of Array.isArray(adds) ? adds : [adds]) await send(tx, [wallet]);
        } else {
          const tx = await pool.initializePositionAndAddLiquidityByStrategy({
            positionPubKey: newPosition.publicKey, user: wallet.publicKey,
            totalXAmount: totalXLamports, totalYAmount: totalYLamports,
            strategy: { minBinId, maxBinId, strategyType }, slippage: slippageBpsToPercent(slippageBps),
          });
          await send(tx, [wallet, newPosition]);
        }
        // Keep the reservation through blockhash expiry even on success: an
        // immediately-following RPC may lag the confirming endpoint. Exits are
        // never blocked; this briefly delays only the next wallet deployment.
        return { success: true, position: newPosition.publicKey.toString(), txHash: txHashes[0], txHashes };
      } catch (err) {
        if (!submitted && err.message.startsWith("ENTRY REFUSED:")) return { success: false, error: err.message };
        if (!submitted) throw err; // Read/build failure: another RPC is safe.
        // Sending then timing out does NOT mean failure. Never RPC-failover
        // into a second mint or clean up possibly funded liquidity blindly.
        return { success: false, pending: true, position: newPosition.publicKey.toString(),
          pool: poolAddressStr, txHashes, error: `DEPLOY UNVERIFIED: ${err.message}` };
      }
    });
  } finally {
    await release();
  }
}


async function findPoolForPosition(connection, wallet, positionAddressStr) {
  // Try SDK first
  const allPositions = await DLMM.getAllLbPairPositionsByUser(connection, wallet.publicKey);
  for (const [lbPairKey, posData] of allPositions) {
    const found = posData.lbPairPositionsData.find(p => p.publicKey.toString() === positionAddressStr);
    if (found) {
      const pool = await DLMM.create(connection, new PublicKey(lbPairKey));
      return { pool, positionData: found, poolAddressStr: lbPairKey };
    }
  }
  // SDK returned empty — fall back to Meteora Portfolio API to get pool address
  const walletAddr = wallet.publicKey.toString();
  const apiUrl = `https://dlmm.datapi.meteora.ag/portfolio/open?user=${walletAddr}`;
  let poolAddressStr = null;
  try {
    const res = await fetch(apiUrl, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const data = await res.json();
      for (const poolData of (data.pools || [])) {
        if ((poolData.listPositions || []).includes(positionAddressStr)) {
          poolAddressStr = poolData.poolAddress;
          break;
        }
      }
    }
  } catch (err) {
    console.warn(`[DLMM] Portfolio API lookup failed: ${err.message}`);
  }
  if (!poolAddressStr) {
    return null;
  }
  // Create pool directly and fetch position via targeted query
  const pool = await DLMM.create(connection, new PublicKey(poolAddressStr));
  const userPositions = await pool.getPositionsByUserAndLbPair(wallet.publicKey);
  const found = userPositions.userPositions.find(p => p.publicKey.toString() === positionAddressStr);
  if (!found) {
    return null;
  }
  return { pool, positionData: found, poolAddressStr };
}

function positionIsEmpty(position) {
  const data = position?.positionData;
  const shares = data?.liquidityShares;
  if (Array.isArray(shares) && shares.length) return shares.every((share) => share.isZero());
  // Current SDK exposes per-bin positionLiquidity strings, not liquidityShares.
  const bins = data?.positionBinData;
  if (!Array.isArray(bins) || !bins.length ||
      bins.some(bin => typeof bin.positionLiquidity !== "string" || !/^\d+$/.test(bin.positionLiquidity))) return null;
  if (bins.some(bin => BigInt(bin.positionLiquidity) > 0n)) return false;
  if (!Number.isSafeInteger(data.lowerBinId) || !Number.isSafeInteger(data.upperBinId) ||
      bins.length !== data.upperBinId - data.lowerBinId + 1 ||
      bins.some((bin, i) => bin.binId !== data.lowerBinId + i)) return null;
  return true;
}

async function positionAccountExists(connection, positionAddressStr) {
  return Boolean(await connection.getAccountInfo(new PublicKey(positionAddressStr), "confirmed"));
}

async function claimFees(positionAddressStr) {
  if (process.env.DRY_RUN === "true" && (positionAddressStr.includes("DRY_RUN") || positionAddressStr.length < 32)) {
    console.warn(JSON.stringify({ success: true, dryRun: true }));
    return { success: true, dryRun: true };
  }
  return await runWithFailover(async (connection) => {
    const wallet = getWallet();

    const found = await findPoolForPosition(connection, wallet, positionAddressStr);
    if (!found) {
      throw new Error(`Position ${positionAddressStr} not found for user ${wallet.publicKey.toString()}`);
    }
    const { pool, positionData } = found;

    if (process.env.DRY_RUN === "true") {
      console.log(`[DRY RUN] Would claim fees for ${positionAddressStr}`);
      return { success: true, dryRun: true };
    }

    const txs = await pool.claimSwapFee({
      owner: wallet.publicKey,
      position: positionData
    });

    const txHashes = [];
    for (const tx of txs) {
      const txHash = await recordedClaim(connection, tx, wallet, positionAddressStr);
      txHashes.push(txHash);
    }
    return {
      success: true,
      txHashes
    };
  });
}

async function closePosition(positionAddressStr, emptyOnly = false) {
  if (process.env.DRY_RUN === "true" && (positionAddressStr.includes("DRY_RUN") || positionAddressStr.length < 32)) {
    console.warn(JSON.stringify({ success: true, dryRun: true, txHashes: ["DRY_RUN_TX_HASH"] }));
    return { success: true, dryRun: true, txHashes: ["DRY_RUN_TX_HASH"] };
  }
  new PublicKey(positionAddressStr);
  const release = await acquireSwapLock(`close-${positionAddressStr}`);
  try {
    return await closePositionLocked(positionAddressStr, emptyOnly);
  } finally {
    await release();
  }
}

async function closePositionLocked(positionAddressStr, emptyOnly = false) {
  const pendingDir = path.join(PROFILE_DIR, "memories", "dlmm_pending_closes");
  const pendingPath = path.join(pendingDir, `${positionAddressStr}.json`);
  let submittedSignature;
  let submissionError;
  if (fs.existsSync(pendingPath)) {
    const pending = JSON.parse(fs.readFileSync(pendingPath, "utf8"));
    if (emptyOnly && !pending.emptyOnly) return { success: false, pending: true,
      error: "Existing withdrawal requires normal close reconciliation" };
    if (await runWithFailover(async c => !await positionAccountExists(c, positionAddressStr))) {
      fs.rmSync(pendingPath, { force: true });
      return { success: true, reconciled: true, txHashes: [pending.signature] };
    }
    // A restart must resume the old signature until chain failure or finalized expiry.
    const status = await runWithFailover(c => reconcilePendingSwap(c, pendingPath, "Close"));
    if (status?.pending) {
      try {
        await runWithFailover(async c => {
          await c.sendRawTransaction(Buffer.from(pending.raw, "base64"), CONFIRM_OPTIONS);
          await confirmSignedTransaction(c, pending);
        });
        fs.rmSync(pendingPath, { force: true });
      } catch (err) {
        return { ...status, error: `Close retry pending: ${err.message}` };
      }
    }
    const gone = await runWithFailover(async c => !await positionAccountExists(c, positionAddressStr));
    if (gone) return { success: true, reconciled: true, txHashes: [pending.signature] };
  }
  return await runWithFailover(async (connection) => {
    if (submittedSignature) {
      if (!await positionAccountExists(connection, positionAddressStr)) {
        fs.rmSync(pendingPath, { force: true });
        return { success: true, txHashes: [submittedSignature], reconciled: true };
      }
      return { success: false, pending: true, txHash: submittedSignature,
        error: `Close submission requires on-chain reconciliation; position still exists (${submissionError || "confirmation unknown"})` };
    }
    const wallet = getWallet();

    const foundPos = await findPoolForPosition(connection, wallet, positionAddressStr);
    if (!foundPos) {
      throw new Error(`Position ${positionAddressStr} not found for user ${wallet.publicKey.toString()}`);
    }
    const { pool, positionData, poolAddressStr } = foundPos;
    if (emptyOnly && positionIsEmpty(positionData) !== true) {
      return { success: false, funded: positionIsEmpty(positionData) === false,
        error: "Empty-only close refused: liquidity is funded or unknown" };
    }

    if (process.env.DRY_RUN === "true") {
      console.log(`[DRY RUN] Would close position ${positionAddressStr}`);
      return { success: true, dryRun: true };
    }

    const sendClose = async (tx) => {
      const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
      tx.recentBlockhash = blockhash;
      tx.feePayer = wallet.publicKey;
      tx.sign(wallet);
      const raw = tx.serialize();
      const signature = bs58.encode(tx.signature);
      recordSubmission(wallet, positionAddressStr, "close", signature, lastValidBlockHeight);
      fs.mkdirSync(pendingDir, { recursive: true, mode: 0o700 });
      const tmp = `${pendingPath}.${process.pid}.tmp`;
      fs.writeFileSync(tmp, JSON.stringify({ signature, blockhash, lastValidBlockHeight, emptyOnly,
        raw: raw.toString("base64") }), { mode: 0o600, flush: true });
      fs.renameSync(tmp, pendingPath);
      submittedSignature = signature;
      console.warn(`[TX] ${JSON.stringify({stage: "close-send", signature: submittedSignature,
        position: positionAddressStr, blockhash, lastValidBlockHeight})}`);
      // Retry the SAME signed bytes across RPCs: one signature cannot execute twice.
      // A timeout is ambiguous; never build a replacement while it may still land.
      const txHash = await runWithFailover(async (rpc) => {
        try {
          const hash = await rpc.sendRawTransaction(raw, CONFIRM_OPTIONS);
          await confirmSignedTransaction(rpc, { signature: hash, blockhash, lastValidBlockHeight });
          return hash;
        } catch (err) {
          submissionError = err.message;
          throw err;
        }
      });
      fs.rmSync(pendingPath, { force: true });
      submittedSignature = null;
      return txHash;
    };

    // The program checks emptiness atomically. Never withdraw liquidity on this path,
    // even if a deposit lands after the SDK read above.
    if (emptyOnly) {
      const txs = await pool.closePositionIfEmpty({ owner: wallet.publicKey, position: positionData });
      const txHashes = [];
      for (const tx of Array.isArray(txs) ? txs : [txs]) txHashes.push(await sendClose(tx));
      return { success: true, txHashes };
    }

    // The SDK claims fees in the same transaction before closing the position.
    const lowerBin = positionData.positionData.lowerBinId;
    const upperBin = positionData.positionData.upperBinId;
    
    console.log(`[DLMM] Withdrawing liquidity from bins ${lowerBin} to ${upperBin}`);

    const txHashes = [];
    try {
      const closeTx = await pool.removeLiquidity({
        user: wallet.publicKey,
        position: positionData.publicKey,
        fromBinId: lowerBin,
        toBinId: upperBin,
        bps: new BN(10000), // 100%
        shouldClaimAndClose: true
      });
      for (const tx of Array.isArray(closeTx) ? closeTx : [closeTx]) {
        txHashes.push(await sendClose(tx));
      }
    } catch (rmErr) {
      // closePositionIfEmpty succeeds as a no-op on funded positions. Only use it when
      // the SDK snapshot positively proves every liquidity share is zero.
      if (submittedSignature || positionIsEmpty(positionData) !== true) throw rmErr;
      console.warn(`[DLMM] removeLiquidity failed (${rmErr.message}); attempting closePositionIfEmpty for empty position ${positionAddressStr}`);
      // Empty-position recovery has no combined withdrawal transaction; claim first.
      try {
        const claimTxs = await pool.claimSwapFee({
          owner: wallet.publicKey,
          position: positionData
        });
        for (const tx of claimTxs) {
          await recordedClaim(connection, tx, wallet, positionAddressStr);
        }
      } catch (err) {
        console.warn(`[DLMM] Fee claim during close warning: ${err.message}`);
      }
      const emptyTx = await pool.closePositionIfEmpty({ owner: wallet.publicKey, position: positionData });
      for (const tx of Array.isArray(emptyTx) ? emptyTx : [emptyTx]) {
        txHashes.push(await sendClose(tx));
      }
    }

    return {
      success: true,
      txHashes
    };
  });
}

async function getPositions(walletAddressStr) {
  return await runWithFailover(async (connection) => {
    const targetWallet = walletAddressStr ? new PublicKey(walletAddressStr) : getWallet().publicKey;
    const allPositions = await DLMM.getAllLbPairPositionsByUser(connection, targetWallet);
    
    const result = [];
    for (const [lbPairKey, posData] of allPositions) {
      const pool = await DLMM.create(connection, new PublicKey(lbPairKey));
      const activeBin = await pool.getActiveBin();
      
      for (const pos of posData.lbPairPositionsData) {
        const data = pos.positionData;
        const lowerBinId = data.lowerBinId;
        const upperBinId = data.upperBinId;
        const inRange = activeBin.binId >= lowerBinId && activeBin.binId <= upperBinId;
        
        result.push({
          position: pos.publicKey.toString(),
          pool: lbPairKey,
          tokenX: pool.tokenX.symbol || pool.lbPair.tokenXMint.toString(),
          tokenY: pool.tokenY.symbol || pool.lbPair.tokenYMint.toString(),
          lower_bin: lowerBinId,
          upper_bin: upperBinId,
          active_bin: activeBin.binId,
          in_range: inRange,
          feeX: data.feeX.toString(),
          feeY: data.feeY.toString()
        });
      }
    }
    return result;
  });
}

function normalizeMint(mint) {
  if (!mint) return mint;
  const SOL_MINT = "So11111111111111111111111111111111111111112";
  if (
    mint === "SOL" || 
    mint === "native" || 
    /^So1+$/.test(mint) || 
    (mint.length >= 32 && mint.length <= 44 && mint.startsWith("So1") && mint !== SOL_MINT)
  ) {
    return SOL_MINT;
  }
  return mint;
}

function slippageBpsToPercent(slippageBps) {
  if (!Number.isSafeInteger(slippageBps) || slippageBps <= 0) {
    throw new Error("Slippage must be a positive integer in basis points");
  }
  return slippageBps / 100;
}

async function getPositionPnl(poolAddressStr, positionAddressStr) {
  const walletAddress = getWallet().publicKey.toString();
  const url = `https://dlmm.datapi.meteora.ag/positions/${poolAddressStr}/pnl?user=${walletAddress}&status=open&pageSize=100&page=1`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Meteora PnL API error: ${res.status}`);
  }
  const data = await res.json();
  const positions = data.positions || data.data || [];
  const found = positions.find(p => (p.positionAddress || p.address || p.position) === positionAddressStr);
  if (!found) {
    throw new Error(`Position ${positionAddressStr} not found in Meteora PnL API`);
  }
  
  const deposit = parseFloat(found.allTimeDeposits?.total?.sol || 0);
  const balancesSol = parseFloat(found.unrealizedPnl?.balancesSol || 0);
  const unclaimedFeeSol = parseFloat(found.unrealizedPnl?.unclaimedFeeTokenX?.amountSol || 0) + 
                           parseFloat(found.unrealizedPnl?.unclaimedFeeTokenY?.amountSol || 0);
  const withdrawalsSol = parseFloat(found.allTimeWithdrawals?.total?.sol || 0);
  const feesClaimedSol = parseFloat(found.allTimeFees?.total?.sol || 0);
  
  let derivedPnlPct = 0;
  if (deposit > 0) {
    derivedPnlPct = ((balancesSol + unclaimedFeeSol + withdrawalsSol + feesClaimedSol - deposit) / deposit) * 100;
  }
  
  return {
    success: true,
    pnl_pct: found.pnlSolPctChange != null ? parseFloat(found.pnlSolPctChange) : derivedPnlPct,
    pnl_sol: found.pnlSol != null ? Number(found.pnlSol) : deposit * derivedPnlPct / 100,
    pnl_currency: "SOL",
    derived_pnl_pct: derivedPnlPct,
    current_value_sol: balancesSol,
    unclaimed_fees_sol: unclaimedFeeSol,
    in_range: !found.isOutOfRange,
    active_bin: found.poolActiveBinId ?? null,
    lower_bin: found.lowerBinId ?? null,
    upper_bin: found.upperBinId ?? null,
    fee_per_tvl_24h: found.feePerTvl24h ? parseFloat(found.feePerTvl24h) : 0
  };
}

async function getSplBalance(tokenMintStr) {
  return await runWithFailover(async (connection) => {
    const wallet = getWallet();
    const token_mint = normalizeMint(tokenMintStr);
    if (token_mint === "So11111111111111111111111111111111111111112") {
      const balance = await connection.getBalance(wallet.publicKey);
      return {
        balance: balance / 1e9,
        decimals: 9
      };
    }
    const mintPubKey = new PublicKey(token_mint);
    const accounts = await connection.getParsedTokenAccountsByOwner(wallet.publicKey, {
      mint: mintPubKey
    });
    if (accounts.value.length === 0) {
      return { balance: 0, decimals: 0 };
    }
    let totalBalance = 0;
    let decimals = 0;
    for (const acc of accounts.value) {
      const tokenAmount = acc.account.data.parsed.info.tokenAmount;
      totalBalance += tokenAmount.uiAmount || 0;
      decimals = tokenAmount.decimals || 0;
    }
    return {
      balance: totalBalance,
      decimals: decimals
    };
  });
}

// Preserve decimal input through scaling; binary multiplication can leave one
// raw unit behind even when the caller supplies the entire token balance.
function swapAmountRaw(amount, decimals) {
  const text = String(amount).trim();
  const match = text.length <= 128 && /^(\d+)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/.exec(text);
  const exponent = match ? Number(match[3] || 0) : NaN;
  if (!match || !Number.isInteger(decimals) || decimals < 0 || decimals > 255
      || !Number.isInteger(exponent) || Math.abs(exponent) > 255) {
    throw new Error("Invalid swap amount or token decimals");
  }
  const fraction = match[2] || "";
  const digits = BigInt(match[1] + fraction);
  const shift = decimals + exponent - fraction.length;
  const raw = shift >= 0 ? digits * 10n ** BigInt(shift) : digits / 10n ** BigInt(-shift);
  if (raw <= 0n || raw > 18446744073709551615n) throw new Error("Swap amount outside positive token u64 range");
  return raw.toString();
}

async function swapToken(inputMintStr, outputMintStr, amountFloat, maxPriceImpactPct = 5, slippageBps = 100, minNetLamports = null) {
  const input_mint = normalizeMint(inputMintStr);
  const output_mint = normalizeMint(outputMintStr);
  if (minNetLamports !== null && (!Number.isSafeInteger(minNetLamports) || minNetLamports < 1
      || output_mint !== "So11111111111111111111111111111111111111112" || input_mint === output_mint)) {
    throw new Error("Net recovery requires token-to-SOL and a positive integer lamport floor");
  }

  if (process.env.DRY_RUN === "true") {
    console.warn(`[DRY RUN] Would swap ${amountFloat} of ${input_mint} to ${output_mint}`);
    return { success: true, dryRun: true, txHash: "DRY_RUN_SWAP_TX_HASH", inputAmount: "0", outputAmount: "0" };
  }

  const wallet = getWallet();
  const release = await acquireSwapLock(wallet.publicKey.toString());
  const pendingDir = path.join(PROFILE_DIR, "memories", "dlmm_pending_swaps");
  const pendingPath = path.join(pendingDir, `${wallet.publicKey}-${input_mint}-${output_mint}.json`);

  try {
    try {
      const previous = await runWithFailover((connection) => reconcilePendingSwap(connection, pendingPath));
      if (previous) return previous;
    } catch (err) {
      return { success: false, pending: true,
        error: `Swap reconciliation unavailable; refusing duplicate submission: ${err.message}` };
    }

    // Fetch quote outside runWithFailover as it's a HTTP call to Jupiter, then execute/send via standard RPC rotation
    let quoteResponse, quoteObservedAt;
    try {
    // 1. Get input decimals
    let decimals = 9;
    if (input_mint !== "So11111111111111111111111111111111111111112") {
      // We'll perform a quick connection just to fetch decimals
      await runWithFailover(async (connection) => {
        const mintInfo = await connection.getParsedAccountInfo(new PublicKey(input_mint));
        decimals = mintInfo.value?.data?.parsed?.info?.decimals;
      });
    }
    const amountRaw = swapAmountRaw(amountFloat, decimals);

    // 2. Fetch a quote within the authorized slippage limit.
    const slippageLadder = [slippageBps]; // Retry later with a fresh quote; never widen the authorized slippage.
    let lastErr = null;
    for (const bps of slippageLadder) {
      try {
        const quoteUrl = `https://api.jup.ag/swap/v1/quote?inputMint=${input_mint}&outputMint=${output_mint}&amount=${amountRaw}&slippageBps=${bps}`;
        const quoteRes = await fetch(quoteUrl, { signal: AbortSignal.timeout(8000) });
        if (!quoteRes.ok) {
          const body = await quoteRes.text();
          let code;
          try { code = JSON.parse(body).errorCode; } catch { /* Non-JSON failures remain unknown. */ }
          if (quoteRes.status === 400 && ["COULD_NOT_FIND_ANY_ROUTE", "NO_ROUTES_FOUND", "TOKEN_NOT_TRADABLE"].includes(code)) {
            return { success: false, aborted: true, reason: "swap_no_route" };
          }
          lastErr = `Jupiter quote API error: ${quoteRes.status} ${body}`;
          continue;
        }
        const q = await quoteRes.json();
        if (!q || !q.outAmount || q.outAmount === "0") {
          lastErr = `Jupiter returned empty quote at slippage ${bps}bps (no route/liquidity)`;
          continue;
        }
        quoteResponse = q;
        quoteObservedAt = Math.floor(Date.now() / 1000);
        if (bps !== slippageBps) {
          console.warn(`[DLMM] Swap quote required elevated slippage ${bps}bps (thin liquidity)`);
        }
        break;
      } catch (e) {
        lastErr = e.message;
      }
    }
    if (!quoteResponse) {
      throw new Error(lastErr || "No Jupiter route found");
    }

    // 3. Price-impact guard — abort before signing if impact exceeds threshold (protects large exits on low-TVL pools)
    const impactPct = parseFloat(quoteResponse.priceImpactPct || "0") * 100;
    if (impactPct > maxPriceImpactPct) {
      return {
        success: false,
        aborted: true,
        reason: "price_impact_exceeded",
        priceImpactPct: impactPct,
        maxPriceImpactPct,
        error: `Swap aborted: price impact ${impactPct.toFixed(2)}% > max ${maxPriceImpactPct}%. Token left unswapped to avoid bad fill.`
      };
    }
    if (impactPct > 1) {
      console.warn(`[DLMM] Swap price impact ${impactPct.toFixed(2)}% (within ${maxPriceImpactPct}% limit)`);
    }
    } catch (err) {
      throw new Error(`Failed to fetch quote from Jupiter: ${err.message}`);
    }

    let submittedSignature;
    return await runWithFailover(async (connection) => {
    if (submittedSignature) return { success: false, pending: true, txHash: submittedSignature,
      error: "Previous swap submission needs reconciliation" };
    // 3. Fetch swap transaction
    const swapRes = await fetch("https://api.jup.ag/swap/v1/swap", {
      method: "POST",
      signal: AbortSignal.timeout(8000),
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        quoteResponse,
        userPublicKey: wallet.publicKey.toString(),
        wrapAndUnwrapSol: true,
        dynamicComputeUnitLimit: true
      })
    });
    if (!swapRes.ok) {
      throw new Error(`Jupiter swap API error: ${swapRes.status} ${await swapRes.text()}`);
    }
    const { swapTransaction } = await swapRes.json();
    
    // 4. Deserialize and sign
    const swapTransactionBuf = Buffer.from(swapTransaction, "base64");
    const transaction = VersionedTransaction.deserialize(swapTransactionBuf);
    
    const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
    transaction.message.recentBlockhash = blockhash;
    // Optional residual recovery: simulate the exact unsigned transaction and
    // reserve the entire quoted slippage allowance before authorizing a send.
    if (minNetLamports !== null) {
      const out = Number(quoteResponse.outAmount), minimum = Number(quoteResponse.otherAmountThreshold);
      if (!Number.isSafeInteger(out) || !Number.isSafeInteger(minimum) || minimum <= 0 || minimum > out) {
        return { success: false, aborted: true, reason: "net_recovery_invalid_quote" };
      }
      const before = await connection.getBalanceAndContext(wallet.publicKey, "confirmed");
      const simulated = await connection.simulateTransaction(transaction, {
        commitment: "confirmed", sigVerify: false, minContextSlot: before.context.slot,
        accounts: { encoding: "base64", addresses: [wallet.publicKey.toString()] }
      });
      const after = await connection.getBalanceAndContext(wallet.publicKey,
        { commitment: "confirmed", minContextSlot: simulated.context.slot });
      const post = simulated.value.accounts?.[0]?.lamports;
      if (simulated.value.err || !Number.isSafeInteger(post) || !Number.isSafeInteger(before.value)
          || before.value !== after.value) {
        return { success: false, aborted: true, reason: "net_recovery_unmeasured" };
      }
      const conservativeNet = post - before.value - (out - minimum);
      if (conservativeNet < minNetLamports) {
        return { success: false, aborted: true, reason: "net_recovery_below_floor",
          conservativeNetLamports: conservativeNet, minNetLamports };
      }
    }
    if (input_mint === "So11111111111111111111111111111111111111112") {
      await assertNativeReserve(connection, wallet, transaction);
    }
    transaction.sign([wallet]);
    
    // 5. Send and confirm
    const rawTransaction = transaction.serialize();
    const signedTxid = bs58.encode(transaction.signatures[0]);
    fs.mkdirSync(pendingDir, { recursive: true, mode: 0o700 });
    const markerTmp = `${pendingPath}.${process.pid}.tmp`;
    fs.writeFileSync(markerTmp, JSON.stringify({ signature: signedTxid, blockhash,
      lastValidBlockHeight, inputMint: input_mint, outputMint: output_mint,
      inputAmount: quoteResponse.inAmount, outputAmount: quoteResponse.outAmount }), { mode: 0o600 });
    fs.renameSync(markerTmp, pendingPath);
    let txid;
    recordSubmission(wallet, process.env.DLMM_SETTLEMENT_POSITION, "swap", signedTxid, lastValidBlockHeight, {
      observed_at: quoteObservedAt, input_mint, output_mint,
      in_amount: quoteResponse.inAmount, out_amount: quoteResponse.outAmount,
      minimum_out_amount: quoteResponse.otherAmountThreshold ?? null,
      authorized_slippage_bps: slippageBps, context_slot: quoteResponse.contextSlot ?? null,
      price_impact_pct: quoteResponse.priceImpactPct ?? null,
      basis: "provider_quote_before_broadcast; raw_token_units; not_realized_proceeds",
    });
    submittedSignature = signedTxid;
    try {
      txid = await connection.sendRawTransaction(rawTransaction, {
        skipPreflight: true,
        maxRetries: RPC_SEND_MAX_RETRIES
      });
    } catch (err) {
      return { success: false, pending: true, txHash: signedTxid,
        error: `Swap submission uncertain: ${err.message}` };
    }

    try {
      const confirmation = await connection.confirmTransaction({
        blockhash, lastValidBlockHeight, signature: txid
      }, "confirmed");
      if (confirmation.value.err) {
        fs.rmSync(pendingPath, { force: true });
        return { success: false, txHash: txid,
          error: `Swap failed: ${JSON.stringify(confirmation.value.err)}` };
      }
    } catch (err) {
      let status;
      try {
        status = (await connection.getSignatureStatuses(
          [txid], { searchTransactionHistory: true }
        )).value[0];
      } catch (statusErr) {
        return { success: false, pending: true, txHash: txid,
          error: `Swap confirmation status unavailable: ${statusErr.message}` };
      }
      if (!status || !["confirmed", "finalized"].includes(status.confirmationStatus)) {
        return { success: false, pending: true, txHash: txid,
          error: `Swap confirmation pending: ${err.message}` };
      }
      if (status.err) {
        fs.rmSync(pendingPath, { force: true });
        return { success: false, txHash: txid,
          error: `Swap failed: ${JSON.stringify(status.err)}` };
      }
    }
    fs.rmSync(pendingPath, { force: true });
    return {
      success: true,
      txHash: txid,
      inputAmount: quoteResponse.inAmount,
      outputAmount: quoteResponse.outAmount
    };
    });
  } finally {
    await release();
  }
}

async function binSnapshot(pool, lower, upper) {
  const data = await pool.getBinsBetweenLowerAndUpperBound(lower, upper);
  const active = await pool.getActiveBin();
  return {ts: Math.floor(Date.now()/1000), active_bin: active.binId,
    price: Number(pool.fromPricePerLamport(Number(active.price))),
    decimals_x: pool.tokenX.mint.decimals, decimals_y: pool.tokenY.mint.decimals,
    sol_is_x: pool.lbPair.tokenXMint.toString() === "So11111111111111111111111111111111111111112",
    bins: data.bins.map(b => ({id:b.binId, x:b.xAmount.toString(), y:b.yAmount.toString(),
      supply:b.supply.toString(), fee_x:b.feeAmountXPerTokenStored.toString(),
      fee_y:b.feeAmountYPerTokenStored.toString(), price:Number(b.pricePerToken)}))};
}

// Read-only reconciliation. A missing transaction remains unknown, never zero.
async function reconcileAccounting() {
  const dir = path.join(PROFILE_DIR, "memories");
  const readRows = (name) => {
    const file = path.join(dir, name);
    return fs.existsSync(file) ? fs.readFileSync(file, "utf8").split("\n").filter(Boolean).map(JSON.parse) : [];
  };
  const events = [...new Map(readRows("dlmm_transactions.jsonl").map(e => [e.signature,e])).values()];
  const facts = new Map([...readRows("dlmm_transaction_facts.jsonl"), ...readRows("dlmm_wallet_transactions.jsonl")].map(r => [r.signature, r]));
  let pending = 0;
  for (const event of events) {
    if (facts.has(event.signature)) continue;
    try {
      const tx = await runWithFailover(connection => connection.getParsedTransaction(event.signature,
        { commitment: "finalized", maxSupportedTransactionVersion: 0 }));
      // A successful RPC returning null means missing evidence, not provider failure.
      if (!tx?.meta) { pending++; continue; }
      // Share finalized evidence with NAV collection instead of fetching it again.
      const { transactionFact } = require("./dlmm_nav.js");
      const fact = transactionFact(tx, event.wallet, event.signature, event);
      fs.appendFileSync(path.join(dir, "dlmm_wallet_transactions.jsonl"), JSON.stringify(fact) + "\n", { mode: 0o600 });
      facts.set(event.signature, fact);
    } catch (err) {
      pending++;
      console.warn(`[ACCOUNTING] ${event.signature}: reconciliation pending`);
    }
  }
  return { recorded: events.length, reconciled: events.filter(e => facts.has(e.signature) && facts.get(e.signature).landed !== false).length,
    expired_unlanded: events.filter(e => facts.get(e.signature)?.landed === false).length, pending };
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command) {
    console.error("No command provided. Exposing: active-bin, deploy, check-bins, claim, close, position-exists, positions, pnl, spl-balance, swap");
    process.exit(1);
  }
  
  try {
    if (command === "reclaim-empty-accounts") {
      if (args.slice(1).some(arg => arg !== "--execute")) throw new Error("Usage: reclaim-empty-accounts [--execute]");
      console.log(JSON.stringify(await reclaimEmptyAccounts(args.includes("--execute"))));
    } else if (command === "accounting") {
      const recorded = await reconcileAccounting();
      const { collect } = require("./dlmm_nav.js");
      const wallet = process.env.SOLANA_PUBLIC_KEY || getWallet().publicKey.toString();
      const nav = await collect({dir: path.join(PROFILE_DIR, "memories"), wallet, PublicKey, rpc: runWithFailover});
      // Advisory local cache only; publication failure must not hide collected facts.
      try {
        require("child_process").execFileSync("python3", [path.join(SCRIPT_DIR, "dlmm_accounting.py"),
          "--profile", PROFILE_DIR, "--sync-pool-memory"], {encoding:"utf8", timeout:20000});
      } catch (_) { console.warn("[ACCOUNTING] Pool cash history publication failed; cached evidence will expire"); }
      console.log(JSON.stringify({recorded, nav}));
    } else if (command === "bin-snapshot") {
      const lower = Number(args[2]), upper = Number(args[3]);
      if (!Number.isInteger(lower) || !Number.isInteger(upper) || upper < lower || upper-lower > 200) throw new Error("Invalid snapshot bounds");
      console.log(JSON.stringify(await runWithFailover(async connection =>
        binSnapshot(await DLMM.create(connection, new PublicKey(args[1])), lower, upper))));
    } else if (command === "active-bin") {
      const pool = args[1];
      if (!pool) throw new Error("Usage: active-bin <pool_address>");
      const res = await getActiveBin(pool);
      console.log(JSON.stringify(res));
    } else if (command === "deploy") {
      const pool = args[1];
      let amountX = 0;
      let amountY = 0;
      let binsBelow = 0;
      let binsAbove = 0;
      let strategyType = "spot";
      let slippageBps = 1000;

      if (!pool) {
        throw new Error("Usage: deploy <pool_address> <amount_x> <amount_y> <bins_below> <bins_above> [strategy_type] [slippage_bps]\n   Or: deploy <pool_address> <amount_sol> <bins_below> [bins_above]");
      }

      // Auto-detect format by checking if 3rd arg is integer (e.g. bins_below in old format)
      const val2 = parseFloat(args[2]);
      const val3 = parseFloat(args[3]);
      const val3IsInt = Number.isInteger(val3);

      if (args.length <= 5 && val3IsInt) {
        // Old format: deploy <pool_address> <amount_sol> <bins_below> [bins_above]
        amountX = 0;
        amountY = val2;
        binsBelow = parseInt(args[3]);
        binsAbove = parseInt(args[4] || "0");
      } else {
        // New format: deploy <pool_address> <amount_x> <amount_y> <bins_below> <bins_above> [strategy_type] [slippage_bps]
        amountX = val2;
        amountY = val3;
        binsBelow = parseInt(args[4]);
        binsAbove = parseInt(args[5] || "0");
        strategyType = args[6] || "spot";
        slippageBps = parseInt(args[7] || "1000");
      }

      if (isNaN(amountX) || isNaN(amountY) || isNaN(binsBelow)) {
        throw new Error("Invalid numeric arguments for deploy command.");
      }

      const res = await deployPosition(pool, amountX, amountY, binsBelow, binsAbove, strategyType, slippageBps);
      console.log(JSON.stringify(res));
    } else if (command === "check-bins") {
      const pool = args[1];
      const binsBelow = parseInt(args[2]);
      const binsAbove = parseInt(args[3] || "0");
      if (!pool || isNaN(binsBelow)) throw new Error("Usage: check-bins <pool_address> <bins_below> [bins_above]");
      const res = await checkBinCoverage(pool, binsBelow, binsAbove);
      console.log(JSON.stringify(res));
    } else if (command === "claim") {
      const position = args[1];
      if (!position) throw new Error("Usage: claim <position_address>");
      const res = await claimFees(position);
      console.log(JSON.stringify(res));
    } else if (command === "close") {
      const position = args[1];
      if (!position) throw new Error("Usage: close <position_address>");
      // CHOKEPOINT: the raw close primitive must not be reachable directly. Every legitimate close
      // flows through dlmm_monitor.py (auto-rules or guarded --override-close), which sets
      // DLMM_CLOSE_AUTH=1 only after the health policy has been applied. A direct
      // `node dlmm_executor.js close <addr>` (gateway agent, shell, stray script) has no token and
      // is refused, so no actor can bypass the GUARD by calling the executor directly.
      // Escape hatches: --force argv flag (explicit manual intent) or DRY_RUN.
      const closeAuthorized =
        process.env.DLMM_CLOSE_AUTH === "1" ||
        process.env.DRY_RUN === "true" ||
        args.includes("--force");
      if (!closeAuthorized) {
        console.error(JSON.stringify({
          success: false,
          error: "CLOSE REFUSED: raw executor close is not authorized. Closes must go through dlmm_monitor.py (which applies the health GUARD and sets DLMM_CLOSE_AUTH). Pass --force for explicit manual override.",
        }));
        process.exit(3);
      }
      const res = await closePosition(position, args.includes("--empty-only"));
      console.log(JSON.stringify(res));
    } else if (command === "position-exists") {
      const position = args[1];
      if (!position) throw new Error("Usage: position-exists <position_address>");
      const exists = await runWithFailover((connection) => positionAccountExists(connection, position));
      console.log(JSON.stringify({ success: true, exists }));
    } else if (command === "positions") {
      const wallet = args[1];
      const res = await getPositions(wallet);
      console.log(JSON.stringify(res));
    } else if (command === "pnl") {
      const pool = args[1];
      const position = args[2];
      if (!pool || !position) throw new Error("Usage: pnl <pool_address> <position_address>");
      const res = await getPositionPnl(pool, position);
      console.log(JSON.stringify(res));
    } else if (command === "spl-balance") {
      const token = args[1];
      if (!token) throw new Error("Usage: spl-balance <token_mint>");
      const res = await getSplBalance(token);
      console.log(JSON.stringify(res));
    } else if (command === "list-tokens") {
      const TOKEN_PROGRAM_ID = new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA");
      const TOKEN_2022_PROGRAM_ID = new PublicKey("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb");
      const listWallet = getWallet();
      const tokens = await runWithFailover(async (connection) => {
        const [v1Accounts, v2Accounts] = await Promise.all([
          connection.getParsedTokenAccountsByOwner(listWallet.publicKey, { programId: TOKEN_PROGRAM_ID }),
          connection.getParsedTokenAccountsByOwner(listWallet.publicKey, { programId: TOKEN_2022_PROGRAM_ID }),
        ]);
        return [...v1Accounts.value, ...v2Accounts.value]
          .map(acc => {
            const info = acc.account.data.parsed.info;
            return {
              mint: info.mint,
              balance: info.tokenAmount.uiAmount || 0,
              decimals: info.tokenAmount.decimals || 0,
            };
          })
          .filter(t => t.balance > 0);
      });
      console.log(JSON.stringify({ success: true, tokens }));
    } else if (command === "swap") {
      const input = args[1];
      const output = args[2];
      const amount = args[3];
      const maxImpact = args[4] != null ? parseFloat(args[4]) : 5;
      const slipBps = args[5] != null ? parseInt(args[5]) : 100;
      if (!input || !output || amount == null) {
        throw new Error("Usage: swap <input_mint> <output_mint> <amount> [max_price_impact_pct] [slippage_bps] [min_net_lamports]");
      }
      const minNetLamports = args[6] != null ? Number(args[6]) : null;
      const res = await swapToken(input, output, amount, maxImpact, slipBps, minNetLamports);
      console.log(JSON.stringify(res));
    } else {
      throw new Error(`Unknown command: ${command}`);
    }
  } catch (err) {
    console.error(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

if (require.main === module) main();
module.exports = { swapAmountRaw, reclaimEmptyAccounts, assertRootBudget, reconcileAccounting, recordSubmission, closePosition, swapToken, confirmSignedTransaction, deployPosition, acquireDeployLock, acquireSwapLock, reconcilePendingSwap,
  assertNoTokenExposure, positionIsEmpty, positionAccountExists, slippageBpsToPercent };
