# WASPADA: Threat-Informed SIEM

**W**ide-**A**rea **S**ignal **P**rocessing for **A**lerting and **D**omain **A**wareness: pengolahan sinyal area luas
untuk peringatan dan kesadaran domain siber. Dua modul: Pemantauan SIEM (di bawah) dan [Pemeriksa APK](#pemeriksa-apk).

SIEM ringan yang mengorelasikan **log keamanan internal**, **intelijen ancaman terbuka (CISA KEV)**, dan **OSINT berita** dalam satu pipeline: **ingest → normalisasi → korelasi → alert**.
Satu kejadian tampak biasa; rangkaiannya lintas sumber adalah ancaman.

Semua data demo **sintetis** (`demo: true`, tampil berlabel "Simulasi") atau berasal dari feed publik (RSS, CISA KEV). Aset di `assets.yaml` adalah contoh. Murni pemantauan defensif.

## Cara kerja

| Tahap | File | Isi |
|---|---|---|
| Ingest | `backend/app.py` (`POST /ingest`), `rss.py`, `kev.py`, `replay.py` | Record masuk via HTTP; field `kind` memilih parser |
| Normalisasi | `backend/normalize.py`, `backend/parsers.py`, `topics.yaml`, `assets.yaml` | Semua sumber → satu skema event (lihat di bawah) |
| Korelasi | `backend/engine.py` + `rules.yaml` | Sliding window per `group_by`, rule = urutan langkah (threshold / sequence / cross-source), plus teknik MITRE ATT&CK |
| Output | `backend/notify.py`, `backend/store.py` (PostgreSQL, JSONB), SSE | Discord webhook, tabel `alerts`, stream real-time ke dashboard |

Rule, kamus topik, dan inventaris aset ada di YAML: tambah rule tanpa menyentuh engine (restart backend setelah mengubah YAML).
Window dihitung dari **timestamp event**, bukan jam dinding, jadi replay demo deterministik.

### Sumber (`kind` di `POST /ingest`)

| `kind` | Input | Event yang dihasilkan |
|---|---|---|
| `news` (default) | Artikel `{timestamp, source, region, title, summary?, url?}` | `news.incident`, `news.diplomatic`, `news.military`, `news.economic` per topik |
| `auth` | `{line, timestamp?}`, satu baris auth.log sshd | `auth.failed`, `auth.success` (baris lain diabaikan) |
| `suricata` | Satu baris `eve.json` (`event_type: alert`) | `ids.scan`, `ids.exploit_attempt`, `ids.alert`; IP tujuan dipetakan ke host lewat `assets.yaml` |
| `kev` | Dibuat oleh `kev.py`: kecocokan CVE CISA KEV × produk di `assets.yaml` | `vuln.kev_match` |

### Skema event

```json
{
  "timestamp": "2026-10-22T09:12:30Z",
  "source": "suricata",
  "event_type": "ids.exploit_attempt",
  "host": "srv-web-01",
  "src_ip": "203.0.113.50",
  "dest_port": 80,
  "cve": "CVE-2021-41773",
  "title": "ET EXPLOIT Apache HTTP Server Path Traversal Attempt (CVE-2021-41773)",
  "demo": true,
  "raw": { "...record asli..." }
}
```

Berita memakai `region` dan `topic` sebagai pengganti `host`/`src_ip`.

### Rule

| Rule | Tipe | Severity | MITRE ATT&CK |
|---|---|---|---|
| Pemindaian port: ≥5 port berbeda dari satu IP dalam 5 menit | threshold | medium | T1046 |
| Eksploitasi pada aset rentan KEV: aset cocok CVE KEV → upaya eksploitasi | cross-source | high | T1190 |
| Brute force berhasil masuk: ≥10 login gagal → login berhasil, IP & host sama | sequence | high | T1110, T1078 |
| Intrusi berhasil pada aset rentan: KEV → eksploitasi → login berhasil | cross-source | critical | T1190, T1078 |
| Lonjakan pemberitaan: ≥5 artikel dari ≥3 media dalam 1 jam | threshold | medium | - |
| Insiden lalu respons diplomatik dalam 6 jam | sequence | high | - |
| Isu memanas lintas wilayah: insiden (dalam negeri) → diplomatik (asing) → militer | cross-source | critical | - |

## API (kontrak untuk frontend Next.js)

| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/ingest` | Satu record atau array record (lihat tabel sumber). Satu record tidak valid = seluruh batch ditolak (422). Event dengan `url` yang sudah ada dibuang |
| `GET` | `/events?limit=200` | Event terbaru |
| `GET` | `/alerts?limit=50` | Alert terbaru, termasuk event pendukung dan `mitre` |
| `GET` | `/stream` | SSE; `event: event` dan `event: alert`, data = JSON |

## Instalasi (untuk kolaborator)

### Prasyarat

| Alat | Versi | Catatan |
|---|---|---|
| Git | apa saja | |
| Docker Desktop | terbaru | Harus **sedang berjalan** sebelum perintah `docker compose`. Menjalankan PostgreSQL, backend SIEM, dan scanner APK |
| Node.js | 20 LTS atau lebih baru | Hanya untuk dashboard Next.js |

Python **tidak perlu** dipasang: semua kode Python berjalan di dalam container (Python 3.11).
Port yang harus kosong: `3000` (dashboard), `8000` (backend), `8001` (scanner APK), `5432` (PostgreSQL).

### Langkah

1. Clone repo:

   ```bash
   git clone https://github.com/WahyuFZP/waspada.git
   cd waspada
   ```

2. (Opsional) Buat file `.env` di root repo. File ini tidak ikut ke Git, dan semua isinya boleh dikosongkan:

   ```
   # alert SIEM ke Discord
   DISCORD_WEBHOOK_URL=
   # cek hash APK ke MalwareBazaar, kunci gratis di https://auth.abuse.ch
   ABUSECH_AUTH_KEY=
   ```

3. Jalankan backend, database, dan scanner APK (build pertama butuh beberapa menit):

   ```bash
   docker compose up -d --build
   docker compose ps
   ```

   Ketiga service (`db`, `backend`, `apk-scanner`) harus berstatus `Up`, dan `db` berstatus `healthy`.

4. Jalankan dashboard di terminal lain:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

   `npm ci` memasang versi paket persis sesuai `package-lock.json`.

5. Buka http://localhost:3000, lalu pilih modul **Pemantauan SIEM** atau **Pemeriksa APK**.
   Dashboard SIEM masih kosong sampai data demo diisi (lihat **Demo** di bawah).

| Alamat | Isi |
|---|---|
| http://localhost:3000 | Dashboard (landing, `/pemantauan`, `/apk`) |
| http://localhost:8000/docs | API backend SIEM |
| http://localhost:8001/docs | API scanner APK |
| `localhost:5432` | PostgreSQL (user/password/db: `waspada`, hanya untuk demo lokal) |

Semua port hanya bisa diakses dari komputer itu sendiri (`127.0.0.1`), bukan dari perangkat lain di Wi-Fi yang sama. Ini disengaja.

### Kalau ada masalah

| Gejala | Penyebab dan solusi |
|---|---|
| `failed to connect to the docker API` / `dockerDesktopLinuxEngine` | Docker Desktop belum berjalan. Buka Docker Desktop, tunggu sampai statusnya *running*, ulangi perintah |
| `npm run dev` memakai port 3001, bukan 3000 | Port 3000 dipakai proses lain. API **hanya menerima** dashboard dari `localhost:3000`, jadi hentikan proses lain itu dulu |
| Dashboard SIEM menampilkan "Terputus" | Backend belum jalan: cek `docker compose ps` dan `docker compose logs backend` |
| Unggah APK gagal "tidak dapat dijangkau" | Service `apk-scanner` belum jalan: cek `docker compose logs apk-scanner` |
| Scanner APK error *permission denied* di `/data` | Volume data dari versi lama (sebelum scanner berjalan sebagai non-root). Jalankan sekali: `docker run --rm -v waspada_apkdata:/data --user root waspada-apk-scanner chown -R 10001 /data`, lalu `docker compose up -d` |
| `npm ci` memberi peringatan `install-scripts ... unrs-resolver` | Aman diabaikan: skrip itu milik alat lint, bukan bagian aplikasi, dan dashboard tetap berjalan normal |
| Setelah `git pull`, perubahan backend/scanner tidak terasa | Build ulang image: `docker compose up -d --build` |

Opsional lain: `CORS_ORIGINS` (default `http://localhost:3000`).

### Demo

Skenario sintetis, deterministik:

```bash
docker compose exec backend python replay.py scenarios/intrusi.jsonl --delay 1
docker compose exec backend python replay.py scenarios/natuna.jsonl --delay 1.5
```

Sumber nyata:

```bash
docker compose exec backend python kev.py   # katalog CISA KEV terbaru x assets.yaml (aman diulang)
docker compose exec backend python rss.py   # polling 21 feed berita setiap 5 menit (feeds.yaml)
```

Jalankan replay `intrusi.jsonl` **sebelum** `kev.py`: event KEV dari skenario memakai URL yang sama dengan hasil `kev.py`, sehingga yang datang belakangan dibuang sebagai duplikat.

Mulai demo dari data kosong: `docker compose down -v` lalu `docker compose up -d` lagi. **Perhatian:** `-v` menghapus semua volume, termasuk database SIEM **dan** riwayat scan APK.

URL backend untuk dashboard bisa diganti lewat `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`) dan `NEXT_PUBLIC_APK_API_URL` (default `http://localhost:8001`).

### Test

SIEM (memakai database terpisah `waspada_test`): `docker compose exec backend pytest -q -p no:cacheprovider`

Scanner APK: `docker compose exec apk-scanner pytest -q -p no:cacheprovider`

## Pemeriksa APK

Modul analisis statis APK (deteksi pencuri OTP / banking trojan) ada di [`apk-scanner/`](apk-scanner/README.md): service `apk-scanner` (port 8001) dan halaman dashboard `/apk`.
