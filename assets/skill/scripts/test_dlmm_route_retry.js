const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const retry = require('./dlmm_route_retry');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dlmm-route-'));
const file = path.join(dir, 'pending');
const quote = {inputMint: 'TOKEN', outputMint: 'So11111111111111111111111111111111111111112',
  routePlan: [{swapInfo: {label: 'Hadron'}}]};
const tx = {message: {staticAccountKeys: ['OTHER', 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4'],
  compiledInstructions: [{programIdIndex: 0}, {programIdIndex: 1}]}};
try {
  const ctx = retry.context(quote, tx, 'position');
  assert.equal(ctx.jupiter_instruction, 1);
  assert.equal(retry.context({...quote, routePlan: [...quote.routePlan, ...quote.routePlan]}, tx, 'position'), null);
  assert.equal(retry.context({...quote, inputMint: quote.outputMint}, tx, 'position'), null);
  assert.equal(retry.context(quote, tx, ''), null);
  assert.equal(retry.context(quote, {message: {}}, 'position'), null);
  for (const error of [null, {InstructionError: [0, {Custom: 6001}]},
    {InstructionError: [1, {Custom: 6008}]}]) {
    retry.recordFailure(file, ctx, error, 100);
    assert.equal(retry.excluded(file, 'position', 101), '');
  }
  retry.recordFailure(file, ctx, {InstructionError: [1, {Custom: 6001}]}, 100);
  assert.equal(retry.excluded(file, 'position', 101), 'Hadron');
  assert.equal(retry.excluded(file, 'other-position', 101), '');
  assert.equal(retry.excluded(file, 'position', 99), '');
  assert.equal(retry.excluded(file, 'position', 400), '');
  assert.equal(fs.statSync(file + '.route').mode & 0o777, 0o600);
  fs.writeFileSync(file + '.route', '{bad');
  assert.equal(retry.excluded(file, 'position', 101), '');
  console.log('Confirmed route failure binding, position isolation and expiry passed');
} finally { fs.rmSync(dir, {recursive: true, force: true}); }
