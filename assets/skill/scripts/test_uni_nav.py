"""uni_nav.py: synthetic wallet and journals, a fake JSON-RPC; no network, no key, nothing real."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uni_nav as n  # noqa: E402

WALLET = '0x' + '1' * 40  # synthetic


def h(v):
    return '0x' + format(v, '064x')


class FakeRPC:
    """Answers by call shape; records every payload so tests can check what was asked."""

    def __init__(self, eth=2 * 10**18, weth=5 * 10**17, usdg=12_345_678, decimals=6, liq=None, fail=False, drop=()):
        self.v = {'eth': eth, 'weth': weth, 'usdg': usdg, 'dec': decimals}
        self.liq, self.fail, self.drop, self.calls = liq or {}, fail, set(drop), []

    def post(self, payload):
        self.calls.append(payload)
        if self.fail:
            raise OSError('connect to https://rpc.example/SECRETKEY failed')
        out = []
        for c in payload:
            m, p = c['method'], c['params']
            if m == 'eth_getBalance':
                v = self.v['eth']; name = 'eth'
            else:
                to, data = p[0]['to'], p[0]['data']
                if to == n.WETH:
                    v = self.v['weth']; name = 'weth'
                elif to == n.USDG and data == n.SEL_DECIMALS:
                    v = self.v['dec']; name = 'dec'
                elif to == n.USDG:
                    v = self.v['usdg']; name = 'usdg'
                else:
                    tid = int(data[10:], 16); name = 'liq'
                    v = self.liq.get((to, tid))
                    if v is not None and to == n.NPM_V3:
                        out.append({'jsonrpc': '2.0', 'id': c['id'], 'result': '0x' + '0' * 64 * 7 + format(v, '064x') + '0' * 64 * 4})
                        continue
            if name in self.drop or v is None:
                out.append({'jsonrpc': '2.0', 'id': c['id'], 'error': {'code': -32000, 'message': 'execution reverted'}})
            else:
                out.append({'jsonrpc': '2.0', 'id': c['id'], 'result': h(v)})
        return out


class UniNavTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.p = Path(self.tmp.name); (self.p / 'memories').mkdir()
        (self.p / '.env').write_text(f'EVM_PRIVATE_KEY=0xnotread\nKRYSTAL_WALLET={WALLET}\nROBINHOOD_RPC_URL=https://rpc.example/SECRETKEY\n')
        self.env = patch.dict('os.environ', {}, clear=False); self.env.start()
        for k in n.ENV_KEYS:
            os.environ.pop(k, None)

    def tearDown(self):
        self.env.stop(); self.tmp.cleanup()

    def rows(self, name, rows):
        (self.p / 'memories' / name).write_text(''.join(json.dumps(r) + '\n' for r in rows))

    def snap(self, fake):
        return n.snapshot(self.p, rpc=n.RPC('unused', post=fake.post), now=1000)

    def test_balances_in_units_and_no_secret_in_row(self):
        fake = FakeRPC()
        row = self.snap(fake)
        self.assertEqual((row['eth'], row['weth'], row['usdg']), (2.0, 0.5, 12.345678))  # USDG at 6 decimals
        self.assertEqual((row['status'], row['errors'], row['ts']), ('ok', [], 1000))
        self.assertEqual(row['lp_mark_quote'], {'ETH': 0.0, 'USDG': 0.0})
        text = json.dumps(row)
        self.assertNotIn(WALLET[2:], text); self.assertNotIn('SECRETKEY', text); self.assertNotIn('notread', text)
        # Only the pinned real USDG contract is read, never any other "USDG".
        tos = {c['params'][0]['to'] for c in fake.calls[0] if c['method'] == 'eth_call'}
        self.assertEqual(tos, {n.WETH, n.USDG})

    def test_usdg_decimals_mismatch_is_unmeasured(self):
        row = self.snap(FakeRPC(decimals=18))
        self.assertIsNone(row['usdg']); self.assertEqual(row['status'], 'partial')
        self.assertIn('USDG decimals mismatch', row['errors'])

    def test_rpc_failure_is_unavailable_and_never_leaks_the_url(self):
        row = self.snap(FakeRPC(fail=True))
        self.assertEqual((row['eth'], row['weth'], row['usdg'], row['status']), (None, None, None, 'unavailable'))
        self.assertNotIn('SECRETKEY', json.dumps(row))

    def test_one_balance_missing_is_partial_not_zero(self):
        row = self.snap(FakeRPC(drop={'weth'}))
        self.assertIsNone(row['weth']); self.assertEqual(row['eth'], 2.0); self.assertEqual(row['status'], 'partial')

    def test_open_positions_valued_at_quote_in_ghosts_and_closed_skipped(self):
        self.rows('uni_positions.jsonl', [
            {'tokenId': '10', 'quoteSymbol': 'WETH', 'quoteIn': '0.2'},   # live
            {'tokenId': '11', 'quoteSymbol': 'WETH', 'quoteIn': '0.3'},   # ghost: zero liquidity
            {'tokenId': '12', 'quoteSymbol': 'USDG', 'quoteIn': '40'},    # live
            {'tokenId': '13', 'quoteSymbol': 'WETH', 'quoteIn': '9'},     # closed successfully
            {'tokenId': '14', 'quoteSymbol': 'PEPE', 'quoteIn': '1'}])    # unknown quote asset
        self.rows('uni_v4_positions.jsonl', [{'tokenId': '10', 'protocol': 'v4', 'quoteSymbol': 'ETH', 'quoteIn': '0.1'}])
        self.rows('uni_closes.jsonl', [{'tokenId': '13', 'success': True}, {'tokenId': '10', 'success': False}])
        fake = FakeRPC(liq={(n.NPM_V3, 10): 5, (n.NPM_V3, 11): 0, (n.NPM_V3, 12): 7, (n.POSM_V4, 10): 9, (n.NPM_V3, 14): 3})
        row = self.snap(fake)
        self.assertAlmostEqual(row['lp_mark_quote']['ETH'], 0.3)  # v3 #10 + v4 #10 (ids collide across versions)
        self.assertEqual(row['lp_mark_quote']['USDG'], 40.0)
        self.assertEqual((row['lp_positions'], row['lp_ghosts'], row['lp_unknown_asset']), ({'ETH': 2, 'USDG': 1}, 1, 1))
        self.assertEqual(row['lp_basis'], 'quote_in_at_mint'); self.assertEqual(row['status'], 'ok')

    def test_burned_token_revert_is_a_ghost_but_a_transport_error_is_unmeasured(self):
        self.rows('uni_positions.jsonl', [{'tokenId': '10', 'quoteSymbol': 'WETH', 'quoteIn': '0.2'}])
        row = self.snap(FakeRPC())  # liquidity call answers "execution reverted": the NFT was burned
        self.assertEqual((row['lp_mark_quote']['ETH'], row['lp_ghosts'], row['status']), (0.0, 1, 'ok'))
        fake = FakeRPC()
        orig = fake.post
        fake.post = lambda payload: [r if r['id'] < 4 else {'jsonrpc': '2.0', 'id': r['id'], 'error': {'code': -32603, 'message': 'internal error'}} for r in orig(payload)]
        row = self.snap(fake)
        self.assertIsNone(row['lp_mark_quote']['ETH']); self.assertEqual(row['status'], 'partial')

    def test_unreadable_liquidity_leaves_that_asset_null(self):
        self.rows('uni_positions.jsonl', [{'tokenId': '10', 'quoteSymbol': 'WETH', 'quoteIn': '0.2'},
                                          {'tokenId': '12', 'quoteSymbol': 'USDG', 'quoteIn': '40'}])
        fake = FakeRPC(liq={(n.NPM_V3, 12): 7})
        orig = fake.post  # the ETH position's read fails in transport, not by revert
        fake.post = lambda payload: [{'jsonrpc': '2.0', 'id': r['id'], 'error': {'code': -32603, 'message': 'timeout'}} if r.get('error') else r for r in orig(payload)]
        row = self.snap(fake)
        self.assertIsNone(row['lp_mark_quote']['ETH']); self.assertEqual(row['lp_mark_quote']['USDG'], 40.0)
        self.assertEqual(row['status'], 'partial')

    def test_env_allowlist_and_override(self):
        env = n.profile_env(self.p)
        self.assertEqual(set(env), {'KRYSTAL_WALLET', 'ROBINHOOD_RPC_URL'})  # the private key is never read into memory
        os.environ['UNI_NAV_WALLET'] = '0x' + '2' * 40
        self.assertEqual(n.profile_env(self.p)['UNI_NAV_WALLET'], '0x' + '2' * 40)

    def test_main_appends_one_row_and_unconfigured_writes_nothing(self):
        out = self.p / 'memories' / 'uni_nav.jsonl'
        real = n.RPC
        with patch.object(n, 'RPC', lambda url: real(url, post=FakeRPC().post)), redirect_stdout(io.StringIO()) as so:
            self.assertEqual(n.main(['--profile', str(self.p)]), 0)
            self.assertEqual(n.main(['--profile', str(self.p)]), 0)
        lines = out.read_text().splitlines()
        self.assertEqual(len(lines), 2); self.assertEqual(json.loads(lines[0])['status'], 'ok')
        self.assertNotIn(WALLET[2:], so.getvalue()); self.assertEqual(oct(out.stat().st_mode & 0o777), '0o600')
        (self.p / '.env').write_text('EVM_PRIVATE_KEY=0xnotread\n')
        out.unlink()
        with redirect_stderr(io.StringIO()) as se:
            self.assertEqual(n.main(['--profile', str(self.p)]), 2)
        self.assertFalse(out.exists()); self.assertIn('no public Robinhood wallet', se.getvalue())


if __name__ == '__main__':
    unittest.main()
