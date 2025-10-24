from __future__ import annotations
import json
from typing import Optional
from engine.state import _conn, update_decision_status, insert_earning

def approve_decision(decision_id: int, payload_override: Optional[dict]=None, strategy_name: Optional[str]=None):
    if decision_id == -1:
        insert_earning(source=f"{strategy_name or 'Auto'}", amount=0.000001, note="Auto-approved marker")
        return True
    with _conn() as con:
        row = con.execute("SELECT id, strategy, action, payload_json, status FROM decisions WHERE id=?", (decision_id,)).fetchone()
        if not row or row[4] != "pending":
            return False
        strategy, payload_json = row[1], row[3]
        payload = json.loads(payload_json)
        insert_earning(source=f"{strategy}", amount=0.000001, note=f"Approved action marker: {payload}")
        update_decision_status(decision_id, "approved")
        return True

def reject_decision(decision_id: int):
    with _conn() as con:
        row = con.execute("SELECT id, status FROM decisions WHERE id=?", (decision_id,)).fetchone()
        if not row or row[1] != "pending":
            return False
        update_decision_status(decision_id, "rejected")
        return True
