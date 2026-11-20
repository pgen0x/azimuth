'use strict';
// DOM stub, synthetic evidence; no browser/network/service access.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict'), {execFileSync} = require('node:child_process');
const script = fs.readFileSync(__dirname + '/index.html', 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
async function render(tab, payload, fail=false, extra={}) {
  // 'rh:<section>' renders that section on the Robinhood venue; its payload is the /api/robinhood answer.
  const rhTab = tab.startsWith('rh:') ? tab.slice(3) : null, own = rhTab ? 'robinhood' : tab;
  const content = {innerHTML: ''}, stamp = {textContent: ''}, intervals = [], calls = [];
  const els = {'#content': content, '#stamp': stamp, '#rhlog': {innerHTML: ''}, '#rhcount': {textContent: ''}};
  // extra.absent: selectors missing from the page, so a handler wired for the wrong view throws as in a browser.
  // extra.tabs: fake venue tab buttons (dataset, attributes, child status nodes, focus) for the header selector.
  const tabs = extra.tabs || [];
  for (const b of tabs) { els['#vt-' + b.dataset.venue] = b; }
  const document = {querySelector: s => els[s] || ((extra.absent || []).includes(s) ? null : {}), querySelectorAll: s => s === '[data-venue]' ? tabs : []};
  const fixtures = {ops: {funnel: {}, health: {}, alerts: []}, overview: {nav: {}, services: [], sources: []}, capital: {north_star: {days: []}, nav_bridge: {}},
    live: {live: {}}, journal: {rows: [], total_in_retained_tail: 0}, hermes: {}, redis: {rows: []}, growth: {tz: 'UTC', north_star: {days: []}, growth: {}, experiments: {}}, ...extra};
  const ctx = {document, Date, console, fetch: async url => {
    calls.push(url); const name = {'agent/brief': 'ops'}[url.replace('/api/', '').split('?')[0]] || url.replace('/api/', '').split('?')[0];
    if ((fail && name === own) || (extra.failing || []).includes(name)) return {ok: false, status: 500, text: async () => 'synthetic failure'};
    return {ok: true, status: 200, json: async () => name === own ? payload : fixtures[name]};
  }, setInterval: fn => intervals.push(fn), module: {exports: {}}};
  // Optional storage: an object (kept per viewer) or 'throw' (blocked site data, private window).
  if (extra.store === 'throw') ctx.localStorage = {getItem() { throw Error('blocked') }, setItem() { throw Error('blocked') }};
  else if (extra.store) ctx.localStorage = {getItem: k => extra.store[k] ?? null, setItem: (k, v) => { extra.store[k] = String(v) }};
  vm.runInNewContext(script + '\nmodule.exports={render,setTab:t=>{tab=t},setVenue,venue:()=>venue,venueStatus,venueToday,venueKey,loadVenues,setRhUnit,setRhNet,rhDayValue,rhCalNs,setCalUnit,fmtSOL,fmtUSD,calUnit:()=>calUnit,calPick,fmtCompact,money,pnlModel};', ctx);
  extra.content = content;
  extra.exports = ctx.module.exports;
  await new Promise(resolve => setImmediate(resolve));
  if (rhTab) ctx.module.exports.setVenue('robinhood', false);
  ctx.module.exports.setTab(rhTab || tab); await ctx.module.exports.render();
  const first = content.innerHTML, before = calls.filter(u => !u.startsWith('/api/venues')).length;
  intervals.forEach(fn => fn()); await new Promise(resolve => setImmediate(resolve));
  assert(!/NaN|undefined/.test(first), first);
  return {exports: ctx.module.exports, html: first, stamp: stamp.textContent, timerFetches: calls.filter(u => !u.startsWith('/api/venues')).length - before, calls, log: els['#rhlog'].innerHTML, count: els['#rhcount'].textContent};
}
(async () => {
  const warning = 'Local collection failed; last successful snapshot retained';
  for (const tab of ['capital', 'live', 'rh:overview', 'rh:capital', 'rh:live', 'journal', 'hermes', 'redis', 'overview', 'ops']) {
    const r = await render(tab, {collected_at: 123, collection_error: warning, rows: [], total_in_retained_tail: 0, services: [], sources: []});
    assert(r.html.includes(warning) && r.html.includes('role="alert"'), tab);
    assert(r.stamp.includes('Observed') && !r.stamp.endsWith('Unknown'), tab);
    if (['capital', 'live', 'rh:capital', 'rh:live'].includes(tab)) assert(r.timerFetches > 0, tab);
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
  // Calendar fixture: a deposit day, a day whose flows are unknown, gains, a loss, a flat fallback day (today).
  const tr=(r,x)=>({...r,d_external_sol:x,d_trading_sol:isFinite(r.d_cash_sol)&&x!=null?r.d_cash_sol-x:null});
  const calDays=[tr({day:'2024-10-01',status:'ok',cash_sol:1.5021,d_cash_sol:0.5021},0.5),days[0],
    tr({...days[1],d_cash_sol:0.01},null),tr(days[2],0),tr(days[3],0),{...tr(days[4],0),cash_fallback:true,cash_ts:1728200000}];
  const month={month:'2024-10',tz:'America/Sao_Paulo',north_star:{month:'2024-10',first_month:'2024-06',current_month:'2024-10',days:calDays,positions:{status:'ok',days:{'2024-10-04':3},positions:5,volume_sol:2.5,volume_measured:5,fees_sol:0.012,fees_measured:4,win_rate_pct:60,realized_measured:5,best_win_sol:0.004,avg_hold_min:135,hold_measured:5}}};
  const charted = await render('capital', {tz:'America/Sao_Paulo', tz_fallback:false, north_star:{status:'ok',days},
    nav_bridge:{status:'incomplete_sources',incomplete_sources:['closes'],d_known_sol:-0.01,components:[
      {component:'network_fees',label:'Network fees',sol:-0.003},{component:'lp_realized',label:'LP realized',sol:null,measured_subtotal_sol:-0.02},{component:'unexplained',label:'Unexplained',sol:null}]}},
    false, {'capital/month': month, 'price/sol': {status:'ok', usd:150}});
  const h = charted.html;
  assert(h.includes('Unexplained <span class="badge">residual</span>'), 'residual badge keyed by component id');
  assert(h.includes('days in America/Sao_Paulo') && h.includes('4 Oct 2024 (America/Sao_Paulo)'), 'zone named on day labels');
  // Revision 5 grid: dashed cells tinted violet (profit) / grey (loss) by size against the month's largest move.
  const M = (sign, cls, cur, body) => `<span class="mv">${sign ? `<span class="sg ${cls}">${sign}</span>` : ''}${cur === '$' ? '$' + body : body + '<small class="unit"> SOL</small>'}</span>`;
  assert(h.includes('class="cell pos" style="--a:0.240"') && h.includes('class="cell neg" style="--a:0.300"') && h.includes('class="cell unk"') && !/pos-[123]|neg-[123]/.test(h), 'calendar tints');
  assert(h.includes('<div class="cell adj"><span class="d">30</span></div>') && h.includes('<div class="cell nod"><span class="d">7</span></div>'), 'adjacent-month and no-data days');
  // Money: only sign + unit glyph coloured, real SOL never silently scaled; flat today; fallback starred; n/a is n/a.
  assert(h.includes(`<span class="vf">${M('+', 'up', '◎', '0.0030')}</span>`) && h.includes(`<span class="vf">${M('−', 'down', '◎', '0.0040')}</span>`) && h.includes('class="cell nod today"'), 'signed SOL values with glyph and today marker');
  assert(!/\+3\.00|mSOL/.test(h), 'no unlabelled milli-SOL');
  assert(h.includes(`<span class="vf">${M('', 'nil', '◎', '0.0000')}*</span>`) && h.includes('Cash from an earlier reading'), 'fallback day keeps the * marker');
  assert(h.includes('<span class="vf"><span class="mv na">n/a</span></span>') && !/class="cell unk"[^>]*>(?:(?!<\/div>).)*0\.0000/.test(h), 'unmeasured day is n/a');
  assert(/Unmeasured&#10;|Unmeasured\n/.test(h) && h.includes('No NAV snapshot this day'), 'unmeasured tooltip');
  assert(h.includes('Trading +0.0030 SOL · +$0.45 at current SOL price'), 'tooltip carries both units');
  // Deposits are not trading: the cell shows the trading change, tags the flow, and the tooltip reconciles.
  assert(h.includes(`<span class="vf">${M('+', 'up', '◎', '0.0021')}</span>`) && !h.includes('0.5021</span></span>'), 'deposit day shows trading only');
  assert(h.includes('<span class="tw">deposit</span><span class="ts" aria-hidden="true">dep</span> <span class="ta">+0.5000</span>'), 'deposit tag');
  assert(h.includes('Deposit +0.5000 SOL excluded (Δ cash +0.5021 SOL)'), 'tooltip reconciles the flow');
  assert(h.includes('Deposits and withdrawals unknown, so trading cannot be split out (Δ cash +0.0100 SOL)'), 'unknown flows leave trading unmeasured');
  // Positions closed per day, from the closes journal.
  assert(h.includes('<span class="np">3 pos</span>') && h.includes('<span class="np">0 pos</span>') && h.includes('3 positions closed'), 'N pos per day');
  // Header: the month's trading PnL, big; flows listed apart from it.
  assert(h.includes(`<span class="caps">October 2024 <span class="acc">PnL</span></span><strong>${M('+', 'up', '◎', '0.0011')}</strong>`), 'big month PnL, trading only');
  assert(h.includes('deposits +0.5000 SOL excluded · cash incl. flows +0.5111 SOL · 2 days n/a, not counted'), 'flows listed separately');
  // WEEK column and weekday totals (Monday-first). October 2024 starts on a Tuesday: 5 week rows.
  assert(h.includes('<span class="dow wkh">WEEK</span>') && (h.match(/<div class="wk">/g) || []).length === 5, 'WEEK column, one pill per row');
  assert(h.includes(`<small><span class="pl">W1</span><span class="ps" aria-hidden="true">W1</span></small><b>${M('+', 'up', '◎', '0.0011')}</b>`), 'week 1 total');
  assert(h.includes(`<span class="pl">Tuesdays</span><span class="ps" aria-hidden="true">Tue</span></small><b>${M('+', 'up', '◎', '0.0021')}</b>`)
    && h.includes(`<span class="pl">Saturdays</span><span class="ps" aria-hidden="true">Sat</span></small><b>${M('−', 'down', '◎', '0.0040')}</b>`)
    && h.includes('<span class="pl">Mondays</span><span class="ps" aria-hidden="true">Mon</span></small><b><span class="mv na">n/a</span></b>'), 'weekday totals, n/a when unmeasured');
  assert(h.includes('<div class="chiplist" aria-label="Week and weekday totals">'), 'phone fallback lists exist');
  // Footer stat strip from the closes/realized journals; partial measurement is disclosed, unmeasurable is n/a (never a dash).
  assert(h.includes(`<span class="caps">Volume</span><b>${M('', 'nil', '◎', '2.5000')}</b>`) && h.includes('<span class="caps">Win rate</span><b>60.0<small class="unit"> %</small></b>'), 'volume and win rate');
  assert(h.includes('title="4 of 5 positions have a measured fee figure"><span class="caps">Fees</span>') && h.includes(`<span class="caps">Best win</span><b>${M('+', 'up', '◎', '0.0040')}</b>`), 'fees and best win');
  assert(h.includes('<span class="caps">Positions</span><b>5</b>') && h.includes('<span class="caps">Avg hold</span><b>2h 15m</b>') && !/—/.test(h), 'positions, hold, no em dash');
  assert(!h.includes('class="calsum"') && !h.includes('class="spark"'), 'summary panel removed');
  assert(!h.includes('◎') && !/class="(pill|dot|conn|vconn)"/.test(h) && h.includes('<span class="tchip up"><small><span class="pl">W1</span>') && h.includes('<span class="tchip down"><small><span class="pl">Saturdays</span>') && h.includes('<span class="tchip nil"><small><span class="pl">W2</span>'), 'text unit, no glyph; dark chips with sign bar, no pills or connectors');
  // Native month input bounded by the data; arrows disabled at the ends.
  assert(/<input type="month" id="calpick" aria-label="Month" value="2024-10" min="2024-06" max="2024-10"/.test(h) && /id="calnext"[^>]*disabled/.test(h) && !/id="calprev"[^>]*disabled/.test(h) && !h.includes('<select id="calpick"'), 'native month input');
  assert((h.match(/class="calkey"/g) || []).length === 1, 'one key');
  assert(charted.calls.some(u => /^\/api\/capital\/month\?month=&tz=/.test(u)) && charted.calls.includes('/api/price/sol'), 'month and price requested');
  // USD view: every money value in dollars; the header says the price is current, not historical.
  const usd = await render('capital', {tz:'America/Sao_Paulo', north_star:{days}, nav_bridge:{}}, false,
    {'capital/month': month, 'price/sol': {status:'ok', usd:150}, store: {'azimuth.calUnit': 'usd'}});
  assert(usd.html.includes(M('+', 'up', '$', '0.45')) && usd.html.includes(M('−', 'down', '$', '0.60')) && usd.html.includes('USD at current SOL price'), 'USD cells');
  assert(usd.html.includes('<span class="ta">+$75.00</span>') && usd.html.includes('deposits +$75.00 excluded') && usd.html.includes(`<span class="caps">Volume</span><b>${M('', 'nil', '$', '375.00')}</b>`) && usd.html.includes('data-unit="usd" aria-pressed="true"'), 'USD flows, stats and toggle state');
  // No price: USD disabled with its reason, SOL still renders, the stored preference is kept.
  const noPrice = await render('capital', {north_star:{days}, nav_bridge:{}}, false,
    {'capital/month': month, 'price/sol': {status:'unavailable', usd:null}, store: {'azimuth.calUnit': 'usd'}});
  assert(/data-unit="usd" aria-pressed="false" title="USD unavailable[^"]*" disabled/.test(noPrice.html) && noPrice.html.includes(M('+', 'up', '◎', '0.0030')), 'USD fails soft');
  // Unreadable position journals: the grid stays, the strip says why.
  const noPos = await render('capital', {north_star:{days}, nav_bridge:{}}, false,
    {'capital/month': {...month, north_star: {...month.north_star, positions: {status:'unavailable', collection_error:'Panel evidence could not be read: OSError'}}}});
  assert(noPos.html.includes('Position statistics unavailable: Panel evidence could not be read: OSError') && !noPos.html.includes('class="np"') && noPos.html.includes('class="pnl"'), 'position stats fail soft');
  // A month that failed to load must not take the rest of the capital tab down.
  const noMonth = await render('capital', {north_star:{days}, nav_bridge:{}}, false, {failing: ['capital/month', 'price/sol']});
  assert(noMonth.html.includes('Calendar month could not be loaded') && noMonth.html.includes('capital / balance'), 'month failure is local');
  // Unit formatting: about four significant decimals in SOL, cents in USD, explicit sign and unit, n/a for null.
  const fx_ = {}; await render('overview', {services: [], sources: []}, false, fx_); const f = fx_.exports;
  for (const [v, want] of [[0.012, '+0.0120 SOL'], [-0.0005, '−0.0005 SOL'], [0.00003, '+0.00003 SOL'], [0.3668, '+0.3668 SOL'], [-1.5, '−1.5000 SOL'],
    [0, '0.0000 SOL'], [-0.0, '0.0000 SOL'], [1e-12, '0.0000 SOL'], [null, 'n/a'], [undefined, 'n/a']]) assert.equal(f.fmtSOL(v), want, String(v));
  for (const [v, want] of [[0.87, '+$0.87'], [-0.05, '−$0.05'], [0.004, '+$0.004'], [-0.00015, '−$0.0002'], [0.0000004, '+$0.0000004'], [1234.5, '+$1,234.50'], [0, '$0.00'], [null, 'n/a']]) assert.equal(f.fmtUSD(v), want, String(v));
  // Narrow-grid and phone cells: compact, never a fake zero for a real move.
  for (const [v, u, want] of [[0.0106, 'sol', '+0.0106'], [-0.000002, 'sol', '≈0'], [0, 'sol', '0.0000'], [null, 'sol', 'n/a'],
    [0.0058, 'usd', '+$0.87'], [-0.000002, 'usd', '≈0'], [1.5, 'usd', '+$225.00']]) assert.equal(f.fmtCompact(v, u, 150), want, `${v} ${u}`);
  assert(h.includes(`<span class="vc" aria-hidden="true">${M('+', 'up', '◎', '0.0030')}</span>`) && f.money(-0.000002, 'sol', 150, {compact: true}) === '<span class="mv">≈0</span>', 'compact value rendered');
  // Week model: Monday-first rows, weekday sums skip unmeasured days, a week with nothing measured is n/a.
  const md = f.pnlModel({month: '2024-02', days: [{day: '2024-02-05', d_trading_sol: 0.01}, {day: '2024-02-12', d_trading_sol: -0.02}, {day: '2024-02-13', d_trading_sol: null}]});
  assert.equal(md.weeks.length, 5); assert.equal(md.weeks[0].days[0].key, '2024-01-29'); assert.equal(md.weeks[0].total, null);
  assert(Math.abs(md.weekday[0] - -0.01) < 1e-12 && md.weekday[1] === null && Math.abs(md.weeks[2].total - -0.02) < 1e-12 && md.max === 0.02, 'week model');
  // Toggle persistence: stored per viewer, read back on load, and every storage failure is swallowed.
  const kept = {}; const a = {store: kept}; await render('overview', {services: [], sources: []}, false, a);
  assert.equal(a.exports.calUnit(), 'sol', 'default unit is SOL'); a.exports.setCalUnit('usd'); assert.equal(kept['azimuth.calUnit'], 'usd');
  const b = {store: kept}; await render('overview', {services: [], sources: []}, false, b); assert.equal(b.exports.calUnit(), 'usd', 'unit restored');
  const c = {store: {'azimuth.calUnit': '<script>'}}; await render('overview', {services: [], sources: []}, false, c); assert.equal(c.exports.calUnit(), 'sol', 'unknown stored value ignored');
  const blocked = {store: 'throw'}; await render('overview', {services: [], sources: []}, false, blocked);
  assert.equal(blocked.exports.calUnit(), 'sol'); blocked.exports.setCalUnit('usd'); assert.equal(blocked.exports.calUnit(), 'usd', 'blocked storage still toggles for the session');
  assert(h.includes('class="unm"') && (h.match(/class="bar fp"/g)||[]).length===1 && (h.match(/class="bar fn"/g)||[]).length===1, 'delta bars: one gain, one loss, hatched unmeasured');
  assert(h.includes('<div class="val">Unknown</div>') && h.includes('class="seg dn"') && h.includes('Δ known SOL, window total'), 'waterfall unknown and total');
  assert(h.includes('tabindex="0" role="group"') && h.includes('Arrow keys'), 'charts keyboard reachable');
  assert(h.includes('Day (America/Sao_Paulo)'), 'table header names zone');
  const fallback = await render('capital', {tz:'UTC', tz_fallback:true, north_star:{days:[]}, nav_bridge:{}});
  assert(fallback.html.includes('days are shown in UTC') && fallback.html.includes('No measured values in this window yet.'), 'fallback + empty states');
  assert(fallback.html.includes('Calendar month could not be loaded') && fallback.html.includes('The NAV bridge has no components'), 'empty chart states');
  const emptyMonth = await render('capital', {north_star:{days:[]}, nav_bridge:{}}, false,
    {'capital/month': {month:'2024-08', north_star:{month:'2024-08', first_month:'2024-08', current_month:'2024-10', days:[]}}});
  assert(emptyMonth.html.includes('No NAV snapshots in August 2024.') && !emptyMonth.html.includes('class="calsum"') && /id="calprev"[^>]*disabled/.test(emptyMonth.html), 'empty month: n/a total, no older month');
  // Picks outside the data or a cleared input are calm empty states, never an error, and cost no request.
  const pick = {'capital/month': month, 'price/sol': {status:'ok', usd:150}};
  await render('capital', {north_star:{days}, nav_bridge:{}}, false, pick);
  const asked = () => pick.content.innerHTML;
  for (const [m, want, state] of [['', 'No month picked. Choose one from June 2024 to October 2024.', 'empty'],
    ['2023-12', 'December 2023 has no capital data: the NAV journal starts in June 2024.', 'range'],
    ['2025-02', 'February 2025 has no capital data: the NAV journal starts in June 2024, and the latest month is October 2024.', 'range']]) {
    assert.equal(pick.exports.calPick(m), state, m); await pick.exports.render();
    assert(asked().includes(want) && !asked().includes('role="status"') && !asked().includes('could not be loaded'), m + ': ' + want);
    assert(/id="calprev"[^>]*disabled/.test(asked()) && /id="calnext"[^>]*disabled/.test(asked()) && !asked().includes('class="calsum"'), m + ' controls');
  }
  assert.equal(pick.exports.calPick('2024-09'), ''); await pick.exports.render();
  assert(!asked().includes('No month picked') && asked().includes('class="pnl"'), 'a valid pick leaves the empty state');
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
  const rhPayload = {collected_at: 200000, tz: 'UTC', monitor_active: false,
    unit: {Id: 'azimuth-rh-monitor.service', ActiveState: 'inactive', SubState: 'dead', UnitFileState: 'disabled'},
    modes: {status: 'ok', started_at: 1000, flags: {robinhood: false, 'rh-turnover': true}},
    logs: [{time: 300, unit: 'azimuth-rh-monitor.service', line: 'turnover re-center ok'}, {time: 200, unit: 'azimuth.service', line: 'scanner[rh-turnover]: gas spike <b>'}],
    positions: [{protocol: 'v4', token_id: '1', pool: '0x' + 'c'.repeat(40), strategy: 'weth_below', quote: 'ETH', token: '[masked]', token_address: 'position-public-token', tick_lower: -600, tick_upper: 0, minted_at: 100, age_s: 90000, last_failed_close: {time: 150, reason: 'revert'}}],
    stranded: {open: [{symbol: 'XYZ', token: '0x' + 'd'.repeat(40), token_address: 'stranded-public-token', amount_raw: '107037025008', reason: 'no pool', time: 120, attempts: 4, next_try: 130}], resolved: [], sources: [{path: 'uni_stranded.jsonl', status: 'ok', rows: 1}, {path: 'uni_v4_stranded.jsonl', status: 'unavailable', rows: 0}]},
    closes: {tz: 'UTC', status: 'ok', closes_total: 3, skipped: {failed: 1, dry_run: 0}, gas: {gas_eth: 0.003, gas_txs: 5, metered: 2, unmetered: 1},
      totals: {ETH: {closes: 2, measured: 1, unmeasured: 1, realized_quote: 0.01, mark_flagged: 1}, USDG: {closes: 1, measured: 0, unmeasured: 1, realized_quote: null, mark_flagged: 0}, unknown: {closes: 2, measured: 0, unmeasured: 2, realized_quote: null, mark_flagged: 0}},
      days: {'1970-01-02': {ETH: {closes: 2, measured: 1, unmeasured: 1, realized_quote: 0.01}}, '1970-01-03': {USDG: {closes: 1, measured: 0, unmeasured: 1, realized_quote: null}}},
      closes: [{time: 90000, reason: 'fill', asset: 'ETH', realized_quote: null, pnl_basis: 'mark', mark_flagged: true, pnl_pct: 90, age_min: 30, gas_eth: null},
               {time: 86500, reason: 'turnover re-center', asset: 'ETH', realized_quote: 0.01, pnl_basis: 'realized', mark_flagged: false, pnl_pct: 2, age_min: 5, gas_eth: 0.001, gas_txs: 3}]}};
  // The venue's sections split the one payload: status and money on overview, charts on capital, tables on live.
  const rh = await render('rh:live', rhPayload), rhO = await render('rh:overview', rhPayload), rhC = await render('rh:capital', rhPayload, false, {'robinhood/month': {month: '1970-01', robinhood: {month: '1970-01', first_month: '1970-01', current_month: '1970-01', days: {}, stats: {}}}, 'price/eth': {status: 'unavailable', usd: null}});
  const rhAll = rhO.html + rhC.html + rh.html;
  assert(rh.calls.some(u => /^\/api\/robinhood\?tz=.+&n=200$/.test(u)), 'viewer zone and default log length requested');
  assert(rhAll.includes('Monitor inactive') && rhAll.includes('weth_below'), 'inactive monitor keeps history');
  assert(rhAll.includes('Realized · USDG</span><strong>Unknown</strong>'), 'wholly unmeasured USDG is Unknown, not 0');
  assert(rhAll.includes('+0.010000') && rhAll.includes('mark: value left behind') && rhAll.includes('Unmeasured'), 'mark row is flagged, not money');
  assert(rhAll.includes('>−0.003000<') && rhAll.includes('1 unmetered'), 'gas is a cost, unmetered counted');
  assert(rhAll.includes('No USDG') === false && /hatch|url\(#h/.test(rhC.html), 'unmeasured day hatched');
  assert(rhAll.includes('position-public-token') && rhAll.includes('stranded-public-token'), 'public token address aliases survive credential masking');
  assert(rhAll.includes('107037025008') && rhAll.includes('raw units'), 'stranded amount labelled raw');
  assert(!rhAll.includes(KEY), 'no key-shaped data');
  assert(rh.log.includes('turnover re-center ok') && rh.log.includes('&lt;b&gt;') && !rh.log.includes('<b>'), 'log escaped');
  assert(rh.count.startsWith('2 of 2'), 'log count');
  assert(rhAll.includes('Realized · unknown unit · never summed</span><strong>Unknown</strong>'), 'unknown unit never summed');
  assert(rhAll.includes('Stranded evidence: partial'), 'stranded source coverage shown, a refused source is not an empty inventory');
  assert(rh.timerFetches > 0, 'robinhood refreshes on the timer');
  const rhEmptyP = {collected_at: 1, unit: {}, modes: {status: 'unknown', flags: {}, note: 'azimuth.service is not running'}, logs: [], positions: [], stranded: {}, closes: {totals: {}, days: {}, closes: []}};
  const rhEmpty = await render('rh:live', rhEmptyP), rhEmptyO = await render('rh:overview', rhEmptyP), rhEmptyC = await render('rh:capital', rhEmptyP, false, {'robinhood/month': {month: '1970-01', robinhood: {month: '1970-01', first_month: null, current_month: '1970-01', days: {}, stats: {}}}, 'price/eth': {status: 'unavailable', usd: null}});
  assert(rhEmptyO.html.includes('Robinhood modes unknown') && rhEmptyC.html.includes('No ETH closes in this window.'), 'empty robinhood');
  assert(rhEmptyC.html.includes('No Robinhood closes in January 1970.'), 'empty calendar month names the venue source');
  assert(rhEmptyO.html.includes('robinhood / wallet') && rhEmptyO.html.includes('No wallet snapshots yet') && rhEmptyO.html.includes('install.sh --with-rh-nav'), 'no snapshots: an empty state, not a fake balance');
  assert(rhEmptyC.html.includes('robinhood / balance') && rhEmptyC.html.includes('there is no balance line'), 'balance empty state');
  // Wallet NAV from uni_nav.jsonl: per-asset totals, never summed; unmeasured parts are n/a, never 0.
  const navP = {...rhEmptyP, nav: {status: 'ok', source: {status: 'ok'}, basis: 'synthetic basis', latest: {ts: 1, status: 'partial', eth: 0.5, weth: 0.25, usdg: null,
      lp_mark_quote: {ETH: 0.1, USDG: 40}, lp_positions: {ETH: 1, USDG: 1}, lp_ghosts: 2, errors: ['usdg balance unreadable'], eth_total: 0.85, usdg_total: null},
    days: [{day: '1970-01-01', status: 'no_snapshot'}, {day: '1970-01-02', status: 'ok', ts: 2, eth_total: 0.8, usdg_total: 50, eth: 0.45, weth: 0.25, lp_eth: 0.1, usdg: 10, lp_usdg: 40, d_eth_total: null},
           {day: '1970-01-03', status: 'partial_day', ts: 3, eth_total: 0.85, usdg_total: null, eth: 0.5, weth: 0.25, lp_eth: 0.1, usdg: null, lp_usdg: 40, d_eth_total: 0.05}]}};
  const navO = await render('rh:overview', navP), navC = await render('rh:capital', navP, false, {'robinhood/month': {month: '1970-01', robinhood: {month: '1970-01', days: {}, stats: {}}}, 'price/eth': {status: 'unavailable', usd: null}});
  assert(navO.html.includes('ETH · wallet + positions</span><strong>0.8500 ETH</strong>') && navO.html.includes('native 0.5000 ETH · WETH 0.2500 ETH · in 1 positions 0.1000 ETH'), 'ETH total with its parts');
  assert(navO.html.includes('USDG · wallet + positions</span><strong>n/a</strong>') && navO.html.includes('a part is unmeasured, so no total'), 'USDG unmeasured is n/a, never 0');
  assert(navO.html.includes('Last snapshot partial: usdg balance unreadable') && navO.html.includes('2 journal-open positions hold no liquidity'), 'partial snapshot and ghosts named');
  assert(navO.html.includes('never added') && !navO.html.includes('No wallet snapshots yet'), 'assets never summed');
  assert(navC.html.includes('robinhood / balance') && navC.html.includes('ETH · native + WETH + positions') && navC.html.includes('stroke:var(--s1)') && navC.html.includes('stroke:var(--s2)'), 'one line chart per asset');
  assert(navC.html.includes('No NAV bridge yet') && /class="bar fp"/.test(navC.html), 'daily ETH change bars; NAV bridge named as missing');
  assert(rhEmpty.log.includes('No log lines retained'), 'empty log state');
  const rhFail = await render('rh:live', null, true);
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
  const ef = await render('ops', {collected_at: 1, alerts: [], funnel: {}, health: {}, entry_funnel: {status: 'ok',
    windows: [{hours: 24, batches: 65, batch_pools: 66, routes: {hermes_ai: 65, deterministic_fallback: 3}, fallback_reasons: {timeout: 3},
               deploys: {total: 3, verified: 2, unverified: 1, unknown: 0}, rejects: {conviction_floor: 2, '<i>x</i>': 1}},
              {hours: 1, batches: 5, batch_pools: 5, routes: {hermes_ai: 5, deterministic_fallback: 0}, fallback_reasons: {}, deploys: {total: 0}, rejects: {}}],
    ticket: {status: 'ok', base_ticket_sol: 0.1, minimum_entry_sol: 0.1, min_score: {pulse: {floor: 30, min_score: 66}, multiday: {floor: 12, min_score: null}}},
    score_bands: {since: 1793890800, bands: {'<50': {n: 1, measured: 1, pending: 0, sum_sol: -0.002, mean_sol: -0.002}}}}});
  assert(ef.html.includes('ops / entry-funnel') && ef.html.includes('conviction_floor') && ef.html.includes('(timeout 3)'), 'entry funnel windows and gates');
  assert(ef.html.includes('&lt;i&gt;x&lt;/i&gt;') && !ef.html.includes('<i>x</i>'), 'reject gate escaped');
  assert(ef.html.includes('None (base below minimum)') && ef.html.includes('>66<'), 'clearing score per mode');
  assert(ef.html.includes('−0.002000') && ef.html.includes('&gt;=70'), 'score bands, unmeasured shown as Unknown');
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
  // An unmeasured LP mark renders as unmeasured with its reason, never as 0 or a crash.
  const lpNull = await render('overview', {nav: {native_sol: 1, ts: 1, lp_mark_sol: null, known_asset_subtotal_sol: null, lp_mark_unmeasured_reason: 'lp_count_mismatch'}, services: [], sources: []});
  assert(lpNull.html.includes('LP capital mark · SOL') && lpNull.html.includes('Unmeasured (lp_count_mismatch)'), 'null LP mark shows unmeasured + reason');
  assert(!lpNull.html.includes('LP capital mark · SOL</span><strong>0</strong>'), 'null LP mark is never shown as 0');
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
  // Venue switch: a per-viewer choice kept in storage; blocked storage still renders; sections with no Robinhood
  // source say so and never fetch (or show) Solana evidence.
  const vstore = {};
  const sol = await render('capital', {north_star: {days: []}, nav_bridge: {}}, false, {store: vstore, 'capital/month': {month: '2024-10', north_star: {month: '2024-10', days: []}}});
  assert(sol.exports.venue() === 'solana', 'Solana is the default venue');
  sol.exports.setVenue('robinhood', false);
  assert(vstore['azimuth.venue'] === 'robinhood' && sol.exports.venue() === 'robinhood', 'venue persisted per viewer');
  const rhBlocked = await render('rh:overview', rhEmptyP, false, {store: 'throw'});
  assert(rhBlocked.html.includes('robinhood / status'), 'blocked storage still switches venue');
  for (const sec of ['ops', 'journal', 'redis']) {
    const none = await render('rh:' + sec, rhEmptyP, false, {absent: ['#filters', '#prev', '#next']});
    assert(none.html.includes(`robinhood / ${sec}`) && none.html.includes('no Robinhood source'), sec + ' empty state');
    assert(!none.html.includes('Could not load this section'), sec + ' wires no Solana handlers');
    assert(!none.calls.some(u => /\/api\/(agent\/brief|journal|redis)/.test(u)), sec + ' fetches no Solana evidence');
  }
  const rhHermes = await render('hermes', {profile: 'p', sessions: []}, false, {store: {'azimuth.venue': 'robinhood'}});
  assert(rhHermes.exports.venue() === 'robinhood' && rhHermes.html.includes('hermes / runtime'), 'hermes is shared by both venues');
  // Robinhood calendar: realized_quote per day, ETH and USDG apart, gas netted by default and labelled.
  const rhMonth = {month: '2026-08', robinhood: {month: '2026-08', first_month: '2026-07', current_month: '2026-09', status: 'ok', days: {
      '2026-08-03': {ETH: {closes: 2, measured: 2, unmeasured: 0, realized_quote: 0.01}, gas_eth: 0.001, gas_metered: 2, gas_unmetered: 0, positions: 2},
      '2026-08-04': {USDG: {closes: 1, measured: 1, unmeasured: 0, realized_quote: 5}, gas_eth: 0.0005, gas_metered: 1, gas_unmetered: 0, positions: 1},
      '2026-08-05': {ETH: {closes: 1, measured: 0, unmeasured: 1, realized_quote: null}, gas_eth: null, gas_metered: 0, gas_unmetered: 1, positions: 1},
      '2026-08-06': {ETH: {closes: 2, measured: 1, unmeasured: 1, realized_quote: -0.002}, unknown: 1, gas_eth: null, gas_metered: 0, gas_unmetered: 3, positions: 3}},
    stats: {positions: 7, volume: {ETH: 0.5, USDG: 100}, volume_measured: 6, win_rate_pct: 66.67, realized_measured: 3, best_win: {ETH: 0.01, USDG: 5},
      avg_hold_min: 90, hold_measured: 7, gas: {gas_eth: 0.0015, metered: 3, unmetered: 4}, fees: null, fees_note: 'Fees are not journaled per Robinhood close.'}}};
  const E = (sign, cls, body) => `<span class="mv">${sign ? `<span class="sg ${cls}">${sign}</span>` : ''}${body}<small class="unit"> ETH</small></span>`;
  const U = (sign, cls, body) => `<span class="mv">${sign ? `<span class="sg ${cls}">${sign}</span>` : ''}$${body}</span>`;
  const rcal = await render('rh:capital', rhEmptyP, false, {store: {}, 'robinhood/month': rhMonth, 'price/eth': {status: 'ok', usd: 3000}});
  const ch = rcal.html;
  assert(rcal.calls.some(u => /^\/api\/robinhood\/month\?month=&tz=/.test(u)) && rcal.calls.includes('/api/price/eth'), 'month and ETH price fetched');
  assert(ch.includes(`<span class="vf">${E('+', 'up', '0.0090')}</span>`), 'ETH day net of gas');
  assert(ch.includes(`<span class="vf">${E('−', 'down', '0.0005')}</span>`) && ch.includes('USDG: +5.0000 USDG (1 / 1 closes measured), not in the ETH view'), 'USDG-only day in ETH view carries only gas, USDG named');
  assert(/class="cell unk"[^>]*data-tip="n\/a in this view/.test(ch), 'wholly unmeasured ETH day is n/a, never 0');
  assert(ch.includes(`${E('−', 'down', '0.0020')}?</span>`) && ch.includes('1 close with an unknown quote asset, never summed'), 'partial day marked ?, unknown asset counted');
  assert(ch.includes('net of gas (−0.0015 ETH)') && ch.includes('4 closes without a gas reading') && ch.includes('1 USDG close not in the ETH view'), 'header names gas basis and exclusions');
  assert(ch.includes('data-gas="net" aria-pressed="true"') && ch.includes('data-unit="eth" aria-pressed="true"'), 'defaults: ETH, net of gas');
  assert(ch.includes('<span class="caps">Gas paid</span><b><span class="mv">0.0015<small class="unit"> ETH</small></span></b>') && ch.includes('title="Fees are not journaled per Robinhood close."><span class="caps">Fees</span><b><span class="mv na">n/a</span>'), 'gas footer stat; fees n/a with reason');
  assert(ch.includes('class="calstats s7"') && ch.includes('<span class="caps">Win rate</span><b>66.7<small class="unit"> %</small>') && ch.includes('<span class="caps">Avg hold</span><b>1h 30m</b>'), 'seven footer stats');
  assert(ch.includes('<span class="np">3 pos</span>') && /min="2026-07" max="2026-09"/.test(ch), 'N pos and month bounds from the first close');
  assert(!/pnl_pct|NaN/.test(ch), 'mark % never summed');
  // USD, gross: ETH at the current price plus USDG at $1. Without a price a USDG-only day still converts.
  const usdStore = {'azimuth.rhUnit': 'usd', 'azimuth.rhGas': 'gross'};
  const rusd = await render('rh:capital', rhEmptyP, false, {store: usdStore, 'robinhood/month': rhMonth, 'price/eth': {status: 'ok', usd: 3000}});
  assert(rusd.html.includes(`<span class="vf">${U('+', 'up', '30.00')}</span>`) && rusd.html.includes(`<span class="vf">${U('+', 'up', '5.00')}</span>`), 'USD: ETH x price, USDG at $1');
  assert(rusd.html.includes('gross, gas not subtracted') && rusd.html.includes('data-gas="gross" aria-pressed="true"'), 'gross labelled');
  assert(rusd.html.includes(`<span class="caps">Volume</span><b>${U('', 'nil', '1,600.00')}</b>`), 'USD volume mixes assets only after conversion');
  const rnop = await render('rh:capital', rhEmptyP, false, {store: {...usdStore}, 'robinhood/month': rhMonth, 'price/eth': {status: 'unavailable', usd: null}});
  assert(rnop.html.includes(`<span class="vf">${U('+', 'up', '5.00')}</span>`) && rnop.html.includes('ETH price unavailable'), 'USDG-only day works without a price');
  assert(/class="cell unk"[^>]*data-tip="n\/a in this view/.test(rnop.html), 'ETH day without a price is n/a');
  const dormant = await render('rh:capital', rhEmptyP, false, {'robinhood/month': {month: '2026-11', robinhood: {month: '2026-11', first_month: '2026-07', last_month: '2026-08', current_month: '2026-11', days: {}, stats: {}}}, 'price/eth': {status: 'ok', usd: 3000}});
  assert(dormant.calls.some(u => u.startsWith('/api/robinhood/month?month=2026-08&')), 'an empty current month lands on the latest month with closes');
  // Pure day math.
  const X = rcal.exports;
  assert(X.rhDayValue({ETH: {closes: 1, measured: 1, realized_quote: 0.02}, gas_eth: 0.005}, 'eth', true, null) === 0.015, 'net ETH');
  assert(X.rhDayValue({ETH: {closes: 1, measured: 1, realized_quote: 0.02}, gas_eth: 0.005}, 'eth', false, null) === 0.02, 'gross ETH');
  assert(X.rhDayValue({USDG: {closes: 1, measured: 1, realized_quote: 3}}, 'usd', false, null) === 3, 'USDG-only USD needs no price');
  assert(X.rhDayValue({ETH: {closes: 1, measured: 1, realized_quote: 0.02}}, 'usd', false, null) === null, 'ETH in USD needs a price');
  assert(X.rhDayValue({USDG: {closes: 1, measured: 0, realized_quote: null}}, 'usd', false, 3000) === null, 'unmeasured USDG is null');
  assert(X.rhDayValue({USDG: {closes: 1, measured: 1, realized_quote: 3}}, 'eth', false, 3000) === null, 'no ETH close, gross: n/a in ETH');
  // Venue selector: status mapping, today's money, keyboard. Fake tab buttons stand in for the header markup.
  const vtab = v => { const kids = {'.vdot': {className: ''}, '.vlab': {textContent: ''}, '.vday': {innerHTML: ''}}, attrs = {};
    return {dataset: {venue: v}, attrs, kids, focused: 0, tabIndex: 0, title: '', setAttribute(k, x) { attrs[k] = x }, querySelector: s => kids[s], focus() { this.focused++ }} };
  const vs = {solana: {state: 'live', label: 'pulse live', basis: 'Scanner start line: pulse=true; azimuth-sol-monitor active.'},
    robinhood: {state: 'observe', label: 'observe-only', basis: 'deploy enabled=false'}};
  const tabsA = [vtab('solana'), vtab('robinhood')];
  const sel = await render('hermes', {profile: 'p', sessions: []}, false, {tabs: tabsA, store: {},
    venues: {status: vs, today: {solana: {realized_sol: 0.0123}, robinhood: {ETH: {realized: -0.002, closes: 2}, USDG: {realized: null, closes: 0}}}}});
  const [vSol, vRh] = tabsA;
  assert(vSol.kids['.vdot'].className === 'vdot s-live' && vSol.kids['.vlab'].textContent === 'pulse live', 'Solana live: green dot + mode label');
  assert(vRh.kids['.vdot'].className === 'vdot s-observe' && vRh.kids['.vlab'].textContent === 'observe-only', 'Robinhood observe-only: amber dot');
  assert(vSol.title.includes('pulse=true'), 'the basis is the tooltip');
  assert(vSol.kids['.vday'].innerHTML.includes('class="up">+0.0123 SOL') && vSol.kids['.vday'].innerHTML.includes('today'), 'Solana today in SOL, signed');
  assert(vRh.kids['.vday'].innerHTML.includes('class="down">−0.0020 ETH') && !vRh.kids['.vday'].innerHTML.includes('USDG'), 'Robinhood today per asset; an asset with no closes is left out');
  const ve = sel.exports;
  for (const [st, want] of [['live', 'live'], ['observe', 'observe'], ['off', 'off'], ['down', 'down'], ['unknown', 'unknown'], ['bogus', 'unknown']])
    assert(ve.venueStatus({status: {robinhood: {state: st, label: 'x'}}}, 'robinhood').state === want, 'status mapping ' + st);
  assert(ve.venueStatus(null, 'solana').label === 'status unavailable' && ve.venueStatus({error: 'boom'}, 'solana').basis.includes('could not'), 'no answer is never guessed');
  assert(ve.venueToday({today: {robinhood: {ETH: {realized: null, closes: 3}}}}, 'robinhood').includes('n/a ETH'), 'unmeasured closes read n/a, never 0');
  assert(ve.venueToday({today: {solana: {realized_sol: null}}}, 'solana') === '', 'unmeasured Solana today shows nothing');
  assert(ve.venueToday({today: {robinhood: {ETH: {realized: null, closes: 0}}}}, 'robinhood') === 'no closes today', 'a quiet day says so');
  assert(ve.venueKey('ArrowRight', 'solana') === 'robinhood' && ve.venueKey('ArrowRight', 'robinhood') === 'solana' && ve.venueKey('ArrowLeft', 'solana') === 'robinhood', 'arrows wrap');
  assert(ve.venueKey('Home', 'robinhood') === 'solana' && ve.venueKey('End', 'solana') === 'robinhood' && ve.venueKey('Enter', 'solana') === null, 'Home/End; other keys ignored');
  let prevented = 0;
  vRh.onkeydown({key: 'ArrowLeft', preventDefault() { prevented++ }});
  assert(ve.venue() === 'solana' && vSol.focused === 1 && prevented === 1, 'ArrowLeft from Robinhood selects and focuses Solana');
  vSol.onkeydown({key: 'ArrowRight', preventDefault() { prevented++ }});
  assert(ve.venue() === 'robinhood' && vRh.focused === 1 && vRh.attrs['aria-selected'] === 'true' && vSol.attrs['aria-selected'] === 'false', 'ArrowRight selects Robinhood');
  assert(vRh.tabIndex === 0 && vSol.tabIndex === -1, 'roving tabindex: only the selected tab is in the Tab order');
  vSol.onkeydown({key: 'a', preventDefault() { prevented++ }});
  assert(prevented === 2 && ve.venue() === 'robinhood', 'other keys pass through');
  const tabsB = [vtab('solana'), vtab('robinhood')];
  await render('hermes', {profile: 'p', sessions: []}, false, {tabs: tabsB, failing: ['venues']});
  assert(tabsB[0].kids['.vdot'].className === 'vdot s-unknown' && tabsB[0].kids['.vlab'].textContent === 'status unavailable', 'failed status fetch: hollow dot, says so');
  console.log('dashboard render: 59 synthetic cases passed, plus venue and Robinhood calendar cases');
})().catch(error => {console.error(error); process.exitCode = 1;});
