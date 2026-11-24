#!/usr/bin/env python3
"""Robinhood Chain wallet snapshot (read-only): one row per run in <profile>/memories/uni_nav.jsonl.

Each row holds the wallet's native ETH, WETH and USDG balances read over public JSON-RPC
(eth_getBalance and ERC-20 balanceOf via eth_call), plus the quote locked in positions that are
still open, per quote asset:

    {"ts", "eth", "weth", "usdg", "lp_mark_quote": {"ETH", "USDG"}, "lp_positions", "lp_ghosts",
     "lp_basis", "status", "errors"}

- No key is read and no transaction is built: the address is the PUBLIC one the Robinhood monitor
  already uses (UNI_NAV_WALLET, else KRYSTAL_WALLET, from the environment or the profile .env).
  Neither the address nor the RPC URL (which may carry a key) is ever written or printed.
- USDG is the real Global Dollar contract only (6 decimals). Impostor tokens that also call
  themselves "USDG" are never read; the contract's decimals() is checked every run and a mismatch
  leaves usdg unmeasured.
- lp_mark_quote is the quote put in at mint (`quoteIn` / `wethIn` of the position journals) for
  positions with no successful close AND non-zero on-chain liquidity: a cost basis, not a price
  mark (`lp_basis` says so). A journal-open position with zero liquidity, or whose token no longer
  exists (the call reverts), is a ghost (closed outside the monitor): counted in lp_ghosts, not valued. A liquidity read that fails leaves that
  asset's lp_mark_quote null, never 0.
- status: "ok" when every figure was measured, "partial" when some are null, "unavailable" when
  no balance could be read. A null is unmeasured, never zero.
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from decimal import Decimal
from pathlib import Path

DEFAULT_RPC = 'https://rpc.mainnet.chain.robinhood.com'
WETH = '0x0bd7d308f8e1639fab988df18a8011f41eacad73'
USDG = '0x5fc5360d0400a0fd4f2af552add042d716f1d168'  # Global Dollar, 6 decimals; the only USDG read
USDG_DECIMALS = 6
NPM_V3 = '0x73991a25c818bf1f1128deaab1492d45638de0d3'  # Uniswap v3 NonfungiblePositionManager
POSM_V4 = '0x58daec3116aae6d93017baaea7749052e8a04fa7'  # Uniswap v4 PositionManager
SEL_BALANCE_OF = '0x70a08231'  # balanceOf(address)
SEL_DECIMALS = '0x313ce567'  # decimals()
SEL_V3_POSITIONS = '0x99fbab88'  # positions(uint256): word 7 is liquidity
SEL_V4_LIQUIDITY = '0x1efeed33'  # getPositionLiquidity(uint256)
ENV_KEYS = ('UNI_NAV_WALLET', 'KRYSTAL_WALLET', 'ROBINHOOD_RPC_URL')
QUOTE_ASSET = {'WETH': 'ETH', 'ETH': 'ETH', 'USDG': 'USDG'}
TIMEOUT_S = 10
BATCH = 50
REVERTED = 'reverted'  # an eth_call the node executed and the contract rejected (not a transport failure)


def profile_env(profile):
    """Only the allowlisted keys from <profile>/.env; the process environment wins."""
    out = {}
    try:
        text = (profile / '.env').read_text()
    except OSError:
        text = ''
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip().removeprefix('export ').strip()
        if k in ENV_KEYS:
            out[k] = v.strip().strip('"').strip("'")
    for k in ENV_KEYS:
        if os.environ.get(k):
            out[k] = os.environ[k]
    return out


def valid_address(a):
    return isinstance(a, str) and len(a) == 42 and a[:2].lower() == '0x' and all(c in '0123456789abcdefABCDEF' for c in a[2:])


def word(v):
    return format(int(v), '064x')


def addr_word(a):
    return a[2:].lower().rjust(64, '0')


class RPC:
    """JSON-RPC batch client. Errors are reduced to a short generic label: an exception text can
    carry the RPC URL, and that URL may carry a key."""

    def __init__(self, url, post=None):
        self.url, self.post = url, post or self._post

    def _post(self, payload):
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(), method='POST',
                                     headers={'Content-Type': 'application/json', 'User-Agent': 'azimuth-uni-nav'})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return json.loads(r.read(1 << 20))

    def batch(self, calls):
        """calls: [(method, params)] -> [result or None], in order."""
        out = []
        for i in range(0, len(calls), BATCH):
            chunk = calls[i:i + BATCH]
            payload = [{'jsonrpc': '2.0', 'id': j, 'method': m, 'params': p} for j, (m, p) in enumerate(chunk)]
            try:
                resp = self.post(payload)
            except Exception:
                out.extend([None] * len(chunk)); continue
            by_id = {r.get('id'): r for r in resp if isinstance(r, dict)} if isinstance(resp, list) else {}
            for j in range(len(chunk)):
                r = by_id.get(j) or {}
                err = r.get('error') if isinstance(r.get('error'), dict) else None
                if err is not None:
                    out.append(REVERTED if 'revert' in str(err.get('message', '')).lower() or err.get('code') == 3 else None)
                else:
                    out.append(r.get('result') if isinstance(r.get('result'), str) else None)
        return out


def hex_int(h):
    try:
        return int(h, 16) if isinstance(h, str) and h.startswith('0x') and len(h) > 2 else None
    except ValueError:
        return None


def units(raw, decimals):
    return None if raw is None else float(Decimal(raw) / (Decimal(10) ** decimals))


def read_jsonl(path):
    rows = []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    rows.append(r)
    except OSError:
        pass
    return rows


def key(row, proto):
    t = row.get('tokenId')
    return (row.get('protocol') or proto, str(t)) if isinstance(t, (str, int)) and str(t) else None


def open_positions(memory):
    """Journal-open positions: minted, with no successful non-dry-run close for the same (protocol, tokenId)."""
    minted = {}
    for name, proto in (('uni_positions.jsonl', 'v3'), ('uni_v4_positions.jsonl', 'v4')):
        for r in read_jsonl(memory / name):
            k = key(r, proto)
            if k:
                minted[k] = r
    done = {key(c, 'v3') for c in read_jsonl(memory / 'uni_closes.jsonl') if c.get('success') is True and not c.get('dry_run')}
    out = []
    for k, r in minted.items():
        if k in done:
            continue
        sym = r.get('quoteSymbol') or ('WETH' if r.get('wethIn') is not None else None)
        asset = QUOTE_ASSET.get(sym.upper()) if isinstance(sym, str) else None
        q = r.get('quoteIn') if r.get('quoteIn') is not None else r.get('wethIn')
        try:
            q = float(q)
        except (TypeError, ValueError):
            q = None
        out.append({'protocol': k[0], 'token_id': k[1], 'asset': asset, 'quote_in': q})
    return out


def liquidity_call(p):
    try:
        tid = int(p['token_id'])
    except ValueError:
        return None
    if p['protocol'] == 'v4':
        return ('eth_call', [{'to': POSM_V4, 'data': SEL_V4_LIQUIDITY + word(tid)}, 'latest'])
    return ('eth_call', [{'to': NPM_V3, 'data': SEL_V3_POSITIONS + word(tid)}, 'latest'])


def liquidity(p, result):
    # positions(tokenId) reverts for a burned v3 NFT ("Invalid token ID"): the position no longer exists.
    if result == REVERTED:
        return 0
    if not isinstance(result, str) or not result.startswith('0x'):
        return None
    body = result[2:]
    if p['protocol'] == 'v4':
        return hex_int('0x' + body[:64]) if len(body) >= 64 else None
    return hex_int('0x' + body[7 * 64:8 * 64]) if len(body) >= 8 * 64 else None


def snapshot(profile, rpc=None, now=None):
    env = profile_env(profile)
    wallet = env.get('UNI_NAV_WALLET') or env.get('KRYSTAL_WALLET')
    if not valid_address(wallet):
        return None
    rpc = rpc or RPC(env.get('ROBINHOOD_RPC_URL') or DEFAULT_RPC)
    errors = []
    base = [('eth_getBalance', [wallet, 'latest']),
            ('eth_call', [{'to': WETH, 'data': SEL_BALANCE_OF + addr_word(wallet)}, 'latest']),
            ('eth_call', [{'to': USDG, 'data': SEL_BALANCE_OF + addr_word(wallet)}, 'latest']),
            ('eth_call', [{'to': USDG, 'data': SEL_DECIMALS}, 'latest'])]
    positions = open_positions(profile / 'memories')
    calls = [(p, liquidity_call(p)) for p in positions]
    res = rpc.batch(base + [c for _, c in calls if c])
    eth_raw, weth_raw, usdg_raw, dec = (hex_int(x) if x != REVERTED else None for x in res[:4])
    for name, v in (('eth', eth_raw), ('weth', weth_raw), ('usdg', usdg_raw)):
        if v is None:
            errors.append(f'{name} balance unreadable')
    if dec is not None and dec != USDG_DECIMALS:
        usdg_raw = None; errors.append('USDG decimals mismatch')
    elif dec is None and usdg_raw is not None:
        usdg_raw = None; errors.append('USDG decimals unreadable')
    lp = {'ETH': 0.0, 'USDG': 0.0}; n = {'ETH': 0, 'USDG': 0}; ghosts = 0; unknown = 0
    it = iter(res[4:])
    for p, c in calls:
        liq = liquidity(p, next(it)) if c else None
        a = p['asset']
        if a is None:
            unknown += 1; continue
        if liq is None or p['quote_in'] is None:
            errors.append(f'{a} position unmeasured'); lp[a] = None; continue
        if liq == 0:
            ghosts += 1; continue
        n[a] += 1
        if lp[a] is not None:
            lp[a] += p['quote_in']
    eth, weth, usdg = units(eth_raw, 18), units(weth_raw, 18), units(usdg_raw, USDG_DECIMALS)
    measured = [eth, weth, usdg]
    status = ('unavailable' if all(v is None for v in measured)
              else 'ok' if None not in measured and None not in lp.values() else 'partial')
    return {'ts': int(now if now is not None else time.time()), 'eth': eth, 'weth': weth, 'usdg': usdg,
            'lp_mark_quote': lp, 'lp_positions': n, 'lp_ghosts': ghosts, 'lp_unknown_asset': unknown,
            'lp_basis': 'quote_in_at_mint', 'status': status, 'errors': sorted(set(errors))}


def append(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (json.dumps(row, separators=(',', ':')) + '\n').encode())
        os.fsync(fd)
    finally:
        os.close(fd)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Robinhood Chain wallet snapshot (read-only) into memories/uni_nav.jsonl')
    ap.add_argument('--profile', required=True, type=Path, help='Hermes profile directory')
    ap.add_argument('--out', type=Path, help='journal path (default <profile>/memories/uni_nav.jsonl)')
    ap.add_argument('--dry-run', action='store_true', help='print the row, write nothing')
    a = ap.parse_args(argv)
    row = snapshot(a.profile)
    if row is None:
        print('uni_nav: no public Robinhood wallet configured (UNI_NAV_WALLET or KRYSTAL_WALLET); nothing written', file=sys.stderr)
        return 2
    if a.dry_run:
        print(json.dumps(row))
        return 0
    append(a.out or a.profile / 'memories' / 'uni_nav.jsonl', row)
    print(f"uni_nav: {row['status']}" + (f" ({'; '.join(row['errors'])})" if row['errors'] else ''))
    return 0 if row['status'] != 'unavailable' else 1


if __name__ == '__main__':
    sys.exit(main())
