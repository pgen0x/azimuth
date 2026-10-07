"""Correlate DLMM webhook reports with completed direct pipeline tool calls.

This prevents accidental model fabrication, not malicious agents with shell access.
"""
import base64
import json
import re
import shlex
import sqlite3
import threading
import time
import uuid
from collections import OrderedDict
from pathlib import Path

MARKER = "DLMM_EXECUTION_RECEIPT="
CLAIM = re.compile(r"\bDEPLOYED\b|\bDRY RUN DEPLOY\b|solscan\.io/tx/", re.I)
_home = None
_lock = threading.Lock()
# ponytail: retain 256 turns; use durable receipts if gateway recovery is required.
_turns = OrderedDict()


def register(ctx):
    global _home
    _home = Path(ctx.manifest.path).absolute().parent.parent
    ctx.register_hook("pre_tool_call", pre)
    ctx.register_hook("post_tool_call", post)
    ctx.register_hook("transform_llm_output", transform)


def scoped(session_id):
    if not _home or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id):
        return False
    try:
        with sqlite3.connect((_home / "state.db").as_uri() + "?mode=ro", uri=True, timeout=1) as db:
            row = db.execute("SELECT source,chat_id FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not row or row[0] != "webhook":
            return False
        chat = row[1] or ""
        if chat.startswith("webhook:dlmm-signal:"):
            return True
        if chat.startswith("webhook:v2:"):
            encoded = chat[len("webhook:v2:"):]
            identity = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            return isinstance(identity, list) and len(identity) == 3 and identity[:2] == [_home.name, "dlmm-signal"]
    except (sqlite3.Error, OSError):
        return None
    except (ValueError, TypeError):
        pass
    return False


def pipeline_args(args):
    try:
        words = shlex.split(args.get("command", ""))
        if words[:2] == ["rtk", "proxy"]:
            words = words[2:]
        if len(words) < 2 or not re.fullmatch(r"python(?:3(?:\.\d+)?)?", Path(words[0]).name):
            return None
        script = Path(words[1]).expanduser()
        if not script.is_absolute():
            script = Path(args.get("workdir") or str(_home)) / script
        if script.resolve() != (_home / "skills/solana-dlmm/scripts/dlmm_pipeline.py").resolve():
            return None
        # Re-quote all arguments: no shell operators, expansion or command substitution.
        words[1] = str(script)
        return words
    except (ValueError, TypeError, OSError):
        return None


def pre(tool_name=None, args=None, session_id="", turn_id="", tool_call_id="", **kwargs):
    if tool_name != "terminal" or not isinstance(args, dict) or not tool_call_id or not scoped(session_id):
        return
    words = pipeline_args(args)
    if not words:
        return
    nonce = uuid.uuid4().hex
    with _lock:
        key = (session_id, turn_id)
        state = _turns.setdefault(key, {"calls": {}, "reports": [], "executions": []})
        state["calls"][tool_call_id] = nonce
        _turns.move_to_end(key)
        while len(_turns) > 256:
            _turns.popitem(last=False)
    args["command"] = shlex.join(["rtk", "proxy", "env", "DLMM_REPORT_NONCE=" + nonce,
                                  "DLMM_REPORT_SESSION=" + session_id] + words)


def post(tool_name=None, result=None, session_id="", turn_id="", tool_call_id="", **kwargs):
    if tool_name != "terminal":
        return
    with _lock:
        state = _turns.get((session_id, turn_id))
        nonce = state["calls"].pop(tool_call_id, None) if state else None
        if not nonce:
            return
        try:
            value = json.loads(result) if isinstance(result, str) else result
            if not isinstance(value, dict) or type(value.get("exit_code")) is not int or value["exit_code"] != 0 or value.get("error"):
                return
            lines = value.get("output", "").strip().splitlines()
            if not lines or not lines[-1].startswith(MARKER):
                return
            receipt = json.loads(lines[-1][len(MARKER):])
            if receipt.get("nonce") != nonce or receipt.get("session_id") != session_id:
                return
            if type(receipt.get("dry_run")) is not bool or type(receipt.get("execution_verified")) is not bool:
                return
            report = receipt.get("report")
            if not isinstance(report, str) or not report.strip() or len(report) > 12000:
                return
            if receipt["dry_run"]:
                label = "🧪 DRY RUN — no live deployment"
            elif receipt["execution_verified"]:
                label = "🚀 DEPLOYED — pipeline verified position"
            else:
                label = "⚠️ SUBMITTED — position verification pending"
            state["reports"].append(label + "\n" + report)
            # Persist public identifiers and verification flags, never report text or nonce.
            identifiers = {}
            for key, pattern in (("position", r"[1-9A-HJ-NP-Za-km-z]{32,44}"),
                                 ("signature", r"[1-9A-HJ-NP-Za-km-z]{64,88}")):
                value = receipt.get(key)
                identifiers[key] = value if isinstance(value, str) and re.fullmatch(pattern, value) else None
            state["executions"].append(dict(identifiers, dry_run=receipt["dry_run"],
                                            execution_verified=receipt["execution_verified"]))
        except (ValueError, TypeError, AttributeError):
            return


def transform(response_text="", session_id="", turn_id="", platform="", **kwargs):
    scope = scoped(session_id)
    if not scope:
        if scope is None and getattr(platform, "value", platform) == "webhook" and CLAIM.search(response_text):
            return "⚠️ UNVERIFIED — report guard could not read session scope. Check transaction evidence before retrying."
        return
    with _lock:
        state = _turns.pop((session_id, turn_id), None)
    reports = state["reports"] if state else []
    status = "receipt_report" if reports else "claim_withheld" if CLAIM.search(response_text) else "no_execution_claim"
    try:
        memory = _home / "memories"
        memory.mkdir(exist_ok=True)
        with (memory / "dlmm_report_guard.jsonl").open("a") as out:
            out.write(json.dumps({"ts": time.time(), "session_id": session_id, "status": status,
                                  "receipt_count": len(reports),
                                  "executions": state["executions"] if state else []}) + "\n")
    except OSError:
        pass
    if reports:
        return "🤖 AI Pick · pipeline execution receipt\n" + "\n\n".join(reports)
    if status == "claim_withheld":
        return "⚠️ UNVERIFIED — deployment report withheld: no completed pipeline receipt for this turn. Check transaction evidence before retrying."
