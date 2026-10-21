"""Replay skenario sintetis (JSONL, satu artikel per baris) ke POST /ingest — demo deterministik."""
import argparse
import json
import time

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("scenario")
parser.add_argument("--api", default="http://localhost:8000")
parser.add_argument("--delay", type=float, default=1.5, help="jeda antar artikel (detik) supaya terlihat satu per satu")
args = parser.parse_args()

with open(args.scenario, encoding="utf-8") as f:
    articles = [json.loads(line) for line in f if line.strip()]

for article in articles:
    r = httpx.post(f"{args.api}/ingest", json=article, timeout=15)
    r.raise_for_status()
    result = r.json()
    print(f"{article['timestamp']} {article['source']:<8} {article['title']}")
    print(f"    -> {result['events']} event, {len(result['alerts'])} alert"
          + (" (duplikat, dilewati)" if result["skipped_duplicates"] else ""))
    time.sleep(args.delay)
