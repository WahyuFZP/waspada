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
| Output | `backend/notify.py`, SQLite, SSE | Discord webhook, tabel `alerts`, stream real-time ke dashboard |

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

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/uvicorn app:app --reload
```

Opsional: set `DISCORD_WEBHOOK_URL` untuk alert ke Discord, `CORS_ORIGINS` (default `http://localhost:3000`).

Demo (skenario sintetis, deterministik):

```bash
.venv/Scripts/python replay.py scenarios/natuna.jsonl --delay 1.5
```

Dashboard (Next.js, alert real-time via SSE `/stream`):

```bash
cd frontend
npm install
npm run dev
```

Buka http://localhost:3000. URL backend bisa diganti lewat `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

Tanpa Python lokal, backend bisa jalan di Docker (lihat konfigurasi `backend` di `.claude/launch.json`).

Polling RSS nyata: `.venv/Scripts/python rss.py` (feed di `feeds.yaml`).

Test: `.venv/Scripts/pytest`
