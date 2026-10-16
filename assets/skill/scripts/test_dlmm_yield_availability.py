import contextlib
import io
from pathlib import Path
import textwrap
import unittest
from unittest.mock import patch
import dlmm_monitor as monitor

class YieldAvailabilityTests(unittest.TestCase):
    def test_zero_is_observed_but_missing_and_invalid_are_unknown(self):
        for value in (0, 0.0, '0', 1.25, '1.25'):
            self.assertEqual(monitor.observed_fee_yield({'fee_per_tvl_24h': value}), float(value))
        for value in (None, True, False, '', 'nan', float('inf'), -1, {}, []):
            self.assertIsNone(monitor.observed_fee_yield({'fee_per_tvl_24h': value}))
        self.assertIsNone(monitor.observed_fee_yield({'fee_per_tvl_24h': 0, 'fee_per_tvl_24h_available':False}))

    def test_unknown_does_not_exit_but_measured_zero_does(self):
        source=Path(monitor.__file__).read_text()
        code=textwrap.dedent(source[source.index('        # 5. Low Yield Exit Check'):source.index('        # 5b. Exit-side liquidity floor')])
        for available, prior in ((False,None),(False,'Stop-Loss'),(True,None)):
            scope=dict(meta={'deployed_at':1,'mode':'turnover'}, now=10000,
                pulse_min_age_before_yield_check=30,min_age_before_yield_check=60,
                min_fee_tvl_24h_tight_limit=5,min_fee_tvl_24h_limit=1,
                is_tight_tp_pos=True,fee_per_tvl_24h=0,fee_yield_available=available,close_reason=prior)
            exec(compile(code,monitor.__file__,'exec'),scope)
            if available:self.assertIn('Low yield',scope['close_reason'])
            else:self.assertEqual(scope['close_reason'],prior)

    def test_report_preserves_unknown_yield_and_break_even(self):
        with patch.object(monitor,'run_command',return_value=('', '',0)):
            row=monitor.build_report_row('position','TOKEN-SOL','pool',{},None,-1,-.001,
                True,0,False,None,1,1,0,False,None,10000,fee_yield_available=False)
        self.assertIsNone(row['fee_per_tvl_24h'])
        self.assertIsNone(row['break_even_days'])
        rendered=monitor.render_status_report([row],100,3,1,30)
        self.assertIn('Fee/TVL unavailable',rendered)
        self.assertNotIn('Low Fee/TVL',rendered)

if __name__=='__main__':unittest.main()
