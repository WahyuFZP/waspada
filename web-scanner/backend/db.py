"""Riwayat pemeriksaan web di SQLite; laporan lengkap disimpan sebagai JSON di kolom report
(mencerminkan apk-scanner/db.py). Juga menyimpan jadwal re-scan (#19)."""
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

_WIB = timezone(timedelta(hours=7))


def _now():
    return datetime.now(_WIB).isoformat(timespec="seconds")


class Db:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS webscans (
            scan_id TEXT PRIMARY KEY, scanned_at TEXT NOT NULL, target TEXT NOT NULL,
            postur TEXT NOT NULL, tertinggi TEXT NOT NULL, jumlah_temuan INTEGER NOT NULL, report TEXT NOT NULL)""")
        # jadwal re-scan (#19): aset yang pemiliknya opt-in untuk dipindai ulang berkala + hasil regresi terakhir
        self.conn.execute("""CREATE TABLE IF NOT EXISTS jadwal (
            id TEXT PRIMARY KEY, target TEXT NOT NULL, host TEXT NOT NULL, interval_jam REAL NOT NULL,
            dibuat TEXT NOT NULL, last_run TEXT, last_scan_id TEXT, status TEXT, detail TEXT)""")
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

    # ---- jadwal re-scan (#19) ----
    _JCOLS = ("id", "target", "host", "interval_jam", "dibuat", "last_run", "last_scan_id", "status", "detail")

    def add_jadwal(self, target, host, interval_jam):
        jid = str(uuid.uuid4())
        self.conn.execute("INSERT INTO jadwal (id, target, host, interval_jam, dibuat) VALUES (?, ?, ?, ?, ?)",
                          (jid, target, host, interval_jam, _now()))
        self.conn.commit()
        return self.get_jadwal(jid)

    def list_jadwal(self):
        rows = self.conn.execute(f"SELECT {', '.join(self._JCOLS)} FROM jadwal ORDER BY dibuat DESC")
        return [dict(zip(self._JCOLS, r)) for r in rows]

    def get_jadwal(self, jid):
        r = self.conn.execute(f"SELECT {', '.join(self._JCOLS)} FROM jadwal WHERE id = ?", (jid,)).fetchone()
        return dict(zip(self._JCOLS, r)) if r else None

    def del_jadwal(self, jid):
        cur = self.conn.execute("DELETE FROM jadwal WHERE id = ?", (jid,))
        self.conn.commit()
        return cur.rowcount > 0

    def update_jadwal(self, jid, last_run, last_scan_id, status, detail):
        self.conn.execute("UPDATE jadwal SET last_run = ?, last_scan_id = ?, status = ?, detail = ? WHERE id = ?",
                          (last_run, last_scan_id, status, detail, jid))
        self.conn.commit()
