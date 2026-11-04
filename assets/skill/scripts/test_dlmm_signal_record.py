import json
import unittest
from pathlib import Path

from dlmm_signal_record import SignalRecordError, parse_signal_record

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


class PipelineWiringTests(unittest.TestCase):
    def test_entry_paths_use_shared_parser(self):
        # dlmm_pipeline runs at import, so check the wiring textually.
        here = Path(__file__).parent
        src = (here / "dlmm_pipeline.py").read_text()
        self.assertIn("signal_record = parse_signal_record(cli.from_signal)", src)
        self.assertNotIn("json.loads(cli.from_signal)", src)
        self.assertNotIn("json.loads(cli.from_signal)", (here / "dlmm_candidate_watch.py").read_text())


if __name__ == "__main__":
    unittest.main()
