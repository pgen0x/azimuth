"""Monitor risk-path integration: hold canary x fee-yield availability, lamport-scale marks (synthetic, offline)."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_monitor as monitor
from test_dlmm_hold_canary import ARM_A, ARM_B, YIELD_BLOCK


def low_yield_fires(position, mode, age, flag, available):
    """Run the real yield-exit block once; True when it selected a Low yield close."""
    with patch.dict(os.environ, {'PULSE_HOLD_CANARY': flag}):
        scope = dict(meta={'deployed_at': 0, 'mode': mode}, now=age * 60, pos_addr=position,
                     pulse_min_age_before_yield_check=30, min_age_before_yield_check=60,
                     min_fee_tvl_24h_tight_limit=5, min_fee_tvl_24h_limit=1, is_tight_tp_pos=True,
                     fee_per_tvl_24h=0, fee_yield_available=available, close_reason=None)
        exec(compile(YIELD_BLOCK, monitor.__file__, 'exec'), vars(monitor) | scope, scope)
        return bool(scope['close_reason'] and 'Low yield' in scope['close_reason'])


class CanaryYieldMatrix(unittest.TestCase):
    def test_unknown_yield_never_fires_and_measured_zero_waits_for_the_arm_grace(self):
        cases = [  # flag, position, mode, grace in minutes
            ('0', ARM_A, 'pulse', 30), ('0', ARM_B, 'pulse', 30), ('0', ARM_A, 'turnover', 60),
            ('1', ARM_A, 'pulse', 30), ('1', ARM_B, 'pulse', 60), ('1', ARM_B, 'turnover', 60)]
        for flag, position, mode, grace in cases:
            with self.subTest(flag=flag, arm='B' if position == ARM_B else 'A', mode=mode):
                self.assertFalse(low_yield_fires(position, mode, 10_000, flag, available=False))
                self.assertFalse(low_yield_fires(position, mode, grace - 1, flag, available=True))
                self.assertTrue(low_yield_fires(position, mode, grace, flag, available=True))


class LamportPrecision(unittest.TestCase):
    def test_close_journal_and_report_row_keep_one_signed_lamport(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'memories').mkdir()
            with patch.object(monitor, 'PROFILE_DIR', tmp):
                for value in (-1e-9, 1e-9, -0.000001234, None):
                    monitor.log_close('pool', 'TOKEN-SOL', {'mode': 'pulse'}, 'position', -0.1, value,
                                      1.0, 5.0, 'synthetic', [], False)
            rows = [json.loads(l) for l in (Path(tmp) / 'memories/dlmm_closes.jsonl').read_text().splitlines()]
        self.assertEqual([r['pnl_sol'] for r in rows], [-1e-9, 1e-9, -0.000001234, None])
        self.assertTrue(all('hold_canary_arm' in r for r in rows))  # the canary field survives the precision change
        with patch.object(monitor, 'run_command', return_value=('', '', 0)):
            row = monitor.build_report_row('position', 'TOKEN-SOL', 'pool', {}, None, -1, -1e-9,
                                           True, 0, False, None, 1, 1, 0, False, None, 10000,
                                           fee_yield_available=True)
        self.assertEqual(row['pnl_sol'], -1e-9)  # six decimals used to round this to -0.0


if __name__ == '__main__':
    unittest.main()
