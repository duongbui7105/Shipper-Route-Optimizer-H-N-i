"""
SQLite đơn giản để lưu lịch sử tìm đường của user.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "history.db")


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            start_label TEXT,
            end_label TEXT,
            waypoints TEXT,
            algorithm TEXT,
            vehicle TEXT,
            mode TEXT,
            distance_m REAL,
            time_s REAL,
            runtime_ms REAL
        )
    """)
    con.commit()
    con.close()


def save(entry: dict):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT INTO history(created_at, start_label, end_label, waypoints,
                            algorithm, vehicle, mode, distance_m, time_s, runtime_ms)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.utcnow().isoformat(),
        entry.get("start_label"),
        entry.get("end_label"),
        json.dumps(entry.get("waypoints", []), ensure_ascii=False),
        entry.get("algorithm"),
        entry.get("vehicle"),
        entry.get("mode"),
        entry.get("distance_m"),
        entry.get("time_s"),
        entry.get("runtime_ms"),
    ))
    con.commit()
    con.close()


def list_recent(limit: int = 20):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def clear_all():
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM history")
    con.commit()
    con.close()
