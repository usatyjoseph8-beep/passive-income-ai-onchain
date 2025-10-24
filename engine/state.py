from __future__ import annotations
import os, sqlite3, json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "incomes.db")

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_db():
    with _conn() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS earnings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT
        );""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS decisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            strategy TEXT NOT NULL,
            action TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            estimated_value REAL NOT NULL DEFAULT 0.0,
            note TEXT
        );""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        );""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS balances(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            token TEXT NOT NULL,
            amount REAL NOT NULL
        );""")
        con.commit()

def insert_earning(source: str, amount: float, note: str = ""):
    with _conn() as con:
        con.execute("INSERT INTO earnings(ts, source, amount, note) VALUES(?,?,?,?)",
                    (datetime.utcnow().isoformat(), source, amount, note))
        con.commit()

def upsert_daily_balance(token: str, amount: float, day: str):
    with _conn() as con:
        row = con.execute("SELECT id FROM balances WHERE day=? AND token=?", (day, token)).fetchone()
        if row:
            con.execute("UPDATE balances SET amount=? WHERE id=?", (amount, row[0]))
        else:
            con.execute("INSERT INTO balances(day, token, amount) VALUES(?,?,?)", (day, token, amount))
        con.commit()

def get_prev_balance(token: str, day: str):
    from datetime import datetime, timedelta
    prev_day = (datetime.fromisoformat(day) - timedelta(days=1)).date().isoformat()
    with _conn() as con:
        row = con.execute("SELECT amount FROM balances WHERE day=? AND token=?", (prev_day, token)).fetchone()
        return row[0] if row else None

def insert_decision(strategy: str, action: str, payload: dict, estimated_value: float, note: str = ""):
    with _conn() as con:
        con.execute("""
            INSERT INTO decisions(created_at, strategy, action, payload_json, status, estimated_value, note)
            VALUES(?,?,?,?, 'pending', ?, ?)
        """, (datetime.utcnow().isoformat(), strategy, action, json.dumps(payload), estimated_value, note))
        con.commit()

def fetch_decisions(status: str | None = None):
    with _conn() as con:
        sql = "SELECT id, created_at, strategy, action, payload_json, status, estimated_value, note FROM decisions"
        args = []
        if status:
            sql += " WHERE status=?"
            args.append(status)
        sql += " ORDER BY id DESC"
        rows = con.execute(sql, args).fetchall()
        return rows

def update_decision_status(decision_id: int, status: str):
    with _conn() as con:
        con.execute("UPDATE decisions SET status=? WHERE id=?", (status, decision_id))
        con.commit()

def get_setting(key: str, default: str = "") -> str:
    with _conn() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        if row and row[0] is not None:
            return row[0]
        return default

def set_setting(key: str, value: str):
    with _conn() as con:
        con.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, value))
        con.commit()

def get_totals():
    from_date = datetime.utcnow() - timedelta(days=7)
    with _conn() as con:
        all_time = (con.execute("SELECT COALESCE(SUM(amount),0) FROM earnings").fetchone()[0]) or 0.0
        last_7 = (con.execute("SELECT COALESCE(SUM(amount),0) FROM earnings WHERE ts >= ?", (from_date.isoformat(),)).fetchone()[0]) or 0.0
        pending = con.execute("SELECT COUNT(*) FROM decisions WHERE status='pending'").fetchone()[0]
    return {"all_time": all_time, "last_7": last_7, "pending": pending}

def get_earnings_df(days: int = 30):
    import pandas as pd
    since = datetime.utcnow() - timedelta(days=days)
    with _conn() as con:
        rows = con.execute("SELECT ts, source, amount, note FROM earnings WHERE ts >= ? ORDER BY ts ASC",
                           (since.isoformat(),)).fetchall()
    if not rows:
        return pd.DataFrame(columns=["ts","source","amount","note"])
    df = pd.DataFrame(rows, columns=["ts","source","amount","note"])
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def get_decisions_df(status: str | None = None):
    import pandas as pd
    rows = fetch_decisions(status)
    if not rows:
        return pd.DataFrame(columns=["id","created_at","strategy","action","payload_json","status","estimated_value","note"])
    df = pd.DataFrame(rows, columns=["id","created_at","strategy","action","payload_json","status","estimated_value","note"])
    return df
