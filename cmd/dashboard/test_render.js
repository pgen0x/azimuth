'use strict';
// DOM stub, synthetic evidence; no browser/network/service access.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const script = fs.readFileSync(__dirname + '/index.html', 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
async function render(tab, payload) {
  const content = {innerHTML: ''}, stamp = {textContent: ''}, intervals = [], calls = [];
  const document = {querySelector: s => s === '#content' ? content : s === '#stamp' ? stamp : {}, querySelectorAll: () => []};
  const fixtures = {overview: {nav: {}, services: [], sources: []}, capital: {north_star: {days: []}, nav_bridge: {}},
    live: {live: {}}, journal: {rows: [], total_in_retained_tail: 0}, evaluation: {}, hermes: {}, redis: {rows: []}};
  const ctx = {document, Date, console, fetch: async url => {
    calls.push(url); const name = url.replace('/api/', '').split('?')[0];
    return {ok: true, json: async () => name === tab ? payload : fixtures[name]};
  }, setInterval: fn => intervals.push(fn), module: {exports: {}}};
  vm.runInNewContext(script + '\nmodule.exports={render,setTab:t=>{tab=t}};', ctx);
  await new Promise(resolve => setImmediate(resolve));
  ctx.module.exports.setTab(tab); await ctx.module.exports.render();
  const first = content.innerHTML, before = calls.length;
  intervals.forEach(fn => fn()); await new Promise(resolve => setImmediate(resolve));
  assert(!/NaN|undefined/.test(first), first);
  return {html: first, stamp: stamp.textContent, timerFetches: calls.length - before};
}
(async () => {
  const warning = 'Local collection failed; last successful snapshot retained';
  for (const tab of ['capital', 'live', 'journal', 'evaluation', 'hermes', 'redis', 'overview']) {
    const r = await render(tab, {collected_at: 123, collection_error: warning, rows: [], total_in_retained_tail: 0, services: [], sources: []});
    assert(r.html.includes(warning) && r.html.includes('role="alert"'), tab);
    assert(r.stamp.includes('Observed') && !r.stamp.endsWith('Unknown'), tab);
    if (tab === 'capital' || tab === 'live') assert(r.timerFetches > 0, tab);
  }
  const r = await render('live', {live: {dust: {status: 'unavailable', fee_lamports: null,
    forfeited_quote_lamports: null, errors: [{reason: '<img src=x onerror=alert(1)>', count: 1}]},
    realized: {status: 'partial', sources: {realized: {status: 'over_cap'}}, days: {'day': {synthetic: {closes: 1, measured: 0, unmeasured: 1, realized_sol: null}}}}}});
  assert(r.html.includes('Unknown <small>(0 / 1, 1 unmeasured)'));
  assert(r.html.includes('over_cap') && r.html.includes('Dust rules not fully measured'));
  assert(!r.html.includes('No dust rule violations'));
  assert(r.html.includes('&lt;img') && !r.html.includes('<img src=x'));
  assert(!r.html.includes('<strong>0</strong>'), 'unavailable amounts must not be unary-negated into zero');
  assert(r.html.includes('Verified fees · SOL</span><strong>Unknown</strong>'));
  assert(r.html.includes('Forfeited quote · SOL</span><strong>Unknown</strong>'));
  const capital = await render('capital', {north_star: {days: []}, nav_bridge: {status: 'incomplete_sources', native_identity_exact: null,
    incomplete_sources: ['transaction_kinds'], fees_by_kind: {unknown: {sol: null}}, components: [{key: 'rent_ledger', label: 'Rent', sol: null}]}});
  assert(capital.html.includes('transaction_kinds') && capital.html.includes('native identity Unknown'));
  assert(!capital.html.includes('<td>0</td>'));
  console.log('dashboard render: 9 synthetic cases passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
