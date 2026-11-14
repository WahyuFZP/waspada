# Konsep: Pemeriksa Keamanan Web (Web Security Scanner) — modul WASPADA

Status: Draft konsep · Tanggal: 2026-11-03

Modul baru WASPADA yang **memeriksa kelemahan keamanan sebuah aplikasi web** supaya pemiliknya bisa
**memperbaikinya sebelum disalahgunakan pelaku**. Sejalan dengan etika pemeriksa APK: alat ini
**hanya memeriksa, tidak menyerang** — ia melaporkan *indikasi kerentanan beserta bukti dan cara
perbaikan*, bukan mengeksploitasi, mencuri data, atau merusak.

Dibangun mencerminkan pipeline `apk-scanner` yang sudah ada: **ekstraksi → rule engine (temuan
berbukti) → scoring → Analisa Akhir berbahasa awam → laporan JSON**. Sebagian besar deteksi
dikerjakan oleh mesin open-source yang sudah teruji (dipanggil sebagai proses terpisah), bukan
ditulis ulang.

---

## 1. Tujuan & batas tegas (authorization-first)

Alat ini **hanya boleh dijalankan terhadap aset yang kamu miliki atau yang kamu punya izin tertulis
untuk menguji** (web app sendiri, lingkungan staging, atau target dalam lingkup pentest resmi).
Memindai situs milik pihak lain tanpa izin melanggar hukum (di Indonesia: UU ITE) dan etika — itu
**di luar cakupan dan ditolak oleh alat**.

Prinsip, sejajar dengan pemeriksa APK:

- **Membantu pemilik memperbaiki**, bukan membantu penyerang menembus. Setiap temuan berujung pada
  langkah perbaikan.
- **Non-destruktif & aman secara bawaan**: utamakan pengamatan pasif; uji aktif dibatasi pada cek
  tak-merusak, ber-rate-limit, dan tidak pernah menghapus/mengubah data atau membebani server (tanpa
  uji DoS/brute-force masif).
- **Berbasis bukti**: setiap temuan mencantumkan apa yang *diamati* (header, versi, status, konfigurasi),
  bukan klaim tanpa bukti. Hasil adalah **indikasi untuk ditinjau manusia**, bukan vonis.
- **Lingkup terkunci**: hanya host/domain dalam daftar izin yang dipindai; tidak keluar lingkup.

## 2. Non-Goals (eksplisit TIDAK dibuat)

- Alat serang/penetrasi terhadap target pihak ketiga tanpa izin.
- Eksploitasi kerentanan: mencuri data, mengubah/menghapus data, mengambil alih akun, menanam
  backdoor, atau menjalankan muatan pada server target.
- Uji beban/penolakan layanan (DoS), brute-force kredensial masif, atau teknik mengelabui pertahanan
  (evasion) agar tidak terdeteksi.
- Menyimpan atau menyebarkan data sensitif yang kebetulan terlihat saat pemeriksaan (ditutup/di-mask
  di laporan, seperti token bot di pemeriksa APK).

## 3. Arsitektur (mencerminkan `apk-scanner`)

```
Scope & otorisasi  ->  Discovery  ->  Pemeriksaan pasif  ->  Cek aktif aman  ->  Komponen & CVE
       |                 (crawl        (header, TLS,         (templated,          (fingerprint
  daftar host izin        dalam         cookie, berkas        non-destruktif,      versi -> CVE)
  + konfirmasi            lingkup)      terekspos)            ber-rate-limit)
  kepemilikan)                                                     |
                                                                   v
                              Rule engine (Temuan berbukti)  ->  Scoring/postur  ->  Analisa Akhir  ->  Laporan JSON
```

Seperti `apk-scanner` memanggil `androguard` (library) dan `APKiD` (CLI terpisah), modul ini
**mengorkestrasi mesin pemeriksa yang sudah matang** dan menyatukan hasilnya ke satu skema temuan —
tidak menulis ulang kapabilitas pemindaian dari nol (lihat §9).

Isolasi galat per tahap tetap dipakai (pola MobSF yang sudah ada): satu tahap yang gagal dicatat di
`tahap_gagal`, tahap lain jalan terus.

## 4. Kategori kerentanan yang diperiksa (OWASP Top 10 2021 + higiene web)

Dijelaskan pada tingkat *apa kelemahannya, bagaimana dideteksi dengan aman, dan cara memperbaikinya*
— bukan cara mengeksploitasi.

| Kode | Kelemahan | Cara deteksi (aman, non-destruktif) | Perbaikan |
|---|---|---|---|
| **W-A01** | Kontrol akses lemah (termasuk IDOR, akses paksa ke halaman) | Dengan akun uji milik sendiri: cek apakah endpoint sensitif bisa diakses tanpa otorisasi yang sesuai; bandingkan akses antar-peran | Otorisasi di sisi server, *deny by default*, cek kepemilikan objek |
| **W-A02** | Kegagalan kriptografi / transport | Versi & cipher TLS (via `testssl.sh`/`sslyze`), HTTPS dipaksa atau tidak, HSTS, data sensitif lewat HTTP | TLS 1.2/1.3, cipher kuat, HSTS, enkripsi data saat transit & simpan |
| **W-A03** | Injeksi (SQL/perintah/XSS) | Lewat mesin DAST teruji dengan cek aman; laporan fokus ke titik input yang tidak ter-sanitasi | *Parameterized query*/prepared statement, validasi input, *output encoding*, CSP |
| **W-A04** | Desain tidak aman | Checklist: ada rate-limit di login, lockout, alur reset sandi aman, verifikasi sisi server | Terapkan kontrol sejak desain; *threat modeling* |
| **W-A05** | Salah konfigurasi keamanan | Header keamanan hilang, pesan galat verbose/stack trace, *directory listing*, berkas contoh/default, metode HTTP berlebih (mis. TRACE), panel admin terekspos | Harden konfigurasi, halaman galat generik, matikan listing, hapus berkas contoh |
| **W-A06** | Komponen usang/rentan | Fingerprint versi framework/library/CMS → cocokkan ke basis data CVE (`osv-scanner`, `retire.js`, Dependency-Check) | Perbarui, pasang SCA di CI, pantau CVE |
| **W-A07** | Kegagalan autentikasi & sesi | Flag cookie sesi (HttpOnly/Secure/SameSite), indikasi *session fixation*, kebijakan sandi, ketersediaan MFA, proteksi *credential stuffing* | Manajemen sesi aman, MFA, rate-limit, rotasi sesi saat login |
| **W-A08** | Kegagalan integritas data/software | Tidak ada Subresource Integrity (SRI) pada skrip pihak ketiga, kanal pembaruan tak bertanda tangan, indikasi *deserialization* tak aman | SRI, artefak bertanda tangan, hindari deserialisasi data tak tepercaya |
| **W-A09** | Logging & monitoring kurang | Checklist (sebagian sulit dilihat dari luar): apakah ada pencatatan & peringatan untuk kejadian keamanan | Logging terpusat, peringatan untuk pola mencurigakan |
| **W-A10** | SSRF | Deteksi fitur yang mengambil URL dari input pengguna; diuji aman dalam lingkup | Allowlist egress, blokir rentang internal & endpoint metadata cloud |
| **W-H01** | Header keamanan | CSP, HSTS, X-Content-Type-Options, frame-ancestors/X-Frame-Options, Referrer-Policy, Permissions-Policy | Set header sesuai kebutuhan aplikasi |
| **W-H02** | CORS longgar | `Access-Control-Allow-Origin: *` bersama kredensial, pantulan Origin tanpa validasi | Allowlist origin eksplisit, jangan gabungkan `*` dengan kredensial |
| **W-H03** | Berkas/informasi terekspos | `.git/`, `.env`, cadangan, `.DS_Store`, dump, dokumentasi API internal, banner versi `Server`/`X-Powered-By` | Hapus dari web root, batasi akses, sembunyikan banner |
| **W-H04** | *Open redirect* & clickjacking | Parameter redirect yang menerima URL eksternal; bisa di-*iframe* tanpa proteksi | Validasi tujuan redirect (allowlist), set `frame-ancestors` |

> Deteksi injeksi (W-A03) dan SSRF (W-A10) **tidak** menyertakan muatan serangan di konsep maupun
> implementasi laporan — alat menandai *lokasi input yang perlu diperiksa/diperbaiki* dan menyerahkan
> verifikasi mendalam ke mesin DAST resmi yang berjalan dalam lingkup berizin.

## 5. Skema Temuan (`Finding`) — mencerminkan `models.py`

```json
{
  "id": "W-A05-002",
  "kategori": "A05:2021 Security Misconfiguration",
  "cwe": "CWE-16",
  "judul": "Header Content-Security-Policy tidak ada",
  "tingkat": "sedang",                 // info | rendah | sedang | tinggi | kritis
  "keyakinan": "tinggi",               // rendah | sedang | tinggi
  "lokasi": { "url": "https://app-saya.example/", "parameter": null, "metode": "GET" },
  "bukti": ["Respons 200 tanpa header 'Content-Security-Policy'"],
  "dampak": "Tanpa CSP, skrip pihak ketiga yang tersuntik lebih mudah berjalan di browser korban.",
  "perbaikan": "Tambahkan header Content-Security-Policy yang membatasi sumber skrip; mulai dengan mode report-only.",
  "referensi": ["https://owasp.org/Top10/A05_2021-Security_Misconfiguration/", "CWE-16"]
}
```

Seperti pemeriksa APK: **setiap temuan hanya muncul bila terpicu**, membawa `bukti` konkret, dan
nilai sensitif di dalam bukti di-mask.

## 6. Scoring & postur risiko

- Tiap temuan punya `tingkat` (selaras pita CVSS): Info · Rendah · Sedang · Tinggi · Kritis.
- **Postur keseluruhan** = tingkat temuan tertinggi + ringkasan jumlah per tingkat (bukan sekadar
  penjumlahan, karena satu kerentanan Kritis sudah cukup serius). Tetap **berbasis bukti**: tiap
  angka tertelusur ke temuan.
- UI WASPADA sekarang 3 level (Rendah/Sedang/Tinggi); untuk web, petakan Kritis→Tinggi pada tampilan,
  atau perluas ke 5 level (keputusan desain UI).

## 7. Analisa Akhir berbahasa awam — mencerminkan `final.py`

Untuk pemilik aplikasi (bukan hanya analis): **status** (mis. "Perlu perbaikan segera" / "Beberapa
hal perlu dibenahi" / "Tidak ditemukan masalah berarti"), **"Mengapa"** (ringkasan temuan tinggi),
dan **"Yang perlu Anda lakukan"** (langkah perbaikan paling berdampak dulu). Nada: menuntun
perbaikan, bukan menakut-nakuti.

## 8. Mekanisme aman bawaan

- **Penegakan lingkup**: hanya host dalam daftar izin; subdomain/host lain di-skip dan dicatat.
- **Konfirmasi kepemilikan/otorisasi** sebelum cek aktif (mis. unggah berkas verifikasi atau rekam
  pernyataan izin pada job).
- **Rate-limit & timeout** per target; hormati `robots.txt` untuk discovery; mode "pasif saja"
  sebagai default paling aman.
- **Tanpa cek merusak**: tidak ada penghapusan data, perubahan state yang tak bisa dibatalkan, DoS,
  atau brute-force masif.
- **Audit log**: catat apa yang diperiksa, kapan, oleh siapa — agar pemeriksaan sendiri akuntabel.

## 9. Integrasi mesin (dipanggil terpisah, seperti APKiD)

| Mesin | Peran | Lisensi | Catatan |
|---|---|---|---|
| OWASP ZAP | DAST (pasif + aktif aman) via API/daemon | Apache-2.0 | Inti pemeriksaan aktif; jalankan dalam lingkup berizin |
| Nuclei | Cek berbasis template (misconfig, berkas terekspos, CVE) | MIT | Template komunitas; pilih yang non-intrusif |
| testssl.sh / sslyze | Postur TLS/sertifikat | GPL-2.0 / AGPL/other | Proses terpisah |
| Nikto | Berkas/konfigurasi server umum | GPL | Opsional |
| osv-scanner / retire.js / OWASP Dependency-Check | Komponen → CVE | Apache/MIT/Apache | SCA |
| nmap | Layanan & versi (bila lingkup mengizinkan) | NPSL | Hanya dengan izin jaringan |

Backend FastAPI + penyimpanan (SQLite/Postgres) + dashboard Next.js mengikuti pola modul `apk-scanner`.
Tinjau lisensi tiap mesin (beberapa GPL/AGPL) sebelum distribusi, seperti catatan lisensi APKiD.

## 10. Alur & API (mencerminkan `/scan`)

Pemindaian web berlangsung lama & asinkron (beda dari APK yang <5 detik), jadi berbasis job:

| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/webscan` | Body: `{ target, lingkup[], mode: "pasif"\|"aktif", konfirmasi_izin }` → `job_id`. Menolak target di luar lingkup/izin |
| `GET` | `/webscan/{job_id}` | Status + laporan (temuan, postur, analisa akhir) saat selesai |
| `GET` | `/webscans` | Riwayat pemeriksaan |

## 11. Risiko & etika

- **Legalitas & izin**: memindai tanpa izin melanggar hukum; otorisasi adalah syarat, bukan opsi.
  Untuk target pihak ketiga yang kebetulan rentan: **responsible disclosure** ke pemiliknya, bukan
  eksploitasi (sejajar dengan etika pelaporan temuan di pemeriksa APK: lapor ke bank/BSSN/Komdigi).
- **False positive/negative**: hasil adalah indikasi; verifikasi manual tetap perlu. Deteksi pasif
  bisa melewatkan kerentanan logika bisnis.
- **Penanganan data**: jangan simpan data sensitif yang terlihat; mask di laporan.
- **Beban target**: rate-limit; pemeriksaan tidak boleh mengganggu layanan produksi (utamakan staging).

## 12. Saran bertahap (MVP → lanjut)

1. **MVP pasif** (paling aman, cepat berguna): header keamanan, flag cookie, postur TLS, CORS, berkas
   terekspos, fingerprint versi → CVE. Semua tanpa cek aktif.
2. **Cek aktif aman** dalam lingkup berizin: integrasi ZAP + Nuclei (template non-intrusif).
3. **Analisa Akhir + dashboard** mengikuti pola `apk-scanner`.
4. **SCA & pemantauan berulang**: re-scan terjadwal, diff antar waktu.
