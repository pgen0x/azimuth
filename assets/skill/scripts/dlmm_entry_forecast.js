// Bind a pre-existing diagnostic to entry geometry. Never an admission gate.
const fs = require('node:fs');
const crypto = require('node:crypto');
const MAX_BYTES = 256 * 1024;
const SOL = 'So11111111111111111111111111111111111111112';
const HORIZONS = {turnover: 3600, pulse: 1800, casual: 14400, multiday: 86400};

function entryForecastReference(file, entry, now) {
  const result = {status: 'unmeasured', recorded_at: now,
    basis: 'pre_submission_reference_only; requires_independent_forecast_binding_and_cash_evaluation',
    net_cash_profit_proved: false};
  if (!Number.isFinite(now) || entry.strategy !== 'bid_ask' || entry.token_y_mint !== SOL
      || entry.amount_x !== 0 || entry.amount_y !== 0.1 || entry.bins_above !== 0
      || !Number.isSafeInteger(entry.entry_bin) || !Number.isSafeInteger(entry.bins_below)
      || entry.bins_below < 0 || entry.bins_below >= 70 || !HORIZONS[entry.mode]) {
    return {...result, reason: 'unsupported_entry_geometry'};
  }
  let fd;
  try {
    fd = fs.openSync(file, 'r');
    const stat = fs.fstatSync(fd);
    if (!stat.isFile()) return {...result, reason: 'forecast_journal_unavailable'};
    const start = Math.max(0, stat.size - MAX_BYTES);
    const buffer = Buffer.alloc(Math.min(stat.size, MAX_BYTES));
    const length = fs.readSync(fd, buffer, 0, buffer.length, start);
    const lines = buffer.subarray(0, length).toString('utf8').split('\n');
    if (start > 0) lines.shift(); // Never parse a truncated first record.
    lines.pop(); // Only newline-terminated records are committed observations.
    let selected = null;
    for (const line of lines) {
      let f;
      try { f = JSON.parse(line); } catch { continue; }
      if (!f || f.status !== 'frozen_prediction' || f.version !== 2
          || f.pool !== entry.pool || f.base_mint !== entry.base_mint || f.mode !== entry.mode
          || f.capital_lamports !== 100000000 || f.bins_below !== entry.bins_below
          || f.bin_step !== entry.bin_step || f.horizon_seconds !== HORIZONS[entry.mode]
          || ![f.baseline_ts, f.frozen_at, f.recorded_at, f.horizon_target_ts, f.linear_fee_lamports].every(Number.isFinite)
          || !(f.baseline_ts <= f.frozen_at && f.frozen_at <= f.recorded_at && f.recorded_at <= now)
          || now - f.baseline_ts > 600 || f.horizon_target_ts <= now
          || f.horizon_target_ts !== f.baseline_ts + f.horizon_seconds || f.linear_fee_lamports < 0
          || ![f.id, f.baseline_sha256, f.prior_sha256].every(v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v))
          || !Array.isArray(f.allocations) || f.allocations.length !== entry.bins_below + 1
          || !f.allocations.every((a, i) => a && a.id === entry.entry_bin - entry.bins_below + i)) continue;
      if (!selected || f.recorded_at > selected.f.recorded_at)
        selected = {f, hash: crypto.createHash('sha256').update(line).digest('hex')};
    }
    if (!selected) return {...result, reason: 'no_matching_forecast_in_bounded_tail', tail_limited: start > 0};
    const {f, hash} = selected;
    return {...result, status: 'matched_reference', forecast_id: f.id,
      forecast_line_sha256: hash, baseline_sha256: f.baseline_sha256, prior_sha256: f.prior_sha256,
      forecast_recorded_at: f.recorded_at, baseline_age_seconds: now - f.baseline_ts,
      linear_fee_lamports: f.linear_fee_lamports, tail_limited: start > 0};
  } catch {
    return {...result, reason: 'forecast_journal_unavailable'};
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
}
module.exports = {entryForecastReference, MAX_BYTES};
