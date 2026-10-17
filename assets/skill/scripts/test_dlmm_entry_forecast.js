const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {entryForecastReference, MAX_BYTES} = require('./dlmm_entry_forecast');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'entry-forecast-'));
const file = path.join(dir, 'forecasts.jsonl');
const entry = {pool:'pool',base_mint:'mint',mode:'turnover',strategy:'bid_ask',
  token_y_mint:'So11111111111111111111111111111111111111112',amount_x:0,amount_y:0.1,
  bins_above:0,bins_below:2,entry_bin:-10,bin_step:100};
const forecast = {version:2,status:'frozen_prediction',pool:'pool',base_mint:'mint',mode:'turnover',
  capital_lamports:100000000,bins_below:2,bin_step:100,horizon_seconds:3600,
  baseline_ts:1000,frozen_at:1001,recorded_at:1002,horizon_target_ts:4600,
  linear_fee_lamports:20000,id:'a'.repeat(64),baseline_sha256:'b'.repeat(64),prior_sha256:'c'.repeat(64),
  allocations:[{id:-12},{id:-11},{id:-10}]};
const write = (...rows) => fs.writeFileSync(file, rows.map(r=>JSON.stringify(r)).join('\n')+'\n');
const read = (now=1100, e=entry) => entryForecastReference(file,e,now);
try {
  assert.equal(read().reason,'forecast_journal_unavailable');
  write(forecast);
  assert.equal(read().status,'matched_reference');
  assert.equal(read().net_cash_profit_proved,false);
  assert.equal(read().baseline_age_seconds,100);
  assert.equal(read(1600).status,'matched_reference');
  assert.equal(read(1601).status,'unmeasured');
  for (const change of [{pool:'other'},{base_mint:'other'},{mode:'pulse'},{amount_y:0.2},
    {amount_x:0.001},{bins_above:1},{entry_bin:-9},{bins_below:3},{bin_step:80}]) {
    assert.equal(read(1100,{...entry,...change}).status,'unmeasured');
  }
  for (const change of [{recorded_at:1101},{frozen_at:1101},{baseline_ts:1101},
    {horizon_target_ts:1100},{horizon_seconds:1800},{capital_lamports:200000000},
    {linear_fee_lamports:-1},{linear_fee_lamports:null},{allocations:[{id:-12},{id:-12},{id:-10}]},
    {id:'invalid'},{version:1},{status:'unmeasured'}]) {
    write({...forecast,...change});assert.equal(read().status,'unmeasured');
  }
  // Future and partial appends cannot replace an earlier eligible observation.
  write(forecast,{...forecast,id:'d'.repeat(64),recorded_at:1200});
  fs.appendFileSync(file,'{"partial":');assert.equal(read().forecast_id,forecast.id);
  write(forecast,{...forecast,id:'e'.repeat(64),recorded_at:1050});
  assert.equal(read().forecast_id,'e'.repeat(64));
  // An old matching record outside the read budget cannot be silently selected.
  fs.writeFileSync(file,JSON.stringify(forecast)+'\n'+'x'.repeat(MAX_BYTES)+'\n');
  assert.equal(read().status,'unmeasured');assert.equal(read().tail_limited,true);
  fs.appendFileSync(file,JSON.stringify(forecast)+'\n');
  assert.equal(read().status,'matched_reference');
  console.log('Entry forecast timing, geometry, partial-write and bounded-read checks passed');
} finally { fs.rmSync(dir,{recursive:true}); }
