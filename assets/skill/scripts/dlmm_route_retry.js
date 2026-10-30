// Bound a temporary Hadron exclusion to a confirmed Jupiter slippage failure.
// Never infer failure from a timeout or increase the caller's slippage.
const fs = require('node:fs');
const SOL = 'So11111111111111111111111111111111111111112';
const JUP = 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4';
const TTL = 300;
function context(quote, transaction, position) {
  if (!position || quote?.outputMint !== SOL || quote.inputMint === SOL
      || !Array.isArray(quote.routePlan) || quote.routePlan.length !== 1
      || quote.routePlan[0]?.swapInfo?.label !== 'Hadron') return null;
  const message = transaction.message;
  const indices = (message?.compiledInstructions || []).flatMap((ix, i) =>
    message.staticAccountKeys?.[ix.programIdIndex]?.toString() === JUP ? [i] : []);
  return indices.length === 1 ? {position, jupiter_instruction: indices[0], dex: 'Hadron'} : null;
}
function recordFailure(file, ctx, error, now = Date.now() / 1000) {
  const ix = error?.InstructionError;
  if (!ctx || ctx.dex !== 'Hadron' || typeof ctx.position !== 'string' || !ctx.position
      || !Number.isSafeInteger(ctx.jupiter_instruction) || ctx.jupiter_instruction < 0
      || !Array.isArray(ix) || ix[0] !== ctx.jupiter_instruction || ix[1]?.Custom !== 6001) return;
  const temporary = `${file}.route.${process.pid}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify({...ctx, failed_at: now, expires_at: now + TTL}), {mode: 0o600});
  fs.renameSync(temporary, `${file}.route`);
}
function excluded(file, position, now = Date.now() / 1000) {
  try {
    const r = JSON.parse(fs.readFileSync(`${file}.route`, 'utf8'));
    return r.dex === 'Hadron' && r.position === position && typeof position === 'string' && position
      && Number.isFinite(r.failed_at) && r.failed_at <= now && now < r.expires_at
      && r.expires_at === r.failed_at + TTL ? 'Hadron' : '';
  } catch { return ''; }
}
module.exports = {context, recordFailure, excluded};
