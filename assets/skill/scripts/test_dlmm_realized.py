#!/usr/bin/env python3
"""dlmm_realized.py --if-pending: the monitor loop's 15-minute poll must not fetch when
every recent close is already reconciled. Offline: backfill is replaced, no network."""
import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlmm_realized as r  # noqa: E402


class IfPendingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.closes = os.path.join(self.tmp.name, "dlmm_closes.jsonl")
        self.realized = os.path.join(self.tmp.name, "dlmm_realized.jsonl")
        self.patches = [mock.patch.object(r, "CLOSES_PATH", self.closes),
                        mock.patch.object(r, "REALIZED_PATH", self.realized),
                        mock.patch.object(r, "get_wallet_address", return_value="W" * 44)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def write(self, path, rows):
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(x) + "\n" for x in rows)

    def run_main(self, *argv):
        with mock.patch.object(r, "backfill") as backfill, mock.patch.object(sys, "argv", ["dlmm_realized.py", *argv]), \
                redirect_stdout(io.StringIO()):
            code = r.main()
        return code, backfill.called

    def test_pending_selects_unreconciled_live_exits_in_window(self):
        now = time.time()
        self.write(self.closes, [
            dict(event="exit", position="done", ts=now - 600),
            dict(event="exit", position="new", ts=now - 300),
            dict(event="exit", position="dry", ts=now - 300, dry_run=True),
            dict(event="compound", position="cmp", ts=now - 300),
            dict(event="exit", position="old", ts=now - 5 * 86400),
            dict(event="exit", ts=now - 300),
        ])
        self.write(self.realized, [dict(position="done", realized_sol=0.001, fetched_at=int(now))])
        self.assertEqual([x["position"] for x in r.pending_closes(2)], ["new"])

    def test_if_pending_skips_fetch_when_all_reconciled(self):
        now = time.time()
        self.write(self.closes, [dict(event="exit", position="done", ts=now - 600)])
        self.write(self.realized, [dict(position="done", realized_sol=0.001, fetched_at=int(now))])
        self.assertEqual(self.run_main("--days", "2", "--if-pending", "--quiet"), (0, False))
        # No journal at all is also nothing to do.
        os.remove(self.closes)
        self.assertEqual(self.run_main("--days", "2", "--if-pending", "--quiet"), (0, False))

    def test_if_pending_fetches_when_a_close_is_unreconciled(self):
        self.write(self.closes, [dict(event="exit", position="new", ts=time.time() - 300)])
        self.assertEqual(self.run_main("--days", "2", "--if-pending", "--quiet"), (0, True))

    def test_without_flag_always_fetches(self):
        self.assertEqual(self.run_main("--days", "7", "--quiet"), (0, True))


if __name__ == "__main__":
    unittest.main()
