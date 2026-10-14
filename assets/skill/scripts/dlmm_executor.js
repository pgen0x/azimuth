const { Connection, Keypair, PublicKey, VersionedTransaction, Transaction, TransactionMessage } = require("@solana/web3.js");
const DLMM = require("@meteora-ag/dlmm");
const { StrategyType } = require("@meteora-ag/dlmm");
const BN = require("bn.js");
const bs58 = require("bs58");
const dotenv = require("dotenv");
const fs = require("fs");
const path = require("path");
const net = require("net");
const riskMark = require("./dlmm_risk_mark");

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
// Loaded only on entry/maintenance paths; exit reconciliation never needs it.
function nativeCashPolicy() {
  const policy = require("./dlmm_cash_policy.json");
  const values = [policy.native_reserve_lamports, policy.entry_rent_allowance_lamports, policy.minimum_entry_lamports];
  if (policy.version !== 1 || !values.every(n => Number.isSafeInteger(n) && n >= 0)
      || !Number.isSafeInteger(values.reduce((sum, n) => sum+n, 0))
      || policy.native_reserve_lamports <= 0 || policy.minimum_entry_lamports <= 0) {
    throw new Error("ENTRY REFUSED: invalid native cash policy");
  }
  return {...policy, entry_floor_lamports: values.reduce((sum, n) => sum+n, 0)};
}

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
      if (err.riskMarkUnavailable || err.message?.startsWith("ENTRY REFUSED:") || err.message?.startsWith("Rent reclaim refused:")) throw err;
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
  const signature = bs58.encode(tx.signature);
  recordSubmission(wallet, position, "claim", signature, lastValidBlockHeight);
  await confirmSignedTransaction(connection, { signature, blockhash, lastValidBlockHeight }, raw);
  return signature;
}

// Reconcile the exact signed signature after either broadcast or confirmation errors.
async function confirmSignedTransaction(connection, strategy, raw, options = CONFIRM_OPTIONS, signal = null) {
  if (signal?.aborted) throw new Error("Transaction observation cancelled; signature remains pending");
  console.warn(`[TX] ${JSON.stringify({stage: "confirm", ...strategy})}`);
  if (raw) {
    try { await connection.sendRawTransaction(raw, options); }
    catch { console.warn("[TX] Broadcast error; reconciling the signed signature"); }
  }
  // A denied WebSocket handshake leaves the SDK reconnecting even after its
  // confirmation promise aborts and HTTP proves success. That keeps this
  // one-shot process alive until the monitor kills it, delaying SOL recovery.
  // Use bounded HTTP status polling without creating a subscription at all.
  const deadline = Date.now() + 8000;
  let previousStatus;
  while (true) {
    if (signal?.aborted) throw new Error("Transaction observation cancelled; signature remains pending");
    const status = (await connection.getSignatureStatuses(
      [strategy.signature], { searchTransactionHistory: true }
    )).value[0];
    const label = status?.confirmationStatus || "unknown";
    if (label !== previousStatus) {
      console.warn(`[TX] ${JSON.stringify({stage: "reconcile", signature: strategy.signature,
        status: label, chainError: status?.err || null})}`);
      previousStatus = label;
    }
    if (status && ["confirmed", "finalized"].includes(status.confirmationStatus)) {
      if (status.err === null) return;
      if (!status.err) throw new Error("Transaction confirmation unmeasured");
      const error = new Error(`Transaction failed: ${JSON.stringify(status.err)}`);
      error.transactionFailed = true;
      throw error;
    }
    const remaining = deadline - Date.now();
    if (remaining <= 0) throw new Error("Transaction confirmation timeout; signed status remains pending");
    await new Promise((resolve, reject) => {
      const finish = (error) => {
        clearTimeout(timer);
        signal?.removeEventListener("abort", cancelled);
        if (error) reject(error); else resolve();
      };
      const cancelled = () => finish(new Error("Transaction observation cancelled; signature remains pending"));
      const timer = setTimeout(() => finish(), Math.min(1000, remaining));
      signal?.addEventListener("abort", cancelled, { once: true });
      if (signal?.aborted) cancelled();
    });
  }
}

async function confirmCloseTransaction(strategy, raw) {
  return confirmExitTransaction(strategy, raw);
}

// Broadcast only the already signed exit bytes with a persisted signature.
// An unresponsive provider must not hold up the other configured providers.
async function confirmExitTransaction(strategy, raw, kind = "close", options = CONFIRM_OPTIONS) {
  if (!["close", "settlement_swap"].includes(kind)) throw new Error("Unsupported exit transport kind");
  const label = kind === "close" ? "Close" : "Settlement swap";
  const logStage = kind === "close" ? "close-fanout" : "settlement-swap-fanout";
  const controller = new AbortController();
  const started = Date.now();
  const rawHash = require("crypto").createHash("sha256").update(raw).digest("hex");
  const urls = [...new Set(RPC_URLS)];
  const observe = (stage, extra = {}) => {
    try {
      const dir = path.join(PROFILE_DIR, "memories");
      fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
      const journal = kind === "close" ? "dlmm_close_transports.jsonl" : "dlmm_swap_transports.jsonl";
      fs.appendFileSync(path.join(dir, journal), JSON.stringify({
        version: 1, signature: strategy.signature, raw_sha256: rawHash, stage,
        transaction_kind: kind,
        observed_at: Date.now() / 1000, elapsed_ms: Date.now() - started,
        rpc_count: urls.length, ...extra, basis: "client_transport_observation_not_finalized_execution",
      }) + "\n", { mode: 0o600 });
    } catch (_) { /* Optional timing evidence must not prevent an exit. */ }
  };
  let outcome = "pending", confirmedRpcIndex = null;
  let timer;
  const deadline = new Promise((_, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new Error(`${label} confirmation timeout; signed status remains pending`));
    }, 8000);
  });
  console.warn(`[TX] ${JSON.stringify({ stage: logStage, signature: strategy.signature,
    rpc_count: urls.length, observed_at: started / 1000 })}`);
  const attempts = urls.map(async (url, index) => {
    const connection = new Connection(url, { commitment: "confirmed", disableRetryOnRateLimit: true,
      fetch: (request, options) => fetch(request, { ...options,
        signal: AbortSignal.any([controller.signal, AbortSignal.timeout(8000)]) }) });
    try {
      await confirmSignedTransaction(connection, strategy, raw, options, controller.signal);
      return { index };
    } catch (error) {
      // A confirmed chain failure is a verdict, not a transport failure that
      // another provider should conceal. Processed/unknown status is pending.
      if (error.transactionFailed) return { index, error };
      throw error;
    }
  });
  observe("started");
  try {
    let result;
    try {
      result = await Promise.race([Promise.any(attempts), deadline]);
    } catch (error) {
      if (error instanceof AggregateError) {
        throw new Error(`${label} RPC confirmation unavailable; signed status remains pending`);
      }
      throw error;
    }
    if (result.error) {
      outcome = "chain_failure";
      throw result.error;
    }
    outcome = "confirmed";
    confirmedRpcIndex = result.index;
    console.warn(`[TX] ${JSON.stringify({ stage: `${logStage}-confirmed`, signature: strategy.signature,
      rpc_index: result.index, elapsed_ms: Date.now() - started })}`);
  } finally {
    clearTimeout(timer);
    controller.abort();
    observe("finished", { outcome, confirmed_rpc_index: confirmedRpcIndex });
  }
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

// Empty-account closes bypass transfer hooks/pauses; other extensions stay excluded.
// The SPL program enforces emptiness and owner authority atomically.
function tokenAccountCanClose(account, owner, raw = "0") {
  const { TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID } = require("@solana/spl-token");
  const info = account.data?.parsed?.info, extensions = info?.extensions;
  const program = account.owner?.toString();
  const supported = program === TOKEN_PROGRAM_ID.toString()
    || program === TOKEN_2022_PROGRAM_ID.toString()
      && Array.isArray(extensions) && extensions.length > 0 && extensions.every(e=>
        e?.extension === "immutableOwner" || raw === "0" && (e?.extension === "pausableAccount"
          || e?.extension === "transferHookAccount" && e.state?.transferring === false));
  return supported && info?.owner === owner && (info.closeAuthority || owner) === owner
    && info.tokenAmount?.amount === raw && info.state === "initialized"
    && info.isNative === false && !info.delegate
    && Number.isSafeInteger(account.lamports) && account.lamports > 0;
}

async function reclaimEmptyAccounts(execute = false, batch = false) {
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
        return tokenAccountCanClose(account, owner) && !excluded.has(info.mint);
      });
      let nativeBalance = null;
      if (batch && accounts.length === 1) {
        try { nativeBalance = (await connection.getBalanceAndContext(wallet.publicKey, "finalized")).value; }
        catch { /* Unknown liquidity cannot authorize a singleton maintenance fee. */ }
      }
      return { connection, accounts, nativeBalance };
    });
    if (state.pending) return state.pending;
    // ponytail: eight accounts per invocation keeps legacy transactions small;
    // the maintenance timer handles remaining accounts on its next interval.
    const accounts = state.accounts.slice(0, 8);
    const result = { success: true, dry_run: !execute || process.env.DRY_RUN === "true",
      eligible: state.accounts.length, accounts: accounts.map(a => ({ account: a.pubkey.toString(),
        mint: a.account.data.parsed.info.mint, program: a.account.owner.toString(), rent_lamports: a.account.lamports })),
      recovered_lamports_before_fee: accounts.reduce((sum, a) => sum + a.account.lamports, 0) };
    let entryLiquidityShortfall = null;
    if (batch) {
      result.batch_minimum_accounts = 2;
      if (accounts.length === 1) {
        const balance = state.nativeBalance;
        if (!Number.isSafeInteger(balance) || balance < 0) {
          return { ...result, deferred: true, reason: "native_balance_unmeasured" };
        }
        result.native_balance_lamports = balance;
        const policy = nativeCashPolicy();
        // Reserve pressure keeps its existing exception. A separate entry
        // liquidity gap is useful only if the measured net refund closes it.
        if (balance - policy.native_reserve_lamports >= result.recovered_lamports_before_fee) {
          const gap = policy.entry_floor_lamports - balance;
          if (gap <= 0 || result.recovered_lamports_before_fee < gap) {
            return { ...result, deferred: true, reason: "waiting_for_second_empty_account" };
          }
          entryLiquidityShortfall = gap;
          result.entry_liquidity_floor_lamports = policy.entry_floor_lamports;
          result.entry_liquidity_shortfall_lamports = gap;
        }
      }
    }
    if (result.dry_run || !accounts.length) return result;
    const connection = state.connection;
    const tx = new Transaction();
    for (const a of accounts) tx.add(createCloseAccountInstruction(a.pubkey, wallet.publicKey, wallet.publicKey, [], a.account.owner));
    // A finalized hash is already available to the bank measuring the fee.
    const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("finalized");
    tx.recentBlockhash = blockhash;
    tx.feePayer = wallet.publicKey;
    const fee = (await connection.getFeeForMessage(tx.compileMessage(), "confirmed")).value;
    if (!Number.isSafeInteger(fee) || fee < 0 || fee >= result.recovered_lamports_before_fee) {
      throw new Error("Rent reclaim refused: unknown or uneconomic network fee");
    }
    if (entryLiquidityShortfall !== null && result.recovered_lamports_before_fee-fee < entryLiquidityShortfall) {
      return {...result, deferred: true, reason: "singleton_net_below_entry_floor", fee_lamports: fee};
    }
    tx.sign(wallet);
    const raw = tx.serialize(), signature = bs58.encode(tx.signature);
    fs.mkdirSync(path.dirname(pendingPath), { recursive: true, mode: 0o700 });
    fs.writeFileSync(pendingPath, JSON.stringify({ signature, blockhash, lastValidBlockHeight }), { mode: 0o600, flag: "wx", flush: true });
    recordSubmission(wallet, null, "rent_reclaim", signature, lastValidBlockHeight);
    await confirmSignedTransaction(connection, { signature, blockhash, lastValidBlockHeight }, raw);
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
  if (post < nativeCashPolicy().native_reserve_lamports) throw new Error("ENTRY REFUSED: rent/fees would breach 0.2 SOL native reserve");
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
  const pdaHistories = new Map();
  try {
    return await runWithFailover(async (connection) => {
      let submitted = false;
      const txHashes = [];
      let newPosition = Keypair.generate();
      let positionCreation = {kind: "keypair"};
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
        // Overlap the bounded optional lookup with existing snapshot/build
        // reads, retaining late replies without extending the entry wait.
        // It is never retried if unavailable or the build fails.
        let pdaHistory = null;
        if (binsBelow + binsAbove <= 69) try {
          const range = `${minBinId}:${maxBinId}`;
          if (!pdaHistories.has(range)) pdaHistories.set(range,
            require("./dlmm_position_pda").beginPositionPdaHistory({pool, wallet: wallet.publicKey,
              lower: minBinId, upper: maxBinId, entryDir, rpcUrl: connection.rpcEndpoint}));
          pdaHistory = pdaHistories.get(range);
        } catch { /* Keep the ordinary initialization. */ }
        let snapshots = { bin_snapshot: null, width_study: null };
        const solMint = "So11111111111111111111111111111111111111112";
        const studySide = strategyTypeStr !== "bid_ask" ? null
          : pool.lbPair.tokenYMint.toString() === solMint && amountX === 0 && binsAbove === 0 ? "below"
          : pool.lbPair.tokenXMint.toString() === solMint && amountY === 0 && binsBelow === 0 ? "above" : null;
        try { snapshots = await entryBinSnapshots(pool, minBinId, maxBinId, studySide); }
        catch { console.warn("[SHADOW] Entry bin snapshot unavailable"); }

        const persistEntry = () => fs.writeFileSync(path.join(entryDir, `${newPosition.publicKey}.json`), JSON.stringify({
          ...context, ...snapshots, root_chain_id: context.root_chain_id || context.recenter_of || newPosition.publicKey.toString(),
          pool: poolAddressStr, position: newPosition.publicKey.toString(),
          entry_bin: activeBin.binId, entry_price: pool.fromPricePerLamport(Number(activeBin.price)),
          bins_below: binsBelow, bins_above: binsAbove, bin_step: Number(pool.lbPair.binStep),
          amount_x: amountX, amount_y: amountY, position_creation: positionCreation,
          deployed_at: Math.floor(Date.now() / 1000),
        }), { mode: 0o600, flag: positionCreation.kind === "wallet_pda" ? "wx" : "w" });
        const send = async (tx, signers, fallback = null) => {
          const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
          const simulate = async candidate => {
            candidate.recentBlockhash = blockhash;
            candidate.lastValidBlockHeight = lastValidBlockHeight;
            candidate.feePayer = wallet.publicKey;
            await assertNativeReserve(connection, wallet, new VersionedTransaction(candidate.compileMessage()));
          };
          try { await simulate(tx); }
          catch (error) {
            if (!fallback || !error.message.includes("simulation unmeasured")) throw error;
            // Only a failed unsigned simulation may switch back. Never rebuild
            // or change identity after persistence, signing or submission.
            newPosition = fallback.signer;
            positionCreation = {kind: "keypair"};
            tx = fallback.transaction;
            signers = [wallet, newPosition];
            await simulate(tx);
          }
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
            await confirmSignedTransaction(rpc, { signature, blockhash, lastValidBlockHeight }, raw);
            return signature;
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
          let tx = await pool.initializePositionAndAddLiquidityByStrategy({
            positionPubKey: newPosition.publicKey, user: wallet.publicKey,
            totalXAmount: totalXLamports, totalYAmount: totalYLamports,
            strategy: { minBinId, maxBinId, strategyType }, slippage: slippageBpsToPercent(slippageBps),
          });
          const fallback = {transaction: tx, signer: newPosition};
          let optimized = null;
          try {
            optimized = await require("./dlmm_position_pda").preparePositionPda({pool, transaction: tx,
              wallet: wallet.publicKey, originalPosition: newPosition.publicKey, lower: minBinId, upper: maxBinId,
              entryDir, rpcUrl: connection.rpcEndpoint, history: pdaHistory});
          } catch { /* An optional optimization cannot prevent an ordinary entry. */ }
          if (optimized) {
            newPosition = {publicKey: optimized.position};
            positionCreation = optimized.creation;
            tx = optimized.transaction;
          }
          await send(tx, optimized ? [wallet] : [wallet, newPosition], optimized ? fallback : null);
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
    for (const history of pdaHistories.values()) history?.cancel?.();
    await release();
  }
}


async function findPoolForPosition(connection, wallet, positionAddressStr) {
  // A local entry is only a pool hint. Prove program, account type, pool and
  // wallet ownership on chain before avoiding the wallet-wide SDK scan.
  let poolHint = null;
  if (path.basename(positionAddressStr) === positionAddressStr) {
    try {
      const entry = JSON.parse(fs.readFileSync(path.join(PROFILE_DIR, "memories", "dlmm_entries",
        `${positionAddressStr}.json`), "utf8"));
      if (entry.position === positionAddressStr && typeof entry.pool === "string") {
        poolHint = new PublicKey(entry.pool);
      }
    } catch { /* Legacy or invalid local evidence uses ordinary discovery. */ }
  }
  if (poolHint) {
    const positionKey = new PublicKey(positionAddressStr);
    const account = await connection.getAccountInfo(positionKey, "confirmed");
    const idl = DLMM.IDL;
    const discriminator = idl.accounts.find(a => a.name === "PositionV2")?.discriminator;
    if (account && account.owner.toString() === idl.address && discriminator
        && account.data.subarray(0, 8).equals(Buffer.from(discriminator))) {
      const pool = await DLMM.create(connection, poolHint);
      const native = pool.program.coder.accounts.decode("positionV2", account.data);
      if (native.owner.toString() === wallet.publicKey.toString()
          && native.lbPair.toString() === poolHint.toString()) {
        const positionData = await pool.getPosition(positionKey);
        if (positionData.publicKey.toString() === positionAddressStr
            && positionData.positionData.owner.toString() === wallet.publicKey.toString()) {
          return { pool, positionData, poolAddressStr: poolHint.toString() };
        }
      }
    }
  }
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

// Best-effort phase boundaries: never persist endpoint URLs, errors or signed bytes.
function closePreparationObserver(position, emptyOnly) {
  try {
    const { performance } = require("node:perf_hooks");
    const started = performance.now();
    const attempt = require("node:crypto").randomUUID();
    const journal = path.join(PROFILE_DIR, "memories", "dlmm_close_preparations.jsonl");
    let previous = started;
    return (stage, signature = null) => {
      try {
        const now = performance.now();
        const record = { version: 1, attempt, position, empty_only: emptyOnly, stage,
          observed_at: Date.now() / 1000, elapsed_ms: now - started,
          since_previous_ms: now - previous, signature,
          basis: "client_preparation_observation_not_finalized_execution" };
        previous = now;
        fs.mkdirSync(path.dirname(journal), { recursive: true, mode: 0o700 });
        fs.appendFileSync(journal, JSON.stringify(record) + "\n", { mode: 0o600 });
      } catch (_) { /* Timing evidence must never prevent an exit. */ }
    };
  } catch (_) { return () => {}; }
}

async function closePosition(positionAddressStr, emptyOnly = false) {
  if (process.env.DRY_RUN === "true" && (positionAddressStr.includes("DRY_RUN") || positionAddressStr.length < 32)) {
    console.warn(JSON.stringify({ success: true, dryRun: true, txHashes: ["DRY_RUN_TX_HASH"] }));
    return { success: true, dryRun: true, txHashes: ["DRY_RUN_TX_HASH"] };
  }
  new PublicKey(positionAddressStr);
  const observe = closePreparationObserver(positionAddressStr, emptyOnly);
  observe("started");
  let release;
  try {
    release = await acquireSwapLock(`close-${positionAddressStr}`);
    observe("lock_acquired");
    const result = await closePositionLocked(positionAddressStr, emptyOnly, observe);
    observe(result.success ? "completed" : result.pending ? "pending" : "refused");
    return result;
  } catch (error) {
    observe("failed");
    throw error;
  } finally {
    if (release) await release();
  }
}

async function closePositionLocked(positionAddressStr, emptyOnly = false, observe = () => {}) {
  const pendingDir = path.join(PROFILE_DIR, "memories", "dlmm_pending_closes");
  const pendingPath = path.join(pendingDir, `${positionAddressStr}.json`);
  let submittedSignature;
  let submissionError;
  if (fs.existsSync(pendingPath)) {
    observe("pending_reconciliation_started");
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
        const raw = Buffer.from(pending.raw, "base64");
        if (pending.emptyOnly) {
          await runWithFailover(c => confirmSignedTransaction(c, pending, raw));
        } else {
          await confirmCloseTransaction(pending, raw);
        }
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

    observe("lookup_started");
    const foundPos = await findPoolForPosition(connection, wallet, positionAddressStr);
    observe("lookup_completed");
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
      observe("blockhash_started");
      const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
      observe("blockhash_completed");
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
      observe("signed_and_persisted", signature);
      console.warn(`[TX] ${JSON.stringify({stage: "close-send", signature: submittedSignature,
        position: positionAddressStr, blockhash, lastValidBlockHeight})}`);
      // The persisted signature is reused across concurrent RPC broadcasts and
      // restarts. A timeout cannot authorize a replacement transaction.
      try {
        const strategy = { signature, blockhash, lastValidBlockHeight };
        if (emptyOnly) {
          await runWithFailover(rpc => confirmSignedTransaction(rpc, strategy, raw));
        } else {
          await confirmCloseTransaction(strategy, raw);
        }
      } catch (err) {
        submissionError = err.message;
        throw err;
      }
      observe("confirmation_completed", signature);
      fs.rmSync(pendingPath, { force: true });
      submittedSignature = null;
      return signature;
    };

    // The program checks emptiness atomically. Never withdraw liquidity on this path,
    // even if a deposit lands after the SDK read above.
    if (emptyOnly) {
      observe("empty_close_build_started");
      const txs = await pool.closePositionIfEmpty({ owner: wallet.publicKey, position: positionData });
      observe("empty_close_build_completed");
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
      observe("withdrawal_build_started");
      const closeTx = await pool.removeLiquidity({
        user: wallet.publicKey,
        position: positionData.publicKey,
        fromBinId: lowerBin,
        toBinId: upperBin,
        bps: new BN(10000), // 100%
        shouldClaimAndClose: true
      });
      observe("withdrawal_build_completed");
      for (const tx of Array.isArray(closeTx) ? closeTx : [closeTx]) {
        txHashes.push(await sendClose(tx));
      }
    } catch (rmErr) {
      // closePositionIfEmpty succeeds as a no-op on funded positions. Only use it when
      // the SDK snapshot positively proves every liquidity share is zero.
      if (submittedSignature || positionIsEmpty(positionData) !== true) throw rmErr;
      console.warn(`[DLMM] removeLiquidity failed (${rmErr.message}); attempting closePositionIfEmpty for empty position ${positionAddressStr}`);
      observe("empty_recovery_started");
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

async function getPositionRiskMark(poolAddressStr, positionAddressStr) {
  try {
    const context = riskMark.loadInitialContext(PROFILE_DIR, poolAddressStr, positionAddressStr);
    riskMark.check(context.submission.wallet === process.env.SOLANA_PUBLIC_KEY, "profile wallet mismatch");
    return await runWithFailover(async connection => {
      // This path needs a public identity and confirmed transfers, never a signer
      // or the indexed PnL API that it is meant to independently verify.
      const positionKey = new PublicKey(positionAddressStr);
      const [pool, account, transaction] = await Promise.all([
        DLMM.create(connection, new PublicKey(poolAddressStr)),
        connection.getAccountInfo(positionKey, "confirmed"),
        connection.getParsedTransaction(context.submission.signature,
          {commitment: "confirmed", maxSupportedTransactionVersion: 0}),
      ]);
      const idl = DLMM.IDL;
      const discriminator = idl.accounts.find(a => a.name === "PositionV2").discriminator;
      riskMark.check(account && account.owner.toString() === idl.address
        && account.data.subarray(0, 8).equals(Buffer.from(discriminator)), "native position account mismatch");
      const native = pool.program.coder.accounts.decode("positionV2", account.data);
      const fundingBinding = {
        definition: idl.instructions.find(i => i.name === "add_liquidity_by_strategy2"),
        initializeDefinitions: idl.instructions.filter(i => ["initialize_position", "initialize_position2", "initialize_position_pda"].includes(i.name)),
        decode: bs58.decode, programId: idl.address,
        tokenX: pool.lbPair.tokenXMint.toString(), tokenY: pool.lbPair.tokenYMint.toString(),
        reserveX: pool.lbPair.reserveX.toString(), reserveY: pool.lbPair.reserveY.toString(),
        decodeInstruction: data => pool.program.coder.instruction.decode(data, "base58"),
        decodeEvent: data => pool.program.coder.events.decode(data),
      };
      const deposit = riskMark.initialDeposit(transaction, context, fundingBinding);
      const position = await pool.getPosition(positionKey);
      // Check after inventory reads: extra add/withdraw/claim transactions make
      // an initial-deposit-only denominator invalid, including unjournaled ones.
      riskMark.onlyInitialSignature(await connection.getSignaturesForAddress(positionKey,
        {limit: 2}, "confirmed"), context);
      // A concurrent local close/claim must not leave an apparently usable mark.
      const latest = riskMark.loadInitialContext(PROFILE_DIR, poolAddressStr, positionAddressStr);
      riskMark.check(latest.submission.signature === context.submission.signature, "funding changed during read");
      const mark = riskMark.markInventory(context, native, position.positionData, pool.lbPair, deposit);
      const allocation = riskMark.initialFundingAllocation(transaction, context, fundingBinding, deposit);
      if (allocation) mark.bin_observation.initial_funding = allocation;
      // Display/entry metadata only: risk valuation above retains exact rational
      // lamport arithmetic. Reuse the fetched pool instead of another RPC read.
      const price = Number(pool.fromPricePerLamport(Number(DLMM.getPriceOfBinByBinId(pool.lbPair.activeId, pool.lbPair.binStep))));
      if (Number.isFinite(price) && price > 0) mark.pool_price = price;
      return mark;
    });
  } catch (error) {
    return {success: false, source: riskMark.SOURCE, position: positionAddressStr, pool: poolAddressStr,
      reason: error.riskMarkUnavailable ? error.message : "Native risk mark unavailable: incomplete read or funding evidence"};
  }
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

async function settlementRentClose(connection, wallet, transaction, mint, raw, evidence = null) {
  const position = process.env.DLMM_SETTLEMENT_POSITION;
  if (!position || !/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(position)) return transaction;
  try {
    const marker = JSON.parse(fs.readFileSync(path.join(PROFILE_DIR, "memories", "dlmm_settlements", `${position}.json`), "utf8"));
    if (marker.position !== position || marker.mint !== mint || transaction.message.header.numRequiredSignatures !== 1
        || transaction.message.staticAccountKeys?.[0]?.toString() !== wallet.publicKey.toString()) return transaction;
    if (evidence ? evidence.position !== position || evidence.positionClosed !== true
                 : await positionAccountExists(connection, position)) return transaction;
    const accounts = evidence?.accounts || await connection.getParsedTokenAccountsByOwner(wallet.publicKey, { mint: new PublicKey(mint) }, "confirmed");
    // ponytail: one full-balance account only; leave split/unsupported inventory to the existing recovery gate.
    if (accounts.value.length !== 1) return transaction;
    const account = accounts.value[0];
    if (account.account.data?.parsed?.info?.mint !== mint
        || !tokenAccountCanClose(account.account, wallet.publicKey.toString(), raw)) return transaction;
    const tables = await Promise.all(transaction.message.addressTableLookups.map(async lookup =>
      (await connection.getAddressLookupTable(lookup.accountKey)).value));
    if (tables.some(table => !table)) return transaction;
    const message = TransactionMessage.decompile(transaction.message, { addressLookupTableAccounts: tables });
    const { createCloseAccountInstruction } = require("@solana/spl-token");
    message.instructions.push(createCloseAccountInstruction(account.pubkey, wallet.publicKey, wallet.publicKey, [], account.account.owner));
    const combined = new VersionedTransaction(message.compileToV0Message(tables));
    if (combined.serialize().length > 1232) return transaction;
    return combined; // The SPL program atomically refuses closure unless the preceding swap empties this account.
  } catch {
    return transaction; // Unknown evidence never credits rent; the existing exact simulation still gates the swap.
  }
}

// A successful ordinary settlement can return its own empty ATA rent in the
// same swap. Optional reads/simulation have a shared 250ms budget and their own
// abortable connection; a slow provider must not delay the already valid swap.
async function ordinarySettlementRentClose(connection, wallet, transaction, mint, raw, evidence, measureRecovery) {
  const controller = new AbortController();
  let timer;
  try {
    const marker = JSON.parse(fs.readFileSync(path.join(PROFILE_DIR, "memories", "dlmm_settlements", `${evidence.position}.json`), "utf8"));
    if (marker.emergency_exit !== false) return null;
    const readConnection = new Connection(connection.rpcEndpoint, {commitment: "confirmed", disableRetryOnRateLimit: true,
      fetch: (url, options) => fetch(url, {...options, signal: controller.signal})});
    const timeout = new Promise(resolve => {
      timer = setTimeout(() => {controller.abort(); resolve(null);}, 250);
    });
    const candidate = (async () => {
      const combined = await settlementRentClose(readConnection, wallet, transaction, mint, raw, evidence);
      if (combined === transaction) return null;
      const net = await measureRecovery(combined, readConnection);
      return !Number.isSafeInteger(net) ? null : {transaction: combined, net,
        rentLamports: evidence.accounts.value[0].account.lamports};
    })();
    return await Promise.race([candidate.catch(() => null), timeout]);
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
    controller.abort();
  }
}

async function settlementInventory(position, mint, wallet) {
  if (!/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(position)) throw new Error("Invalid settlement position");
  const marker = JSON.parse(fs.readFileSync(path.join(PROFILE_DIR, "memories", "dlmm_settlements", `${position}.json`), "utf8"));
  if (marker.position !== position || marker.mint !== mint) throw new Error("Settlement marker mismatch");
  const read = () => JSON.parse(require("child_process").execFileSync("python3", [
    path.join(SCRIPT_DIR, "dlmm_accounting.py"), "--profile", PROFILE_DIR,
    "--settlement-inventory", position, mint, wallet], { encoding: "utf8", timeout: 20000 }));
  let proof = read();
  if (proof.pending_signatures?.length) {
    await reconcileAccounting(new Set(proof.pending_signatures));
    proof = read();
    if (proof.pending_signatures?.length) {
      // A null transaction cannot prove expiry. Refresh the same finalized
      // history proof as accounting, instead of waiting for its periodic run.
      const pending = new Set(proof.pending_signatures), now = Math.floor(Date.now()/1000);
      const events = fs.readFileSync(path.join(PROFILE_DIR, "memories", "dlmm_transactions.jsonl"), "utf8")
        .split("\n").filter(Boolean).map(JSON.parse).filter(e => pending.has(e.signature)
          && e.kind === "swap" && e.position === position && e.wallet === wallet
          && Number.isSafeInteger(e.ts) && e.ts > 0 && now-e.ts > 120
          && Number.isSafeInteger(e.lastValidBlockHeight) && e.lastValidBlockHeight > 0);
      if (events.length) {
        try {
          const height = await runWithFailover(c => c.getBlockHeight("finalized"));
          if (events.some(e => Number.isSafeInteger(height) && height > e.lastValidBlockHeight)) {
            const { collect } = require("./dlmm_nav.js");
            await collect({dir:path.join(PROFILE_DIR, "memories"), wallet, PublicKey,
              rpc:runWithFailover, historyOnly:true, includeRentHistory:false});
            proof = read();
          }
        } catch (_) {
          console.warn("[SETTLEMENT] Expiry evidence unavailable; inventory remains unproven");
        }
      }
    }
  }
  return proof;
}

async function swapToken(inputMintStr, outputMintStr, amountFloat, maxPriceImpactPct = 5, slippageBps = 100, minNetLamports = null, smallSettlement = false) {
  const input_mint = normalizeMint(inputMintStr);
  const output_mint = normalizeMint(outputMintStr);
  if (minNetLamports !== null && (!Number.isSafeInteger(minNetLamports) || minNetLamports < 1
      || output_mint !== "So11111111111111111111111111111111111111112" || input_mint === output_mint)) {
    throw new Error("Net recovery requires token-to-SOL and a positive integer lamport floor");
  }
  if (smallSettlement && (slippageBps !== 100 || minNetLamports === null
      || !process.env.DLMM_SETTLEMENT_POSITION)) {
    throw new Error("Small-settlement allowance requires an owned settlement, 100 bps and a net recovery floor");
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

    let inventory;
    if (process.env.DLMM_SETTLEMENT_POSITION) {
      if (output_mint !== "So11111111111111111111111111111111111111112" || input_mint === output_mint) {
        throw new Error("Settlement requires token-to-SOL");
      }
      inventory = await settlementInventory(process.env.DLMM_SETTLEMENT_POSITION, input_mint, wallet.publicKey.toString());
      if (!inventory.success) return inventory;
      if (inventory.amount_raw === "0") return { success: true, settled: true, inputAmount: "0" };
    }

    // Fetch quote outside runWithFailover as it's a HTTP call to Jupiter, then execute/send via standard RPC rotation
    let quoteResponse, quoteObservedAt, inputRaw, selectedSlippageBps = slippageBps;
    try {
    // 1. Get input decimals
    let decimals = 9;
    if (!inventory && input_mint !== "So11111111111111111111111111111111111111112") {
      // We'll perform a quick connection just to fetch decimals
      await runWithFailover(async (connection) => {
        const mintInfo = await connection.getParsedAccountInfo(new PublicKey(input_mint));
        decimals = mintInfo.value?.data?.parsed?.info?.decimals;
      });
    }
    const amountRaw = inventory ? swapAmountRaw(inventory.amount_raw, 0) : swapAmountRaw(amountFloat, decimals);
    if (inventory && amountFloat !== `raw:${amountRaw}`) {
      return { success: false, aborted: true, reason: "settlement_amount_mismatch" };
    }
    inputRaw = amountRaw;

    // 2. Fetch a quote within the authorized slippage limit.
    // The explicit small-settlement allowance caps another 200 bps at the
    // 5,000-lamport base transaction fee. Larger ordinary exits stay at 100.
    const smallOutLimit = 250000n;
    const slippageLadder = [slippageBps];
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
        if (inventory && (q?.inputMint !== input_mint || q?.outputMint !== output_mint || q?.inAmount !== amountRaw)) {
          return { success: false, aborted: true, reason: "settlement_quote_mismatch" };
        }
        if (!q || !q.outAmount || q.outAmount === "0") {
          lastErr = `Jupiter returned empty quote at slippage ${bps}bps (no route/liquidity)`;
          continue;
        }
        if (smallSettlement) {
          if (typeof q.outAmount !== "string" || !/^[0-9]+$/.test(q.outAmount) || BigInt(q.outAmount) <= 0n) {
            return { success: false, aborted: true, reason: "net_recovery_invalid_quote" };
          }
          if (bps === 100 && BigInt(q.outAmount) <= smallOutLimit) {
            // Never rewrite a saved quote's threshold. Requote the same owned
            // input at the allowed ceiling, paced for the keyless quote route.
            await new Promise(resolve => setTimeout(resolve, 2100));
            slippageLadder.push(300);
            continue;
          }
          if (bps === 300) {
            if (BigInt(q.outAmount) > smallOutLimit) {
              return { success: false, aborted: true, reason: "small_settlement_value_changed" };
            }
            if (q.swapMode !== "ExactIn" || q.slippageBps !== 300
                || typeof q.otherAmountThreshold !== "string" || !/^[0-9]+$/.test(q.otherAmountThreshold)
                || BigInt(q.otherAmountThreshold) <= 0n || BigInt(q.otherAmountThreshold) > BigInt(q.outAmount)
                || BigInt(q.otherAmountThreshold) < BigInt(q.outAmount) * 9700n / 10000n) {
              return { success: false, aborted: true, reason: "small_settlement_quote_limit_mismatch" };
            }
          }
        }
        quoteResponse = q;
        selectedSlippageBps = bps;
        quoteObservedAt = Math.floor(Date.now() / 1000);
        if (bps !== slippageBps) {
          console.warn(`[DLMM] Small settlement requoted at ${bps}bps; output <= ${smallOutLimit} lamports`);
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
    let settlementRead = null;
    if (inventory) {
      if (await positionAccountExists(connection, process.env.DLMM_SETTLEMENT_POSITION)) {
        return { success: false, reason: "settlement_position_still_open" };
      }
      const accounts = await connection.getParsedTokenAccountsByOwner(wallet.publicKey,
        { mint: new PublicKey(input_mint) }, { commitment: "confirmed", minContextSlot: inventory.slot });
      const raw = accounts.value.reduce((sum, a) => {
        const info = a.account.data.parsed.info;
        if (info.owner !== wallet.publicKey.toString() || info.mint !== input_mint) throw new Error("Invalid settlement token account");
        return sum + BigInt(info.tokenAmount.amount);
      }, 0n);
      if (raw.toString() !== inventory.wallet_balance_raw || raw < BigInt(inputRaw)) {
        return { success: false, reason: "settlement_inventory_changed" };
      }
      settlementRead = {position: process.env.DLMM_SETTLEMENT_POSITION, positionClosed: true, accounts};
    }
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
    let transaction = VersionedTransaction.deserialize(swapTransactionBuf);
    let tokenRentCloseIncluded = false;
    let ordinaryTokenRentClose = false;
    let netRecoveryEvidence = null;
    
    const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
    transaction.message.recentBlockhash = blockhash;
    // Optional residual recovery: simulate the exact unsigned transaction and
    // reserve the entire quoted slippage allowance before authorizing a send.
    if (minNetLamports !== null) {
      const out = Number(quoteResponse.outAmount), minimum = Number(quoteResponse.otherAmountThreshold);
      if (!Number.isSafeInteger(out) || !Number.isSafeInteger(minimum) || minimum <= 0 || minimum > out) {
        return { success: false, aborted: true, reason: "net_recovery_invalid_quote" };
      }
      const recoveryMeasurements = new WeakMap();
      const measureRecovery = async (candidate, readConnection = connection) => {
        const messageHash = require("crypto").createHash("sha256")
          .update(candidate.message.serialize()).digest("hex");
        const before = await readConnection.getBalanceAndContext(wallet.publicKey, "confirmed");
        const simulated = await readConnection.simulateTransaction(candidate, {
          commitment: "confirmed", sigVerify: false, minContextSlot: before.context.slot,
          accounts: { encoding: "base64", addresses: [wallet.publicKey.toString()] }
        });
        const after = await readConnection.getBalanceAndContext(wallet.publicKey,
          { commitment: "confirmed", minContextSlot: simulated.context.slot });
        const post = simulated.value.accounts?.[0]?.lamports;
        if (simulated.value.err || !Number.isSafeInteger(post) || !Number.isSafeInteger(before.value)
            || before.value !== after.value) return null;
        const currentHash = require("crypto").createHash("sha256")
          .update(candidate.message.serialize()).digest("hex");
        if (currentHash !== messageHash) return null;
        recoveryMeasurements.set(candidate, {
          message_sha256: messageHash,
          simulation_slot: simulated.context.slot,
          wallet_read_before_slot: before.context.slot,
          wallet_read_after_slot: after.context.slot,
          simulated_wallet_delta_lamports: post - before.value,
        });
        return post - before.value - (out - minimum);
      };
      let conservativeNet = await measureRecovery(transaction);
      if (conservativeNet === null) {
        return { success: false, aborted: true, reason: "net_recovery_unmeasured" };
      }
      if (conservativeNet < minNetLamports && quoteResponse.inputMint === input_mint
          && quoteResponse.outputMint === output_mint && quoteResponse.inAmount === inputRaw) {
        const combined = await settlementRentClose(connection, wallet, transaction, input_mint, inputRaw);
        if (combined !== transaction) {
          const withRent = await measureRecovery(combined);
          if (withRent !== null && withRent >= minNetLamports) {
            transaction = combined; conservativeNet = withRent; tokenRentCloseIncluded = true;
          }
        }
      } else if (smallSettlement && selectedSlippageBps === 100 && settlementRead
          && quoteResponse.inputMint === input_mint && quoteResponse.outputMint === output_mint
          && quoteResponse.inAmount === inputRaw && quoteResponse.swapMode === "ExactIn"
          && quoteResponse.slippageBps === 100) {
        const candidate = await ordinarySettlementRentClose(connection, wallet, transaction,
          input_mint, inputRaw, settlementRead, measureRecovery);
        // Rent is an existing asset, not profit. Do not accept a worse simulated
        // sale merely because adding the refund makes its cash receipt larger.
        if (candidate && candidate.net - candidate.rentLamports >= conservativeNet) {
          transaction = candidate.transaction; conservativeNet = candidate.net;
          tokenRentCloseIncluded = ordinaryTokenRentClose = true;
        }
      }
      if (conservativeNet < minNetLamports) {
        return { success: false, aborted: true, reason: "net_recovery_below_floor",
          conservativeNetLamports: conservativeNet, minNetLamports };
      }
      // Preserve the exact selected simulation's gate value, including any
      // accepted rent-close variant. This is cash recovery, not position profit.
      netRecoveryEvidence = {
        version: 1, recorded_at: Date.now() / 1000,
        ...recoveryMeasurements.get(transaction),
        conservative_wallet_delta_lamports: conservativeNet,
        required_minimum_lamports: minNetLamports,
        reserved_quote_slippage_lamports: out - minimum,
        token_rent_close_included: tokenRentCloseIncluded,
        basis: "unsigned_selected_transaction_simulated_wallet_delta_minus_quote_slippage; includes_account_debits_and_refunds; not_realized_proceeds_or_position_profit",
      };
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
    const txid = signedTxid;
    recordSubmission(wallet, process.env.DLMM_SETTLEMENT_POSITION, "swap", signedTxid, lastValidBlockHeight, {
      observed_at: quoteObservedAt, input_mint, output_mint,
      in_amount: quoteResponse.inAmount, out_amount: quoteResponse.outAmount,
      minimum_out_amount: quoteResponse.otherAmountThreshold ?? null,
      authorized_slippage_bps: selectedSlippageBps, context_slot: quoteResponse.contextSlot ?? null,
      small_settlement_requote: smallSettlement && selectedSlippageBps === 300,
      token_rent_close_included: tokenRentCloseIncluded,
      ordinary_token_rent_close: ordinaryTokenRentClose,
      ...(netRecoveryEvidence ? { net_recovery: netRecoveryEvidence } : {}),
      price_impact_pct: quoteResponse.priceImpactPct ?? null,
      basis: "provider_quote_before_broadcast; raw_token_units; not_realized_proceeds",
    });
    submittedSignature = signedTxid;
    try {
      const strategy = { blockhash, lastValidBlockHeight, signature: txid };
      const options = { skipPreflight: true, maxRetries: RPC_SEND_MAX_RETRIES };
      if (inventory) await confirmExitTransaction(strategy, rawTransaction, "settlement_swap", options);
      else await confirmSignedTransaction(connection, strategy, rawTransaction, options);
    } catch (err) {
      if (err.transactionFailed) {
        fs.rmSync(pendingPath, { force: true });
        return { success: false, txHash: txid, error: err.message };
      }
      // The bounded fanout already sought a confirmed verdict from every
      // configured provider. Leave the persisted signature for the next tick;
      // another unbounded read here must not hold up the settlement worker.
      if (inventory) return { success: false, pending: true, txHash: txid,
        error: `Settlement swap confirmation pending: ${err.message}` };
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

async function entryBinSnapshots(pool, lower, upper, studySide) {
  // Observe a fixed 70-bin alternative alongside the actual mint range. This
  // changes only the read bounds; transaction construction retains lower/upper.
  const studyLower = studySide === "below" ? Math.min(lower, upper - 69) : lower;
  const studyUpper = studySide === "above" ? Math.max(upper, lower + 69) : upper;
  if (studyLower === lower && studyUpper === upper) {
    return { bin_snapshot: await binSnapshot(pool, lower, upper), width_study: null };
  }
  try {
    const snapshot = await binSnapshot(pool, studyLower, studyUpper);
    return {
      bin_snapshot: { ...snapshot, bins: snapshot.bins.filter(b => b.id >= lower && b.id <= upper) },
      width_study: { target_bins: 70, lower_bin: studyLower, upper_bin: studyUpper, snapshot },
    };
  } catch (_) {
    // An unavailable wider observation must not erase the original baseline.
    return { bin_snapshot: await binSnapshot(pool, lower, upper), width_study: null };
  }
}

async function binSnapshot(pool, lower, upper, mayRead = () => true) {
  if (!mayRead()) return {status: "deferred", reason: "wallet_trade_active"};
  const data = await pool.getBinsBetweenLowerAndUpperBound(lower, upper);
  if (!mayRead()) return {status: "deferred", reason: "wallet_trade_active"};
  const active = await pool.getActiveBin();
  return {ts: Math.floor(Date.now()/1000), active_bin: active.binId,
    price: Number(pool.fromPricePerLamport(Number(active.price))),
    decimals_x: pool.tokenX.mint.decimals, decimals_y: pool.tokenY.mint.decimals,
    sol_is_x: pool.lbPair.tokenXMint.toString() === "So11111111111111111111111111111111111111112",
    bins: data.bins.map(b => ({id:b.binId, x:b.xAmount.toString(), y:b.yAmount.toString(),
      supply:b.supply.toString(), fee_x:b.feeAmountXPerTokenStored.toString(),
      fee_y:b.feeAmountYPerTokenStored.toString(), price:Number(b.pricePerToken)}))};
}

// Background evidence only. The caller caps this process at three seconds;
// never load a signing key or acquire a lock ahead of the trading workers.
async function candidateBinSnapshot(poolAddress, below = 69, above = 16, fixedAnchor = null) {
  if (!Number.isInteger(below) || below < 0 || below > 69
      || !Number.isInteger(above) || above < 0 || above > 16) {
    throw new Error("Invalid candidate snapshot bounds");
  }
  if (fixedAnchor !== null && (!Number.isSafeInteger(fixedAnchor) || Math.abs(fixedAnchor) > 100000)) {
    throw new Error("Invalid candidate snapshot anchor");
  }
  const address = new PublicKey(poolAddress);
  const wallet = process.env.SOLANA_PUBLIC_KEY;
  if (!wallet) throw new Error("Candidate snapshots require SOLANA_PUBLIC_KEY");
  new PublicKey(wallet);
  const started = Date.now();
  const mayRead = () => !require("./dlmm_nav").walletTradeActive(wallet);
  if (!mayRead()) return {status: "deferred", reason: "wallet_trade_active"};
  return runWithFailover(async connection => {
    if (!mayRead()) return {status: "deferred", reason: "wallet_trade_active"};
    const pool = await DLMM.create(connection, address);
    const tokenX = pool.lbPair.tokenXMint.toString(), tokenY = pool.lbPair.tokenYMint.toString();
    if (tokenY !== "So11111111111111111111111111111111111111112" || tokenX === tokenY) {
      throw new Error("Candidate snapshot requires SOL as token Y");
    }
    const anchor = fixedAnchor === null ? pool.lbPair.activeId : fixedAnchor;
    if (!Number.isSafeInteger(anchor)) throw new Error("Invalid candidate active bin");
    const snapshot = await binSnapshot(pool, anchor - below, anchor + above, mayRead);
    if (snapshot.status === "deferred") return snapshot;
    let canonical;
    try {
      canonical = await require("./dlmm_canonical_liquidity").observeCanonicalLiquidity(connection.rpcEndpoint, tokenX,
        {mayRead, timeoutMs: Math.max(0, 2000 - (Date.now() - started))});
    } catch {
      canonical = {version: 1, status: "unmeasured", reason: "native_evidence_unavailable",
        base_mint: tokenX, quote_mint: tokenY, request_started_at: Date.now()/1000, observed_at: Date.now()/1000};
    }
    return {...snapshot, status: "observed", pool: address.toString(),
      bin_step: Number(pool.lbPair.binStep), canonical_liquidity: canonical,
      token_x_mint: tokenX, token_y_mint: tokenY, anchor_bin: anchor,
      lower_bin: anchor - below, upper_bin: anchor + above,
      basis: "native_candidate_pool_bin_state_not_position_return"};
  });
}

// Read-only reconciliation. A missing transaction remains unknown, never zero.
async function reconcileAccounting(signatures = null) {
  const dir = path.join(PROFILE_DIR, "memories");
  const readRows = (name) => {
    const file = path.join(dir, name);
    return fs.existsSync(file) ? fs.readFileSync(file, "utf8").split("\n").filter(Boolean).map(JSON.parse) : [];
  };
  const events = [...new Map(readRows("dlmm_transactions.jsonl").map(e => [e.signature,e])).values()];
  const facts = new Map([...readRows("dlmm_transaction_facts.jsonl"), ...readRows("dlmm_wallet_transactions.jsonl")].map(r => [r.signature, r]));
  let pending = 0;
  for (const event of events) {
    if (signatures && !signatures.has(event.signature)) continue;
    if (facts.has(event.signature)) continue;
    try {
      const { parsedAccountingTransaction, transactionFact } = require("./dlmm_nav.js");
      const tx = await runWithFailover(connection => parsedAccountingTransaction(connection, event.signature));
      // A successful RPC returning null means missing evidence, not provider failure.
      if (!tx?.meta) { pending++; continue; }
      // Share finalized evidence with NAV collection instead of fetching it again.
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
    console.error("No command provided. Exposing: active-bin, deploy, check-bins, claim, close, position-exists, positions, pnl, pnl-onchain, spl-balance, swap");
    process.exit(1);
  }
  
  try {
    if (command === "reclaim-empty-accounts") {
      if (args.slice(1).some(arg => !["--execute", "--batch"].includes(arg))) throw new Error("Usage: reclaim-empty-accounts [--execute] [--batch]");
      console.log(JSON.stringify(await reclaimEmptyAccounts(args.includes("--execute"), args.includes("--batch"))));
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
    } else if (command === "candidate-bin-snapshot") {
      if (args.length < 2 || args.length > 5) throw new Error("Usage: candidate-bin-snapshot <pool> [below=69] [above=16] [fixed_anchor]");
      console.log(JSON.stringify(await candidateBinSnapshot(args[1],
        args[2] === undefined ? 69 : Number(args[2]), args[3] === undefined ? 16 : Number(args[3]),
        args[4] === undefined ? null : Number(args[4]))));
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
    } else if (command === "pnl-onchain") {
      if (args.length !== 3) throw new Error("Usage: pnl-onchain <pool_address> <position_address>");
      console.log(JSON.stringify(await getPositionRiskMark(args[1], args[2])));
    } else if (command === "spl-balance") {
      const token = args[1];
      if (!token) throw new Error("Usage: spl-balance <token_mint>");
      const res = await getSplBalance(token);
      console.log(JSON.stringify(res));
    } else if (command === "settlement-balance") {
      console.log(JSON.stringify(await settlementInventory(args[1], args[2], getWallet().publicKey.toString())));
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
        throw new Error("Usage: swap <input_mint> <output_mint> <amount> [max_price_impact_pct] [slippage_bps] [min_net_lamports] [--small-settlement]");
      }
      const minNetLamports = args[6] != null ? Number(args[6]) : null;
      if (args[7] != null && args[7] !== "--small-settlement" || args.length > 8) {
        throw new Error("Unknown swap option");
      }
      const res = await swapToken(input, output, amount, maxImpact, slipBps, minNetLamports, args[7] === "--small-settlement");
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
module.exports = { settlementInventory, swapAmountRaw, reclaimEmptyAccounts, assertRootBudget, reconcileAccounting, recordSubmission, closePosition, swapToken, confirmSignedTransaction, deployPosition, acquireDeployLock, acquireSwapLock, reconcilePendingSwap,
  assertNoTokenExposure, positionIsEmpty, positionAccountExists, slippageBpsToPercent, settlementRentClose, ordinarySettlementRentClose, tokenAccountCanClose, getPositionRiskMark, candidateBinSnapshot };
