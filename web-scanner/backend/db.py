"""Riwayat pemeriksaan web di SQLite; laporan lengkap disimpan sebagai JSON di kolom report
(mencerminkan apk-scanner/db.py)."""
import json
import sqlite3


class Db:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS webscans (
            scan_id TEXT PRIMARY KEY, scanned_at TEXT NOT NULL, target TEXT NOT NULL,
            postur TEXT NOT NULL, tertinggi TEXT NOT NULL, jumlah_temuan INTEGER NOT NULL, report TEXT NOT NULL)""")
        self.conn.commit()

    def save(self, r):
        self.conn.execute("INSERT OR REPLACE INTO webscans VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (r["scan_id"], r["scanned_at"], r["target"], r["ringkasan"]["postur"],
                           r["ringkasan"]["tertinggi"], len(r["temuan"]), json.dumps(r)))
        self.conn.commit()

    def list(self, limit=200):
        cols = ("scan_id", "scanned_at", "target", "postur", "tertinggi", "jumlah_temuan")
        rows = self.conn.execute(
            f"SELECT {', '.join(cols)} FROM webscans ORDER BY scanned_at DESC LIMIT ?", (limit,))
        return [dict(zip(cols, r)) for r in rows]

    def get(self, scan_id):
        row = self.conn.execute("SELECT report FROM webscans WHERE scan_id = ?", (scan_id,)).fetchone()
        return json.loads(row[0]) if row else None
