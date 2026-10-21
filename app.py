"""API WASPADA: POST /ingest, GET /events, GET /alerts, GET /stream (SSE)."""
import asyncio
import json
import os

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import notify
from engine import Engine, load_rules
from normalize import load_topics, normalize
from store import Store

app = FastAPI(title="WASPADA OSINT-SIEM")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["*"], allow_headers=["*"])

topics = load_topics()
# shortcut: state window hanya di memori, hilang saat restart; muat ulang dari tabel events jika perlu tahan restart
engine = Engine(load_rules())
store = Store(os.environ.get("WASPADA_DB", "waspada.db"))
subscribers: set[asyncio.Queue] = set()


def publish(kind, data):
    for q in subscribers:
        q.put_nowait((kind, data))


@app.post("/ingest")
async def ingest(payload: dict | list[dict] = Body(...)):
    articles = payload if isinstance(payload, list) else [payload]
    fresh = [a for a in articles if not store.seen_url(a.get("url"))]
    batch = []
    for i, article in enumerate(fresh):  # validasi semua dulu supaya batch tidak masuk setengah
        try:
            batch += normalize(article, topics)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, f"artikel #{i}: {exc}")

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
    return {"events": len(batch), "alerts": [a["id"] for a in alerts], "skipped_duplicates": len(articles) - len(fresh)}


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
