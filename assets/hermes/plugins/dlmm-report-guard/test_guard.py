"""Offline hook replay: no RPC, inference, transaction, or Telegram send."""
import base64
import contextlib
import importlib.util
import io
import json
import os
import shlex
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("guard", HERE / "__init__.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
sys.path.insert(0, str(HERE.parents[2] / "skill/scripts"))
import dlmm_pipeline as pipeline

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp) / "solanza"
    plugin = home / "plugins/dlmm-report-guard"
    script = home / "skills/solana-dlmm/scripts/dlmm_pipeline.py"
    plugin.mkdir(parents=True)
    script.parent.mkdir(parents=True)
    script.touch()
    with sqlite3.connect(home / "state.db") as db:
        db.execute("CREATE TABLE sessions(id TEXT, source TEXT, chat_id TEXT)")
        identity = base64.urlsafe_b64encode(json.dumps(["solanza", "dlmm-signal", "delivery"]).encode()).decode().rstrip("=")
        db.executemany("INSERT INTO sessions VALUES (?,?,?)", [
            ("session", "webhook", "webhook:v2:" + identity),
            ("other", "telegram", "123"),
            ("route", "webhook", "webhook:another-route:delivery"),
        ])
    hooks = {}
    guard.register(SimpleNamespace(manifest=SimpleNamespace(path=str(plugin)),
                                   register_hook=lambda name, fn: hooks.update({name: fn})))
    assert set(hooks) == {"pre_tool_call", "post_tool_call", "transform_llm_output"}
    ids = dict(session_id="session", turn_id="turn", tool_call_id="call")
    fabricated = "🚀 DEPLOYED SI-SOL\nPosition Size | 0.29887497 SOL\nTX | https://solscan.io/tx/fabricated"
    assert "report withheld" in guard.transform(fabricated, **ids)
    assert guard.transform(fabricated, session_id="other") is None
    assert guard.transform(fabricated, session_id="route") is None
    assert guard.transform("❌ REJECTED — momentum screen", **ids) is None
    assert guard.transform("[SILENT]", **ids) is None
    for command in ["echo " + str(script), "python3 -c 'print(1)'", "python3 /tmp/dlmm_pipeline.py"]:
        args = {"command": command}
        guard.pre(tool_name="terminal", args=args, **ids)
        assert args["command"] == command

    def prepare():
        args = {"command": shlex.join(["python3", str(script), "--from-signal", '{"name":"$(echo bad)"}'])}
        guard.pre(tool_name="terminal", args=args, **ids)
        words = shlex.split(args["command"])
        assert words[:3] == ["rtk", "proxy", "env"]
        return words[3].split("=", 1)[1]

    def result(nonce, dry=False, verified=True):
        os.environ.update(DLMM_REPORT_NONCE=nonce, DLMM_REPORT_SESSION="session")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            pipeline.emit_execution_receipt("SI-SOL actual-position\nPosition Size | 0.12 SOL", "actual-position", "actual-signature", dry, verified)
        return {"output": out.getvalue(), "exit_code": 0, "error": None}

    for dry, verified, label in [(False, True, "🚀 DEPLOYED"), (False, False, "SUBMITTED"), (True, True, "no live deployment")]:
        nonce = prepare()
        guard.post(tool_name="terminal", result=json.dumps(result(nonce, dry, verified)), **ids)
        report = guard.transform(fabricated, **ids)
        assert label in report and "0.12 SOL" in report and "0.29887497" not in report
        assert "report withheld" in guard.transform(fabricated, **ids)  # consumed, cannot reuse
    for bad in ["nonce", "exit", "bool", "pending", "error", "trailing", "turn"]:
        nonce = prepare()
        value = result("0" * 32 if bad == "nonce" else nonce)
        if bad == "exit": value["exit_code"] = 1
        if bad == "bool": value["exit_code"] = False
        if bad == "pending": value["exit_code"] = None
        if bad == "error": value["error"] = "failed"
        if bad == "trailing": value["output"] += "invented extra output\n"
        guard.post(tool_name="terminal", result=value, **(dict(ids, turn_id="other-turn") if bad == "turn" else ids))
        assert "report withheld" in guard.transform(fabricated, **ids)
    rows = [json.loads(line) for line in (home / "memories/dlmm_report_guard.jsonl").read_text().splitlines()]
    assert any(row["status"] == "receipt_report" for row in rows)
    assert all(set(row) == {"ts", "session_id", "status", "receipt_count"} for row in rows)
    assert not guard.scoped("bad/session")
    with contextlib.redirect_stdout(io.StringIO()):
        os.environ["DLMM_REPORT_NONCE"] = "invalid"
        pipeline.emit_execution_receipt("report", "position", "signature", False, True)
print("DLMM report guard offline replay passed")
