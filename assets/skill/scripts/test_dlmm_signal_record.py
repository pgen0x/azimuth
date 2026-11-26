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


class FromSignalResolvesToDeliveryTests(unittest.TestCase):
    """--from-signal runs gates on the daemon's delivered record, never on retyped JSON."""
    DELIVERED_POOL = "2v3XPhyAnDeLiVeReDpooLxxxxxxxxxxhj1fz"
    TYPED_POOL = "2v3XPhYGNmAnGLeDpooLxxxxxxxxxxxhj1fz"

    def record(self, **changes):
        rec = dict(pool=self.DELIVERED_POOL, name="SYN-SOL", base_mint="M" * 32, base_symbol="SYN",
                   tvl=20000, volatility=2.5, score=61, mode="pulse")
        rec.update(changes)
        return rec

    def run_pipeline(self, typed, delivered_or_error, env=None):
        import contextlib
        import io
        import os
        from unittest.mock import patch
        import dlmm_pipeline as pipeline

        class Reached(Exception):
            pass
        seen = {}

        def conviction(records, mode):
            seen["records"] = records
            raise Reached()

        def delivered(pool, mode):
            seen["asked"] = (pool, mode)
            if isinstance(delivered_or_error, Exception):
                raise delivered_or_error
            return delivered_or_error
        params = dict(MIN_TVL_USD=10000, MIN_FEE_TVL_24H=1, MIN_ORGANIC_SCORE=60,
                      MIN_MCAP_USD=150000, MIN_HOLDERS=100, MAX_POSITIONS=4)
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(pipeline, "PROFILE_DIR", tmp), \
                patch.object(pipeline.sys, "argv", ["pipeline", "--mode", "pulse", "--from-signal", json.dumps(typed)]), \
                patch.object(pipeline, "load_soul_dlmm_params", return_value=params), \
                patch.object(pipeline, "reconcile_redis_vs_meteora"), \
                patch.object(pipeline, "get_active_positions_count_for_mode", return_value=0), \
                patch.object(pipeline, "risk_pause_refusal", return_value=None, create=True), \
                patch.object(pipeline, "get_wallet_sol_balance", return_value=10.0), \
                patch.object(pipeline, "record_pipeline_candidates", return_value=0), \
                patch.object(pipeline, "load_delivered_record", side_effect=delivered), \
                patch.object(pipeline, "apply_batch_conviction", side_effect=conviction), \
                patch.dict(os.environ, env or {}), contextlib.redirect_stdout(out):
            os.environ.pop("DLMM_FROM_SIGNAL_UNVERIFIED", None) if not env else None
            try:
                pipeline.main()
                code = 0
            except Reached:
                code = "reached"
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), seen

    def test_typed_pool_not_delivered_aborts(self):
        code, out, seen = self.run_pipeline(self.record(pool=self.TYPED_POOL),
                                            SignalRecordError("no pulse signal delivered"))
        self.assertEqual(code, 1)
        self.assertEqual(seen["asked"], (self.TYPED_POOL, "pulse"))
        self.assertIn("Aborting: --from-signal pool not in a delivered pulse signal", out)
        self.assertNotIn("records", seen)

    def test_drifted_numbers_use_the_delivered_record(self):
        delivered = self.record()
        typed = self.record(tvl=99999, score=88)
        typed.pop("volatility")                     # a dropped key is drift too, not an abort
        code, out, seen = self.run_pipeline(typed, delivered)
        self.assertEqual(code, "reached")
        self.assertEqual(seen["records"], [delivered])
        self.assertIn("Signal record drift from delivery journal ignored: score, tvl, volatility", out)

    def test_exact_record_prints_no_drift(self):
        code, out, seen = self.run_pipeline(self.record(), self.record())
        self.assertEqual(code, "reached")
        self.assertNotIn("drift", out)

    def test_operator_escape_still_passes(self):
        typed = self.record(pool=self.TYPED_POOL)
        code, out, seen = self.run_pipeline(typed, SignalRecordError("not delivered"),
                                            env={"DLMM_FROM_SIGNAL_UNVERIFIED": "1"})
        self.assertEqual(code, "reached")
        self.assertEqual(seen["records"], [typed])
        self.assertIn("DLMM_FROM_SIGNAL_UNVERIFIED=1", out)


if __name__ == "__main__":
    unittest.main()
