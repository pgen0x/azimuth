"""Funnel telemetry rows: conviction-floor rejects and deploy verification verdicts."""
import json
import os
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


if __name__ == '__main__':
    unittest.main()
