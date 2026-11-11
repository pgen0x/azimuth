#!/usr/bin/env python3
"""Wallet-cash basis for closed Solana DLMM positions: what the wallet actually got.

WHY THIS EXISTS. `dlmm_realized.jsonl` takes deposit / withdrawal / fee flows
from the Meteora datapi. The withdrawal values the token side of a close at a
price. When the monitor then sells that token through Jupiter, the SOL that
lands can be well below that price — thin pools and dump exits worst of all —
so `realized_sol` overstates wallet cash, and every consumer inherits it.

This pass joins each closed position to the finalized transactions the executor
already journaled for it (`dlmm_transactions.jsonl`: `claim`/`close` by
position, and the settlement `swap`, which carries the position through
DLMM_SETTLEMENT_POSITION), reads them over read-only RPC, and writes

  memories/dlmm_realized_cash.jsonl   one line per position, append-only;
                                      a later line supersedes an earlier one

with these fields (SOL unless the name says raw):

  cash_close_sol        SOL the claim/close txs paid the wallet, gross of tx fees,
                        excluding the position-account rent refund
  cash_swap_sol         SOL the settlement swap(s) paid for the position's tokens
  cash_out_sol          cash_close_sol + cash_swap_sol
  cash_realized_sol     cash_out_sol - deposit_sol (datapi deposit)
  swap_gap_sol          (withdrawal_sol + fee_sol) - cash_out_sol; positive means
                        the datapi row overstated the cash that came back
  tx_fee_sol            network fees of every journaled tx (failed ones too) —
                        NOT netted into the figures above
  position_rent_refund_sol   position-account rent returned at close — NOT netted
  token_account_rent_net_sol rent moved INTO wallet token accounts (negative =
                        refunded, e.g. a sold token's ATA closed) — NOT netted
  cash_basis            "wallet"   every figure measured: close proven on chain,
                                   and the swaps sold exactly the tokens the
                                   position paid out (or it paid out none)
                        "partial"  linked, but the token side does not balance
                                   (sold less, or sold more than the position paid)
                        "unlinked" no proven close, or tokens paid out and no
                                   landed swap
  Only "wallet" rows carry cash_out_sol / cash_realized_sol / swap_gap_sol.
  Anything else is unmeasured — None, never 0.0.

Read-only: getTransaction only, no signing, no wallet file. The wallet comes from
the journal events themselves.

Usage (normally via `dlmm_realized.py --cash`):
  python3 dlmm_realized_cash.py --days 7
"""
import argparse
import json
import os
import time
import urllib.request

import dlmm_realized as realized_mod
from dlmm_realized import cash_path_for, load_cash

WSOL = "So11111111111111111111111111111111111111112"
LAMPORTS = 1e9
CLOSE_KINDS = ("claim", "close")
SWAP_KIND = "swap"
# Per-run RPC budget: unlinked rows are retried every run, so bound the cost.
DEFAULT_MAX_TX = 60


def _keys(tx):
    return [k["pubkey"] if isinstance(k, dict) else k
            for k in tx["transaction"]["message"]["accountKeys"]]


def tx_flows(tx, wallet, position=None):
    """Wallet-perspective flows of one finalized jsonParsed transaction.

    Returns None when the tx is missing or does not involve the wallet. Lamport
    arithmetic is integral. `cash_lamports` is trading cash only:

      native delta + fee                    (gross of the network fee)
      + wallet WSOL token-amount delta      (persistent WSOL accounts)
      + rent delta of wallet token accounts (rent is a reserve, not trading cash)
      - position-account rent refund
    A temporary WSOL account created and closed inside the tx is in neither
    token-balance list, so its round trip is already inside the native delta.
    """
    if not tx or not tx.get("meta") or not tx.get("transaction"):
        return None
    meta = tx["meta"]
    keys = _keys(tx)
    if wallet not in keys:
        return None
    i = keys.index(wallet)
    pre, post = meta["preBalances"], meta["postBalances"]
    fee = int(meta.get("fee") or 0) if i == 0 else 0
    failed = meta.get("err") is not None
    out = {"failed": failed, "fee_lamports": fee, "cash_lamports": 0,
           "position_rent_refund_lamports": 0, "token_account_rent_lamports": 0,
           "token_deltas_raw": {}, "position_closed": False}
    if failed:
        return out

    rows = {}
    for side, balances in (("pre", meta.get("preTokenBalances") or []),
                           ("post", meta.get("postTokenBalances") or [])):
        for t in balances:
            if t.get("owner") == wallet:
                rows.setdefault(t["accountIndex"], {})[side] = t
    wsol_delta = rent_delta = 0
    deltas = {}
    for n, sides in rows.items():
        mint = (sides.get("post") or sides.get("pre"))["mint"]
        amt = {s: int(sides[s]["uiTokenAmount"]["amount"]) if s in sides else 0 for s in ("pre", "post")}
        # A WSOL account's lamports are rent + its token amount; any other
        # token account's lamports are all rent.
        native = amt if mint == WSOL else {"pre": 0, "post": 0}
        if mint == WSOL:
            wsol_delta += amt["post"] - amt["pre"]
        else:
            deltas[mint] = deltas.get(mint, 0) + amt["post"] - amt["pre"]
        rent_pre = pre[n] - native["pre"] if "pre" in sides else 0
        rent_post = post[n] - native["post"] if "post" in sides else 0
        rent_delta += rent_post - rent_pre

    refund = 0
    if position and position in keys:
        p = keys.index(position)
        if pre[p] > 0 and post[p] == 0:
            refund = pre[p]
            out["position_closed"] = True
    out["cash_lamports"] = (post[i] - pre[i]) + fee + wsol_delta + rent_delta - refund
    out["position_rent_refund_lamports"] = refund
    out["token_account_rent_lamports"] = rent_delta
    out["token_deltas_raw"] = {m: v for m, v in deltas.items() if v}
    return out


def position_cash(realized_row, events, txs, now=None):
    """Pure join: one position's realized row + journal events + {sig: tx|None}.

    `events` are this position's dlmm_transactions.jsonl rows. A signature whose
    tx is None never landed (or is not visible yet) and contributes nothing; the
    token equation is what proves the set of landed txs is complete.
    """
    pos = realized_row["position"]
    seen, close_ev, swap_ev = set(), [], []
    for e in events:
        sig = e.get("signature")
        if not sig or sig in seen:
            continue
        seen.add(sig)
        if e.get("kind") in CLOSE_KINDS:
            close_ev.append(e)
        elif e.get("kind") == SWAP_KIND:
            swap_ev.append(e)
    wallets = {e.get("wallet") for e in close_ev + swap_ev}
    rec = {"position": pos, "cash_basis": "unlinked", "cash_reason": None,
           "cash_close_sol": None, "cash_swap_sol": None, "cash_out_sol": None,
           "cash_realized_sol": None, "cash_realized_pct": None, "swap_gap_sol": None,
           "tx_fee_sol": None, "position_rent_refund_sol": None,
           "token_account_rent_net_sol": None, "token_mint": None,
           "token_out_raw": None, "token_sold_raw": None,
           "close_signatures": [], "swap_signatures": [],
           "source": "finalized_rpc_transactions",
           "fetched_at": int(time.time() if now is None else now)}
    if not close_ev or len(wallets) != 1 or None in wallets:
        rec["cash_reason"] = "close_not_journaled" if not close_ev else "wallet_ambiguous"
        return rec
    wallet = next(iter(wallets))

    fee = refund = rent = close_cash = swap_cash = 0
    closed = False
    close_tokens, swap_tokens, landed_swaps = {}, {}, 0
    for kind_events, is_close in ((close_ev, True), (swap_ev, False)):
        for e in kind_events:
            flows = tx_flows(txs.get(e["signature"]), wallet, pos if is_close else None)
            if flows is None:
                continue
            fee += flows["fee_lamports"]
            if flows["failed"]:
                continue
            (rec["close_signatures"] if is_close else rec["swap_signatures"]).append(e["signature"])
            refund += flows["position_rent_refund_lamports"]
            rent += flows["token_account_rent_lamports"]
            bucket = close_tokens if is_close else swap_tokens
            for mint, v in flows["token_deltas_raw"].items():
                bucket[mint] = bucket.get(mint, 0) + v
            if is_close:
                close_cash += flows["cash_lamports"]
                closed = closed or flows["position_closed"]
            else:
                swap_cash += flows["cash_lamports"]
                landed_swaps += 1
    rec.update(tx_fee_sol=round(fee / LAMPORTS, 9),
               position_rent_refund_sol=round(refund / LAMPORTS, 9),
               token_account_rent_net_sol=round(rent / LAMPORTS, 9),
               cash_close_sol=round(close_cash / LAMPORTS, 9))
    if landed_swaps:
        rec["cash_swap_sol"] = round(swap_cash / LAMPORTS, 9)
    if not closed:
        rec["cash_reason"] = "close_unproven"
        return rec

    paid = {m: v for m, v in close_tokens.items() if v > 0}
    if len(paid) > 1:
        rec.update(cash_basis="partial", cash_reason="multiple_token_mints")
        return rec
    mint = next(iter(paid), None)
    out_raw = paid.get(mint, 0)
    sold_raw = -swap_tokens.get(mint, 0) if mint else 0
    rec.update(token_mint=mint, token_out_raw=str(out_raw), token_sold_raw=str(sold_raw))
    if out_raw and not landed_swaps:
        rec["cash_reason"] = "swap_unlinked"
        return rec
    if sold_raw != out_raw or (not out_raw and landed_swaps):
        rec.update(cash_basis="partial",
                   cash_reason="partial_sale" if sold_raw < out_raw else "sold_beyond_position")
        return rec

    deposit = realized_mod._f(realized_row.get("deposit_sol"), None)
    withdrawal = realized_mod._f(realized_row.get("withdrawal_sol"), None)
    fee_sol = realized_mod._f(realized_row.get("fee_sol"), None)
    if deposit is None or deposit <= 0:
        rec.update(cash_basis="partial", cash_reason="deposit_unmeasured")
        return rec
    cash_out = (close_cash + (swap_cash if landed_swaps else 0)) / LAMPORTS
    rec.update(cash_basis="wallet",
               cash_out_sol=round(cash_out, 9),
               cash_realized_sol=round(cash_out - deposit, 9),
               cash_realized_pct=round(100.0 * (cash_out - deposit) / deposit, 4))
    if withdrawal is not None and fee_sol is not None:
        rec["swap_gap_sol"] = round(withdrawal + fee_sol - cash_out, 9)
    return rec


def rpc_url():
    # Same variable the executor reads; the keyless public endpoint otherwise.
    urls = [u.strip() for u in (os.environ.get("SOLANA_RPC_URLS") or "").split(",") if u.strip()]
    return urls[0] if urls else "https://api.mainnet-beta.solana.com"


def fetch_tx(signature, url=None, tries=3):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getTransaction",
                       "params": [signature, {"encoding": "jsonParsed", "commitment": "finalized",
                                              "maxSupportedTransactionVersion": 0}]}).encode()
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url or rpc_url(), data=body,
                                         headers={"Content-Type": "application/json",
                                                  "User-Agent": "dlmm-lp/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            if "error" in data:
                raise RuntimeError(str(data["error"])[:200])
            return data.get("result")
        except Exception as exc:
            last = exc
            if attempt < tries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last


def load_events(memories):
    by_pos = {}
    path = os.path.join(memories, "dlmm_transactions.jsonl")
    if not os.path.exists(path):
        return by_pos
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("position"):
                by_pos.setdefault(e["position"], []).append(e)
    return by_pos


def _same(a, b):
    return {k: v for k, v in a.items() if k != "fetched_at"} == \
        {k: v for k, v in b.items() if k != "fetched_at"}


def reconcile(realized_path, days, max_tx=DEFAULT_MAX_TX, fetch=fetch_tx, quiet=False, now=None):
    """Write a cash row for each realized position closed in the window that has
    no "wallet" row yet. An unmeasured row is rewritten only when it changes.

    PASS THE CALLER'S `realized_path` (see dlmm_realized.apply_realized): the
    journal and the cash file are both resolved beside it.
    """
    now = time.time() if now is None else now
    cutoff = now - days * 86400
    path = cash_path_for(realized_path)
    known = load_cash(path)
    events = load_events(os.path.dirname(realized_path))
    rows = realized_mod.load_realized(realized_path)
    todo = [r for r in rows.values() if (r.get("closed_at") or 0) >= cutoff
            and (known.get(r["position"]) or {}).get("cash_basis") != "wallet"]
    todo.sort(key=lambda r: r.get("closed_at") or 0, reverse=True)
    budget, written, counts = max_tx, 0, {}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as out:
        for row in todo:
            evs = events.get(row["position"], [])
            sigs = list(dict.fromkeys(e["signature"] for e in evs if e.get("signature")
                                      and e.get("kind") in CLOSE_KINDS + (SWAP_KIND,)))
            if len(sigs) > budget:
                break
            txs = {}
            try:
                for sig in sigs:
                    txs[sig] = fetch(sig)
            except Exception as exc:
                if not quiet:
                    print(f"⚠️ cash: {row.get('pair', '?')}: tx fetch failed ({exc}) — left unmeasured")
                budget -= len(txs) + 1
                continue
            budget -= len(sigs)
            rec = position_cash(row, evs, txs, now=now)
            counts[rec["cash_basis"]] = counts.get(rec["cash_basis"], 0) + 1
            prev = known.get(rec["position"])
            if prev and _same(prev, rec):
                continue
            out.write(json.dumps(rec) + "\n")
            known[rec["position"]] = rec
            written += 1
    if not quiet:
        tally = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "nothing pending"
        print(f"✅ cash: {tally}; +{written} rows → {path}")
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=7.0)
    ap.add_argument("--max-tx", type=int, default=DEFAULT_MAX_TX)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    # As __main__ through the profile's scripts path, __file__ keeps the
    # symlinked path, so this is the profile's memories dir, not the repo's.
    profile = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    reconcile(os.path.join(profile, "memories", "dlmm_realized.jsonl"), args.days,
              max_tx=args.max_tx, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
