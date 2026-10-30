"""tz_util day keys and labels across zones; no network, no services."""
import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tz_util  # noqa: E402

# 2024-10-04 20:30 UTC: already the 5th east of +3:30, still the 4th west of UTC.
TS = datetime(2024, 10, 4, 20, 30, tzinfo=timezone.utc).timestamp()


class TzUtilTests(unittest.TestCase):
    def at(self, name):
        return patch.dict(os.environ, {"DLMM_TZ": name})

    def test_default_is_utc(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(tz_util.zone_name(), "UTC")
            self.assertEqual(tz_util.local_date_str(TS), "2024-10-04")
            self.assertEqual(tz_util.local_time_str(ts=TS), "20:30 UTC")

    def test_unknown_zone_falls_back_to_utc(self):
        with self.at("Mars/Olympus"):
            self.assertEqual(tz_util.zone_name(), "UTC")
            self.assertEqual(tz_util.local_time_str("%Y-%m-%d %H:%M %Z", TS), "2024-10-04 20:30 UTC")

    def test_positive_offset_moves_to_next_day(self):
        with self.at("Asia/Tokyo"):
            self.assertEqual(tz_util.local_date_str(TS), "2024-10-05")
            self.assertEqual(tz_util.local_time_str(ts=TS), "05:30 JST")

    def test_negative_offset_stays_on_the_day(self):
        with self.at("America/Sao_Paulo"):
            self.assertEqual(tz_util.local_date_str(TS), "2024-10-04")
            self.assertEqual(tz_util.local_time_str("%H:%M", TS), "17:30")
        with self.at("Pacific/Pago_Pago"):  # UTC-11: next UTC morning is still the 4th
            late = datetime(2024, 10, 5, 10, 0, tzinfo=timezone.utc).timestamp()
            self.assertEqual(tz_util.local_date_str(late), "2024-10-04")

    def test_dst_zone_uses_the_offset_in_force(self):
        with self.at("Europe/Berlin"):
            summer = datetime(2024, 7, 1, 22, 30, tzinfo=timezone.utc).timestamp()
            winter = datetime(2024, 1, 1, 22, 30, tzinfo=timezone.utc).timestamp()
            self.assertEqual(tz_util.local_date_str(summer), "2024-07-02")  # +2
            self.assertEqual(tz_util.local_date_str(winter), "2024-01-01")  # +1
            self.assertEqual(tz_util.local_time_str("%Z", summer), "CEST")

    def test_now_is_aware(self):
        with self.at("Asia/Kolkata"):
            self.assertIsNotNone(tz_util.local_dt().tzinfo)


if __name__ == "__main__":
    unittest.main()
