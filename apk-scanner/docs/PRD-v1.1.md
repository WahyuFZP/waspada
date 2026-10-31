# PRD: APK Security Scanner (MVP)

Status: Draft v1.1 · Tanggal: 2026-10-30 · Pemilik: Wahyu Fikri Zeni Putra
Revisi dari v1 berdasarkan spike instalasi & uji API (lihat §15).

## Perubahan dari v1

| Bagian | Perubahan | Alasan |
|---|---|---|
| §3 | Androguard dipin **4.1.4** (PyPI), APKiD **3.2.0** lewat CLI, runtime **Docker `python:3.11-slim`** | Python 3.15 gagal memasang dependensi; branch `master` GitHub Androguard adalah v5 (belum rilis, API beda); APKiD sulit dipasang di Windows |
| §7 R02/R04/R05 | Dideteksi dari atribut `android:permission` pada `<service>`/`<receiver>` dan intent filter, **bukan** dari daftar permission | `BIND_*` bukan `<uses-permission>`; `get_permissions()` tidak pernah memuatnya, sehingga rule v1 tidak akan pernah terpicu |
| §7 R01 | Bukti tambahan: receiver dengan intent `SMS_RECEIVED` | Lebih kuat dari sekadar permission |
| §7 R08 | Hanya kategori APKiD `packer`, `obfuscator`, `protector` | Aplikasi sah (F-Droid) ditandai `r8 without marker (suspicious)` di kategori `compiler`; tanpa filter, R08 false positive |
| §7 R09 | Definisi pasti + daftar pengecualian | Aplikasi sah memuat banyak URL biasa (mis. `api.jamendo.com`, `schemas.android.com`) |
| §7 R10, R11 | Rule baru: kirim SMS diam-diam, kirim data ke bot Telegram | Dua pola paling khas pencuri OTP di Indonesia (APK undangan/kurir/tilang) |
| §9 | `min_sdk`/`target_sdk` boleh `null` | APK uji nyata tidak mencantumkan `targetSdkVersion` |
| §12 | Test rule & skor memakai data buatan (tanpa APK); fixture crafted dibuat dengan apktool | Test cepat, fixture mudah dibuat |

## 1. Tujuan

Alat **static analysis** untuk menilai apakah sebuah file APK menunjukkan **indikasi berbahaya**, khususnya pola malware/phishing yang dirancang mencuri OTP dan data input aplikasi perbankan (banking trojan). Alat **tidak pernah menjalankan/menginstall APK** dan **tidak mengambil OTP/data pribadi**; ia hanya membaca isi APK secara statis dan menghasilkan skor risiko berbasis bukti plus laporan JSON.

Output adalah **indikasi untuk ditinjau manusia**, bukan vonis malware final.

## 2. Non-Goals (eksplisit TIDAK dibuat di MVP)

- Dynamic analysis / sandbox / emulator (tidak ada eksekusi APK).
- Multi-user, login, role.
- Deteksi kemiripan ikon/brand app (ML).
- Integrasi API eksternal (VirusTotal, dll). File pengguna tidak dikirim ke pihak mana pun.
- Decompile DEX ke Java penuh.
- Analisis signing certificate (ditunda ke v2).
- Split APK (`.apks`, `.xapk`): ditolak dengan pesan jelas (ditunda ke v2).

## 3. Tech Stack

- Runtime: **Docker**, image dasar `python:3.11-slim` (Linux). Diuji: semua dependensi terpasang dengan `pip` saja.
- Backend: Python 3.11 · FastAPI (REST) · **Androguard `==4.1.4`** (PyPI, Apache-2.0; jangan mengikuti README branch `master` GitHub karena itu Androguard 5 dengan API berbeda) · **APKiD `==3.2.0`** (dipanggil sebagai CLI `apkid -j`, lisensi GPL/komersial; tidak ada API Python resmi) · `yara-python-dex` (otomatis ikut APKiD)
- Penyimpanan: **SQLite** (riwayat scan), file JSON laporan di disk
- Dashboard: Next.js (App Router) · single-user lokal, tanpa auth
- Test: pytest
- Bahasa UI & laporan: Indonesia

## 4. Alur Pengguna

1. User buka dashboard → upload file `.apk`.
2. Backend validasi → parse → jalankan rule engine → hitung skor.
3. Hasil tersimpan ke SQLite + file JSON; dashboard tampilkan skor, daftar temuan (dengan bukti), dan metadata.
4. User bisa lihat daftar scan sebelumnya dan buka ulang laporannya.

## 5. Arsitektur & Struktur File

```
apk-scanner/
├── docker-compose.yml          # backend (python:3.11-slim) + frontend
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt        # androguard==4.1.4, apkid==3.2.0, fastapi, uvicorn, pytest
│   ├── main.py                 # FastAPI: POST /scan, GET /scans, GET /scans/{id}
│   ├── validator.py            # validasi file APK
│   ├── parser.py               # wrapper Androguard: manifest, permission, komponen, intent filter, strings
│   ├── rules.py                # definisi rule + evaluasi (rule engine)
│   ├── scoring.py              # hitung skor dari temuan
│   ├── packer.py               # jalankan CLI `apkid -j`, ambil kategori packer/obfuscator/protector
│   ├── report.py               # susun JSON sesuai schema
│   ├── db.py                   # SQLite: simpan/ambil riwayat
│   ├── models.py               # dataclass Finding, ScanResult
│   └── tests/
│       ├── test_validator.py
│       ├── test_parser.py
│       ├── test_rules.py
│       ├── test_scoring.py
│       └── fixtures/           # APK contoh (benign + crafted-suspicious)
```

Dashboard tidak dibuat sebagai aplikasi Next.js terpisah: dibangun sebagai halaman `/apk` dan `/apk/[id]` di aplikasi Next.js WASPADA (`frontend/app/apk/`), memakai tema dan komponen yang sama. Backend berjalan sebagai service `apk-scanner` di `docker-compose.yml` root (port 8001).

Backend adalah sumber kebenaran; frontend hanya menampilkan JSON dari API.
Backend berjalan di container: APK berasal dari luar dan tidak tepercaya, jadi bila ada celah di parser, dampaknya terkurung di container.

## 6. Pipeline Analisis (backend)

1. **Validasi** (`validator.py`): file adalah ZIP valid, berisi `AndroidManifest.xml` dan `classes.dex`. Tolak kalau tidak. Batas ukuran file: 150 MB. Batas total ukuran terekstrak (dibaca dari central directory ZIP, tanpa ekstraksi): 500 MB, untuk menolak zip bomb. File disimpan dengan nama **SHA-256**, bukan nama asli (mencegah path traversal); APK dibaca dari memori/arsip, tidak diekstrak ke disk.
2. **Hash** (`parser.py`): SHA-256 dari file APK.
3. **Parse manifest** (Androguard 4.1.4, `androguard.core.apk.APK`):
   - `get_package()`, `get_androidversion_name()`, `get_androidversion_code()`, `get_min_sdk_version()`, `get_target_sdk_version()` (boleh `None`).
   - `get_permissions()`: daftar `<uses-permission>`.
   - `get_activities()`, `get_services()`, `get_receivers()`.
   - `get_intent_filters("service"|"receiver", nama)`: action per komponen.
   - `get_android_manifest_xml()`: atribut `android:permission` per `<service>`/`<receiver>` (namespace `{http://schemas.android.com/apk/res/android}`).
4. **Ekstrak strings** (`androguard.core.dex.DEX(bytes).get_strings()` untuk setiap DEX dari `get_all_dex()`): URL (`https?://...`), IPv4, dan string penanda (lihat R10, R11).
5. **Packer** (`packer.py`): jalankan `apkid -j <file>` sebagai subprocess (timeout 60 detik), baca `files[].matches`, ambil hanya kategori `packer`, `obfuscator`, `protector`. Kategori lain (`compiler`, `anti_vm`, dst.) dicatat sebagai info tanpa bobot.
6. **Rule engine** (`rules.py`): jalankan semua rule atas data di atas → daftar `Finding`.
7. **Scoring** (`scoring.py`): jumlahkan bobot temuan → skor 0–100 + level.
8. **Report** (`report.py`): susun JSON. Simpan ke SQLite + file.

## 7. Rule Engine: daftar rule MVP

Setiap rule menghasilkan `Finding` **hanya jika terpicu**, dengan bukti konkret (permission/komponen/string yang ditemukan). Bobot = kontribusi ke skor.

| ID | Rule | Pemicu | Bobot |
|----|------|--------|-------|
| R01 | Baca SMS | permission `READ_SMS` dan/atau `RECEIVE_SMS`; bukti tambahan bila ada receiver dengan action `android.provider.Telephony.SMS_RECEIVED` | 20 |
| R02 | Accessibility service | `<service>` dengan `android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"` **atau** intent filter action `android.accessibilityservice.AccessibilityService` | 20 |
| R03 | Overlay layar | permission `SYSTEM_ALERT_WINDOW` | 15 |
| R04 | Baca notifikasi | `<service>` dengan `android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"` **atau** action `android.service.notification.NotificationListenerService` | 15 |
| R05 | Device admin | `<receiver>` dengan `android:permission="android.permission.BIND_DEVICE_ADMIN"` **atau** action `android.app.action.DEVICE_ADMIN_ENABLED` | 15 |
| R06 | Dropper | permission `REQUEST_INSTALL_PACKAGES` | 10 |
| R07 | **Kombinasi banking-trojan** | minimal 2 dari {R01, R02, R03, R04, R10} terpicu bersamaan | +25 (bonus) |
| R08 | Packer/obfuscator | APKiD melaporkan kategori `packer`, `obfuscator`, atau `protector` | 15 |
| R09 | IP/URL mencurigakan | IPv4 publik literal (bukan `127.*`, `10.*`, `172.16–31.*`, `192.168.*`, `0.*`) atau URL ke layanan shortlink (`bit.ly`, `s.id`, `tinyurl.com`, dst.), **setelah** mengecualikan domain umum (`schemas.android.com`, `android.com`, `google.com`, `googleapis.com`, `w3.org`, `apache.org`, dst.; daftar di konfigurasi) | 10 |
| R10 | Kirim SMS diam-diam | permission `SEND_SMS` **dan** string `sendTextMessage` atau `sendMultipartTextMessage` di DEX | 20 |
| R11 | Kirim data ke bot Telegram | string `api.telegram.org/bot` **atau** pola token bot `\d{8,10}:[A-Za-z0-9_-]{35}` di DEX/resources | 30 |

Catatan:
- R07 adalah inti deteksi banking trojan: satuan permission wajar, **kombinasinya** yang berbahaya.
- R11 berbobot tertinggi: aplikasi sah hampir tidak pernah mengirim data ke bot Telegram, sementara pola ini paling sering dipakai pencuri OTP lokal. Token yang ditemukan **hanya dicatat sebagai bukti** (disamarkan di laporan, mis. `123456789:AA…xyz`) dan **tidak pernah dipakai** untuk mengakses bot.
- Daftar permission "dangerous" lain (location, contacts, camera) dicatat di laporan sebagai info, **tanpa bobot**, agar false-positive rendah.

## 8. Scoring (`scoring.py`)

- Skor = min(100, Σ bobot temuan terpicu).
- Level:
  - 0–29: **Rendah**
  - 30–59: **Sedang**
  - 60–100: **Tinggi**
- Skor **berbasis bukti**: setiap angka bisa ditelusuri ke daftar `bukti` di tiap temuan. Tidak ada komponen skor tanpa rule yang memicunya.
- Contoh: SMS (R01 20) + Accessibility (R02 20) + kombinasi (R07 25) = 65 → **Tinggi**. Satu permission SMS saja = 20 → **Rendah**.

## 9. Schema Laporan JSON

```json
{
  "schema_version": "1.1",
  "scan_id": "uuid",
  "scanned_at": "2026-10-30T10:50:00+07:00",
  "file": {
    "nama": "contoh.apk",
    "ukuran_bytes": 5242880,
    "sha256": "..."
  },
  "aplikasi": {
    "package": "com.example.app",
    "version_name": "1.0",
    "version_code": 1,
    "min_sdk": 21,
    "target_sdk": null
  },
  "permission": {
    "semua": ["android.permission.READ_SMS", "..."],
    "berbahaya": ["android.permission.READ_SMS"]
  },
  "packer": { "terdeteksi": true, "detail": ["Jiagu"], "info_lain": { "compiler": ["r8 without marker (suspicious)"] } },
  "url_ip": ["http://1.2.3.4/c2", "https://login-bank.example"],
  "temuan": [
    {
      "rule_id": "R01",
      "judul": "Aplikasi dapat membaca SMS",
      "tingkat": "tinggi",
      "bobot": 20,
      "bukti": ["android.permission.READ_SMS", "android.permission.RECEIVE_SMS", "receiver .SmsReceiver: android.provider.Telephony.SMS_RECEIVED"],
      "penjelasan": "Permission SMS sering dipakai untuk mencuri OTP yang dikirim via SMS."
    }
  ],
  "skor": 65,
  "level_risiko": "Tinggi",
  "catatan": "Hasil ini adalah indikasi static-analysis untuk ditinjau manusia, bukan vonis malware final."
}
```

`version_code`, `min_sdk`, `target_sdk` dikonversi ke integer; `null` bila tidak dicantumkan di manifest.

## 10. API

- `POST /scan`: body file APK (multipart). Response: ScanResult JSON (schema §9). `422` untuk file yang bukan APK valid, `413` untuk file terlalu besar.
- `GET /scans`: daftar ringkas scan (scan_id, nama file, skor, level, waktu).
- `GET /scans/{id}`: ScanResult lengkap.

## 11. Dashboard (Next.js)

- **Halaman Upload**: drag-drop APK, tombol scan, progress.
- **Halaman Hasil**: kartu skor + level (warna per level, selalu dengan label teks), tabel temuan dengan bukti & penjelasan bahasa awam, metadata aplikasi, daftar permission berbahaya, URL/IP, status packer. Tombol download JSON.
- **Halaman Riwayat**: tabel scan sebelumnya (dari `GET /scans`), klik → buka hasil.

## 12. Unit Test (acceptance)

- `test_validator`: tolak file non-APK (txt, zip tanpa manifest, zip bomb kecil buatan); terima APK valid.
- `test_parser`: SHA-256 benar untuk file fixture; package, versi, permission, receiver, dan intent filter ter-parse sesuai manifest fixture; `target_sdk` `None` tidak membuat error.
- `test_rules` (input: dict hasil parse buatan, **tanpa APK**, supaya cepat):
  - `READ_SMS` memicu R01; SMS + Accessibility memicu R01+R02+R07.
  - Service dengan `android:permission=BIND_ACCESSIBILITY_SERVICE` tanpa `<uses-permission>` tetap memicu R02.
  - APKiD hanya `compiler: r8 without marker (suspicious)` **tidak** memicu R08.
  - URL `https://schemas.android.com/...` tidak memicu R09; `http://203.0.113.10/x` memicu R09.
  - String `api.telegram.org/bot` memicu R11, dan token disamarkan di bukti.
  - Data bersih tidak memicu apa pun.
- `test_scoring`: kombinasi temuan menghasilkan skor & level yang benar; skor di-cap di 100.
- Fixtures:
  - **Benign**: APK uji dari repo Androguard (tag `v4.1.4`, `tests/data/APK/`), mis. `com.politedroid_4.apk` (18 KB) dan `com.teleca.jamendo_35.apk` (416 KB). Diunduh saat setup test dengan checksum, atau disimpan dengan atribusi sumber.
  - **Crafted-suspicious** (2 buah, buatan sendiri, tanpa kode jahat): bongkar APK benign dengan **apktool**, tambahkan `<uses-permission>` SMS/`SEND_SMS`/`SYSTEM_ALERT_WINDOW`, `<service>` accessibility, dan string `api.telegram.org/bot`, lalu rakit ulang (`apktool b`). Tidak perlu ditandatangani karena hanya dianalisis statis.
  - **Tidak** memakai sampel malware asli di repo.

## 13. Definition of Done (MVP)

- [ ] `docker compose up` menjalankan backend + dashboard.
- [ ] Upload APK via dashboard → dapat skor + temuan + JSON.
- [ ] Semua 11 rule (§7) jalan dan menghasilkan bukti.
- [ ] Riwayat scan tersimpan di SQLite & bisa dibuka ulang.
- [ ] Laporan JSON sesuai schema §9.
- [ ] Semua unit test §12 lulus.
- [ ] README: cara menjalankan dengan Docker, plus atribusi lisensi pihak ketiga (Androguard Apache-2.0, APKiD GPL/komersial, fixture Androguard).

## 14. Risiko & Batasan

- **False positive**: app sah juga bisa minta SMS/Accessibility. Mitigasi: scoring kombinasi (R07), filter kategori APKiD (R08), daftar pengecualian domain (R09), hasil disajikan sebagai indikasi, bukan vonis.
- **False negative**: malware ter-obfuscate berat bisa menyembunyikan string/permission dinamis, atau mengunduh muatan setelah terpasang. Di luar jangkauan static analysis MVP. Dicatat di laporan bila packer terdeteksi (R08).
- **Versi dependensi**: Androguard 5 (branch `master`) mengubah API; tetap pin `androguard==4.1.4` sampai v5 dirilis dan diuji. Python 3.15 belum didukung dependensi (pyyaml gagal di-build).
- **Lisensi**: APKiD berlisensi GPL/komersial. Dipanggil sebagai proses terpisah dan dicatat di README; bila repo dirilis open source, gunakan lisensi yang kompatibel atau evaluasi ulang.
- **Etika**: alat hanya membaca APK. Token/URL pelaku yang ditemukan adalah bukti untuk dilaporkan (bank terkait, BSSN, aduan Komdigi, Telegram), **tidak** dipakai untuk mengakses sistem pelaku.
- Static-only: perilaku runtime (mis. permission yang diminta saat jalan) tidak terlihat. Ini batasan desain yang disengaja.

## 15. Hasil spike (2026-10-30)

Diuji di container `python:3.11-slim` dengan `pip install androguard==4.1.4 apkid==3.2.0` (tanpa paket sistem tambahan).

| Hal | Hasil |
|---|---|
| Instalasi | Berhasil: androguard 4.1.4, apkid 3.2.0, yara-python-dex 1.1.0 |
| Python 3.15 (Windows) | Gagal: `Failed building wheel for pyyaml` |
| Waktu parse manifest + strings | 0,02–0,04 detik per APK uji |
| `com.politedroid_4.apk` | package `com.politedroid`, versi 1.3 (4), min SDK 3, target SDK `None`, permission `READ_CALENDAR` + `RECEIVE_BOOT_COMPLETED`, receiver dengan action `BOOT_COMPLETED`, 238 string DEX |
| `com.teleca.jamendo_35.apk` | package `com.teleca.jamendo`, versi `1.0.4 [BETA]` (35), min/target SDK 4/8, 5 permission, 2 service, 2.555 string DEX, URL sah `api.jamendo.com` dll. |
| Output `apkid -j` | `{"apkid_version": "3.2.0", "files": [{"filename": "<apk>!classes.dex", "matches": {"compiler": ["dx", "r8 without marker (suspicious)"]}}], "rules_sha256": "..."}` |
| Catatan APKiD | Aplikasi sah ditandai `r8 without marker (suspicious)` di kategori `compiler`, dasar filter R08 |
