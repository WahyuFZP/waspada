"""API Pemeriksa Keamanan Web (pasif): POST /webscan, GET /webscans, GET /webscans/{id}.

PASIF & berizin: hanya memindai target yang pemiliknya mengonfirmasi otorisasi (field `authorized`),
dan hanya host target (penguncian lingkup di scope.py). Pemeriksaan dijalankan sinkron di threadpool
dengan batas waktu, seperti apk-scanner (pemindaian pasif singkat).

Model ancaman = single-user lokal (sama seperti apk-scanner). Endpoint ini mengambil URL dari input,
jadi bila kelak diekspos ke publik ia menjadi vektor SSRF: tambahkan allowlist egress / blokir rentang
internal di lapisan ini sebelum dibuka ke luar laptop. Untuk pemakaian lokal oleh pemilik, target
localhost/staging justru kasus utama, jadi tidak diblokir di sini.
"""
import asyncio
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import diff
import fetch
import final
import jadwal
import report
import rules
import scoring
import siem
import tls
from db import Db
from scope import OutOfScope, authorize

DATA = Path(os.environ.get("DATA_DIR", "data"))
SCAN_TIMEOUT = 60  # pemindaian pasif + cek berkas biasanya < 10 dtk; batas ini menjaga server responsif
WIB = timezone(timedelta(hours=7))  # stempel waktu jadwal (#19)
(DATA / "reports").mkdir(parents=True, exist_ok=True)
db = Db(str(DATA / "webscans.db"))

app = FastAPI(title="WASPADA Web Security Scanner (pasif)")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["*"], allow_headers=["*"])


class Permintaan(BaseModel):
    target: str
    authorized: bool = False          # pemilik mengonfirmasi hak menguji target ini
    periksa_berkas: bool = True       # cek berkas terekspos (.git/.env/...)
    delay: float = Field(0.5, allow_inf_nan=False)  # jeda antar-permintaan; NaN lolos dari jepitan min/max
    operator: str | None = None       # label operator untuk rekaman audit (opsional, tak diminta di UI)
    periksa_tls: bool = False         # #20 probe TLS AKTIF lanjutan (opt-in; membuka beberapa handshake)


class VerifReq(BaseModel):
    authorized: bool = False          # izin WAJIB dikonfirmasi ulang: verifikasi memindai ulang target


class JadwalReq(BaseModel):
    target: str
    authorized: bool = False          # izin WAJIB: menjadwalkan = menyetujui re-scan pasif berulang target ini
    interval_jam: float = 24.0        # jarak antar re-scan (jam)


def run_scan(base, host, periksa_berkas, delay, operator, periksa_tls=False):
    obs = fetch.observe(base, host, delay=delay, cek_exposed=periksa_berkas)
    findings = rules.evaluate(obs)
    errors = obs.get("errors", [])
    if periksa_tls:  # #20 probe TLS AKTIF, hanya saat diminta eksplisit (opt-in, authorization-first)
        temuan_tls, catatan = tls.probe(host, urlsplit(base).port or 443)
        findings = findings + temuan_tls
        if catatan:
            errors = errors + [catatan]
    nilai = scoring.nilai(findings)
    akhir = final.conclude(findings, nilai)
    hasil = report.build(base, findings, nilai, akhir, errors, operator)
    siem.kirim(hasil)  # #16 jembatan ke SIEM (opt-in via SIEM_INGEST_URL, fail-safe)
    return hasil


def _rescan(base, host, periksa_tls=False):
    findings = rules.evaluate(fetch.observe(base, host, cek_exposed=True))
    if periksa_tls:  # #20: temuan TLS aktif hanya bisa diverifikasi dengan menjalankan ulang probe TLS, bukan fetch pasif
        findings += tls.probe(host, urlsplit(base).port or 443)[0]
    return findings


@app.post("/webscan")
async def webscan(req: Permintaan):
    try:
        base, host = authorize(req.target, req.authorized)
    except OutOfScope as exc:
        raise HTTPException(403, str(exc))
    delay = min(max(req.delay, 0.0), 2.0)  # jepit agar satu job tidak menggantung lama
    try:
        result = await asyncio.wait_for(
            run_in_threadpool(run_scan, base, host, req.periksa_berkas, delay, req.operator, req.periksa_tls),
            SCAN_TIMEOUT)
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(504, f"Pemeriksaan melebihi {SCAN_TIMEOUT} detik dan dihentikan.")
    db.save(result)
    (DATA / "reports" / f"{result['scan_id']}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


@app.get("/webscans")
def list_webscans(limit: int = 200):
    return db.list(min(limit, 1000))


@app.get("/webscans/{scan_id}")
def get_webscan(scan_id: str):
    r = db.get(scan_id)
    if not r:
        raise HTTPException(404, "scan tidak ditemukan")
    return r


@app.get("/webscans/{scan_id}/diff")
def diff_webscan(scan_id: str, vs: str):
    """Perubahan scan_id (baru) dibanding vs (lama): temuan BARU/HILANG/TETAP + delta postur. Read-only."""
    baru, lama = db.get(scan_id), db.get(vs)
    if not baru or not lama:
        raise HTTPException(404, "scan tidak ditemukan")
    return diff.diff(lama, baru)


@app.post("/webscans/{scan_id}/verifikasi")
async def verifikasi(scan_id: str, req: VerifReq, rule: str, judul: str):
    """Periksa-ulang SATU temuan setelah ditambal: pindai ulang pasif target yang sama (jalur yang sudah ada),
    saring ke temuan diminta -> 'teratasi' | 'masih ada' | 'berubah'. Izin wajib dikonfirmasi ulang."""
    lama = db.get(scan_id)
    if not lama:
        raise HTTPException(404, "scan tidak ditemukan")
    try:
        base, host = authorize(lama["target"], req.authorized)
    except OutOfScope as exc:
        raise HTTPException(403, str(exc))
    try:
        baru = await asyncio.wait_for(
            run_in_threadpool(_rescan, base, host, rule.startswith("W-TLS")), SCAN_TIMEOUT)
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(504, f"Verifikasi melebihi {SCAN_TIMEOUT} detik dan dihentikan.")
    cocok = next((f for f in baru if f.judul == judul), None)
    if cocok:
        return {"status": "masih ada", "temuan": report._temuan(cocok),
                "pesan": "Temuan ini masih terdeteksi — perbaikan belum berhasil atau belum diterapkan."}
    if any(f.id == rule for f in baru):
        return {"status": "berubah", "temuan": None,
                "pesan": "Temuan persis ini hilang, tetapi masalah sejenis (id sama) masih ada — tinjau ulang."}
    return {"status": "teratasi", "temuan": None,
            "pesan": "Temuan ini sudah tidak terdeteksi. Perbaikan tampaknya berhasil."}


# ---- Penjadwal re-scan + alert regresi (#19) ----
# Otorisasi: menambah jadwal (dengan authorized=true) = izin DURABEL untuk re-scan PASIF berulang target itu;
# lingkup tetap terkunci ke host (scope.py) dan dapat dicabut kapan saja via DELETE. Penjadwalan waktu diserahkan
# ke cron/launchd atau scheduler.py yang memicu POST /jadwal/jalankan.

_pass_lock = threading.Lock()  # serialisasi lintasan: pemicu kedua (cron + tombol UI) menunggu, lalu baca last_run baru


def _pass_jadwal():
    """Satu lintasan: pindai ulang jadwal yang jatuh tempo, nilai regresi vs scan sebelumnya, perbarui baris.

    Diserialisasi dengan _pass_lock agar dua pemicu beruntun tidak memindai target yang sama dua kali
    (pemicu kedua membaca last_run yang sudah diperbarui -> tak lagi jatuh tempo)."""
    with _pass_lock:
        now = datetime.now(WIB)
        hasil = []
        for row in db.list_jadwal():
            if not jadwal.jatuh_tempo(row, now):
                continue
            stamp = now.isoformat(timespec="seconds")
            try:  # satu target gagal (scan ATAU simpan/diff) tak boleh menghentikan lintasan
                laporan = run_scan(row["target"], row["host"], True, 0.5, "penjadwal")
                db.save(laporan)
                (DATA / "reports" / f"{laporan['scan_id']}.json").write_text(
                    json.dumps(laporan, ensure_ascii=False, indent=2), encoding="utf-8")
                prev = db.get(row["last_scan_id"]) if row.get("last_scan_id") else None
                if prev:  # bandingkan vs lintasan penjadwal sebelumnya (mode sama, pasif) — bukan scan manual acak (mis. ber-TLS)
                    status, detail = jadwal.nilai_regresi(diff.diff(prev, laporan))
                else:
                    status, detail = "baru", "pemindaian dasar pertama (belum ada pembanding)"
                db.update_jadwal(row["id"], stamp, laporan["scan_id"], status, detail)
                hasil.append({"target": row["target"], "status": status, "detail": detail, "scan_id": laporan["scan_id"]})
            except Exception as exc:
                db.update_jadwal(row["id"], stamp, row.get("last_scan_id"), "gagal", type(exc).__name__)
                hasil.append({"target": row["target"], "status": "gagal", "detail": type(exc).__name__, "scan_id": None})
        return {"dijalankan": len(hasil), "hasil": hasil}


@app.get("/jadwal")
def list_jadwal():
    return db.list_jadwal()


@app.post("/jadwal")
def tambah_jadwal(req: JadwalReq):
    try:
        base, host = authorize(req.target, req.authorized)  # otorisasi WAJIB & direkam saat menambah
    except OutOfScope as exc:
        raise HTTPException(403, str(exc))
    return db.add_jadwal(base, host, max(req.interval_jam, 1.0))  # minimal 1 jam: cegah re-scan beruntun


@app.delete("/jadwal/{jadwal_id}")
def hapus_jadwal(jadwal_id: str):
    if not db.del_jadwal(jadwal_id):
        raise HTTPException(404, "jadwal tidak ditemukan")
    return {"dihapus": jadwal_id}


@app.post("/jadwal/jalankan")
async def jalankan_jadwal():
    """Pindai ulang semua jadwal yang jatuh tempo (dipicu cron/launchd atau scheduler.py). Sinkron di threadpool."""
    if _pass_lock.locked():  # lintasan masih jalan: jangan antre memenuhi threadpool, pemicu ini cukup dilewati
        return {"dijalankan": 0, "hasil": [], "sedang_berjalan": True}
    return await run_in_threadpool(_pass_jadwal)
