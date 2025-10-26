# edge_agent/utils/storage.py
import sqlite3
from pathlib import Path

class EventLogger:
    def __init__(self, sqlite_path: str):
        self.path = Path(sqlite_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        con = sqlite3.connect(self.path)
        try:
            con.execute(
                "CREATE TABLE IF NOT EXISTS events("
                "ts TEXT, kind TEXT, level TEXT, note TEXT)"
            )
            con.commit()
        finally:
            con.close()

    def log(self, ts: str, kind: str, level: str, note: str) -> None:
        con = sqlite3.connect(self.path)
        try:
            con.execute(
                "INSERT INTO events(ts, kind, level, note) VALUES(?,?,?,?)",
                (ts, kind, level, note),
            )
            con.commit()
        finally:
            con.close()
