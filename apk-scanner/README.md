# WASPADA: Pemeriksa APK (APK Security Scanner, MVP)

Analisis **statis** file APK dari luar Play Store untuk menemukan indikasi pencuri OTP dan banking trojan:
membaca SMS, layanan Aksesibilitas, overlay, pembaca notifikasi, kirim SMS diam-diam, dan pengiriman data ke bot Telegram.
APK **tidak pernah dipasang atau dijalankan**. Hasilnya indikasi untuk ditinjau manusia, bukan vonis malware final.

Setiap scan juga menghasilkan **Analisa Akhir**: kesimpulan berbahasa awam (*Berbahaya*, *Mencurigakan*, atau
*Tidak ditemukan indikasi berbahaya*) beserta alasan dan langkah yang disarankan, disusun dari skor rule,
sertifikat penandatangan, cek hash ke MalwareBazaar (opsional), dan pengelompokan domain tujuan.

Spesifikasi lengkap: [docs/PRD-v1.2.md](docs/PRD-v1.2.md).

## Menjalankan

Backend berjalan di Docker (`python:3.11-slim`), sebagai service `apk-scanner` di `docker-compose.yml` root:

```bash
docker compose up -d --build apk-scanner
```

API di http://localhost:8001 (dokumentasi: `/docs`). Data (APK karantina bernama SHA-256, laporan JSON, `scans.db`) disimpan di volume Docker `apkdata`.

Dashboard ada di aplikasi Next.js WASPADA: halaman **http://localhost:3000/apk** (unggah + riwayat) dan `/apk/<scan_id>` (hasil).
URL backend bisa diganti lewat `NEXT_PUBLIC_APK_API_URL`.

### Cek hash ke MalwareBazaar (opsional)

Mati secara default. Untuk mengaktifkan, ambil kunci gratis di https://auth.abuse.ch, simpan di file `.env` di root repo:

```
ABUSECH_AUTH_KEY=kunci-anda
```

lalu jalankan ulang `docker compose up -d apk-scanner`. Hanya **hash SHA-256** yang dikirim, tidak pernah file APK.
Tanpa kunci, laporan menandai pemeriksaan ini "dilewati".

## API

| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/scan` | Multipart `file` (.apk, maks. 150 MB). Balikan laporan JSON schema 1.2 (termasuk `analisa_akhir` dan `tahap_gagal`). `422` bila bukan APK valid, `413` bila terlalu besar |
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
| R12 | Pola pencegat OTP: receiver `SMS_RECEIVED` + ≥2 pemberat (prioritas >0, `SEND_SMS`, `BOOT_COMPLETED`, `READ_PHONE_STATE`); ikut R07 | 25 |
| R13 | Meniru aplikasi resmi: package menumpang nama resmi / package resmi berkunci debug, label homoglyph, label menyebut merek lain; versi janggal & App Link palsu menguatkan | 20–60 |
| R14 | Muatan tersembunyi: berkas "gambar" berisi ZIP/DEX/ELF, atau DEX/ELF di `assets/` | 15–40 |
| R15 | Penanda uji antivirus EICAR | 30 |
| R16 | Jejak apktool (`apktool.yml`, `original/`): APK dirakit ulang | 10 |
| R17 | WebView tidak aman: `addJavascriptInterface` dan/atau `onReceivedSslError`+`proceed` (+akses file) | 20–60 |
| R18 | Lalu lintas tidak aman: `usesCleartextTraffic`, NSC `cleartextTrafficPermitted="true"`, CA pengguna (nilainya dibaca; config pengetat tidak tertandai) | 15–30 |
| R19 | Manifest lemah: `debuggable`, provider exported+grantUri, StrandHogg (`taskAffinity=""`+`singleTask`) | 10–30 |
| R20 | Anti-analisis: string root / emulator / Frida-Xposed / debugger, 10 per kategori | 10–30 |
| R21–R23 | Kapabilitas lazim: pustaka native (.so), layanan push FCM, pembacaan identitas perangkat — masing-masing Sedang sendirian dan menumpuk (pilihan sensitivitas; aplikasi Flutter + Firebase + analitik yang sah = 90, Tinggi) | 30 |

R01 bernilai 30 (bukan 20) bila ada receiver `SMS_RECEIVED`. Skor = min(100, jumlah bobot); 0–29 Rendah, 30–59 Sedang, 60–100 Tinggi.

Semua rule bisa dijalankan dari terminal tanpa Docker/API: `python cli.py app.apk` (mencetak `VERDICT=` per APK).

## Test

```bash
docker compose exec apk-scanner pytest -q -p no:cacheprovider
```

Test rule & skor memakai data buatan. Test parser dan API memakai dua APK uji resmi dari repo Androguard
(`com.politedroid_4.apk`, `com.teleca.jamendo_35.apk`, tag `v4.1.4`) yang diunduh ke `/tmp` di container saat test,
dengan checksum SHA-256 dipin. Repo ini **tidak** menyimpan sampel malware.

## Etika

- Hanya membaca APK; tidak menjalankan, tidak mengirim file ke layanan pihak ketiga. Satu-satunya data yang bisa
  keluar adalah hash SHA-256 ke MalwareBazaar, dan hanya bila `ABUSECH_AUTH_KEY` diatur.
- Token bot atau URL pelaku yang ditemukan adalah bukti untuk dilaporkan (bank terkait, BSSN, aduan Komdigi, Telegram),
  **bukan** untuk dipakai mengakses sistem pelaku.

## Lisensi pihak ketiga

| Komponen | Lisensi | Cara dipakai |
|---|---|---|
| [Androguard](https://github.com/androguard/androguard) 4.1.4 | Apache-2.0 | Library Python |
| [APKiD](https://github.com/rednaga/APKiD) 3.2.0 | GPL / komersial (dual) | Dipanggil sebagai CLI terpisah (`apkid -j`) |
| yara-python-dex 1.1.0 | Apache-2.0 | Dependensi APKiD |
| [MalwareBazaar](https://bazaar.abuse.ch) (abuse.ch) | Ketentuan layanan abuse.ch | API cek hash, opsional; hanya SHA-256 yang dikirim |
| [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF) | GPL-3.0 | **Tidak dipakai sebagai kode**; hanya acuan desain (isolasi galat per tahap) |
| APK uji dari repo Androguard | mengikuti repo Androguard | Diunduh saat test, tidak didistribusikan |
