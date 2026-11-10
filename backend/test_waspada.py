import json
import os
from pathlib import Path

# DB terpisah (dibuat oleh db/init.sql) supaya test tidak menghapus data demo
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "postgresql://waspada:waspada@localhost:5432/waspada_test")
for _k in ("DISCORD_WEBHOOK_URL", "OPENWA_URL", "OPENWA_API_KEY", "OPENWA_SESSION", "WA_ALERT_CHAT"):
    os.environ.pop(_k, None)  # test tidak boleh mengirim ke Discord atau WA sungguhan

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


def test_whatsapp_only_for_urgent_alerts_and_only_when_configured(monkeypatch):
    from notify import targets
    alert = {"rule": "Pemindaian diikuti login berhasil", "severity": "critical", "timestamp": "2026-11-10T02:00:00Z",
             "group": {"host": "srv-latihan", "src_ip": "172.18.0.7"}, "mitre": [{"id": "T1046", "name": "x"}],
             "events": [{"title": "baris log mentah yang tidak boleh ikut"}]}
    for k in ("OPENWA_URL", "OPENWA_API_KEY", "OPENWA_SESSION", "WA_ALERT_CHAT"):
        monkeypatch.delenv(k, raising=False)
    assert targets(alert) == []  # tanpa env: tidak ada kanal

    monkeypatch.setenv("OPENWA_URL", "http://host.docker.internal:2785/")
    monkeypatch.setenv("OPENWA_API_KEY", "kunci-uji")
    monkeypatch.setenv("OPENWA_SESSION", "waspada alert")
    monkeypatch.setenv("WA_ALERT_CHAT", "120363000000000000@g.us")
    [(name, url, payload, headers)] = targets(alert)
    assert url == "http://host.docker.internal:2785/api/sessions/waspada%20alert/messages/send-text"
    assert headers == {"X-API-Key": "kunci-uji"} and payload["chatId"] == "120363000000000000@g.us"
    assert "Pemindaian diikuti login berhasil" in payload["text"] and "T1046" in payload["text"]
    assert "baris log mentah" not in payload["text"]
    assert targets({**alert, "severity": "medium"}) == []  # medium tidak dikirim ke WA


def test_sequence_matches_events_in_the_same_second_regardless_of_arrival_order():
    # serangan cepat: nmap dan login dalam detik yang sama, dan pengirim mengirim auth.log sebelum eve.json
    from engine import Engine, load_rules
    engine = Engine([r for r in load_rules() if r["name"] == "Pemindaian diikuti login berhasil"])
    base = {"timestamp": "2026-11-10T01:34:00Z", "host": "srv-latihan", "src_ip": "172.18.0.9"}
    assert engine.process({**base, "event_type": "auth.success"}) == []
    alerts = [a for port in (21, 23, 80, 443, 3389) for a in engine.process({**base, "event_type": "ids.scan", "dest_port": port})]
    assert [a["rule"] for a in alerts] == ["Pemindaian diikuti login berhasil"]
    assert [e["event_type"] for e in alerts[0]["events"]] == ["ids.scan"] * 5 + ["auth.success"]

    # login yang jelas SEBELUM pemindaian tetap tidak dihitung
    engine = Engine(engine.rules)
    engine.process({**base, "timestamp": "2026-11-10T01:33:00Z", "event_type": "auth.success"})
    assert [a for port in (21, 23, 80, 443, 3389) for a in engine.process({**base, "event_type": "ids.scan", "dest_port": port})] == []


def test_auth_parser_reads_sshd_and_ignores_other_lines():
    ok = normalize({"kind": "auth", "line": "Oct 22 09:15:30 srv-web-01 sshd[1]: Accepted publickey for budi from 10.0.0.7 port 5 ssh2",
                    "timestamp": "2026-10-22T09:15:30Z"}, load_topics())
    assert [(e["event_type"], e["host"], e["user"], e["src_ip"]) for e in ok] == [("auth.success", "srv-web-01", "budi", "10.0.0.7")]
    bad_user = normalize({"kind": "auth", "line": "Oct 22 09:15:31 srv-web-01 sshd[1]: Failed password for invalid user admin from 10.0.0.7 port 5 ssh2"}, load_topics())
    assert bad_user[0]["event_type"] == "auth.failed" and bad_user[0]["user"] == "admin"
    assert normalize({"kind": "auth", "line": "Oct 22 09:15:32 srv-web-01 sshd[1]: pam_unix(sshd:session): session opened"}, load_topics()) == []


def test_suricata_rejects_bad_ip_and_kev_matches_assets():
    r = client.post("/ingest", json={"kind": "suricata", "event_type": "alert", "timestamp": "2026-10-22T09:00:00Z",
                                     "src_ip": "not-an-ip", "dest_ip": "10.10.1.20", "alert": {"signature": "x"}})
    assert r.status_code == 422

    from kev import match_kev
    from parsers import load_assets
    vulns = [{"cveID": "CVE-2024-21762", "vendorProject": "Fortinet", "product": "FortiOS and FortiProxy SSL-VPN"},
             {"cveID": "CVE-2000-0001", "vendorProject": "Other", "product": "FortiOS"}]
    assert [(m["host"], m["cve"]) for m in match_kev(vulns, load_assets()["hosts"], "2026-10-22T00:00:00Z")] == [("fw-01", "CVE-2024-21762")]


def test_suricata_host_prefers_inventory_then_sensor_then_dest_ip():
    from normalize import parse_ts
    from parsers import load_assets, parse_suricata
    base = {"event_type": "alert", "timestamp": "2026-11-04T02:00:00.123456+0000", "src_ip": "172.18.0.9",
            "alert": {"signature": "WASPADA SCAN"}}
    host = lambda **kw: parse_suricata({**base, **kw}, parse_ts, load_assets())[0]["host"]  # noqa: E731
    assert host(dest_ip="10.10.1.20", host="sensor-a") == "srv-web-01"
    assert host(dest_ip="172.18.0.4", host="srv-latihan") == "srv-latihan"
    assert host(dest_ip="172.18.0.4") == "172.18.0.4"
    assert host(dest_ip="172.18.0.4", host=123) == "172.18.0.4"


def test_intrusion_scenario_correlates_kev_ids_and_auth():
    severities = []
    for line in (SCENARIO.parent / "intrusi.jsonl").read_text(encoding="utf-8").splitlines():
        r = client.post("/ingest", json=json.loads(line))
        assert r.status_code == 200, r.text
        new = {a["id"]: a for a in client.get("/alerts").json()}
        severities += [(new[i]["rule"], new[i]["severity"]) for i in r.json()["alerts"]]
    assert severities == [("Pemindaian port", "medium"), ("Eksploitasi pada aset rentan KEV", "high"),
                          ("Brute force berhasil masuk", "high"), ("Intrusi berhasil pada aset rentan", "critical"),
                          ("Pemindaian diikuti login berhasil", "critical")]

    # brute force & intrusi punya timestamp sama, jadi cari berdasarkan nama rule, bukan posisi
    critical = next(a for a in client.get("/alerts").json() if a["rule"] == "Intrusi berhasil pada aset rentan")
    assert critical["group"] == {"host": "srv-web-01"}  # IP tujuan Suricata dipetakan ke host lewat assets.yaml
    assert [e["source"] for e in critical["events"]] == ["cisa_kev", "suricata", "auth"]
    assert [t["id"] for t in critical["mitre"]] == ["T1190", "T1078"]
    assert all(e["demo"] for e in critical["events"])

    # kev.py mengirim ulang CVE yang sama untuk host yang sama -> dibuang sebagai duplikat
    kev_line = json.loads((SCENARIO.parent / "intrusi.jsonl").read_text(encoding="utf-8").splitlines()[0])
    r = client.post("/ingest", json={**kev_line, "timestamp": "2026-10-23T00:00:00Z"})
    assert r.json()["skipped_duplicates"] == 1 and r.json()["events"] == 0


def test_invalid_article_rejected_whole_batch():
    # timestamp unik: tidak boleh sama dengan event dari test lain di DB test yang sama
    good = {"timestamp": "2026-10-25T08:00:00Z", "source": "a", "region": "domestic", "title": "Insiden di Papua"}
    r = client.post("/ingest", json=[good, {**good, "region": "mars"}])
    assert r.status_code == 422
    assert all(e["timestamp"] != good["timestamp"] for e in client.get("/events").json())


def test_geoip_scopes_for_internal_and_documentation_ips():
    import geoip
    assert geoip.lookup("10.0.0.7") == {"scope": "internal"}
    assert geoip.lookup("203.0.113.50") == {"scope": "reserved"}  # rentang dokumentasi, dipakai skenario demo


def test_geoip_public_ip_has_country_and_owner():
    import pytest

    import geoip
    if not geoip.COUNTRY:
        pytest.skip("database DB-IP belum diunduh (image dibangun tanpa internet)")
    g = geoip.lookup("8.8.8.8")
    assert g["scope"] == "public" and g["country_code"] == "US" and "Google" in (g["org"] or "")


def test_security_events_carry_geo_but_news_does_not():
    line = "Oct 22 09:15:30 srv-web-01 sshd[1]: Accepted publickey for budi from 10.0.0.7 port 5 ssh2"
    [e] = normalize({"kind": "auth", "line": line, "timestamp": "2026-10-22T09:15:30Z"}, load_topics())
    assert e["geo"] == {"scope": "internal"}
    news = normalize({"timestamp": "2026-10-21T08:00:00Z", "source": "x", "region": "domestic",
                      "title": "Navy warships near Natuna"}, load_topics())
    assert "geo" not in news[0]


def test_ingest_token_required_when_configured(monkeypatch):
    import sys
    monkeypatch.setattr(sys.modules["app"], "INGEST_TOKEN", "rahasia-uji")
    line = {"kind": "auth", "line": "Nov  4 09:15:31 srv-latihan sshd[1]: Failed password for latihan from 10.0.0.9 port 5 ssh2"}
    assert client.post("/ingest", json=line).status_code == 401
    assert client.post("/ingest", json=line, headers={"X-Ingest-Token": "salah"}).status_code == 401
    assert client.post("/ingest", json=line, headers={"X-Ingest-Token": "rahasia-uji"}).status_code == 200


def test_events_can_be_filtered_by_source():
    client.post("/ingest", json={"timestamp": "2026-11-04T08:00:00Z", "source": "media-uji", "region": "domestic",
                                 "title": "Navy warships near Natuna", "url": "https://example.com/filter-uji"})
    client.post("/ingest", json={"kind": "auth", "timestamp": "2026-11-04T08:01:00Z",
                                 "line": "Nov  4 08:01:00 srv-latihan sshd[1]: Failed password for latihan from 10.0.0.9 port 5 ssh2"})
    sources = {e["source"] for e in client.get("/events?sources=auth,suricata").json()}
    assert "auth" in sources and sources <= {"auth", "suricata"}  # berita "media-uji" tidak ikut
    assert "media-uji" in {e["source"] for e in client.get("/events").json()}


def test_alert_handling_appends_history_and_requires_note_to_close():
    alert_id = client.get("/alerts").json()[0]["id"]  # test skenario di atas sudah membuat alert
    url = f"/alerts/{alert_id}"
    assert client.patch(url, json={"status": "dibuang"}).status_code == 422
    assert client.patch(url, json={"status": "selesai"}).status_code == 422  # selesai wajib ada catatan
    assert client.patch("/alerts/tidak-ada", json={"status": "ditangani"}).status_code == 404

    client.patch(url, json={"status": "ditangani", "note": "  IP diblokir di firewall  "})
    alert = client.patch(url, json={"status": "selesai", "note": "Akun latihan direset"}).json()
    assert alert["status"] == "selesai"
    assert [(h["status"], h["note"]) for h in alert["handling"]] == [
        ("ditangani", "IP diblokir di firewall"), ("selesai", "Akun latihan direset")]
    assert next(a for a in client.get("/alerts").json() if a["id"] == alert_id)["status"] == "selesai"
