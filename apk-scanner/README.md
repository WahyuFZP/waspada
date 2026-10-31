# WASPADA: Pemeriksa APK (APK Security Scanner, MVP)

Analisis **statis** file APK dari luar Play Store untuk menemukan indikasi pencuri OTP dan banking trojan:
membaca SMS, layanan Aksesibilitas, overlay, pembaca notifikasi, kirim SMS diam-diam, dan pengiriman data ke bot Telegram.
APK **tidak pernah dipasang atau dijalankan**. Hasilnya indikasi untuk ditinjau manusia, bukan vonis malware final.

Spesifikasi lengkap: [docs/PRD-v1.1.md](docs/PRD-v1.1.md).

## Menjalankan

Backend berjalan di Docker (`python:3.11-slim`), sebagai service `apk-scanner` di `docker-compose.yml` root:

```bash
docker compose up -d --build apk-scanner
```

API di http://localhost:8001 (dokumentasi: `/docs`). Data (APK karantina bernama SHA-256, laporan JSON, `scans.db`) disimpan di volume Docker `apkdata`.

Dashboard ada di aplikasi Next.js WASPADA: halaman **http://localhost:3000/apk** (unggah + riwayat) dan `/apk/<scan_id>` (hasil).
URL backend bisa diganti lewat `NEXT_PUBLIC_APK_API_URL`.

## API

| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/scan` | Multipart `file` (.apk, maks. 150 MB). Balikan laporan JSON schema 1.1. `422` bila bukan APK valid, `413` bila terlalu besar |
| `GET` | `/scans` | Riwayat ringkas |
| `GET` | `/scans/{scan_id}` | Laporan lengkap |

## Rule

| ID | Rule | Bobot |
|---|---|---|
| R01 | Baca SMS (`READ_SMS`/`RECEIVE_SMS`, bukti receiver `SMS_RECEIVED`) | 20 |
| R02 | Layanan Aksesibilitas (atribut service atau intent filter) | 20 |
| R03 | Overlay layar (`SYSTEM_ALERT_WINDOW`) | 15 |
| R04 | Pembaca notifikasi | 15 |
| R05 | Admin perangkat | 15 |
| R06 | Dropper (`REQUEST_INSTALL_PACKAGES`) | 10 |
| R07 | Kombinasi ≥2 dari R01/R02/R03/R04/R10 | +25 |
| R08 | Packer/obfuscator/protector (APKiD) | 15 |
| R09 | IP publik literal atau tautan pendek | 10 |
| R10 | Kirim SMS diam-diam (`SEND_SMS` + `sendTextMessage`) | 20 |
| R11 | Kirim data ke bot Telegram (token disamarkan di laporan) | 30 |

Skor = min(100, jumlah bobot); 0–29 Rendah, 30–59 Sedang, 60–100 Tinggi.

## Test

```bash
docker compose exec apk-scanner pytest -q -p no:cacheprovider
```

Test rule & skor memakai data buatan. Test parser dan API memakai dua APK uji resmi dari repo Androguard
(`com.politedroid_4.apk`, `com.teleca.jamendo_35.apk`, tag `v4.1.4`) yang diunduh ke `/tmp` di container saat test,
dengan checksum SHA-256 dipin. Repo ini **tidak** menyimpan sampel malware.

## Etika

- Hanya membaca APK; tidak menjalankan, tidak mengirim file ke layanan pihak ketiga.
- Token bot atau URL pelaku yang ditemukan adalah bukti untuk dilaporkan (bank terkait, BSSN, aduan Komdigi, Telegram),
  **bukan** untuk dipakai mengakses sistem pelaku.

## Lisensi pihak ketiga

| Komponen | Lisensi | Cara dipakai |
|---|---|---|
| [Androguard](https://github.com/androguard/androguard) 4.1.4 | Apache-2.0 | Library Python |
| [APKiD](https://github.com/rednaga/APKiD) 3.2.0 | GPL / komersial (dual) | Dipanggil sebagai CLI terpisah (`apkid -j`) |
| yara-python-dex 1.1.0 | Apache-2.0 | Dependensi APKiD |
| APK uji dari repo Androguard | mengikuti repo Androguard | Diunduh saat test, tidak didistribusikan |
