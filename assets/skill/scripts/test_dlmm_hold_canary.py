"""PULSE_HOLD_CANARY: deterministic A/B of the pulse yield-check grace (synthetic, offline)."""
import hashlib
import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_monitor as monitor

IDS = [f'position-{i}' for i in range(200)]
ARM_B = next(p for p in IDS if int(hashlib.sha256(p.encode()).hexdigest()[:8], 16) % 2 == 1)
ARM_A = next(p for p in IDS if int(hashlib.sha256(p.encode()).hexdigest()[:8], 16) % 2 == 0)
SOURCE = Path(monitor.__file__).read_text()
YIELD_BLOCK = textwrap.dedent(SOURCE[SOURCE.index('        # 5. Low Yield Exit Check'):
                                     SOURCE.index('        # 5b. Exit-side liquidity floor')])


def first_low_yield_close(position, mode, ages, flag):
    """Run the real yield-exit block tick by tick; return the age of the first Low yield close."""
    with patch.dict(os.environ, {'PULSE_HOLD_CANARY': flag}):
        for age in ages:
            scope = dict(meta={'deployed_at': 0, 'mode': mode}, now=age * 60, pos_addr=position,
                         pulse_min_age_before_yield_check=30, min_age_before_yield_check=60,
                         min_fee_tvl_24h_tight_limit=5, min_fee_tvl_24h_limit=1, is_tight_tp_pos=True,
                         fee_per_tvl_24h=0, fee_yield_available=True, close_reason=None)
            exec(compile(YIELD_BLOCK, monitor.__file__, 'exec'), vars(monitor) | scope, scope)
            if scope['close_reason'] and 'Low yield' in scope['close_reason']:
                return age
    return None


class HoldCanaryTests(unittest.TestCase):
    def test_arm_is_off_by_default_and_stable_when_on(self):
        with patch.dict(os.environ, {'PULSE_HOLD_CANARY': '0'}):
            self.assertTrue(all(monitor.pulse_hold_canary_arm(p) is None for p in IDS))
        with patch.dict(os.environ, {'PULSE_HOLD_CANARY': '1'}):
            arms = [monitor.pulse_hold_canary_arm(p) for p in IDS]
            self.assertEqual(arms, [monitor.pulse_hold_canary_arm(p) for p in IDS])
            self.assertEqual(set(arms), {'A', 'B'})
            self.assertTrue(70 <= arms.count('B') <= 130)  # roughly half of 200
            self.assertEqual(monitor.pulse_hold_canary_arm(ARM_B), 'B')
            self.assertIsNone(monitor.pulse_hold_canary_arm(''))
            self.assertIsNone(monitor.pulse_hold_canary_arm(None))

    def test_grace_matches_the_old_expression_when_off(self):
        old = lambda meta: 30 if meta.get('mode') == 'pulse' else 60
        for flag in ('0', ''):
            with patch.dict(os.environ, {'PULSE_HOLD_CANARY': flag}):
                for mode in ('pulse', 'turnover', None, 'casual'):
                    for p in (ARM_A, ARM_B):
                        self.assertEqual(monitor.yield_grace_minutes_for({'mode': mode}, p, 30, 60), old({'mode': mode}))

    def test_only_arm_b_pulse_changes_when_on(self):
        with patch.dict(os.environ, {'PULSE_HOLD_CANARY': '1'}):
            self.assertEqual(monitor.yield_grace_minutes_for({'mode': 'pulse'}, ARM_B, 30, 60), 60.0)
            self.assertEqual(monitor.yield_grace_minutes_for({'mode': 'pulse'}, ARM_A, 30, 60), 30)
            for mode in ('turnover', None, 'casual'):
                self.assertEqual(monitor.yield_grace_minutes_for({'mode': mode}, ARM_B, 30, 60), 60)
                self.assertEqual(monitor.yield_grace_minutes_for({'mode': mode}, ARM_A, 30, 45), 45)

    def test_tick_sequence_through_the_real_yield_block(self):
        ages = [10, 31, 45, 59, 61, 90]
        self.assertEqual(first_low_yield_close(ARM_B, 'pulse', ages, '0'), 31)
        self.assertEqual(first_low_yield_close(ARM_A, 'pulse', ages, '1'), 31)
        self.assertEqual(first_low_yield_close(ARM_B, 'pulse', ages, '1'), 61)
        for flag in ('0', '1'):
            self.assertEqual(first_low_yield_close(ARM_B, 'turnover', ages, flag), 61)

    def test_close_row_records_the_arm(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(monitor, 'PROFILE_DIR', tmp):
            os.makedirs(os.path.join(tmp, 'memories'))
            for flag, mode, position, want in (('0', 'pulse', ARM_B, None), ('1', 'pulse', ARM_B, 'B'),
                                               ('1', 'pulse', ARM_A, 'A'), ('1', 'turnover', ARM_B, None)):
                with patch.dict(os.environ, {'PULSE_HOLD_CANARY': flag}):
                    monitor.log_close('pool', 'T-SOL', {'mode': mode}, position, 0.0, 0.0, 0.0, 31.0, 'Low yield', [], True)
                row = json.loads(Path(tmp, 'memories', 'dlmm_closes.jsonl').read_text().splitlines()[-1])
                self.assertIn('hold_canary_arm', row)
                self.assertEqual(row['hold_canary_arm'], want, (flag, mode))


if __name__ == '__main__':
    unittest.main()
