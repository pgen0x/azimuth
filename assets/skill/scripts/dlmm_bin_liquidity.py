"""Read-only Meteora DLMM bin liquidity over keyless Solana JSON-RPC.

No key, no wallet, no transaction, no node/SDK: bin-array PDAs are derived here
(sha256 + an ed25519 on-curve check) and the accounts are decoded by layout.

BinArray account (10136 bytes): 8 discriminator | i64 index | u8 version |
7 pad | 32 lb_pair | 70 x Bin(144): u64 amount_x, u64 amount_y, u128 price,
u128 liquidity_supply, 2 x u128 reward, 2 x u128 fee/token, 2 x u128 amount_in.
Bin b lives in array floor(b / 70); its price is (1 + step/1e4)^b in raw units,
human = raw * 10^(dec_x - dec_y). An array that was never initialized holds no
liquidity.
"""
import base64
import hashlib
import json
import math
import struct
import urllib.error
import urllib.request

PROGRAM = "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"
PUBLIC_RPC = "https://api.mainnet-beta.solana.com"
BINS_PER_ARRAY = 70
BIN_SIZE = 144
HEADER = 56
ARRAY_LEN = HEADER + BINS_PER_ARRAY * BIN_SIZE
MAX_KEYS = 100  # getMultipleAccounts limit

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_P = 2 ** 255 - 19
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)


def b58decode(s):
    n = 0
    for ch in s:
        n = n * 58 + _B58.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\0" * (len(s) - len(s.lstrip("1"))) + raw


def b58encode(b):
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + out


def on_curve(b):
    """True if 32 bytes decode to an ed25519 point (PDAs must not)."""
    y = int.from_bytes(b, "little") & ((1 << 255) - 1)
    if y >= _P:
        return False
    u, v = (y * y - 1) % _P, (_D * y * y + 1) % _P
    x2 = u * pow(v, _P - 2, _P) % _P
    if x2 == 0:
        return True
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P == 0:
        return True
    x = x * _SQRT_M1 % _P
    return (x * x - x2) % _P == 0


def find_pda(seeds, program=PROGRAM):
    pid = b58decode(program)
    for bump in range(255, -1, -1):
        h = hashlib.sha256(b"".join(seeds) + bytes([bump]) + pid + b"ProgramDerivedAddress").digest()
        if not on_curve(h):
            return b58encode(h)
    raise ValueError("no PDA")


def bin_array_key(pool, index):
    return find_pda([b"bin_array", b58decode(pool), struct.pack("<q", index)])


def bin_id_for(price, bin_step, dec_x, dec_y):
    """Nearest bin id for a human price (Y per X)."""
    return round(math.log(price * 10 ** (dec_y - dec_x)) / math.log1p(bin_step / 1e4))


def bin_price(bin_id, bin_step, dec_x, dec_y):
    return (1 + bin_step / 1e4) ** bin_id * 10 ** (dec_x - dec_y)


def decode_array(data, pool, bin_step, dec_x, dec_y):
    """{bin_id: value in Y} for one bin array; raises on a foreign account."""
    if len(data) < ARRAY_LEN:
        raise ValueError("short bin array")
    index = struct.unpack_from("<q", data, 8)[0]
    if b58encode(data[24:56]) != pool:
        raise ValueError("bin array of another pair")
    out = {}
    for j in range(BINS_PER_ARRAY):
        ax, ay = struct.unpack_from("<QQ", data, HEADER + j * BIN_SIZE)
        if ax or ay:
            b = index * BINS_PER_ARRAY + j
            out[b] = ax / 10 ** dec_x * bin_price(b, bin_step, dec_x, dec_y) + ay / 10 ** dec_y
    return out


class BinReader:
    """Reads pool liquidity per bin around a price. `gate` paces calls (shared
    Gate from grad_paper); `opener` is injectable for tests."""

    def __init__(self, gate, rpc_url=PUBLIC_RPC, opener=urllib.request.urlopen, timeout=25):
        self.gate, self.rpc_url, self.opener, self.timeout = gate, rpc_url, opener, timeout
        self.keys = {}
        self.calls = self.failures = 0

    def _key(self, pool, index):
        k = (pool, index)
        if k not in self.keys:
            self.keys[k] = bin_array_key(pool, index)
        return self.keys[k]

    def _rpc(self, method, params):
        self.gate.acquire()
        self.calls += 1
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        req = urllib.request.Request(self.rpc_url, body, {"content-type": "application/json",
                                                          "User-Agent": "research-client"})
        try:
            with self.opener(req, timeout=self.timeout) as resp:
                doc = json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                self.gate.penalize()
            return None
        except (urllib.error.URLError, OSError, ValueError):
            return None
        if "result" not in doc:
            return None
        self.gate.ok()
        return doc["result"]

    def liquidity(self, pool, price, bin_step, dec_x, dec_y, span=0.21):
        """{bin_id: Y value} for bins within +-span of price, or None on any failure."""
        try:
            center = bin_id_for(price, bin_step, dec_x, dec_y)
            k = math.ceil(math.log1p(span) / math.log1p(bin_step / 1e4))
        except (ValueError, ZeroDivisionError):
            return None
        lo_i, hi_i = (center - k) // BINS_PER_ARRAY, (center + k) // BINS_PER_ARRAY
        indices = list(range(lo_i, hi_i + 1))
        out = {}
        for start in range(0, len(indices), MAX_KEYS):
            chunk = indices[start:start + MAX_KEYS]
            res = self._rpc("getMultipleAccounts",
                            [[self._key(pool, i) for i in chunk], {"encoding": "base64", "commitment": "confirmed"}])
            values = (res or {}).get("value") if isinstance(res, dict) else None
            if not isinstance(values, list) or len(values) != len(chunk):
                self.failures += 1
                return None
            for acct in values:
                if acct is None:
                    continue  # never initialized: no liquidity there
                try:
                    if acct.get("owner") != PROGRAM:
                        raise ValueError("owner")
                    out.update(decode_array(base64.b64decode(acct["data"][0]), pool, bin_step, dec_x, dec_y))
                except (ValueError, KeyError, TypeError, IndexError, struct.error):
                    self.failures += 1
                    return None
        return {"center": center, "lo": center - k, "hi": center + k, "liq": out}


def bin_fee_share(candles, liq, our_lo, our_hi, our_per_bin, bin_step, dec_x, dec_y, p_start):
    """Our share of the hour's pool fees from bin liquidity.

    For each 5m candle the traded bins are those between its low and high;
    our share is our liquidity over all liquidity in those bins (pool + ours where
    we sit), so bins outside our range dilute it and empty bins add nothing.
    Candles are weighted by volume (equal weights if none has volume). With no
    candle the price sat in the bin of p_start all hour. Returns None if the
    traded bins fall outside the snapshot.
    """
    spans, weights = [], []
    for c in candles or [{"low": p_start, "high": p_start, "volume": 1.0}]:
        a = bin_id_for(min(c["low"], c["high"]), bin_step, dec_x, dec_y)
        b = bin_id_for(max(c["low"], c["high"]), bin_step, dec_x, dec_y)
        spans.append((a, b))
        weights.append(max(0.0, c.get("volume") or 0.0))
    if sum(weights) <= 0:
        weights = [1.0] * len(spans)
    total_w = sum(weights)
    share = 0.0
    for (a, b), w in zip(spans, weights):
        if a < liq["lo"] or b > liq["hi"]:
            return None
        ours = theirs = 0.0
        for bid in range(a, b + 1):
            mine = our_per_bin if our_lo <= bid <= our_hi else 0.0
            ours += mine
            theirs += liq["liq"].get(bid, 0.0) + mine
        share += w / total_w * (ours / theirs if theirs > 0 else 0.0)
    return share
