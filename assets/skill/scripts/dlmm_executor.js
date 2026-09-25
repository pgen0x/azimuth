const { Connection, Keypair, PublicKey, VersionedTransaction } = require("@solana/web3.js");
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
      const connection = new Connection(rpcUrl, "confirmed");
      return await fn(connection);
    } catch (err) {
      console.warn(`[RPC WARN] Failed execution on RPC #${currentRpcIndex}: ${err.message}`);
      currentRpcIndex = (currentRpcIndex + 1) % RPC_URLS.length;
      attempts++;
    }
  }
  throw new Error(`All ${RPC_URLS.length} RPC endpoints failed to execute the command.`);
}

// Durable accounting evidence is written before broadcast, including uncertain sends.
function recordSubmission(wallet, position, kind, signature, lastValidBlockHeight) {
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
    kind, signature, lastValidBlockHeight,
  }) + "\n", { mode: 0o600 });
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
    confirmation = await connection.confirmTransaction(strategy, "confirmed");
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

async function reconcilePendingSwap(connection, pendingPath) {
  if (!fs.existsSync(pendingPath)) return null;
  let pending;
  try {
    pending = JSON.parse(fs.readFileSync(pendingPath, "utf8"));
  } catch (err) {
    return { success: false, pending: true, error: `Swap reconciliation blocked by invalid marker: ${err.message}` };
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
      error: "Swap confirmation pending from a previous submission" };
  }
  fs.rmSync(pendingPath, { force: true });
  return null;
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
        fs.writeFileSync(path.join(entryDir, `${newPosition.publicKey}.json`), JSON.stringify({
          ...context, root_chain_id: context.root_chain_id || context.recenter_of || newPosition.publicKey.toString(),
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
          const hash = await connection.sendRawTransaction(raw, {
            preflightCommitment: "confirmed", maxRetries: RPC_SEND_MAX_RETRIES
          });
          await confirmSignedTransaction(connection, { signature: hash, blockhash, lastValidBlockHeight });
          return hash;
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
        if (err.message.startsWith("ENTRY REFUSED:")) return { success: false, error: err.message };
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
  for (const [lbPairKey, posData] of Object.entries(allPositions)) {
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
    const res = await fetch(apiUrl);
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
  const shares = position?.positionData?.liquidityShares;
  return Array.isArray(shares) ? shares.every((share) => share.isZero()) : null;
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

async function closePosition(positionAddressStr) {
  if (process.env.DRY_RUN === "true" && (positionAddressStr.includes("DRY_RUN") || positionAddressStr.length < 32)) {
    console.warn(JSON.stringify({ success: true, dryRun: true, txHashes: ["DRY_RUN_TX_HASH"] }));
    return { success: true, dryRun: true, txHashes: ["DRY_RUN_TX_HASH"] };
  }
  let submittedSignature;
  return await runWithFailover(async (connection) => {
    if (submittedSignature) {
      if (!await positionAccountExists(connection, positionAddressStr)) {
        return { success: true, txHashes: [submittedSignature], reconciled: true };
      }
      return { success: false, pending: true, txHash: submittedSignature,
        error: "Close submission requires on-chain reconciliation; position still exists" };
    }
    const wallet = getWallet();

    const foundPos = await findPoolForPosition(connection, wallet, positionAddressStr);
    if (!foundPos) {
      throw new Error(`Position ${positionAddressStr} not found for user ${wallet.publicKey.toString()}`);
    }
    const { pool, positionData, poolAddressStr } = foundPos;

    if (process.env.DRY_RUN === "true") {
      console.log(`[DRY RUN] Would close position ${positionAddressStr}`);
      return { success: true, dryRun: true };
    }

    // Step 1: Claim any swap fees first to clear state
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

    const sendClose = async (tx) => {
      const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
      tx.recentBlockhash = blockhash;
      tx.feePayer = wallet.publicKey;
      tx.sign(wallet);
      const raw = tx.serialize();
      const signature = bs58.encode(tx.signature);
      recordSubmission(wallet, positionAddressStr, "close", signature, lastValidBlockHeight);
      submittedSignature = signature;
      console.warn(`[TX] ${JSON.stringify({stage: "close-send", signature: submittedSignature,
        position: positionAddressStr, blockhash, lastValidBlockHeight})}`);
      const txHash = await connection.sendRawTransaction(raw, CONFIRM_OPTIONS);
      await confirmSignedTransaction(connection, { signature: txHash, blockhash, lastValidBlockHeight });
      submittedSignature = null;
      return txHash;
    };

    // Step 2: Remove all liquidity and close position
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
    for (const [lbPairKey, posData] of Object.entries(allPositions)) {
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
          tokenX: pool.tokenX.symbol,
          tokenY: pool.tokenY.symbol,
          lower_bin: lowerBinId,
          upper_bin: upperBinId,
          active_bin: activeBin.binId,
          in_range: inRange,
          feeX: pos.feeX.toString(),
          feeY: pos.feeY.toString()
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

async function swapToken(inputMintStr, outputMintStr, amountFloat, maxPriceImpactPct = 5, slippageBps = 100) {
  const input_mint = normalizeMint(inputMintStr);
  const output_mint = normalizeMint(outputMintStr);

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
    let quoteResponse;
    try {
    // 1. Get input decimals
    let decimals = 9;
    if (input_mint !== "So11111111111111111111111111111111111111112") {
      // We'll perform a quick connection just to fetch decimals
      await runWithFailover(async (connection) => {
        const mintInfo = await connection.getParsedAccountInfo(new PublicKey(input_mint));
        decimals = mintInfo.value?.data?.parsed?.info?.decimals ?? 9;
      });
    }
    const amountRaw = Math.floor(amountFloat * Math.pow(10, decimals)).toString();

    // 2. Fetch quote — retry with escalating slippage on failure (thin pools reject tight slippage)
    const slippageLadder = [slippageBps, slippageBps * 3, slippageBps * 8];
    let lastErr = null;
    for (const bps of slippageLadder) {
      try {
        const quoteUrl = `https://api.jup.ag/swap/v1/quote?inputMint=${input_mint}&outputMint=${output_mint}&amount=${amountRaw}&slippageBps=${bps}`;
        const quoteRes = await fetch(quoteUrl);
        if (!quoteRes.ok) {
          lastErr = `Jupiter quote API error: ${quoteRes.status} ${await quoteRes.text()}`;
          continue;
        }
        const q = await quoteRes.json();
        if (!q || !q.outAmount || q.outAmount === "0") {
          lastErr = `Jupiter returned empty quote at slippage ${bps}bps (no route/liquidity)`;
          continue;
        }
        quoteResponse = q;
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        quoteResponse,
        userPublicKey: wallet.publicKey.toString(),
        wrapAndUnwrapSol: true
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
    recordSubmission(wallet, process.env.DLMM_SETTLEMENT_POSITION, "swap", signedTxid, lastValidBlockHeight);
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

// Read-only reconciliation. A missing transaction remains unknown, never zero.
async function reconcileAccounting() {
  const dir = path.join(PROFILE_DIR, "memories");
  const readRows = (name) => {
    const file = path.join(dir, name);
    return fs.existsSync(file) ? fs.readFileSync(file, "utf8").split("\n").filter(Boolean).map(JSON.parse) : [];
  };
  const events = readRows("dlmm_transactions.jsonl");
  const facts = new Map(readRows("dlmm_transaction_facts.jsonl").map(r => [r.signature, r]));
  let pending = 0;
  for (const event of events) {
    if (facts.has(event.signature)) continue;
    try {
      const tx = await runWithFailover(async connection => {
        const result = await connection.getParsedTransaction(event.signature,
          { commitment: "finalized", maxSupportedTransactionVersion: 0 });
        if (!result?.meta) throw new Error("Transaction not indexed/finalized");
        return result;
      });
      const keys = tx.transaction.message.accountKeys.map(k => k.pubkey.toString());
      const index = keys.indexOf(event.wallet);
      if (index < 0) throw new Error("Wallet missing from transaction");
      if (![tx.meta.preBalances[index], tx.meta.postBalances[index], tx.meta.fee].every(Number.isSafeInteger)) {
        throw new Error("Unsafe native balance precision");
      }
      const tokens = {};
      for (const [rows, sign] of [[tx.meta.preTokenBalances, -1n], [tx.meta.postTokenBalances, 1n]]) {
        for (const row of rows || []) {
          if (row.owner === event.wallet) tokens[row.mint] = (tokens[row.mint] || 0n) + sign * BigInt(row.uiTokenAmount.amount);
        }
      }
      const fact = { signature: event.signature, wallet: event.wallet, slot: tx.slot,
        block_time: tx.blockTime, observed_at: Math.floor(Date.now() / 1000), failed: !!tx.meta.err,
        wallet_delta_lamports: tx.meta.postBalances[index] - tx.meta.preBalances[index],
        fee_lamports: index === 0 ? tx.meta.fee : 0,
        token_deltas_raw: Object.fromEntries(Object.entries(tokens).map(([mint, amount]) => [mint, amount.toString()])),
        basis: "finalized_transaction_balances" };
      fs.appendFileSync(path.join(dir, "dlmm_transaction_facts.jsonl"), JSON.stringify(fact) + "\n", { mode: 0o600 });
      facts.set(event.signature, fact);
    } catch (err) {
      pending++;
      console.warn(`[ACCOUNTING] ${event.signature}: reconciliation pending`);
    }
  }
  return { recorded: new Set(events.map(e => e.signature)).size, reconciled: facts.size, pending };
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command) {
    console.error("No command provided. Exposing: active-bin, deploy, check-bins, claim, close, position-exists, positions, pnl, spl-balance, swap");
    process.exit(1);
  }
  
  try {
    if (command === "accounting") {
      console.log(JSON.stringify(await reconcileAccounting()));
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
      const res = await closePosition(position);
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
      const amount = parseFloat(args[3]);
      const maxImpact = args[4] != null ? parseFloat(args[4]) : 5;
      const slipBps = args[5] != null ? parseInt(args[5]) : 100;
      if (!input || !output || isNaN(amount)) {
        throw new Error("Usage: swap <input_mint> <output_mint> <amount> [max_price_impact_pct] [slippage_bps]");
      }
      const res = await swapToken(input, output, amount, maxImpact, slipBps);
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
module.exports = { reconcileAccounting, recordSubmission, closePosition, swapToken, confirmSignedTransaction, deployPosition, acquireDeployLock, acquireSwapLock, reconcilePendingSwap,
  assertNoTokenExposure, positionIsEmpty, positionAccountExists, slippageBpsToPercent };
