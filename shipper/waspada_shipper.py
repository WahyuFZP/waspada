#!/usr/bin/env python3
"""Pengirim log WASPADA: ikuti auth.log (sshd) dan eve.json (Suricata), kirim baris baru ke POST /ingest.

Hanya pustaka standar Python 3.8+, supaya bisa langsung dijalankan di server satuan tanpa pip.

    INGEST_TOKEN=... python3 waspada_shipper.py --api http://siem.satuan:8000 \
        --auth /var/log/auth.log --suricata /var/log/suricata/eve.json

Token dibaca dari env INGEST_TOKEN, bukan argumen: argumen terlihat oleh semua user lewat daftar proses.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

BATCH = 200
MAX_PENDING = 10_000  # server mati lama: yang tertua dibuang agar memori tidak terus tumbuh


def log(*parts):
    print(time.strftime("%H:%M:%S"), *parts, file=sys.stderr, flush=True)


class Follower:
    """Seperti `tail -F`: baca baris baru, tahan file dirotasi (inode berubah) atau dipotong (ukuran mengecil).

    File yang sudah ada saat pengirim mulai dibaca dari akhir (log lama tidak dikirim ulang); file yang baru muncul
    kemudian dibaca dari awal, karena seluruh isinya baru.
    """

    def __init__(self, path, from_start=False):
        self.path = path
        self.fh = None
        self.ino = None
        self.buf = ""
        self.skip_existing = not from_start and os.path.exists(path)

    def _open(self, at_end):
        try:
            self.fh = open(self.path, encoding="utf-8", errors="replace", newline="")
        except FileNotFoundError:
            return False
        self.ino = os.fstat(self.fh.fileno()).st_ino
        self.buf = ""
        if at_end:
            self.fh.seek(0, os.SEEK_END)
        return True

    def _read(self):
        data = self.buf + self.fh.read()
        *full, self.buf = data.split("\n")  # potongan baris terakhir ditahan sampai newline-nya tiba
        return [line.rstrip("\r") for line in full if line.strip()]

    def lines(self):
        if self.fh is None:
            if not self._open(at_end=self.skip_existing):
                return []
            self.skip_existing = False
        out = self._read()
        try:
            st = os.stat(self.path)
        except FileNotFoundError:
            return out  # sedang dirotasi; file baru dibuka di putaran berikutnya
        if st.st_ino != self.ino:  # dirotasi: sisa file lama sudah terbaca di atas, lanjut file baru dari awal
            self.fh.close()
            if self._open(at_end=False):
                out += self._read()
        elif st.st_size < self.fh.tell():  # dipotong (truncate)
            self.fh.seek(0)
            self.buf = ""
            out += self._read()
        return out


def to_records(kind, lines):
    """Baris mentah -> record /ingest. Suricata: hanya event_type alert (sisanya diabaikan backend juga)."""
    if kind == "auth":
        return [{"kind": "auth", "line": line} for line in lines]
    records = []
    for line in lines:
        try:
            rec = json.loads(line)
        except ValueError:
            log("lewati baris eve.json bukan JSON:", line[:80])
            continue
        if isinstance(rec, dict) and rec.get("event_type") == "alert":
            records.append({**rec, "kind": "suricata"})
    return records


class Rejected(Exception):
    pass


def post(api, token, records):
    """-> kode HTTP. Galat jaringan dilempar agar pemanggil mencoba lagi nanti."""
    req = urllib.request.Request(
        f"{api}/ingest",
        data=json.dumps(records).encode(),
        headers={"Content-Type": "application/json", "X-Ingest-Token": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def send(api, token, records, post=post):
    """Kirim satu batch. 422 = ada record ditolak: kirim ulang satu per satu agar record lain tidak ikut hilang."""
    code = post(api, token, records)
    if code == 401:
        raise Rejected("token ingest ditolak (401): periksa INGEST_TOKEN di pengirim dan backend")
    if code >= 500:
        raise OSError(f"server membalas {code}")
    if code == 422:
        for rec in records:
            if post(api, token, [rec]) == 422:
                log("record ditolak backend, dilewati:", json.dumps(rec)[:120])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--api", default="http://localhost:8000", help="alamat backend WASPADA")
    p.add_argument("--auth", help="path auth.log (sshd)")
    p.add_argument("--suricata", help="path eve.json Suricata")
    p.add_argument("--interval", type=float, default=1.0, help="jeda pemeriksaan file (detik)")
    p.add_argument("--from-start", action="store_true", help="kirim juga isi file yang sudah ada saat mulai")
    args = p.parse_args(argv)
    sources = [(k, Follower(path, args.from_start)) for k, path in (("auth", args.auth), ("suricata", args.suricata)) if path]
    if not sources:
        p.error("isi minimal salah satu: --auth atau --suricata")
    token = os.environ.get("INGEST_TOKEN", "")
    log("mengikuti", ", ".join(f.path for _, f in sources), "->", args.api)

    pending, backoff = [], 1
    while True:
        for kind, follower in sources:
            pending += to_records(kind, follower.lines())
        if len(pending) > MAX_PENDING:
            log(f"antrean penuh, {len(pending) - MAX_PENDING} record tertua dibuang")
            pending = pending[-MAX_PENDING:]
        while pending:
            try:
                send(args.api, token, pending[:BATCH])
            except Rejected as exc:
                sys.exit(str(exc))
            except OSError as exc:  # termasuk URLError: backend belum siap atau jaringan putus, data tetap di antrean
                log(f"gagal kirim ({exc}), coba lagi dalam {backoff} dtk; antrean {len(pending)}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                break
            log(f"terkirim {min(len(pending), BATCH)} record")
            pending, backoff = pending[BATCH:], 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
