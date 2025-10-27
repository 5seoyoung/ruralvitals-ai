# edge_agent/utils/storage.py
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events(
  ts TEXT NOT NULL,
  resident_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  level TEXT NOT NULL,
  note TEXT
);
CREATE INDEX IF NOT EXISTS idx_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_resident ON events(resident_id);
"""

class EventLogger:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.sqlite_path)
        cur = con.cursor()
        for stmt in SCHEMA.strip().split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)
        con.commit(); con.close()

    def log(self, ts: str, resident_id: str, kind: str, level: str, note: str):
        con = sqlite3.connect(self.sqlite_path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO events(ts,resident_id,kind,level,note) VALUES(?,?,?,?,?)",
            (ts, resident_id, kind, level, note),
        )
        con.commit(); con.close()
