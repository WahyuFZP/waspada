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
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import diff
import fetch
import final
import report
import rules
import scoring
from db import Db
from scope import OutOfScope, authorize

DATA = Path(os.environ.get("DATA_DIR", "data"))
SCAN_TIMEOUT = 60  # pemindaian pasif + cek berkas biasanya < 10 dtk; batas ini menjaga server responsif
(DATA / "reports").mkdir(parents=True, exist_ok=True)
db = Db(str(DATA / "webscans.db"))

app = FastAPI(title="WASPADA Web Security Scanner (pasif)")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["*"], allow_headers=["*"])


class Permintaan(BaseModel):
    target: str
    authorized: bool = False          # pemilik mengonfirmasi hak menguji target ini
    periksa_berkas: bool = True       # cek berkas terekspos (.git/.env/...)
    delay: float = 0.5                # jeda antar-permintaan
    operator: str | None = None       # label operator untuk rekaman audit (opsional, tak diminta di UI)


class VerifReq(BaseModel):
    authorized: bool = False          # izin WAJIB dikonfirmasi ulang: verifikasi memindai ulang target


def run_scan(base, host, periksa_berkas, delay, operator):
    obs = fetch.observe(base, host, delay=delay, cek_exposed=periksa_berkas)
    findings = rules.evaluate(obs)
    nilai = scoring.nilai(findings)
    akhir = final.conclude(findings, nilai)
    return report.build(base, findings, nilai, akhir, obs.get("errors", []), operator)


def _rescan(base, host):
    return rules.evaluate(fetch.observe(base, host, cek_exposed=True))


@app.post("/webscan")
async def webscan(req: Permintaan):
    try:
        base, host = authorize(req.target, req.authorized)
    except OutOfScope as exc:
        raise HTTPException(403, str(exc))
    delay = min(max(req.delay, 0.0), 2.0)  # jepit agar satu job tidak menggantung lama
    try:
        result = await asyncio.wait_for(
            run_in_threadpool(run_scan, base, host, req.periksa_berkas, delay, req.operator), SCAN_TIMEOUT)
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
        baru = await asyncio.wait_for(run_in_threadpool(_rescan, base, host), SCAN_TIMEOUT)
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
