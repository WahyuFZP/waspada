"""Penyimpanan PostgreSQL: event dan alert disimpan sebagai JSONB untuk audit."""
import psycopg
from psycopg.types.json import Jsonb


class Store:
    def __init__(self, url):
        # autocommit: tiap insert langsung tersimpan; satu koneksi cukup untuk skala demo
        self.db = psycopg.connect(url, autocommit=True)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id BIGSERIAL PRIMARY KEY, ts TIMESTAMPTZ NOT NULL, url TEXT, body JSONB NOT NULL);
            CREATE INDEX IF NOT EXISTS events_url ON events (url);
            CREATE INDEX IF NOT EXISTS events_ts ON events (ts DESC);
            CREATE TABLE IF NOT EXISTS alerts (id TEXT PRIMARY KEY, ts TIMESTAMPTZ NOT NULL, body JSONB NOT NULL);
        """)

    def add_event(self, event):
        self.db.execute("INSERT INTO events (ts, url, body) VALUES (%s, %s, %s)",
                        (event["timestamp"], event.get("url"), Jsonb(event)))

    def add_alert(self, alert):
        self.db.execute("INSERT INTO alerts VALUES (%s, %s, %s)", (alert["id"], alert["timestamp"], Jsonb(alert)))

    def seen_url(self, url):
        return url is not None and self.db.execute("SELECT 1 FROM events WHERE url = %s", (url,)).fetchone() is not None

    def _latest(self, table, limit):
        return [r[0] for r in self.db.execute(f"SELECT body FROM {table} ORDER BY ts DESC, id DESC LIMIT %s", (limit,))]

    def events(self, limit=200):
        return self._latest("events", limit)

    def alerts(self, limit=50):
        return self._latest("alerts", limit)

    def reset(self):
        """Kosongkan tabel (dipakai test)."""
        self.db.execute("TRUNCATE events, alerts")
