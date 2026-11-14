"""Riwayat scan di SQLite; laporan lengkap disimpan sebagai JSON di kolom report dan di file."""
import json
import sqlite3


class Db:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS scans (
            scan_id TEXT PRIMARY KEY, scanned_at TEXT NOT NULL, nama TEXT NOT NULL, sha256 TEXT NOT NULL,
            skor INTEGER NOT NULL, level TEXT NOT NULL, report TEXT NOT NULL, package TEXT)""")
        try:  # migrasi DB lama (tabel sudah ada tanpa kolom package untuk lineage diff #10); abaikan bila ada
            self.conn.execute("ALTER TABLE scans ADD COLUMN package TEXT")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

    def save(self, r):
        self.conn.execute(
            "INSERT INTO scans (scan_id, scanned_at, nama, sha256, skor, level, report, package) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (r["scan_id"], r["scanned_at"], r["file"]["nama"], r["file"]["sha256"], r["skor"],
             r["level_risiko"], json.dumps(r), r["aplikasi"]["package"]))
        self.conn.commit()

    def list(self, limit=200):
        rows = self.conn.execute(
            "SELECT scan_id, scanned_at, nama, sha256, skor, level, package FROM scans ORDER BY scanned_at DESC LIMIT ?", (limit,))
        return [dict(zip(("scan_id", "scanned_at", "nama", "sha256", "skor", "level_risiko", "package"), r)) for r in rows]

    def get(self, scan_id):
        row = self.conn.execute("SELECT report FROM scans WHERE scan_id = ?", (scan_id,)).fetchone()
        return json.loads(row[0]) if row else None
