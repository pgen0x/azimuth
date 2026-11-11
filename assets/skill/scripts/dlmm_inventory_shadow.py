#!/usr/bin/env python3
"""Shadow-only inventory-share exit for pulse ``sol_bidask`` positions.

THE PATTERN. A SOL-only BidAsk ladder sits below spot, so a token that grinds
down fills it bin by bin: the position quietly converts SOL into the falling
token. A slow grind never trips the velocity rules (fast-out reads a 5m candle),
so the exit that finally fires is the 1h downtrend floor — by which point most
of the position is token, and the settlement swap has to sell that bag into a
thin book. The wallet-cash basis (``dlmm_realized_cash.py``) shows that sale as
the largest source of the gap between the datapi mark and the cash that landed.

THE CANDIDATE RULE. Exit when ALL of these hold:

  token share of position value  >= INV_SHARE_PCT          (default 50)
  mark PnL %                     <= INV_SHARE_PNL_PCT      (default -2.0)
  entry pool_liquidity_usd       <  INV_SHARE_MAX_LIQ_USD  (default 25000)

THIS MODULE NEVER CLOSES ANYTHING. It is a research journal. The monitor queues
an evaluation per tick, ``flush_tick_observers`` writes it after every risk and
close decision of that tick, and nothing here returns a value the monitor reads.
The evidence behind the rule is one decisive event, which is exactly why it has
to earn forward evidence before it may act.

Inputs are the tick's own verified native mark (``dlmm_risk_mark.js``) and the
position's stored entry signal — no RPC or API call. Anything unmeasured (no
verified mark, unknown entry liquidity, inconsistent inventory) never fires:
an unmeasured value is not a trigger.

Output, ``<profile>/memories/dlmm_inventory_shadow.jsonl``: at most one row per
position, the first tick the rule would have fired. ``mark_value_sol`` /
``mark_pnl_sol`` are the counterfactual "exit at fire" mark, so a later join on
``position`` against ``dlmm_realized_cash.jsonl`` (``cash_realized_sol``) shows
what firing would have changed. The fire value is a MARK, not executable
proceeds: it carries the same token-side valuation the cash basis exists to
correct, so the comparison overstates the rule by roughly the sale gap.

Kill switch: INV_SHARE_SHADOW=false (or 0/no/off) disables evaluation entirely.

Report:  python3 dlmm_stats.py --inventory-shadow
"""
import hashlib
import json
import math
import os
import re
import stat

SCHEMA = 1
SHADOW_FILE = "dlmm_inventory_shadow.jsonl"
MARKER_DIR = "dlmm_inventory_shadow.d"
MAX_BYTES = 16 * 1024 * 1024
# Native inventory and value_lamports_upper are two views of the same mark. A
# reconstruction that disagrees by more than this is not trusted.
VALUE_TOLERANCE = 0.01
DEFAULTS = {"INV_SHARE_PCT": 50.0, "INV_SHARE_PNL_PCT": -2.0, "INV_SHARE_MAX_LIQ_USD": 25000.0}
_POSITION = re.compile(r"[A-Za-z0-9_-]{1,64}")
_RAW = re.compile(r"[0-9]{1,39}")


def enabled(env=None):
    """On by default. INV_SHARE_SHADOW=false|0|no|off turns evaluation off."""
    value = (os.environ if env is None else env).get("INV_SHARE_SHADOW", "true")
    return value.strip().lower() not in ("false", "0", "no", "off")


def thresholds(env=None):
    """Env-tunable thresholds; a malformed or non-finite value keeps the default."""
    env = os.environ if env is None else env
    out = {}
    for key, default in DEFAULTS.items():
        try:
            value = float(env.get(key, default))
        except (TypeError, ValueError):
            value = default
        out[key] = value if math.isfinite(value) else default
    return out


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _raw(value):
    return int(value) if isinstance(value, str) and _RAW.fullmatch(value) else None


def token_share(mark):
    """Token side's share (0..1) of a verified native mark's value, or None.

    Uses only the mark's own fields: inventory raw amounts (principal + unclaimed
    fees), the active bin and the bin step. A DLMM bin price is quoted in raw Y
    per raw X, so a raw token amount converts to lamports without decimals.
    The total is checked against ``value_lamports_upper``; a disagreement means
    the inputs are not one consistent mark, and returns None.
    """
    if not isinstance(mark, dict):
        return None
    inventory, observation = mark.get("inventory"), mark.get("bin_observation")
    if not isinstance(inventory, dict) or not isinstance(observation, dict):
        return None
    sol_is_x, step, active = observation.get("sol_is_x"), observation.get("bin_step"), mark.get("active_bin")
    if type(sol_is_x) is not bool or type(step) is not int or not 0 < step <= 10000 or type(active) is not int:
        return None
    amounts = [_raw(inventory.get(k)) for k in ("net_x_raw", "net_y_raw", "net_fee_x_raw", "net_fee_y_raw")]
    total_upper = _raw(mark.get("value_lamports_upper"))
    if None in amounts or total_upper is None:
        return None
    x, y = amounts[0] + amounts[2], amounts[1] + amounts[3]
    try:
        price = math.exp(active * math.log1p(step / 10000.0))  # raw Y per raw X
    except OverflowError:
        return None
    if not math.isfinite(price) or price <= 0:
        return None
    # SOL=Y: the token is X and is worth x*price lamports. SOL=X: the token is Y.
    token_lamports, sol_lamports = (y / price, x) if sol_is_x else (x * price, y)
    total = token_lamports + sol_lamports
    if not math.isfinite(total) or total <= 0:
        return None
    if abs(total - total_upper) > VALUE_TOLERANCE * max(total, total_upper):
        return None
    return token_lamports / total


def entry_liquidity_usd(meta):
    """The entry gate's pool_liquidity_usd from the stored signal, or None."""
    signal = meta.get("signal") if isinstance(meta, dict) else None
    gates = signal.get("entry_live_gates") if isinstance(signal, dict) else None
    value = gates.get("pool_liquidity_usd") if isinstance(gates, dict) else None
    return float(value) if _finite(value) and value > 0 else None


def evaluate(position, pool, meta, mark, now, env=None):
    """Pure: the row to journal if the rule would fire on this tick, else None.

    ``mark`` must be the tick's VERIFIED native mark (the caller only passes one
    that passed ``verified_risk_mark``). Mode and strategy are checked here too,
    so a mis-scoped caller cannot widen the study.
    """
    if not enabled(env) or not isinstance(meta, dict) or not isinstance(mark, dict):
        return None
    if meta.get("mode") != "pulse" or meta.get("strategy") != "sol_bidask":
        return None
    if not isinstance(position, str) or not _POSITION.fullmatch(position):
        return None
    t = thresholds(env)
    liq = entry_liquidity_usd(meta)
    pnl_pct, pnl_sol = mark.get("pnl_pct"), mark.get("pnl_sol")
    share = token_share(mark)
    if liq is None or share is None or not _finite(pnl_pct) or not _finite(pnl_sol):
        return None   # unmeasured is not a trigger
    if not (share * 100.0 >= t["INV_SHARE_PCT"] and pnl_pct <= t["INV_SHARE_PNL_PCT"]
            and liq < t["INV_SHARE_MAX_LIQ_USD"]):
        return None
    deployed = meta.get("deployed_at")
    return dict(
        version=SCHEMA, ts=now, position=position, pool=pool, mode="pulse",
        token_share=round(share, 6), pnl_pct=round(pnl_pct, 6), entry_liq_usd=round(liq, 2),
        age_min=round((now - deployed) / 60.0, 2) if _finite(deployed) else None,
        mark_value_sol=int(mark["value_lamports_upper"]) / 1e9, mark_pnl_sol=pnl_sol,
        deposit_sol=int(mark["deposit_lamports"]) / 1e9 if _raw(mark.get("deposit_lamports")) else None,
        active_bin=mark.get("active_bin"), thresholds=t,
        basis="shadow_would_fire; native_mark_not_executable; never_closed")


def _marker(position):
    return hashlib.sha256(position.encode()).hexdigest()[:32]


def record(profile_dir, row):
    """Append ``row`` once per position. Best effort: never raises.

    The O_EXCL marker claim is the dedupe, so a restart cannot write a second
    row. A claim is not proof of a persisted row: a failed write after the claim
    loses that observation, which must stay unknown rather than be retried late
    with a different mark.
    """
    from dlmm_research_io import research_writer, research_write
    try:
        if not isinstance(row, dict) or not _POSITION.fullmatch(str(row.get("position"))):
            return False
        memory = os.path.join(profile_dir, "memories")
        markers = os.path.join(memory, MARKER_DIR)
        ident = _marker(row["position"])
        try:
            if not stat.S_ISDIR(os.lstat(markers).st_mode):
                raise OSError("marker_not_directory")
            if os.path.lexists(os.path.join(markers, ident)):
                return False
        except FileNotFoundError:
            pass
        payload = (json.dumps(row, allow_nan=False) + "\n").encode()
        os.makedirs(markers, mode=0o700, exist_ok=True)
        marker_fd = os.open(markers, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            with research_writer(os.path.join(memory, SHADOW_FILE), len(payload), MAX_BYTES) as fd:
                try:
                    os.close(os.open(ident, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                     0o600, dir_fd=marker_fd))
                except FileExistsError:
                    return False
                research_write(fd, payload)
        finally:
            os.close(marker_fd)
        return True
    except Exception as error:
        print("INVENTORY_SHADOW_ERROR " + type(error).__name__)
        return False


def load_rows(path):
    """First row per position (the file is append-only; later duplicates are ignored)."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row.get("position") and row["position"] not in out:
                out[row["position"]] = row
    return out


def join(shadow_rows, cash_rows):
    """Join would-fire rows to wallet-cash rows on ``position``.

    ``delta_sol = mark_pnl_sol (fire) - cash_realized_sol (actual)``: positive
    means firing would have done better, on the mark. Only ``cash_basis ==
    "wallet"`` rows are measured; the rest are counted, never treated as 0.0.
    """
    measured, unmeasured = [], 0
    for position, row in shadow_rows.items():
        cash = cash_rows.get(position) or {}
        actual = cash.get("cash_realized_sol")
        if cash.get("cash_basis") != "wallet" or not _finite(actual) or not _finite(row.get("mark_pnl_sol")):
            unmeasured += 1
            continue
        measured.append(dict(position=position, fire_pnl_sol=row["mark_pnl_sol"], actual_cash_sol=actual,
                             delta_sol=row["mark_pnl_sol"] - actual, closed_positive=actual > 0))
    return measured, unmeasured


def report(profile_dir):
    """Text summary for the kill rule. Pure read of two journals."""
    from dlmm_realized import cash_path_for, load_cash
    memory = os.path.join(profile_dir, "memories")
    rows = load_rows(os.path.join(memory, SHADOW_FILE))
    cash = load_cash(cash_path_for(os.path.join(memory, "dlmm_realized.jsonl")))
    measured, unmeasured = join(rows, cash)
    lines = [f"Inventory-share shadow: {len(rows)} would-fire position(s); "
             f"{len(measured)} joined to wallet cash, {unmeasured} unmeasured"]
    if measured:
        deltas = [m["delta_sol"] for m in measured]
        mean = sum(deltas) / len(deltas)
        lines.append(f"  mean(fire mark - actual cash) = {mean:+.6f} SOL  (sum {sum(deltas):+.6f})")
        lines.append(f"  fired on positions that later closed positive: "
                     f"{sum(m['closed_positive'] for m in measured)}/{len(measured)}")
    lines.append("  note: the fire value is a mark, not sale proceeds; it overstates the rule by the sale gap")
    return "\n".join(lines)
