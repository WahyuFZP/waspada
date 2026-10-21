# WASPADA — OSINT-SIEM

Pipeline bergaya SIEM untuk berita: **ingest → normalisasi → korelasi → alert**.
Satu berita terlihat biasa; rangkaiannya lintas media dalam & luar negeri adalah isu yang memanas.

Semua data demo **sintetis** (ditandai `[SINTETIS]`) atau berita publik dari RSS. Murni pemantauan, bukan tool ofensif.

## Cara kerja

| Tahap | File | Isi |
|---|---|---|
| Ingest | `backend/app.py` (`POST /ingest`), `backend/rss.py` | Artikel masuk via HTTP atau polling RSS |
| Normalisasi | `backend/normalize.py` + `topics.yaml` | Artikel → event seragam: `topic` (entity) + `event_type` (`news.incident`, `news.diplomatic`, `news.military`, ...) |
| Korelasi | `backend/engine.py` + `rules.yaml` | Sliding window per topik, rule = urutan langkah (threshold / sequence / cross-source) |
| Output | `backend/notify.py`, `backend/store.py` (PostgreSQL, JSONB), SSE | Discord webhook, tabel `alerts`, stream real-time ke dashboard |

Rule dan kamus topik ada di YAML — tambah rule tanpa menyentuh engine.
Window dihitung dari **timestamp event**, bukan jam dinding, jadi replay demo deterministik.

### Skema event

```json
{
  "timestamp": "2026-10-21T09:15:03Z",
  "source": "antara",
  "region": "domestic",
  "event_type": "news.incident",
  "topic": "natuna",
  "title": "...",
  "url": "https://...",
  "raw": { "...artikel asli..." }
}
```

### Rule demo

| # | Rule | Tipe | Severity |
|---|---|---|---|
| 1 | Lonjakan pemberitaan: ≥5 artikel dari ≥3 media dalam 1 jam | threshold | medium |
| 2 | Insiden lalu respons diplomatik dalam 6 jam | sequence | high |
| 3 | Insiden (media dalam negeri) → diplomatik (media asing) → militer, dalam 24 jam | cross-source | critical |

## API (kontrak untuk frontend Next.js)

| Method | Path | Keterangan |
|---|---|---|
| `POST` | `/ingest` | Body: satu artikel atau array artikel `{timestamp, source, region, title, summary?, url?}` |
| `GET` | `/events?limit=200` | Event terbaru |
| `GET` | `/alerts?limit=50` | Alert terbaru, termasuk event pendukung |
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
docker compose exec backend python replay.py scenarios/natuna.jsonl --delay 1.5
```

Mulai demo dari data kosong: `docker compose down -v` (menghapus volume Postgres) lalu `docker compose up` lagi.

Dashboard (Next.js, alert real-time via SSE `/stream`):

```bash
cd frontend
npm install
npm run dev
```

Buka http://localhost:3000. URL backend bisa diganti lewat `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

Polling RSS nyata: `docker compose exec backend python rss.py` (feed di `feeds.yaml`).

Test (memakai database terpisah `waspada_test`): `docker compose exec backend pytest -q -p no:cacheprovider`
