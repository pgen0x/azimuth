#!/usr/bin/env python3
"""Wallet-cash basis (dlmm_realized_cash.py) over synthetic jsonParsed transactions.

Offline: every address, amount and signature below is made up. Run:
  python3 assets/skill/scripts/test_dlmm_realized_cash.py
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlmm_realized as realized  # noqa: E402
import dlmm_realized_cash as cash  # noqa: E402

WALLET, POSITION, RESERVE, ATA, WSOL_ATA, ROUTER = (
    "WalletSynthetic", "PositionSynthetic", "PoolReserveSynthetic",
    "TokenAtaSynthetic", "WsolAtaSynthetic", "RouterSynthetic")
MINT = "MintSynthetic"
ATA_RENT = 2_039_280
POS_RENT = 40_000_000
TOKENS = 1_000_000
SOL = 1_000_000_000


def tok(index, amount, mint=MINT, owner=WALLET):
    return {"accountIndex": index, "mint": mint, "owner": owner,
            "uiTokenAmount": {"amount": str(amount)}}


def tx(keys, pre, post, fee=5000, pre_tok=(), post_tok=(), err=None):
    return {"slot": 1, "blockTime": 1,
            "transaction": {"message": {"accountKeys": [
                {"pubkey": k, "signer": i == 0, "writable": True} for i, k in enumerate(keys)]}},
            "meta": {"err": err, "fee": fee, "preBalances": list(pre), "postBalances": list(post),
                     "preTokenBalances": list(pre_tok), "postTokenBalances": list(post_tok)}}


def close_tx(sol_out=80_000_000, tokens=TOKENS, fee=5000):
    """Close: SOL arrives via a temp WSOL account (absent from token lists),
    the position account's rent comes back, tokens land in an existing ATA."""
    keys = [WALLET, POSITION, RESERVE, ATA]
    pre = [SOL, POS_RENT, 500 * SOL, ATA_RENT]
    post = [SOL + sol_out + POS_RENT - fee, 0, 500 * SOL - sol_out, ATA_RENT]
    pre_tok = [tok(3, 0)] if tokens else []
    post_tok = [tok(3, tokens)] if tokens else []
    return tx(keys, pre, post, fee, pre_tok, post_tok)


def swap_tx(sold=TOKENS, held=TOKENS, proceeds=150_000_000, fee=5280, err=None):
    """Jupiter-style sale: tokens leave the ATA, SOL lands natively; a full sale
    also closes the ATA, whose rent refund must not count as proceeds."""
    keys = [WALLET, ATA, ROUTER]
    if err:
        return tx(keys, [SOL, ATA_RENT, SOL], [SOL - fee, ATA_RENT, SOL], fee,
                  [tok(1, held)], [tok(1, held)], err=err)
    closed = sold == held
    post_wallet = SOL + proceeds + (ATA_RENT if closed else 0) - fee
    return tx(keys, [SOL, ATA_RENT, 9 * SOL], [post_wallet, 0 if closed else ATA_RENT, 9 * SOL - proceeds],
              fee, [tok(1, held)], [] if closed else [tok(1, held - sold)])


def ev(kind, sig, position=POSITION):
    return {"ts": 1, "wallet": WALLET, "position": position, "kind": kind, "signature": sig}


ROW = {"position": POSITION, "pool": "PoolSynthetic", "pair": "SYN-SOL", "closed_at": 1000,
       "deposit_sol": 0.25, "withdrawal_sol": 0.21, "fee_sol": 0.03,
       "realized_sol": -0.01, "realized_pct": -4.0, "fetched_at": 1000}


class TxFlowsTests(unittest.TestCase):
    def test_close_separates_rent_refund_and_fee(self):
        f = cash.tx_flows(close_tx(), WALLET, POSITION)
        self.assertEqual(f["cash_lamports"], 80_000_000)
        self.assertEqual(f["position_rent_refund_lamports"], POS_RENT)
        self.assertEqual(f["fee_lamports"], 5000)
        self.assertEqual(f["token_deltas_raw"], {MINT: TOKENS})
        self.assertTrue(f["position_closed"])

    def test_persistent_wsol_account_counts_as_sol(self):
        # Proceeds land in a pre-existing WSOL account, not natively.
        keys = [WALLET, ATA, WSOL_ATA]
        wsol = cash.WSOL
        t = tx(keys, [SOL, ATA_RENT, ATA_RENT + 5], [SOL - 5000, ATA_RENT, ATA_RENT + 5 + 7_000_000],
               5000, [tok(1, 10), tok(2, 5, wsol)], [tok(1, 0), tok(2, 7_000_005, wsol)])
        f = cash.tx_flows(t, WALLET)
        self.assertEqual((f["cash_lamports"], f["token_account_rent_lamports"]), (7_000_000, 0))
        self.assertEqual(f["token_deltas_raw"], {MINT: -10})

    def test_new_token_account_rent_is_a_reserve_not_a_cost(self):
        keys = [WALLET, POSITION, RESERVE, ATA]
        t = tx(keys, [SOL, POS_RENT, SOL, 0], [SOL + 1000 + POS_RENT - ATA_RENT - 5000, 0, SOL - 1000, ATA_RENT],
               5000, [], [tok(3, 7)])
        f = cash.tx_flows(t, WALLET, POSITION)
        self.assertEqual((f["cash_lamports"], f["token_account_rent_lamports"]), (1000, ATA_RENT))

    def test_missing_or_foreign_tx_is_none(self):
        self.assertIsNone(cash.tx_flows(None, WALLET))
        self.assertIsNone(cash.tx_flows(close_tx(), "SomeoneElse"))


class PositionCashTests(unittest.TestCase):
    def test_close_plus_full_swap_is_wallet_basis(self):
        events = [ev("close", "sigClose"), ev("swap", "sigSwap"), ev("close", "sigClose")]
        rec = cash.position_cash(ROW, events, {"sigClose": close_tx(), "sigSwap": swap_tx()}, now=2000)
        self.assertEqual(rec["cash_basis"], "wallet")
        self.assertAlmostEqual(rec["cash_close_sol"], 0.08)
        self.assertAlmostEqual(rec["cash_swap_sol"], 0.15)
        self.assertAlmostEqual(rec["cash_out_sol"], 0.23)
        self.assertAlmostEqual(rec["cash_realized_sol"], -0.02)
        self.assertAlmostEqual(rec["cash_realized_pct"], -8.0)
        self.assertAlmostEqual(rec["swap_gap_sol"], 0.01)  # 0.21 + 0.03 - 0.23
        # Fees and rent stay out of the cash figures, reported on their own.
        self.assertAlmostEqual(rec["tx_fee_sol"], 10_280 / 1e9)
        self.assertAlmostEqual(rec["position_rent_refund_sol"], POS_RENT / 1e9)
        self.assertAlmostEqual(rec["token_account_rent_net_sol"], -ATA_RENT / 1e9)
        self.assertEqual((rec["token_out_raw"], rec["token_sold_raw"]), (str(TOKENS), str(TOKENS)))
        self.assertEqual(rec["close_signatures"], ["sigClose"])  # duplicate journal row counted once

    def test_failed_swap_retry_costs_only_its_fee(self):
        events = [ev("close", "c"), ev("swap", "bad"), ev("swap", "lost"), ev("swap", "good")]
        txs = {"c": close_tx(), "bad": swap_tx(err={"InstructionError": [0, "x"]}), "lost": None,
               "good": swap_tx()}
        rec = cash.position_cash(ROW, events, txs)
        self.assertEqual(rec["cash_basis"], "wallet")
        self.assertAlmostEqual(rec["cash_out_sol"], 0.23)
        self.assertAlmostEqual(rec["tx_fee_sol"], (5000 + 5280 + 5280) / 1e9)
        self.assertEqual(rec["swap_signatures"], ["good"])

    def test_close_with_no_token_side_needs_no_swap(self):
        rec = cash.position_cash(ROW, [ev("close", "c")], {"c": close_tx(sol_out=240_000_000, tokens=0)})
        self.assertEqual(rec["cash_basis"], "wallet")
        self.assertIsNone(rec["cash_swap_sol"])
        self.assertAlmostEqual(rec["cash_out_sol"], 0.24)
        self.assertAlmostEqual(rec["cash_realized_sol"], -0.01)
        self.assertAlmostEqual(rec["swap_gap_sol"], 0.0)
        self.assertEqual(rec["token_out_raw"], "0")

    def test_unlinked_swap_is_unmeasured_not_zero(self):
        for events, txs in (([ev("close", "c")], {"c": close_tx()}),
                            ([ev("close", "c"), ev("swap", "s")], {"c": close_tx(), "s": None})):
            rec = cash.position_cash(ROW, events, txs)
            self.assertEqual((rec["cash_basis"], rec["cash_reason"]), ("unlinked", "swap_unlinked"))
            for key in ("cash_out_sol", "cash_realized_sol", "cash_realized_pct", "swap_gap_sol"):
                self.assertIsNone(rec[key], key)
            self.assertAlmostEqual(rec["cash_close_sol"], 0.08)  # the measured part is still shown

    def test_unproven_close_is_unlinked(self):
        rec = cash.position_cash(ROW, [ev("close", "c")], {"c": None})
        self.assertEqual((rec["cash_basis"], rec["cash_reason"]), ("unlinked", "close_unproven"))
        rec = cash.position_cash(ROW, [ev("swap", "s")], {"s": swap_tx()})
        self.assertEqual((rec["cash_basis"], rec["cash_reason"]), ("unlinked", "close_not_journaled"))

    def test_partial_sale_is_partial_and_unmeasured(self):
        events = [ev("close", "c"), ev("swap", "s")]
        rec = cash.position_cash(ROW, events, {"c": close_tx(), "s": swap_tx(sold=600_000)})
        self.assertEqual((rec["cash_basis"], rec["cash_reason"]), ("partial", "partial_sale"))
        self.assertEqual((rec["token_out_raw"], rec["token_sold_raw"]), (str(TOKENS), "600000"))
        self.assertIsNone(rec["cash_out_sol"])
        self.assertIsNone(rec["cash_realized_sol"])
        self.assertAlmostEqual(rec["cash_swap_sol"], 0.15)
        # Selling more than the position paid out mixes in other inventory.
        rec = cash.position_cash(ROW, events, {"c": close_tx(tokens=500_000), "s": swap_tx()})
        self.assertEqual((rec["cash_basis"], rec["cash_reason"]), ("partial", "sold_beyond_position"))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mem = Path(self.tmp.name)
        self.realized = self.mem / "dlmm_realized.jsonl"
        self.realized.write_text(json.dumps(ROW) + "\n")
        (self.mem / "dlmm_transactions.jsonl").write_text(
            "\n".join(json.dumps(e) for e in [ev("deploy", "d"), ev("close", "c"), ev("swap", "s")]) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def reconcile(self, txs):
        calls = []

        def fetch(sig):
            calls.append(sig)
            return txs.get(sig)
        with contextlib.redirect_stdout(io.StringIO()):
            cash.reconcile(str(self.realized), days=7, fetch=fetch, now=2000)
        return calls

    def test_reconcile_retries_until_wallet_then_stops(self):
        self.assertEqual(self.reconcile({"c": close_tx()}), ["c", "s"])  # deploy is never fetched
        got = realized.load_cash(realized.cash_path_for(str(self.realized)))
        self.assertEqual(got[POSITION]["cash_basis"], "unlinked")
        self.reconcile({"c": close_tx()})  # unchanged: no duplicate line
        self.assertEqual(len((self.mem / "dlmm_realized_cash.jsonl").read_text().splitlines()), 1)
        self.reconcile({"c": close_tx(), "s": swap_tx()})
        got = realized.load_cash(realized.cash_path_for(str(self.realized)))
        self.assertEqual(got[POSITION]["cash_basis"], "wallet")
        self.assertEqual(self.reconcile({}), [])  # settled rows are not refetched

    def test_fetch_failure_leaves_row_unmeasured(self):
        def boom(sig):
            raise OSError("rpc down")
        with contextlib.redirect_stdout(io.StringIO()):
            cash.reconcile(str(self.realized), days=7, fetch=boom, now=2000)
        self.assertEqual(realized.load_cash(realized.cash_path_for(str(self.realized))), {})

    def test_apply_realized_default_unchanged_and_cash_opt_in(self):
        self.reconcile({"c": close_tx(), "s": swap_tx()})
        default = realized.apply_realized([{"position": POSITION, "pnl_sol": 9}], str(self.realized))[0]
        self.assertEqual((default["pnl_sol"], default["pnl_basis"]), (-0.01, "realized"))
        self.assertAlmostEqual(default["cash_realized_sol"], -0.02)  # both figures available
        self.assertEqual(default["cash_basis"], "wallet")
        opted = realized.apply_realized([{"position": POSITION, "pnl_sol": 9}], str(self.realized), basis="cash")[0]
        self.assertAlmostEqual(opted["pnl_sol"], -0.02)
        self.assertEqual(opted["pnl_basis"], "cash")
        with self.assertRaises(ValueError):
            realized.apply_realized([], str(self.realized), basis="bogus")

    def test_cash_opt_in_without_link_is_unmeasured(self):
        self.reconcile({"c": close_tx()})
        rec = realized.apply_realized([{"position": POSITION, "pnl_sol": 9}], str(self.realized), basis="cash")[0]
        self.assertEqual((rec["pnl_sol"], rec["pnl_pct"], rec["pnl_basis"]), (None, None, "cash_unmeasured"))
        # No cash file at all: default consumers see no cash fields, not zeros.
        os.remove(self.mem / "dlmm_realized_cash.jsonl")
        rec = realized.apply_realized([{"position": POSITION}], str(self.realized))[0]
        self.assertNotIn("cash_realized_sol", rec)

    def test_isolated_module_load_needs_no_sibling(self):
        # The dashboard loads dlmm_realized.py by file path without the scripts
        # dir on sys.path; the cash merge must not import a sibling module.
        self.reconcile({"c": close_tx(), "s": swap_tx()})
        here = Path(realized.__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("isolated_realized", realized.__file__)
        module = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, "path", [p for p in sys.path if Path(p or ".").resolve() != here]), \
                mock.patch.dict(sys.modules, {k: v for k, v in sys.modules.items() if not k.startswith("dlmm_")},
                                clear=True):
            spec.loader.exec_module(module)
            rec = module.apply_realized([{"position": POSITION}], path=str(self.realized))[0]
        self.assertEqual(rec["cash_basis"], "wallet")

    def test_weights_cash_basis_is_opt_in(self):
        import dlmm_weights as weights
        self.reconcile({"c": close_tx(), "s": swap_tx()})
        records = {POSITION: {"position": POSITION, "signal": {"score": 1}, "mode": "pulse"},
                   "Unlinked": {"position": "Unlinked", "signal": {"score": 1}}}
        with mock.patch.object(weights, "REALIZED_PATH", str(self.realized)):
            got = weights.wallet_cash_closes(records)
        self.assertEqual([r["position"] for r in got], [POSITION])
        self.assertEqual(got[0]["outcome_basis"], weights.WALLET_CASH_BASIS)
        self.assertAlmostEqual(weights.outcome_sol(got[0]), -0.02)
        self.assertIsNone(weights.outcome_sol({**got[0], "cash_pnl_upper_sol": 0.1}))
        self.assertIsNone(weights.outcome_sol({**got[0], "cash_pnl_lower_sol": None, "cash_pnl_upper_sol": None}))
        # The default path never reads the cash file.
        closes = self.mem / "closes.jsonl"
        closes.write_text(json.dumps({"position": POSITION, "signal": {"score": 1}, "ts": 9e12}) + "\n")
        with mock.patch.object(weights, "wallet_cash_closes") as wallet, \
                mock.patch.object(weights, "CLOSES_PATH", str(closes)), \
                mock.patch.object(weights, "report", return_value={"chains": [], "rent_refund_groups": []}):
            self.assertEqual(weights.load_recent_closes(), [])
            wallet.assert_not_called()
            weights.load_recent_closes(cash_basis=True)
            wallet.assert_called_once()

    def test_scoreboard_and_brief_show_both(self):
        import dlmm_stats as stats
        self.reconcile({"c": close_tx(), "s": swap_tx()})
        closes = realized.apply_realized([{"position": POSITION, "mode": "pulse", "pnl_sol": 9, "age_min": 5},
                                          {"position": "Other", "mode": "pulse", "pnl_sol": .1, "age_min": 5,
                                           "pnl_basis": "realized"}], str(self.realized))
        with mock.patch.object(stats, "load_closes", return_value=closes), \
                mock.patch.object(stats, "load_realized", return_value={}), \
                mock.patch.object(stats, "redis_keys", return_value=[]), \
                mock.patch.object(stats, "redis_scard", return_value=0), \
                mock.patch.object(stats, "accounting_report", return_value={"rent_refund_groups": []}):
            card = stats.build_card(24)
            self.assertIn("Wallet cash PnL (swap proceeds) | -0.0200 SOL over 1/2", card)
            self.assertIn("LP PnL on same closes -0.0100", card)
            with mock.patch.object(stats, "load_closes", return_value=[{"pnl_sol": .1, "pnl_basis": "realized"}]):
                self.assertIn("Wallet cash PnL (swap proceeds) | Unmeasured", stats.build_card(24))

        brief_path = Path(__file__).resolve().parents[2] / "hermes/scripts/sol_dlmm_proposal_brief.py"
        spec = importlib.util.spec_from_file_location("brief_cash", brief_path)
        brief = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(brief)
        closes_path = self.mem / "dlmm_closes.jsonl"
        closes_path.write_text(json.dumps({"position": POSITION, "mode": "pulse", "pnl_sol": 9, "ts": 1990}) + "\n")
        out = io.StringIO()
        with mock.patch.object(brief, "CLOSES_PATH", str(closes_path)), \
                mock.patch.object(brief, "REALIZED_PATH", str(self.realized)), \
                mock.patch.object(brief, "CASH_PATH", str(self.mem / "dlmm_realized_cash.jsonl")), \
                mock.patch.object(brief.time, "time", return_value=2000), contextlib.redirect_stdout(out):
            brief.section_modes(brief.load_closes())
        text = out.getvalue()
        self.assertIn("Wallet cash basis: 1/1", text)
        self.assertIn("| -0.0100 | -0.0200 (1) |", text)


if __name__ == "__main__":
    unittest.main()
