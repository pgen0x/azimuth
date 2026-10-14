import datetime
import io
import json
import unittest
from unittest.mock import patch

import dlmm_reconcile


class CalendarCoverageTest(unittest.TestCase):
    def check_window(self, today, days, expected_months):
        class FixedDatetime(datetime.datetime):
            @classmethod
            def now(cls, tz=None):
                return cls.fromisoformat(today).replace(tzinfo=tz)

        requested = []

        def response(req, timeout):
            month = req.full_url.split('month=')[1]
            requested.append(month)
            return io.BytesIO(json.dumps({'data_points': [
                {'date_time': month + '-15', 'pnl_sol': '1.25'},
            ]}).encode())

        with patch.object(dlmm_reconcile.datetime, 'datetime', FixedDatetime), \
                patch.object(dlmm_reconcile.urllib.request, 'urlopen', response):
            rows = dlmm_reconcile.fetch_calendar('wallet', days)
        self.assertEqual(requested, expected_months)
        cutoff = datetime.date.fromisoformat(today) - datetime.timedelta(days=days)
        expected_dates = [m + '-15' for m in expected_months
                          if cutoff.isoformat() <= m + '-15' <= today]
        self.assertEqual(rows, [(d, 1.25) for d in expected_dates])

    def test_funding_window_includes_intermediate_months(self):
        self.check_window('2026-10-14', 78,
                          ['2026-07', '2026-08', '2026-09', '2026-10'])

    def test_year_boundary(self):
        self.check_window('2027-02-16', 80,
                          ['2026-11', '2026-12', '2027-01', '2027-02'])

    def test_same_month_requested_once(self):
        self.check_window('2026-10-20', 10, ['2026-10'])


if __name__ == '__main__':
    unittest.main()
