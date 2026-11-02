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

## Menjalankan

Backend + PostgreSQL lewat Docker Compose (hanya butuh Docker Desktop):

```bash
docker compose up --build
```

API di http://localhost:8000 (docs: `/docs`), Postgres di `localhost:5432` (user/password/db: `waspada`).
Opsional: set `DISCORD_WEBHOOK_URL` sebelum `docker compose up` untuk alert ke Discord, `CORS_ORIGINS` (default `http://localhost:3000`).

Demo (skenario sintetis, deterministik):

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

Mulai demo dari data kosong: `docker compose down -v` (menghapus volume Postgres) lalu `docker compose up` lagi.

Dashboard (Next.js, alert real-time via SSE `/stream`):

```bash
cd frontend
npm install
npm run dev
```

Buka http://localhost:3000. URL backend bisa diganti lewat `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

Test (memakai database terpisah `waspada_test`): `docker compose exec backend pytest -q -p no:cacheprovider`

## Pemeriksa APK

Modul analisis statis APK (deteksi pencuri OTP / banking trojan) ada di [`apk-scanner/`](apk-scanner/README.md): service `apk-scanner` (port 8001) dan halaman dashboard `/apk`.
