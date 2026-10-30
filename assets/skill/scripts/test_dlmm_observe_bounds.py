"""Regression tests for the observe-bundle review (I/O bounds, isolation, dedup).

Each test inverts one counterexample from the offline review probes: the opt-in
research observers must stay bounded, never block on special files, never abort
the sampler on a corrupt research journal, and dedup first triggers atomically.
All fixtures are synthetic and local; nothing touches a network or a wallet.
"""
import contextlib
import io
import json
import multiprocessing
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_candidate_watch as watch
import dlmm_monitor as monitor
import dlmm_shadow as shadow

POOL = 'A' * 32
MINT = 'B' * 32
POSITION = 'C' * 32


def reject(ident='reject:new', stamp=9900, pool=POOL):
    return dict(id=ident, ts=stamp, pool=pool, mode='pulse', gate='pvp', name='TEST-SOL',
                candidate=dict(base_mint=MINT, sol_is_x=False))


def sample(pool=POOL, stamp=10000, anchor=0, lower=-69, upper=16):
    return dict(status='observed', pool=pool, ts=stamp, active_bin=anchor, anchor_bin=anchor,
                lower_bin=anchor + lower, upper_bin=anchor + upper, price=.001, decimals_x=6, decimals_y=9,
                sol_is_x=False, token_x_mint=MINT, token_y_mint=watch.SOL_MINT,
                bins=[dict(id=i, x='0', y='1000000', supply=str(1000000 * 2 ** 64), fee_x='0', fee_y='0', price=.001)
                      for i in range(anchor + lower, anchor + upper + 1)])


def shadow_rows(profile):
    path = Path(profile) / 'memories' / monitor.SHADOW_EXITS_FILE
    return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []


def observe_after(profile, barrier):
    monitor.PROFILE_DIR = profile
    os.environ['DLMM_SHADOW_EXITS'] = '1'
    barrier.wait(timeout=5)
    for _ in range(20):
        monitor.shadow_exit_observe(POSITION, 'pulse', -1, -.001, 1, False, {'bot_holders_pct': 25})


def special_file_child(profile, kind, done):
    monitor.PROFILE_DIR = profile
    os.environ.update(DLMM_SHADOW_EXITS='1', DLMM_REJECT_IDENTITY='1', DRY_RUN='false')
    with contextlib.redirect_stdout(io.StringIO()):
        if kind == 'monitor':
            monitor.shadow_exit_observe(POSITION, 'pulse', 0, None, 0, False, {})
        else:
            watch.record_pipeline_reject(profile, 'pulse', 'pvp', POOL, MINT, False, 'TEST-SOL')
    done.set()


class ObserveBoundsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile = Path(self.tmp.name)
        (self.profile / 'memories').mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    # 1. reject writer: bounded payload, lock still nonblocking
    def test_reject_row_payload_is_bounded(self):
        with patch.dict(os.environ, {'DLMM_REJECT_IDENTITY': '1', 'DRY_RUN': 'false'}), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertTrue(watch.record_pipeline_reject(self.profile, 'pulse', 'pvp', POOL, MINT, False, 'N' * 1048576))
        size = (self.profile / 'memories' / watch.REJECT_FILENAME).stat().st_size
        self.assertLess(size, 1024)
        self.assertLess(len(out.getvalue()), 1024)
        row = json.loads((self.profile / 'memories' / watch.REJECT_FILENAME).read_text())
        self.assertEqual(row['name'], 'N' * watch.REJECT_NAME_MAX)

    def test_reject_writer_refuses_full_journal_and_held_lock(self):
        file = self.profile / 'memories' / watch.REJECT_FILENAME
        file.touch()
        with patch.dict(os.environ, {'DLMM_REJECT_IDENTITY': '1', 'DRY_RUN': 'false'}), \
                contextlib.redirect_stdout(io.StringIO()):
            with file.open('a') as held:
                watch.fcntl.flock(held, watch.fcntl.LOCK_EX | watch.fcntl.LOCK_NB)
                self.assertFalse(watch.record_pipeline_reject(self.profile, 'pulse', 'pvp', POOL, MINT, False, 'X'))
            self.assertEqual(file.stat().st_size, 0)
            with patch.object(watch, 'REJECT_MAX_BYTES', 0):
                file.write_text('x\n')
                self.assertFalse(watch.record_pipeline_reject(self.profile, 'pulse', 'pvp', POOL, MINT, False, 'X'))
            self.assertEqual(file.read_text(), 'x\n')

    # 1. both observers return promptly on a FIFO path and write nothing
    def test_fifo_paths_never_block_observers(self):
        ctx = multiprocessing.get_context('fork')
        for kind, name in [('monitor', monitor.SHADOW_EXITS_FILE), ('pipeline', watch.REJECT_FILENAME)]:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'memories' / name
                path.parent.mkdir()
                os.mkfifo(path)
                done = ctx.Event()
                child = ctx.Process(target=special_file_child, args=(tmp, kind, done))
                child.start()
                finished = done.wait(2)
                if child.is_alive():
                    child.terminate()
                child.join(2)
                self.assertTrue(finished, kind)

    # 1. monitor observer: no history scan, O(1) per tick
    def test_monitor_never_rescans_history(self):
        file = self.profile / 'memories' / monitor.SHADOW_EXITS_FILE
        file.write_text(''.join(json.dumps(dict(position=f'old:{i}', variant='half_bot21')) + '\n' for i in range(1000)))
        with patch.dict(os.environ, {'DLMM_SHADOW_EXITS': '1'}), patch.object(monitor, 'PROFILE_DIR', str(self.profile)), \
                patch.object(monitor.json, 'loads', wraps=json.loads) as decode, \
                patch('builtins.open', side_effect=AssertionError('journal must not be read')):
            for _ in range(3):
                monitor.shadow_exit_observe('old:0', 'pulse', 0, None, 0, False, {})
        self.assertEqual(decode.call_count, 0)
        self.assertEqual(len(file.read_text().splitlines()), 1001)  # one new first trigger for old:0

    def test_monitor_first_trigger_once_and_capped(self):
        with patch.dict(os.environ, {'DLMM_SHADOW_EXITS': '1'}), patch.object(monitor, 'PROFILE_DIR', str(self.profile)):
            for _ in range(5):
                monitor.shadow_exit_observe(POSITION, 'pulse', -1, -.001, 1, False, {'bot_holders_pct': 25})
            rows = shadow_rows(self.profile)
            self.assertEqual(sorted(r['variant'] for r in rows), ['give_0.5_1.0', 'half_bot21'])
            self.assertEqual(len({r['event_id'] for r in rows}), 2)
            monitor.shadow_exit_observe('x' * 65, 'pulse', 0, None, 0, False, {})   # oversized id refused
            monitor.shadow_exit_observe('../escape', 'pulse', 0, None, 0, False, {})
            self.assertEqual(len(shadow_rows(self.profile)), 2)

    def test_recorded_triggers_cost_no_journal_open(self):
        with patch.dict(os.environ, {'DLMM_SHADOW_EXITS': '1'}), patch.object(monitor, 'PROFILE_DIR', str(self.profile)):
            monitor.shadow_exit_observe(POSITION, 'pulse', -1, -.001, 1, False, {'bot_holders_pct': 25})
            with patch('os.open', side_effect=AssertionError('steady state must not open the journal')) as opened:
                for _ in range(3):
                    monitor.shadow_exit_observe(POSITION, 'pulse', -1, -.001, 1, False, {'bot_holders_pct': 25})
            self.assertEqual(opened.call_count, 0)

    def test_fifo_with_reader_is_refused_without_claiming_marker(self):
        path = self.profile / 'memories' / monitor.SHADOW_EXITS_FILE
        os.mkfifo(path)
        reader = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        try:
            with patch.dict(os.environ, {'DLMM_SHADOW_EXITS': '1'}), patch.object(monitor, 'PROFILE_DIR', str(self.profile)):
                monitor.shadow_exit_observe(POSITION, 'pulse', 0, None, 0, False, {})
            self.assertEqual(os.read(reader, 4096), b'')  # writer closed, nothing written into the pipe
        finally:
            os.close(reader)
        markers = self.profile / 'memories' / 'dlmm_shadow_exits.d'
        self.assertEqual(list(markers.iterdir()) if markers.exists() else [], [])

    def test_index_failure_is_isolated_from_the_sampler(self):
        with patch.dict(os.environ, {'DLMM_BRACKET_REJECTS': '1'}), \
                patch.object(shadow, 'index_reject_brackets', side_effect=RuntimeError('boom')), \
                patch.object(shadow.time, 'monotonic', return_value=0):
            data = shadow.collect_candidate_bins(self.profile, {}, 40)
        self.assertEqual(data['reject_brackets_scheduled'], 0)
        self.assertEqual(data['reject_brackets_errors'], ['index:RuntimeError'])

    def test_exclusive_marker_decides_a_raced_trigger(self):
        # Deterministic race: both writers pass the cheap pre-check before either claims the marker.
        with patch.dict(os.environ, {'DLMM_SHADOW_EXITS': '1'}), patch.object(monitor, 'PROFILE_DIR', str(self.profile)), \
                patch('os.path.lexists', return_value=False):
            for _ in range(2):
                monitor.shadow_exit_observe(POSITION, 'pulse', -1, -.001, 1, False, {'bot_holders_pct': 25})
        self.assertEqual(sorted(r['variant'] for r in shadow_rows(self.profile)), ['give_0.5_1.0', 'half_bot21'])

    # 4. overlapping writers keep exactly one row per first trigger
    def test_concurrent_writers_keep_one_row_per_trigger(self):
        ctx = multiprocessing.get_context('fork')
        barrier = ctx.Barrier(4)
        procs = [ctx.Process(target=observe_after, args=(str(self.profile), barrier)) for _ in range(4)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(10)
            self.assertEqual(p.exitcode, 0)
        rows = shadow_rows(self.profile)
        self.assertEqual(sorted(r['variant'] for r in rows), ['give_0.5_1.0', 'half_bot21'])

    # 2. bracket index honours the phase deadline
    def test_bracket_index_stops_at_phase_deadline(self):
        file = self.profile / 'memories' / shadow.PIPELINE_REJECT_FILENAME
        file.write_text(''.join(json.dumps(reject(ident=f'reject:old:{i}', stamp=1)) + '\n' for i in range(1000)))
        clock, reads = [0.0], [0]
        original = shadow.research_rows

        def slow(path, *a, **k):
            for row in original(path, *a, **k):
                if Path(path) == file:
                    clock[0] += 1
                    reads[0] += 1
                yield row
        with patch.dict(os.environ, {'DLMM_BRACKET_REJECTS': '1'}), patch.object(shadow, 'research_rows', side_effect=slow), \
                patch.object(shadow.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(shadow.time, 'time', return_value=10000), \
                patch.object(shadow.subprocess, 'check_output', side_effect=AssertionError('RPC forbidden')):
            data = shadow.collect_candidate_bins(self.profile, {}, 40)
        self.assertLessEqual(reads[0], shadow.CANDIDATE_BUDGET_SECONDS + 1)
        self.assertTrue(data['candidate_bin_budget_exhausted'])
        self.assertTrue(data['reject_brackets_deadline'])

    # 2. corrupt research journals are reported, never abort the sampler
    def test_research_journal_corruption_is_isolated_and_reported(self):
        good = json.dumps(reject()) + '\n'
        for bad in ['{\n', json.dumps(dict(reject(), candidate=['bad'])) + '\n', 'x' * 70000 + '\n', '[1]\n']:
            rejects = self.profile / 'scanner.jsonl'
            rejects.write_text('')
            journal = self.profile / 'memories' / shadow.PIPELINE_REJECT_FILENAME
            journal.write_text(bad + good)
            for flag in ['0', '1']:
                with patch.dict(os.environ, {'DLMM_BRACKET_REJECTS': flag}), \
                        patch.object(shadow, 'collect_liquidation', return_value=0) as liquidation, \
                        patch.object(shadow.time, 'time', return_value=10000):
                    shadow.collect(self.profile, rejects)
                self.assertEqual(liquidation.call_count, 1, (bad[:10], flag))
            report = {}
            with patch.dict(os.environ, {'DLMM_BRACKET_REJECTS': '1'}):
                scheduled = shadow.index_reject_brackets(self.profile, {}, 10000, float('inf'), report)
            self.assertEqual(report['reject_brackets_invalid_rows'], 1, bad[:10])
            self.assertEqual(scheduled, 1)  # the valid row after the corrupt one still counts

    def test_special_research_journal_reported_not_read(self):
        journal = self.profile / 'memories' / shadow.PIPELINE_REJECT_FILENAME
        os.mkfifo(journal)
        report = {}
        with patch.dict(os.environ, {'DLMM_BRACKET_REJECTS': '1'}):
            self.assertEqual(shadow.index_reject_brackets(self.profile, {}, 10000, float('inf'), report), 0)
        self.assertEqual(report['reject_brackets_errors'], ['rejects:not_regular_file'])

    # 3. terminal dedup needs the bracket's own anchor and full coverage
    def _bracket_case(self, history):
        shadow.append(self.profile / 'memories' / shadow.BRACKET_FILENAME, dict(
            bracket_id='reject:a', bracket_gate='pvp', bracket_phase='baseline', pool=POOL, base_mint=MINT,
            status='observed', ts=10000, anchor_bin=0))
        if history:
            shadow.append(self.profile / 'memories/dlmm_candidate_bin_samples.jsonl', dict(history, collected_at=13601))
        with patch.dict(os.environ, {'DLMM_BRACKET_REJECTS': '1'}), patch.object(shadow.time, 'time', return_value=13900), \
                patch.object(shadow.time, 'monotonic', return_value=0), \
                patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(sample(stamp=13900)).encode()) as rpc:
            data = shadow.collect_candidate_bins(self.profile, {}, 40)
        brackets = [json.loads(l) for l in (self.profile / 'memories' / shadow.BRACKET_FILENAME).read_text().splitlines()]
        return data, rpc.call_count, [b for b in brackets if b['bracket_phase'] == 'terminal']

    def test_unrelated_anchor_does_not_complete_bracket(self):
        data, reads, terminals = self._bracket_case(sample(stamp=13601, anchor=3))
        self.assertEqual((data['reject_brackets_scheduled'], reads, len(terminals)), (1, 1, 1))
        self.assertEqual(terminals[0]['anchor_bin'], 0)

    def test_partial_coverage_does_not_complete_bracket(self):
        data, reads, terminals = self._bracket_case(sample(stamp=13601, anchor=0, lower=-30))
        self.assertEqual((reads, len(terminals)), (1, 1))

    def test_matching_history_completes_bracket_without_a_read(self):
        data, reads, terminals = self._bracket_case(sample(stamp=13601, anchor=0))
        self.assertEqual((reads, len(terminals)), (0, 1))
        self.assertEqual(terminals[0]['reused_sample_collected_at'], 13601)
        # completion is recorded, so the next run does not schedule it again
        report = {}
        with patch.dict(os.environ, {'DLMM_BRACKET_REJECTS': '1'}):
            self.assertEqual(shadow.index_reject_brackets(self.profile, {}, 13900, float('inf'), report), 0)

    def test_flags_off_touch_nothing(self):
        with patch.dict(os.environ, {'DLMM_SHADOW_EXITS': '0', 'DLMM_REJECT_IDENTITY': '0', 'DLMM_BRACKET_REJECTS': '0'}), \
                patch.object(monitor, 'PROFILE_DIR', str(self.profile)), \
                patch('os.open', side_effect=AssertionError('no I/O when off')):
            self.assertIsNone(monitor.shadow_exit_observe(POSITION, 'pulse', 0, None, 0, False, {}))
            self.assertFalse(watch.record_pipeline_reject(self.profile, 'pulse', 'pvp', POOL, MINT, False, 'X'))
            self.assertEqual(shadow.index_reject_brackets(self.profile, {}, 1, float('inf'), {}), 0)


if __name__ == '__main__':
    unittest.main()
