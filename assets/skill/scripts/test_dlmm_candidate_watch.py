"""Live watch receipts stay separate from rejects and cannot backfill entry history."""
import contextlib
from copy import deepcopy
import fcntl
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import dlmm_candidate_watch as watch
import dlmm_pipeline as pipeline
import dlmm_shadow as shadow

POOL = 'CqJVXBTY644ZBtPCkbaqV7Nu8Qzau2A4sChtpkvQQLLi'
MINT = 'EkFRff9a2jKztJHML1LG9FRmEkPJDR6XAYp3uCPdpump'


def cli(records=None, **changes):
    return SimpleNamespace(**dict(dict(mode='pulse', from_batch=json.dumps(records or []),
                                      from_signal=None), **changes))


def candidate(**changes):
    return dict(dict(pool=POOL, base_mint=MINT, sol_is_x=False,
                     secret='must-not-persist', score=999), **changes)


def snapshot():
    return dict(status='observed', pool=POOL, ts=10000, active_bin=0, anchor_bin=0,
                lower_bin=-69, upper_bin=16, price=.001, decimals_x=6,
                decimals_y=9, sol_is_x=False, token_x_mint=MINT,
                token_y_mint=watch.SOL_MINT,
                bins=[dict(id=i, x='0', y='1000000', supply=str(1000000 * 2**64),
                           fee_x='0', fee_y='0', price=.001) for i in range(-69, 17)])


class CandidateWatchTests(unittest.TestCase):
    def due_forecast(self, **changes):
        return dict(dict(version=1, id='frozen-test', status='frozen_prediction',
            pool=POOL, base_mint=MINT, mode='turnover', baseline_ts=6400,
            frozen_at=6401, recorded_at=6402, horizon_seconds=3600,
            horizon_target_ts=10000, bins_below=44,
            allocations=[dict(id=i) for i in range(-44,1)]), **changes)

    def test_expired_watch_still_collects_due_forecast_without_renewing_it(self):
        for version in (1, 2):
            with self.subTest(version=version):
                self.profile = Path(self.directory.name)/str(version)
                forecast_file = self.profile/'memories'/shadow.FORECAST_FILE
                shadow.append(forecast_file, self.due_forecast(version=version))
                before = forecast_file.read_bytes()
                # Original candidate selection has expired; no current watch inputs.
                with patch.object(shadow.time, 'time', return_value=10000), \
                     patch.object(shadow.time, 'monotonic', return_value=0), \
                     patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(snapshot()).encode()) as read:
                    result = shadow.collect_candidate_bins(self.profile, {}, 40)
                    self.assertEqual(result['candidate_bin_snapshots_observed'], 1)
                    self.assertEqual(read.call_count, 1)
                    self.assertEqual(read.call_args.args[0][-1], '0')
                    self.assertEqual(forecast_file.read_bytes(), before)
                with patch.object(shadow.time, 'time', return_value=10300), \
                     patch.object(shadow.time, 'monotonic', return_value=0), \
                     patch.object(shadow.subprocess, 'check_output') as read:
                    shadow.collect_candidate_bins(self.profile, {}, 40)
                    read.assert_not_called()  # Already observed within terminal window.

    def test_forecast_terminal_reuses_only_valid_covering_history(self):
        """A due forecast (no bracket) must not be suppressed by history that does not prove its read."""
        def shifted(anchor):
            row = snapshot(); row.update(anchor_bin=anchor, active_bin=anchor, lower_bin=anchor-69, upper_bin=anchor+16)
            row['bins'] = [dict(b, id=b['id']+anchor) for b in row['bins']]
            return row
        incomplete = snapshot(); incomplete.update(lower_bin=-10); incomplete['bins'] = [b for b in incomplete['bins'] if b['id'] >= -10]
        other_mint = snapshot(); other_mint['token_x_mint'] = watch.SOL_MINT
        malformed = snapshot(); del malformed['bins']
        cases = dict(wrong_anchor=(shifted(5), True), incomplete_coverage=(incomplete, True),
                     wrong_mint=(other_mint, True), malformed=(malformed, True), covering=(snapshot(), False))
        for name, (row, must_read) in cases.items():
            with self.subTest(case=name):
                self.profile = Path(self.directory.name)/name
                shadow.append(self.profile/'memories'/shadow.FORECAST_FILE, self.due_forecast())
                shadow.append(self.profile/'memories/dlmm_candidate_bin_samples.jsonl', dict(row, collected_at=10000))
                with patch.object(shadow.time, 'time', return_value=10300), \
                     patch.object(shadow.time, 'monotonic', return_value=0), \
                     patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(dict(snapshot(), ts=10300)).encode()) as read:
                    result = shadow.collect_candidate_bins(self.profile, {}, 40)
                if must_read:
                    self.assertEqual(read.call_count, 1)
                    self.assertEqual(read.call_args.args[0][-1], '0')  # the forecast's own anchor
                    self.assertEqual(result['candidate_bin_snapshots_observed'], 1)
                else:
                    read.assert_not_called()  # valid covering history completes the terminal

    def test_live_candidate_terminal_read_can_freeze_next_prediction(self):
        forecast_file = self.profile/'memories'/shadow.FORECAST_FILE
        shadow.append(forecast_file, self.due_forecast())
        prior = dict(snapshot(), ts=9700, collected_at=9701, status='observed',
                     base_mint=MINT, mode='turnover', bin_step=100)
        prior['bins'] = [dict(b, y='1000000000', supply=str(1000000000 * 2**64)) for b in prior['bins']]
        shadow.append(self.profile/'memories/dlmm_candidate_bin_samples.jsonl', prior)
        current = dict(snapshot(), bin_step=100)
        current['bins'] = [dict(b, fee_y='100') for b in prior['bins']]
        candidates = {POOL: dict(pool=POOL,base_mint=MINT,mode='turnover',
                                source_id='watch:new',source_ts=9900)}
        with patch.object(shadow.time,'time',return_value=10000), \
             patch.object(shadow.time,'monotonic',return_value=0), \
             patch.object(shadow.subprocess,'check_output',return_value=json.dumps(current).encode()) as read:
            result = shadow.collect_candidate_bins(self.profile,candidates,40)
        self.assertEqual(read.call_count,1)
        self.assertEqual(result['candidate_bin_snapshots_observed'],1)
        self.assertEqual(result['candidate_fee_forecasts_frozen'],1)
        records=shadow.rows(forecast_file)
        self.assertEqual(len(records),2)
        self.assertEqual(records[0]['id'],'frozen-test')
        self.assertEqual(records[1]['baseline_ts'],10000)
        self.assertEqual(records[1]['horizon_target_ts'],13600)
        self.assertLess(records[1]['recorded_at'],records[1]['horizon_target_ts'])

    def test_live_terminal_missing_current_bins_refreshes_without_replacing_terminal(self):
        shadow.append(self.profile/'memories'/shadow.FORECAST_FILE, self.due_forecast())
        terminal = dict(snapshot(), active_bin=50, bin_step=100)
        fresh = dict(terminal, anchor_bin=50, lower_bin=-19, upper_bin=66,
                     bins=[dict(b, id=b['id']+50) for b in snapshot()['bins']])
        candidates = {POOL: dict(pool=POOL, base_mint=MINT, mode='turnover',
                                source_id='watch:new', source_ts=9900)}
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output',
                          side_effect=[json.dumps(terminal).encode(), json.dumps(fresh).encode()]) as read:
            result = shadow.collect_candidate_bins(self.profile, candidates, 40)
        self.assertEqual(result['candidate_bin_snapshots_observed'], 2)
        self.assertEqual(read.call_args_list[0].args[0][-1], '0')
        self.assertEqual(read.call_args_list[1].args[0][-1], '16')
        saved = shadow.rows(self.profile/'memories/dlmm_candidate_bin_samples.jsonl')
        self.assertEqual([s['anchor_bin'] for s in saved], [0, 50])
        self.assertIn('terminal_target_ts', saved[0])
        self.assertNotIn('terminal_target_ts', saved[1])
        self.assertTrue(saved[1]['baseline_refresh_after_terminal'])
        # No prior current geometry: the new sample is evidence for a future
        # forecast, never a fabricated immediately usable prediction.
        self.assertEqual(result['candidate_fee_forecasts_frozen'], 0)

    def test_baseline_refresh_never_displaces_due_terminals_or_exceeds_read_cap(self):
        pools = [POOL, POOL[:-1]+'j', POOL[:-1]+'k']
        candidates = {}
        for pool in pools:
            shadow.append(self.profile/'memories'/shadow.FORECAST_FILE,
                          self.due_forecast(pool=pool, id='frozen-'+pool))
            candidates[pool] = dict(pool=pool, base_mint=MINT, mode='turnover',
                                    source_id='watch:new', source_ts=9900)
        def terminal(command, **kwargs):
            self.assertEqual(command[-1], '0')
            return json.dumps(dict(snapshot(), pool=command[3], active_bin=50, bin_step=100)).encode()
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', side_effect=terminal) as read:
            result = shadow.collect_candidate_bins(self.profile, candidates, 40)
        self.assertEqual(read.call_count, 3)
        self.assertEqual(result['candidate_bin_snapshots_observed'], 3)
        saved = shadow.rows(self.profile/'memories/dlmm_candidate_bin_samples.jsonl')
        self.assertEqual({r['pool'] for r in saved}, set(pools))
        self.assertTrue(all('terminal_target_ts' in r for r in saved))

    def test_expired_terminal_cannot_request_new_baseline_after_price_move(self):
        shadow.append(self.profile/'memories'/shadow.FORECAST_FILE, self.due_forecast())
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output',
                          return_value=json.dumps(dict(snapshot(), active_bin=50, bin_step=100)).encode()) as read:
            result = shadow.collect_candidate_bins(self.profile, {}, 40)
        self.assertEqual(read.call_count, 1)
        self.assertEqual(result['candidate_fee_forecasts_frozen'], 0)

    def test_terminal_watch_rejects_late_future_expired_and_invalid_identity(self):
        for changes in (dict(version=0), dict(version=3), dict(version=True),
                        dict(version=2.0), dict(version='2'),
                        dict(recorded_at=10000), dict(horizon_target_ts=10001),
                        dict(pool='bad'), dict(base_mint=watch.SOL_MINT),
                        dict(frozen_at=float('nan')), dict(horizon_seconds=1),
                        dict(allocations=[]), dict(bins_below=70)):
            candidates = {}
            shadow.index_due_forecast(candidates, self.due_forecast(**changes), 10000)
            self.assertEqual(candidates, {})
        for now in (9999,10601):
            candidates = {}
            shadow.index_due_forecast(candidates, self.due_forecast(), now)
            self.assertEqual(candidates, {})

    def test_due_watch_keeps_pool_and_request_limits(self):
        candidates = {}
        for i in range(65):
            pool = '1'*30 + str(i//9+1) + str(i%9+1)
            shadow.index_due_forecast(candidates, self.due_forecast(pool=pool), 10000)
        self.assertEqual(len(candidates), 64)
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', side_effect=TimeoutError) as read:
            result = shadow.collect_candidate_bins(self.profile, candidates, 40)
            self.assertEqual(read.call_count, 3)
            self.assertEqual(result['candidate_bin_snapshots_attempted'], 3)

    def test_terminal_observation_precedes_ordinary_candidate(self):
        shadow.append(self.profile/'memories'/shadow.FORECAST_FILE, self.due_forecast())
        fresh_pool = '1'*32
        fresh = {fresh_pool: dict(pool=fresh_pool, base_mint=MINT, mode='turnover',
            source_id='fresh', source_ts=10000)}
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', side_effect=TimeoutError) as read:
            shadow.collect_candidate_bins(self.profile, fresh, 40)
        self.assertEqual(read.call_args_list[0].args[0][3], POOL)
        self.assertEqual(read.call_count, 2)

    def test_terminal_snapshot_rejects_executor_that_ignores_frozen_anchor(self):
        shadow.append(self.profile/'memories'/shadow.FORECAST_FILE,
            self.due_forecast(allocations=[dict(id=i) for i in range(-244,-199)]))
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(snapshot()).encode()):
            result = shadow.collect_candidate_bins(self.profile, {}, 40)
        self.assertEqual(result['candidate_bin_snapshots_observed'], 0)
        self.assertEqual(result['candidate_fee_forecasts_frozen'], 0)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.profile = Path(self.directory.name)
        self.file = self.profile / 'memories' / watch.WATCH_FILENAME
        self.env = patch.dict(os.environ, {'DRY_RUN': 'false'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_bounded_public_identities_only(self):
        records = [candidate(pool='1' * 30 + str(i // 9 + 1) + str(i % 9 + 1))
                   for i in range(80)]
        records.insert(1, records[0])
        with patch.object(watch.time, 'time', return_value=10000):
            self.assertEqual(watch.record_pipeline_candidates(self.profile, cli(records)), 64)
        rows = shadow.rows(self.file)
        self.assertEqual(len(rows), 64)
        self.assertEqual(len({r['pool'] for r in rows}), 64)
        self.assertTrue(all(r['id'].startswith('watch:') and r['ts'] == 10000 for r in rows))
        self.assertTrue(all(r['candidate'] == dict(base_mint=MINT, sol_is_x=False) for r in rows))
        self.assertNotIn('must-not-persist', self.file.read_text())
        self.assertNotIn('score', self.file.read_text())

    def test_invalid_dry_run_and_missing_inputs_do_not_append(self):
        invalid = [None, 'record', candidate(pool='bad'), candidate(base_mint=watch.SOL_MINT),
                   candidate(sol_is_x=True), candidate(sol_is_x=0)]
        for args in [cli(invalid), cli(from_batch='bad json'), cli(from_batch='{}'),
                     cli([candidate()], mode='unknown'), cli(from_batch=None)]:
            self.assertEqual(watch.record_pipeline_candidates(self.profile, args), 0)
        with patch.dict(os.environ, {'DRY_RUN': 'true'}):
            self.assertEqual(watch.record_pipeline_candidates(self.profile, cli([candidate()])), 0)
        self.assertFalse(self.file.exists())

    def test_single_signal_and_unavailable_or_busy_journal(self):
        args = cli(from_batch=None, from_signal=json.dumps(candidate()))
        self.assertEqual(watch.record_pipeline_candidates(self.profile, args), 1)
        before = self.file.read_bytes()
        with self.file.open('a') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(watch.record_pipeline_candidates(self.profile, args), 0)
        self.assertEqual(self.file.read_bytes(), before)
        with patch.object(watch.Path, 'mkdir', side_effect=OSError('disk unavailable')):
            self.assertEqual(watch.record_pipeline_candidates(self.profile, args), 0)

    def test_actual_pipeline_records_before_capacity_exit(self):
        params = dict(MIN_TVL_USD=10000, MIN_FEE_TVL_24H=1, MIN_ORGANIC_SCORE=60,
                      MIN_MCAP_USD=150000, MIN_HOLDERS=100, MAX_POSITIONS=1)
        with patch.object(pipeline, 'PROFILE_DIR', str(self.profile)), \
             patch.object(pipeline.sys, 'argv', ['pipeline', '--mode', 'pulse',
                                                '--from-batch', json.dumps([candidate()])]), \
             patch.object(pipeline, 'load_soul_dlmm_params', return_value=params), \
             patch.object(pipeline, 'reconcile_redis_vs_meteora'), \
             patch.object(pipeline, 'get_active_positions_count_for_mode', return_value=1), \
             patch.object(pipeline, 'defer_capacity_signals'), \
             patch.object(pipeline, 'get_wallet_sol_balance', side_effect=AssertionError('capacity exit')), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                pipeline.main()
        self.assertEqual(stopped.exception.code, 0)
        self.assertEqual(len(shadow.rows(self.file)), 1)
        with patch.object(pipeline.sys, 'argv', ['pipeline', '--pick-context']), \
             patch.object(pipeline, 'ai_pick_context', return_value={}), \
             patch.object(pipeline, 'record_pipeline_candidates', side_effect=AssertionError('read-only context')), \
             contextlib.redirect_stdout(io.StringIO()):
            pipeline.main()

    def test_scanner_watch_collected_without_pipeline_or_rejection(self):
        rejects = self.profile / 'rejects.jsonl'
        rejects.write_text('')
        (self.profile / 'solana_candidate_watch.jsonl').write_text(json.dumps(dict(
            ts=10000, pool=POOL, mode='pulse', id='watch:scanner-test',
            source='scanner_before_routing', candidate=dict(base_mint=MINT, sol_is_x=False)))+'\n')
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(snapshot()).encode()) as read, \
             patch.object(shadow, 'collect_liquidation', return_value=0):
            result = shadow.collect(self.profile, rejects)
        self.assertEqual(result['rejects_total'], 0)
        self.assertEqual(result['outcomes_attempted'], 0)
        self.assertEqual(result['candidate_bin_snapshots_observed'], 1)
        self.assertEqual(read.call_count, 1)
        sample = shadow.rows(self.profile / 'memories/dlmm_candidate_bin_samples.jsonl')[0]
        self.assertEqual(sample['source_id'], 'watch:scanner-test')

    def test_actual_collector_watch_is_not_a_reject_or_late_forecast(self):
        with patch.object(watch.time, 'time', return_value=10000):
            watch.record_pipeline_candidates(self.profile, cli([candidate()]))
        rejects = self.profile / 'rejects.jsonl'
        rejects.write_text('')
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(snapshot()).encode()) as read, \
             patch.object(shadow, 'collect_liquidation', return_value=0):
            result = shadow.collect(self.profile, rejects)
        self.assertEqual(result['rejects_total'], 0)
        self.assertEqual(result['outcomes_attempted'], 0)
        self.assertEqual(result['candidate_bin_snapshots_observed'], 1)
        self.assertEqual(read.call_count, 1)
        self.assertFalse((self.profile / 'memories/dlmm_reject_outcomes.jsonl').exists())
        samples = self.profile / 'memories/dlmm_candidate_bin_samples.jsonl'
        self.assertTrue(shadow.rows(samples)[0]['source_id'].startswith('watch:'))
        initial = snapshot()
        initial['ts'] = 10240
        initial['bins'] = [dict(b, fee_y='100') for b in initial['bins'] if -44 <= b['id'] <= 0]
        entry = dict(position='future', pool=POOL, base_mint=MINT, mode='pulse',
                     deployed_at=10241, bin_snapshot=initial)
        self.assertEqual(shadow.pre_entry_bin_coverage([entry], samples, 10300)[0]['status'], 'observed')
        late = deepcopy(entry)
        late['bin_snapshot']['ts'] = 9990
        late['deployed_at'] = 9991
        self.assertEqual(shadow.pre_entry_bin_coverage([late], samples, 10300)[0]['status'], 'unmeasured')


class RejectIdentityTests(unittest.TestCase):
    """Opt-in reject identity and bracket reads; both are no-ops unless enabled."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.profile = Path(self.directory.name)
        self.memory = self.profile / 'memories'
        self.env = patch.dict(os.environ, {'DRY_RUN': 'false'})
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop('DLMM_REJECT_IDENTITY', None)
        os.environ.pop('DLMM_BRACKET_REJECTS', None)

    def reject(self, **changes):
        out = io.StringIO()
        args = dict(dict(profile=self.profile, mode='pulse', gate='pvp', pool=POOL, mint=MINT,
                         sol_is_x=False, name='FOO-SOL'), **changes)
        with contextlib.redirect_stdout(out):
            done = watch.record_pipeline_reject(**args)
        return done, out.getvalue()

    def test_identity_is_off_by_default(self):
        self.assertEqual(self.reject(), (False, ''))
        self.assertFalse((self.memory / watch.REJECT_FILENAME).exists())

    def test_identity_line_and_row(self):
        os.environ['DLMM_REJECT_IDENTITY'] = '1'
        done, printed = self.reject()
        self.assertTrue(done)
        self.assertTrue(printed.startswith('REJECT_IDENTITY '))
        line = json.loads(printed.split(' ', 1)[1])
        row = shadow.rows(self.memory / watch.REJECT_FILENAME)[0]
        self.assertEqual(line, row)
        self.assertEqual((row['pool'], row['mode'], row['gate'], row['name']), (POOL, 'pulse', 'pvp', 'FOO-SOL'))
        self.assertEqual(row['candidate'], dict(base_mint=MINT, sol_is_x=False))
        self.assertTrue(row['id'].startswith('reject:'))
        for bad in (dict(gate='Not A Slug'), dict(pool='invalid'), dict(mode='unknown'), dict(gate=None)):
            self.assertEqual(self.reject(**bad), (False, ''))
        self.assertEqual(len(shadow.rows(self.memory / watch.REJECT_FILENAME)), 1)

    def test_identity_dry_run_prints_without_writing(self):
        os.environ.update(DLMM_REJECT_IDENTITY='1', DRY_RUN='true')
        done, printed = self.reject()
        self.assertTrue(done and printed.startswith('REJECT_IDENTITY '))
        self.assertFalse((self.memory / watch.REJECT_FILENAME).exists())

    def test_identity_write_failure_never_raises(self):
        os.environ['DLMM_REJECT_IDENTITY'] = '1'
        with patch.object(watch.fcntl, 'flock', side_effect=BlockingIOError):
            done, _ = self.reject()
        self.assertFalse(done)

    def test_every_pipeline_skip_line_is_followed_by_its_identity(self):
        import ast
        source = Path(pipeline.__file__).read_text()
        body = [node for node in ast.walk(ast.parse(source)) if hasattr(node, 'body') and isinstance(node.body, list)]
        skips = followed = 0
        gates = set()
        for parent in body:
            for block in (parent.body, getattr(parent, 'orelse', []) or []):
                for i, stmt in enumerate(block):
                    call = getattr(stmt, 'value', None)
                    if not (isinstance(stmt, ast.Expr) and isinstance(call, ast.Call)
                            and getattr(call.func, 'id', None) == 'print' and call.args
                            and isinstance(call.args[0], ast.JoinedStr)):
                        continue
                    head = call.args[0].values[0]
                    if not (isinstance(head, ast.Constant) and head.value.startswith('Skipping ')
                            and not head.value.startswith('Skipping malformed')):
                        continue
                    skips += 1
                    # The identity precedes its skip line, so the daemon's last-line chat
                    # summary (internal/deploy Summarize) can never be an identity line.
                    prev = block[i - 1] if i > 0 else None
                    if (isinstance(prev, ast.Expr) and isinstance(prev.value, ast.Call)
                            and getattr(prev.value.func, 'id', None) == 'record_pipeline_reject'):
                        followed += 1
                        gate = prev.value.args[2].value
                        self.assertRegex(gate, watch.REJECT_GATE)
                        gates.add(gate)
        # Floors keep the AST walk honest: master's pipeline has 29 skip sites over
        # 28 distinct gates (bin_array_rent appears on both sizing paths).
        self.assertGreaterEqual(skips, 29)
        self.assertEqual(followed, skips)
        self.assertGreaterEqual(len(gates), 28)

    def test_reject_outcome_keeps_pool_identity(self):
        row = dict(id='a', ts=100, mode='pulse', gate='cooldown', pool=POOL, snapshot={'pool_price': 1},
                   candidate={'base_mint': MINT, 'sol_is_x': False})
        out = shadow.rejected_outcome(row, 1.02, 1900)
        self.assertEqual((out['pool'], out['base_mint'], out['status']), (POOL, MINT, 'measured'))

    def pipeline_reject(self, ident, gate, ts, pool=POOL):
        shadow.append(self.memory / shadow.PIPELINE_REJECT_FILENAME, dict(
            id=ident, ts=ts, pool=pool, mode='pulse', gate=gate, name='FOO-SOL',
            candidate=dict(base_mint=MINT, sol_is_x=False)))

    def test_brackets_are_off_by_default_and_reads_unchanged(self):
        self.pipeline_reject('reject:a', 'pvp', 9900)
        other = POOL[:-1] + 'j'
        calls = []
        def read(command, **kwargs):
            calls.append(command[3:])
            return json.dumps(dict(snapshot(), pool=command[3])).encode()
        candidates = {other: dict(pool=other, base_mint=MINT, mode='pulse', source_id='w', source_ts=9950)}
        with patch.object(shadow.time, 'time', return_value=10000), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', side_effect=read):
            result = shadow.collect_candidate_bins(self.profile, candidates, 40)
        self.assertEqual(calls, [[other, '69', '16']])
        self.assertNotIn('reject_brackets_scheduled', result)  # OFF adds no keys
        self.assertFalse((self.memory / shadow.BRACKET_FILENAME).exists())

    def test_bracket_baseline_is_stratified_then_terminal_on_same_anchor(self):
        os.environ['DLMM_BRACKET_REJECTS'] = '1'
        pool_b = POOL[:-1] + 'k'
        # gate "pvp" already has a baseline today; "pool_cash_upper_bound" has none -> it goes first
        shadow.append(self.memory / shadow.BRACKET_FILENAME, dict(
            bracket_id='reject:old', bracket_gate='pvp', bracket_phase='baseline', pool=POOL[:-1] + 'm',
            base_mint=MINT, status='observed', ts=5000, anchor_bin=0, collected_at=5000))
        self.pipeline_reject('reject:pvp', 'pvp', 9800)
        self.pipeline_reject('reject:cash', 'pool_cash_upper_bound', 9900, pool=pool_b)
        self.pipeline_reject('reject:stale', 'momentum_m5_dump', 9000, pool=POOL[:-1] + 'n')   # > 10 min old
        clock = [10000]
        reads = []
        def read(command, **kwargs):
            reads.append(command[3:])
            return json.dumps(dict(snapshot(), pool=command[3], ts=int(clock[0]))).encode()
        with patch.object(shadow.time, 'time', side_effect=lambda: clock[0]), \
             patch.object(shadow.time, 'monotonic', return_value=0), \
             patch.object(shadow.subprocess, 'check_output', side_effect=read):
            first = shadow.collect_candidate_bins(self.profile, {}, 40)
            self.assertEqual(first['reject_brackets_scheduled'], 1)
            self.assertEqual(reads, [[pool_b, '69', '16']])
            row = [r for r in shadow.rows(self.memory / shadow.BRACKET_FILENAME) if r['bracket_id'] == 'reject:cash'][0]
            self.assertEqual((row['bracket_phase'], row['status'], row['anchor_bin']), ('baseline', 'observed', 0))
            reads.clear()
            clock[0] = 10000 + shadow.BRACKET_HORIZON_SECONDS + 10
            # A pool that already owns a due terminal keeps it; the bracket terminal waits.
            busy = {pool_b: dict(pool=pool_b, base_mint=MINT, mode='pulse', source_id='f', source_ts=9000,
                                 terminal_only=True, terminal_target_ts=clock[0] - 5, terminal_anchor_bin=3)}
            shadow.index_reject_brackets(self.profile, busy, clock[0], float('inf'), {})
            self.assertEqual(busy[pool_b]['terminal_anchor_bin'], 3)
            second = shadow.collect_candidate_bins(self.profile, {}, 40)
            self.assertGreaterEqual(second['reject_brackets_scheduled'], 1)
            self.assertIn([pool_b, '69', '16', '0'], reads)
            phases = [(r['bracket_id'], r['bracket_phase']) for r in shadow.rows(self.memory / shadow.BRACKET_FILENAME)]
            self.assertIn(('reject:cash', 'terminal'), phases)
            self.assertNotIn('reject:stale', [p[0] for p in phases])
            # A completed bracket is never scheduled or read again, even inside its window.
            reads.clear()
            clock[0] += 300
            third = shadow.collect_candidate_bins(self.profile, {}, 40)
            self.assertEqual(third['reject_brackets_scheduled'], 0)
            self.assertNotIn([pool_b, '69', '16', '0'], reads)


if __name__ == '__main__':
    unittest.main()
