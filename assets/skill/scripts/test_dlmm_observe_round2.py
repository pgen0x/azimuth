"""Offline regression of observe-bundle2 counterexamples. Synthetic profiles only."""
import ast
import contextlib
import io
import json
import os
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_candidate_watch as watch
import dlmm_monitor as monitor
import dlmm_observer_gate as gate
import dlmm_research_io as research
import dlmm_shadow as shadow
from test_dlmm_observe_bounds import POOL, MINT, POSITION, sample, shadow_rows


class Round2Tests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.profile = Path(tmp.name)
        self.memory = self.profile / 'memories'
        self.memory.mkdir()
        for p in (patch.dict(os.environ, dict(DLMM_SHADOW_EXITS='1', DLMM_REJECT_IDENTITY='1',
                                             DLMM_BRACKET_REJECTS='1', DRY_RUN='false')),
                  patch.object(monitor, 'PROFILE_DIR', str(self.profile)),
                  contextlib.redirect_stdout(io.StringIO())):
            p.__enter__(); self.addCleanup(p.__exit__, None, None, None)

    def observe(self, position=POSITION):
        return monitor.shadow_exit_observe(position, 'pulse', -1, -.001, 1, False, {'bot_holders_pct': 25})

    def test_no_scan_and_no_age_eviction(self):
        directory = self.memory / 'dlmm_shadow_exits.d'
        directory.mkdir()
        for i in range(1000):
            (directory / f'{i:032x}').touch()
        with patch.object(os, 'scandir', side_effect=AssertionError('no prune')) as scan:
            self.observe()
            self.assertEqual(scan.call_count, 0)
        self.assertEqual(len(shadow_rows(self.profile)), 2)
        old = time.time() - 31 * 86400
        for item in directory.iterdir():
            os.utime(item, (old, old))
        self.observe('another-position')
        self.observe()
        self.assertEqual(sum(r['position'] == POSITION for r in shadow_rows(self.profile)), 2)

    def test_symlink_directory_and_replacement_race_leave_foreign_files_untouched(self):
        for race in (False, True):
            with self.subTest(race=race), tempfile.TemporaryDirectory() as tmp:
                outside = Path(tmp)
                sentinel = outside / 'keep.txt'; sentinel.write_text('keep')
                os.utime(sentinel, (1, 1))
                directory = self.memory / 'dlmm_shadow_exits.d'
                if race:
                    directory.mkdir()
                else:
                    directory.symlink_to(outside)
                real_open = os.open
                def replaced(path, flags, *args, **kwargs):
                    if str(path) == str(directory) and flags & os.O_DIRECTORY:
                        directory.rmdir(); directory.symlink_to(outside)
                    return real_open(path, flags, *args, **kwargs)
                with patch.object(os, 'open', side_effect=replaced if race else real_open):
                    self.observe()
                self.assertEqual(sentinel.read_text(), 'keep')
                self.assertEqual(list(outside.iterdir()), [sentinel])
                self.assertEqual(shadow_rows(self.profile), [])
                directory.unlink()

    def test_oversized_line_checks_deadline_on_each_read(self):
        file = self.memory / 'bad.jsonl'
        file.write_bytes(b'x' * (2 * 1024 * 1024) + b'\n')
        clock = [0]; original = os.fdopen
        class Clocked:
            def __init__(self, stream): self.stream = stream
            def __getattr__(self, name): return getattr(self.stream, name)
            def __enter__(self): return self
            def __exit__(self, *args): self.stream.close()
            def readline(self, *args):
                clock[0] += 1
                return self.stream.readline(*args)
        report = {}
        with patch.object(os, 'fdopen', side_effect=lambda *a, **k: Clocked(original(*a, **k))), \
                patch.object(shadow.time, 'monotonic', side_effect=lambda: clock[0]):
            self.assertEqual(list(shadow.research_rows(file, 10, report, 'test')), [])
        self.assertEqual(clock[0], 10)
        self.assertTrue(report['reject_brackets_deadline'])
        self.assertEqual(report['reject_brackets_invalid_rows'], 1)

    def writers(self):
        return [('monitor', monitor.SHADOW_EXITS_FILE, lambda: self.observe()),
                ('reject', watch.REJECT_FILENAME,
                 lambda: watch.record_pipeline_reject(self.profile, 'pulse', 'pvp', POOL, MINT, False, 'TEST')),
                ('bracket', shadow.BRACKET_FILENAME,
                 lambda: shadow.append_research(self.memory / shadow.BRACKET_FILENAME, {'example': True}))]

    def test_all_writers_refuse_projected_cap_without_claiming_markers(self):
        cap = 64 * 1024 * 1024
        for name, filename, writer in self.writers():
            with self.subTest(writer=name):
                file = self.memory / filename
                with file.open('wb') as stream:
                    stream.seek(cap - 2); stream.write(b'\n')
                result = writer()
                self.assertFalse(result)
                self.assertEqual(file.stat().st_size, cap - 1)
        directory = self.memory / 'dlmm_shadow_exits.d'
        self.assertEqual(list(directory.iterdir()), [])

    def test_size_is_checked_after_lock_and_exact_cap_is_valid(self):
        file = self.memory / 'race.jsonl'
        file.write_bytes(b'{}\n')
        original = research.fcntl.flock
        def lock_then_competitor(fd, flags):
            self.assertTrue(flags & research.fcntl.LOCK_NB)
            # A cooperating writer completed while this caller was acquiring its lock.
            with file.open('ab') as stream: stream.write(b'{}\n')
            return original(fd, flags)
        with patch.object(research.fcntl, 'flock', side_effect=lock_then_competitor):
            with self.assertRaises(OSError):
                with research.research_writer(file, 3, 8) as fd:
                    research.research_write(fd, b'{}\n')
        self.assertEqual(file.read_bytes(), b'{}\n{}\n')
        with research.research_writer(file, 3, 9) as fd:
            research.research_write(fd, b'{}\n')
        self.assertEqual(file.stat().st_size, 9)

    def test_short_write_preserves_prefix_reports_failure_and_refuses_partial_tail(self):
        original = os.write
        for name, filename, writer in self.writers():
            with self.subTest(writer=name):
                file = self.memory / filename
                file.write_bytes(b'{"keep":true}\n')
                with patch.object(os, 'write', side_effect=lambda fd, data: original(fd, data[:5])):
                    self.assertFalse(writer())
                partial = file.read_bytes()
                self.assertTrue(partial.startswith(b'{"keep":true}\n'))
                self.assertFalse(partial.endswith(b'\n'))
                writer()
                if name == 'monitor': self.observe('next-position')
                self.assertEqual(file.read_bytes(), partial)
                report = {}
                self.assertEqual(list(shadow.research_rows(file, float('inf'), report, 'test')), [{'keep': True}])
                self.assertEqual(report['reject_brackets_invalid_rows'], 1)

    def test_bracket_append_refuses_oversized_row_and_contended_lock(self):
        file = self.memory / shadow.BRACKET_FILENAME
        self.assertFalse(shadow.append_research(file, {'oversized': 'x' * 65536}))
        self.assertFalse(file.exists())
        file.touch()
        with file.open('a') as held:
            research.fcntl.flock(held, research.fcntl.LOCK_EX | research.fcntl.LOCK_NB)
            self.assertFalse(shadow.append_research(file, {'ok': True}))
        self.assertEqual(file.stat().st_size, 0)

    def bracket_fixture(self, snapshot):
        shadow.append(self.memory / shadow.BRACKET_FILENAME, dict(
            bracket_id='reject:synthetic', bracket_gate='pvp', bracket_phase='baseline',
            pool=POOL, base_mint=MINT, status='observed', ts=10000, anchor_bin=0))
        if snapshot is not None:
            shadow.append(self.memory / 'dlmm_candidate_bin_samples.jsonl', dict(snapshot, collected_at=13899))

    def collect(self):
        with patch.object(shadow.time, 'time', return_value=13900), \
                patch.object(shadow.time, 'monotonic', return_value=0), \
                patch.object(shadow.subprocess, 'check_output', return_value=json.dumps(sample(stamp=13900)).encode()) as rpc:
            result = shadow.collect_candidate_bins(self.profile, {}, 40)
        return result, rpc.call_count

    def test_invalid_history_cannot_complete_or_throttle_terminal(self):
        for kind in ('valid', 'missing_bins', 'wrong_mint', 'wrong_counter', 'wrong_bin'):
            with self.subTest(kind=kind):
                for file in self.memory.iterdir(): file.unlink()
                history = sample(stamp=13601)
                if kind == 'missing_bins': history['bins'] = []
                if kind == 'wrong_mint': history['token_x_mint'] = 'D' * 32
                if kind == 'wrong_counter': history['bins'][0]['x'] = '-1'
                if kind == 'wrong_bin': history['bins'][0]['id'] = 5
                self.bracket_fixture(history)
                result, reads = self.collect()
                self.assertEqual(reads, 0 if kind == 'valid' else 1)
                terminal = [r for r in shadow.iter_rows(self.memory / shadow.BRACKET_FILENAME)
                            if r.get('bracket_phase') == 'terminal']
                self.assertEqual(len(terminal), 1)
                if kind != 'valid':
                    self.assertGreater(result['reject_brackets_invalid_rows'], 0)
                    self.assertNotIn('reused_sample_collected_at', terminal[0])

    def test_failed_append_reported_for_reused_and_new_terminal(self):
        for reused in (True, False):
            with self.subTest(reused=reused):
                for file in self.memory.iterdir(): file.unlink()
                self.bracket_fixture(sample(stamp=13601) if reused else None)
                with patch.object(shadow, 'append_research', return_value=False):
                    result, reads = self.collect()
                self.assertEqual(reads, 0 if reused else 1)
                self.assertEqual(result['reject_brackets_errors'], ['append:refused'])

    def test_all_closes_precede_observer_failures_and_keep_original_times(self):
        source = Path(monitor.__file__).read_text()
        # Execute production risk/close slices; the structural companion test
        # verifies that the sole flush is after the whole production for-loop.
        risk = textwrap.dedent(source[source.index('        peak_pnl = float(meta.get('):
                                      source.index('        # 3. Pumped Far Above Range Check')])
        close = textwrap.dedent(source[source.index('        # Execute close if triggered'):
                                       source.index('            if close_res and close_res.get("success"):',
                                                    source.index('        # Execute close if triggered'))])
        traces = []
        for enabled in ('0', '1'):
            pending, events = [], []
            for i in range(2):
                scope = dict(vars(monitor), pending_observers=pending,
                             meta=dict(mode='pulse', peak_pnl=1, deployed_at=0, signal={'bot_holders_pct': 25}),
                             pos_addr='position' + str(i), pool=POOL, pair='TEST', pnl_pct=-9, pnl_sol_actual=-.009,
                             fee_per_tvl_24h=20, in_range=True, stop_loss_pct=-3, now=1000,
                             turnover_trailing_trigger_pct=1.2, turnover_trailing_drop_pct=.6,
                             trailing_trigger_pct=3, trailing_drop_pct=1.5, is_dry_run_stored=False,
                             wallet_address='synthetic-wallet', native_mark={'synthetic': i},
                             run_command=lambda *a: None, print=lambda *a: None)
                scope['close_position'] = lambda pos, *a, **k: (events.append(('close', pos, k)) or ({'success': False}, None))
                with patch.dict(os.environ, DLMM_SHADOW_EXITS=enabled), patch.object(monitor.time, 'time', return_value=1000):
                    exec(risk, scope); exec(close, scope)
            self.assertEqual([kind for kind, *_ in events], ['close', 'close'])
            observations = []
            def observe(*args):
                observations.append((len(events), args[-1]))
                raise OSError('synthetic observer failure')
            with patch.object(monitor, 'shadow_exit_observe', side_effect=observe), \
                    patch.object(monitor, 'record_close_bin_observation', side_effect=observe):
                monitor.flush_tick_observers(pending)
            self.assertEqual(observations, [(2, 1000)] * (4 if enabled == '1' else 2))
            self.assertTrue(all(row[2]['emergency_exit'] for row in events))
            traces.append(events)
        self.assertEqual(traces[0], traces[1])


def journal_line(flag=True, **changes):
    row = dict(component='monitor', pid=123, regular_tick=True, started_at=101, completed_at=102,
               flags={'DLMM_SHADOW_EXITS': flag})
    row.update(changes)
    return json.dumps(dict(MESSAGE='OBSERVER_TICK ' + json.dumps(row),
                           _PID='99', __REALTIME_TIMESTAMP='102000000'))


class DeploymentGateTests(unittest.TestCase):
    def test_pipeline_checks_fresh_descendant_python_environment_not_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp); (proc / 'stat').write_text('btime 100\n')
            for pid, parent in ((10, 1), (11, 10), (12, 11)):
                directory = proc / str(pid); directory.mkdir()
                fields = ['S', str(parent)] + ['0'] * 17 + [str(os.sysconf('SC_CLK_TCK'))]
                (directory / 'stat').write_text(str(pid) + ' (python3) ' + ' '.join(fields))
                (directory / 'cmdline').write_bytes(b'/usr/bin/python3\0/synthetic/dlmm_pipeline.py\0')
                (directory / 'environ').write_bytes(b'DLMM_REJECT_IDENTITY=1\0SECRET=never-return-this\0')
            # Intermediate shell has initial flag=1; actual child after sourcing has flag=0.
            (proc / '11/cmdline').write_bytes(b'bash\0-c\0python3 /synthetic/dlmm_pipeline.py\0')
            (proc / '12/environ').write_bytes(b'DLMM_REJECT_IDENTITY=0\0SECRET=never-return-this\0')
            with self.assertRaisesRegex(RuntimeError, 'mismatch'):
                gate.pipeline_child(proc, 10, True, 100.5, 102)
            proof = gate.pipeline_child(proc, 10, False, 100.5, 102)
            self.assertEqual(proof['pid'], 12)
            self.assertFalse(proof['flags']['DLMM_REJECT_IDENTITY'])
            self.assertNotIn('SECRET', json.dumps(proof))
            self.assertIsNone(gate.pipeline_child(proc, 99, False, 100.5, 102))
            self.assertIsNone(gate.pipeline_child(proc, 10, False, 101.5, 102))

    def test_only_fresh_regular_completed_child_with_expected_flag_passes(self):
        self.assertIsNotNone(gate.match_tick(journal_line(), 'monitor', True, 100, 103))
        for changes in ({'started_at': 99}, {'completed_at': 99}, {'completed_at': float('nan')},
                        {'regular_tick': False}, {'component': 'pipeline'}, {'pid': 0}):
            with self.subTest(changes=changes):
                self.assertIsNone(gate.match_tick(journal_line(**changes), 'monitor', True, 100, 103))
        self.assertIsNone(gate.match_tick('{}', 'monitor', True, 100, 103))
        with self.assertRaisesRegex(RuntimeError, 'mismatch'):
            gate.match_tick(journal_line(False), 'monitor', True, 100, 103)
        self.assertIsNotNone(gate.match_tick(journal_line(False), 'monitor', False, 100, 103))

    def test_empty_journal_deadline_and_journal_failure_stop_gate(self):
        from types import SimpleNamespace
        with patch.object(gate.time, 'monotonic', side_effect=[0, 0, 0, 1, 2]), \
                patch.object(gate.time, 'sleep'), \
                patch.object(gate.subprocess, 'run', return_value=SimpleNamespace(stdout='')) as run:
            with self.assertRaisesRegex(RuntimeError, 'no fresh'):
                gate.wait_for_tick('synthetic-unit', 'monitor', True, 100, 1)
            self.assertEqual(run.call_count, 1)
        with patch.object(gate.subprocess, 'run', side_effect=OSError('synthetic error')):
            with self.assertRaises(OSError):
                gate.wait_for_tick('synthetic-unit', 'monitor', True, 100, 1)

    def test_completed_status_uses_child_environment_and_normal_exit_zero_only(self):
        for exit_code in (None, 0, 1):
            out = io.StringIO()
            def main():
                os.environ['DLMM_SHADOW_EXITS'] = '0'  # analogous to child after .env override
                if exit_code is not None: raise SystemExit(exit_code)
            with patch.dict(os.environ, DLMM_SHADOW_EXITS='1'), contextlib.redirect_stderr(out):
                if exit_code is None:
                    research.run_observed_main('monitor', main)
                else:
                    with self.assertRaises(SystemExit) as caught: research.run_observed_main('monitor', main)
                    self.assertEqual(caught.exception.code, exit_code)
            if exit_code == 1:
                self.assertEqual(out.getvalue(), '')
            else:
                row = json.loads(out.getvalue().removeprefix('OBSERVER_TICK '))
                self.assertFalse(row['flags']['DLMM_SHADOW_EXITS'])
                self.assertEqual(row['pid'], os.getpid())


if __name__ == '__main__':
    unittest.main()
