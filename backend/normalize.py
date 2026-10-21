"""Artikel mentah -> event ternormalisasi (satu event per pasangan topic x category yang cocok)."""
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

REGIONS = {"domestic", "foreign"}


def load_topics(path=Path(__file__).with_name("topics.yaml")):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    # kata utuh + akhiran Inggris opsional (warship -> warships, deploy -> deployed)
    compile_ = lambda kws: re.compile(r"\b(?:" + "|".join(map(re.escape, kws)) + r")(?:s|es|ed)?\b", re.I)
    return {k: {name: compile_(kws) for name, kws in data[k].items()} for k in ("topics", "categories")}


def parse_ts(value):
    """ISO-8601 -> aware UTC datetime. Tanpa zona waktu dianggap UTC."""
    ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def normalize(article, topics):
    """Validasi artikel (batas kepercayaan: datang dari luar) lalu petakan ke nol atau lebih event."""
    for field in ("timestamp", "source", "region", "title"):
        if not article.get(field):
            raise ValueError(f"field wajib kosong: {field}")
    if article["region"] not in REGIONS:
        raise ValueError(f"region harus salah satu dari {sorted(REGIONS)}")
    ts = parse_ts(article["timestamp"]).astimezone(timezone.utc)

    text = f"{article['title']} {article.get('summary', '')}"
    base = {
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": str(article["source"]).lower(),
        "region": article["region"],
        "title": article["title"],
        "url": article.get("url"),
        "raw": article,
    }
    return [
        {**base, "topic": topic, "event_type": f"news.{cat}"}
        for topic, t_re in topics["topics"].items() if t_re.search(text)
        for cat, c_re in topics["categories"].items() if c_re.search(text)
    ]
