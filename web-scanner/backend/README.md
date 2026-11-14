# WASPADA — Pemeriksa Keamanan Web (MVP pasif)

Modul pendamping pemeriksa APK: memeriksa kelemahan keamanan sebuah **aplikasi web milik sendiri atau
yang Anda diizinkan menguji**, lalu menyarankan perbaikan. **Pasif & non-destruktif** — hanya
mengambil respons dan mengamatinya; tidak mengeksploitasi, tidak mengubah data, tidak membebani server.

Konsep lengkap (termasuk tahap aktif/DAST lanjutan): [`../../docs/web-scanner-concept.md`](../../docs/web-scanner-concept.md).

## Menjalankan

```bash
pip install -r requirements.txt
```

```bash
python cli.py http://localhost:3000 --authorized
```

`--authorized` wajib: menegaskan Anda memiliki / diizinkan menguji target. Tanpa itu, pemeriksaan
ditolak. Memindai web milik orang lain tanpa izin melanggar UU ITE.

Opsi: `--json` (laporan lengkap), `--no-exposed` (lewati cek berkas terekspos), `--delay N` (jeda
antar-permintaan, default 0.5 dtk).

## Yang diperiksa (MVP pasif)

| ID | Temuan | Tingkat |
|---|---|---|
| W-A02-01 | Situs lewat HTTP tanpa enkripsi | tinggi |
| W-A02-02 | HSTS tidak ada | sedang |
| W-A02-03/04 | Sertifikat TLS kedaluwarsa / segera kedaluwarsa | tinggi / sedang |
| W-H01 | Content-Security-Policy tidak ada | sedang |
| W-H04 | Tidak ada proteksi clickjacking (X-Frame-Options / frame-ancestors) | sedang |
| W-H05/06/07 | X-Content-Type-Options / Referrer-Policy / Permissions-Policy tidak ada | rendah / rendah / info |
| W-A07-01 | Cookie tanpa Secure/HttpOnly/SameSite | sedang |
| W-H02 | CORS `*` + kredensial | tinggi |
| W-H09 | Versi perangkat lunak terungkap (Server / X-Powered-By) | rendah |
| W-H03 | Berkas sensitif terekspos (`.git`, `.env`, dll.) | kritis / tinggi |
| W-H08 | Redirect keluar host target | rendah |

Postur = tingkat tertinggi + jumlah per tingkat. Analisa Akhir memberi langkah perbaikan berbahasa awam.

## API (integrasi WASPADA)

Jalan sebagai service di `127.0.0.1:8002` (lokal) atau service `web-scanner` di `docker-compose.yml`.
Pola sama dengan apk-scanner: pemindaian sinkron di threadpool + timeout, riwayat di SQLite.

```bash
cd web-scanner/backend && .venv/bin/uvicorn main:app --port 8002
```

| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/webscan` | Body JSON `{ "target": "...", "authorized": true, "periksa_berkas": true, "delay": 0.5 }`. `403` bila `authorized` tak di-set atau target di luar lingkup |
| `GET` | `/webscans` | Riwayat ringkas |
| `GET` | `/webscans/{scan_id}` | Laporan lengkap |

```bash
curl -s -X POST localhost:8002/webscan \
  -H 'content-type: application/json' \
  -d '{"target":"http://localhost:3000","authorized":true}'
```

> Catatan Docker: untuk memindai aplikasi di `localhost` laptop, jalankan service ini **lokal**, bukan
> di container (di dalam container `localhost` = container itu, bukan host). Karena endpoint mengambil
> URL dari input, bila diekspos ke publik tambahkan allowlist egress (SSRF) — lihat `scope.py`.

## Arsitektur

Mencerminkan `apk-scanner/backend/`: `scope.py` (otorisasi & kunci lingkup) → `fetch.py` (ambil bukti
pasif) → `rules.py` (temuan berbukti) → `scoring.py` (postur) → `final.py` (analisa akhir) →
`report.py` (JSON). Rule diuji tanpa jaringan dengan amatan buatan (`tests/`).

## Langkah berikutnya (lihat konsep §12)

1. Cek aktif aman dalam lingkup berizin: integrasi **OWASP ZAP** + **Nuclei** (template non-intrusif).
2. SCA komponen → CVE (`osv-scanner` / `retire.js`).
3. API async (`POST /webscan`) + kartu hasil di dashboard WASPADA.

## Test

```bash
pytest -q
```
