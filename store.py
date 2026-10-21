"""Penyimpanan SQLite: event dan alert disimpan sebagai JSON untuk audit."""
import json
import sqlite3


class Store:
    def __init__(self, path="waspada.db"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts TEXT, url TEXT, body TEXT);
            CREATE TABLE IF NOT EXISTS alerts (id TEXT PRIMARY KEY, ts TEXT, body TEXT);
        """)

    def add_event(self, event):
        self.db.execute("INSERT INTO events (ts, url, body) VALUES (?, ?, ?)",
                        (event["timestamp"], event.get("url"), json.dumps(event)))
        self.db.commit()

    def add_alert(self, alert):
        self.db.execute("INSERT INTO alerts VALUES (?, ?, ?)", (alert["id"], alert["timestamp"], json.dumps(alert)))
        self.db.commit()

    def seen_url(self, url):
        return url is not None and self.db.execute("SELECT 1 FROM events WHERE url = ?", (url,)).fetchone() is not None

    def _latest(self, table, limit):
        rows = self.db.execute(f"SELECT body FROM {table} ORDER BY ts DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in rows]

    def events(self, limit=200):
        return self._latest("events", limit)

    def alerts(self, limit=50):
        return self._latest("alerts", limit)
