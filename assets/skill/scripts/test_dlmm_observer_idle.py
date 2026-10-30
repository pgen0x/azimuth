"""Cgroup/proc fixtures only; no real unit or process control."""
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import dlmm_observer_idle as idle


class IdleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name); self.proc = self.root / 'proc'; self.proc.mkdir()
        self.cg = self.root / 'cgroup'; self.unit = self.cg / 'unit'; self.unit.mkdir(parents=True)
        (self.unit / 'cgroup.procs').write_text('10\n')
        self.command(10, b'azimuth\0')
        self.clock = 0

    def command(self, pid, value):
        directory = self.proc / str(pid); directory.mkdir(exist_ok=True)
        (directory / 'cmdline').write_bytes(value)

    def sleep(self, seconds):
        self.clock += seconds

    def wait(self, timeout=3, output='/unit', sleep=None):
        with patch.object(idle.subprocess, 'run', return_value=SimpleNamespace(stdout=output)), \
                patch.object(idle.time, 'monotonic', side_effect=lambda: self.clock), \
                patch.object(idle.time, 'sleep', side_effect=sleep or self.sleep):
            return idle.wait_idle('azimuth', timeout, proc=self.proc, cgroups=self.cg)

    def test_nested_trade_processes_block_but_unrelated_cgroups_do_not(self):
        nested = self.unit / 'worker'; nested.mkdir(); (nested / 'cgroup.procs').write_text('11\n12\n')
        self.command(11, b'python3\0/profile/dlmm_pipeline.py\0SECRET_BATCH_DATA\0')
        self.command(12, b'node\0/profile/dlmm_executor.js\0deploy\0')
        other = self.cg / 'other'; other.mkdir(); (other / 'cgroup.procs').write_text('13\n')
        self.command(13, b'node\0/dlmm_executor.js\0')
        busy, count = idle.busy_pids(self.unit, self.proc, float('inf'))
        self.assertEqual((busy, count), ([11, 12], 3))
        with self.assertRaisesRegex(RuntimeError, 'did not become idle'):
            self.wait()
        (nested / 'cgroup.procs').write_text('')
        proof = self.wait()
        self.assertEqual(proof['status'], 'idle')
        self.assertNotIn('SECRET_BATCH_DATA', json.dumps(proof))

    def test_waits_for_completion_and_a_full_quiet_interval(self):
        (self.unit / 'cgroup.procs').write_text('10\n11\n')
        self.command(11, b'python3\0/dlmm_pipeline.py\0')
        def finish(seconds):
            self.sleep(seconds)
            if self.clock >= .6: self.command(11, b'finished\0')
        proof = self.wait(sleep=finish)
        self.assertGreaterEqual(self.clock, 1.6)
        self.assertGreaterEqual(proof['quiet_seconds'], 1)

    def test_new_work_restarts_the_quiet_interval(self):
        (self.unit / 'cgroup.procs').write_text('10\n11\n')
        self.command(11, b'finished\0')
        def intermittent(seconds):
            self.sleep(seconds)
            self.command(11, b'node\0/dlmm_executor.js\0' if .6 <= self.clock < 1 else b'finished\0')
        proof = self.wait(timeout=4, sleep=intermittent)
        self.assertGreaterEqual(self.clock, 2)
        self.assertGreaterEqual(proof['quiet_seconds'], 1)

    def test_missing_invalid_symlink_or_unreadable_sources_never_prove_idle(self):
        for group in ('', '/', '/missing', '/../unit'):
            with self.subTest(group=group), self.assertRaises((OSError, RuntimeError)):
                self.wait(output=group)
        (self.cg / 'link').symlink_to(self.unit)
        with self.assertRaises(RuntimeError): self.wait(output='/link')
        (self.proc / '10/cmdline').unlink()
        with self.assertRaisesRegex(RuntimeError, 'unavailable'): self.wait()
        self.command(10, b'azimuth\0')
        with patch.object(idle, 'read_bounded', side_effect=PermissionError('synthetic unreadable')):
            with self.assertRaises(PermissionError): self.wait()
        (self.unit / 'cgroup.procs').write_text('invalid\n')
        with self.assertRaisesRegex(RuntimeError, 'invalid cgroup'): self.wait()

    def test_exited_process_is_rechecked_without_killing_anything(self):
        (self.unit / 'cgroup.procs').write_text('10\n99\n')  # 99 has already exited
        proof = self.wait()
        self.assertEqual(proof['status'], 'idle')
        self.assertGreaterEqual(proof['quiet_seconds'], 1)

    def test_bounded_large_arguments_and_pid_lists(self):
        self.command(10, b'python3\0/dlmm_pipeline.py\0' + b'x' * 100000)
        self.assertEqual(idle.busy_pids(self.unit, self.proc, float('inf'))[0], [10])
        self.command(10, b'x' * 100000)
        with self.assertRaisesRegex(RuntimeError, 'oversized'): self.wait()
        (self.unit / 'cgroup.procs').write_bytes(b'10\n' * 30000)
        with self.assertRaisesRegex(RuntimeError, 'read cap'): self.wait()

    def test_systemctl_failure_cannot_pass(self):
        with patch.object(idle.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'fixture')):
            with self.assertRaises(subprocess.CalledProcessError):
                idle.wait_idle('azimuth', 1, self.proc, self.cg)


if __name__ == '__main__':
    unittest.main()
