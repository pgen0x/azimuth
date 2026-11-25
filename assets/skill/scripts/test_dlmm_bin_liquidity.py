"""Bin liquidity reader: PDAs, account decode, fee share, RPC failure handling."""
import base64
import io
import json
import struct
import unittest

import dlmm_bin_liquidity as bl
import grad_paper as gp

POOL = "5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6"


def array_bytes(index, amounts, pool=POOL):
    """A synthetic BinArray: amounts = {slot: (raw_x, raw_y)}."""
    data = bytearray(bl.ARRAY_LEN)
    struct.pack_into("<q", data, 8, index)
    data[24:56] = bl.b58decode(pool)
    for slot, (ax, ay) in amounts.items():
        struct.pack_into("<QQ", data, bl.HEADER + slot * bl.BIN_SIZE, ax, ay)
    return bytes(data)


class FakeRPC:
    def __init__(self, arrays, fail=False):
        self.arrays, self.fail, self.calls = arrays, fail, []

    def __call__(self, req, timeout):
        body = json.loads(req.data)
        self.calls.append(body)
        if self.fail:
            raise OSError("down")
        keys = body["params"][0]
        lookup = {bl.bin_array_key(POOL, i): i for i in self.arrays}
        value = []
        for k in keys:
            i = lookup.get(k)
            value.append(None if i is None else {"owner": bl.PROGRAM,
                         "data": [base64.b64encode(self.arrays[i]).decode(), "base64"]})
        return io.BytesIO(json.dumps({"result": {"context": {"slot": 1}, "value": value}}).encode())


def gate():
    return gp.Gate(6000, clock=lambda: 0.0, sleep=lambda s: None)


class PdaTests(unittest.TestCase):
    def test_known_mainnet_bin_array_addresses(self):
        # verified against mainnet on 2026-11-25 (owner = DLMM program, lb_pair = pool)
        self.assertEqual(bl.bin_array_key(POOL, -96), "3MbEJY4VafKhxPmufcdqd22isGPERwvJuWJmqTqTzwXk")
        self.assertEqual(bl.bin_array_key(POOL, -97), "C48nHgzJBNKYqPUuf1fCMpK4yBKR6MXWVG5EJuqywLDh")

    def test_base58_round_trip(self):
        self.assertEqual(bl.b58encode(bl.b58decode(POOL)), POOL)
        self.assertEqual(bl.b58encode(bl.b58decode("1112")), "1112")


class DecodeTests(unittest.TestCase):
    def test_values_bins_in_quote(self):
        # bin step 100, decimals 0/0: bin 70 is array 1 slot 0, price 1.01^70
        data = array_bytes(1, {0: (2, 0), 1: (0, 5)})
        out = bl.decode_array(data, POOL, 100, 0, 0)
        self.assertAlmostEqual(out[70], 2 * 1.01 ** 70)
        self.assertAlmostEqual(out[71], 5.0)
        self.assertEqual(len(out), 2)

    def test_negative_ids_and_foreign_pair(self):
        out = bl.decode_array(array_bytes(-1, {69: (0, 7)}), POOL, 4, 9, 6)
        self.assertIn(-1, out)
        with self.assertRaises(ValueError):
            bl.decode_array(array_bytes(0, {}, pool="11111111111111111111111111111111"), POOL, 4, 9, 6)

    def test_price_and_bin_id_agree_with_decimals(self):
        b = bl.bin_id_for(68.875, 4, 9, 6)
        self.assertEqual(b, -6690)  # SOL-USDC/4 live active bin on 2026-11-25
        self.assertAlmostEqual(bl.bin_price(b, 4, 9, 6), 68.875, delta=0.03)


class ReaderTests(unittest.TestCase):
    def test_reads_arrays_around_price_and_treats_missing_as_empty(self):
        rpc = FakeRPC({0: array_bytes(0, {10: (0, 100)})})
        r = bl.BinReader(gate(), opener=rpc).liquidity(POOL, 1.01 ** 10, 100, 0, 0, span=0.5)
        self.assertEqual(r["center"], 10)
        self.assertEqual(r["liq"], {10: 100.0})
        self.assertEqual(len(rpc.calls), 1)
        self.assertGreater(len(rpc.calls[0]["params"][0]), 1)  # neighbours requested, absent ones empty

    def test_rpc_failure_returns_none(self):
        reader = bl.BinReader(gate(), opener=FakeRPC({}, fail=True))
        self.assertIsNone(reader.liquidity(POOL, 1.0, 100, 0, 0))
        self.assertEqual(reader.failures, 1)


def liq_book(center=0, lo=-50, hi=50, per_bin=100.0):
    return {"center": center, "lo": lo, "hi": hi, "liq": {b: per_bin for b in range(lo, hi + 1)}}


def cndl(low, high, vol=1.0):
    return {"low": low, "high": high, "volume": vol}


class FeeShareTests(unittest.TestCase):
    def share(self, candles, our_lo, our_hi, ours, book=None):
        return bl.bin_fee_share(candles, book or liq_book(), our_lo, our_hi, ours, 100, 0, 0, 1.0)

    def test_in_range_share_is_ours_over_all_liquidity(self):
        s = self.share([cndl(1.0, 1.0)], -5, 5, 10.0)
        self.assertAlmostEqual(s, 10.0 / 110.0)

    def test_traded_bins_outside_our_range_dilute(self):
        s = self.share([cndl(1.0, 1.01 ** 9)], -5, 5, 10.0)  # bins 0..9, we hold 0..5
        self.assertAlmostEqual(s, 6 * 10.0 / (10 * 100.0 + 6 * 10.0))
        self.assertEqual(self.share([cndl(1.01 ** 20, 1.01 ** 21)], -5, 5, 10.0), 0.0)

    def test_narrow_earns_more_per_in_range_hour_than_wide(self):
        value = 110.0  # same notional, spread over 11 vs 21 bins
        narrow = self.share([cndl(1.0, 1.01 ** 2)], -5, 5, value / 11)
        wide = self.share([cndl(1.0, 1.01 ** 2)], -10, 10, value / 21)
        self.assertGreater(narrow, wide)
        self.assertAlmostEqual(narrow / wide, (10 / 110) / (110 / 21 / (100 + 110 / 21)), places=6)

    def test_volume_weights_candles_and_empty_bins_add_nothing(self):
        book = liq_book()
        book["liq"].pop(3)
        s = self.share([cndl(1.01 ** 3, 1.01 ** 3, vol=3.0), cndl(1.0, 1.0, vol=1.0)], -5, 5, 10.0, book)
        self.assertAlmostEqual(s, 0.75 * 1.0 + 0.25 * 10.0 / 110.0)

    def test_quiet_hour_uses_the_start_bin_and_outside_snapshot_is_none(self):
        self.assertAlmostEqual(self.share([], -5, 5, 10.0), 10.0 / 110.0)
        self.assertIsNone(self.share([cndl(1.01 ** 60, 1.01 ** 61)], -5, 5, 10.0))


if __name__ == "__main__":
    unittest.main()
