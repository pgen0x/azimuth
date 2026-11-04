import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dlmm_signal_record import SignalRecordError, load_delivered_record, parse_signal_record

RECORD = {"mode": "pulse", "pool": "P" * 43, "name": "X-SOL", "base_mint": "M" * 43,
          "base_symbol": "X", "tvl": 10000, "volatility": 1.0, "score": 60}
TEXT = json.dumps(RECORD)


class ParseSignalRecordTests(unittest.TestCase):
    def test_plain_record(self):
        self.assertEqual(parse_signal_record(TEXT), RECORD)
        self.assertEqual(parse_signal_record("  " + TEXT + "\n"), RECORD)

    def test_element_copied_with_array_closer(self):
        # Observed as "Extra data": the payload's "]" came along.
        self.assertEqual(parse_signal_record(TEXT + "]"), RECORD)
        self.assertEqual(parse_signal_record(TEXT + " ]\n"), RECORD)
        self.assertEqual(parse_signal_record(TEXT + ","), RECORD)

    def test_python_repr_refused(self):
        # The agent rewrote the record as a Python dict; values may have changed.
        with self.assertRaises(SignalRecordError):
            parse_signal_record(TEXT.replace("60}", "60, \"x\": True}"))

    def test_single_element_array(self):
        self.assertEqual(parse_signal_record("[" + TEXT + "]"), RECORD)

    def test_ambiguous_inputs_still_refused(self):
        other = json.dumps(dict(RECORD, pool="Q" * 43))
        for bad in ("[" + TEXT + "," + other + "]",  # two records
                    TEXT + other,                     # two concatenated objects
                    TEXT + ", " + other + "]",        # tail of a longer array
                    TEXT + " --mode pulse",           # trailing text
                    "[" + TEXT + "]]",                # array plus a stray closer
                    "[]", "[1]", '"x"', "",
                    TEXT[:-1]):                       # truncated
            with self.subTest(bad=bad[-40:]):
                with self.assertRaises(SignalRecordError):
                    parse_signal_record(bad)

    def test_messages_keep_pipeline_wording(self):
        with self.assertRaisesRegex(SignalRecordError, "got an array; pass ONE payload element"):
            parse_signal_record("[" + TEXT + "," + TEXT + "]")
        with self.assertRaisesRegex(SignalRecordError, "not valid JSON: Extra data"):
            parse_signal_record(TEXT + "x")

    def test_non_string(self):
        with self.assertRaises(SignalRecordError):
            parse_signal_record(None)


POOL = "5EqdM7FBGypHBZAm8duPxioAeJ2BTG1SvDrrPKc3fyj3"
OTHER = "HgEJs5LSjd3da5LTsTJXa3nXjT1oucdLemeUq6V1gbsS"


def prepared(ts, records, as_json=False):
    signal = {"type": "alert", "timestamp": ts, "source": "meteora_pool_discovery"}
    if as_json:
        signal["payload_json"] = json.dumps(records)
    else:
        signal["payload"] = records
    return {"delivery_id": "d%d" % ts, "observed_at": ts, "signal": signal, "stage": "prepared"}


class DeliveredRecordTests(unittest.TestCase):
    def journal(self, rows, prefix=b""):
        f = tempfile.NamedTemporaryFile("wb", suffix=".jsonl", delete=False)
        self.addCleanup(Path(f.name).unlink)
        f.write(prefix)
        for row in rows:
            f.write(json.dumps(row).encode() + b"\n")
        f.close()
        return f.name

    def rec(self, pool=POOL, mode="pulse", **kw):
        return dict(RECORD, pool=pool, mode=mode, **kw)

    def test_newest_matching_record_wins(self):
        path = self.journal([
            prepared(1000, [self.rec(tvl=1)]),
            {"delivery_id": "d1000", "observed_at": 1001, "stage": "accepted", "http_status": 202},
            prepared(1100, [self.rec(OTHER), self.rec(tvl=2)]),
            prepared(1200, [self.rec(OTHER)]),
        ])
        self.assertEqual(load_delivered_record(POOL, "pulse", path, now=1300)["tvl"], 2)

    def test_rows_after_now_ignored(self):
        path = self.journal([prepared(1000, [self.rec(tvl=1)]), prepared(1100, [self.rec(tvl=2)])])
        self.assertEqual(load_delivered_record(POOL, "pulse", path, now=1050)["tvl"], 1)

    def test_record_returned_verbatim(self):
        r = self.rec(name="Bob's-SOL", is_pvp=True, gmgn_smart_wallets=None)
        path = self.journal([prepared(1000, [r])])
        self.assertEqual(load_delivered_record(POOL, "pulse", path, now=1000), r)

    def test_mode_must_match(self):
        path = self.journal([prepared(1000, [self.rec(mode="turnover")])])
        with self.assertRaisesRegex(SignalRecordError, "no pulse signal"):
            load_delivered_record(POOL, "pulse", path, now=1000)
        self.assertEqual(load_delivered_record(POOL, "turnover", path, now=1000)["mode"], "turnover")

    def test_stale_record_refused(self):
        path = self.journal([prepared(1000, [self.rec()])])
        self.assertTrue(load_delivered_record(POOL, "pulse", path, now=1000 + 1800))
        with self.assertRaisesRegex(SignalRecordError, "last 30 minutes"):
            load_delivered_record(POOL, "pulse", path, now=1000 + 1801)

    def test_payload_json_fallback(self):
        path = self.journal([prepared(1000, [self.rec()], as_json=True)])
        self.assertEqual(load_delivered_record(POOL, "pulse", path, now=1000)["pool"], POOL)

    def test_partial_first_line_of_tail_ignored(self):
        old = json.dumps(prepared(900, [self.rec(tvl=9)])).encode()
        path = self.journal([prepared(1000, [self.rec(tvl=1)])], prefix=old + b"\n")
        rec = load_delivered_record(POOL, "pulse", path, now=1000, tail_bytes=len(json.dumps(prepared(1000, [self.rec(tvl=1)]))) + 10)
        self.assertEqual(rec["tvl"], 1)

    def test_bad_inputs(self):
        path = self.journal([prepared(1000, [self.rec()])])
        for bad in ("", "{\"pool\": 1}", POOL + " --mode pulse", "0" * 44):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(SignalRecordError, "not a Solana pool address"):
                    load_delivered_record(bad, "pulse", path, now=1000)
        with self.assertRaisesRegex(SignalRecordError, "unreadable"):
            load_delivered_record(POOL, "pulse", path + ".missing", now=1000)

    def test_env_override(self):
        from dlmm_signal_record import delivery_journal_path
        self.assertEqual(str(delivery_journal_path({"SOLANA_DELIVERY_PATH": "/x/y.jsonl"})), "/x/y.jsonl")
        self.assertTrue(str(delivery_journal_path({})).endswith(".local/state/azimuth/solana_deliveries.jsonl"))


class EntryAuditTests(unittest.TestCase):
    def audit(self, stdout=None, exc=None):
        import dlmm_pipeline
        def runner(*a, **kw):
            if exc:
                raise exc
            return SimpleNamespace(stdout=stdout, returncode=0)
        return dlmm_pipeline.run_entry_audit("M" * 43, runner=runner, script=Path("audit_token.py"))

    def test_verdicts(self):
        self.assertEqual(self.audit(json.dumps({"verdict": "FAIL", "reason": "Dev holds 40.0%"})),
                         ("FAIL", "Dev holds 40.0%"))
        self.assertEqual(self.audit(json.dumps({"verdict": "PASS", "risk_level": 1}))[0], "PASS")
        self.assertEqual(self.audit(json.dumps({"verdict": "UNKNOWN", "reason": "API Error"})),
                         ("UNKNOWN", "API Error"))

    def test_unavailable_is_unknown_never_pass(self):
        for kw in ({"stdout": ""}, {"stdout": "Traceback"}, {"stdout": "[1]"},
                   {"exc": subprocess.TimeoutExpired("x", 45)}, {"exc": OSError("boom")}):
            with self.subTest(**{k: str(v) for k, v in kw.items()}):
                self.assertEqual(self.audit(**kw)[0], "UNKNOWN")

    def test_audit_script_resolves(self):
        import dlmm_pipeline
        self.assertIsNotNone(dlmm_pipeline._audit_script())


class PipelineWiringTests(unittest.TestCase):
    def test_entry_paths_use_shared_parser(self):
        # dlmm_pipeline runs at import, so check the wiring textually.
        here = Path(__file__).parent
        src = (here / "dlmm_pipeline.py").read_text()
        self.assertIn("signal_record = parse_signal_record(cli.from_signal)", src)
        self.assertNotIn("json.loads(cli.from_signal)", src)
        self.assertNotIn("json.loads(cli.from_signal)", (here / "dlmm_candidate_watch.py").read_text())

    def test_from_pool_feeds_the_from_signal_path(self):
        src = (Path(__file__).parent / "dlmm_pipeline.py").read_text()
        resolve = src.index("delivered = load_delivered_record(cli.from_pool, mode)")
        self.assertIn("cli.from_signal = json.dumps(delivered)", src[resolve:resolve + 400])
        # Resolved before anything else reads cli.from_signal.
        self.assertLess(resolve, src.index("record_pipeline_candidates(PROFILE_DIR, cli)"))
        self.assertLess(resolve, src.index("if cli.from_batch or cli.from_signal:\n        automatic_strategy"))


if __name__ == "__main__":
    unittest.main()
