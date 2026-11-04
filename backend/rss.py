"""Poll feed RSS di feeds.yaml dan kirim artikelnya ke POST /ingest (duplikat URL dibuang oleh API)."""
import argparse
import logging
import os
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import httpx
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
socket.setdefaulttimeout(20)  # satu feed yang lambat tidak boleh menahan polling feed lain selamanya
AGENT = "Mozilla/5.0 (compatible; WASPADA-OSINT/1.0)"  # beberapa penerbit menolak user-agent bawaan feedparser


def articles_from(feed):
    parsed = feedparser.parse(feed["url"], agent=AGENT)
    for entry in parsed.entries:
        when = entry.get("published_parsed") or entry.get("updated_parsed")
        ts = datetime(*when[:6], tzinfo=timezone.utc) if when else datetime.now(timezone.utc)
        if entry.get("title"):
            yield {"timestamp": ts.isoformat(), "source": feed["name"], "region": feed["region"],
                   "title": entry.title, "summary": entry.get("summary", ""), "url": entry.get("link")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--interval", type=int, default=300, help="detik antar polling")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    feeds = yaml.safe_load(Path(__file__).with_name("feeds.yaml").read_text(encoding="utf-8"))

    while True:
        for feed in feeds:
            try:
                batch = sorted(articles_from(feed), key=lambda a: a["timestamp"])
                r = httpx.post(f"{args.api}/ingest", json=batch, timeout=30, headers={"X-Ingest-Token": os.environ.get("INGEST_TOKEN", "")})
                r.raise_for_status()
                logging.info("%s: %d artikel -> %s", feed["name"], len(batch), r.json())
            except Exception as exc:  # satu feed rusak tidak boleh menghentikan feed lain
                logging.warning("%s gagal: %s", feed["name"], exc)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
