import contextlib
import fcntl
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dlmm_alerts  # noqa: E402
from dlmm_alerts import enqueue, flush_one, hermes_profile, hermes_send_argv  # noqa: E402

NAME = 'example-profile'  # synthetic


def profile_root(tmp):
    root = Path(tmp) / '.hermes' / 'profiles' / NAME
    root.mkdir(parents=True)
    return root


def outbox(root):
    return Path(root) / 'memories/dlmm_alert_outbox'


def put(root, text, age_s=0, now=None, **extra):
    """An outbox item queued age_s ago (the file-name prefix is the queue time)."""
    now = time.time() if now is None else now
    d = outbox(root)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f'{int((now - age_s) * 1e9):020d}-{abs(hash(text)) % 10**8:08d}.json'
    path.write_text(json.dumps({'target': 'telegram:test', 'text': text, **extra}))
    return path


class Transport(unittest.TestCase):
    def test_profile_name_rules(self):
        self.assertEqual(hermes_profile('/home/u/.hermes/profiles/' + NAME, env={}), NAME)
        self.assertEqual(hermes_profile('/home/u/.hermes/profiles/' + NAME + '/', env={}), NAME)
        self.assertIsNone(hermes_profile('/home/u/.hermes', env={}))          # default home: no flag
        self.assertIsNone(hermes_profile('/srv/anywhere', env={}))
        self.assertIsNone(hermes_profile('/home/u/.hermes/profiles/-x', env={}))
        self.assertEqual(hermes_profile('/srv/anywhere', env={'HERMES_PROFILE': 'other'}), 'other')
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(hermes_profile('/home/u/.hermes/profiles/' + NAME, env={'HERMES_PROFILE': 'bad name'}), NAME)
        self.assertIn('invalid HERMES_PROFILE', err.getvalue())
        self.assertEqual(hermes_send_argv('/home/u/.hermes/profiles/' + NAME, env={}), ['hermes', '-p', NAME, 'send'])
        self.assertEqual(hermes_send_argv('/srv/anywhere', env={}), ['hermes', 'send'])

    def test_the_symlinked_scripts_dir_is_never_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / 'repo'
            real.mkdir()
            root = profile_root(tmp)
            (root / 'link').symlink_to(real)
            self.assertEqual(hermes_profile(root, env={}), NAME)


class Outbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = profile_root(self.tmp.name)
        self.env = patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop('HERMES_PROFILE', None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def flush(self, run, now=None):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            n = flush_one(self.root, now=now, run=run)
        return n, err.getvalue()

    def test_persist_without_network_and_deliver_exact_body_with_the_profile(self):
        calls = []

        def deliver(args, **kwargs):
            calls.append(args)
            self.assertEqual(args[:6], ['hermes', '-p', NAME, 'send', '-t', 'telegram:test'])
            self.assertEqual(Path(args[7]).read_text(), 'close\nexact body')
            self.assertEqual(kwargs['timeout'], 30)
            return subprocess.CompletedProcess(args, 0)
        enqueue(self.root, 'telegram:test', 'close\nexact body')
        paths = list(outbox(self.root).glob('*.json'))
        self.assertEqual((len(paths), paths[0].stat().st_mode & 0o777), (1, 0o600))
        self.assertEqual(self.flush(deliver)[0], 1)
        self.assertFalse(paths[0].exists())
        self.assertEqual(len(calls), 1)

    def test_failure_is_logged_and_does_not_block_the_queue(self):
        now = time.time()
        first = put(self.root, 'first', age_s=60, now=now)
        put(self.root, 'second', age_s=30, now=now)
        sent = []

        def run(args, **kwargs):
            body = Path(args[args.index('-f') + 1]).read_text()
            if body == 'first':
                return subprocess.CompletedProcess(args, 1, b'', b"hermes send: Platform 'telegram' is not configured")
            sent.append(body)
            return subprocess.CompletedProcess(args, 0, b'', b'')
        n, err = self.flush(run, now)
        self.assertEqual((n, sent), (1, ['second']))
        self.assertIn('SEND FAILED', err)
        self.assertIn('exit 1', err)
        self.assertIn('not configured', err)
        item = json.loads(first.read_text())
        self.assertEqual((item['attempts'], item['last_error'], item['next_attempt_at']), (1, '1', now + 60))
        # Inside its backoff the failed item is not retried.
        calls = []
        self.assertEqual(self.flush(lambda a, **k: calls.append(a) or subprocess.CompletedProcess(a, 0), now + 30)[0], 0)
        self.assertEqual(calls, [])
        # After it, it is; the backoff doubles on each failure.
        self.flush(lambda a, **k: subprocess.CompletedProcess(a, 2, b'', b'x'), now + 61)
        item = json.loads(first.read_text())
        self.assertEqual((item['attempts'], item['next_attempt_at']), (2, now + 61 + 120))
        self.assertEqual(self.flush(lambda a, **k: subprocess.CompletedProcess(a, 0), now + 182)[0], 1)
        self.assertFalse(first.exists())

    def test_timeout_and_missing_binary_are_failures_not_crashes(self):
        now = time.time()
        p = put(self.root, 'x', now=now)

        def timeout(args, **kwargs):
            raise subprocess.TimeoutExpired('hermes', 30)
        n, err = self.flush(timeout, now)
        self.assertEqual(n, 0)
        self.assertIn('exit timeout', err)
        self.assertEqual(json.loads(p.read_text())['attempts'], 1)

        def missing(args, **kwargs):
            raise FileNotFoundError('hermes')
        n, err = self.flush(missing, now + 3600)
        self.assertIn('exit FileNotFoundError', err)
        self.assertTrue(p.exists())

    def test_stale_backlog_is_archived_unsent(self):
        now = time.time()
        stale = [put(self.root, f'old close card {i}', age_s=25 * 3600 + i, now=now) for i in range(93)]
        fresh = put(self.root, 'fresh', age_s=60, now=now)
        sent = []
        n, err = self.flush(lambda a, **k: sent.append(Path(a[a.index('-f') + 1]).read_text())
                            or subprocess.CompletedProcess(a, 0), now)
        self.assertEqual((n, sent), (1, ['fresh']))       # not one of the 93 reaches the chat
        self.assertFalse(any(p.exists() for p in stale) or fresh.exists())
        self.assertEqual(len(list((outbox(self.root) / 'archive').glob('*.json'))), 93)
        self.assertEqual(err.count('archived'), 93)
        self.assertIn('older than 24h', err)
        # The boundary: exactly 24h is still sent.
        edge = put(self.root, 'edge', age_s=24 * 3600, now=now)
        self.assertEqual(self.flush(lambda a, **k: subprocess.CompletedProcess(a, 0), now)[0], 1)
        self.assertFalse(edge.exists())

    def test_malformed_items_are_archived(self):
        d = outbox(self.root)
        d.mkdir(parents=True)
        now = time.time()
        for i, body in enumerate(['{torn', '[]', json.dumps({'target': '', 'text': 'x'}), json.dumps({'target': 't'})]):
            (d / f'{int(now * 1e9) + i:020d}-bad.json').write_text(body)
        calls = []
        n, err = self.flush(lambda a, **k: calls.append(a), now)
        self.assertEqual((n, calls), (0, []))
        self.assertEqual(len(list((d / 'archive').glob('*.json'))), 4)
        self.assertEqual(list(d.glob('*.json')), [])

    def test_one_message_per_flush_and_bounded_attempts(self):
        now = time.time()
        for i in range(5):
            put(self.root, f'm{i}', age_s=100 - i, now=now)
        calls = []
        self.assertEqual(self.flush(lambda a, **k: calls.append(a) or subprocess.CompletedProcess(a, 0), now)[0], 1)
        self.assertEqual(len(calls), 1)
        calls.clear()
        self.flush(lambda a, **k: calls.append(a) or subprocess.CompletedProcess(a, 1), now)
        self.assertEqual(len(calls), dlmm_alerts.MAX_SENDS_PER_FLUSH)  # a dead transport costs at most 3 tries a tick

    def test_disabled_target_and_busy_worker(self):
        enqueue(self.root, '', 'disabled')
        self.assertFalse(outbox(self.root).exists())
        enqueue(self.root, 'telegram:test', 'x')
        calls = []
        with open(outbox(self.root) / '.lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.flush(lambda a, **k: calls.append(a))[0], 0)
        self.assertEqual(calls, [])


class OtherSenders(unittest.TestCase):
    def test_daily_card_and_robinhood_alert_name_the_profile_and_log_failures(self):
        import dlmm_stats
        import uni_monitor
        for module, call in ((dlmm_stats, lambda: dlmm_stats.send_card('card')),
                             (uni_monitor, lambda: uni_monitor.alert('rh alert'))):
            with tempfile.TemporaryDirectory() as tmp, \
                    patch.object(module, 'PROFILE_DIR', str(profile_root(tmp))), \
                    patch.dict(os.environ, {'DLMM_ALERT_TARGET': 'telegram'}), \
                    patch.object(module.subprocess, 'run',
                                 return_value=subprocess.CompletedProcess([], 1, b'', b'not configured')) as run, \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                os.environ.pop('HERMES_PROFILE', None)
                call()
            self.assertEqual(run.call_args.args[0][:4], ['hermes', '-p', NAME, 'send'], module.__name__)
            self.assertIn('SEND FAILED', err.getvalue(), module.__name__)


if __name__ == '__main__':
    unittest.main()
