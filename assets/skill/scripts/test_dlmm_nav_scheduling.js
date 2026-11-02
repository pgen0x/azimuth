// Offline final-payload regressions for bounded, fair NAV quote scheduling.
const assert = require('node:assert/strict');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const vm = require('node:vm'), Module = require('node:module');
const source = path.join(__dirname, 'dlmm_nav.js');

function harness(count, latency, rateLimit = false) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nav-scheduling-'));
  const clock = {time: Date.UTC(2026, 10, 2), trading: false};
  const mints = Array.from({length: count}, (_, i) => `synthetic-mint-${i}`);
  const requests = [];
  let order = [...mints];
  const amounts = {};
  const requireFromSource = Module.createRequire(source);
  const mockedFs = {...fs, readFileSync(file, ...args) {
    if (file === '/proc/net/unix') return clock.trading
      ? '000: 2 0 00010000 0001 01 0 @azimuth-dlmm-entry-synthetic-wallet\n' : '';
    return fs.readFileSync(file, ...args);
  }};
  const context = {
    require: name => name === 'fs' ? mockedFs : requireFromSource(name),
    module: {exports: {}}, Date: {now: () => clock.time, parse: Date.parse},
    AbortSignal, BigInt, console, process: {env: {DLMM_HELIUS_WALLET_PRICES: 'false'}, pid: process.pid},
    setTimeout(callback, delay) {clock.time += delay; callback();},
    async fetch(url) {
      if (url.includes('/quote?')) {
        requests.push(new URL(url).searchParams.get('inputMint')); clock.time += latency;
        return {ok: false, status: rateLimit ? 429 : 400,
          headers: {get: () => null}, json: async () => ({errorCode: 'NO_ROUTES_FOUND'})};
      }
      return {ok: true, json: async () => url.includes('assets/search')
        ? [] : {totalPositions: 0, pools: [], hasNext: false}};
    },
  };
  vm.runInNewContext(fs.readFileSync(source, 'utf8'), context, {filename: source});
  const connection = {getBlockHeight: async () => 1, getSignaturesForAddress: async () => [],
    getSlot: async () => 1000, getBalance: async () => 1000000000,
    getParsedTokenAccountsByOwner: async (_, options) => ({value:
      options.programId.toString().startsWith('Tokenkeg') ? order.map(mint => ({pubkey: 'account-' + mint, account: {
        lamports: 2039280, data: {parsed: {info: {mint, tokenAmount: {amount: amounts[mint] || '1', decimals: 9}}}},
      }})) : []}), getAccountInfo: async () => null};
  const collect = () => context.module.exports.collect({dir, wallet: 'synthetic-wallet',
    PublicKey: function(value) {return {toString: () => value};}, rpc: fn => fn(connection)});
  return {dir, clock, mints, requests, collect,
    setOrder: value => {order = value;}, setAmount: (mint, raw) => {amounts[mint] = raw;},
    snapshot: () => JSON.parse(fs.readFileSync(path.join(dir, 'dlmm_nav.jsonl'), 'utf8').trim().split('\n').at(-1)),
    cursor: () => JSON.parse(fs.readFileSync(path.join(dir, 'dlmm_quote_cursor.json'), 'utf8')).offset,
    clean: () => fs.rmSync(dir, {recursive: true, force: true})};
}

(async () => {
  const deadline = harness(30, 4000);
  try {
    for (let i = 0; i < 6; i++) {
      const before = deadline.requests.length;
      await deadline.collect();
      assert.equal(deadline.snapshot().valuation_coverage.quote_attempts, deadline.requests.length - before,
        'A pre-request budget deferral must not consume a quote attempt');
      assert.equal(deadline.snapshot().nav_sol, null);
      deadline.clock.time += 420000;
    }
    assert.equal(new Set(deadline.requests).size, deadline.mints.length, 'No unrequested mint is skipped forever');
    assert.equal(deadline.cursor(), deadline.requests.length % deadline.mints.length);
  } finally {deadline.clean();}
  const trading = harness(5, 0);
  try {
    trading.clock.trading = true; await trading.collect();
    assert.equal(trading.requests.length, 0); assert.equal(trading.cursor(), 0);
    assert.equal(trading.snapshot().valuation_coverage.quote_attempts, 0);
    assert.equal(trading.snapshot().valuation_coverage.unknown_by_reason.quote_trading_deferred, 5);
    trading.clock.trading = false; await trading.collect();
    assert.equal(trading.requests[0], trading.mints[0], 'Trading deferral preserves the next request');
  } finally {trading.clean();}
  const limited = harness(50, 0, true);
  try {
    await limited.collect(); const coverage = limited.snapshot().valuation_coverage;
    assert.equal(limited.requests.length, 1); assert.equal(coverage.quote_attempts, 1);
    assert.equal(coverage.quote_budget_cap, 40);
    assert.equal(coverage.unknown_by_reason.quote_rate_limit_deferred, 40);
    assert.equal(coverage.unknown_by_reason.quote_budget_deferred, 10,
      'Accounts outside the selection cap were never rate-limit attempted');
  } finally {limited.clean();}
  const reordered = harness(50, 300);
  try {
    await reordered.collect(); const served = new Set(reordered.requests);
    const waiting = reordered.mints.filter(mint => !served.has(mint));
    assert.ok(waiting.length > 0);
    // Move the legacy numeric cursor onto already-served accounts.
    reordered.setOrder([...reordered.mints.slice(14), ...reordered.mints.slice(0, 14)]);
    reordered.clock.time += 420000; const before = reordered.requests.length;
    await reordered.collect();
    assert.equal(reordered.requests[before], waiting[0], 'Existing backlog wins despite RPC account-order churn');
  } finally {reordered.clean();}
  const arrivals = harness(60, 300);
  try {
    arrivals.clock.trading = true; await arrivals.collect();
    assert.equal(arrivals.requests.length, 0);
    const newcomers = Array.from({length: 20}, (_, i) => 'new-account-' + i);
    arrivals.setOrder([...newcomers, ...arrivals.mints]);
    arrivals.clock.trading = false; arrivals.clock.time += 420000;
    await arrivals.collect();
    assert.equal(arrivals.requests[0], arrivals.mints[0], 'New arrivals cannot jump ahead of never-served FIFO');
  } finally {arrivals.clean();}
  const retained = harness(5, 0);
  try {
    await retained.collect();
    const cache = {};
    for (const mint of retained.mints.slice(0, 3)) cache[mint] = {schema_version: 2, in_amount: '1', out_lamports: '1000', observed_at: Math.floor(retained.clock.time / 1000), slot: 1000};
    fs.writeFileSync(path.join(retained.dir, 'dlmm_quote_marks.json'), JSON.stringify(cache));
    retained.clock.time += 420000; await retained.collect();
    retained.setOrder([...retained.mints].reverse());
    retained.setAmount(retained.mints[0], '2');
    const before = retained.requests.length; await retained.collect();
    assert.equal(retained.requests[before], retained.mints[0], 'Cache hits and amount changes preserve account service age');
  } finally {retained.clean();}
  const leftover = harness(5, 0);
  try {
    const oldTemporary = path.join(leftover.dir, 'dlmm_quote_schedule.json.' + process.pid + '.tmp');
    fs.writeFileSync(oldTemporary, 'orphan from a previous process with this PID');
    await leftover.collect();
    assert.equal(leftover.requests.length, 5, 'A stale PID temporary file cannot abort collection');
    assert.equal(fs.readFileSync(oldTemporary, 'utf8'), 'orphan from a previous process with this PID');
  } finally {leftover.clean();}
  for (const invalid of ['broken JSON', JSON.stringify({schema_version: 1, counter: -1, orders: {}}),
    JSON.stringify({schema_version: 1, counter: 1, orders: {'fake-account': 2}}),
    JSON.stringify({schema_version: 1, counter: Number.MAX_SAFE_INTEGER, orders: {}})]) {
    const damaged = harness(10, 0);
    try {
      fs.writeFileSync(path.join(damaged.dir, 'dlmm_quote_cursor.json'), JSON.stringify({offset: 7}));
      fs.writeFileSync(path.join(damaged.dir, 'dlmm_quote_schedule.json'), invalid);
      await damaged.collect();
      assert.equal(damaged.requests[0], damaged.mints[7], 'Corrupt history falls back to legacy cursor order');
    } finally {damaged.clean();}
  }
  console.log('NAV quote scheduling preserves service fairness, FIFO, cached history and legacy fallback');
})().catch(error => {console.error(error); process.exitCode = 1;});
