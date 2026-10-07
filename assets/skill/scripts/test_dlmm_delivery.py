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
    deliveries.write_text("".join(json.dumps(dict(delivery_id=x, observed_at=10, stage="prepared"))+"\n" for x in ["old", "new", "other", "duplicate"]))
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
        ])
    result = {x["delivery_id"]: x for x in delivery_outcomes(profile, deliveries, 0, 20)["deliveries"]}
    assert result["old"]["session_id"] == "legacy"
    assert result["new"]["session_id"] == "multiplex"
    assert result["new"]["session_state"] == "not_ended_at_cutoff"
    assert result["other"]["session_state"] == "unobserved"
    assert result["duplicate"]["session_state"] == "ambiguous"
    assert all(x["execution_verified"] is False for x in result.values())
print("Legacy and multiplex delivery correlation passed; profile isolation and ambiguity preserved")
