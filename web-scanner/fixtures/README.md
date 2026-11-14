# Target Latihan Kerentanan Web — WASPADA

Web yang **sengaja salah-konfigurasi** sebagai target uji untuk [web-scanner](../backend/) pasif.
Analog dengan APK decoy di proyek ini: **jinak** (gaya EICAR) — tidak ada kode serangan, tidak ada
data asli, tidak mengubah apa pun. "Rentan"-nya murni dari **sinyal** yang diamati pemeriksa pasif.

Isi berkas umpan (`.env`, `.git/config`, dll.) adalah **nilai palsu** dan di-*inline* di
[`app.py`](app.py) — bukan folder `.git`/berkas `.env` nyata di disk, agar tidak membuat repo-git
bersarang atau menaruh berkas mirip-rahasia yang bisa salah ter-commit.

## Menjalankan

Hanya pustaka standar Python, tanpa dependensi:

```bash
python3 app.py
```

- `http://localhost:8003` — situs salah-konfigurasi (+ berkas umpan)
- `http://localhost:8004` — open-redirect ke host lain (demo W-H08; lihat catatan di bawah tabel)

Keduanya mengikat `127.0.0.1` saja — **jangan ekspos target rentan ke jaringan**.

## Memindai

Pastikan service web-scanner aktif di `:8002`, lalu salah satu:

```bash
curl -X POST localhost:8002/webscan -H 'content-type: application/json' \
  -d '{"target":"http://localhost:8003","authorized":true}'
```

Atau lewat dashboard `http://localhost:3000/web`, atau CLI:

```bash
cd ../backend && python cli.py http://localhost:8003 --authorized
```

Untuk demo W-H08, pindai juga `http://localhost:8004`.

## Kelemahan yang ditanam → temuan yang diharapkan (port 8003)

| Kelemahan ditanam | Temuan | Tingkat |
|---|---|---|
| Dilayani lewat HTTP polos | W-A02-01 | tinggi |
| CSP ada tapi longgar (wildcard, `unsafe-inline`/`unsafe-eval`) | W-H01-02 | sedang |
| Tanpa X-Frame-Options & frame-ancestors | W-H04 | sedang |
| X-Content-Type-Options tak dikirim | W-H05 | rendah |
| Referrer-Policy tak dikirim | W-H06 | rendah |
| Permissions-Policy tak dikirim | W-H07 | info |
| Cookie `SESSIONID` tanpa HttpOnly | W-A07-01 | sedang |
| Cookie `SESSIONID` SameSite=None tanpa Secure | W-A07-02 | sedang |
| CORS `*` + `Allow-Credentials: true` | W-H02 | tinggi |
| Banner `Server` + `X-Powered-By` berisi versi | W-H09 ×2 | rendah |
| Skrip/CSS pihak ketiga tanpa SRI | W-A08-01 | rendah |
| Pustaka JS usang & rentan (jQuery 3.4.1) | W-A06-01 | sedang |
| 6 berkas umpan ter-ekspos | W-H03 ×6 | kritis/tinggi |
| (port 8004) open-redirect ke host lain | W-H08 | rendah |

Postur yang diharapkan: **buruk** (ada temuan kritis dari `.git`/`.env` yang terekspos).

> **Catatan port 8004:** redirect-nya menuju host lain, jadi pemeriksa **berhenti dan tidak mem-follow**
> (lingkup dikunci ke host berizin). Yang dinilai adalah respons 302 dari :8004 sendiri (header keamanannya)
> ditambah W-H08, temuan pembeda yang menandai "redirect keluar host berizin".
> Memisahkan W-H08 murni tidak bisa: aturan ini baru menyala bila target redirect memberi respons,
> dan respons apa pun ikut memicu aturan dasar HTTP/header.

## Batasan (yang TIDAK bisa didemokan secara lokal)

HSTS (**W-A02-02**, dan versi "ada tapi lemah"-nya **W-A02-05**) dan sertifikat TLS segera-kedaluwarsa (**W-A02-04**) hanya relevan di HTTPS dan
butuh deployment HTTPS nyata dengan sertifikat **tepercaya** — pemeriksa (benar) **memverifikasi
TLS**, jadi menolak sertifikat self-signed di localhost.

Sertifikat **kedaluwarsa** (**W-A02-03**) bahkan tak bisa dimunculkan pemeriksa ini sama sekali:
httpx menolak koneksi ke sertifikat kedaluwarsa **sebelum** probe TLS sempat jalan, sehingga amatan
berhenti tanpa status dan aturan itu tak pernah tercapai. (Memperbaikinya berarti mengubah
`backend/fetch.py`/`rules.py` yang merupakan kontrak baku, jadi di sini cukup dicatat.)

Pemeriksa ini **pasif**: ia tidak menguji XSS/SQLi/dll. Target latihan karenanya tidak memuat
endpoint eksploitatif — itu ranah tahap aktif (ZAP/Nuclei) di
[`../../docs/web-scanner-concept.md`](../../docs/web-scanner-concept.md).

## Uji cepat (offline)

Guard-nya ikut di test backend, jadi drift pada aturan scanner langsung ketahuan:

```bash
cd ../backend && .venv/bin/pytest -q tests/test_vuln_fixture.py
```

Memastikan tiap berkas umpan masih cocok dengan tanda-isi deteksi pemeriksa. (Server `app.py`
sendiri murni pustaka standar — `python3 app.py` cukup, tanpa dependensi.)
