import fcntl
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from dlmm_alerts import enqueue, flush_one


class AlertTests(unittest.TestCase):
    def test_persist_without_network_and_deliver_exact_body(self):
        with tempfile.TemporaryDirectory() as root, patch('dlmm_alerts.subprocess.run') as run:
            enqueue(root, 'telegram:test', 'close\nexact body')
            run.assert_not_called()
            paths = list((Path(root)/'memories/dlmm_alert_outbox').glob('*.json'))
            self.assertEqual(len(paths), 1)
            self.assertEqual(paths[0].stat().st_mode & 0o777, 0o600)
            def deliver(args, **kwargs):
                self.assertEqual(args[:4], ['hermes', 'send', '-t', 'telegram:test'])
                self.assertEqual(Path(args[5]).read_text(), 'close\nexact body')
                self.assertEqual(kwargs['timeout'], 30)
                return subprocess.CompletedProcess(args, 0)
            run.side_effect = deliver
            flush_one(root)
            self.assertFalse(paths[0].exists())

    def test_failure_timeout_and_busy_worker_preserve_queue(self):
        with tempfile.TemporaryDirectory() as root, patch('dlmm_alerts.subprocess.run') as run:
            enqueue(root, 'telegram:test', 'close')
            directory = Path(root)/'memories/dlmm_alert_outbox'
            run.return_value = subprocess.CompletedProcess([], 1)
            flush_one(root)
            self.assertEqual(len(list(directory.glob('*.json'))), 1)
            run.side_effect = subprocess.TimeoutExpired('hermes', 30)
            flush_one(root)
            self.assertEqual(len(list(directory.glob('*.json'))), 1)
            run.reset_mock()
            with open(directory/'.lock', 'a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                flush_one(root)
                run.assert_not_called()

    def test_disabled_and_one_message_per_flush(self):
        with tempfile.TemporaryDirectory() as root, patch('dlmm_alerts.subprocess.run') as run:
            enqueue(root, '', 'disabled')
            self.assertFalse((Path(root)/'memories').exists())
            enqueue(root, 'telegram:test', 'one')
            enqueue(root, 'telegram:test', 'two')
            run.return_value = subprocess.CompletedProcess([], 0)
            flush_one(root)
            self.assertEqual(run.call_count, 1)
            remaining = list((Path(root)/'memories/dlmm_alert_outbox').glob('*.json'))
            self.assertEqual(json.loads(remaining[0].read_text())['text'], 'two')

if __name__ == '__main__':
    unittest.main()
