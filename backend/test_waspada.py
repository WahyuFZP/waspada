import json
import os
from pathlib import Path

# DB terpisah (dibuat oleh db/init.sql) supaya test tidak menghapus data demo
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql://waspada:waspada@localhost:5432/waspada_test")
os.environ.pop("DISCORD_WEBHOOK_URL", None)

from fastapi.testclient import TestClient  # noqa: E402

from app import app, store  # noqa: E402
from normalize import load_topics, normalize  # noqa: E402

store.reset()
client = TestClient(app)
SCENARIO = Path(__file__).parent / "scenarios" / "natuna.jsonl"


def test_keyword_whole_word_and_plural():
    topics = load_topics()
    art = {"timestamp": "2026-10-21T08:00:00Z", "source": "x", "region": "domestic"}
    assert normalize({**art, "title": "Kritik warga soal Natuna"}, topics) == []  # "kri" bukan "kritik"
    events = normalize({**art, "title": "Navy warships near Natuna"}, topics)
    assert [e["event_type"] for e in events] == ["news.military"]


def test_natuna_scenario_escalates_medium_high_critical():
    severities = []
    for line in SCENARIO.read_text(encoding="utf-8").splitlines():
        r = client.post("/ingest", json=json.loads(line))
        assert r.status_code == 200, r.text
        severities += [a["severity"] for a in client.get("/alerts").json() if a["id"] in r.json()["alerts"]]
    assert severities == ["medium", "high", "critical"]

    critical = client.get("/alerts").json()[0]
    assert critical["rule"] == "Isu memanas lintas wilayah"
    assert [(e["event_type"], e["region"]) for e in critical["events"]] == [
        ("news.incident", "domestic"), ("news.diplomatic", "foreign"), ("news.military", "foreign")]

    # replay ulang: URL sama -> dibuang, tidak ada alert ganda
    r = client.post("/ingest", json=json.loads(SCENARIO.read_text(encoding="utf-8").splitlines()[0]))
    assert r.json() == {"events": 0, "alerts": [], "skipped_duplicates": 1}


def test_source_url_must_be_http_and_reaches_discord():
    art = {"timestamp": "2026-10-23T08:00:00Z", "source": "a", "region": "domestic", "title": "Insiden di Papua"}
    r = client.post("/ingest", json={**art, "url": "javascript:alert(1)"})
    assert r.status_code == 422

    from notify import discord_payload
    event = normalize({**art, "url": "https://example.com/berita/1"}, load_topics())[0]
    alert = {"rule": "r", "severity": "high", "group": {"topic": "papua"}, "timestamp": art["timestamp"], "events": [event]}
    assert "[Insiden di Papua](https://example.com/berita/1)" in discord_payload(alert)["embeds"][0]["description"]


def test_invalid_article_rejected_whole_batch():
    good = {"timestamp": "2026-10-22T08:00:00Z", "source": "a", "region": "domestic", "title": "Insiden di Papua"}
    r = client.post("/ingest", json=[good, {**good, "region": "mars"}])
    assert r.status_code == 422
    assert all(e["timestamp"] != good["timestamp"] for e in client.get("/events").json())
