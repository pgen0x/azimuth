// Before-signing optimization only. The executor still simulates the final tx.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {performance} = require('node:perf_hooks');
const {PublicKey, Transaction, TransactionInstruction, SystemProgram, SYSVAR_RENT_PUBKEY} = require('@solana/web3.js');
const AMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo';
const tag = name => crypto.createHash('sha256').update('global:' + name).digest().subarray(0, 8);

function historyRead(url, address, fetchFn, timeoutMs) {
  const controller = new AbortController();
  const history = {address, waitUntil: performance.now() + 300, settled: false, unused: false};
  let timer, resolve;
  history.read = new Promise(done => {resolve = done;});
  const finish = unused => {
    if (history.settled) return;
    history.settled = true;
    history.unused = unused === true;
    clearTimeout(timer);
    controller.abort();
    resolve(history.unused);
  };
  history.cancel = () => finish(false);
  timer = setTimeout(history.cancel, timeoutMs);
  void (async () => {
    try {
      const response = await fetchFn(url, {method: 'POST', headers: {'content-type': 'application/json'},
        signal: controller.signal, body: JSON.stringify({jsonrpc: '2.0', id: 1,
          method: 'getSignaturesForAddress', params: [address, {limit: 1, commitment: 'confirmed'}]})});
      if (!response.ok) return finish(false);
      const data = await response.json();
      finish(!data.error && Array.isArray(data.result) && data.result.length === 0);
    } catch { finish(false); }
  })();
  return history;
}

async function historyUnused(history) {
  if (history.settled) return history.unused === true;
  // Replies may arrive during a slower builder, but entry never waits beyond
  // the original 300 ms window measured from the start of the lookup.
  const remaining = Number.isFinite(history.waitUntil)
    ? Math.min(300, history.waitUntil - performance.now()) : 0;
  if (remaining <= 0) return false;
  let timer;
  try {
    return await Promise.race([history.read, new Promise(resolve => {
      timer = setTimeout(() => resolve(false), remaining);
    })]);
  } finally {
    clearTimeout(timer);
  }
}

function derive(pool, wallet, lower, upper) {
  const width = upper - lower + 1;
  if (!Number.isSafeInteger(lower) || !Number.isSafeInteger(upper)
      || lower < -(2 ** 31) || upper >= 2 ** 31 || width < 1 || width > 70
      || pool.program.programId.toString() !== AMM) throw new Error('Unsupported position');
  const lo = Buffer.alloc(4), size = Buffer.alloc(4);
  lo.writeInt32LE(lower); size.writeInt32LE(width);
  return PublicKey.findProgramAddressSync([Buffer.from('position'), pool.pubkey.toBuffer(), wallet.toBuffer(), lo, size], pool.program.programId)[0];
}

function beginPositionPdaHistory({pool, wallet, lower, upper, entryDir, rpcUrl}, fetchFn = fetch) {
  try {
    const position = derive(pool, wallet, lower, upper);
    if (fs.existsSync(path.join(entryDir, position.toString() + '.json'))) return null;
    // The three-second lifetime is background only. preparePositionPda keeps
    // the original wait deadline and cancels a still-pending read immediately.
    return historyRead(rpcUrl, position.toString(), fetchFn, 3000);
  } catch { return null; }
}

async function preparePositionPda({pool, transaction, wallet, originalPosition, lower, upper, entryDir, rpcUrl, history}, fetchFn = fetch) {
  try {
    const width = upper - lower + 1;
    if (!Number.isSafeInteger(lower) || !Number.isSafeInteger(upper)
        || lower < -(2 ** 31) || upper >= 2 ** 31 || width < 1 || width > 70
        || pool.program.programId.toString() !== AMM
        || transaction.signatures.some(s => s.signature !== null)
        || !transaction.feePayer.equals(wallet)) return null;
    const message = transaction.compileMessage();
    if (message.header.numRequiredSignatures !== 2
        || !message.accountKeys.slice(0, 2).every(key => key.equals(wallet) || key.equals(originalPosition))) return null;
    const instructions = transaction.instructions;
    const matching = instructions.filter(ix => ix.programId.toString() === AMM && ix.data.subarray(0, 8).equals(tag('initialize_position')));
    if (matching.length !== 1) return null;
    const init = matching[0];
    const eventAuthority = PublicKey.findProgramAddressSync([Buffer.from('__event_authority')], pool.program.programId)[0];
    const expected = [wallet, originalPosition, pool.pubkey, wallet, SystemProgram.programId, SYSVAR_RENT_PUBKEY, eventAuthority, pool.program.programId];
    if (init.data.length !== 16 || init.data.readInt32LE(8) !== lower || init.data.readInt32LE(12) !== width
        || init.keys.length !== expected.length || !init.keys.every((meta, i) => meta.pubkey.equals(expected[i]))
        || instructions.some(ix => ix !== init && ix.keys.some(meta => meta.pubkey.equals(originalPosition) && meta.isSigner))) return null;
    const position = derive(pool, wallet, lower, upper);
    // Never reuse a journal identity, including a closed or failed old entry.
    if (fs.existsSync(path.join(entryDir, position.toString() + '.json'))) return null;
    if (history === undefined) {
      history = historyRead(rpcUrl, position.toString(), fetchFn, 300);
    }
    if (!history || history.address !== position.toString() || await historyUnused(history) !== true) return null;
    const pda = await pool.program.methods.initializePositionPda(lower, width).accountsStrict({
      payer: wallet, base: wallet, position, lbPair: pool.pubkey, owner: wallet,
      systemProgram: SystemProgram.programId, rent: SYSVAR_RENT_PUBKEY,
      eventAuthority, program: pool.program.programId}).instruction();
    const pdaKeys = [wallet, wallet, position, pool.pubkey, wallet, SystemProgram.programId, SYSVAR_RENT_PUBKEY, eventAuthority, pool.program.programId];
    if (!pda.programId.equals(pool.program.programId) || pda.data.length !== 16
        || !pda.data.subarray(0, 8).equals(tag('initialize_position_pda'))
        || pda.data.readInt32LE(8) !== lower || pda.data.readInt32LE(12) !== width
        || pda.keys.length !== pdaKeys.length || !pda.keys.every((meta, i) => meta.pubkey.equals(pdaKeys[i]))) return null;
    const rewritten = new Transaction({feePayer: wallet, blockhash: transaction.recentBlockhash,
      lastValidBlockHeight: transaction.lastValidBlockHeight});
    for (const ix of instructions) {
      rewritten.add(ix === init ? pda : new TransactionInstruction({programId: ix.programId, data: Buffer.from(ix.data),
        keys: ix.keys.map(meta => ({...meta, pubkey: meta.pubkey.equals(originalPosition) ? position : meta.pubkey}))}));
    }
    const final = rewritten.compileMessage();
    if (final.header.numRequiredSignatures !== 1 || !final.accountKeys[0].equals(wallet)) return null;
    return {transaction: rewritten, position,
      creation: {kind: 'wallet_pda', base: wallet.toString(), lower_bin_id: lower, width}};
  } catch {
    // History, SDK or layout uncertainty retains the ordinary unsigned builder.
    return null;
  } finally {
    history?.cancel?.();
  }
}

module.exports = {preparePositionPda, beginPositionPdaHistory};
