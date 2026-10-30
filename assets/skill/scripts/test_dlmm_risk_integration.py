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


def sl_replay(*, pct, stop=-3, age=5, in_range=True, portfolio=False, indexed='fee10', indicators=False):
    """Run the production valuation, stop-loss, downtrend/indicator and timing slices with stubbed reads.
    Base d9156a6 read the indexed position whenever the portfolio row was missing, so its fee rate
    reached the young in-range SL grace. Returns (scope, commands)."""
    import contextlib, io, textwrap, time
    from test_dlmm_monitor_bounds import SuspectRiskTests, POOL, POSITION
    mark = SuspectRiskTests().mark(pct=pct)
    lo, hi = (-465, -430) if in_range else (-420, -400)
    mark.update(active_bin=-450, lower_bin=lo, upper_bin=hi, in_range=in_range)
    source = Path(monitor.__file__).read_text(); calls = []; now = time.time()
    scope = dict(vars(monitor), now=now, meta={'deployed_at': now - age * 60, 'mode': 'multiday'}, pair='TEST-SOL',
                 pool=POOL, pos_addr=POSITION, is_dry_run_stored=False, api_available=portfolio,
                 bp={'pool': POOL, 'pnl_pct': pct, 'pnl_sol': pct * .001, 'fee_per_tvl_24h': 10.0, 'pool_price': 1.0}
                 if portfolio else {'pool': POOL},
                 entry_price=1.0, bins_below=35, pnl_pct=pct, pnl_sol_actual=pct * .001, in_range=in_range,
                 active_bin=-450, pnl_data=None, stop_loss_pct=stop, fee_per_tvl_24h=1)
    def read(cmd, **kw):
        calls.append((cmd, kw.get('timeout')))
        if ' pnl-onchain ' in cmd: return mark, None
        if ' active-bin ' in cmd: return {'binId': -450, 'price': 1.0}, None
        assert ' pnl ' in cmd, cmd
        if indexed == 'failure': return None, 'indexer unavailable'
        fee = {'fee10': 10.0, 'fee5': 5.0, 'null': None}[indexed]
        return {'success': True, 'pnl_pct': pct, 'pnl_sol': pct * .001, 'fee_per_tvl_24h': fee, 'in_range': in_range}, None
    scope.update(run_command_json=read, run_command=lambda *a, **k: ('', '', 0))
    def block(a, b): return textwrap.dedent(source[source.index(a):source.index(b)])
    with contextlib.redirect_stdout(io.StringIO()):
        exec('for _ in [None]:\n' + textwrap.indent(block('        # Get current pool price', '        # Pool aggregates do not include'), '    '), scope)
        scope.update(close_reason=None, emergency_close=False, emergency_reason=None)
        exec(block('        # 2. Hard Stop-Loss Check', '        # 3. Pumped Far Above'), scope)
        scope['stop_reason'] = scope['close_reason']
        scope.update(is_tight_tp_pos=False, price_change_h1=0, params={'INDICATORS_ENABLED': indicators},
                     check_local_indicators=lambda *a: False)
        exec(block('        downtrend_pnl_only_limit =', '        # 5d. Fast-out velocity exit'), scope)
        exec(block('        close_reason, protected_risk_exit = protect_tight_exit(', '        # --report-only: collect state'), scope)
    return scope, [c for c, _ in calls if ' pnl ' in c], [t for c, t in calls if ' pnl ' in c]


class StopLossGraceDifferential(unittest.TestCase):
    """Native-first valuation must not remove the base's young in-range SL grace (codex PR-C review P1)."""
    def test_measured_high_fee_keeps_the_grace_like_the_base(self):
        for pct, stop, indicators in ((-4, -3, False), (-9, -8, True)):  # codex's two controls
            with self.subTest(pct=pct, stop=stop):
                scope, reads, timeouts = sl_replay(pct=pct, stop=stop, indicators=indicators)
                self.assertIsNone(scope['stop_reason']); self.assertIsNone(scope['close_reason'])
                self.assertFalse(scope['emergency_close'])
                self.assertEqual(scope['pnl_pct'], pct)  # native mark still decides the P&L
                self.assertEqual(len(reads), 1); self.assertEqual(timeouts, [monitor.SL_GRACE_FEE_TIMEOUT_SECS])
                self.assertTrue(scope['fee_yield_available']); self.assertEqual(scope['fee_per_tvl_24h'], 10.0)

    def test_unknown_or_low_fee_is_never_treated_as_healthy(self):
        for indexed in ('fee5', 'null', 'failure'):
            with self.subTest(indexed=indexed):
                scope, reads, _ = sl_replay(pct=-4, indexed=indexed)
                self.assertIn('Hard Stop-Loss', scope['stop_reason']); self.assertEqual(len(reads), 1)
                self.assertEqual(scope['fee_yield_available'], indexed == 'fee5')

    def test_emergency_and_ineligible_positions_never_wait_for_fee_context(self):
        cases = (dict(pct=-7, stop=-3),                      # below the emergency floor
                 dict(pct=-4, age=20),                        # past the 15-minute grace window
                 dict(pct=-4, in_range=False),                # out of range
                 dict(pct=-2))                                # above the stop-loss
        for case in cases:
            with self.subTest(**case):
                scope, reads, _ = sl_replay(**case)
                self.assertEqual(reads, [])
                if case['pct'] == -7: self.assertTrue(scope['emergency_close'])
                elif case['pct'] == -2: self.assertIsNone(scope['stop_reason'])
                else: self.assertIn('Hard Stop-Loss', scope['stop_reason'])

    def test_portfolio_fee_context_needs_no_extra_read(self):
        scope, reads, _ = sl_replay(pct=-4, portfolio=True)
        self.assertEqual(reads, []); self.assertIsNone(scope['stop_reason'])


if __name__ == '__main__':
    unittest.main()
