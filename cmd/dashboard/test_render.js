'use strict';
// DOM stub, synthetic evidence; no browser/network/service access.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict'), {execFileSync} = require('node:child_process');
const script = fs.readFileSync(__dirname + '/index.html', 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
async function render(tab, payload, fail=false, extra={}) {
  const content = {innerHTML: ''}, stamp = {textContent: ''}, intervals = [], calls = [];
  const els = {'#content': content, '#stamp': stamp, '#rhlog': {innerHTML: ''}, '#rhcount': {textContent: ''}};
  const document = {querySelector: s => els[s] || {}, querySelectorAll: () => []};
  const fixtures = {ops: {funnel: {}, health: {}, alerts: []}, overview: {nav: {}, services: [], sources: []}, capital: {north_star: {days: []}, nav_bridge: {}},
    live: {live: {}}, journal: {rows: [], total_in_retained_tail: 0}, hermes: {}, redis: {rows: []}, growth: {tz: 'UTC', north_star: {days: []}, growth: {}, experiments: {}}, ...extra};
  const ctx = {document, Date, console, fetch: async url => {
    calls.push(url); const name = {'agent/brief': 'ops'}[url.replace('/api/', '').split('?')[0]] || url.replace('/api/', '').split('?')[0];
    if ((fail && name === tab) || (extra.failing || []).includes(name)) return {ok: false, status: 500, text: async () => 'synthetic failure'};
    return {ok: true, status: 200, json: async () => name === tab ? payload : fixtures[name]};
  }, setInterval: fn => intervals.push(fn), module: {exports: {}}};
  vm.runInNewContext(script + '\nmodule.exports={render,setTab:t=>{tab=t}};', ctx);
  await new Promise(resolve => setImmediate(resolve));
  ctx.module.exports.setTab(tab); await ctx.module.exports.render();
  const first = content.innerHTML, before = calls.length;
  intervals.forEach(fn => fn()); await new Promise(resolve => setImmediate(resolve));
  assert(!/NaN|undefined/.test(first), first);
  return {html: first, stamp: stamp.textContent, timerFetches: calls.length - before, calls, log: els['#rhlog'].innerHTML, count: els['#rhcount'].textContent};
}
(async () => {
  const warning = 'Local collection failed; last successful snapshot retained';
  for (const tab of ['capital', 'live', 'robinhood', 'journal', 'hermes', 'redis', 'overview', 'ops']) {
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
    incomplete_sources: ['transaction_kinds'], fees_by_kind: {unknown: {sol: null}}, components: [{component: 'rent_ledger', label: 'Rent', sol: null}]}});
  assert(capital.html.includes('transaction_kinds') && capital.html.includes('native identity Unknown'));
  assert(!capital.html.includes('<td>0</td>'));
  // Charts: unmeasured days are hatched, never drawn or labelled as zero; day labels name the zone.
  const days=[{day:'2024-10-02',status:'no_snapshot'},
    {day:'2024-10-03',status:'ok',cash_sol:1,known_sol:1.2},
    {day:'2024-10-04',status:'ok',cash_sol:1.003,known_sol:1.21,d_cash_sol:0.003,d_known_sol:0.01},
    {day:'2024-10-05',status:'ok',cash_sol:0.999,known_sol:1.19,d_cash_sol:-0.004,d_known_sol:-0.02},
    {day:'2024-10-06',status:'partial_day',cash_sol:0.999,known_sol:1.19,d_cash_sol:0,d_known_sol:0}];
  const charted = await render('capital', {tz:'America/Sao_Paulo', tz_fallback:false, north_star:{status:'ok',days},
    nav_bridge:{status:'incomplete_sources',incomplete_sources:['closes'],d_known_sol:-0.01,components:[
      {component:'network_fees',label:'Network fees',sol:-0.003},{component:'lp_realized',label:'LP realized',sol:null,measured_subtotal_sol:-0.02},{component:'unexplained',label:'Unexplained',sol:null}]}});
  const h = charted.html;
  assert(h.includes('Unexplained <span class="badge">residual</span>'), 'residual badge keyed by component id');
  assert(h.includes('days in America/Sao_Paulo') && h.includes('4 Oct 2024 (America/Sao_Paulo)'), 'zone named on day labels');
  assert(h.includes('class="cell pos-3"') && h.includes('class="cell neg-3"') && h.includes('class="cell unk"'), 'calendar states');
  assert(h.includes('+3.00') && h.includes('−4.00') && h.includes('class="cell  today"'), 'signed mSOL values and today marker');
  assert(/Unmeasured&#10;|Unmeasured\n/.test(h) && h.includes('No NAV snapshot this day'), 'unmeasured tooltip');
  assert(h.includes('class="unm"') && (h.match(/class="bar fp"/g)||[]).length===1 && (h.match(/class="bar fn"/g)||[]).length===1, 'delta bars: one gain, one loss, hatched unmeasured');
  assert(h.includes('<div class="val">Unknown</div>') && h.includes('class="seg dn"') && h.includes('Δ known SOL, window total'), 'waterfall unknown and total');
  assert(h.includes('tabindex="0" role="group"') && h.includes('Arrow keys'), 'charts keyboard reachable');
  assert(h.includes('Day (America/Sao_Paulo)'), 'table header names zone');
  const fallback = await render('capital', {tz:'UTC', tz_fallback:true, north_star:{days:[]}, nav_bridge:{}});
  assert(fallback.html.includes('days are shown in UTC') && fallback.html.includes('No measured values in this window yet.'), 'fallback + empty states');
  assert(fallback.html.includes('No days in the capital history yet.') && fallback.html.includes('The NAV bridge has no components'), 'empty chart states');
  const live = await render('live', {tz:'Pacific/Pago_Pago', collected_at: 1730606400, live:{dust:{}, realized:{status:'ok',days:{
    '2024-11-01':{pulse:{closes:2,measured:2,unmeasured:0,realized_sol:0.002},turnover:{closes:1,measured:0,unmeasured:1,realized_sol:null}},
    '2024-11-02':{turnover:{closes:1,measured:1,unmeasured:0,realized_sol:-0.001}}}}}});
  assert(live.html.includes('+0.001000') && live.html.includes('days in Pacific/Pago_Pago'), 'cumulative realized hero + zone');
  assert(live.html.includes('var(--s1)') && live.html.includes('var(--s2)') && live.html.includes('>?</text>'), 'mode colours fixed by name, unmeasured marker');
  assert(live.html.includes('turnover Unknown SOL (0 / 1 closes, 1 unmeasured)'), 'unmeasured mode is Unknown, not 0');
  const empty = await render('live', {live:{dust:{}, realized:{days:{}}}});
  assert(empty.html.includes('No closes since the cutover yet.'), 'empty realized chart');
  const failing = await render('capital', null, true);
  assert(failing.html.includes('Could not load this section') && failing.html.includes('Retry loading'), 'error state');
  assert(!/\u2014/.test(charted.html + live.html + h), 'no em dash in UI text');
  // Owner policy: no other bot in rendered evidence. The page relies on the collector filter, so the
  // fixture goes through collect.own_only with a made-up name in the operator deny-list first.
  const other = 'otherbot';
  const filtered = JSON.parse(execFileSync('python3', ['-c',
    'import json,sys; sys.path.insert(0, sys.argv[1]); import collect; print(json.dumps(collect.own_only(json.load(sys.stdin))))', __dirname],
    {input: JSON.stringify({nav: {native_sol: 1, tokens: [{[other + '_mark']: 1, own: 2}]}, services: [], sources: []}),
     env: {...process.env, DASHBOARD_HIDE_KEYS: other}}));
  const ov = await render('overview', filtered);
  assert(!ov.html.toLowerCase().includes(other) && ov.html.includes('&quot;own&quot;: 2'), 'no other-bot keys in raw evidence');
  assert(!/evaluation/i.test(ov.html), 'no evaluation section');
  // Robinhood: inactive monitor still shows history; money per asset; unmeasured and mark rows never read as money.
  const KEY = 'ab'.repeat(32);
  const rh = await render('robinhood', {collected_at: 200000, tz: 'UTC', monitor_active: false,
    unit: {Id: 'azimuth-rh-monitor.service', ActiveState: 'inactive', SubState: 'dead', UnitFileState: 'disabled'},
    modes: {status: 'ok', started_at: 1000, flags: {robinhood: false, 'rh-turnover': true}},
    logs: [{time: 300, unit: 'azimuth-rh-monitor.service', line: 'turnover re-center ok'}, {time: 200, unit: 'azimuth.service', line: 'scanner[rh-turnover]: gas spike <b>'}],
    positions: [{protocol: 'v4', token_id: '1', pool: '0x' + 'c'.repeat(40), strategy: 'weth_below', quote: 'ETH', token: '[masked]', token_address: 'position-public-token', tick_lower: -600, tick_upper: 0, minted_at: 100, age_s: 90000, last_failed_close: {time: 150, reason: 'revert'}}],
    stranded: {open: [{symbol: 'XYZ', token: '0x' + 'd'.repeat(40), token_address: 'stranded-public-token', amount_raw: '107037025008', reason: 'no pool', time: 120, attempts: 4, next_try: 130}], resolved: [], sources: [{path: 'uni_stranded.jsonl', status: 'ok', rows: 1}, {path: 'uni_v4_stranded.jsonl', status: 'unavailable', rows: 0}]},
    closes: {tz: 'UTC', status: 'ok', closes_total: 3, skipped: {failed: 1, dry_run: 0}, gas: {gas_eth: 0.003, gas_txs: 5, metered: 2, unmetered: 1},
      totals: {ETH: {closes: 2, measured: 1, unmeasured: 1, realized_quote: 0.01, mark_flagged: 1}, USDG: {closes: 1, measured: 0, unmeasured: 1, realized_quote: null, mark_flagged: 0}, unknown: {closes: 2, measured: 0, unmeasured: 2, realized_quote: null, mark_flagged: 0}},
      days: {'1970-01-02': {ETH: {closes: 2, measured: 1, unmeasured: 1, realized_quote: 0.01}}, '1970-01-03': {USDG: {closes: 1, measured: 0, unmeasured: 1, realized_quote: null}}},
      closes: [{time: 90000, reason: 'fill', asset: 'ETH', realized_quote: null, pnl_basis: 'mark', mark_flagged: true, pnl_pct: 90, age_min: 30, gas_eth: null},
               {time: 86500, reason: 'turnover re-center', asset: 'ETH', realized_quote: 0.01, pnl_basis: 'realized', mark_flagged: false, pnl_pct: 2, age_min: 5, gas_eth: 0.001, gas_txs: 3}]}});
  assert(rh.calls.some(u => /^\/api\/robinhood\?tz=.+&n=200$/.test(u)), 'viewer zone and default log length requested');
  assert(rh.html.includes('Monitor inactive') && rh.html.includes('weth_below'), 'inactive monitor keeps history');
  assert(rh.html.includes('Realized · USDG</span><strong>Unknown</strong>'), 'wholly unmeasured USDG is Unknown, not 0');
  assert(rh.html.includes('+0.010000') && rh.html.includes('mark: value left behind') && rh.html.includes('Unmeasured'), 'mark row is flagged, not money');
  assert(rh.html.includes('>−0.003000<') && rh.html.includes('1 unmetered'), 'gas is a cost, unmetered counted');
  assert(rh.html.includes('No USDG') === false && /hatch|url\(#h/.test(rh.html), 'unmeasured day hatched');
  assert(rh.html.includes('position-public-token') && rh.html.includes('stranded-public-token'), 'public token address aliases survive credential masking');
  assert(rh.html.includes('107037025008') && rh.html.includes('raw units'), 'stranded amount labelled raw');
  assert(!rh.html.includes(KEY), 'no key-shaped data');
  assert(rh.log.includes('turnover re-center ok') && rh.log.includes('&lt;b&gt;') && !rh.log.includes('<b>'), 'log escaped');
  assert(rh.count.startsWith('2 of 2'), 'log count');
  assert(rh.html.includes('Realized · unknown unit · never summed</span><strong>Unknown</strong>'), 'unknown unit never summed');
  assert(rh.html.includes('Stranded evidence: partial'), 'stranded source coverage shown, a refused source is not an empty inventory');
  assert(rh.timerFetches > 0, 'robinhood refreshes on the timer');
  const rhEmpty = await render('robinhood', {collected_at: 1, unit: {}, modes: {status: 'unknown', flags: {}, note: 'azimuth.service is not running'}, logs: [], positions: [], stranded: {}, closes: {totals: {}, days: {}, closes: []}});
  assert(rhEmpty.html.includes('Robinhood modes unknown') && rhEmpty.html.includes('No ETH closes in this window.'), 'empty robinhood');
  assert(rhEmpty.log.includes('No log lines retained'), 'empty log state');
  const rhFail = await render('robinhood', null, true);
  assert(rhFail.html.includes('Could not load this section'), 'robinhood error state');
  // Ops: funnel, health and alerts from the agent brief; unknown stays Unknown, red flags are announced.
  const ops = await render('ops', {collected_at: 1000, alerts: [{code: 'disk_low', message: 'disk free 9.0% < 15% <b>'}],
    funnel: {hours: 12, status: 'ok', batches: 3, batch_pools: 4, deploys: 1, last_deploy_ts: 900, direct_deploy: {deployed: 0, not_deployed: 2},
      routes: {hermes_ai: 2, 'deterministic_fallback:timeout': 1}, daemon_rejects: {'re-entry cooldown': 5}, pipeline_rejects: {downtrend_h6: 2}},
    health: {units: [{unit: 'azimuth.service', active: 'active', sub: 'running', enabled: 'enabled'}, {unit: 'azimuth-sol-monitor.service', active: 'failed', sub: 'failed', enabled: 'disabled'}],
      failed_units: ['azimuth-sol-monitor.service'], disk_free_pct: 9, mem_available_mb: null, monitor_tick_age_s: 400}});
  assert(ops.calls.some(u => u === '/api/agent/brief?hours=12'), 'ops reads the agent brief');
  assert(ops.html.includes('role="alert"') && ops.html.includes('disk_low') && ops.html.includes('&lt;b&gt;') && !ops.html.includes('<b>'), 'alerts announced and escaped');
  assert(ops.html.includes('deterministic_fallback:timeout') && ops.html.includes('downtrend_h6') && ops.html.includes('re-entry cooldown'), 'funnel histograms');
  assert(ops.html.includes('MemAvailable</span><strong class="">Unknown') || ops.html.includes('MemAvailable</span><strong>Unknown'), 'unmeasured memory is Unknown');
  assert(ops.html.includes('7 min ago') && ops.html.includes('badge bad">failed / failed') && ops.html.includes('badge bad">disabled'), 'stale tick and failed unit');
  assert(ops.timerFetches > 0, 'ops refreshes on the timer');
  const opsOk = await render('ops', {collected_at: 1, alerts: [], funnel: {}, health: {}});
  assert(opsOk.html.includes('No red flags') && opsOk.html.includes('No observed records'), 'empty ops');
  const opsFail = await render('ops', null, true);
  assert(opsFail.html.includes('Could not load this section'), 'ops error state');
  // The overview must not restate a fixed SOL entry floor: the cash policy decides entry.
  for (const native of [0.1, 0.2, 1, null]) {
    const ov = await render('overview', {nav: {native_sol: native, ts: 1}, services: [], sources: []});
    assert(!/0\.35|Below 0\.|floor/.test(ov.html), 'no hard-coded entry floor');
    assert(!ov.html.includes('meets the'), 'a static balance never reads as entry authorization');
    assert(ov.html.includes('configured cash policy'), 'neutral entry-policy note');
  }
  // Growth: today's split keeps unmeasured parts unmeasured; experiments are counts only.
  const day = (d, native, extra = {}) => ({day: d, status: 'ok', native_sol: native, lp_mark_sol: 0.1, refundable_rent_sol: 0.05, cash_sol: native + 0.15, known_sol: native + 0.2, ...extra});
  const growth = {tz: 'UTC', north_star: {days: [day('2033-05-16', 1), {day: '2033-05-17', status: 'no_snapshot'}, day('2033-05-18', 1.1, {status: 'partial_day'})]},
    growth: {day: '2033-05-18', status: 'partial', d_native_sol: 0.1, native_start_sol: 1, native_end_sol: 1.1, start_ts: 1, end_ts: 2, d_lp_mark_sol: 0, d_refundable_rent_sol: -0.05,
      components: [{component: 'realized_lp', label: 'Realized LP', sol: null, closes: 2, pending: 1, measured_subtotal_sol: 0.02},
        {component: 'rent_reclaimed', label: 'Rent reclaimed', sol: 0.049, rent_recovered_sol: 0.05, forfeited_quote_sol: 0.001, closed_accounts: 3},
        {component: 'network_fees', label: 'Network fees', sol: -0.00001, transactions: 2}, {component: 'external', label: 'External', sol: 0},
        {component: 'other', label: 'Other', sol: null}]},
    experiments: {status: 'ok', basis: 'Counts only.', geometry_shadow: {entries: 4, report: {status: 'ok', verdict: 'NEED-DATA', closed: 1, treated: 1, pools: 1, days: 1, gate: {min_n: 30, min_pools: 10, min_days: 7}}},
      hold_canary: {arms: {A: 14, B: 12}, closes: 26, first_ts: 1}, active_bin_reanchor: {entries: 27, reanchored: 0, max_drift_bins: null, since: 1}}};
  const gv = await render('overview', {nav: {}, services: [], sources: []}, false, {growth});
  assert(gv.calls.some(u => u.startsWith('/api/growth?tz=')), 'growth is fetched with the viewer zone');
  assert(gv.html.includes('growth / today') && gv.html.includes('+0.100000'), 'today native delta');
  assert(gv.html.includes('1 of 2 closes not reconciled yet'), 'pending closes named');
  assert((gv.html.match(/>unmeasured</g) || []).length === 2, 'realized and other stay unmeasured, never 0');
  assert(gv.html.includes('+0.049000') && gv.html.includes('−0.000010'), 'measured parts signed');
  assert(gv.html.includes('growth / balance') && gv.html.includes('style="fill:var(--s1)"'), 'stacked native bars drawn');
  assert(gv.html.includes('experiments / live studies') && gv.html.includes('A 14 · B 12') && gv.html.includes('NEED-DATA') && gv.html.includes('0 of 27 entries'), 'experiments counts');
  const ovFail = await render('overview', {nav: {}, services: [], sources: []}, false, {failing: ['growth']});
  assert(ovFail.html.includes('overview / known') && ovFail.html.includes('Growth data unavailable: synthetic failure'), 'a growth failure never blanks the overview');
  const ovEmpty = await render('overview', {nav: {}, services: [], sources: []});
  assert(ovEmpty.html.includes('No measured days in this window yet') && ovEmpty.html.includes('report unavailable'), 'empty growth states');
  console.log('dashboard render: 59 synthetic cases passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
