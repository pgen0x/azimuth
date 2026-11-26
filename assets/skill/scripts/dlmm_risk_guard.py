#!/usr/bin/env python3
"""Wallet drawdown guard: pauses NEW Solana entries when equity falls too far
below its high-water mark. Exits are never paused.

Run by azimuth-risk-guard.timer every 10 minutes. It writes a pause file; the
one choke point that honours it is `assertNotRiskPaused()` in
dlmm_executor.js `deployPosition` (pulse, AI-agent and re-center mints all go
through it), and dlmm_pipeline.py checks it early to skip work.

Equity
    For each registered profile, the newest `memories/dlmm_nav.jsonl` row that is
    acceptable: `lp_mark_sol` non-null, `wallet_history_complete` true, and a finite
    `known_asset_subtotal_sol` and `external_flow_lamports`. Not `nav_sol`: that is
    null whenever any dust token has no quote route, which would blind the guard.
    E = sum of known_asset_subtotal_sol; F = sum of external_flow_lamports / 1e9.
    F is cumulative since the profile's first NAV snapshot (`coverage_since`), so
    it changes only on a deposit or withdrawal.

Flow-neutral high-water mark
    adj = E - F is unchanged by a deposit or withdrawal (both legs move by the same
    amount), so the stored mark is `hwm_adj = max(hwm_adj, adj)`. The peak is then
    restated in today's capital: peak = hwm_adj + F, and dd = 1 - E / peak.
    With no flows since the mark this is exactly 1 - E/E_hwm. It is not the
    literal `1 - adj/hwm`: adj is not on the equity scale when cumulative flows
    are non-zero (it can even be negative), so that ratio would be meaningless.
    A deposit raises the peak and the equity alike, so it neither trips the guard
    nor inflates the mark; a loss after it is measured against the larger capital.

Pauses (fail closed) come in two kinds, recorded as `kind` in the pause file:
    drawdown  dd >= RISK_MAX_DRAWDOWN (env, default 0.30; outside (0, 1) keeps 0.30).
              A measured loss: cleared ONLY by `--resume --note "..."`, which journals who
              and why and resets the mark to the current adj equity.
    evidence  the guard cannot measure: no acceptable row for every profile for 12h (an
              alert at 2h); no high-water mark yet, or an unreadable mark file; a peak that
              is not positive; a NAV basis change with no measured peak to carry over; an
              unreadable pause file. Not a loss, so it CLEARS ITSELF on the first clean
              evaluation (acceptable rows, a mark, drawdown below the limit), journaled as
              auto_clear. If that evaluation measures a loss instead, the pause becomes a
              drawdown pause.
    A pause file without a kind (written before kinds existed) is treated as drawdown.
    Each pause and each clear alerts once, and a pause re-alerts every 6h while it holds,
    through the profile's alert outbox (dlmm_alerts.py; flushed by the monitor loop with `hermes -p <profile> send`).

NAV basis change: when a profile's wallet or coverage_since differs from the one the mark
was set on, the flow sum restarted and adj is no longer comparable. The guard restates the
last measured peak equity at the new flows (journaled as rebase) and keeps going, so the
loss since that peak still counts. Without a measured peak it is an evidence pause.

Files (dir: AZIMUTH_RISK_STATE_DIR, default ~/.local/state/azimuth):
    risk_hwm.json     the mark, its basis per profile, alert bookkeeping
    risk_pause.json   {paused, kind, at, dd, hwm, equity, reason}; path overridable with
                      AZIMUTH_RISK_PAUSE_FILE, which the executor reads too
    risk_status.json  the last evaluation, for the dashboard
    risk_guard.jsonl  journal of pauses, resumes, inits and alerts

Usage:
    dlmm_risk_guard.py --profile P [--profile P2]       evaluate once (the timer)
    dlmm_risk_guard.py --profile P --status             print, change nothing
    dlmm_risk_guard.py --profile P --init-hwm current|<SOL equity>
    dlmm_risk_guard.py --profile P --resume --note "why"
Profiles may also come from RISK_GUARD_PROFILES (comma-separated paths).
"""
import argparse
import contextlib
import fcntl
import getpass
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

DEFAULT_MAX_DD = 0.30
BLIND_ALERT_S = 2 * 3600
BLIND_PAUSE_S = 12 * 3600
DD_EPSILON = 1e-9
REALERT_S = 6 * 3600
TAIL_BYTES = 4 << 20
FUTURE_SKEW_S = 300


# ------------------------------------------------------------------ config

def max_drawdown(env=None):
    env = os.environ if env is None else env
    try:
        v = float(env.get("RISK_MAX_DRAWDOWN", ""))
    except ValueError:
        return DEFAULT_MAX_DD
    return v if math.isfinite(v) and 0 < v < 1 else DEFAULT_MAX_DD


def state_dir(env=None):
    env = os.environ if env is None else env
    return Path(env.get("AZIMUTH_RISK_STATE_DIR") or Path.home() / ".local/state/azimuth")


def pause_path(env=None):
    env = os.environ if env is None else env
    return Path(env.get("AZIMUTH_RISK_PAUSE_FILE") or state_dir(env) / "risk_pause.json")


# ------------------------------------------------------------------ io

def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    with open(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
        json.dump(obj, f, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _read_json(path):
    """(obj, error). A missing file is (None, None); unreadable or corrupt is (None, reason)."""
    try:
        text = Path(path).read_text()
    except FileNotFoundError:
        return None, None
    except OSError as e:
        return None, f"unreadable: {e.__class__.__name__}"
    try:
        obj = json.loads(text)
    except ValueError:
        return None, "corrupt"
    return (obj, None) if isinstance(obj, dict) else (None, "corrupt")


def _journal(sd, event):
    sd.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(sd / "risk_guard.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (json.dumps(event, sort_keys=True) + "\n").encode())
    finally:
        os.close(fd)


@contextlib.contextmanager
def _locked(sd):
    sd.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(sd / ".risk_guard.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def _tail_rows(path, limit=TAIL_BYTES):
    """Rows of the last `limit` bytes, newest last. The NAV journal is large."""
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - limit))
            data = f.read()
    except OSError:
        return []
    lines = data.split(b"\n")
    if size > limit:
        lines = lines[1:]  # the first line is partial
    out = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


# ------------------------------------------------------------------ observation

def _num(v):
    return float(v) if type(v) in (int, float) and math.isfinite(v) else None


def acceptable(row, now):
    """The row's (equity, flow_sol) when it may be used, else None."""
    ts = _num(row.get("ts"))
    equity = _num(row.get("known_asset_subtotal_sol"))
    flow = _num(row.get("external_flow_lamports"))
    if ts is None or ts > now + FUTURE_SKEW_S or equity is None or flow is None:
        return None
    if _num(row.get("lp_mark_sol")) is None or row.get("wallet_history_complete") is not True:
        return None
    return equity, flow / 1e9


def basis_of(row):
    wallet = str(row.get("wallet") or "")
    return {"wallet": hashlib.sha256(wallet.encode()).hexdigest()[:16] if wallet else None,
            "coverage_since": row.get("coverage_since")}


def observe(profiles, now):
    """Newest acceptable row per profile, summed. Missing rows are reported, never zero."""
    per, missing = {}, []
    for p in profiles:
        found = None
        for row in reversed(_tail_rows(Path(p) / "memories" / "dlmm_nav.jsonl")):
            got = acceptable(row, now)
            if got:
                found = {"ts": int(row["ts"]), "equity": got[0], "flow": got[1], "basis": basis_of(row)}
                break
        if found:
            per[str(p)] = found
        else:
            missing.append(str(p))
    obs = {"profiles": per, "missing": missing}
    if per and not missing:
        obs["equity"] = sum(v["equity"] for v in per.values())
        obs["flow"] = sum(v["flow"] for v in per.values())
        obs["adj"] = obs["equity"] - obs["flow"]
        obs["oldest_ts"] = min(v["ts"] for v in per.values())
    return obs


def drawdown(hwm_adj, obs):
    """(peak, dd) with the peak restated in today's capital; dd None when unmeasurable."""
    peak = hwm_adj + obs["flow"]
    if not math.isfinite(peak) or peak <= 0:
        return peak, None
    return peak, 1 - obs["equity"] / peak


# ------------------------------------------------------------------ guard

def _alert(profiles, text, env=None):
    env = os.environ if env is None else env
    target = env.get("DLMM_ALERT_TARGET", "telegram")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from dlmm_alerts import enqueue
        enqueue(profiles[0], target, text)
        return True
    except Exception as e:  # the pause itself must never depend on the alert
        print(f"risk guard: alert not queued ({e.__class__.__name__})", file=sys.stderr)
        return False


def _pause(sd, pp, profiles, now, reason, kind, obs=None, peak=None, dd=None, env=None):
    """Write the pause, or upgrade an evidence pause to a drawdown one. Returns the action or None.

    kind "drawdown" is a real loss and is cleared only by --resume. kind "evidence" is a gap
    in what the guard can see (blind, no or corrupt mark, unmeasurable peak, corrupt pause file)
    and clears itself once a full evaluation is clean. A pause without a kind (written before kinds
    existed) is treated as drawdown: manual."""
    current, _ = _read_json(pp)
    if current and current.get("paused") is True:
        held = current.get("kind") if current.get("kind") in ("drawdown", "evidence") else "drawdown"
        if not (held == "evidence" and kind == "drawdown"):
            return None  # keep the first record; it already alerted
    record = {"paused": True, "kind": kind, "at": int(now), "reason": reason, "dd": dd, "hwm": peak,
              "equity": (obs or {}).get("equity")}
    _write_json(pp, record)
    upgraded = bool(current and current.get("paused") is True)
    _journal(sd, {"event": "pause_upgrade" if upgraded else "pause", **record})
    dd_txt = f"{dd:.1%}" if dd is not None else "n/a"
    how = ("Resume by hand: dlmm_risk_guard.py --resume --note \"...\"" if kind == "drawdown"
           else "This clears itself once the guard can measure equity again.")
    _alert(profiles, f"🛑 Azimuth risk guard PAUSED new entries ({kind}): {reason} (drawdown {dd_txt}). "
                     f"Exits keep running. {how}", env)
    return "upgraded" if upgraded else "paused"


def _clear(sd, pp, profiles, now, prior, why, env=None):
    record = {"paused": False, "cleared_at": int(now), "cleared": why,
              "prior_reason": (prior or {}).get("reason"), "prior_kind": (prior or {}).get("kind")}
    _write_json(pp, record)
    _journal(sd, {"event": "auto_clear", **record})
    _alert(profiles, f"✅ Azimuth risk guard resumed new entries: {why} "
                     f"(was: {record['prior_reason'] or 'unreadable pause file'}).", env)


def evaluate(profiles, now=None, env=None, write=True):
    """One guard pass. Returns the status dict; with write=False nothing on disk changes."""
    env = os.environ if env is None else env
    now = int(time.time() if now is None else now)
    sd, pp = state_dir(env), pause_path(env)
    limit = max_drawdown(env)
    state, state_err = _read_json(sd / "risk_hwm.json")
    pause, pause_err = _read_json(pp)
    obs = observe(profiles, now)
    status = {"ts": now, "max_drawdown": limit, "equity": obs.get("equity"), "peak": None, "dd": None,
              "paused": bool(pause and pause.get("paused") is True) or pause_err is not None,
              "pause_reason": (pause or {}).get("reason") if (pause or {}).get("paused") is True
              else (f"pause file {pause_err}" if pause_err else None),
              "pause_kind": None, "blind_s": None, "row_age_s": None, "missing_profiles": obs["missing"],
              "action": None}

    # Blind: no acceptable row for some profile, or the newest one is old.
    blind_since = obs.get("oldest_ts")
    if blind_since is None:
        blind_since = (state or {}).get("blind_since") or now
    blind_s = now - blind_since
    status["blind_s"] = blind_s
    if "oldest_ts" in obs:
        status["row_age_s"] = now - obs["oldest_ts"]

    # Evidence gaps (the guard cannot measure) versus a measured loss. Only the second is manual.
    evidence, loss = [], []
    if state_err:
        evidence.append(f"risk_hwm.json {state_err}")
    elif state is None or _num(state.get("hwm_adj")) is None:
        evidence.append("no high-water mark (run --init-hwm)")
    if blind_s >= BLIND_PAUSE_S:
        evidence.append(f"blind {blind_s / 3600:.1f}h: no acceptable NAV row for every profile")

    new_hwm, rebase, measured = None, None, False
    if state and _num(state.get("hwm_adj")) is not None and "adj" in obs:
        basis = state.get("basis") or {}
        changed = {p for p, v in obs["profiles"].items() if basis.get(p) != v["basis"]}
        changed |= {p for p in basis if p not in obs["profiles"]}
        hwm_adj = state["hwm_adj"]
        if changed:
            # The flow sum restarted (new wallet or NAV journal), so the stored mark is not comparable.
            # Restate the last measured peak at today's flows; without one the gap stays open.
            last_peak = _num(state.get("last_peak_sol"))
            if last_peak is None:
                evidence.append("NAV basis changed (wallet or coverage_since) for " + ", ".join(sorted(changed))
                                + " and no measured peak to carry over (run --init-hwm)")
                hwm_adj = None
            else:
                hwm_adj = last_peak - obs["flow"]
                rebase = {"changed": sorted(changed), "peak_sol": last_peak,
                          "basis": {p: v["basis"] for p, v in obs["profiles"].items()}}
        if hwm_adj is not None:
            hwm_adj = max(hwm_adj, obs["adj"])
            peak, dd = drawdown(hwm_adj, obs)
            status.update(peak=peak, dd=dd)
            if dd is None:
                evidence.append("peak equity not positive; drawdown unmeasurable")
            else:
                measured = True
                if dd >= limit - DD_EPSILON:
                    loss.append(f"drawdown {dd:.1%} >= {limit:.0%}")
            if rebase or hwm_adj > state["hwm_adj"]:
                new_hwm = hwm_adj
    reasons = loss + evidence

    if not write:
        if reasons and not status["paused"]:
            status["pause_reason"] = "would pause: " + "; ".join(reasons)
        return status

    with _locked(sd):
        state = dict(state or {})
        if new_hwm is not None:
            state.update(hwm_adj=new_hwm, hwm_set_at=now)
        if rebase:
            state["basis"] = rebase["basis"]
            _journal(sd, {"event": "rebase", "at": now, "profiles": rebase["changed"], "peak_sol": rebase["peak_sol"]})
            _alert(profiles, "ℹ️ Azimuth risk guard: NAV basis changed (wallet or NAV journal); the high-water mark "
                             "was carried over from the last measured peak.", env)
        if measured and status["peak"] is not None:
            state["last_peak_sol"] = status["peak"]
        alerts = state.setdefault("alerted", {})
        if BLIND_ALERT_S <= blind_s < BLIND_PAUSE_S and not alerts.get("blind"):
            if _alert(profiles, f"⚠️ Azimuth risk guard is blind for {blind_s / 3600:.1f}h (no acceptable NAV "
                                "row). New entries pause at 12h.", env):
                alerts["blind"] = now
                _journal(sd, {"event": "blind_alert", "at": now, "blind_s": blind_s})
        if blind_s < BLIND_ALERT_S:
            alerts.pop("blind", None)
        state["blind_since"] = None if "oldest_ts" in obs else blind_since
        if pause_err and not reasons:
            # A torn or corrupt pause file is itself an evidence gap; a clean evaluation replaces it.
            _clear(sd, pp, profiles, now, None, "pause file was unreadable; equity measured below the limit", env)
            status.update(paused=False, pause_reason=None, action="cleared")
        elif reasons:
            kind = "drawdown" if loss else "evidence"
            reason = "; ".join(reasons)
            action = _pause(sd, pp, profiles, now, reason, kind, obs, status["peak"], status["dd"], env)
            status["action"] = action or "still paused"
            if action:
                alerts["pause"] = now
            status["paused"] = True
            status["pause_reason"] = reason if action else (status["pause_reason"] or reason)
        elif pause and pause.get("paused") is True and pause.get("kind") == "evidence":
            _clear(sd, pp, profiles, now, pause, "equity is measurable again and below the limit", env)
            status.update(paused=False, pause_reason=None, action="cleared")
        current, _ = _read_json(pp)
        if current and current.get("paused") is True:
            status["pause_kind"] = current.get("kind") if current.get("kind") in ("drawdown", "evidence") else "drawdown"
            last = alerts.get("pause") or current.get("at") or now
            if now - last >= REALERT_S:
                hours = (now - (current.get("at") or now)) / 3600
                if _alert(profiles, f"🛑 Azimuth risk guard: new entries STILL paused ({status['pause_kind']}, "
                                    f"{hours:.0f}h): {current.get('reason')}. Exits keep running.", env):
                    alerts["pause"] = now
                    _journal(sd, {"event": "pause_realert", "at": now})
            elif not alerts.get("pause"):
                alerts["pause"] = last
        else:
            alerts.pop("pause", None)
        if not state_err:
            _write_json(sd / "risk_hwm.json", state)
        _write_json(sd / "risk_status.json", status)
    return status


def set_mark(profiles, value, now=None, env=None, resume_note=None):
    """--init-hwm / --resume. The mark is set on the current acceptable rows."""
    env = os.environ if env is None else env
    now = int(time.time() if now is None else now)
    sd, pp = state_dir(env), pause_path(env)
    obs = observe(profiles, now)
    if "adj" not in obs:
        raise SystemExit("risk guard: no acceptable NAV row for " + ", ".join(obs["missing"])
                         + "; cannot set a mark")
    if value == "current":
        hwm_adj = obs["adj"]
    else:
        try:
            equity = float(value)
        except ValueError:
            raise SystemExit("risk guard: --init-hwm takes 'current' or an equity in SOL")
        if not math.isfinite(equity) or equity <= 0:
            raise SystemExit("risk guard: equity must be > 0")
        hwm_adj = equity - obs["flow"]  # the given equity, stated at today's flows
    with _locked(sd):
        state = {"hwm_adj": hwm_adj, "hwm_set_at": now, "alerted": {}, "blind_since": None,
                 "last_peak_sol": hwm_adj + obs["flow"],
                 "basis": {p: v["basis"] for p, v in obs["profiles"].items()}}
        _write_json(sd / "risk_hwm.json", state)
        event = {"event": "resume" if resume_note is not None else "init_hwm", "at": now,
                 "by": getpass.getuser(), "hwm_peak_equity": hwm_adj + obs["flow"], "equity": obs["equity"]}
        if resume_note is not None:
            event["note"] = resume_note
            _write_json(pp, {"paused": False, "resumed_at": now, "note": resume_note, "by": event["by"]})
        _journal(sd, event)
    return event


def format_status(s):
    def pct(v):
        return f"{v:.1%}" if v is not None else "n/a"

    def sol(v):
        return f"{v:.4f} SOL" if v is not None else "n/a"

    age = f"{s['row_age_s'] / 60:.0f}m" if s.get("row_age_s") is not None else "none"
    head = f"PAUSED ({s['pause_reason']})" if s["paused"] else "entries allowed"
    if not s["paused"] and s.get("pause_reason"):
        head += f"; {s['pause_reason']}"
    return (f"risk guard: {head}\n"
            f"  drawdown {pct(s['dd'])} of max {pct(s['max_drawdown'])}; equity {sol(s['equity'])}; "
            f"peak (flow-adjusted) {sol(s['peak'])}\n"
            f"  newest acceptable NAV row {age} old; missing profiles: {', '.join(s['missing_profiles']) or 'none'}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Wallet drawdown guard for new Solana entries")
    ap.add_argument("--profile", action="append", default=[], help="Hermes profile dir (repeatable)")
    ap.add_argument("--status", action="store_true", help="print the current evaluation, change nothing")
    ap.add_argument("--init-hwm", metavar="SOL|current", help="set the high-water mark (once, at deploy)")
    ap.add_argument("--resume", action="store_true", help="clear a pause and reset the mark (needs --note)")
    ap.add_argument("--note", help="why the pause is being cleared (journaled)")
    a = ap.parse_args(argv)
    profiles = a.profile or [p for p in os.environ.get("RISK_GUARD_PROFILES", "").split(",") if p.strip()]
    if not profiles:
        ap.error("no profile: pass --profile or set RISK_GUARD_PROFILES")
    if a.resume:
        if not (a.note or "").strip():
            ap.error("--resume needs --note \"why\"")
        print(json.dumps(set_mark(profiles, "current", resume_note=a.note.strip())))
        return 0
    if a.init_hwm:
        print(json.dumps(set_mark(profiles, a.init_hwm)))
        return 0
    status = evaluate(profiles, write=not a.status)
    print(format_status(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
