"""The exit-liquidity-floor live gate is journaled; the gate decision itself is unchanged."""
import contextlib
import io
import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

import dlmm_candidate_watch as watch
import dlmm_pipeline as pipeline

# Synthetic identities only.
POOL = 'SynthPoo1' + 'P' * 34
MINT = 'SynthMint' + 'M' * 34
FLOOR = 7000.0


def candidate(**extra):
    row = dict(name='SYN-SOL', pool=POOL, base_mint=MINT, base_symbol='SYN', sol_is_x=False,
               tvl=4000.0, active_tvl=3000.0)
    row.update(extra)
    return row


def gate(c, liquidity, *, other_reason=None):
    """Stand-in for predeploy_live_gate_reject: same evidence dict, same reasons."""
    c['entry_live_gates'] = dict(pool_liquidity_usd=liquidity, exit_liquidity_floor_usd=FLOOR)
    if liquidity is not None and liquidity < FLOOR:
        return f"pool liquidity ${liquidity:,.0f} below exit floor ${FLOOR:,.0f}"
    return other_reason


class ExitLiquidityJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile = Path(self.tmp.name)
        (self.profile / 'memories').mkdir()
        self.env = patch.dict(os.environ, {'DLMM_REJECT_IDENTITY': '1', 'DRY_RUN': 'false'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def rows(self):
        path = self.profile / 'memories' / watch.REJECT_FILENAME
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def snippet(self, start, end):
        source = Path(pipeline.__file__).read_text()
        begin = source.index(start)
        return textwrap.dedent(source[begin:source.index(end, begin)])

    def run_single_signal_abort(self, c, liquidity, other_reason=None):
        """The real non-batch live-gate block of main(), executed on its own."""
        code = self.snippet('    if not batch_mode or cli.pool:\n        rejection = predeploy_live_gate_reject(winner',
                            '    print(f"\\n🚀 WINNING CANDIDATE')
        ns = dict(vars(pipeline), winner=c, deploy_sol=0.1, timeframe='5m', mode='pulse', batch_mode=False,
                  cli=None, PROFILE_DIR=str(self.profile),
                  predeploy_live_gate_reject=lambda cand, sol, tf: gate(cand, liquidity, other_reason=other_reason))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                exec(compile(code, pipeline.__file__, 'exec'), ns)
            except SystemExit as stop:
                return stop.code, out.getvalue()
        return None, out.getvalue()

    def run_batch_pick(self, c, liquidity, other_reason=None):
        """The real batch live-gate block of the pick loop, run inside a one-item loop."""
        body = self.snippet('            if batch_mode:\n                rejection = predeploy_live_gate_reject(c',
                            '            winner = c\n')
        code = 'winner = None\nfor c in candidates:\n' + textwrap.indent(body, '    ') + '    winner = c\n'
        ns = dict(vars(pipeline), candidates=[c], deploy_sol=0.1, timeframe='5m', mode='pulse', batch_mode=True,
                  PROFILE_DIR=str(self.profile),
                  predeploy_live_gate_reject=lambda cand, sol, tf: gate(cand, liquidity, other_reason=other_reason))
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code, pipeline.__file__, 'exec'), ns)
        return ns['winner']

    def test_single_signal_below_floor_writes_one_row_and_still_aborts(self):
        code, out = self.run_single_signal_abort(candidate(), 1000.0)
        self.assertEqual(code, 0)
        self.assertIn('Aborting deploy: live gate rejected: pool liquidity $1,000 below exit floor $7,000', out)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row['gate'], row['mode'], row['pool'], row['candidate']['base_mint']),
                         ('exit_liquidity_floor', 'pulse', POOL, MINT))
        self.assertEqual(row['dexscreener_liquidity_usd'], 1000.0)
        self.assertEqual(row['meteora_tvl_usd'], 4000.0)
        self.assertEqual(row['meteora_active_tvl_usd'], 3000.0)
        self.assertEqual(row['floor_usd'], FLOOR)
        self.assertAlmostEqual(row['liq_ratio'], 0.25)
        self.assertTrue(row['id'].startswith('reject:'))

    def test_missing_meteora_tvl_is_null_never_zero(self):
        for tvl in (None, 0, -5, 'NaN', True, 'junk'):
            with self.subTest(tvl=tvl):
                c = candidate(tvl=tvl)
                c.pop('active_tvl')
                code, _ = self.run_single_signal_abort(c, 1000.0)
                self.assertEqual(code, 0)
                row = self.rows()[-1]
                self.assertIsNone(row['meteora_tvl_usd'])
                self.assertIsNone(row['meteora_active_tvl_usd'])
                self.assertIsNone(row['liq_ratio'])
                self.assertEqual(row['dexscreener_liquidity_usd'], 1000.0)

    def test_single_signal_other_live_reasons_unchanged(self):
        code, out = self.run_single_signal_abort(candidate(), 9000.0, other_reason='dumping -9.00% in last 5m')
        self.assertEqual(code, 0)
        self.assertIn('live gate rejected: dumping', out)
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.run_single_signal_abort(candidate(), 9000.0)[0], None)
        self.assertEqual(self.rows(), [])

    def test_batch_pick_labels_floor_and_keeps_generic_live_gate(self):
        self.assertIsNone(self.run_batch_pick(candidate(), 1000.0))
        self.assertIsNone(self.run_batch_pick(candidate(), 9000.0, other_reason='dumping'))
        self.assertIsNotNone(self.run_batch_pick(candidate(), 9000.0))
        rows = self.rows()
        self.assertEqual([r['gate'] for r in rows], ['exit_liquidity_floor', 'live_gate'])
        self.assertEqual(rows[0]['liq_ratio'], 0.25)
        self.assertNotIn('dexscreener_liquidity_usd', rows[1])

    def test_unknown_depth_is_not_the_floor_gate(self):
        c = candidate()
        c['entry_live_gates'] = dict(pool_liquidity_usd=None, exit_liquidity_floor_usd=FLOOR)
        self.assertIsNone(pipeline.exit_liquidity_reject_evidence(c))
        self.assertIsNone(pipeline.exit_liquidity_reject_evidence(candidate()))
        c['entry_live_gates'] = dict(pool_liquidity_usd=7000.0, exit_liquidity_floor_usd=FLOOR)
        self.assertIsNone(pipeline.exit_liquidity_reject_evidence(c))  # inclusive boundary passes
        # Malformed evidence never raises on the abort path; it just is not this gate.
        for gates in ('junk', dict(pool_liquidity_usd='5', exit_liquidity_floor_usd=FLOOR),
                      dict(pool_liquidity_usd=float('nan'), exit_liquidity_floor_usd=FLOOR),
                      dict(pool_liquidity_usd=True, exit_liquidity_floor_usd=FLOOR)):
            self.assertIsNone(pipeline.exit_liquidity_reject_evidence(dict(entry_live_gates=gates)))

    def test_reject_extra_cannot_override_identity_or_store_non_numbers(self):
        self.assertEqual(watch.reject_extra(dict(gate=1.0, pool=2.0, id=3.0, ok=4, bad=float('inf'),
                                                 txt='x', flag=True, huge=10 ** 400, Bad=1.0)),
                         dict(ok=4.0, bad=None, txt=None, flag=None, huge=None))
        self.assertEqual(watch.reject_extra(None), {})

    def test_extra_rows_still_satisfy_reject_readers(self):
        self.run_single_signal_abort(candidate(), 1000.0)
        row = self.rows()[0]
        # Fields the bracket collector and the cohort evaluator key on.
        for key in ('id', 'gate', 'pool', 'mode', 'ts'):
            self.assertIn(key, row)
        self.assertEqual(row['candidate'], dict(base_mint=MINT, sol_is_x=False))
        self.assertRegex(row['gate'], watch.REJECT_GATE)

    def test_journal_stays_opt_in(self):
        with patch.dict(os.environ, {'DLMM_REJECT_IDENTITY': '0'}):
            code, _ = self.run_single_signal_abort(candidate(), 1000.0)
        self.assertEqual(code, 0)
        self.assertEqual(self.rows(), [])


if __name__ == '__main__':
    unittest.main()
