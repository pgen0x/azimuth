"""Funnel telemetry rows: conviction-floor rejects and deploy verification verdicts."""
import ast
import json
import os
import textwrap
import time
from types import SimpleNamespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dlmm_pipeline as pipeline

POOL = 'CqJVXBTY644ZBtPCkbaqV7Nu8Qzau2A4sChtpkvQQLLi'
MINT = 'EkFRff9a2jKztJHML1LG9FRmEkPJDR6XAYp3uCPdpump'


class FunnelRowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile = Path(self.tmp.name)
        (self.profile / 'memories').mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self, name):
        path = self.profile / 'memories' / name
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_conviction_floor_reject_is_journaled(self):
        weak = dict(name='WEAK-SOL', pool=POOL, base_mint=MINT, sol_is_x=False, score=10.0)
        strong = dict(name='STRONG-SOL', pool=POOL, base_mint=MINT, sol_is_x=False, score=80.0)
        with patch.object(pipeline, 'PROFILE_DIR', str(self.profile)), \
                patch.object(pipeline, 'load_signal_weights', return_value={}), \
                patch.dict(os.environ, {'DLMM_REJECT_IDENTITY': '1'}):
            kept = pipeline.apply_batch_conviction([weak, strong], 'pulse')
        self.assertEqual([c['name'] for c in kept], ['STRONG-SOL'])
        rows = self.rows('dlmm_pipeline_rejects.jsonl')
        self.assertEqual([(r['gate'], r['mode'], r['pool'], r['name']) for r in rows],
                         [('conviction_floor', 'pulse', POOL, 'WEAK-SOL')])

    def test_conviction_floor_reject_stays_opt_in(self):
        weak = dict(name='WEAK-SOL', pool=POOL, base_mint=MINT, sol_is_x=False, score=10.0)
        env = {k: v for k, v in os.environ.items() if k != 'DLMM_REJECT_IDENTITY'}
        with patch.object(pipeline, 'PROFILE_DIR', str(self.profile)), \
                patch.object(pipeline, 'load_signal_weights', return_value={}), \
                patch.dict(os.environ, env, clear=True):
            self.assertEqual(pipeline.apply_batch_conviction([weak], 'pulse'), [])
        self.assertEqual(self.rows('dlmm_pipeline_rejects.jsonl'), [])

    def test_deploy_verification_row(self):
        self.assertTrue(pipeline.record_deploy_verification(str(self.profile), 'Pos1', 'pulse', True))
        self.assertTrue(pipeline.record_deploy_verification(str(self.profile), 'Pos2', 'pulse', False))
        rows = self.rows('dlmm_deploy_verifications.jsonl')
        self.assertEqual([(r['position'], r['mode'], r['verified']) for r in rows],
                         [('Pos1', 'pulse', True), ('Pos2', 'pulse', False)])
        self.assertTrue(all(isinstance(r['ts'], float) for r in rows))

    def test_deploy_verification_never_raises(self):
        self.assertFalse(pipeline.record_deploy_verification(str(self.profile / 'missing'), 'Pos1', 'pulse', True))
        self.assertFalse(pipeline.record_deploy_verification(str(self.profile), None, 'pulse', True))


    # The real deploy -> verification block of main(), executed on its own: every entry route
    # (batch, --from-signal, --from-pool) reaches it through the one executor deploy call.
    def run_verify_block(self, res, pnl_results):
        source = Path(pipeline.__file__).read_text()
        start = source.index('    position_address = res.get("position"')
        end = source.index('    active_bin = bins_below', start)
        calls = []

        def pnl(cmd):
            calls.append(cmd)
            return (pnl_results.pop(0) if pnl_results else None), 'not indexed'
        ns = dict(vars(pipeline), res=res, winner=dict(pool=POOL), mode='pulse', PROFILE_DIR=str(self.profile),
                  run_command_json=pnl, time=SimpleNamespace(sleep=lambda s: None, time=time.time))
        exec(compile(textwrap.dedent(source[start:end]), pipeline.__file__, 'exec'), ns)
        return ns, calls

    def test_unverified_deploy_is_recorded_false(self):
        ns, calls = self.run_verify_block(dict(success=True, position='PosU', txHash='tx'), [])
        self.assertIs(ns['verified'], False)
        self.assertEqual(len(calls), 3)  # the UNVERIFIED branch: three on-chain lookups, all empty
        self.assertEqual([(r['position'], r['verified']) for r in self.rows('dlmm_deploy_verifications.jsonl')], [('PosU', False)])

    def test_late_verified_deploy_is_recorded_true(self):
        ns, calls = self.run_verify_block(dict(success=True, position='PosV', txHash='tx'), [None, dict(success=True)])
        self.assertIs(ns['verified'], True)
        self.assertEqual(len(calls), 2)
        self.assertEqual([(r['position'], r['verified']) for r in self.rows('dlmm_deploy_verifications.jsonl')], [('PosV', True)])

    def test_dry_run_deploy_writes_no_row(self):
        ns, calls = self.run_verify_block(dict(success=True, dryRun=True), [])
        self.assertIs(ns['verified'], True)
        self.assertEqual((calls, self.rows('dlmm_deploy_verifications.jsonl')), ([], []))

    def test_single_deploy_site_binds_verified_first(self):
        tree = ast.parse(Path(pipeline.__file__).read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        deploys = [n for n in ast.walk(main) if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'run_command_json'
                   and n.args and getattr(n.args[0], 'id', None) == 'deploy_cmd']
        records = [n for n in ast.walk(main) if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'record_deploy_verification']
        self.assertEqual((len(deploys), len(records)), (1, 1))
        # `verified` is bound unconditionally at main()'s top level, after the deploy and before the record.
        binds = [s for s in main.body if isinstance(s, ast.Assign) and any(getattr(t, 'id', None) == 'verified' for t in s.targets)]
        self.assertEqual(len(binds), 1)
        self.assertLess(deploys[0].lineno, binds[0].lineno)
        self.assertLess(binds[0].lineno, records[0].lineno)

if __name__ == '__main__':
    unittest.main()
