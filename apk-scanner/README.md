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
| R12 | Aplikasi judi online: ≥2 istilah taruhan (kasino, togel, sabung, …) + alur setor/tarik dana. Analisa Akhir selalu *Berbahaya* | 30 |
| R13 | Kunci rahasia server tertanam (mis. file `.env` di dalam APK). Hanya nama kunci yang dilaporkan | 10 |
| R14 | Berusaha menghindari pemeriksaan (APKiD: deteksi emulator, anti-debug, manipulasi resource) | 10 |
| R15 | Pola pencegat OTP: receiver `SMS_RECEIVED` + ≥2 pemberat (prioritas >0, `SEND_SMS`, `BOOT_COMPLETED`, `READ_PHONE_STATE`); tidak ikut R07 karena syaratnya sama dengan R01 | 25 |
| R16 | Meniru aplikasi resmi (aplikasi saudara resmi seperti WhatsApp Business dikecualikan): package menumpang nama resmi / package resmi berkunci debug, label homoglyph, label menyebut merek lain; versi janggal & App Link palsu menguatkan | 20–60 |
| R17 | Muatan tersembunyi: berkas "gambar" berisi ZIP/DEX/ELF, atau DEX/ELF di `assets/` | 15–40 |
| R18 | Penanda uji antivirus EICAR | 30 |
| R19 | Jejak apktool (`apktool.yml`, `original/`): APK dirakit ulang | 10 |
| R20 | WebView tidak aman: `addJavascriptInterface` dan/atau override `onReceivedSslError` (+akses file). Maks. 25 agar tidak memvonis sendirian: SDK iklan sah punya pola yang sama | 10–25 |
| R21 | Lalu lintas tidak aman: `usesCleartextTraffic`, NSC `cleartextTrafficPermitted="true"`, CA pengguna (nilainya dibaca; config pengetat tidak tertandai) | 15–30 |
| R22 | Manifest lemah: `debuggable`, provider exported+grantUri, StrandHogg (`taskAffinity=""`+`singleTask`) | 10–30 |
| R23 | Jejak alat analisis Frida/Xposed (cek root/emulator saja tidak dihitung: ada di Firebase Crashlytics) | 15 |
| R24–R26 | Kapabilitas lazim: pustaka native (.so), layanan push FCM, pembacaan identitas perangkat — bobot 30 tampil di laporan, tetapi sumbangan gabungannya ke skor dibatasi 29 (`scoring.KAP_MAKS`) | 30 |
| R27 | Manifest tidak terbaca walau arsip utuh (mungkin sengaja dirusak) | 20 |
| R28 | Tanda tangan tidak cocok dengan penerbit resmi (`signer_resmi.json`) | 50 |

Selain DEX dan resource, scanner juga membaca string di library native (`lib/*/*.so`, maks. 32 MB per file),
karena aplikasi Flutter menaruh logikanya di `libapp.so`. Tautan pendek tanpa `https://` (`bit.ly/…`) ikut tertangkap.

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
