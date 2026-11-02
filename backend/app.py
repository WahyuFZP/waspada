"""API WASPADA: POST /ingest (berita, log auth, Suricata, CISA KEV), GET /events, GET /alerts, GET /stream (SSE)."""
import asyncio
import json
import os

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import notify
from engine import Engine, load_rules
from normalize import load_topics, normalize
from parsers import load_assets
from store import Store

app = FastAPI(title="WASPADA OSINT-SIEM")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["*"], allow_headers=["*"])

topics = load_topics()
assets = load_assets()
# shortcut: state window hanya di memori, hilang saat restart; muat ulang dari tabel events jika perlu tahan restart
engine = Engine(load_rules())
store = Store(os.environ.get("DATABASE_URL", "postgresql://waspada:waspada@localhost:5433/waspada"))
subscribers: set[asyncio.Queue] = set()


def publish(kind, data):
    for q in subscribers:
        q.put_nowait((kind, data))


@app.post("/ingest")
async def ingest(payload: dict | list[dict] = Body(...)):
    records = payload if isinstance(payload, list) else [payload]
    normalized = []
    for i, record in enumerate(records):  # validasi semua dulu supaya batch tidak masuk setengah
        try:
            normalized += normalize(record, topics, assets)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, f"record #{i}: {exc}")
    # dedupe per event (bukan per record): url KEV baru dibuat oleh parser, tidak ada di record mentah
    batch = [e for e in normalized if not store.seen_url(e.get("url"))]

    alerts = []
    for event in batch:
        store.add_event(event)
        publish("event", event)
        for alert in engine.process(event):
            store.add_alert(alert)
            publish("alert", alert)
            alerts.append(alert)
    for alert in alerts:
        await notify.send(alert)
    return {"events": len(batch), "alerts": [a["id"] for a in alerts], "skipped_duplicates": len(normalized) - len(batch)}


@app.get("/events")
def get_events(limit: int = 200):
    return store.events(min(limit, 1000))


@app.get("/alerts")
def get_alerts(limit: int = 50):
    return store.alerts(min(limit, 500))


@app.get("/stream")
async def stream():
    q = asyncio.Queue()
    subscribers.add(q)

    async def gen():
        try:
            while True:
                try:
                    kind, data = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"event: {kind}\ndata: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"  # jaga koneksi tetap hidup lewat proxy
        finally:
            subscribers.discard(q)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
