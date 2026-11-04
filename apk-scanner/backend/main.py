"""API APK Security Scanner: POST /scan, GET /scans, GET /scans/{id}. APK hanya dibaca, tidak pernah dijalankan."""
import asyncio
import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

import diff
import final
import packer
import parser as apk_parser
import report
import rules
import scoring
from db import Db
from validator import MAX_BYTES, InvalidApk, validate

DATA = Path(os.environ.get("DATA_DIR", "data"))
# APK uji nyata selesai < 5 detik; batas ini hanya untuk APK rekayasa yang membuat parser berputar tanpa henti
ANALYZE_TIMEOUT = 120
(DATA / "apk").mkdir(parents=True, exist_ok=True)
(DATA / "reports").mkdir(parents=True, exist_ok=True)
db = Db(str(DATA / "scans.db"))

app = FastAPI(title="WASPADA APK Security Scanner")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["*"], allow_headers=["*"])


def analyze(path, filename, size):
    """Pipeline PRD §6 langkah 3-8 (dijalankan di thread: androguard & APKiD bersifat blocking)."""
    parsed = apk_parser.parse(path)
    pk = packer.scan(path)
    findings = rules.evaluate(parsed, pk)
    skor, level = scoring.score(findings)
    akhir = final.conclude(parsed, pk, findings, level)
    return report.build(filename, size, parsed, pk, findings, skor, level, akhir)


@app.post("/scan")
async def scan(file: UploadFile):
    filename = Path(file.filename or "tanpa-nama.apk").name[:200]  # hanya nama, buang path dari klien
    size = 0
    with tempfile.NamedTemporaryFile(dir=DATA / "apk", suffix=".part", delete=False) as tmp:
        try:
            while chunk := await file.read(1 << 20):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(413, "file melebihi 150 MB")
                tmp.write(chunk)
        except HTTPException:
            tmp.close()
            os.unlink(tmp.name)
            raise
    try:
        validate(tmp.name, size)
    except InvalidApk as exc:
        os.unlink(tmp.name)
        raise HTTPException(422, str(exc))

    sha = apk_parser.sha256_file(tmp.name)
    path = DATA / "apk" / f"{sha}.apk"  # karantina dengan nama hash, bukan nama asli dari klien
    os.replace(tmp.name, path)
    try:
        # shortcut: thread yang melewati batas waktu tidak bisa dihentikan paksa, hanya dibatasi mem/cpu container;
        # pindahkan analisis ke proses terpisah bila scanner dibuka untuk pengguna di luar laptop ini
        result = await asyncio.wait_for(run_in_threadpool(analyze, str(path), filename, size), ANALYZE_TIMEOUT)
    except TimeoutError:
        raise HTTPException(504, f"Analisis melebihi {ANALYZE_TIMEOUT} detik dan dihentikan. APK ini mungkin sengaja dibuat untuk mengganggu pemeriksa.")
    except Exception as exc:  # APK lolos validasi tapi tidak bisa diurai androguard
        raise HTTPException(422, f"APK tidak dapat dianalisis: {type(exc).__name__}: {exc}")
    db.save(result)
    (DATA / "reports" / f"{result['scan_id']}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


@app.get("/scans")
def list_scans(limit: int = 200):
    return db.list(min(limit, 1000))


@app.get("/scans/{scan_id}")
def get_scan(scan_id: str):
    r = db.get(scan_id)
    if not r:
        raise HTTPException(404, "scan tidak ditemukan")
    return r


@app.get("/scans/{scan_id}/diff")
def diff_scan(scan_id: str, vs: str):
    """Perubahan scan_id (baru) dibanding vs (lama): temuan BARU/HILANG/TETAP + delta skor. Read-only."""
    baru, lama = db.get(scan_id), db.get(vs)
    if not baru or not lama:
        raise HTTPException(404, "scan tidak ditemukan")
    return diff.diff(lama, baru)
