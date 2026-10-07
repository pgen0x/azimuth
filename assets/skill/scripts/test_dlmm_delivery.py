import base64
import json
from pathlib import Path
import sqlite3
import tempfile
from dlmm_evaluate import delivery_outcomes

with tempfile.TemporaryDirectory() as tmp:
    profile = Path(tmp) / "solanza"
    profile.mkdir()
    deliveries = profile / "deliveries.jsonl"
    deliveries.write_text("".join(json.dumps(dict(delivery_id=x, observed_at=10, stage="prepared"))+"\n" for x in ["old", "new", "other", "duplicate", "pending", "dry", "legacy-receipt"]))
    def v2(name, ident):
        return "webhook:v2:" + base64.urlsafe_b64encode(json.dumps([name,"dlmm-signal",ident], separators=(",",":")).encode()).decode().rstrip("=")
    with sqlite3.connect(profile / "state.db") as conn:
        conn.execute("CREATE TABLE sessions (id TEXT, source TEXT, chat_id TEXT, started_at REAL, ended_at REAL)")
        conn.executemany("INSERT INTO sessions VALUES (?, 'webhook', ?, 11, ?)", [
            ("legacy", "webhook:dlmm-signal:old", 12),
            ("multiplex", v2("solanza", "new"), None),
            ("wrong-profile", v2("nabil", "other"), 12),
            ("duplicate-a", "webhook:dlmm-signal:duplicate", 12),
            ("duplicate-b", v2("solanza", "duplicate"), 12),
            ("pending", v2("solanza", "pending"), None),
            ("dry", v2("solanza", "dry"), None),
            ("legacy-receipt", v2("solanza", "legacy-receipt"), None),
        ])
    result = {x["delivery_id"]: x for x in delivery_outcomes(profile, deliveries, 0, 20)["deliveries"]}
    assert result["old"]["session_id"] == "legacy"
    assert result["new"]["session_id"] == "multiplex"
    assert result["new"]["session_state"] == "not_ended_at_cutoff"
    assert result["other"]["session_state"] == "unobserved"
    assert result["duplicate"]["session_state"] == "ambiguous"
    assert all(x["execution_verified"] is False for x in result.values())
    assert result["old"]["session_state"] == "ended"
    memory = profile / "memories"
    memory.mkdir()
    def receipt(dry=False, verified=True):
        return dict(position="2"*44, signature="3"*88, dry_run=dry, execution_verified=verified)
    def output(session, executions, ts=15, status="receipt_report"):
        return dict(session_id=session, ts=ts, status=status, receipt_count=len(executions), executions=executions)
    outputs = [output("multiplex", [receipt()]), output("pending", [receipt(verified=False)]),
               output("dry", [receipt(dry=True)]), output("wrong-profile", [receipt()]),
               output("duplicate-a", [receipt()]), output("legacy", [receipt()], ts=9),
               dict(session_id="legacy-receipt", ts=15, status="receipt_report", receipt_count=1)]
    journal = memory / "dlmm_report_guard.jsonl"
    journal.write_text("".join(json.dumps(x)+"\n" for x in outputs))
    before = {x["delivery_id"]:x for x in delivery_outcomes(profile, deliveries, 0, 14)["deliveries"]}
    assert not before["new"]["execution_verified"] and before["new"]["output_state"] == "unobserved"
    after = {x["delivery_id"]:x for x in delivery_outcomes(profile, deliveries, 0, 20)["deliveries"]}
    assert after["new"]["execution_verified"] and after["new"]["output_state"] == "prepared"
    assert after["new"]["session_state"] == "not_ended_at_cutoff"  # output preparation does not close a session
    assert after["new"]["guard_outputs"][0]["elapsed_seconds"] == 4
    for ident in ["pending", "dry", "legacy-receipt"]:
        assert after[ident]["output_state"] == "prepared" and not after[ident]["execution_verified"]
    for ident in ["old", "other", "duplicate"]:
        assert after[ident]["output_state"] == "unobserved" and not after[ident]["execution_verified"]
    for bad in [dict(receipt(), dry_run="false"), dict(receipt(), execution_verified=1),
                dict(receipt(), signature=None), dict(receipt(), position="invalid"), None]:
        journal.write_text(json.dumps(output("multiplex", [bad]))+"\n")
        value = next(x for x in delivery_outcomes(profile, deliveries, 0, 20)["deliveries"] if x["delivery_id"] == "new")
        assert not value["execution_verified"]
    mismatch=output("multiplex", [receipt()]);mismatch["receipt_count"]=0
    journal.write_text(json.dumps(mismatch)+"\n")
    assert not next(x for x in delivery_outcomes(profile, deliveries, 0, 20)["deliveries"] if x["delivery_id"]=="new")["execution_verified"]
print("Delivery correlation and guarded receipt replay passed; cutoffs, pending/dry runs, legacy, profile isolation and ambiguity preserved")
