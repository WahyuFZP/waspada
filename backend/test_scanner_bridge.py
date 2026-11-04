"""Tes jembatan pemeriksa -> SIEM (#16): record scanner -> event -> alert. Murni normalize+engine, tanpa DB."""
import pytest

from engine import Engine, load_rules
from normalize import load_topics, normalize

REKAM = {"kind": "scanner", "scanner": "web", "timestamp": "2026-11-04T05:00:00Z", "host": "contoh.example",
         "severity": "critical", "title": "Pemeriksa Web: postur buruk di contoh.example",
         "url": "http://localhost:3000/web/x",
         "temuan": [{"judul": "Berkas sensitif terekspos: /.env", "tingkat": "kritis"}], "saran": ["Hapus .env"]}


def test_scanner_record_normalizes_and_alerts_critical():
    [ev] = normalize(REKAM, load_topics(), {"by_ip": {}})
    assert ev["event_type"] == "scanner.finding" and ev["severity"] == "critical" and ev["host"] == "contoh.example"
    alerts = Engine(load_rules()).process(ev)
    assert len(alerts) == 1 and alerts[0]["severity"] == "critical" and "kritis" in alerts[0]["rule"].lower()


def test_scanner_high_alerts_high_not_critical():
    [ev] = normalize({**REKAM, "severity": "high"}, load_topics(), {"by_ip": {}})
    alerts = Engine(load_rules()).process(ev)
    assert len(alerts) == 1 and alerts[0]["severity"] == "high"


def test_scanner_record_missing_field_rejected():
    with pytest.raises(ValueError):
        normalize({"kind": "scanner", "scanner": "web"}, load_topics(), {"by_ip": {}})
