import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import dlmm_retention as retention

NOW = 2_000_000_000
DAY = 86400


def line(**row):
    return (json.dumps(row) + '\n').encode()


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.memory = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        patcher = mock.patch.object(retention.time, 'sleep', lambda s: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, data):
        path = self.memory / name
        path.write_bytes(data)
        os.chmod(path, 0o600)
        return path

    def test_dry_run_is_default_and_writes_nothing(self):
        data = line(ts=NOW - 20 * DAY) + line(ts=NOW)
        path = self.write('dlmm_bin_samples.jsonl', data)
        result, = retention.run(self.memory, 14, ['dlmm_bin_samples.jsonl'], apply=False, now=NOW)
        self.assertEqual((result['status'], result['archived_rows']), ('planned', 1))
        self.assertEqual(path.read_bytes(), data)
        self.assertFalse((self.memory / 'archive').exists())

    def test_byte_exact_prefix_split_and_archive_aware_readers(self):
        old = [line(collected_at=NOW - d * DAY, pool='p%d' % d) for d in (30, 20, 15)]
        late_old = line(collected_at=NOW - 40 * DAY, pool='late')   # after a new row: stays live
        new = [line(collected_at=NOW - DAY, pool='n'), late_old, line(collected_at=NOW, pool='m')]
        data = b''.join(old + new)
        path = self.write('dlmm_candidate_bin_samples.jsonl', data)
        result, = retention.run(self.memory, 14, ['dlmm_candidate_bin_samples.jsonl'], apply=True, now=NOW)
        self.assertEqual((result['status'], result['archived_rows']), ('archived', 3))
        self.assertEqual(path.read_bytes(), b''.join(new))
        self.assertEqual(retention.archived_bytes(path), data)
        self.assertEqual([r['pool'] for r in retention.archived_rows(path)],
                         ['p30', 'p20', 'p15', 'n', 'late', 'm'])
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
        # A second run later appends another archive and still reproduces the bytes.
        result, = retention.run(self.memory, 14, ['dlmm_candidate_bin_samples.jsonl'], apply=True,
                                now=NOW + 13.5 * DAY)
        self.assertEqual(result['archived_rows'], 2)  # n and late; m is newer than the cutoff
        self.assertEqual(len(retention.archives(path)), 2)
        self.assertEqual(retention.archived_bytes(path), data)

    def test_prefix_stops_at_unstamped_corrupt_or_partial_line(self):
        for stopper in (line(other=1), b'{bad\n', line(ts=True)):
            with self.subTest(stopper=stopper):
                data = line(ts=NOW - 30 * DAY) + stopper + line(ts=NOW - 29 * DAY)
                path = self.write('dlmm_bin_samples.jsonl', data)
                self.assertEqual(retention.prefix_end(path, ('ts',), NOW - 14 * DAY)[1], 1)
        path = self.write('dlmm_bin_samples.jsonl', b'{"ts": 1}')  # unterminated
        self.assertEqual(retention.prefix_end(path, ('ts',), NOW), (0, 0))

    def test_nav_and_unknown_files_refused_and_floor_enforced(self):
        self.write('dlmm_nav.jsonl', line(ts=NOW - 90 * DAY))
        results = retention.run(self.memory, 14, ['dlmm_nav.jsonl', 'other.jsonl'], apply=True, now=NOW)
        self.assertEqual([r['status'] for r in results], ['refused_not_in_policy'] * 2)
        self.assertFalse((self.memory / 'archive').exists())
        result, = retention.run(self.memory, 1, ['dlmm_bin_samples.jsonl'], apply=True, now=NOW)
        self.assertEqual(result['status'], 'refused_below_floor')
        self.assertNotIn('dlmm_nav.jsonl', retention.POLICY)

    def test_append_racing_the_swap_is_kept(self):
        data = line(recorded_at=NOW - 30 * DAY) + line(recorded_at=NOW)
        path = self.write('dlmm_candidate_fee_forecasts.jsonl', data)
        raced = line(recorded_at=NOW + 1)
        stale_writer = open(path, 'ab')  # opened before the swap: writes hit the OLD inode
        self.addCleanup(stale_writer.close)
        calls = []

        def sleep(_):
            if not calls:
                stale_writer.write(raced)
                stale_writer.flush()
            calls.append(1)
        with mock.patch.object(retention.time, 'sleep', sleep):
            retention.run(self.memory, 14, ['dlmm_candidate_fee_forecasts.jsonl'], apply=True, now=NOW)
        self.assertEqual(path.read_bytes(), line(recorded_at=NOW) + raced)
        self.assertEqual(retention.archived_bytes(path), data + raced)

    def test_concurrent_run_is_locked_out(self):
        import fcntl
        with open(self.memory / '.retention.lock', 'w') as held:
            fcntl.flock(held, fcntl.LOCK_EX)
            self.assertEqual(retention.run(self.memory, 14, ['dlmm_bin_samples.jsonl'], True, NOW),
                             [dict(status='locked')])

    def test_missing_file(self):
        result, = retention.run(self.memory, 14, ['dlmm_bin_samples.jsonl'], apply=True, now=NOW)
        self.assertEqual(result['status'], 'missing')
        self.assertEqual(list(retention.archived_rows(self.memory / 'dlmm_bin_samples.jsonl')), [])


class ReaderWiringTests(unittest.TestCase):
    def test_full_history_research_readers_include_archives(self):
        here = Path(__file__).parent
        for name in ('dlmm_fee_forecast.py', 'dlmm_candidate_replay.py', 'dlmm_entry_forecast_evaluation.py'):
            self.assertIn('from dlmm_retention import archived_', (here / name).read_text(), name)


if __name__ == '__main__':
    unittest.main()
