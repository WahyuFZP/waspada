"""Record mentah -> event ternormalisasi. Artikel: satu event per pasangan topic x category yang cocok."""
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import yaml

import geoip
import parsers

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


def normalize(article, topics, assets=None):
    """Validasi record (batas kepercayaan: datang dari luar) lalu petakan ke nol atau lebih event.

    Field 'kind' memilih parser: news (default, artikel RSS), auth (sshd), suricata (eve.json), kev (kev.py).
    """
    kind = article.get("kind", "news")
    if kind != "news":
        if kind == "auth":
            events = parsers.parse_auth(article, parse_ts)
        elif kind == "suricata":
            events = parsers.parse_suricata(article, parse_ts, assets or {"by_ip": {}})
        elif kind == "kev":
            events = parsers.parse_kev(article, parse_ts)
        else:
            raise ValueError(f"kind tidak dikenal: {kind!r}")
        # penanda data simulasi supaya dashboard bisa melabelinya dan data demo mudah dihapus;
        # geo = negara & pemilik jaringan IP sumber (offline, lihat geoip.py)
        return [{**e, "demo": bool(article.get("demo")), **({"geo": geoip.lookup(e["src_ip"])} if e.get("src_ip") else {})}
                for e in events]

    for field in ("timestamp", "source", "region", "title"):
        if not article.get(field):
            raise ValueError(f"field wajib kosong: {field}")
    if article["region"] not in REGIONS:
        raise ValueError(f"region harus salah satu dari {sorted(REGIONS)}")
    # url dipasang sebagai link di dashboard & Discord: hanya http(s), tolak javascript:/data: dan sejenisnya
    if article.get("url") and urlsplit(str(article["url"])).scheme not in ("http", "https"):
        raise ValueError("url harus diawali http:// atau https://")
    ts =parse_ts(article["timestamp"]).astimezone(timezone.utc)

    text = f"{article['title']} {article.get('summary', '')}"
    base = {
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": str(article["source"]).lower(),
        "region": article["region"],
        "title": article["title"],
        "url": article.get("url"),
        "raw": article,
        "demo": bool(article.get("demo")),
    }
    return [
        {**base, "topic": topic, "event_type": f"news.{cat}"}
        for topic, t_re in topics["topics"].items() if t_re.search(text)
        for cat, c_re in topics["categories"].items() if c_re.search(text)
    ]
