# WASPADA: Skema Data

Dokumen ini menjelaskan bentuk data yang mengalir dan tersimpan di WASPADA. Arsitektur dan alur antar-layanan ada di [ARCHITECTURE.md](ARCHITECTURE.md).

Ada dua penyimpanan terpisah:

| Modul | Penyimpanan | Isi |
|---|---|---|
| Pemantauan SIEM (`backend/`) | PostgreSQL 16, tabel `events` dan `alerts` (JSONB) | Event ternormalisasi dan alert hasil korelasi |
| Pemeriksa APK (`apk-scanner/`) | SQLite `scans.db` + file JSON per laporan, di volume `apkdata` | Laporan pemindaian APK |

---

## 1. Pemantauan SIEM

### 1.1 Record masuk (`POST /ingest`)

Satu record atau array record. Field `kind` memilih parser. Satu record tidak valid membuat seluruh batch ditolak (`422`). Bila backend diberi `INGEST_TOKEN`, request wajib membawa header `X-Ingest-Token` dengan nilai yang sama; tanpa itu `401`.

| `kind` | Field wajib | Contoh sumber |
|---|---|---|
| `news` (default) | `timestamp`, `source`, `region` (`domestic`/`foreign`), `title`; opsional `summary`, `url` (hanya `http`/`https`) | RSS media (`rss.py`) |
| `auth` | `line` (satu baris `auth.log` sshd); opsional `timestamp` | Log SSH server satuan |
| `suricata` | Satu baris `eve.json` dengan `event_type: "alert"`, `alert.signature`, `src_ip`, `dest_ip`; opsional `dest_port`, `alert.metadata.cve` | Sensor IDS Suricata |
| `kev` | `timestamp`, `host`, `cve`, `vendor`, `product`; opsional `ransomware` | Dibuat oleh `kev.py` (CISA KEV × `assets.yaml`) |

Field `demo: true` menandai data simulasi (dari `replay.py`); dashboard melabelinya "Simulasi".

### 1.2 Event ternormalisasi

Semua sumber dipetakan ke satu bentuk. Field yang tidak relevan untuk suatu sumber tidak ada.

```json
{
  "timestamp": "2026-10-22T09:12:30Z",
  "source": "suricata",
  "event_type": "ids.exploit_attempt",
  "title": "ET EXPLOIT Apache HTTP Server Path Traversal Attempt (CVE-2021-41773)",
  "host": "srv-web-01",
  "src_ip": "203.0.113.50",
  "dest_port": 80,
  "cve": "CVE-2021-41773",
  "geo": { "scope": "reserved" },
  "demo": true,
  "raw": { "...record asli...": "..." }
}
```

| Field | Tipe | Ada pada | Keterangan |
|---|---|---|---|
| `timestamp` | string ISO-8601 UTC (`...Z`) | semua | Waktu kejadian, bukan waktu masuk. Window korelasi dihitung dari field ini |
| `source` | string | semua | Nama media (huruf kecil), atau `auth` / `suricata` / `cisa_kev` |
| `event_type` | string | semua | Lihat tabel 1.3 |
| `title` | string | semua | Ringkasan yang dibaca manusia |
| `url` | string \| null | berita, KEV | Dipakai juga untuk membuang duplikat |
| `region` | `domestic` \| `foreign` | berita | Asal media |
| `topic` | string | berita | Kunci dari `topics.yaml` (mis. `natuna`) |
| `host` | string | auth, suricata, KEV | Nama aset dari `assets.yaml`; IP tujuan apa adanya bila tidak ada di inventaris |
| `src_ip` | string | auth, suricata | IP sumber, sudah divalidasi |
| `user` | string | auth | Akun yang mencoba login |
| `dest_port` | integer \| null | suricata | 0–65535 |
| `cve` | string \| null | suricata, KEV | Format `CVE-YYYY-NNNN` |
| `geo` | object | event yang punya `src_ip` | Lihat 1.4 |
| `demo` | boolean | semua | Data simulasi |
| `raw` | object | semua | Record mentah, untuk audit |

### 1.3 Jenis event

| `event_type` | Sumber | Arti |
|---|---|---|
| `news.incident`, `news.diplomatic`, `news.military`, `news.economic` | berita | Satu event per pasangan topik × kategori yang cocok |
| `auth.success`, `auth.failed` | auth | Login SSH berhasil / gagal |
| `ids.scan` | suricata | Signature mengandung `SCAN` |
| `ids.exploit_attempt` | suricata | Ada CVE, atau signature mengandung `EXPLOIT`/`ATTACK` |
| `ids.alert` | suricata | Peringatan IDS lain |
| `vuln.kev_match` | KEV | Aset memakai produk yang ada di katalog CISA KEV |

### 1.4 Lokasi IP (`geo`)

Ditambahkan saat normalisasi untuk setiap event yang punya `src_ip` (`backend/geoip.py`). Sumber data: DB-IP Lite (CC BY 4.0), dibaca **offline**; IP tidak dikirim ke layanan luar.

| `scope` | Kondisi | Field tambahan |
|---|---|---|
| `public` | IP publik | `country_code` (ISO, mis. `US`), `country` (nama Inggris), `asn` (nomor), `org` (pemilik jaringan); bisa `null` bila tidak ditemukan |
| `internal` | 10/8, 172.16/12, 192.168/16, 127/8, fc00::/7, ::1 | tidak ada |
| `reserved` | Rentang khusus lain yang bukan milik siapa pun, mis. 203.0.113.0/24 (dokumentasi, dipakai skenario demo) | tidak ada |

Lokasi tidak pernah ditebak untuk IP `internal` atau `reserved`. Event yang masuk sebelum fitur ini tidak punya `geo`.

### 1.5 Alert

Dibuat oleh `engine.py` saat rangkaian event dalam satu window cocok dengan rule di `rules.yaml`.

```json
{
  "id": "3f9c0a...",
  "rule": "Intrusi berhasil pada aset rentan",
  "severity": "critical",
  "mitre": [{ "id": "T1190", "name": "Exploit Public-Facing Application" }],
  "group": { "host": "srv-web-01" },
  "timestamp": "2026-10-22T09:20:00Z",
  "events": [ "...event pendukung, urut waktu..." ]
}
```

| Field | Keterangan |
|---|---|
| `id` | UUID hex |
| `rule` | Nama rule |
| `severity` | `low` / `medium` / `high` / `critical` |
| `mitre` | Teknik MITRE ATT&CK `[{id, name}]`, boleh kosong |
| `group` | Nilai field `group_by` rule, mis. `{src_ip, host}` |
| `timestamp` | Waktu event pendukung terakhir |
| `events` | Event pendukung lengkap (bukti) |

Rule ditulis di `rules.yaml`: `name`, `severity`, `window` (`5m`, `6h`, `30d`), `group_by`, `steps` (tiap langkah: `match`, `count`, `distinct`), `mitre`.

### 1.6 Tabel PostgreSQL

Dibuat otomatis oleh `backend/store.py`. Database `waspada_test` terpisah dibuat oleh `db/init.sql` untuk test.

```sql
CREATE TABLE events (
  id   BIGSERIAL PRIMARY KEY,
  ts   TIMESTAMPTZ NOT NULL,   -- = event.timestamp
  url  TEXT,                   -- = event.url, untuk membuang duplikat
  body JSONB NOT NULL          -- event lengkap (1.2)
);
CREATE INDEX events_url ON events (url);
CREATE INDEX events_ts  ON events (ts DESC);

CREATE TABLE alerts (
  id   TEXT PRIMARY KEY,       -- = alert.id
  ts   TIMESTAMPTZ NOT NULL,   -- = alert.timestamp
  body JSONB NOT NULL          -- alert lengkap (1.5)
);
```

### 1.7 Membaca event (`GET /events`)

| Parameter | Default | Arti |
|---|---|---|
| `limit` | 200 | Jumlah event terbaru |
| `sources` | semua | Daftar `source` dipisah koma, mis. `auth,suricata` (dipakai halaman `/log`) |

### 1.8 Stream real-time (`GET /stream`)

Server-Sent Events. `event: event` membawa satu event (1.2), `event: alert` membawa satu alert (1.5). Komentar `: ping` dikirim setiap 15 detik agar koneksi tetap hidup.

---

## 2. Pemeriksa APK

Spesifikasi lengkap laporan (schema `1.2`) ada di [apk-scanner/docs/PRD-v1.2.md §9](apk-scanner/docs/PRD-v1.2.md). Ringkasnya:

| Bagian laporan | Isi |
|---|---|
| `file` | Nama (tanpa path), ukuran, SHA-256 |
| `aplikasi` | Package, versi, SDK min/target |
| `permission` | Semua izin dan yang berisiko |
| `packer` | Hasil APKiD: packer/obfuscator, info lain (anti-emulator, dll.), galat |
| `url_ip` | URL dan IP yang tertanam |
| `temuan` | Daftar aturan R01–R14 yang terpicu, masing-masing dengan `bukti` |
| `skor`, `level_risiko` | 0–100; Rendah / Sedang / Tinggi |
| `analisa_akhir` | Status (Berbahaya / Mencurigakan / Tidak ditemukan indikasi berbahaya), alasan, saran, sertifikat, hasil cek hash MalwareBazaar, domain per kategori |
| `tahap_gagal` | Tahap analisis yang gagal; kosong bila semua berhasil |

Token bot dan nilai rahasia selalu disamarkan atau hanya disebut namanya.

### 2.1 Tabel SQLite `scans`

Dibuat oleh `apk-scanner/backend/db.py`. Laporan lengkap juga ditulis ke `reports/<scan_id>.json`, dan APK disimpan di karantina sebagai `apk/<sha256>.apk`.

```sql
CREATE TABLE scans (
  scan_id    TEXT PRIMARY KEY,
  scanned_at TEXT NOT NULL,     -- ISO-8601 WIB
  nama       TEXT NOT NULL,     -- nama file dari pengguna, tanpa path
  sha256     TEXT NOT NULL,
  skor       INTEGER NOT NULL,
  level      TEXT NOT NULL,     -- Rendah | Sedang | Tinggi
  report     TEXT NOT NULL      -- laporan JSON lengkap
);
```
